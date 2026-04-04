# LIVE DB Role Value Inventory Report

## 1. Summary

本報告僅針對**目前線上使用中的資料庫**進行唯讀盤點，未做任何程式碼修改、migration 變更或資料清理。

盤點結果重點：
- `roles` 主表目前有 6 個角色值：`super_admin`、`company_admin`、`hr_manager`、`employee`、`customer_service`、`manager`。
- `user_company_memberships.role_id`（實際指派）目前只出現 2 個角色值：`company_admin`、`employee`。
- legacy 值 `admin`、`hr`、`system_admin` 目前在主表與指派資料都不存在。
- legacy 值 `manager` 仍存在 `roles` 主表，但目前未出現在 live assignment。

---

## 2. Active Database Target Inspected

- 來源設定：`backend/.env`（`DATABASE_URL`）
- 連線目標：`postgresql://postgres:***@127.0.0.1:5432/attendance_db`
- 實際連線驗證：
  - `current_database() = attendance_db`
  - `current_user = postgres`
  - `inet_server_addr = 127.0.0.1`
  - `inet_server_port = 5432`

> 本次所有查詢均為 `SELECT`（唯讀）。

---

## 3. Relevant Tables and Columns (Phase 1)

依 `backend/app/modules/auth/models.py` 與 `backend/app/modules/customer_service/models.py` schema 定義，role inventory 相關表如下：

### 3.1 Available Roles（可用角色主檔）
- Table: `roles`
- Columns:
  - `id` (PK, role identifier)
  - `name`
  - `description`
  - `created_at`

### 3.2 Assigned Roles（實際角色指派）
- Table: `user_company_memberships`
- Columns:
  - `role_id` (FK -> `roles.id`)  **[核心 live assignment 欄位]**
  - `user_id`
  - `company_id`
  - `is_active`
  - `created_at`
  - `updated_at`

### 3.3 Role-related Foreign Key / Mapping Data
- Table: `role_permissions`
  - `role_id` (FK -> `roles.id`)
  - 說明：屬於權限映射（role-permission mapping），不是 user assignment，但可作為角色存在性輔助證據。

### 3.4 Related Membership Context (No role_id)
- Table: `support_company_assignments`
  - 與 `customer_service` 功能相關，但表內無 role 欄位；不可直接代表 role value 指派。

### 3.5 Users table check
- Table: `users`
  - 無 `role_id` 或 role text 欄位（僅有 `manager_id`，非角色字典值）。

---

## 4. Role Master Table Inventory (Phase 2)

查詢：`SELECT id, name, description, created_at FROM roles ORDER BY id;`

| role_id | name | description | status |
|---|---|---|---|
| `company_admin` | Company Admin | Full access within company | Present in master |
| `customer_service` | Customer Service | Can access multiple companies (assigned list) | Present in master |
| `employee` | Employee | Regular employee (can create own attendance) | Present in master |
| `hr_manager` | HR Manager | HR admin access: can manage company members and view company info | Present in master |
| `manager` | Manager | Can approve attendance for team members | Present in master |
| `super_admin` | Super Admin | System-level super admin (platform scope, no company required) | Present in master |

Master rows total: **6**

---

## 5. Live Assigned Role Inventory (Phase 2)

### 5.1 `user_company_memberships`（主要 assignment 表）

查詢：`SELECT role_id, COUNT(*) FROM user_company_memberships GROUP BY role_id ORDER BY COUNT(*) DESC, role_id;`

| role_id | row_count |
|---|---:|
| `company_admin` | 2 |
| `employee` | 1 |

補充：
- `total_memberships = 3`
- `active_memberships = 3`
- `inactive_memberships = 0`

### 5.2 其他 assignment 類表

- `support_company_assignments`：無角色值欄位，不產生 role value inventory。

### 5.3 Role-permission mapping（非 user assignment）

查詢：`SELECT role_id, COUNT(*) FROM role_permissions GROUP BY role_id ORDER BY role_id;`

| role_id | role_permission_rows |
|---|---:|
| `company_admin` | 11 |
| `customer_service` | 3 |
| `employee` | 2 |
| `hr_manager` | 4 |
| `manager` | 4 |

