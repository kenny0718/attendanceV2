# P2_A1 Taipei Boundary Audit

> **Ticket Type**: Audit
> **Phase**: 2
> **Priority**: High
> **Execution Mode**: Read-only
> **Status**: Done
> **Audit Date**: 2026-04-06

---

# 1. Goal

盤點 `attendance` 模組內所有與：
- `today`
- `date range`
- `business date`
- `break` 查詢
- `reporting` 查詢
- `session` 查詢

有關的日期邊界實作，判定其是否符合：

- **SA2.1：所有 today / date range / business date 必須以 `Asia/Taipei` 為準**

本次為**純盤點**，不修改任何 code。

---

# 2. Scope

## In Scope
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/api/punch.py`
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/api/reporting_helpers.py`
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/reporting_repo.py`
- `backend/app/modules/attendance/reporting_service.py`
- `backend/app/modules/attendance/api/break_deduction.py`

## Out of Scope
- 修正 timezone code
- 建立新的 boundary helper
- 調整 API contract
- 非 `attendance` 模組的日期設計

---

# 3. Search Targets Executed

本次實際盤點包含以下 pattern：

1. `date.today()`
2. `datetime.now()`
3. `utcnow`
4. `replace(tzinfo=timezone.utc)`
5. `datetime.combine`
6. `ZoneInfo("Asia/Taipei")`
7. `timezone.utc`
8. `astimezone(...)`
9. `business_day` / `business_date`
10. reporting / sessions / break 查詢入口

---

# 4. Executive Summary

## 4.1 結論
本次盤點結果：

- **存在 1 個明確 HIGH 風險點**
- **存在多個 MEDIUM 風險點**
- **沒有看到 attendance 模組內明確採用 `ZoneInfo("Asia/Taipei")` 的業務日 owner**
- **目前模組整體偏向「UTC-aware timestamp 系統」，但不是「Taipei business-date 系統」**

## 4.2 最重要發現
最明確的不符合 SA2.1 的地方在：
- `GET /api/v1/attendance/break-punches`

它用：
- `date.today()`
- `datetime.combine(...)`
- `.replace(tzinfo=timezone.utc)`

來決定「今天」的查詢區間。

這會把**伺服器本地 today** 與 **UTC 午夜** 混在一起，並直接拿來當業務日邊界，**不是 Taipei-aware business date**。

## 4.3 模組整體風格判定
可分成三類：

1. **UTC timestamp capture**
   - 例如 punch-in / punch-out / break-in / break-out 記錄當下時間
   - 這些通常不是業務日邊界問題本身

2. **UTC-normalized datetime range filtering**
   - reporting API 接受 timezone-aware datetime，然後轉成 UTC 查詢
   - 這在技術上可行，但**沒有明確保證業務日一定由 Taipei 擁有**

3. **pseudo-business-day logic using UTC midnight**
   - `break-punches` 屬於這一類
   - 這是本次盤點中最危險的點

---

# 5. Findings Inventory

以下逐點列出命中位置與判定。

## 5.1 HIGH — 直接用 UTC 當業務日

### A. `api/breaks.py` 的今日 break 查詢
檔案：`backend/app/modules/attendance/api/breaks.py`

命中：
- `date.today()`
- `datetime.combine(...)`
- `.replace(tzinfo=timezone.utc)`

邏輯摘要：
- 先取 `today = date.today()`
- 再做 `start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)`
- `end_of_day = start_of_day + timedelta(days=1)`
- 用這個 range 查 `AttendancePunch.punch_time`

問題：
- `date.today()` 取的是執行環境當地日期，不等於 Taipei business date owner
- `datetime.combine(today, midnight)` 生成 naive datetime
- `.replace(tzinfo=timezone.utc)` 只是**貼上 UTC 標籤**，不是時區轉換
- 如果需求是 Taipei 業務日，正確概念應是：
  - 先得到 `Asia/Taipei` 的當地日期
  - 建立 Taipei 午夜
  - 再換算成 UTC 查詢邊界

風險判定：
- **HIGH**

原因：
- 這一段是在做「today」查詢
- 直接決定 break punches 落在哪一天
- 會影響使用者看到的今日外出/返回記錄
- 若跨 UTC 日界但仍在台北同一業務日，結果可能錯誤

結論：
- **UTC-based，不符合 SA2.1**

---

## 5.2 MEDIUM — 未明確 timezone owner / ambiguous

### B. `api/reporting.py` 的 sessions / user-summary / company-summary
檔案：`backend/app/modules/attendance/api/reporting.py`

觀察：
- `start_date` / `end_date` 型別是 `datetime`
- 只要求 timezone-aware
- 呼叫 `_normalize_to_utc(...)` 後交給 repo
- 檔內註解寫到：
  - 「月份歸屬 = punch_in_time Asia/Taipei date」

實際情況：
- 這裡**沒有**看到 attendance 模組內部自行把「Taipei business date」轉成查詢邊界
- 它只是接收一個已帶時區的 datetime，然後轉成 UTC
- 如果 caller 傳的是 Taipei-aware range，結果可能正確
- 但如果 caller 傳的是其他 timezone-aware range，這層不會阻止

風險判定：
- **MEDIUM**

原因：
- 不是直接錯把 UTC 當業務日
- 但**也沒有明確由 attendance 模組擁有 Taipei business-date normalization**
- 註解宣稱 Taipei ownership，實作上卻是「依賴外部傳入正確的 timezone-aware datetime」

結論：
- **ambiguous**

---

### C. `api/reporting_helpers.py` 的 `_normalize_to_utc(...)`
檔案：`backend/app/modules/attendance/api/reporting_helpers.py`

觀察：
- `_normalize_to_utc(dt)` 只做 `dt.astimezone(timezone.utc)`
- `_validate_datetime_range(...)` 只檢查是否為 timezone-aware

問題本質：
- helper 負責的是「aware datetime → UTC」
- 不是「business date belongs to Asia/Taipei」
- 這代表 boundary ownership 沒有落在這一層

風險判定：
- **MEDIUM**

原因：
- helper 本身沒有錯
- 但不足以滿足 SA2.1
- 若上層沒有先用 Taipei 建立 business day boundary，這層會把任意 timezone-aware range 合法化

結論：
- **ambiguous**

---

### D. `reporting_repo.py` 的 date range filtering
檔案：`backend/app/modules/attendance/reporting_repo.py`

觀察：
- `get_sessions_for_reporting(...)`
- `count_sessions_for_reporting(...)`
- `get_user_summary_sessions(...)`
- `get_company_summary_sessions(...)`

都使用：
- `AttendanceSession.punch_in_time >= start_utc`
- `AttendanceSession.punch_in_time < end_utc`

判定：
- repo 層假設呼叫者提供的是正確 UTC boundary
- repo 不負責 business date ownership

風險判定：
- **MEDIUM**

原因：
- repo 實作本身乾淨一致
- 但它只承接 `start_utc/end_utc`
- 若上游沒有明確 Taipei normalization，整體仍然 ambiguous

結論：
- **ambiguous**

---

### E. `repo.py` 的 business date range query helper
檔案：`backend/app/modules/attendance/repo.py`

命中：
- `get_sessions_by_company_user_business_date_range(...)`
- `get_punches_by_company_user_business_date_range(...)`

觀察：
- 兩者都接受：
  - `business_day_start`
  - `business_day_end`
- 註解明寫：
  - business date → datetime range 的換算由 service 層決定
  - repo 不做業務推論

判定：
- 這代表目前 attendance 模組內還沒有在 repo 層落地 Taipei ownership
- 也表示「business date」概念目前只是參數命名，不是受保證的 Taipei-aware 型態

風險判定：
- **MEDIUM**

原因：
- 沒有直接做錯
- 但沒有把 `Asia/Taipei` 規則封裝在這裡
- 若上游 caller 用 UTC range 當 business date，repo 也會照單全收

結論：
- **ambiguous**

---

## 5.3 LOW — 已採 UTC-aware timestamp，但不是業務日計算

### F. `api/punch.py` 的 punch-in / punch-out / current-status
檔案：`backend/app/modules/attendance/api/punch.py`

命中：
- `datetime.now(timezone.utc)`

使用位置：
- punch-in 建立 `punch_in_time`
- punch-out 建立 `punch_out_time`
- current-status 計算 elapsed

判定：
- 這些是在記錄事件發生時間或算經過分鐘數
- **不是 today/business-date boundary 決定點**

風險判定：
- **LOW**

結論：
- **UTC-based，但不屬於本票主要違規點**

---

### G. `api/breaks.py` 的 break-out / break-in 寫入時間
檔案：`backend/app/modules/attendance/api/breaks.py`

命中：
- `request.punch_time or datetime.now(timezone.utc)`

判定：
- 這是事件時間戳記
- 不是 today/date-range 查詢邊界

風險判定：
- **LOW**

結論：
- **UTC-based，但不是業務日 ownership 問題本身**

---

### H. `repo.py` 的 `get_current_time()` / `close_session.updated_at`
檔案：`backend/app/modules/attendance/repo.py`

命中：
- `datetime.now(timezone.utc)`

判定：
- 這是系統更新時間戳
- 不屬於 business day calculation

風險判定：
- **LOW**

結論：
- **UTC-based，但不是違反 SA2.1 的核心點**

---

# 6. Required Topic-by-Topic Audit Result

依你指定的類別，逐項回答如下。

## 6.1 today 判斷

### 發現位置
- `backend/app/modules/attendance/api/breaks.py` 的 `get_break_punches()`

### 判定
- **UTC-based**

### 等級
- **HIGH**

### 原因
- 直接用 `date.today()` + `datetime.combine(...)` + `replace(tzinfo=timezone.utc)` 作為今日查詢邊界
- 不是 Taipei-aware business date

---

## 6.2 date range 計算

### 發現位置
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/api/reporting_helpers.py`
- `backend/app/modules/attendance/reporting_repo.py`
- `backend/app/modules/attendance/repo.py`（business_date_range helpers）

