"""應用程式設定"""

import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


def is_testing() -> bool:
    """檢測是否在測試模式
    
    檢測方式：
    1. APP_ENV 環境檢查（優先）- production 永不允許
    2. pytest 是否在運行
    3. TESTING 環境變數
    
    WP-11-05D: Production 環境即使 TESTING=true 也必須拒絕
    """
    # WP-11-05D: Production gate - 優先檢查環境類型
    app_env = os.getenv("APP_ENV", "").lower()
    if app_env in ("production", "prod"):
        # Production 環境永不允許測試模式
        return False
    
    # Check if pytest is running
    if "pytest" in sys.modules:
        return True
    
    # Check TESTING environment variable
    testing_env = os.getenv("TESTING", "false").lower()
    if testing_env in ("true", "1", "yes"):
        return True
    
    return False


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


# Timezone configuration (Added to fix ImportError from commit 601387c)
TIMEZONE = ZoneInfo("Asia/Taipei")


def get_current_time() -> datetime:
    """獲取當前時間（帶時區）
    
    Returns:
        datetime: 當前時間（Asia/Taipei UTC+8）
    """
    return datetime.now(TIMEZONE)
