"""
ナレッジベース管理
成功事例・FAQ・お役立ち情報を管理し、パーソナライズ検索を提供
"""
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from app.models import SuccessCase, FAQ, PersonaType


class KnowledgeBase:
    """ナレッジベース管理クラス"""
    
    def __init__(self, data_dir: str = "data/knowledge"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.success_cases: List[SuccessCase] = []
        self.faqs: List[FAQ] = []
        
    def load(self):
        """ナレッジベースを読み込み"""
        # 成功事例
        cases_file = self.data_dir / "success_cases.json"
        if cases_file.exists():
            with open(cases_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.success_cases = [SuccessCase(**case) for case in data]
        else:
            self._create_default_success_cases()
        
        # FAQ
        faq_file = self.data_dir / "faq.json"
        if faq_file.exists():
            with open(faq_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.faqs = [FAQ(**faq) for faq in data]
        else:
            self._create_default_faqs()
    
    def _create_default_success_cases(self):
        """デフォルトの成功事例を作成"""
        default_cases = [
            {
                "id": "case_001",
                "title": "育児と両立！半年で月収20万円を達成した主婦Cさんの事例",
                "customer_profile": "30代主婦、2児の母",
                "genre": "料理・お弁当レシピ",
                "initial_situation": "フォロワー0、Instagram完全初心者。毎日の家事育児に追われながら、在宅でできる副収入を探していた",
                "achievement": "フォロワー2万人、月収20万円達成、企業からのPR案件も獲得",
                "period": "半年",
                "success_points": "毎日作っていたお弁当をそのままコンテンツ化。講師のアドバイスで写真の撮り方と投稿時間を最適化。子どもが寝た後の1〜2時間を活用",
                "related_personas": ["子育てママ", "副業ワーカー"],
                "related_challenges": ["在宅で稼ぎたい", "育児と両立したい", "時間が無い"],
                "keywords": ["在宅", "育児", "お弁当", "料理", "主婦", "初心者"]
            },
            {
                "id": "case_002",
                "title": "仕事と両立！隙間時間で半年で月収15万円を達成したBさんの事例",
                "customer_profile": "40代会社員、男性",
                "genre": "ビジネス・自己啓発",
                "initial_situation": "フォロワー500、自己流で1年間運用するも伸び悩み。平日は仕事で忙しく、時間の確保が課題だった",
                "achievement": "フォロワー1.5万人、月収15万円達成。会社員を続けながら副収入を確立",
                "period": "半年",
                "success_points": "通勤時間（往復1時間）と昼休み（30分）を活用した効率的な投稿スケジュールを確立。週末にまとめて投稿を作成するバッチ作業スタイル",
                "related_personas": ["副業ワーカー"],
                "related_challenges": ["時間が無い", "自己流の限界", "副業で稼ぎたい"],
                "keywords": ["副業", "会社員", "時短", "効率化", "ビジネス", "隙間時間"]
            },
            {
                "id": "case_003",
                "title": "完全初心者から3ヶ月でフォロワー5000人！Dさんの急成長事例",
                "customer_profile": "30代パート、女性",
                "genre": "ダイエット・美容",
                "initial_situation": "Instagramのアカウントすら持っていなかった完全初心者。自分のダイエット記録を残したいという軽い気持ちでスタート",
                "achievement": "3ヶ月でフォロワー5,000人達成。現在はアフィリエイト収入も発生",
                "period": "3ヶ月",
                "success_points": "自身のダイエット体験をリアルタイムで発信。Before/Afterの変化が共感を呼び、同じ悩みを持つフォロワーが急増",
                "related_personas": ["子育てママ", "自己実現チャレンジャー"],
                "related_challenges": ["初心者で不安", "何から始めればいいかわからない"],
                "keywords": ["初心者", "ダイエット", "美容", "3ヶ月", "急成長"]
            },
            {
                "id": "case_004",
                "title": "店舗集客に成功！月間来店数2倍を達成したオーナーEさん",
                "customer_profile": "40代エステサロンオーナー、女性",
                "genre": "美容・ビジネス",
                "initial_situation": "地方でエステサロンを経営。広告費をかけてもなかなか新規顧客が増えず、Instagram活用を決意",
                "achievement": "フォロワー8,000人、月間来店数が2倍に増加、広告費50%削減",
                "period": "4ヶ月",
                "success_points": "ビフォーアフターの施術事例を定期投稿。地域タグを活用した地元へのリーチ強化。ストーリーズでの日常発信でファン化を促進",
                "related_personas": ["ビジネスオーナー"],
                "related_challenges": ["集客を増やしたい", "広告費を抑えたい", "事業に活用したい"],
                "keywords": ["集客", "店舗", "サロン", "ビジネス", "経営者"]
            },
            {
                "id": "case_005",
                "title": "好きなことを仕事に！趣味のハンドメイドで月収10万円達成のFさん",
                "customer_profile": "30代主婦、ハンドメイド作家志望",
                "genre": "ハンドメイド・クラフト",
                "initial_situation": "趣味でアクセサリーを作っていたが、販売方法がわからなかった。「私の作品なんて売れるのかな」と不安だった",
                "achievement": "フォロワー1.2万人、月収10万円、ミンネでの販売も開始",
                "period": "半年",
                "success_points": "制作過程をリールで発信し、作品への愛着を伝える。講師のアドバイスで商品撮影と価格設定を最適化",
                "related_personas": ["子育てママ", "自己実現チャレンジャー"],
                "related_challenges": ["好きなことで稼ぎたい", "自分に自信がない"],
                "keywords": ["ハンドメイド", "趣味", "好きなこと", "クラフト", "販売"]
            }
        ]
        
        self.success_cases = [SuccessCase(**case) for case in default_cases]
        self._save_success_cases()
    
    def _create_default_faqs(self):
        """デフォルトのFAQを作成"""
        default_faqs = [
            {
                "id": "faq_001",
                "category": "サービス内容",
                "question": "初心者でも大丈夫ですか？",
                "answer": "もちろんです！SnsClubの生徒さんの約8割は、Instagramをほとんど触ったことがない初心者の方からスタートされています。講師がマンツーマンでサポートしますので、「フォロワーの増やし方」「投稿の作り方」といった基本から、丁寧にお教えします。",
                "related_personas": ["全て"],
                "keywords": ["初心者", "未経験", "不安", "大丈夫"]
            },
            {
                "id": "faq_002",
                "category": "料金・支払い",
                "question": "料金はいくらですか？",
                "answer": "半年間のプログラムで54.8万円となっております。分割払いも可能ですので、ご安心ください。多くの生徒さんが半年以内に投資額を回収されています。詳細は個別相談で担当者が丁寧にご説明いたします。",
                "related_personas": ["全て"],
                "keywords": ["料金", "価格", "費用", "いくら", "金額"]
            },
            {
                "id": "faq_003",
                "category": "料金・支払い",
                "question": "分割払いはできますか？",
                "answer": "はい、分割払いも可能です。詳細な支払いプランについては、個別相談で担当者がご相談に応じますので、お気軽にお問い合わせください。",
                "related_personas": ["全て"],
                "keywords": ["分割", "支払い", "ローン", "月々"]
            },
            {
                "id": "faq_004",
                "category": "サポート体制",
                "question": "どんなサポートがありますか？",
                "answer": "専任の講師によるマンツーマンサポートが基本です。週に1回のZoom面談、LINEでの質問対応（24時間以内に返信）、月1回のグループセミナーなど、手厚いサポート体制を整えています。一人で悩まず、いつでも相談できる環境があります。",
                "related_personas": ["全て"],
                "keywords": ["サポート", "講師", "相談", "質問"]
            },
            {
                "id": "faq_005",
                "category": "時間・両立",
                "question": "仕事や育児と両立できますか？",
                "answer": "多くの生徒さんが、仕事や育児と両立しながら成果を出されています。1日30分〜1時間の作業時間があれば十分に取り組めます。隙間時間の使い方や効率的な運用方法も、講師がしっかりアドバイスします。",
                "related_personas": ["副業ワーカー", "子育てママ"],
                "keywords": ["時間", "両立", "仕事", "育児", "忙しい"]
            },
            {
                "id": "faq_006",
                "category": "成果・実績",
                "question": "本当に稼げるようになりますか？",
                "answer": "個人差はありますが、カリキュラムに沿って継続的に取り組んでいただければ、多くの方が成果を出されています。重要なのは、正しい方法で継続すること。講師が一人ひとりの状況に合わせたアドバイスを行い、目標達成をサポートします。",
                "related_personas": ["全て"],
                "keywords": ["稼げる", "収益", "成果", "結果", "本当"]
            },
            {
                "id": "faq_007",
                "category": "サービス内容",
                "question": "どんなジャンルでも大丈夫ですか？",
                "answer": "料理、ダイエット、美容、育児、ビジネス、ハンドメイドなど、様々なジャンルで成功されている生徒さんがいらっしゃいます。あなたの得意なこと、好きなことを活かしたジャンル選びから、講師がサポートします。",
                "related_personas": ["全て"],
                "keywords": ["ジャンル", "分野", "テーマ", "何でも"]
            },
            {
                "id": "faq_008",
                "category": "勉強会",
                "question": "勉強会はどんな内容ですか？",
                "answer": "無料の勉強会では、Instagram運用の基礎知識、フォロワーの増やし方、収益化の仕組みなどを約90分でお伝えしています。実際の成功事例も多数ご紹介しますので、「自分にもできそう」というイメージが湧くと好評です。",
                "related_personas": ["全て"],
                "keywords": ["勉強会", "セミナー", "内容", "何"]
            },
            {
                "id": "faq_009",
                "category": "個別相談",
                "question": "個別相談では何をしますか？",
                "answer": "個別相談では、あなたの現状や目標をヒアリングし、最適な運用戦略を一緒に考えます。また、SnsClubのサービス詳細やサポート体制についても詳しくご説明します。無理な勧誘は一切ありませんので、ご安心ください。",
                "related_personas": ["全て"],
                "keywords": ["個別相談", "面談", "相談", "何"]
            },
            {
                "id": "faq_010",
                "category": "その他",
                "question": "顔出しは必要ですか？",
                "answer": "顔出しなしでも全く問題ありません。実際に、顔出しせずにフォロワー数万人を達成している生徒さんも多くいらっしゃいます。イラストアイコンや、手元だけの写真など、様々な方法がありますので、ご安心ください。",
                "related_personas": ["全て"],
                "keywords": ["顔出し", "顔", "身バレ", "匿名"]
            }
        ]
        
        self.faqs = [FAQ(**faq) for faq in default_faqs]
        self._save_faqs()
    
    def _save_success_cases(self):
        """成功事例を保存"""
        cases_file = self.data_dir / "success_cases.json"
        with open(cases_file, "w", encoding="utf-8") as f:
            json.dump([case.model_dump() for case in self.success_cases], f, ensure_ascii=False, indent=2)
    
    def _save_faqs(self):
        """FAQを保存"""
        faq_file = self.data_dir / "faq.json"
        with open(faq_file, "w", encoding="utf-8") as f:
            json.dump([faq.model_dump() for faq in self.faqs], f, ensure_ascii=False, indent=2)
    
    def search_success_cases(
        self,
        persona: Optional[str] = None,
        challenges: Optional[List[str]] = None,
        genre: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        exclude_ids: Optional[List[str]] = None,
        limit: int = 3
    ) -> List[SuccessCase]:
        """成功事例を検索"""
        results = []
        exclude_ids = exclude_ids or []
        
        for case in self.success_cases:
            if case.id in exclude_ids:
                continue
            
            score = 0
            
            # ペルソナマッチング
            if persona and persona in case.related_personas:
                score += 3
            
            # 課題マッチング
            if challenges:
                for challenge in challenges:
                    if any(challenge in c for c in case.related_challenges):
                        score += 2
            
            # ジャンルマッチング
            if genre and genre.lower() in case.genre.lower():
                score += 2
            
            # キーワードマッチング
            if keywords:
                for keyword in keywords:
                    if keyword in case.keywords:
                        score += 1
            
            if score > 0:
                results.append((score, case))
        
        # スコア順にソートして上位を返す
        results.sort(key=lambda x: x[0], reverse=True)
        return [case for _, case in results[:limit]]
    
    def search_faqs(
        self,
        keywords: Optional[List[str]] = None,
        category: Optional[str] = None,
        limit: int = 3
    ) -> List[FAQ]:
        """FAQを検索"""
        results = []
        
        for faq in self.faqs:
            score = 0
            
            # カテゴリマッチング
            if category and category in faq.category:
                score += 2
            
            # キーワードマッチング
            if keywords:
                for keyword in keywords:
                    # 質問文でマッチング
                    if keyword in faq.question:
                        score += 3
                    # キーワードリストでマッチング
                    if keyword in faq.keywords:
                        score += 2
                    # 回答文でマッチング
                    if keyword in faq.answer:
                        score += 1
            
            if score > 0:
                results.append((score, faq))
        
        # スコア順にソートして上位を返す
        results.sort(key=lambda x: x[0], reverse=True)
        return [faq for _, faq in results[:limit]]
    
    def get_case_by_id(self, case_id: str) -> Optional[SuccessCase]:
        """IDで成功事例を取得"""
        for case in self.success_cases:
            if case.id == case_id:
                return case
        return None


# グローバルインスタンス
knowledge_base = KnowledgeBase()
