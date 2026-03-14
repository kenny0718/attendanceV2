# DEVELOPMENT MASTER PLAN

**建立日期：** 2026-03-11
**版本：** v1.0
**基於：** SYSTEM_GROUND_TRUTH.md（2026-03-11 驗證基線）
**性質：** 官方開發序列控制文件 — 單一事實來源（Single Source of Truth）

---

## 重要聲明

本文件依據 `docs/SYSTEM_GROUND_TRUTH.md`（2026-03-11 code scan）所建立的驗證基線制定。
所有 WP 執行順序以本文件為準。任何與本文件衝突的舊有文件，以本文件為準。

**本文件不得在未完成對應 WP 驗收條件前提前更新 WP 狀態。**

---

## 1. Purpose

本文件定義系統驗證基線確立後的官方開發序列，作為所有開發決策的最終依據。

本文件是以下事項的單一事實來源（Single Source of Truth）：

- **開發序列**：WP 執行的先後順序與依賴關係
- **WP 優先級**：P0（安全修正）/ P1（功能完整）/ P2（平台擴展）分級
- **模組完成追蹤**：各模組 Auth / Feature Gate / 測試 / 生產就緒狀態
- **整合順序**：跨模組依賴與整合時間點
- **驗收標準**：每個 WP 的 Definition of Done

---

## 2. Development Phases

Phase 1 — Security Baseline Repair     [當前階段 — P0 安全修正]
  WP-C1-01 -> WP-C1-02 -> WP-C1-03 -> WP-C1-04 -> WP-C1-05 -> WP-C1-06 -> WP-C1-07
       ↓
Phase 2 — Core Feature Completion      [P1 核心功能補完]
  WP-C2-01 -> WP-C2-02
       ↓
Phase 3 — Frontend Expansion           [P1 前端擴展]
  Admin Dashboard -> Admin Location -> Reporting UI -> Leave/Approval UI
       ↓
Phase 4 — SaaS Platform Completion     [P2 平台完整化]
  Plan Gates -> Tenant Limits -> Advanced Reporting -> Public API Docs

---

### Phase 1 — Security Baseline Repair

**目標：** 消除所有 P0 安全風險，建立可信任的系統基線。

**進入條件：** SYSTEM_GROUND_TRUTH.md 驗證基線已建立（2026-03-11 完成）

**退出條件（Phase 1 全部完成才可進入 Phase 2）：**
- [ ] 所有 API endpoint 使用 JWT 身份驗證
- [ ] 8 個回歸測試在真實 PostgreSQL 通過
- [ ] Tenant Isolation 在真實 PostgreSQL 驗證
- [ ] Feature Gate 已套用至所有核心 API
- [ ] API 文件完整

---

#### WP-C1-01 — PostgreSQL 執行環境驗證

**優先級：** P0（所有後續 WP 的基礎）
**狀態：** NOT_STARTED
**預估工時：** 30-60 分鐘
**依賴：** 無（Phase 1 起點）

**目標：** 建立真實 PostgreSQL 執行環境，確認 Migration chain 可正確執行至 HEAD。

**交付物：**
- PostgreSQL 測試資料庫可連線（attendance_test）
- alembic upgrade head 執行成功，HEAD = 008_wp_11_13
- 所有 DB table 正確建立（至少 15 個）
- test_business_invariant.py 和 test_model_constraints.py 取得基線通過率

**Definition of Done：**
- [ ] alembic upgrade head 無錯誤
- [ ] alembic heads 只顯示一個 head（008_wp_11_13）
- [ ] 確認所有 table 建立
- [ ] test_business_invariant.py 執行並記錄通過率
- [ ] test_model_constraints.py 執行並記錄通過率
- [ ] WORKSTREAM_STATUS_LEDGER.md 更新

**背景（SYSTEM_GROUND_TRUTH.md V-14 / NV-01 / NV-02）：**
test_business_invariant.py 和 test_model_constraints.py 硬碼
postgresql://attendance_user:attendance_pass@localhost:5432/attendance_test
但 runtime 從未執行確認。

---

#### WP-C1-02 — Attendance 模組 JWT 身份驗證遷移

**優先級：** P0
**狀態：** NOT_STARTED
**預估工時：** 2-4 小時
**依賴：** WP-C1-01

