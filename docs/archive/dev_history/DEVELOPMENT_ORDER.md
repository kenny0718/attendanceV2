# Attendance System V2 — Development Order (Fine-grained WPs)

**Rule:** One WP at a time. Small steps. Every WP must pass tests before moving on.

---

## 0) Non-negotiable Rules (Hard Constraints)

### Tenant isolation is mandatory
- All reads/writes must be scoped by `company_id`
- API requests must not accept `company_id` from client body/query for business entities
- `company_id` must come from Tenant Context (header now, JWT later)

### Alembic is the source of truth
- Any table used in runtime must have an Alembic migration
- `init_db` auto-create is not allowed as the "real" path

### Every Work Package (WP) must include
- ✅ Allowed modification scope (`@Files` / `@Folders`)
- ⛔ Forbidden modification scope (avoid cross-module changes)
- Files changed/added list
- Tests added/updated list (with intent)
- Test command(s) to run
- Acceptance criteria checklist
- Suggested commit message

---

## 1) Current Status

✅ **Phase 0–8 done:** EventBus, DB baseline, Backup, Audit, Notifications base, Tenant Isolation (header `X-Company-ID`)

⚠️ **Outstanding:**
- **Tenants (company)** must be formalized in DB + CRUD
- **Auth** must move from header-based to JWT + RBAC
- **Attendance core** regression suite is 0/8 passing

---

## 2) Execution Plan (Work Packages)

### Phase 9: Tenants (5 WPs)

#### WP-09-01 — Tenants: Alembic migration only

**Goal:** Create `tenants` table migration (no code changes yet)

**✅ Allowed:**
- `@Folders backend/alembic/versions/` (new migration file)

**⛔ Forbidden:**
- Any `backend/app/` code
- Any tests (migration test comes in next WP)

**Expected files:**
- `backend/alembic/versions/004_create_tenants.py`

**Migration schema:**
```sql
CREATE TABLE tenants (
    id VARCHAR(50) PRIMARY KEY,  -- company_id
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_tenants_is_active ON tenants(is_active);
```

