# P1 Option B Fix Decomposition

> **Document Type**: Fix Decomposition Plan
> **Scope**: Phase 1 Option B — canonical duration = net work duration
> **Execution Mode**: Planning only
> **Status**: Draft for human review
> **Inputs**:
> - `docs/attendance/remediation/00_control/P1_PHASE_GATE_REVIEW.md`
> - `docs/attendance/remediation/01_audit/P1_A1_DURATION_WRITE_AUDIT.md`
> - `docs/attendance/remediation/01_audit/P1_A2_DURATION_FLOW_AUDIT.md`
> **Last Updated**: 2026-04-04

---

# 0. Purpose

本文件的目的，是為 **Option B（canonical = net work duration）** 提供一份安全的 Fix 拆解方案。

本文件只定義：
- Fix 應如何分階段
- 每個階段的修改目標與風險
- 哪些檔案不能直接動
- 哪一刀應該先下
- rollback 怎麼做

本文件**不做**以下事情：
- 不修改任何 code
- 不產出 diff
- 不改 schema
- 不直接授權進入實作

---

# 1. Current Constraint Summary

依 `P1_A1`、`P1_A2` 與 `P1 Phase Gate Review`：

目前系統狀態為：
- `duration_minutes = gross_minutes`
- `policy` 依賴 gross semantics
- `reporting / summary` 依賴 gross semantics
- `net_work_minutes` 僅為 derived 結果
- `repo.close_session()` 是 persistence 寫入點，但不是 canonical semantic owner

因此 Option B 不是單點修補，而是：

- **canonical semantic migration**
- 需要從「先建立 canonical 計算來源」開始
- 再逐步切換 policy
- 最後才切換 persistence 與 reporting

---

# 2. High-Risk vs Safer Files

## 2.1 高風險檔案（禁止直接大改）

以下檔案屬高風險，禁止直接做大規模混合修改：

### P0 / 禁止直接改寫
- `backend/app/modules/attendance/repo.py`

### P1 / 僅可局部修改
- `backend/app/modules/attendance/api/punch.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/api/reporting.py`

### 高影響但可控的語意核心檔
- `backend/app/modules/attendance/punch_close_domain.py`
- `backend/app/modules/attendance/policy_engine.py`

原因：
- 這些檔案位於 close flow、policy input、reporting read path 的主鏈上
- 一次混改容易同時改壞 semantic、transaction、API response 與 tests

## 2.2 可以先動的檔案（相對安全）

以下檔案適合做第一階段引入型修改：

- `backend/app/modules/attendance/work_hour_engine.py`
- `backend/app/modules/attendance/api/break_deduction.py`
- 新增的 pure/domain calculation 檔案（若需要）
- 純測試檔（僅在對應 phase 允許時）

原因：
- 這些檔案較適合承接 canonical calculation source
- 可先建立能力，不立即切換主鏈行為
- 可降低第一刀風險

---

# 3. Fix Phase Decomposition

## Phase F1 — 引入 canonical 計算來源（不改既有行為）

### 修改目標
建立一個**非 API** 的 canonical duration 計算來源，使系統具備輸出 net canonical duration 的能力，但此階段：

- 不改 `duration_minutes` 寫入值
- 不改 policy 使用值
- 不改 reporting 讀值
- 不改 API contract
- 不改 DB

也就是：

**先引入 canonical calculator，但不切換主鏈。**

### 涉及檔案
優先應集中在相對安全層：
- `backend/app/modules/attendance/work_hour_engine.py`
- `backend/app/modules/attendance/api/break_deduction.py`
- 或新增一個非 API 的 pure/domain calculation 檔案

盡量避免此階段直接修改：
- `backend/app/modules/attendance/api/punch.py`
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/policy_engine.py`

### 風險等級
**Low**

原因：
- 不切換主鏈行為
- 不變更 persisted value
- 不影響對外 API
- 不觸及 migration 問題

### 是否需要 migration
**No**

### rollback 方式
- 若新增 canonical calculator 或新純函式，直接停用或移除其接線
- 因未改主鏈 persisted semantics，rollback 成本低

### Phase Exit Condition
此階段完成後，系統應該能回答：
- 是否已存在單一 canonical duration source？
- 該 source 是否可輸出 net canonical work duration？
- 是否仍完全不影響既有系統行為？

---

## Phase F2 — 讓 policy 使用 canonical（仍不改 DB）

### 修改目標
讓 policy evaluation 改為使用 canonical duration，但仍保持：

- `repo.close_session()` 寫入舊的 gross persisted value
- reporting 仍讀舊的 persisted value
- API 對外 `duration_minutes` 仍不切換 stored semantics

也就是：

**先把 policy 從 gross 切到 canonical，但 DB 與 reporting 暫時不切。**

### 涉及檔案
主要涉及：
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/punch_close_domain.py`
- `backend/app/modules/attendance/policy_engine.py`
- 視需要局部接到 `backend/app/modules/attendance/api/punch.py`

