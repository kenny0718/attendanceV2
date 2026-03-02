# Next WP Ticket — WP-09-01

**Selected WP:** WP-09-01  
**Reason:** First step in critical path (blocks all other Phase 9-11 work)  
**Priority:** 🔴 P0

---

## WP-09-01 — Tenants: Alembic Migration Only

### Goal
Create `tenants` table migration (no code changes yet).  
This is the foundation for tenant existence validation (Gap 1).

---

### Context
- Currently, `tenant_context.py` accepts any `X-Company-ID` without validation
- This is a **security risk** (Gap 1 in GAP_REPORT.md)
- Before we can enforce validation, we need the `tenants` table to exist
- This WP creates ONLY the migration (no models, no repo, no API)

---

### Allowed Modification Scope

**✅ Allowed:**
- `@Folders backend/alembic/versions/` (new migration file)

**⛔ Forbidden:**
- Any `backend/app/` code (models, repo, service, API)
- Any tests (migration test comes in WP-09-02)
- Any other modules

---

### Expected Files

**New Files:**
```
backend/alembic/versions/004_create_tenants.py
```

**Modified Files:**
- None

---

### Migration Schema

```python
"""create tenants table

Revision ID: 004
Revises: 003
Create Date: 2026-03-02

Phase 9: Create tenants table for tenant existence validation
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Create tenants table
    
    Design:
    - id (VARCHAR 50) as PK (company_id)
    - name (VARCHAR 255) NOT NULL
    - is_active (BOOLEAN) DEFAULT TRUE
    - timezone (VARCHAR 50) DEFAULT 'UTC'
    - created_at (TIMESTAMP) DEFAULT NOW()
    - updated_at (TIMESTAMP) DEFAULT NOW()
    - Index on is_active for fast active tenant queries
    """
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(50), primary_key=True, comment='Company ID (tenant identifier)'),
        sa.Column('name', sa.String(255), nullable=False, comment='Company name'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('TRUE'), comment='Active status'),
        sa.Column('timezone', sa.String(50), nullable=False, server_default=sa.text("'UTC'"), comment='Company timezone'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'), comment='Created timestamp (UTC)'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'), comment='Updated timestamp (UTC)'),
    )
    
    # Index for fast active tenant queries
    op.create_index('idx_tenants_is_active', 'tenants', ['is_active'])

def downgrade() -> None:
    """Drop tenants table"""
    op.drop_index('idx_tenants_is_active', table_name='tenants')
    op.drop_table('tenants')
```

---

### Test Command

```bash
cd backend

# Test upgrade
alembic upgrade head

# Verify table exists
psql -h 127.0.0.1 -U attendance_user -d attendance_db -c "\d tenants"

# Test downgrade
alembic downgrade -1

# Verify table dropped
psql -h 127.0.0.1 -U attendance_user -d attendance_db -c "\d tenants"

# Re-apply
alembic upgrade head

# Verify current migration
alembic current
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Running upgrade 003 -> 004, create tenants table
```

---

### Acceptance Criteria

- [ ] Migration file `004_create_tenants.py` created
- [ ] `alembic upgrade head` succeeds
- [ ] Table `tenants` exists in DB after upgrade
- [ ] Table has columns: `id`, `name`, `is_active`, `timezone`, `created_at`, `updated_at`
- [ ] Index `idx_tenants_is_active` exists
- [ ] `alembic downgrade -1` succeeds
- [ ] Table `tenants` dropped after downgrade
- [ ] `alembic upgrade head` succeeds again (re-apply)
- [ ] `alembic current` shows revision `004`

---

### Suggested Commit Message

```
chore(tenants): add tenants table migration

- Create tenants table with id (PK), name, is_active, timezone
- Add index on is_active for fast active tenant queries
- Migration 004, revises 003
- Supports WP-09-05 tenant existence validation

Refs: WP-09-01, Gap Report #1
```

---

### Dependencies

**Prerequisite WPs:**
- None (this is the first WP in Phase 9)

**Blocks:**
- WP-09-02 (needs table to exist)
- WP-09-03 (needs model/repo from WP-09-02)
- WP-09-04 (needs service from WP-09-03)
- WP-09-05 (needs repo from WP-09-02)

---

### Estimated Time

**0.5 day** (2-4 hours)

**Breakdown:**
- Create migration file: 30 min
- Test upgrade/downgrade: 30 min
- Verify schema: 15 min
- Commit + push: 15 min

---

### Risks

**Low Risk:**
- Simple table creation (no foreign keys, no complex logic)
- Can easily rollback with `alembic downgrade -1`

**Mitigation:**
- Test on local DB first
- Verify downgrade works before committing

---

### Notes

- This WP creates ONLY the migration (no code)
- Do NOT create `tenants/models.py` yet (that's WP-09-02)
- Do NOT create `tenants/repo.py` yet (that's WP-09-02)
- Do NOT modify `tenant_context.py` yet (that's WP-09-05)

---

### Verification After Completion

Run this query to verify table structure:

```sql
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns
WHERE table_name = 'tenants'
ORDER BY ordinal_position;
```

**Expected Output:**
```
 column_name  |          data_type          | is_nullable | column_default
--------------+-----------------------------+-------------+----------------
 id           | character varying           | NO          | 
 name         | character varying           | NO          | 
 is_active    | boolean                     | NO          | true
 timezone     | character varying           | NO          | 'UTC'::text
 created_at   | timestamp without time zone | NO          | now()
 updated_at   | timestamp without time zone | NO          | now()
```

---

### Next Steps After WP-09-01

1. ✅ Commit and push
2. ✅ Update STATUS_MATRIX.md (mark migration 004 as ✅)
3. ✅ Proceed to WP-09-02 (Tenants model + repo + unit tests)

---

**Ready to Start:** Yes  
**Blocker:** None  
**Assignee:** Cursor AI  
**Status:** 🔲 Not Started
