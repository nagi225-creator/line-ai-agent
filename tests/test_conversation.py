"""
会話機能のテスト
"""
import pytest
import asyncio
from datetime import datetime

# テスト用にパスを追加
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import Customer, PersonaType, ConversationStatus
from app.persona_analyzer import persona_analyzer
from app.knowledge_base import knowledge_base


class TestPersonaAnalyzer:
    """ペルソナ分析のテスト"""
    
    def setup_method(self):
        """各テスト前の初期化"""
        self.customer = Customer(user_id="test_user_001")
    
    def test_extract_occupation_company_worker(self):
        """会社員の抽出テスト"""
        message = "私は会社員です。平日は仕事で忙しいです。"
        customer = persona_analyzer.analyze_message(message, self.customer)
        assert customer.occupation == "会社員"
    
    def test_extract_occupation_housewife(self):
        """主婦の抽出テスト"""
        message = "専業主婦をしています。子どもが2人います。"
        customer = persona_analyzer.analyze_message(message, self.customer)
        assert customer.occupation == "主婦"
    
    def test_extract_genres(self):
        """興味ジャンルの抽出テスト"""
        message = "料理が好きで、毎日お弁当を作っています。ダイエットにも興味があります。"
        customer = persona_analyzer.analyze_message(message, self.customer)
        assert "料理" in customer.interest_genre
        assert "ダイエット" in customer.interest_genre
    
    def test_extract_challenges(self):
        """課題の抽出テスト"""
        message = "副業で稼ぎたいのですが、時間が無いのが悩みです。"
        customer = persona_analyzer.analyze_message(message, self.customer)
        assert "副業" in customer.challenges or any("時間" in c for c in customer.challenges)
    
    def test_estimate_persona_side_worker(self):
        """副業ワーカーペルソナの判定テスト"""
        self.customer.occupation = "会社員"
        self.customer.challenges = ["時間が無い", "副業で稼ぎたい"]
        
        persona = persona_analyzer._estimate_persona(self.customer)
        assert persona == PersonaType.SIDE_WORKER
    
    def test_estimate_persona_child_raising_mom(self):
        """子育てママペルソナの判定テスト"""
        self.customer.occupation = "主婦"
        self.customer.challenges = ["育児と両立したい", "在宅で稼ぎたい"]
        
        persona = persona_analyzer._estimate_persona(self.customer)
        assert persona == PersonaType.CHILD_RAISING_MOM


class TestKnowledgeBase:
    """ナレッジベースのテスト"""
    
    def setup_method(self):
        """各テスト前の初期化"""
        knowledge_base.load()
    
    def test_load_success_cases(self):
        """成功事例の読み込みテスト"""
        assert len(knowledge_base.success_cases) > 0
    
    def test_load_faqs(self):
        """FAQの読み込みテスト"""
        assert len(knowledge_base.faqs) > 0
    
    def test_search_success_cases_by_persona(self):
        """ペルソナによる成功事例検索テスト"""
        cases = knowledge_base.search_success_cases(
            persona="子育てママ",
            limit=3
        )
        assert len(cases) > 0
        # 子育てママに関連する事例が含まれているか
        has_related = any("子育てママ" in case.related_personas for case in cases)
        assert has_related
    
    def test_search_success_cases_by_challenge(self):
        """課題による成功事例検索テスト"""
        cases = knowledge_base.search_success_cases(
            challenges=["時間が無い"],
            limit=3
        )
        assert len(cases) > 0
    
    def test_search_faqs_by_keyword(self):
        """キーワードによるFAQ検索テスト"""
        faqs = knowledge_base.search_faqs(
            keywords=["初心者"],
            limit=3
        )
        assert len(faqs) > 0
        # 初心者に関連するFAQが含まれているか
        has_related = any("初心者" in faq.keywords or "初心者" in faq.question for faq in faqs)
        assert has_related
    
    def test_search_faqs_by_price(self):
        """料金関連のFAQ検索テスト"""
        faqs = knowledge_base.search_faqs(
            keywords=["料金"],
            limit=3
        )
        assert len(faqs) > 0
    
    def test_exclude_mentioned_cases(self):
        """言及済み事例の除外テスト"""
        # まず全ての事例IDを取得
        all_case_ids = [case.id for case in knowledge_base.success_cases]
        
        # 最初の事例を除外して検索
        if all_case_ids:
            cases = knowledge_base.search_success_cases(
                exclude_ids=[all_case_ids[0]],
                limit=10
            )
            result_ids = [case.id for case in cases]
            assert all_case_ids[0] not in result_ids


class TestConversationFlow:
    """会話フローのテスト"""
    
    def test_initial_greeting(self):
        """初期挨拶のテスト"""
        customer = Customer(
            user_id="test_user_002",
            display_name="テスト太郎"
        )
        # ウェルカムメッセージに名前が含まれるか確認
        # （実際のAI応答はモックが必要）
        assert customer.display_name is not None
    
    def test_status_progression(self):
        """ステータス遷移のテスト"""
        customer = Customer(user_id="test_user_003")
        
        # 初期状態
        assert customer.status == ConversationStatus.INITIAL
        
        # ステータス更新
        customer.status = ConversationStatus.HEARING
        assert customer.status == ConversationStatus.HEARING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
