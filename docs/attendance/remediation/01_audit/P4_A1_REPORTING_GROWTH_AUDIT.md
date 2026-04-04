# P4_A1 Reporting Growth Audit

> **Ticket Type**: Audit
> **Phase**: 4
> **Priority**: Medium
> **Execution Mode**: Read-only
> **Status**: Not Started

---

# 1. Goal

評估 `api/reporting.py`、`reporting_repo.py`、`reporting_service.py` 的當前責任分布與成長風險，判定未來新增報表是否會導致 reporting 再次集中化。

---

# 2. Context

目前 reporting 雖未明顯失控，但已有成長壓力。此票目的是建立治理邊界，而不是新增報表或直接拆檔。

---

# 3. Scope

## In Scope
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/reporting_repo.py`
- `backend/app/modules/attendance/reporting_service.py`
- reporting 相關 schema / tests

## Out of Scope
- 實際新增任何 reporting endpoint
- canonical duration 修正
- company summary 效能優化實作

---

# 4. Search Targets

必查項目：

1. `reporting.py` 目前責任清單
2. response shaping 是否過重
3. company summary 的資料取得策略
4. scope / feature gate / validation 是否重複擴散
5. 新報表加入時，最可能先失控的層

---

# 5. Evidence Requirements

必須提供：

1. reporting 責任分布圖
2. growth bottleneck 清單
3. `reporting.py` 是否接近拆分門檻的判定
4. company summary 成長風險描述
5. 未來應避免的擴張模式

---

# 6. Output File

輸出檔案固定為：
- `docs/attendance/remediation/01_audit/P4_A1_REPORTING_GROWTH_AUDIT.md`

---

# 7. Prohibited Actions

禁止：
- 直接新增 reporting endpoint
- 順手拆 `reporting.py`
- 做效能優化 diff
- 直接把本票變成 route refactor

---

# 8. Audit Result

待執行。

執行完成後至少要回答：
- reporting 哪一層最先會失控？
- `reporting.py` 是否已達必拆門檻？
- company summary 現況是否只是暫時可接受？

---

# 9. Risk Level

預設風險：MEDIUM

原因：此票屬成長治理議題，但若延後太久會快速升高風險。

---

# 10. Open Questions

1. 未來新增 2~3 種報表時，哪個檔案會先跨過 size gate？
2. reporting repo 是否會被迫承擔過多 read-model 特例？
3. 是否需要 route-level decomposition 而非單檔繼續長大？

---

# 11. Gate Recommendation

預設：`Gate Pending`

若本票顯示 `reporting.py` 已接近治理門檻，應先提 decomposition，再談實作。
