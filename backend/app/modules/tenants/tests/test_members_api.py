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


# ── S1-13A1: PATCH /{company_id}/members/{membership_id} ──────────────────────────────────────────────

def _seed_role(db, role_id: str) -> None:
    """Ensure role exists (required by FK constraint)"""
    from app.modules.auth.models import Role
    existing = db.query(Role).filter(Role.id == role_id).first()
    if not existing:
        r = Role(id=role_id, name=role_id.replace("_", " ").title())
        db.add(r)
        db.flush()


class TestUpdateMember:
    """PATCH /api/admin/companies/{company_id}/members/{membership_id} (S1-13A1)"""

    def test_super_admin_can_update_display_name(self, client, db_session):
        suffix = str(uuid4())[:8]
        company_id = f"upd-co-{suffix}"
        _seed_company(db_session, company_id)
        _seed_role(db_session, "employee")
        user = _seed_user(db_session, f"OldName {suffix}")
        membership = _seed_membership(db_session, user.id, company_id, f"user-{suffix}", role_id="employee")
        db_session.commit()

        _override(client, _super_admin())
        try:
            resp = client.patch(
                f"/api/admin/companies/{company_id}/members/{membership.id}",
                json={"display_name": "NewName"},
            )
        finally:
            _clear()

        assert resp.status_code == 200, resp.json()
        assert resp.json()["display_name"] == "NewName"
        assert resp.json()["membership_id"] == str(membership.id)

    def test_super_admin_can_update_role_id(self, client, db_session):
        suffix = str(uuid4())[:8]
        company_id = f"upd-role-{suffix}"
        _seed_company(db_session, company_id)
        _seed_role(db_session, "employee")
        _seed_role(db_session, "hr_manager")
        user = _seed_user(db_session, f"RoleUser {suffix}")
        membership = _seed_membership(db_session, user.id, company_id, f"roleuser-{suffix}", role_id="employee")
        db_session.commit()

        _override(client, _super_admin())
        try:
            resp = client.patch(
                f"/api/admin/companies/{company_id}/members/{membership.id}",
                json={"display_name": f"RoleUser {suffix}", "role_id": "hr_manager"},
            )
        finally:
            _clear()

        assert resp.status_code == 200, resp.json()
        assert resp.json()["role_id"] == "hr_manager"

    def test_invalid_role_id_returns_422(self, client, db_session):
        suffix = str(uuid4())[:8]
        company_id = f"upd-inv-{suffix}"
        _seed_company(db_session, company_id)
        _seed_role(db_session, "employee")
        user = _seed_user(db_session, f"InvRole {suffix}")
        membership = _seed_membership(db_session, user.id, company_id, f"inv-{suffix}", role_id="employee")
        db_session.commit()

        _override(client, _super_admin())
        try:
            resp = client.patch(
                f"/api/admin/companies/{company_id}/members/{membership.id}",
                json={"display_name": "x", "role_id": "nonexistent_role_xyz"},
            )
        finally:
            _clear()

        assert resp.status_code == 422, resp.json()
        assert resp.json()["detail"]["code"] == "INVALID_ROLE"

    def test_membership_not_found_returns_404(self, client, db_session):
        suffix = str(uuid4())[:8]
        company_id = f"upd-nf-{suffix}"
        _seed_company(db_session, company_id)
        db_session.commit()

        _override(client, _super_admin())
        try:
            import uuid as _u
            resp = client.patch(
                f"/api/admin/companies/{company_id}/members/{_u.uuid4()}",
                json={"display_name": "x"},
            )
        finally:
            _clear()

        assert resp.status_code == 404, resp.json()
        assert resp.json()["detail"]["code"] == "MEMBERSHIP_NOT_FOUND"

    def test_no_fields_returns_422(self, client, db_session):
        suffix = str(uuid4())[:8]
        company_id = f"upd-empty-{suffix}"
        _seed_company(db_session, company_id)
        _seed_role(db_session, "employee")
        user = _seed_user(db_session, f"Empty {suffix}")
        membership = _seed_membership(db_session, user.id, company_id, f"empty-{suffix}", role_id="employee")
        db_session.commit()

        _override(client, _super_admin())
        try:
            resp = client.patch(
                f"/api/admin/companies/{company_id}/members/{membership.id}",
                json={},
            )
        finally:
            _clear()

        assert resp.status_code == 422, resp.json()
        assert resp.json()["detail"]["code"] == "NO_FIELDS_TO_UPDATE"

    def test_company_admin_cross_company_forbidden(self, client, db_session):
        suffix = str(uuid4())[:8]
        company_id = f"upd-other-{suffix}"
        _seed_company(db_session, company_id)
        _seed_role(db_session, "employee")
        user = _seed_user(db_session, f"OtherUser {suffix}")
        membership = _seed_membership(db_session, user.id, company_id, f"other-{suffix}", role_id="employee")
        db_session.commit()

        _override(client, _company_admin("dev-tenant"))
        try:
            resp = client.patch(
                f"/api/admin/companies/{company_id}/members/{membership.id}",
                json={"display_name": "Hacked"},
            )
        finally:
            _clear()

        assert resp.status_code == 403, resp.json()
        assert resp.json()["detail"]["code"] == "SCOPE_FORBIDDEN"


