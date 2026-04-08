# ATTENDANCE REMEDIATION GOVERNANCE CONTROL

> **Document Type**: Governance Control File
> **Execution Style**: Phase-Based Controlled Remediation
> **Mandatory Pattern**: Every Phase MUST follow `Audit → Gate → Fix`
> **Scope**: `backend/app/modules/attendance`, `backend/app/main.py`, related governance-controlled attendance paths
> **Status**: ACTIVE
> **Last Updated**: 2026-04-04

---

# 0. Purpose

本文件不是一般開發待辦文件，也不是自由實作計畫。

本文件的唯一目的，是讓 Cursor / AI / 後續執行者能以**治理型、不可跳步、可稽核**的方式，依序修整 Attendance 模組目前已識別出的架構偏差與風險。

本文件採用固定控制模式：

**每個 Phase = Audit → Gate → Fix**

任何 Phase 若未完成 Audit 或未通過 Gate：

- ❌ 禁止進入 Fix
- ❌ 禁止提前處理下一個 Phase
- ❌ 禁止把多個 Phase 混成一次修改

---

# 1. Governing Inputs

本控制文件的執行，必須以下列文件為依據：

1. `docs/00_AI_GOVERNANCE/STOP_GATES.md`
2. `docs/00_AI_GOVERNANCE/CURSOR_EXECUTION_CONTROL.md`
3. `docs/00_AI_GOVERNANCE/CURSOR_BACKEND_SAFE_EDIT_RULES.md`
4. `docs/00_AI_GOVERNANCE/AI_CONTEXT.md`
5. `docs/01_ARCHITECTURE/SA_MODULE_SPEC_v2.1.md`
6. `docs/00_AI_GOVERNANCE/ATTENDANCE_MODULE_STRUCTURE_AUDIT_REPORT.md`

若上述文件之間有衝突：
- 以 `STOP_GATES.md` 為最高優先
- 其次依序遵守治理控制文件與架構規範

---

# 2. Hard Execution Rules

## 2.1 Mandatory Order

所有修整任務必須嚴格依下列順序執行：

- Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5

禁止：
- 跳 Phase
- 並行處理多個 Phase
- 先 Fix 再補 Audit
- 在未完成前一個 Phase Gate 前，先進入下一個 Phase

## 2.2 Phase Lock Rule

每一個 Phase 都必須產出三段結果：

1. **Audit Result**
2. **Gate Decision**
3. **Fix Scope Confirmation**

未完整產出三段結果：
- 視為該 Phase 未完成
- 不得寫檔
- 不得執行修整

## 2.3 Scope Lock Rule

每一個 Phase 只能處理該 Phase 明確列出的目標。

禁止：
- 順手重構無關區塊
- 順便清理命名
- 順便調整其他 endpoint
- 順便做下一個 Phase 的預處理

## 2.4 Safe Edit Rule

所有實作必須遵守：
- patch-style edits only
- 不可整檔重寫
- 不可對異常檔 / 截斷檔 / 0KB 檔案寫入
- 高風險核心檔只能做局部可驗證修改

---

# 3. Protected Core Files

以下檔案視為本修整工作的高風險核心檔：

## P0 — Forbidden Direct Rewrite
- `backend/app/main.py`
- `backend/app/modules/attendance/api/__init__.py`
- `backend/app/modules/attendance/repo.py`

規則：
- 禁止整檔改寫
- 禁止一次加入多項邏輯
- 若修整需要觸及，必須先單獨 Audit 該檔

