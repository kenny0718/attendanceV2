# A1-3C Backend/Test Legacy Header Path Removal — Completion Report

- Date: 2026-03-25
- Status: Completed
- Scope: Retire `X-Company-ID` / `X-User-ID` legacy header dependency path from backend and test layer
- Risk Level: Low

---

## Summary

Successfully retired all legacy header dependency functions from `backend/app/core/tenant_context.py` and cleaned up the corresponding test utility and direct test files. All production endpoints were already using the JWT actor path (`get_actor_with_company`); this ticket removed the no-op residual code that had remained since WP-C1-07 migration.

---

## Files Changed

| File | Action | Detail |
|------|--------|--------|
| `backend/app/core/tenant_context.py` | Modified | Removed 3 legacy functions: `get_current_company_id`, `get_current_company_id_with_membership`, `get_current_user_id`. Module replaced with retirement notice. |
| `backend/app/tests/utils/auth.py` | Modified | Removed `override_all_auth_dependencies` function and `from app.core.tenant_context import ...` import. Retained `create_test_actor`, `create_super_admin_actor`, `override_actor_dependency`. |
| `backend/app/modules/attendance/tests/test_out_checkpoint.py` | Modified | Replaced `override_all_auth_dependencies` with `override_actor_dependency` (7 call sites). Updated import. Functionally equivalent — endpoint already uses JWT actor only. |
| `backend/app/core/tests/test_tenant_context.py` | Deleted | Entire file (11 tests in 2 classes) protected only the legacy header path. No production coverage value after retirement. |

---

## Legacy Path Removed

### Functions retired from `tenant_context.py`

| Function | Header Dependency | Reason |
|----------|------------------|--------|
| `get_current_company_id` | `X-Company-ID` (required) | No production caller since WP-C1-07 |
| `get_current_company_id_with_membership` | `X-Company-ID` + `X-User-ID` (required) | No production caller since WP-C1-07 |
| `get_current_user_id` | `X-User-ID` (optional) | No production caller since WP-C1-07 |

### Test utility retired from `tests/utils/auth.py`

- `override_all_auth_dependencies`: was overriding both old header deps and new JWT dep simultaneously. All callers migrated to `override_actor_dependency`.

---

## Validation Result

| Check | Result |
|-------|--------|
| `python3 -m py_compile tenant_context.py` | OK ✅ |
| `python3 -m py_compile tests/utils/auth.py` | OK ✅ |
| `python3 -m py_compile test_out_checkpoint.py` | OK ✅ |
| grep: live import of old functions in any `.py` | NONE ✅ |
| grep: `override_all_auth_dependencies` in any `.py` | NONE (only comment in auth.py) ✅ |
| Remaining references to old names | Comments/docstrings only (dependencies.py:259, backup/api.py:6, audit/api.py:7, admin_location_api.py:7) ✅ |
| JWT actor path (`get_actor_with_company`) untouched | Confirmed ✅ |

---

## Known Limitations

- Comments in `backup/api.py`, `audit/api.py`, `admin_location_api.py`, and `dependencies.py` still mention `get_current_company_id` as historical context. These are harmless and not in scope for this ticket.
- No pytest run was executed (environment constraint). Validation was static only (py_compile + grep).

---

## Non-Scope Files Touched

`test_out_checkpoint.py` received a minimal mechanical substitution (`override_all_auth_dependencies` → `override_actor_dependency`), required to fix broken references after removing the old function. This is within allowed scope ("修正刪除後的引用").

---

## NEXT_WP_TICKET.md updated

NO (per task scope rules)

---

## A1-3 Series Completion Status

| Ticket | Status |
|--------|--------|
| A1-3a — Commit A1-2R to git baseline | ✅ Done |
| A1-3b — Remove frontend legacy header injection | ✅ Done |
| A1-3c — Retire backend/test legacy header path | ✅ Done (this ticket) |
