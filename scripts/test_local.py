"""
ローカルテスト用スクリプト
LINE接続なしでAI応答をテストできます
"""
import asyncio
import sys
from pathlib import Path

# パスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.models import Customer, Message, ConversationContext, PersonaType, ConversationStatus
from app.database import db
from app.knowledge_base import knowledge_base
from app.ai_engine import initialize_ai_engine
from app.persona_analyzer import persona_analyzer
from config import get_settings


async def test_conversation():
    """会話テスト"""
    print("=" * 60)
    print("LINE自動応答AIエージェント - ローカルテスト")
    print("=" * 60)
    
    # 設定読み込み
    try:
        settings = get_settings()
    except Exception as e:
        print(f"\n⚠️ 環境変数が設定されていません: {e}")
        print("`.env.example` をコピーして `.env` を作成し、APIキーを設定してください。")
        return
    
    # 初期化
    print("\n🔄 システム初期化中...")
    await db.initialize()
    knowledge_base.load()
    ai_engine = initialize_ai_engine(
        api_key=settings.openai_api_key,
        model=settings.openai_model
    )
    print(f"✅ ナレッジベース: {len(knowledge_base.success_cases)}件の成功事例, {len(knowledge_base.faqs)}件のFAQ")
    
    # テスト用顧客を作成
    test_user_id = "test_local_user"
    customer = Customer(
        user_id=test_user_id,
        display_name="テストユーザー",
        status=ConversationStatus.INITIAL
    )
    await db.save_customer(customer)
    
    # ウェルカムメッセージ
    welcome = await ai_engine.generate_welcome_message(customer)
    print(f"\n🤖 AIアシスタント:\n{welcome}")
    
    # 会話ループ
    print("\n" + "-" * 60)
    print("💬 会話を開始します（'quit' で終了）")
    print("-" * 60)
    
    messages = []
    
    while True:
        # ユーザー入力
        user_input = input("\n👤 あなた: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 テストを終了します")
            break
        
        if not user_input:
            continue
        
        # メッセージを保存
        user_msg = Message(user_id=test_user_id, role="user", content=user_input)
        messages.append(user_msg)
        await db.save_message(user_msg)
        
        # コンテキストを構築
        context = ConversationContext(
            customer=customer,
            messages=messages,
            mentioned_cases=await db.get_mentioned_cases(test_user_id)
        )
        
        # AI応答を生成
        print("\n🔄 応答生成中...")
        response = await ai_engine.generate_response(context, user_input)
        
        # 顧客情報を更新
        customer = context.customer
        await db.save_customer(customer)
        
        # 応答を保存
        assistant_msg = Message(user_id=test_user_id, role="assistant", content=response)
        messages.append(assistant_msg)
        await db.save_message(assistant_msg)
        
        print(f"\n🤖 AIアシスタント:\n{response}")
        
        # 顧客プロファイル情報を表示
        print(f"\n📊 顧客プロファイル:")
        print(f"   - 職業: {customer.occupation or '未取得'}")
        print(f"   - 興味: {', '.join(customer.interest_genre) if customer.interest_genre else '未取得'}")
        print(f"   - 課題: {', '.join(customer.challenges) if customer.challenges else '未取得'}")
        persona_value = customer.persona if isinstance(customer.persona, str) else customer.persona.value
        print(f"   - ペルソナ: {persona_value}")


async def test_knowledge_search():
    """ナレッジベース検索テスト"""
    print("\n" + "=" * 60)
    print("ナレッジベース検索テスト")
    print("=" * 60)
    
    knowledge_base.load()
    
    # 成功事例検索
    print("\n📚 成功事例検索（ペルソナ: 副業ワーカー）:")
    cases = knowledge_base.search_success_cases(
        persona="副業ワーカー",
        challenges=["時間が無い"],
        limit=2
    )
    for case in cases:
        print(f"  - {case.title}")
    
    # FAQ検索
    print("\n❓ FAQ検索（キーワード: 料金）:")
    faqs = knowledge_base.search_faqs(keywords=["料金"], limit=2)
    for faq in faqs:
        print(f"  Q: {faq.question}")
        print(f"  A: {faq.answer[:50]}...")


async def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ローカルテスト")
    parser.add_argument("--mode", choices=["chat", "knowledge"], default="chat",
                       help="テストモード: chat（会話）, knowledge（ナレッジ検索）")
    args = parser.parse_args()
    
    if args.mode == "chat":
        await test_conversation()
    elif args.mode == "knowledge":
        await test_knowledge_search()


if __name__ == "__main__":
    asyncio.run(main())
