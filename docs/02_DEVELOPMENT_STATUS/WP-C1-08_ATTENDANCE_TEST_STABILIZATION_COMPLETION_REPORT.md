# WP-C1-08 Attendance Test Stabilization — COMPLETION REPORT

**票號：** WP-C1-08 Phase B  
**完成日期：** 2026-03-17  
**執行者：** AI session（Cursor Agent）  
**前置條件：** WP-C1-07 COMPLETE ✅  
**本報告性質：** 正式結案報告，依 Pre-Audit（Phase A）結論收尾

---

## 1. Objective（本票目標）

對 WP-C1-07 完成後遺留的 attendance 測試層不完整遷移進行修復，使 4 個已識別可修的測試檔案通過。
本票**不修改任何 production code**（api.py / service.py / repo.py / models.py 均未觸碰），
所有修改嚴格限定於測試層。

---

## 2. Scope（範圍邊界）

### 2.1 本票範圍內（IN SCOPE）

- 修復 4 個測試檔案中的測試層問題（hdr() 殘留、feature gate mock 缺失）
- 測試層修正屬於 WP-C1-07 遺留的不完整遷移，本票收尾
- SES-07 角色設定問題修正（test 層 role_id 從 admin 改為 employee）

### 2.2 本票範圍外（OUT OF SCOPE）

- production code 修改（嚴格禁止）
- 處理 pre-existing 失敗（WP-C1-04 已分類記錄的問題）
- 進入 Phase C 或新增修復任務
- test_api.py、test_out_checkpoint.py、test_migration.py、test_business_invariant.py 等 pre-existing 問題

---

## 3. Phase A Baseline（基線數據）

**執行指令：**

```
TEST_DATABASE_URL=postgresql+psycopg2://postgres:***@127.0.0.1:5432/attendance_test_db \
  pytest app/modules/attendance/tests/ -v
```

**基線結果：**

| 指標 | 數值 |
|------|------|
| Total collected | 179 |
| PASS | 85 |
| FAIL | 85 |
| ERROR | 9 |

**穩定 PASS 核心測試群（Phase A 已確認）：**

| 測試檔 | PASS 數 | 覆蓋功能 |
|--------|---------|----------|
| test_feature_gate.py | 6/6 | attendance.core feature gate |
| test_model_constraints.py | 20/20 | DB model constraints |
| test_policy_engine.py | 28/28 | Policy engine 計算邏輯 |
| test_router_v1_jwt_migration.py | 12/12 | JWT migration 驗證 |
| test_tenant_isolation_wp_c1_05.py | 9/9 | WP-C1-05 tenant isolation |

---

## 4. Phase B Files Changed（修復的檔案）

本票 Phase B 修改的 4 個測試檔案：

### 4.1 test_reporting_sessions.py

**問題類型：** WP-C1-07 遷移不完整（hdr() 殘留 + user_a.id.id typo）  
**修正內容：**
- 移除所有 `hdr()` 函數呼叫（`NameError: name 'hdr' is not defined`）
- 改用 `override_actor_dependency` + `make_actor_company` 模式
- 修正 `user_a.id.id` typo（多一層 `.id`）
- 補齊 `_require_attendance_feature` mock patch

**修正結果：** 16/16 PASS ✅

### 4.2 test_reporting_user_summary.py

**問題類型：** WP-C1-07 遷移不完整（hdr() 殘留）  
**修正內容：**
- 移除所有 `hdr()` 函數呼叫
- 改用 `override_actor_dependency` + `make_actor_company` 模式
- 補齊 `_require_attendance_feature` mock patch

**修正結果：** 13/13 PASS ✅

### 4.3 test_reporting_company_summary.py

**問題類型：** WP-C1-07 遷移不完整（hdr() 殘留）  
**修正內容：**
- 移除所有 `hdr()` 函數呼叫
- 改用 `override_actor_dependency` + `make_actor_company` 模式
- 補齊 `_require_attendance_feature` mock patch

**修正結果：** 14/14 PASS ✅

### 4.4 test_break_out_enforcement.py

**問題類型：** feature gate 未 mock + unittest.mock.patch import 缺失  
**修正內容：**
- 補齊 `unittest.mock.patch` import
- 補齊 `_require_attendance_feature` mock patch（參考 test_router_v1_jwt_migration.py 的 mock_gate 寫法）

**修正結果：** 6/6 PASS ✅

---

## 5. Phase B Test Results（修復驗證結果）

### 5.1 修復的 4 個測試檔案

| 測試檔 | 修復前 | 修復後 |
|--------|--------|--------|
| test_reporting_sessions.py | 0/16 FAIL | **16/16 PASS** ✅ |
| test_reporting_user_summary.py | 0/13 FAIL | **13/13 PASS** ✅ |
| test_reporting_company_summary.py | 0/14 FAIL | **14/14 PASS** ✅ |
| test_break_out_enforcement.py | 0/6 FAIL | **6/6 PASS** ✅ |
| **合計** | **0/49** | **49/49 PASS** ✅ |

