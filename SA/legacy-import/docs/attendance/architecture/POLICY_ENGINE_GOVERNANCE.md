# POLICY_ENGINE_GOVERNANCE

> **Document Type**: Architecture Governance Specification  
> **Scope**: `backend/app/modules/attendance/policy_engine.py`  
> **Status**: Active Governance Rule  
> **Execution Mode**: Analysis and documentation only  
> **Last Updated**: 2026-04-06

---

# 0. Purpose

本文件定義 `policy_engine.py` 的正式治理邊界、允許保留內容、禁止膨脹項目、未來模組分配策略、size gate、擴充流程規則與拆分原則。

本文件的目的是：

- 防止 `policy_engine.py` 再次持續膨脹
- 防止 pure rule / missing segment / schedule-specific 細節重新回塞至 orchestration façade
- 建立未來新增 policy 功能時可直接執行的模組分配規則
- 作為後續 Cursor 任務、PR 審查與治理票判定的前置規格

本文件**不授權**任何立即拆分、重構、API 變更或模組新增。本文件僅定義治理規則。

---

# 1. Current State Analysis

## 1.1 File Size Status

- `policy_engine.py` 目前總行數：**593 行**
- 依本文件定義之治理門檻，此檔案已高於一般安全維護範圍
- 目前狀態判定：**高風險膨脹檔案**

## 1.2 Current Public Entrypoints

`policy_engine.py` 目前主要 public entrypoints 如下：

1. `AttendancePolicyEngine.evaluate(...)`
   - 基本 policy evaluation façade
   - 無 schedule resolver 參與
   - 處理 policy fallback、late / early leave / overtime 評估、結果組裝

2. `AttendancePolicyEngine.evaluate_with_schedule_v2(...)`
   - schedule-aware evaluation façade
   - 透過 `ScheduleBaselineResolver` 取得 baseline
   - 協調 business date、schedule window、late / early leave 評估與最終結果組裝

3. `AttendancePolicyEngine.evaluate_with_schedule(...)`
   - 以 `WorkSchedule` 為輸入的 schedule-aware façade
   - 支援 split shift 工作窗計算
   - 執行 schedule mode 分支與結果組裝

4. `get_policy_engine()`
   - façade factory / dependency injection entry

## 1.3 Current Major Internal Sections

`policy_engine.py` 目前主要區塊如下：

1. `PolicyEvaluationResult`
   - 結果物件定義
   - 結果欄位承載
   - `to_dict()` 輸出轉換

2. `AttendancePolicyEngine` 類別常數
   - fallback 預設值
   - default work start / end time
   - default overtime / grace period

3. 基本 evaluation façade
   - `evaluate(...)`

4. pure calculation helpers
   - `_calculate_late(...)`
   - `_calculate_early_leave(...)`
   - `_calculate_overtime(...)`
   - `_to_business_date(...)`
   - `_calculate_late_from_datetime(...)`
   - `_calculate_early_leave_from_datetime(...)`
   - `_calculate_work_minutes_split_shift(...)`

5. schedule-aware evaluation façade
   - `evaluate_with_schedule_v2(...)`
   - `evaluate_with_schedule(...)`

6. dependency injection factory
   - `get_policy_engine()`

## 1.4 Responsibility Classification by Function / Section

