"""Tests for Companies API (WP-S1-09A)

GET  /api/admin/companies  — list all companies (super_admin only)
POST /api/admin/companies  — create company   (super_admin only)

使用 PostgreSQL Test DB + Transaction Rollback（與現有 entitlements 測試相同策略）
"""

import pytest
from uuid import uuid4

from app.core.scope import Actor, UserRole
from app.core.dependencies import get_current_actor
from app.modules.tenants.models import Tenant
from app.main import app


# ── helper fixtures ───────────────────────────────────────────────────

def _make_super_admin_actor() -> Actor:
    return Actor(user_id=uuid4(), role=UserRole.SUPER_ADMIN)


def _make_company_admin_actor(company_id: str = "dev-tenant") -> Actor:
    """company_admin — COMPANY_USER platform role, active_role_id='company_admin'"""
    return Actor(
        user_id=uuid4(),
        role=UserRole.COMPANY_USER,
        company_memberships={company_id},
        active_company_id=company_id,
        active_role_id="company_admin",
    )


def _make_employee_actor(company_id: str = "dev-tenant") -> Actor:
    return Actor(
        user_id=uuid4(),
        role=UserRole.COMPANY_USER,
        company_memberships={company_id},
        active_company_id=company_id,
        active_role_id="employee",
    )


def _override_actor(client, actor: Actor):
    """Override get_current_actor dependency and return cleanup callable."""
    app.dependency_overrides[get_current_actor] = lambda: actor


def _clear_actor():
    app.dependency_overrides.pop(get_current_actor, None)


# ── GET /api/admin/companies ──────────────────────────────────────────

class TestListCompanies:
    """GET /api/admin/companies"""

    def test_super_admin_can_list_companies(self, db_session, client):
        """super_admin 可列出所有公司"""
        # 建立兩間測試公司
        db_session.add(Tenant(id="list-co-1", name="List Co 1", timezone="UTC", is_active=True))
        db_session.add(Tenant(id="list-co-2", name="List Co 2", timezone="Asia/Taipei", is_active=True))
        db_session.commit()

        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.get("/api/admin/companies")
        finally:
            _clear_actor()

        assert response.status_code == 200
        data = response.json()
        assert "companies" in data
        assert "total" in data
        ids = [c["id"] for c in data["companies"]]
        assert "list-co-1" in ids
        assert "list-co-2" in ids

    def test_list_companies_response_shape(self, db_session, client):
        """回應包含正確欄位 (id, name, is_active, timezone, created_at)"""
        db_session.add(Tenant(id="shape-co", name="Shape Co", timezone="UTC", is_active=True))
        db_session.commit()

        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.get("/api/admin/companies")
        finally:
            _clear_actor()

        assert response.status_code == 200
        companies = response.json()["companies"]
        co = next((c for c in companies if c["id"] == "shape-co"), None)
        assert co is not None
        assert co["name"] == "Shape Co"
        assert co["is_active"] is True
        assert co["timezone"] == "UTC"
        assert "created_at" in co

    def test_company_admin_cannot_list_companies(self, db_session, client):
        """company_admin 不可列出所有公司 → 403"""
        _override_actor(client, _make_company_admin_actor())
        try:
            response = client.get("/api/admin/companies")
        finally:
            _clear_actor()

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "SCOPE_FORBIDDEN"

    def test_employee_cannot_list_companies(self, db_session, client):
        """employee 不可列出所有公司 → 403"""
        _override_actor(client, _make_employee_actor())
        try:
            response = client.get("/api/admin/companies")
        finally:
            _clear_actor()

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "SCOPE_FORBIDDEN"

    def test_unauthenticated_cannot_list_companies(self, client):
        """未驗證請求 → 401"""
        # 不設置任何 actor override，使用實際 JWT 驗證
        # 沒有 Authorization header → 401
        response = client.get("/api/admin/companies")
        # dependency_overrides 已清除，get_current_actor 會要求 JWT
        assert response.status_code == 401


# ── POST /api/admin/companies ─────────────────────────────────────────

