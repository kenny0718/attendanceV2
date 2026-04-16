"""應用程式設定"""

import os
import sys
from datetime import datetime, timezone
from pydantic_settings import BaseSettings, SettingsConfigDict


def is_testing() -> bool:
    """檢測是否在測試模式
    
    檢測方式：
    1. pytest 是否在運行
    2. TESTING 環境變數
    """
    if "pytest" in sys.modules:
        return True
    
    testing_env = os.getenv("TESTING", "false").lower()
    if testing_env in ("true", "1", "yes"):
        return True
    
    return False


def get_utc_now() -> datetime:
    """取得當前 UTC 時間"""
    return datetime.now(timezone.utc)


class Settings(BaseSettings):
    """應用程式設定"""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    app_name: str = "Attendance V2 API"
    debug: bool = False

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:Raxcxtjq260!@127.0.0.1:5432/attendance_db",
    )

    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY",
        "dev-secret-key-change-in-production-min-32-chars-required",
    )
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
    refresh_token_days: int = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))
    session_idle_timeout_minutes: int = int(os.getenv("SESSION_IDLE_TIMEOUT_MINUTES", "60"))
    session_absolute_timeout_hours: int = int(os.getenv("SESSION_ABSOLUTE_TIMEOUT_HOURS", "12"))
    refresh_cookie_name: str = os.getenv("REFRESH_COOKIE_NAME", "attendance_refresh_token")
    refresh_cookie_secure: bool = os.getenv("REFRESH_COOKIE_SECURE", "false").lower() in ("true", "1", "yes")
    refresh_cookie_samesite: str = os.getenv("REFRESH_COOKIE_SAMESITE", "lax")


settings = Settings()
