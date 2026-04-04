# WP-C1-08 Phase A — Attendance 測試盤點 Pre-Audit 報告

**票號：** WP-C1-08 Phase A  
**執行日期：** 2026-03-17  
**執行者：** AI（Cursor Agent）  
**前置條件：** WP-C1-07 COMPLETE ✅  
**本階段性質：** 只做盤點，不修改任何 code / test / docs

---

## 1. 執行環境

| 項目 | 值 |
|------|----|
| 資料庫 | PostgreSQL attendance_test_db（127.0.0.1:5432）|
| Python | 3.11.2 |
| pytest | 9.0.2 |
| Migration HEAD | 009_wp_11_08（21 tables）|
| 執行指令 | TEST_DATABASE_URL=postgresql+psycopg2://postgres:***@127.0.0.1:5432/attendance_test_db pytest app/modules/attendance/tests/ -v |

---

## 2. Attendance 測試檔案清單

| # | 檔案 | 測試數 | 備注 |
|---|------|--------|------|
| 1 | test_api.py | 5 | 舊版 /api/attendance/mock-create endpoint 測試 |
| 2 | test_break_out_enforcement.py | 6 | Break-out location policy enforcement |
| 3 | test_business_invariant.py | 12 | One open session invariant + lifecycle |
| 4 | test_feature_gate.py | 6 | Feature Gate（attendance.core）|
| 5 | test_location_policy.py | 8 | Location policy service 邏輯 |
| 6 | test_migration.py | 9 | Alembic migration upgrade/downgrade |
| 7 | test_model_constraints.py | 20 | DB 層 model constraints |
| 8 | test_out_checkpoint.py | 7 | OUT Checkpoint API |
| 9 | test_phase4.py | 0 | 空檔案（無測試）|
| 10 | test_policy_engine.py | 28 | Policy engine 計算邏輯 |
| 11 | test_punch_api.py | 0 | 空檔案（無測試）|
| 12 | test_regression.py | 1 | Cross-midnight regression |
| 13 | test_reporting_company_summary.py | 14 | Reporting company-summary endpoint |
| 14 | test_reporting_sessions.py | 16 | Reporting sessions endpoint |
| 15 | test_reporting_user_summary.py | 13 | Reporting user-summary endpoint |
| 16 | test_router_v1_jwt_migration.py | 12 | JWT Migration 驗證（WP-C1-07 新增）|
| 17 | test_tenant_isolation.py | 9 | 舊版 tenant isolation（含 Phase2 cross-company）|
| 18 | test_tenant_isolation_wp_c1_05.py | 9 | WP-C1-05 新版 tenant isolation |
| 19 | test_tenant_validation.py | 4 | 舊版 AttendanceRepository tenant validation |

合計 collect：179 tests

---

## 3. pytest 實際結果（總覽）

```
總計：179 collected
結果：85 passed / 85 failed / 9 errors / 26 warnings
執行時間：84.60s
```

### 3.1 逐檔結果

| 測試檔 | PASS | FAIL | ERROR | 狀態 |
|--------|------|------|-------|------|
| test_feature_gate.py | 6 | 0 | 0 | ALL PASS |
| test_model_constraints.py | 20 | 0 | 0 | ALL PASS |
| test_policy_engine.py | 28 | 0 | 0 | ALL PASS |
| test_router_v1_jwt_migration.py | 12 | 0 | 0 | ALL PASS |
| test_tenant_isolation_wp_c1_05.py | 9 | 0 | 0 | ALL PASS |
| test_business_invariant.py | 7 | 5 | 0 | PARTIAL |
| test_location_policy.py | 2 | 1 | 6 | PARTIAL |
| test_tenant_validation.py | 2 | 2 | 0 | PARTIAL |
| test_regression.py | 0 | 1 | 0 | FAIL |
| test_api.py | 0 | 5 | 0 | ALL FAIL |
| test_break_out_enforcement.py | 0 | 6 | 0 | ALL FAIL |
| test_migration.py | 0 | 9 | 0 | ALL FAIL |
| test_out_checkpoint.py | 0 | 7 | 0 | ALL FAIL |
| test_reporting_company_summary.py | 0 | 14 | 0 | ALL FAIL |
| test_reporting_sessions.py | 0 | 16 | 0 | ALL FAIL |
| test_reporting_user_summary.py | 0 | 13 | 0 | ALL FAIL |
| test_tenant_isolation.py | 0 | 6 | 3 | ALL FAIL/ERR |
| test_phase4.py | — | — | — | 空檔案 |
| test_punch_api.py | — | — | — | 空檔案 |

