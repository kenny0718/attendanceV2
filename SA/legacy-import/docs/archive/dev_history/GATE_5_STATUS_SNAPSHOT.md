# Gate 5 — Status Snapshot

**Project**: SaaS Multi-Tenant Attendance System  
**Gate**: 5 (Attendance Core APIs)  
**Snapshot Date**: 2026-03-03  
**Auth Model**: 🔒 FROZEN (Gate 4 closed)

---

## Current Completion Status

### ✅ WP-11-00: Gate 5 Kickoff Pack
**Status**: COMPLETED  
**Deliverables**:
- `docs/GATE_5_ATTENDANCE_ROADMAP.md` — Complete roadmap for Gate 5
- `docs/GATE_5_BOUNDARY_RULES.md` — Frozen auth boundary rules
- `docs/GATE_PROGRESS_TRACKER.md` — Progress tracking document

### ✅ WP-11-01 Phase A: Domain Spec
**Status**: COMPLETED  
**Deliverables**:
- `docs/WP-11-01_ATTENDANCE_DOMAIN_MODEL_SPEC.md` — Complete domain specification
  - 3 tables defined (sessions, punches, policies)
  - Business invariant specified
  - Test plan documented

### ✅ WP-11-01 Phase B: Implementation
**Status**: COMPLETED  
**Deliverables**:
- Migration: `001_create_attendance_domain_v2.py`
- Models: `AttendanceSession`, `AttendancePunch`, `AttendancePolicy`
- Repositories: 3 repository classes with full CRUD
- Tests: 41 automated tests
- Documentation: `docs/WP-11-01_PHASE_B_REPORT.md`

### ⏳ WP-11-02: Punch In/Out API
**Status**: PENDING (Ready for kickoff)

---

## Existing Attendance Tables

### Table 1: `attendance_sessions`

**Purpose**: Represents a complete work session (punch in → punch out)

**Key Columns**:
- `id` (UUID, PK)
- `company_id` (VARCHAR(255), FK → tenants.id, NOT NULL)
- `user_id` (UUID, FK → users.id, NOT NULL)
- `punch_in_time` (TIMESTAMPTZ, NOT NULL)
- `punch_out_time` (TIMESTAMPTZ, NULL) — NULL indicates open session
- `status` (VARCHAR(20), NOT NULL, DEFAULT 'open') — 'open' or 'closed'
- `duration_minutes` (INTEGER, NULL) — Computed on close
- `policy_id` (UUID, FK → attendance_policies.id, NULL)
- `notes` (TEXT, NULL)
- `created_at`, `updated_at` (TIMESTAMPTZ)

**Major Constraints**:
- `CHECK (status IN ('open', 'closed'))` — Status validation
- `UNIQUE (company_id, user_id) WHERE status = 'open'` — **Core business invariant**

**Major Indexes**:
- `idx_sessions_company_id` — Tenant isolation
- `idx_sessions_user_id` — User queries
- `idx_sessions_company_user` — Composite lookup
- `idx_sessions_company_punch_in` — Date range queries
- `idx_sessions_status_open` (partial) — Open session queries
- `uq_sessions_company_user_open` (UNIQUE, partial) — Invariant enforcement

**Foreign Keys**:
- `company_id → tenants.id` (ON DELETE CASCADE)
- `user_id → users.id` (ON DELETE CASCADE)
- `policy_id → attendance_policies.id` (ON DELETE SET NULL)

---

### Table 2: `attendance_punches`

**Purpose**: Audit trail for all punch events

**Key Columns**:
- `id` (UUID, PK)
- `session_id` (UUID, FK → attendance_sessions.id, NOT NULL)
- `company_id` (VARCHAR(255), FK → tenants.id, NOT NULL) — Denormalized
- `user_id` (UUID, FK → users.id, NOT NULL) — Denormalized
- `punch_type` (VARCHAR(20), NOT NULL) — 'in', 'out', 'break_start', 'break_end'
- `punch_time` (TIMESTAMPTZ, NOT NULL)
- `ip_address` (VARCHAR(45), NULL)
- `user_agent` (TEXT, NULL)
- `location_lat`, `location_lng` (NUMERIC, NULL)
- `device_id` (VARCHAR(255), NULL)
- `photo_url` (TEXT, NULL)
- `notes` (TEXT, NULL)
- `created_at` (TIMESTAMPTZ)

