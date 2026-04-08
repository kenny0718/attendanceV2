# P2 Boundary Fix Spec — Taipei Business-Date Boundary Alignment

> **Document Type**: Fix Specification
> **Phase**: 2 — Taipei Business Date Boundary Alignment
> **Purpose**: Define the unified target contract and ownership model for Taipei business-date boundaries before any implementation
> **Execution Mode**: Specification only
> **Status**: Draft for human review
> **Inputs**:
> - `docs/attendance/remediation/00_control/ATTENDANCE_REMEDIATION_GOVERNANCE_CONTROL.md`
> - `docs/attendance/remediation/01_audit/P2_A1_TAIPEI_BOUNDARY_AUDIT.md`
> - `docs/attendance/remediation/01_audit/P2_A2_BOUNDARY_CONSISTENCY_AUDIT.md`
> - `backend/app/modules/attendance/api/breaks.py`
> - `backend/app/modules/attendance/api/reporting.py`
> - `backend/app/modules/attendance/api/reporting_helpers.py`
> - `backend/app/modules/attendance/reporting_repo.py`
> - `backend/app/modules/attendance/repo.py`
> **Last Updated**: 2026-04-06

---

# 0. Purpose

本文件的唯一目的，是為 Phase 2 定義一份**正式、可治理、不可含糊**的 Taipei business-date boundary 統一規格。

本文件不是實作說明，也不是 diff 提案。

本文件只定義：
- target contract
- owner layer
- responsibility / non-responsibility
- allowed / forbidden fix scope
- acceptance criteria
- gate recommendation

本文件**不得**：
- 修改任何 code
- 直接修 `breaks.py` / `reporting.py`
- 順便處理 Phase 1 canonical 問題
- 順便處理 Phase 3 breaks boundary convergence 問題

---

# 1. Background and Problem Statement

依據已完成的 P2_A1 / P2_A2：

目前 Attendance 模組存在以下已確認事實：

1. `break-punches` 目前直接以 UTC-based today boundary 處理
2. `reporting` 與 `breaks` 已形成不同 boundary ownership
3. 問題主要位於 API / helper ownership 層
4. repo query layer 目前不是主要偏差來源
5. Phase 2 現況 Gate = BLOCK，不能直接進入實作

因此 Phase 2 的核心任務不是「修某一個 query」，而是：

- 先定義**統一 business-date contract**
- 再定義**唯一 boundary owner**
- 再決定 future fix 應落在哪一層

---

# 2. Target Contract Definition

## 2.1 Canonical Contract Statement

自 Phase 2 起，Attendance 模組內凡屬下列語意：
- `today`
- `current day`
- `business date`
- `date range ownership`
- 任何以日為單位的 attendance query boundary

**一律視為 `Asia/Taipei` 業務日語意，不得以 UTC calendar date 取代。**

這是本 Phase 的最高層 target contract。

## 2.2 Business-Date Owner

`Asia/Taipei` 必須被明確定義為 Attendance 模組的：

- **business-date owner**

這代表：
- 業務日的歸屬，不由伺服器 local date 決定
- 不由 UTC date 決定
- 不由各 endpoint 自行決定
- 不由 caller 任意傳入任意 timezone 來隱性決定

## 2.3 Meaning of "today"

在 Attendance 模組內，`today` 的正式語意應定義為：

- **the current calendar day in `Asia/Taipei`**

不是：
- server local date
- UTC date
- request arrival date in arbitrary timezone

## 2.4 Meaning of "business date"

`business date` 的正式語意應定義為：

- **a calendar date interpreted in `Asia/Taipei` timezone**

也就是：
- `2026-03-12` 不是抽象 date
- 它必須被解讀為 `Asia/Taipei` 的 `2026-03-12`

## 2.5 Meaning of "date range"

Attendance 內凡標記為 business-date query 的 date range，必須代表：

- **a UTC query range derived from a Taipei-owned business-day boundary**

亦即：
1. 先決定 Taipei business date / datetime boundary
2. 再換算成 UTC query range
3. repo 只吃最終 UTC boundary

---

# 3. Boundary Conversion Contract

## 3.1 Required Conversion Rule

若輸入是 business date 或 `today` 類語意，轉換流程必須是：