---

## 4. Warnings 盤點

警告數量：26 個（每次執行固定出現）

| 警告分類 | 來源 | 數量 | 說明 |
|----------|------|------|------|
| PydanticDeprecatedSince20（class-based config）| attendance/schemas.py | 4 | PunchResponse / SessionResponse / OutCheckpointListItem / AllowedLocationResponse 使用舊版 class Config |
| PydanticDeprecatedSince20（@validator）| attendance/schemas.py | 1 | OutCheckpointCreateRequest.gps 使用舊版 @validator |
| PydanticDeprecatedSince20（class-based config）| leave/schemas.py | 5 | 多個 Leave schemas |
| PydanticDeprecatedSince20（@validator）| leave/schemas.py | 4 | 多個 Leave schema validators |
| DeprecationWarning（on_event）| app/main.py | 1 | FastAPI @app.on_event("startup") 已棄用 |
| DeprecationWarning（alembic path_separator）| alembic/config.py | 9 | alembic.ini 缺少 path_separator=os |

結論：所有 26 個 warnings 均為 Pydantic V1->V2 遷移、FastAPI lifespan deprecation 及 Alembic 設定問題。不影響功能，屬技術債。

---

## 5. 失敗根本原因分類（共 10 類型）

### 5.1 類型 A：舊版 Header-based auth（舊 router /api/attendance/）

影響：test_api.py（5 FAIL）、test_tenant_isolation.py::TestTenantIsolation（6 FAIL）

根本原因：舊 router mock-create / approve 使用 get_current_company_id（X-Company-ID header），
非 JWT Actor 模式，override_actor_dependency 無效。
實際失敗：assert 422 == 200（header missing）、assert 422 == 401

分類：PRE-EXISTING — WP-C1-07 明確將舊 router 排除在遷移範圍外。本票不修改。

---

### 5.2 類型 B：OUT Checkpoint API Endpoint 不存在

影響：test_out_checkpoint.py（7 FAIL）

根本原因：POST /api/v1/attendance/out-checkpoint endpoint 未建立。
WP-C1-09 只建 model/repo，未建 API endpoint。
測試使用 override_all_auth_dependencies，但 punch-in 仍返回 403（feature gate）。
實際失敗：assert 403 == 201

分類：PRE-EXISTING（WP-C1-09 遺留）。本票不修改。

---

### 5.3 類型 C：Reporting 三個測試檔 — hdr() 函數殘留（WP-C1-07 遷移不完整）

影響：test_reporting_sessions.py（16 FAIL）、test_reporting_user_summary.py（13 FAIL）、test_reporting_company_summary.py（14 FAIL）

根本原因：
- WP-C1-07 遷移時，部分測試改用 override_actor_dependency，但其他測試仍保留 headers=hdr(...) 舊式呼叫
- hdr() 函數已被刪除，但呼叫點未全部清理
- NameError: name 'hdr' is not defined
- test_reporting_sessions.py 中另有 user_a.id.id typo（多一層 .id）

分類：本票可修 — 測試層 WP-C1-07 遺留不完整遷移，修正方式明確。

---

### 5.4 類型 D：test_migration.py — 硬碼舊帳號

影響：test_migration.py（9 FAIL）

