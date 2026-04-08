# System Blueprint — SaaS Multi-Tenant Architecture v1

**Document Version:** 1.0  
**Created:** 2026-03-02  
**Purpose:** Single source of truth for system architecture and design decisions

---

## 1) Architecture Type

### A Architecture (同庫同表 + company_id 隔離)

**Definition:**
- **Single Database:** All tenants share one PostgreSQL database
- **Single Schema:** All tenants share same tables
- **Tenant Isolation:** Via `company_id` column in every Tenant Data table
- **Query Enforcement:** All queries must filter by `company_id`

**Why A Architecture:**
- Simpler deployment (one DB instance)
- Easier backup/restore (single DB dump)
- Cost-effective for small-medium scale
- Suitable for B2B SaaS with moderate tenant count

**Trade-offs:**
- ❌ Less isolation than B/C architecture (separate DB per tenant)
- ❌ Risk of cross-tenant data leak if code bug
- ✅ Simpler to manage
- ✅ Lower infrastructure cost

---

## 2) Data Classification

### 2.1 Tenant Data (租戶資料)

**Definition:** Data that belongs to a specific company/tenant.

**Hard Rules:**
- ✅ MUST have `company_id` column (non-nullable, indexed)
- ✅ MUST filter by `company_id` in all queries
- ✅ MUST NOT accept `company_id` from client request body/query
- ✅ MUST inject `company_id` from Tenant Context (server-side)

**Tables:**
| Table | Migration | Status |
|-------|-----------|--------|
| `attendance_records` | 001 | ✅ Exists |
| `notifications` | ⚠️ Auto-create | ⚠️ Exists (no migration) |
| `audit_logs` | 002 | ✅ Exists |
| `audit_retention_policies` | 003 | ✅ Exists |
| `tenants` | 004 | ❌ Missing (WP-09-01) |
| `users` | 005 | ❌ Missing (WP-10-02) |
| `locations` | Future | ❌ Not planned yet |
| `leave_requests` | Future | ❌ Not planned yet |
| `accrual_ledger` | Future | ❌ Not planned yet |

---

### 2.2 System Data (系統資料)

**Definition:** Data that is global/shared across all tenants.

**Hard Rules:**
- ✅ MUST NOT have `company_id` column
- ✅ Read-only for most users (admin-only write)
- ✅ MUST NOT reference Tenant Data as foreign key

**Tables (Future):**
- `permission_codes` (RBAC permission definitions)
- `system_settings` (global config)
- `feature_flags` (global feature toggles)

**Note:** Currently no System Data tables exist (all tables are Tenant Data).

---

## 3) Request Context Flow

### 3.1 Current State (Phase 0-8): Header-Based

```
Client Request
    ↓
Header: X-Company-ID: company-A
    ↓
FastAPI Dependency: get_current_company_id()
    ↓
Extract company_id from header
    ↓
⚠️ NO VALIDATION (accepts any value)
    ↓
Inject into repo/service calls
    ↓
Repo: WHERE company_id = 'company-A'
```

**Problems:**
- ❌ No tenant existence check
- ❌ No tenant active status check
- ❌ Client can send any `company_id`
- ❌ No user identity (no `staff_id`, no roles)

---

### 3.2 Target State (Phase 10+): JWT-Based

```
Client Request
    ↓
Header: Authorization: Bearer <JWT>
    ↓
FastAPI Dependency: get_current_user()
    ↓
Decode JWT → Extract claims:
    - company_id
    - staff_id
    - roles: ["employee", "manager", ...]
    ↓
Validate JWT signature
    ↓
Check tenant exists in DB (tenants table)
    ↓
Check tenant is_active = true
    ↓
Check user has required permission (RBAC)
    ↓
Inject company_id + user into repo/service calls
    ↓
Repo: WHERE company_id = <from JWT>
```

**Benefits:**
- ✅ Tenant existence enforced
- ✅ Tenant active status enforced
- ✅ User identity tracked
- ✅ RBAC enforced
- ✅ Cannot forge `company_id` (server-signed JWT)

---

### 3.3 Transition Strategy (AUTH_TRANSITION_PLAN.md)

**Phase 1: Coexistence (WP-10-04)**
- JWT login API available
- Existing endpoints still accept header
- New endpoints can optionally require JWT

**Phase 2: Batch Migration (WP-10-06+)**
- Migrate endpoints in batches:
  - Batch 1: Attendance
  - Batch 2: Notifications
  - Batch 3: Backup
  - Batch 4: Audit
  - Batch 5: Tenants

**Phase 3: Header Removal (Future)**
- Remove `X-Company-ID` header support
- All endpoints require JWT

