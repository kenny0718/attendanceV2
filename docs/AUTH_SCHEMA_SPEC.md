# Auth Schema Specification

**Document Version:** 1.0  
**Created:** 2026-03-03  
**Purpose:** Authoritative database schema specification for Phase 10 Auth module  
**Status:** Approved for WP-10-02 implementation

---

## A) Scope

### What This Document Defines
- Database tables, columns, types, constraints, indexes
- RBAC data model (roles, permissions, relationships)
- Naming conventions and type strategies
- Migration plan for WP-10-02

### What This Document Does NOT Define
- JWT implementation details → See `AUTH_TRANSITION_PLAN.md`
- API endpoints → See WP-10-04 (JWT Login API)
- Password hashing algorithms → See WP-10-03 (Auth Repo)
- Endpoint migration batches → See `AUTH_TRANSITION_PLAN.md` Section 3

### Authority
- WP-10-02 (Users Migration + Model) MUST implement exactly as specified here
- Any deviation requires updating this document first
- This is the single source of truth for auth schema

---

## B) Naming & Conventions

### B.1 Table Naming
- **Convention:** `snake_case`, plural nouns
- **Examples:** `users`, `roles`, `permissions`, `user_roles`, `role_permissions`

### B.2 Column Naming
- **Convention:** `snake_case`
- **Primary Keys:** `id` (except tenants which uses `id` as company_id)
- **Foreign Keys:** `{table_singular}_id` (e.g., `user_id`, `role_id`)
- **Timestamps:** `created_at`, `updated_at`, `last_login_at`
- **Booleans:** `is_{adjective}` (e.g., `is_active`, `is_otp`)

### B.3 UUID Strategy
- **Type:** PostgreSQL `UUID` (via `sqlalchemy.dialects.postgresql.UUID`)
- **Generation:** Python `uuid.uuid4()` (application-side, not DB default)
- **Reason:** Consistent with existing tables (`attendance_records`, `notifications`)

### B.4 Tenant Isolation Naming
- **Column:** `company_id` (NOT `tenant_id`)
- **Reason:** Consistency with existing tables (`attendance_records`, `notifications`, `audit_logs`)
- **Type:** `VARCHAR(255)` (matches `tenants.id`)
- **Nullable:** `NOT NULL` for all Tenant Data tables
- **Index:** Always indexed (single column or composite)

---

## C) Tables

### C.1 Table: `users`

**Purpose:** Store user accounts (employees, managers, admins, customer service)

**Type:** Tenant Data (has `company_id`)

**Columns:**

| Column | Type | Nullable | Default | Comment |
|--------|------|----------|---------|---------|
| `id` | UUID | NOT NULL | uuid4() | User ID (PK) |
| `company_id` | VARCHAR(255) | NOT NULL | - | Company ID (Tenant Isolation) |
| `username` | VARCHAR(100) | NOT NULL | - | Username for login |
| `email` | VARCHAR(255) | NOT NULL | - | Email address |
| `password_hash` | VARCHAR(255) | NOT NULL | - | Bcrypt/Argon2 hash (never plaintext) |
| `is_active` | BOOLEAN | NOT NULL | TRUE | Active status (soft delete) |
| `is_otp` | BOOLEAN | NOT NULL | FALSE | Is this an OTP (one-time password) account? |
| `must_change_password` | BOOLEAN | NOT NULL | FALSE | Force password change on next login |
| `last_login_at` | TIMESTAMP | NULL | - | Last successful login (UTC) |
| `created_at` | TIMESTAMP | NOT NULL | utcnow() | Created timestamp (UTC) |
| `updated_at` | TIMESTAMP | NOT NULL | utcnow() | Updated timestamp (UTC) |

**Primary Key:**
- `id` (UUID)

**Unique Constraints:**
- `UNIQUE (company_id, username)` — Username unique per tenant
- `UNIQUE (company_id, email)` — Email unique per tenant

**Rationale for per-tenant uniqueness:**
- Different companies can have same username/email
- Prevents cross-tenant username collision
- Aligns with A Architecture (same table, tenant isolation via `company_id`)

