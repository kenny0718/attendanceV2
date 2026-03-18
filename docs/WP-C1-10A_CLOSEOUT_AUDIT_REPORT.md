# WP-C1-10A — C1 / Gate 5 Closeout Audit Report

**報告日期：** 2026-03-18  
**報告類型：** Closeout Audit / Gap Inventory  
**執行範圍：** C1 系列全部 WP + 所有模組層級盤點  
**執行人：** AI Pair Programmer（audit only，不修改任何 code）  
**依據文件：** GATE_PROGRESS_TRACKER.md、WORKSTREAM_STATUS_LEDGER.md、MODULE_STATUS_MATRIX.md、CURRENT_SYSTEM_STATE.md、WP-C1-08 Completion Report、直接 repo scan

---

## 1. Executive Summary

| 項目 | 結論 |
|------|------|
| C1 / Gate 5 主線 WP 完成度 | ~90%（WP-C1-01 ~ WP-C1-08 全部 COMPLETE）|
| Gate 5 是否 technically complete | **否**（存在 blocking gaps）|
| Blocking gaps 數量 | 3 個（GAP-C1-001, 002, 003）|
| Non-blocking gaps 數量 | 17 個（可後補）|
| Gate 5 是否可立即關閉 | **否**（條件式關閉需先解決 3 個 blocking gaps）|

### 主要風險

1. **attendance 舊 router 仍 Header auth**（GAP-C1-001）— 11 個測試持續 FAIL，auth pattern 未統一
2. **OUT Checkpoint API endpoint 未實作**（GAP-C1-002）— 7 個測試持續 FAIL；功能層缺口
3. **leave 模組 JWT 未遷移**（GAP-C1-003）— 與系統其他模組 auth pattern 不一致

---

## 2. WP Coverage Table

| WP | 名稱 | Code | Test | Docs | Closeout Status | Notes |
|----|------|------|------|------|-----------------|-------|
| WP-C1-01 | PostgreSQL 環境建立 + Migration 驗證 | YES | YES（20/20）| YES | VERIFIED | 21 tables；head=009 |
| WP-C1-03 | Auth 轉換 Batch 2（audit/notifications/backup）| YES | YES（78/78）| YES | COMPLETE | E2E 未驗證 |
| WP-C1-04 | PostgreSQL 回歸測試 | YES | YES（78/78）| YES | COMPLETE | 37 pre-existing 已分類 |
| WP-C1-05 | Tenant Isolation 真實 DB 驗證 | YES | YES（39/39）| YES | COMPLETE | 39/39 PASS on PostgreSQL |
| WP-C1-06 | Feature Gate 套用至所有 API | YES | YES（22/22）| YES | COMPLETE | 5 核心模組 gated |
| WP-C1-07 | Attendance router_v1 JWT 遷移 | YES | YES（12/12）| YES | COMPLETE | 舊 router 仍 Header（向後相容）|
| WP-C1-08 | Attendance Test Stabilization | YES | PARTIAL（134/179）| YES | COMPLETE with gaps | 36+9 pre-existing |
| WP-C1-09 | Governance Consolidation | N/A | N/A | YES | COMPLETE | 治理收斂票 |
| WP-C1-09A | Governance Reconstruction | N/A | N/A | YES | COMPLETE | 治理修復票 |

### WP-C1-08 Pre-existing 失敗明細

| 類型 | 測試檔 | 數量 | 阻塞性 |
|------|--------|------|--------|
| 舊 router Header auth | test_api.py, test_tenant_isolation.py::TestTenantIsolation | 11 FAIL | BLOCKING（GAP-C1-001）|
| OUT Checkpoint API 不存在 | test_out_checkpoint.py | 7 FAIL | BLOCKING（GAP-C1-002）|
| migration 舊帳號硬碼 | test_migration.py | 9 FAIL | NON-BLOCKING |
| business_invariant repo 介面不符 | test_business_invariant.py | 5 FAIL | NON-BLOCKING |
| location_policy fixture 不符 | test_location_policy.py | 6 ERROR + 1 FAIL | NON-BLOCKING |
| tenant_validation 舊 repo 介面 | test_tenant_validation.py | 2 FAIL | NON-BLOCKING |
| cross_midnight punch_time 被 API 忽略 | test_regression.py | 1 FAIL | NON-BLOCKING |
| test_phase4 空檔案依賴 | test_tenant_isolation.py | 3 ERROR | NON-BLOCKING |

---

## 3. Module Audit Matrix

