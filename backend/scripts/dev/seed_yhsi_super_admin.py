#!/usr/bin/env python3
"""
YHSI Super Admin Seed

DEVELOPMENT USE ONLY. Do NOT run in production.

Creates or reuses a fixed super_admin account for YHSI:
  company_id    : yhsi
  company_name  : YHSI
  login_username: yhsimis
  password      : Yh2028109!  (set ONLY on first user creation; never overwritten)
  role_id       : super_admin

Idempotent: safe to rerun. Will skip any record that already exists.
If Membership exists but role_id != super_admin → aborts with error.

Usage:
  cd /opt/attendance-system/backend
  python scripts/dev/seed_yhsi_super_admin.py
"""

import sys
import os
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.modules.auth.models import User, Membership, Role
from app.modules.tenants.models import Tenant
from app.core.security.password import hash_password

# ---------------------------------------------------------------------------
# Seed configuration
# ---------------------------------------------------------------------------
COMPANY_ID        = "yhsi"
COMPANY_NAME      = "YHSI"
COMPANY_TIMEZONE  = "Asia/Taipei"

LOGIN_USERNAME    = "yhsimis"
PLAIN_PASSWORD    = "Yh2028109!"
DISPLAY_NAME      = "YHSI MIS Admin"
ROLE_ID           = "super_admin"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _status(label: str, created: bool) -> str:
    tag = "CREATED" if created else "EXISTS "
    return f"  [{tag}]  {label}"


def ensure_role(db: Session) -> tuple[Role, bool]:
    existing = db.query(Role).filter(Role.id == ROLE_ID).first()
    if existing:
        return existing, False
    role = Role(
        id=ROLE_ID,
        name="Super Admin",
        description="System-level super admin (platform scope)"
    )
    db.add(role)
    db.flush()
    return role, True


def ensure_tenant(db: Session) -> tuple[Tenant, bool]:
    existing = db.query(Tenant).filter(Tenant.id == COMPANY_ID).first()
    if existing:
        return existing, False
    tenant = Tenant(
        id=COMPANY_ID,
        name=COMPANY_NAME,
        timezone=COMPANY_TIMEZONE,
        is_active=True,
    )
    db.add(tenant)
    db.flush()
    return tenant, True


def ensure_user_and_membership(db: Session) -> tuple[User, Membership, bool, bool, str]:
    """
    Returns: (user, membership, user_created, membership_created, password_status)

    Strategy:
    1. Check if Membership (yhsi, yhsimis) already exists.
       - If exists and role_id != super_admin → ABORT
       - If exists and role_id == super_admin → skip (idempotent)
    2. If Membership does not exist → create User (email=None) + Membership.
       Password is set ONLY on first User creation.
    """
    membership = (
        db.query(Membership)
        .filter(
            Membership.company_id == COMPANY_ID,
            Membership.login_username == LOGIN_USERNAME,
        )
        .first()
    )

    if membership:
        # Safety check: role must be correct
        if membership.role_id != ROLE_ID:
            raise RuntimeError(
                f"ABORT: Membership ({COMPANY_ID}, {LOGIN_USERNAME}) already exists "
                f"with role_id='{membership.role_id}', expected '{ROLE_ID}'. "
                f"Manual review required — seed aborted."
            )
        # Reuse existing user
        user = db.query(User).filter(User.id == membership.user_id).first()
        if not user:
            raise RuntimeError(
                f"ABORT: Membership found but User {membership.user_id} missing — "
                f"data integrity issue. Manual review required."
            )
        return user, membership, False, False, "unchanged (user pre-existed)"

    # Membership does not exist → create User + Membership
    user = User(
        id=uuid.uuid4(),
        display_name=DISPLAY_NAME,
        email=None,            # email intentionally null per audit
        password_hash=hash_password(PLAIN_PASSWORD),
        is_active=True,
        is_otp=False,
        must_change_password=False,
    )
    db.add(user)
    db.flush()

    membership = Membership(
        id=uuid.uuid4(),
        user_id=user.id,
        company_id=COMPANY_ID,
        role_id=ROLE_ID,
        login_username=LOGIN_USERNAME,
        login_email=None,
        is_active=True,
    )
    db.add(membership)
    db.flush()

    return user, membership, True, True, f"initialized to: {PLAIN_PASSWORD}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_seed() -> None:
    db: Session = SessionLocal()
    try:
        print("\n" + "=" * 60)
        print("  YHSI Super Admin Seed — DEVELOPMENT USE ONLY")
        print("=" * 60)

        # Step 1: Role
        print("\n[Role]")
        _, role_created = ensure_role(db)
        print(_status(f"role: {ROLE_ID}", role_created))

        # Step 2: Tenant
        print("\n[Tenant]")
        _, tenant_created = ensure_tenant(db)
        print(_status(f"tenant: {COMPANY_ID} ({COMPANY_NAME})", tenant_created))

        # Step 3: User + Membership
        print("\n[User + Membership]")
        user, membership, user_created, mem_created, pw_status = ensure_user_and_membership(db)
        print(_status(f"user: {DISPLAY_NAME} (id={user.id})", user_created))
        print(_status(
            f"membership: company={COMPANY_ID}, login={LOGIN_USERNAME}, role={ROLE_ID}",
            mem_created
        ))
        print(f"  [PASSWORD]  {pw_status}")

        # Commit
        db.commit()

        print("\n" + "=" * 60)
        print("  Seed completed successfully.")
        print("=" * 60)
        print("\n[Login Credentials — DEVELOPMENT ONLY]")
        print(f"  company_id     : {COMPANY_ID}")
        print(f"  login_username : {LOGIN_USERNAME}")
        print(f"  password       : {PLAIN_PASSWORD}")
        print(f"  role_id        : {ROLE_ID}")
        print(f"  endpoint       : POST /api/internal/auth/login")
        print()

        # Summary table for completion report output
        print("[Seed Status Summary]")
        print(f"  role       : {'CREATED' if role_created else 'EXISTS/REUSED'}")
        print(f"  tenant     : {'CREATED' if tenant_created else 'EXISTS/REUSED'}")
        print(f"  user       : {'CREATED' if user_created else 'EXISTS/REUSED'}")
        print(f"  membership : {'CREATED' if mem_created else 'EXISTS/REUSED'}")
        print(f"  password   : {pw_status}")
        print()

    except RuntimeError as e:
        db.rollback()
        print(f"\n[ABORT] {e}")
        sys.exit(1)
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seed failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
