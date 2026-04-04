# P5_A1 Legacy/New Flow Coupling Audit

> **Ticket Type**: Audit
> **Phase**: 5
> **Priority**: Medium
> **Execution Mode**: Read-only
> **Status**: Not Started

---

# 1. Goal

盤點 `service.py` 與 `repo.py` 中 legacy flow 與新 Attendance flow 的耦合情況，確認哪些是不可動契約、哪些是可治理技術債。

---

# 2. Context

目前 `repo.py` 與 `service.py` 同時承載 legacy 與新架構責任，雖然短期可運作，但長期會提高 unsafe edit 風險與維護成本。

本票只做耦合盤點與分類。

---

# 3. Scope

## In Scope
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/api/legacy.py`
- 與 legacy/new flow 關聯的 tests

## Out of Scope
- 實際拆分 service / repo
- 調整 route contract
- 廣泛 technical debt cleanup

---

# 4. Search Targets

必查項目：

1. legacy 與新 flow 的共存區塊
2. production contract 仍依賴的 legacy 路徑
3. 新 flow 是否反向依賴 legacy helper / repo
4. `repo.py` / `service.py` 的中心化熱點
5. 是否觸發高風險核心檔治理條件

---

# 5. Evidence Requirements

必須提供：

1. legacy 依賴地圖
2. new flow 依賴地圖
3. 可動 / 不可動 區塊清單
4. 高風險核心檔觸碰風險判定
5. 是否需要 decomposition plan 才能進 Gate

---

# 6. Output File

輸出檔案固定為：
- `docs/attendance/remediation/01_audit/P5_A1_LEGACY_NEW_FLOW_COUPLING_AUDIT.md`

---

# 7. Prohibited Actions

禁止：
- 修改 `repo.py`
- 修改 `service.py`
- 嘗試一次性拆分 legacy/new flow
- 順便清理其他技術債

---

# 8. Audit Result

待執行。

執行完成後至少要回答：
- 哪些 legacy flow 仍屬 production contract？
- 哪些耦合可被治理、哪些不可動？
- 後續是否一定需要 decomposition plan？

---

# 9. Risk Level

預設風險：MEDIUM-HIGH

原因：此票觸及高風險核心檔，但仍屬治理盤點，不應提前實作。

---

# 10. Open Questions

1. `repo.py` 中哪些舊責任其實已無現行路由依賴？
2. `service.py` 是否已超過安全擴張邊界？
3. 若未先做 decomposition，是否任何 Fix 都會過於危險？

---

# 11. Gate Recommendation

預設：`Gate Pending`

若本票顯示核心檔耦合過深，應先阻擋直接進 Fix。
