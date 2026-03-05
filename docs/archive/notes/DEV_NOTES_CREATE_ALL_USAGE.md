# create_all() Usage Report (G3-01)

**Date:** 2026-03-03  
**Purpose:** Locate all Base.metadata.create_all() calls and assess spec compliance

---

## 📍 Location Summary

### Production Code (Runtime)

| File | Line | Context | Severity |
|------|------|---------|----------|
| `app/core/database.py` | 88 | `init_db()` function | 🔴 HIGH |
| `app/main.py` | 41 | Startup event calls `init_db()` | 🔴 HIGH |

### Test Code (Test Fixtures)

| File | Line | Context | Severity |
|------|------|---------|----------|
| `app/conftest.py` | 76 | `test_db` fixture | ✅ OK (test only) |
| `app/conftest.py` | 105 | `test_db_session` fixture | ✅ OK (test only) |
| `app/conftest.py` | 134 | Another test fixture | ✅ OK (test only) |

### Test Code (Individual Table Creation)

**Note:** These use `__table__.create()` not `Base.metadata.create_all()` - different pattern

| File | Line | Pattern | Severity |
|------|------|---------|----------|
| `app/core/tests/test_tenant_context.py` | 27 | `Tenant.__table__.create()` | ✅ OK (test only) |
| `app/modules/notifications/tests/conftest.py` | 43-44 | Individual table creates | ✅ OK (test only) |
| `app/modules/backup/tests/conftest.py` | 58-60 | Individual table creates | ✅ OK (test only) |
| `app/modules/tenants/tests/test_*.py` | Various | Individual table creates | ✅ OK (test only) |
| `app/modules/attendance/tests/test_*.py` | Various | Individual table creates | ✅ OK (test only) |
| `app/modules/audit/tests/conftest.py` | 61-63 | Individual table creates | ✅ OK (test only) |

---

## 🚨 Spec Violations

### Violation 1: Production Runtime create_all()

**Location:** `app/core/database.py:88` + `app/main.py:41`

**Code:**
```python
# app/core/database.py
def init_db() -> None:
    """初始化資料庫（建立所有資料表）
    
    注意：生產環境應使用 Alembic migration
    """
    logger.info("初始化資料庫...")
    Base.metadata.create_all(bind=engine)
    logger.info("資料庫初始化完成")

# app/main.py
@app.on_event("startup")
async def startup_event():
    """應用啟動時初始化資料庫與 EventBus"""
    try:
        init_db()  # <-- Calls create_all() on every startup
        logger.info("資料庫初始化成功")
    except Exception as e:
        logger.warning(f"資料庫初始化失敗（可能尚未設定 PostgreSQL）: {e}")
```

**Why it violates spec:**
1. **SA_MODULE_SPEC v1.7** requires: "Schema changes via Alembic migrations only"
2. **GAP_REPORT.md Gap #5** identifies this as P1 spec compliance issue
3. **SYSTEM_BLUEPRINT** Section 2.3.2 states: "Use Alembic for all schema changes"

**Impact:**
- Every application startup runs `create_all()`
- Bypasses migration version control
- Can cause schema drift between environments
- Makes rollback impossible
- Conflicts with Alembic's migration tracking

**Current Mitigation:**
- Comment in code says "生產環境應使用 Alembic migration"
- Try/except catches errors if tables already exist
- But still violates spec by attempting create_all()

---

## ✅ Acceptable Usage

### Test Fixtures (conftest.py)

**Pattern:**
```python
@pytest.fixture(scope="function")
def test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)  # OK for tests
    # ...
```

**Why acceptable:**
- Test-only code (not production runtime)
- Uses in-memory SQLite or test database
- Ensures clean state for each test
- Standard pytest pattern

### Individual Table Creation in Tests

**Pattern:**
```python
Tenant.__table__.create(bind=engine, checkfirst=True)
AttendanceRecord.__table__.create(bind=engine, checkfirst=True)
```

**Why acceptable:**
- Test-only code
- Creates specific tables needed for test
- Uses `checkfirst=True` to avoid errors
- More granular than `create_all()`

---

## 📋 Minimum Fix Recommendations

### Option 1: Remove init_db() Call (Recommended)

**Changes:**
1. Remove `init_db()` call from `app/main.py:41`
2. Keep `init_db()` function for backward compatibility (mark as deprecated)
3. Add comment: "Use `alembic upgrade head` instead"

**Pros:**
- Minimal code change
- Forces proper migration usage
- Spec compliant

**Cons:**
- Requires manual `alembic upgrade head` before first run
- May break existing deployment scripts

### Option 2: Conditional init_db() (Development Only)

**Changes:**
1. Only call `init_db()` if `settings.ENVIRONMENT == "development"`
2. Add warning log if called in production

**Pros:**
- Maintains development convenience
- Prevents production violations

**Cons:**
- Still violates spec in development
- Can cause dev/prod schema drift

### Option 3: Replace with Alembic Check

**Changes:**
1. Replace `init_db()` with `check_migrations()`
2. Check if Alembic head matches DB version
3. Fail startup if migrations not applied

**Pros:**
- Enforces migration discipline
- Spec compliant
- Prevents schema drift

**Cons:**
- More complex implementation
- Requires Alembic integration

---

## 🎯 Recommended Action (G3-02)

**For G3-02 implementation:**

1. **Remove production create_all():**
   - Comment out `init_db()` call in `app/main.py`
   - Add startup check for Alembic version instead

2. **Keep test fixtures unchanged:**
   - `conftest.py` usage is acceptable
   - Individual test `__table__.create()` is acceptable

3. **Add migration for notifications:**
   - Create `005_create_notifications.py` migration
   - Make it idempotent (check if table exists)
   - This addresses the root cause of why `create_all()` was needed

4. **Update documentation:**
   - Add deployment guide: "Run `alembic upgrade head` before starting app"
   - Update README with migration commands

---

## 📊 Summary

| Category | Count | Action |
|----------|-------|--------|
| Production violations | 2 | 🔴 Must fix (G3-02) |
| Test fixtures | 3 | ✅ Keep as-is |
| Test table creates | ~17 | ✅ Keep as-is |

**Total violations requiring fix:** 2 (both in production runtime)

**Estimated effort:** Low (1-2 hours for G3-02)

---

**Generated by:** G3-01 (Gate 3, Spec Compliance)  
**Next step:** G3-02 (Add Notifications Migration + Remove create_all())