**Indexes:**
- `idx_users_company_id` on (`company_id`)
- `idx_users_company_username` on (`company_id`, `username`) — Login query
- `idx_users_company_email` on (`company_id`, `email`) — Email login query
- `idx_users_is_active` on (`is_active`) — Filter active users

**Foreign Keys:**
- `company_id` → `tenants.id` (ON DELETE CASCADE)

**Notes:**
- `password_hash` stores bcrypt/argon2 hash (WP-10-03 decides algorithm)
- `is_otp` + `must_change_password` support OTP accounts (Regression Test 8)
- `last_login_at` for audit trail (optional, can be NULL)

---

### C.2 Table: `roles`

**Purpose:** Define roles (employee, manager, company_admin, customer_service)

**Type:** System Data (NO `company_id` — roles are global)

**Rationale:**
- Roles are predefined and shared across all tenants
- Simplifies RBAC logic (no per-tenant role customization)
- Aligns with SYSTEM_BLUEPRINT Section 2.2 (System Data)

**Columns:**

| Column | Type | Nullable | Default | Comment |
|--------|------|----------|---------|---------|
| `id` | VARCHAR(50) | NOT NULL | - | Role ID (PK, e.g., "employee") |
| `name` | VARCHAR(100) | NOT NULL | - | Display name (e.g., "Employee") |
| `description` | TEXT | NULL | - | Role description |
| `created_at` | TIMESTAMP | NOT NULL | utcnow() | Created timestamp (UTC) |

**Primary Key:**
- `id` (VARCHAR, e.g., "employee", "manager", "company_admin", "customer_service")

**Unique Constraints:**
- `UNIQUE (id)` (enforced by PK)

**Indexes:**
- None (small table, PK index sufficient)

**Foreign Keys:**
- None

**Predefined Roles (seeded in migration):**

| id | name | description |
|----|------|-------------|
| `employee` | Employee | Regular employee (can create own attendance) |
| `manager` | Manager | Can approve attendance for team members |
| `company_admin` | Company Admin | Full access within company |
| `customer_service` | Customer Service | Can access multiple companies (assigned list) |

**Notes:**
- Roles are seeded in migration (WP-10-02)
- No per-tenant role customization (future enhancement if needed)
- `customer_service` role has special handling (see Section C.6)

---

### C.3 Table: `permissions`

**Purpose:** Define granular permissions (e.g., `attendance:approve`, `backup:export`)

**Type:** System Data (NO `company_id` — permissions are global)

**Rationale:**
- Permissions are predefined and shared across all tenants
- Simplifies RBAC logic
- Aligns with SYSTEM_BLUEPRINT Section 2.2 (System Data)

**Columns:**

| Column | Type | Nullable | Default | Comment |
|--------|------|----------|---------|---------|
| `id` | VARCHAR(100) | NOT NULL | - | Permission ID (PK, e.g., "attendance:approve") |
| `resource` | VARCHAR(50) | NOT NULL | - | Resource name (e.g., "attendance") |
| `action` | VARCHAR(50) | NOT NULL | - | Action name (e.g., "approve") |
| `description` | TEXT | NULL | - | Permission description |
| `created_at` | TIMESTAMP | NOT NULL | utcnow() | Created timestamp (UTC) |

**Primary Key:**
- `id` (VARCHAR, e.g., "attendance:approve")

**Unique Constraints:**
- `UNIQUE (id)` (enforced by PK)
- `UNIQUE (resource, action)` — Prevent duplicate resource:action pairs

**Indexes:**
- `idx_permissions_resource` on (`resource`) — Query by resource

**Foreign Keys:**
- None

**Permission Naming Convention:**
- Format: `{resource}:{action}` or `{resource}:{action}:{scope}`
- Examples:
  - `attendance:create:self` — Create own attendance
  - `attendance:approve` — Approve attendance
  - `backup:export` — Export backup
  - `audit:read` — Read audit logs
  - `tenants:manage` — Manage tenants

