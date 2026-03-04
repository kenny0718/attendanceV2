# Migration Chain Audit Report
## WP-11-04A 後的 Alembic 鏈審查

**審查日期：** 2026-03-04  
**審查範圍：** backend/alembic/versions/*.py  
**測試 DB：** attendance_migration_audit_db

---

## Output（審查結果）

### 1. Graph Summary

**Current Head:**
```
wp_11_04a_entitlements (head)
```

**Heads Count:** 1 (✅ Single head, no multiple heads issue)

**Branches:** None detected

**Complete Chain (from root to head):**
```
004 (tenants) [ROOT: down_revision=None]
  ↓
3532deda024c (auth/users)
  ↓
005 (notifications)
  ↓
002 (audit_logs)
  ↓
003 (audit_retention_policies)
  ↓
001 (attendance domain) ⚠️
  ↓
wp_11_04a_entitlements (entitlements)
```

**Status:** 
- ✅ No circular dependencies
- ✅ Single head
- 🔴 **CRITICAL: Migration 001 has internal table ordering bug**
- 🔴 **CRITICAL: Fresh DB rebuild FAILS at migration 001**

---

### 2. Migration Table

| # | Filename | Revision | Down Revision | Tables Created | Special Operations |
|---|----------|----------|---------------|----------------|-------------------|
| 1 | `004_create_tenants.py` | `004` | `None` (ROOT) | `tenants` | ✅ Root migration |
| 2 | `3532deda024c_create_auth_tables_v2_platform_first.py` | `3532deda024c` | `004` | `users`, `roles`, `permissions`, `user_roles` | Auth domain |
| 3 | `005_create_notifications.py` | `005` | `3532deda024c` | `notifications` | |
| 4 | `002_create_audit_logs.py` | `002` | `005` | `audit_logs` | |
| 5 | `003_create_audit_retention_policies.py` | `003` | `002` | `audit_retention_policies` | |
| 6 | `001_create_attendance_domain_v2.py` | `001` | `003` | `attendance_sessions`, `attendance_policies`, `attendance_punches` | 🔴 **BUG: Creates sessions before policies** |
| 7 | `wp_11_04a_entitlements.py` | `wp_11_04a_entitlements` | `001` | `company_entitlements`, `support_company_assignments` | ⚠️ Was manually executed via SQL in test DB |

**Execution Order:** 004 → 3532deda024c → 005 → 002 → 003 → 001 → wp_11_04a

---

### 3. Fresh DB Rebuild Result

**Test Database:** `attendance_migration_audit_db` (全新空 DB)

**Command:**
```bash
DATABASE_URL="postgresql://postgres@127.0.0.1:5432/attendance_migration_audit_db" \
  alembic upgrade head
```

**Result:** 🔴 **FAILED**

**Error Location:** Migration `001` (Create attendance domain v2)

**Error Message:**
```
psycopg2.errors.UndefinedTable: relation "attendance_policies" does not exist

[SQL: 
CREATE TABLE attendance_sessions (
  ...
  FOREIGN KEY(policy_id) REFERENCES attendance_policies (id) ON DELETE SET NULL,
  ...
)
]
```

**Root Cause:**
Migration 001 creates tables in this order:
1. `attendance_sessions` (line 36) - **references `attendance_policies.id`**
2. `attendance_policies` (line 80) - **created AFTER sessions**
3. `attendance_punches` (line 121)

**Migrations Applied Before Failure:**
- ✅ 004 (tenants)
- ✅ 3532deda024c (auth)
- ✅ 005 (notifications)
- ✅ 002 (audit_logs)
- ✅ 003 (audit_retention_policies)
- ❌ 001 (attendance) - **FAILED**

**Tables Created in Audit DB:** None (transaction rolled back)

---

### 4. Critical Findings

#### 🔴 **P0-CRITICAL-1: Migration 001 Cannot Execute on Fresh DB**

**Issue:** 
- `attendance_sessions` table is created BEFORE `attendance_policies` table
- `attendance_sessions` has FK constraint: `FOREIGN KEY(policy_id) REFERENCES attendance_policies (id)`
- PostgreSQL rejects the FK because `attendance_policies` doesn't exist yet

**Impact:**
- ❌ **Cannot rebuild database from scratch**
- ❌ **New environments cannot be initialized**
- ❌ **CI/CD pipelines will fail**
- ❌ **Disaster recovery impossible**

**Evidence:**
```python
# alembic/versions/001_create_attendance_domain_v2.py

def upgrade() -> None:
    # Line 36: Create attendance_sessions FIRST
    op.create_table(
        'attendance_sessions',
        ...
        sa.ForeignKeyConstraint(['policy_id'], ['attendance_policies.id'], ...),  # ❌ References non-existent table
    )
    
    # Line 80: Create attendance_policies SECOND
    op.create_table(
        'attendance_policies',
        ...
    )
```

**Why This Wasn't Caught:**
- Production DB likely had manual interventions
- Test DB (attendance_test_db) manually executed migrations with SQL workarounds
- Migration 001 was **skipped** in WP-11-04A-Fix-Tests (see report)

---

#### 🔴 **P0-CRITICAL-2: Test DB Used Manual SQL Instead of Alembic**

**Issue:**
According to `docs/WP-11-04A-Fix-Tests-REPORT.md`:
- Migration 001 was **skipped** in test DB setup
- Migration wp_11_04a was **manually executed via SQL** instead of `alembic upgrade`

**Evidence from Report:**
```
Migration 執行：
- 建立測試 DB：CREATE DATABASE attendance_test_db
- 執行 migration 到 003：alembic upgrade 003
- 手動執行 wp_11_04a migration（SQL）
- 跳過 001（attendance domain，有內部順序問題）
```

**Impact:**
- ⚠️ Test DB schema != Production DB schema (if production has 001)
- ⚠️ Migration history is inconsistent
- ⚠️ `alembic current` will show wrong state
- ⚠️ Future migrations may fail due to missing base

---

#### 🟡 **P1-WARNING-1: Confusing Migration Numbering**

**Issue:**
Migration numbers don't reflect execution order:
- 004 executes FIRST (root)
- 002, 003 execute in MIDDLE
- 001 executes LAST (before wp_11_04a)

**Impact:**
- 😕 Confusing for developers
- 😕 Hard to understand migration history
- 😕 `alembic history` output is misleading

**Not Critical Because:**
- Alembic uses `down_revision` chain, not filename numbers
- Functionally works (if 001 bug is fixed)

---

#### 🟡 **P1-WARNING-2: No Validation That wp_11_04a Was Properly Applied**

**Issue:**
- wp_11_04a was manually executed via SQL in test DB
- No verification that SQL matches the migration file
- `alembic_version` table may not have correct entry

**Impact:**
- ⚠️ `alembic current` may show wrong state
- ⚠️ Future `alembic upgrade` may try to re-apply
- ⚠️ Schema drift between environments

---

### 5. Recommended Fix Plan

#### **P0 (Must Fix Before Any New Deployment)**

##### **P0-FIX-1: Fix Migration 001 Table Ordering**

**Strategy:** Create a NEW migration to fix the issue (DO NOT modify 001)

**Why Not Modify 001:**
- Production DB may have already applied 001 (with manual workarounds)
- Modifying 001 would break `alembic_version` checksums
- Alembic will detect tampering and refuse to run

**Recommended Approach:**

**Option A: Create Bridge Migration (Safest)**
```python
# alembic/versions/001b_fix_attendance_table_order.py
"""Fix attendance table creation order

Revision ID: 001b
Revises: 003
Create Date: 2026-03-04

This migration fixes the table ordering bug in 001.
It creates attendance_policies BEFORE attendance_sessions.
"""

revision = '001b'
down_revision = '003'  # Insert BEFORE 001

def upgrade() -> None:
    # Check if tables already exist (for production)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'attendance_policies' not in existing_tables:
        # Create attendance_policies FIRST
        op.create_table(
            'attendance_policies',
            # ... (copy from 001, line 80-100)
        )
    
    if 'attendance_sessions' not in existing_tables:
        # Create attendance_sessions SECOND
        op.create_table(
            'attendance_sessions',
            # ... (copy from 001, line 36-60)
        )
    
    if 'attendance_punches' not in existing_tables:
        # Create attendance_punches THIRD
        op.create_table(
            'attendance_punches',
            # ... (copy from 001, line 121-140)
        )

def downgrade() -> None:
    op.drop_table('attendance_punches')
    op.drop_table('attendance_sessions')
    op.drop_table('attendance_policies')
```

**Then:**
1. Change 001's `down_revision` from `'003'` to `'001b'`
2. Mark 001 as deprecated (add comment: "DEPRECATED: Use 001b instead")
3. Keep 001 for historical reference but it will never execute

**Migration Chain After Fix:**
```
004 → 3532deda024c → 005 → 002 → 003 → 001b (NEW) → 001 (SKIPPED) → wp_11_04a
```

**Option B: Deprecate 001 Entirely (Cleaner)**
```python
# alembic/versions/001_create_attendance_domain_v2.py
# Change down_revision to point to non-existent revision
down_revision = 'DEPRECATED'  # This will make alembic skip it

# alembic/versions/001b_create_attendance_domain_v3.py
revision = '001b'
down_revision = '003'
# ... correct table order ...
```

**Then update wp_11_04a:**
```python
# alembic/versions/wp_11_04a_entitlements.py
down_revision = '001b'  # Point to new migration
```

---

##### **P0-FIX-2: Verify and Fix Test DB State**

**Action Items:**

1. **Check alembic_version in test DB:**
```sql
SELECT * FROM alembic_version;
```

2. **If wp_11_04a is NOT in alembic_version:**
```sql
-- Manually insert (since it was applied via SQL)
INSERT INTO alembic_version (version_num) VALUES ('wp_11_04a_entitlements');
```

3. **Verify schema matches migration:**
```bash
# Compare actual tables vs expected
psql -d attendance_test_db -c "\d company_entitlements"
psql -d attendance_test_db -c "\d support_company_assignments"
```

4. **If 001 tables exist in test DB:**
```sql
-- Check if attendance tables exist
SELECT tablename FROM pg_tables WHERE schemaname='public' 
  AND tablename LIKE 'attendance_%';
```

If they DON'T exist (because 001 was skipped):
- Either apply 001b (after creating it)
- Or document that test DB is "partial schema for testing only"

---

#### **P1 (Should Fix, Not Urgent)**

##### **P1-FIX-1: Rename Migrations to Reflect Order**

**Not Recommended** because:
- Requires changing all `revision` IDs
- Breaks existing `alembic_version` entries
- High risk, low benefit

**Alternative:** Add comments to each migration file:
```python
# alembic/versions/004_create_tenants.py
"""create tenants table

Revision ID: 004
Revises: None
Create Date: 2026-03-02

EXECUTION ORDER: 1/7 (First migration)
"""
```

---

##### **P1-FIX-2: Add Migration Validation Tests**

Create a test that validates migration chain:

```python
# backend/tests/test_migrations.py
import pytest
from alembic import command
from alembic.config import Config

def test_fresh_db_migration():
    """Test that alembic upgrade head works on empty DB"""
    # Create temp DB
    # Run alembic upgrade head
    # Assert no errors
    # Assert all expected tables exist
```

---

### 6. Safe Migration Path for Production

**Assumption:** Production DB may have already applied 001 (with manual fixes)

**Step-by-Step Plan:**

1. **Check Production State:**
```sql
-- On production DB
SELECT version_num FROM alembic_version;
SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;
```

2. **If Production Has 001 Applied:**
   - Create 001b with `if not exists` checks
   - Apply 001b (will skip table creation if they exist)
   - Update wp_11_04a to point to 001b
   - Mark 001 as deprecated

3. **If Production Does NOT Have 001:**
   - Lucky! Just create 001b with correct order
   - Skip 001 entirely
   - Apply 001b → wp_11_04a

4. **For New Environments:**
   - Use 001b instead of 001
   - Clean migration path

---

### 7. Verification Checklist

After implementing fixes:

- [ ] Fresh DB: `alembic upgrade head` succeeds
- [ ] Production DB: `alembic upgrade head` succeeds (idempotent)
- [ ] Test DB: `alembic current` shows correct version
- [ ] All tables exist: `\dt` shows all expected tables
- [ ] No orphaned migrations: `alembic heads` shows single head
- [ ] History is clean: `alembic history` shows linear chain
- [ ] Tests pass: `pytest backend/tests/test_migrations.py`

---

## Summary

**Current State:** 🔴 **BROKEN - Cannot rebuild from scratch**

**Root Cause:** Migration 001 creates tables in wrong order (sessions before policies)

**Immediate Risk:** 
- New environments cannot be initialized
- Disaster recovery impossible
- CI/CD will fail

**Recommended Action:** 
- **P0:** Create 001b migration with correct table order
- **P0:** Update wp_11_04a to point to 001b
- **P0:** Deprecate 001
- **P1:** Add migration validation tests

**Estimated Effort:** 2-4 hours (including testing)

**Risk Level:** Medium (if done carefully with `if not exists` checks)

---

**Auditor:** Claude (Kiro AI)  
**Report Generated:** 2026-03-04 14:30 UTC+8