## P1 — Localized Change Only
- `backend/app/modules/attendance/api/punch.py`
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/service.py`

規則：
- 只能局部小步修改
- 每一步都必須可驗證
- 不得順便做跨責任層擴散修改

## P2 — Controlled Safe Change
- `backend/app/modules/attendance/reporting_service.py`
- `backend/app/modules/attendance/reporting_repo.py`
- `backend/app/modules/attendance/checkpoint_repo.py`
- 其他純輔助型 attendance 檔案

---

# 4. Execution Template for Every Phase

每個 Phase 都必須套用以下固定模板：

## A. Audit
必須回答：
- 本 Phase 的 Primary Layer 是什麼？
- 本 Phase 的 Secondary Layers 是什麼？
- 為什麼不是其他層？
- 目前偏差點具體在哪裡？
- 涉及哪些檔案？
- 哪些檔案屬高風險核心檔？

## B. Gate
必須明確判定：
- 是否允許進入 Fix？（YES / NO）
- 若 NO，阻擋原因是什麼？
- 是否觸發 STOP GATE？
- 是否需要先提出拆分方案？
- 是否需要先做更小範圍 decomposition？

## C. Fix
只有 Gate = YES 才能執行。

Fix 階段必須事先界定：
- 允許修改檔案
- 禁止修改檔案
- 可接受的最小差異範圍
- 驗收條件
- 完成後要回報的 evidence

---

# 5. Phase 1 — Canonical Work Duration Alignment

## 5.1 Objective

修整 `duration_minutes` 的語意，使其與 SA2.1 v2.1 定義的 canonical work duration 對齊。

## 5.2 Why Phase 1 Comes First

此問題是整個 Attendance 模組最上游的語意偏差。
若 canonical 定義不正確：
- reporting 會讀到錯誤基礎值
- overtime / paid hours / future analytics 都會建立在錯誤欄位語意上
- 後續 Phase 的正確性無法保證

## 5.3 Audit

### Audit Targets
- `backend/app/modules/attendance/api/punch.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/work_hour_engine.py`
- `backend/app/modules/attendance/api/break_deduction.py`
- 與 canonical duration 寫入相關之 schema / tests

### Mandatory Audit Questions
1. `duration_minutes` 目前在哪一層被決定？
2. `gross_minutes`、`net_work_minutes`、policy evaluation、session close 寫入點各自位於哪裡？
3. canonical 值應該由哪個 layer 負責？
4. 目前是否已有可重用之 work hour engine？
5. 若沒有，是否需要先拆出最小合法計算單元？

### Expected Audit Output
- 一份清楚的 canonical data flow 圖
- 明確指出目前寫入 `duration_minutes` 的唯一位置
- 明確指出與 SA2.1 的差距

## 5.4 Gate

只有同時滿足以下條件，才能進入 Fix：

- 已證明 canonical 寫入點唯一且可控
- 已確認不會破壞 JWT actor flow
- 已確認不會造成跨 module import
- 已確認修改目標檔案未觸發不可繞過的 STOP GATE
- 已確認若需新增邏輯，不會直接塞入超過 size gate 的高風險檔而無拆分方案

### Gate Failure Conditions
任一成立即 Gate = NO：
- 無法定位 canonical 寫入唯一責任點
- 需要對 `repo.py` 或 `punch.py` 做大規模擴張
- 需要新增複雜計算卻沒有 decomposition plan
- 需要先釐清 work_hour_engine 的責任邊界

## 5.5 Fix Scope

### Allowed
- 最小差異修整 canonical duration 的決定與寫入路徑
- 必要的小範圍 service / engine 對齊
- 補齊與 canonical 定義直接相關的驗收測試

### Forbidden
- 順便重構 punch API 全體
- 順便重命名大量 schema
- 順便清理 reporting endpoint
- 把多個工時計算議題一次整包處理

## 5.6 Completion Evidence

完成後必須能證明：
- `duration_minutes` 已符合 SA2.1 v2.1 定義
- break deduction 與 canonical 寫入關係清楚
- reporting 讀取 canonical 欄位時不再建立於 gross 語意之上

---

# 6. Phase 2 — Taipei Business Date Boundary Alignment

## 6.1 Objective

修整所有「today / business date / date range ownership」相關行為，使其一致遵守 `Asia/Taipei` 業務日規則。

## 6.2 Why Phase 2 Is After Phase 1

時間邊界與 canonical duration 都屬 reporting correctness 的基礎，但 canonical 語意是更上游的資料定義，因此必須先處理。

## 6.3 Audit

### Audit Targets
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/reporting_repo.py`
- 與 Taipei ownership / business date 相關 tests

### Mandatory Audit Questions
1. 系統哪些 endpoint 使用「today」或日期區間？
2. 哪些地方使用 UTC date 代替 business date？
3. 哪些查詢已符合 Taipei ownership？
4. `break-punches` 是否與 reporting 的日期歸屬規則一致？

### Expected Audit Output
- 一份 attendance 日期邊界清單
- 一份不一致點列表
- 明確指出應由哪一層負責 business date normalization

## 6.4 Gate

進入 Fix 前，必須先確認：
- 已完整列出所有受 Taipei 規則影響的 attendance endpoint
- 不會因局部修正造成 reporting / breaks 規則再次分岔
- 修整將落在單一責任層，而不是散落多處硬編碼