**Major Constraints**:
- `CHECK (punch_type IN ('in', 'out', 'break_start', 'break_end'))` — Type validation

**Major Indexes**:
- `idx_punches_session_id` — Session-based queries
- `idx_punches_company_id` — Tenant isolation
- `idx_punches_user_id` — User queries
- `idx_punches_company_time` — Time-range queries
- `idx_punches_type` — Type filtering

**Foreign Keys**:
- `session_id → attendance_sessions.id` (ON DELETE CASCADE)
- `company_id → tenants.id` (ON DELETE CASCADE)
- `user_id → users.id` (ON DELETE CASCADE)

**Design Note**: `company_id` and `user_id` denormalized for performance and tenant isolation without JOINs.

---

### Table 3: `attendance_policies`

**Purpose**: Company-specific attendance rules

**Key Columns**:
- `id` (UUID, PK)
- `company_id` (VARCHAR(255), FK → tenants.id, NOT NULL)
- `name` (VARCHAR(255), NOT NULL)
- `description` (TEXT, NULL)
- `work_start_time` (TIME, NOT NULL)
- `work_end_time` (TIME, NOT NULL)
- `grace_period_minutes` (INTEGER, NOT NULL, DEFAULT 0)
- `overtime_threshold_minutes` (INTEGER, NULL)
- `is_active` (BOOLEAN, NOT NULL, DEFAULT TRUE)
- `is_default` (BOOLEAN, NOT NULL, DEFAULT FALSE)
- `created_at`, `updated_at` (TIMESTAMPTZ)

**Major Constraints**:
- `UNIQUE (company_id) WHERE is_default = TRUE` — One default policy per company

**Major Indexes**:
- `idx_policies_company_id` — Tenant isolation
- `idx_policies_company_active` — Active policy queries
- `idx_policies_company_default` (partial) — Default policy lookup
- `uq_policies_company_default` (UNIQUE, partial) — Default constraint

**Foreign Keys**:
- `company_id → tenants.id` (ON DELETE CASCADE)

---

## Core Invariant Enforcement

### Business Rule

**Invariant**: One open session per `(company_id, user_id)` at any given time.

**Formal Definition**:
```
∀ (company_id, user_id): COUNT(*) WHERE status='open' ≤ 1
```

### Enforcement Layer 1: Database

**Mechanism**: PostgreSQL partial unique index

```sql
CREATE UNIQUE INDEX uq_sessions_company_user_open 
ON attendance_sessions(company_id, user_id) 
WHERE status = 'open';
```

**How It Works**:
- Index only includes rows where `status = 'open'`
- Multiple closed sessions allowed (not in index)
- Duplicate open sessions rejected at database level
- Prevents race conditions in concurrent requests

**Error Behavior**:
```python
# Second open session attempt
db.commit()  # Raises IntegrityError with constraint name
```

### Enforcement Layer 2: Repository

**Mechanism**: Application-level pre-check

**File**: `backend/app/modules/attendance/repo.py`

**Implementation**:
```python
class AttendanceSessionRepository:
    def create_session(self, company_id, user_id, ...):
        # Check for existing open session
        open_session = self.get_open_session(company_id, user_id)
        if open_session:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "User already has an open attendance session",
                    "open_session_id": str(open_session.id),
                    "punch_in_time": open_session.punch_in_time.isoformat()
                }
            )
        
        # Proceed with creation
        session = AttendanceSession(...)
        db.add(session)
        db.commit()
```

**Benefits**:
- User-friendly error messages (HTTP 409 with context)
- Early rejection (before database round-trip)
- Detailed error response (includes existing session info)

### Defense in Depth

