# Gate-Based Development Process

**Version:** 1.0  
**Created:** 2026-03-02  
**Purpose:** Strict gate-based development flow with verification at each step

---

## 🚨 Hard Rules

1. **Sequential Only:** Must follow Gate 0 → Gate 1 → Gate 2 → Gate 3 → Gate 4 → Gate 5
2. **No Skipping:** Cannot start next gate until current gate PASS
3. **One Unit at a Time:** Only work on one G0-01, WP-09-01, etc. at a time
4. **Verification Required:** Each unit must pass acceptance criteria before commit
5. **Blocking Gates:** If Gate 0 fails, all subsequent work is blocked

---

## 📊 Progress Tracker

See: `GATE_PROGRESS_TRACKER.md` for detailed status of each unit.

---

## Gate 0 — Test System Baseline (BLOCKING) 🔴

**Purpose:** Fix pytest collection error before any development work

**Status:** 🔲 Not Started

**Blocking:** All subsequent gates

### G0-01 — Identify Collection Error

**Goal:** Locate the pytest collection error

**Actions:**
```bash
cd backend
source ../venv/bin/activate
pytest --collect-only -q 2>&1 | tee ../docs/DEV_NOTES_TEST_COLLECT_ERROR.md
```

**Expected Output:**
- Error stack trace saved to `docs/DEV_NOTES_TEST_COLLECT_ERROR.md`

**Acceptance Criteria:**
- [ ] Error identified and documented
- [ ] Root cause understood (import/fixture/typing issue)

**Files Modified:** None (investigation only)

**Commit:** N/A (investigation phase)

---

### G0-02 — Fix Collection Error

**Goal:** Fix the minimum code to pass collection

**Actions:**
- Fix import errors
- Fix fixture errors
- Fix typing errors
- Do NOT refactor unrelated code

**Test Command:**
```bash
cd backend
pytest --collect-only -q
# Expected: collected 82 items (no errors)

pytest -q --co
# Expected: collection succeeds
```

**Acceptance Criteria:**
- [ ] `pytest --collect-only -q` returns 0 exit code
- [ ] No "ERROR" in output
- [ ] Shows "collected X items"

**Files Modified:** (TBD based on error)

**Commit Message:**
```
fix(tests): resolve pytest collection error

- Fix [specific issue found in G0-01]
- All tests now collectible
- Baseline established for Gate 1

Refs: Gate 0, G0-02
```

---

### G0-03 — Update Status Documents

**Goal:** Mark Gate 0 complete in tracking documents

**Actions:**
```bash
# Update STATUS_MATRIX.md
# Update GATE_PROGRESS_TRACKER.md
# Mark G0-01, G0-02, G0-03 as ✅
```

**Acceptance Criteria:**
- [ ] STATUS_MATRIX.md updated
- [ ] GATE_PROGRESS_TRACKER.md updated
- [ ] Gate 0 marked as ✅ PASS

**Files Modified:**
- `docs/STATUS_MATRIX.md`
- `docs/GATE_PROGRESS_TRACKER.md`

**Commit Message:**
```
docs: mark Gate 0 complete

- Test collection error fixed
- Baseline established
- Ready for Gate 1 (Phase 9)

Refs: Gate 0
```

---

## Gate 1 — Phase 9: Tenants Foundation

**Purpose:** Create tenants module (table, model, repo, service, API)

**Status:** 🔲 Not Started

**Prerequisite:** Gate 0 PASS ✅

**Blocking:** Gate 2 (tenant context enforcement)

### WP-09-01 — Tenants Migration Only

**Goal:** Create tenants table via Alembic migration

**Actions:**
- Create `backend/alembic/versions/004_create_tenants.py`
- Schema: id (PK), name, is_active, timezone, created_at, updated_at
- Index on is_active

**Test Command:**
```bash
cd backend
alembic upgrade head
psql -h 127.0.0.1 -U attendance_user -d attendance_db -c "\d tenants"
alembic downgrade -1
alembic upgrade head
alembic current
```

**Acceptance Criteria:**
- [ ] Migration file created
- [ ] `alembic upgrade head` succeeds
- [ ] Table exists after upgrade
- [ ] `alembic downgrade -1` succeeds
- [ ] Table dropped after downgrade
- [ ] Re-upgrade succeeds
- [ ] `alembic current` shows 004

**Files Added:**
- `backend/alembic/versions/004_create_tenants.py`

**Files Modified:** None