| Section / Function | Current Responsibility | Classification |
|---|---|---|
| `PolicyEvaluationResult` | 最終輸出資料結構與 `to_dict()` 組裝 | result assembly |
| `AttendancePolicyEngine.DEFAULT_*` 常數 | fallback policy 預設值定義 | fallback / compatibility logic |
| `evaluate(...)` | policy 評估主流程、fallback 套用、呼叫計算、組裝結果 | orchestration + result assembly |
| `_calculate_late(...)` | 遲到純計算 | pure rule calculation |
| `_calculate_early_leave(...)` | 早退純計算 | pure rule calculation |
| `_calculate_overtime(...)` | 加班純計算 | pure rule calculation |
| `_to_business_date(...)` | Taipei business date 正規化 | orchestration support / boundary support |
| `_calculate_late_from_datetime(...)` | 以已解析 expected start 執行遲到純計算 | pure rule calculation |
| `_calculate_early_leave_from_datetime(...)` | 以已解析 expected end 執行早退純計算 | pure rule calculation |
| `evaluate_with_schedule_v2(...)` | baseline resolve、schedule-aware orchestration、fallback、結果組裝 | orchestration + schedule-specific logic + fallback / compatibility logic + result assembly |
| `evaluate_with_schedule(...)` | schedule-aware orchestration、split shift 分支、結果組裝 | orchestration + schedule-specific logic + result assembly |
| `_calculate_work_minutes_split_shift(...)` | split shift 工時計算 | pure rule calculation + schedule-specific logic |
| `get_policy_engine()` | façade factory | orchestration support |

## 1.5 Missing Segment Status

目前 `policy_engine.py` **未直接承載完整 missing segment 純規則實作**，但檔內已有明確訊號顯示該責任與 schedule-aware evaluation 之間存在未來接點：

- `policy_missing_segment.py` 已獨立存在
- `evaluate_with_schedule_v2(...)` 中存在 `missing_segment is deferred` 註記
- 代表 missing segment 已被辨識為應拆出之責任，而非 `policy_engine.py` 的核心膨脹區

因此，missing segment 治理判定如下：

- `policy_engine.py` 可**協調** missing segment 結果
- `policy_engine.py` 不得再實作 missing segment 細則本體

## 1.6 Current Structural Risk Assessment

目前 `policy_engine.py` 的主要風險不是 public entrypoint 過多，而是**單一 façade 檔案內混合了過多責任層次**：

1. orchestration
2. pure rule calculation
3. schedule-specific branching
4. fallback / compatibility defaults
5. result assembly
6. 部分 boundary / normalization 支援

其中最應被視為膨脹來源的區塊為：

### A. Pure rule calculation 已與 façade 共檔

以下責任本質上不屬於 orchestration façade 核心：

- `_calculate_late(...)`
- `_calculate_early_leave(...)`
- `_calculate_overtime(...)`
- `_calculate_late_from_datetime(...)`
- `_calculate_early_leave_from_datetime(...)`
- `_calculate_work_minutes_split_shift(...)`

這些函式屬於**可抽離 pure logic**，其中部分責任已在 `policy_rules.py` 有對應落點，顯示檔內仍存在未完全收斂的重複責任。

### B. Schedule-specific logic 已成為主要膨脹區

以下邏輯已明顯超出最小 façade：

- baseline resolve 後的 normalized windows 處理
- default window fallback
- split shift work-minute 分支
- `schedule.mode` 導向的分支判定

此類內容若持續擴寫，將使 `policy_engine.py` 成為 schedule policy 細節集中點，風險極高。

### C. Result assembly 與 result model 已開始增長

`PolicyEvaluationResult` 目前仍屬合理範圍，但已包含：

- policy metadata
- timing 區塊
- evaluation 區塊
- schedule violation flags
- `to_dict()` response-like 輸出

若未治理，未來極易膨脹成結果正規化、相容層、UI/response shaping 的集中點。

## 1.7 Current Keep / Extract / Overgrown Classification

| Category | Current Contents | Governance Judgment |
|---|---|---|
| Core (應保留) | public evaluation façade、最終結果組裝、已拆模組協調 | 可保留於 `policy_engine.py` |
| Extractable (可外移) | pure late / early / overtime 計算、split shift 工時計算、schedule 純規則 | 未來應優先外移 |
| Overgrown (已過度膨脹) | façade 檔內同時承載 pure rule 與 schedule branch 細節，且與外部分拆模組責任重疊 | 已進入治理狀態，禁止再加重 |

---

# 2. Core Boundary Definition

## 2.1 Formal Core Boundary

`policy_engine.py` 未來**允許保留的責任 ONLY** 如下：

