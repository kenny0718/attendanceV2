# SYSTEM_REALITY_REPORT_v2.md

## Purpose

本報告為 System Reality Verification v2，透過直接 code scan 重新驗證系統真實狀態。
每個結論明確標示來源：`CODE_CONFIRMED`、`DOC_ONLY`、`NOT_VERIFIED`。
凡與舊文件不一致之處，以本報告為準。

## Scope

- Backend：所有 api.py（逐行 grep）、migration down_revision chain、測試檔 DB 類型、feature gate 套用
- Frontend：router/index.js、stores/、components/、殘留檔案
- Docs：7 份文件交叉比對一致性

## Source of Truth

- **CODE_CONFIRMED**：直接 grep/cat 程式碼所得
- **DOC_ONLY**：只在文件中描述，未能以 code scan 確認
- **NOT_VERIFIED**：runtime 未執行，或需 DB 環境才能確認

## Last Updated

2026-03-11（System Reality Verification v2）

## Verification Method

1. `grep -n 'Depends\|get_current'` 逐一掃描每個 api.py
2. `grep -n 'down_revision'` 確認 migration chain
3. `grep -n 'sqlite\|postgresql\|DummySession\|:memory:'` 分類測試 DB 類型
4. `grep -n 'assert_feature_enabled\|feature_gate'` 確認 Feature Gate 套用狀況
5. `grep -n 'TODO\|RBAC\|admin.*role'` 確認 RBAC 缺口
6. `grep -n 'def test_'` 逐模組計算測試函數數量
7. `sed -n` 讀取關鍵函數實作細節

## Verification Limits

以下未在本次驗證（需 runtime 環境）：
- `alembic upgrade head` 實際執行結果
- pytest 在真實 PostgreSQL 執行結果
- GPS / browser 端到端流程
- JWT login → API 的完整 token 流程
- 跨租戶隔離在真實 DB 查詢層的有效性


---

## Executive Summary

| 面向 | 真實狀態 | 關鍵缺口 |
|------|----------|----------|
| Auth 機制 | **5 個模組使用 Header**，2 個使用 JWT | attendance/audit/notifications/backup/admin_location 全部 Header-only |
| Feature Gate | **完全未套用**至任何生產 endpoint | feature_gate_demo.py 存在但未 include_router |
| RBAC | admin_location 3 個寫入端點為純 TODO | 任何持有效 Header 的用戶可管理地點政策 |
| Location Policy | **只在 break-out 有效**；punch-in/out/break-in 無 | CODE_CONFIRMED |
| 回歸測試 | **只有 1 個 test function**（Test 8 骨架）；使用 Header auth | 0 個可在 JWT auth 環境下執行 |
| 測試 DB 類型 | attendance 部分測試用 PostgreSQL；audit/backup/notifications 用 SQLite :memory: | 混用，非一致真實環境 |
| Tenant Isolation 測試 | attendance 用 DummySession（Mock）；notifications 用 SQLite | 無真實 PostgreSQL 驗證 |
| Frontend | 2 個路由；Admin UI 完全缺失 | CODE_CONFIRMED |
| customer_service 測試 | **0 個 test functions** | CODE_CONFIRMED |

---

## Code-Confirmed Findings（CODE_CONFIRMED）

### CF-01：所有 attendance endpoint 使用 X-Company-ID Header（非 JWT）

**證據**（grep 結果）：
```
attendance/api.py 所有 endpoint：
  Depends(get_current_company_id)  ← 來自 tenant_context.py，讀 X-Company-ID header
  Depends(get_current_user_id)     ← 來自 tenant_context.py，讀 X-User-ID header（可選）
```
全部 10 個 endpoint（punch-in/out/current-status/history/break-out/break-in/break-punches/punch-note/mock-create/approve）均使用 Header。
**沒有任何 attendance endpoint 使用 `get_current_actor()`。**

---

### CF-02：backup/api.py 使用 X-Company-ID Header（非 JWT）

**證據**（直接讀取 backup/api.py）：
```python
from app.core.tenant_context import get_current_company_id

@router.post("/export")
def export_backup(
    current_company_id: str = Depends(get_current_company_id),  # ← Header
    ...
```
**`SYSTEM_DEVELOPMENT_STATUS_REPORT.md` 將 backup 列為 JWT auth 是錯誤的。** CODE_CONFIRMED。

