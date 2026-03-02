"""Global test configuration

Phase 9 (WP-09-05): Provide tenant setup utilities for tests
"""

import pytest
from app.core.database import get_db
from app.modules.tenants.repo import TenantRepository


def ensure_test_tenants():
    """Utility function to ensure test tenants exist
    
    Call this from test fixtures that need tenants in PostgreSQL.
    For SQLite tests, create tenants in the test DB directly.
    """
    try:
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
    except Exception:
        # If PostgreSQL connection fails, skip (tests using SQLite will handle their own tenants)
        pass
