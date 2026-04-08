# Gap Report — Missing Components & Violations

**Generated:** 2026-03-02  
**Purpose:** Identify gaps between current state and specifications

---

## Executive Summary

**Current State:** Phase 0-8 complete (EventBus, DB baseline, Backup, Audit, Notifications, Tenant Isolation foundation)

**Critical Gaps (P0):**
1. Tenant context does NOT enforce tenant existence/active status
2. Tenants module completely missing
3. Auth module completely missing (no JWT, no RBAC)
4. Attendance core logic missing (0/8 regression tests passing)

**Risk Level:** 🔴 HIGH — System accepts any `company_id` without validation (security risk)

---

## Gap 1: Tenant Context Validation (P0) 🔴

### Current Behavior
```python
# core/tenant_context.py
def get_current_company_id(x_company_id: str = Header(...)):
    if not x_company_id or not x_company_id.strip():
        raise HTTPException(400, "Missing X-Company-ID header")
    return x_company_id.strip()  # ❌ Accepts ANY value
```

### Problem
- Accepts `X-Company-ID: non-existent-company` without checking DB
- Does NOT query `tenants` table (table doesn't exist yet)
- Does NOT check `is_active` flag
- Does NOT return 404 for non-existent tenant
- Does NOT return 403 for inactive tenant

### Required Behavior (per DEVELOPMENT_ORDER.md WP-09-05)
```python
def get_current_company_id(x_company_id: str = Header(...), db: Session = Depends(get_db)):
    if not x_company_id:
        raise HTTPException(400, "Missing X-Company-ID header")
    
    # Check tenant exists
    tenant = tenants_repo.get_by_id(x_company_id)
    if not tenant:
        raise HTTPException(404, "Tenant not found")  # ✅ Required
    
    # Check tenant active
    if not tenant.is_active:
        raise HTTPException(403, "Tenant inactive")  # ✅ Required
    
    return x_company_id
```

### Impact
- **Security Risk:** Malicious client can send any `company_id` and access system
- **Data Integrity Risk:** Can create data for non-existent tenants
- **Violates:** SA_MODULE_SPEC v1.7 §11 (Tenant Isolation P0)
- **Violates:** DEVELOPMENT_ORDER.md WP-09-05

### Blocker
- Requires `tenants` table to exist (WP-09-01)
- Requires `tenants` repo (WP-09-02)

### Fix
- **WP-09-01:** Create tenants migration
- **WP-09-02:** Create tenants model/repo
- **WP-09-05:** Update `tenant_context.py` to enforce checks

### Severity
🔴 **P0 — Critical**

---

## Gap 2: Tenants Module Missing (P0) 🔴

### Current State
```bash
$ ls backend/app/modules/
attendance  audit  backup  notifications
# ❌ No tenants/ folder
```

### Missing Components
- ❌ `tenants/` folder
- ❌ Migration `004_create_tenants.py`
- ❌ `tenants/models.py` (Tenant model)
- ❌ `tenants/repo.py` (CRUD)
- ❌ `tenants/service.py` (validation)
- ❌ `tenants/api.py` (REST endpoints)
- ❌ `tenants/tests/` (unit + feature tests)
- ❌ `tenants/docs.md`

### Impact
- Cannot enforce tenant existence (Gap 1)
- Cannot manage companies via API
- Cannot deactivate tenants
- Violates SA_MODULE_SPEC v1.7 (tenants is a required module)

### Fix
- **WP-09-01:** Migration only
- **WP-09-02:** Model + Repo + unit tests
- **WP-09-03:** Service + validation + unit tests
- **WP-09-04:** API + feature tests

### Severity
🔴 **P0 — Critical** (blocks Gap 1 fix)

---

## Gap 3: Auth Module Missing (P0) 🔴

### Current State
```bash
$ ls backend/app/modules/
attendance  audit  backup  notifications
# ❌ No auth/ folder

$ ls backend/app/core/
config.py  database.py  event_bus.py  tenant_context.py
# ❌ No security.py, no rbac.py, no dependencies.py
```

### Missing Components

#### 3.1 Auth Module
- ❌ `auth/` folder
- ❌ Migration `005_create_users.py`
- ❌ `auth/models.py` (User model)
- ❌ `auth/repo.py` (user CRUD + password verification)
- ❌ `auth/service.py` (login logic)
- ❌ `auth/api.py` (POST /api/auth/login)
- ❌ `auth/tests/`
- ❌ `auth/docs.md`

#### 3.2 Core Security
- ❌ `core/security.py` (JWT encode/decode, password hashing)
- ❌ `core/rbac.py` (role/permission logic)
- ❌ `core/dependencies.py` (FastAPI guards: `require_permission`, `get_current_user`)

### Impact
- No user identity (no `staff_id`, no roles)
- No JWT tokens
- No RBAC enforcement
- Cannot run regression tests 7-8 (customer_service, OTP)
- Still using insecure header-only auth
- Violates AUTH_TRANSITION_PLAN.md (Phase 10 not started)

### Fix
- **WP-10-01:** Auth schema design doc
- **WP-10-02:** Users migration + model
- **WP-10-03:** Auth repo + password hashing
- **WP-10-04:** JWT login API
- **WP-10-05:** RBAC logic
- **WP-10-06:** Migrate attendance endpoints to JWT (batch 1)

### Severity
🔴 **P0 — Critical** (blocks regression tests, blocks RBAC)

---

## Gap 4: Attendance Core Logic Missing (P0) 🔴

### Current State
- ✅ Attendance module exists
- ✅ Basic CRUD works
- ❌ No status enum (NO_MATCH, PENDING_APPROVAL, APPROVED)
- ❌ No IN/OUT pairing logic
- ❌ No work time calculation
- ❌ No day close logic
- ❌ No missing card detection
- ❌ No approve → recalculate logic

### Missing Components

#### 4.1 Status Enum
```python
# ❌ Missing in models.py
class AttendanceStatus(str, Enum):
    APPROVED = "APPROVED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    NO_MATCH = "NO_MATCH"
    REJECTED = "REJECTED"
```

#### 4.2 Model Fields
```python
# Current model (incomplete)
class AttendanceRecord(Base):
    id = Column(UUID)
    company_id = Column(String)
    employee_id = Column(String)
    approved_by = Column(String)
    approved_at = Column(DateTime)
    created_at = Column(DateTime)
    # ❌ Missing: status, type, timestamp, reason
```

#### 4.3 Business Logic
- ❌ `attendance/inference.py` (pairing logic)
- ❌ `attendance/day_close.py` (day close logic)
- ❌ Validation: NO_MATCH must have reason
- ❌ Approve → recalculate day

### Impact
- 0/8 regression tests passing
- Cannot validate core business rules
- Cannot detect missing cards
- Cannot calculate work time
- Violates ATTENDANCE_REGRESSION_SPEC.md (all 8 tests fail)

### Fix
- **WP-11-01:** Status enum + state machine doc
- **WP-11-02:** IN/OUT pairing logic
- **WP-11-03:** Work time calculation
- **WP-11-04:** Day close + missing card detection
- **WP-11-05:** Approve → recalculate
- **WP-11-06:** Implement 8 regression tests

### Severity
🔴 **P0 — Critical** (core business logic)

---

## Gap 5: Notifications Migration Missing (P1) 🟡

### Current State
```python
# notifications module uses auto-create
Base.metadata.create_all(bind=engine)  # ❌ Not via Alembic
```

### Problem
- Violates SA_MODULE_SPEC v1.7: "Alembic is the source of truth"
- Migration history incomplete
- Cannot track schema changes
- Harder to rollback

### Impact
- **Functional:** System works, but not following best practice
- **Maintenance:** Harder to manage schema evolution

### Fix
- Create `004_create_notifications.py` migration (or renumber after tenants/users)
- Remove auto-create logic
- Apply migration

### Severity
🟡 **P1 — Medium** (functional but violates spec)

---

## Gap 6: Module Boundary Violations (P1) 🟡

### Current State
```python
# backup/importer.py
from app.modules.notifications.models import Notification  # ⚠️ Cross-module import
from app.modules.attendance.models import AttendanceRecord  # ⚠️ Cross-module import
```

### Problem
- Backup module directly imports models from other modules
- Violates SA_MODULE_SPEC v1.7 §2: "禁止跨模組直接 import 對方 service/repo/models"

### Analysis
- **Tolerable:** Backup is a special case (needs to know all Tenant Data tables)
- **Not P0:** System functional, just architectural concern

### Recommendation
- Document this as an **exception** in SA_MODULE_SPEC v1.7
- Add comment in backup code explaining why this is allowed
- Alternative: Create a central registry of Tenant Data tables

### Severity
🟡 **P1 — Low** (tolerable exception)

---

## Gap 7: Test Execution Status (P1) 🟡

### Current State
```bash
$ pytest --collect-only
collected 82 items / 1 error
```

### Problem
- 1 error during test collection (likely import or config issue)
- Unknown if all 82 tests pass

### Impact
- Cannot verify current functionality
- Cannot run regression tests
- CI/CD blocked

### Fix
- Run full test suite: `pytest -v`
- Identify and fix the 1 error
- Ensure all tests pass before proceeding to WP-09

### Severity
🟡 **P1 — Medium** (need to verify baseline)

---

## Gap 8: Missing Spec Documents (P2) 🟢

### Current State
- ✅ `DEVELOPMENT_ORDER.md` exists
- ✅ `AUTH_TRANSITION_PLAN.md` exists
- ✅ `ATTENDANCE_REGRESSION_SPEC.md` exists
- ❌ `AUTH_SCHEMA_SPEC.md` missing (required by WP-10-01)
- ❌ `ATTENDANCE_STATE_MACHINE.md` missing (required by WP-11-01)
- ❌ `SYSTEM_BLUEPRINT_SAAS_MULTI_TENANT_v1.md` missing (this report will create it)

### Impact
- Cannot start WP-10-01 without auth schema spec
- Cannot start WP-11-01 without state machine spec

### Fix
- WP-10-01 will create `AUTH_SCHEMA_SPEC.md`
- WP-11-01 will create `ATTENDANCE_STATE_MACHINE.md`
- This report creates `SYSTEM_BLUEPRINT_SAAS_MULTI_TENANT_v1.md`

### Severity
🟢 **P2 — Low** (will be created as part of WPs)

---

## Summary Table

| Gap # | Component | Severity | Blocker For | Required WP |
|-------|-----------|----------|-------------|-------------|
| 1 | Tenant context validation | 🔴 P0 | Security | WP-09-05 |
| 2 | Tenants module | 🔴 P0 | Gap 1 | WP-09-01 to WP-09-04 |
| 3 | Auth module | 🔴 P0 | RBAC, Tests 7-8 | WP-10-01 to WP-10-06 |
| 4 | Attendance core logic | 🔴 P0 | Tests 1-6 | WP-11-01 to WP-11-06 |
| 5 | Notifications migration | 🟡 P1 | Best practice | (Future WP) |
| 6 | Module boundary | 🟡 P1 | Architecture | (Document exception) |
| 7 | Test execution | 🟡 P1 | CI/CD | (Fix before WP-09) |
| 8 | Missing specs | 🟢 P2 | WP-10/11 start | WP-10-01, WP-11-01 |

---

## Critical Path

```
WP-09-01 (Tenants migration)
    ↓
WP-09-02 (Tenants model/repo)
    ↓
WP-09-03 (Tenants service)
    ↓
WP-09-04 (Tenants API)
    ↓
WP-09-05 (Tenant context enforce) ← Fixes Gap 1 🔴
    ↓
WP-10-01 (Auth schema spec)
    ↓
WP-10-02 to WP-10-06 (Auth module) ← Fixes Gap 3 🔴
    ↓
WP-11-01 to WP-11-06 (Attendance core) ← Fixes Gap 4 🔴
```

**Estimated Time:** 17 WPs × 0.5-1 day = 8-17 days

---

## Recommendations

### Immediate Actions (Before Starting WP-09-01)
1. ✅ Run full test suite: `pytest -v` (fix any failures)
2. ✅ Verify DB connection and migrations applied
3. ✅ Review this Gap Report with team
4. ✅ Confirm WP-09-01 is the correct next step

### Phase 9 (Tenants)
- **Priority:** 🔴 P0
- **Duration:** 2-3 days (5 WPs)
- **Goal:** Fix Gap 1 + Gap 2

### Phase 10 (Auth)
- **Priority:** 🔴 P0
- **Duration:** 3-4 days (6 WPs)
- **Goal:** Fix Gap 3

### Phase 11 (Attendance Core)
- **Priority:** 🔴 P0
- **Duration:** 3-4 days (6 WPs)
- **Goal:** Fix Gap 4, pass 8 regression tests

### Future (P1/P2)
- Add notifications migration (Gap 5)
- Document module boundary exception (Gap 6)
- Create missing spec docs as needed (Gap 8)

---

**Next Step:** Proceed to WP-09-01 (Tenants migration)