class TestCreateCompany:
    """POST /api/admin/companies"""

    def test_super_admin_can_create_company(self, db_session, client):
        """super_admin 可建立新公司"""
        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.post(
                "/api/admin/companies",
                json={"id": "new-co-1", "name": "New Company 1", "timezone": "Asia/Taipei"},
            )
        finally:
            _clear_actor()

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "new-co-1"
        assert data["name"] == "New Company 1"
        assert data["timezone"] == "Asia/Taipei"
        assert data["is_active"] is True
        assert "created_at" in data

    def test_create_company_default_timezone(self, db_session, client):
        """timezone 預設為 UTC"""
        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.post(
                "/api/admin/companies",
                json={"id": "tz-default-co", "name": "TZ Default Co"},
            )
        finally:
            _clear_actor()

        assert response.status_code == 201
        assert response.json()["timezone"] == "UTC"

    def test_create_company_duplicate_rejected(self, db_session, client):
        """重複 company ID → 409 DUPLICATE_COMPANY"""
        # 先建立公司
        db_session.add(Tenant(id="dup-co", name="Dup Co", timezone="UTC", is_active=True))
        db_session.commit()

        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.post(
                "/api/admin/companies",
                json={"id": "dup-co", "name": "Dup Co Again"},
            )
        finally:
            _clear_actor()

        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "DUPLICATE_COMPANY"

    def test_create_company_missing_required_fields(self, db_session, client):
        """缺少必要欄位 → 422 Unprocessable Entity"""
        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.post(
                "/api/admin/companies",
                json={"name": "No ID Company"},  # 缺少 id
            )
        finally:
            _clear_actor()

        assert response.status_code == 422

    def test_create_company_empty_id_rejected(self, db_session, client):
        """空字串 id → 422"""
        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.post(
                "/api/admin/companies",
                json={"id": "", "name": "Empty ID Co"},
            )
        finally:
            _clear_actor()

        assert response.status_code == 422

    def test_company_admin_cannot_create_company(self, db_session, client):
        """company_admin 不可建立公司 → 403"""
        _override_actor(client, _make_company_admin_actor())
        try:
            response = client.post(
                "/api/admin/companies",
                json={"id": "forbidden-co", "name": "Forbidden Co"},
            )
        finally:
            _clear_actor()

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "SCOPE_FORBIDDEN"

    def test_employee_cannot_create_company(self, db_session, client):
        """employee 不可建立公司 → 403"""
        _override_actor(client, _make_employee_actor())
        try:
            response = client.post(
                "/api/admin/companies",
                json={"id": "emp-co", "name": "Employee Co"},
            )
        finally:
            _clear_actor()

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "SCOPE_FORBIDDEN"

    def test_unauthenticated_cannot_create_company(self, client):
        """未驗證請求 → 401"""
        response = client.post(
            "/api/admin/companies",
            json={"id": "unauth-co", "name": "Unauth Co"},
        )
        assert response.status_code == 401


# ── S1-11A: GET /api/admin/companies/{company_id} ────────────────────

class TestGetCompany:
    """GET /api/admin/companies/{company_id}"""

    def test_super_admin_can_get_company(self, db_session, client):
        """super_admin 可讀取單一公司"""
        db_session.add(Tenant(id="detail-co-1", name="Detail Co", timezone="Asia/Taipei", is_active=True))
        db_session.commit()

        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.get("/api/admin/companies/detail-co-1")
        finally:
            _clear_actor()

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "detail-co-1"
        assert data["name"] == "Detail Co"
        assert data["timezone"] == "Asia/Taipei"
        assert data["is_active"] is True
        assert "created_at" in data

    def test_get_company_not_found(self, db_session, client):
        """company 不存在 → 404"""
        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.get("/api/admin/companies/nonexistent-xyz")
        finally:
            _clear_actor()

        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "COMPANY_NOT_FOUND"

    def test_company_admin_cannot_get_company(self, db_session, client):
        """company_admin → 403"""
        db_session.add(Tenant(id="detail-co-2", name="Detail Co 2", timezone="UTC", is_active=True))
        db_session.commit()

        _override_actor(client, _make_company_admin_actor())
        try:
            response = client.get("/api/admin/companies/detail-co-2")
        finally:
            _clear_actor()

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "SCOPE_FORBIDDEN"

    def test_employee_cannot_get_company(self, db_session, client):
        """employee → 403"""
        db_session.add(Tenant(id="detail-co-3", name="Detail Co 3", timezone="UTC", is_active=True))
        db_session.commit()

        _override_actor(client, _make_employee_actor())
        try:
            response = client.get("/api/admin/companies/detail-co-3")
        finally:
            _clear_actor()

        assert response.status_code == 403

    def test_unauthenticated_cannot_get_company(self, client):
        """未驗證 → 401"""
        response = client.get("/api/admin/companies/any-co")
        assert response.status_code == 401


# ── S1-11A: PATCH /api/admin/companies/{company_id} ──────────────────