**目標：** attendance 模組全部 10 個 endpoint 從 X-Company-ID Header 遷移至 JWT Bearer。
同步實作 admin_location 模組 RBAC（管理員權限檢查）。

**受影響 Endpoint（SYSTEM_GROUND_TRUTH.md 1.3）：**

| Endpoint | 行號 |
|----------|------|
| POST /mock-create | L70-73 |
| POST /{id}/approve | L84-90 |
| POST /v1/punch-in | L109-115 |
| POST /v1/punch-out | L173-179 |
| GET  /v1/current-status | L266-270 |
| GET  /v1/history | L352-359 |
| POST /v1/break-out | L410-416 |
| POST /v1/break-in | L493-499 |
| GET  /v1/break-punches | L544-549 |
| PATCH /v1/punch/{id}/note | L607-613 |

**admin_location RBAC 缺口（SYSTEM_GROUND_TRUTH.md 2.1）：**

| Endpoint | 行號 | 現況 |
|----------|------|------|
| POST / (create) | L47 | TODO 驗證管理員權限 — 無 RBAC |
| PUT /{id} | L166 | TODO 驗證管理員權限 — 無 RBAC |
| DELETE /{id} | L207 | TODO 驗證管理員權限 — 無 RBAC |

**Definition of Done：**
- [ ] attendance/api.py 所有 endpoint 改用 get_current_actor()
- [ ] get_current_company_id 在 attendance 模組中已移除
- [ ] admin_location_api.py 3 個寫入 endpoint 實作 RBAC
- [ ] 既有 attendance 測試更新為使用 JWT token
- [ ] 所有 attendance 測試在真實 DB 通過
- [ ] WORKSTREAM_STATUS_LEDGER.md 更新
- [ ] MODULE_STATUS_MATRIX.md attendance auth 欄位更新為 VERIFIED

---

#### WP-C1-03 — Audit / Backup / Notifications 模組 Auth 遷移

**優先級：** P0
**狀態：** NOT_STARTED
**預估工時：** 2-4 小時
**依賴：** WP-C1-02

| 模組 | Endpoint 數 | 現況 |
|------|------------|------|
| audit | 5 | X-Company-ID Header（L34,106,195,237,294）|
| backup | 2 | X-Company-ID Header（L22, L56）|
| notifications | 1 | X-Company-ID Header（L35-40）|

**Definition of Done：**
- [ ] audit/api.py 全部 5 個 endpoint 使用 JWT
- [ ] backup/api.py 全部 2 個 endpoint 使用 JWT
- [ ] notifications/api.py 1 個 endpoint 使用 JWT
- [ ] 3 個模組的測試更新為 JWT 模式
- [ ] 所有測試改用 PostgreSQL（移除 SQLite :memory:）
- [ ] 所有測試在真實 DB 通過
- [ ] WORKSTREAM_STATUS_LEDGER.md 更新
- [ ] MODULE_STATUS_MATRIX.md 相關模組 auth 欄位更新

---

#### WP-C1-04 — 回歸測試實作（8 個測試）

**優先級：** P0
**狀態：** NOT_STARTED（現況：1/8 骨架，0/8 通過）
**預估工時：** 3-5 小時
**依賴：** WP-C1-02

**現況（SYSTEM_GROUND_TRUTH.md V-08）：**
test_regression.py 只有 Test 8（cross-midnight）骨架存在（L51），Test 1-7 完全不存在。

**Definition of Done：**
- [ ] Test 1-8 全部實作
- [ ] 所有 8 個測試使用 JWT auth
- [ ] 所有 8 個測試在真實 PostgreSQL 通過
- [ ] pytest tests/attendance/test_regression.py -v 結果記錄
- [ ] WORKSTREAM_STATUS_LEDGER.md 更新

---

#### WP-C1-05 — Tenant Isolation 在真實 PostgreSQL 驗證

**優先級：** P0
**狀態：** NOT_STARTED（現況：DummySession Mock，非真實 DB）
**預估工時：** 2-3 小時
**依賴：** WP-C1-04

**現況（SYSTEM_GROUND_TRUTH.md V-09）：**
test_tenant_isolation.py L20: class DummySession，L91: db = DummySession()。
全部 9 個 test function 使用 Mock，非真實 DB 驗證。

