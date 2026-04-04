# P2_A2 Boundary Consistency Audit

> **Ticket Type**: Audit
> **Phase**: 2
> **Priority**: High
> **Execution Mode**: Read-only
> **Status**: Not Started

---

# 1. Goal

比對 Attendance 各 endpoint 與查詢路徑的日期邊界是否一致，特別是 `breaks` 與 `reporting` 之間是否存在不同 business date ownership 規則。

---

# 2. Context

P2_A1 先做全盤點；本票則進一步做**一致性比對**，確認不是單一錯點，而是整體規則是否分岔。

---

# 3. Scope

## In Scope
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/reporting_repo.py`
- 其他明確使用日期區間的 attendance endpoint

## Out of Scope
- 修正 timezone helper
- 非 attendance 模組的日期設計

---

# 4. Search Targets

必查項目：

1. `break-punches` 的日期歸屬規則
2. reporting sessions / summaries 的 range 規則
3. 是否存在同一資料在不同 endpoint 下落入不同日期
4. query 層與 API 層是否分別重複處理 boundary
5. 測試與實作是否一致

---

# 5. Evidence Requirements

必須提供：

1. 一致性比較表
2. breaks vs reporting 差異清單
3. 層級責任判定（API / repo / helper）
4. 是否存在 duplicated boundary logic
5. 若不一致，差異是否足以阻擋進 Gate

---

# 6. Output File

輸出檔案固定為：
- `docs/attendance/remediation/01_audit/P2_A2_BOUNDARY_CONSISTENCY_AUDIT.md`

---

# 7. Prohibited Actions

禁止：
- 直接修改 endpoint 行為
- 順手建立共用 boundary helper
- 將本票變成 Fix proposal

---

# 8. Audit Result

待執行。

執行完成後至少要回答：
- breaks 與 reporting 是否一致？
- 不一致是在 API 層還是 query 層發生？
- 是否有資格進入 Phase 2 Gate？

---

# 9. Risk Level

預設風險：HIGH

原因：若一致性不存在，局部修正會放大後續維護風險。

---

# 10. Open Questions

1. 是否存在看似一致、實際跨午夜失真的 query？
2. summary 與 raw list 是否使用不同 ownership 規則？
3. duplicated logic 是有意為之還是歷史遺留？

---

# 11. Gate Recommendation

預設：`Gate Pending`

若本票證明規則分岔，應優先阻擋直接進 Fix。
