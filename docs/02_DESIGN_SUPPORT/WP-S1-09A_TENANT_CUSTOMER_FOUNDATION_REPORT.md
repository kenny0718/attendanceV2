# WP-S1-09A — Tenant / Customer Creation Foundation Report

**Date**: 2026-03-20
**Status**: COMPLETE
**Type**: Backend-only — no frontend, no seed, no auth redesign, no bootstrap-admin

---

## Summary

Implemented the minimal backend foundation for platform-level tenant/customer management.

Two endpoints added under `GET /api/admin/companies` and `POST /api/admin/companies`,
both enforced as super_admin-only via the existing `Actor.is_super_admin()` pattern.

All backend layers (schema, API endpoint, service, repo) were wired using existing
infrastructure. No new models, no new service methods, no new repo methods were needed.

All 13 focused backend tests pass (13/13).

---

## Pre-Implementation Findings

### 1. Existing tenant create path

- `TenantRepository.create()` — `backend/app/modules/tenants/repo.py`
  Accepts: `tenant_id`, `name`, `timezone`, `is_active`. Commits to DB. Returns `Tenant`.
- `TenantService.create_tenant()` — `backend/app/modules/tenants/service.py`
  Wraps repo; checks `repo.exists(tenant_id)` first and raises `ValueError` if duplicate.
  This is the canonical create path reused by the new endpoint.

### 2. Existing tenant list path

- `TenantRepository.list_all(limit, offset)` — `backend/app/modules/tenants/repo.py`
  Orders by `created_at DESC`. Returns `List[Tenant]`.
- `TenantService.list_tenants(limit, offset)` — `backend/app/modules/tenants/service.py`
  Thin wrapper over repo. Already present and reused by the new list endpoint.

### 3. Existing super_admin enforcement pattern

- `get_current_actor()` — `backend/app/core/dependencies.py`
  Parses JWT, maps `role_id` → `UserRole`, constructs `Actor`. Used as `Depends(get_current_actor)`.
- `Actor.is_super_admin()` — `backend/app/core/scope.py`
  Returns `True` iff `actor.role == UserRole.SUPER_ADMIN`.
- Pattern used by all entitlement endpoints: inject `actor`, call `actor.is_super_admin()`,
  raise `HTTP 403` with `{"code": "SCOPE_FORBIDDEN", "message": "..."}` if not super_admin.
- Same pattern adopted verbatim in the two new endpoints.

### 4. Supported tenant fields used

From `Tenant` model (`backend/app/modules/tenants/models.py`):

| Field | Type | Used in schemas |
|-------|------|-----------------|
| `id` | String(50) PK | Yes |
| `name` | String(255) NOT NULL | Yes |
| `is_active` | Boolean NOT NULL | Yes (read-only in response) |
| `timezone` | String(50) NOT NULL DEFAULT 'UTC' | Yes |
| `created_at` | DateTime | Yes (response only) |
| `updated_at` | DateTime | Not included (not needed for summary) |

### 5. Duplicate constraint / path already existing

- `TenantRepository.exists(tenant_id)` performs a `COUNT` query.
- `TenantService.create_tenant()` calls `exists()` before insert and raises
  `ValueError(f"Tenant {tenant_id} already exists")` if found.
- The new `POST /api/admin/companies` endpoint catches `ValueError` and maps it to
  `HTTP 409 DUPLICATE_COMPANY`. No new constraint was needed.

---

## Files Changed

| File | Purpose | Change type |
|------|---------|-------------|
| `backend/app/modules/tenants/schemas.py` | Added `CreateCompanyRequest`, `CompanyResponse`, `CompanyListResponse` | Modified |
| `backend/app/modules/tenants/api.py` | Added `GET ""` and `POST ""` routes to existing router | Modified |
| `backend/app/modules/tenants/tests/test_companies_api.py` | 13 focused backend tests for both endpoints | New |
| `docs/02_DEVELOPMENT_STATUS/WP-S1-09A_TENANT_CUSTOMER_FOUNDATION_REPORT.md` | This report | New |

**No other files changed.**

---

## APIs Added

### GET /api/admin/companies

- **Router prefix**: `/api/admin/companies` (existing router in `tenants/api.py`)
- **Permission**: `actor.is_super_admin()` — raises `HTTP 403` otherwise
- **Service call**: `TenantService.list_tenants(limit=200, offset=0)`
- **Response**: `CompanyListResponse` — `{companies: [...], total: N}`
- **Each company item**: `id`, `name`, `is_active`, `timezone`, `created_at`

### POST /api/admin/companies

- **Permission**: `actor.is_super_admin()` — raises `HTTP 403` otherwise
- **Request body**: `CreateCompanyRequest` — `id` (required), `name` (required), `timezone` (default: `UTC`)
- **Service call**: `TenantService.create_tenant(tenant_id, name, timezone)`
- **Duplicate handling**: `ValueError` from service → `HTTP 409 DUPLICATE_COMPANY`
- **Validation errors**: Pydantic → `HTTP 422`
- **Response**: `CompanyResponse` — `id`, `name`, `is_active`, `timezone`, `created_at`
- **Status code**: `HTTP 201 Created`

---

## Access Control Validation

