"""Test tenant validation in attendance creation

Phase 9: WP-09-04 - Integrate tenant_exists() into attendance validation
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.core.database import Base
from app.modules.attendance.models import AttendanceRecord
from app.modules.attendance.repo import AttendanceRepository
from app.modules.tenants.models import Tenant
from app.modules.tenants.repo import TenantRepository


# Test database (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def test_db():
    """Create test database"""
    # Create both tables
    Tenant.__table__.create(bind=engine, checkfirst=True)
    AttendanceRecord.__table__.create(bind=engine, checkfirst=True)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        AttendanceRecord.__table__.drop(bind=engine, checkfirst=True)
        Tenant.__table__.drop(bind=engine, checkfirst=True)


class TestAttendanceTenantValidation:
    """Test tenant validation in attendance operations"""
    
    def test_create_attendance_with_valid_tenant(self, test_db):
        """Test: Create attendance with valid tenant succeeds"""
        # Setup: Create tenant
        tenant_repo = TenantRepository(test_db)
        tenant_repo.create("company-A", "Company A")
        
        # Test: Create attendance record
        attendance_repo = AttendanceRepository(test_db)
        record = attendance_repo.create_attendance_record(
            company_id="company-A",
            employee_id="emp-001"
        )
        
        assert record is not None
        assert record.company_id == "company-A"
        assert record.employee_id == "emp-001"
    
    def test_create_attendance_with_invalid_tenant(self, test_db):
        """Test: Create attendance with invalid tenant raises 404"""
        # Test: Try to create attendance for non-existent tenant
        attendance_repo = AttendanceRepository(test_db)
        
        with pytest.raises(HTTPException) as exc_info:
            attendance_repo.create_attendance_record(
                company_id="non-existent-tenant",
                employee_id="emp-001"
            )
        
        assert exc_info.value.status_code == 404
        assert "does not exist" in exc_info.value.detail["error"]
    
    def test_approve_attendance_with_tenant_isolation(self, test_db):
        """Test: Approve attendance respects tenant isolation"""
        # Setup: Create two tenants
        tenant_repo = TenantRepository(test_db)
        tenant_repo.create("company-A", "Company A")
        tenant_repo.create("company-B", "Company B")
        
        # Setup: Create attendance for company-A
        attendance_repo = AttendanceRepository(test_db)
        record = attendance_repo.create_attendance_record(
            company_id="company-A",
            employee_id="emp-001"
        )
        
        # Test: Try to approve with wrong company_id (company-B)
        result = attendance_repo.approve_attendance_record(
            company_id="company-B",
            record_id=record.id,
            approved_by="approver-B"
        )
        
        # Should return None (tenant isolation)
        assert result is None
        
        # Test: Approve with correct company_id (company-A)
        result = attendance_repo.approve_attendance_record(
            company_id="company-A",
            record_id=record.id,
            approved_by="approver-A"
        )
        
        assert result is not None
        assert result.approved_by == "approver-A"
        assert result.approved_at is not None
    
    def test_get_attendance_records_with_tenant_isolation(self, test_db):
        """Test: Get attendance records respects tenant isolation"""
        # Setup: Create two tenants
        tenant_repo = TenantRepository(test_db)
        tenant_repo.create("company-A", "Company A")
        tenant_repo.create("company-B", "Company B")
        
        # Setup: Create attendance for both companies
        attendance_repo = AttendanceRepository(test_db)
        attendance_repo.create_attendance_record("company-A", "emp-A1")
        attendance_repo.create_attendance_record("company-A", "emp-A2")
        attendance_repo.create_attendance_record("company-B", "emp-B1")
        
        # Test: Query company-A records
        records_a = attendance_repo.get_attendance_records("company-A")
        assert len(records_a) == 2
        assert all(r.company_id == "company-A" for r in records_a)
        
        # Test: Query company-B records
        records_b = attendance_repo.get_attendance_records("company-B")
        assert len(records_b) == 1
        assert all(r.company_id == "company-B" for r in records_b)
