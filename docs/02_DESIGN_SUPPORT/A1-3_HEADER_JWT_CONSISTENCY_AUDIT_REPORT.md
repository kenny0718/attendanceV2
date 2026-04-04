# A1-3 Header / JWT Consistency Audit Report

- Date: 2026-03-24
- Status: Audit Complete
- Scope: `X-Company-ID` / `X-User-ID` header vs JWT actor consistency — frontend + backend
- Audit Depth: Medium (keyword/dependency-chain tracking, no full-module scan)

---

## 1. Executive Summary

### Overall Judgment: Yellow

The project has successfully migrated the primary authentication path to JWT actor (`get_current_actor` / `get_actor_with_company`). However, the following legacy items remain:

1. **Frontend `client.js`** sends `X-Company-ID` and `X-User-ID` on **every API request** (global interceptor). These headers are no longer read by any production endpoint. They are active technical debt with low runtime risk but non-zero confusion potential.

2. **`backend/app/core/tenant_context.py`** still contains three legacy header-based dependency functions (`get_current_company_id`, `get_current_company_id_with_membership`, `get_current_user_id`). These functions are **not imported by any production endpoint** — only referenced in tests and the test utility helper.

3. **`backend/app/tests/utils/auth.py`** still imports and overrides `get_current_company_id` / `get_current_user_id` via `override_all_auth_dependencies`. This function is logically obsolete since WP-C1-07 completed the JWT actor migration for all router_v1 endpoints.

4. **`backend/app/modules/attendance/api.py`** still contains `is_admin = actor.active_role_id == "manager"` in git HEAD (the A1-2 fix exists only as an uncommitted worktree change). This is a role branch risk noted in A1-2, not a header risk.

### Is direct full removal safe?

**Not yet for `tenant_context.py`.** The test utility `override_all_auth_dependencies` imports these legacy functions. Before removing them, the test utility and any tests using it must be verified and cleaned. The frontend removal is safe immediately.

---

## 2. Frontend Findings

### F-1: `frontend/src/api/client.js` — Global Header Injection (Active but Benign)

- **File**: `frontend/src/api/client.js` lines 23–35
- **Behavior**: Every request through `apiClient` sends:
  - `X-Company-ID`: from `localStorage.getItem('company')` → `companyData.id`
  - `X-User-ID`: from `localStorage.getItem('user')` → `userData.id`
  - `Authorization: Bearer <token>`: from `localStorage.getItem('token')`
- **Source**: `localStorage` — values set during login
- **Risk**: Headers are sent but **no production backend endpoint currently reads them**. All router_v1 / tenants / admin endpoints use JWT actor only. Headers are ignored by the server.
- **Classification**: Active but Benign (residual, no runtime behavior impact)
- **Note**: Headers are conditionally set — absent on unauthenticated requests.

### F-2: No other frontend files inject these headers

- `frontend/src/stores/` — no header injection found.
- No individual API call files manually add `X-Company-ID` or `X-User-ID`.

---

## 3. Backend Findings

### B-1: `backend/app/core/tenant_context.py` — Legacy Header Dependency Module (Residual / No-op for Production)

- **Functions defined**:
  - `get_current_company_id(x_company_id = Header(..., alias="X-Company-ID"))`
  - `get_current_company_id_with_membership(x_company_id, x_user_id = Header(...))`
  - `get_current_user_id(x_user_id = Header(None, alias="X-User-ID"))`
- **Production endpoint importers**: **NONE**
  - Full scan found no `from app.core.tenant_context import` in any production endpoint.
  - `admin_location_api.py`, `audit/api.py`, `backup/api.py` mention the old name in comments only.
- **Active importers**: test-only
  - `backend/app/core/tests/test_tenant_context.py`
  - `backend/app/tests/utils/auth.py` (`override_all_auth_dependencies`)
- **Classification**: Residual / No-op (production), Active in test layer only

### B-2: `backend/app/core/dependencies.py` — JWT Actor Primary Path (Healthy)

- `get_current_actor()`: reads only `Authorization: Bearer <token>`. Derives `active_company_id` / `active_role_id` from JWT claims + DB membership. No `X-Company-ID` / `X-User-ID` read.
- `get_actor_with_company()`: wraps `get_current_actor`, enforces `active_company_id` presence.
- **Classification**: JWT primary path — fully clean.

### B-3: `backend/app/modules/attendance/api.py` — JWT Primary, One Role Gap

- All endpoints use `Depends(get_actor_with_company)`. No header reading.
- `actor.active_company_id` is the sole company scope source.
- **Gap (line 718)**: `is_admin = actor.active_role_id == "manager"` — A1-2 role alignment fix exists in worktree but is **not committed to git HEAD**.
- **Classification**: JWT primary (clean for header audit), role gap is A1-2 scope.