**Predefined Permissions (seeded in migration):**

| id | resource | action | description |
|----|----------|--------|-------------|
| `attendance:create:self` | attendance | create:self | Create own attendance record |
| `attendance:approve` | attendance | approve | Approve attendance records |
| `notifications:read:self` | notifications | read:self | Read own notifications |
| `backup:export` | backup | export | Export company backup |
| `backup:restore` | backup | restore | Restore company backup |
| `audit:read` | audit | read | Read audit logs |
| `audit:export` | audit | export | Export audit logs |
| `audit:manage` | audit | manage | Manage audit retention policies |
| `audit:purge` | audit | purge | Purge old audit logs |
| `tenants:read` | tenants | read | Read tenant information |
| `tenants:manage` | tenants | manage | Manage tenants |

**Notes:**
- Permissions are seeded in migration (WP-10-02)
- `:self` suffix indicates user can only access their own data
- No `:self` suffix means user can access all data within company

---

### C.4 Table: `user_roles`

**Purpose:** Many-to-many relationship between users and roles

**Type:** Tenant Data (has `company_id` — user-role assignment is per-tenant)

**Rationale:**
- Same user can have different roles in different companies (if multi-company access)
- Aligns with tenant isolation (user roles are scoped to company)

**Columns:**

| Column | Type | Nullable | Default | Comment |
|--------|------|----------|---------|---------|
| `id` | UUID | NOT NULL | uuid4() | Assignment ID (PK) |
| `user_id` | UUID | NOT NULL | - | User ID (FK → users.id) |
| `role_id` | VARCHAR(50) | NOT NULL | - | Role ID (FK → roles.id) |
| `company_id` | VARCHAR(255) | NOT NULL | - | Company ID (Tenant Isolation) |
| `created_at` | TIMESTAMP | NOT NULL | utcnow() | Created timestamp (UTC) |

**Primary Key:**
- `id` (UUID)

**Unique Constraints:**
- `UNIQUE (user_id, role_id, company_id)` — Prevent duplicate assignments

**Indexes:**
- `idx_user_roles_user_id` on (`user_id`) — Query user's roles
- `idx_user_roles_company_id` on (`company_id`) — Tenant isolation
- `idx_user_roles_user_company` on (`user_id`, `company_id`) — Composite query

**Foreign Keys:**
- `user_id` → `users.id` (ON DELETE CASCADE)
- `role_id` → `roles.id` (ON DELETE CASCADE)
- `company_id` → `tenants.id` (ON DELETE CASCADE)

**Notes:**
- A user can have multiple roles within same company
- Same user can have different roles in different companies (customer_service case)

---

### C.5 Table: `role_permissions`

**Purpose:** Many-to-many relationship between roles and permissions

**Type:** System Data (NO `company_id` — role-permission mapping is global)

**Rationale:**
- Role-permission mapping is predefined and shared across all tenants
- Simplifies RBAC logic (no per-tenant permission customization)

**Columns:**

| Column | Type | Nullable | Default | Comment |
|--------|------|----------|---------|---------|
| `id` | UUID | NOT NULL | uuid4() | Assignment ID (PK) |
| `role_id` | VARCHAR(50) | NOT NULL | - | Role ID (FK → roles.id) |
| `permission_id` | VARCHAR(100) | NOT NULL | - | Permission ID (FK → permissions.id) |
| `created_at` | TIMESTAMP | NOT NULL | utcnow() | Created timestamp (UTC) |

**Primary Key:**
- `id` (UUID)

**Unique Constraints:**
- `UNIQUE (role_id, permission_id)` — Prevent duplicate assignments

**Indexes:**
- `idx_role_permissions_role_id` on (`role_id`) — Query role's permissions

**Foreign Keys:**
- `role_id` → `roles.id` (ON DELETE CASCADE)
- `permission_id` → `permissions.id` (ON DELETE CASCADE)

**Predefined Mappings (seeded in migration):**

