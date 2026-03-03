# Gate Progress Tracker

**Project:** SaaS Multi-Tenant Attendance System  
**Current Gate:** Gate 4 (Auth)  
**Last Updated:** 2026-03-03

---

## Gate 4 — Phase 10: Auth (JWT + RBAC)

### WP-10-02B — Users Migration + Model (Platform-First v2)

**Status:** ✅ Complete  
**Date:** 2026-03-03  
**Commit:** 32de20e

**Deliverables:**
- ✅ Migration: `3532deda024c_create_auth_tables_v2_platform_first.py`
- ✅ Models: User, Membership, Role, Permission, RolePermission
- ✅ Repository: AuthRepository with membership methods
- ✅ Tests: 24 tests, all passing

**Key Changes:**
- User: removed `company_id`, `username`; added `display_name`
- Membership: new model (user-company relationship + role)
- UNIQUE constraints: `(company_id, login_username)`, `(user_id, company_id)`

---

### WP-10-03B — Tenant Context v2 (Membership Validation)

**Status:** ✅ Complete  
**Date:** 2026-03-03  
**Commit:** [pending]

**Deliverables:**
- ✅ `tenant_context.py`: Added `get_current_company_id_with_membership()`
- ✅ Membership validation: `user_has_company_access(user_id, company_id)`
- ✅ Anti-enumeration: No membership → 404 (not 403)
- ✅ Tests: 13 tests, all passing
- ✅ Regression: All module tests passing (83 tests total)

**Security Enhancement:**
- Validates user has active membership before granting company access
- Returns 404 for no membership (anti-enumeration, prevents tenant discovery)
- Backward compatible: old `get_current_company_id()` preserved

**Test Results:**
```
app/core/tests/test_tenant_context.py: 13 passed
app/modules/attendance/tests/: 24 passed
app/modules/notifications/tests/: 13 passed
app/modules/backup/tests/: 22 passed
app/modules/audit/tests/: 24 passed
---
Total: 96 passed
```

**404 Generation Layer:**
- **Layer:** `tenant_context.py` (Dependency Injection)
- **Why:** Intercepts before API handler, unified enforcement
- **Anti-Enumeration:** Attacker cannot distinguish:
  - Tenant does not exist
  - Tenant exists but user has no membership
  - Both return 404 "Tenant not found"

---

## Next Steps

**WP-10-04** — JWT Login API + Tests  
**WP-10-05** — RBAC Logic + Tests  
**WP-10-06** — Auth Transition Batch 1 (Attendance)

---

**Document End**

### WP-10-04A — Login API Contract Lock (JWT)

**Status:** ✅ Complete  
**Date:** 2026-03-03  
**Commit:** [pending]

**Deliverables:**
- ✅ `docs/WP-10-04_LOGIN_API_CONTRACT.md` - Locked API contract
- ✅ `test_login_api.py` - 13 tests (TDD red phase)
- ✅ All tests failing as expected (endpoint not implemented yet)

**API Contract (Locked):**
- Endpoint: `POST /api/internal/auth/login`
- Request: `{company_id, login_username, password}`
- Response: `{access_token, token_type, user, company, role}`
- Anti-enumeration: No membership → 404 "Invalid credentials"
- Wrong password → 401 "Invalid credentials"

**Test Coverage:**
```
Success cases: 2 tests
Anti-enumeration: 4 tests
Wrong password: 1 test
Validation: 6 tests
---
Total: 13 tests (all failing - TDD red phase)
```

**Next:** WP-10-04B (Implementation - TDD green phase)

