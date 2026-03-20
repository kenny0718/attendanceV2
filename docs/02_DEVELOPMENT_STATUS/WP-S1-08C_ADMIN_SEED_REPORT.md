# WP-S1-08C — Admin Test Account / Seed Report

**Date**: 2026-03-20  
**Status**: COMPLETE  
**Type**: Development seed — READ-ONLY audit verified, no frontend/API/route changes

---

## Summary

Implemented a minimal, idempotent development seed script that creates four
test identities required for access-control testing in WP-S1-08B and WP-S1-09A.

The script reuses all existing backend infrastructure:
- `app.modules.auth.models` (User, Membership, Role)
- `app.modules.tenants.models` (Tenant)
- `app.core.security.password.hash_password` (bcrypt)
- `app.core.database.SessionLocal` (DB connection)

No new models, services, or API endpoints were created.

---

## Files Changed

| File | Purpose | New / Modified |
|------|---------|---------------|
| `backend/scripts/__init__.py` | Package marker | New (empty) |
| `backend/scripts/dev/__init__.py` | Package marker | New (empty) |
| `backend/scripts/dev/seed_admin_accounts.py` | Main seed script | New |
| `docs/02_DEVELOPMENT_STATUS/WP-S1-08C_ADMIN_SEED_REPORT.md` | This report | New |

**No frontend files changed.**  
**No API endpoints added.**  
**No route guard changes.**

---

## How to Run

```bash
cd /opt/attendance-system/backend
python scripts/dev/seed_admin_accounts.py
```

### Prerequisites
- PostgreSQL running at `127.0.0.1:5432`
- Database `attendance_db` exists and schema is up to date (`alembic upgrade head`)
- Python venv activated (or PYTHONPATH set to backend dir)

### Rerun behaviour
Fully idempotent. On every rerun:
- Existing records print `[EXISTS ]`
- Missing records print `[CREATED]`
- No duplicates are ever created

---

## Seeded Identities

### 1. super_admin Role

| Field | Value |
|-------|-------|
| role_id | `super_admin` |
| name | Super Admin |
| scope | Global / system-level (no company_id) |
| seeded by migration | ❌ Not in original migration — added by seed |

---

### 2. Test Tenant

| Field | Value |
|-------|-------|
| tenant_id | `dev-tenant` |
| name | Dev Test Company |
| timezone | Asia/Taipei |
| is_active | true |

---

### 3. Super Admin User

| Field | Value |
|-------|-------|
| email | `superadmin@system.local` |
| display_name | Super Admin |
| password | `DevSuperAdmin2026!` |
| user_id | `b806de78-ed61-4b8d-85d4-659f66a3ac1c` |
| Membership | ❌ None — super_admin is global scope |
| Platform role | `super_admin` |

**Login note**: Cannot use `POST /api/internal/auth/login` because that endpoint
requires `company_id + login_username` via Membership lookup.
A dedicated super_admin login endpoint (WP-S1-09A scope) is required.
For testing JWT-level super_admin access, a JWT can be manually minted
using `app.core.security.jwt.create_access_token`.

---

### 4. Company Admin User

| Field | Value |
|-------|-------|
| company_id | `dev-tenant` |
| login_username | `companyadmin` |
| password | `DevCompanyAdmin2026!` |
| display_name | Company Admin |
| email | `admin@dev-tenant.local` |
| user_id | `7d642221-cf3f-4ee8-8472-f154eb2d8c61` |
| role_id | `company_admin` |
| Platform UserRole | `COMPANY_USER` → `is_admin() = True` |

**Login**:
```json
POST /api/internal/auth/login
{
  "company_id": "dev-tenant",
  "login_username": "companyadmin",
  "password": "DevCompanyAdmin2026!"
}
```

---

### 5. Employee User

| Field | Value |
|-------|-------|
| company_id | `dev-tenant` |
| login_username | `employee` |
| password | `DevEmployee2026!` |
| display_name | Test Employee |
| email | `employee@dev-tenant.local` |
| user_id | `7d7a17cc-2b53-4abe-89bd-90c818f5c34f` |
| role_id | `employee` |
| Platform UserRole | `COMPANY_USER` → `is_admin() = False`, `is_employee() = True` |