| Scenario | App Check | DB Check | Result |
|----------|-----------|----------|--------|
| Normal punch in | ✅ Pass | ✅ Pass | Session created |
| Duplicate punch in | ❌ Fail | N/A | HTTP 409 with details |
| Race condition | ✅ Pass (both) | ❌ Fail (second) | First succeeds, second gets IntegrityError |

**Why Both?**
- Application check: Handles 99% of cases gracefully
- Database check: Ultimate safety net for race conditions

---

## Tenant Isolation Implementation

### Principle

**Rule**: All attendance data must be scoped to `company_id` (tenant ID).

**Enforcement**: Every query MUST include `WHERE company_id = ?`

### Implementation Layer 1: Schema

**All tables have `company_id`**:
- `attendance_sessions.company_id`
- `attendance_punches.company_id`
- `attendance_policies.company_id`

**Foreign keys enforce referential integrity**:
- All `company_id` columns reference `tenants.id`
- ON DELETE CASCADE ensures clean tenant deletion

### Implementation Layer 2: Repository

**All repository methods enforce tenant scope**:

```python
class AttendanceSessionRepository:
    def get_session_by_id(self, company_id, session_id):
        # MUST include company_id filter
        return self.db.query(AttendanceSession).filter(
            AttendanceSession.id == session_id,
            AttendanceSession.company_id == company_id  # ← Mandatory
        ).first()
    
    def get_sessions(self, company_id, user_id=None, ...):
        # MUST include company_id filter
        query = self.db.query(AttendanceSession).filter(
            AttendanceSession.company_id == company_id  # ← Mandatory
        )
        # ... additional filters
```

**Cross-company access prevention**:
- Company A cannot read Company B's sessions
- Company A cannot update Company B's sessions
- Company A cannot delete Company B's sessions

### Implementation Layer 3: API (WP-11-02)

**Planned enforcement** (not yet implemented):

```python
@router.post("/punch-in")
def punch_in(
    company_id: str = Depends(get_current_company_id),  # From JWT
    user_id: UUID = Depends(get_current_user_id),       # From JWT
    db: Session = Depends(get_db)
):
    # company_id injected from JWT, not from request body
    repo = AttendanceSessionRepository(db)
    session = repo.create_session(company_id, user_id, ...)
    return session
```

**Key principle**: `company_id` comes from JWT claims, never from request body.

---

## Auth Freeze Compliance

### Gate 4 Frozen Boundaries

**Frozen Components** (DO NOT MODIFY):
- Auth schema: `users`, `user_company_memberships`, `roles`, `permissions`, `role_permissions`
- JWT contract: Payload structure (`sub`, `company_id`, `role_id`, `iat`, `exp`)
- Anti-enumeration: Timing-safe comparisons, generic error messages
- Membership validation: `tenant_context.get_current_company_id()` logic

### Gate 5 Compliance

**How Gate 5 respects frozen boundaries**:

✅ **Read-only FK references**:
- `attendance_sessions.user_id → users.id` (FK only, no data duplication)
- `attendance_sessions.company_id → tenants.id` (FK only)

✅ **No auth schema modifications**:
- Zero changes to `users`, `user_company_memberships`, `roles` tables
- No new columns added to auth tables
- No index changes on auth tables

✅ **No JWT contract changes**:
- JWT payload structure unchanged
- No new claims added
- No claim removal

✅ **Uses frozen tenant_context**:
- `tenant_context.get_current_company_id()` used as-is
- No modifications to tenant validation logic

✅ **No anti-enumeration changes**:
- Error messages follow existing patterns
- No user existence leakage

### Verification

**Migration file check**:
```bash
grep -E "ALTER TABLE (users|user_company_memberships|roles)" \
  backend/alembic/versions/001_create_attendance_domain_v2.py
# Output: (empty) ✅
```

**Auth module check**:
```bash
git diff HEAD backend/app/modules/auth/
# Output: (empty) ✅
```

---

## Known Risks & Limitations

### Risk 1: Race Condition Window

**Issue**: Millisecond window between application check and database commit

**Scenario**:
```
T1: Request A checks open session → None
T2: Request B checks open session → None
T3: Request A commits → Success
T4: Request B commits → IntegrityError
```