**Commit Message:**
```
chore(tenants): add tenants table migration

- Create tenants table with id (PK), name, is_active, timezone
- Add index on is_active for fast queries
- Migration 004, revises 003

Refs: WP-09-01, Gate 1
```

---

### WP-09-02 — Tenants Model + Repo + Unit Tests

**Goal:** Create Tenant ORM model and repository with unit tests

**Actions:**
- Create `backend/app/modules/tenants/__init__.py`
- Create `backend/app/modules/tenants/models.py`
- Create `backend/app/modules/tenants/repo.py`
- Create `backend/app/modules/tenants/tests/__init__.py`
- Create `backend/app/modules/tenants/tests/test_repo.py`

**Test Command:**
```bash
cd backend
pytest app/modules/tenants/tests/test_repo.py -v
```

**Acceptance Criteria:**
- [ ] All repo unit tests pass
- [ ] CRUD operations work (create, get_by_id, list_all, update)
- [ ] Tenant isolation verified (if applicable)

**Files Added:**
- `backend/app/modules/tenants/__init__.py`
- `backend/app/modules/tenants/models.py`
- `backend/app/modules/tenants/repo.py`
- `backend/app/modules/tenants/tests/__init__.py`
- `backend/app/modules/tenants/tests/test_repo.py`

**Files Modified:** None

**Commit Message:**
```
feat(tenants): add Tenant model and repository with unit tests

- Create Tenant ORM model
- Implement TenantRepository with CRUD methods
- Add comprehensive unit tests
- All tests pass

Refs: WP-09-02, Gate 1
```

---

### WP-09-03 — Tenants Service + Validation + Unit Tests

**Goal:** Add service layer with business validation

**Actions:**
- Create `backend/app/modules/tenants/service.py`
- Create `backend/app/modules/tenants/tests/test_service.py`
- Validation: tenant_id format, name not empty, timezone valid

**Test Command:**
```bash
cd backend
pytest app/modules/tenants/tests/test_service.py -v
```

**Acceptance Criteria:**
- [ ] All service unit tests pass
- [ ] Validation rules enforced (invalid input → ValueError)
- [ ] Business logic correct

**Files Added:**
- `backend/app/modules/tenants/service.py`
- `backend/app/modules/tenants/tests/test_service.py`

**Files Modified:** None

**Commit Message:**
```
feat(tenants): add service layer with validation rules

- Implement TenantService with validation
- Validate tenant_id format, name, timezone
- Add comprehensive unit tests
- All tests pass

Refs: WP-09-03, Gate 1
```

---

### WP-09-04 — Tenants API + Feature Tests

**Goal:** Add REST API endpoints with feature tests

**Actions:**
- Create `backend/app/modules/tenants/api.py`
- Create `backend/app/modules/tenants/docs.md`
- Create `backend/app/modules/tenants/tests/test_api.py`
- Modify `backend/app/main.py` (register router)

**Test Command:**
```bash
cd backend
pytest app/modules/tenants/tests/test_api.py -v
pytest app/modules/tenants/tests/ -v
```

**Acceptance Criteria:**
- [ ] All API tests pass
- [ ] POST /api/tenants creates tenant
- [ ] GET /api/tenants lists tenants
- [ ] GET /api/tenants/{id} returns tenant
- [ ] PATCH /api/tenants/{id} updates tenant
- [ ] DELETE /api/tenants/{id} deactivates tenant
- [ ] Router registered in main.py

**Files Added:**
- `backend/app/modules/tenants/api.py`
- `backend/app/modules/tenants/docs.md`
- `backend/app/modules/tenants/tests/test_api.py`

**Files Modified:**
- `backend/app/main.py`

**Commit Message:**
```
feat(tenants): add REST API endpoints with feature tests

- Implement tenants CRUD API
- Register router in main.py
- Add comprehensive feature tests
- Add API documentation
- All tests pass

Refs: WP-09-04, Gate 1
```

---

## Gate 2 — Tenant Context Security (P0) 🔥

**Purpose:** Fix Gap 1 — Enforce tenant existence and active status

**Status:** 🔲 Not Started

**Prerequisite:** Gate 1 PASS ✅ (WP-09-04 complete)

**Blocking:** Gate 3, Gate 4, Gate 5

### WP-09-05 — Tenant Context Enforce Existence + Active

**Goal:** Strengthen tenant_context.py to validate tenant in DB

**Actions:**
- Modify `backend/app/core/tenant_context.py`
- Add DB query to check tenant exists
- Add check for is_active flag
- Return 404 if not exists, 403 if inactive
- Create `backend/app/core/tests/test_tenant_context.py` (if not exists)

