"""應用程式設定"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """應用程式設定"""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    app_name: str = "Attendance V2 API"
    debug: bool = False

    # 資料庫設定：優先吃環境變數 DATABASE_URL，沒有才用預設（不含密碼）
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://attendance_user@127.0.0.1:5432/attendance_db",
    )


settings = Settings()
