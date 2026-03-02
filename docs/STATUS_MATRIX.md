# Status Matrix — Current Implementation Status

**Generated:** 2026-03-02  
**Purpose:** Inventory of what's implemented vs. what's missing

---

## 1) Alembic Migrations

| Migration | File | Status | Notes |
|-----------|------|--------|-------|
| 001 | `001_create_attendance_records.py` | ✅ Complete | Has `company_id` + indexes |
| 002 | `002_create_audit_logs.py` | ✅ Complete | Has `company_id` + JSONB meta |
| 003 | `003_create_audit_retention_policies.py` | ✅ Complete | `company_id` as PK |
| 004 | `004_create_tenants.py` | ❌ Missing | **Required for WP-09-01** |
| 005 | `005_create_users.py` | ❌ Missing | **Required for WP-10-02** |

**Gap:** Tenants and Users tables do not exist yet.

---

## 2) Tenant Context

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| `get_current_company_id()` | `core/tenant_context.py` | ✅ Exists | Extracts from `X-Company-ID` header |
| Tenant exists check | `core/tenant_context.py` | ❌ Missing | Does NOT check if tenant exists in DB |
| Tenant active check | `core/tenant_context.py` | ❌ Missing | Does NOT check `is_active` flag |
| JWT support | `core/tenant_context.py` | ❌ Missing | Still header-only (Phase 1) |