# ── S1-13A2: login_username edit ──────────────────────────────────────────────

class TestUpdateMemberUsername:
    """PATCH /{company_id}/members/{membership_id} — login_username (S1-13A2)

    Covers:
    - success: can update login_username
    - same company duplicate -> 409 DUPLICATE_LOGIN_USERNAME
    - different company same name -> allowed (200)
    - display_name only (no login_username) still works (A1 regression)
    """

    def test_super_admin_can_update_login_username(self, client, db_session):
        """super_admin can update login_username to a new unique value"""
        suffix = str(uuid4())[:8]
        company_id = f"uname-ok-{suffix}"
        _seed_company(db_session, company_id)
        _seed_role(db_session, "employee")
        user = _seed_user(db_session, f"UsernameUser {suffix}")
        membership = _seed_membership(db_session, user.id, company_id, f"oldname-{suffix}", role_id="employee")
        db_session.commit()

        _override(client, _super_admin())
        try:
            resp = client.patch(
                f"/api/admin/companies/{company_id}/members/{membership.id}",
                json={"display_name": f"UsernameUser {suffix}", "login_username": f"newname-{suffix}"},
            )
        finally:
            _clear()

        assert resp.status_code == 200, resp.json()
        assert resp.json()["login_username"] == f"newname-{suffix}"

    def test_same_company_duplicate_username_returns_409(self, client, db_session):
        """Duplicate login_username within same company -> 409 DUPLICATE_LOGIN_USERNAME"""
        suffix = str(uuid4())[:8]
        company_id = f"uname-dup-{suffix}"
        _seed_company(db_session, company_id)
        _seed_role(db_session, "employee")
        # user1: will try to take user2's username
        user1 = _seed_user(db_session, f"User1 {suffix}")
        mem1 = _seed_membership(db_session, user1.id, company_id, f"user1-{suffix}", role_id="employee")
        # user2: existing username
        user2 = _seed_user(db_session, f"User2 {suffix}")
        _seed_membership(db_session, user2.id, company_id, f"user2-{suffix}", role_id="employee")
        db_session.commit()

        _override(client, _super_admin())
        try:
            resp = client.patch(
                f"/api/admin/companies/{company_id}/members/{mem1.id}",
                json={"display_name": f"User1 {suffix}", "login_username": f"user2-{suffix}"},
            )
        finally:
            _clear()

        assert resp.status_code == 409, resp.json()
        assert resp.json()["detail"]["code"] == "DUPLICATE_LOGIN_USERNAME"

    def test_different_company_same_username_allowed(self, client, db_session):
        """Same login_username in different company should be allowed"""
        suffix = str(uuid4())[:8]
        company_a = f"uname-ca-{suffix}"
        company_b = f"uname-cb-{suffix}"
        _seed_company(db_session, company_a)
        _seed_company(db_session, company_b)
        _seed_role(db_session, "employee")
        shared_name = f"shared-{suffix}"

        # user in company_b already has the shared name
        user_b = _seed_user(db_session, f"UserB {suffix}")
        _seed_membership(db_session, user_b.id, company_b, shared_name, role_id="employee")

        # user in company_a wants to use the same login_username
        user_a = _seed_user(db_session, f"UserA {suffix}")
        mem_a = _seed_membership(db_session, user_a.id, company_a, f"old-{suffix}", role_id="employee")
        db_session.commit()

        _override(client, _super_admin())
        try:
            resp = client.patch(
                f"/api/admin/companies/{company_a}/members/{mem_a.id}",
                json={"display_name": f"UserA {suffix}", "login_username": shared_name},
            )
        finally:
            _clear()

        assert resp.status_code == 200, resp.json()
        assert resp.json()["login_username"] == shared_name

    def test_display_name_only_no_login_username_regression(self, client, db_session):
        """A1 regression: display_name only patch still works without login_username"""
        suffix = str(uuid4())[:8]
        company_id = f"uname-reg-{suffix}"
        _seed_company(db_session, company_id)
        _seed_role(db_session, "employee")
        user = _seed_user(db_session, f"OldDisplay {suffix}")
        membership = _seed_membership(db_session, user.id, company_id, f"reguser-{suffix}", role_id="employee")
        db_session.commit()

        _override(client, _super_admin())
        try:
            resp = client.patch(
                f"/api/admin/companies/{company_id}/members/{membership.id}",
                json={"display_name": "NewDisplay"},
            )
        finally:
            _clear()

        assert resp.status_code == 200, resp.json()
        data = resp.json()
        assert data["display_name"] == "NewDisplay"
        # login_username must remain unchanged
        assert data["login_username"] == f"reguser-{suffix}"


