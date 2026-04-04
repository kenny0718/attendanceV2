# P3_A2 Breaks DB Write Audit

> **Ticket Type**: Audit
> **Phase**: 3
> **Priority**: Medium-High
> **Execution Mode**: Read-only
> **Status**: Not Started

---

# 1. Goal

定位 breaks 相關資料寫入與 commit 路徑，確認寫入責任是否集中且可治理。

---

# 2. Context

即使已知道 `breaks.py` 有越界問題，也需要進一步確認實際 DB write 是否分散在多處，否則後續 Fix 會有隱藏競寫與副作用風險。

---

# 3. Scope

## In Scope
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/repo.py`
- breaks update / note update / punch state 相關 tests

## Out of Scope
- UI / frontend
- duration canonical semantics
- reporting aggregation

---

# 4. Search Targets

必查項目：

1. breaks 相關的所有寫入點
2. `commit`, `flush`, `refresh` 等 persistence 行為
3. API / service / repo 是否都各自做寫入
4. note update 與 break punch state 是否共用相同寫入責任鏈
5. 是否存在 legacy 路徑側寫同資料

---

# 5. Evidence Requirements

必須提供：

1. breaks 寫入點清單
2. commit 責任鏈圖
3. 寫入是否集中於單一路徑
4. 是否存在 side effect / duplicate write 風險
5. 是否能以最小差異方式治理

---

# 6. Output File

輸出檔案固定為：
- `docs/attendance/remediation/01_audit/P3_A2_BREAKS_DB_WRITE_AUDIT.md`

---

# 7. Prohibited Actions

禁止：
- 修改任何 DB write 位置
- 直接新增 repo abstraction
- 順便統一所有 attendance 寫入模式

---

# 8. Audit Result

待執行。

執行完成後至少要回答：
- breaks 寫入是否集中？
- commit 責任是在 API 還是其他層？
- 後續治理是否可能以小步進行？

---

# 9. Risk Level

預設風險：MEDIUM-HIGH

原因：資料寫入分散常是後續修整失敗的主要來源。

---

# 10. Open Questions

1. 是否存在多 endpoint 共用同一 DB write 片段？
2. 測試是否能偵測 duplicated write？
3. breaks note update 是否混入其他 domain action？

---

# 11. Gate Recommendation

預設：`Gate Pending`

若寫入分散，應優先阻擋直接進 Fix。
