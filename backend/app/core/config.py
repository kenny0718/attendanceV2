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
    # Check if pytest is running
    if "pytest" in sys.modules:
        return True
    
    # Check TESTING environment variable
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

    # 資料庫設定：優先吃環境變數 DATABASE_URL，沒有才用預設
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:Raxcxtjq260!@127.0.0.1:5432/attendance_db",
    )

    # JWT 設定 (WP-10-04B)
    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY",
        "dev-secret-key-change-in-production-min-32-chars-required",
    )


settings = Settings()
