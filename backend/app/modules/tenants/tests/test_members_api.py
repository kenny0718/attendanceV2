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

    def test_company_admin_can_list_own_company_members(self, client, db_session):
        """company_admin 可查詢 own company members (A1-1)"""
        suffix = str(uuid4())[:8]
        company_id = f"test-co-{suffix}"
        _seed_company(db_session, company_id)

        _override(client, _company_admin(company_id))
        try:
            resp = client.get(f"/api/admin/companies/{company_id}/members")
        finally:
            _clear()

        assert resp.status_code == 200
        assert resp.json()["company_id"] == company_id

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



# ── WP-S1-10D: Create Member tests ───────────────────────────────────

class TestCreateCompanyMember:

    def test_super_admin_success(self, client, db_session):
        suffix = str(uuid4())[:8]
        company_id = f"create-co-{suffix}"
        _seed_company(db_session, company_id)

        _override(client, _super_admin())
        try:
            resp = client.post(
                f"/api/admin/companies/{company_id}/members",
                json={
                    "display_name": f"New User {suffix}",
                    "email": f"newuser-{suffix}@test.example",
                    "login_username": f"newuser-{suffix}",
                    "password": "password123",
                    "role_id": TEST_ROLE_ID,
                },
            )
        finally:
            _clear()

        assert resp.status_code == 201
        data = resp.json()
        assert data["company_id"] == company_id
        assert data["login_username"] == f"newuser-{suffix}"
        assert data["display_name"] == f"New User {suffix}"
        assert data["role_id"] == TEST_ROLE_ID
        assert data["is_active"] is True
        assert "membership_id" in data
        assert "user_id" in data

        from app.modules.auth.models import User as _User, Membership as _Membership
        import uuid as _uuid
        mem = db_session.query(_Membership).filter(
            _Membership.id == _uuid.UUID(data["membership_id"])
        ).first()
        assert mem is not None
        assert mem.company_id == company_id
        assert mem.login_username == f"newuser-{suffix}"

        user = db_session.query(_User).filter(
            _User.id == _uuid.UUID(data["user_id"])
        ).first()
        assert user is not None
        assert user.display_name == f"New User {suffix}"

    def test_super_admin_success_member_appears_in_list(self, client, db_session):
        suffix = str(uuid4())[:8]
        company_id = f"list-after-create-{suffix}"
        _seed_company(db_session, company_id)

        _override(client, _super_admin())
        try:
            client.post(
                f"/api/admin/companies/{company_id}/members",
                json={
                    "display_name": f"Listed User {suffix}",
                    "email": None,
                    "login_username": f"listed-{suffix}",
                    "password": "password123",
                    "role_id": TEST_ROLE_ID,
                },
            )
            list_resp = client.get(f"/api/admin/companies/{company_id}/members")
        finally:
            _clear()

        assert list_resp.status_code == 200
        members = list_resp.json()["members"]
        usernames = [m["login_username"] for m in members]
        assert f"listed-{suffix}" in usernames

    def test_duplicate_login_username_409(self, client, db_session):
        suffix = str(uuid4())[:8]
        company_id = f"dup-co-{suffix}"
        _seed_company(db_session, company_id)
        user = _seed_user(db_session, f"Existing {suffix}")
        _seed_membership(db_session, user.id, company_id, f"dup-user-{suffix}")

        _override(client, _super_admin())
        try:
            resp = client.post(
                f"/api/admin/companies/{company_id}/members",
                json={
                    "display_name": f"Another {suffix}",
                    "email": None,
                    "login_username": f"dup-user-{suffix}",
                    "password": "password123",
                    "role_id": TEST_ROLE_ID,
                },
            )
        finally:
            _clear()

        assert resp.status_code == 409
        assert resp.json()["detail"]["code"] == "DUPLICATE_LOGIN_USERNAME"

    def test_invalid_role_422(self, client, db_session):
        suffix = str(uuid4())[:8]
        company_id = f"role-co-{suffix}"
        _seed_company(db_session, company_id)

        _override(client, _super_admin())
        try:
            resp = client.post(
                f"/api/admin/companies/{company_id}/members",
                json={
                    "display_name": f"User {suffix}",
                    "email": None,
                    "login_username": f"user-{suffix}",
                    "password": "password123",
                    "role_id": "nonexistent_role_xyz",
                },
            )
        finally:
            _clear()

        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "INVALID_ROLE"

    def test_company_not_found_404(self, client):
        _override(client, _super_admin())
        try:
            resp = client.post(
                "/api/admin/companies/nonexistent-xyz/members",
                json={
                    "display_name": "Test",
                    "email": None,
                    "login_username": "testuser",
                    "password": "password123",
                    "role_id": TEST_ROLE_ID,
                },
            )
        finally:
            _clear()

        assert resp.status_code == 404
        assert resp.json()["detail"]["code"] == "COMPANY_NOT_FOUND"

    def test_company_admin_can_create_member_in_own_company(self, client, db_session):
        suffix = str(uuid4())[:8]
        company_id = f"allow-co-{suffix}"
        _seed_company(db_session, company_id)

        _override(client, _company_admin(company_id))
        try:
            resp = client.post(
                f"/api/admin/companies/{company_id}/members",
                json={
                    "display_name": "Test",
                    "email": None,
                    "login_username": f"testuser-{suffix}",
                    "password": "password123",
                    "role_id": TEST_ROLE_ID,
                },
            )
        finally:
            _clear()

        assert resp.status_code == 201

    def test_employee_forbidden_403(self, client, db_session):
        suffix = str(uuid4())[:8]
        company_id = f"emp-co-{suffix}"
        _seed_company(db_session, company_id)

        _override(client, _employee(company_id))
        try:
            resp = client.post(
                f"/api/admin/companies/{company_id}/members",
                json={
                    "display_name": "Test",
                    "email": None,
                    "login_username": "testuser",
                    "password": "password123",
                    "role_id": TEST_ROLE_ID,
                },
            )
        finally:
            _clear()

        assert resp.status_code == 403

    def test_unauthenticated_401(self, client, db_session):
        suffix = str(uuid4())[:8]
        company_id = f"unauth-co-{suffix}"
        _seed_company(db_session, company_id)

        _clear()
        resp = client.post(
            f"/api/admin/companies/{company_id}/members",
            json={
                "display_name": "Test",
                "email": None,
                "login_username": "testuser",
                "password": "password123",
                "role_id": TEST_ROLE_ID,
            },
        )
        assert resp.status_code == 401

    def test_validation_error_short_password_422(self, client, db_session):
        suffix = str(uuid4())[:8]
        company_id = f"val-co-{suffix}"
        _seed_company(db_session, company_id)

        _override(client, _super_admin())
        try:
            resp = client.post(
                f"/api/admin/companies/{company_id}/members",
                json={
                    "display_name": "Test",
                    "email": None,
                    "login_username": "testuser",
                    "password": "123",
                    "role_id": TEST_ROLE_ID,
                },
            )
        finally:
            _clear()

        assert resp.status_code == 422

    def test_validation_error_missing_fields_422(self, client, db_session):
        suffix = str(uuid4())[:8]
        company_id = f"misfield-co-{suffix}"
        _seed_company(db_session, company_id)

        _override(client, _super_admin())
        try:
            resp = client.post(
                f"/api/admin/companies/{company_id}/members",
                json={"display_name": "Test"},
            )
        finally:
            _clear()

        assert resp.status_code == 422



