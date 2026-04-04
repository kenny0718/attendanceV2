# P2_A1 Taipei Boundary Audit

> **Ticket Type**: Audit
> **Phase**: 2
> **Priority**: High
> **Execution Mode**: Read-only
> **Status**: Not Started

---

# 1. Goal

盤點 Attendance 模組所有以「today / current date / business date / date range」為核心的邏輯，確認是否一致遵守 `Asia/Taipei` 業務日規則。

---

# 2. Context

目前已知 `break-punches` 可能仍以 UTC 日期邊界處理，這會造成與 reporting 或使用者體感上的日期歸屬不一致。

本票目標是做**全面盤點**。

---

# 3. Scope

## In Scope
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/reporting_repo.py`
- 其他 attendance 內與 date boundary 直接相關的查詢實作
- 與 Taipei ownership 相關 tests

## Out of Scope
- canonical duration
- breaks layer 職責整理
- 修正 timezone code

---

# 4. Search Targets

必查項目：

1. `date.today()` / `datetime.utcnow()` / `timezone.utc` / Taipei tz 相關使用點
2. start/end of day 的計算方式
3. `today` 類 endpoint 的 business date ownership
4. report range normalization
5. 跨午夜與跨月查詢邏輯

---

# 5. Evidence Requirements

必須提供：

1. 所有 attendance 日期邊界處理點清單
2. 哪些點已符合 Taipei 規則
3. 哪些點仍以 UTC 假性業務日運作
4. 每個不一致點所屬 layer
5. 是否存在統一 normalization 責任層

---

# 6. Output File

輸出檔案固定為：
- `docs/attendance/remediation/01_audit/P2_A1_TAIPEI_BOUNDARY_AUDIT.md`

---

# 7. Prohibited Actions

禁止：
- 修改 timezone / datetime 程式碼
- 順便做 boundary helper 重構
- 把 reporting 與 breaks 一起直接修正

---

# 8. Audit Result

待執行。

執行完成後至少要回答：
- attendance 模組有哪些日期邊界處理點？
- 哪些不是 Taipei business date？
- 有沒有單一可治理的 normalization 層？

---

# 9. Risk Level

預設風險：HIGH

原因：日期歸屬錯誤會直接造成查詢結果與業務語意錯位。

---

# 10. Open Questions

1. reporting 與 breaks 是否共享同一個 business date 規則？
2. UTC-normalized query 是否被誤認為 Taipei business date？
3. 測試是否已覆蓋跨午夜情境？

---

# 11. Gate Recommendation

預設：`Gate Pending`

必須先完成全盤點，才可討論局部修正是否安全。