**Definition of Done：**
- [ ] test_tenant_isolation.py 改用真實 PostgreSQL session
- [ ] 全部 9 個 tenant isolation 測試通過
- [ ] 跨 company_id 資料存取確認被正確拒絕
- [ ] WORKSTREAM_STATUS_LEDGER.md 更新
- [ ] MODULE_STATUS_MATRIX.md tenant_isolation 欄位更新為 VERIFIED

---

#### WP-C1-06 — Feature Gate 套用至生產 Endpoint

**優先級：** P1
**狀態：** NOT_STARTED（現況：0 個生產 endpoint 套用）
**預估工時：** 2-4 小時
**依賴：** WP-C1-03

**現況（SYSTEM_GROUND_TRUTH.md V-04）：**
feature_gate_demo.py L27,65,111 有示範，但生產 endpoint 中呼叫數為 0。

| 模組 | Endpoint 數 | 現況 |
|------|------------|------|
| attendance/api.py | 10 | feature gate 呼叫數 = 0 |
| audit/api.py | 5 | feature gate 呼叫數 = 0 |
| backup/api.py | 2 | feature gate 呼叫數 = 0 |
| admin_location_api.py | 5 | feature gate 呼叫數 = 0 |

**Definition of Done：**
- [ ] 確認各 endpoint 對應的 feature flag 名稱（參照 core/features.py）
- [ ] 所有核心生產 endpoint 套用 require_enabled() 或等效 gate 檢查
- [ ] Feature Gate 在 tenant 無對應 entitlement 時正確回傳 403
- [ ] 測試新增 feature gate 關閉情境的測試案例
- [ ] WORKSTREAM_STATUS_LEDGER.md 更新
- [ ] MODULE_STATUS_MATRIX.md 各模組 feature_gate 欄位更新

---

#### WP-C1-07 — API 文件完整化

**優先級：** P1
**狀態：** NOT_STARTED
**預估工時：** 2-3 小時
**依賴：** WP-C1-06

**Definition of Done：**
- [ ] 所有模組 endpoint 有 OpenAPI/FastAPI schema 描述
- [ ] 錯誤碼（400 / 401 / 403 / 404 / 422）文件化
- [ ] API_DOCUMENTATION_v2.0.md 更新至最新狀態
- [ ] WORKSTREAM_STATUS_LEDGER.md 更新

---

### Phase 1 完成檢查點

| 條件 | 負責 WP | 狀態 |
|------|---------|------|
| 所有 API endpoint 使用 JWT 身份驗證 | WP-C1-02, WP-C1-03 | ⬜ |
| admin_location RBAC 實作 | WP-C1-02 範圍內 | ⬜ |
| 8 個回歸測試在真實 PostgreSQL 通過 | WP-C1-04 | ⬜ |
| Tenant Isolation 在真實 PostgreSQL 驗證 | WP-C1-05 | ⬜ |
| Feature Gate 套用至所有核心 API | WP-C1-06 | ⬜ |
| API 文件完整 | WP-C1-07 | ⬜ |

**Gate 5 宣告完成條件：Phase 1 全部條件達成**

---

### Phase 2 — Core Feature Completion

**目標：** 補完核心業務功能缺口。
**進入條件：** Phase 1 所有 WP 完成（Gate 5 宣告完成）

---

#### WP-C2-01 — Location Policy 擴展至所有打卡動作

**優先級：** P1
**狀態：** NOT_STARTED（現況：僅 break_out 有 location policy check）
**預估工時：** 2-4 小時
**依賴：** Phase 1 完成

**受影響動作（SYSTEM_GROUND_TRUTH.md V-05, V-06）：**

| 打卡動作 | Endpoint | Location Policy | 行號 |
|---------|----------|-----------------|------|
| punch_in | POST /v1/punch-in | 無 | L109 |
| punch_out | POST /v1/punch-out | 無 | L173 |
| break_in | POST /v1/break-in | 無 | L493 |
| break_out | POST /v1/break-out | 有（條件式） | L445-461 |

**Definition of Done：**
- [ ] punch_in 套用 check_location_policy()
- [ ] punch_out 套用 check_location_policy()
- [ ] break_in 套用 check_location_policy()
- [ ] break_out 條件式改為強制驗證
- [ ] 4 個打卡動作的 location policy 測試案例通過
- [ ] WP-11-13 Manual QA 可同步執行
- [ ] WORKSTREAM_STATUS_LEDGER.md 更新

