# WP-11-05D — Attendance Approval Workflow

**Status**: 📋 PLANNED  
**Priority**: 🔴 P0  
**Gate**: Attendance Domain  
**Estimated Time**: 3-4 hours

---

## 🎯 Goal

Add manager approval workflow for attendance sessions.

Enable managers to:
- View pending attendance sessions
- Approve or reject sessions
- Track approval history

---

## 🔄 Workflow

```
1. Employee punches (normal or late)
   → Session created with status='pending' (if NO_MATCH)

2. Manager reviews pending sessions
   → GET /api/v1/attendance/pending

3. Manager approves or rejects
   → POST /api/v1/attendance/sessions/{id}/approve
   → POST /api/v1/attendance/sessions/{id}/reject

4. Session status updated
   → pending → approved (or rejected)
```

---

## 🔧 API Required

### 1. GET /api/v1/attendance/pending

**Purpose**: List pending sessions for manager review

**Query params**:
- `department_id` (optional): Filter by department
- `limit`, `offset`: Pagination

**Response**:
```json
{
  "sessions": [
    {
      "session_id": "uuid",
      "user_id": "uuid",
      "user_name": "張三",
      "date": "2026-03-05",
      "punch_in_time": "09:20:00",
      "punch_out_time": "18:00:00",
      "reason": "交通延誤",
      "status": "pending",
      "created_at": "2026-03-05T09:20:15Z"
    }
  ],
  "total": 5
}
```

---

### 2. POST /api/v1/attendance/sessions/{id}/approve

**Purpose**: Approve a pending session

**Request**:
```json
{
  "reviewer_notes": "已確認原因，核准"
}
```

**Response**:
```json
{
  "session_id": "uuid",
  "status": "approved",
  "reviewed_by": "manager_user_id",
  "reviewed_at": "2026-03-05T10:30:00Z"
}
```

---

### 3. POST /api/v1/attendance/sessions/{id}/reject

**Purpose**: Reject a pending session

**Request**:
```json
{
  "reviewer_notes": "原因不充分，請重新申請"
}
```

**Response**:
```json
{
  "session_id": "uuid",
  "status": "rejected",
  "reviewed_by": "manager_user_id",
  "reviewed_at": "2026-03-05T10:30:00Z"
}
```

---

## 🔐 Permission

**Manager role required**:
- Check user has `manager` role
- Check user has access to target company
- Check user has access to target department (if applicable)

**Scope validation**:
```python
if not user.is_manager:
    raise HTTPException(403, "Manager role required")

if session.company_id != user.company_id:
    raise HTTPException(403, "Cannot approve other company's sessions")
```

---

## 📊 Database Changes

### Add fields to `attendance_sessions`

New migration required:

```sql
ALTER TABLE attendance_sessions
ADD COLUMN reason TEXT,
ADD COLUMN reviewer_id UUID,
ADD COLUMN reviewer_notes TEXT,
ADD COLUMN reviewed_at TIMESTAMP WITH TIME ZONE;
```

---

## 🎨 UI Dependency

Manager dashboard needs:
- **Today attendance** page (shows all employees)
- **Approval queue** page (shows pending sessions)

---

## ✅ Verification

### Test flow

```bash
# 1. Create pending session
POST /api/v1/attendance/punch-in
POST /api/v1/attendance/punch-out
→ status='pending'

# 2. Manager lists pending
GET /api/v1/attendance/pending
→ Should see the session

# 3. Manager approves
POST /api/v1/attendance/sessions/{id}/approve
→ status becomes 'approved'

# 4. Verify
GET /api/v1/attendance/sessions/{id}
→ Check status='approved'
→ Check reviewed_by is set
→ Check reviewed_at is set
```

---

## ✅ Done Definition

- ✅ Approval endpoints exist (pending, approve, reject)
- ✅ Status transitions enforced (pending → approved/rejected)
- ✅ Manager permission validated
- ✅ Tenant isolation enforced
- ✅ All tests pass
- ✅ Approval history tracked

---

## 🔄 Next WP

**WP-11-05E**: Manager Attendance Dashboard (UI)

---

**Created**: 2026-03-05  
**Owner**: Backend Team
