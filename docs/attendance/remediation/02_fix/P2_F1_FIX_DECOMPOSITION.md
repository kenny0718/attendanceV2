# P2 F1 Fix Decomposition — Taipei Boundary Ownership First Cut

> **Document Type**: Fix Decomposition
> **Phase**: 2 — Taipei Business Date Boundary Alignment
> **Purpose**: Decompose Phase 2 into executable fix stages while preserving the Phase 2 boundary ownership contract
> **Execution Mode**: Planning / decomposition only
> **Status**: Draft for human review
> **Inputs**:
> - `docs/attendance/remediation/02_fix/P2_BOUNDARY_FIX_SPEC.md`
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

本文件的目的，是把 Phase 2 拆成可執行、可驗證、不可跳步的 fix 階段。

本文件只做 decomposition，不做任何實作。

本文件必須遵守已確立的 Phase 2 規格：
- `today / business date` 一律以 `Asia/Taipei` 為 owner
- boundary owner 必須集中在 normalization / helper layer
- `breaks` 與 `reporting` 必須共用同一 contract
- 第一刀不可先修 repo
- 第一刀不可直接修 scattered route logic

本文件**不得**：
- 修改任何 code
- 產出 diff
- 直接進入 F2 / F3 實作
- 整理 git / commit 訊息

---

# 1. Decomposition Objective

Phase 2 的真正修正目標，不是單點修補某個 query，而是：

1. 建立**唯一且明確**的 Taipei business-date normalization owner
2. 再讓 `breaks` 接入同一 contract
3. 再讓 `reporting` entry normalization 接入同一 contract
4. 最後以 consistency tests 封住 regression

因此本 Phase 應拆為：
- **F1 — 建立 normalization owner（pure/helper）**
- **F2 — breaks 接到同一 contract**
- **F3 — reporting entry normalization 接到同一 contract**
- **F4 — consistency tests / regression coverage**

---

# 2. Global Decomposition Rules

以下規則適用於 F1 ~ F4 全階段：

## 2.1 Mandatory sequencing
必須依序執行：
- F1 → F2 → F3 → F4

禁止：
- 跳過 F1 直接修 F2
- 在 F1 同時接 `breaks` + `reporting`
- 在 F2 順便修 F3
- 在 F3 順便做 schema 或 migration

## 2.2 Scope lock
每一階段只能處理該階段的 primary objective。

## 2.3 Ownership lock
- normalization owner 只能有一個語意來源
- repo 不可成為 owner
- route 不可各自擁有獨立 boundary 規則

## 2.4 Risk control
高風險檔案只能在對應階段以最小局部差異觸碰，不得在 decomposition 階段就擴張工作票範圍。

---

# 3. Stage Overview

## F1 — Define canonical Taipei boundary normalization owner
### Goal
在 non-repo pure/helper layer 建立單一 Taipei boundary normalization owner。

### Primary outcome
- 有一個明確的 pure/helper contract
- 可以把 Taipei `today` / `business date` 轉成 canonical UTC query boundary
- 尚未接入任何 route wiring

### Why first
因為問題根源在 ownership，不在 repo query shape。
若沒有先建立 owner，後續 F2 / F3 只會把不同 wiring 接到不同規則。

---

## F2 — Align breaks to the canonical boundary contract
### Goal
讓 `break-punches` 停止使用 route-local today 邏輯，改接 F1 定義的 canonical contract。

### Primary outcome
- breaks 不再用 `date.today()` + 假 UTC 午夜當 owner
- breaks 與 canonical boundary contract 對齊

### Why second
因為 `break-punches` 是當前最明確的 HIGH risk 路徑，且偏差點最集中。

---

## F3 — Align reporting entry normalization to the same contract
### Goal
讓 reporting entry normalization 的語意不再只是「accept aware datetime and convert to UTC」，而是明確收斂到 Taipei-owned boundary contract。

### Primary outcome
- reporting 的 entry normalization 語意與 F1 對齊
- 與 breaks 共用同一 boundary contract

### Why third
因為 reporting 目前內部雖相對一致，但 owner 仍然 ambiguous。
在 F2 修正 breaks 後，再收斂 reporting，風險較低且更容易驗證對齊。

---

## F4 — Add consistency tests and regression coverage
### Goal
補齊 breaks / reporting 共用 boundary contract 的驗收與 regression tests。

### Primary outcome
- Taipei midnight ownership 有對等測試
- cross-month ownership 有對等測試
- breaks vs reporting consistency 有直接證據
- naive datetime rejection（若適用）仍成立

### Why fourth
因為 F4 必須鎖定 F1~F3 已落地的 contract，否則容易測錯目標或重複改測。

---

# 4. Detailed Stage Specification

# 4.1 F1 — Define canonical Taipei boundary normalization owner

## Goal
建立一個單一、可測試、pure/helper 型的 Taipei boundary normalization owner。

