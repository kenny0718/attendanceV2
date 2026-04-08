# P2 F2 Fix Spec — Align break-punches to Canonical Taipei Boundary Owner

> **Document Type**: Fix Specification
> **Phase**: 2 — Taipei Business Date Boundary Alignment
> **Ticket**: F2 — Align `break-punches` to the canonical Taipei boundary normalization owner
> **Purpose**: Define how `break-punches` should adopt the F1 Taipei business-date owner without changing reporting or repo ownership
> **Execution Mode**: Specification only
> **Status**: Draft for human review
> **Inputs**:
> - `docs/attendance/remediation/02_fix/P2_BOUNDARY_FIX_SPEC.md`
> - `docs/attendance/remediation/02_fix/P2_F1_FIX_DECOMPOSITION.md`
> - `docs/attendance/remediation/02_fix/P2_F1_EXECUTION_REPORT.md`
> - `backend/app/modules/attendance/api/breaks.py`
> - `backend/app/modules/attendance/api/reporting_helpers.py`
> **Last Updated**: 2026-04-06

---

# 0. Purpose

本文件的唯一目的，是為 Phase 2 / F2 定義一份正式修正規格，使：

- `GET /api/v1/attendance/break-punches`
- 不再使用 route-level UTC-based today boundary
- 改為依附 F1 已建立的 canonical Taipei boundary normalization owner

本文件只定義：
- F2 target
- 接線方式
- responsibility split
- 風險
- acceptance criteria
- prohibited actions

本文件**不得**：
- 修改任何 code
- 產出 diff
- 同時修 `reporting.py`
- 改動 repo ownership
- 處理 schema / migration

---

# 1. Background

依據 P2_A1 / P2_A2 與 P2 F1 execution result：

目前已知：

1. `break-punches` 仍使用 route-level `date.today()`
2. 仍使用 `datetime.combine(...)`
3. 仍使用 `.replace(tzinfo=timezone.utc)`
4. 以上做法已被判定為 HIGH risk 的 UTC-based pseudo-business-day logic
5. F1 已建立 canonical Taipei boundary owner，但尚未接入 runtime flow

因此 F2 的核心任務不是建立新規格，而是：

- 讓 `break-punches` **接到 F1 owner**
- 同時維持：
  - repo ownership 不變
  - reporting 尚不改動
  - query shape 不變

---

# 2. F2 Target Definition

## 2.1 Primary Target

F2 完成後，`break-punches` 必須滿足：

- 不再使用 `date.today()` 當 Attendance business day owner
- 不再使用 `datetime.combine(...) + replace(tzinfo=UTC)` 假造日界線
- 改以 F1 owner 輸出的：
  - `start_utc`
  - `end_utc`

作為唯一 query boundary

## 2.2 Semantic Target

F2 完成後，`break-punches` 中的 `today` 必須正式代表：

- **today in `Asia/Taipei`**

不是：
- server local date
- UTC date
- route-level ad hoc date calculation

## 2.3 Query Target

F2 完成後，`break-punches` 的查詢條件必須維持為：

- `AttendancePunch.punch_time >= start_utc`
- `AttendancePunch.punch_time < end_utc`

也就是：
- query shape 保留
- 只替換 boundary source

---

# 3. Wiring Strategy

## 3.1 Required Wiring Principle

F2 的接線原則必須是：

- `breaks.py` 只負責取用 boundary owner 的結果
- boundary 語意不得在 route 內自行重算

## 3.2 Recommended Wiring Point

建議接線位置：
- `backend/app/modules/attendance/api/breaks.py`
- `get_break_punches()` 內目前生成 `today/start_of_day/end_of_day` 的區塊

替換目標：
- 只替換 boundary source
- 不擴張 endpoint 其他責任

## 3.3 Should F2 Call the F1 Owner Directly or Through Wrapper?

建議判定如下：

### Preferred
- 可直接透過 existing helper module 使用 F1 owner

### Allowed alternative
- 若 `breaks.py` 需要一個極小型 wrapper / helper call 才能保持可讀性，該 wrapper 必須：
  - 只做 boundary owner 取用
  - 不新增第二套 owner 規則
  - 不混入 response shaping / query logic / actor logic

### Forbidden
- 不可建立 route-local duplicated today logic
- 不可在 `breaks.py` 內重新實作 Taipei date -> UTC range
- 不可繞開 F1 owner 再造一套 break 專用 boundary helper

## 3.4 API vs Helper Responsibility Split

### API Layer must do
- 取得目前需要的 `today` 語意
- 呼叫 F1 owner 或其極小型 wrapper
- 接收 `start_utc` / `end_utc`
- 使用既有 query shape 查詢 break punches
- 回傳既有 response shape

### Helper Layer must do
- 擁有 Taipei business-date owner
- 定義 today/business-date → canonical UTC boundary
- 保持 pure / deterministic

### API Layer must not do
- 不可自己決定 business-day owner
- 不可自己建立 Taipei boundary
- 不可自己實作 `today -> UTC range`

### Helper Layer must not do
- 不可做 DB query
- 不可組 response
- 不可處理 actor / permission

---

# 4. Risk Assessment

## 4.1 User-Visible Risk

F2 會直接影響：
- 使用者看到的「今日外出/返回記錄」

因此 F2 是 Phase 2 目前最明確的使用者可見修正。