### B-4: `backend/app/modules/tenants/` endpoints — JWT Primary (Healthy)

- `api.py`, `api_members.py`, `api_entitlements.py`, `api_onboarding.py` all use `Depends(get_current_actor)`.
- `actor.active_company_id` is company scope source. No header reading.
- **Classification**: JWT primary path — fully clean.

### B-5: `backend/app/tests/utils/auth.py` — Legacy Dependency Import (Test Layer Only)

- `override_all_auth_dependencies` imports `get_current_company_id` / `get_current_user_id` and overrides them for tests.
- Its docstring notes it was needed for "router_v1 endpoints that still use old header dependency" — but WP-C1-07 has completed that migration.
- No evidence found of any currently active test that calls `override_all_auth_dependencies` for a production-path purpose.
- **Classification**: Active (test utility API surface), logically obsolete.

---

## 4. Consistency Gaps

| # | Gap | Type | Risk |
|---|-----|------|------|
| G-1 | Frontend `client.js` sends `X-Company-ID` / `X-User-ID` on every request | Technical debt / residual | Low — backend ignores |
| G-2 | `tenant_context.py` legacy functions still defined and functional | Residual (no production caller) | Low — maintenance surface |
| G-3 | `tests/utils/auth.py::override_all_auth_dependencies` imports legacy deps | Active (test utility), obsolete | Low — false signal of old path |
| G-4 | `attendance/api.py` line 718: `is_admin = actor.active_role_id == "manager"` (uncommitted A1-2 fix) | Role branch gap | Medium — company_admin/hr_manager cannot query other sessions in HEAD |
| G-5 | `test_tenant_context.py` tests legacy header functions directly | Test layer residual | Low — not a production risk |

### Truly behavior-risky gap
- **G-4** only — A1-2 role branch fix not committed to HEAD.

### Technical debt / residual only
- G-1, G-2, G-3, G-5 — no current production behavior impact.

### Unknown / needs follow-up
- Whether `override_all_auth_dependencies` is called by any active test. If zero callers, can be immediately removed.

---

## 5. Risk Classification Summary

| Item | Classification | Severity |
|------|----------------|----------|
| Frontend global `X-Company-ID` / `X-User-ID` injection | Active but Benign | Low |
| `tenant_context.py` legacy functions (no production caller) | Residual / No-op | Low |
| `override_all_auth_dependencies` in test utils | Active (test layer), logically obsolete | Low |
| `is_admin = actor.active_role_id == "manager"` (uncommitted A1-2 fix) | Active and risky (role gap) | Medium |
| `test_tenant_context.py` direct header tests | Residual (test only) | Low |

---

## 6. Recommended Next Action

**Recommendation: B — Minimal targeted removal tickets**

Rationale:
- The backend production path is already clean for header/JWT consistency.
- No urgent behavior risk exists from the header residuals (G-1, G-2, G-3).
- G-4 (A1-2 role branch) is the only medium-risk item. Its fix already exists as a worktree change and only needs committing.
- Remaining items are safe to remove in small isolated tickets without requiring prior test additions.

---

## 7. Suggested Small Ticket Breakdown

### Ticket A1-3a — Commit A1-2 worktree fix to git HEAD

- **Scope**: Commit `attendance/api.py` worktree change (`is_admin = actor.is_admin()`)
- **Files**: `backend/app/modules/attendance/api.py`
- **Risk**: Low (fix already at syntax-checked worktree state)
- **Priority**: High (only medium-risk active gap)

### Ticket A1-3b — Remove frontend legacy header injection

- **Scope**: Remove `X-Company-ID` / `X-User-ID` injection block from `frontend/src/api/client.js` (lines 23–35)
- **Files**: `frontend/src/api/client.js`
- **Risk**: Low — no backend endpoint reads these headers; `Authorization` header is unaffected
- **Priority**: Medium (cleanup)

### Ticket A1-3c — Retire `tenant_context.py` legacy header dependencies

- **Scope**:
  1. Verify no test calls `override_all_auth_dependencies` for production-path coverage
  2. Remove `override_all_auth_dependencies` from `backend/app/tests/utils/auth.py`
  3. Remove `get_current_company_id`, `get_current_company_id_with_membership`, `get_current_user_id` from `backend/app/core/tenant_context.py`
  4. Remove or repurpose `backend/app/core/tests/test_tenant_context.py`
- **Files**: `backend/app/core/tenant_context.py`, `backend/app/tests/utils/auth.py`, `backend/app/core/tests/test_tenant_context.py`
- **Risk**: Low-Medium — must verify no active test caller before removing
- **Priority**: Medium (cleanup, no production behavior impact)

---

## 8. Non-Scope Impact

- No production code was modified during this audit.
- No tests were modified.
- NEXT_WP_TICKET.md was not modified.

## 9. NEXT_WP_TICKET.md updated

NO
