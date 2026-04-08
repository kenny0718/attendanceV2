# WP-11-08 Phase 1 Schema Design
Leave Request System - Attendance System

**Status:** APPROVED - Design Finalized
**Date:** 2026-03-15
**WP:** WP-11-08 Leave Request System
**Phase:** Phase 1 - Backend Foundation
**Based on:** WP-11-08_PRE_EXECUTION_REPORT.md (Conclusion: NOT READY - pending manager_id addition)

---

## Purpose

This document defines the approved Phase 1 database schema for the Leave Request System (WP-11-08).

It serves as the engineering source of truth for:
- Migration file: 009_wp_11_08_create_leave_tables.py
- SQLAlchemy ORM models: backend/app/modules/leave/models.py
- Auth model update: backend/app/modules/auth/models.py (users.manager_id)

All implementation must match this document exactly.
Any deviation requires updating this document first.

---

## Confirmed Design Decisions

The following decisions are finalized and must not be changed without explicit WP authorization.

| Decision | Confirmed Value |
|----------|----------------|
| Approval model | Manager Chain + Policy Table |
| Policy mode | Strict - no policy = reject submission |
| Fallback behavior | None - no fallback to Level 1 or generic admin |
| users.manager_id exists | No - must be added in Phase 1 migration |
| Leave request reason | Required (NOT NULL) |
| Approver per request | One current authorized approver |
| Multi-step workflow | Not in Phase 1 |
| HR co-sign flow | Not in Phase 1 |
| Delegation flow | Not in Phase 1 |
| Policy scope | leave_type_id nullable (NULL = company-wide default) |
| Tenant isolation | Mandatory - all queries WHERE company_id |
| Date storage | Asia/Taipei local date (DATE type, not TIMESTAMPTZ) |

---

## Scope of Phase 1

### Included in Phase 1

- Add users.manager_id (self-referencing FK, nullable)
- Create leave_types table
- Create leave_approval_policies table
- Create leave_requests table
- Create leave_approval_logs table
- Manager Chain approval resolution (Level 1 and Level 2)
- Strict Policy Mode enforcement
- Tenant isolation on all leave tables
- Leave type annual quota tracking (dynamic calculation)
- Leave request status lifecycle (pending / approved / rejected / cancelled)

### Excluded from Phase 1

- Multi-step approval workflow engine
- HR co-sign or dual-approval flows
- Approver delegation / substitution
- Leave balance table (balances computed dynamically)
- Integration with attendance_sessions or reporting module
- Frontend UI (Phase 2)
- Leave conflict detection with attendance sessions
- Half-day leave enforcement (field is reserved, not enforced in Phase 1)
- Level 3+ approval chain

---

## Schema Components

Phase 1 introduces the following schema changes:

| Component | Type | Action |
|-----------|------|--------|
| users.manager_id | Column addition | ALTER TABLE users ADD COLUMN |
| leave_types | New table | CREATE TABLE |
| leave_approval_policies | New table | CREATE TABLE |
| leave_requests | New table | CREATE TABLE |
| leave_approval_logs | New table | CREATE TABLE |

Migration file: 009_wp_11_08_create_leave_tables.py
down_revision: 008_wp_11_13

---

## Table-by-Table Definition

### 0. users.manager_id (Column Addition - Prerequisite)

**Purpose:**
Enables Manager Chain approval resolution. This is the foundational prerequisite
for the entire leave approval system. Without this field, manager chain cannot function.

**Current State:** MISSING - does not exist in any migration (001b through 008).
Phase 1 migration must add this column before creating any leave tables.

**Field Definition:**

    Column:      manager_id
    Type:        UUID
    Nullable:    YES (employees without a manager are valid users)
    FK:          REFERENCES users(id) ON DELETE SET NULL
    Self-ref:    Yes - points to another row in the same users table

