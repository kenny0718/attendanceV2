# WP-11-05C — Policy Engine Integration

**Status**: 📋 PLANNED  
**Priority**: 🔴 P0  
**Gate**: Attendance Domain  
**Estimated Time**: 2-3 hours

---

## 🎯 Goal

Integrate `AttendancePolicyEngine` into punch-out process.

**Current situation**:
- ✅ Policy Engine exists (`policy_engine.py`, 24KB)
- ❌ But not connected to API
- ❌ No automatic late/overtime detection

**Target**: Punch-out automatically evaluates policy and stores result.

---

## 🔄 Target Flow

```
1. Employee punch-in
   → Create session (status='open')

2. Employee punch-out
   → Calculate:
      - is_late, late_minutes
      - is_early_leave, early_leave_minutes
      - is_overtime, overtime_minutes
      - duration_minutes
   → Store result in session
   → Return policy_evaluation in response
```

---

## 🔧 API Impact

### Modify endpoint

**POST** `/api/v1/attendance/punch-out`

Add policy evaluation step:

```python
# After punch-out
policy = get_user_policy(user_id, company_id)
evaluation = policy_engine.evaluate(session, policy)

# Update session
session.duration_minutes = evaluation['work_minutes']
session.policy_id = policy.id if policy else None

# Return in response
return {
    "session": session,
    "policy_evaluation": evaluation  # ← New field
}
```

---

## 📊 Expected Behavior

### Scenario 1: On-time punch

```
Punch-in:  09:00 (policy start: 09:00)
Punch-out: 18:00 (policy end: 18:00)

Result:
- is_late: false
- is_overtime: false
- duration_minutes: 540
```

### Scenario 2: Late punch

```
Punch-in:  09:20 (20 min late, grace=15)
Punch-out: 18:00

Result:
- is_late: true
- late_minutes: 5 (20 - 15 grace)
- duration_minutes: 520
```

### Scenario 3: Overtime

```
Punch-in:  09:00
Punch-out: 19:00 (1 hour overtime)

Result:
- is_overtime: true
- overtime_minutes: 60
- duration_minutes: 600
```

---

## 📂 Data Fields Updated

In `AttendanceSession`:
- `duration_minutes` ← calculated
- `policy_id` ← applied policy
- `notes` ← optional (policy evaluation notes)

---

## ✅ Verification

### Test flow

```bash
# 1. Punch-in
POST /api/v1/attendance/punch-in
→ session_id

# 2. Punch-out
POST /api/v1/attendance/punch-out
→ Check response has policy_evaluation

# 3. Query session
GET /api/v1/attendance/sessions/{session_id}
→ Check duration_minutes is set
→ Check policy_id is set
```

---

## ✅ Done Definition

- ✅ Punch-out runs `policy_engine.evaluate()`
- ✅ Session record updated with duration/policy
- ✅ API response includes `policy_evaluation`
- ✅ All tests pass
- ✅ Cross-midnight scenarios work

---

## 🔄 Next WP

**WP-11-05D**: Approval Workflow

---

**Created**: 2026-03-05  
**Owner**: Backend Team
