"""Login API Tests (WP-10-04A)

TDD Red Phase: 13 tests based on WP-10-04_LOGIN_API_CONTRACT.md

Test Coverage:
- Success cases (3 tests)
- Error cases - Anti-Enumeration (4 tests)
- Validation cases (4 tests)
- JWT validation (2 tests)
"""

import pytest
import jwt
from fastapi.testclient import TestClient
from app.main import app
from app.modules.auth.repo import AuthRepository


client = TestClient(app)


# ========== Success Cases (3 tests) ==========

def test_login_success_returns_token_and_user_info(db, test_tenant, seed_roles):
    """Test successful login returns JWT token and user info"""
    # Arrange: Create user + membership
    auth_repo = AuthRepository(db)
    user = auth_repo.create_user(
        display_name="John Doe",
        plain_password="SecurePass123!",
        email="john@example.com"
    )
    auth_repo.create_membership(
        user_id=user.id,
        company_id="company-A",
        role_id="employee",
        login_username="john.doe"
    )
    
    # Act: Login
    response = client.post(
        "/api/internal/auth/login",
        json={
            "company_id": "company-A",
            "login_username": "john.doe",
            "password": "SecurePass123!"
        }
    )
    
    # Assert: 200 + token + user info
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    assert "user" in data
    assert data["user"]["id"] == str(user.id)
    assert data["user"]["display_name"] == "John Doe"
    assert data["user"]["email"] == "john@example.com"
    
    assert "company" in data
    assert data["company"]["id"] == "company-A"
    assert data["company"]["name"] == "Company A"
    
    assert "role" in data
    assert data["role"]["id"] == "employee"
    assert data["role"]["name"] == "Employee"


def test_login_success_jwt_contains_required_claims(db, test_tenant, seed_roles):
    """Test JWT token contains required claims (sub, company_id, role_id, exp, iat)"""
    # Arrange
    auth_repo = AuthRepository(db)
    user = auth_repo.create_user(
        display_name="Jane Smith",
        plain_password="Password456!",
        email="jane@example.com"
    )
    auth_repo.create_membership(
        user_id=user.id,
        company_id="company-A",
        role_id="manager",
        login_username="jane.smith"
    )
    
    # Act
    response = client.post(
        "/api/internal/auth/login",
        json={
            "company_id": "company-A",
            "login_username": "jane.smith",
            "password": "Password456!"
        }
    )
    
    # Assert: Decode JWT and check claims
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Decode without expiry verification (for testing)
    from app.core.config import settings
    decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"], options={"verify_exp": False})
    
    assert "sub" in decoded
    assert decoded["sub"] == str(user.id)
    assert "company_id" in decoded
    assert decoded["company_id"] == "company-A"
    assert "role_id" in decoded
    assert decoded["role_id"] == "manager"
    assert "exp" in decoded
    assert "iat" in decoded