---

## 4) Module Boundaries (SA_MODULE_SPEC v1.7)

### 4.1 Module Structure

**Required Files (per module):**
```
backend/app/modules/<module_name>/
    __init__.py
    models.py       # SQLAlchemy ORM models
    repo.py         # Data access layer (CRUD)
    service.py      # Business logic
    api.py          # FastAPI routes
    docs.md         # API documentation
    tests/          # Unit + feature tests
        __init__.py
        test_api.py
        test_service.py
        test_repo.py
        test_tenant_isolation.py
```

---

### 4.2 Module List

| Module | Status | Phase | Priority |
|--------|--------|-------|----------|
| **tenants** | ❌ Missing | 9 | 🔴 P0 |
| **auth** | ❌ Missing | 10 | 🔴 P0 |
| **attendance** | ✅ Exists | 1,4,11 | 🔴 P0 |
| **notifications** | ✅ Exists | 2 | ✅ Done |
| **backup** | ✅ Exists | 3,5 | ✅ Done |
| **audit** | ✅ Exists | 6,7,8 | ✅ Done |
| **locations** | ❌ Missing | Future | 🟡 P1 |
| **approvals** | ❌ Missing | Future | 🟡 P1 |
| **leave** | ❌ Missing | Future | 🟡 P1 |
| **accrual** | ❌ Missing | Future | 🟡 P1 |
| **vehicles** | ❌ Missing | Future | 🟠 P2 |
| **dispatch** | ❌ Missing | Future | 🟠 P2 |
| **reporting** | ❌ Missing | Future | 🟠 P2 |

---

### 4.3 Cross-Module Interaction Rules

**Forbidden:**
- ❌ Direct import of other module's `repo/service/models`
- ❌ Direct write to other module's tables
- ❌ Circular dependencies

**Allowed:**
- ✅ EventBus (preferred for async cross-module communication)
- ✅ Public Interface (minimal, for sync queries)

**Example (EventBus):**
```python
# attendance/service.py
def approve_attendance(record_id):
    # ... update record ...
    event_bus.emit("attendance.approved", {
        "record_id": record_id,
        "company_id": company_id,
        "employee_id": employee_id
    })

# notifications/event_handlers.py
@event_bus.subscribe("attendance.approved")
def handle_attendance_approved(event):
    # Create notification
    notification_repo.create(...)
```

**Exception (Backup Module):**
- Backup module MAY import models from other modules (to know Tenant Data tables)
- This is documented as an exception in SA_MODULE_SPEC v1.7

---

## 5) Module Dependency Graph

### 5.1 Current Dependencies (Phase 0-8)

```
┌─────────────┐
│   tenants   │ (missing)
└─────────────┘
       ↑
       │ (will depend on)
       │
┌─────────────┐
│    auth     │ (missing)
└─────────────┘
       ↑
       │ (will depend on)
       │
┌─────────────┐     ┌─────────────┐
│ attendance  │────→│notifications│
└─────────────┘     └─────────────┘
       ↑                   ↑
       │                   │
       └───────┬───────────┘
               │
         ┌─────────────┐
         │   backup    │
         └─────────────┘
               ↑
               │
         ┌─────────────┐
         │    audit    │
         └─────────────┘
```

**Legend:**
- `A → B` = A emits event, B subscribes
- `A ← B` = B depends on A (via Public Interface)

---

### 5.2 Target Dependencies (Phase 9-11)

```
┌─────────────┐
│   tenants   │ ← tenant_context depends on this
└─────────────┘
       ↑
       │
┌─────────────┐
│    auth     │ ← all protected endpoints depend on this
└─────────────┘
       ↑
       │
┌─────────────┐     ┌─────────────┐
│ attendance  │────→│notifications│
└─────────────┘     └─────────────┘
       ↑                   ↑
       │                   │
       └───────┬───────────┘
               │
         ┌─────────────┐
         │   backup    │ ← imports models (exception)
         └─────────────┘
               ↑
               │
         ┌─────────────┐
         │    audit    │ ← logs all operations
         └─────────────┘
```

---

### 5.3 Forbidden Dependencies

**Rule:** Lower-level modules MUST NOT depend on higher-level modules.

**Forbidden:**
- ❌ `tenants` → `auth` (tenants is lower-level)
- ❌ `auth` → `attendance` (auth is lower-level)
- ❌ `notifications` → `attendance` (would create circular dependency)

**Allowed:**
- ✅ `auth` → `tenants` (auth can query tenants)
- ✅ `attendance` → `notifications` (via EventBus)
- ✅ `backup` → all modules (special case)