**Migration SQL:**

    ALTER TABLE users
    ADD COLUMN manager_id UUID REFERENCES users(id) ON DELETE SET NULL;

    CREATE INDEX idx_users_manager_id ON users(manager_id)
    WHERE manager_id IS NOT NULL;

**ORM Addition (auth/models.py User class):**

    manager_id = Column(
        UUID(as_uuid=True),
        ForeignKey(users.id, ondelete=SET NULL),
        nullable=True,
        comment=Direct manager user_id (self-referencing, Manager Chain)
    )

**Design Rationale:**
- Nullable: employees at the top of hierarchy have no manager
- ON DELETE SET NULL: manager leaving does not delete employee record
- Self-referencing FK: minimal change, no separate org-chart table required
- No org-chart redesign: this single field is sufficient for 2-level chain

---

### 1. leave_types

**Purpose:**
Defines the leave categories available to employees within each company.
Each company configures its own leave types independently (tenant isolation).

**Key Fields:**

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| id | UUID PK | No | gen_random_uuid() |
| company_id | VARCHAR(255) | No | Tenant isolation (FK to tenants.id) |
| code | VARCHAR(50) | No | Internal code (annual, sick, personal, etc.) |
| name | VARCHAR(100) | No | Display name shown in UI |
| description | TEXT | Yes | Optional description |
| annual_days | INTEGER | Yes | Annual quota (NULL = unlimited) |
| is_active | BOOLEAN | No | Default true; soft-delete pattern |
| created_at | TIMESTAMPTZ | No | UTC timestamp |
| updated_at | TIMESTAMPTZ | No | UTC timestamp |

**FK Relationships:**
- company_id REFERENCES tenants(id) ON DELETE CASCADE

**Constraints:**
- UNIQUE (company_id, code): leave type codes must be unique per company
- CHECK annual_days > 0 OR annual_days IS NULL

**Indexes:**
- idx_leave_types_company (company_id)
- idx_leave_types_company_active (company_id, is_active)

---

### 2. leave_approval_policies

**Purpose:**
Defines the approval level required for leave requests, based on duration and leave type.
This is the core configuration table for the Manager Chain approval system.
Each company configures its own policies independently.

**Strict Policy Mode:**
If no matching policy is found at submission time, the leave request is REJECTED with 422.
There is no fallback to Level 1 or any generic admin approval.
Companies must configure at least one policy before employees can submit leave requests.

**Key Fields:**

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| id | UUID PK | No | gen_random_uuid() |
| company_id | VARCHAR(255) | No | Tenant isolation (FK to tenants.id) |
| leave_type_id | UUID | Yes | NULL = company-wide default policy |
| min_days | NUMERIC(4,1) | No | Lower bound of duration range (inclusive) |
| max_days | NUMERIC(4,1) | Yes | Upper bound (inclusive), NULL = no upper limit |
| approval_level | INTEGER | No | Required approval level: 1 or 2 |
| is_active | BOOLEAN | No | Default true |
| created_at | TIMESTAMPTZ | No | UTC timestamp |
| updated_at | TIMESTAMPTZ | No | UTC timestamp |

**FK Relationships:**
- company_id REFERENCES tenants(id) ON DELETE CASCADE
- leave_type_id REFERENCES leave_types(id) ON DELETE CASCADE (nullable)

**Constraints:**
- CHECK min_days > 0
- CHECK max_days IS NULL OR max_days >= min_days
- CHECK approval_level IN (1, 2)

**Indexes:**
- idx_leave_approval_policies_company (company_id)
- idx_leave_approval_policies_company_active (company_id, is_active)
- idx_leave_approval_policies_company_type (company_id, leave_type_id)

**Policy Lookup Order (Service Layer):**

    Step 1: Query with company_id + leave_type_id + days range
            (type-specific policy)

    Step 2: If not found, query with company_id + leave_type_id IS NULL + days range
            (company-wide default policy)

    Step 3: If still not found, REJECT with 422
            "No leave approval policy configured for this company"
            (Strict Policy Mode - no fallback)

