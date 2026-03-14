# WP-C1-08 Remaining Failure Reclassification

**Date**: 2026-03-12  
**Status**: Phase 2 Fixture Layer COMPLETE — Remaining failures reclassified  
**Author**: AI session (Cursor)

---

## Summary

Phase 2 fixture infrastructure work is complete.
All remaining test failures are **not pytest setup problems**.
They are product-level defects or unimplemented features.

| Category | Count | Files |
|----------|-------|-------|
| Missing API endpoint | 7 | test_out_checkpoint.py |
| Missing domain support | 5 | test_break_out_enforcement.py |
| Business logic bug | 1 | test_regression.py |
| **Total remaining** | **13** | 3 files |

---

## Group 1: Missing API Endpoint

**File**: `test_out_checkpoint.py`  
**Failing tests** (7/7):
- `TestOutCheckpointMultiSubmit::test_multi_checkpoint_allowed`
- `TestOutCheckpointGPSValidation::test_mobile_requires_gps`
- `TestOutCheckpointGPSValidation::test_pc_no_gps_allowed`
- `TestOutCheckpointDedup::test_anti_spam_duplicate_checkpoint`
- `TestOutCheckpointGPSCoordinates::test_invalid_latitude`
- `TestOutCheckpointList::test_list_checkpoints_pagination`
- `TestOutCheckpointWithoutSession::test_checkpoint_without_session`

**Exact failure cause**:
```
HTTP POST /api/v1/attendance/out-checkpoint -> 404 Not Found
```
The endpoint does not exist in `api.py`. The model (`attendance_out_checkpoints`) and repo backup exist, but the route was never registered.

**Classification**: `ENDPOINT_NOT_IMPLEMENTED`

**Evidence**:
- `grep -n "out.checkpoint" api.py` → 0 results
- Model `AttendanceOutCheckpoint` exists in `models.py` line 197
- Repo code exists in `repo.py.backup` line 624

**Suggested follow-up ticket**: `WP-C1-09` — Implement `/api/v1/attendance/out-checkpoint` endpoint

**Boundary**:
- Register route in `api.py`
- Wire `OutCheckpointRepository` from repo backup
- Add GPS validation (device_type=mobile requires gps)
- Add dedup logic (30s + 50m window)
- Add list endpoint with pagination

---

## Group 2: Missing Domain Support (location_id)

**File**: `test_break_out_enforcement.py`  
**Failing tests** (5/6):
- `test_break_out_without_location_no_policy_succeeds`
- `test_break_out_with_location_no_policy_succeeds`
- `test_break_out_within_allowed_location_succeeds`
- `test_break_out_tenant_isolation`
- `test_break_out_multiple_locations_matches_any`

**Passing test** (1/6):
- `test_break_out_outside_allowed_location_fails` ✅ (403 path — does not touch location_id)

**Exact failure cause**:
```
TypeError: AttendanceSessionRepository.create_punch() got an unexpected keyword argument 'location_id'
```
The `break-out` endpoint attempts to pass `location_id` to `create_punch()`, but the repo method does not accept this parameter. The `AttendancePunch` model may have the column, but the repo layer does not expose it.

**Classification**: `MISSING_DOMAIN_SUPPORT`

**Evidence**:
```
app/modules/attendance/api.py: break_out() calls repo.create_punch(..., location_id=...)
app/modules/attendance/repo.py: create_punch() signature does not include location_id
```

**Suggested follow-up ticket**: `WP-C1-10` — Add location_id support to create_punch()

**Boundary**:
- Add `location_id` parameter to `AttendanceSessionRepository.create_punch()`
- Verify `AttendancePunch` model has `location_id` column
- Add migration if column is missing
- No API schema changes needed

---

## Group 3: Business Logic Bug (cross-midnight duration)

**File**: `test_regression.py`  
**Failing test** (1/1):
- `TestRegressionSuite::test_8_cross_midnight_work_attribution`

**Exact failure cause**:
```
AssertionError: Expected 180 minutes, got 0
  session.duration_minutes == 0
  expected: 180 (punch_in=2026-03-31 23:00, punch_out=2026-04-01 02:00)
```
Log shows: `Closed session: id=..., duration=0m`

The `punch-out` API responds 200 OK, but `duration_minutes` is calculated as 0. Root cause is in `repo.py` close_session() or `policy_engine.py` duration calculation — likely a timezone-naive datetime comparison that treats cross-midnight as negative or zero.

**Classification**: `BUSINESS_LOGIC_BUG`

**Evidence**:
```
repo.py log: "Closed session: duration=0m"
policy_engine.py log: "late=True (388m), early_leave=True (631m), overtime=False (0m)"
Test input: punch_in=2026-03-31T23:00:00, punch_out=2026-04-01T02:00:00
Expected duration: 180 minutes
```

**Suggested follow-up ticket**: `WP-C1-11` — Fix cross-midnight duration_minutes calculation

**Boundary**:
- Investigate `repo.py` `close_session()` duration calculation
- Check if `punch_in_time` and `punch_out_time` are timezone-aware
- Fix to correctly calculate duration across midnight boundary
- Do NOT change API response schema

---

## Implementation Priority Order

Based on dependency and risk:

```
Priority 1 (Low risk, clear fix):
  WP-C1-10 — location_id support in create_punch()
  Estimated effort: 30 min
  Risk: LOW (repo-only change)

Priority 2 (Medium effort, isolated fix):
  WP-C1-11 — cross-midnight duration_minutes fix
  Estimated effort: 1 hour
  Risk: LOW-MEDIUM (repo/engine logic change)

Priority 3 (Largest scope):
  WP-C1-09 — out-checkpoint endpoint implementation
  Estimated effort: 2-3 hours
  Risk: MEDIUM (new endpoint + business logic)
```

---

## Phase 2 Fixture Work — Completed Checklist

- [x] `attendance/tests/conftest.py` created
- [x] `client()` fixture defined
- [x] `test_session(db)` fixture defined
- [x] `test_user(test_session)` fixture defined (compatible with global User model)
- [x] Module-level `client = TestClient(app)` removed from `test_out_checkpoint.py`
- [x] `test_user2` fixture fixed (removed invalid `company_id`, `username` fields)
- [x] `test_regression.py` updated to use shared fixtures
- [x] `fixture not found` errors resolved for all Phase 2 test files
- [x] Phase 1 baseline (183 passed) remains stable

---

**Report Generated**: 2026-03-12  
**Phase 2 Status**: FIXTURE_COMPLETE  
**Ready for Phase 3 (production code fixes)**: YES
