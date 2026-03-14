# CURSOR EXECUTION ENTRY

**版本：** v1.0
**建立日期：** 2026-03-11
**基於：** SYSTEM_GROUND_TRUTH.md / DEVELOPMENT_MASTER_PLAN.md / ACCEPTANCE_TEST_PLAN.md
**性質：** Cursor 執行入口文件 — 每次開始工作前的唯一入口

---

## 1. Purpose

本文件是 Cursor 每次開始工作時的唯一執行入口。

**本文件的功能：**

- 固定每次工作開始前的讀檔順序
- 定義不可違反的執行規則
- 明確當前工作起點與完成條件
- 防止因舊記憶或對話內容誤導導致錯誤決策

**強制規定：**

- 不可跳過本文件直接開始改 code
- 不可只依賴舊的對話記憶或 session 摘要
- 不可參考 archive 目錄或標記為 Superseded 的文件
- 必須以 repo 內現行文件為唯一事實來源
- 每次新的 Cursor 對話開始，都必須重新執行本文件定義的讀檔流程

---

## 2. Required Read Order

每次開始工作前，必須依照以下順序讀取文件。不可跳過，不可顛倒順序。

| 順序 | 文件 | 用途 |
|------|------|------|
| 1 | docs/SYSTEM_GROUND_TRUTH.md | 系統真實現況基線（2026-03-11 code scan 驗證）|
| 2 | docs/DEVELOPMENT_MASTER_PLAN.md | 官方開發序列與 WP 定義（Single Source of Truth）|
| 3 | docs/ACCEPTANCE_TEST_PLAN.md | 每個 WP 的驗收測試標準與執行程序 |
| 4 | docs/NEXT_WP_TICKET.md | 當前應執行的工作包與起點 |
| 5 | docs/WORKSTREAM_STATUS_LEDGER.md | 歷史執行記錄（已完成 WP 的狀態帳本）|
| 6 | docs/MODULE_STATUS_MATRIX.md | 各模組目前的 Auth / Feature Gate / 測試 / 完成度狀態 |
| 7 | docs/GATE_PROGRESS_TRACKER.md | Gate 5 層級進度與完成條件追蹤 |

**各文件說明：**

**docs/SYSTEM_GROUND_TRUTH.md**
系統現況的唯一權威基線。基於 2026-03-11 的直接 code scan 驗證，不是估計或文件描述。
包含：Auth 機制確認、RBAC 缺口、Feature Gate 狀態、Migration chain、測試覆蓋現況、P0/P1 風險矩陣。
任何與本文件衝突的舊報告，一律以本文件為準。

**docs/DEVELOPMENT_MASTER_PLAN.md**
官方開發序列控制文件。定義 Phase 1-4、所有 WP 的執行順序、依賴關係、Definition of Done。
這是開發決策的最終依據，不得因為任何理由跳過或違反其定義的順序。

**docs/ACCEPTANCE_TEST_PLAN.md**
每個 WP 完成後的驗收測試標準。定義了環境驗證、Auth 驗證、回歸測試、Tenant Isolation 測試的具體步驟。
所有測試必須在真實 PostgreSQL 執行，不得使用 Mock DB 或 SQLite。

**docs/NEXT_WP_TICKET.md**
當前應執行的 WP 說明、阻塞狀態、執行步驟。每次開始工作前必讀，確認當前起點。

**docs/WORKSTREAM_STATUS_LEDGER.md**
所有已完成 WP 的執行記錄帳本。記錄完成日期、git commit、已驗證項目、未驗證項目、測試結果。
每完成一個 WP 必須更新本文件。

**docs/MODULE_STATUS_MATRIX.md**
各模組的 Auth 方式、Feature Gate 套用、測試覆蓋、完成度的矩陣狀態。
每完成一個影響模組狀態的 WP 必須更新本文件。

**docs/GATE_PROGRESS_TRACKER.md**
Gate 5 的完成條件清單與各 WP 進度狀態追蹤。

---

## 3. Execution Rules

以下規則為強制性規定，不得以任何理由違反或例外處理。

### Rule 1 — 一次只執行一個 WP

不得同時進行多個 WP。
當前 WP 的 Definition of Done 全部達成前，不得開始下一個 WP。
不得「順手」開始下一個 WP，即使看起來很簡單。

### Rule 2 — 不得跳 Phase / 不得跳順序

必須遵守 DEVELOPMENT_MASTER_PLAN.md 定義的 Phase 與 WP 執行順序。
Phase 2 不得在 Phase 1 未完成前開始。
Phase 3 不得在 Phase 2 核心 WP 未完成前開始。
不得因為「某個功能看起來更重要」而跳過安全修正類 WP。