# ── WP-S1-10E: Add Member Atomicity tests ────────────────────────────

class TestAddMemberAtomicity:

    def test_duplicate_login_leaves_no_orphan_user(self, client, db_session):
        """membership duplicate → rollback，DB 不對留孤兒 user"""
        from app.modules.auth.models import User as _User
        import uuid as _uuid

        suffix = str(uuid4())[:8]
        company_id = f"atom-mem-co-{suffix}"
        _seed_company(db_session, company_id)

        # Seed existing member with same login_username
        existing_user = _seed_user(db_session, f"Existing {suffix}")
        _seed_membership(db_session, existing_user.id, company_id, f"dup-login-{suffix}")

        _override(client, _super_admin())
        try:
            resp = client.post(
                f"/api/admin/companies/{company_id}/members",
                json={
                    "display_name": f"New Dup {suffix}",
                    "email": None,
                    "login_username": f"dup-login-{suffix}",  # same as existing
                    "password": "password123",
                    "role_id": TEST_ROLE_ID,
                },
            )
        finally:
            _clear()

        assert resp.status_code == 409
        assert resp.json()["detail"]["code"] == "DUPLICATE_LOGIN_USERNAME"

        # Atomicity check: the user that was flushed (display_name=f"New Dup {suffix}")
        # must NOT exist in DB — the rollback should have removed it.
        # We search by display_name which is unique enough in this test.
        orphan = db_session.query(_User).filter(
            _User.display_name == f"New Dup {suffix}"
        ).first()
        assert orphan is None, f"Orphan user found in DB: id={orphan.id if orphan else None}"

    def test_success_both_user_and_membership_exist(self, client, db_session):
        """success: DB 同時存在 user 和 membership"""
        from app.modules.auth.models import User as _User, Membership as _Membership
        import uuid as _uuid

        suffix = str(uuid4())[:8]
        company_id = f"atom-ok-co-{suffix}"
        _seed_company(db_session, company_id)

        _override(client, _super_admin())
        try:
            resp = client.post(
                f"/api/admin/companies/{company_id}/members",
                json={
                    "display_name": f"Atomic OK {suffix}",
                    "email": f"atomok-{suffix}@test.example",
                    "login_username": f"atomok-{suffix}",
                    "password": "password123",
                    "role_id": TEST_ROLE_ID,
                },
            )
        finally:
            _clear()

        assert resp.status_code == 201
        data = resp.json()

        # Verify both exist in DB
        user = db_session.query(_User).filter(
            _User.id == _uuid.UUID(data["user_id"])
        ).first()
        assert user is not None
        assert user.display_name == f"Atomic OK {suffix}"

        mem = db_session.query(_Membership).filter(
            _Membership.id == _uuid.UUID(data["membership_id"])
        ).first()
        assert mem is not None
        assert mem.company_id == company_id
        assert mem.user_id == _uuid.UUID(data["user_id"])