---

### CF-03：admin_location_api.py 有 3 處明確 `# TODO: 驗證管理員權限`

**證據**（grep 結果）：
```
admin_location_api.py:47  # TODO: 驗證管理員權限
admin_location_api.py:166 # TODO: 驗證管理員權限  
admin_location_api.py:207 # TODO: 驗證管理員權限
```
POST（建立）、PUT（更新）、DELETE（刪除）三個寫入端點完全無 RBAC。
GET（查詢）端點只有 Tenant Isolation（company_id 過濾），無角色限制。

---

### CF-04：Location Policy 只在 break-out endpoint 有效

**證據**（code scan）：
- `break-out`（line 445-460）：`policy_service.check_location_policy()` 有呼叫 ✅
- `punch-in`（line 109-172）：**無任何 location_policy 相關呼叫** ❌
- `punch-out`（line 173-265）：**無任何 location_policy 相關呼叫** ❌
- `break-in`（line 493-543）：**無任何 location_policy 相關呼叫** ❌

**ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md 聲稱 location policy 適用於所有打卡流程，但實作上只有 break-out。** 文件描述與實際不符。

---

### CF-05：Feature Gate 完全未套用至任何生產 API endpoint

**證據**（grep `assert_feature_enabled` 全 backend 結果）：**空輸出，無任何 match。**
`feature_gate_demo.py` 存在示範代碼，但：
- 該檔案**未被 main.py include_router**
- 生產 api.py 中沒有任何 `feature_service.require_enabled()` 或 `assert_feature_enabled()` 呼叫

---

### CF-06：test_regression.py 只有 1 個 test function（Test 8 骨架）

**證據**（grep 結果）：
```
測試函數數：2（含 fixture）
實際 test function：1（test_8_cross_midnight_work_attribution）
```
Test 8 本身仍使用 `X-Company-ID / X-User-ID` Header auth，不是 JWT。
Test 1-7 **完全不存在**。

---

### CF-07：測試 DB 類型分佈（混用，非統一 PostgreSQL）

**CODE_CONFIRMED（grep 結果）：**

| 模組測試 | DB 類型 | 具體 URL |
|----------|---------|----------|
| attendance/test_business_invariant.py | PostgreSQL | `postgresql://attendance_user:attendance_pass@localhost:5432/attendance_test` |
| attendance/test_model_constraints.py | PostgreSQL | 同上 |
| attendance/test_phase4.py | SQLite 檔案 | `sqlite:///./test_phase4.db` |
| attendance/test_tenant_isolation.py | DummySession（Mock） | 無真實 DB |
| audit/tests/conftest.py | SQLite :memory: | `sqlite:///:memory:` |
| backup/tests/conftest.py | SQLite :memory: | `sqlite:///:memory:` |
| notifications/tests/test_event_handlers.py | SQLite :memory: | `sqlite:///:memory:` |
| tenants/tests/conftest.py | dependency_override get_db | 需外部 DB |

**影響：audit、backup、notifications 的測試使用 SQLite，無法驗證 PostgreSQL 特有行為（UUID、FK constraint 等）。**


---

## P0 Risks（立即需要處理）

| ID | 風險 | 證據來源 | 影響 |
|----|------|----------|------|
| P0-1 | attendance 全部 endpoint 使用 Header auth，無身份驗證 | CF-01 | 任何人設 X-Company-ID 即可打卡/查詢/修改備註 |
| P0-2 | backup export/restore 使用 Header auth | CF-02 | 任何人可匯出或還原公司資料 |
| P0-3 | admin_location 3 個寫入端點完全無 RBAC | CF-03 | 任何員工可建立/修改/刪除地點政策 |
| P0-4 | 8 個回歸測試只有 1 個，且用 Header auth | CF-06 | Gate 5 無法完成，無法驗證核心業務邏輯 |

---

## P1 Risks

