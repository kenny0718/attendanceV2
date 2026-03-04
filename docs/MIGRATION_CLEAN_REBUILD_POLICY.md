# Migration Chain Clean Rebuild Policy

**Last Updated:** 2026-03-04  
**Status:** ✅ ENFORCED

---

## Policy

**All new environments and CI pipelines MUST use:**

```bash
alembic upgrade head
```

**Prohibited:**
- ❌ Manual SQL execution of migrations
- ❌ Skipping migrations
- ❌ Partial migration chains
- ❌ Hand-crafted schema without alembic

---

## Enforcement

### 1. Migration Smoke Test (MANDATORY)

Location: `backend/tests/test_migration_smoke.py`

This test:
- Creates a fresh empty database
- Runs `alembic upgrade head`
- Verifies all expected tables exist
- **MUST pass before any PR is merged**

Run it:
```bash
cd backend
pytest tests/test_migration_smoke.py -v
```

### 2. CI Integration (TODO)

Add to CI pipeline:
```yaml
- name: Test Fresh DB Migration
  run: |
    cd backend
    pytest tests/test_migration_smoke.py -v
```

---

## Migration Chain History

### Current Chain (2026-03-04)

```
004 (tenants) [ROOT]
  ↓
3532deda024c (auth/users)
  ↓
005 (notifications)
  ↓
002 (audit_logs)
  ↓
003 (audit_retention_policies)
  ↓
001b (attendance_domain_FIXED) ✅ Correct table order
  ↓
wp_11_04a (entitlements) [HEAD]
```

### Deprecated Migrations

**001_create_attendance_domain_v2.py** (DEPRECATED)
- **Status:** Removed from chain (renamed to `.deprecated`)
- **Reason:** Created `attendance_sessions` BEFORE `attendance_policies`, causing FK constraint failure
- **Replacement:** `001b_create_attendance_domain_v2_fixed.py`
- **Date Deprecated:** 2026-03-04

---

## For Developers

### Adding a New Migration

1. **Create migration:**
   ```bash
   alembic revision -m "your_description"
   ```

2. **Edit the generated file:**
   - Ensure correct `down_revision`
   - Create tables in correct order (respect FK dependencies)
   - Add indexes and constraints

3. **Test on fresh DB:**
   ```bash
   # Create test DB
   createdb attendance_test_new
   
   # Run migration
   DATABASE_URL="postgresql://...attendance_test_new" alembic upgrade head
   
   # Verify
   psql attendance_test_new -c "\dt"
   
   # Cleanup
   dropdb attendance_test_new
   ```

4. **Run smoke test:**
   ```bash
   pytest tests/test_migration_smoke.py -v
   ```

5. **Only merge if smoke test passes** ✅

### Common Mistakes to Avoid

❌ **Creating tables in wrong order:**
```python
# BAD: sessions references policies, but policies created later
op.create_table('attendance_sessions', ...)  # has FK to policies
op.create_table('attendance_policies', ...)  # created AFTER
```

✅ **Correct order:**
```python
# GOOD: policies created first
op.create_table('attendance_policies', ...)
op.create_table('attendance_sessions', ...)  # FK now works
```

❌ **Skipping migrations in tests:**
```python
# BAD
alembic upgrade 003  # Skip 001
# Manually execute SQL for wp_11_04a
```

✅ **Always use full chain:**
```python
# GOOD
alembic upgrade head  # Runs all migrations
```

---

## Historical Context

### WP-11-04A-Fix-Tests (2026-03-04)

**Problem:**
- Test DB used manual SQL instead of alembic
- Migration 001 was skipped due to table ordering bug
- Fresh DB rebuild failed

**Solution:**
- Created `001b` with correct table order
- Deprecated `001` (renamed to `.deprecated`)
- Updated `wp_11_04a` to point to `001b`
- Added migration smoke test

**Result:**
- ✅ Fresh DB rebuild now works
- ✅ No manual SQL needed
- ✅ CI-ready migration chain

---

## Troubleshooting

### "Multiple heads" error

**Symptom:**
```
FAILED: Multiple head revisions are present
```

**Cause:** Two migrations have the same `down_revision`

**Fix:**
```bash
alembic heads  # See which revisions are heads
# Update one migration's down_revision to point to the other
```

### "Revision X not found" error

**Symptom:**
```
KeyError: 'some_revision_id'
```

**Cause:** A migration references a non-existent `down_revision`

**Fix:**
- Check all migration files for correct `down_revision` values
- Ensure no typos in revision IDs

### Fresh DB migration fails

**Symptom:**
```
psycopg2.errors.UndefinedTable: relation "some_table" does not exist
```

**Cause:** Table creation order violates FK constraints

**Fix:**
- Reorder table creation in the migration
- Create referenced tables BEFORE tables that reference them
- See "Common Mistakes" section above

---

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Migration Chain Audit Report](./MIGRATION_CHAIN_AUDIT_REPORT.md)
- [WP-11-04A Fix Tests Report](./WP-11-04A-Fix-Tests-REPORT.md)
