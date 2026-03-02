"""Tenants Repository Unit Tests"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
    # Only create tenants table (avoid JSONB issues with notifications table in SQLite)
    Tenant.__table__.create(bind=engine, checkfirst=True)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Tenant.__table__.drop(bind=engine, checkfirst=True)


class TestTenantRepository:
    """Tenant Repository unit tests"""
    
    def test_create_tenant(self, test_db):
        """Test: Create tenant"""
        repo = TenantRepository(test_db)
        
        tenant = repo.create(
            tenant_id="company-A",
            name="Company A",
            timezone="Asia/Taipei"
        )
        
        assert tenant.id == "company-A"
        assert tenant.name == "Company A"
        assert tenant.timezone == "Asia/Taipei"
        assert tenant.is_active is True
        assert tenant.created_at is not None
    
    def test_get_by_id_exists(self, test_db):
        """Test: Get tenant by ID (exists)"""
        repo = TenantRepository(test_db)
        
        # Create tenant
        repo.create("company-A", "Company A")
        
        # Get tenant
        tenant = repo.get_by_id("company-A")
        
        assert tenant is not None
        assert tenant.id == "company-A"
        assert tenant.name == "Company A"
    
    def test_get_by_id_not_exists(self, test_db):
        """Test: Get tenant by ID (not exists)"""
        repo = TenantRepository(test_db)
        
        tenant = repo.get_by_id("non-existent")
        
        assert tenant is None
    
    def test_list_all(self, test_db):
        """Test: List all tenants"""
        repo = TenantRepository(test_db)
        
        # Create multiple tenants
        repo.create("company-A", "Company A")
        repo.create("company-B", "Company B")
        repo.create("company-C", "Company C")
        
        # List all
        tenants = repo.list_all()
        
        assert len(tenants) == 3
        # Should be ordered by created_at desc (newest first)
        assert tenants[0].id == "company-C"
        assert tenants[1].id == "company-B"
        assert tenants[2].id == "company-A"
    
    def test_list_all_pagination(self, test_db):
        """Test: List all tenants with pagination"""
        repo = TenantRepository(test_db)
        
        # Create 5 tenants
        for i in range(5):
            repo.create(f"company-{i}", f"Company {i}")
        
        # Get first 2
        page1 = repo.list_all(limit=2, offset=0)
        assert len(page1) == 2
        
        # Get next 2
        page2 = repo.list_all(limit=2, offset=2)
        assert len(page2) == 2
        
        # Ensure different results
        assert page1[0].id != page2[0].id
    
    def test_update_tenant(self, test_db):
        """Test: Update tenant"""
        repo = TenantRepository(test_db)
        
        # Create tenant
        repo.create("company-A", "Company A")
        
        # Update
        updated = repo.update("company-A", name="Company A Updated", timezone="America/New_York")
        
        assert updated is not None
        assert updated.name == "Company A Updated"
        assert updated.timezone == "America/New_York"
    
    def test_update_non_existent(self, test_db):
        """Test: Update non-existent tenant"""
        repo = TenantRepository(test_db)
        
        updated = repo.update("non-existent", name="Test")
        
        assert updated is None
    
    def test_exists_true(self, test_db):
        """Test: Tenant exists"""
        repo = TenantRepository(test_db)
        
        repo.create("company-A", "Company A")
        
        assert repo.exists("company-A") is True
    
    def test_exists_false(self, test_db):
        """Test: Tenant does not exist"""
        repo = TenantRepository(test_db)
        
        assert repo.exists("non-existent") is False
    
    def test_is_active_true(self, test_db):
        """Test: Tenant is active"""
        repo = TenantRepository(test_db)
        
        repo.create("company-A", "Company A", is_active=True)
        
        assert repo.is_active("company-A") is True
    
    def test_is_active_false(self, test_db):
        """Test: Tenant is inactive"""
        repo = TenantRepository(test_db)
        
        repo.create("company-A", "Company A", is_active=False)
        
        assert repo.is_active("company-A") is False
    
    def test_is_active_non_existent(self, test_db):
        """Test: Non-existent tenant returns False"""
        repo = TenantRepository(test_db)
        
        assert repo.is_active("non-existent") is False
    
    def test_deactivate_tenant(self, test_db):
        """Test: Deactivate tenant"""
        repo = TenantRepository(test_db)
        
        # Create active tenant
        repo.create("company-A", "Company A", is_active=True)
        
        # Deactivate
        repo.update("company-A", is_active=False)
        
        # Verify
        assert repo.is_active("company-A") is False
        tenant = repo.get_by_id("company-A")
        assert tenant.is_active is False