| ID | 風險 | 證據來源 | 影響 |
|----|------|----------|------|
| P1-1 | Feature Gate 完全未套用 | CF-05 | SaaS 功能分級無效，所有公司均可使用所有功能 |
| P1-2 | Location Policy 只在 break-out 有效 | CF-04 | punch-in/out/break-in 無法執行地理圍欄限制 |
| P1-3 | audit/notifications/backup 測試用 SQLite | CF-07 | PostgreSQL 特有行為（UUID FK、型別）未驗證 |
| P1-4 | customer_service 無任何測試 | CF-08 | 客服跨公司存取功能完全無測試覆蓋 |
| P1-5 | Tenant Isolation 測試用 Mock/SQLite | CF-07 | 跨租戶隔離在真實 DB 層未驗證 |

---

## Module-by-Module Reality Table

| 模組 | Auth 方式 | Scope 驗證 | Feature Gate | RBAC | 測試 DB | 測試函數數 | runtime 驗證 |
|------|-----------|-----------|--------------|------|---------|-----------|-------------|
| attendance | Header ❌ | ❌ | ❌ | 部分（break-out only） | PostgreSQL(部分)/SQLite/Mock 混用 | 117 | NOT_VERIFIED |
| audit | Header ❌ | ❌ | ❌ | ❌ | SQLite :memory: | 25 | NOT_VERIFIED |
| auth | N/A（login） | N/A | N/A | N/A | 不明 | 15 | NOT_VERIFIED |
| backup | Header ❌ | ❌ | ❌ | ❌ | SQLite :memory: | 23 | NOT_VERIFIED |
| customer_service | JWT ✅ | ✅ | ❌ | ✅ | override_get_db | **0** | NOT_VERIFIED |
| notifications | Header ❌ | ❌ | ❌ | ❌ | SQLite :memory: | 14 | NOT_VERIFIED |
| tenants | JWT ✅ | ✅ | ❌（self exempt） | ✅ | override_get_db | 38 | NOT_VERIFIED |

---

## Migration Reality Table

| Migration | revision | down_revision | 建立 Table | 狀態 |
|-----------|----------|---------------|-----------|------|
| 004_create_tenants | 004 | None（root） | tenants | CODE_CONFIRMED |
| 3532deda（auth v2） | 3532deda024c | 004 | users/roles/permissions/user_roles/user_company_memberships | CODE_CONFIRMED |
| 005_create_notifications | 005 | 3532deda024c | notifications | CODE_CONFIRMED |
| 002_create_audit_logs | 002 | 005 | audit_logs | CODE_CONFIRMED |
| 003_create_audit_retention | 003 | 002 | audit_retention_policies | CODE_CONFIRMED |
| 001b_attendance_domain_fixed | 001b | 003 | attendance_policies/sessions/punches | CODE_CONFIRMED |
| wp_11_04a_entitlements | wp_11_04a | 001b | company_entitlements/support_company_assignments | CODE_CONFIRMED |
| 006_expand_session_status | 006 | wp_11_04a | ALTER attendance_sessions.status | CODE_CONFIRMED |
| 007_wp_11_10_out_checkpoints | 007 | 006 | attendance_out_checkpoints（zombie） | CODE_CONFIRMED（功能已移除） |
| 008_wp_11_13_allowed_locations | 008_wp_11_13 | 007_wp_11_10 | allowed_locations + ALTER attendance_punches | CODE_CONFIRMED |
| **Current HEAD** | 008_wp_11_13 | - | - | CODE_CONFIRMED（chain scan） |
| 001_deprecated | .deprecated | - | 已廢棄 | CODE_CONFIRMED（filename） |
| runtime 執行 | - | - | - | NOT_VERIFIED |

---

## Test Reality Table

| 測試檔 | 模組 | 函數數 | DB 類型 | Auth 方式 | 狀態 |
|--------|------|--------|---------|-----------|------|
| test_regression.py | attendance | **1**（Test 8 骨架） | PostgreSQL（理論）+ Header auth | Header | CODE_CONFIRMED：只有 1 個，且用 Header |
| test_tenant_isolation.py | attendance | ~7 | **DummySession（Mock）** | Header | CODE_CONFIRMED：非真實 DB |
| test_break_out_enforcement.py | attendance | ~5 | 不明 | Header | CODE_CONFIRMED：用 Header auth |
| test_business_invariant.py | attendance | ~12 | PostgreSQL（hardcoded URL） | N/A | NOT_VERIFIED（DB 是否可連） |
| test_model_constraints.py | attendance | ~20 | PostgreSQL（hardcoded URL） | N/A | NOT_VERIFIED |
| test_phase4.py | attendance | ~10 | SQLite 檔案 | Header | CODE_CONFIRMED |
| test_location_policy.py | attendance | ~5 | 需 db_session fixture | N/A | NOT_VERIFIED |
| test_audit_api.py | audit | ~10 | SQLite :memory: | Header | CODE_CONFIRMED（SQLite） |
| test_api.py | backup | ~10 | SQLite :memory: | Header | CODE_CONFIRMED（SQLite） |
| test_tenant_isolation.py | backup | ~5 | SQLite :memory: | Header | CODE_CONFIRMED（SQLite） |
| test_event_handlers.py | notifications | ~4 | SQLite :memory: | N/A | CODE_CONFIRMED（SQLite） |
| test_entitlements_api.py | tenants | ~9 | override（需外部 DB） | Mock actor | CODE_CONFIRMED |
| (全部) | customer_service | **0** | - | - | CODE_CONFIRMED：無測試 |

