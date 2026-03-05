"""Audit tests configuration

Phase 9 (WP-09-05): Add tenant setup for audit tests
"""

import pytest
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.database import get_db
from app.modules.tenants.repo import TenantRepository
from app.modules.tenants.models import Tenant
from app.modules.audit.models import AuditLog, AuditRetentionPolicy
from datetime import datetime


# Test database (in-memory SQLite for unit tests)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create SQLite-compatible models
Base = declarative_base()

class AuditLogSQLite(Base):
    """SQLite-compatible AuditLog model"""
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
    """SQLite-compatible AuditRetentionPolicy model"""
    __tablename__ = "audit_retention_policies"
    
    company_id = Column(String(255), primary_key=True)
    retention_days = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


@pytest.fixture
def test_db():
    """Create test database with all tables (SQLite for unit tests)"""
    # Create tables
    Tenant.__table__.create(bind=engine, checkfirst=True)
    AuditLogSQLite.__table__.create(bind=engine, checkfirst=True)
    AuditRetentionPolicySQLite.__table__.create(bind=engine, checkfirst=True)
    
    db = TestingSessionLocal()
    
    # Create test tenants
    tenant_repo = TenantRepository(db)
    tenant_repo.create("company-test", "Test Company", is_active=True)
    tenant_repo.create("company-001", "Company 001", is_active=True)
    tenant_repo.create("company-002", "Company 002", is_active=True)
    tenant_repo.create("company-A", "Company A", is_active=True)
    tenant_repo.create("company-B", "Company B", is_active=True)
    tenant_repo.create("test-company-retention", "Test Company Retention", is_active=True)
    
    try:
        yield db
    finally:
        db.close()
        AuditRetentionPolicySQLite.__table__.drop(bind=engine, checkfirst=True)
        AuditLogSQLite.__table__.drop(bind=engine, checkfirst=True)
        Tenant.__table__.drop(bind=engine, checkfirst=True)




@pytest.fixture(scope="function", autouse=True)
def override_get_db_for_all_tests(test_db):
    """Auto-apply get_db override for all audit tests (uses SQLite)"""
    from app.main import app
    
    # Override get_db to use the test_db session (with tables and tenants already created)
    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # Don't close here, let test_db fixture manage it
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield
    
    # Cleanup
    app.dependency_overrides.clear()

@pytest.fixture(scope="function", autouse=True)
def setup_test_tenant_for_api():
    """Setup test tenant in PostgreSQL for API tests using TestClient"""
    try:
        db = next(get_db())
        tenant_repo = TenantRepository(db)
        
        # Create tenants if not exist
        tenants = [
            ("company-test", "Test Company"),
            ("company-001", "Company 001"),
            ("company-002", "Company 002"),
            ("company-A", "Company A"),
            ("company-B", "Company B"),
            ("test-company-retention", "Test Company Retention"),
        ]
        
        for tenant_id, tenant_name in tenants:
            if not tenant_repo.exists(tenant_id):
                tenant_repo.create(tenant_id, tenant_name, is_active=True)
        
        # Clean up tables for test isolation
        db.query(AuditRetentionPolicy).delete(synchronize_session=False)
        db.query(AuditRetentionPolicy).delete(synchronize_session=False)
        db.query(AuditLog).delete(synchronize_session=False)
        db.commit()
        
    except Exception:
        # If PostgreSQL connection fails, skip
        pass
    
    yield
    
    # Cleanup after test
    try:
        db = next(get_db())
        db.query(AuditRetentionPolicy).delete(synchronize_session=False)
        db.query(AuditRetentionPolicy).delete(synchronize_session=False)
        db.query(AuditLog).delete(synchronize_session=False)
        db.commit()
    except Exception:
        pass