根本原因：硬碼 postgresql://attendance_user:attendance_pass@localhost:5432/attendance_test，
帳號不存在，DROP SCHEMA 無權限。
實際失敗：AssertionError: assert 'attendance_sessions' in []

分類：PRE-EXISTING（環境設定問題，WP-C1-04 已記錄）。本票不修改。

---

### 5.5 類型 E：test_break_out_enforcement.py — feature gate 未 mock

影響：test_break_out_enforcement.py（6 FAIL）

根本原因：測試呼叫 punch-in 返回 403，因為測試未 mock _require_attendance_feature，
feature gate 正常觸發，DB 中無 attendance.core feature 記錄。
使用 override_actor_dependency 但未 patch feature gate。
實際失敗：assert 403 == 201（punch-in 失敗）

分類：本票可修 — 測試層缺少 feature gate mock，修正方式明確（參考 test_router_v1_jwt_migration.py 的 mock_gate 寫法）。

---

### 5.6 類型 F：test_business_invariant.py — repo 介面不符

影響：test_business_invariant.py（5 FAIL）

根本原因：測試呼叫 AttendanceSessionRepository.close_session(company_id=...) 但
現行 repo 不接受 company_id 參數（介面已演化）。
實際失敗：TypeError: close_session() got an unexpected keyword argument 'company_id'

分類：PRE-EXISTING — repo 介面演化，測試未同步，本票不修改（避免觸碰 repo.py）。

---

### 5.7 類型 G：test_location_policy.py — fixture 不存在

影響：test_location_policy.py（6 ERROR + 1 FAIL）

根本原因：
- TestLocationPolicyService 使用 db_session fixture，但 attendance conftest 中無此 fixture（可用的是 db / test_session）
- fixture 'db_session' not found
- TestDistanceCalculation::test_haversine_distance FAIL（計算結果與預期不符）
- TestDistanceCalculation::test_same_location_zero_distance PASS（基本邏輯正常）

分類：PRE-EXISTING — fixture 名稱不符，haversine 計算問題，均為舊版遺留。本票不修改。

---

### 5.8 類型 H：test_tenant_validation.py — 舊版 AttendanceRepository 介面

影響：test_tenant_validation.py（2 FAIL）

根本原因：測試呼叫 AttendanceRepository.create_attendance_record() 舊簽名，
現行 repo 不再有此方法。使用 SQLite in-memory，與 PostgreSQL 環境不一致。

分類：PRE-EXISTING（WP-C1-04 已記錄）。本票不修改。

---

### 5.9 類型 I：test_regression.py::test_8_cross_midnight — punch_time 被 API 忽略

影響：test_regression.py（1 FAIL）

根本原因：API punch-in 使用 datetime.now() 覆蓋傳入的 punch_time。
測試傳入 2026-03-31 23:00:00，但 session.punch_in_time 為 2026-03-17（今日）。
實際失敗：assert datetime.date(2026, 3, 17) == datetime.date(2026, 3, 31)

分類：PRE-EXISTING（WP-C1-04、WP-C1-07 均記錄）。punch_time 忽略為 API 設計問題，需業務層決策。本票不修改。

---

### 5.10 類型 J：test_tenant_isolation.py::TestCrossCompanyIsolation — 依賴空檔 test_phase4

影響：test_tenant_isolation.py::TestCrossCompanyIsolation（3 ERROR）

根本原因：fixture setup_phase2_database 執行 from app.modules.attendance.tests.test_phase4 import engine, TestingSessionLocal，但 test_phase4.py 是空檔案，無法 import。

分類：PRE-EXISTING — test_phase4.py 為空檔案，此依賴永遠無法解決。本票不修改。


---

## 6. 問題彙總分類表