---

## 6. Required Role Checks (Specified 9 Values)

檢核目標：
`super_admin`, `company_admin`, `hr_manager`, `employee`, `customer_service`, `manager`, `admin`, `hr`, `system_admin`

| role_id | In roles master | In memberships assignments | Classification |
|---|---|---|---|
| `super_admin` | Yes | No (0) | Present only in roles seed/master table |
| `company_admin` | Yes | Yes (2) | Active in live data; Present in assignments/memberships |
| `hr_manager` | Yes | No (0) | Present only in roles seed/master table |
| `employee` | Yes | Yes (1) | Active in live data; Present in assignments/memberships |
| `customer_service` | Yes | No (0) | Present only in roles seed/master table |
| `manager` | Yes | No (0) | Present only in roles seed/master table |
| `admin` | No | No (0) | Not present in live data |
| `hr` | No | No (0) | Not present in live data |
| `system_admin` | No | No (0) | Not present in live data |

---

## 7. Legacy Role Findings (Phase 3)

Legacy values under review: `manager`, `admin`, `hr`, `system_admin`

- `manager`
  - live assignments (`user_company_memberships.role_id`): **不存在（0）**
  - roles master: **存在**
  - 判定：目前屬於「僅存在主表/seed」
- `admin`
  - live assignments: **不存在（0）**
  - roles master: **不存在**
  - 判定：目前 live DB 未發現
- `hr`
  - live assignments: **不存在（0）**
  - roles master: **不存在**
  - 判定：目前 live DB 未發現
- `system_admin`
  - live assignments: **不存在（0）**
  - roles master: **不存在**
  - 判定：目前 live DB 未發現

---

## 8. Cleanup Safety Assessment

就**資料庫現況（live data only）**判斷：

- 直接風險（資料清理層面）：
  - `admin` / `hr` / `system_admin` 在目前資料庫看不到任何主表或 assignment 使用，資料層風險低。
  - `manager` 仍存在 `roles` 主表（且有 `role_permissions` 映射），雖無 live assignment，但不能直接視為可安全移除。

- 是否可進行 role cleanup（程式碼相容層移除）？
  - **目前不建議直接判定 safe**。
  - 原因：`manager` 仍在主表與權限映射中，且本報告僅做資料盤點，未涵蓋 runtime token、外部整合、歷史備份/匯入路徑與程式碼分支可達性驗證。

結論：**以資料證據來看，legacy roles 中僅 `manager` 仍有主表足跡；完整 cleanup 是否安全，仍需結合程式碼與流程驗證。**

---

## 9. Recommended Next Step

1. 先完成「角色治理決策」：是否保留 `manager` 作為可配置但暫未使用角色。  
2. 若目標是移除 legacy 相容層，建議再做一輪：
   - API/JWT 實際登入 token role 抽樣驗證
   - 匯入/備份還原流程 role 值驗證
   - 程式碼分支可達性（manager/admin/hr/system_admin）驗證
3. 在上述驗證全部通過後，再規劃受控清理（先停用再刪除）。

---

## Appendix — Executed Read-Only Query Set

- DB target verification:
  - `SELECT current_database(), current_user, inet_server_addr(), inet_server_port();`
- Role-related column discovery:
  - `SELECT table_schema, table_name, column_name, data_type FROM information_schema.columns WHERE column_name ILIKE '%role%' ...`
- Public table listing:
  - `SELECT table_name FROM information_schema.tables WHERE table_schema='public' ...`
- Role-related table schema columns:
  - `SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema='public' AND table_name IN (...) ...`
- Role master inventory:
  - `SELECT id, name, description, created_at FROM roles ORDER BY id;`
- Membership assignment inventory:
  - `SELECT role_id, COUNT(*) FROM user_company_memberships GROUP BY role_id ...`
- Required 9-role check:
  - CTE join of target roles vs `roles` and `user_company_memberships`
- Membership active/inactive counts:
  - `SELECT COUNT(*), COUNT(*) FILTER (...) FROM user_company_memberships;`
- Role-permission mapping counts:
  - `SELECT role_id, COUNT(*) FROM role_permissions GROUP BY role_id;`
