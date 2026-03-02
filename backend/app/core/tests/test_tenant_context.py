"""Tests for tenant context validation

Phase 9 (WP-09-05): Test tenant existence and active status validation
"""

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.tenant_context import get_current_company_id
from app.modules.tenants.models import Tenant


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
    Tenant.__table__.create(bind=engine, checkfirst=True)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Tenant.__table__.drop(bind=engine, checkfirst=True)


class TestTenantContextValidation:
    """Test tenant context validation"""
    
    def test_valid_active_tenant(self, test_db):
        """Test: Valid active tenant succeeds"""
        # Setup: Create active tenant
        tenant = Tenant(id="company-A", name="Company A", is_active=True)
        test_db.add(tenant)
        test_db.commit()
        
        # Test: Get company_id with valid tenant
        company_id = get_current_company_id(x_company_id="company-A", db=test_db)
        
        assert company_id == "company-A"
    
    def test_non_existent_tenant_returns_404(self, test_db):
        """Test: Non-existent tenant returns 404"""
        # Test: Try to get non-existent tenant
        with pytest.raises(HTTPException) as exc_info:
            get_current_company_id(x_company_id="non-existent", db=test_db)
        
        assert exc_info.value.status_code == 404
        assert "does not exist" in str(exc_info.value.detail)
    
    def test_inactive_tenant_returns_403(self, test_db):
        """Test: Inactive tenant returns 403"""
        # Setup: Create inactive tenant
        tenant = Tenant(id="company-B", name="Company B", is_active=False)
        test_db.add(tenant)
        test_db.commit()
        
        # Test: Try to get inactive tenant
        with pytest.raises(HTTPException) as exc_info:
            get_current_company_id(x_company_id="company-B", db=test_db)
        
        assert exc_info.value.status_code == 403
        assert "not active" in str(exc_info.value.detail)
    
    def test_missing_header_returns_400(self, test_db):
        """Test: Missing X-Company-ID header returns 400"""
        # Test: Try with empty header
        with pytest.raises(HTTPException) as exc_info:
            get_current_company_id(x_company_id="", db=test_db)
        
        assert exc_info.value.status_code == 400
        assert "Missing" in exc_info.value.detail
    
    def test_whitespace_header_returns_400(self, test_db):
        """Test: Whitespace-only header returns 400"""
        # Test: Try with whitespace header
        with pytest.raises(HTTPException) as exc_info:
            get_current_company_id(x_company_id="   ", db=test_db)
        
        assert exc_info.value.status_code == 400
        assert "Missing" in exc_info.value.detail
    
    def test_tenant_deactivation_blocks_access(self, test_db):
        """Test: Deactivating tenant blocks access"""
        # Setup: Create active tenant
        tenant = Tenant(id="company-C", name="Company C", is_active=True)
        test_db.add(tenant)
        test_db.commit()
        
        # Test: Access succeeds when active
        company_id = get_current_company_id(x_company_id="company-C", db=test_db)
        assert company_id == "company-C"
        
        # Setup: Deactivate tenant
        tenant.is_active = False
        test_db.commit()
        
        # Test: Access fails when inactive
        with pytest.raises(HTTPException) as exc_info:
            get_current_company_id(x_company_id="company-C", db=test_db)
        
        assert exc_info.value.status_code == 403
