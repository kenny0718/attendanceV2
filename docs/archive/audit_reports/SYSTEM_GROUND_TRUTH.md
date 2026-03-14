# SYSTEM GROUND TRUTH

掃描日期: 2026-03-11
性質: 純驗證 Read-Only
目的: 建立開發規劃前的權威系統現況基線

---

## 1. Authentication Reality

### 1.1 get_current_company_id 實作方式

檔案: backend/app/core/tenant_context.py
L23: x_company_id = Header(..., alias="X-Company-ID")
L57: 缺少 header 回傳 400

結論: 所有 endpoint 身份識別來自 HTTP Header，非 JWT。

### 1.2 各模組 Auth 機制

| 模組 | 機制 | Endpoints |
|------|------|-----------|
| attendance v1 | Header X-Company-ID | 8 |
| attendance mock/approve | Header X-Company-ID | 2 |
| admin_location | Header X-Company-ID | 5 |
| audit | Header X-Company-ID | 5 |
| backup | Header X-Company-ID | 3 |
| notifications | Header X-Company-ID | 1 |
| tenants | JWT Bearer | 3 |
| customer_service | JWT Bearer | 3 |
| auth | Issues JWT | 1 |

Header auth modules: 5, total endpoints: 24
JWT auth modules: 2 (tenants, customer_service)

### 1.3 Endpoint 清單 (Header auth)

attendance/api.py:
  L70-73   POST /mock-create
  L84-90   POST /{id}/approve
  L109-115 POST /v1/punch-in
  L173-179 POST /v1/punch-out
  L266-270 GET  /v1/current-status
  L352-359 GET  /v1/history
  L410-416 POST /v1/break-out
  L493-499 POST /v1/break-in
  L544-549 GET  /v1/break-punches
  L607-613 PATCH /v1/punch/{id}/note

admin_location_api.py:
  L24-29   POST   / (create)
  L69-75   GET    / (list)
  L112-116 GET    /{location_id}
  L142-148 PUT    /{location_id}
  L190-194 DELETE /{location_id}

audit/api.py:
  L32-34   GET  /logs
  L104-106 GET  /export
  L192-195 GET  /retention
  L233-237 PUT  /retention
  L290-294 POST /purge

backup/api.py:
  L20-23  POST /export
  L53-57  POST /restore
  L98-99  GET  / (placeholder)

notifications/api.py:
  L35-40  GET /

tenants/api.py (JWT):
  L24-28  GET   /{company_id}/entitlements
  L49-54  PATCH /{company_id}/entitlements
  L82-87  POST  /{company_id}/entitlements/apply-plan

customer_service/api.py (JWT):
  L24-27  GET    /assigned-companies
  L45-49  POST   /assignments
  L71-75  DELETE /assignments

---

## 2. RBAC Enforcement

### 2.1 admin_location_api.py RBAC 狀態

檔案: backend/app/modules/attendance/admin_location_api.py

| 行號 | Endpoint | RBAC 狀態 |
|------|----------|-----------|
| L25  | POST create | TODO 驗證管理員權限 L47 - 無 RBAC |
| L143 | PUT update  | TODO 驗證管理員權限 L166 - 無 RBAC |
| L191 | DELETE      | TODO 驗證管理員權限 L207 - 無 RBAC |
| L70  | GET list    | 無 RBAC |
| L113 | GET single  | 無 RBAC |

結論: admin_location 5 個 endpoint 全部無 RBAC。

### 2.2 全專案 require_role / require_permission 搜尋

結果: 0 個匹配。
RBAC 僅透過 get_current_actor + scope 邏輯實作，且僅存在於 tenants/customer_service。

---

## 3. Feature Gate Status

基礎設施:
  feature_service.py L86: get_feature_service() 存在
  feature_gate_demo.py L27,65,111: require_enabled() - 示範檔，非生產 endpoint

生產 endpoint 中 feature gate 呼叫數:
  attendance/api.py:     0
  audit/api.py:          0
  backup/api.py:         0
  admin_location_api.py: 0

結論: Feature Gate 基礎設施完整，但完全未套用至任何生產 API endpoint。

---

## 4. Location Policy Coverage

check_location_policy() 生產代碼唯一呼叫位置:
  attendance/api.py L445-448 (break_out endpoint)

