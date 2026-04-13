"""Test fixtures for tenants module.

使用 PostgreSQL Test DB，每個測試前重建 fresh schema，避免 schema drift。
並在每個測試 session 內補齊 roles，避免 Membership.role_id FK 失敗。
"""

import pytest
from fastapi.testclient import TestClient
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


TEST_DATABASE_URL = "postgresql+psycopg2://postgres:Raxcxtjq260!@127.0.0.1:5432/attendance_test_db"


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True, echo=False)
    yield engine
    engine.dispose()


def _reset_public_schema(engine) -> None:
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


def _prepare_fresh_schema(engine) -> None:
    _reset_public_schema(engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    _prepare_fresh_schema(test_engine)

    SessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    session = SessionLocal()

    roles_data = [
        ("employee", "Employee", "Regular employee"),
        ("company_admin", "Company Admin", "Full access within company"),
        ("customer_service", "Customer Service", "Can access multiple companies"),
        ("hr_manager", "HR Manager", "HR admin access"),
        ("super_admin", "Super Admin", "Platform super admin"),
    ]
    for role_id, name, description in roles_data:
        if session.query(Role).filter(Role.id == role_id).first() is None:
            session.add(Role(id=role_id, name=name, description=description))
    session.commit()

    yield session

    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