def test_login_success_with_different_company(db, test_tenant_b, seed_roles):
    """Test user can login to different company with different username"""
    # Arrange: User with membership in company-B
    auth_repo = AuthRepository(db)
    user = auth_repo.create_user(
        display_name="Bob Wilson",
        plain_password="BobPass789!",
        email="bob@example.com"
    )
    auth_repo.create_membership(
        user_id=user.id,
        company_id="company-B",
        role_id="employee",
        login_username="bob.wilson"
    )
    
    # Act
    response = client.post(
        "/api/internal/auth/login",
        json={
            "company_id": "company-B",
            "login_username": "bob.wilson",
            "password": "BobPass789!"
        }
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["company"]["id"] == "company-B"
    assert data["company"]["name"] == "Company B"


# ========== Error Cases - Anti-Enumeration (4 tests) ==========

def test_login_company_not_exists_returns_404(db, seed_roles):
    """Test login with non-existent company returns 404 (anti-enumeration)"""
    # Act: Login with invalid company
    response = client.post(
        "/api/internal/auth/login",
        json={
            "company_id": "non-existent-company",
            "login_username": "john.doe",
            "password": "SecurePass123!"
        }
    )
    
    # Assert: 404 with generic message
    assert response.status_code == 404
    assert response.json()["detail"] == "Invalid credentials"


def test_login_membership_not_exists_returns_404(db, test_tenant, seed_roles):
    """Test login with non-existent membership returns 404 (anti-enumeration)"""
    # Act: Login with invalid username (no membership)
    response = client.post(
        "/api/internal/auth/login",
        json={
            "company_id": "company-A",
            "login_username": "non.existent.user",
            "password": "SomePassword123!"
        }
    )
    
    # Assert: 404 with generic message
    assert response.status_code == 404
    assert response.json()["detail"] == "Invalid credentials"


def test_login_membership_inactive_returns_404(db, test_tenant, seed_roles):
    """Test login with inactive membership returns 404 (anti-enumeration)"""
    # Arrange: Create user with inactive membership
    auth_repo = AuthRepository(db)
    user = auth_repo.create_user(
        display_name="Inactive User",
        plain_password="InactivePass123!",
        email="inactive@example.com"
    )
    auth_repo.create_membership(
        user_id=user.id,
        company_id="company-A",
        role_id="employee",
        login_username="inactive.user",
        is_active=False  # Inactive membership
    )
    
    # Act
    response = client.post(
        "/api/internal/auth/login",
        json={
            "company_id": "company-A",
            "login_username": "inactive.user",
            "password": "InactivePass123!"
        }
    )
    
    # Assert: 404 with generic message
    assert response.status_code == 404
    assert response.json()["detail"] == "Invalid credentials"


def test_login_wrong_password_returns_401(db, test_tenant, seed_roles):
    """Test login with wrong password returns 401"""
    # Arrange: Create user + membership
    auth_repo = AuthRepository(db)
    user = auth_repo.create_user(
        display_name="Test User",
        plain_password="CorrectPassword123!",
        email="test@example.com"
    )
    auth_repo.create_membership(
        user_id=user.id,
        company_id="company-A",
        role_id="employee",
        login_username="test.user"
    )
    
    # Act: Login with wrong password
    response = client.post(
        "/api/internal/auth/login",
        json={
            "company_id": "company-A",
            "login_username": "test.user",
            "password": "WrongPassword123!"
        }
    )
    
    # Assert: 401 with generic message
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


# ========== Validation Cases (4 tests) ==========

def test_login_missing_company_id_returns_422(db):
    """Test login without company_id returns 422"""
    response = client.post(
        "/api/internal/auth/login",
        json={
            "login_username": "john.doe",
            "password": "SecurePass123!"
        }
    )
    
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(err["loc"] == ["body", "company_id"] for err in detail)


def test_login_missing_login_username_returns_422(db):
    """Test login without login_username returns 422"""
    response = client.post(
        "/api/internal/auth/login",
        json={
            "company_id": "company-A",
            "password": "SecurePass123!"
        }
    )
    
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(err["loc"] == ["body", "login_username"] for err in detail)


def test_login_missing_password_returns_422(db):
    """Test login without password returns 422"""
    response = client.post(
        "/api/internal/auth/login",
        json={
            "company_id": "company-A",
            "login_username": "john.doe"
        }
    )
    
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(err["loc"] == ["body", "password"] for err in detail)


def test_login_empty_fields_returns_422(db):
    """Test login with empty fields returns 422"""
    response = client.post(
        "/api/internal/auth/login",
        json={
            "company_id": "",
            "login_username": "",
            "password": ""
        }
    )
    
    assert response.status_code == 422


# ========== JWT Validation (2 tests) ==========

def test_jwt_token_expires_in_900_seconds(db, test_tenant, seed_roles):
    """Test JWT token expires in 900 seconds (15 minutes)"""
    # Arrange
    auth_repo = AuthRepository(db)
    user = auth_repo.create_user(
        display_name="Token Test User",
        plain_password="TokenPass123!",
        email="token@example.com"
    )
    auth_repo.create_membership(
        user_id=user.id,
        company_id="company-A",
        role_id="employee",
        login_username="token.user"
    )
    
    # Act
    response = client.post(
        "/api/internal/auth/login",
        json={
            "company_id": "company-A",
            "login_username": "token.user",
            "password": "TokenPass123!"
        }
    )
    
    # Assert: Check exp - iat = 900
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    from app.core.config import settings
    decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"], options={"verify_exp": False})
    
    exp = decoded["exp"]
    iat = decoded["iat"]
    assert exp - iat == 900


def test_jwt_token_uses_hs256_algorithm(db, test_tenant, seed_roles):
    """Test JWT token uses HS256 algorithm"""
    # Arrange
    auth_repo = AuthRepository(db)
    user = auth_repo.create_user(
        display_name="Algo Test User",
        plain_password="AlgoPass123!",
        email="algo@example.com"
    )
    auth_repo.create_membership(
        user_id=user.id,
        company_id="company-A",
        role_id="employee",
        login_username="algo.user"
    )
    
    # Act
    response = client.post(
        "/api/internal/auth/login",
        json={
            "company_id": "company-A",
            "login_username": "algo.user",
            "password": "AlgoPass123!"
        }
    )
    
    # Assert: Decode header to check algorithm
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Decode header without verification
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"
