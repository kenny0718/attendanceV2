"""Global test configuration

Phase 9 (WP-09-05): Auto-create test tenants for all tests
"""

import pytest
from app.core.database import get_db
from app.modules.tenants.repo import TenantRepository


@pytest.fixture(scope="session", autouse=True)
def setup_test_tenants():
    """Setup common test tenants for all tests"""
    db = next(get_db())
    tenant_repo = TenantRepository(db)
    
    # Create common test tenants if they don't exist
    test_tenants = [
        ("company-test", "Test Company"),
        ("company-a", "Company A"),
        ("company-b", "Company B"),
        ("company-001", "Company 001"),
        ("company-002", "Company 002"),
    ]
    
    for tenant_id, name in test_tenants:
        if not tenant_repo.exists(tenant_id):
            tenant_repo.create(tenant_id, name, is_active=True)
    
    yield
    
    # Cleanup is optional (tenants can persist)