**Login**:
```json
POST /api/internal/auth/login
{
  "company_id": "dev-tenant",
  "login_username": "employee",
  "password": "DevEmployee2026!"
}
```

---

## Idempotency Check

Each identity uses lookup-first logic before insert:

| Identity | Lookup Key |
|---------|------------|
| Role | `roles.id` |
| Tenant | `tenants.id` |
| User | `users.email` (unique per seeded identity) |
| Membership | `(company_id, login_username)` UNIQUE constraint |

Second run output (verified 2026-03-20):
```
[EXISTS ]  role: super_admin
[EXISTS ]  role: company_admin
[EXISTS ]  role: employee
[EXISTS ]  tenant: dev-tenant (Dev Test Company)
[EXISTS ]  user: superadmin@system.local (display: Super Admin)
[EXISTS ]  user: admin@dev-tenant.local (display: Company Admin)
[EXISTS ]  membership: company_id=dev-tenant, login=companyadmin, role=company_admin
[EXISTS ]  user: employee@dev-tenant.local (display: Test Employee)
[EXISTS ]  membership: company_id=dev-tenant, login=employee, role=employee
  Seed completed successfully.
```

---

## Validation

### Role scope correctness
- `super_admin` role created in `roles` table with no `company_id` (global)
- Backend `_map_role_id_to_user_role()` in `dependencies.py` maps `super_admin` → `UserRole.SUPER_ADMIN`
- `Actor.is_super_admin()` returns `True` for JWT with `role_id: super_admin`
- `Actor.has_active_company()` returns `True` for super_admin without membership

### Company admin scope correctness
- Membership links `company_admin` role to `dev-tenant`
- `_map_role_id_to_user_role()` maps `company_admin` → `UserRole.COMPANY_USER`
- `Actor.active_role_id = "company_admin"` → `Actor.is_admin() = True`
- `ScopeChecker.assert_company_scope()` passes for `dev-tenant`

### Employee scope correctness
- Membership links `employee` role to `dev-tenant`
- `Actor.active_role_id = "employee"` → `Actor.is_employee() = True`, `is_admin() = False`
- Cannot access admin-only endpoints after WP-S1-08B is implemented

### Login verification
- Company admin and employee can log in via `POST /api/internal/auth/login`
- super_admin cannot log in via current login endpoint (no Membership by design)
- This is expected behaviour documented in WP-S1-08A audit (R4 / G6)

---

## Test Purpose of Each Account

| Account | Test Purpose |
|---------|--------------|
| super_admin | Verify platform-level access; future `/api/admin/*` endpoint testing |
| companyadmin | Verify admin-level access to `/schedule`, `/attendance/reports/*`, admin UI |
| employee | Verify restricted access — should be blocked from admin routes after WP-S1-08B |

---

## Assumptions and Limitations

1. **super_admin cannot login via `/api/internal/auth/login`** — this endpoint requires Membership. A super_admin login path belongs to WP-S1-09A scope.
2. **Passwords are hardcoded for development** — must not be used in staging/production.
3. **Script connects to `attendance_db` (production DB URL from config)** — do not run against production.
4. **`user_id` values are stable** — recorded above; if DB is wiped and reseeded, new UUIDs will be generated.
5. **`super_admin` role was not in original migration** — seed adds it. A future migration should include it formally.

---

## Out of Scope Confirmed

- ❌ No frontend files changed
- ❌ No API endpoints added
- ❌ No route guard changes
- ❌ No auth redesign
- ❌ No role model redesign
- ❌ No admin UI created
- ❌ No new business logic layer added

---

## Next Steps

| Ticket | Dependency on this seed |
|--------|------------------------|
| WP-S1-08B — Route Access Control | Use `companyadmin` and `employee` to verify route guards |
| WP-S1-09A — Tenant/Customer Creation API | Use `super_admin` JWT to test new admin endpoints |
