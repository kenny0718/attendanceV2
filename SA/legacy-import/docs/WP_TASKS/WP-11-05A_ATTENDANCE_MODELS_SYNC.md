# WP-11-05A — Attendance Models Sync

**Status**: 📋 PLANNED  
**Priority**: 🔴 P0  
**Gate**: Attendance Domain  
**Estimated Time**: 1.5-2 hours

---

## 🎯 Goal

Align SQLAlchemy models with existing migration:

`backend/alembic/versions/001b_create_attendance_domain_v2_fixed.py`

**Problem**:
- Migration already created 3 tables: `attendance_sessions`, `attendance_policies`, `attendance_punches`
- But `models.py` only contains: `AttendanceRecord` (old table)
- This causes:
  - ❌ ImportError in tests
  - ❌ Policy Engine cannot run
  - ❌ Next WPs blocked

---

## 📂 Scope

### ✅ Allowed to modify

- `backend/app/modules/attendance/models.py`
- `docs/NEXT_WP_TICKET.md`

### ❌ Forbidden

- ❌ Migrations (already correct)
- ❌ API files
- ❌ Service files
- ❌ Schema files

---

## 📝 Required Models

### Add (3 new classes)

1. `AttendancePolicy`
2. `AttendanceSession`
3. `AttendancePunch`

### Keep (backward compatibility)

- `AttendanceRecord` (mark as deprecated)

---

## 🔍 Schema Source

**Migration file is the source of truth.**

Models must match:
- ✅ Column names
- ✅ Column types
- ✅ Indexes
- ✅ Constraints
- ✅ Foreign keys

**No schema guessing allowed.**

---

## ✅ Verification

### 1. Import test

```bash
cd /opt/attendance-system/backend
python3 -c "from app.modules.attendance.models import AttendanceSession, AttendancePolicy, AttendancePunch; print('✅ Import success')"
```

**Expected**: No ImportError

### 2. Column count test

```bash
python3 -c "from app.modules.attendance.models import AttendanceSession; print(f'Columns: {len(AttendanceSession.__table__.columns)}')"
```

**Expected**: 12 columns

### 3. Run regression test

```bash
pytest backend/app/modules/attendance/tests/test_regression.py::TestRegressionSuite::test_8_cross_midnight_work_attribution -v
```

**Expected**: Tests run without ImportError (may SKIP, but no import errors)

---

## ✅ Done Definition

- ✅ Models import successfully
- ✅ Column counts match migration (12, 12, 14)
- ✅ Constraints match migration
- ✅ Regression tests run (no ImportError)
- ✅ `NEXT_WP_TICKET.md` updated

---

## 🔄 Next WP

**WP-11-05B**: Session Status Expansion

---

**Created**: 2026-03-05  
**Owner**: Backend Team