1. 以 `Asia/Taipei` 建立日界線
2. 取得 Taipei local start-of-day
3. 取得 Taipei local next-day start-of-day
4. 將這兩個 boundary 轉成 UTC
5. 以半開區間查詢：
   - `>= start_utc`
   - `< end_utc`

## 3.2 Canonical Query Boundary Shape

所有 Taipei business-date query boundary 必須採用同一個 canonical shape：

- `start_utc` = Taipei business-day start converted to UTC
- `end_utc` = next Taipei business-day start converted to UTC

Query contract 固定為：

- `timestamp >= start_utc`
- `timestamp < end_utc`

## 3.3 Prohibited Conversion Patterns

以下做法在 Phase 2 target contract 下**明確禁止**：

- `date.today()` 直接作為 Attendance business day owner
- `datetime.combine(...).replace(tzinfo=timezone.utc)` 來假造業務日起點
- 先做 naive datetime，再貼 `UTC` 標籤當成轉換
- 讓每個 endpoint 各自寫 `today` / `start_of_day` / `end_of_day`
- 讓 repo 自行推論 Taipei business date

## 3.4 Reporting Range Contract

對 reporting 類 endpoint：

若其 API contract 接收 datetime range，則正式規格應為：
- 該 range 必須代表 Taipei business-date ownership 所產生的合法邊界
- normalization layer 可負責把合法 boundary 轉成 UTC
- 但不得接受「任意 timezone-aware 即視為合法 business-date owner」的模糊語意

換句話說：
- `timezone-aware` 是技術條件
- `Taipei-owned business boundary` 是語意條件
- 兩者不可混為一談

---

# 4. Boundary Ownership Definition

## 4.1 Required Owner Layer

Phase 2 的正式規格要求：

- **Taipei business-date ownership 必須落在單一 normalization layer**
- **不可分散在 route / endpoint handler**

這個 owner layer 必須屬於：
- attendance 模組內的 non-repo normalization / helper boundary layer

## 4.2 Why the Owner Cannot Be Route-Level

不能讓每個 endpoint 自己算 today range，原因如下：

1. **規則分岔風險高**
   - `breaks` 與 `reporting` 已證明會分岔

2. **測試覆蓋不對稱**
   - 某些 route 可能有 Taipei boundary 測試，某些沒有

3. **語意無法集中治理**
   - 無法保證所有 `today` 都代表同一件事

4. **容易重複犯同型錯誤**
   - `date.today()`
   - `datetime.combine(...)`
   - `.replace(tzinfo=timezone.utc)`

5. **不利於 future audit**
   - 邊界規則散在 route，難以稽核

## 4.3 Breaks and Reporting Contract Unification

正式規格要求：

- `breaks` 與 `reporting` **必須共用同一 normalization contract**

這不一定表示它們必須呼叫同一個 function name，
但至少必須共享同一組規則：

- same business-date owner
- same Taipei boundary meaning
- same UTC range conversion semantics
- same half-open query shape

## 4.4 Owner Layer Responsibilities

owner layer 的責任應只有：

- 接受 Taipei business-date semantics 所需的最小輸入
- 產出 canonical UTC query boundary
- 提供清楚、可重用、可測試的 boundary normalization contract

owner layer **不應**：
- 直接存取 DB
- 直接跑 query
- 直接決定 response payload
- 混入 actor / permission 邏輯
- 混入 unrelated reporting aggregation

---

# 5. Responsibility / Non-Responsibility by Layer

## 5.1 API Layer

### API layer can do
- 接收 request input
- 驗證 request 是否符合 endpoint contract
- 將 business-date / today 類需求委派給 normalization layer
- 將 normalization 後的 UTC boundary 傳給 repo 或 service
- 回傳 response

### API layer cannot do
- 不可自定 business-date owner
- 不可自己計算 Taipei boundary
- 不可自己實作 `today -> UTC range` 規則
- 不可在多個 route 內重複硬編碼 boundary conversion

## 5.2 Helper / Normalization Layer

### Helper layer can do
- 擁有 Taipei business-date normalization contract
- 定義 `today` / business date / Taipei range 的統一轉換規則
- 輸出 canonical `start_utc` / `end_utc`
- 做與 boundary semantics 直接相關的最小驗證

### Helper layer cannot do
- 不可讀寫 DB
- 不可做 repo 存取
- 不可做 response shaping
- 不可承接 Phase 1 canonical duration semantics
- 不可承接 Phase 3 breaks service/repo boundary 收斂任務

