# Attendance 開發順序總控文件

**文件版本：** 1.0  
**建立日期：** 2026-03-04  
**目的：** 建立 Gate 5 下 WP-11-01～WP-11-06 的唯一執行順序，避免 AI 亂跳工作包  
**狀態：** ✅ ACTIVE

---

## Authority & Rules（權威來源）

### 架構權威
- **SA_MODULE_SPEC_v2.1.md** — 唯一架構權威規範
  - Platform-First Identity 架構定義
  - Tenant Isolation 規則
  - Feature Flags 機制
  - 所有模組必須遵循的規範

### 順序權威
- **MASTER_DEVELOPMENT_ROADMAP_v2.md** — 開發路線圖與 WP 順序權威
  - 6 個 Phase 的執行順序
  - 31 個 Work Packages 定義
  - 依賴關係與啟動條件

### 現況權威
- **REALITY_AUDIT_STATUS_INVENTORY.md** — 系統現況盤點
  - 7 個已實作模組狀態
  - 79 個 Python 檔案清單
  - 29 個測試檔案
  - 模組完成度評估

### 歷史文件規則
- **docs/archive/** — 僅供歷史參考，不作為開發依據
- 所有 archive 內的文件（包含舊版 SA、舊版 Roadmap、Phase 1-7 報告）均不可作為開發決策依據

---

## Single Source of Truth: WP Order（唯一順序）

Gate 5 下的 Work Packages 必須按以下順序執行：

| WP | 一句話目的 | 狀態 |
|-----|-----------|------|
| **WP-11-01** | 建立 Attendance Domain Model（models + repo + tests） | ✅ COMPLETED |
| **WP-11-02** | 實作 Punch In/Out API（打卡核心功能） | ✅ COMPLETED |
| **WP-11-03** | 實作 Policy Engine v1（政策評估引擎） | ✅ COMPLETED |
| **WP-11-04A** | 實作 Company Entitlements + Feature Flags | ✅ COMPLETED |
| **WP-11-04B** | Gate Ready Audit（審查 + 產出報告，不做新功能） | 🎯 CURRENT |
| **WP-11-05** | Attendance Regression Tests（8 個核心回歸測試） | ⏳ NEXT |
| **WP-11-06** | Attendance Reporting v1（報表模組） | ⏳ PLANNED |

**關鍵原則：**
- 不可跳過任何 WP
- 不可同時執行多個 WP
- 每個 WP 必須完成 Exit Criteria 才能進入下一個
- 完成任何 WP 後必須更新 NEXT_WP_TICKET.md + GATE_PROGRESS_TRACKER.md

---

## Per-WP Execution Card（每個 WP 執行卡）

---

### WP-11-01: Attendance Domain Model

**Goal:**  
建立 Attendance 模組的 Domain Model（models + repo + migration + tests）

**Inputs:**
- `@Files docs/SA_MODULE_SPEC_v2.1.md`
- `@Files docs/MASTER_DEVELOPMENT_ROADMAP_v2.md`

**Touch Points:**
- `@Folders backend/app/modules/attendance/`
- `@Folders backend/alembic/versions/`

**Deliverables:**
- `backend/alembic/versions/001b_create_attendance_domain_v2_fixed.py`
- `backend/app/modules/attendance/models.py`
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/tests/test_model_constraints.py`
- `backend/app/modules/attendance/tests/test_migration.py`
- `backend/app/modules/attendance/tests/test_business_invariant.py`
- `docs/WP-11-01_PHASE_B_REPORT.md`

**Tests:**
- `pytest backend/app/modules/attendance/tests/test_model_constraints.py` (20 tests)
- `pytest backend/app/modules/attendance/tests/test_migration.py` (9 tests)
- `pytest backend/app/modules/attendance/tests/test_business_invariant.py` (12 tests)
- **Total: 41/41 PASS**

**Do-Not:**
- ❌ 不要實作 API endpoints（那是 WP-11-02）
- ❌ 不要實作 Policy Engine（那是 WP-11-03）
- ❌ 不要修改 auth schema（Gate 4 已凍結）

**Exit Criteria:**
- ✅ 3 個 tables 建立（sessions, punches, policies）
- ✅ Business invariant 強制執行（一個 user 只能有一個 open session）
- ✅ Tenant isolation 強制執行（所有查詢有 company_id）
- ✅ 41/41 測試通過
- ✅ Migration 可 upgrade/downgrade

**Gate Updates:**
- 完成後更新 `docs/NEXT_WP_TICKET.md` → Next: WP-11-02
- 完成後更新 `docs/GATE_PROGRESS_TRACKER.md` → WP-11-01: ✅ COMPLETED

**Status:** ✅ COMPLETED (2026-03-03)

---

### WP-11-02: Punch In/Out API

**Goal:**  
實作打卡核心 API（Punch In/Out/Current Status/History）

**Inputs:**
- `@Files docs/SA_MODULE_SPEC_v2.1.md`
- `@Files docs/MASTER_DEVELOPMENT_ROADMAP_v2.md`
- `@Files docs/WP-11-01_PHASE_B_REPORT.md`（WP-11-01 交付物）

**Touch Points:**
- `@Folders backend/app/modules/attendance/`（api.py, service.py, schemas.py）

**Deliverables:**
- `backend/app/modules/attendance/api.py`（新增 4 個 endpoints）
- `backend/app/modules/attendance/service.py`（業務邏輯）
- `backend/app/modules/attendance/schemas.py`（Pydantic schemas）
- `backend/app/modules/attendance/tests/test_punch_api.py`
- `docs/WP-11-02_REPORT.md`

**Tests:**
- `pytest backend/app/modules/attendance/tests/test_punch_api.py` (17 tests)
- **Total: 17/17 PASS**

**Do-Not:**
- ❌ 不要實作 Policy Engine（那是 WP-11-03）
- ❌ 不要實作 Reporting（那是 WP-11-06）
- ❌ 不要修改 auth schema（Gate 4 已凍結）
- ❌ 不要修改 migration（Domain Model 已凍結）

**Exit Criteria:**
- ✅ 4 個 endpoints 實作完成（punch-in, punch-out, current-status, history）
- ✅ JWT authentication 整合完成
- ✅ Scope 驗證實作（Scope → Tenant → Feature）
- ✅ 17/17 測試通過
- ✅ OpenAPI 文件自動生成

**Gate Updates:**
- 完成後更新 `docs/NEXT_WP_TICKET.md` → Next: WP-11-03
- 完成後更新 `docs/GATE_PROGRESS_TRACKER.md` → WP-11-02: ✅ COMPLETED

**Status:** ✅ COMPLETED (2026-03-03)

---

### WP-11-03: Policy Engine v1

**Goal:**  
實作 Policy Engine（遲到/早退/加班計算）

**Inputs:**
- `@Files docs/SA_MODULE_SPEC_v2.1.md`
- `@Files docs/MASTER_DEVELOPMENT_ROADMAP_v2.md`
- `@Files docs/WP-11-02_REPORT.md`（WP-11-02 交付物）

**Touch Points:**
- `@Folders backend/app/modules/attendance/`（policy_engine.py）

**Deliverables:**
- `backend/app/modules/attendance/policy_engine.py`（24KB）
- `backend/app/modules/attendance/tests/test_policy_engine.py`
- `docs/WP-11-03_REPORT.md`
- `docs/SPLIT_SHIFT_DESIGN.md`（665 lines）

**Tests:**
- `pytest backend/app/modules/attendance/tests/test_policy_engine.py` (12 tests)
- `pytest backend/app/modules/attendance/tests/test_split_shift.py` (12 tests)
- **Total: 24/24 PASS**

**Do-Not:**
- ❌ 不要實作 Reporting（那是 WP-11-06）
- ❌ 不要修改 API endpoints（WP-11-02 已完成）
- ❌ 不要修改 migration（Domain Model 已凍結）

**Exit Criteria:**
- ✅ Policy evaluation engine 實作完成
- ✅ Late/overtime detection 運作正常
- ✅ Split shift support 實作完成
- ✅ 24/24 測試通過

**Gate Updates:**
- 完成後更新 `docs/NEXT_WP_TICKET.md` → Next: WP-11-04A
- 完成後更新 `docs/GATE_PROGRESS_TRACKER.md` → WP-11-03: ✅ COMPLETED

**Status:** ✅ COMPLETED (2026-03-04)

---

### WP-11-04A: Company Entitlements + Feature Flags

**Goal:**  
實作 Company Entitlements 與 Feature Flags 系統

**Inputs:**
- `@Files docs/SA_MODULE_SPEC_v2.1.md`
- `@Files docs/MASTER_DEVELOPMENT_ROADMAP_v2.md`

**Touch Points:**
- `@Folders backend/alembic/versions/`（新增 migration）
- `@Folders backend/app/modules/tenants/`（entitlements 相關）
- `@Folders backend/app/modules/customer_service/`（assignments 相關）

**Deliverables:**
- `backend/alembic/versions/wp_11_04a_entitlements.py`
- `backend/app/modules/tenants/`（entitlements API）
- `backend/app/modules/customer_service/`（assignments API）
- `docs/WP-11-04A_COMPLETION_REPORT_FINAL.md`

**Tests:**
- `pytest backend/app/modules/tenants/tests/test_entitlements_api.py`
- `pytest backend/app/modules/customer_service/tests/`

**Do-Not:**
- ❌ 不要修改 attendance 模組（已完成）
- ❌ 不要修改 auth schema（Gate 4 已凍結）

**Exit Criteria:**
- ✅ `company_entitlements` table 建立
- ✅ `support_company_assignments` table 建立
- ✅ Entitlements CRUD API 完成
- ✅ Feature gate 驗證機制完成
- ✅ 所有測試通過

**Gate Updates:**
- 完成後更新 `docs/NEXT_WP_TICKET.md` → Next: WP-11-04B
- 完成後更新 `docs/GATE_PROGRESS_TRACKER.md` → WP-11-04A: ✅ COMPLETED

**Status:** ✅ COMPLETED (2026-03-04)

---

### WP-11-04B: Gate Ready Audit

**Goal:**  
執行 Gate Ready Audit（只做審查 + 產出報告，不做新功能）

**Inputs:**
- `@Files docs/SA_MODULE_SPEC_v2.1.md`
- `@Files docs/MASTER_DEVELOPMENT_ROADMAP_v2.md`
- `@Files docs/REALITY_AUDIT_STATUS_INVENTORY.md`
- `@Files docs/WP-11-04B_KICKOFF_PLAN.md`
- `@Files docs/WP-11-04B_GATE_READY_REPORT.md`

**Touch Points:**
- `@Folders backend/app/modules/attendance/`（只檢查，不修改）
- `@Folders backend/alembic/versions/`（只檢查，不修改）

**Deliverables:**
- `docs/MIGRATION_CHAIN_AUDIT_REPORT.md`（Migration Chain 審查報告）
- `docs/TENANT_ISOLATION_AUDIT_REPORT.md`（Tenant Isolation 審查報告）
- `docs/ATTENDANCE_REGRESSION_SPEC.md`（WP-11-05 準備文件）

**Tests:**
- ❌ 本 WP 不執行測試（只審查）
- ✅ 但需確認現有測試狀態（41 + 17 + 24 = 82 tests）

**Do-Not:**
- ❌ 不要新增任何 API endpoint
- ❌ 不要做 Reporting（那是 WP-11-06）
- ❌ 不要改 migration / schema
- ❌ 不要修改任何程式碼
- ✅ 只新增/更新 docs 報告檔

**Exit Criteria:**
- ✅ Migration Chain Audit 完成（無分叉、可重建）
- ✅ Tenant Isolation Audit 完成（所有查詢有 company_id 限制）
- ✅ Regression Spec 準備完成（至少 8 個場景，含 cross-midnight）
- ✅ Go/No-Go 結論產出（是否可進入 WP-11-05）

**Gate Updates:**
- 完成後更新 `docs/NEXT_WP_TICKET.md` → Next: WP-11-05
- 完成後更新 `docs/GATE_PROGRESS_TRACKER.md` → WP-11-04B: ✅ COMPLETED

**Status:** 🎯 CURRENT (2026-03-04)

---

### WP-11-05: Attendance Regression Tests

**Goal:**  
實作並通過 8 個 Attendance 核心回歸測試

**Inputs:**
- `@Files docs/SA_MODULE_SPEC_v2.1.md`
- `@Files docs/MASTER_DEVELOPMENT_ROADMAP_v2.md`
- `@Files docs/ATTENDANCE_REGRESSION_SPEC.md`（WP-11-04B 交付物）

**Touch Points:**
- `@Folders backend/app/modules/attendance/tests/`（新增回歸測試檔）

**Deliverables:**
- `backend/app/modules/attendance/tests/test_regression.py`（8 個測試）
- `docs/WP-11-05_REGRESSION_TEST_REPORT.md`

**Tests:**
- `pytest backend/app/modules/attendance/tests/test_regression.py` (8 tests)
- **Required: 8/8 PASS**

**Test Scenarios (Minimum 8):**
1. NO_MATCH 未填原因 → 拒絕
2. NO_MATCH 有原因 → PENDING
3. APPROVED → 推導正確
4. PENDING 不參與推導與日結
5. 21:00 日結缺卡正確
6. approve pending → 該日重算
7. customer_service 未指派公司 → 403
8. cross-midnight（例如 3/31 23:00 上班到 4/1 02:00）
   - raw_duration 應為正數（punch_out - punch_in，UTC-aware datetime）
   - session 所屬日期 = punch_in_time 的 Asia/Taipei 日期（SA v2.1 §29.2 Session Ownership Date）
   - 月報歸屬 = punch_in_time 所在月份（SA v2.1 §29.3）

**Additional Scenarios (Optional):**
- double punch prevention（重複打卡）
- tenant isolation negative test（跨 company 查不到資料）
- policy fallback（無政策時 fallback）
- edge case（例如缺 punch-out、或時間邊界）

**Do-Not:**
- ❌ 不要修改 API endpoints（WP-11-02 已完成）
- ❌ 不要修改 Policy Engine（WP-11-03 已完成）
- ❌ 不要做 Reporting（那是 WP-11-06）

**Exit Criteria:**
- ✅ 8/8 核心回歸測試實作完成
- ✅ 8/8 測試通過
- ✅ 測試報告已產出
- ✅ Cross-midnight 場景驗證通過

**Gate Updates:**
- 完成後更新 `docs/NEXT_WP_TICKET.md` → Next: WP-11-06
- 完成後更新 `docs/GATE_PROGRESS_TRACKER.md` → WP-11-05: ✅ COMPLETED

**Status:** ⏳ NEXT

---

### WP-11-06: Attendance Reporting v1

**Goal:**  
實作 Attendance Reporting v1（報表模組）

**Inputs:**
- `@Files docs/SA_MODULE_SPEC_v2.1.md`
- `@Files docs/MASTER_DEVELOPMENT_ROADMAP_v2.md`
- `@Files docs/WP-11-04B_KICKOFF_PLAN.md`（報表需求）

**Touch Points:**
- `@Folders backend/app/modules/attendance/`（新增 reporting 相關 API）

**Deliverables:**
- `backend/app/modules/attendance/api.py`（新增 reporting endpoints）
- `backend/app/modules/attendance/service.py`（新增 reporting 邏輯）
- `backend/app/modules/attendance/tests/test_reporting_api.py`
- `docs/WP-11-06_REPORTING_REPORT.md`

**Tests:**
- `pytest backend/app/modules/attendance/tests/test_reporting_api.py` (15+ tests)

**Key Features:**
- 員工出勤記錄查詢（GET /api/v1/attendance/sessions）
- 公司出勤統計報表（GET /api/v1/attendance/reports/company-summary）
- 個人出勤統計（GET /api/v1/attendance/reports/user-summary）
- CSV 匯出功能（可選）

**Do-Not:**
- ❌ 不要修改 Domain Model（WP-11-01 已凍結）
- ❌ 不要修改 Punch API（WP-11-02 已完成）
- ❌ 不要修改 Policy Engine（WP-11-03 已完成）

**Exit Criteria:**
- ✅ 3 個 reporting endpoints 實作完成
- ✅ Scope 驗證實作（Company User 只能查自己）
- ✅ Tenant Isolation 強制執行
- ✅ 15+ 測試通過
- ✅ CSV 匯出功能運作正常（如實作）

**Gate Updates:**
- 完成後更新 `docs/NEXT_WP_TICKET.md` → Next: Phase 2 (Core Backend Completion)
- 完成後更新 `docs/GATE_PROGRESS_TRACKER.md` → WP-11-06: ✅ COMPLETED
- 完成後更新 `docs/GATE_PROGRESS_TRACKER.md` → Gate 5: ✅ COMPLETE

**Status:** ⏳ PLANNED

---

## Gate Updates Rules（完成任何 WP 後的更新規則）

### 必須更新的文件

每完成一個 WP，必須更新以下兩個文件：

#### 1. NEXT_WP_TICKET.md
- 更新 "Selected WP" → 下一個 WP
- 更新 "Status" → 當前 WP 狀態
- 最小差異更新（只改必要欄位）

#### 2. GATE_PROGRESS_TRACKER.md
- 更新對應 WP 的 Status → ✅ COMPLETED
- 更新 Completion Date
- 更新 Test Results
- 更新 Overall Progress 百分比
- 最小差異更新（不要重寫整份）

### 更新時機
- ✅ WP Exit Criteria 全部滿足後
- ✅ 所有測試通過後
- ✅ 交付物全部產出後

### 更新原則
- 只更新必要欄位
- 不要重寫整份文件
- 保持文件格式一致
- 記錄完成日期

---

## Current Position（當前位置）

**依據：**
- `docs/REALITY_AUDIT_STATUS_INVENTORY.md` (2026-03-04)
- `docs/GATE_PROGRESS_TRACKER.md` (2026-03-03)
- `docs/NEXT_WP_TICKET.md` (2026-03-02)

**當前狀態：**

| WP | Status | Completion Date | Tests |
|----|--------|-----------------|-------|
| WP-11-01 | ✅ COMPLETED | 2026-03-03 | 41/41 PASS |
| WP-11-02 | ✅ COMPLETED | 2026-03-03 | 17/17 PASS |
| WP-11-03 | ✅ COMPLETED | 2026-03-04 | 24/24 PASS |
| WP-11-04A | ✅ COMPLETED | 2026-03-04 | All PASS |
| **WP-11-04B** | **🎯 CURRENT** | **-** | **-** |
| WP-11-05 | ⏳ NEXT | - | - |
| WP-11-06 | ⏳ PLANNED | - | - |

**Current WP:** WP-11-04B (Gate Ready Audit)  
**Next WP:** WP-11-05 (Attendance Regression Tests)  
**Gate 5 Progress:** 4/7 WPs completed (57%)

---

## Summary

本文件為 Gate 5 下 WP-11-01～WP-11-06 的唯一執行順序權威。

**核心原則：**
1. 按順序執行，不可跳過
2. 每個 WP 有明確的 Goal、Inputs、Deliverables、Tests、Do-Not、Exit Criteria
3. 完成任何 WP 後必須更新 NEXT_WP_TICKET.md + GATE_PROGRESS_TRACKER.md
4. SA v1.9 是架構權威、Roadmap v2 是順序權威、Reality Audit 是現況權威
5. archive 僅歷史、不作依據

**當前位置：**
- Current: WP-11-04B (Gate Ready Audit)
- Next: WP-11-05 (Attendance Regression Tests)

---

**文件版本：** 1.0  
**建立日期：** 2026-03-04  
**維護者：** 架構團隊  
**狀態：** ✅ ACTIVE

---

**END OF ATTENDANCE_DEVELOPMENT_MASTER_FLOW.md**
