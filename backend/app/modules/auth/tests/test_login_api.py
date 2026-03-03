"""Login API Tests (TDD - Red Phase)

WP-10-04A: Test-first implementation of login API
Contract: docs/WP-10-04_LOGIN_API_CONTRACT.md

These tests define the locked behavior and should FAIL initially.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.modules.tenants.models import Tenant
from app.modules.auth.models import User, Membership, Role
from app.core.security.password import hash_password


client = TestClient(app)


@pytest.fixture
def test_tenant(db: Session):
    """Create test tenant"""
    tenant = Tenant(
        id="company-test",
        name="Test Company",
        is_active=True,
        timezone="Asia/Taipei"
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def inactive_tenant(db: Session):
    """Create inactive tenant"""
    tenant = Tenant(
        id="company-inactive",
        name="Inactive Company",
        is_active=False,
        timezone="Asia/Taipei"
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def test_role(db: Session):
    """Create test role"""
    role = Role(
        id="employee",
        name="Employee",
        description="Regular employee"
    )
    db.add(role)
    db.commit()
    return role


@pytest.fixture
def test_user(db: Session):
    """Create test user with known password"""
    user = User(
        id=uuid.uuid4(),
        display_name="Test User",
        email="test@example.com",
        password_hash=hash_password("SecurePass123!"),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_membership(db: Session, test_user, test_tenant, test_role):
    """Create active membership"""
    membership = Membership(
        id=uuid.uuid4(),
        user_id=test_user.id,
        company_id=test_tenant.id,
        role_id=test_role.id,
        login_username="testuser",
        is_active=True
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


@pytest.fixture
def inactive_membership(db: Session, test_user, test_tenant, test_role):
    """Create inactive membership"""
    user = User(
        id=uuid.uuid4(),
        display_name="Inactive User",
        password_hash=hash_password("SecurePass123!"),
        is_active=True
    )
    db.add(user)
    db.commit()
    
    membership = Membership(
        id=uuid.uuid4(),
        user_id=user.id,
        company_id=test_tenant.id,
        role_id=test_role.id,
        login_username="inactiveuser",
        is_active=False  # Inactive
    )
    db.add(membership)
    db.commit()
    return membership


class TestLoginAPISuccess:
    """Test successful login scenarios"""
    
    def test_valid_login_returns_200_with_token(self, db: Session, test_tenant, test_membership):
        """Test valid login returns 200 with JWT token"""
        response = client.post(
            "/api/internal/auth/login",
            json={
                "company_id": test_tenant.id,
                "login_username": "testuser",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        
        # Check user info
        assert "user" in data
        assert "id" in data["user"]
        assert "display_name" in data["user"]
        assert data["user"]["display_name"] == "Test User"
        
        # Check company info
        assert "company" in data
        assert data["company"]["id"] == test_tenant.id
        assert data["company"]["name"] == "Test Company"
        
        # Check role info
        assert "role" in data
        assert data["role"]["id"] == "employee"
        assert data["role"]["name"] == "Employee"
    
    def test_jwt_token_contains_required_claims(self, db: Session, test_tenant, test_membership):
        """Test JWT token contains required claims (sub, company_id, role_id)"""
        response = client.post(
            "/api/internal/auth/login",
            json={
                "company_id": test_tenant.id,
                "login_username": "testuser",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Decode JWT token (will be implemented in WP-10-04B)
        token = data["access_token"]
        assert token is not None
        assert len(token) > 0
        
        # TODO: Decode and verify claims in WP-10-04B
        # Expected claims: sub (user_id), company_id, role_id, exp, iat


class TestLoginAPIAntiEnumeration:
    """Test anti-enumeration error semantics (404 for all scenarios)"""
    
    def test_company_not_exists_returns_404(self, db: Session):
        """Test non-existent company returns 404 with generic message"""
        response = client.post(
            "/api/internal/auth/login",
            json={
                "company_id": "nonexistent-company",
                "login_username": "testuser",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Invalid credentials"
    
    def test_membership_not_exists_returns_404(self, db: Session, test_tenant):
        """Test non-existent membership returns 404 (anti-enumeration)"""
        response = client.post(
            "/api/internal/auth/login",
            json={
                "company_id": test_tenant.id,
                "login_username": "nonexistent-user",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Invalid credentials"
    
    def test_membership_inactive_returns_404(self, db: Session, test_tenant, inactive_membership):
        """Test inactive membership returns 404 (anti-enumeration)"""
        response = client.post(
            "/api/internal/auth/login",
            json={
                "company_id": test_tenant.id,
                "login_username": "inactiveuser",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Invalid credentials"
    
    def test_company_inactive_returns_404(self, db: Session, inactive_tenant, test_role):
        """Test inactive company returns 404 (anti-enumeration)"""
        # Create user and membership for inactive company
        user = User(
            id=uuid.uuid4(),
            display_name="User in Inactive Company",
            password_hash=hash_password("SecurePass123!"),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        membership = Membership(
            id=uuid.uuid4(),
            user_id=user.id,
            company_id=inactive_tenant.id,
            role_id=test_role.id,
            login_username="testuser",
            is_active=True
        )
        db.add(membership)
        db.commit()
        
        response = client.post(
            "/api/internal/auth/login",
            json={
                "company_id": inactive_tenant.id,
                "login_username": "testuser",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Invalid credentials"


class TestLoginAPIWrongPassword:
    """Test wrong password returns 401 (but same message as 404)"""
    
    def test_wrong_password_returns_401(self, db: Session, test_tenant, test_membership):
        """Test wrong password returns 401 with generic message"""
        response = client.post(
            "/api/internal/auth/login",
            json={
                "company_id": test_tenant.id,
                "login_username": "testuser",
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Invalid credentials"


class TestLoginAPIValidation:
    """Test request validation errors (422)"""
    
    def test_missing_company_id_returns_422(self, db: Session):
        """Test missing company_id returns 422"""
        response = client.post(
            "/api/internal/auth/login",
            json={
                "login_username": "testuser",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_missing_login_username_returns_422(self, db: Session):
        """Test missing login_username returns 422"""
        response = client.post(
            "/api/internal/auth/login",
            json={
                "company_id": "company-test",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_missing_password_returns_422(self, db: Session):
        """Test missing password returns 422"""
        response = client.post(
            "/api/internal/auth/login",
            json={
                "company_id": "company-test",
                "login_username": "testuser"
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_empty_company_id_returns_422(self, db: Session):
        """Test empty company_id returns 422"""
        response = client.post(
            "/api/internal/auth/login",
            json={
                "company_id": "",
                "login_username": "testuser",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_empty_login_username_returns_422(self, db: Session):
        """Test empty login_username returns 422"""
        response = client.post(
            "/api/internal/auth/login",
            json={
                "company_id": "company-test",
                "login_username": "",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_empty_password_returns_422(self, db: Session):
        """Test empty password returns 422"""
        response = client.post(
            "/api/internal/auth/login",
            json={
                "company_id": "company-test",
                "login_username": "testuser",
                "password": ""
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