| role_id | permission_id |
|---------|---------------|
| `employee` | `attendance:create:self` |
| `employee` | `notifications:read:self` |
| `manager` | `attendance:create:self` |
| `manager` | `attendance:approve` |
| `manager` | `notifications:read:self` |
| `manager` | `audit:read` |
| `company_admin` | `attendance:create:self` |
| `company_admin` | `attendance:approve` |
| `company_admin` | `notifications:read:self` |
| `company_admin` | `backup:export` |
| `company_admin` | `backup:restore` |
| `company_admin` | `audit:read` |
| `company_admin` | `audit:export` |
| `company_admin` | `audit:manage` |
| `company_admin` | `audit:purge` |
| `company_admin` | `tenants:read` |
| `company_admin` | `tenants:manage` |
| `customer_service` | `attendance:approve` |
| `customer_service` | `audit:read` |
| `customer_service` | `tenants:read` |

**Notes:**
- Mappings are seeded in migration (WP-10-02)
- `customer_service` has limited permissions (no backup/restore)

---

### C.6 Table: `customer_service_assignments` (Optional — Future Enhancement)

**Purpose:** Track which companies a customer_service user can access

**Type:** Tenant Data (has `company_id`)

**Status:** NOT IMPLEMENTED in WP-10-02 (future enhancement)

**Rationale:**
- Customer service users need multi-company access
- JWT claim `assigned_companies` can be populated from this table
- For WP-10-02, we defer this and use a simpler approach (see Section D)

**Columns (if implemented in future):**

| Column | Type | Nullable | Default | Comment |
|--------|------|----------|---------|---------|
| `id` | UUID | NOT NULL | uuid4() | Assignment ID (PK) |
| `user_id` | UUID | NOT NULL | - | User ID (FK → users.id) |
| `company_id` | VARCHAR(255) | NOT NULL | - | Assigned company ID (FK → tenants.id) |
| `created_at` | TIMESTAMP | NOT NULL | utcnow() | Created timestamp (UTC) |

**Decision for WP-10-02:**
- ❌ Do NOT create this table in WP-10-02
- ✅ Use simpler approach: customer_service users belong to a "master" company
- ✅ JWT claim `assigned_companies` can be hardcoded or configured externally
- ✅ Future WP can add this table if needed

---

### C.7 Table: `refresh_tokens` (Optional — NOT IMPLEMENTED)

**Purpose:** Store refresh tokens for JWT token rotation

**Status:** NOT IMPLEMENTED in WP-10-02

**Rationale:**
- Refresh tokens can be stateless (signed JWT) without DB storage
- DB storage only needed if we want to revoke refresh tokens
- For WP-10-02, we use stateless refresh tokens (no DB table)

**Decision for WP-10-02:**
- ❌ Do NOT create this table
- ✅ Use stateless refresh tokens (JWT with longer expiry)
- ✅ Token revocation handled by short access token expiry (15 min)
- ✅ Future WP can add this table if revocation needed

**Extension Point (if needed in future):**
- Create `refresh_tokens` table with columns: `id`, `user_id`, `token_hash`, `expires_at`, `revoked_at`
- Store hash of refresh token (not plaintext)
- Check on refresh: if `revoked_at` is set → reject

---

### C.8 Table: `jwt_blacklist` (Optional — NOT IMPLEMENTED)

**Purpose:** Blacklist revoked JWT access tokens

**Status:** NOT IMPLEMENTED in WP-10-02

**Rationale:**
- Access tokens are short-lived (15 min)
- Blacklisting requires DB query on every request (performance cost)
- For WP-10-02, we accept 15-min window for revoked tokens

**Decision for WP-10-02:**
- ❌ Do NOT create this table
- ✅ Accept short window (15 min) for revoked tokens
- ✅ Use short access token expiry to minimize risk
- ✅ Future WP can add this table if immediate revocation needed

**Extension Point (if needed in future):**
- Create `jwt_blacklist` table with columns: `id`, `token_jti`, `expires_at`
- Store JWT `jti` claim (unique token ID)
- Check on every request: if `jti` in blacklist → reject