### 判定
- **ambiguous**

### 等級
- **MEDIUM**

### 原因
- 系統要求輸入 aware datetime，並一律轉成 UTC 查詢
- 但沒有明確在 attendance 模組內把「business date = Asia/Taipei」固化成標準轉換責任
- 換句話說：
  - 它能處理 timezone-aware range
  - 但沒有保證 range 的語意一定來自 Taipei 業務日

---

## 6.3 break 查詢

### 發現位置
- `backend/app/modules/attendance/api/breaks.py` 的 `get_break_punches()`
- `backend/app/modules/attendance/repo.py` 的 `get_punches_by_company_user_business_date_range(...)`

### 判定
- `get_break_punches()`：**UTC-based**
- `get_punches_by_company_user_business_date_range(...)`：**ambiguous**

### 等級
- `get_break_punches()`：**HIGH**
- business_date_range helper：**MEDIUM**

---

## 6.4 reporting 查詢

### 發現位置
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/api/reporting_helpers.py`
- `backend/app/modules/attendance/reporting_repo.py`

### 判定
- **ambiguous**

### 等級
- **MEDIUM**

### 原因
- reporting 路徑是「caller 提供 aware datetime → normalize to UTC → repo filter punch_in_time」
- 並沒有真正把 `Asia/Taipei` 業務日 ownership 收斂到單一 normalization 層

---

## 6.5 session 查詢

### 發現位置
- `backend/app/modules/attendance/api/punch.py` 的 `/history`
- `backend/app/modules/attendance/repo.py` 的 `get_sessions(...)` / `count_sessions(...)`
- `backend/app/modules/attendance/repo.py` 的 `get_sessions_by_company_user_business_date_range(...)`

### 判定
- `/history` 與 `get_sessions(...)`：**無業務日計算，非本票核心問題**
- `get_sessions_by_company_user_business_date_range(...)`：**ambiguous**

### 等級
- 一般 history/session list：**LOW / informational**
- business date range helper：**MEDIUM**

---

# 7. Classification Table

| Location | Use Case | Current Behavior | Classification | Risk |
|---|---|---|---|---|
| `api/breaks.py:get_break_punches()` | today break query | `date.today()` + UTC midnight tagging | UTC-based | HIGH |
| `api/reporting.py` | reporting date range entry | accepts aware datetime, normalize to UTC | ambiguous | MEDIUM |
| `api/reporting_helpers.py:_normalize_to_utc()` | datetime normalization | timezone-aware → UTC only | ambiguous | MEDIUM |
| `reporting_repo.py` | reporting repo filters | uses `start_utc/end_utc` directly | ambiguous | MEDIUM |
| `repo.py:get_sessions_by_company_user_business_date_range()` | session business-date query | caller-owned boundary | ambiguous | MEDIUM |
| `repo.py:get_punches_by_company_user_business_date_range()` | break/punch business-date query | caller-owned boundary | ambiguous | MEDIUM |
| `api/punch.py` punch-in/out/current-status | event timestamp / elapsed | `datetime.now(timezone.utc)` | UTC-based but not business-date logic | LOW |
| `api/breaks.py` break-in/out | event timestamp | `datetime.now(timezone.utc)` | UTC-based but not business-date logic | LOW |
| `repo.py:get_current_time()` | system update timestamp | `datetime.now(timezone.utc)` | UTC-based but not business-date logic | LOW |

---

# 8. Pattern Search Result Summary

## 8.1 `date.today()`
- 發現：`backend/app/modules/attendance/api/breaks.py`
- 判定：**HIGH**

## 8.2 `datetime.now()`
- 發現多處 `datetime.now(timezone.utc)`
- 主要用於事件時間戳記
- 判定：**多數 LOW，非業務日邊界本身**

## 8.3 `utcnow`
- 本次盤點範圍內**未見明確使用**

## 8.4 `replace(tzinfo=timezone.utc)`
- 發現：`backend/app/modules/attendance/api/breaks.py`
- 判定：**HIGH**

## 8.5 `datetime.combine`
- 發現：`backend/app/modules/attendance/api/breaks.py`
- 判定：**HIGH**

## 8.6 `ZoneInfo("Asia/Taipei")`
- 本次盤點範圍內**未見使用**

這一點本身就是重要信號：
- attendance 模組目前**沒有明確的 Taipei-aware business-date owner**

---

# 9. Core Assessment

## 9.1 是否存在 Taipei-aware business day owner？
**沒有明確看到。**

目前看到的只有：
- UTC-aware timestamp capture
- aware datetime → UTC normalization
- caller 傳入 boundary，repo 直接使用

但沒有看到一個明確層負責：
- 「今天」一定以 `Asia/Taipei` 決定
- business date 一定先轉為 Taipei midnight boundary
- 再換算成 UTC query range

## 9.2 是否存在直接用 UTC 當業務日？
**有。**

最清楚的例子就是：
- `api/breaks.py:get_break_punches()`

## 9.3 reporting 是否已符合 SA2.1？
**不能判定為已符合。**

理由：
- 它只要求 aware datetime
- 再轉成 UTC
- 沒有自己保證「業務日一定來自 Taipei」

因此目前較準確的結論是：
- **reporting 是 timezone-aware / UTC-normalized**
- **但不是明確 Taipei-owned**

---

# 10. Risk Analysis

## HIGH
- `break-punches` 今日查詢直接錯用 UTC 邊界
- 會直接造成今日 break 記錄歸屬錯誤
- 對使用者可見，且跨午夜最容易出錯

## MEDIUM
- reporting 與 business-date helpers 缺乏單一 Taipei normalization owner
- 會造成：
  - 規則散落於 caller
  - 註解與實作語意可能不一致
  - 未來修一處、漏一處的風險高

## LOW
- UTC-aware event timestamps 本身不是問題
- 只要後續業務日 ownership 明確，這些保留 UTC 很合理

---

# 11. Final Answers to Required Questions

## attendance 模組有哪些日期邊界處理點？
有，主要包括：
- `api/breaks.py:get_break_punches()` 的 today 查詢
- `api/reporting.py` 的 `start_date/end_date` 查詢入口
- `api/reporting_helpers.py` 的 UTC normalization
- `reporting_repo.py` 的 `start_utc/end_utc` 過濾
- `repo.py` 的 business_date_range 查詢 helper

## 哪些不是 Taipei business date？
明確不是的：
- `api/breaks.py:get_break_punches()`

無法證明已是 Taipei-owned、因此只能列為 ambiguous 的：
- reporting 全鏈路
- `repo.py` 的 business_date_range helpers

## 有沒有單一可治理的 normalization 層？
**目前沒有。**

目前最接近的點是：
- `api/reporting_helpers.py:_normalize_to_utc()`

但它只做「aware datetime → UTC」，
**不是**「Taipei business date → UTC query boundary」。

---

# 12. Gate Recommendation

## 結論
- **Gate Recommendation: BLOCK / NEED FIX PLAN**

## 原因
1. 已存在明確 HIGH 風險點：`break-punches` today boundary
2. reporting / business-date helpers 缺少明確 `Asia/Taipei` ownership
3. 若直接局部修正而不先定義 boundary owner，後續很容易產生新的分岔

---

# 13. Suggested Next Audit Linkage

本票完成後，下一步應銜接：
- `P2_A2_BOUNDARY_CONSISTENCY_AUDIT`

因為本票已證明：
- 至少有一處直接錯用 UTC
- 其餘多處則是 timezone-aware 但 owner 不明

下一票需要進一步確認：
- breaks 與 reporting 是否已經實際分岔
- boundary ownership 應落在哪一層
- 修正時是否能以單一 normalization 策略收斂