---

## 6) P0 Non-Negotiables

### 6.1 Tenant Isolation (P0)

**Rules:**
1. All Tenant Data tables MUST have `company_id`
2. All queries MUST filter by `company_id`
3. No endpoint MAY accept `company_id` from client
4. Backup/restore MUST force overwrite `company_id`
5. Tenant context MUST enforce tenant existence + active status

**Verification:** See ACCEPTANCE_CHECKLIST.md Section 1

---

### 6.2 Single-Tenant Backup/Restore (P0)

**Rules:**
1. Export MUST include only one `company_id`
2. Restore MUST reject multi-company backup files
3. Restore MUST force overwrite all `company_id` to target
4. Restore MUST use transaction (rollback on failure)

**Verification:** See ACCEPTANCE_CHECKLIST.md Section 5

---

### 6.3 Attendance 8 Regression Tests (P0)

**Rules:**
1. NO_MATCH without reason → reject
2. NO_MATCH with reason → PENDING_APPROVAL
3. APPROVED → inference correct
4. PENDING_APPROVAL excluded from inference/day close
5. Day close at 21:00 → missing cards detected
6. Approve PENDING → recalculate day
7. customer_service unassigned company → 403
8. OTP one-time use + force password change

**Verification:** See ACCEPTANCE_CHECKLIST.md Section 4

---

## 7) Database Schema Overview

### 7.1 Current Tables (Phase 0-8)

| Table | Type | company_id | Migration | Status |
|-------|------|------------|-----------|--------|
| `attendance_records` | Tenant Data | ✅ Yes | 001 | ✅ |
| `notifications` | Tenant Data | ✅ Yes | ⚠️ Auto | ⚠️ |
| `audit_logs` | Tenant Data | ✅ Yes | 002 | ✅ |
| `audit_retention_policies` | Tenant Data | ✅ Yes (PK) | 003 | ✅ |

---

### 7.2 Target Tables (Phase 9-11)

| Table | Type | company_id | Migration | Status |
|-------|------|------------|-----------|--------|
| `tenants` | Tenant Data | ✅ Yes (PK) | 004 | ❌ WP-09-01 |
| `users` | Tenant Data | ✅ Yes | 005 | ❌ WP-10-02 |

---

### 7.3 Foreign Key Strategy

**Current:** No foreign keys (to simplify single-tenant backup/restore)

**Future:** May add foreign keys with `ON DELETE CASCADE` (within same tenant only)

**Rule:** Foreign keys MUST NOT cross tenant boundaries.

---

## 8) API Endpoint Inventory

### 8.1 Current Endpoints (Phase 0-8)

| Endpoint | Method | Module | Auth | Status |
|----------|--------|--------|------|--------|
| `/health` | GET | core | None | ✅ |
| `/api/attendance/mock-create` | POST | attendance | Header | ✅ |
| `/api/attendance/{id}/approve` | POST | attendance | Header | ✅ |
| `/api/notifications` | GET | notifications | Header | ✅ |
| `/api/backup/export` | POST | backup | Header | ✅ |
| `/api/backup/restore` | POST | backup | Header | ✅ |
| `/api/audit/logs` | GET | audit | Header | ✅ |
| `/api/audit/export` | GET | audit | Header | ✅ |
| `/api/audit/retention` | GET | audit | Header | ✅ |
| `/api/audit/retention` | PUT | audit | Header | ✅ |
| `/api/audit/purge` | POST | audit | Header | ✅ |

**Total:** 11 endpoints (all header-based auth)

---

### 8.2 Target Endpoints (Phase 9-11)

| Endpoint | Method | Module | Auth | Status |
|----------|--------|--------|------|--------|
| `/api/tenants` | POST | tenants | JWT (admin) | ❌ WP-09-04 |
| `/api/tenants` | GET | tenants | JWT (admin) | ❌ WP-09-04 |
| `/api/tenants/{id}` | GET | tenants | JWT (admin) | ❌ WP-09-04 |
| `/api/tenants/{id}` | PATCH | tenants | JWT (admin) | ❌ WP-09-04 |
| `/api/tenants/{id}` | DELETE | tenants | JWT (admin) | ❌ WP-09-04 |
| `/api/auth/login` | POST | auth | None | ❌ WP-10-04 |
| `/api/auth/refresh` | POST | auth | JWT | ❌ WP-10-04 |

**Total (after Phase 9-10):** 18 endpoints

---

## 9) Testing Strategy

### 9.1 Test Pyramid

