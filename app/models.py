"""
データモデル定義
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class PersonaType(str, Enum):
    """顧客ペルソナタイプ"""
    SIDE_WORKER = "副業ワーカー"      # 会社員で副業を探している
    CHILD_RAISING_MOM = "子育てママ"   # 育児中の主婦・パート
    BUSINESS_OWNER = "ビジネスオーナー" # 経営者・役員
    SELF_ACHIEVER = "自己実現チャレンジャー"  # 自由・可能性を求める
    UNKNOWN = "未特定"


class ConversationStatus(str, Enum):
    """会話ステータス"""
    INITIAL = "友だち追加直後"
    HEARING = "ヒアリング中"
    SEMINAR_INVITED = "勉強会案内済み"
    SEMINAR_APPLIED = "勉強会申込済み"
    SEMINAR_ATTENDED = "勉強会参加済み"
    CONSULTATION_INVITED = "個別相談案内済み"
    CONSULTATION_SCHEDULED = "個別相談予約済み"
    CONSULTATION_DONE = "個別相談完了"


class Customer(BaseModel):
    """顧客情報"""
    user_id: str = Field(..., description="LINE ユーザーID")
    display_name: Optional[str] = Field(None, description="LINE表示名")
    
    # プロファイル情報
    occupation: Optional[str] = Field(None, description="職業")
    interest_genre: Optional[List[str]] = Field(default_factory=list, description="興味ジャンル")
    challenges: Optional[List[str]] = Field(default_factory=list, description="課題・悩み")
    goals: Optional[str] = Field(None, description="目標")
    
    # ペルソナ・ステータス
    persona: PersonaType = Field(default=PersonaType.UNKNOWN, description="推定ペルソナ")
    status: ConversationStatus = Field(default=ConversationStatus.INITIAL, description="会話ステータス")
    
    # メタ情報
    source: Optional[str] = Field(None, description="流入経路")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True


class Message(BaseModel):
    """メッセージ"""
    id: Optional[str] = None
    user_id: str
    role: str = Field(..., description="user または assistant")
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ConversationContext(BaseModel):
    """会話コンテキスト"""
    customer: Customer
    messages: List[Message] = Field(default_factory=list)
    current_topic: Optional[str] = None
    mentioned_cases: List[str] = Field(default_factory=list, description="言及済みの成功事例ID")


class SuccessCase(BaseModel):
    """成功事例"""
    id: str
    title: str
    customer_profile: str = Field(..., description="顧客属性（年齢、職業など）")
    genre: str = Field(..., description="ジャンル")
    initial_situation: str = Field(..., description="開始時の状況")
    achievement: str = Field(..., description="達成した成果")
    period: str = Field(..., description="期間")
    success_points: str = Field(..., description="成功のポイント")
    related_personas: List[str] = Field(default_factory=list)
    related_challenges: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)


class FAQ(BaseModel):
    """よくある質問"""
    id: str
    category: str
    question: str
    answer: str
    related_personas: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
