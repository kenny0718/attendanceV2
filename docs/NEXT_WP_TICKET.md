# Next WP Ticket — WP-11-05B

**Selected WP:** WP-11-05B  
**Reason:** WP-11-05A (Models Sync) completed, ready for status expansion  
**Priority:** 🔴 P0

---

## Completed WPs

### WP-11-05A — Attendance Models Sync
**Date**: 2026-03-05  
**Status**: ✅ COMPLETED

**Deliverables**:
- ✅ Added `AttendanceSession` model (11 columns)
- ✅ Added `AttendancePolicy` model (12 columns)
- ✅ Added `AttendancePunch` model (14 columns)
- ✅ Kept `AttendanceRecord` for backward compatibility (marked as deprecated)
- ✅ All models synced with migration 001b

**Verification Results**:
- ✅ Import test: PASS
- ✅ Column counts: PASS (11, 12, 14)
- ⚠️ Regression test: API not implemented yet (expected)

**Next**: WP-11-05B (Session Status Expansion)

---

## WP-11-05B — Session Status Expansion

### Goal
Expand attendance session status constraint to support approval workflow.

**Current status values**:
- `open`
- `closed`

**New status values required**:
- `pending`
- `approved`
- `rejected`
- `missing_punch_out`

---

### Context
- WP-11-05A completed (Models exist)
- Status constraint currently: `status IN ('open', 'closed')`
- Need to expand for approval workflow

---

### Scope

**In Scope:**
- New alembic migration to alter CheckConstraint
- Update model status field comment
- Update schema status field description

**Out of Scope:**
- ❌ No API changes yet (WP-11-05C/D)
- ❌ No workflow logic yet (WP-11-05D)

---

### Expected Files

**New Files:**
```
backend/alembic/versions/wp_11_05b_expand_session_status.py
```

**Modified Files:**
```
backend/app/modules/attendance/models.py (comment update)
backend/app/modules/attendance/schemas.py (description update)
docs/NEXT_WP_TICKET.md (update to WP-11-05C after completion)
```

---

### Acceptance Criteria

- [ ] DB constraint updated to allow 6 status values
- [ ] Model comment updated
- [ ] Schema description updated
- [ ] Migration has downgrade path
- [ ] No regression test failures

---

### Dependencies

**Prerequisite WPs:**
- ✅ WP-11-05A — COMPLETED

**Blocks:**
- WP-11-05C (Policy Engine Integration)
- WP-11-05D (Approval Workflow)

---

**Ready to Start:** Yes  
**Blocker:** None  
**Assignee:** Backend Team  
**Status:** ⏳ NEXT