**Test Command:**
```bash
cd backend
pytest app/core/tests/test_tenant_context.py -v

# Regression tests (must still pass)
pytest app/modules/attendance/tests/ -v
pytest app/modules/notifications/tests/ -v
pytest app/modules/backup/tests/ -v
pytest app/modules/audit/tests/ -v
```

**Acceptance Criteria:**
- [ ] Valid active tenant → requests succeed
- [ ] Non-existent tenant → 404
- [ ] Inactive tenant → 403
- [ ] All regression tests pass (no breakage)

**Files Modified:**
- `backend/app/core/tenant_context.py`

**Files Added:**
- `backend/app/core/tests/test_tenant_context.py` (if new)

**Commit Message:**
```
feat(tenant): enforce tenant existence and active status in context

- Query tenants table to validate company_id
- Return 404 for non-existent tenant
- Return 403 for inactive tenant
- All regression tests pass
- Fixes Gap 1 (P0 security issue)

Refs: WP-09-05, Gate 2, Gap Report #1
```

---

## Gate 3 — Spec Compliance (Notifications Migration) 🟡

**Purpose:** Fix Gap 5 — Remove create_all(), use Alembic only

**Status:** 🔲 Not Started

**Prerequisite:** Gate 2 PASS ✅

**Blocking:** None (P1, can defer)

### G3-01 — Locate create_all() Calls

**Goal:** Find all Base.metadata.create_all() usage

**Actions:**
```bash
cd backend
grep -rn "create_all" app/
```

**Expected Output:**
- List of files using create_all()
- Document in `docs/DEV_NOTES_CREATE_ALL_USAGE.md`

**Acceptance Criteria:**
- [ ] All create_all() calls documented

**Files Modified:** None (investigation only)

**Commit:** N/A

---

### G3-02 — Add Notifications Migration

**Goal:** Create retroactive migration for notifications table

**Actions:**
- Create migration (005 or renumber after users)
- Check if table exists before creating (idempotent)
- Remove create_all() from runtime code

**Test Command:**
```bash
cd backend
alembic upgrade head
pytest app/modules/notifications/tests/ -v
```

**Acceptance Criteria:**
- [ ] Migration created
- [ ] Migration can upgrade/downgrade
- [ ] Notifications tests still pass
- [ ] No create_all() in runtime code

**Files Added:**
- `backend/alembic/versions/00X_create_notifications.py`

**Files Modified:**
- Remove create_all() from relevant files

**Commit Message:**
```
chore(notifications): add Alembic migration (retroactive)

- Create notifications table migration
- Remove create_all() from runtime
- Make migration idempotent (check if exists)
- All tests pass
- Fixes Gap 5 (spec compliance)

Refs: Gate 3, Gap Report #5
```

---

### G3-03 — Remove Phase 2 Skipped Tests (Attendance Cross-Tenant Isolation)

**Goal:** Implement and enable 3 skipped Phase 2 cross-tenant isolation tests

**Actions:**
- Implement `test_phase2_cross_company_read_forbidden`
- Implement `test_phase2_cross_company_update_forbidden`
- Implement `test_phase2_cross_company_delete_forbidden`
- Use existing TestClient and tenant fixtures (company-A, company-B)
- Create attendance records for company-B, attempt access from company-A context
- Verify proper isolation (403/404/empty results based on endpoint behavior)

**Test Command:**
```bash
cd backend
pytest app/modules/attendance/tests/test_tenant_isolation.py -v
pytest app/modules/attendance/tests/ -v  # Full regression
```

**Acceptance Criteria:**
- [ ] All 3 tests implemented (no pytest.skip())
- [ ] test_phase2_cross_company_read_forbidden PASS
- [ ] test_phase2_cross_company_update_forbidden PASS
- [ ] test_phase2_cross_company_delete_forbidden PASS
- [ ] All other attendance tests still pass (no regression)
- [ ] Total: 24 passed, 0 skipped (was 21 passed, 3 skipped)

**Files Modified:**
- `backend/app/modules/attendance/tests/test_tenant_isolation.py`

**Files Added:** None

**Commit Message:**
```
test(attendance): implement Phase 2 cross-tenant isolation tests

- Remove pytest.skip() from 3 Phase 2 tests
- Implement cross-company read/update/delete isolation tests
- Verify tenant_context properly blocks cross-tenant access
- All tests pass (24 passed, 0 skipped)
- Completes Phase 2 tenant isolation requirements

Refs: Gate 3, G3-03, PHASE1_IMPLEMENTATION_COMPLETE.md
```

