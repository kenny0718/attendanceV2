from uuid import uuid4

from app.core.dependencies import get_current_actor
from app.core.scope import Actor, UserRole
from app.main import app
from app.modules.auth.models import Membership, Role, User
from app.modules.tenants.models import Tenant


TEST_ROLE_ID = "company_admin"


def _super_admin():
    return Actor(user_id=uuid4(), role=UserRole.SUPER_ADMIN)


def _override(actor):
    app.dependency_overrides[get_current_actor] = lambda: actor


def _clear():
    app.dependency_overrides.pop(get_current_actor, None)


def _seed_role(db_session, role_id: str = TEST_ROLE_ID) -> Role:
    role = db_session.query(Role).filter(Role.id == role_id).first()
    if role is None:
        role = Role(id=role_id, name="Company Admin", description="Test role")
        db_session.add(role)
        db_session.flush()
    return role


def _seed_company(db_session, company_id: str) -> Tenant:
    company = Tenant(id=company_id, name=f"Test Co {company_id}", timezone="UTC", is_active=True)
    db_session.add(company)
    db_session.flush()
    return company


def _seed_user(db_session, display_name: str) -> User:
    import uuid
    from app.core.security.password import hash_password

    user = User(
        id=uuid.uuid4(),
        display_name=display_name,
        email=f"{display_name.lower().replace(' ', '.')}@test.example",
        password_hash=hash_password("testpass123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _seed_membership(db_session, user_id, company_id: str, login_username: str, role_id: str = TEST_ROLE_ID) -> Membership:
    import uuid

    membership = Membership(
        id=uuid.uuid4(),
        user_id=user_id,
        company_id=company_id,
        role_id=role_id,
        login_username=login_username,
        is_active=True,
    )
    db_session.add(membership)
    db_session.flush()
    return membership


def test_list_company_members_includes_uses_schedule(client, db_session):
    suffix = str(uuid4())[:8]
    company_id = f"member-list-{suffix}"
    _seed_role(db_session)
    _seed_company(db_session, company_id)
    user = _seed_user(db_session, f"List User {suffix}")
    membership = _seed_membership(db_session, user.id, company_id, f"list-user-{suffix}")
    membership.uses_schedule = True
    db_session.flush()

    _override(_super_admin())
    try:
        resp = client.get(f"/api/admin/companies/{company_id}/members")
    finally:
        _clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["members"][0]["uses_schedule"] is True


def test_create_company_member_supports_uses_schedule(client, db_session):
    suffix = str(uuid4())[:8]
    company_id = f"member-create-{suffix}"
    _seed_role(db_session)
    _seed_company(db_session, company_id)

    _override(_super_admin())
    try:
        resp = client.post(
            f"/api/admin/companies/{company_id}/members",
            json={
                "display_name": f"Schedule Member {suffix}",
                "email": None,
                "login_username": f"schedule-member-{suffix}",
                "password": "password123",
                "role_id": TEST_ROLE_ID,
                "uses_schedule": True,
            },
        )
    finally:
        _clear()

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["uses_schedule"] is True

    import uuid as _uuid
    membership = db_session.query(Membership).filter(
        Membership.id == _uuid.UUID(data["membership_id"])
    ).first()
    assert membership is not None
    assert membership.uses_schedule is True


def test_update_company_member_can_change_uses_schedule(client, db_session):
    suffix = str(uuid4())[:8]
    company_id = f"member-update-{suffix}"
    _seed_role(db_session)
    _seed_company(db_session, company_id)
    user = _seed_user(db_session, f"Update User {suffix}")
    membership = _seed_membership(db_session, user.id, company_id, f"update-user-{suffix}")

    _override(_super_admin())
    try:
        resp = client.patch(
            f"/api/admin/companies/{company_id}/members/{membership.id}",
            json={"uses_schedule": True},
        )
    finally:
        _clear()

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["uses_schedule"] is True

    db_session.refresh(membership)
    assert membership.uses_schedule is True