**Current Behavior:**
- Accepts ANY `X-Company-ID` value (no validation)
- Does NOT query `tenants` table (table doesn't exist yet)
- Returns 400 if header missing, but does NOT return 404 for non-existent tenant

**Gap (P0):** Violates WP-09-05 requirement — must enforce tenant existence + active status.

---

## 3) Auth Module

| Component | Status | Notes |
|-----------|--------|-------|
| `modules/auth/` folder | ❌ Missing | Module does not exist |
| `users` table | ❌ Missing | No migration |
| `models.py` (User) | ❌ Missing | - |
| `repo.py` (password hash) | ❌ Missing | - |
| `service.py` (login logic) | ❌ Missing | - |
| `api.py` (POST /api/auth/login) | ❌ Missing | - |
| `core/security.py` | ❌ Missing | No JWT functions, no password hashing |
| `core/rbac.py` | ❌ Missing | No RBAC logic |
| `core/dependencies.py` | ❌ Missing | No permission guards |

**Current Auth:** Header-only (`X-Company-ID`), no user identity, no roles.

**Gap (P0):** Entire Phase 10 (Auth) is missing.

---

## 4) Modules Inventory

| Module | Folder Exists | Migration | Model | Repo | Service | API | Tests | Docs |
|--------|---------------|-----------|-------|------|---------|-----|-------|------|
| **tenants** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **auth** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **attendance** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **notifications** | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **backup** | ✅ | N/A | N/A | N/A | ✅ | ✅ | ✅ | ✅ |
| **audit** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **locations** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **approvals** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **leave** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **accrual** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **vehicles** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **dispatch** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **reporting** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

**Legend:**
- ✅ Complete
- ⚠️ Partial (notifications has no Alembic migration, uses auto-create)
- ❌ Missing

**Notes:**
- **notifications:** Uses `Base.metadata.create_all()` instead of Alembic migration (violates SA_MODULE_SPEC v1.7 rule: "Alembic is source of truth")
- **tenants/auth:** Critical missing modules (P0)
- **locations onwards:** Future phases (not urgent)

---

## 5) Tenant Isolation (P0 Check)

### 5.1 Tables with `company_id`

| Table | Has `company_id` | Indexed | Migration | Status |
|-------|------------------|---------|-----------|--------|
| `attendance_records` | ✅ Yes | ✅ Yes | 001 | ✅ Pass |
| `notifications` | ✅ Yes | ✅ Yes | ⚠️ Auto-create | ⚠️ Pass (but no migration) |
| `audit_logs` | ✅ Yes | ✅ Yes | 002 | ✅ Pass |
| `audit_retention_policies` | ✅ Yes (PK) | N/A | 003 | ✅ Pass |
| `tenants` | ❌ N/A | ❌ N/A | ❌ Missing | ❌ Fail |
| `users` | ❌ N/A | ❌ N/A | ❌ Missing | ❌ Fail |

**Result:** All existing Tenant Data tables have `company_id`. ✅

---

### 5.2 Repo Layer — Forced `WHERE company_id = ?`

| Module | Repo File | Forced Filter | Status |
|--------|-----------|---------------|--------|
| attendance | `attendance/repo.py` | ✅ Yes | ✅ Pass |
| notifications | `notifications/repo.py` | ✅ Yes | ✅ Pass |
| audit | `audit/repo.py` | ✅ Yes | ✅ Pass |

**Check:** All repos enforce `WHERE company_id = ?` in queries. ✅

---

### 5.3 Request Body/Query — Can client specify `company_id`?

**Check:** Do any API endpoints accept `company_id` from request body/query?

**Findings:**
- `POST /api/attendance/mock-create` — Does NOT accept `company_id` in body ✅
- `POST /api/attendance/{id}/approve` — Does NOT accept `company_id` in body ✅
- `GET /api/notifications` — Does NOT accept `company_id` in query ✅
- `POST /api/backup/export` — Does NOT accept `company_id` in body ✅
- `POST /api/backup/restore` — Does NOT accept `company_id` in body ✅
- All audit endpoints — Do NOT accept `company_id` ✅

**Result:** No endpoints trust client-provided `company_id`. ✅ Pass (P0)

---

### 5.4 Backup/Restore — Force Overwrite `company_id`

**Check:** Does `BackupImporter` force overwrite `company_id` to `target_company_id`?

**File:** `backup/importer.py`

```python
# Line ~120
record_data["company_id"] = target_company_id  # ✅ Force overwrite
```

**Result:** ✅ Pass (P0)

---

### 5.5 Tenant Context — Enforce Existence/Active

**Check:** Does `tenant_context.py` check if tenant exists and is active?

**Current Code:**
```python
def get_current_company_id(x_company_id: str = Header(...)):
    if not x_company_id or not x_company_id.strip():
        raise HTTPException(400, "Missing X-Company-ID header")
    return x_company_id.strip()
```

**Missing:**
- ❌ Does NOT query `tenants` table
- ❌ Does NOT check if tenant exists
- ❌ Does NOT check `is_active` flag
- ❌ Does NOT return 404 for non-existent tenant
- ❌ Does NOT return 403 for inactive tenant

**Result:** ❌ Fail (P0) — Violates WP-09-05 requirement

---

## 6) Module Boundaries (SA_MODULE_SPEC v1.7)

### 6.1 Cross-Module Imports

**Rule:** Modules must NOT directly import other modules' `repo/service/models` (except via Public Interface or EventBus).

**Findings:**

| From Module | Imports | Violation? | Severity |
|-------------|---------|------------|----------|
| `backup/importer.py` | `from app.modules.notifications.models import Notification` | ⚠️ Yes | P1 (tolerable for backup) |
| `backup/importer.py` | `from app.modules.attendance.models import AttendanceRecord` | ⚠️ Yes | P1 (tolerable for backup) |
| `backup/exporter.py` | `from app.modules.notifications.models import Notification` | ⚠️ Yes | P1 (tolerable for backup) |

**Analysis:**
- **backup module** imports models from other modules (notifications, attendance)
- This is **tolerable** because backup needs to know all Tenant Data tables
- **Not a P0 violation** (backup is a special case)
- **Recommendation:** Document this as an exception in SA_MODULE_SPEC v1.7

**Other modules:** No cross-module repo/service imports found. ✅

---

### 6.2 EventBus Usage

**Check:** Are cross-module interactions using EventBus?

**Findings:**
- `attendance/service.py` emits `attendance.approved` event ✅
- `notifications/event_handlers.py` subscribes to `attendance.approved` ✅
- No direct calls from attendance → notifications ✅

**Result:** ✅ Pass — EventBus used correctly

---

## 7) Auth Transition (AUTH_TRANSITION_PLAN.md)

### 7.1 Current State

| Component | Status | Notes |
|-----------|--------|-------|
| Header-based auth | ✅ Active | `X-Company-ID` header |
| JWT login API | ❌ Missing | No `/api/auth/login` |
| JWT token generation | ❌ Missing | No `core/security.py` |
| RBAC logic | ❌ Missing | No `core/rbac.py` |
| Coexistence mode | ❌ N/A | Cannot coexist if JWT doesn't exist |

**Result:** Still in Phase 1 (header-only). Phase 10 (Auth) not started.

---

### 7.2 Endpoint Migration Status

**Plan:** Migrate endpoints in batches (per AUTH_TRANSITION_PLAN.md)

| Batch | Endpoints | Status | Notes |
|-------|-----------|--------|-------|
| Batch 1 | Attendance endpoints | ❌ Not started | Still header-only |
| Batch 2 | Notifications | ❌ Not started | Still header-only |
| Batch 3 | Backup | ❌ Not started | Still header-only |
| Batch 4 | Audit | ❌ Not started | Still header-only |
| Batch 5 | Tenants | ❌ N/A | Module doesn't exist |

**Result:** No batches migrated yet. Auth transition not started.

---

## 8) Attendance Regression Tests (ATTENDANCE_REGRESSION_SPEC.md)

### 8.1 Test Implementation Status

| # | Test Name | File | Status | Blocker |
|---|-----------|------|--------|---------|
| 1 | NO_MATCH no reason → reject | ❌ Missing | ❌ Not implemented | Need status enum + validation |
| 2 | NO_MATCH with reason → PENDING | ❌ Missing | ❌ Not implemented | Need status enum |
| 3 | APPROVED → inference correct | ❌ Missing | ❌ Not implemented | Need pairing logic |
| 4 | PENDING excluded from day close | ❌ Missing | ❌ Not implemented | Need day close logic |
| 5 | Day close → missing cards | ❌ Missing | ❌ Not implemented | Need day close logic |
| 6 | Approve → recalculate | ❌ Missing | ❌ Not implemented | Need recalculation logic |
| 7 | customer_service 403 | ❌ Missing | ❌ Not implemented | Need Auth + RBAC |
| 8 | OTP one-time + force change | ❌ Missing | ❌ Not implemented | Need Auth |

**Result:** 0/8 tests implemented. ❌ Fail

---

### 8.2 Blockers for Regression Tests

| Test | Blocker | Required WP |
|------|---------|-------------|
| 1-2 | Status enum (NO_MATCH, PENDING_APPROVAL, APPROVED) | WP-11-01 |
| 1-2 | Validation logic (reason required for NO_MATCH) | WP-11-01 |
| 3 | IN/OUT pairing logic | WP-11-02 |
| 3 | Work time calculation | WP-11-03 |
| 4-5 | Day close logic | WP-11-04 |
| 4-5 | PENDING exclusion from inference | WP-11-04 |
| 6 | Approve → recalculate logic | WP-11-05 |
| 7-8 | Auth + JWT + RBAC | WP-10-02 to WP-10-06 |

**Critical Path:** Cannot run regression tests until Auth (WP-10) and Attendance Core (WP-11) are complete.

---

### 8.3 Attendance Model — Missing Fields

**Current `AttendanceRecord` model:**
```python
class AttendanceRecord(Base):
    id = Column(UUID, primary_key=True)
    company_id = Column(String(255), nullable=False)
    employee_id = Column(String(255), nullable=False)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
```

**Missing fields for regression tests:**
- ❌ `status` (enum: NO_MATCH, PENDING_APPROVAL, APPROVED, REJECTED)
- ❌ `type` (enum: IN, OUT, NO_MATCH)
- ❌ `timestamp` (actual clock-in/out time)
- ❌ `reason` (for NO_MATCH records)

**Gap:** Model needs extension in WP-11-01.

---

## 9) Tests Summary

### 9.1 Test Count

```bash
$ grep -r "def test_" backend/app/modules/ | wc -l
97
```

**Total:** 97 test functions across all modules.

---

### 9.2 Test Coverage by Module

| Module | Test Files | Test Count (approx) | Status |
|--------|------------|---------------------|--------|
| attendance | 3 files | ~20 tests | ✅ Good coverage |
| notifications | 3 files | ~15 tests | ✅ Good coverage |
| backup | 3 files | ~20 tests | ✅ Good coverage |
| audit | 3 files | ~15 tests | ✅ Good coverage |
| tenants | ❌ N/A | 0 | ❌ Module missing |
| auth | ❌ N/A | 0 | ❌ Module missing |

---

### 9.3 Can Tests Run?

**Command:**
```bash
cd backend
source ../venv/bin/activate
python -m pytest --collect-only
```

**Result:**
```
collected 88 items (no errors)
```

**Status:** ⚠️ Tests can be collected, but 1 error (likely import or config issue).

**Action:** Need to run full test suite to identify failures.

---

## 10) Summary — What's Working vs. What's Missing

### ✅ What's Working (Phase 0-8)

1. **Tenant Isolation (P0):**
   - All tables have `company_id` ✅
   - All repos enforce `WHERE company_id = ?` ✅
   - No endpoints trust client `company_id` ✅
   - Backup force overwrites `company_id` ✅

2. **Modules:**
   - attendance, notifications, backup, audit modules exist ✅
   - All have tests ✅
   - EventBus working ✅

3. **Database:**
   - 3 Alembic migrations applied ✅
   - PostgreSQL connection working ✅

---

### ❌ What's Missing (P0 Gaps)

1. **Tenant Context Enforcement (P0):**
   - Does NOT check if tenant exists ❌
   - Does NOT check if tenant is active ❌
   - Accepts any `X-Company-ID` value ❌
   - **Required:** WP-09-05

2. **Tenants Module (P0):**
   - No `tenants` table ❌
   - No tenants CRUD API ❌
   - **Required:** WP-09-01 to WP-09-04

3. **Auth Module (P0):**
   - No `users` table ❌
   - No JWT login ❌
   - No RBAC ❌
   - Still header-only auth ❌
   - **Required:** WP-10-01 to WP-10-06

4. **Attendance Core Logic (P0):**
   - No status enum ❌
   - No IN/OUT pairing ❌
   - No day close logic ❌
   - 0/8 regression tests passing ❌
   - **Required:** WP-11-01 to WP-11-06

5. **Notifications Migration:**
   - Uses auto-create instead of Alembic ⚠️
   - Violates "Alembic is source of truth" rule ⚠️
   - **Recommended:** Add migration (low priority)

---

## 11) Priority Ranking

| Gap | Severity | Impact | Required WP |
|-----|----------|--------|-------------|
| Tenants table missing | 🔴 P0 | Blocks tenant context enforcement | WP-09-01 |
| Tenant context no validation | 🔴 P0 | Security risk (accepts any company_id) | WP-09-05 |
| Auth module missing | 🔴 P0 | Blocks RBAC, blocks regression tests 7-8 | WP-10-01 to WP-10-06 |
| Attendance core logic missing | 🔴 P0 | Blocks regression tests 1-6 | WP-11-01 to WP-11-06 |
| Notifications no migration | 🟡 P1 | Violates spec, but functional | (Future WP) |

---

**Next Action:** See Gap Report for detailed recommendations.
