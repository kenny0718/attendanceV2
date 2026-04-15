"""Tests for Admin Onboarding API (WP-S1-09C)

POST /api/admin/companies/onboarding
"""

from uuid import uuid4

from app.core.scope import Actor, UserRole
from app.core.dependencies import get_current_actor
from app.modules.tenants.models import Tenant
from app.main import app


def _super_admin():
    return Actor(user_id=uuid4(), role=UserRole.SUPER_ADMIN)


def _company_admin(company_id="dev-tenant"):
    return Actor(
        user_id=uuid4(),
        role=UserRole.COMPANY_USER,
        company_memberships={company_id},
        active_company_id=company_id,
        active_role_id="company_admin",
    )


def _employee(company_id="dev-tenant"):
    return Actor(
        user_id=uuid4(),
        role=UserRole.COMPANY_USER,
        company_memberships={company_id},
        active_company_id=company_id,
        active_role_id="employee",
    )


def _override(client, actor):
    app.dependency_overrides[get_current_actor] = lambda: actor


def _clear():
    app.dependency_overrides.pop(get_current_actor, None)


TEST_ROLE_ID = "company_admin"


def _payload(suffix=None, role_id=TEST_ROLE_ID, tax_id=None, company_fields=None):
    s = suffix or str(uuid4())[:8]
    payload = {
        "company": {
            "id": f"onb-co-{s}",
            "name": f"Onboard Co {s}",
            "tax_id": tax_id,
            "timezone": "Asia/Taipei",
        },
        "initial_user": {
            "display_name": f"Admin User {s}",
            "login_username": f"admin-{s}",
            "password": "SecurePass123",
            "email": f"admin-{s}@example.com",
            "role_id": role_id,
        },
    }
    if company_fields:
        payload["company"].update(company_fields)
    return payload


URL = "/api/admin/companies/onboarding"


class TestAdminOnboarding:

    def test_super_admin_can_onboard_with_tax_id(self, db_session, client):
        payload = _payload(tax_id="24536806")
        _override(client, _super_admin())
        try:
            resp = client.post(URL, json=payload)
        finally:
            _clear()

        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["company"]["id"] == payload["company"]["id"]
        assert data["company"]["tax_id"] == "24536806"
        assert data["membership"]["role_id"] == TEST_ROLE_ID

    def test_onboarding_persists_tax_id(self, db_session, client):
        payload = _payload(tax_id="24536806")
        _override(client, _super_admin())
        try:
            resp = client.post(URL, json=payload)
        finally:
            _clear()

        assert resp.status_code == 201, resp.text
        company_id = resp.json()["company"]["id"]
        tenant = db_session.query(Tenant).filter(Tenant.id == company_id).first()
        assert tenant is not None
        assert tenant.tax_id == "24536806"

    def test_onboarding_persists_company_profile_fields(self, db_session, client):
        payload = _payload(
            tax_id="24536806",
            company_fields={
                "display_name": "展示名稱",
                "owner_name": "負責人測試",
                "registered_address": "台北市中山區南京東路 1 號",
                "contact_address": "台北市中山區南京東路 2 號",
                "contact_phone": "02-12345678",
                "contact_email": "company@example.com",
            },
        )
        _override(client, _super_admin())
        try:
            resp = client.post(URL, json=payload)
        finally:
            _clear()

        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["company"]["display_name"] == "展示名稱"
        assert data["company"]["owner_name"] == "負責人測試"
        assert data["company"]["registered_address"] == "台北市中山區南京東路 1 號"
        assert data["company"]["contact_address"] == "台北市中山區南京東路 2 號"
        assert data["company"]["contact_phone"] == "02-12345678"
        assert data["company"]["contact_email"] == "company@example.com"

    def test_invalid_tax_id_rejected(self, client):
        payload = _payload(tax_id="12345678")
        _override(client, _super_admin())
        try:
            resp = client.post(URL, json=payload)
        finally:
            _clear()

        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert any(err["loc"][-1] == "tax_id" for err in detail)

    def test_duplicate_tax_id_rejected(self, db_session, client):
        db_session.add(Tenant(id="existing-tax", name="Existing Tax", tax_id="24536806", timezone="UTC", is_active=True))
        db_session.commit()

        payload = _payload(tax_id="24536806")
        _override(client, _super_admin())
        try:
            resp = client.post(URL, json=payload)
        finally:
            _clear()

        assert resp.status_code == 409
        assert resp.json()["detail"]["code"] == "DUPLICATE_TAX_ID"

    def test_company_admin_cannot_onboard(self, db_session, client):
        _override(client, _company_admin())
        try:
            resp = client.post(URL, json=_payload())
        finally:
            _clear()
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "SCOPE_FORBIDDEN"

    def test_employee_cannot_onboard(self, db_session, client):
        _override(client, _employee())
        try:
            resp = client.post(URL, json=_payload())
        finally:
            _clear()
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "SCOPE_FORBIDDEN"

    def test_unauthenticated_cannot_onboard(self, client):
        resp = client.post(URL, json=_payload())
        assert resp.status_code == 401

    def test_invalid_role_id_rejected(self, db_session, client):
        payload = _payload(role_id="nonexistent_role_xyz")

        _override(client, _super_admin())
        try:
            resp = client.post(URL, json=payload)
        finally:
            _clear()

        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "INVALID_ROLE"
        tenant = db_session.query(Tenant).filter(Tenant.id == payload["company"]["id"]).first()
        assert tenant is None

    def test_missing_required_fields_rejected(self, db_session, client):
        _override(client, _super_admin())
        try:
            resp = client.post(URL, json={"company": {"id": "x", "name": "X"}})
        finally:
            _clear()
        assert resp.status_code == 422

    def test_short_password_rejected(self, db_session, client):
        payload = _payload()
        payload["initial_user"]["password"] = "abc"
        _override(client, _super_admin())
        try:
            resp = client.post(URL, json=payload)
        finally:
            _clear()
        assert resp.status_code == 422


class TestOnboardingAtomicity:

    def test_duplicate_tax_id_leaves_no_orphan_user(self, client, db_session):
        from app.modules.auth.models import User as _User

        db_session.add(Tenant(id="dup-tax-1", name="Dup Tax", tax_id="24536806", timezone="UTC", is_active=True))
        db_session.commit()
        user_count_before = db_session.query(_User).count()

        payload = _payload(tax_id="24536806")
        _override(client, _super_admin())
        try:
            resp = client.post(URL, json=payload)
        finally:
            _clear()
        assert resp.status_code == 409

        user_count_after = db_session.query(_User).count()
        assert user_count_after == user_count_before

    def test_invalid_role_leaves_no_orphan_user(self, client, db_session):
        from app.modules.auth.models import User as _User

        user_count_before = db_session.query(_User).count()
        payload = _payload(role_id="nonexistent_role_xyz", tax_id="24536806")
        _override(client, _super_admin())
        try:
            resp = client.post(URL, json=payload)
        finally:
            _clear()
        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "INVALID_ROLE"

        user_count_after = db_session.query(_User).count()
        assert user_count_after == user_count_before
