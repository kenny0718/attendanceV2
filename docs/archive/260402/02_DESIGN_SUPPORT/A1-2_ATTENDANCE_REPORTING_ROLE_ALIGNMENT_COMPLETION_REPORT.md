# A1-2 Attendance Reporting Role Alignment — Completion Report

- Date: 2026-03-24
- Status: Completed
- Scope: `GET /api/v1/attendance/sessions` authorization branch alignment only (stabilization/alignment)

## Summary

This task completed minimal authorization branch alignment for attendance sessions reporting:

- Removed the `manager` single-point runtime special-case in `get_sessions_reporting`.
- Aligned to normalized role model by using generalized admin check (`actor.is_admin()`), which covers:
  - `super_admin`
  - `company_admin`
  - `hr_manager`
- Kept employee behavior unchanged: employee can query self only.
- Preserved company scope boundary (query remains constrained by `company_id = actor.active_company_id` repository filters).

No change was made to `company-summary` logic, tenants module, frontend, or unrelated attendance endpoints.

## Files Changed

- `backend/app/modules/attendance/api.py`
- `backend/app/modules/attendance/tests/test_legacy_role_cleanup_phase1b.py`
- `backend/app/modules/attendance/tests/test_reporting_sessions.py`

## Access Rule Before / After

### Before

- `get_sessions_reporting` used:
  - `is_admin = actor.active_role_id == "manager"`
- Effect:
  - only `manager` special-case could query other users’ sessions.
  - `company_admin` / `hr_manager` / `super_admin` were not covered by this branch.

### After

- `get_sessions_reporting` now uses:
  - `is_admin = actor.is_admin()`
- Effect:
  - `super_admin`, `company_admin`, `hr_manager` can query other users’ sessions within active company scope.
  - `employee` is still restricted to own sessions only.
  - no legacy `manager` single-point special-case in code path.

## Tests Added / Updated

### Updated

- `test_legacy_role_cleanup_phase1b.py`
  - Replaced legacy assertion that required `manager` single-point branch.
  - Added assertions to protect normalized admin branch usage and absence of legacy tuple checks.

### Added (minimal in existing file)

- `test_reporting_sessions.py` (`TestSES12RoleBranchAlignment`)
  - `company_admin` can query other user sessions (200)
  - `hr_manager` can query other user sessions (200)
  - `super_admin` can query other user sessions in active company scope (200)
  - `employee` querying other user sessions is rejected (403)
  - admin querying cross-company `user_id` remains constrained by active company scope
  - cross-company data is not returned
  - current behavior is `200 + empty result`
  - this ticket did not convert this scenario to explicit 403 because scope is role branch alignment, not reporting authorization semantics redesign

## Validation Result

- Runtime test execution: **NOT RUN**
  - reason: environment does not have `pytest` installed (`python3 -m pytest` unavailable).
- Static syntax validation: **PASS**
  - `python3 -m py_compile` passed for all modified files.

## Known Limitation

- Full runtime assertions could not be executed in this environment due to missing pytest package.
- Behavior is validated by code-path alignment + syntax check; runtime test pass should be confirmed in CI/dev env with pytest available.
- If future policy decides cross-company target query should return explicit 403, it should be handled in a separate small ticket and is out of scope for A1-2.

## Non-Scope Impact

- No non-scope files were modified by this task.
- Existing unrelated working-tree changes (from prior tasks) were left untouched.

## NEXT_WP_TICKET.md updated

NO