---

## Gate 4 — Phase 10: Auth (JWT + RBAC)

**Purpose:** Implement authentication and authorization

**Status:** 🔲 Not Started

**Prerequisite:** Gate 2 PASS ✅ (WP-09-05 complete)

**Blocking:** Gate 5 (attendance regression tests 7-8)

### WP-10-01 — Auth Schema Spec

**Goal:** Design auth schema (users table, roles, JWT claims)

**Actions:**
- Create `docs/AUTH_SCHEMA_SPEC.md`
- Define users table schema
- Define roles (employee, manager, company_admin, customer_service)
- Define JWT claims structure

**Acceptance Criteria:**
- [ ] Document created
- [ ] Schema reviewed and approved

**Files Added:**
- `docs/AUTH_SCHEMA_SPEC.md`

**Commit Message:**
```
docs(auth): add auth schema specification

- Define users table schema
- Define roles and permissions
- Define JWT claims structure
- Ready for implementation

Refs: WP-10-01, Gate 4
```

---

### WP-10-02 — Users Migration + Model

**Goal:** Create users table and ORM model

**Actions:**
- Create `backend/alembic/versions/00X_create_users.py`
- Create `backend/app/modules/auth/__init__.py`
- Create `backend/app/modules/auth/models.py`

**Test Command:**
```bash
cd backend
alembic upgrade head
psql -h 127.0.0.1 -U attendance_user -d attendance_db -c "\d users"
```

**Acceptance Criteria:**
- [ ] Migration applied successfully
- [ ] Users table exists
- [ ] User model created

**Files Added:**
- `backend/alembic/versions/00X_create_users.py`
- `backend/app/modules/auth/__init__.py`
- `backend/app/modules/auth/models.py`

**Commit Message:**
```
chore(auth): add users table migration and model

- Create users table with company_id, username, email, password_hash, roles
- Add unique constraints on (company_id, username) and (company_id, email)
- Create User ORM model

Refs: WP-10-02, Gate 4
```

---

### WP-10-03 — Auth Repo + Password Hashing + Tests

**Goal:** Implement auth repository with password hashing

**Actions:**
- Create `backend/app/core/security.py` (hash/verify functions)
- Create `backend/app/modules/auth/repo.py`
- Create `backend/app/modules/auth/tests/test_repo.py`

**Test Command:**
```bash
cd backend
pytest app/modules/auth/tests/test_repo.py -v
```

**Acceptance Criteria:**
- [ ] All repo tests pass
- [ ] Passwords hashed (never plaintext)
- [ ] Verify password works correctly

**Files Added:**
- `backend/app/core/security.py`
- `backend/app/modules/auth/repo.py`
- `backend/app/modules/auth/tests/__init__.py`
- `backend/app/modules/auth/tests/test_repo.py`

**Commit Message:**
```
feat(auth): add auth repository with password hashing

- Implement password hashing (bcrypt/argon2)
- Create AuthRepository with user CRUD
- Add comprehensive unit tests
- All tests pass

Refs: WP-10-03, Gate 4
```

---

### WP-10-04 — JWT Login API + Tests

**Goal:** Implement JWT login endpoint

**Actions:**
- Extend `backend/app/core/security.py` (JWT encode/decode)
- Create `backend/app/modules/auth/service.py`
- Create `backend/app/modules/auth/api.py`
- Create `backend/app/modules/auth/tests/test_api.py`
- Modify `backend/app/main.py` (register router)

**Test Command:**
```bash
cd backend
pytest app/modules/auth/tests/test_api.py -v
```

**Acceptance Criteria:**
- [ ] Valid login → 200 + JWT token
- [ ] Invalid login → 401
- [ ] Token contains correct claims (company_id, staff_id, roles)
- [ ] All tests pass
- [ ] Existing header endpoints still work (coexistence)

**Files Added:**
- `backend/app/modules/auth/service.py`
- `backend/app/modules/auth/api.py`
- `backend/app/modules/auth/tests/test_api.py`

**Files Modified:**
- `backend/app/core/security.py`
- `backend/app/main.py`

**Commit Message:**
```
feat(auth): add JWT login API with tests

- Implement POST /api/auth/login
- Generate JWT tokens with claims
- Add comprehensive tests
- Coexistence mode (header still works)
- All tests pass

Refs: WP-10-04, Gate 4
```

---

### WP-10-05 — RBAC Logic + Tests