class TestUpdateCompany:
    """PATCH /api/admin/companies/{company_id}"""

    def test_super_admin_can_update_name(self, db_session, client):

        """super_admin 可更新 name，DB 真的改變"""
        db_session.add(Tenant(id="upd-co-1", name="Old Name", timezone="UTC", is_active=True))
        db_session.commit()

        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.patch(
                "/api/admin/companies/upd-co-1",
                json={"name": "New Name"},
            )
        finally:
            _clear_actor()

        assert response.status_code == 200
        assert response.json()["name"] == "New Name"
        db_session.expire_all()
        tenant = db_session.query(Tenant).filter_by(id="upd-co-1").first()
        assert tenant.name == "New Name"

    def test_super_admin_can_update_timezone(self, db_session, client):
        """super_admin 可更新 timezone，DB 真的改變"""
        db_session.add(Tenant(id="upd-co-2", name="Tz Co", timezone="UTC", is_active=True))
        db_session.commit()

        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.patch(
                "/api/admin/companies/upd-co-2",
                json={"timezone": "Asia/Tokyo"},
            )
        finally:
            _clear_actor()

        assert response.status_code == 200
        assert response.json()["timezone"] == "Asia/Tokyo"
        db_session.expire_all()
        tenant = db_session.query(Tenant).filter_by(id="upd-co-2").first()
        assert tenant.timezone == "Asia/Tokyo"

    def test_super_admin_can_deactivate_company(self, db_session, client):
        """super_admin 可停用 company，DB is_active 變 False"""
        db_session.add(Tenant(id="upd-co-3", name="Active Co", timezone="UTC", is_active=True))
        db_session.commit()

        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.patch(
                "/api/admin/companies/upd-co-3",
                json={"is_active": False},
            )
        finally:
            _clear_actor()

        assert response.status_code == 200
        assert response.json()["is_active"] is False
        db_session.expire_all()
        tenant = db_session.query(Tenant).filter_by(id="upd-co-3").first()
        assert tenant.is_active is False

    def test_super_admin_can_reactivate_company(self, db_session, client):
        """super_admin 可重新啟用 company"""
        db_session.add(Tenant(id="upd-co-4", name="Inactive Co", timezone="UTC", is_active=False))
        db_session.commit()

        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.patch(
                "/api/admin/companies/upd-co-4",
                json={"is_active": True},
            )
        finally:
            _clear_actor()

        assert response.status_code == 200
        assert response.json()["is_active"] is True
        db_session.expire_all()
        tenant = db_session.query(Tenant).filter_by(id="upd-co-4").first()
        assert tenant.is_active is True

    def test_update_company_not_found(self, db_session, client):
        """company 不存在 → 404"""
        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.patch(
                "/api/admin/companies/nonexistent-upd-xyz",
                json={"name": "Ghost"},
            )
        finally:
            _clear_actor()

        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "COMPANY_NOT_FOUND"

    def test_update_company_empty_body_rejected(self, db_session, client):
        """空 body → 422"""
        db_session.add(Tenant(id="upd-co-5", name="Empty Body Co", timezone="UTC", is_active=True))
        db_session.commit()

        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.patch(
                "/api/admin/companies/upd-co-5",
                json={},
            )
        finally:
            _clear_actor()

        assert response.status_code == 422

    def test_company_admin_cannot_update_company(self, db_session, client):
        """company_admin → 403"""
        db_session.add(Tenant(id="upd-co-6", name="Co Admin Target", timezone="UTC", is_active=True))
        db_session.commit()

        _override_actor(client, _make_company_admin_actor())
        try:
            response = client.patch(
                "/api/admin/companies/upd-co-6",
                json={"name": "Hacked"},
            )
        finally:
            _clear_actor()

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "SCOPE_FORBIDDEN"

    def test_employee_cannot_update_company(self, db_session, client):
        """employee → 403"""
        db_session.add(Tenant(id="upd-co-7", name="Emp Target", timezone="UTC", is_active=True))
        db_session.commit()

        _override_actor(client, _make_employee_actor())
        try:
            response = client.patch(
                "/api/admin/companies/upd-co-7",
                json={"name": "Hacked"},
            )
        finally:
            _clear_actor()

        assert response.status_code == 403

    def test_unauthenticated_cannot_update_company(self, client):
        """未驗證 → 401"""
        response = client.patch(
            "/api/admin/companies/any-co",
            json={"name": "Ghost"},
        )
        assert response.status_code == 401
