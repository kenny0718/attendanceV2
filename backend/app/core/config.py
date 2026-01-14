"""應用程式設定"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """應用程式設定"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )
    
    app_name: str = "Attendance V2 API"
    debug: bool = False


# 全域設定實例
settings = Settings()