### Gate Failure Conditions
- 只想修 `breaks.py`，但未確認 reporting 同步規則
- 無法定義 business date normalization 的唯一責任層
- 修正方式會在 API 層複製同類邏輯到多個 endpoint

## 6.5 Fix Scope

### Allowed
- 最小差異修整 Taipei 業務日邊界
- 統一 `today` / date ownership 的計算責任
- 補日期邊界與跨午夜驗收測試

### Forbidden
- 順便重構所有 reporting endpoint
- 順便調整 unrelated timezone formatting
- 順便做前端顯示改造

## 6.6 Completion Evidence

完成後必須能證明：
- `break-punches` 與 reporting 採相同 business date 規則
- 台北午夜邊界 / 跨日 / 跨月 ownership 測試成立
- 無新的 UTC date 假性業務日寫法殘留在 attendance 主鏈路

---

# 7. Phase 3 — API / Service / Repo Boundary Convergence for Breaks

## 7.1 Objective

收斂 `breaks.py` 的責任邊界，避免 API handler 持續直接查詢 ORM、直接執行資料更新與 commit。

## 7.2 Why Phase 3 Is Separate

此 Phase 不處理 canonical 定義，也不處理 reporting 擴張，而是專注修正 responsibility boundary。

## 7.3 Audit

### Audit Targets
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/repo.py`
- 若必要，新增或調整 break 專屬最小服務/資料層

### Mandatory Audit Questions
1. `breaks.py` 目前有哪些邏輯其實不應存在於 API layer？
2. 哪些是 query only？哪些是 business orchestration？哪些是 response shaping？
3. 是否需要拆分新檔？
4. 若需要拆分，新檔責任是否單一？

### Expected Audit Output
- `breaks.py` 現況責任切片
- API / Service / Repo 應歸位項目列表
- 拆分 YES / NO 判定

## 7.4 Gate

只有以下條件都成立，才能進入 Fix：
- 已判定哪些邏輯該移出 API
- 已確認不會把 aggregation 塞進 repo
- 已確認不會把 DB query 塞進 service 而破壞邊界
- 若新增檔案，已先完成責任說明

### Gate Failure Conditions
- 邊界尚未釐清就直接搬程式
- 試圖同時重構所有 attendance API
- 將 breaks 特例做成不可重用的大型 helper 雜湊層

## 7.5 Fix Scope

### Allowed
- 將 `breaks.py` 中明顯非 API 責任的邏輯收斂到正確層次
- 增加最小必要的 repo function 或 service orchestration
- 補 break note update / break punches 查詢的邊界驗證

### Forbidden
- 順便重構 punch / checkpoints / reporting
- 一次性建立大而全的新 abstraction
- 把 one-off 邏輯抽成過度設計的 framework

## 7.6 Completion Evidence

完成後必須能證明：
- API layer 只保留 request/response + permission + minimal orchestration
- query 移到 repo
- business flow 移到 service 或明確責任層
- `breaks.py` 複雜度下降且責任更單一

---

# 8. Phase 4 — Reporting Growth Control

## 8.1 Objective

建立 reporting 後續擴展的治理邊界，避免 `api/reporting.py` 演化成新的 monolithic 熱點。

## 8.2 Important Governance Constraint

若此階段觸發 `GATE-REPORTING-SCOPE`，則：
- 必須停止
- 不得直接在 `reporting.py` 新增功能
- 必須改以 decomposition / alternative structure proposal 處理

## 8.3 Audit

### Audit Targets
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/reporting_repo.py`
- `backend/app/modules/attendance/reporting_service.py`
- reporting tests

### Mandatory Audit Questions
1. `reporting.py` 現在承擔哪些責任？
2. 未來若新增 2~3 種報表，哪一層最先失控？
3. company summary 全量拉取是否仍可接受？
4. 是否需要 route-level decomposition，而不是繼續擴張單檔？

### Expected Audit Output
- reporting 責任分布圖
- growth bottleneck 清單
- decomposition 門檻判定

## 8.4 Gate

進入 Fix 前必須先確認：
- 本階段不是在 `reporting.py` 上新增新功能，而是做治理式結構收斂
- 未違反 Reporting Module Refactor 未完成的限制
- 若需拆分，已提出新檔責任

