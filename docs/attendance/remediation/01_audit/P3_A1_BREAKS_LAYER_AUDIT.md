# P3_A1 Breaks Layer Audit

> **Ticket Type**: Audit
> **Phase**: 3
> **Priority**: Medium-High
> **Execution Mode**: Read-only
> **Status**: Not Started

---

# 1. Goal

審查 `breaks.py` 的責任分布，判定其中哪些邏輯屬於 API 層、哪些其實應歸 service / repo。

---

# 2. Context

目前已知 `breaks.py` 可能直接查詢 ORM、直接更新資料、直接 commit，屬於典型邊界鬆散情況。

本票目的是做責任切片，不是直接搬程式。

---

# 3. Scope

## In Scope
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/repo.py`
- breaks 相關 schema / tests

## Out of Scope
- 其他 attendance API 的整理
- duration semantics
- timezone 修正

---

# 4. Search Targets

必查項目：

1. API handler 內的 ORM query
2. API handler 內的 DB write / commit
3. request parsing / permission / orchestration / response shaping 的切分
4. 是否已有可承接的 service / repo 方法
5. 是否需要最小新責任檔案

---

# 5. Evidence Requirements

必須提供：

1. `breaks.py` 內責任切片清單
2. 明顯越界的邏輯列表
3. 現有 service / repo 能否承接的判定
4. 是否需要拆分新責任檔的 YES/NO
5. 哪些檔案屬高風險核心檔

---

# 6. Output File

輸出檔案固定為：
- `docs/attendance/remediation/01_audit/P3_A1_BREAKS_LAYER_AUDIT.md`

---

# 7. Prohibited Actions

禁止：
- 直接搬移邏輯
- 順便重構 punch / reporting
- 發明大型抽象層

---

# 8. Audit Result

待執行。

執行完成後至少要回答：
- `breaks.py` 哪些區塊不該留在 API 層？
- 現有 service / repo 是否足夠承接？
- 是否需要最小拆分？

---

# 9. Risk Level

預設風險：MEDIUM-HIGH

原因：此票直接影響邊界收斂，但仍需避免高風險核心檔擴張。

---

# 10. Open Questions

1. 現有 `service.py` 是否已過度集中，不適合再收進更多 breaks 邏輯？
2. `repo.py` 是否會成為新的風險承接點？
3. 是否已有 tests 可支撐邊界搬移後驗證？

---

# 11. Gate Recommendation

預設：`Gate Pending`

此票只能先判定責任切片，不得直接視為可實作重構。