---

#### WP-C2-02 — Reporting Backend 基礎建設

**優先級：** P1
**狀態：** NOT_STARTED
**預估工時：** 4-8 小時
**依賴：** WP-C2-01

**交付物：**
- reporting/ 模組結構（api.py / service.py / repo.py / schemas.py）
- 基礎報表 endpoint（出勤摘要、打卡歷史彙總）
- JWT auth + Feature Gate + 測試覆蓋

**Definition of Done：**
- [ ] reporting 模組基礎結構建立
- [ ] 至少 2 個報表查詢 endpoint
- [ ] JWT auth + Feature Gate 套用
- [ ] 測試在真實 DB 通過
- [ ] WORKSTREAM_STATUS_LEDGER.md 更新

---

### Phase 3 — Frontend Expansion

**目標：** 擴展前端功能，支援管理操作與報表展示。
**進入條件：** Phase 2 WP-C2-01 完成

**現況（SYSTEM_GROUND_TRUTH.md V-12）：**
目前有效前端路由僅 2 個（/ Home.vue，/login Login.vue）。
Admin UI、Reporting UI、Leave/Approval UI 均不存在。

---

#### Phase 3-A — Admin Dashboard

**目標：** 建立管理員總覽頁面（/admin 路由）。

**Definition of Done：**
- [ ] /admin 路由建立
- [ ] Admin Dashboard 元件實作
- [ ] 管理員身份驗證（非管理員導回首頁）
- [ ] 基本統計資料顯示

---

#### Phase 3-B — Admin Location Management

**目標：** 建立地點政策管理 UI（對應 admin_location_api.py 的 5 個 endpoint）。

**Definition of Done：**
- [ ] /admin/locations 路由建立
- [ ] 地點管理 CRUD UI 完整（新增/編輯/刪除）
- [ ] 前端 RBAC：非管理員無法存取
- [ ] 整合後端 admin_location API（JWT auth）

---

#### Phase 3-C — Reporting UI

**目標：** 建立報表展示介面（對應 WP-C2-02 後端）。

**Definition of Done：**
- [ ] /reports 路由建立
- [ ] 出勤統計圖表可顯示真實資料
- [ ] 日期範圍篩選正確運作
- [ ] Feature Gate 控制報表功能存取

---

#### Phase 3-D — Leave / Approval UI

**目標：** 建立請假申請與主管審核介面。

**Definition of Done：**
- [ ] /leave 路由（員工申請）
- [ ] /approvals 路由（主管審核）
- [ ] 請假申請流程完整
- [ ] 主管審核動作可執行

---

### Phase 4 — SaaS Platform Completion

**目標：** 完成 SaaS 多租戶平台的商業功能。
**進入條件：** Phase 3 核心功能穩定

---

#### Phase 4-A — Plan-based Feature Gates

依照訂閱方案（Basic / Pro / Enterprise）控制功能存取。
交付物：方案定義完整（core/features.py 擴展）、各功能與方案對應矩陣。

---

#### Phase 4-B — Tenant Limits

套用每個租戶的資源限制（員工數、位置數、資料保留期限）。
交付物：limits 強制執行、超出限制返回適當錯誤、管理介面顯示使用量。

---

#### Phase 4-C — Advanced Reporting

進階報表功能（跨部門、跨時段、自訂維度）。
交付物：跨月份報表、部門彙總、自訂欄位匯出。

---

#### Phase 4-D — Public API Documentation

對外公開的 API 文件（合作夥伴整合用）。
交付物：OpenAPI spec 完整輸出、開發者文件網頁、API 版本管理策略。

---

## 3. Module Completion Matrix

**權威來源：** docs/MODULE_STATUS_MATRIX.md（本矩陣為摘要視圖）

**狀態定義：**
- VERIFIED = 在真實 PostgreSQL 執行並確認正確
- CODE_COMPLETE = 程式碼存在，runtime 未驗證
- PARTIAL = 部分實作，有明確缺口
- MISSING = 完全缺失

### 當前狀態（截至 2026-03-11 基線）

