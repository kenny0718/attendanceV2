# Auth Transition Plan — Header to JWT Migration

**Document Version:** 1.0  
**Created:** 2026-03-02  
**Status:** Planning

---

## 1) Overview

### Current State (Phase 0-8)
- Authentication: `X-Company-ID` header only
- No user identity (no `staff_id`, no roles)
- No password/login mechanism
- Tenant isolation works but is "trust-based" (client sends company_id)

### Target State (Phase 10+)
- Authentication: JWT tokens with claims (`company_id`, `staff_id`, `roles`)
- User identity: users table with password hashing
- RBAC: role-based permissions (`employee`, `manager`, `company_admin`, `customer_service`)
- Tenant isolation: enforced by JWT claims (server-side)

---

## 2) Transition Strategy

### Option A: Hard Cut (NOT RECOMMENDED)
- Remove header-based auth completely
- All endpoints require JWT immediately
- **Risk:** High — breaks all existing tests and clients

### Option B: Gradual Migration (RECOMMENDED) ✅

**Phase 1: Coexistence (WP-10-04)**
- JWT login API available
- Existing endpoints still accept `X-Company-ID` header
- New endpoints can optionally require JWT
- **Duration:** 1-2 WPs

**Phase 2: Batch Migration (WP-10-06+)**
- Migrate endpoints in batches (see section 3)
- Each batch: update endpoint → update tests → verify regression
- Header-based auth gradually deprecated
- **Duration:** 2-4 WPs

**Phase 3: Header Removal (Future)**
- Remove `X-Company-ID` header support completely
- All endpoints require JWT
- **Duration:** 1 WP (cleanup)

---

## 3) Endpoint Migration Batches

### Batch 1: Attendance (WP-10-06)
**Priority:** High (core business logic)

| Endpoint | Current Auth | New Auth | Required Permission |
|----------|--------------|----------|---------------------|
| `POST /api/attendance/mock-create` | Header | JWT | `attendance:create:self` |
| `POST /api/attendance/{id}/approve` | Header | JWT | `attendance:approve` |

**Regression Tests:**
- `app/modules/attendance/tests/test_api.py`
- `app/modules/attendance/tests/test_tenant_isolation.py`

**Acceptance:**
- [ ] Endpoints require JWT
- [ ] RBAC enforced (employee cannot approve)
- [ ] All tests pass with JWT tokens
- [ ] Header-based auth removed

---

### Batch 2: Notifications (Future WP)
**Priority:** Medium (read-only, low risk)

| Endpoint | Current Auth | New Auth | Required Permission |
|----------|--------------|----------|---------------------|
| `GET /api/notifications` | Header | JWT | `notifications:read:self` |

**Regression Tests:**
- `app/modules/notifications/tests/test_api.py`

**Acceptance:**
- [ ] Endpoint requires JWT
- [ ] Tenant isolation via JWT claims
- [ ] All tests pass

---

### Batch 3: Backup (Future WP)
**Priority:** High (admin-only, sensitive)

| Endpoint | Current Auth | New Auth | Required Permission |
|----------|--------------|----------|---------------------|
| `POST /api/backup/export` | Header | JWT | `backup:export` (admin only) |
| `POST /api/backup/restore` | Header | JWT | `backup:restore` (admin only) |

**Regression Tests:**
- `app/modules/backup/tests/test_api.py`
- `app/modules/backup/tests/test_tenant_isolation.py`

**Acceptance:**
- [ ] Endpoints require JWT + admin role
- [ ] Non-admin users → 403
- [ ] All tests pass

---

### Batch 4: Audit (Future WP)
**Priority:** Medium (read-only, admin/manager)

| Endpoint | Current Auth | New Auth | Required Permission |
|----------|--------------|----------|---------------------|
| `GET /api/audit/logs` | Header | JWT | `audit:read` (manager+) |
| `GET /api/audit/export` | Header | JWT | `audit:export` (admin only) |
| `GET /api/audit/retention` | Header | JWT | `audit:read` (manager+) |
| `PUT /api/audit/retention` | Header | JWT | `audit:manage` (admin only) |
| `POST /api/audit/purge` | Header | JWT | `audit:purge` (admin only) |

**Regression Tests:**
- `app/modules/audit/tests/test_audit_api.py`

**Acceptance:**
- [ ] Endpoints require JWT + correct role
- [ ] RBAC enforced
- [ ] All tests pass

---

### Batch 5: Tenants (Future WP)
**Priority:** High (admin-only, critical)