1. **Policy evaluation orchestration**
   - 接受 evaluation 所需輸入
   - 決定應協調哪些子模組
   - 保持單一 evaluation façade

2. **Final evaluation result assembly**
   - 將各子模組輸出組裝為單一 `PolicyEvaluationResult`
   - 執行最小必要欄位整合

3. **Coordination of extracted modules**
   - 協調 `policy_rules.py`
   - 協調 `policy_missing_segment.py`
   - 協調 schedule model / schedule rule 子模組

4. **Minimal fallback handling required by façade contract**
   - 僅允許 façade 為維持 evaluation contract 所需之最小 fallback
   - 不得在 façade 中累積新相容層與歷史分支

5. **Single public evaluation façade maintenance**
   - 維持集中且可治理的 public evaluation entry
   - 不得將 public evaluation 入口拆得四散且不可追蹤

## 2.2 What Is Core

以下責任屬於 `policy_engine.py` 核心責任：

- 決定 evaluation flow 的主序
- 決定需呼叫哪些外部規則模組
- 將 policy / session / schedule 評估結果整合成單一結果
- 維持 façade 層 API 穩定性
- 保持 boundary 與 orchestration 層面的最小必要 glue code

## 2.3 What Is Not Core

以下責任**不是** `policy_engine.py` 核心責任：

- 新的 pure rule functions
- missing segment 規則細節
- 大型 schedule-specific branch calculations
- 資料查詢與跨模組 repo / DB 整合細節
- response shaping / UI-friendly formatting
- analytics、reporting、API payload decoration
- trace building、debug payload expansion、explainability 堆疊
- 任意為了方便直接塞入 façade 的純邏輯

---

# 3. Allowed Retained Contents

`policy_engine.py` 允許繼續保留之內容，必須限於以下範圍：

## 3.1 Allowed

- `evaluate(...)` 類型的 façade 入口
- `evaluate_with_schedule(...)` 類型的 façade 入口
- `evaluate_with_schedule_v2(...)` 類型的 façade 入口
- `PolicyEvaluationResult` 或其最小必要等價結果組裝層
- façade 所需最小 fallback 決策
- façade 到外部 rule / missing-segment / schedule 模組的接線
- 極小量 business-date / expected-boundary glue code（僅限 orchestration 所需）

## 3.2 Allowed but Restricted

以下內容僅在**無法合理外移**時才可短暫存在於 `policy_engine.py`：

- 極小的 normalization glue code
- façade contract 所需的一次性欄位轉接
- 單一 entrypoint 的最小 compatibility wrapper

此類內容必須同時滿足：

1. 行數極小
2. 無自成規則體系
3. 不形成可複用 pure logic 群
4. 不引入第二層 schedule branch

---

# 4. Forbidden Growth Rules

以下內容**禁止再進入** `policy_engine.py`：

## 4.1 Pure Rule Expansion — Forbidden

禁止新增大量 pure rule functions，包括但不限於：

- 遲到變體規則
- 早退變體規則
- overtime 變體規則
- work-minute overlap / merge / normalization 純計算
- tolerance / rounding / grace 細節演算法

此類邏輯一律不得直接新增到 `policy_engine.py`。

## 4.2 Missing Segment Rule Expansion — Forbidden

禁止新增 missing segment 規則實作至 `policy_engine.py`，包括但不限於：

- expected / actual / exception segment 覆蓋計算
- missing gap merge / overlap / tolerance 演算法
- dry-run trace 細節
- decidability 判定細節
- evidence sufficiency 規則細節

## 4.3 Schedule-Specific Branch Expansion — Forbidden

禁止在 `policy_engine.py` 持續擴寫大型 schedule-specific branch logic，包括但不限於：

- 多班別 / 多段班 / 彈性班的規則演算法本體
- schedule mode 對應的大量 `if/elif` 分支
- shift / window / segment 的 overlap、裁切、拼接、補洞計算
- schedule-specific overtime / late / early leave 細則

## 4.4 Cross-Module Data Dependency Expansion — Forbidden

