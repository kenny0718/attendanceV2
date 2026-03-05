"""Pytest 共用測試 fixtures

提供測試資料庫連線管理，確保：
1. 使用獨立的測試資料庫（避免污染 production）
2. 每個測試前清空並重建 schema
3. 自動 override FastAPI 的 get_db dependency
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app


def get_test_database_url() -> str:
    """取得測試資料庫 URL
    
    優先順序：
    1. TEST_DATABASE_URL 環境變數
    2. DATABASE_URL 環境變數
    3. 預設測試資料庫
    
    安全檢查：強制要求資料庫名稱包含 'test'，避免誤傷正式庫
    """
    test_db_url = os.getenv(
        "TEST_DATABASE_URL",
        os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://postgres:Raxcxtjq260!@127.0.0.1:5432/attendance_test_db"
        )
    )
    
    # 安全檢查：必須是測試資料庫
    if "test" not in test_db_url.lower():
        raise ValueError(
            f"測試資料庫 URL 必須包含 'test' 關鍵字，避免誤傷正式庫。\n"
            f"當前 URL: {test_db_url}\n"
            f"請設定環境變數：TEST_DATABASE_URL=postgresql+psycopg2://user:pass@host:port/dbname_test"
        )
    
    return test_db_url


# 建立測試用 engine（模組層級，所有測試共用）
test_engine = create_engine(
    get_test_database_url(),
    pool_pre_ping=True,
    echo=False  # 測試時不輸出 SQL（加快速度）
)

# 測試用 SessionLocal
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


@pytest.fixture(scope="function")
def test_db():
    """測試資料庫 session fixture（每個測試函數獨立）
    
    每個測試前：
    - drop_all() 清空所有表
    - create_all() 重建 schema
    
    每個測試後：
    - 關閉 session
    - 清除 app.dependency_overrides
    """
    # 每個測試前：清空並重建所有表
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    # 建立測試 session
    db = TestingSessionLocal()
    
    # Override FastAPI 的 get_db dependency
    def override_get_db():
        try:
            yield db
        finally:
            # 每次請求後 flush，確保數據可見
            db.flush()
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        yield db
    finally:
        # 測試後清理
        db.close()
        # 清除 override（避免影響其他測試）
        app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_db_session():
    """測試資料庫 session fixture（別名，相容不同命名習慣）"""
    # 每個測試前：清空並重建所有表
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    # 建立測試 session
    db = TestingSessionLocal()
    
    # Override FastAPI 的 get_db dependency
    def override_get_db():
        try:
            yield db
        finally:
            db.flush()
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        yield db
    finally:
        db.close()
        app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def db():
    """測試資料庫 session fixture（別名，用於 audit 測試）
    
    直接返回 test_db_session 的實例，確保命名一致性。
    """
    # 每個測試前：清空並重建所有表
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    # 建立測試 session
    session = TestingSessionLocal()
    
    # Override FastAPI 的 get_db dependency
    def override_get_db():
        try:
            yield session
        finally:
            session.flush()
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        yield session
    finally:
        session.close()
        app.dependency_overrides.clear()
