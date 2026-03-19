"""
Schedule module tests configuration

WP-S1-05: Integration Testing + Entitlement Setup

Provides:
- test_db: PostgreSQL session with all tables created
- schedule_db: ensures test tenants + test user exist
- schedule_entitlement: ensures schedule.core is enabled
- actor_a / actor_b: pre-built test actors
"""

import os
import pytest
from uuid import uuid4, UUID
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app

# Import all models so Base.metadata has them all
from app.modules.attendance.models import (  # noqa: F401
    AttendanceOutCheckpoint, AttendanceSession, AttendancePunch,
    AttendancePolicy, AllowedLocation
)
from app.modules.schedule.models import ShiftTemplate, ShiftAssignment  # noqa: F401
from app.modules.auth.models import User  # noqa: F401
from app.modules.tenants.models import Tenant, CompanyEntitlement
from app.core.features import FeatureKeys
from app.tests.utils.auth import create_test_actor

# Test company constants
SCHEDULE_COMPANY_A = "schedule-test-company-a"
SCHEDULE_COMPANY_B = "schedule-test-company-b"

# Fixed test user UUID for reproducibility
# This UUID must exist in the users table before creating shift_assignments
TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000099")


def get_test_db_url() -> str:
    return os.getenv(
        "TEST_DATABASE_URL",
        os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://postgres:Raxcxtjq260!@127.0.0.1:5432/attendance_test_db"
        )
    )


# Module-level engine (shared across tests in this module)
_test_engine = create_engine(get_test_db_url(), pool_pre_ping=True, echo=False)
_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


@pytest.fixture(scope="function")
def test_db():
    """PostgreSQL test DB session with all schedule tables created."""
    Base.metadata.drop_all(bind=_test_engine, checkfirst=True)
    Base.metadata.create_all(bind=_test_engine, checkfirst=True)

    db = _TestingSessionLocal()

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


@pytest.fixture
def schedule_db(test_db):
    """Ensure test companies and a test user exist (FK constraints)."""
    db = test_db

    # Create test tenants
    for cid, cname in [
        (SCHEDULE_COMPANY_A, "Schedule Test Company A"),
        (SCHEDULE_COMPANY_B, "Schedule Test Company B"),
    ]:
        if not db.query(Tenant).filter(Tenant.id == cid).first():
            db.add(Tenant(id=cid, name=cname, is_active=True))

    # Create test user (required by shift_assignments.user_id FK -> users.id)
    if not db.query(User).filter(User.id == TEST_USER_ID).first():
        db.add(User(
            id=TEST_USER_ID,
            display_name="Schedule Test User",
            password_hash="dummy_hash_not_used",
            is_active=True,
        ))

    db.commit()
    return db


@pytest.fixture
def schedule_entitlement(schedule_db):
    """Ensure schedule.core is enabled for SCHEDULE_COMPANY_A."""
    db = schedule_db
    existing = db.query(CompanyEntitlement).filter(
        CompanyEntitlement.company_id == SCHEDULE_COMPANY_A,
        CompanyEntitlement.feature_key == FeatureKeys.SCHEDULE_CORE,
    ).first()
    if not existing:
        db.add(CompanyEntitlement(
            id=uuid4(),
            company_id=SCHEDULE_COMPANY_A,
            feature_key=FeatureKeys.SCHEDULE_CORE,
            enabled=True,
        ))
        db.commit()
    return db


@pytest.fixture
def actor_a(schedule_entitlement):
    """Test Actor for SCHEDULE_COMPANY_A (schedule.core enabled)."""
    return create_test_actor(
        company_id=SCHEDULE_COMPANY_A,
        user_id=TEST_USER_ID,
        role_id="admin",
    )


@pytest.fixture
def actor_b(schedule_db):
    """Test Actor for SCHEDULE_COMPANY_B (no schedule.core entitlement)."""
    return create_test_actor(
        company_id=SCHEDULE_COMPANY_B,
        user_id=TEST_USER_ID,
        role_id="admin",
    )
