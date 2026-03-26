"""Tests for Membership Active Toggle API (WP-S1-10C)

PATCH /api/admin/companies/{company_id}/members/{membership_id}/active

覆蓋：
- super_admin 可停用 membership（DB 狀態確認）
- super_admin 可重新啟用 membership（DB 狀態確認）
- company_admin → 403
- employee → 403
- unauthenticated → 401
- company not found → 404
- membership not found → 404
- membership 不屬於該 company → 409
- invalid membership_id (non-UUID) → 422
"""

import pytest
import uuid
from uuid import uuid4

from app.core.scope import Actor, UserRole
from app.core.dependencies import get_current_actor
from app.modules.tenants.models import Tenant
from app.modules.auth.models import User, Membership
from app.main import app
from app.core.security.password import hash_password


# ── actor helpers ─────────────────────────────────────────────────────

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


def _hr_manager(company_id="dev-tenant"):
    return Actor(
        user_id=uuid4(),
        role=UserRole.COMPANY_USER,
        company_memberships={company_id},
        active_company_id=company_id,
        active_role_id="hr_manager",
    )


def _override(client, actor):
    app.dependency_overrides[get_current_actor] = lambda: actor


def _clear():
    app.dependency_overrides.pop(get_current_actor, None)


TEST_ROLE_ID = "admin"


# ── DB seed helpers ───────────────────────────────────────────────────

def _seed_company(db, company_id: str) -> Tenant:
    co = Tenant(id=company_id, name=f"Test Co {company_id}", timezone="UTC", is_active=True)
    db.add(co)
    db.flush()
    return co


def _seed_user(db, display_name: str) -> User:
    u = User(
        id=uuid.uuid4(),
        display_name=display_name,
        email=f"{display_name.lower().replace(' ', '.')}@test.example",
        password_hash=hash_password("testpass123"),
        is_active=True,
    )
    db.add(u)
    db.flush()
    return u


def _seed_membership(
    db, user_id, company_id: str, login_username: str,
    role_id: str = TEST_ROLE_ID, is_active: bool = True
) -> Membership:
    m = Membership(
        id=uuid.uuid4(),
        user_id=user_id,
        company_id=company_id,
        role_id=role_id,
        login_username=login_username,
        is_active=is_active,
    )
    db.add(m)
    db.flush()
    return m


def _patch(client, company_id: str, membership_id: str, is_active: bool):
    return client.patch(
        f"/api/admin/companies/{company_id}/members/{membership_id}/active",
        json={"is_active": is_active},
    )


# ── tests ─────────────────────────────────────────────────────────────

