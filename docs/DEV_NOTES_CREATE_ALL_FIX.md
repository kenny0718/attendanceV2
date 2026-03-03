# create_all() Production Fix (G3-04)

**Date:** 2026-03-03  
**Purpose:** Remove Base.metadata.create_all() from production runtime

---

## 🔧 Changes Made

### 1. app/main.py
- **Removed:** `init_db()` call from startup event
- **Added:** Comment explaining Alembic-only requirement
- **Added:** Log message reminding to run `alembic upgrade head`

**Before:**
```python
try:
    init_db()
    logger.info("資料庫初始化成功")
except Exception as e:
    logger.warning(f"資料庫初始化失敗: {e}")
```

**After:**
```python
# Schema changes must be managed via Alembic migrations only (SA_MODULE_SPEC v1.7)
# Deployment: Run `alembic upgrade head` before starting the application
logger.info("應用啟動 - 確保已執行 alembic upgrade head")
```

### 2. app/core/database.py
- **Marked:** `init_db()` function as DEPRECATED
- **Added:** Comprehensive deprecation warning
- **Added:** Python warnings.warn() for runtime detection
- **Kept:** Function implementation for backward compatibility

---

## 📋 Deployment Requirements

### Before Starting Application

**REQUIRED:** Run Alembic migrations to ensure database schema is up-to-date:

```bash
cd backend
alembic upgrade head
```

### Verification

Check current migration version:
```bash
alembic current
# Should show: 005 (head)
```

### What Happens If Migrations Not Applied?

- Application will start successfully
- Database operations may fail if tables don't exist
- No automatic schema creation
- Clear error messages will indicate missing tables

---

## ✅ Compliance Status

**Before G3-04:**
- ❌ `Base.metadata.create_all()` called on every startup
- ❌ Violated SA_MODULE_SPEC v1.7
- ❌ Risk of schema drift

**After G3-04:**
- ✅ No `create_all()` in production runtime
- ✅ Complies with SA_MODULE_SPEC v1.7
- ✅ Schema managed exclusively by Alembic
- ✅ All tests pass (no regression)

---

## 🧪 Testing Results

All regression tests pass:

| Module | Result |
|--------|--------|
| attendance | 24 passed |
| notifications | 13 passed |
| backup | 22 passed |
| audit | 24 passed |

**Total:** 83+ passed, 0 failed

---

## 📝 Startup Behavior Change

### Old Behavior (Before G3-04)
1. Application starts
2. Calls `init_db()`
3. Runs `Base.metadata.create_all(bind=engine)`
4. Creates all tables if they don't exist
5. Continues startup

### New Behavior (After G3-04)
1. Application starts
2. Logs: "應用啟動 - 確保已執行 alembic upgrade head"
3. **Does NOT create tables**
4. Continues startup
5. Database operations will fail if migrations not applied

---

## 🚀 Deployment Checklist

- [ ] Run `alembic upgrade head` before starting app
- [ ] Verify `alembic current` shows `005 (head)`
- [ ] Update deployment scripts to include migration step
- [ ] Update CI/CD pipeline to run migrations
- [ ] Document migration requirement in README

---

**Refs:** Gate 3, G3-04, Gap Report #5, DEV_NOTES_CREATE_ALL_USAGE.md