| 類型 | 影響測試檔 | 失敗數 | 分類 | Phase B 是否修改 |
|------|-----------|--------|------|------------------|
| A：舊 router header auth | test_api.py, test_tenant_isolation.py::TestTenantIsolation | 11 | PRE-EXISTING | 不修改 |
| B：OUT Checkpoint API 404 | test_out_checkpoint.py | 7 | PRE-EXISTING（WP-C1-09）| 不修改 |
| C：hdr() 函數殘留 | test_reporting_sessions.py, test_reporting_user_summary.py, test_reporting_company_summary.py | 43 | 本票可修 | 修改 |
| D：migration 舊帳號 | test_migration.py | 9 | PRE-EXISTING（環境）| 不修改 |
| E：break_out 未 mock feature gate | test_break_out_enforcement.py | 6 | 本票可修 | 修改 |
| F：business_invariant repo 介面不符 | test_business_invariant.py | 5 | PRE-EXISTING | 不修改 |
| G：location_policy fixture 不符 | test_location_policy.py | 6 ERROR + 1 FAIL | PRE-EXISTING | 不修改 |
| H：tenant_validation 舊 repo 介面 | test_tenant_validation.py | 2 | PRE-EXISTING | 不修改 |
| I：test_8 cross_midnight punch_time 被忽略 | test_regression.py | 1 | PRE-EXISTING | 不修改 |
| J：test_phase4 空檔案依賴 | test_tenant_isolation.py::TestCrossCompanyIsolation | 3 ERROR | PRE-EXISTING | 不修改 |

本票可修合計：49 個失敗（類型 C + E）
Pre-existing 保留合計：36 FAIL + 9 ERROR

---

## 7. 穩定 PASS 的測試（85 passed）

下列測試在 WP-C1-07 完成後已穩定通過，確認核心功能正常：

| 測試檔 | PASS 數 | 覆蓋功能 |
|--------|---------|----------|
| test_feature_gate.py | 6/6 | attendance.core feature gate 完整驗證 |
| test_model_constraints.py | 20/20 | DB model constraints 完整驗證 |
| test_policy_engine.py | 28/28 | Policy engine 所有計算邏輯 |
| test_router_v1_jwt_migration.py | 12/12 | JWT migration 所有 11 endpoints 驗證 |
| test_tenant_isolation_wp_c1_05.py | 9/9 | WP-C1-05 tenant isolation 完整驗證 |
| test_business_invariant.py | 7/12 | DB-level invariant 通過；repo 介面失敗為 pre-existing |
| test_location_policy.py | 2/8 | TestDistanceCalculation 基本測試通過 |
| test_tenant_validation.py | 2/4 | SQLite 基本驗證通過 |

核心功能穩定性確認：
- JWT Actor flow: STABLE
- Feature Gate: STABLE
- Tenant Isolation（WP-C1-05 版本）: STABLE
- Policy Engine: STABLE
- Model Constraints: STABLE

---

## 8. Phase B 建議修改清單

### 8.1 應修改的檔案（測試層只改 4 個）

| 檔案 | 修改內容 | 預計影響 |
|------|----------|----------|
| test_reporting_sessions.py | 移除所有 hdr() 呼叫，改為 override_actor_dependency；修正 user_a.id.id typo | 16 FAIL -> PASS |
| test_reporting_user_summary.py | 移除所有 hdr() 呼叫，改為 override_actor_dependency | 13 FAIL -> PASS |
| test_reporting_company_summary.py | 移除所有 hdr() 呼叫，改為 override_actor_dependency | 14 FAIL -> PASS |
| test_break_out_enforcement.py | 新增 feature gate mock（patch _require_attendance_feature）| 6 FAIL -> PASS |

Phase B 修改後預期新增 PASS：49 個

### 8.2 不應修改的檔案