它必須能表達：
- `today`
- `business date`
- Taipei local day boundary
- canonical UTC query range

但**不得**接入既有 `breaks` 或 `reporting` route。

## Allowed files
### Preferred / low-risk
- `backend/app/modules/attendance/api/reporting_helpers.py`
- 一個新的單一責任 boundary helper 檔案（若必要）
- 與 pure boundary owner 直接對應的新測試檔或純 helper 測試檔

### Conditionally allowed
- 其他 attendance 純 helper 類檔案，但前提是責任單一且不碰 DB / repo / route

## Forbidden files
### High-risk 暫禁動
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/main.py`
- `backend/app/modules/attendance/api/__init__.py`

### Also forbidden
- 任何 schema / migration 檔案
- 任何與 Phase 1 / Phase 3 相關的 engine / service 重構檔案

## Risk level
- **MEDIUM**

原因：
- 雖然不碰 route wiring，但會建立未來全 Phase 2 的 semantic owner
- 若 contract 定義錯誤，後續 F2 / F3 都會接錯

## Validation targets
F1 驗證目標必須只聚焦 pure contract：

1. Taipei `today` / business date 可以被一致解讀
2. 可以產出 canonical `start_utc` / `end_utc`
3. range shape 固定為：
   - `>= start_utc`
   - `< end_utc`
4. 不含 repo / DB / route dependency
5. 不改變既有 runtime 行為

## Rollback strategy
若 F1 contract 設計失敗，回滾方式必須是：
- 移除新建 helper / contract
- 回到 spec-only 狀態
- 不影響任何既有 route 或 repo

因為 F1 不應接線，所以 rollback 應非常局部。

## Explicit first-cut constraints
F1 必須明確遵守：
- **只能建立 normalization owner**
- **不可改 repo ownership**
- **不可同時修 breaks + reporting wiring**
- **不可碰 schema / migration**
- **不可把 arbitrary aware datetime 直接升格成合法 business-date owner**

---

# 4.2 F2 — Align breaks to the canonical boundary contract

## Goal
將 `GET /api/v1/attendance/break-punches` 接到 F1 建立的 canonical Taipei boundary contract。

## Allowed files
- `backend/app/modules/attendance/api/breaks.py`
- F1 建立的 boundary helper / normalization owner 檔案
- 與 `break-punches` boundary 直接相關的測試檔

## Forbidden files
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/reporting_repo.py`
- `backend/app/modules/attendance/service.py`
- 任何 schema / migration 檔

## Risk level
- **HIGH**

原因：
- 這是第一個把 canonical contract 接進 production route 的地方
- 直接影響使用者可見的今日 break 查詢

## Validation targets
1. `break-punches` 不再使用 `date.today()` 當 owner
2. 不再使用 `datetime.combine(...).replace(tzinfo=timezone.utc)` 假造 boundary
3. 改用 F1 的 canonical `start_utc` / `end_utc`
4. 台北凌晨 / 跨月 break 歸屬正確
5. 未引入 reporting side effect

## Rollback strategy
若 F2 接線造成風險：
- 只回滾 `breaks.py` 與其直屬 tests 的接線改動
- 保留 F1 owner contract
- 不回滾 reporting 任何部分

---

# 4.3 F3 — Align reporting entry normalization to the same contract

## Goal
讓 reporting entry normalization 收斂到 F1 所定義的 Taipei-owned contract。

## Allowed files
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/api/reporting_helpers.py`
- F1 建立的 boundary helper / normalization owner 檔案
- `backend/app/modules/attendance/reporting_repo.py`（僅在必要且最小差異前提下）
- reporting 相關測試檔

## Forbidden files
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/api/breaks.py`（除非僅為 shared import 修正，原則上不可再動）
- `backend/app/modules/attendance/service.py`
- 任何 schema / migration 檔

## Risk level
- **HIGH**

原因：
- reporting 涵蓋 sessions / user-summary / company-summary
- 涉及既有 datetime input contract 與共享 helper 語意

## Validation targets
1. reporting entry normalization 與 F1 contract 對齊
2. `breaks` 與 `reporting` 使用同一 boundary owner
3. naive datetime rejection（若原 contract 適用）仍成立
4. Taipei midnight / cross-month ownership 仍成立
5. repo query shape 維持穩定，或僅最小必要變動

## Rollback strategy
若 F3 導致 reporting regression：
- 只回滾 reporting entry normalization wiring
- 保留 F1 owner contract
- 保留 F2 breaks 對齊成果，除非已證明 contract 本身錯誤

---

# 4.4 F4 — Consistency tests and regression coverage

## Goal
建立完整的一致性驗收證據，使 Phase 2 修正可被治理與回歸測試保護。