## 5.3 Repo Query Layer

### Repo layer can do
- 接受已正規化完成的 `start_utc` / `end_utc`
- 用固定查詢型態執行 `>= start_utc` / `< end_utc`
- 保持 query field 與 tenant isolation 規則穩定

### Repo layer cannot do
- 不可自己推論 Taipei today
- 不可自己做 business date normalization
- 不可接受 ambiguous date 並自行解讀
- 不可成為 business-date owner

## 5.4 Service Layer

### Service layer can do
- 若某些 orchestration flow 需要 business-date boundary，可委派 normalization layer 取得 boundary
- 組合 API / helper / repo 之間的資料流

### Service layer cannot do
- 不可成為多頭 owner，與 helper 重複定義 boundary
- 不可另起一套 Taipei date conversion 規則

---

# 6. Scope Definition for Future Fix

## 6.1 Primary Fix Objective

此票未來的 fix scope，**只處理 boundary ownership 對齊**。

更精確地說：
- 只修 `today / business date / date range ownership`
- 只修 Taipei boundary semantics
- 只修 breaks / reporting 的規則一致性

## 6.2 Explicit Non-Goals

本票 future fix **不處理**：
- Phase 1 canonical duration semantics
- Phase 3 API / service / repo 全面責任收斂
- break deduction engine
- reporting aggregation logic
- front-end display timezone formatting
- 資料庫 schema 變更

## 6.3 Files Potentially Allowed in Future Fix

依治理控制文件，本 Phase 未來 fix 可優先考慮的檔案應限制在：

### P1 — Localized Change Only
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/api/reporting.py`

### P2 — Controlled Safe Change
- `backend/app/modules/attendance/api/reporting_helpers.py`
- `backend/app/modules/attendance/reporting_repo.py`
- 其他純 boundary helper 類輔助檔案（若需新增，必須責任單一）

### Test Files
- `backend/app/modules/attendance/tests/test_reporting_sessions.py`
- `backend/app/modules/attendance/tests/test_reporting_user_summary.py`
- `backend/app/modules/attendance/tests/test_reporting_company_summary.py`
- 與 `break-punches` boundary 直接相關的新測試或既有測試檔

## 6.4 Files Temporarily Forbidden for This Ticket

未來 fix 在本票範圍內，原則上**暫時禁止**主動觸及：

### P0 — Forbidden Direct Rewrite
- `backend/app/main.py`
- `backend/app/modules/attendance/api/__init__.py`
- `backend/app/modules/attendance/repo.py`

### Also Out of Scope for Phase 2 boundary ownership fix
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/api/punch.py`
- `backend/app/modules/attendance/work_hour_engine.py`
- Phase 3 以後才該治理的 breaks service/repo convergence 路徑

## 6.5 Why Repo Must Not Be the First Fix Target

本文件明確規定：
- **第一刀不可直接修 repo**

原因：
1. audit 已確認問題主要不在 repo query layer
2. repo 目前只承接 boundary，不應成為 owner
3. 若先改 repo，容易把 ownership 推錯層
4. `repo.py` 屬 P0 高風險核心檔，必須避免不必要觸碰

---

# 7. Acceptance Criteria

## 7.1 Contract Acceptance

未來 fix 完成後，必須能正式證明：

1. `today / current day / business date` 在 Attendance 模組內都明確代表 `Asia/Taipei`
2. Taipei business date 一律先轉成 canonical UTC query boundary
3. `breaks` 與 `reporting` 使用同一套 boundary ownership contract
4. repo query layer 不再自行承擔 business-date 推論

## 7.2 Behavior Acceptance

未來 fix 完成後，必須成立：

1. `break-punches` 不再使用 UTC-based 假性 today boundary
2. reporting 與 breaks 對同一 Taipei boundary 附近資料不會產生不同日期歸屬
3. half-open range semantics 一致：
   - `>= start_utc`
   - `< end_utc`

## 7.3 Required Test Coverage

未來 fix 必須至少補齊以下測試：

### A. Taipei midnight ownership
必須驗證：
- Taipei 凌晨資料屬於正確 Taipei date
- 不會被歸到 UTC 前一日

### B. Cross-month ownership
必須驗證：
- 跨月邊界資料的歸屬正確
- Taipei 月份歸屬不受 UTC 月界線誤導