### Gate Failure Conditions
- 企圖把新報表直接加到 `reporting.py`
- 企圖在 reporting 主檔增加更多 business logic
- 未完成 decomposition plan 就對 reporting 主檔做大修改

## 8.5 Fix Scope

### Allowed
- 建立 reporting 擴展的結構邊界
- 拆出更清楚的 reporting route/service responsibility（若 Gate 允許）
- 收斂 company summary 未來成長風險

### Forbidden
- 直接在主 reporting 檔新增一批新 endpoint
- 用「先塞進去再說」的方式延後重構
- 把 reporting 的查詢、聚合、格式化重新混回同一層

## 8.6 Completion Evidence

完成後必須能證明：
- reporting 的成長邊界已明確
- 新報表不會被預設塞回 `reporting.py`
- company summary / list / future reports 的分層策略已成立

---

# 9. Phase 5 — Legacy / New Flow Decoupling

## 9.1 Objective

降低 `repo.py` 與 `service.py` 中 legacy flow 與新 attendance flow 混存造成的中心化風險。

## 9.2 Why This Is Last

這一階段涉及結構收尾與技術債治理，不應在上游語意與邊界尚未收斂前提前進行。

## 9.3 Audit

### Audit Targets
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/api/legacy.py`
- legacy attendance record flow 對現行系統的依賴程度

### Mandatory Audit Questions
1. 哪些 legacy 流程仍為 production contract？
2. 哪些可隔離？哪些不可動？
3. 拆分後是否會影響現行路由與契約？
4. 是否會觸發超過 400 行檔案的 decomposition gate？

### Expected Audit Output
- legacy 依賴地圖
- 可安全解耦項目列表
- 禁止動區與可搬移區清單

## 9.4 Gate

進入 Fix 前必須先確認：
- 已明確區分 compatibility contract 與 internal technical debt
- 已提出 decomposition plan
- 不會直接對 `repo.py` 進行大面積重寫
- 不會破壞 legacy route contract

### Gate Failure Conditions
- 未盤清 legacy contract 就開始移動責任
- 對 `repo.py` / `service.py` 做大規模重排
- 嘗試一次性「清乾淨」所有歷史技術債

## 9.5 Fix Scope

### Allowed
- 有治理依據的小步解耦
- 拆出責任更單一的 legacy/new flow 邊界
- 最小風險地降低中心化程度

### Forbidden
- 全面重構 attendance service / repo
- 一次性改動所有引用點
- 未有明確相容性驗證即改動 legacy contract

## 9.6 Completion Evidence

完成後必須能證明：
- `repo.py` / `service.py` 的中心化程度下降
- legacy 與 new flow 邊界更清楚
- 高風險核心檔的後續修改壓力下降

---

# 10. Phase Exit Rule

每完成一個 Phase，必須先輸出一份 Phase Exit Report，至少包含：

1. Phase Name
2. Audit 結論
3. Gate 結論（YES / NO）
4. 實際修改檔案清單
5. 明確未修改檔案清單
6. 驗收結果
7. 是否允許進入下一個 Phase

若未輸出 Phase Exit Report：
- 視為該 Phase 未正式完成
- 不得進入下一階段

---

# 11. Stop Conditions

執行任何 Phase 時，若出現以下任一情況，必須立即停止：

- 觸發 `STOP_GATES.md` 任一 Hard Stop
- 需要修改 P0 核心檔但尚無明確最小差異方案
- 發現目標檔案異常、截斷、0KB、結構缺失
- 發現本 Phase 其實依賴前一個未完成的結構前提
- 修整範圍開始跨出當前 Phase 的治理邊界

回報格式必須遵守 governance stop report 格式，不得自行繼續。

---

# 12. Final Execution Principle

本文件的核心不是「快點修完」，而是：

**以治理順序建立可驗證、可停止、可稽核的修整鏈。**

因此正確流程永遠是：

**Audit → Gate → Fix → Exit Report → Next Phase**

而不是：

**看到問題 → 直接修改 → 邊改邊想 → 之後再補治理說明**

---

# 13. Immediate Next Action

若要開始執行，唯一允許的起點是：

## Start with Phase 1 Audit Only

第一步只能做：
- 讀檔
- 定位 canonical duration 寫入點
- 輸出 Phase 1 Audit Result

在 **Phase 1 Gate 明確通過前**：
- ❌ 禁止進入 Phase 1 Fix
- ❌ 禁止開始 Phase 2
- ❌ 禁止任何先行重構
