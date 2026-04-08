# WP-11-05B — Session Status Expansion

**Status**: 📋 PLANNED  
**Priority**: 🔴 P0  
**Gate**: Attendance Domain  
**Estimated Time**: 1 hour

---

## 🎯 Goal

Extend attendance session state machine to support approval workflow.

**Current status values**:
- `open`
- `closed`

**New status values required**:
- `pending`
- `approved`
- `rejected`
- `missing_punch_out`

---

## 📋 Reason

Approval workflow requires intermediate states:
- Manager needs to review `pending` sessions
- UI needs to display approval queue
- System needs to distinguish normal completion vs approved completion

---

## 🔧 Changes Required

### 1. Update database constraint

Modify CheckConstraint in new migration:

```sql
status IN (
  'open',
  'closed',
  'pending',
  'approved',
  'rejected',
  'missing_punch_out'
)
```

### 2. Update model

File: `backend/app/modules/attendance/models.py`

Update `AttendanceSession.status` field comment.

### 3. Update schema

File: `backend/app/modules/attendance/schemas.py`

Update `SessionResponse.status` field description.

---

## 📂 Files Allowed

- ✅ New alembic migration
- ✅ `models.py`
- ✅ `schemas.py`

## ❌ Not Allowed

- ❌ No API changes yet (WP-11-05C/D)
- ❌ No workflow logic yet (WP-11-05D)

---

## ✅ Verification

### 1. Create session with new status

```python
session = AttendanceSession(
    company_id="test",
    user_id=uuid4(),
    punch_in_time=datetime.now(),
    status='pending'  # ← New status
)
db.add(session)
db.commit()  # Should not raise constraint error
```

### 2. Run tests

```bash
pytest backend/app/modules/attendance/tests/ -v
```

**Expected**: No constraint violations

---

## ✅ Done Definition

- ✅ DB constraint updated (6 status values)
- ✅ Model supports new states
- ✅ Schema updated
- ✅ No regression failures
- ✅ Migration has downgrade path

---

## 🔄 Next WP

**WP-11-05C**: Policy Engine Integration

---

**Created**: 2026-03-05  
**Owner**: Backend Team
