# Acceptance Checklist — System Verification

**Purpose:** Verify system compliance with specifications  
**Updated:** 2026-03-02

---

## How to Use This Checklist

Each item has:
- **Verification Method:** Command to run or test to check
- **Pass Criteria:** What output/behavior indicates pass
- **Status:** ✅ Pass / ❌ Fail / ⚠️ Partial / 🔲 Not Tested

---

## Section 1: Tenant Isolation (P0)

### 1.1 All Tenant Data Tables Have `company_id`

**Verification:**
```sql
-- Run in psql
\d attendance_records
\d notifications
\d audit_logs
\d audit_retention_policies
```

**Pass Criteria:**
- Each table has `company_id` column
- `company_id` is indexed (or part of PK)

**Status:** ✅ Pass (verified in STATUS_MATRIX.md)

---

### 1.2 All Repos Enforce `WHERE company_id = ?`

**Verification:**
```bash
# Check repo files
grep -n "company_id ==" backend/app/modules/*/repo.py
```

**Pass Criteria:**
- All query methods filter by `company_id`
- No queries without `company_id` filter

**Status:** ✅ Pass (verified in STATUS_MATRIX.md)

---

### 1.3 No Endpoints Accept `company_id` from Client

**Verification:**
```bash
# Check API files for request body/query params
grep -rn "company_id.*Body\|company_id.*Query" backend/app/modules/*/api.py
```

**Pass Criteria:**
- No matches found (or only in comments)
- `company_id` always from `Depends(get_current_company_id)`

**Status:** ✅ Pass (verified in STATUS_MATRIX.md)

---

### 1.4 Backup Force Overwrites `company_id`

**Verification:**
```bash
# Check importer.py
grep -A 2 'company_id.*target_company_id' backend/app/modules/backup/importer.py
```

**Pass Criteria:**
- Line exists: `record_data["company_id"] = target_company_id`

**Status:** ✅ Pass (verified in STATUS_MATRIX.md)

---

### 1.5 Tenant Context Enforces Existence + Active Status

**Verification:**
```bash
# Check tenant_context.py
grep -n "tenants.*get_by_id\|is_active" backend/app/core/tenant_context.py
```

**Pass Criteria:**
- Code queries `tenants` table
- Returns 404 if tenant not found
- Returns 403 if tenant inactive

**Status:** ❌ Fail (Gap 1 — not implemented yet)

**Required WP:** WP-09-05

---

### 1.6 Cross-Tenant Read Forbidden

**Verification:**
```bash
cd backend
pytest app/modules/attendance/tests/test_tenant_isolation.py::TestCrossCompanyIsolation::test_phase2_cross_company_read_forbidden -v
```

**Pass Criteria:**
- Test passes
- Company A cannot read Company B's data

**Status:** 🔲 Not Tested (need to run)

---

### 1.7 Cross-Tenant Update Forbidden

**Verification:**
```bash
cd backend
pytest app/modules/attendance/tests/test_tenant_isolation.py::TestCrossCompanyIsolation::test_phase2_cross_company_update_forbidden -v
```

**Pass Criteria:**
- Test passes
- Company A cannot update Company B's data (returns 404, not 403)

**Status:** 🔲 Not Tested (need to run)

---

### 1.8 Cross-Tenant Delete Forbidden

**Verification:**
```bash
cd backend
pytest app/modules/attendance/tests/test_tenant_isolation.py::TestCrossCompanyIsolation::test_phase2_cross_company_delete_forbidden -v
```

**Pass Criteria:**
- Test passes
- Company A cannot delete Company B's data (returns 404)

**Status:** 🔲 Not Tested (need to run)

---

## Section 2: Tenants Module

### 2.1 Tenants Table Exists

**Verification:**
```sql
-- Run in psql
\d tenants
```

**Pass Criteria:**
- Table exists
- Columns: `id` (PK), `name`, `is_active`, `timezone`, `created_at`, `updated_at`