| Role | GET /api/admin/companies | POST /api/admin/companies |
|------|--------------------------|---------------------------|
| `super_admin` | ✅ 200 OK | ✅ 201 Created |
| `company_admin` (COMPANY_USER) | ✅ 403 SCOPE_FORBIDDEN | ✅ 403 SCOPE_FORBIDDEN |
| `employee` (COMPANY_USER) | ✅ 403 SCOPE_FORBIDDEN | ✅ 403 SCOPE_FORBIDDEN |
| Unauthenticated (no JWT) | ✅ 401 Unauthorized | ✅ 401 Unauthorized |

All validated by tests (13/13 passed).

---

## Duplicate Handling

- `TenantService.create_tenant()` calls `TenantRepository.exists(tenant_id)` before insert.
- If the tenant ID already exists, service raises `ValueError("Tenant {id} already exists")`.
- `POST /api/admin/companies` catches `ValueError` and returns:
  ```json
  HTTP 409 Conflict
  {"detail": {"code": "DUPLICATE_COMPANY", "message": "Tenant dup-co already exists"}}
  ```
- Test `test_create_company_duplicate_rejected` verifies this path.

---

## Tests

File: `backend/app/modules/tenants/tests/test_companies_api.py`

All tests use PostgreSQL Test DB + Transaction Rollback strategy
(same as existing `test_entitlements_api.py`).
Dependency injection uses `app.dependency_overrides[get_current_actor]`.

### TestListCompanies (5 tests)

| Test | Validates |
|------|-----------|
| `test_super_admin_can_list_companies` | super_admin gets 200, both tenants appear in list |
| `test_list_companies_response_shape` | Response has id, name, is_active, timezone, created_at |
| `test_company_admin_cannot_list_companies` | COMPANY_USER with admin role → 403 SCOPE_FORBIDDEN |
| `test_employee_cannot_list_companies` | COMPANY_USER with employee role → 403 SCOPE_FORBIDDEN |
| `test_unauthenticated_cannot_list_companies` | No JWT → 401 |

### TestCreateCompany (8 tests)

| Test | Validates |
|------|-----------|
| `test_super_admin_can_create_company` | super_admin gets 201, response fields correct |
| `test_create_company_default_timezone` | Omitting timezone defaults to UTC |
| `test_create_company_duplicate_rejected` | Duplicate id → 409 DUPLICATE_COMPANY |
| `test_create_company_missing_required_fields` | Missing id → 422 |
| `test_create_company_empty_id_rejected` | Empty string id → 422 (min_length=1) |
| `test_company_admin_cannot_create_company` | COMPANY_USER admin role → 403 SCOPE_FORBIDDEN |
| `test_employee_cannot_create_company` | COMPANY_USER employee role → 403 SCOPE_FORBIDDEN |
| `test_unauthenticated_cannot_create_company` | No JWT → 401 |

**Result: 13 / 13 PASSED**

```
============================= test session starts ==============================
collected 13 items

app/modules/tenants/tests/test_companies_api.py::TestListCompanies::test_super_admin_can_list_companies PASSED
app/modules/tenants/tests/test_companies_api.py::TestListCompanies::test_list_companies_response_shape PASSED
app/modules/tenants/tests/test_companies_api.py::TestListCompanies::test_company_admin_cannot_list_companies PASSED
app/modules/tenants/tests/test_companies_api.py::TestListCompanies::test_employee_cannot_list_companies PASSED
app/modules/tenants/tests/test_companies_api.py::TestListCompanies::test_unauthenticated_cannot_list_companies PASSED
app/modules/tenants/tests/test_companies_api.py::TestCreateCompany::test_super_admin_can_create_company PASSED
app/modules/tenants/tests/test_companies_api.py::TestCreateCompany::test_create_company_default_timezone PASSED
app/modules/tenants/tests/test_companies_api.py::TestCreateCompany::test_create_company_duplicate_rejected PASSED
app/modules/tenants/tests/test_companies_api.py::TestCreateCompany::test_create_company_missing_required_fields PASSED
app/modules/tenants/tests/test_companies_api.py::TestCreateCompany::test_create_company_empty_id_rejected PASSED
app/modules/tenants/tests/test_companies_api.py::TestCreateCompany::test_company_admin_cannot_create_company PASSED
app/modules/tenants/tests/test_companies_api.py::TestCreateCompany::test_employee_cannot_create_company PASSED
app/modules/tenants/tests/test_companies_api.py::TestCreateCompany::test_unauthenticated_cannot_create_company PASSED

======================= 13 passed, 19 warnings in 0.42s =======================
```

---

## Out of Scope Confirmed

- ✅ No frontend files changed
- ✅ No bootstrap-admin endpoint added
- ✅ No user creation flow added
- ✅ No membership creation flow added
- ✅ No seed changes
- ✅ No auth endpoint redesign
- ✅ No role model redesign
- ✅ No route guard changes
- ✅ No full tenant CRUD suite (no PATCH, no DELETE, no GET /{id})
- ✅ No invite / password setup flow
- ✅ No billing / subscription logic

---

## Internal Naming Note

The internal model and service use the name **Tenant** (`Tenant`, `TenantService`, `TenantRepository`).
The API path uses `/api/admin/companies` as required by the ticket spec.
No refactoring of internal naming was performed — the mismatch is documented here and
aligns with the existing codebase convention (entitlement endpoints already used `/api/admin/companies/{id}/...`).

---

*Report generated: 2026-03-20*
*Implementation: WP-S1-09A Foundation Option A (backend-only)*