### Rule 3 — 改 code 前必須先回報執行計畫

在任何正式修改程式碼之前，必須先輸出 Pre-Execution Report（格式見第 4 章）。
Pre-Execution Report 必須明確說明：
- 本次執行的 WP 是什麼
- 預計修改哪些檔案
- 預計執行哪些測試
- 完成後會更新哪些文件

### Rule 4 — 測試未通過不得標記完成

不得在以下情況下將 WP 標記為完成：
- 測試失敗（FAIL）
- 測試未執行（僅 code scan 或 code review）
- 測試使用 Mock DB 或 SQLite（需真實 PostgreSQL）
- 測試有 SKIP 但未說明原因

### Rule 5 — 完成後必須更新文件

每完成一個 WP，以下文件必須更新：
- docs/WORKSTREAM_STATUS_LEDGER.md（必須）
- docs/MODULE_STATUS_MATRIX.md（若模組狀態有變動）
視情況更新：
- docs/GATE_PROGRESS_TRACKER.md（若影響 Gate 條件）
- docs/NEXT_WP_TICKET.md（更新為下一個 WP）

### Rule 6 — 遇到阻塞必須記錄

若遇到以下情況，不得靜默跳過，必須立即記錄至 WORKSTREAM_STATUS_LEDGER.md：
- DB 無法連線
- Migration 執行失敗
- 測試持續失敗且無法解決
- 依賴項目缺失
- 環境配置問題
阻塞記錄必須包含：阻塞原因、嘗試過的解法、當前狀態。

### Rule 7 — 不得以文件存在視為功能完成

以下四項必須分開判定，不得互相替代：
- 規格文件存在 ≠ 程式碼完成
- 程式碼存在 ≠ 測試通過
- 測試存在 ≠ 測試在真實 DB 通過
- 文件更新 ≠ 功能完成

狀態標籤必須使用第 6 章定義的分類，不得使用模糊描述。

### Rule 8 — 不得自動擴大範圍

只完成當前 WP 定義的範圍。
不得在執行當前 WP 時順手修改其他模組、補充其他功能、重構不相關的程式碼。
若發現其他問題，記錄至 WORKSTREAM_STATUS_LEDGER.md，留待對應 WP 處理。
---

## 4. Required Pre-Execution Output

每次開始正式開發前，必須先輸出以下格式的 Pre-Execution Report。
在此報告輸出並確認無誤之前，不可開始修改任何程式碼。

```
## Pre-Execution Report

**Current WP:** WP-[ID] — [名稱]
**Phase:** Phase [N] — [Phase 名稱]
**Objective:** [本 WP 的目標一句話說明]

**Files to Read:**
- docs/SYSTEM_GROUND_TRUTH.md（確認現況）
- docs/DEVELOPMENT_MASTER_PLAN.md（確認 WP 定義）
- docs/ACCEPTANCE_TEST_PLAN.md（確認驗收標準）
- [其他本 WP 需要閱讀的檔案]

**Files to Modify:**
- [列出預計修改的程式碼檔案，含路徑]

**Tests to Run:**
- [列出完成後需執行的測試指令]

**Files to Update After Completion:**
- docs/WORKSTREAM_STATUS_LEDGER.md（必須）
- docs/MODULE_STATUS_MATRIX.md（若模組狀態變動）
- docs/GATE_PROGRESS_TRACKER.md（若影響 Gate 條件）
- docs/NEXT_WP_TICKET.md（更新為下一個 WP）

**Conflict Check:**
- NEXT_WP_TICKET.md 與 DEVELOPMENT_MASTER_PLAN.md 一致：[YES / NO，若 NO 說明差異]
```

**特別規定：**

若讀檔後發現 NEXT_WP_TICKET.md 與 DEVELOPMENT_MASTER_PLAN.md 有衝突，
必須先回報衝突內容，由人工確認後再繼續，不得自行判斷並推進。

---

## 5. Completion Rules

一個 WP 必須同時滿足以下所有條件，才可被標記為完成：

