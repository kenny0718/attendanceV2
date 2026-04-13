"""Audit tests configuration

Phase 9 (WP-09-05): Add tenant setup for audit tests
"""

from datetime import datetime
import uuid

import pytest
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.core.features import FeatureKeys
from app.modules.audit.models import AuditLog, AuditRetentionPolicy
from app.modules.tenants.models import Tenant
from app.modules.tenants.repo import TenantRepository


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class AuditLogSQLite(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True)
    company_id = Column(String(255), nullable=False, index=True)
    action = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    actor = Column(String(255), nullable=True)
    request_id = Column(String(255), nullable=True)
    ip = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    meta = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class AuditRetentionPolicySQLite(Base):
    __tablename__ = "audit_retention_policies"

    company_id = Column(String(255), primary_key=True)
    retention_days = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class CompanyEntitlementSQLite(Base):
    __tablename__ = "company_entitlements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(50), nullable=False, index=True)
    feature_key = Column(String(100), nullable=False, index=True)
    enabled = Column(Boolean, nullable=False, default=False)
    updated_by_user_id = Column(String(36), nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


TENANTS = [
    ("company-test", "Test Company"),
    ("company-001", "Company 001"),
    ("company-002", "Company 002"),
    ("company-A", "Company A"),
    ("company-B", "Company B"),
    ("test-company-retention", "Test Company Retention"),
    ("audit-iso-a", "Audit Iso A"),
    ("audit-iso-b", "Audit Iso B"),
]


@pytest.fixture
def test_db():
    """Create test database with all tables (SQLite for unit tests)"""
    Tenant.__table__.create(bind=engine, checkfirst=True)
    AuditLogSQLite.__table__.create(bind=engine, checkfirst=True)
    AuditRetentionPolicySQLite.__table__.create(bind=engine, checkfirst=True)
    CompanyEntitlementSQLite.__table__.create(bind=engine, checkfirst=True)

    db = TestingSessionLocal()

    tenant_repo = TenantRepository(db)
    for tenant_id, tenant_name in TENANTS:
        tenant_repo.create(tenant_id, tenant_name, is_active=True)

    for tenant_id, _ in TENANTS:
        db.add(
            CompanyEntitlementSQLite(
                company_id=tenant_id,
                feature_key=FeatureKeys.AUDIT_CORE,
                enabled=True,
            )
        )
    db.commit()

    try:
        yield db
    finally:
        db.close()
        CompanyEntitlementSQLite.__table__.drop(bind=engine, checkfirst=True)
        AuditRetentionPolicySQLite.__table__.drop(bind=engine, checkfirst=True)
        AuditLogSQLite.__table__.drop(bind=engine, checkfirst=True)
        Tenant.__table__.drop(bind=engine, checkfirst=True)


@pytest.fixture(scope="function", autouse=True)
def override_get_db_for_all_tests(test_db):
    """Auto-apply get_db override for all audit tests (uses SQLite)"""
    from app.main import app

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()


@pytest.fixture(scope="function", autouse=True)
def setup_test_tenant_for_api():
    """Setup test tenant in PostgreSQL for API tests using TestClient"""
    try:
        db = next(get_db())
        tenant_repo = TenantRepository(db)

        for tenant_id, tenant_name in TENANTS:
            if not tenant_repo.exists(tenant_id):
                tenant_repo.create(tenant_id, tenant_name, is_active=True)

        db.query(AuditRetentionPolicy).delete(synchronize_session=False)
        db.query(AuditLog).delete(synchronize_session=False)
        db.commit()

    except Exception:
        pass

    yield

    try:
        db = next(get_db())
        db.query(AuditRetentionPolicy).delete(synchronize_session=False)
        db.query(AuditLog).delete(synchronize_session=False)
        db.commit()
    except Exception:
        pass