**Example Policy Configuration:**

| company_id | leave_type_id | min_days | max_days | approval_level |
|------------|---------------|----------|----------|----------------|
| company_a | NULL (default)| 1 | 2 | 1 |
| company_a | NULL (default)| 3 | NULL | 2 |
| company_a | sick_leave_id | 1 | NULL | 1 |

In this example: sick leave always requires only Level 1 approval regardless of duration.
Other leave types use the company-wide default (1-2 days = Level 1, 3+ days = Level 2).

---

### 3. leave_requests

**Purpose:**
Stores all leave request submissions from employees.
Each record captures the full context of a leave request including the resolved approver.

**Key Fields:**

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| id | UUID PK | No | gen_random_uuid() |
| company_id | VARCHAR(255) | No | Tenant isolation (FK to tenants.id) |
| user_id | UUID | No | Requester (FK to users.id) |
| leave_type_id | UUID | No | FK to leave_types.id |
| start_date | DATE | No | Leave start date (Asia/Taipei local date) |
| end_date | DATE | No | Leave end date inclusive (Asia/Taipei local date) |
| total_days | NUMERIC(4,1) | No | Calculated duration (supports 0.5 for half-day) |
| is_half_day | BOOLEAN | No | Default false; reserved for future use |
| reason | TEXT | No | Required - employee must provide reason |
| status | VARCHAR(20) | No | Default pending |
| required_approval_level | INTEGER | No | 1 or 2 - resolved from policy at submission |
| approver_id | UUID | Yes | Resolved from manager chain at submission time |
| approved_at | TIMESTAMPTZ | Yes | Timestamp when approved (UTC) |
| rejected_at | TIMESTAMPTZ | Yes | Timestamp when rejected (UTC) |
| cancelled_at | TIMESTAMPTZ | Yes | Timestamp when cancelled (UTC) |
| created_at | TIMESTAMPTZ | No | UTC timestamp |
| updated_at | TIMESTAMPTZ | No | UTC timestamp |

**FK Relationships:**
- company_id REFERENCES tenants(id) ON DELETE CASCADE
- user_id REFERENCES users(id) ON DELETE CASCADE
- leave_type_id REFERENCES leave_types(id) ON DELETE RESTRICT
- approver_id REFERENCES users(id) ON DELETE SET NULL

**Constraints:**
- CHECK status IN (pending, approved, rejected, cancelled)
- CHECK end_date >= start_date
- CHECK total_days > 0
- CHECK required_approval_level IN (1, 2)

**Indexes:**
- idx_leave_requests_company (company_id)
- idx_leave_requests_company_user (company_id, user_id)
- idx_leave_requests_company_status (company_id, status)
- idx_leave_requests_approver (approver_id) -- enables manager to find pending requests
- idx_leave_requests_user_dates (user_id, start_date, end_date)
- idx_leave_requests_leave_type (leave_type_id)

**Why approver_id is stored at submission time:**

The approver_id is resolved and stored when the leave request is submitted, not at approval time.
This design has several advantages:
- Immutable record: manager reassignment after submission does not change who must approve
- Efficient query: manager can query all requests WHERE approver_id = me
- Audit integrity: the approval chain at submission time is preserved
- Decoupled from org changes: org restructuring does not affect pending approvals

**Why reason is required (NOT NULL):**

Requiring a reason at submission time:
- Provides context for the approver to make informed decisions
- Creates an audit trail for compliance purposes
- Aligns with Taiwan labor law documentation requirements
- Reduces back-and-forth between employee and manager

---

### 4. leave_approval_logs

**Purpose:**
Immutable audit log of all approval actions taken on leave requests.
Every approve, reject, and cancel action creates a log entry.
This table is append-only and records are never updated or deleted.