## 4.2 Expected Behavior Change

F2 上線後，以下行為可能會改變：

### A. Today break display may change
原本落在：
- UTC 前一日
- 但其實屬於台北今日

的 break punch，可能會在 F2 後被正確顯示到台北今日。

### B. Taipei midnight boundary will change ownership
特別是台北：
- 00:00 ~ 07:59

這段在 UTC 邊界下最容易被錯分。

### C. Cross-day behavior will change
原本以 UTC-based today 處理的 break 記錄，在跨日情境下可能重新歸屬。

### D. Cross-month behavior will change
月末 / 月初附近的 break punch，將依 Taipei 月界線重新落位。

## 4.3 Why This Risk Is Acceptable

這些變化是：
- **預期中的修正性變化**
- 不是額外引入的新規則
- 而是將行為拉回已明確定義的 target contract

---

# 5. Scope and Boundaries

## 5.1 Allowed Future Change Scope for F2

F2 未來實作可觸及：
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/api/reporting_helpers.py`（若只為最小必要 helper exposure / import 使用）
- 與 `break-punches` boundary 直接相關的 tests

## 5.2 Forbidden Files for F2

F2 明確禁止修改：
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/reporting_repo.py`
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/main.py`
- `backend/app/modules/attendance/api/__init__.py`
- 任何 schema / migration 檔

## 5.3 Scope Lock

F2 只處理：
- `break-punches` boundary ownership 對齊

F2 不處理：
- reporting 對齊
- repo convergence
- Phase 3 breaks responsibility refactor
- API contract redesign

---

# 6. Acceptance Criteria

## 6.1 Boundary Source Acceptance

F2 完成後，必須能證明：

1. `break-punches` 不再使用 `date.today()`
2. 不再使用 `datetime.combine(...) + replace(tzinfo=timezone.utc)`
3. boundary source 來自 F1 canonical owner

## 6.2 Semantic Acceptance

F2 完成後，必須成立：

1. `break-punches` 中的 `today` 明確等於 `Asia/Taipei` today
2. Taipei midnight ownership 正確
3. cross-day ownership 依 Taipei boundary 判定
4. cross-month ownership 依 Taipei boundary 判定

## 6.3 Query Acceptance

F2 完成後，query shape 必須仍為：

- `>= start_utc`
- `< end_utc`

也就是：
- 不改 query shape
- 不改 repo ownership
- 不引入 punch_out_time / 其他欄位過濾邏輯

## 6.4 Isolation Acceptance

F2 完成後，必須能證明：

1. reporting 尚未被修改
2. reporting 既有 normalization 行為未被一起改動
3. repo 層未被觸碰
4. schema 未被修改

## 6.5 Required Test Acceptance

F2 未來實作至少必須補齊：

### A. Taipei midnight ownership
- 台北凌晨 break punch 應屬於正確 Taipei date
- 不得被落到 UTC 前一日

### B. Cross-month ownership
- 月末 / 月初 break punch 應依 Taipei 月界線歸屬

### C. No UTC-based today logic remains
- 測試或靜態證據需能證明 `break-punches` 已不再依賴舊邏輯

### D. Query shape unchanged
- 仍以 `>= start_utc, < end_utc` 查 `punch_time`

---

# 7. Non-Goals

F2 不是用來：

- 修 reporting
- 對齊 reporting entry normalization
- 修改 repo query contract
- 改 schema / migration
- 改 breaks API contract
- 做 breaks service/repo boundary convergence

這些都不屬於本票。

---

# 8. Prohibited Actions

本票未來實作時，明確禁止：

1. 修改 `reporting.py`
2. 修改 `reporting_repo.py`
3. 修改 `repo.py`
4. 同時修 reporting
5. 修改 schema / migration
6. 在 `breaks.py` 內重建第二套 Taipei boundary 規則
7. 直接把 query owner 下沉到 repo

---

# 9. Gate Recommendation

## 9.1 Can F2 proceed after F1?
**YES**

原因：
- F1 canonical owner 已建立
- F2 的 primary route 已明確
- 問題點集中且可控
- 不需要先改 repo 才能成立

## 9.2 Conditions for entering implementation
F2 進入實作前，必須再確認：

1. F1 helper 仍未被其他 runtime flow 非預期使用
2. `breaks.py` 目前待替換的 boundary block 唯一且可控
3. F2 的測試範圍已先界定為 break-specific boundary ownership
4. 不會藉 F2 順手打開 reporting 路徑

## 9.3 Recommended First Implementation Move

F2 未來實作的第一步，應該是：

- 只在 `breaks.py` 內替換 boundary source block
- 只把 `today/start_of_day/end_of_day` 改為依賴 F1 owner
- 其他 query、response、scope、limit 行為全部保持不變

---

# 10. Final Statement

本文件正式定義：

- F2 的目標不是修整整個 Attendance boundary system
- 而是讓 `break-punches` 從 route-level UTC today 邏輯
- 收斂到 F1 已建立的 canonical Taipei boundary owner

F2 完成後應達成：
- `break-punches` 不再使用舊的 UTC-based pseudo-business-day logic
- query shape 保持不變
- reporting 不受影響
- repo ownership 不改變
- Taipei midnight / cross-day / cross-month 的 break ownership 轉為正確語意
