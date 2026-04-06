# P2_A2 Boundary Consistency Audit

> **Ticket Type**: Audit
> **Phase**: 2
> **Priority**: High
> **Execution Mode**: Read-only
> **Status**: Done
> **Audit Date**: 2026-04-06

---

# 1. Goal

比對 Attendance 各 endpoint 與查詢路徑的日期邊界是否一致，特別是：

- `breaks`
- `reporting`

之間是否存在不同的 business date ownership 規則。

本票只做一致性盤點，不修改任何 code。

---

# 2. Context

P2_A1 已先確認：
- `break-punches` 存在明確 HIGH 風險
- reporting 路徑偏向 timezone-aware / UTC-normalized
- 但 attendance 模組內沒有明確單一 `Asia/Taipei` business-date owner

P2_A2 要進一步回答：
- 這些路徑只是局部瑕疵，還是整體規則已經分岔？
- 不一致是發生在 API 層、helper 層、還是 query 層？
- 是否存在 duplicated boundary logic？
- 現況是否足以阻擋直接進 Fix？

---

# 3. Scope

## In Scope
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/api/reporting_helpers.py`
- `backend/app/modules/attendance/reporting_repo.py`
- `backend/app/modules/attendance/tests/test_reporting_sessions.py`
- `backend/app/modules/attendance/tests/test_reporting_user_summary.py`
- `backend/app/modules/attendance/tests/test_reporting_company_summary.py`
- `backend/app/modules/attendance/tests/test_punch_break_integration.py`
- `backend/app/modules/attendance/tests/test_break_out_enforcement.py`

## Out of Scope
- 修正 timezone helper
- 建立共用 boundary helper
- 直接提出 fix diff
- 非 attendance 模組的日期設計

---

# 4. Audit Method

本次比對重點如下：

1. `break-punches` 的日期歸屬規則
2. reporting sessions / summaries 的 range 規則
3. 是否存在同一資料在不同 endpoint 下落入不同日期
4. query 層與 API 層是否分別重複處理 boundary
5. 測試與實作是否一致

---

# 5. Executive Summary

## 5.1 核心結論
**breaks 與 reporting 不一致。**

而且這不是單純一個函式寫錯，而是：
- `reporting` 已形成一條相對一致的 boundary 鏈
- `break-punches` 使用另一套不同的 today ownership 規則

這表示 attendance 模組目前在 boundary 規則上已經**分岔**。

## 5.2 分岔位置
不一致主要發生在：
- **API 層**
- **helper / normalization ownership 層**

query 層本身反而相對一致：
- reporting repo 是單純接受 `start_utc/end_utc`
- break-punches 則在 API 層就先決定了 today boundary

## 5.3 最重要結論
### reporting 路徑
是：
- caller 構造 timezone-aware range
- API 驗證 aware datetime
- helper 統一轉 UTC
- repo 用 UTC boundary 過濾 `punch_in_time`

### break-punches 路徑
是：
- API 內直接用 `date.today()`
- 用 `datetime.combine(...)`
- 再用 `.replace(tzinfo=timezone.utc)` 生出查詢區間

這兩套設計不是同一規則。

---

# 6. Evidence

## 6.1 Breaks path
檔案：`backend/app/modules/attendance/api/breaks.py`

`GET /api/v1/attendance/break-punches`
的 today boundary 是：

- `today = date.today()`
- `start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)`
- `end_of_day = start_of_day + timedelta(days=1)`

再查：
- `AttendancePunch.punch_time >= start_of_day`
- `AttendancePunch.punch_time < end_of_day`

### 判定
這條路徑：
- 在 API 層直接決定 today ownership
- 沒有使用 Taipei-aware range builder
- 也沒有共享 reporting helper

因此它與 reporting 不是同一條 boundary 規則。

---

## 6.2 Reporting path
檔案：
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/api/reporting_helpers.py`
- `backend/app/modules/attendance/reporting_repo.py`

reporting 路徑的共同結構：