---

## D) RBAC Semantics

### D.1 Roles

**Predefined Roles:**

| Role | Description | Typical Users |
|------|-------------|---------------|
| `employee` | Regular employee | All staff members |
| `manager` | Team manager | Department heads, supervisors |
| `company_admin` | Company administrator | HR, IT admins |
| `customer_service` | Customer service rep | Support staff (multi-company access) |

**Role Hierarchy (Implicit):**
- `employee` < `manager` < `company_admin`
- `customer_service` is separate (not in hierarchy)

**Notes:**
- No explicit hierarchy in DB (permissions are explicit)
- Higher roles have superset of lower role permissions

---

### D.2 Permission Naming Convention

**Format:** `{resource}:{action}` or `{resource}:{action}:{scope}`

**Examples:**
- `attendance:create:self` — Create own attendance
- `attendance:approve` — Approve any attendance (within company)
- `backup:export` — Export company backup
- `audit:read` — Read audit logs

**Scope Suffixes:**
- `:self` — User can only access their own data
- No suffix — User can access all data within company

**Consistency with Existing Code:**
- Aligns with FastAPI dependency pattern: `Depends(require_permission("attendance:approve"))`
- Aligns with RBAC check pattern: `has_permission(user, "backup:export")`

---

### D.3 Customer Service Multi-Company Access

**Problem:**
- `customer_service` role needs to access multiple companies
- JWT claim `company_id` is single-valued
- How to handle multi-company access?

**Solution (WP-10-02):**
- JWT claim: `company_id` = customer service user's "home" company
- JWT claim: `assigned_companies` = `["company-A", "company-B", ...]` (array)
- Middleware: check if requested `company_id` in `assigned_companies`
- If not assigned → 403

**Schema Decision:**
- ❌ Do NOT create `customer_service_assignments` table in WP-10-02
- ✅ `assigned_companies` can be:
  - Hardcoded in JWT generation (WP-10-04)
  - Configured in environment variable
  - Stored in `users` table as JSONB column (future enhancement)
- ✅ Future WP can add `customer_service_assignments` table if needed

**JWT Claims Example:**
```json
{
  "sub": "user-123",
  "company_id": "master-company",
  "staff_id": "cs-001",
  "roles": ["customer_service"],
  "assigned_companies": ["company-A", "company-B", "company-C"],
  "exp": 1234567890
}
```

**Middleware Logic (WP-10-05):**
```python
def get_current_company_id(token: JWT, requested_company_id: str):
    if "customer_service" in token.roles:
        if requested_company_id not in token.assigned_companies:
            raise HTTPException(403, "Not assigned to this company")
    else:
        if requested_company_id != token.company_id:
            raise HTTPException(403, "Cannot access other company")
    return requested_company_id
```

---

## E) Index Strategy

### E.1 Common Query Patterns

**Login Query (most frequent):**
```sql
SELECT * FROM users
WHERE company_id = ? AND username = ? AND is_active = TRUE;
```
**Index:** `idx_users_company_username` on (`company_id`, `username`)

**Email Login Query:**
```sql
SELECT * FROM users
WHERE company_id = ? AND email = ? AND is_active = TRUE;
```
**Index:** `idx_users_company_email` on (`company_id`, `email`)

**User Roles Query:**
```sql
SELECT r.* FROM roles r
JOIN user_roles ur ON r.id = ur.role_id
WHERE ur.user_id = ? AND ur.company_id = ?;
```
**Index:** `idx_user_roles_user_company` on (`user_id`, `company_id`)

**Role Permissions Query:**
```sql
SELECT p.* FROM permissions p
JOIN role_permissions rp ON p.id = rp.permission_id
WHERE rp.role_id = ?;
```
**Index:** `idx_role_permissions_role_id` on (`role_id`)

---

### E.2 Index Summary

