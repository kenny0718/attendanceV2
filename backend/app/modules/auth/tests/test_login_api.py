"""Login API Tests (WP-10-04A)"""

import jwt
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.repo import AuthRepository

client = TestClient(app)


def test_login_success_returns_token_and_user_info(db, test_tenant, seed_roles):
    auth_repo = AuthRepository(db)
    user = auth_repo.create_user(
        display_name="John Doe",
        plain_password="SecurePass123!",
        email="john@example.com",
    )
    auth_repo.create_membership(
        user_id=user.id,
        company_id="company-A",
        role_id="employee",
        login_username="john.doe",
    )

    response = client.post(
        "/api/internal/auth/login",
        json={
            "company_id": "company-A",
            "login_username": "john.doe",
            "password": "SecurePass123!",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == str(user.id)
    assert data["company"]["id"] == "company-A"
    assert data["role"]["id"] == "employee"


def test_login_success_with_tax_id_as_company_input(db, test_tenant, seed_roles):
    test_tenant.tax_id = "24536806"
    db.commit()

    auth_repo = AuthRepository(db)
    user = auth_repo.create_user(
        display_name="Tax Login User",
        plain_password="TaxPass123!",
        email="tax@example.com",
    )
    auth_repo.create_membership(
        user_id=user.id,
        company_id="company-A",
        role_id="employee",
        login_username="tax.user",
    )

    response = client.post(
        "/api/internal/auth/login",
        json={
            "company_id": "24536806",
            "login_username": "tax.user",
            "password": "TaxPass123!",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["company"]["id"] == "company-A"
    assert data["company"]["name"] == "Company A"


def test_login_wrong_password_returns_401(db, test_tenant, seed_roles):
    auth_repo = AuthRepository(db)
    user = auth_repo.create_user(
        display_name="Test User",
        plain_password="CorrectPassword123!",
        email="test@example.com",
    )
    auth_repo.create_membership(
        user_id=user.id,
        company_id="company-A",
        role_id="employee",
        login_username="test.user",
    )

    response = client.post(
        "/api/internal/auth/login",
        json={
            "company_id": "company-A",
            "login_username": "test.user",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_missing_company_id_returns_422(db):
    response = client.post(
        "/api/internal/auth/login",
        json={
            "login_username": "john.doe",
            "password": "SecurePass123!",
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(err["loc"] == ["body", "company_id"] for err in detail)


def test_jwt_token_contains_required_claims(db, test_tenant, seed_roles):
    auth_repo = AuthRepository(db)
    user = auth_repo.create_user(
        display_name="Jane Smith",
        plain_password="Password456!",
        email="jane@example.com",
    )
    auth_repo.create_membership(
        user_id=user.id,
        company_id="company-A",
        role_id="manager",
        login_username="jane.smith",
    )

    response = client.post(
        "/api/internal/auth/login",
        json={
            "company_id": "company-A",
            "login_username": "jane.smith",
            "password": "Password456!",
        },
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    from app.core.config import settings
    decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"], options={"verify_exp": False})

    assert decoded["sub"] == str(user.id)
    assert decoded["company_id"] == "company-A"
    assert decoded["role_id"] == "manager"
    assert "exp" in decoded
    assert "iat" in decoded
