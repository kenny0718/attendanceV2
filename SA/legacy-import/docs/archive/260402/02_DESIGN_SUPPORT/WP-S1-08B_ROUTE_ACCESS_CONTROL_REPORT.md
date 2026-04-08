# WP-S1-08B — Frontend Route Access Control Report

**Date**: 2026-03-20
**Status**: COMPLETE
**Type**: Frontend-only — no backend, no API, no seed, no auth redesign

---

## Summary

Implemented explicit frontend route access control for `/schedule` and `/admin`.

- Added `isCompanyAdmin` and `isSuperAdmin` getters to `stores/auth.js`
  using exact role ID string comparison (no broad matching)
- Added `/admin` route definition pointing to existing `Admin.vue`
- Added `requiresCompanyAdmin` and `requiresSuperAdmin` meta flags
- Extended `beforeEach` guard in `router/index.js` to enforce per-route role policy
- `company_admin` and `super_admin` are treated as distinct, non-equivalent roles

---

## Pre-Implementation Findings

### 1. Exact frontend role value shape

After login, the backend returns:
```json
{ "role": { "id": "company_admin", "name": "Company Admin" } }
```
The auth store saves `role` as the full object.
The `userRole` getter returns `state.role?.id` (a string).

The seeded company admin will have `role.id === "company_admin"` after login.
The seeded employee will have `role.id === "employee"` after login.

### 2. Seeded company admin mapping

Seeded identity: `login_username=companyadmin`, `role_id=company_admin` (DB)
Frontend after login: `authStore.userRole === "company_admin"` ✅ maps correctly

### 3. Whether /admin route existed before changes

`/admin` route did **NOT** exist in `router/index.js` before this ticket.
`Admin.vue` existed but was unreachable via router. Confirmed by WP-S1-08A audit (R1).

### 4. Whether /schedule was requiresAuth-only before changes

`/schedule` had only `meta: { requiresAuth: true }` — no role check.
Any authenticated user (including employee) could access it. Confirmed by WP-S1-08A audit (R5).

---

## Files Changed

| File | Change | Purpose |
|------|--------|---------|
| `frontend/src/stores/auth.js` | Added `isCompanyAdmin` and `isSuperAdmin` getters | Explicit, exact role checks for route guards |
| `frontend/src/router/index.js` | Added `/admin` route; added `requiresCompanyAdmin`/`requiresSuperAdmin` meta; extended `beforeEach` | Enforce access policy per route |

**No other files changed.**

---

## Access Rules Implemented

### /schedule

```
meta: { requiresAuth: true, requiresCompanyAdmin: true }

Guard logic:
  if (to.meta.requiresCompanyAdmin) {
    if (!authStore.isCompanyAdmin) → next('/')
  }

isCompanyAdmin = state.role?.id === 'company_admin'  // exact match only
```

| User | Result |
|------|--------|
| Unauthenticated | Caught by `requiresAuth` check → redirect `/login` |
| `employee` (role.id = "employee") | `isCompanyAdmin` = false → redirect `/` |
| `company_admin` (role.id = "company_admin") | `isCompanyAdmin` = true → access allowed |
| `super_admin` (role.id = "super_admin") | `isCompanyAdmin` = false → redirect `/` |

### /admin

```
meta: { requiresAuth: true, requiresSuperAdmin: true }

Guard logic:
  if (to.meta.requiresSuperAdmin) {
    if (!authStore.isSuperAdmin) → next('/')
  }

isSuperAdmin = state.role?.id === 'super_admin'  // exact match only
```

| User | Result |
|------|--------|
| Unauthenticated | Caught by `requiresAuth` check → redirect `/login` |
| `employee` | `isSuperAdmin` = false → redirect `/` |
| `company_admin` | `isSuperAdmin` = false → redirect `/` |
| `super_admin` | `isSuperAdmin` = true → access allowed |

---

## Validation

### Company admin (role.id = "company_admin")
- `/schedule`: ✅ isCompanyAdmin = true → allowed
- `/admin`: ✅ isSuperAdmin = false → redirect `/`

### Employee (role.id = "employee")
- `/schedule`: ✅ isCompanyAdmin = false → redirect `/`
- `/admin`: ✅ isSuperAdmin = false → redirect `/`

### Unauthenticated
- `/schedule`: ✅ requiresAuth + !isAuthenticated → redirect `/login`
- `/admin`: ✅ requiresAuth + !isAuthenticated → redirect `/login`

### Super admin (role.id = "super_admin")
- `/admin`: ✅ isSuperAdmin = true → allowed (once login is possible)
- `/schedule`: ✅ isCompanyAdmin = false → redirect `/` (correct — no tenant context)
- **Limitation**: super_admin cannot login via `POST /api/internal/auth/login`
  because this endpoint requires `company_id + login_username` via Membership.
  The super_admin seeded in WP-S1-08C has no Membership by design.
  The `/admin` route protection logic is correct and ready;
  actual end-to-end testing requires a super_admin login endpoint (WP-S1-09A scope).

---

## Mismatch / Limitation Notes

### Role naming
No mismatch found. The DB `roles.id` values (`company_admin`, `employee`, `super_admin`)
flow directly through the login API response into `localStorage['role']` and Pinia state.
The `userRole` getter (`state.role?.id`) returns exactly the same string as the DB value.

### super_admin login limitation
The current `POST /api/internal/auth/login` endpoint requires a Membership record
(`company_id` + `login_username`). The seeded super_admin user has no Membership (global scope by design).
This is a **known, documented backend limitation** from WP-S1-08A (R4) and WP-S1-08C.
It does NOT affect the correctness of the frontend route guard.
Frontend is ready; backend super_admin login path belongs to WP-S1-09A.

### Session restore role safety
The existing `restoreSession()` restores `role` from `localStorage['role']`.
This is sufficient for route guard purposes — the guard reads `authStore.isCompanyAdmin`
or `authStore.isSuperAdmin` after restore. No additional change needed for this ticket.

---

## Out of Scope Confirmed

- ✔ No backend files changed
- ✔ No API endpoints added or modified
- ✔ No seed data modified
- ✔ No auth architecture redesign
- ✔ No role model changes
- ✔ No Admin.vue UI changes
- ✔ No refresh token system
- ✔ No tenant/customer creation work
