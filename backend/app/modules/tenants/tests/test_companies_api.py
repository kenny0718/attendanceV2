"""Tests for Companies API (WP-S1-09A)

GET  /api/admin/companies  — list all companies (super_admin only)
POST /api/admin/companies  — create company   (super_admin only)
"""

from uuid import uuid4

from app.core.scope import Actor, UserRole
from app.core.dependencies import get_current_actor
from app.modules.auth.models import Membership, User
from app.modules.tenants.models import Tenant
from app.main import app


def _make_super_admin_actor() -> Actor:
    return Actor(user_id=uuid4(), role=UserRole.SUPER_ADMIN)


def _make_company_admin_actor(company_id: str = "dev-tenant") -> Actor:
    return Actor(
        user_id=uuid4(),
        role=UserRole.COMPANY_USER,
        company_memberships={company_id},
        active_company_id=company_id,
        active_role_id="company_admin",
    )


def _make_hr_manager_actor(company_id: str = "dev-tenant") -> Actor:
    return Actor(
        user_id=uuid4(),
        role=UserRole.COMPANY_USER,
        company_memberships={company_id},
        active_company_id=company_id,
        active_role_id="hr_manager",
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
    app.dependency_overrides[get_current_actor] = lambda: actor


def _clear_actor():
    app.dependency_overrides.pop(get_current_actor, None)


class TestListCompanies:

    def test_super_admin_can_list_companies(self, db_session, client):
        db_session.add(Tenant(id="list-co-1", name="List Co 1", tax_id="24536806", timezone="UTC", is_active=True))
        db_session.add(Tenant(id="list-co-2", name="List Co 2", tax_id="12345675", timezone="Asia/Taipei", is_active=True))
        db_session.commit()

        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.get("/api/admin/companies")
        finally:
            _clear_actor()

        assert response.status_code == 200
        data = response.json()
        ids = [c["id"] for c in data["companies"]]
        assert "list-co-1" in ids
        assert "list-co-2" in ids

    def test_list_companies_response_shape(self, db_session, client):
        db_session.add(Tenant(id="shape-co", name="Shape Co", tax_id="24536806", timezone="UTC", is_active=True))
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
        assert co["tax_id"] == "24536806"
        assert "created_at" in co
        assert "display_name" in co
        assert "registered_address" in co

    def test_company_admin_can_list_companies_s11c(self, db_session, client):
        db_session.add(Tenant(id="dev-tenant", name="Dev Tenant", tax_id="24536806", timezone="UTC", is_active=True))
        db_session.add(Tenant(id="other-tenant", name="Other Tenant", tax_id="12345675", timezone="UTC", is_active=True))
        db_session.commit()

        _override_actor(client, _make_company_admin_actor("dev-tenant"))
        try:
            response = client.get("/api/admin/companies")
        finally:
            _clear_actor()

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["companies"][0]["id"] == "dev-tenant"

    def test_hr_manager_can_list_own_company(self, db_session, client):
        db_session.add(Tenant(id="dev-tenant", name="Dev Tenant", tax_id="24536806", timezone="UTC", is_active=True))
        db_session.commit()

        _override_actor(client, _make_hr_manager_actor("dev-tenant"))
        try:
            response = client.get("/api/admin/companies")
        finally:
            _clear_actor()

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["companies"][0]["id"] == "dev-tenant"

    def test_employee_cannot_list_companies(self, db_session, client):
        _override_actor(client, _make_employee_actor())
        try:
            response = client.get("/api/admin/companies")
        finally:
            _clear_actor()

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "SCOPE_FORBIDDEN"

    def test_unauthenticated_cannot_list_companies(self, client):
        response = client.get("/api/admin/companies")
        assert response.status_code == 401


class TestCreateCompany:

    def test_super_admin_can_create_company(self, db_session, client):
        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.post(
                "/api/admin/companies",
                json={
                    "id": "new-co-1",
                    "name": "New Company 1",
                    "tax_id": "24536806",
                    "display_name": "新公司",
                    "owner_name": "王小明",
                    "registered_address": "台北市信義區測試路 1 號",
                    "timezone": "Asia/Taipei",
                },
            )
        finally:
            _clear_actor()

        assert response.status_code == 201
        data = response.json()
        assert data["tax_id"] == "24536806"
        assert data["display_name"] == "新公司"
        assert data["owner_name"] == "王小明"
        assert data["registered_address"] == "台北市信義區測試路 1 號"

    def test_create_company_default_timezone(self, db_session, client):
        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.post(
                "/api/admin/companies",
                json={"id": "tz-default-co", "name": "TZ Default Co", "tax_id": "24536806"},
            )
        finally:
            _clear_actor()

        assert response.status_code == 201
        assert response.json()["timezone"] == "UTC"

    def test_create_company_duplicate_rejected(self, db_session, client):
        db_session.add(Tenant(id="dup-co", name="Dup Co", tax_id="24536806", timezone="UTC", is_active=True))
        db_session.commit()

        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.post(
                "/api/admin/companies",
                json={"id": "dup-co", "name": "Dup Co Again", "tax_id": "12345675"},
            )
        finally:
            _clear_actor()

        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "DUPLICATE_COMPANY"

    def test_create_company_duplicate_tax_id_rejected(self, db_session, client):
        db_session.add(Tenant(id="dup-tax", name="Dup Tax", tax_id="24536806", timezone="UTC", is_active=True))
        db_session.commit()

        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.post(
                "/api/admin/companies",
                json={"id": "dup-tax-2", "name": "Dup Tax Again", "tax_id": "24536806"},
            )
        finally:
            _clear_actor()

        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "DUPLICATE_TAX_ID"

    def test_create_company_invalid_tax_id_rejected(self, db_session, client):
        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.post(
                "/api/admin/companies",
                json={"id": "bad-tax", "name": "Bad Tax", "tax_id": "12345678"},
            )
        finally:
            _clear_actor()

        assert response.status_code == 422

    def test_company_admin_cannot_create_company(self, db_session, client):
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
        response = client.post(
            "/api/admin/companies",
            json={"id": "unauth-co", "name": "Unauth Co"},
        )
        assert response.status_code == 401


class TestCompanyDetail:

    def test_super_admin_can_get_company_detail_with_member_summary(self, db_session, client):
        tenant = Tenant(id="detail-co", name="Detail Co", tax_id="24536806", timezone="UTC", is_active=True)
        db_session.add(tenant)
        db_session.flush()

        user1 = User(id=uuid4(), display_name="Admin A", password_hash="x", is_active=True)
        user2 = User(id=uuid4(), display_name="HR B", password_hash="x", is_active=True)
        db_session.add_all([user1, user2])
        db_session.flush()

        db_session.add_all([
            Membership(id=uuid4(), user_id=user1.id, company_id="detail-co", role_id="company_admin", login_username="admin-a", is_active=True),
            Membership(id=uuid4(), user_id=user2.id, company_id="detail-co", role_id="hr_manager", login_username="hr-b", is_active=False),
        ])
        db_session.commit()

        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.get("/api/admin/companies/detail-co")
        finally:
            _clear_actor()

        assert response.status_code == 200
        data = response.json()
        assert data["company"]["id"] == "detail-co"
        assert data["member_summary"]["admin_count"] == 2
        assert data["member_summary"]["active_admin_count"] == 1
        assert data["member_summary"]["has_company_admin"] is True
        assert data["member_summary"]["has_hr_manager"] is True

    def test_company_admin_can_get_own_company_detail(self, db_session, client):
        db_session.add(Tenant(id="dev-tenant", name="Dev Tenant", timezone="UTC", is_active=True))
        db_session.commit()

        _override_actor(client, _make_company_admin_actor("dev-tenant"))
        try:
            response = client.get("/api/admin/companies/dev-tenant")
        finally:
            _clear_actor()

        assert response.status_code == 200
        assert response.json()["company"]["id"] == "dev-tenant"

    def test_employee_cannot_get_company_detail(self, db_session, client):
        db_session.add(Tenant(id="dev-tenant", name="Dev Tenant", timezone="UTC", is_active=True))
        db_session.commit()

        _override_actor(client, _make_employee_actor("dev-tenant"))
        try:
            response = client.get("/api/admin/companies/dev-tenant")
        finally:
            _clear_actor()

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "SCOPE_FORBIDDEN"


class TestLookupByTaxId:

    def test_super_admin_can_lookup_tax_id_stub_response(self, client):
        _override_actor(client, _make_super_admin_actor())
        try:
            response = client.post("/api/admin/companies/lookup-by-tax-id", json={"tax_id": "24536806"})
        finally:
            _clear_actor()

        assert response.status_code == 200
        data = response.json()
        assert data == {
            "tax_id": "24536806",
            "name": None,
            "owner_name": None,
            "registered_address": None,
            "found": False,
        }

    def test_company_admin_cannot_lookup_tax_id(self, client):
        _override_actor(client, _make_company_admin_actor())
        try:
            response = client.post("/api/admin/companies/lookup-by-tax-id", json={"tax_id": "24536806"})
        finally:
            _clear_actor()

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "SCOPE_FORBIDDEN"
