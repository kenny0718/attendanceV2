#!/usr/bin/env python3
"""
WP-S1-08C — Admin Test Account Seed

DEVELOPMENT USE ONLY. Do NOT run in production.

Creates or reuses the following identities for access-control testing:
  1. super_admin role      (system-level, global)
  2. super_admin user      (no company/membership needed)
  3. dev-tenant company    (test tenant)
  4. company admin user    (membership: dev-tenant / company_admin role)
  5. employee user         (membership: dev-tenant / employee role)

Idempotent: safe to rerun, will skip existing records.

Usage:
  cd /opt/attendance-system/backend
  python scripts/dev/seed_admin_accounts.py
"""

import sys
import os
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — allow running from any cwd
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
# Seed configuration  (change passwords before sharing beyond local dev)
# ---------------------------------------------------------------------------
SUPER_ADMIN_ROLE_ID      = "super_admin"
COMPANY_ADMIN_ROLE_ID    = "company_admin"
EMPLOYEE_ROLE_ID         = "employee"

TENANT_ID                = "dev-tenant"
TENANT_NAME              = "Dev Test Company"
TENANT_TIMEZONE          = "Asia/Taipei"

SUPER_ADMIN_DISPLAY_NAME = "Super Admin"
SUPER_ADMIN_PASSWORD     = "DevSuperAdmin2026!"
SUPER_ADMIN_EMAIL        = "superadmin@system.local"

COMPANY_ADMIN_DISPLAY    = "Company Admin"
COMPANY_ADMIN_USERNAME   = "companyadmin"
COMPANY_ADMIN_PASSWORD   = "DevCompanyAdmin2026!"
COMPANY_ADMIN_EMAIL      = "admin@dev-tenant.local"

EMPLOYEE_DISPLAY         = "Test Employee"
EMPLOYEE_USERNAME        = "employee"
EMPLOYEE_PASSWORD        = "DevEmployee2026!"
EMPLOYEE_EMAIL           = "employee@dev-tenant.local"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _status(label: str, created: bool) -> str:
    return f"[{'CREATED' if created else 'EXISTS ':6}]  {label}"


def ensure_role(db: Session, role_id: str, name: str, description: str) -> tuple[Role, bool]:
    """Return (role, created). Creates only if not found."""
    existing = db.query(Role).filter(Role.id == role_id).first()
    if existing:
        return existing, False
    role = Role(id=role_id, name=name, description=description)
    db.add(role)
    db.flush()
    return role, True


def ensure_tenant(db: Session, tenant_id: str, name: str, timezone: str) -> tuple[Tenant, bool]:
    """Return (tenant, created). Creates only if not found."""
    existing = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if existing:
        return existing, False
    tenant = Tenant(id=tenant_id, name=name, timezone=timezone, is_active=True)
    db.add(tenant)
    db.flush()
    return tenant, True


def ensure_user(
    db: Session,
    display_name: str,
    email: str,
    plain_password: str,
    lookup_email: str,
) -> tuple[User, bool]:
    """Return (user, created). Looks up by email; creates if not found."""
    existing = db.query(User).filter(User.email == lookup_email).first()
    if existing:
        return existing, False
    user = User(
        id=uuid.uuid4(),
        display_name=display_name,
        email=email,
        password_hash=hash_password(plain_password),
        is_active=True,
        is_otp=False,
        must_change_password=False,
    )
    db.add(user)
    db.flush()
    return user, True


def ensure_membership(
    db: Session,
    user_id: uuid.UUID,
    company_id: str,
    role_id: str,
    login_username: str,
    login_email: str | None = None,
) -> tuple[Membership, bool]:
    """Return (membership, created). Looks up by (company_id, login_username)."""
    existing = (
        db.query(Membership)
        .filter(
            Membership.company_id == company_id,
            Membership.login_username == login_username,
        )
        .first()
    )
    if existing:
        return existing, False
    membership = Membership(
        id=uuid.uuid4(),
        user_id=user_id,
        company_id=company_id,
        role_id=role_id,
        login_username=login_username,
        login_email=login_email,
        is_active=True,
    )
    db.add(membership)
    db.flush()
    return membership, True


# ---------------------------------------------------------------------------
# Main seed logic
# ---------------------------------------------------------------------------

