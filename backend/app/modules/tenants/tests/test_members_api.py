"""Tests for Admin Members API (WP-S1-10B)

GET /api/admin/companies/{company_id}/members

覆蓋：
- super_admin 成功查看 members（含 user + membership 資料）
- company_admin → 403
- employee → 403
- unauthenticated → 401
- company not found → 404
- empty company (no members) → 200 empty list
"""

import pytest
from uuid import uuid4

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


TEST_ROLE_ID = "admin"


# ── DB seed helpers ───────────────────────────────────────────────────

def _seed_company(db, company_id: str) -> Tenant:
    co = Tenant(id=company_id, name=f"Test Co {company_id}", timezone="UTC", is_active=True)
    db.add(co)
    db.flush()
    return co


def _seed_user(db, display_name: str) -> User:
    import uuid
    from app.core.security.password import hash_password
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


def _seed_membership(db, user_id, company_id: str, login_username: str, role_id: str = TEST_ROLE_ID) -> Membership:
    import uuid
    m = Membership(
        id=uuid.uuid4(),
        user_id=user_id,
        company_id=company_id,
        role_id=role_id,
        login_username=login_username,
        is_active=True,
    )
    db.add(m)
    db.flush()
    return m


# ── tests ─────────────────────────────────────────────────────────────

class TestListCompanyMembers:

    def test_super_admin_success_with_member(self, client, db_session):
        """super_admin 查看有 1 個 member 的公司，應得到 200 + 正確資料"""
        suffix = str(uuid4())[:8]
        company_id = f"test-co-{suffix}"

        co = _seed_company(db_session, company_id)
        user = _seed_user(db_session, f"Alice {suffix}")
        mem = _seed_membership(db_session, user.id, company_id, f"alice-{suffix}")

        _override(client, _super_admin())
        try:
            resp = client.get(f"/api/admin/companies/{company_id}/members")
        finally:
            _clear()

        assert resp.status_code == 200
        data = resp.json()
        assert data["company_id"] == company_id
        assert data["total"] == 1
        assert len(data["members"]) == 1

        member = data["members"][0]
        assert member["login_username"] == f"alice-{suffix}"
        assert member["display_name"] == f"Alice {suffix}"
        assert member["role_id"] == TEST_ROLE_ID
        assert member["company_id"] == company_id
        assert member["membership_is_active"] is True
        assert member["user_is_active"] is True
        assert "membership_id" in member
        assert "user_id" in member
        assert "membership_created_at" in member

    def test_super_admin_empty_company(self, client, db_session):
        """公司存在但沒有 member，應得到 200 + 空 list"""
        suffix = str(uuid4())[:8]
        company_id = f"empty-co-{suffix}"
        _seed_company(db_session, company_id)

        _override(client, _super_admin())
        try:
            resp = client.get(f"/api/admin/companies/{company_id}/members")
        finally:
            _clear()

        assert resp.status_code == 200
        data = resp.json()
        assert data["company_id"] == company_id
        assert data["total"] == 0
        assert data["members"] == []

    def test_super_admin_multiple_members(self, client, db_session):
        """公司有多個 member，應全部回傳"""
        suffix = str(uuid4())[:8]
        company_id = f"multi-co-{suffix}"
        _seed_company(db_session, company_id)

        for i in range(3):
            u = _seed_user(db_session, f"User{i} {suffix}")
            _seed_membership(db_session, u.id, company_id, f"user{i}-{suffix}")

        _override(client, _super_admin())
        try:
            resp = client.get(f"/api/admin/companies/{company_id}/members")
        finally:
            _clear()

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["members"]) == 3

    def test_company_not_found(self, client):
        """company 不存在 → 404"""
        _override(client, _super_admin())
        try:
            resp = client.get("/api/admin/companies/nonexistent-co-xyz/members")
        finally:
            _clear()

        assert resp.status_code == 404
        assert resp.json()["detail"]["code"] == "COMPANY_NOT_FOUND"

    def test_company_admin_forbidden(self, client, db_session):
        """company_admin → 403"""
        suffix = str(uuid4())[:8]
        company_id = f"test-co-{suffix}"
        _seed_company(db_session, company_id)

        _override(client, _company_admin(company_id))
        try:
            resp = client.get(f"/api/admin/companies/{company_id}/members")
        finally:
            _clear()

        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "SCOPE_FORBIDDEN"

    def test_employee_forbidden(self, client, db_session):
        """employee → 403"""
        suffix = str(uuid4())[:8]
        company_id = f"test-co-{suffix}"
        _seed_company(db_session, company_id)

        _override(client, _employee(company_id))
        try:
            resp = client.get(f"/api/admin/companies/{company_id}/members")
        finally:
            _clear()

        assert resp.status_code == 403

    def test_unauthenticated(self, client):
        """未登入 → 401"""
        _clear()
        resp = client.get("/api/admin/companies/any-co/members")
        assert resp.status_code == 401