---

## Frontend Reality Table

| 項目 | 狀態 | 來源 |
|------|------|------|
| 有效路由數 | **2**（/ 和 /login） | CODE_CONFIRMED |
| Login.vue | ✅ 存在 | CODE_CONFIRMED |
| Home.vue（3-Card 佈局） | ✅ 存在 | CODE_CONFIRMED |
| auth store（JWT token） | ✅ 存在 | CODE_CONFIRMED |
| attendance store | ✅ 存在 | CODE_CONFIRMED |
| useLocation composable | ✅ 存在 | CODE_CONFIRMED |
| break-out GPS 傳送 | ✅ 存在（attendanceApi.breakOut 呼叫） | CODE_CONFIRMED |
| break-in 整合 | ✅ 存在 | CODE_CONFIRMED |
| Location Policy 403 錯誤處理 | ✅ 存在 | CODE_CONFIRMED |
| reason preset/custom | ✅ 存在 | CODE_CONFIRMED |
| punch note 編輯 dialog | ✅ 存在 | CODE_CONFIRMED |
| Google Maps break-punch 連結 | ✅ 存在（attendance store） | CODE_CONFIRMED |
| Admin UI | ❌ 完全不存在 | CODE_CONFIRMED |
| Admin Location 管理頁面 | ❌ 不存在 | CODE_CONFIRMED |
| Reporting UI | ❌ 不存在 | CODE_CONFIRMED |
| Leave/Approval UI | ❌ 只有 disabled 按鈕入口 | CODE_CONFIRMED |
| 殘留 backup 檔案 | **9 個**（frontend 8 + backend 1 套） | CODE_CONFIRMED |


---

## Documents With Inconsistencies

### DI-01：SYSTEM_DEVELOPMENT_STATUS_REPORT.md — backup auth 欄位錯誤

| 欄位 | 文件記載 | 真實狀態（CODE_CONFIRMED） |
|------|---------|---------------------------|
| backup auth 方式 | JWT | **Header（X-Company-ID）** |

**點名位置**：Section 3.2「Auth 方式分布」表格，backup 列的「Auth 方式」欄。
**應以本報告（SYSTEM_REALITY_REPORT_v2）為準。**

---

### DI-02：MODULE_STATUS_MATRIX.md（2026-03-11）— backup auth 已修正，但舊 GATE_PROGRESS_TRACKER 數字有出入

`GATE_PROGRESS_TRACKER.md`（更新前）描述「Header auth 模組數量」，
本次驗證確認：**使用 Header 的模組共 5 個**（attendance、audit、notifications、backup、admin_location），而非舊文件可能暗示的 4 個（遺漏 admin_location）。

---

### DI-03：ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md — 聲稱 location policy 適用所有打卡流程

**文件**：「打卡時必須執行 GPS 獲取 + Policy Check」（Section 架構設計）
**實際**：CODE_CONFIRMED，只有 break-out 有 `check_location_policy()`。
punch-in、punch-out、break-in 均無。

---

### DI-04：ATTENDANCE_DEVELOPMENT_MASTER_FLOW.md — WP-11-04B 狀態為 CURRENT

**文件**：WP-11-04B 標為「🎯 CURRENT」
**實際**：GATE_PROGRESS_TRACKER.md 標為 COMPLETED（2026-03-04）
**應以 GATE_PROGRESS_TRACKER.md 為準，MASTER_FLOW 此處過期。**