| 模組 | Auth 狀態 | Feature Gate | 測試覆蓋 | 生產就緒 | 優先級 |
|------|----------|--------------|---------|---------|-------|
| attendance | PARTIAL Header JWT | MISSING | PARTIAL 1/8 | NO | P0 |
| audit | PARTIAL Header JWT | MISSING | CODE_COMPLETE SQLite | NO | P0 |
| backup | PARTIAL Header JWT | MISSING | CODE_COMPLETE SQLite | NO | P0 |
| notifications | PARTIAL Header JWT | MISSING | CODE_COMPLETE SQLite | NO | P0 |
| tenants | CODE_COMPLETE JWT | PARTIAL | CODE_COMPLETE 38 tests | NEAR | P1 |
| customer_service | CODE_COMPLETE JWT | MISSING | PARTIAL 0 tests | NEAR | P1 |
| auth | CODE_COMPLETE JWT | MISSING | CODE_COMPLETE | NEAR | P1 |
| admin_location | PARTIAL Header no-RBAC | MISSING | MISSING | NO | P0 |

### 目標狀態（Phase 1 完成後）

| 模組 | Auth 目標 | Feature Gate | 測試目標 | 生產就緒 |
|------|----------|--------------|---------|----------|
| attendance | VERIFIED JWT | VERIFIED | 8/8 回歸測試 PASS | OK |
| audit | VERIFIED JWT | VERIFIED | PostgreSQL tests PASS | OK |
| backup | VERIFIED JWT | VERIFIED | PostgreSQL tests PASS | OK |
| notifications | VERIFIED JWT | VERIFIED | PostgreSQL tests PASS | OK |
| tenants | VERIFIED JWT | VERIFIED | 38 tests PASS | OK |
| customer_service | VERIFIED JWT | VERIFIED | tests 新增並 PASS | OK |
| auth | VERIFIED | N/A | tests PASS | OK |
| admin_location | VERIFIED JWT RBAC | VERIFIED | tests 新增並 PASS | OK |

---

## 4. WP Execution Rules

Cursor 在執行每個 WP 時必須遵守以下規則：

### Rule 1 — 一次只執行一個 WP

不得同時開始多個 WP。當前 WP 未完成（Definition of Done 未全部達成）前，不得開始下一個 WP。

### Rule 2 — 完成後必須更新 WORKSTREAM_STATUS_LEDGER

每個 WP 完成後，必須在 docs/WORKSTREAM_STATUS_LEDGER.md 新增對應章節，記錄：
完成日期、Git Commit、已完成交付物、已驗證項目、未驗證項目、測試結果、下一步。

### Rule 3 — 完成後必須更新 MODULE_STATUS_MATRIX

若 WP 改變了某模組的 Auth / Feature Gate / 測試覆蓋 / 生產就緒狀態，
必須同步更新 docs/MODULE_STATUS_MATRIX.md 對應欄位。

### Rule 4 — 測試必須在標記 WP 完成前通過

不得在測試未通過的情況下將 WP 標記為完成。
若測試失敗，必須修正後重新執行，確認通過後才可更新狀態文件。

### Rule 5 — 不得跳過 Phase 順序

Phase 2 不得在 Phase 1 未完成前開始。
Phase 3 不得在 Phase 2 核心 WP 未完成前開始。
Phase 4 不得在 Phase 3 未完成前開始。

### Rule 6 — 遇到阻塞立即記錄

若 WP 執行中遇到阻塞，立即在 WORKSTREAM_STATUS_LEDGER.md 記錄阻塞原因，不得無聲失敗。

---

## 5. Definition of Done

一個 WP 被視為完成，必須同時滿足以下所有條件：

### 5.1 通用條件（所有 WP）

| 條件 | 說明 |
|------|------|
| 程式碼已實作 | 功能代碼已撰寫並可執行 |
| 測試已撰寫 | 針對新功能有對應測試案例 |
| 測試已通過 | pytest 執行結果為 PASS（非 SKIP、非 ERROR）|
| 帳本已更新 | WORKSTREAM_STATUS_LEDGER.md 新增本 WP 章節 |
| 矩陣已更新 | MODULE_STATUS_MATRIX.md 對應欄位已反映新狀態 |

### 5.2 Phase 1 特定條件