| Module | Functional Status | Test Files | JWT Auth | Feature Gate | Governance | Overall Status |
|--------|------------------|-----------|----------|--------------|------------|----------------|
| attendance | CODE_COMPLETE | 20 files；134/179 PASS | PARTIAL（router_v1 OK；舊 router Header）| YES（attendance.core）| docs.md v2.1 | PARTIAL |
| auth | CODE_COMPLETE | 3 files；runtime 未驗證 | N/A（發 token）| N/A | 無 docs.md | CODE_COMPLETE |
| audit | CODE_COMPLETE | 6 files；27/27 PASS | YES（JWT Actor WP-C1-03）| YES（audit.core）| docs.md 存在 | COMPLETE |
| backup | CODE_COMPLETE | 5 files；25/25 PASS | YES（JWT Actor WP-C1-03）| YES（backup.core）| docs.md 存在 | COMPLETE |
| notifications | CODE_COMPLETE | 5 files；26/26 PASS | YES（JWT Actor WP-C1-03）| YES（notifications.core）| docs.md 存在 | COMPLETE |
| tenants | CODE_COMPLETE | 4 files；runtime 未驗證 | PARTIAL（get_current_actor，非 get_actor_with_company）| N/A（設計決策）| 無 docs.md | CODE_COMPLETE |
| leave | COMPLETE（code）| 3 files（feature_gate + tenant_isolation 僅）| NO（get_current_user_id 舊式）| YES（leave.core）| 無 docs.md | GAP |
| customer_service | CODE_COMPLETE | 0 test files | PARTIAL（get_current_actor）| NO | 無 docs.md | UNKNOWN |
| schedule | NOT STARTED | N/A | N/A | N/A | N/A | NOT STARTED |

---

## 4. Gap Inventory

| ID | Type | Module | Description | Severity | Blocking | Evidence |
|----|------|--------|-------------|----------|----------|----------|
| GAP-C1-001 | JWT_GAP | attendance | 舊 router（/api/attendance/）仍 Header auth（get_current_company_id），未遷移至 JWT Actor | HIGH | YES | api.py L76,L92-93；test_api.py 11 FAIL |
| GAP-C1-002 | MODULE_GAP | attendance | OUT Checkpoint API endpoint 未實作（/api/v1/attendance/out-checkpoint），model/repo 存在但 router 未建 | HIGH | YES | test_out_checkpoint.py 7 FAIL；WP-C1-08 report |
| GAP-C1-003 | JWT_GAP | leave | 全部 5 endpoints 使用 get_current_user_id/company_id 舊式 auth，未遷移至 JWT Actor | HIGH | YES | leave/api.py L26,L70-71,L110-111 |
| GAP-C1-004 | TEST_GAP | leave | 無功能性 test_api.py；僅有 test_feature_gate.py + test_tenant_isolation.py | MEDIUM | NO | ls leave/tests/ 3 files only |
| GAP-C1-005 | TEST_GAP | customer_service | tests/ 完全無測試（僅 __init__.py）| HIGH | NO | ls customer_service/tests/ |
| GAP-C1-006 | JWT_GAP | customer_service | 使用 get_current_actor() 非 get_actor_with_company()；auth pattern 不一致 | MEDIUM | NO | customer_service/api.py L11,L25 |
| GAP-C1-007 | MODULE_GAP | customer_service | 無 feature gate、無 docs.md、無任何測試；整體狀態未稽核 | HIGH | NO | repo scan |
| GAP-C1-008 | TEST_GAP | attendance | test_migration.py 9 FAIL（硬碼舊帳號環境問題）| MEDIUM | NO | WP-C1-08 report |
| GAP-C1-009 | TEST_GAP | attendance | test_business_invariant.py 5 FAIL（repo 介面不符）| MEDIUM | NO | WP-C1-08 report |
| GAP-C1-010 | TEST_GAP | attendance | test_location_policy.py 6 ERROR + 1 FAIL（fixture 不符）| MEDIUM | NO | WP-C1-08 report |
| GAP-C1-011 | TEST_GAP | attendance | test_tenant_validation.py 2 FAIL（舊 repo 介面）| LOW | NO | WP-C1-08 report |
| GAP-C1-012 | TEST_GAP | attendance | test_regression.py::test_8 1 FAIL（cross_midnight punch_time 被 API 忽略）| MEDIUM | NO | WP-C1-08 report |
| GAP-C1-013 | TEST_GAP | attendance | test_tenant_isolation.py::TestCrossCompanyIsolation 3 ERROR（空檔案依賴）| LOW | NO | WP-C1-08 report |
| GAP-C1-014 | DOC_GAP | auth | 無獨立 docs.md；runtime 登入流程未在真實 DB 驗證 | MEDIUM | NO | repo scan |
| GAP-C1-015 | DOC_GAP | tenants | 無獨立 docs.md；runtime 未驗證 | MEDIUM | NO | repo scan |
| GAP-C1-016 | JWT_GAP | tenants | 使用 get_current_actor() 非 get_actor_with_company()；pattern 與主流不一致 | LOW | NO | tenants/api.py |
| GAP-C1-017 | INTEGRATION_GAP | all | 無任何 E2E integration test（真實 JWT + PostgreSQL 端到端驗證）| HIGH | NO | repo scan；WP-C1-03 report |
| GAP-C1-018 | INTEGRATION_GAP | frontend | WP-11-13 Manual QA BLOCKED（GPS + UI 人工測試）；需真實瀏覽器環境 | MEDIUM | NO | GATE_PROGRESS_TRACKER.md |
| GAP-C1-019 | MODULE_GAP | schedule | 完全未實作；無 code、migration、test | LOW | NO | repo scan |
| GAP-C1-020 | DOC_GAP | customer_service | 無 docs.md | LOW | NO | repo scan |