### API 層
- 接收 `start_date` / `end_date`
- `_validate_datetime_range(...)`：要求必須為 timezone-aware datetime
- `_normalize_to_utc(...)`：轉成 UTC

### repo 層
統一使用：
- `punch_in_time >= start_utc`
- `punch_in_time < end_utc`

### 判定
這條路徑的規則雖然沒有把 Taipei ownership 完整封裝在 attendance 模組內，
但它至少內部是**一致的**：
- aware datetime input
- API validator
- shared UTC normalization helper
- shared repo filtering convention

---

# 7. Consistency Comparison Table

| Dimension | Breaks (`/break-punches`) | Reporting (`/sessions`, `/reports/*`) | Consistent? |
|---|---|---|---|
| boundary owner | API route 自己決定 today | caller 提供 range，API/helper 正規化 | No |
| timezone source | `date.today()` + 假 UTC 午夜 | timezone-aware datetime input | No |
| normalization helper | 無 | `_normalize_to_utc(...)` | No |
| query boundary type | API 內現場組 `start_of_day/end_of_day` | shared `start_utc/end_utc` | No |
| query field | `AttendancePunch.punch_time` | `AttendanceSession.punch_in_time` | Partial only |
| boundary semantics | today by local date + UTC label | explicit range filtering | No |
| Taipei ownership evidence | 無 | 依賴 caller 傳入 Taipei range，測試有此使用方式 | Partial / asymmetric |
| automated tests | 未看到 boundary 測試 | 有 Taipei cross-midnight / cross-month 測試 | No |

---

# 8. Same Data, Different Ownership Risk

## 8.1 是否存在同一資料在不同 endpoint 下落入不同日期？
**有這個風險，而且是合理可預期的。**

原因：
- reporting 假設查詢區間可由 Taipei-aware range 提供
- break-punches 則自己用本地 `today` + UTC 午夜貼標

因此同一個位於台北業務日邊界附近的 punch / session，可能出現：
- reporting 視為屬於 Taipei 的某一天
- break-punches 卻依另一個邊界歸到別天或查不到

## 8.2 哪些情境最危險？
最危險的是：
- 台北凌晨 00:00～07:59 之間的資料
- 跨月最後一天 / 第一日
- UTC 前一日但 Taipei 已進入新業務日的資料

這些情境 reporting 的測試明確有考慮，
但 break-punches 沒看到相同等級的測試或相同的 boundary 邏輯。

---

# 9. Layer Responsibility Assessment

## 9.1 Breaks
### API 層
- 直接擁有 boundary 計算
- 直接把 today 決策寫死在 endpoint 中

### helper 層
- 無共享 normalization helper

### query 層
- 單純吃 API 算好的 start/end

### 判定
- boundary ownership 落在 API 層
- 且是孤立實作

---

## 9.2 Reporting
### API 層
- 收 aware datetime
- 驗證 naive/aware
- 呼叫 shared helper 做 UTC normalization

### helper 層
- `_validate_datetime_range(...)`
- `_normalize_to_utc(...)`

### query 層
- 統一使用 `start_utc/end_utc`
- 統一以 `punch_in_time` 作 filter

### 判定
- boundary responsibility 分散在 API + shared helper
- 雖然沒有明確 Taipei owner，但 reporting 內部邏輯相對收斂且一致

---

# 10. Duplicated / Divergent Logic Assessment

## 10.1 是否存在 duplicated boundary logic？
**有，但更準確地說是 divergent logic。**

不是同一套 helper 被重複實作，而是：
- reporting 有一套 shared normalization flow
- breaks 完全沒接這套 flow，自己在 route 裡重建一套 today 邊界

## 10.2 duplicated logic 是有意還是歷史遺留？
從目前形態看，比較像：
- **歷史遺留 / 演進不一致**

理由：
1. reporting 路徑已經抽出 helper 與 repo
2. break-punches 仍維持 route 內手寫 boundary
3. breaks 沒有對齊 reporting 的 shared normalization pattern
4. 測試覆蓋也明顯不對稱

---

# 11. Test Consistency Audit

## 11.1 Reporting tests
已看到明確 boundary 測試：