class TestToggleMembershipActive:

    def test_super_admin_deactivate_membership(self, client, db_session):
        """super_admin 停用 membership → 200，DB is_active=False"""
        suffix = str(uuid4())[:8]
        company_id = f"tog-co-{suffix}"
        _seed_company(db_session, company_id)
        user = _seed_user(db_session, f"Bob {suffix}")
        mem = _seed_membership(db_session, user.id, company_id, f"bob-{suffix}", is_active=True)

        _override(client, _super_admin())
        try:
            resp = _patch(client, company_id, str(mem.id), False)
        finally:
            _clear()

        assert resp.status_code == 200
        data = resp.json()
        assert data["is_active"] is False
        assert data["membership_id"] == str(mem.id)
        assert data["company_id"] == company_id

        # Verify DB state
        db_session.refresh(mem)
        assert mem.is_active is False

    def test_super_admin_reactivate_membership(self, client, db_session):
        """super_admin 重新啟用 membership → 200，DB is_active=True"""
        suffix = str(uuid4())[:8]
        company_id = f"tog-co-{suffix}"
        _seed_company(db_session, company_id)
        user = _seed_user(db_session, f"Carol {suffix}")
        mem = _seed_membership(db_session, user.id, company_id, f"carol-{suffix}", is_active=False)

        _override(client, _super_admin())
        try:
            resp = _patch(client, company_id, str(mem.id), True)
        finally:
            _clear()

        assert resp.status_code == 200
        data = resp.json()
        assert data["is_active"] is True

        # Verify DB state
        db_session.refresh(mem)
        assert mem.is_active is True

    def test_company_admin_can_toggle_own_company_membership(self, client, db_session):
        """company_admin 可切換 own company membership (A1-1)"""
        suffix = str(uuid4())[:8]
        company_id = f"tog-co-{suffix}"
        _seed_company(db_session, company_id)
        user = _seed_user(db_session, f"Dave {suffix}")
        mem = _seed_membership(db_session, user.id, company_id, f"dave-{suffix}")

        _override(client, _company_admin(company_id))
        try:
            resp = _patch(client, company_id, str(mem.id), False)
        finally:
            _clear()

        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_employee_forbidden(self, client, db_session):
        """employee → 403"""
        suffix = str(uuid4())[:8]
        company_id = f"tog-co-{suffix}"
        _seed_company(db_session, company_id)
        user = _seed_user(db_session, f"Eve {suffix}")
        mem = _seed_membership(db_session, user.id, company_id, f"eve-{suffix}")

        _override(client, _employee(company_id))
        try:
            resp = _patch(client, company_id, str(mem.id), False)
        finally:
            _clear()

        assert resp.status_code == 403

    def test_unauthenticated(self, client):
        """未登入 → 401"""
        _clear()
        resp = _patch(client, "any-co", str(uuid4()), False)
        assert resp.status_code == 401

    def test_company_not_found(self, client):
        """company 不存在 → 404"""
        _override(client, _super_admin())
        try:
            resp = _patch(client, "nonexistent-co-xyz", str(uuid4()), False)
        finally:
            _clear()

        assert resp.status_code == 404
        assert resp.json()["detail"]["code"] == "COMPANY_NOT_FOUND"

    def test_membership_not_found(self, client, db_session):
        """membership 不存在 → 404"""
        suffix = str(uuid4())[:8]
        company_id = f"tog-co-{suffix}"
        _seed_company(db_session, company_id)

        _override(client, _super_admin())
        try:
            resp = _patch(client, company_id, str(uuid4()), False)
        finally:
            _clear()

        assert resp.status_code == 404
        assert resp.json()["detail"]["code"] == "MEMBERSHIP_NOT_FOUND"

    def test_membership_company_mismatch(self, client, db_session):
        """membership 屬於另一家公司 → 409"""
        suffix = str(uuid4())[:8]
        company_a = f"tog-co-a-{suffix}"
        company_b = f"tog-co-b-{suffix}"
        _seed_company(db_session, company_a)
        _seed_company(db_session, company_b)

        user = _seed_user(db_session, f"Frank {suffix}")
        mem_b = _seed_membership(db_session, user.id, company_b, f"frank-{suffix}")

        _override(client, _super_admin())
        try:
            # Try to toggle mem_b using company_a in URL
            resp = _patch(client, company_a, str(mem_b.id), False)
        finally:
            _clear()

        assert resp.status_code == 409
        assert resp.json()["detail"]["code"] == "MEMBERSHIP_COMPANY_MISMATCH"

    def test_invalid_membership_id(self, client, db_session):
        """非 UUID 格式的 membership_id → 422"""
        suffix = str(uuid4())[:8]
        company_id = f"tog-co-{suffix}"
        _seed_company(db_session, company_id)

        _override(client, _super_admin())
        try:
            resp = _patch(client, company_id, "not-a-uuid", False)
        finally:
            _clear()

        assert resp.status_code == 422



class TestAuthorizationBoundaryA11:

    def test_company_admin_cross_company_toggle_forbidden(self, client, db_session):
        suffix = str(uuid4())[:8]
        own_company = f"own-tog-{suffix}"
        other_company = f"other-tog-{suffix}"
        _seed_company(db_session, own_company)
        _seed_company(db_session, other_company)
        user = _seed_user(db_session, f"Cross {suffix}")
        mem = _seed_membership(db_session, user.id, other_company, f"cross-{suffix}")

        _override(client, _company_admin(own_company))
        try:
            resp = _patch(client, other_company, str(mem.id), False)
        finally:
            _clear()

        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "SCOPE_FORBIDDEN"

    def test_hr_manager_cross_company_toggle_forbidden(self, client, db_session):
        suffix = str(uuid4())[:8]
        own_company = f"own-tog-{suffix}"
        other_company = f"other-tog-{suffix}"
        _seed_company(db_session, own_company)
        _seed_company(db_session, other_company)
        user = _seed_user(db_session, f"Cross HR {suffix}")
        mem = _seed_membership(db_session, user.id, other_company, f"crosshr-{suffix}")

        _override(client, _hr_manager(own_company))
        try:
            resp = _patch(client, other_company, str(mem.id), False)
        finally:
            _clear()

        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "SCOPE_FORBIDDEN"

    def test_super_admin_can_toggle_cross_company(self, client, db_session):
        suffix = str(uuid4())[:8]
        company_id = f"sa-tog-{suffix}"
        _seed_company(db_session, company_id)
        user = _seed_user(db_session, f"SA Toggle {suffix}")
        mem = _seed_membership(db_session, user.id, company_id, f"satog-{suffix}")

        _override(client, _super_admin())
        try:
            resp = _patch(client, company_id, str(mem.id), False)
        finally:
            _clear()

        assert resp.status_code == 200
        assert resp.json()["is_active"] is False