## Allowed files
- `backend/app/modules/attendance/tests/test_reporting_sessions.py`
- `backend/app/modules/attendance/tests/test_reporting_user_summary.py`
- `backend/app/modules/attendance/tests/test_reporting_company_summary.py`
- `backend/app/modules/attendance/tests` 下與 `break-punches` boundary 直接相關的測試檔
- 與 F1 owner contract 直接相關的 pure tests

## Forbidden files
- runtime code files（除非為測試所需的最小 import/fixture 修補，原則上不應再動）
- schema / migration
- `repo.py`

## Risk level
- **MEDIUM**

原因：
- 主要是測試補齊
- 但若測試設計錯誤，會固化錯誤 contract

## Validation targets
1. Taipei midnight ownership
2. cross-month ownership
3. breaks vs reporting consistency
4. naive datetime rejection（若 endpoint contract 適用）
5. regression evidence 可直接支撐 Phase 2 completion proof

## Rollback strategy
若 F4 測試設計失敗：
- 只回滾新增或變更的測試
- 保留 F1~F3 runtime contract
- 重新以已確立 spec 重寫驗收測試

---

# 5. File Movement Control Matrix

## 5.1 Files that may move first
Phase 2 第一刀可先動的檔案，必須限制在 pure/helper owner 範圍：

- `backend/app/modules/attendance/api/reporting_helpers.py`
- 新增的單一責任 boundary helper 檔案（若必要）
- 與 pure boundary owner 直接對應的測試檔

## 5.2 High-risk temporarily locked files
以下檔案在 F1 階段屬高風險暫禁動：

- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/main.py`
- `backend/app/modules/attendance/api/__init__.py`

## 5.3 Files only unlock in later stages
### F2 才可解鎖
- `backend/app/modules/attendance/api/breaks.py`

### F3 才可解鎖
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/reporting_repo.py`（若必要）

### Still locked throughout Phase 2 unless separately audited
- `backend/app/modules/attendance/repo.py`
- `backend/app/main.py`
- `backend/app/modules/attendance/api/__init__.py`

---

# 6. Why F1 Must Stay Narrow

F1 必須刻意保持狹窄，原因如下：

1. audit 已證明問題核心在 owner layer
2. spec 已明定第一刀不可先修 repo
3. 若 F1 同時碰 `breaks` + `reporting`，將無法區分 contract 錯誤與 wiring 錯誤
4. 若 F1 就改 route，rollback 複雜度會提高
5. 只有先建立 pure owner，F2 / F3 才有共同依附點

因此 F1 的成功標準不是「功能看起來修好了」，而是：

- **Taipei boundary owner 已經存在**
- **contract 已可被重用**
- **但 runtime wiring 仍未改動**

---

# 7. Validation Strategy Across Stages

## 7.1 F1 validation
- pure helper contract tests
- no runtime wiring changes
- no repo changes

## 7.2 F2 validation
- `break-punches` Taipei ownership tests
- no reporting regression caused by breaks alignment

## 7.3 F3 validation
- reporting Taipei ownership tests
- naive datetime rejection remains valid where applicable
- no repo ownership drift

## 7.4 F4 validation
- direct consistency proof: breaks vs reporting
- cross-midnight / cross-month regression coverage

---

# 8. Rollback Principles

所有階段 rollback 都必須遵守：

1. 只回滾該階段引入的最小差異
2. 不把後續階段尚未依附的純 contract 一起誤刪
3. 若 owner contract 已被證明正確，優先回滾 wiring，不回滾 F1
4. 若 F1 contract 本身被證明錯誤，才允許回滾 owner layer

---

# 9. Gate Recommendation for Decomposition

## 9.1 Can Phase 2 proceed into F1?
**YES**

因為目前已具備：
- P2_A1 audit result
- P2_A2 consistency audit result
- P2 spec
- 明確 owner layer definition
- 明確 first-cut restrictions

## 9.2 Can Phase 2 skip directly to F2 or F3?
**NO**

因為：
- F2 / F3 都需要一個先存在的 canonical owner
- 若直接修 route，只會重新複製 ownership 分岔

## 9.3 Recommended immediate next action
下一步唯一合法動作應是：

- **執行 F1：建立單一 Taipei boundary normalization owner（pure/helper only）**

不是：
- 直接修 `breaks.py`
- 直接修 `reporting.py`
- 直接改 `repo.py`

---

# 10. Final Statement

本 decomposition 正式將 Phase 2 拆成四段：

- F1：建立 normalization owner
- F2：對齊 breaks
- F3：對齊 reporting
- F4：補 consistency tests

其中第一刀 F1 的邊界必須嚴格鎖定為：

- 只建立 owner
- 不接 route
- 不動 repo
- 不碰 schema
- 不同時處理 breaks + reporting wiring

在 F1 未完成前，任何直接修 `breaks` 或 `reporting` 的行為，都應視為違反本 decomposition 與 Phase 2 spec。
