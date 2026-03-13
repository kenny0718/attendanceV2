"""Shared pytest fixtures for attendance tests

Provides:
- client: FastAPI TestClient
- test_session: Database session (alias for db fixture from root conftest)
- test_user: Test User object in the database
"""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.models import User
from app.modules.tenants.models import Tenant


@pytest.fixture
def client():
    """Shared TestClient fixture for attendance tests"""
    return TestClient(app)


@pytest.fixture
def test_session(db):
    """Alias for root conftest db fixture
    
    Provides SQLAlchemy session with test database.
    Automatically overrides app.dependency_overrides[get_db].
    """
    return db


@pytest.fixture
def test_user(test_session):
    """Create test user and tenant in test database
    
    Ensures test tenant exists, then creates a test user.
    User model has no company_id (global identity).
    """
    # Ensure test tenant exists
    tenant = test_session.query(Tenant).filter(
        Tenant.id == "company-test"
    ).first()
    
    if not tenant:
        tenant = Tenant(
            id="company-test",
            name="Test Company",
            is_active=True
        )
        test_session.add(tenant)
        test_session.commit()
    
    # Create test user (User model: id, display_name, password_hash, is_active)
    user = User(
        id=uuid4(),
        display_name="Test User",
        password_hash="dummy_hash",
        is_active=True
    )
    # Attach company_id as plain attribute for use in tests
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    
    # Attach company_id for convenience in tests
    user.company_id = "company-test"
    
    return user