禁止在 `policy_engine.py` 新增下列依賴：

- 新的 repo access
- 跨模組 DB query orchestration
- 直接讀取 attendance API request / response 模型
- reporting 模組邏輯依賴
- 非 façade 必要的 service 串接堆疊

## 4.5 API / UI Coupling — Forbidden

禁止在 `policy_engine.py` 新增：

- FastAPI request/response shaping
- UI 導向欄位格式化
- API payload decoration
- serialization policy 累積
- endpoint-specific response 組裝責任

## 4.6 Background / Async / Runtime Side-Effect Expansion — Forbidden

禁止在 `policy_engine.py` 新增：

- background aggregation / background evaluation
- async task dispatch
- queue / worker integration
- side-effectful runtime process

`policy_engine.py` 的治理定位是**evaluation façade**，不是 runtime workflow engine。

---

# 5. Future Module Allocation Strategy

## 5.1 Formal Allocation Rule

未來新增 policy 相關責任時，**新邏輯一律先判定模組歸屬，不可回塞 `policy_engine.py`**。

除 façade orchestration 與最小 result assembly 外，所有可獨立命名的規則責任，都應進入對應子模組。

## 5.2 Module Allocation Matrix

### A. `policy_rules.py`

用途：**純規則計算**

應放入：

- late 純計算
- early leave 純計算
- overtime 純計算
- 基本時間交集、分鐘計算、閾值判定
- 可單元測試的 deterministic policy rules

不得回塞 `policy_engine.py` 的內容：

- 新遲到規則
- 新早退規則
- 新 overtime 變形規則
- 新 tolerance / grace / threshold 演算法

### B. `policy_missing_segment.py`

用途：**missing segment / dry-run / 缺口判定純邏輯**

應放入：

- expected / actual / exception segment 規則
- uncovered segment 判定
- boundary tolerance 決策
- decidability / evidence sufficiency 純判定

不得回塞 `policy_engine.py` 的內容：

- 新 missing-segment algorithm
- 新 trace overlap / merge 演算法
- 例外覆蓋規則
- 缺口原因分類細則

### C. `policy_schedule_models.py`

用途：**schedule / shift / segment 模型與共享型別**

應放入：

- `WorkWindow`
- `FlexTimeBand`
- `WorkSchedule`
- schedule-related shared constants
- 供 façade 與純規則共用的資料模型

不得回塞 `policy_engine.py` 的內容：

- 大型 schedule model 定義
- 新 schedule data container
- schedule configuration normalization model

### D. `policy_schedule_rules.py`（若未來必要）

用途：**schedule-specific pure calculation**

適合放入：

- split shift work-minute calculation
- normalized windows overlap 计算
- first / last window 推導純邏輯
- schedule mode 對應之 deterministic calculation

明確規則：

- 一旦 schedule-specific pure calculation 超過 façade 最小 glue code，必須進此類模組
- 不得長期留在 `policy_engine.py`

### E. `policy_result_factory.py` 或 `policy_result_builder.py`（若未來必要）

用途：**result assembly / normalization**

適合放入：

- `PolicyEvaluationResult` 建構流程擴大時
- 多 entrypoint 共用結果組裝
- result normalization / output contract 對齊

明確規則：

- 若結果組裝開始出現多階段 normalization、compatibility、欄位映射，必須自 `policy_engine.py` 外移

## 5.3 Absolute Non-Backfill Rule

以下新邏輯**一律不得回塞** `policy_engine.py`：

- 可單獨命名的 pure rule
- 可獨立測試的 schedule calculation
- 可獨立測試的 missing segment 決策
- 可共用的結果正規化器
- 任何 DB / repo / API 耦合處理

---

# 6. Size Gate

## 6.1 Governance Thresholds

`policy_engine.py` 的正式治理門檻如下：

### Gate 1 — Review Required

- **> 400 行**：
  - 每次新增內容都**必須**先檢查是否屬於可外移責任
  - PR / 任務說明中**必須**寫明為何不能外移