**Key Fields:**

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| id | UUID PK | No | gen_random_uuid() |
| company_id | VARCHAR(255) | No | Tenant isolation (denormalized from leave_request) |
| leave_request_id | UUID | No | FK to leave_requests.id |
| actor_user_id | UUID | No | User who performed the action |
| action | VARCHAR(20) | No | approved / rejected / cancelled |
| approval_level | INTEGER | No | The level at which this action was taken (1 or 2) |
| comment | TEXT | Yes | Optional message from approver or requester |
| created_at | TIMESTAMPTZ | No | UTC timestamp (immutable) |

**FK Relationships:**
- company_id REFERENCES tenants(id) ON DELETE CASCADE
- leave_request_id REFERENCES leave_requests(id) ON DELETE CASCADE
- actor_user_id REFERENCES users(id) ON DELETE CASCADE

**Constraints:**
- CHECK action IN (approved, rejected, cancelled)
- CHECK approval_level IN (1, 2)
- No updated_at: this table is append-only, records are never modified

**Indexes:**
- idx_leave_approval_logs_request (leave_request_id)
- idx_leave_approval_logs_company (company_id)
- idx_leave_approval_logs_actor (actor_user_id)

**Why company_id is denormalized:**
Tenant isolation requires company_id in every query.
Denormalizing from leave_requests avoids a JOIN on every audit query
and follows the same pattern used in attendance_punches.

---

## Approval Resolution Rules

The following rules govern how the approval level and approver are determined at submission time.

### Level Definitions

| Level | Approver | Resolved Via |
|-------|----------|--------------|
| Level 1 | Direct manager | employee.manager_id |
| Level 2 | Manager of manager | employee.manager_id.manager_id |

### Submission Validation Flow

    [CHECK 1] employee.manager_id IS NULL?
              YES -> 422: Employee has no direct manager assigned
              NO  -> continue

    [CHECK 2] Query leave_approval_policies
              Step 1: company_id + leave_type_id + days range
              Step 2: company_id + leave_type_id IS NULL + days range
              NO MATCH -> 422: No leave approval policy configured
              MATCH -> approval_level resolved

    [CHECK 3] Resolve approver_id
              Level 1:
                approver_id = employee.manager_id
                (already validated in CHECK 1)

              Level 2:
                manager = get_user(employee.manager_id)
                manager.manager_id IS NULL?
                  YES -> 422: Approval chain incomplete
                  NO  -> approver_id = manager.manager_id

    [TENANT CHECK] Validate manager belongs to same company
              manager.company_membership.company_id != employee.company_id?
                YES -> 422: Manager is not in the same company

    [SUCCESS] Create leave_request with resolved approver_id

### Strict Policy Mode

> CRITICAL: There is NO fallback behavior in this system.

| Situation | Behavior |
|-----------|----------|
| No matching policy found | 422 - submission rejected |
| Policy found but Level 2 chain broken | 422 - submission rejected |
| No fallback to Level 1 | Correct - not allowed |
| No generic admin fallback | Correct - not allowed |
| No default approval level | Correct - policy must be configured |

### Approval Authorization

When approving or rejecting a leave request:

    if leave_request.approver_id != actor.user_id:
        raise 403 - Not the authorized approver for this request

Only the specifically resolved approver can take action on a request.
Generic admin role (is_admin()) does not grant approval rights.

---

## Request Status Rules

### Status Definitions

| Status | Description | Set By | Conditions |
|--------|-------------|--------|------------|
| pending | Submitted, awaiting approval | System at creation | Initial state |
| approved | Approved by authorized approver | Approver via /approve | actor.user_id == approver_id |
| rejected | Rejected by authorized approver | Approver via /reject | actor.user_id == approver_id |
| cancelled | Cancelled by requester | Requester via /cancel | actor.user_id == user_id AND status == pending |

### Status Transition Rules

    pending  -> approved    (approver action)
    pending  -> rejected    (approver action)
    pending  -> cancelled   (requester action only)

    approved  -> (terminal state, no further transitions)
    rejected  -> (terminal state, no further transitions)
    cancelled -> (terminal state, no further transitions)

