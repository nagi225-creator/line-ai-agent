"""
Lステップ API クライアント
Lステップとの連携機能を提供
"""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LstepClient:
    """Lステップ API クライアント"""
    
    # Lステップ API エンドポイント
    BASE_URL = "https://api.linestep.jp/v1"
    
    def __init__(self, api_key: str, account_id: str):
        """
        Args:
            api_key: Lステップ APIキー
            account_id: Lステップ アカウントID
        """
        self.api_key = api_key
        self.account_id = account_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_friend(self, line_user_id: str) -> Optional[Dict[str, Any]]:
        """
        友だち情報を取得
        
        Args:
            line_user_id: LINE ユーザーID
        
        Returns:
            友だち情報（名前、タグ、カスタムフィールドなど）
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/accounts/{self.account_id}/friends/{line_user_id}",
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.info(f"Friend not found in Lstep: {line_user_id}")
                    return None
                else:
                    logger.error(f"Lstep API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Lstep API request failed: {e}")
            return None
    
    async def get_friend_tags(self, line_user_id: str) -> List[str]:
        """
        友だちのタグ一覧を取得
        
        Args:
            line_user_id: LINE ユーザーID
        
        Returns:
            タグ名のリスト
        """
        friend = await self.get_friend(line_user_id)
        if friend and "tags" in friend:
            return [tag["name"] for tag in friend["tags"]]
        return []
    
    async def add_tag(self, line_user_id: str, tag_name: str) -> bool:
        """
        友だちにタグを追加
        
        Args:
            line_user_id: LINE ユーザーID
            tag_name: タグ名
        
        Returns:
            成功したかどうか
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/accounts/{self.account_id}/friends/{line_user_id}/tags",
                    headers=self.headers,
                    json={"tag_name": tag_name},
                    timeout=10.0
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Tag added: {tag_name} to {line_user_id}")
                    return True
                else:
                    logger.error(f"Failed to add tag: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Lstep API request failed: {e}")
            return False
    
    async def remove_tag(self, line_user_id: str, tag_name: str) -> bool:
        """
        友だちからタグを削除
        
        Args:
            line_user_id: LINE ユーザーID
            tag_name: タグ名
        
        Returns:
            成功したかどうか
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.BASE_URL}/accounts/{self.account_id}/friends/{line_user_id}/tags/{tag_name}",
                    headers=self.headers,
                    timeout=10.0
                )
                
                return response.status_code in [200, 204]
                    
        except Exception as e:
            logger.error(f"Lstep API request failed: {e}")
            return False
    
    async def get_custom_fields(self, line_user_id: str) -> Dict[str, Any]:
        """
        カスタムフィールド（アンケート回答など）を取得
        
        Args:
            line_user_id: LINE ユーザーID
        
        Returns:
            カスタムフィールドの辞書
        """
        friend = await self.get_friend(line_user_id)
        if friend and "custom_fields" in friend:
            return friend["custom_fields"]
        return {}
    
    async def set_custom_field(
        self, 
        line_user_id: str, 
        field_name: str, 
        value: Any
    ) -> bool:
        """
        カスタムフィールドを設定
        
        Args:
            line_user_id: LINE ユーザーID
            field_name: フィールド名
            value: 値
        
        Returns:
            成功したかどうか
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.BASE_URL}/accounts/{self.account_id}/friends/{line_user_id}/custom_fields",
                    headers=self.headers,
                    json={field_name: value},
                    timeout=10.0
                )
                
                return response.status_code in [200, 201]
                    
        except Exception as e:
            logger.error(f"Lstep API request failed: {e}")
            return False
    
    async def trigger_scenario(self, line_user_id: str, scenario_id: str) -> bool:
        """
        シナリオを発動
        
        Args:
            line_user_id: LINE ユーザーID
            scenario_id: シナリオID
        
        Returns:
            成功したかどうか
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/accounts/{self.account_id}/scenarios/{scenario_id}/trigger",
                    headers=self.headers,
                    json={"line_user_id": line_user_id},
                    timeout=10.0
                )
                
                return response.status_code in [200, 201]
                    
        except Exception as e:
            logger.error(f"Lstep API request failed: {e}")
            return False
    
    async def notify_staff(self, line_user_id: str, message: str) -> bool:
        """
        スタッフに通知（人間へのハンドオフ）
        
        Args:
            line_user_id: LINE ユーザーID
            message: 通知メッセージ
        
        Returns:
            成功したかどうか
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/accounts/{self.account_id}/notifications",
                    headers=self.headers,
                    json={
                        "line_user_id": line_user_id,
                        "message": message,
                        "type": "handoff"
                    },
                    timeout=10.0
                )
                
                return response.status_code in [200, 201]
                    
        except Exception as e:
            logger.error(f"Lstep API request failed: {e}")
            return False


class LstepDataMapper:
    """LステップデータをAIシステム用に変換"""
    
    # タグからペルソナへのマッピング
    TAG_TO_PERSONA = {
        "会社員": "副業ワーカー",
        "副業": "副業ワーカー",
        "主婦": "子育てママ",
        "育児": "子育てママ",
        "ママ": "子育てママ",
        "経営者": "ビジネスオーナー",
        "オーナー": "ビジネスオーナー",
        "店舗": "ビジネスオーナー",
    }
    
    # タグからジャンルへのマッピング
    TAG_TO_GENRE = {
        "料理": "料理",
        "レシピ": "料理",
        "ダイエット": "ダイエット",
        "美容": "美容",
        "コスメ": "美容",
        "育児": "育児",
        "子育て": "育児",
        "ビジネス": "ビジネス",
    }
    
    @classmethod
    def extract_persona_from_tags(cls, tags: List[str]) -> Optional[str]:
        """タグからペルソナを推定"""
        for tag in tags:
            for keyword, persona in cls.TAG_TO_PERSONA.items():
                if keyword in tag:
                    return persona
        return None
    
    @classmethod
    def extract_genres_from_tags(cls, tags: List[str]) -> List[str]:
        """タグからジャンルを抽出"""
        genres = []
        for tag in tags:
            for keyword, genre in cls.TAG_TO_GENRE.items():
                if keyword in tag and genre not in genres:
                    genres.append(genre)
        return genres
    
    @classmethod
    def extract_source_from_tags(cls, tags: List[str]) -> Optional[str]:
        """タグから流入経路を抽出"""
        source_keywords = ["Instagram", "X", "Twitter", "Meta", "広告", "紹介"]
        for tag in tags:
            for keyword in source_keywords:
                if keyword in tag:
                    return tag
        return None


# グローバルインスタンス（初期化は後で行う）
lstep_client: Optional[LstepClient] = None


def initialize_lstep_client(api_key: str, account_id: str) -> LstepClient:
    """Lステップクライアントを初期化"""
    global lstep_client
    lstep_client = LstepClient(api_key=api_key, account_id=account_id)
    return lstep_client