| Endpoint | Current Auth | New Auth | Required Permission |
|----------|--------------|----------|---------------------|
| `POST /api/tenants` | None (new) | JWT | `tenants:create` (super admin) |
| `GET /api/tenants` | None (new) | JWT | `tenants:read` (admin+) |
| `GET /api/tenants/{id}` | None (new) | JWT | `tenants:read` (admin+) |
| `PATCH /api/tenants/{id}` | None (new) | JWT | `tenants:manage` (admin+) |
| `DELETE /api/tenants/{id}` | None (new) | JWT | `tenants:delete` (super admin) |

**Note:** Tenants API is new, so no migration needed — just enforce JWT from start.

**Acceptance:**
- [ ] All endpoints require JWT
- [ ] Only admin/super admin can access
- [ ] All tests pass

---

## 4) Testing Strategy

### Unit Tests
- Each module's unit tests should NOT depend on auth
- Mock `current_user` in tests
- Example:
  ```python
  @pytest.fixture
  def mock_user():
      return User(id="user-1", company_id="company-A", roles=["employee"])
  
  def test_create_attendance(client, mock_user):
      # Mock get_current_user dependency
      app.dependency_overrides[get_current_user] = lambda: mock_user
      response = client.post("/api/attendance/mock-create", json={...})
      assert response.status_code == 201
  ```

### Integration Tests
- Use real JWT tokens
- Test RBAC enforcement
- Example:
  ```python
  def test_employee_cannot_approve(client, employee_token):
      headers = {"Authorization": f"Bearer {employee_token}"}
      response = client.post("/api/attendance/123/approve", headers=headers)
      assert response.status_code == 403
  ```

### Regression Tests
- After each batch migration, run ALL tests for that module
- Ensure no functionality broken
- Command:
  ```bash
  pytest app/modules/attendance/tests/ -v  # Batch 1
  pytest app/modules/notifications/tests/ -v  # Batch 2
  # etc.
  ```

---

## 5) Rollback Plan

### If JWT Migration Fails
1. **Revert code changes** (git revert)
2. **Keep header-based auth** as fallback
3. **Fix issues** in isolated branch
4. **Re-attempt migration** after fixes

### Coexistence Period
- During WP-10-04 to WP-10-06, both header and JWT work
- If JWT has issues, clients can still use header
- **Remove header support only after all batches pass**

---

## 6) Migration Checklist

### Pre-Migration (WP-10-01 to WP-10-05)
- [ ] Auth schema designed (`AUTH_SCHEMA_SPEC.md`)
- [ ] Users table created (migration 005)
- [ ] JWT login API working
- [ ] RBAC logic implemented
- [ ] All auth unit tests pass

### Batch 1: Attendance (WP-10-06)
- [ ] Endpoints updated to require JWT
- [ ] RBAC guards applied
- [ ] Tests updated to use JWT tokens
- [ ] All attendance tests pass
- [ ] Regression tests pass

### Batch 2-5: Other Modules (Future WPs)
- [ ] Notifications migrated
- [ ] Backup migrated
- [ ] Audit migrated
- [ ] Tenants enforced JWT from start

### Post-Migration (Future)
- [ ] All endpoints require JWT
- [ ] Header-based auth removed
- [ ] All tests pass
- [ ] Documentation updated

---

## 7) Customer Service Special Case

### Problem
- `customer_service` role can access multiple companies (assigned list)
- JWT claim `company_id` is single-valued
- How to handle multi-company access?

### Solution (Recommended)
- JWT claim: `company_id` = customer service's "home" company
- JWT claim: `assigned_companies` = `["company-A", "company-B", ...]`
- Middleware: check if requested `company_id` in `assigned_companies`
- If not assigned → 403

### Implementation (Future WP)
- Add `assigned_companies` to JWT claims
- Add `customer_service_check` dependency
- Apply to all endpoints

---

## 8) Timeline Estimate

| Phase | WPs | Duration | Status |
|-------|-----|----------|--------|
| Auth Schema | WP-10-01 | 0.5 day | Pending |
| Users Table | WP-10-02 | 0.5 day | Pending |
| Auth Repo | WP-10-03 | 1 day | Pending |
| JWT Login | WP-10-04 | 1 day | Pending |
| RBAC Logic | WP-10-05 | 1 day | Pending |
| Batch 1 (Attendance) | WP-10-06 | 1 day | Pending |
| Batch 2-5 | Future | 2-3 days | Pending |
| **Total** | **6-7 WPs** | **7-9 days** | - |

---

**Done. This plan will be referenced in WP-10-01 onwards.**