---

## 5. Gate 5 Assessment

### 結論

**Gate 5 / C1 尚不可立即關閉。建議採條件式關閉路徑（Conditional Closeout）。**

### Gate 5 Technically Complete？

**否。** 存在 3 個 blocking gaps（GAP-C1-001, 002, 003）。

### Blocking vs Non-blocking

**Blocking（必須修才可關 Gate）：**

| Gap | 原因 |
|-----|------|
| GAP-C1-001 | attendance 舊 router 仍 Header auth — auth pattern 未統一；11 個測試持續 FAIL |
| GAP-C1-002 | OUT Checkpoint API endpoint 缺失 — 7 個測試 FAIL；功能層明確缺口 |
| GAP-C1-003 | leave 模組 JWT 未遷移 — 5 個 endpoints 使用舊式 auth；與系統 pattern 不一致 |

**Non-blocking（可後補）：** GAP-C1-004 ~ GAP-C1-020

包含：customer_service 測試缺失、auth/tenants 無 docs.md、E2E test 缺失、WP-11-13 Manual QA BLOCKED、schedule 未實作等。

### 條件式關閉條件

若以下三項完成，Gate 5 即可宣告條件式關閉：

1. GAP-C1-001 解決：attendance 舊 router JWT 遷移（或明確廢棄並移除對應測試）
2. GAP-C1-002 解決：OUT Checkpoint API endpoint 實作
3. GAP-C1-003 解決：leave 模組 JWT Actor 遷移

---

## 6. Recommended Next WPs

### WP-C1-10 — Attendance Old Router JWT Migration（解決 GAP-C1-001）

**目標：** 將 attendance 舊 router（/api/attendance/mock-create 等）從 Header auth 遷移至 JWT Actor，或明確廢棄  
**範圍：**
- 確認舊 router endpoints 是否仍有前端或外部呼叫
- 若有使用：遷移至 get_actor_with_company pattern
- 若無使用：標記 deprecated，更新 test_api.py 以反映正確期望
- 修正 test_api.py 11 FAIL
**不包含：** 新功能、schema 變更、其他模組

---

### WP-C1-11 — OUT Checkpoint API Implementation（解決 GAP-C1-002）

**目標：** 補實 OUT Checkpoint API endpoint（/api/v1/attendance/out-checkpoint）  
**範圍：**
- model/repo 已存在，補實 router endpoint
- 修正 test_out_checkpoint.py 7 FAIL
- 更新 attendance/docs.md 相關說明
**不包含：** 前端整合、新 migration、其他模組

---

### WP-C1-12 — Leave Module JWT Migration + Test Completion（解決 GAP-C1-003, 004）

**目標：** leave 模組 auth 統一至 JWT Actor + 補齊功能測試  
**範圍：**
- leave/api.py 所有 5 endpoints 遷移至 get_actor_with_company
- 建立 test_api.py（功能性測試）
- 更新 test_tenant_isolation.py 以使用 JWT Actor pattern
**不包含：** leave 前端、新業務邏輯、schema 變更

---

### WP-C1-13 — Customer Service Module Audit + Baseline（解決 GAP-C1-005, 006, 007, 020）

**目標：** customer_service 模組完整稽核 + 補齊最小測試基準  
**範圍：**
- 確認 3 個 endpoints 的實際功能與 auth pattern
- 建立基本 test_api.py
- 評估是否需要 feature gate
- 補齊 docs.md
**不包含：** 新業務功能、schema 變更

---

### WP-C1-14 — Attendance Test Gap Resolution（解決 GAP-C1-008~013）

**目標：** 修復 attendance 模組剩餘 non-blocking test gaps  
**範圍：**
- test_migration.py 帳號問題（環境修正）
- test_business_invariant.py repo 介面對齊
- test_location_policy.py fixture 修正
- test_regression.py::test_8 cross_midnight 修正
**不包含：** production code 新功能、其他模組

---

## 7. Scope Control Confirmation

| 項目 | 結果 |
|------|------|
| production code changed | **NO** |
| API behavior changed | **NO** |
| test files changed | **NO** |
| repo cleanup performed | **NO** |

---

**最後更新：** 2026-03-18  
**更新原因：** WP-C1-10A Closeout Audit — C1 / Gate 5 全面盤點，建立 Gap Inventory，拆分後續 WP