**Goal:** Implement role-based permission checking

**Actions:**
- Create `backend/app/core/rbac.py`
- Create `backend/app/core/dependencies.py` (permission guards)
- Create `backend/app/core/tests/test_rbac.py`

**Test Command:**
```bash
cd backend
pytest app/core/tests/test_rbac.py -v
```

**Acceptance Criteria:**
- [ ] RBAC logic implemented
- [ ] Permission checks work correctly
- [ ] All unit tests pass
- [ ] No endpoints modified yet (next WP)

**Files Added:**
- `backend/app/core/rbac.py`
- `backend/app/core/dependencies.py`
- `backend/app/core/tests/test_rbac.py`

**Commit Message:**
```
feat(rbac): add role-based permission checking

- Implement RBAC logic (employee, manager, admin)
- Create FastAPI permission guards
- Add comprehensive unit tests
- All tests pass

Refs: WP-10-05, Gate 4
```

---

### WP-10-06 — Auth Transition Batch 1 (Attendance)

**Goal:** Migrate attendance endpoints to require JWT

**Actions:**
- Modify `backend/app/modules/attendance/api.py` (add JWT dependency)
- Update `backend/app/modules/attendance/tests/` (use JWT tokens)
- Create test fixtures for JWT tokens

**Test Command:**
```bash
cd backend
pytest app/modules/attendance/tests/ -v
```

**Acceptance Criteria:**
- [ ] Attendance endpoints require JWT
- [ ] RBAC enforced (employee cannot approve)
- [ ] All attendance tests pass with JWT
- [ ] Header-based auth removed from batch 1

**Files Modified:**
- `backend/app/modules/attendance/api.py`
- `backend/app/modules/attendance/tests/*.py`

**Commit Message:**
```
feat(auth): migrate attendance endpoints to JWT auth (batch 1)

- Attendance endpoints now require JWT
- RBAC enforced (employee/manager permissions)
- Update all tests to use JWT tokens
- All tests pass
- Fixes Gap 3 (auth missing)

Refs: WP-10-06, Gate 4, Gap Report #3
```

---

## Gate 5 — Phase 11: Attendance Core Logic

**Purpose:** Implement attendance business logic and pass 8 regression tests

**Status:** 🔲 Not Started

**Prerequisite:** Gate 4 PASS ✅ (WP-10-06 complete)

**Blocking:** None (final gate)

### WP-11-01 — Attendance State Machine + Enum

**Goal:** Define status enum and state transitions

**Actions:**
- Create `docs/ATTENDANCE_STATE_MACHINE.md`
- Add status enum to `backend/app/modules/attendance/models.py`
- Create migration to add status, type, timestamp, reason fields

**Test Command:**
```bash
cd backend
alembic upgrade head
grep -n "AttendanceStatus" app/modules/attendance/models.py
```

**Acceptance Criteria:**
- [ ] State machine documented
- [ ] Enum added to model
- [ ] Migration applied
- [ ] Fields added to table

**Files Added:**
- `docs/ATTENDANCE_STATE_MACHINE.md`
- `backend/alembic/versions/00X_add_attendance_status_fields.py`

**Files Modified:**
- `backend/app/modules/attendance/models.py`

**Commit Message:**
```
docs(attendance): add state machine specification and enum

- Define AttendanceStatus enum
- Document state transitions
- Add migration for status/type/timestamp/reason fields
- Ready for business logic implementation

Refs: WP-11-01, Gate 5
```

---

### WP-11-02 — IN/OUT Pairing Logic + Tests

**Goal:** Implement IN/OUT pairing algorithm

**Actions:**
- Create `backend/app/modules/attendance/inference.py`
- Create `backend/app/modules/attendance/tests/test_inference.py`

**Test Command:**
```bash
cd backend
pytest app/modules/attendance/tests/test_inference.py -v
```

**Acceptance Criteria:**
- [ ] Pairing logic implemented
- [ ] All unit tests pass
- [ ] Edge cases handled (cross-day, multiple IN/OUT)

**Files Added:**
- `backend/app/modules/attendance/inference.py`
- `backend/app/modules/attendance/tests/test_inference.py`

**Commit Message:**
```
feat(attendance): implement IN/OUT pairing logic

- Add pair_in_out() function
- Handle unpaired IN/OUT
- Handle cross-day boundary
- Add comprehensive unit tests
- All tests pass

Refs: WP-11-02, Gate 5
```

---

### WP-11-03 — Work Time Calculation + Tests

**Goal:** Calculate work hours from paired IN/OUT