| 打卡動作  | Endpoint           | Location Policy | 行號     |
|-----------|--------------------|-----------------|----------|
| punch_in  | POST /v1/punch-in  | 無              | L109     |
| punch_out | POST /v1/punch-out | 無              | L173     |
| break_in  | POST /v1/break-in  | 無              | L493     |
| break_out | POST /v1/break-out | 有（條件式）    | L445-461 |

break_out 條件: 只在 request.location 有值時才執行。無 location 則跳過。

Location Policy Service: attendance/location_policy_service.py
  L39:  get_active_allowed_locations()
  L53:  check_location_policy()
  L79:  若無地點配置則允許所有位置
  L136: get_location_policy_service()
GPS: attendance/gps_utils.py calculate_distance() Haversine

---

## 5. Migration Chain

HEAD: 008_wp_11_13 - 無分叉，單一線性結構

Chain:
  None -> 004 -> 3532deda024c -> 005 -> 002 -> 003 -> 001b
       -> wp_11_04a_entitlements -> 006 -> 007_wp_11_10 -> 008_wp_11_13

| revision             | down_revision          | 主要操作                            | 狀態       |
|----------------------|------------------------|-------------------------------------|------------|
| 004                  | None                   | CREATE TABLE tenants                | ROOT       |
| 3532deda024c         | 004                    | CREATE users/roles/permissions/...  | ACTIVE     |
| 005                  | 3532deda024c           | CREATE TABLE notifications          | ACTIVE     |
| 002                  | 005                    | CREATE TABLE audit_logs             | ACTIVE     |
| 003                  | 002                    | CREATE TABLE audit_retention_...    | ACTIVE     |
| 001b                 | 003                    | CREATE TABLE attendance_...         | ACTIVE     |
| wp_11_04a_entitle... | 001b                   | CREATE TABLE company_entitlements   | ACTIVE     |
| 006                  | wp_11_04a_entitlements | ALTER attendance_sessions.status    | ACTIVE     |
| 007_wp_11_10         | 006                    | CREATE TABLE out_checkpoints zombie | ACTIVE     |
| 008_wp_11_13         | 007_wp_11_10           | CREATE TABLE allowed_locations +ALT | HEAD       |
| 001 deprecated       | --                     | 已廢棄                              | DEPRECATED |

runtime: NOT VERIFIED (未執行 alembic upgrade head)

---

## 6. Test Coverage Reality

### 6.1 Attendance Tests

| 測試檔 | functions | DB 類型 | Auth |
|--------|-----------|---------|------|
| test_api.py | 5 | SQLite/Mock | Header |
| test_policy_engine.py | 26 | 純 Python 無 DB | N/A |
| test_tenant_isolation.py | 9 | DummySession Mock | Header |
| test_business_invariant.py | 12 | PostgreSQL localhost:5432 | N/A |
| test_model_constraints.py | 20 | PostgreSQL localhost:5432 | N/A |
| test_migration.py | 9 | PostgreSQL alembic | N/A |
| test_location_policy.py | 8 | db_session fixture | N/A |
| test_break_out_enforcement.py | 8 | PostgreSQL test_session | Header |
| test_phase4.py | 6 | SQLite file | Header |
| test_out_checkpoint.py | 7 | 不明 | Header |
| test_tenant_validation.py | 4 | SQLite memory | N/A |
| test_regression.py | 1 | PostgreSQL 理論 | Header |

### 6.2 其他模組 Tests

| 模組 | functions | DB 類型 |
|------|-----------|--------|
| audit | 10 | SQLite memory |
| backup | 10 | SQLite memory |
| notifications | 4 | SQLite memory |
| tenants | 38 | override_get_db |
| core | 22 | PostgreSQL fixture |
| customer_service | 0 | -- |

### 6.3 Regression Test 現況

test_regression.py:
  Test 1-7: 不存在
  Test 8: test_8_cross_midnight_work_attribution L51 - 骨架存在，Header auth

### 6.4 Tenant Isolation 測試

test_tenant_isolation.py:
  L20: class DummySession - Mock，非真實 DB
  L91: db = DummySession() - 非 PostgreSQL
全部 9 個 test function 使用 DummySession。

---

## 7. Frontend Reality

Router: frontend/src/router/index.js
  /      -> Home.vue  (requiresAuth: true)
  /login -> Login.vue (requiresAuth: false)

有效路由: 2 個。無 Admin、無 Reporting、無 Leave/Approval 路由。