**Test command:**
```bash
cd backend
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

**Acceptance:**
- [ ] Migration file created
- [ ] `alembic upgrade head` succeeds
- [ ] `alembic downgrade -1` succeeds
- [ ] Table exists in DB after upgrade

**Commit:**
```
chore(tenants): add tenants table migration
```

---

#### WP-09-02 — Tenants: Model + Repo + Unit Tests

**Goal:** Create Tenant ORM model and repository with unit tests (no API yet)

**✅ Allowed:**
- `@Folders backend/app/modules/tenants/` (new: `models.py`, `repo.py`, `__init__.py`)
- `@Folders backend/app/modules/tenants/tests/` (new: `test_repo.py`)

**⛔ Forbidden:**
- `service.py` / `api.py` (next WP)
- `backend/app/main.py` (no router registration yet)
- Any other modules

**Expected files:**
```
backend/app/modules/tenants/__init__.py
backend/app/modules/tenants/models.py
backend/app/modules/tenants/repo.py
backend/app/modules/tenants/tests/__init__.py
backend/app/modules/tenants/tests/test_repo.py
```

**Repo methods (minimum):**
- `create(tenant_id, name, **kwargs) -> Tenant`
- `get_by_id(tenant_id) -> Tenant | None`
- `list_all(limit, offset) -> List[Tenant]`
- `update(tenant_id, **fields) -> Tenant`
- `exists(tenant_id) -> bool`
- `is_active(tenant_id) -> bool`

**Test cases:**
- Create tenant → exists in DB
- Get by id → returns correct tenant
- Get non-existent → returns None
- List all → pagination works
- Update fields → persisted
- `is_active()` checks `is_active` flag

**Test command:**
```bash
cd backend
pytest app/modules/tenants/tests/test_repo.py -v
```

**Acceptance:**
- [ ] All repo unit tests pass
- [ ] No API/service code added yet

**Commit:**
```
feat(tenants): add Tenant model and repository with unit tests
```

---

#### WP-09-03 — Tenants: Service + Validation + Unit Tests

**Goal:** Add service layer with business validation (no API yet)

**✅ Allowed:**
- `@Files backend/app/modules/tenants/service.py` (new)
- `@Files backend/app/modules/tenants/tests/test_service.py` (new)

**⛔ Forbidden:**
- `api.py` (next WP)
- `backend/app/main.py`
- Any other modules

**Expected files:**
```
backend/app/modules/tenants/service.py
backend/app/modules/tenants/tests/test_service.py
```

**Service methods:**
- `create_tenant(tenant_id, name, timezone, **kwargs)`
  - Validate: `tenant_id` format (alphanumeric + dash/underscore)
  - Validate: `name` not empty
  - Validate: `timezone` in pytz.all_timezones (if provided)
  - Raise `ValueError` on validation failure
- `get_tenant(tenant_id)`
- `list_tenants(limit, offset)`
- `update_tenant(tenant_id, **fields)`
  - Validate fields same as create
- `deactivate_tenant(tenant_id)` (set `is_active=False`)

**Test cases:**
- Valid create → success
- Invalid `tenant_id` format → ValueError
- Empty `name` → ValueError
- Invalid `timezone` → ValueError
- Update with invalid fields → ValueError
- Deactivate → `is_active=False`

**Test command:**
```bash
cd backend
pytest app/modules/tenants/tests/test_service.py -v
```

**Acceptance:**
- [ ] All service unit tests pass
- [ ] Validation rules enforced
- [ ] No API code added yet

**Commit:**
```
feat(tenants): add service layer with validation rules
```

---

#### WP-09-04 — Tenants: API + Feature Tests

**Goal:** Add REST API endpoints with feature tests

**✅ Allowed:**
- `@Files backend/app/modules/tenants/api.py` (new)
- `@Files backend/app/modules/tenants/docs.md` (new)
- `@Files backend/app/main.py` (router registration only)
- `@Files backend/app/modules/tenants/tests/test_api.py` (new)

**⛔ Forbidden:**
- `tenant_context.py` changes (next WP)
- Any other modules

**Expected files:**
```
backend/app/modules/tenants/api.py
backend/app/modules/tenants/docs.md
backend/app/modules/tenants/tests/test_api.py
backend/app/main.py (modified: add router)
```

**API endpoints:**
- `POST /api/tenants` — Create tenant (admin only, no auth yet)
- `GET /api/tenants` — List tenants (pagination)
- `GET /api/tenants/{id}` — Get tenant by id
- `PATCH /api/tenants/{id}` — Update tenant
- `DELETE /api/tenants/{id}` — Deactivate tenant (soft delete)

**Test cases:**
- POST valid → 201 + tenant created
- POST invalid → 422 + error details
- GET list → 200 + pagination
- GET by id → 200 + tenant data
- GET non-existent → 404
- PATCH valid → 200 + updated
- PATCH invalid → 422
- DELETE → 200 + `is_active=False`

**Test command:**
```bash
cd backend
pytest app/modules/tenants/tests/test_api.py -v
pytest app/modules/tenants/tests/ -v  # all tests
```

**Acceptance:**
- [ ] All API tests pass
- [ ] Router registered in `main.py`
- [ ] API docs written

**Commit:**
```
feat(tenants): add REST API endpoints with feature tests
```

---

#### WP-09-05 — Tenant Context: Enforce existence + active status

**Goal:** Strengthen `tenant_context.py` to check tenant exists and is active

**✅ Allowed:**
- `@Files backend/app/core/tenant_context.py` (modify)
- `@Files backend/app/core/dependencies.py` (if needed)
- `@Folders backend/app/modules/*/tests/` (regression tests)

**⛔ Forbidden:**
- New features in any module
- Auth changes (next phase)

**Changes:**
- Modify `get_company_id()` or equivalent to:
  1. Extract `X-Company-ID` from header
  2. Check tenant exists in DB (via `tenants` repo)
  3. Check tenant `is_active=True`
  4. Return 404 if not exists
  5. Return 403 if inactive

**Test cases:**
- Valid active tenant → requests succeed
- Non-existent tenant → 404
- Inactive tenant → 403
- **Regression:** Run all existing module tests (attendance, notifications, backup, audit)

**Test command:**
```bash
cd backend
# Tenant context tests
pytest app/core/tests/test_tenant_context.py -v

# Regression: all modules
pytest app/modules/attendance/tests/ -v
pytest app/modules/notifications/tests/ -v
pytest app/modules/backup/tests/ -v
pytest app/modules/audit/tests/ -v
```

**Acceptance:**
- [ ] Tenant existence enforced
- [ ] Active status enforced
- [ ] All regression tests pass
- [ ] 404/403 behavior documented

**Commit:**
```
feat(tenant): enforce tenant existence and active status in context
```

---

### Phase 10: Auth (6 WPs)

**Note:** Before starting Phase 10, read `@Files docs/AUTH_TRANSITION_PLAN.md` for the header→JWT transition strategy.

#### WP-10-01 — Auth: Schema design document

**Goal:** Write auth schema spec (users/staff table, roles, JWT claims)

**✅ Allowed:**
- `@Files docs/AUTH_SCHEMA_SPEC.md` (new)

**⛔ Forbidden:**
- Any code changes

**Document must include:**
- Users/staff table schema (or reuse existing if any)
- Roles: `employee`, `manager`, `company_admin`, `customer_service`
- JWT claims structure: `company_id`, `staff_id`, `roles`, `exp`, `iat`
- Password hashing strategy (bcrypt/argon2)
- Token expiry: access token (15min), refresh token (7 days)

**Acceptance:**
- [ ] Document created
- [ ] Schema reviewed and approved

**Commit:**
```
docs(auth): add auth schema specification
```

---

#### WP-10-02 — Auth: Users table migration + model

**Goal:** Create users/staff table and ORM model

**✅ Allowed:**
- `@Folders backend/alembic/versions/` (new migration)
- `@Files backend/app/modules/auth/models.py` (new)
- `@Files backend/app/modules/auth/__init__.py` (new)

**⛔ Forbidden:**
- Repo/service/API (next WPs)

**Expected files:**
```
backend/alembic/versions/005_create_users.py
backend/app/modules/auth/__init__.py
backend/app/modules/auth/models.py
```

**Migration schema:**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id VARCHAR(50) NOT NULL,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    roles JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(company_id, username),
    UNIQUE(company_id, email)
);
CREATE INDEX idx_users_company_id ON users(company_id);
CREATE INDEX idx_users_email ON users(email);
```

**Test command:**
```bash
cd backend
alembic upgrade head
```

**Acceptance:**
- [ ] Migration applied successfully
- [ ] User model created

**Commit:**
```
chore(auth): add users table migration and model
```

---

#### WP-10-03 — Auth: Repo + password hashing + unit tests

**Goal:** Create auth repository with password hashing

**✅ Allowed:**
- `@Files backend/app/modules/auth/repo.py` (new)
- `@Files backend/app/core/security.py` (new, for password hashing)
- `@Files backend/app/modules/auth/tests/test_repo.py` (new)

**⛔ Forbidden:**
- Service/API (next WPs)

**Expected files:**
```
backend/app/modules/auth/repo.py
backend/app/core/security.py
backend/app/modules/auth/tests/__init__.py
backend/app/modules/auth/tests/test_repo.py
```

**Repo methods:**
- `create_user(company_id, username, email, password, roles)`
- `get_by_username(company_id, username)`
- `get_by_email(company_id, email)`
- `verify_password(user, password) -> bool`
- `update_password(user_id, new_password)`

**Security functions:**
- `hash_password(password) -> str`
- `verify_password(password, hash) -> bool`

**Test cases:**
- Create user → password hashed
- Verify correct password → True
- Verify wrong password → False
- Get by username → returns user
- Tenant isolation: company A cannot get company B's user

**Test command:**
```bash
cd backend
pytest app/modules/auth/tests/test_repo.py -v
```

**Acceptance:**
- [ ] All repo tests pass
- [ ] Passwords never stored in plaintext

**Commit:**
```
feat(auth): add auth repository with password hashing
```

---

#### WP-10-04 — Auth: JWT service + login API + tests

**Goal:** Implement JWT login endpoint (header/JWT coexist, no切換 yet)

**✅ Allowed:**
- `@Files backend/app/modules/auth/service.py` (new)
- `@Files backend/app/modules/auth/api.py` (new)
- `@Files backend/app/core/security.py` (extend: JWT functions)
- `@Files backend/app/main.py` (router registration)
- `@Files backend/app/modules/auth/tests/test_api.py` (new)

**⛔ Forbidden:**
- Modifying existing endpoints to require JWT (next WP)
- Removing header-based auth

**Expected files:**
```
backend/app/modules/auth/service.py
backend/app/modules/auth/api.py
backend/app/core/security.py (add JWT functions)
backend/app/modules/auth/tests/test_api.py
backend/app/main.py (modified)
```

**API endpoints:**
- `POST /api/auth/login` — Login with username/password
  - Returns: `{"access_token": "...", "token_type": "bearer"}`
- `POST /api/auth/refresh` (optional)

**JWT claims:**
```json
{
  "sub": "user_id",
  "company_id": "company-A",
  "staff_id": "staff_id",
  "roles": ["employee"],
  "exp": 1234567890,
  "iat": 1234567890
}
```

**Test cases:**
- Valid login → 200 + JWT token
- Invalid username → 401
- Invalid password → 401
- Inactive user → 401
- Token contains correct claims
- Token signature valid

**Test command:**
```bash
cd backend
pytest app/modules/auth/tests/test_api.py -v
```

**Acceptance:**
- [ ] Login API works
- [ ] JWT tokens generated correctly
- [ ] All tests pass
- [ ] Existing endpoints still work with header

**Commit:**
```
feat(auth): add JWT login API with tests
```

---

#### WP-10-05 — RBAC: Role model + permission checks + tests

**Goal:** Implement RBAC permission checking (no enforcement yet)

**✅ Allowed:**
- `@Files backend/app/core/rbac.py` (new)
- `@Files backend/app/core/dependencies.py` (new: permission guards)
- `@Files backend/app/core/tests/test_rbac.py` (new)

**⛔ Forbidden:**
- Applying guards to endpoints (next WP)

**Expected files:**
```
backend/app/core/rbac.py
backend/app/core/dependencies.py
backend/app/core/tests/test_rbac.py
```

**Roles & Permissions:**
- `employee`: `attendance:create:self`, `attendance:read:self`
- `manager`: `employee` + `attendance:approve`, `attendance:read:team`
- `company_admin`: `manager` + `tenants:manage`, `users:manage`
- `customer_service`: special (can access assigned companies only)

**Functions:**
- `has_permission(user, permission) -> bool`
- `require_permission(permission)` — FastAPI dependency
- `require_role(role)` — FastAPI dependency

**Test cases:**
- Employee has `attendance:create:self` → True
- Employee has `attendance:approve` → False
- Manager has `attendance:approve` → True
- Admin has all permissions → True

**Test command:**
```bash
cd backend
pytest app/core/tests/test_rbac.py -v
```

**Acceptance:**
- [ ] RBAC logic implemented
- [ ] All unit tests pass
- [ ] No endpoints modified yet

**Commit:**
```
feat(rbac): add role-based permission checking
```

---

#### WP-10-06 — Auth transition: Batch 1 endpoints to JWT

**Goal:** Convert first batch of endpoints to require JWT (see `AUTH_TRANSITION_PLAN.md`)

**✅ Allowed:**
- `@Files backend/app/modules/attendance/api.py` (add JWT dependency)
- `@Files backend/app/modules/attendance/tests/` (update tests)

**⛔ Forbidden:**
- Other modules (batch 2+)

**Batch 1 endpoints:**
- `POST /api/attendance/mock-create` → require JWT + `attendance:create:self`
- `POST /api/attendance/{id}/approve` → require JWT + `attendance:approve`

**Changes:**
- Add `current_user: User = Depends(get_current_user)` to endpoints
- Add `require_permission("attendance:create:self")` guard
- Remove or deprecate `X-Company-ID` header dependency
- Update tests to use JWT tokens

**Test cases:**
- Valid JWT + correct role → 200
- Valid JWT + wrong role → 403
- No JWT → 401
- Invalid JWT → 401
- **Regression:** All attendance tests pass with JWT

**Test command:**
```bash
cd backend
pytest app/modules/attendance/tests/ -v
```

**Acceptance:**
- [ ] Batch 1 endpoints require JWT
- [ ] RBAC enforced
- [ ] All tests pass
- [ ] Header-based auth removed from batch 1

**Commit:**
```
feat(auth): migrate attendance endpoints to JWT auth (batch 1)
```

---

### Phase 11/12: Attendance Core (6 WPs)

**Note:** Before starting, read `@Files docs/ATTENDANCE_REGRESSION_SPEC.md` for the 8 regression test cases.

#### WP-11-01 — Attendance: Status enum + state machine spec

**Goal:** Define attendance record status and state transitions (document + enum)

**✅ Allowed:**
- `@Files docs/ATTENDANCE_STATE_MACHINE.md` (new)
- `@Files backend/app/modules/attendance/models.py` (add status enum)

**⛔ Forbidden:**
- Business logic implementation (next WPs)

**Status enum:**
```python
class AttendanceStatus(str, Enum):
    APPROVED = "APPROVED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    NO_MATCH = "NO_MATCH"
    REJECTED = "REJECTED"
```

**State transitions (document):**
- `NO_MATCH` (no reason) → rejected at creation
- `NO_MATCH` (with reason) → `PENDING_APPROVAL`
- `PENDING_APPROVAL` → `APPROVED` (manager approves)
- `PENDING_APPROVAL` → `REJECTED` (manager rejects)
- `APPROVED` → immutable (cannot change)

**Acceptance:**
- [ ] Document created
- [ ] Enum added to model
- [ ] No logic implemented yet

**Commit:**
```
docs(attendance): add state machine specification
```

---

#### WP-11-02 — Attendance: IN/OUT pairing logic + unit tests

**Goal:** Implement IN/OUT pairing algorithm (no API changes)

**✅ Allowed:**
- `@Files backend/app/modules/attendance/inference.py` (new)
- `@Files backend/app/modules/attendance/tests/test_inference.py` (new)

**⛔ Forbidden:**
- API/service changes (next WP)

**Expected files:**
```
backend/app/modules/attendance/inference.py
backend/app/modules/attendance/tests/test_inference.py
```

**Functions:**
- `pair_in_out(records: List[AttendanceRecord]) -> List[Pair]`
  - Pair consecutive IN/OUT within same day
  - Unpaired IN → missing OUT
  - Unpaired OUT → missing IN

**Test cases:**
- IN at 09:00, OUT at 18:00 → paired
- IN at 09:00, no OUT → unpaired IN
- OUT at 18:00, no IN → unpaired OUT
- Multiple IN/OUT same day → multiple pairs
- Cross-day records → not paired

**Test command:**
```bash
cd backend
pytest app/modules/attendance/tests/test_inference.py -v
```

**Acceptance:**
- [ ] Pairing logic implemented
- [ ] All unit tests pass

**Commit:**
```
feat(attendance): implement IN/OUT pairing logic
```

---

#### WP-11-03 — Attendance: Work time calculation + tests

**Goal:** Calculate work hours from paired IN/OUT

**✅ Allowed:**
- `@Files backend/app/modules/attendance/inference.py` (extend)
- `@Files backend/app/modules/attendance/tests/test_inference.py` (extend)

**⛔ Forbidden:**
- API changes

**Functions:**
- `calculate_work_time(pair: Pair) -> timedelta`
  - Simple: OUT time - IN time
  - (Future: break time deduction)

**Test cases:**
- 09:00 IN, 18:00 OUT → 9 hours
- 09:00 IN, 13:00 OUT → 4 hours
- Unpaired → 0 hours

**Test command:**
```bash
cd backend
pytest app/modules/attendance/tests/test_inference.py::test_calculate_work_time -v
```

**Acceptance:**
- [ ] Work time calculation correct
- [ ] All tests pass

**Commit:**
```
feat(attendance): add work time calculation
```

---

#### WP-11-04 — Attendance: Day close at 21:00 + missing card detection

**Goal:** Implement day close logic (exclude PENDING, detect missing cards)

**✅ Allowed:**
- `@Files backend/app/modules/attendance/day_close.py` (new)
- `@Files backend/app/modules/attendance/tests/test_day_close.py` (new)

**⛔ Forbidden:**
- Scheduled job (future)

**Expected files:**
```
backend/app/modules/attendance/day_close.py
backend/app/modules/attendance/tests/test_day_close.py
```

**Functions:**
- `close_day(company_id, date, cutoff_time="21:00")`
  - Get all records for date (exclude `PENDING_APPROVAL`)
  - Pair IN/OUT
  - Detect missing cards:
    - Unpaired IN → "missing OUT"
    - Unpaired OUT → "missing IN"
  - Mark day as closed

**Test cases:**
- Day with complete pairs → no missing cards
- Day with unpaired IN → missing OUT detected
- Day with unpaired OUT → missing IN detected
- `PENDING_APPROVAL` records → excluded from day close
- After 21:00 → day closed

**Test command:**
```bash
cd backend
pytest app/modules/attendance/tests/test_day_close.py -v
```

**Acceptance:**
- [ ] Day close logic implemented
- [ ] PENDING excluded
- [ ] Missing cards detected
- [ ] All tests pass

**Commit:**
```
feat(attendance): implement day close and missing card detection
```

---

#### WP-11-05 — Attendance: Approve pending → recalculate day

**Goal:** When PENDING approved, recalculate that day's inference

**✅ Allowed:**
- `@Files backend/app/modules/attendance/service.py` (modify approve logic)
- `@Files backend/app/modules/attendance/tests/test_service.py` (extend)

**⛔ Forbidden:**
- Other modules

**Changes:**
- `approve_attendance(record_id)`:
  1. Change status `PENDING_APPROVAL` → `APPROVED`
  2. Get record date
  3. Re-run inference for that day (call `pair_in_out` + `calculate_work_time`)
  4. Update day summary

**Test cases:**
- Approve PENDING → status = APPROVED
- Approve PENDING → day recalculated
- Approve PENDING → work time updated
- Approve non-PENDING → error

**Test command:**
```bash
cd backend
pytest app/modules/attendance/tests/test_service.py::test_approve_recalculates -v
```

**Acceptance:**
- [ ] Approve triggers recalculation
- [ ] All tests pass

**Commit:**
```
feat(attendance): recalculate day when approving pending records
```

---

#### WP-11-06 — Attendance: 8 regression tests (final validation)

**Goal:** Implement and pass all 8 regression tests from `ATTENDANCE_REGRESSION_SPEC.md`

**✅ Allowed:**
- `@Files backend/app/modules/attendance/tests/test_regression.py` (new)
- Bug fixes in inference/day_close/service

**⛔ Forbidden:**
- New features

**Expected files:**
```
backend/app/modules/attendance/tests/test_regression.py
```

**8 regression tests:**
1. NO_MATCH without reason → rejected
2. NO_MATCH with reason → PENDING
3. APPROVED → inference correct
4. PENDING not in inference/day close
5. 21:00 day close → missing cards detected
6. Approve pending → day recalculated
7. (Auth) customer_service unassigned company → 403
8. (Auth) OTP one-time use + force password change

**Test command:**
```bash
cd backend
pytest app/modules/attendance/tests/test_regression.py -v
```

**Acceptance:**
- [ ] 8/8 regression tests pass
- [ ] No cross-tenant leakage
- [ ] All attendance tests pass

**Commit:**
```
test(attendance): add 8 core regression tests and validate
```

---

## 3) Summary Table

| WP ID | Name | Prerequisite | Test Command |
|-------|------|--------------|--------------|
| WP-09-01 | Tenants migration | - | `alembic upgrade head` |
| WP-09-02 | Tenants model/repo | WP-09-01 | `pytest app/modules/tenants/tests/test_repo.py -v` |
| WP-09-03 | Tenants service | WP-09-02 | `pytest app/modules/tenants/tests/test_service.py -v` |
| WP-09-04 | Tenants API | WP-09-03 | `pytest app/modules/tenants/tests/test_api.py -v` |
| WP-09-05 | Tenant context enforce | WP-09-04 | `pytest app/core/tests/ app/modules/*/tests/ -v` |
| WP-10-01 | Auth schema doc | WP-09-05 | (document review) |
| WP-10-02 | Users migration + model | WP-10-01 | `alembic upgrade head` |
| WP-10-03 | Auth repo + password | WP-10-02 | `pytest app/modules/auth/tests/test_repo.py -v` |
| WP-10-04 | JWT login API | WP-10-03 | `pytest app/modules/auth/tests/test_api.py -v` |
| WP-10-05 | RBAC logic | WP-10-04 | `pytest app/core/tests/test_rbac.py -v` |
| WP-10-06 | Auth transition batch 1 | WP-10-05 | `pytest app/modules/attendance/tests/ -v` |
| WP-11-01 | Attendance state machine doc | WP-10-06 | (document review) |
| WP-11-02 | IN/OUT pairing | WP-11-01 | `pytest app/modules/attendance/tests/test_inference.py -v` |
| WP-11-03 | Work time calculation | WP-11-02 | `pytest app/modules/attendance/tests/test_inference.py -v` |
| WP-11-04 | Day close + missing cards | WP-11-03 | `pytest app/modules/attendance/tests/test_day_close.py -v` |
| WP-11-05 | Approve → recalculate | WP-11-04 | `pytest app/modules/attendance/tests/test_service.py -v` |
| WP-11-06 | 8 regression tests | WP-11-05 | `pytest app/modules/attendance/tests/test_regression.py -v` |

---

**Done. Total: 17 WPs (5 Tenants + 6 Auth + 6 Attendance)**