**Actions:**
- Extend `backend/app/modules/attendance/inference.py`
- Extend `backend/app/modules/attendance/tests/test_inference.py`

**Test Command:**
```bash
cd backend
pytest app/modules/attendance/tests/test_inference.py::test_calculate_work_time -v
```

**Acceptance Criteria:**
- [ ] Work time calculation correct
- [ ] All tests pass

**Files Modified:**
- `backend/app/modules/attendance/inference.py`
- `backend/app/modules/attendance/tests/test_inference.py`

**Commit Message:**
```
feat(attendance): add work time calculation

- Implement calculate_work_time()
- Handle unpaired records (0 hours)
- Add unit tests
- All tests pass

Refs: WP-11-03, Gate 5
```

---

### WP-11-04 — Day Close + Missing Card Detection + Tests

**Goal:** Implement day close logic at 21:00

**Actions:**
- Create `backend/app/modules/attendance/day_close.py`
- Create `backend/app/modules/attendance/tests/test_day_close.py`

**Test Command:**
```bash
cd backend
pytest app/modules/attendance/tests/test_day_close.py -v
```

**Acceptance Criteria:**
- [ ] Day close logic implemented
- [ ] PENDING_APPROVAL excluded
- [ ] Missing cards detected
- [ ] All tests pass

**Files Added:**
- `backend/app/modules/attendance/day_close.py`
- `backend/app/modules/attendance/tests/test_day_close.py`

**Commit Message:**
```
feat(attendance): implement day close and missing card detection

- Add close_day() function
- Exclude PENDING_APPROVAL from day close
- Detect missing IN/OUT
- Add comprehensive tests
- All tests pass

Refs: WP-11-04, Gate 5
```

---

### WP-11-05 — Approve Triggers Recalculation + Tests

**Goal:** Recalculate day when PENDING approved

**Actions:**
- Modify `backend/app/modules/attendance/service.py`
- Extend `backend/app/modules/attendance/tests/test_service.py`

**Test Command:**
```bash
cd backend
pytest app/modules/attendance/tests/test_service.py::test_approve_recalculates -v
```

**Acceptance Criteria:**
- [ ] Approve PENDING → status = APPROVED
- [ ] Approve triggers day recalculation
- [ ] Work time updated
- [ ] All tests pass

**Files Modified:**
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/tests/test_service.py`

**Commit Message:**
```
feat(attendance): recalculate day when approving pending records

- Approve changes status to APPROVED
- Trigger day recalculation
- Update work time
- Add tests
- All tests pass

Refs: WP-11-05, Gate 5
```

---

### WP-11-06 — 8 Regression Tests (Final Validation)

**Goal:** Implement and pass all 8 regression tests

**Actions:**
- Create `backend/app/modules/attendance/tests/test_regression.py`
- Implement all 8 tests from ATTENDANCE_REGRESSION_SPEC.md
- Fix any bugs found

**Test Command:**
```bash
cd backend
pytest app/modules/attendance/tests/test_regression.py -v
```

**Acceptance Criteria:**
- [ ] Test 1: NO_MATCH no reason → reject ✅
- [ ] Test 2: NO_MATCH with reason → PENDING ✅
- [ ] Test 3: APPROVED → inference correct ✅
- [ ] Test 4: PENDING excluded ✅
- [ ] Test 5: Day close → missing cards ✅
- [ ] Test 6: Approve → recalculate ✅
- [ ] Test 7: customer_service 403 ✅
- [ ] Test 8: OTP one-time + force change ✅
- [ ] 8/8 tests pass
- [ ] All attendance tests pass

**Files Added:**
- `backend/app/modules/attendance/tests/test_regression.py`

**Files Modified:**
- Bug fixes as needed

**Commit Message:**
```
test(attendance): add 8 core regression tests and validate

- Implement all 8 regression tests
- All tests pass (8/8)
- Attendance core logic complete
- Fixes Gap 4 (core logic missing)

Refs: WP-11-06, Gate 5, Gap Report #4
```

---

## 🎯 Summary

**Total Gates:** 6 (Gate 0 to Gate 5)  
**Total Units:** 26 (G0-01 to WP-11-06)  
**Estimated Time:** 15-20 days

**Critical Path:**
```
Gate 0 (Test Baseline) → Gate 1 (Tenants) → Gate 2 (Security) → Gate 4 (Auth) → Gate 5 (Attendance)
```

**See:** `GATE_PROGRESS_TRACKER.md` for detailed status tracking.
