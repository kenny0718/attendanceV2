from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.core.database import get_db
from app.core.security.jwt import create_access_token
from app.modules.auth.repo import AuthRepository
from app.modules.tenants.repo import CompanyEntitlementRepository, TenantRepository

client = TestClient(app)

JWT_COMPANY_A = "s106-jwt-company-a"
JWT_COMPANY_B = "s106-jwt-company-b"
JWT_USER_ID = UUID("00000000-0000-4000-a000-000000000106")
JWT_ROLE_ID = "company_admin"
SCHEDULE_FEATURE_KEY = "schedule.core"


@pytest.fixture(scope="function")
def jwt_test_db(db):
    auth_repo = AuthRepository(db)
    entitlement_repo = CompanyEntitlementRepository(db)
    tenant_repo = TenantRepository(db)

    db.execute(
        text(
            """
            INSERT INTO roles (id, name, description, created_at)
            VALUES (:id, :name, :description, NOW())
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {
            "id": JWT_ROLE_ID,
            "name": "Company Admin",
            "description": "JWT test role",
        },
    )
    db.commit()

    user = auth_repo.get_user_by_id(JWT_USER_ID)
    if not user:
        db.execute(
            text(
                """
                INSERT INTO users (
                    id,
                    display_name,
                    email,
                    password_hash,
                    is_active,
                    is_otp,
                    must_change_password,
                    created_at,
                    updated_at
                )
                VALUES (
                    :id,
                    :display_name,
                    :email,
                    :password_hash,
                    TRUE,
                    FALSE,
                    FALSE,
                    NOW(),
                    NOW()
                )
                """
            ),
            {
                "id": str(JWT_USER_ID),
                "display_name": "JWT Schedule Admin",
                "email": "jwt.schedule.admin@example.com",
                "password_hash": "$2b$12$abcdefghijklmnopqrstuuR4x1u4zvA9w8Q2v5W6n7m8o9p0q1r2",
            },
        )
        db.commit()

    for company_id, enabled in ((JWT_COMPANY_A, True), (JWT_COMPANY_B, False)):
        tenant = tenant_repo.get_by_id(company_id)
        if not tenant:
            tenant_repo.create(tenant_id=company_id, name=company_id, timezone="Asia/Taipei")

        membership = auth_repo.get_membership(JWT_USER_ID, company_id)
        if not membership:
            auth_repo.create_membership(
                user_id=JWT_USER_ID,
                company_id=company_id,
                role_id=JWT_ROLE_ID,
                login_username=f"jwt-{company_id}",
                is_active=True,
                uses_schedule=True,
            )

        entitlement_repo.upsert_entitlement(
            company_id=company_id,
            feature_key=SCHEDULE_FEATURE_KEY,
            enabled=enabled,
            updated_by_user_id=JWT_USER_ID,
        )

    def _override_get_db():
        try:
            yield db
        finally:
            db.flush()

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield db
    finally:
        app.dependency_overrides.pop(get_db, None)


def make_jwt(company_id: str, user_id: UUID = JWT_USER_ID, role_id: str = JWT_ROLE_ID) -> str:
    return create_access_token(
        {
            "sub": str(user_id),
            "company_id": company_id,
            "role_id": role_id,
            "session_id": "test-session-real-jwt",
            "type": "access",
        }
    )


def auth_headers(company_id: str) -> dict:
    return {"Authorization": f"Bearer {make_jwt(company_id)}"}


class TestRealJWTAuthBaseline:
    def test_no_token_returns_401(self, jwt_test_db):
        r = client.get("/api/v1/schedule/shift-templates")
        assert r.status_code == 401, r.text

    def test_invalid_token_returns_401(self, jwt_test_db):
        r = client.get(
            "/api/v1/schedule/shift-templates",
            headers={"Authorization": "Bearer invalid.token.value"},
        )
        assert r.status_code == 401, r.text

    def test_valid_jwt_company_a_list_returns_200(self, jwt_test_db):
        r = client.get("/api/v1/schedule/shift-templates", headers=auth_headers(JWT_COMPANY_A))
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_valid_jwt_company_b_no_entitlement_returns_403(self, jwt_test_db):
        r = client.get("/api/v1/schedule/shift-templates", headers=auth_headers(JWT_COMPANY_B))
        assert r.status_code == 403, r.text
        assert r.json()["detail"]["feature"] == SCHEDULE_FEATURE_KEY


class TestTemplateRealJWTFlow:
    def _template_payload(self, code: str) -> dict:
        return {
            "company_id": JWT_COMPANY_A,
            "code": code,
            "name": f"JWT Template {code}",
            "start_time": "09:00:00",
            "end_time": "18:00:00",
            "break_minutes": 60,
            "is_overnight": False,
            "is_active": True,
        }

    def test_create_template_real_jwt(self, jwt_test_db):
        code = f"JWTC_{uuid4().hex[:6].upper()}"
        r = client.post(
            "/api/v1/schedule/shift-templates",
            json=self._template_payload(code),
            headers=auth_headers(JWT_COMPANY_A),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["company_id"] == JWT_COMPANY_A
        assert data["code"] == code

    def test_get_template_real_jwt(self, jwt_test_db):
        code = f"JWTG_{uuid4().hex[:6].upper()}"
        created = client.post(
            "/api/v1/schedule/shift-templates",
            json=self._template_payload(code),
            headers=auth_headers(JWT_COMPANY_A),
        )
        assert created.status_code == 201, created.text
        tid = created.json()["id"]

        r = client.get(
            f"/api/v1/schedule/shift-templates/{tid}",
            headers=auth_headers(JWT_COMPANY_A),
        )
        assert r.status_code == 200, r.text
        assert r.json()["id"] == tid

    def test_list_templates_real_jwt(self, jwt_test_db):
        code = f"JWTL_{uuid4().hex[:6].upper()}"
        created = client.post(
            "/api/v1/schedule/shift-templates",
            json=self._template_payload(code),
            headers=auth_headers(JWT_COMPANY_A),
        )
        assert created.status_code == 201, created.text

        r = client.get("/api/v1/schedule/shift-templates", headers=auth_headers(JWT_COMPANY_A))
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1


class TestAssignmentRealJWTFlow:
    def _create_template(self):
        code = f"JWTA_{uuid4().hex[:6].upper()}"
        r = client.post(
            "/api/v1/schedule/shift-templates",
            json={
                "company_id": JWT_COMPANY_A,
                "code": code,
                "name": f"Assignment Template {code}",
                "start_time": "09:00:00",
                "end_time": "18:00:00",
                "break_minutes": 60,
                "is_overnight": False,
                "is_active": True,
            },
            headers=auth_headers(JWT_COMPANY_A),
        )
        assert r.status_code == 201, r.text
        return r.json()["id"]

    def test_create_assignment_real_jwt(self, jwt_test_db):
        template_id = self._create_template()
        r = client.post(
            "/api/v1/schedule/shift-assignments",
            json={
                "company_id": JWT_COMPANY_A,
                "user_id": str(JWT_USER_ID),
                "shift_template_id": template_id,
                "work_date": "2026-04-01",
            },
            headers=auth_headers(JWT_COMPANY_A),
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["company_id"] == JWT_COMPANY_A
        assert data["user_id"] == str(JWT_USER_ID)

    def test_get_assignment_real_jwt(self, jwt_test_db):
        template_id = self._create_template()
        created = client.post(
            "/api/v1/schedule/shift-assignments",
            json={
                "company_id": JWT_COMPANY_A,
                "user_id": str(JWT_USER_ID),
                "shift_template_id": template_id,
                "work_date": "2026-04-02",
            },
            headers=auth_headers(JWT_COMPANY_A),
        )
        assert created.status_code == 201, created.text
        aid = created.json()["id"]

        r = client.get(
            f"/api/v1/schedule/shift-assignments/{aid}",
            headers=auth_headers(JWT_COMPANY_A),
        )
        assert r.status_code == 200, r.text
        assert r.json()["id"] == aid

    def test_cancel_assignment_real_jwt(self, jwt_test_db):
        template_id = self._create_template()
        created = client.post(
            "/api/v1/schedule/shift-assignments",
            json={
                "company_id": JWT_COMPANY_A,
                "user_id": str(JWT_USER_ID),
                "shift_template_id": template_id,
                "work_date": "2026-04-03",
            },
            headers=auth_headers(JWT_COMPANY_A),
        )
        assert created.status_code == 201, created.text
        aid = created.json()["id"]

        r = client.post(
            f"/api/v1/schedule/shift-assignments/{aid}/cancel",
            headers=auth_headers(JWT_COMPANY_A),
        )
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "cancelled"


class TestNegativeCasesRealJWT:
    def _make_company_a_template(self):
        code = f"JWTX_{uuid4().hex[:6].upper()}"
        r = client.post(
            "/api/v1/schedule/shift-templates",
            json={
                "company_id": JWT_COMPANY_A,
                "code": code,
                "name": f"Cross Tenant Template {code}",
                "start_time": "09:00:00",
                "end_time": "18:00:00",
                "break_minutes": 60,
                "is_overnight": False,
                "is_active": True,
            },
            headers=auth_headers(JWT_COMPANY_A),
        )
        assert r.status_code == 201, r.text
        return r.json()["id"]

    def test_no_entitlement_list_blocked(self, jwt_test_db):
        r = client.get("/api/v1/schedule/shift-templates", headers=auth_headers(JWT_COMPANY_B))
        assert r.status_code == 403
        assert r.json()["detail"]["code"] == "FEATURE_DISABLED"

    def test_no_entitlement_create_blocked(self, jwt_test_db):
        r = client.post(
            "/api/v1/schedule/shift-templates",
            json={
                "company_id": JWT_COMPANY_B,
                "code": f"JWTB_{uuid4().hex[:6].upper()}",
                "name": "Blocked Create",
                "start_time": "09:00:00",
                "end_time": "18:00:00",
                "break_minutes": 60,
                "is_overnight": False,
                "is_active": True,
            },
            headers=auth_headers(JWT_COMPANY_B),
        )
        assert r.status_code == 403
        assert r.json()["detail"]["code"] == "FEATURE_DISABLED"

    def test_cross_tenant_template_blocked(self, jwt_test_db):
        tid = self._make_company_a_template()
        r = client.get(
            f"/api/v1/schedule/shift-templates/{tid}",
            headers=auth_headers(JWT_COMPANY_B),
        )
        assert r.status_code in (403, 404), r.text

    def test_unauthenticated_assignment_blocked(self, jwt_test_db):
        r = client.get("/api/v1/schedule/shift-assignments")
        assert r.status_code == 401
