"""Test fixtures for tenants module

WP-11-04A: Tenants module test fixtures
使用 PostgreSQL Test DB + Transaction Rollback 策略
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app


# 測試資料庫 URL（使用獨立的測試 DB）
TEST_DATABASE_URL = "postgresql+psycopg2://postgres:Raxcxtjq260!@127.0.0.1:5432/attendance_test_db"


@pytest.fixture(scope="session")
def test_engine():
    """建立測試資料庫 engine（session scope，整個測試 session 共用）"""
    engine = create_engine(TEST_DATABASE_URL)
    
    # 確保測試 DB 有最新的 schema（執行 migrations）
    # 注意：這裡假設測試 DB 已經執行過 alembic upgrade head
    # 如果需要，可以在這裡自動執行 migration
    
    yield engine
    
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """提供測試用的資料庫 session（使用 transaction rollback 確保隔離）"""
    # 建立連線
    connection = test_engine.connect()
    
    # 開始 transaction
    transaction = connection.begin()
    
    # 建立 session（綁定到這個 transaction）
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()
    
    yield session
    
    # 測試結束後 rollback（確保資料不會真的寫入）
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """提供 TestClient，並 override get_db dependency"""
    
    def override_get_db():
        """Override get_db 使用測試 session"""
        try:
            yield db_session
        finally:
            pass
    
    # Override FastAPI dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # 建立 TestClient
    with TestClient(app) as test_client:
        yield test_client
    
    # 清理 overrides
    app.dependency_overrides.clear()
