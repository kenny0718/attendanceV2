# MAIN ROUTER WIRING INVENTORY

## 1. Summary
本文件僅盤點 `backend/app/main.py` 的 router wiring 結構，列出 include_router 來源、router 定義位置、prefix、endpoint 與 full path 展開，不包含設計、建議或修改。

`backend/app/main.py` 目前共有 12 個 `app.include_router(...)` 呼叫。
其中 `attendance_router_v1` 為 aggregation router；其餘目前掛載到 `main.py` 的 router 為直接掛載 router。

## 2. Files Inspected
- `backend/app/main.py`
- `backend/app/modules/attendance/api/__init__.py`
- `backend/app/modules/attendance/api/legacy.py`
- `backend/app/modules/attendance/api/punch.py`
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/api/checkpoints.py`
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/feature_gate_demo.py`
- `backend/app/modules/attendance/admin_location_api.py`
- `backend/app/modules/notifications/api.py`
- `backend/app/modules/backup/api.py`
- `backend/app/modules/audit/api.py`
- `backend/app/modules/auth/api.py`
- `backend/app/modules/tenants/api.py`
- `backend/app/modules/customer_service/api.py`
- `backend/app/modules/leave/api.py`
- `backend/app/modules/schedule/api.py`

## 3. Router Include Inventory

| line | router | source_module |
|------|--------|---------------|
| 60 | attendance_router | `app.modules.attendance.api` |
| 61 | attendance_router_v1 | `app.modules.attendance.api` |
| 62 | attendance_gate_demo_router | `app.modules.attendance.feature_gate_demo` |
| 63 | admin_location_router | `app.modules.attendance.admin_location_api` |
| 64 | notifications_router | `app.modules.notifications.api` |
| 65 | backup_router | `app.modules.backup.api` |
| 66 | audit_router | `app.modules.audit.api` |
| 67 | auth_router | `app.modules.auth.api` |
| 68 | tenants_router | `app.modules.tenants.api` |
| 69 | customer_service_router | `app.modules.customer_service.api` |
| 70 | leave_router_v1 | `app.modules.leave.api` |
| 71 | schedule_router | `app.modules.schedule.api` |

## 4. Router Definitions

| router | prefix | defined_in |
|--------|--------|------------|
| attendance_router | `/api/attendance` | `backend/app/modules/attendance/api/legacy.py` |
| attendance_router_v1 | none (aggregation router) | `backend/app/modules/attendance/api/__init__.py` |
| attendance_gate_demo_router | `/api/attendance` | `backend/app/modules/attendance/feature_gate_demo.py` |
| admin_location_router | `/api/v1/admin/allowed-locations` | `backend/app/modules/attendance/admin_location_api.py` |
| notifications_router | `/api/notifications` | `backend/app/modules/notifications/api.py` |
| backup_router | `/api/backup` | `backend/app/modules/backup/api.py` |
| audit_router | `/api/audit` | `backend/app/modules/audit/api.py` |
| auth_router | `/api/internal/auth` | `backend/app/modules/auth/api.py` |
| tenants_router | `/api/admin/companies` | `backend/app/modules/tenants/api.py` |
| customer_service_router | `/api/customer-service` | `backend/app/modules/customer_service/api.py` |
| leave_router_v1 | `/api/v1/leave` | `backend/app/modules/leave/api.py` |
| schedule_router | `/api/v1/schedule` | `backend/app/modules/schedule/api.py` |

## 5. Full Path Expansion