class TestAuthorizationBoundaryA11:

    def test_company_admin_cross_company_list_members_forbidden(self, client, db_session):
        suffix = str(uuid4())[:8]
        own_company = f"own-co-{suffix}"
        other_company = f"other-co-{suffix}"
        _seed_company(db_session, own_company)
        _seed_company(db_session, other_company)

        _override(client, _company_admin(own_company))
        try:
            resp = client.get(f"/api/admin/companies/{other_company}/members")
        finally:
            _clear()

        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "SCOPE_FORBIDDEN"

    def test_hr_manager_cross_company_create_member_forbidden(self, client, db_session):
        suffix = str(uuid4())[:8]
        own_company = f"own-co-{suffix}"
        other_company = f"other-co-{suffix}"
        _seed_company(db_session, own_company)
        _seed_company(db_session, other_company)

        _override(client, _hr_manager(own_company))
        try:
            resp = client.post(
                f"/api/admin/companies/{other_company}/members",
                json={
                    "display_name": "HR Cross",
                    "email": None,
                    "login_username": f"hrcross-{suffix}",
                    "password": "password123",
                    "role_id": TEST_ROLE_ID,
                },
            )
        finally:
            _clear()

        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "SCOPE_FORBIDDEN"

    def test_super_admin_can_create_member_cross_company(self, client, db_session):
        suffix = str(uuid4())[:8]
        company_id = f"sa-cross-{suffix}"
        _seed_company(db_session, company_id)

        _override(client, _super_admin())
        try:
            resp = client.post(
                f"/api/admin/companies/{company_id}/members",
                json={
                    "display_name": "SA Cross",
                    "email": None,
                    "login_username": f"sacross-{suffix}",
                    "password": "password123",
                    "role_id": TEST_ROLE_ID,
                },
            )
        finally:
            _clear()

        assert resp.status_code == 201