### Gate 2 — Non-Core Growth Prohibited

- **> 550 行**：
  - **禁止**新增任何非核心責任
  - 僅允許 façade orchestration、小型接線、極小結果組裝修正
  - pure rule / schedule rule / missing segment 邏輯不得再新增

### Gate 3 — Split Ticket Required

- **> 650 行**：
  - **不得直接擴寫**
  - **必須先開治理票或拆分票**
  - 未有拆分方案前，不得合併新功能進 `policy_engine.py`

## 6.2 Current Gate Status

`policy_engine.py` 目前為 **593 行**，因此目前已落在：

- 已超過 400 行審查門檻
- 已超過 550 行非核心責任禁止門檻
- 尚未達 650 行強制先拆門檻

正式結論：

- `policy_engine.py` **目前不得再新增非核心責任**

---

# 7. Expansion Workflow Rules

以下規則為未來新增 policy 功能時的強制流程。

## 7.1 Mandatory Workflow

1. **不可直接先改 `policy_engine.py`**
2. **必須先判定責任歸屬**
3. 若為 pure rule，**優先放入 `policy_rules.py`**
4. 若為 missing segment，**優先放入 `policy_missing_segment.py`**
5. 若為 schedule-specific pure calculation，**優先放入既有 schedule model/rule 模組或新 schedule rule 模組**
6. 若為結果組裝擴張，**先判定是否應建立 result builder/factory**
7. 只有在外部模組落點確定後，才可回到 `policy_engine.py` 做最小 façade 接線

## 7.2 Allowed Changes to `policy_engine.py`

若未來任務需要修改 `policy_engine.py`，僅允許以下類型：

- orchestration 接線
- façade 保持
- 極小 result assembly 調整
- 極小 fallback contract 修正
- 子模組呼叫順序的最小調整

## 7.3 Disallowed Workflow

以下做法為違規：

- 為了省事直接把 pure rule 塞進 `policy_engine.py`
- 因為 schedule 規則只改一點點就直接放 façade
- 因為 missing segment 尚未最終定案就先放在 engine 中暫存
- 因為 API 很近就直接讓 engine 讀 request / response shape
- 因為結果欄位多了幾個就開始在 engine 內疊 UI / response shaping

---

# 8. Split Strategy Principles

本節定義未來拆分原則，但本文件**不執行拆分**。

## 8.1 Responsibility-Based Split Only

拆分必須以**責任分離**為主，不得只依行數機械切割。

正確拆分優先序：

1. pure logic
2. missing segment logic
3. schedule-specific pure calculation
4. result assembly / normalization
5. 最後才考慮 façade 周邊整理

## 8.2 Public Evaluation Façade Must Remain Discoverable

不可把 public evaluation 入口拆得四散。

必須保持：

- 使用者能在單一主要入口找到 evaluation façade
- orchestration flow 仍然可追蹤
- policy engine 作為 façade 的定位不消失

## 8.3 Prioritize Extracting Pure Logic First

拆分時優先處理：

- 遲到 / 早退 / overtime 純演算法
- split shift 工時計算
- expected / actual / exception segment 純判定
- schedule overlap / tolerance 純運算

不得優先把 façade 拆成多個入口，再把純邏輯留在原檔。

## 8.4 No Direct API / Repo Knowledge in `policy_engine.py`

拆分後的正式方向必須保持：

- `policy_engine.py` 不直接承載 API 細節
- `policy_engine.py` 不直接承載 repo 細節
- `policy_engine.py` 不成為跨模組 query orchestration 中心

## 8.5 Avoid Compatibility Layer Accumulation

拆分時不得為保守相容而在 `policy_engine.py` 留下大量 wrapper / adapter / legacy branch。

原則如下：

- façade 可有最小 wrapper
- 不可累積歷史版本分支
- 不可讓 engine 長期同時承擔 v1 / v2 / legacy rule trees

---

# 9. Governance Gate

以下為 PR 與任務驗收的正式治理門檻。

## 9.1 PR-Level Mandatory Checks