| module | router | prefix | endpoint | full_path |
|--------|--------|--------|----------|-----------|
| attendance | attendance_router | `/api/attendance` | `/mock-create` | `/api/attendance/mock-create` |
| attendance | attendance_router | `/api/attendance` | `/{attendance_record_id}/approve` | `/api/attendance/{attendance_record_id}/approve` |
| attendance | attendance_router_v1 → `_punch_router_v1` | `/api/v1/attendance` | `/punch-in` | `/api/v1/attendance/punch-in` |
| attendance | attendance_router_v1 → `_punch_router_v1` | `/api/v1/attendance` | `/punch-out` | `/api/v1/attendance/punch-out` |
| attendance | attendance_router_v1 → `_punch_router_v1` | `/api/v1/attendance` | `/current-status` | `/api/v1/attendance/current-status` |
| attendance | attendance_router_v1 → `_punch_router_v1` | `/api/v1/attendance` | `/history` | `/api/v1/attendance/history` |
| attendance | attendance_router_v1 → `_breaks_router_v1` | `/api/v1/attendance` | `/break-out` | `/api/v1/attendance/break-out` |
| attendance | attendance_router_v1 → `_breaks_router_v1` | `/api/v1/attendance` | `/break-in` | `/api/v1/attendance/break-in` |
| attendance | attendance_router_v1 → `_breaks_router_v1` | `/api/v1/attendance` | `/break-punches` | `/api/v1/attendance/break-punches` |
| attendance | attendance_router_v1 → `_breaks_router_v1` | `/api/v1/attendance` | `/punch/{punch_id}/note` | `/api/v1/attendance/punch/{punch_id}/note` |
| attendance | attendance_router_v1 → `_checkpoints_router_v1` | `/api/v1/attendance` | `/out-checkpoint` | `/api/v1/attendance/out-checkpoint` |
| attendance | attendance_router_v1 → `_checkpoints_router_v1` | `/api/v1/attendance` | `/out-checkpoints` | `/api/v1/attendance/out-checkpoints` |
| attendance | attendance_router_v1 → `reporting_router` | `/api/v1/attendance` | `/sessions` | `/api/v1/attendance/sessions` |
| attendance | attendance_router_v1 → `reporting_router` | `/api/v1/attendance` | `/reports/user-summary` | `/api/v1/attendance/reports/user-summary` |
| attendance | attendance_router_v1 → `reporting_router` | `/api/v1/attendance` | `/reports/company-summary` | `/api/v1/attendance/reports/company-summary` |
| attendance | attendance_gate_demo_router | `/api/attendance` | `/shift-overrides` | `/api/attendance/shift-overrides` |
| attendance | attendance_gate_demo_router | `/api/attendance` | `/shift-templates` | `/api/attendance/shift-templates` |
| attendance | attendance_gate_demo_router | `/api/attendance` | `/split-shifts` | `/api/attendance/split-shifts` |
| attendance-admin | admin_location_router | `/api/v1/admin/allowed-locations` | `` | `/api/v1/admin/allowed-locations` |
| attendance-admin | admin_location_router | `/api/v1/admin/allowed-locations` | `` | `/api/v1/admin/allowed-locations` |
| attendance-admin | admin_location_router | `/api/v1/admin/allowed-locations` | `/{location_id}` | `/api/v1/admin/allowed-locations/{location_id}` |
| attendance-admin | admin_location_router | `/api/v1/admin/allowed-locations` | `/{location_id}` | `/api/v1/admin/allowed-locations/{location_id}` |
| attendance-admin | admin_location_router | `/api/v1/admin/allowed-locations` | `/{location_id}` | `/api/v1/admin/allowed-locations/{location_id}` |
| notifications | notifications_router | `/api/notifications` | `` | `/api/notifications` |
| backup | backup_router | `/api/backup` | `/export` | `/api/backup/export` |
| backup | backup_router | `/api/backup` | `/restore` | `/api/backup/restore` |
| backup | backup_router | `/api/backup` | `/` | `/api/backup/` |
| audit | audit_router | `/api/audit` | `/logs` | `/api/audit/logs` |
| audit | audit_router | `/api/audit` | `/export` | `/api/audit/export` |
| audit | audit_router | `/api/audit` | `/retention` | `/api/audit/retention` |
| audit | audit_router | `/api/audit` | `/retention` | `/api/audit/retention` |
| audit | audit_router | `/api/audit` | `/purge` | `/api/audit/purge` |
| auth | auth_router | `/api/internal/auth` | `/login` | `/api/internal/auth/login` |
| tenants | tenants_router | `/api/admin/companies` | `` | `/api/admin/companies` |
| tenants | tenants_router | `/api/admin/companies` | `` | `/api/admin/companies` |
| tenants | tenants_router | `/api/admin/companies` | `/{company_id}` | `/api/admin/companies/{company_id}` |
| tenants | tenants_router | `/api/admin/companies` | `/{company_id}` | `/api/admin/companies/{company_id}` |
| customer_service | customer_service_router | `/api/customer-service` | `/assigned-companies` | `/api/customer-service/assigned-companies` |
| customer_service | customer_service_router | `/api/customer-service` | `/assignments` | `/api/customer-service/assignments` |
| customer_service | customer_service_router | `/api/customer-service` | `/assignments` | `/api/customer-service/assignments` |
| leave | leave_router_v1 | `/api/v1/leave` | `/requests` | `/api/v1/leave/requests` |
| leave | leave_router_v1 | `/api/v1/leave` | `/my-requests` | `/api/v1/leave/my-requests` |
| leave | leave_router_v1 | `/api/v1/leave` | `/pending` | `/api/v1/leave/pending` |
| leave | leave_router_v1 | `/api/v1/leave` | `/requests/{request_id}/approve` | `/api/v1/leave/requests/{request_id}/approve` |
| leave | leave_router_v1 | `/api/v1/leave` | `/requests/{request_id}/reject` | `/api/v1/leave/requests/{request_id}/reject` |
| schedule | schedule_router | `/api/v1/schedule` | `/shift-templates` | `/api/v1/schedule/shift-templates` |
| schedule | schedule_router | `/api/v1/schedule` | `/shift-templates` | `/api/v1/schedule/shift-templates` |
| schedule | schedule_router | `/api/v1/schedule` | `/shift-templates/{template_id}` | `/api/v1/schedule/shift-templates/{template_id}` |
| schedule | schedule_router | `/api/v1/schedule` | `/shift-templates/{template_id}` | `/api/v1/schedule/shift-templates/{template_id}` |
| schedule | schedule_router | `/api/v1/schedule` | `/shift-templates/{template_id}/activate` | `/api/v1/schedule/shift-templates/{template_id}/activate` |
| schedule | schedule_router | `/api/v1/schedule` | `/shift-templates/{template_id}/deactivate` | `/api/v1/schedule/shift-templates/{template_id}/deactivate` |
| schedule | schedule_router | `/api/v1/schedule` | `/shift-assignments` | `/api/v1/schedule/shift-assignments` |
| schedule | schedule_router | `/api/v1/schedule` | `/shift-assignments` | `/api/v1/schedule/shift-assignments` |
| schedule | schedule_router | `/api/v1/schedule` | `/shift-assignments/{assignment_id}` | `/api/v1/schedule/shift-assignments/{assignment_id}` |
| schedule | schedule_router | `/api/v1/schedule` | `/shift-assignments/{assignment_id}` | `/api/v1/schedule/shift-assignments/{assignment_id}` |
| schedule | schedule_router | `/api/v1/schedule` | `/shift-assignments/{assignment_id}/cancel` | `/api/v1/schedule/shift-assignments/{assignment_id}/cancel` |