### `test_reporting_sessions.py`
- `SES-03 Taipei midnight ownership`
- `SES-04 cross-month ownership`

### `test_reporting_user_summary.py`
- `USR-03 cross-midnight session ownership`
- `USR-07 naive datetime rejection`

### `test_reporting_company_summary.py`
- `CMP-03 cross-midnight session ownership`
- `CMP-07 naive datetime rejection`

### 判定
reporting 的測試清楚表達：
- Taipei business-date ownership 是重要需求
- aware datetime 與跨午夜邊界有被測

---

## 11.2 Breaks tests
本次盤點看到的 break 相關測試：
- `test_punch_break_integration.py`
- `test_break_out_enforcement.py`

這些測試主要涵蓋：
- punch-out 與 break deduction integration
- location policy enforcement
- non-blocking audit behavior

**未看到**：
- `GET /api/v1/attendance/break-punches` 的 today boundary 測試
- Taipei midnight ownership 測試
- cross-midnight / cross-month break 歸屬測試
- 與 reporting 對照的一致性測試

### 判定
測試覆蓋明顯不一致：
- reporting 有 boundary 測試
- breaks 幾乎沒有 boundary 測試

這進一步支持「規則分岔且未被共同治理」的結論。

---

# 12. Findings

## Finding A — reporting internally consistent, breaks not aligned
- reporting 內部有 shared validation + normalization + repo filtering 鏈
- breaks 沒有接這條鏈
- 結論：**breaks 與 reporting 不一致**

## Finding B — inconsistency is primarily at API/helper ownership layer
- reporting 由 API + helper 共同處理 boundary
- breaks 直接在 endpoint 內硬編 today 邏輯
- 結論：**不一致主要發生在 API / helper 層**

## Finding C — query layer is not the main divergence point
- reporting repo 相對單純且一致
- breaks 的問題在 query 前 boundary 已經算錯
- 結論：**query 層不是主要分岔來源**

## Finding D — tests are asymmetric
- reporting 對 Taipei boundary 有明確測試
- breaks 缺少對等測試
- 結論：**測試與實作治理深度不一致**

---

# 13. Final Answers to Required Questions

## breaks 與 reporting 是否一致？
**不一致。**

reporting 使用：
- aware datetime input
- shared UTC normalization
- shared repo date-range filter

break-punches 使用：
- `date.today()`
- `datetime.combine(...)`
- `replace(tzinfo=timezone.utc)`

兩者不是同一套 boundary ownership 規則。

## 不一致是在 API 層還是 query 層發生？
**主要在 API 層與 helper ownership 層發生。**

- reporting：API + helper + repo 有一條鏈
- breaks：API route 自己決定 today boundary

repo/query 層不是主要問題點。

## 是否有資格進入 Phase 2 Gate？
**目前不建議直接進 Fix Gate。**

因為：
1. 規則已分岔
2. 至少一條 breaks 路徑明確錯誤
3. reporting 與 breaks 沒有共享 boundary owner
4. 測試覆蓋不對稱，容易修一邊漏一邊

---

# 14. Gate Recommendation

## 結論
- **Gate Recommendation: BLOCK**

## 理由
1. `break-punches` 與 reporting boundary 不一致
2. inconsistency 不只是一個 query 條件，而是 ownership 分岔
3. 若直接修一個 endpoint，很可能繼續維持分岔結構
4. 必須先定義：
   - 誰擁有 `Asia/Taipei` business date
   - 哪一層負責 Taipei date → UTC range normalization
   - breaks 與 reporting 是否應共享同一套 boundary contract

---

# 15. Recommended Next Step

在進入 Fix 前，應先建立一個小型 fix-spec / gate，至少回答：

1. `today` 是否一律解讀為 `Asia/Taipei` today
2. Taipei business date boundary 是否由 shared helper 擁有
3. break query 與 reporting query 是否採相同 boundary contract
4. 需要補哪些跨午夜一致性測試

在這些問題沒先定義前，直接修補 `break-punches` 雖然能止血，但仍不足以稱為 boundary consistency fix。
