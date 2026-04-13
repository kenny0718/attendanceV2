"""Pytest 共用測試 fixtures

提供測試資料庫連線管理，確保：
1. 使用獨立的測試資料庫（避免污染 production）
2. 每個測試前清空並重建 schema
3. 自動 override FastAPI 的 get_db dependency
"""

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app

# Ensure all models are registered in Base.metadata for create_all()/drop_all()
from app.modules.attendance.models import (  # noqa: F401
    AllowedLocation,
    AttendanceOutCheckpoint,
    AttendancePolicy,
    AttendancePunch,
    AttendanceRecord,
    AttendanceSession,
)
from app.modules.audit.models import AuditLog, AuditRetentionPolicy  # noqa: F401
from app.modules.auth.models import (  # noqa: F401
    Membership,
    Permission,
    Role,
    RolePermission,
    User,
)
from app.modules.customer_service.models import SupportCompanyAssignment  # noqa: F401
from app.modules.leave.models import (  # noqa: F401
    LeaveApprovalLog,
    LeaveApprovalPolicy,
    LeaveRequest,
    LeaveType,
)
from app.modules.notifications.models import Notification  # noqa: F401
from app.modules.schedule.models import ShiftAssignment, ShiftSegment, ShiftTemplate  # noqa: F401
from app.modules.tenants.models import CompanyEntitlement, Tenant  # noqa: F401


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
            "postgresql+psycopg2://postgres:Raxcxtjq260!@127.0.0.1:5432/attendance_test_db",
        ),
    )

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
    echo=False,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def _reset_public_schema() -> None:
    """徹底重建 public schema，避免 PostgreSQL DDL 殘留型別物件。"""
    with test_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


def _prepare_fresh_schema() -> None:
    _reset_public_schema()
    Base.metadata.create_all(bind=test_engine)


@pytest.fixture(scope="function")
def test_db():
    """測試資料庫 session fixture（每個測試函數獨立）"""
    _prepare_fresh_schema()

    db = TestingSessionLocal()

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
def test_db_session():
    """測試資料庫 session fixture（別名，相容不同命名習慣）"""
    _prepare_fresh_schema()

    db = TestingSessionLocal()

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
    """測試資料庫 session fixture（別名，用於舊測試）"""
    _prepare_fresh_schema()

    session = TestingSessionLocal()

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