| Table | Index Name | Columns | Purpose |
|-------|------------|---------|---------|
| `users` | `idx_users_company_id` | (`company_id`) | Tenant isolation |
| `users` | `idx_users_company_username` | (`company_id`, `username`) | Login query |
| `users` | `idx_users_company_email` | (`company_id`, `email`) | Email login |
| `users` | `idx_users_is_active` | (`is_active`) | Filter active users |
| `user_roles` | `idx_user_roles_user_id` | (`user_id`) | Query user's roles |
| `user_roles` | `idx_user_roles_company_id` | (`company_id`) | Tenant isolation |
| `user_roles` | `idx_user_roles_user_company` | (`user_id`, `company_id`) | Composite query |
| `role_permissions` | `idx_role_permissions_role_id` | (`role_id`) | Query role's permissions |
| `permissions` | `idx_permissions_resource` | (`resource`) | Query by resource |

---

## F) Migration Plan

### F.1 Migration Sequence

**WP-10-02 will create ONE migration:**
- **Revision ID:** `006`
- **Revises:** `005` (notifications migration)
- **File:** `backend/alembic/versions/006_create_auth_tables.py`

**Tables Created (in order):**
1. `roles` (no dependencies)
2. `permissions` (no dependencies)
3. `users` (depends on `tenants`)
4. `user_roles` (depends on `users`, `roles`, `tenants`)
5. `role_permissions` (depends on `roles`, `permissions`)

**Seed Data (in same migration):**
- Insert 4 roles (`employee`, `manager`, `company_admin`, `customer_service`)
- Insert 11 permissions (see Section C.3)
- Insert role-permission mappings (see Section C.5)

---

### F.2 Upgrade Requirements

**Migration 006 upgrade() must:**
1. Create `roles` table
2. Create `permissions` table
3. Create `users` table with foreign key to `tenants`
4. Create `user_roles` table with foreign keys
5. Create `role_permissions` table with foreign keys
6. Create all indexes
7. Seed roles data (4 rows)
8. Seed permissions data (11 rows)
9. Seed role_permissions data (~20 rows)

**Idempotency:**
- Check if tables exist before creating (use `op.get_bind().execute("SELECT ...")`)
- Skip seed data if already exists

---

### F.3 Downgrade Requirements

**Migration 006 downgrade() must:**
1. Drop `role_permissions` table (drop FK constraints first)
2. Drop `user_roles` table (drop FK constraints first)
3. Drop `users` table (drop FK constraints first)
4. Drop `permissions` table
5. Drop `roles` table

**Order matters:** Drop tables with foreign keys first

---

### F.4 Testing Requirements

**After migration:**
```bash
cd backend
alembic upgrade head
alembic current  # Should show: 006 (head)

# Verify tables exist
psql -c "\d users"
psql -c "\d roles"
psql -c "\d permissions"
psql -c "\d user_roles"
psql -c "\d role_permissions"

# Verify seed data
psql -c "SELECT COUNT(*) FROM roles;"  # Should be 4
psql -c "SELECT COUNT(*) FROM permissions;"  # Should be 11
psql -c "SELECT COUNT(*) FROM role_permissions;"  # Should be ~20

# Test downgrade
alembic downgrade -1
alembic current  # Should show: 005

# Test re-upgrade
alembic upgrade head
alembic current  # Should show: 006 (head)
```

---

## G) Acceptance Mapping

### G.1 WP-10-01 Acceptance Criteria (from GATE_BASED_DEVELOPMENT.md)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Document created | ✅ | This document (AUTH_SCHEMA_SPEC.md) |
| Schema reviewed and approved | ✅ | Aligns with SA_MODULE_SPEC v1.7, SYSTEM_BLUEPRINT |
| Tables defined (users, roles, permissions, pivots) | ✅ | Section C (5 tables) |
| Columns, types, constraints specified | ✅ | Section C (detailed per table) |
| Indexes specified | ✅ | Section E (9 indexes) |
| RBAC semantics defined | ✅ | Section D (roles, permissions, mappings) |
| Migration plan specified | ✅ | Section F (migration 006) |
| Naming conventions documented | ✅ | Section B (snake_case, UUID, company_id) |
| Tenant isolation strategy documented | ✅ | Section B.4, C.1, C.4 |
| Customer service multi-company documented | ✅ | Section C.6, D.3 |