| 條件 | 說明 |
|------|------|
| 程式碼已實作 | 功能代碼已撰寫，語法無錯誤，可執行 |
| 測試已撰寫 | 針對新功能有對應的測試案例 |
| 測試已執行 | pytest 實際執行，非僅 code review |
| 測試已通過 | 結果為 PASS，不含未說明原因的 SKIP 或 FAIL |
| DB 環境正確 | 測試在真實 PostgreSQL 執行，非 Mock / SQLite |
| Ledger 已更新 | WORKSTREAM_STATUS_LEDGER.md 新增本 WP 章節 |
| Matrix 已更新 | MODULE_STATUS_MATRIX.md 對應欄位反映新狀態 |
| 下一步已記錄 | Ledger 章節包含後續行動或下一個 WP 資訊 |

**特別警告 — 以下情況不算完成：**

- 只有程式碼完成 ≠ WP 完成
- 只有測試檔案存在 ≠ WP 完成
- 只有文件更新 ≠ WP 完成
- 測試在 SQLite / Mock 通過 ≠ WP 完成
- 測試有 SKIP 且無說明 ≠ WP 完成

若狀態影響 Gate 5 完成條件或下一個 WP 的啟動條件，
必須同步更新 GATE_PROGRESS_TRACKER.md 與 NEXT_WP_TICKET.md。

---

## 6. Status Classification Rules

以下狀態標籤為唯一允許使用的分類，不得混用或自創其他標籤。

| 狀態 | 定義 | 使用時機 |
|------|------|----------|
| NOT_STARTED | 完全尚未開始 | WP 尚未進入執行 |
| IN_PROGRESS | 正在進行中 | WP 已開始但未達 Definition of Done |
| DOC_COMPLETE | 規格文件存在，程式碼未完成或未驗證 | 僅有文件，無對應實作 |
| CODE_COMPLETE | 程式碼已實作，但未在真實環境執行驗證 | 代碼存在，runtime 未確認 |
| VERIFIED | 已在真實 PostgreSQL 環境執行並確認正確 | 測試通過 + runtime 確認 |
| BLOCKED | 有明確阻塞原因，無法繼續 | 環境問題、依賴缺失、測試持續失敗 |

**使用規則：**

- CODE_COMPLETE 不等於 VERIFIED
- VERIFIED 必須有具體的 pytest 結果記錄作為依據
- BLOCKED 必須記錄阻塞原因，不得無說明
- DOC_COMPLETE 僅適用於「有規格但無代碼」的情況

---

## 7. Work Execution Flow

每次工作的標準流程，必須依序執行，不得跳步。

```
Step 1 — 讀取 Required Read Order
  依照第 2 章順序，讀取 7 份核心文件。
  確認無衝突後才可繼續。

Step 2 — 確認當前 WP
  從 NEXT_WP_TICKET.md 確認當前應執行的 WP。
  與 DEVELOPMENT_MASTER_PLAN.md 核對一致性。
  若有衝突，先回報衝突，等待人工確認。

Step 3 — 輸出 Pre-Execution Report
  使用第 4 章模板輸出報告。
  列出本次要讀的檔案、要修改的檔案、要執行的測試、要更新的文件。
  確認無誤後才開始修改程式碼。

Step 4 — 執行當前 WP
  按照 DEVELOPMENT_MASTER_PLAN.md 中 WP 的定義範圍執行。
  不得擴大範圍，不得順手修改其他模組。
  遇到問題立即記錄，不得靜默跳過。

Step 5 — 執行測試
  執行 ACCEPTANCE_TEST_PLAN.md 中對應 WP 的驗收測試。
  必須在真實 PostgreSQL 環境執行。
  記錄 pytest 結果（通過數 / 總數）。

Step 6 — 更新文件
  更新 WORKSTREAM_STATUS_LEDGER.md（必須）。
  更新 MODULE_STATUS_MATRIX.md（若狀態有變）。
  視情況更新 GATE_PROGRESS_TRACKER.md 與 NEXT_WP_TICKET.md。

Step 7 — 回報完成或阻塞狀態
  若所有 Definition of Done 達成：回報 WP 完成，列出通過的測試數。
  若有阻塞：回報阻塞原因、已嘗試的解法、當前狀態，等待指示。
```
---

## 8. Current Starting Point

以下資訊基於 SYSTEM_GROUND_TRUTH.md（2026-03-11）、DEVELOPMENT_MASTER_PLAN.md、NEXT_WP_TICKET.md。

| 項目 | 值 |
|------|-----|
| 當前 Phase | Phase 1 — Security Baseline Repair |
| 當前建議 WP | WP-C1-01 — PostgreSQL 執行環境驗證 |
| Gate 5 估計完成度 | 40% |
| P0 技術債 | 4 項（見下表）|

**4 項 P0 技術債（截至 2026-03-11）：**