任何新增 policy 功能的 PR，必須滿足：

1. **不得直接向 `policy_engine.py` 新增 pure rule**
2. 新增 schedule / segment 規則前，**必須先判定模組歸屬**
3. 超過 size gate 時，**必須先開治理票或拆分票**
4. 每次修改 `policy_engine.py`，**必須標註為什麼不能放到外部模組**

## 9.2 Required Justification When Touching `policy_engine.py`

凡修改 `policy_engine.py`，任務說明或 PR 描述中**必須**明確回答：

- 此修改屬於哪一種核心責任？
- 為何不能放入 `policy_rules.py`？
- 為何不能放入 `policy_missing_segment.py`？
- 若是 schedule-specific 邏輯，為何不是 schedule rule/module 責任？
- 此修改是否只屬 façade 接線或最小結果組裝？

若無上述說明，應視為治理不通過。

## 9.3 Automatic Rejection Conditions

以下任一情況成立時，應視為治理不通過：

- 在 `policy_engine.py` 新增新的 pure rule block
- 在 `policy_engine.py` 新增 missing segment algorithm
- 在 `policy_engine.py` 新增大型 schedule branch tree
- 在 `policy_engine.py` 引入新的 repo / API / response shaping 耦合
- 在未開治理票前，於 >650 行狀態直接擴寫

---

# 10. Cursor Task Rules

本節可直接作為未來 Cursor 任務前置規則。

## 10.1 Mandatory Instruction Set

當任務涉及 policy evaluation 擴充時，Cursor **必須**遵守以下順序：

1. 先讀 `policy_engine.py`
2. 先判定新增責任是：
   - orchestration
   - pure rule
   - missing segment
   - schedule-specific pure calculation
   - result assembly / normalization
3. 先選定外部模組落點
4. 若非核心責任，禁止先改 `policy_engine.py`
5. 若需改 `policy_engine.py`，僅可做最小 façade 接線
6. 任務說明中必須寫出責任歸屬與無法外移理由

## 10.2 Prohibited Cursor Behavior

Cursor 不得：

- 看到 engine 有相關上下文就直接續塞新邏輯
- 把暫時性規則先放 engine，之後再說
- 因為修改範圍較小而忽略模組歸屬
- 把 schedule-specific 計算直接留在 façade
- 把 response shaping 混入 evaluation engine

---

# 11. Final Governance Conclusion

`policy_engine.py` 的正式定位應為：

- **單一 public policy evaluation façade**
- **最小 orchestration 層**
- **最小 final result assembly 層**
- **已拆出子模組的協調層**

`policy_engine.py` 的正式定位**不應再是**：

- pure rule 函式倉庫
- missing segment 規則主體
- schedule-specific 演算法集中點
- API / repo / reporting 耦合層
- UI / response shaping 承載層

正式治理結論如下：

1. `policy_engine.py` 已屬高風險膨脹檔案
2. 目前僅允許保留 façade orchestration 與最小結果組裝責任
3. 新 pure rule / missing segment / schedule rule **一律不得回塞** `policy_engine.py`
4. 未來新增功能必須先判定模組歸屬，再做 façade 接線
5. 目前已超過 550 行門檻，**禁止再新增非核心責任**

---

# 12. Enforcement Summary

為避免歧義，最終治理用語如下：

## 12.1 Allowed

- 允許：orchestration
- 允許：單一 façade 維持
- 允許：最小 final result assembly
- 允許：已拆模組接線

## 12.2 Forbidden

- 禁止：pure rule 回塞
- 禁止：missing segment 規則回塞
- 禁止：大型 schedule branch 回塞
- 禁止：API / repo / reporting 耦合回塞
- 禁止：UI / response shaping 回塞
- 禁止：背景流程與副作用擴張

## 12.3 Mandatory

- 必須：先判定責任歸屬
- 必須：優先放入外部對應模組
- 必須：超過 size gate 時先走治理流程
- 必須：每次修改 `policy_engine.py` 說明無法外移原因