def run_seed() -> None:
    db: Session = SessionLocal()
    try:
        print("\n" + "=" * 60)
        print("  WP-S1-08C — Admin Test Account Seed")
        print("  DEVELOPMENT USE ONLY")
        print("=" * 60)

        # ── Step 1: Ensure roles exist ─────────────────────────────
        print("\n[Roles]")
        _, sa_role_created = ensure_role(
            db, SUPER_ADMIN_ROLE_ID, "Super Admin",
            "System-level super admin (platform scope, no company required)"
        )
        print(_status(f"role: {SUPER_ADMIN_ROLE_ID}", sa_role_created))

        _, ca_role_created = ensure_role(
            db, COMPANY_ADMIN_ROLE_ID, "Company Admin",
            "Full access within company"
        )
        print(_status(f"role: {COMPANY_ADMIN_ROLE_ID}", ca_role_created))

        _, emp_role_created = ensure_role(
            db, EMPLOYEE_ROLE_ID, "Employee",
            "Regular employee (can create own attendance)"
        )
        print(_status(f"role: {EMPLOYEE_ROLE_ID}", emp_role_created))

        # ── Step 2: Ensure dev tenant ──────────────────────────────
        print("\n[Tenant]")
        tenant, tenant_created = ensure_tenant(
            db, TENANT_ID, TENANT_NAME, TENANT_TIMEZONE
        )
        print(_status(f"tenant: {TENANT_ID} ({TENANT_NAME})", tenant_created))

        # ── Step 3: super_admin user (NO membership needed) ────────
        print("\n[Super Admin User]")
        sa_user, sa_created = ensure_user(
            db,
            display_name=SUPER_ADMIN_DISPLAY_NAME,
            email=SUPER_ADMIN_EMAIL,
            plain_password=SUPER_ADMIN_PASSWORD,
            lookup_email=SUPER_ADMIN_EMAIL,
        )
        print(_status(f"user: {SUPER_ADMIN_EMAIL} (display: {SUPER_ADMIN_DISPLAY_NAME})", sa_created))
        print(f"         user_id : {sa_user.id}")
        print(f"         NOTE    : super_admin has no Membership (global scope)")
        print(f"         NOTE    : login via direct DB call or future /api/admin/login")

        # ── Step 4: Company admin user + membership ────────────────
        print("\n[Company Admin User]")
        ca_user, ca_created = ensure_user(
            db,
            display_name=COMPANY_ADMIN_DISPLAY,
            email=COMPANY_ADMIN_EMAIL,
            plain_password=COMPANY_ADMIN_PASSWORD,
            lookup_email=COMPANY_ADMIN_EMAIL,
        )
        print(_status(f"user: {COMPANY_ADMIN_EMAIL} (display: {COMPANY_ADMIN_DISPLAY})", ca_created))
        print(f"         user_id : {ca_user.id}")

        ca_membership, ca_mem_created = ensure_membership(
            db,
            user_id=ca_user.id,
            company_id=TENANT_ID,
            role_id=COMPANY_ADMIN_ROLE_ID,
            login_username=COMPANY_ADMIN_USERNAME,
            login_email=COMPANY_ADMIN_EMAIL,
        )
        print(_status(
            f"membership: company_id={TENANT_ID}, login={COMPANY_ADMIN_USERNAME}, role={COMPANY_ADMIN_ROLE_ID}",
            ca_mem_created
        ))

        # ── Step 5: Employee user + membership ─────────────────────
        print("\n[Employee User]")
        emp_user, emp_created = ensure_user(
            db,
            display_name=EMPLOYEE_DISPLAY,
            email=EMPLOYEE_EMAIL,
            plain_password=EMPLOYEE_PASSWORD,
            lookup_email=EMPLOYEE_EMAIL,
        )
        print(_status(f"user: {EMPLOYEE_EMAIL} (display: {EMPLOYEE_DISPLAY})", emp_created))
        print(f"         user_id : {emp_user.id}")

        emp_membership, emp_mem_created = ensure_membership(
            db,
            user_id=emp_user.id,
            company_id=TENANT_ID,
            role_id=EMPLOYEE_ROLE_ID,
            login_username=EMPLOYEE_USERNAME,
            login_email=EMPLOYEE_EMAIL,
        )
        print(_status(
            f"membership: company_id={TENANT_ID}, login={EMPLOYEE_USERNAME}, role={EMPLOYEE_ROLE_ID}",
            emp_mem_created
        ))

        # ── Commit all ─────────────────────────────────────────────
        db.commit()
        print("\n" + "=" * 60)
        print("  Seed completed successfully.")
        print("=" * 60)

        # ── Summary ───────────────────────────────────────────────
        print("\n[Login Credentials — DEVELOPMENT ONLY]")
        print()
        print("  Super Admin (system scope, no company login):")
        print(f"    email    : {SUPER_ADMIN_EMAIL}")
        print(f"    password : {SUPER_ADMIN_PASSWORD}")
        print(f"    note     : cannot login via /api/internal/auth/login")
        print(f"               (no Membership — needs super_admin login endpoint)")
        print()
        print(f"  Company Admin (tenant: {TENANT_ID}):")
        print(f"    company_id : {TENANT_ID}")
        print(f"    username   : {COMPANY_ADMIN_USERNAME}")
        print(f"    password   : {COMPANY_ADMIN_PASSWORD}")
        print(f"    role_id    : {COMPANY_ADMIN_ROLE_ID}")
        print()
        print(f"  Employee (tenant: {TENANT_ID}):")
        print(f"    company_id : {TENANT_ID}")
        print(f"    username   : {EMPLOYEE_USERNAME}")
        print(f"    password   : {EMPLOYEE_PASSWORD}")
        print(f"    role_id    : {EMPLOYEE_ROLE_ID}")
        print()

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