### Timestamp Fields

| Action | Field Updated |
|--------|---------------|
| Approved | approved_at = NOW() UTC |
| Rejected | rejected_at = NOW() UTC |
| Cancelled | cancelled_at = NOW() UTC |
| Any action | updated_at = NOW() UTC |

### Leave Balance Impact

| Status | Counts Against Annual Quota |
|--------|------------------------------|
| pending | No |
| approved | Yes (deducted dynamically at query time) |
| rejected | No |
| cancelled | No |

Balance formula:

    available_days = leave_type.annual_days
                   - SUM(total_days WHERE status=approved
                              AND YEAR(start_date) = current_year
                              AND leave_type_id = target_type
                              AND user_id = current_user)

---

## Out-of-Scope Items

The following features are explicitly excluded from Phase 1.
They may be implemented in future WPs after Phase 1 is complete and verified.

| Feature | Reason for Exclusion |
|---------|----------------------|
| Multi-step approval workflow | Phase 3+ scope; adds significant complexity |
| HR co-sign or dual-approval | Not required for SME MVP |
| Approver delegation / substitution | Not required for MVP |
| Level 3+ approval chain | Policy table supports it structurally; deferred |
| leave_balances table | Dynamic calculation is sufficient for MVP |
| Attendance session integration | Leave and attendance are independent in MVP |
| Leave conflict detection | No overlap check with attendance sessions |
| Half-day leave enforcement | is_half_day field reserved but not enforced |
| Frontend UI | Phase 2 |
| CSV/PDF export of leave records | Future scope |
| Leave request modification after submission | Not in MVP |
| Automatic absence marking | Requires attendance integration |

---

## Final Schema Conclusion

### Why This Schema Fits Taiwan SMEs

Taiwan SME organizations typically have:
- Clear 2-3 level reporting hierarchies (employee -> manager -> director)
- Approval requirements that vary by leave duration
- Per-company policy customization needs
- Simple leave types (annual, sick, personal, bereavement)

This schema addresses all of these:
- users.manager_id: simple self-referencing field captures reporting hierarchy
- leave_approval_policies: configurable per company, per leave type, per duration
- leave_types: fully customizable per company with UNIQUE(company_id, code)
- Strict Policy Mode: forces admin setup before system goes live (no silent errors)

### Why This Schema Fits SaaS Multi-Tenant Design

Every table follows the platform-first multi-tenant architecture (SA v2.1):
- All tables have company_id as the first filtering column
- All queries enforce WHERE company_id = actor.active_company_id
- Leave types and policies are fully isolated per tenant
- manager_id cross-company validation prevents data leakage
- approval_logs denormalize company_id for efficient tenant-scoped audit queries

### Schema Readiness After Phase 1

| Item | Before Phase 1 | After Phase 1 |
|------|---------------|---------------|
| users.manager_id | MISSING (blocking) | Added (nullable self-ref FK) |
| leave_types | Does not exist | Created |
| leave_approval_policies | Does not exist | Created |
| leave_requests | Does not exist | Created |
| leave_approval_logs | Does not exist | Created |
| Manager Chain resolution | NOT POSSIBLE | Operational |
| Leave submission | NOT POSSIBLE | Operational |
| Leave approval | NOT POSSIBLE | Operational |

### Migration Summary

    File: 009_wp_11_08_create_leave_tables.py
    down_revision: 008_wp_11_13
    Tables created: 4 (leave_types, leave_approval_policies,
                       leave_requests, leave_approval_logs)
    Columns added: 1 (users.manager_id)
    Indexes added: 14
    Total schema changes: minimal and non-breaking

---

**END OF WP-11-08_PHASE1_SCHEMA_DESIGN.md**

*Author: AI (Cursor session, 2026-03-15)*
*Based on: WP-11-08_PRE_EXECUTION_REPORT.md (Conclusion: NOT READY)*
*Status: APPROVED - ready for implementation*
