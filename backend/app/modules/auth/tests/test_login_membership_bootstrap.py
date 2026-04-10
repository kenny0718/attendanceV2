import jwt
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.repo import AuthRepository

client = TestClient(app)


def test_login_response_includes_membership_bootstrap_with_default_uses_schedule(db, test_tenant, seed_roles):
    auth_repo = AuthRepository(db)
    user = auth_repo.create_user(
        display_name="Bootstrap User",
        plain_password="BootstrapPass123!",
        email="bootstrap@example.com",
    )
    membership = auth_repo.create_membership(
        user_id=user.id,
        company_id="company-A",
        role_id="employee",
        login_username="bootstrap.user",
    )

    response = client.post(
        "/api/internal/auth/login",
        json={
            "company_id": "company-A",
            "login_username": "bootstrap.user",
            "password": "BootstrapPass123!",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["membership"]["membership_id"] == str(membership.id)
    assert data["membership"]["company_id"] == "company-A"
    assert data["membership"]["role_id"] == "employee"
    assert data["membership"]["login_username"] == "bootstrap.user"
    assert data["membership"]["is_active"] is True
    assert data["membership"]["uses_schedule"] is False


def test_login_response_includes_membership_bootstrap_with_uses_schedule_true(db, test_tenant, seed_roles):
    auth_repo = AuthRepository(db)
    user = auth_repo.create_user(
        display_name="Schedule User",
        plain_password="SchedulePass123!",
        email="schedule@example.com",
    )
    membership = auth_repo.create_membership(
        user_id=user.id,
        company_id="company-A",
        role_id="employee",
        login_username="schedule.user",
        uses_schedule=True,
    )

    response = client.post(
        "/api/internal/auth/login",
        json={
            "company_id": "company-A",
            "login_username": "schedule.user",
            "password": "SchedulePass123!",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["membership"]["membership_id"] == str(membership.id)
    assert data["membership"]["uses_schedule"] is True

    token = data["access_token"]
    from app.core.config import settings
    decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"], options={"verify_exp": False})
    assert decoded["company_id"] == "company-A"
    assert decoded["role_id"] == "employee"
