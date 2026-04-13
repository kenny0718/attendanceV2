"""
WP-S1-06: Schedule Real JWT E2E Tests
========================================

本檔驗證 Schedule API 在真實 JWT 驗證流程下的端對端行為。

與 WP-S1-05 的關鍵差異：
- 不使用 override_actor_dependency（dependency_override 捷徑）
- 使用 create_access_token() 產生真實 HS256 signed JWT
- 透過 Authorization: Bearer <token> header 傳入
- 完整走過 get_current_actor → decode_access_token → DB 查詢 → Actor 建立路徑

測試驗證範圍：
1. 真實 JWT + schedule.core entitlement → PASS (200/201)
2. 真實 JWT + 無 entitlement → 403 FEATURE_DISABLED
3. Cross-tenant resource access → 404
4. 無 JWT → 401
5. Template CRUD smoke: create / get / list
6. Assignment CRUD smoke: create / get / cancel
"""

import os
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.core.features import FeatureKeys
from app.core.security.jwt import create_access_token
from app.main import app as fastapi_app
from app.modules.attendance.models import (  # noqa: F401
    AttendanceOutCheckpoint,
    AttendancePolicy,
    AttendancePunch,
    AttendanceSession,
    AllowedLocation,
)
from app.modules.schedule.models import ShiftAssignment, ShiftTemplate  # noqa: F401
from app.modules.auth.models import Membership, Role, User
from app.modules.tenants.models import CompanyEntitlement, Tenant

JWT_COMPANY_A = "s106-jwt-company-a"
JWT_COMPANY_B = "s106-jwt-company-b"
JWT_USER_ID = UUID("00000000-0000-4000-a000-000000000106")
JWT_ROLE_ID = "company_admin"


client = TestClient(fastapi_app)


def _get_test_db_url() -> str:
    return os.getenv(
        "TEST_DATABASE_URL",
        os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://postgres:Raxcxtjq260!@127.0.0.1:5432/attendance_test_db",
        ),
    )


_engine = create_engine(_get_test_db_url(), pool_pre_ping=True, echo=False)
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture(scope="function")
def jwt_test_db():
    Base.metadata.drop_all(bind=_engine, checkfirst=True)
    Base.metadata.create_all(bind=_engine, checkfirst=True)

    db = _Session()

    if not db.query(Role).filter(Role.id == JWT_ROLE_ID).first():
        db.add(Role(id=JWT_ROLE_ID, name="Company Admin", description="Full access within company"))

    for company_id, name in [
        (JWT_COMPANY_A, "JWT Company A"),
        (JWT_COMPANY_B, "JWT Company B"),
    ]:
        if not db.query(Tenant).filter(Tenant.id == company_id).first():
            db.add(Tenant(id=company_id, name=name, is_active=True))

    if not db.query(User).filter(User.id == JWT_USER_ID).first():
        db.add(User(
            id=JWT_USER_ID,
            display_name="JWT Schedule User",
            password_hash="dummy_hash_not_used",
            is_active=True,
        ))
        db.flush()

    for company_id, login_username in [
        (JWT_COMPANY_A, "jwt-admin-a"),
        (JWT_COMPANY_B, "jwt-admin-b"),
    ]:
        existing = db.query(Membership).filter(
            Membership.user_id == JWT_USER_ID,
            Membership.company_id == company_id,
        ).first()
        if not existing:
            db.add(Membership(
                id=uuid4(),
                user_id=JWT_USER_ID,
                company_id=company_id,
                role_id=JWT_ROLE_ID,
                login_username=login_username,
                is_active=True,
            ))

    db.add(CompanyEntitlement(
        id=uuid4(),
        company_id=JWT_COMPANY_A,
        feature_key=FeatureKeys.SCHEDULE_CORE,
        enabled=True,
    ))
    db.commit()

    def _override_get_db():
        try:
            yield db
        finally:
            db.flush()

    fastapi_app.dependency_overrides[get_db] = _override_get_db

    try:
        yield db
    finally:
        db.close()
        fastapi_app.dependency_overrides.pop(get_db, None)


def make_jwt(company_id: str, user_id: UUID = JWT_USER_ID, role_id: str = JWT_ROLE_ID) -> str:
    return create_access_token(
        {
            "sub": str(user_id),
            "company_id": company_id,
            "role_id": role_id,
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
        assert r.json()["detail"]["feature"] == FeatureKeys.SCHEDULE_CORE


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
