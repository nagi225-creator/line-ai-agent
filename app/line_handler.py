"""
LINE Webhook ハンドラー
LINE Messaging APIからのイベントを処理
Lステップとの連携機能を含む
"""
import hashlib
import hmac
import base64
from datetime import datetime
from typing import Optional
import logging
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    TextMessage,
    PushMessageRequest
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    FollowEvent,
    UnfollowEvent
)
from linebot.v3.exceptions import InvalidSignatureError

from app.models import Customer, Message, ConversationStatus, PersonaType
from app.database import db
from app.ai_engine import ai_engine
from app.lstep_client import lstep_client, LstepDataMapper

logger = logging.getLogger(__name__)


class LineHandler:
    """LINE Webhookハンドラークラス"""
    
    def __init__(
        self, 
        channel_access_token: str, 
        channel_secret: str,
        ai_mode_tag: str = "AI対話モード"
    ):
        self.channel_secret = channel_secret
        self.ai_mode_tag = ai_mode_tag
        
        # LINE API設定
        configuration = Configuration(access_token=channel_access_token)
        self.api_client = AsyncApiClient(configuration)
        self.line_bot_api = AsyncMessagingApi(self.api_client)
        
        # Webhookハンドラー
        self.handler = WebhookHandler(channel_secret)
        
        # イベントハンドラーを登録
        self._register_handlers()
    
    def _register_handlers(self):
        """イベントハンドラーを登録"""
        
        @self.handler.add(FollowEvent)
        async def handle_follow(event: FollowEvent):
            """友だち追加イベント"""
            await self._handle_follow(event)
        
        @self.handler.add(UnfollowEvent)
        async def handle_unfollow(event: UnfollowEvent):
            """ブロックイベント"""
            await self._handle_unfollow(event)
        
        @self.handler.add(MessageEvent, message=TextMessageContent)
        async def handle_text_message(event: MessageEvent):
            """テキストメッセージイベント"""
            await self._handle_text_message(event)
    
    async def _handle_follow(self, event: FollowEvent):
        """友だち追加時の処理"""
        user_id = event.source.user_id
        
        # ユーザープロファイルを取得
        try:
            profile = await self.line_bot_api.get_profile(user_id)
            display_name = profile.display_name
        except Exception:
            display_name = None
        
        # 顧客情報を作成
        customer = Customer(
            user_id=user_id,
            display_name=display_name,
            status=ConversationStatus.INITIAL,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Lステップから追加情報を取得
        customer = await self._enrich_customer_from_lstep(customer)
        
        # 保存
        await db.save_customer(customer)
        
        # AI対話モードがONの場合のみウェルカムメッセージを送信
        if await self._should_ai_respond(user_id):
            if ai_engine:
                welcome_message = await ai_engine.generate_welcome_message(customer)
                
                # メッセージを保存
                assistant_msg = Message(
                    user_id=user_id,
                    role="assistant",
                    content=welcome_message
                )
                await db.save_message(assistant_msg)
                
                # 返信
                await self.line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=welcome_message)]
                    )
                )
        else:
            logger.info(f"AI mode not enabled for user {user_id}, skipping welcome message")
    
    async def _handle_unfollow(self, event: UnfollowEvent):
        """ブロック時の処理"""
        # 必要に応じてログを記録
        user_id = event.source.user_id
        print(f"User {user_id} unfollowed")
    
    async def _handle_text_message(self, event: MessageEvent):
        """テキストメッセージの処理"""
        user_id = event.source.user_id
        user_message = event.message.text
        
        # AI対話モードを確認
        if not await self._should_ai_respond(user_id):
            logger.info(f"AI mode not enabled for user {user_id}, ignoring message")
            return  # Lステップに処理を任せる
        
        # ユーザーメッセージを保存
        user_msg = Message(
            user_id=user_id,
            role="user",
            content=user_message
        )
        await db.save_message(user_msg)
        
        # 人間への転送リクエストを検知
        if self._is_handoff_request(user_message):
            await self._handle_handoff(event, user_id, user_message)
            return
        
        # 会話コンテキストを取得
        context = await db.get_conversation_context(user_id)
        
        # Lステップから最新情報を取得して反映
        context.customer = await self._enrich_customer_from_lstep(context.customer)
        
        # AI応答を生成
        if ai_engine:
            response_text = await ai_engine.generate_response(context, user_message)
            
            # 顧客情報を更新（ペルソナ分析の結果）
            await db.save_customer(context.customer)
            
            # Lステップにもペルソナ情報を同期
            await self._sync_to_lstep(context.customer)
            
            # 応答メッセージを保存
            assistant_msg = Message(
                user_id=user_id,
                role="assistant",
                content=response_text
            )
            await db.save_message(assistant_msg)
            
            # 返信
            await self.line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=response_text)]
                )
            )
        else:
            # AIエンジンが初期化されていない場合
            await self.line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(
                        text="申し訳ありません、現在システムの準備中です。しばらくお待ちください🙏"
                    )]
                )
            )
    
    async def _should_ai_respond(self, user_id: str) -> bool:
        """
        AI対話モードが有効かどうかを確認
        Lステップで特定のタグが付いている場合のみAIが応答
        """
        if not lstep_client:
            # Lステップ未設定の場合は常にAIが応答
            return True
        
        try:
            tags = await lstep_client.get_friend_tags(user_id)
            return self.ai_mode_tag in tags
        except Exception as e:
            logger.error(f"Failed to check AI mode tag: {e}")
            # エラー時はAIが応答する（フォールバック）
            return True
    
    async def _enrich_customer_from_lstep(self, customer: Customer) -> Customer:
        """Lステップから顧客情報を取得して補完"""
        if not lstep_client:
            return customer
        
        try:
            # タグを取得
            tags = await lstep_client.get_friend_tags(customer.user_id)
            
            if tags:
                # 流入経路を抽出
                source = LstepDataMapper.extract_source_from_tags(tags)
                if source and not customer.source:
                    customer.source = source
                
                # ペルソナを推定
                persona = LstepDataMapper.extract_persona_from_tags(tags)
                if persona and (customer.persona == PersonaType.UNKNOWN or customer.persona == "未特定"):
                    customer.persona = persona
                
                # ジャンルを抽出
                genres = LstepDataMapper.extract_genres_from_tags(tags)
                if genres:
                    existing = set(customer.interest_genre or [])
                    customer.interest_genre = list(existing | set(genres))
            
            # カスタムフィールドを取得
            custom_fields = await lstep_client.get_custom_fields(customer.user_id)
            
            if custom_fields:
                # アンケート回答などを反映
                if "occupation" in custom_fields and not customer.occupation:
                    customer.occupation = custom_fields["occupation"]
                if "goals" in custom_fields and not customer.goals:
                    customer.goals = custom_fields["goals"]
                    
        except Exception as e:
            logger.error(f"Failed to enrich customer from Lstep: {e}")
        
        return customer
    
    async def _sync_to_lstep(self, customer: Customer):
        """顧客情報をLステップに同期"""
        if not lstep_client:
            return
        
        try:
            # ペルソナをタグとして追加
            persona_value = customer.persona if isinstance(customer.persona, str) else customer.persona.value
            if persona_value and persona_value != "未特定":
                await lstep_client.add_tag(customer.user_id, f"ペルソナ:{persona_value}")
            
            # 興味ジャンルをタグとして追加
            for genre in (customer.interest_genre or []):
                await lstep_client.add_tag(customer.user_id, f"興味:{genre}")
                
        except Exception as e:
            logger.error(f"Failed to sync to Lstep: {e}")
    
    def _is_handoff_request(self, message: str) -> bool:
        """人間への転送リクエストを検知"""
        handoff_keywords = [
            "人と話したい",
            "担当者と話したい",
            "スタッフと話したい",
            "人間と話したい",
            "オペレーター",
            "問い合わせ",
            "クレーム",
            "返金",
            "解約"
        ]
        return any(keyword in message for keyword in handoff_keywords)
    
    async def _handle_handoff(self, event: MessageEvent, user_id: str, message: str):
        """人間への転送処理"""
        # Lステップに通知
        if lstep_client:
            await lstep_client.notify_staff(
                user_id,
                f"【人間対応リクエスト】\nユーザーメッセージ: {message}"
            )
            # AI対話モードを解除
            await lstep_client.remove_tag(user_id, self.ai_mode_tag)
        
        # ユーザーに返信
        await self.line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(
                    text="承知いたしました。担当スタッフにお繋ぎいたしますので、少々お待ちください🙏\n\nスタッフより改めてご連絡いたします。"
                )]
            )
        )
    
    def verify_signature(self, body: str, signature: str) -> bool:
        """署名を検証"""
        hash_value = hmac.new(
            self.channel_secret.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_signature = base64.b64encode(hash_value).decode('utf-8')
        return hmac.compare_digest(signature, expected_signature)
    
    async def handle_webhook(self, body: str, signature: str):
        """Webhookを処理"""
        if not self.verify_signature(body, signature):
            raise InvalidSignatureError("Invalid signature")
        
        self.handler.handle(body, signature)


# グローバルインスタンス（初期化は後で行う）
line_handler: Optional[LineHandler] = None


def initialize_line_handler(
    channel_access_token: str, 
    channel_secret: str,
    ai_mode_tag: str = "AI対話モード"
):
    """LINE Handlerを初期化"""
    global line_handler
    line_handler = LineHandler(
        channel_access_token=channel_access_token,
        channel_secret=channel_secret,
        ai_mode_tag=ai_mode_tag
    )
    return line_handler
