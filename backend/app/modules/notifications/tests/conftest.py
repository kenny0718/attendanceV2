"""Notifications tests configuration

Phase 9 (WP-09-05): Add tenant setup for notifications tests
"""

import pytest
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.database import get_db
from app.modules.tenants.repo import TenantRepository
from app.modules.tenants.models import Tenant
from app.modules.notifications.models import Notification
from datetime import datetime


# Test database (in-memory SQLite for unit tests)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a SQLite-compatible Notification model (TEXT instead of JSONB)
Base = declarative_base()

class NotificationSQLite(Base):
    """SQLite-compatible Notification model (for testing only)"""
    __tablename__ = "notifications"
    
    id = Column(String(32), primary_key=True)
    company_id = Column(String(255), nullable=False, index=True)
    event_type = Column(String(255), nullable=False)
    event_payload = Column(Text, nullable=False)  # TEXT instead of JSONB for SQLite
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


@pytest.fixture
def test_db():
    """Create test database with tenants and notifications tables (SQLite for unit tests)"""
    # Create tables
    Tenant.__table__.create(bind=engine, checkfirst=True)
    NotificationSQLite.__table__.create(bind=engine, checkfirst=True)
    
    db = TestingSessionLocal()
    
    # Create test tenants (all tenants used in tests)
    tenant_repo = TenantRepository(db)
    tenant_repo.create("company-test", "Test Company", is_active=True)
    tenant_repo.create("company-001", "Company 001", is_active=True)
    tenant_repo.create("company-002", "Company 002", is_active=True)
    tenant_repo.create("company-A", "Company A", is_active=True)
    tenant_repo.create("company-B", "Company B", is_active=True)
    tenant_repo.create("company-from-payload", "Company From Payload", is_active=True)
    
    try:
        yield db
    finally:
        db.close()
        NotificationSQLite.__table__.drop(bind=engine, checkfirst=True)
        Tenant.__table__.drop(bind=engine, checkfirst=True)


@pytest.fixture(scope="function", autouse=True)
def setup_test_tenant_for_api():
    """Setup test tenant in PostgreSQL for API tests using TestClient
    
    Also cleans up notifications table before each test to ensure isolation.
    """
    try:
        db = next(get_db())
        tenant_repo = TenantRepository(db)
        
        # Create tenants if not exist
        if not tenant_repo.exists("company-test"):
            tenant_repo.create("company-test", "Test Company", is_active=True)
        if not tenant_repo.exists("company-001"):
            tenant_repo.create("company-001", "Company 001", is_active=True)
        if not tenant_repo.exists("company-002"):
            tenant_repo.create("company-002", "Company 002", is_active=True)
        if not tenant_repo.exists("company-A"):
            tenant_repo.create("company-A", "Company A", is_active=True)
        if not tenant_repo.exists("company-B"):
            tenant_repo.create("company-B", "Company B", is_active=True)
        if not tenant_repo.exists("company-from-payload"):
            tenant_repo.create("company-from-payload", "Company From Payload", is_active=True)
        
        # Clean up notifications table for test isolation
        db.query(Notification).delete()
        db.commit()
        
    except Exception as e:
        # If PostgreSQL connection fails, skip (SQLite tests will use test_db fixture)
        pass
    
    yield
    
    # Cleanup after test
    try:
        db = next(get_db())
        db.query(Notification).delete()
        db.commit()
    except Exception:
        pass
