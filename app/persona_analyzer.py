"""
ペルソナ分析モジュール
会話内容から顧客のペルソナを推定し、プロファイルを更新する
"""
from typing import List, Optional, Tuple
import re
from app.models import Customer, PersonaType, ConversationStatus


class PersonaAnalyzer:
    """ペルソナ分析クラス"""
    
    # ペルソナ判定用キーワード
    PERSONA_KEYWORDS = {
        PersonaType.SIDE_WORKER: {
            "occupation": ["会社員", "サラリーマン", "OL", "正社員", "勤め"],
            "keywords": ["副業", "副収入", "仕事終わり", "通勤", "平日", "休日", "本業"],
            "challenges": ["時間が無い", "仕事と両立", "隙間時間"]
        },
        PersonaType.CHILD_RAISING_MOM: {
            "occupation": ["主婦", "主夫", "ママ", "パート", "専業"],
            "keywords": ["育児", "子ども", "子供", "赤ちゃん", "保育園", "幼稚園", "在宅", "家事"],
            "challenges": ["育児と両立", "在宅で", "子どもがいて"]
        },
        PersonaType.BUSINESS_OWNER: {
            "occupation": ["経営", "オーナー", "社長", "役員", "自営", "個人事業", "店舗"],
            "keywords": ["集客", "売上", "ビジネス", "事業", "店", "サロン", "会社"],
            "challenges": ["集客を増やしたい", "広告費", "新規顧客"]
        },
        PersonaType.SELF_ACHIEVER: {
            "occupation": [],  # 職業は問わない
            "keywords": ["自由", "可能性", "挑戦", "夢", "好きなこと", "自分らしく", "新しい"],
            "challenges": ["自分を変えたい", "何か始めたい", "可能性を広げたい"]
        }
    }
    
    # 興味ジャンルキーワード
    GENRE_KEYWORDS = {
        "料理": ["料理", "レシピ", "お弁当", "食事", "クッキング", "ご飯"],
        "ダイエット": ["ダイエット", "痩せ", "体重", "ボディメイク", "筋トレ"],
        "美容": ["美容", "コスメ", "メイク", "スキンケア", "美肌"],
        "育児": ["育児", "子育て", "子ども", "ママ", "赤ちゃん"],
        "ビジネス": ["ビジネス", "仕事", "キャリア", "自己啓発", "投資"],
        "ハンドメイド": ["ハンドメイド", "手作り", "クラフト", "アクセサリー", "DIY"],
        "ライフスタイル": ["日常", "暮らし", "インテリア", "旅行", "カフェ"]
    }
    
    # 課題キーワード
    CHALLENGE_KEYWORDS = [
        "時間が無い", "時間がない", "忙しい",
        "自己流の限界", "伸び悩み", "やり方がわからない",
        "稼ぎたい", "収入", "収益化",
        "初心者", "未経験", "始めたい",
        "不安", "自信がない", "できるか",
        "在宅", "家で", "リモート",
        "副業", "本業以外",
        "両立", "育児", "仕事"
    ]
    
    def analyze_message(self, message: str, customer: Customer) -> Customer:
        """
        メッセージを分析して顧客プロファイルを更新
        
        Args:
            message: 顧客のメッセージ
            customer: 現在の顧客情報
        
        Returns:
            更新された顧客情報
        """
        # 職業の抽出
        occupation = self._extract_occupation(message)
        if occupation and not customer.occupation:
            customer.occupation = occupation
        
        # 興味ジャンルの抽出
        genres = self._extract_genres(message)
        if genres:
            existing = set(customer.interest_genre or [])
            customer.interest_genre = list(existing | set(genres))
        
        # 課題の抽出
        challenges = self._extract_challenges(message)
        if challenges:
            existing = set(customer.challenges or [])
            customer.challenges = list(existing | set(challenges))
        
        # ペルソナの推定
        if customer.persona == PersonaType.UNKNOWN or customer.persona == "未特定":
            customer.persona = self._estimate_persona(customer)
        
        return customer
    
    def _extract_occupation(self, message: str) -> Optional[str]:
        """メッセージから職業を抽出"""
        message_lower = message.lower()
        
        # 直接的な職業表現を探す
        patterns = [
            (r"会社員", "会社員"),
            (r"サラリーマン", "会社員"),
            (r"OL", "会社員"),
            (r"主婦|専業主婦", "主婦"),
            (r"主夫", "主夫"),
            (r"パート|アルバイト", "パート・アルバイト"),
            (r"経営者|社長|オーナー", "経営者"),
            (r"役員", "経営者・役員"),
            (r"自営業|個人事業", "自営業"),
            (r"フリーランス", "フリーランス"),
            (r"学生", "学生"),
        ]
        
        for pattern, occupation in patterns:
            if re.search(pattern, message):
                return occupation
        
        return None
    
    def _extract_genres(self, message: str) -> List[str]:
        """メッセージから興味ジャンルを抽出"""
        found_genres = []
        message_lower = message.lower()
        
        for genre, keywords in self.GENRE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message or keyword in message_lower:
                    if genre not in found_genres:
                        found_genres.append(genre)
                    break
        
        return found_genres
    
    def _extract_challenges(self, message: str) -> List[str]:
        """メッセージから課題を抽出"""
        found_challenges = []
        
        for challenge in self.CHALLENGE_KEYWORDS:
            if challenge in message:
                found_challenges.append(challenge)
        
        return found_challenges
    
    def _estimate_persona(self, customer: Customer) -> PersonaType:
        """顧客情報からペルソナを推定"""
        scores = {
            PersonaType.SIDE_WORKER: 0,
            PersonaType.CHILD_RAISING_MOM: 0,
            PersonaType.BUSINESS_OWNER: 0,
            PersonaType.SELF_ACHIEVER: 0
        }
        
        # 職業によるスコアリング
        if customer.occupation:
            for persona, keywords in self.PERSONA_KEYWORDS.items():
                for occ_keyword in keywords["occupation"]:
                    if occ_keyword in customer.occupation:
                        scores[persona] += 5
                        break
        
        # 興味ジャンルによるスコアリング
        if customer.interest_genre:
            genre_str = " ".join(customer.interest_genre)
            for persona, keywords in self.PERSONA_KEYWORDS.items():
                for keyword in keywords["keywords"]:
                    if keyword in genre_str:
                        scores[persona] += 2
        
        # 課題によるスコアリング
        if customer.challenges:
            challenge_str = " ".join(customer.challenges)
            for persona, keywords in self.PERSONA_KEYWORDS.items():
                for challenge in keywords["challenges"]:
                    if challenge in challenge_str:
                        scores[persona] += 3
        
        # 最高スコアのペルソナを選択
        max_score = max(scores.values())
        if max_score > 0:
            for persona, score in scores.items():
                if score == max_score:
                    return persona
        
        return PersonaType.UNKNOWN
    
    def get_persona_description(self, persona: PersonaType) -> str:
        """ペルソナの説明を取得"""
        descriptions = {
            PersonaType.SIDE_WORKER: "本業を持ちながら副収入を求めている方",
            PersonaType.CHILD_RAISING_MOM: "育児や家事と両立しながら在宅収入を求めている方",
            PersonaType.BUSINESS_OWNER: "事業の集客やブランディングにInstagramを活用したい方",
            PersonaType.SELF_ACHIEVER: "新しい可能性に挑戦し、自分らしい働き方を求めている方",
            PersonaType.UNKNOWN: "まだ詳しくお話をお聞きできていない方"
        }
        return descriptions.get(persona, descriptions[PersonaType.UNKNOWN])


# グローバルインスタンス
persona_analyzer = PersonaAnalyzer()