| 檔案 | 原因 |
|------|------|
| attendance/api.py | 本票嚴格禁止修改 |
| attendance/service.py | 本票嚴格禁止修改 |
| attendance/repo.py | 本票嚴格禁止修改 |
| test_api.py | 舊 router 向後相容，pre-existing |
| test_out_checkpoint.py | OUT Checkpoint API 未實作（WP-C1-09）|
| test_migration.py | 硬碼舊帳號，環境問題 |
| test_business_invariant.py（失敗部分）| repo 介面演化，需謹慎評估 |
| test_location_policy.py | fixture 問題 + haversine，pre-existing |
| test_tenant_validation.py（失敗部分）| 舊 repo 介面，pre-existing |
| test_regression.py | punch_time API 設計問題，需業務層決策 |
| test_tenant_isolation.py | 舊 router + test_phase4 依賴，pre-existing |

---

## 9. Phase B 預期結果

| 指標 | Phase A（現況）| Phase B（預期）|
|------|---------------|----------------|
| PASS | 85 | ~134 |
| FAIL | 85 | ~36 |
| ERROR | 9 | 9（不變）|
| 核心功能穩定 PASS | 75/75 | 75/75（不變）|
| 本票修復 | 0 | 49 |
| Pre-existing 保留 | 85+9 | 36+9 |

---

## 10. Pre-existing 問題清單（不應在本票處理）

| # | 問題 | 影響測試數 | 建議後續 |
|---|------|-----------|----------|
| 1 | 舊 router /api/attendance/ 使用 X-Company-ID header | 11 | 舊版向後相容，不遷移 |
| 2 | OUT Checkpoint API endpoint 未實作 | 7 | WP-C1-09 補完 |
| 3 | test_migration.py 硬碼舊帳號 attendance_user | 9 | 環境設定專票 |
| 4 | test_business_invariant.py repo 介面不符（close_session 簽名變更）| 5 | 評估 repo 介面是否回補 |
| 5 | test_location_policy.py 使用 db_session fixture（不存在）| 6 ERROR | fixture 對齊專票 |
| 6 | test_location_policy.py::TestDistanceCalculation::test_haversine_distance | 1 | haversine 計算邏輯問題 |
| 7 | test_tenant_validation.py 舊版 AttendanceRepository 介面 | 2 | 舊 repo 介面，不修改 |
| 8 | test_regression.py::test_8_cross_midnight — punch_time 被 API 忽略 | 1 | 業務層設計決策 |
| 9 | test_tenant_isolation.py::TestCrossCompanyIsolation 依賴空檔 test_phase4.py | 3 ERROR | 清理空依賴或重寫 |

---

## 11. 最終盤點結論

| 確認項目 | 結論 |
|----------|------|
| 穩定 PASS 核心功能測試 | 75/75（feature gate + model constraints + policy engine + JWT migration + tenant isolation）|
| 本票可修的測試層問題 | 明確識別：4 個測試檔，49 個失敗，原因明確 |
| Pre-existing 失敗 | 36 FAIL + 9 ERROR，全部分類完成 |
| Warnings 盤點 | 26 個，均為技術債，不影響功能 |
| 業務邏輯未觸碰 | api.py / service.py / repo.py 均未修改 |

### Phase B 進入條件

Pre-Audit 完成，以下條件已滿足：
- 已確認 75 個穩定 PASS 測試作為回歸基線
- 已確認 4 個本票可修的測試檔及具體修改方式
- 已確認 36+9 個 pre-existing 問題，Phase B 不觸碰
- 已確認不修改任何業務邏輯（api.py / service.py / repo.py）

Phase B 可進入：修復 test_reporting_sessions.py、test_reporting_user_summary.py、
test_reporting_company_summary.py、test_break_out_enforcement.py 四個測試檔的測試層問題。

---

*本報告由 AI 依據 2026-03-17 實際 pytest 執行結果產出。*
*執行命令：TEST_DATABASE_URL=postgresql+psycopg2://postgres:***@127.0.0.1:5432/attendance_test_db*
*pytest app/modules/attendance/tests/ -v（179 collected, 85 passed, 85 failed, 9 errors, 26 warnings）*