# ── S1-13A3: PATCH /{company_id}/members/{membership_id}/password ─────────────

class TestResetMemberPassword:
    """PATCH /api/admin/companies/{company_id}/members/{membership_id}/password (S1-13A3)

    Covers:
    - super_admin success: password updated and hash is valid
    - short password (<6 chars) rejected with 422
    - non-admin (employee) forbidden (403)
    - cross-company forbidden (403)
    - verify new hash with verify_password
    - A1/A2 update flow not affected (checked implicitly by TestUpdateMember passing)
    """

    def test_super_admin_can_reset_password(self, client, db_session):
        """super_admin can reset a member password; new hash verifies correctly"""
        from app.core.security.password import verify_password
        suffix = str(uuid4())[:8]
        company_id = f"pwd-ok-{suffix}"
        _seed_company(db_session, company_id)
        _seed_role(db_session, "employee")
        user = _seed_user(db_session, f"PwdUser {suffix}")
        membership = _seed_membership(db_session, user.id, company_id, f"pwduser-{suffix}", role_id="employee")
        db_session.commit()

        old_hash = user.password_hash

        _override(client, _super_admin())
        try:
            resp = client.patch(
                f"/api/admin/companies/{company_id}/members/{membership.id}/password",
                json={"new_password": "newpass123"},
            )
        finally:
            _clear()

        assert resp.status_code == 200, resp.json()
        data = resp.json()
        # Response must NOT contain password or hash
        assert "password" not in data
        assert "password_hash" not in data
        assert "hash" not in str(data)
        assert data["membership_id"] == str(membership.id)

        # Verify hash actually changed and new password verifies
        db_session.refresh(user)
        assert user.password_hash != old_hash, "password_hash should have changed"
        assert verify_password("newpass123", user.password_hash), "new password should verify"

    def test_short_password_rejected(self, client, db_session):
        """Password shorter than 6 chars must be rejected (422)"""
        suffix = str(uuid4())[:8]
        company_id = f"pwd-short-{suffix}"
        _seed_company(db_session, company_id)
        _seed_role(db_session, "employee")
        user = _seed_user(db_session, f"ShortPwd {suffix}")
        membership = _seed_membership(db_session, user.id, company_id, f"short-{suffix}", role_id="employee")
        db_session.commit()

        _override(client, _super_admin())
        try:
            resp = client.patch(
                f"/api/admin/companies/{company_id}/members/{membership.id}/password",
                json={"new_password": "abc"},
            )
        finally:
            _clear()

        assert resp.status_code == 422, resp.json()

    def test_employee_cannot_reset_password(self, client, db_session):
        """Regular employee must be forbidden (403)"""
        suffix = str(uuid4())[:8]
        company_id = f"pwd-emp-{suffix}"
        _seed_company(db_session, company_id)
        _seed_role(db_session, "employee")
        user = _seed_user(db_session, f"EmpUser {suffix}")
        membership = _seed_membership(db_session, user.id, company_id, f"emp-{suffix}", role_id="employee")
        db_session.commit()

        _override(client, _employee(company_id))
        try:
            resp = client.patch(
                f"/api/admin/companies/{company_id}/members/{membership.id}/password",
                json={"new_password": "newpass123"},
            )
        finally:
            _clear()

        assert resp.status_code == 403, resp.json()

    def test_company_admin_cross_company_forbidden(self, client, db_session):
        """company_admin cannot reset password of member in different company"""
        suffix = str(uuid4())[:8]
        company_id = f"pwd-cross-{suffix}"
        _seed_company(db_session, company_id)
        _seed_role(db_session, "employee")
        user = _seed_user(db_session, f"CrossUser {suffix}")
        membership = _seed_membership(db_session, user.id, company_id, f"cross-{suffix}", role_id="employee")
        db_session.commit()

        _override(client, _company_admin("dev-tenant"))
        try:
            resp = client.patch(
                f"/api/admin/companies/{company_id}/members/{membership.id}/password",
                json={"new_password": "newpass123"},
            )
        finally:
            _clear()

        assert resp.status_code == 403, resp.json()
        assert resp.json()["detail"]["code"] == "SCOPE_FORBIDDEN"