### 5.2 持續穩定的測試群（Phase B 不變）

| 測試檔 | 狀態 |
|--------|------|
| test_feature_gate.py | 6/6 PASS ✅ |
| test_router_v1_jwt_migration.py | 12/12 PASS ✅ |
| test_tenant_isolation_wp_c1_05.py | 9/9 PASS ✅ |

### 5.3 整體 PASS 提升

| 指標 | Phase A | Phase B（完成後） |
|------|---------|-------------------|
| PASS | 85 | **134** |
| FAIL | 85 | 36 |
| ERROR | 9 | 9（不變） |
| Total | 179 | 179（不變） |

---

## 6. Boundary Note — SES-07 角色設定修正

**問題描述：**  
SES-07 的原始測試因角色設定錯誤（預設 `role_id="admin"`）而無法正確驗證 employee 權限限制。

**修正方式：**  
在測試層將 `role_id` 修正為 `"employee"`。

**定性：**  
此修正屬於**測試設計修正**，不屬於 production code 變更。Production code 的員工權限邏輯本身正確；
測試未能正確反映員工角色的驗證場景，已在本票測試層修正。

---

## 7. Remaining Issues Classification（剩餘問題定性）

以下問題**明確標注為 pre-existing**，來源為 WP-C1-04 已記錄範圍，
**不阻塞 WP-C1-08 收尾結論**：

| 類型 | 影響測試 | 失敗數 | 來源 / 分類 |
|------|----------|--------|-------------|
| 舊 router header auth（/api/attendance/） | test_api.py, test_tenant_isolation.py::TestTenantIsolation | 11 FAIL | PRE-EXISTING（WP-C1-04）|
| OUT Checkpoint API endpoint 不存在 | test_out_checkpoint.py | 7 FAIL | PRE-EXISTING（WP-C1-09 遺留）|
| test_migration.py 硬碼舊帳號 | test_migration.py | 9 FAIL | PRE-EXISTING（環境問題，WP-C1-04）|
| business_invariant repo 介面不符 | test_business_invariant.py | 5 FAIL | PRE-EXISTING（WP-C1-04）|
| location_policy fixture 不符 | test_location_policy.py | 6 ERROR + 1 FAIL | PRE-EXISTING（WP-C1-04）|
| tenant_validation 舊 repo 介面 | test_tenant_validation.py | 2 FAIL | PRE-EXISTING（WP-C1-04）|
| cross_midnight punch_time 被 API 忽略 | test_regression.py | 1 FAIL | PRE-EXISTING（WP-C1-04）|
| test_phase4 空檔案依賴 | test_tenant_isolation.py::TestCrossCompanyIsolation | 3 ERROR | PRE-EXISTING（WP-C1-04）|

**Pre-existing 合計：36 FAIL + 9 ERROR**（與 Phase A Pre-Audit 預測完全一致）

---

## 8. Final Closure Recommendation（最終結案建議）

### 8.1 本票結論

**WP-C1-08 已完成本票範圍內的測試穩定化修復。**

- Phase A（Pre-Audit）：識別 4 個本票可修測試檔，確認 85 PASS 基線，分類 36+9 pre-existing 問題
- Phase B（修復）：修復 4 個測試檔，新增 49 個 PASS，總 PASS 從 85 提升至 134
- Pre-existing 問題：全部保留、已分類，不阻塞本票收尾

### 8.2 狀態宣告

**WP-C1-08 狀態：COMPLETE**

### 8.3 不進入 Phase C

本票不進入 Phase C，不擴票修復剩餘 pre-existing 問題。  
下一步交由 roadmap / NEXT_WP_TICKET.md 控制。

### 8.4 交接資訊

剩餘的 36 FAIL + 9 ERROR 已全部分類，相關問題已記錄於：
- `docs/02_DEVELOPMENT_STATUS/WP-C1-08_ATTENDANCE_TEST_STABILIZATION_PRE_AUDIT.md` — 完整分類表（Section 10）
- `docs/02_DEVELOPMENT_STATUS/WP-C1-04_POSTGRESQL_REGRESSION_REPORT.md` — PostgreSQL 回歸記錄

---

## 9. Production Code Change Confirmation

**本票是否修改任何 production code：NO**

本票嚴格限定於測試層修復，以下檔案均未觸碰：

| 檔案 | 狀態 |
|------|------|
| attendance/api.py | 未修改 ✅ |
| attendance/service.py | 未修改 ✅ |
| attendance/repo.py | 未修改 ✅ |
| attendance/models.py | 未修改 ✅ |
| attendance/policy_engine.py | 未修改 ✅ |
| attendance/schemas.py | 未修改 ✅ |

---

*本報告由 AI 依據 