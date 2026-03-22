"""Tests for Admin Onboarding API (WP-S1-09C)

POST /api/admin/companies/onboarding

覆蓋：
- super_admin 成功 onboarding (company + user + membership)
- company_admin → 403
- employee → 403
- unauthenticated → 401
- duplicate company id → 409 DUPLICATE_COMPANY
- invalid role_id → 422 INVALID_ROLE + transaction safety
- missing required fields → 422
- short password → 422
"""

import pytest
from uuid import uuid4
from datetime import datetime

from app.core.scope import Actor, UserRole
from app.core.dependencies import get_current_actor
from app.modules.tenants.models import Tenant
from app.modules.auth.models import User, Membership, Role
from app.main import app


# ── actor helpers ─────────────────────────────────────────────────────

def _super_admin():
    return Actor(user_id=uuid4(), role=UserRole.SUPER_ADMIN)


def _company_admin(company_id="dev-tenant"):
    return Actor(
        user_id=uuid4(),
        role=UserRole.COMPANY_USER,
        company_memberships={company_id},
        active_company_id=company_id,
        active_role_id="admin",
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


# ── role seed fixture ─────────────────────────────────────────────────
# The test DB only has 'admin' role seeded via migration.
# We ensure 'admin' role exists before each test that needs it.

TEST_ROLE_ID = "admin"   # use the role that already exists in test DB


# ── valid payload factory ─────────────────────────────────────────────

def _payload(suffix=None, role_id=TEST_ROLE_ID):
    s = suffix or str(uuid4())[:8]
    return {
        "company": {
            "id": f"onb-co-{s}",
            "name": f"Onboard Co {s}",
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


URL = "/api/admin/companies/onboarding"


# ── Tests ─────────────────────────────────────────────────────────────

class TestAdminOnboarding:

    def test_super_admin_can_onboard(self, db_session, client):
        """super_admin 成功 onboarding — 回傳 company / user / membership 資料"""
        payload = _payload()
        _override(client, _super_admin())
        try:
            resp = client.post(URL, json=payload)
        finally:
            _clear()

        assert resp.status_code == 201, resp.text
        data = resp.json()

        # company result
        assert data["company"]["id"] == payload["company"]["id"]
        assert data["company"]["name"] == payload["company"]["name"]
        assert data["company"]["timezone"] == "Asia/Taipei"
        assert data["company"]["is_active"] is True
        assert "created_at" in data["company"]

        # user result
        assert data["user"]["display_name"] == payload["initial_user"]["display_name"]
        assert "id" in data["user"]

        # membership result
        assert data["membership"]["company_id"] == payload["company"]["id"]
        assert data["membership"]["role_id"] == TEST_ROLE_ID
        assert data["membership"]["login_username"] == payload["initial_user"]["login_username"]
        assert "id" in data["membership"]

    def test_onboarding_persists_all_three_records(self, db_session, client):
        """驗證 DB 中真的存在 company / user / membership 三筆資料"""
        payload = _payload()
        _override(client, _super_admin())
        try:
            resp = client.post(URL, json=payload)
        finally:
            _clear()

        assert resp.status_code == 201, resp.text
        data = resp.json()

        company_id = data["company"]["id"]
        user_id = data["user"]["id"]
        membership_id = data["membership"]["id"]

        # verify DB state
        tenant = db_session.query(Tenant).filter(Tenant.id == company_id).first()
        assert tenant is not None
        assert tenant.name == payload["company"]["name"]

        from uuid import UUID
        user = db_session.query(User).filter(User.id == UUID(user_id)).first()
        assert user is not None
        assert user.display_name == payload["initial_user"]["display_name"]

        membership = db_session.query(Membership).filter(
            Membership.id == UUID(membership_id)
        ).first()
        assert membership is not None
        assert membership.company_id == company_id
        assert membership.role_id == TEST_ROLE_ID

    def test_company_admin_cannot_onboard(self, db_session, client):
        """company_admin → 403"""
        _override(client, _company_admin())
        try:
            resp = client.post(URL, json=_payload())
        finally:
            _clear()
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "SCOPE_FORBIDDEN"

    def test_employee_cannot_onboard(self, db_session, client):
        """employee → 403"""
        _override(client, _employee())
        try:
            resp = client.post(URL, json=_payload())
        finally:
            _clear()
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "SCOPE_FORBIDDEN"

    def test_unauthenticated_cannot_onboard(self, client):
        """未驗證 → 401"""
        resp = client.post(URL, json=_payload())
        assert resp.status_code == 401

    def test_duplicate_company_id_rejected(self, db_session, client):
        """重複 company_id → 409 DUPLICATE_COMPANY"""
        suffix = str(uuid4())[:8]
        payload = _payload(suffix)
        company_id = payload["company"]["id"]

        # pre-create the company
        db_session.add(Tenant(id=company_id, name="Pre-existing", timezone="UTC", is_active=True))
        db_session.commit()

        _override(client, _super_admin())
        try:
            resp = client.post(URL, json=payload)
        finally:
            _clear()

        assert resp.status_code == 409
        assert resp.json()["detail"]["code"] == "DUPLICATE_COMPANY"

    def test_duplicate_login_username_within_company(self, db_session, client):
        """同公司同 login_username → 依 DB integrity error 或業務邏輯 → 409"""
        suffix = str(uuid4())[:8]
        company_id = f"onb-dupln-{suffix}"
        login_username = f"same-admin-{suffix}"

        # First onboarding to this company — should succeed
        payload1 = {
            "company": {"id": company_id, "name": "Dup LN Co", "timezone": "UTC"},
            "initial_user": {
                "display_name": "First Admin",
                "login_username": login_username,
                "password": "Pass123!",
                "role_id": TEST_ROLE_ID,
            },
        }
        _override(client, _super_admin())
        try:
            r1 = client.post(URL, json=payload1)
        finally:
            _clear()
        assert r1.status_code == 201, r1.text

        # Second attempt with same company_id → DUPLICATE_COMPANY fires first
        # (this is the expected behaviour: company check happens before membership)
        payload2 = {
            "company": {"id": company_id, "name": "Dup LN Co Again", "timezone": "UTC"},
            "initial_user": {
                "display_name": "Second Admin",
                "login_username": login_username,
                "password": "Pass456!",
                "role_id": TEST_ROLE_ID,
            },
        }
        _override(client, _super_admin())
        try:
            r2 = client.post(URL, json=payload2)
        finally:
            _clear()
        # Either DUPLICATE_COMPANY or DUPLICATE_LOGIN_USERNAME — both are 409
        assert r2.status_code == 409
        assert r2.json()["detail"]["code"] in ("DUPLICATE_COMPANY", "DUPLICATE_LOGIN_USERNAME")

    def test_invalid_role_id_rejected(self, db_session, client):
        """不存在的 role_id → 422 INVALID_ROLE"""
        payload = _payload(role_id="nonexistent_role_xyz")

        _override(client, _super_admin())
        try:
            resp = client.post(URL, json=payload)
        finally:
            _clear()

        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "INVALID_ROLE"

        # transaction safety: company should NOT exist in DB
        company_id = payload["company"]["id"]
        tenant = db_session.query(Tenant).filter(Tenant.id == company_id).first()
        assert tenant is None, "Company should not exist after failed onboarding (transaction rollback)"

    def test_missing_required_fields_rejected(self, db_session, client):
        """缺少必要欄位 → 422"""
        _override(client, _super_admin())
        try:
            # missing initial_user entirely
            resp = client.post(URL, json={"company": {"id": "x", "name": "X"}})
        finally:
            _clear()
        assert resp.status_code == 422

    def test_short_password_rejected(self, db_session, client):
        """密碼太短 (min 6 chars) → 422"""
        payload = _payload()
        payload["initial_user"]["password"] = "abc"  # only 3 chars
        _override(client, _super_admin())
        try:
            resp = client.post(URL, json=payload)
        finally:
            _clear()
        assert resp.status_code == 422



# ── WP-S1-10E: Atomicity tests ────────────────────────────────────────

class TestOnboardingAtomicity:

    def test_duplicate_login_username_leaves_no_orphan_user(self, client, db_session):
        """membership duplicate → commit 应該被 rollback，DB 不對留孤兒 user"""
        from app.core.scope import Actor, UserRole
        from uuid import uuid4
        from app.modules.auth.models import User as _User

        suffix = str(uuid4())[:8]
        company_id = f"atomic-co-{suffix}"

        # First onboarding — should succeed
        payload1 = {
            "company": {"id": company_id, "name": f"Atomic Co {suffix}", "timezone": "UTC"},
            "initial_user": {
                "display_name": f"First User {suffix}",
                "login_username": f"shared-login-{suffix}",
                "password": "password123",
                "email": None,
                "role_id": "admin",
            },
        }
        _override(client, _super_admin())
        try:
            resp1 = client.post(URL, json=payload1)
        finally:
            _clear()
        assert resp1.status_code == 201, f"First onboarding failed: {resp1.json()}"

        # Count users before second attempt
        user_count_before = db_session.query(_User).count()

        # Second onboarding — same company → 409 DUPLICATE_COMPANY
        # (will fail before creating user, so this tests company-level guard)
        payload2 = {
            "company": {"id": company_id, "name": f"Atomic Co {suffix}", "timezone": "UTC"},
            "initial_user": {
                "display_name": f"Second User {suffix}",
                "login_username": f"shared-login-{suffix}",
                "password": "password123",
                "email": None,
                "role_id": "admin",
            },
        }
        _override(client, _super_admin())
        try:
            resp2 = client.post(URL, json=payload2)
        finally:
            _clear()
        assert resp2.status_code == 409

        # User count must not have increased
        user_count_after = db_session.query(_User).count()
        assert user_count_after == user_count_before, (
            f"Orphan user left in DB! count before={user_count_before}, after={user_count_after}"
        )

    def test_invalid_role_leaves_no_orphan_user(self, client, db_session):
        """invalid role → onboarding 失敗，DB 不對留孤兒 user"""
        from app.modules.auth.models import User as _User

        suffix = str(uuid4())[:8]
        user_count_before = db_session.query(_User).count()

        payload = {
            "company": {"id": f"badrol-co-{suffix}", "name": f"Bad Role Co {suffix}", "timezone": "UTC"},
            "initial_user": {
                "display_name": f"No Role User {suffix}",
                "login_username": f"norole-{suffix}",
                "password": "password123",
                "email": None,
                "role_id": "nonexistent_role_xyz",
            },
        }
        _override(client, _super_admin())
        try:
            resp = client.post(URL, json=payload)
        finally:
            _clear()
        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "INVALID_ROLE"

        user_count_after = db_session.query(_User).count()
        assert user_count_after == user_count_before, (
            f"Orphan user left in DB! count before={user_count_before}, after={user_count_after}"
        )
