"""
AIエンジン - OpenAI APIを使用した応答生成
"""
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
from datetime import datetime

from app.models import (
    Customer, Message, ConversationContext, 
    PersonaType, ConversationStatus, SuccessCase, FAQ
)
from app.knowledge_base import knowledge_base
from app.persona_analyzer import persona_analyzer


class AIEngine:
    """AI応答生成エンジン"""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """システムプロンプトを読み込み"""
        prompt_path = Path("prompts/system_prompt.txt")
        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        return self._get_default_system_prompt()
    
    def _get_default_system_prompt(self) -> str:
        """デフォルトのシステムプロンプト"""
        return """あなたは「SnsClub」のLINE公式アカウントで活動する、Instagram運用サポートの専門AIアシスタントです。
フレンドリーで親しみやすく、顧客に寄り添った対話を心がけてください。
絵文字も適度に使用し、堅苦しくない自然な会話をしてください。"""
    
    def _build_context_prompt(self, context: ConversationContext) -> str:
        """顧客コンテキストを含むプロンプトを構築"""
        customer = context.customer
        
        # 顧客情報のサマリー
        customer_info = []
        if customer.display_name:
            customer_info.append(f"お名前: {customer.display_name}さん")
        if customer.occupation:
            customer_info.append(f"職業: {customer.occupation}")
        if customer.interest_genre:
            customer_info.append(f"興味ジャンル: {', '.join(customer.interest_genre)}")
        if customer.challenges:
            customer_info.append(f"課題: {', '.join(customer.challenges)}")
        if customer.goals:
            customer_info.append(f"目標: {customer.goals}")
        
        persona_value = customer.persona if isinstance(customer.persona, str) else customer.persona.value
        if persona_value != "未特定":
            customer_info.append(f"推定ペルソナ: {persona_value}")
        
        status_value = customer.status if isinstance(customer.status, str) else customer.status.value
        customer_info.append(f"ステータス: {status_value}")
        
        context_prompt = f"""
## 現在の顧客情報
{chr(10).join(customer_info) if customer_info else "（まだヒアリング前です）"}

## 対話の指針
- この顧客に合わせた対話を心がけてください
- まだ情報が少ない場合は、自然な形でヒアリングを進めてください
- 既に言及した成功事例: {', '.join(context.mentioned_cases) if context.mentioned_cases else 'なし'}
"""
        return context_prompt
    
    def _get_relevant_knowledge(
        self, 
        context: ConversationContext,
        user_message: str
    ) -> str:
        """関連するナレッジを取得"""
        customer = context.customer
        knowledge_parts = []
        
        # キーワード抽出
        keywords = self._extract_keywords(user_message)
        
        # 成功事例の検索
        persona_value = customer.persona if isinstance(customer.persona, str) else customer.persona.value
        cases = knowledge_base.search_success_cases(
            persona=persona_value if persona_value != "未特定" else None,
            challenges=customer.challenges,
            keywords=keywords,
            exclude_ids=context.mentioned_cases,
            limit=2
        )
        
        if cases:
            knowledge_parts.append("## 参考にできる成功事例")
            for case in cases:
                knowledge_parts.append(f"""
### {case.title}
- プロフィール: {case.customer_profile}
- ジャンル: {case.genre}
- 開始時: {case.initial_situation}
- 成果: {case.achievement}
- 期間: {case.period}
- ポイント: {case.success_points}
""")
        
        # FAQの検索（質問っぽい内容の場合）
        if "?" in user_message or "？" in user_message or any(
            word in user_message for word in ["ですか", "ますか", "どう", "いくら", "何"]
        ):
            faqs = knowledge_base.search_faqs(keywords=keywords, limit=2)
            if faqs:
                knowledge_parts.append("## 関連するFAQ")
                for faq in faqs:
                    knowledge_parts.append(f"""
Q: {faq.question}
A: {faq.answer}
""")
        
        return "\n".join(knowledge_parts) if knowledge_parts else ""
    
    def _extract_keywords(self, message: str) -> List[str]:
        """メッセージからキーワードを抽出"""
        # 簡易的なキーワード抽出
        keywords = []
        
        keyword_patterns = [
            "初心者", "料金", "費用", "時間", "仕事", "育児", "副業",
            "稼", "収益", "フォロワー", "ジャンル", "サポート", "講師",
            "勉強会", "個別相談", "料理", "ダイエット", "美容",
            "不安", "大丈夫", "できる", "分割", "支払い"
        ]
        
        for pattern in keyword_patterns:
            if pattern in message:
                keywords.append(pattern)
        
        return keywords
    
    def _build_messages(
        self,
        context: ConversationContext,
        user_message: str,
        knowledge: str
    ) -> List[Dict[str, str]]:
        """API用のメッセージリストを構築"""
        messages = []
        
        # システムプロンプト + コンテキスト + ナレッジ
        full_system_prompt = self.system_prompt
        full_system_prompt += "\n\n" + self._build_context_prompt(context)
        if knowledge:
            full_system_prompt += "\n\n" + knowledge
        
        messages.append({
            "role": "system",
            "content": full_system_prompt
        })
        
        # 会話履歴（直近のメッセージ）
        for msg in context.messages[-10:]:  # 直近10件
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # 現在のユーザーメッセージ
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    async def generate_response(
        self,
        context: ConversationContext,
        user_message: str
    ) -> str:
        """応答を生成"""
        # 顧客プロファイルを更新
        context.customer = persona_analyzer.analyze_message(
            user_message, 
            context.customer
        )
        
        # 関連ナレッジを取得
        knowledge = self._get_relevant_knowledge(context, user_message)
        
        # メッセージを構築
        messages = self._build_messages(context, user_message, knowledge)
        
        # OpenAI APIを呼び出し
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return "申し訳ありません、一時的に応答ができない状態です。少し時間をおいてから再度メッセージをお送りください🙏"
    
    async def generate_welcome_message(self, customer: Customer) -> str:
        """ウェルカムメッセージを生成"""
        name_part = f"{customer.display_name}さん、" if customer.display_name else ""
        
        return f"""こんにちは！{name_part}SnsClubの公式LINEに友だち追加していただき、ありがとうございます😊

私はInstagram運用のサポートを担当しているAIアシスタントです。あなたの目標達成をお手伝いさせていただきますね！

まず、簡単にお伺いしたいのですが、Instagramでどんなことに興味がありますか？✨"""


# グローバルインスタンス（初期化は後で行う）
ai_engine: Optional[AIEngine] = None


def initialize_ai_engine(api_key: str, model: str = "gpt-4-turbo-preview"):
    """AIエンジンを初期化"""
    global ai_engine
    ai_engine = AIEngine(api_key=api_key, model=model)
    return ai_engine