**Status:** ❌ Fail (table doesn't exist)

**Required WP:** WP-09-01

---

### 2.2 Tenants Migration Applied

**Verification:**
```bash
cd backend
alembic current
```

**Pass Criteria:**
- Shows migration `004` (or later) applied

**Status:** ❌ Fail (migration doesn't exist)

**Required WP:** WP-09-01

---

### 2.3 Tenants CRUD API Works

**Verification:**
```bash
cd backend
pytest app/modules/tenants/tests/test_api.py -v
```

**Pass Criteria:**
- All tests pass
- POST /api/tenants creates tenant
- GET /api/tenants lists tenants
- GET /api/tenants/{id} returns tenant
- PATCH /api/tenants/{id} updates tenant

**Status:** ❌ Fail (module doesn't exist)

**Required WP:** WP-09-04

---

### 2.4 Tenant Validation Rules Enforced

**Verification:**
```bash
cd backend
pytest app/modules/tenants/tests/test_service.py::test_invalid_tenant_id_format -v
pytest app/modules/tenants/tests/test_service.py::test_empty_name -v
pytest app/modules/tenants/tests/test_service.py::test_invalid_timezone -v
```

**Pass Criteria:**
- All tests pass
- Invalid `tenant_id` format → ValueError
- Empty `name` → ValueError
- Invalid `timezone` → ValueError

**Status:** ❌ Fail (module doesn't exist)

**Required WP:** WP-09-03

---

## Section 3: Auth Module

### 3.1 Users Table Exists

**Verification:**
```sql
-- Run in psql
\d users
```

**Pass Criteria:**
- Table exists
- Columns: `id`, `company_id`, `username`, `email`, `password_hash`, `roles`, `is_active`
- Unique constraint on `(company_id, username)`
- Unique constraint on `(company_id, email)`

**Status:** ❌ Fail (table doesn't exist)

**Required WP:** WP-10-02

---

### 3.2 Password Hashing Works

**Verification:**
```bash
cd backend
pytest app/modules/auth/tests/test_repo.py::test_password_hashed -v
pytest app/modules/auth/tests/test_repo.py::test_verify_correct_password -v
pytest app/modules/auth/tests/test_repo.py::test_verify_wrong_password -v
```

**Pass Criteria:**
- All tests pass
- Passwords never stored in plaintext
- Correct password → True
- Wrong password → False

**Status:** ❌ Fail (module doesn't exist)

**Required WP:** WP-10-03

---

### 3.3 JWT Login API Works

**Verification:**
```bash
cd backend
pytest app/modules/auth/tests/test_api.py::test_valid_login_returns_token -v
pytest app/modules/auth/tests/test_api.py::test_invalid_login_returns_401 -v
```

**Pass Criteria:**
- Valid login → 200 + JWT token
- Invalid login → 401
- Token contains claims: `company_id`, `staff_id`, `roles`

**Status:** ❌ Fail (module doesn't exist)

**Required WP:** WP-10-04

---

### 3.4 RBAC Permission Checks Work

**Verification:**
```bash
cd backend
pytest app/core/tests/test_rbac.py::test_employee_has_self_permissions -v
pytest app/core/tests/test_rbac.py::test_employee_cannot_approve -v
pytest app/core/tests/test_rbac.py::test_manager_can_approve -v
```

**Pass Criteria:**
- Employee has `attendance:create:self` → True
- Employee has `attendance:approve` → False
- Manager has `attendance:approve` → True

**Status:** ❌ Fail (RBAC not implemented)

**Required WP:** WP-10-05

---

### 3.5 JWT Required on Protected Endpoints

**Verification:**
```bash
cd backend
pytest app/modules/attendance/tests/test_api.py -v
```

**Pass Criteria:**
- After WP-10-06, attendance endpoints require JWT
- No JWT → 401
- Invalid JWT → 401
- Valid JWT + wrong role → 403

**Status:** ❌ Fail (still header-only)

**Required WP:** WP-10-06

---

## Section 4: Attendance Core Logic

### 4.1 Status Enum Exists

**Verification:**
```bash
grep -n "class AttendanceStatus" backend/app/modules/attendance/models.py
```

**Pass Criteria:**
- Enum exists with values: APPROVED, PENDING_APPROVAL, NO_MATCH, REJECTED

**Status:** ❌ Fail (enum doesn't exist)

**Required WP:** WP-11-01

---

### 4.2 IN/OUT Pairing Works

**Verification:**
```bash
cd backend
pytest app/modules/attendance/tests/test_inference.py::test_pair_in_out -v
```

**Pass Criteria:**
- IN at 09:00, OUT at 18:00 → 1 pair
- Unpaired IN → detected
- Unpaired OUT → detected

**Status:** ❌ Fail (pairing logic doesn't exist)

**Required WP:** WP-11-02

---

### 4.3 Work Time Calculation Works

**Verification:**
```bash
cd backend
pytest app/modules/attendance/tests/test_inference.py::test_calculate_work_time -v
```

**Pass Criteria:**
- 09:00 IN, 18:00 OUT → 9 hours
- Unpaired → 0 hours

**Status:** ❌ Fail (calculation doesn't exist)

**Required WP:** WP-11-03

---

### 4.4 Day Close Detects Missing Cards

**Verification:**
```bash
cd backend
pytest app/modules/attendance/tests/test_day_close.py::test_day_close_missing_out -v
```

**Pass Criteria:**
- Day with unpaired IN → "missing OUT" detected
- Day with unpaired OUT → "missing IN" detected

**Status:** ❌ Fail (day close doesn't exist)

**Required WP:** WP-11-04

---

### 4.5 PENDING Excluded from Day Close

**Verification:**
```bash
cd backend
pytest app/modules/attendance/tests/test_day_close.py::test_pending_excluded_from_day_close -v
```

**Pass Criteria:**
- PENDING_APPROVAL records not included in pairs
- PENDING_APPROVAL records not counted as missing cards

**Status:** ❌ Fail (day close doesn't exist)

**Required WP:** WP-11-04

---

### 4.6 Approve Triggers Recalculation

**Verification:**
```bash
cd backend
pytest app/modules/attendance/tests/test_service.py::test_approve_recalculates_day -v
```

**Pass Criteria:**
- Approve PENDING → status = APPROVED
- Approve PENDING → day recalculated
- Work time updated

**Status:** ❌ Fail (recalculation doesn't exist)

**Required WP:** WP-11-05

---

### 4.7 Regression Test 1: NO_MATCH No Reason → Reject

**Verification:**
```bash
cd backend
pytest app/modules/attendance/tests/test_regression.py::test_no_match_without_reason_rejected -v
```

**Pass Criteria:**
- POST with `type=NO_MATCH`, `reason=None` → 422
- Error message mentions "reason"

**Status:** ❌ Fail (test doesn't exist)

**Required WP:** WP-11-06

---

### 4.8 Regression Test 2: NO_MATCH With Reason → PENDING

**Verification:**
```bash
cd backend
pytest app/modules/attendance/tests/test_regression.py::test_no_match_with_reason_pending -v
```

**Pass Criteria:**
- POST with `type=NO_MATCH`, `reason="Forgot"` → 201
- Record status = PENDING_APPROVAL

**Status:** ❌ Fail (test doesn't exist)

**Required WP:** WP-11-06

---

### 4.9 Regression Test 3: APPROVED → Inference Correct

**Verification:**
```bash
cd backend
pytest app/modules/attendance/tests/test_regression.py::test_approved_records_inference -v
```

**Pass Criteria:**
- IN 09:00 + OUT 18:00 → 1 pair, 9 hours

**Status:** ❌ Fail (test doesn't exist)

**Required WP:** WP-11-06

---

### 4.10 Regression Test 4: PENDING Excluded

**Verification:**
```bash
cd backend
pytest app/modules/attendance/tests/test_regression.py::test_pending_excluded_from_day_close -v
```

**Pass Criteria:**
- PENDING records not in inference
- PENDING records not in day close

**Status:** ❌ Fail (test doesn't exist)

**Required WP:** WP-11-06

---

### 4.11 Regression Test 5: Day Close Missing Cards

**Verification:**
```bash
cd backend
pytest app/modules/attendance/tests/test_regression.py::test_day_close_missing_out -v
```

**Pass Criteria:**
- Unpaired IN → missing OUT detected

**Status:** ❌ Fail (test doesn't exist)

**Required WP:** WP-11-06

---

### 4.12 Regression Test 6: Approve → Recalculate

**Verification:**
```bash
cd backend
pytest app/modules/attendance/tests/test_regression.py::test_approve_pending_recalculates_day -v
```

**Pass Criteria:**
- Approve PENDING → day recalculated

**Status:** ❌ Fail (test doesn't exist)

**Required WP:** WP-11-06

---

### 4.13 Regression Test 7: customer_service 403

**Verification:**
```bash
cd backend
pytest app/modules/attendance/tests/test_regression.py::test_customer_service_unassigned_company_403 -v
```

**Pass Criteria:**
- customer_service accessing unassigned company → 403

**Status:** ❌ Fail (test doesn't exist, Auth not implemented)

**Required WP:** WP-11-06 (after WP-10-06)

---

### 4.14 Regression Test 8: OTP One-Time + Force Change

**Verification:**
```bash
cd backend
pytest app/modules/auth/tests/test_regression.py::test_otp_one_time_use_and_force_change -v
```

**Pass Criteria:**
- OTP login → must change password
- OTP reuse → 401

**Status:** ❌ Fail (test doesn't exist, Auth not implemented)

**Required WP:** WP-11-06 (after WP-10-06)

---

## Section 5: Cross-Module Integration

### 5.1 EventBus Works

**Verification:**
```bash
cd backend
pytest app/modules/notifications/tests/test_event_handlers.py::test_attendance_approved_creates_notification -v
```

**Pass Criteria:**
- Approve attendance → `attendance.approved` event emitted
- Notification created in DB

**Status:** 🔲 Not Tested (need to run)

---

### 5.2 No Cross-Module Direct Imports (Except Backup)

**Verification:**
```bash
grep -rn "from app.modules.*import" backend/app/modules/ | grep -v backup | grep -v "from app.modules.notifications.models\|from app.modules.attendance.models"
```

**Pass Criteria:**
- No matches (or only within same module)
- Backup module is exception (documented)

**Status:** ✅ Pass (verified in GAP_REPORT.md)

---

## Section 6: Database & Migrations

### 6.1 All Migrations Applied

**Verification:**
```bash
cd backend
alembic current
```

**Pass Criteria:**
- Shows latest migration (currently 003, should be 005+ after Phase 9-10)

**Status:** ⚠️ Partial (003 applied, but 004-005 missing)

---

### 6.2 Migrations Can Upgrade/Downgrade

**Verification:**
```bash
cd backend
alembic downgrade -1
alembic upgrade head
```

**Pass Criteria:**
- Both commands succeed
- No errors

**Status:** 🔲 Not Tested (need to run)

---

### 6.3 Notifications Has Migration (Not Auto-Create)

**Verification:**
```bash
ls backend/alembic/versions/ | grep notifications
```

**Pass Criteria:**
- Migration file exists (e.g., `004_create_notifications.py`)

**Status:** ❌ Fail (uses auto-create, violates spec)

**Required:** Future WP (P1)

---

## Section 7: Tests

### 7.1 All Tests Can Be Collected

**Verification:**
```bash
cd backend
pytest --collect-only
```

**Pass Criteria:**
- No errors during collection
- Shows count: "collected X items"

**Status:** ⚠️ Partial (collected 82 items / 1 error)

**Action:** Fix the 1 error before WP-09

---

### 7.2 All Existing Tests Pass

**Verification:**
```bash
cd backend
pytest -v
```

**Pass Criteria:**
- All tests pass (or known failures documented)

**Status:** 🔲 Not Tested (need to run)

**Action:** Run before WP-09

---

### 7.3 Test Coverage > 80%

**Verification:**
```bash
cd backend
pytest --cov=app --cov-report=term-missing
```

**Pass Criteria:**
- Coverage > 80% for core modules

**Status:** 🔲 Not Tested (need to run)

---

## Summary

| Section | Total Items | ✅ Pass | ❌ Fail | ⚠️ Partial | 🔲 Not Tested |
|---------|-------------|---------|---------|------------|---------------|
| 1. Tenant Isolation | 8 | 4 | 1 | 0 | 3 |
| 2. Tenants Module | 4 | 0 | 4 | 0 | 0 |
| 3. Auth Module | 5 | 0 | 5 | 0 | 0 |
| 4. Attendance Core | 14 | 0 | 14 | 0 | 0 |
| 5. Cross-Module | 2 | 1 | 0 | 0 | 1 |
| 6. Database | 3 | 0 | 1 | 1 | 1 |
| 7. Tests | 3 | 0 | 0 | 1 | 2 |
| **Total** | **39** | **5** | **25** | **2** | **7** |

**Pass Rate:** 5/39 = 12.8%

**Critical Failures (P0):** 25 items

**Next Actions:**
1. Run full test suite to verify baseline
2. Start WP-09-01 (Tenants migration)
3. Work through WP-09 to WP-11 to fix all P0 failures
