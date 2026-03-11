"""應用程式設定

P1 Time Policy (2026-03-10):
- DB datetime 寫入 → get_utc_now() 或 datetime.now(timezone.utc)
- 業務日期邊界（台灣今日範圍）→ TIMEZONE 計算後轉 UTC 查詢
- get_current_time() 保留僅供顯示/業務邏輯，禁止用於 DB 寫入
"""

import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


def is_testing() -> bool:
    """檢測是否在測試模式

    WP-11-05D: Production 環境即使 TESTING=true 也必須拒絕
    """
    app_env = os.getenv("APP_ENV", "").lower()
    if app_env in ("production", "prod"):
        return False
    if "pytest" in sys.modules:
        return True
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

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:Raxcxtjq260!@127.0.0.1:5432/attendance_db",
    )

    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY",
        "dev-secret-key-change-in-production-min-32-chars-required",
    )


settings = Settings()


# ---------------------------------------------------------------------------
# Timezone constants
# P1 Time Policy:
#   TIMEZONE     → 業務邏輯用（台灣日期邊界計算）
#   TIMEZONE_UTC → DB 寫入用
# ---------------------------------------------------------------------------
TIMEZONE = ZoneInfo("Asia/Taipei")
TIMEZONE_UTC = timezone.utc


def get_utc_now() -> datetime:
    """獲取當前 UTC 時間（timezone-aware）

    P1 Policy: 所有 DB datetime 欄位寫入必須使用此函數。

    Returns:
        datetime: UTC aware datetime
    """
    return datetime.now(TIMEZONE_UTC)


def get_current_time() -> datetime:
    """獲取當前台灣時間（timezone-aware）

    WARNING: 禁止用於 DB 寫入。
    僅供業務邏輯（台灣日期邊界計算）與非 DB 顯示用途。
    DB datetime 寫入請改用 get_utc_now()。

    Returns:
        datetime: Asia/Taipei aware datetime
    """
    return datetime.now(TIMEZONE)