| WP | 額外條件 |
|----|----------|
| WP-C1-01 | alembic upgrade head 成功；table 列表正確 |
| WP-C1-02 | get_current_company_id 在 attendance 中完全移除 |
| WP-C1-03 | audit / backup / notifications 測試改用 PostgreSQL |
| WP-C1-04 | 8/8 回歸測試在真實 DB 通過 |
| WP-C1-05 | DummySession 完全移除，改用真實 PostgreSQL session |
| WP-C1-06 | 所有核心 endpoint 有 feature gate；403 行為已測試 |
| WP-C1-07 | API_DOCUMENTATION_v2.0.md 更新至最新 endpoint 狀態 |

### 5.3 不可接受的完成狀態

- 測試存在但未執行
- 測試使用 Mock DB（非真實 PostgreSQL）
- 狀態文件未更新
- 僅有程式碼但無測試
- 測試有部分 SKIP 但未說明原因

---

## 6. Risk Register

### R-01 — PostgreSQL 環境不可用（HIGH）

**影響：** WP-C1-01 無法完成，阻塞所有後續 WP
**緩解：** WP-C1-01 第一步即確認 PostgreSQL 可連線；若失敗立即記錄並升級

### R-02 — Migration Chain 執行失敗（MEDIUM）

**影響：** WP-C1-01 無法完成，需先修正 migration 錯誤
**緩解：** 逐一執行 migration 確認每一步成功；失敗時記錄具體 revision

### R-03 — Auth 遷移破壞現有測試（MEDIUM）

**影響：** WP-C1-02 / WP-C1-03 執行時測試大量失敗
**緩解：** 遷移前先備份測試檔；逐模組遷移並驗證

### R-04 — 回歸測試業務邏輯不明確（LOW）

**影響：** WP-C1-04 實作時不確定測試案例的正確預期行為
**緩解：** 參照 ATTENDANCE_REGRESSION_SPEC.md 確認規格

---

## 7. Document Governance

### 7.1 本文件更新規則

本文件僅在以下情況可修改：
1. WP 狀態變更（NOT_STARTED -> IN_PROGRESS -> COMPLETED）
2. 新增 WP 或調整 WP 順序（需說明原因）
3. 發現新的 P0 風險需要插入緊急 WP

每次修改必須更新文件頂部的最後更新日期。
不得在未完成驗收條件時將 WP 標記為 COMPLETED。

### 7.2 與其他文件的關係

| 文件 | 關係 | 說明 |
|------|------|------|
| SYSTEM_GROUND_TRUTH.md | 基礎依據 | 本計劃基於此文件的驗證基線制定 |
| WORKSTREAM_STATUS_LEDGER.md | 執行記錄 | 每完成一個 WP 必須更新 |
| MODULE_STATUS_MATRIX.md | 模組狀態 | 反映各模組最新狀態 |
| GATE_PROGRESS_TRACKER.md | Gate 進度 | Gate 5 完成條件追蹤 |
| NEXT_WP_TICKET.md | 下一步指引 | 始終指向本文件定義的下一個 WP |

### 7.3 衝突解決規則

若本文件與其他文件有衝突，以本文件為準。
例外：若 SYSTEM_GROUND_TRUTH.md 有新的 code scan 結果顯示本文件有誤，則優先修正本文件。

---

## 8. Current Status Summary

**文件建立日期：** 2026-03-11
**當前階段：** Phase 1 — Security Baseline Repair
**當前執行 WP：** 無（WP-C1-01 待開始）
**Gate 5 完成度估算：** 40%

### 技術債快照（2026-03-11 基線）

| 類型 | 數量 | 說明 |
|------|------|------|
| P0 安全風險 | 4 項 | Header auth x5 模組；admin_location 無 RBAC；回歸測試 1/8；tenant isolation Mock |
| Header auth endpoint 待遷移 | 24 個 | attendance(10)+audit(5)+backup(2)+notifications(1)+admin_location(5) |
| 回歸測試缺口 | 7/8 | Test 1-7 未實作 |
| Feature Gate 缺口 | 24 個 endpoint | 所有生產 endpoint 未套用 |
| Frontend 路由缺口 | 4 個 | Admin / Admin Location / Reports / Leave 均不存在 |

---

*本文件由系統驗證基線建立後生成（2026-03-11）。*
*權威依據：docs/SYSTEM_GROUND_TRUTH.md。*