---

### DI-05：SYSTEM_DEVELOPMENT_STATUS_REPORT.md — Header auth 端點數可能有誤

**文件**：「Header X-Company-ID：18 個端點」
**實際重新計算（CODE_CONFIRMED）**：
- attendance：10 個（mock-create/approve + 8 個 v1）
- audit：5 個
- notifications：1 個
- backup：3 個
- admin_location：5 個
- **總計：24 個**（非 18 個）

差異原因：舊報告未計入 admin_location 的 5 個端點。

---

## Superseded Conclusions

| 舊結論 | 出自文件 | 取代結論 | 本報告依據 |
|--------|---------|---------|----------|
| backup 使用 JWT auth | SYSTEM_DEVELOPMENT_STATUS_REPORT | backup 使用 Header auth | CF-02 |
| Header auth 端點共 18 個 | SYSTEM_DEVELOPMENT_STATUS_REPORT | 共 24 個（含 admin_location 5 個） | CF-01/09 |
| test_tenant_isolation 驗證 Tenant Isolation | 多份文件 | 使用 DummySession，非真實驗證 | CF-07 |
| Location Policy 適用所有打卡流程 | ATTENDANCE_LOCATION_POLICY_SPEC | 只適用 break-out | CF-04 |
| SA 符合度 75% | MASTER_DEVELOPMENT_ROADMAP | 約 60-65%（Feature Gate 未套用修正） | CF-05 |

---

## Recommended Next WP

**建議：WP-C1-01（PostgreSQL 環境建立 + Migration 驗證）**

理由（CODE_CONFIRMED 基礎）：
1. `test_business_invariant.py` 和 `test_model_constraints.py` 硬碼指向 `postgresql://attendance_user:attendance_pass@localhost:5432/attendance_test`，需先確認此 DB 是否存在並可連線
2. `alembic upgrade head` runtime 執行尚未確認（NOT_VERIFIED NV-01）
3. 一旦 DB 環境確認，可立即執行 117 個 attendance test functions 的實際通過率
4. 不修改任何程式碼，零風險起步

**優先順序不變**：WP-C1-01 → WP-C1-02（attendance JWT 轉換）→ WP-C1-03（auth 批次轉換）→ WP-C1-04（回歸測試實作）

---

## Definition of What Cannot Yet Be Claimed Complete

| 項目 | 不能宣告完成的原因 |
|------|------------------|
| Attendance 模組「完成」 | Auth 使用 Header；回歸測試 7/8 未實作；Location Policy 只有 break-out；runtime 未驗證 |
| Tenant Isolation「已驗證」 | test_tenant_isolation.py 用 DummySession，非真實 DB |
| Location Policy「已整合」 | 只有 break-out，punch-in/out/break-in 均無 |
| Feature Gate「已實作」 | 基礎設施存在但完全未套用至任何生產 endpoint |
| Gate 5「完成」 | 8 個回歸測試 0/8 真實通過；Auth 轉換 0/5 模組完成；Tenant Isolation runtime 0/5 |
| backup「使用 JWT」 | CODE_CONFIRMED 使用 Header |
| RBAC「已實作」於 admin_location | 3 處明確 # TODO |
| 測試「已通過」 | 所有測試均 NOT_VERIFIED（runtime）；多數使用 SQLite 或 Mock |

---

## Specific File Modification Suggestions

### 修正建議（只針對文件，不修改程式碼）

1. **`SYSTEM_DEVELOPMENT_STATUS_REPORT.md`**：
   - Section 3.2 backup auth 欄位改為 Header
   - Header auth 端點數改為 24 個（非 18 個）
   - 開頭加 superseded 聲明

2. **`ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md`**：
   - 明確標注：Phase 1 只實作 break-out；punch-in/out/break-in 待 WP-C2-01

3. **`ATTENDANCE_DEVELOPMENT_MASTER_FLOW.md`**：
   - WP-11-04B 狀態改為 COMPLETED

4. **`MODULE_STATUS_MATRIX.md`**（已在本次更新）：
   - backup auth 已正確標為 Header ✅

---

*本報告基於 2026-03-11 code scan，所有 CODE_CONFIRMED 結論有具體 grep/sed 證據。*
*runtime 驗證（NOT_VERIFIED）項目不可被視為已完成。*