**Result:** ✅ All acceptance criteria met

---

### G.2 ACCEPTANCE_CHECKLIST.md Section 3 (Auth Module)

| Item | Status | Notes |
|------|--------|-------|
| 3.1 Users Table Exists | ⏳ | Will be created in WP-10-02 |
| 3.2 Password Hashing Works | ⏳ | Will be implemented in WP-10-03 |
| 3.3 JWT Login API Works | ⏳ | Will be implemented in WP-10-04 |
| 3.4 RBAC Permission Checks Work | ⏳ | Will be implemented in WP-10-05 |
| 3.5 JWT Required on Protected Endpoints | ⏳ | Will be implemented in WP-10-06 |

**Result:** Schema spec complete, implementation pending

---

### G.3 AUTH_TRANSITION_PLAN.md Alignment

| Requirement | Status | Notes |
|-------------|--------|-------|
| Users table schema | ✅ | Section C.1 |
| Roles table schema | ✅ | Section C.2 |
| Permissions table schema | ✅ | Section C.3 |
| User-role relationship | ✅ | Section C.4 |
| Role-permission relationship | ✅ | Section C.5 |
| Customer service multi-company | ✅ | Section C.6, D.3 |
| JWT claims structure | ✅ | Section D.3 (example provided) |
| Refresh tokens decision | ✅ | Section C.7 (not implemented, rationale provided) |
| JWT blacklist decision | ✅ | Section C.8 (not implemented, rationale provided) |

**Result:** ✅ Fully aligned with AUTH_TRANSITION_PLAN.md

---

## H) Summary

### H.1 Tables Created (WP-10-02)

| Table | Type | Rows (Seed) | Purpose |
|-------|------|-------------|---------|
| `roles` | System Data | 4 | Define roles |
| `permissions` | System Data | 11 | Define permissions |
| `users` | Tenant Data | 0 | User accounts |
| `user_roles` | Tenant Data | 0 | User-role assignments |
| `role_permissions` | System Data | ~20 | Role-permission mappings |

**Total:** 5 tables, ~35 seed rows

---

### H.2 Tables NOT Created (Deferred)

| Table | Reason | Future WP |
|-------|--------|-----------|
| `customer_service_assignments` | Simpler approach (JWT claims) | Future enhancement |
| `refresh_tokens` | Stateless refresh tokens | Future enhancement |
| `jwt_blacklist` | Short token expiry sufficient | Future enhancement |

---

### H.3 Key Decisions

1. **Roles are global** (no `company_id`) — Simplifies RBAC
2. **Permissions are global** (no `company_id`) — Simplifies RBAC
3. **User-role assignments are per-tenant** (has `company_id`) — Supports multi-company users
4. **Username/email unique per tenant** — Prevents cross-tenant collision
5. **Customer service uses JWT claims** (no DB table) — Simpler for WP-10-02
6. **No refresh token table** — Stateless refresh tokens
7. **No JWT blacklist** — Short expiry sufficient

---

### H.4 Next Steps

**WP-10-02 (Users Migration + Model):**
- Create migration `006_create_auth_tables.py`
- Implement upgrade/downgrade
- Seed roles, permissions, role_permissions
- Test migration

**WP-10-03 (Auth Repo + Password Hashing):**
- Implement `AuthRepository` with CRUD
- Implement password hashing (bcrypt/argon2)
- Unit tests

**WP-10-04 (JWT Login API):**
- Implement `POST /api/auth/login`
- Generate JWT tokens with claims
- Feature tests

**WP-10-05 (RBAC Logic):**
- Implement permission checking
- Create FastAPI dependencies
- Unit tests

**WP-10-06 (Auth Transition Batch 1):**
- Migrate attendance endpoints to JWT
- Update tests
- Regression tests

---

**Document End**

**Approved for WP-10-02 implementation.**
