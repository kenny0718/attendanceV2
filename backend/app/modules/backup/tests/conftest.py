"""Backup tests configuration

Phase 9 (WP-09-05): Add tenant setup for backup tests
"""

import pytest
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.database import get_db
from app.modules.tenants.repo import TenantRepository
from app.modules.tenants.models import Tenant
from app.modules.notifications.models import Notification
from app.modules.attendance.models import AttendanceRecord
from datetime import datetime


# Test database (in-memory SQLite for unit tests)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create SQLite-compatible models
Base = declarative_base()

class NotificationSQLite(Base):
    """SQLite-compatible Notification model"""
    __tablename__ = "notifications"
    
    id = Column(String(36), primary_key=True)
    company_id = Column(String(255), nullable=False, index=True)
    event_type = Column(String(255), nullable=False)
    event_payload = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class AttendanceRecordSQLite(Base):
    """SQLite-compatible AttendanceRecord model"""
    __tablename__ = "attendance_records"
    
    id = Column(String(36), primary_key=True)
    company_id = Column(String(255), nullable=False, index=True)
    employee_id = Column(String(255), nullable=False)
    check_in_time = Column(DateTime, nullable=False)
    check_out_time = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)


@pytest.fixture
def test_db():
    """Create test database with all tables (SQLite for unit tests)"""
    # Create tables
    Tenant.__table__.create(bind=engine, checkfirst=True)
    NotificationSQLite.__table__.create(bind=engine, checkfirst=True)
    AttendanceRecordSQLite.__table__.create(bind=engine, checkfirst=True)
    
    db = TestingSessionLocal()
    
    # Create test tenants
    tenant_repo = TenantRepository(db)
    tenant_repo.create("company-test", "Test Company", is_active=True)
    tenant_repo.create("company-001", "Company 001", is_active=True)
    tenant_repo.create("company-002", "Company 002", is_active=True)
    tenant_repo.create("company-A", "Company A", is_active=True)
    tenant_repo.create("company-B", "Company B", is_active=True)
    tenant_repo.create("company-empty", "Empty Company", is_active=True)
    tenant_repo.create("company-target", "Target Company", is_active=True)
    tenant_repo.create("company-source", "Source Company", is_active=True)
    
    try:
        yield db
    finally:
        db.close()
        AttendanceRecordSQLite.__table__.drop(bind=engine, checkfirst=True)
        NotificationSQLite.__table__.drop(bind=engine, checkfirst=True)
        Tenant.__table__.drop(bind=engine, checkfirst=True)


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
            ("company-empty", "Empty Company"),
            ("company-target", "Target Company"),
            ("company-source", "Source Company"),
        ]
        
        for tenant_id, tenant_name in tenants:
            if not tenant_repo.exists(tenant_id):
                tenant_repo.create(tenant_id, tenant_name, is_active=True)
        
        # Clean up tables for test isolation
        db.query(Notification).delete(synchronize_session=False)
        db.query(AttendanceRecord).delete(synchronize_session=False)
        db.commit()
        
    except Exception:
        # If PostgreSQL connection fails, skip
        pass
    
    yield
    
    # Cleanup after test
    try:
        db = next(get_db())
        db.query(Notification).delete(synchronize_session=False)
        db.query(AttendanceRecord).delete(synchronize_session=False)
        db.commit()
    except Exception:
        pass
