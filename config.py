"""
アプリケーション設定
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # LINE Messaging API
    line_channel_access_token: str = Field(..., env="LINE_CHANNEL_ACCESS_TOKEN")
    line_channel_secret: str = Field(..., env="LINE_CHANNEL_SECRET")
    
    # OpenAI
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    
    # Lステップ連携
    lstep_api_key: Optional[str] = Field(default=None, env="LSTEP_API_KEY")
    lstep_account_id: Optional[str] = Field(default=None, env="LSTEP_ACCOUNT_ID")
    lstep_ai_mode_tag: str = Field(default="AI対話モード", env="LSTEP_AI_MODE_TAG")
    
    # Application
    app_env: str = Field(default="development", env="APP_ENV")
    debug: bool = Field(default=True, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/database.db",
        env="DATABASE_URL"
    )
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    @property
    def lstep_enabled(self) -> bool:
        """Lステップ連携が有効かどうか"""
        return bool(self.lstep_api_key and self.lstep_account_id)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """設定のシングルトンインスタンスを取得"""
    return Settings()