| P0 ID | 描述 | 來源 |
|-------|------|------|
| P0-1 | attendance / audit / notifications / backup / admin_location 共 24 個 endpoint 使用 Header auth，非 JWT | SYSTEM_GROUND_TRUTH.md 1.2 |
| P0-2 | admin_location_api.py 3 個寫入 endpoint 完全無 RBAC（# TODO）| SYSTEM_GROUND_TRUTH.md 2.1 |
| P0-3 | 8 個回歸測試只有 Test 8 骨架，Test 1-7 未實作，0/8 在真實 DB 通過 | SYSTEM_GROUND_TRUTH.md V-08 |
| P0-4 | test_tenant_isolation.py 使用 DummySession，非真實 PostgreSQL 驗證 | SYSTEM_GROUND_TRUTH.md V-09 |

**WP-C1-01 說明：**

WP-C1-01 是所有後續工作的基礎。目標是建立真實 PostgreSQL 執行環境並確認 Migration chain 可正確執行至 HEAD（008_wp_11_13）。
本 WP 不修改任何程式碼，只執行環境設定與驗證，風險極低，預估 30-60 分鐘可完成。

**在 WP-C1-01 完成前，不得開始以下工作：**

- JWT auth 遷移（WP-C1-02）
- 回歸測試實作（WP-C1-04）
- 任何新功能開發（Phase 2 / Phase 3）

**WP-C1-01 Definition of Done（快速參考）：**

- [ ] alembic upgrade head 執行成功，無錯誤
- [ ] alembic heads 只顯示一個 head（008_wp_11_13）
- [ ] 確認所有 table 建立（最少 15 個）
- [ ] test_business_invariant.py 執行並記錄通過率
- [ ] test_model_constraints.py 執行並記錄通過率
- [ ] WORKSTREAM_STATUS_LEDGER.md 更新

---

## 9. Document Authority Hierarchy

當文件之間有衝突時，依照以下優先序決定以哪份文件為準：

```
1. docs/SYSTEM_GROUND_TRUTH.md         （code scan 實際驗證結果，最高優先）
2. docs/DEVELOPMENT_MASTER_PLAN.md     （官方開發序列，第二優先）
3. docs/MODULE_STATUS_MATRIX.md        （模組狀態，第三優先）
4. docs/ACCEPTANCE_TEST_PLAN.md        （驗收標準）
5. docs/GATE_PROGRESS_TRACKER.md       （Gate 進度）
6. docs/NEXT_WP_TICKET.md              （當前工作指引）
7. docs/WORKSTREAM_STATUS_LEDGER.md    （執行記錄）
8. 其他 docs/ 文件
9. archive/ 目錄（僅供歷史參考，不作為開發依據）
```

**已知文件不一致（截至 2026-03-11）：**

| 文件 | 問題 | 正確來源 |
|------|------|----------|
| SYSTEM_DEVELOPMENT_STATUS_REPORT.md | backup 模組 auth 方式誤標為 JWT，實際為 Header | MODULE_STATUS_MATRIX.md |
| REALITY_AUDIT_STATUS_INVENTORY.md | 未含 migration 006/007/008，已過期 | SYSTEM_GROUND_TRUTH.md |
| SA_REALITY_GAP_REPORT.md | 未反映 WP-11-13 實作，已過期 | SYSTEM_GROUND_TRUTH.md |

---

## 10. Quick Reference — Phase 1 WP Sequence

```
WP-C1-01  PostgreSQL 環境建立 + Migration 驗證      [當前 WP — 建議立即執行]
   |
WP-C1-02  Attendance 模組 JWT Auth 遷移 + RBAC      [依賴 C1-01]
   |
WP-C1-03  Audit / Backup / Notifications Auth 遷移  [依賴 C1-02]
   |
WP-C1-04  8 個回歸測試實作（真實 DB）               [依賴 C1-02]
   |
WP-C1-05  Tenant Isolation 真實 DB 驗證             [依賴 C1-04]
   |
WP-C1-06  Feature Gate 套用至所有生產 Endpoint      [依賴 C1-03]
   |
WP-C1-07  API 文件完整化                            [依賴 C1-06]
   |
[Phase 1 Complete — Gate 5 宣告完成]
   |
WP-C2-01  Location Policy 擴展至所有打卡動作
   |
WP-C2-02  Reporting Backend 基礎建設
```

---

**END OF CURSOR_EXECUTION_ENTRY.md**
**版本：** v1.0
**建立日期：** 2026-03-11
**下次更新觸發條件：** WP-C1-01 完成後，更新第 8 章「Current Starting Point」