功能狀況:
  Login / Home / Auth store: VERIFIED EXISTS
  Attendance store / useLocation: VERIFIED EXISTS
  break-out GPS / 403 處理: VERIFIED EXISTS
  punch note dialog: VERIFIED EXISTS
  Google Maps break-punch link: VERIFIED EXISTS
  Admin UI: NOT EXISTS
  Admin Location 管理頁面: NOT EXISTS
  Reporting UI: NOT EXISTS
  Leave/Approval UI: NOT EXISTS

---

## 8. P0 / P1 Risk Matrix

P0 立即影響安全性:

| ID | 描述 | 檔案 行號 |
|----|------|----------|
| P0-1 | attendance endpoint 全部 Header auth | attendance/api.py L72,88,112,176,268,357,413,496,547,611 |
| P0-2 | backup export/restore Header auth | backup/api.py L22, L56 |
| P0-3 | admin_location 寫入端點無 RBAC | admin_location_api.py L47, L166, L207 |
| P0-4 | audit 5 endpoint 全部 Header auth | audit/api.py L34,106,195,237,294 |

P1 功能正確性:

| ID | 描述 | 檔案 行號 |
|----|------|----------|
| P1-1 | Feature Gate 未套用至任何生產 endpoint | feature_gate_demo.py L27,65,111 |
| P1-2 | Location Policy 只在 break-out 有效 | attendance/api.py L445 |
| P1-3 | 回歸測試 7/8 不存在 | test_regression.py L51 |
| P1-4 | tenant_isolation 測試用 DummySession | test_tenant_isolation.py L20,91 |
| P1-5 | audit/backup/notifications 用 SQLite | 各 test_*.py |
| P1-6 | customer_service 無任何測試 | customer_service/ |

---

## 9. Verified vs Not Verified

VERIFIED CODE_CONFIRMED:

| V-01 | attendance/admin_location/audit/backup/notifications 使用 Header auth | tenant_context.py L23 |
| V-02 | backup 使用 Header auth 非 JWT | backup/api.py L12, L22 |
| V-03 | admin_location 5 endpoint 無 RBAC | admin_location_api.py L47,166,207 |
| V-04 | Feature Gate 只在 feature_gate_demo.py | feature_gate_demo.py L27,65,111 |
| V-05 | Location Policy 只在 break_out | attendance/api.py L445 |
| V-06 | punch_in/punch_out/break_in 無 location policy | attendance/api.py L109,173,493 |
| V-07 | Migration HEAD = 008_wp_11_13 單一線性 chain | alembic/versions/ |
| V-08 | test_regression.py 只有 Test 8 骨架 | test_regression.py L51 |
| V-09 | test_tenant_isolation.py 用 DummySession | test_tenant_isolation.py L20, L91 |
| V-10 | audit/backup/notifications 測試用 SQLite | 各 test_*.py |
| V-11 | customer_service 無任何測試 | 目錄掃描 |
| V-12 | Frontend 只有 2 個路由 | router/index.js |
| V-13 | tenants/customer_service 使用 JWT | tenants/api.py L27 |
| V-14 | test_business_invariant + test_model_constraints 硬碼 PG URL | 各檔 L26-27 |

NOT VERIFIED 需 runtime 執行:

| NV-01 | alembic upgrade head 實際執行結果 | 未執行 migration |
| NV-02 | PostgreSQL localhost:5432 是否可連線 | 未嘗試連線 |
| NV-03 | test_business_invariant + test_model_constraints 實際通過率 | 需真實 DB |
| NV-04 | pytest 全套執行結果 | 未執行 |
| NV-05 | JWT login 到 attendance API 完整流程 | 未執行 |
| NV-06 | GPS 到 break-out 端到端 | 未執行 |
| NV-07 | Tenant Isolation 在真實 DB 查詢層 | 測試用 Mock |

---

## 10. Recommended Next Action

WP-C1-01: PostgreSQL 環境建立 + Migration 驗證

理由:
1. test_business_invariant.py 和 test_model_constraints.py 硬碼 postgresql://attendance_user:attendance_pass@localhost:5432/attendance_test (V-14)
2. alembic upgrade head runtime 未確認 (NV-01)
3. 一旦 DB 環境確認，可立即執行現有測試取得實際通過率
4. 不修改任何程式碼，零風險

本文件基於 2026-03-11 code scan。所有 VERIFIED 結論有具體 grep/read 證據。
NOT VERIFIED 項目不可被視為已完成或已通過。