**Mitigation**:
- Database constraint catches race condition
- Second request gets IntegrityError (not ideal UX, but rare)
- Future: Add retry logic in API layer (WP-11-02)

**Impact**: Low (millisecond window, unlikely in practice)

---

### Risk 2: PostgreSQL Dependency

**Issue**: Partial unique indexes are PostgreSQL-specific

**Limitation**: Not portable to MySQL, SQLite

**Mitigation**: Project standardized on PostgreSQL; no multi-DB support planned

**Status**: Acceptable

---

### Risk 3: No API Layer Yet

**Issue**: Domain model cannot be used until API implemented

**Impact**:
- Cannot test end-to-end flows
- Cannot validate JWT integration
- Cannot test request/response DTOs

**Resolution**: WP-11-02 will implement RESTful APIs

**Status**: Expected (phased approach)

---

### Limitation 1: Policy Evaluation Not Implemented

**Scope**: WP-11-01 defines policy schema only

**Missing**:
- Late detection logic
- Overtime calculation
- Grace period enforcement

**Resolution**: WP-11-03 will implement policy engine

---

### Limitation 2: No Reporting

**Scope**: WP-11-01 focuses on data layer

**Missing**:
- Daily/weekly/monthly summaries
- Team-level aggregation
- Export to CSV/Excel

**Resolution**: WP-11-04 will implement reports

---

### Limitation 3: Test Database Configuration

**Issue**: Tests use hardcoded connection string

```python
TEST_DATABASE_URL = "postgresql://attendance_user:attendance_pass@localhost:5432/attendance_test"
```

**Impact**: Tests fail if database not configured

**Future Enhancement**: Use environment variables or test fixtures

---

## Test Coverage Summary

### Test Files (WP-11-01 Phase B)

1. **`test_model_constraints.py`** — 20 tests
   - NOT NULL constraints
   - CHECK constraints
   - Foreign key constraints
   - Default values
   - CASCADE behavior

2. **`test_migration.py`** — 9 tests
   - Migration upgrade (tables, columns, indexes, FKs)
   - Migration downgrade
   - Idempotency

3. **`test_business_invariant.py`** — 12 tests
   - One open session invariant (DB + app level)
   - Session lifecycle
   - Tenant isolation

**Total**: 41 tests

### Coverage Areas

✅ Database schema integrity  
✅ Migration correctness  
✅ Business invariant enforcement  
✅ Tenant isolation  
✅ Session lifecycle  
✅ Constraint validation  

❌ API endpoints (WP-11-02)  
❌ JWT integration (WP-11-02)  
❌ Policy evaluation (WP-11-03)  
❌ Reports (WP-11-04)  

---

## Dependencies

### Upstream Dependencies (Frozen)

- ✅ Gate 4 Auth — FROZEN, used via FK references
- ✅ Tenant Context v2 — FROZEN, used as-is
- ✅ JWT Contract — FROZEN, will be consumed in WP-11-02

### Downstream Dependencies (Pending)

- ⏳ WP-11-02 — Punch In/Out API (depends on WP-11-01)
- ⏳ WP-11-03 — Policy Engine (depends on WP-11-02)
- ⏳ WP-11-04 — Reports (depends on WP-11-02)
- ⏳ WP-11-05 — Audit Hooks (depends on WP-11-02)

---

## Next Milestone

**WP-11-02: Punch In/Out API**

**Prerequisites**:
- ✅ Domain model implemented (WP-11-01 Phase B)
- ✅ Business invariant enforced
- ✅ Tenant isolation verified
- ⏳ Precheck checklist approved

**Estimated Duration**: 5 days

**Key Deliverables**:
- RESTful endpoints (punch-in, punch-out, status, history)
- JWT authentication integration
- Request/response DTOs
- E2E API tests
- OpenAPI documentation

---

**Snapshot Prepared By**: AI Assistant  
**Review Status**: Pending  
**Last Updated**: 2026-03-03

---

**End of Snapshot**