## 6. Aggregation Mapping

### Aggregation router
- `attendance_router_v1`
  - defined in: `backend/app/modules/attendance/api/__init__.py`
  - local definition: `router_v1 = APIRouter()`
  - composed by:
    - `_punch_router_v1` from `backend/app/modules/attendance/api/punch.py`
    - `_breaks_router_v1` from `backend/app/modules/attendance/api/breaks.py`
    - `_checkpoints_router_v1` from `backend/app/modules/attendance/api/checkpoints.py`
    - `reporting_router` from `backend/app/modules/attendance/api/reporting.py`

### Directly mounted routers
- `attendance_router` → `backend/app/modules/attendance/api/legacy.py`
- `attendance_gate_demo_router` → `backend/app/modules/attendance/feature_gate_demo.py`
- `admin_location_router` → `backend/app/modules/attendance/admin_location_api.py`
- `notifications_router` → `backend/app/modules/notifications/api.py`
- `backup_router` → `backend/app/modules/backup/api.py`
- `audit_router` → `backend/app/modules/audit/api.py`
- `auth_router` → `backend/app/modules/auth/api.py`
- `tenants_router` → `backend/app/modules/tenants/api.py`
- `customer_service_router` → `backend/app/modules/customer_service/api.py`
- `leave_router_v1` → `backend/app/modules/leave/api.py`
- `schedule_router` → `backend/app/modules/schedule/api.py`

## 7. Observations
- `main.py` 內同時掛載 `/api/attendance` 與 `/api/v1/attendance` 兩種 attendance prefix。
- `attendance_router_v1` 本身沒有 prefix；prefix 來自被 include 的子 router。
- `attendance_router` 與 `attendance_gate_demo_router` 都使用 `/api/attendance` prefix。
- `admin_location_router` 使用 `/api/v1/admin/allowed-locations`，不屬於 attendance 的 `/api/attendance` 或 `/api/v1/attendance` prefix。
- `backup_router` 的 `@router.get("/")` 會形成 `/api/backup/` 路徑。
- `tenants_router` 在 `backend/app/modules/tenants/api.py` 檔內還會呼叫 `_reg_entitlements(router)`、`_reg_onboarding(router)`、`_reg_members(router)`，但這些子路由內容不在本次盤點展開範圍，因為本票僅根據 `main.py` 直接掛載 router 與其定義檔盤點。
- `schedule_router` 與 `leave_router_v1` 使用 `/api/v1/...` 形式。
- `notifications_router`、`backup_router`、`audit_router`、`auth_router`、`tenants_router`、`customer_service_router` 使用非 `/api/v1/...` prefix。
- 存在多種 prefix 格式：`/api/...`、`/api/v1/...`、`/api/internal/...`。
- 在本次盤點範圍內，未發現完全相同的 method+full_path 重複定義；但 `admin_location_router`、`tenants_router`、`schedule_router` 各自有多個不同 HTTP method 共用相同 full path。