此階段仍應避免大改：
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/api/reporting.py`

### 風險等級
**Medium**

原因：
- policy 的 `work_minutes`、overtime 結果可能改變
- 雖未改 DB，但已開始切換內部語意
- 必須避免 policy 與 persisted semantics 混淆造成誤判

### 是否需要 migration
**No（但需先寫清語意切分）**

因為此階段還沒改 stored historical data。

### rollback 方式
- 將 policy input 恢復為 gross path
- 保留 F1 建立的 canonical calculator，但暫不使用

### Phase Exit Condition
此階段完成後，系統應能回答：
- policy 是否已改用 canonical duration？
- DB persisted `duration_minutes` 是否仍維持 gross？
- 這種雙軌狀態是否被明確標示，且不影響 API contract？

---

## Phase F3 — 切換 persistence 與 reporting

### 修改目標
正式把 stored `duration_minutes` 從 gross 切換為 net canonical duration，並讓 reporting / summary 與 persisted semantics 對齊。

此階段代表真正完成 Option B 的主切換。

### 涉及檔案
高風險主鏈檔案會被觸及：
- `backend/app/modules/attendance/api/punch.py`
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/reporting_service.py`
- `backend/app/modules/attendance/reporting_repo.py`（若 read-side 說明需同步）
- `backend/app/modules/attendance/tests/...`（punch、policy、reporting 相關）

### 風險等級
**High**

原因：
- persisted semantics 會改變
- reporting totals 會改變
- 既有測試前提會改變
- 歷史資料與新資料的語意一致性會變成核心議題

### 是否需要 migration
**Yes — migration plan required**

至少需先定義：
- 是否回填歷史 `duration_minutes`
- 是否保留歷史 gross 值不動
- reporting 如何處理舊資料與新資料
- 是否需要階段性 feature cutover

### rollback 方式
- rollback 不應只靠單一 code revert
- 必須依 migration 策略決定：
  - 若未做資料回填，則可回退寫入路徑並恢復 gross semantics
  - 若已做資料回填，則需有獨立 data rollback / restore strategy

### Phase Exit Condition
此階段完成後，系統應能證明：
- `duration_minutes` 已成為 net canonical duration
- policy 與 reporting 都讀同一語意
- historical data handling 已被明確定義
- 對外 contract 變化已被評估與驗證

---

# 4. The First Cut（第一刀）

## 4.1 定義

**第一刀必須是：Phase F1 — 引入 canonical 計算來源（不改既有行為）**

## 4.2 為什麼這是第一刀

因為它滿足以下條件：

- 低風險
- 不改 API contract
- 不改 DB
- 不改 persisted semantics
- 不需要 migration
- 可先把 canonical semantic owner 從 API 外移的方向建立起來

## 4.3 第一刀禁止事項

第一刀不得：
- 直接修改 `repo.close_session()` 的寫入語意
- 直接讓 `policy_engine` 改吃新的 persisted value
- 直接改 `/sessions`、`/reports/user-summary`、`/reports/company-summary` 的輸出語意
- 直接改 schema
- 直接做 historical data migration

## 4.4 第一刀成功標準

第一刀完成後，應滿足：

1. 已存在單一 canonical calculation source
2. 主鏈系統行為完全不變
3. API response 完全不變
4. DB persisted data 完全不變
5. 為 F2 / F3 準備好安全切換前提

---

# 5. Cross-Phase Rules

## 5.1 不可跳階段

禁止：
- 直接從現況跳到 F3
- 在未完成 F1 時先改 policy
- 在未完成 F2 時先切 reporting persisted semantics

## 5.2 不可混合修改

禁止單次修改中同時混入：
- canonical calculator introduction
- policy semantic switch
- persistence semantic switch
- reporting semantic switch

## 5.3 高風險檔案原則

即使到了 F3，也應遵守：
- `repo.py` 不可大規模整檔重寫
- `api/punch.py` 不可一次混入多種新責任
- `api/reporting.py` 不可順便擴張 unrelated reporting logic

---

# 6. Migration Planning Requirement

若人工最終選擇 Option B，則在進入 F3 前，至少需先補一份 migration plan，回答：

1. 既有 `duration_minutes` 是否回填？
2. 若不回填，歷史 gross 與新 net 是否允許共存？
3. reporting 對混合語意資料如何處理？
4. 是否需要 cutover date / version boundary？
5. rollback 時資料層如何處理？

沒有 migration plan：
- **不得進入 F3**

---

# 7. Recommended Execution Order

若人工選擇 Option B，建議固定執行順序：

1. **F1** — 引入 canonical 計算來源（不改既有行為）
2. **F2** — 讓 policy 使用 canonical（仍不改 DB）
3. **補 migration plan**
4. **F3** — 切換 persistence 與 reporting

---

# 8. Final Decomposition Summary

Option B 的安全拆解核心原則只有一句：

**先建立 canonical source，再切 policy，最後才切 persistence 與 reporting。**

若違反這個順序，風險將集中爆發在：
- `api/punch.py`
- `repo.py`
- `policy_engine.py`
- `reporting` read path

因此本文件的結論不是「現在就改」，而是：

- **Option B 可以做，但只能以分階段、可 rollback、含 migration 規劃的方式做。**
