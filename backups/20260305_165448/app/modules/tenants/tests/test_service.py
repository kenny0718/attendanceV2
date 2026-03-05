"""Tenants Service Integration Tests"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.modules.tenants.models import Tenant
from app.modules.tenants.service import TenantService


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
    # Only create tenants table
    Tenant.__table__.create(bind=engine, checkfirst=True)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Tenant.__table__.drop(bind=engine, checkfirst=True)


class TestTenantService:
    """Tenant Service integration tests"""
    
    def test_create_tenant(self, test_db):
        """Test: Create tenant"""
        service = TenantService(test_db)
        
        tenant = service.create_tenant(
            tenant_id="company-A",
            name="Company A",
            timezone="Asia/Taipei"
        )
        
        assert tenant.id == "company-A"
        assert tenant.name == "Company A"
        assert tenant.timezone == "Asia/Taipei"
        assert tenant.is_active is True
    
    def test_create_duplicate_tenant(self, test_db):
        """Test: Create duplicate tenant raises ValueError"""
        service = TenantService(test_db)
        
        # Create first tenant
        service.create_tenant("company-A", "Company A")
        
        # Try to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            service.create_tenant("company-A", "Company A Duplicate")
    
    def test_get_tenant(self, test_db):
        """Test: Get tenant"""
        service = TenantService(test_db)
        
        # Create tenant
        service.create_tenant("company-A", "Company A")
        
        # Get tenant
        tenant = service.get_tenant("company-A")
        
        assert tenant is not None
        assert tenant.id == "company-A"
    
    def test_get_non_existent_tenant(self, test_db):
        """Test: Get non-existent tenant returns None"""
        service = TenantService(test_db)
        
        tenant = service.get_tenant("non-existent")
        
        assert tenant is None
    
    def test_list_tenants(self, test_db):
        """Test: List tenants"""
        service = TenantService(test_db)
        
        # Create multiple tenants
        service.create_tenant("company-A", "Company A")
        service.create_tenant("company-B", "Company B")
        service.create_tenant("company-C", "Company C")
        
        # List all
        tenants = service.list_tenants()
        
        assert len(tenants) == 3
    
    def test_list_tenants_pagination(self, test_db):
        """Test: List tenants with pagination"""
        service = TenantService(test_db)
        
        # Create 5 tenants
        for i in range(5):
            service.create_tenant(f"company-{i}", f"Company {i}")
        
        # Get first page
        page1 = service.list_tenants(limit=2, offset=0)
        assert len(page1) == 2
        
        # Get second page
        page2 = service.list_tenants(limit=2, offset=2)
        assert len(page2) == 2
        
        # Ensure different results
        assert page1[0].id != page2[0].id
    
    def test_update_tenant(self, test_db):
        """Test: Update tenant"""
        service = TenantService(test_db)
        
        # Create tenant
        service.create_tenant("company-A", "Company A")
        
        # Update
        updated = service.update_tenant("company-A", name="Company A Updated")
        
        assert updated is not None
        assert updated.name == "Company A Updated"
    
    def test_update_non_existent_tenant(self, test_db):
        """Test: Update non-existent tenant returns None"""
        service = TenantService(test_db)
        
        updated = service.update_tenant("non-existent", name="Test")
        
        assert updated is None
    
    def test_deactivate_tenant(self, test_db):
        """Test: Deactivate tenant"""
        service = TenantService(test_db)
        
        # Create active tenant
        service.create_tenant("company-A", "Company A", is_active=True)
        
        # Deactivate
        deactivated = service.deactivate_tenant("company-A")
        
        assert deactivated is not None
        assert deactivated.is_active is False
    
    def test_activate_tenant(self, test_db):
        """Test: Activate tenant"""
        service = TenantService(test_db)
        
        # Create inactive tenant
        service.create_tenant("company-A", "Company A", is_active=False)
        
        # Activate
        activated = service.activate_tenant("company-A")
        
        assert activated is not None
        assert activated.is_active is True
    
    def test_tenant_exists(self, test_db):
        """Test: Check tenant exists"""
        service = TenantService(test_db)
        
        # Create tenant
        service.create_tenant("company-A", "Company A")
        
        # Check exists
        assert service.tenant_exists("company-A") is True
        assert service.tenant_exists("non-existent") is False
    
    def test_tenant_is_active(self, test_db):
        """Test: Check tenant is active"""
        service = TenantService(test_db)
        
        # Create active tenant
        service.create_tenant("company-A", "Company A", is_active=True)
        
        # Create inactive tenant
        service.create_tenant("company-B", "Company B", is_active=False)
        
        # Check active status
        assert service.tenant_is_active("company-A") is True
        assert service.tenant_is_active("company-B") is False
        assert service.tenant_is_active("non-existent") is False
    
    def test_full_lifecycle(self, test_db):
        """Test: Full tenant lifecycle (create -> update -> deactivate -> activate)"""
        service = TenantService(test_db)
        
        # Create
        tenant = service.create_tenant("company-A", "Company A")
        assert tenant.is_active is True
        
        # Update
        updated = service.update_tenant("company-A", name="Company A Updated", timezone="America/New_York")
        assert updated.name == "Company A Updated"
        assert updated.timezone == "America/New_York"
        
        # Deactivate
        deactivated = service.deactivate_tenant("company-A")
        assert deactivated.is_active is False
        assert service.tenant_is_active("company-A") is False
        
        # Activate
        activated = service.activate_tenant("company-A")
        assert activated.is_active is True
        assert service.tenant_is_active("company-A") is True