### C. Breaks vs reporting consistency
必須驗證：
- 同一 business-date boundary 附近資料
- breaks query 與 reporting query 的 ownership 一致

### D. Naive datetime rejection（若 endpoint contract 適用）
必須驗證：
- 對接收 datetime range 的 endpoint
- naive datetime 仍被拒絕
- 且 rejection 與 business-date contract 不衝突

## 7.4 Negative Acceptance

未來 fix 完成後，以下情況必須不存在：

- `date.today()` 被直接當作 attendance business day owner
- `datetime.combine(...).replace(tzinfo=timezone.utc)` 被用來建立 business-day query range
- route-level duplicated today boundary logic
- reporting 與 breaks 各自擁有不同業務日語意

---

# 8. Prohibited Actions

本票在 spec 與 future fix 兩階段，都必須遵守以下禁止事項：

## 8.1 Spec Stage Prohibitions
- 不可修改任何 code
- 不可產出 diff
- 不可直接修 `breaks.py` / `reporting.py`
- 不可順便處理 Phase 1 或 Phase 3 問題

## 8.2 Future Fix Prohibitions
- 不可直接從 repo 層開始修
- 不可在多個 route 重複硬編 boundary 邏輯
- 不可把 arbitrary timezone-aware input 直接等同於合法 business-date owner
- 不可順便重構 reporting aggregation
- 不可順便做 breaks service/repo 全面收斂
- 不可引入與 boundary owner 無關的 schema / migration 變更

---

# 9. Gate Decision

## 9.1 Can Phase 2 enter Fix Decomposition?
**YES — but only into controlled fix decomposition, not direct code implementation.**

也就是：
- 可以進入 Phase 2 的 fix decomposition / first-cut planning
- **不可直接進入任意實作**
- 必須先依本 spec 把第一刀切到正確 owner layer

## 9.2 Why Gate Is No Longer Fully Blocked at Spec Level

在 P2_A1 / P2_A2 後，原本的 BLOCK 原因是：
- 缺少統一 target contract
- 缺少明確 owner layer
- breaks / reporting 已分岔但未定義收斂規格

本 spec 的存在，正是用來解除上述「規格缺位」的阻擋條件。

因此本階段可判定：
- **Audit completed**
- **Gate spec available**
- **May proceed to fix decomposition**

但仍不得跳過 decomposition 直接改碼。

---

# 10. First-Cut Fix Recommendation

## 10.1 First Cut Must Target Owner Layer

第一刀應先修：
- **helper / normalization owner layer**

不得先修：
- repo layer
- route-level scattered fixes

## 10.2 Why First Cut Must Not Start from Repo

理由如下：

1. repo 不是問題 owner
2. query 形狀目前大致正確
3. 真正要統一的是 business-date normalization contract
4. 若先改 repo，會把語意責任往下沉，違反本 spec

## 10.3 Recommended Decomposition Order

建議的未來拆分順序：

1. **F1 — Define canonical Taipei boundary normalization contract**
   - 只建立 owner layer 的 pure contract
   - 不改 route wiring

2. **F2 — Align break-punches to the canonical boundary contract**
   - 把最明確的 HIGH risk endpoint 接到正確 owner

3. **F3 — Align reporting entry normalization to the same contract**
   - 收斂 reporting 的 boundary ownership 語意
   - 維持 repo query contract 不變或最小變動

4. **F4 — Add consistency tests and regression coverage**
   - 補齊跨午夜 / 跨月 / breaks vs reporting consistency 驗收

這樣才能符合治理控制文件的：
- 小步
- 可驗證
- 不把 P0/P1 高風險檔一次打開太多

---

# 11. Final Statement

本文件正式定義：

- Attendance 模組內的 `today / business date / date range ownership`
- 必須一律以 `Asia/Taipei` 為 business-date owner
- Taipei business date 必須先經單一 normalization layer 轉成 canonical UTC query boundary
- `breaks` 與 `reporting` 必須共用同一 boundary contract
- repo query layer 不得成為 owner
- Phase 2 未來第一刀必須先落在 helper / normalization owner layer

在此規格未被後續 fix decomposition 明確承接前，
**不得直接對 `breaks.py` 或 `reporting.py` 做隨機 boundary 修補。**