```
        ┌─────────────┐
        │   E2E (5%)  │ ← Full API flow tests
        └─────────────┘
       ┌───────────────┐
       │ Feature (20%) │ ← API endpoint tests
       └───────────────┘
      ┌─────────────────┐
      │  Unit (75%)     │ ← Repo/service/logic tests
      └─────────────────┘
```

---

### 9.2 Test Coverage Requirements

| Module | Unit Tests | Feature Tests | Tenant Isolation Tests |
|--------|------------|---------------|------------------------|
| tenants | ✅ Required | ✅ Required | ✅ Required |
| auth | ✅ Required | ✅ Required | ✅ Required |
| attendance | ✅ Exists | ✅ Exists | ✅ Exists |
| notifications | ✅ Exists | ✅ Exists | ✅ Exists |
| backup | ✅ Exists | ✅ Exists | ✅ Exists |
| audit | ✅ Exists | ✅ Exists | ✅ Exists |

---

### 9.3 Regression Test Suite

**Location:** `backend/app/modules/attendance/tests/test_regression.py`

**Status:** 0/8 tests implemented

**Required:** All 8 tests must pass before Phase 11 complete

**See:** ATTENDANCE_REGRESSION_SPEC.md for detailed test cases

---

## 10) Deployment & Operations

### 10.1 Environment

- **OS:** Debian 12 (LXC container)
- **Python:** 3.11.2
- **Framework:** FastAPI
- **ORM:** SQLAlchemy (sync)
- **Database:** PostgreSQL 15
- **Migration:** Alembic

---

### 10.2 Configuration

**Environment Variables:**
- `DATABASE_URL` — PostgreSQL connection string
- `TEST_DATABASE_URL` — Test DB connection string
- `JWT_SECRET_KEY` — JWT signing key (after Phase 10)
- `JWT_ALGORITHM` — JWT algorithm (default: HS256)
- `JWT_EXPIRY_MINUTES` — Access token expiry (default: 15)

---

### 10.3 Migration Strategy

**Rule:** Alembic is the source of truth (no auto-create)

**Process:**
1. Create migration: `alembic revision -m "description"`
2. Edit migration file
3. Apply: `alembic upgrade head`
4. Verify: `alembic current`
5. Test rollback: `alembic downgrade -1`
6. Re-apply: `alembic upgrade head`

---

## 11) Security Considerations

### 11.1 Tenant Isolation (P0)

- ✅ All queries filtered by `company_id`
- ✅ No client-provided `company_id`
- ⚠️ Tenant existence not enforced yet (WP-09-05)

---

### 11.2 Authentication (Phase 10)

- ❌ Currently header-only (insecure)
- ✅ Will use JWT with signature verification
- ✅ Will use bcrypt/argon2 for password hashing
- ✅ Will enforce RBAC

---

### 11.3 Authorization (Phase 10)

- ❌ Currently no RBAC
- ✅ Will enforce role-based permissions
- ✅ Will use FastAPI dependencies for guards

---

## 12) Performance Considerations

### 12.1 Database Indexes

**Required indexes (all Tenant Data tables):**
- `company_id` (single column index)
- `(company_id, created_at)` (composite index for time-range queries)

---

### 12.2 Query Optimization

**Rule:** Always filter by `company_id` first (uses index)

**Good:**
```sql
SELECT * FROM attendance_records
WHERE company_id = 'company-A'
  AND created_at > '2026-01-01'
ORDER BY created_at DESC
LIMIT 50;
```

**Bad:**
```sql
SELECT * FROM attendance_records
WHERE created_at > '2026-01-01'  -- ❌ No company_id filter
ORDER BY created_at DESC
LIMIT 50;
```

---

## 13) Future Enhancements (Out of Scope)

### 13.1 PostgreSQL RLS (Row Level Security)

**Goal:** Database-level tenant isolation (last line of defense)

**Status:** Not planned for Phase 9-11

---

### 13.2 Multi-Region Deployment

**Goal:** Deploy to multiple regions for lower latency

**Status:** Not planned

---

### 13.3 Read Replicas

**Goal:** Scale read queries with replicas

**Status:** Not planned

---

## 14) References

- **SA_MODULE_SPEC v1.7:** Module structure and boundaries
- **DEVELOPMENT_ORDER.md:** Work package execution order
- **AUTH_TRANSITION_PLAN.md:** Header → JWT migration strategy
- **ATTENDANCE_REGRESSION_SPEC.md:** 8 core regression tests
- **STATUS_MATRIX.md:** Current implementation status
- **GAP_REPORT.md:** Missing components and violations
- **ACCEPTANCE_CHECKLIST.md:** Verification methods

---

**Document End**
