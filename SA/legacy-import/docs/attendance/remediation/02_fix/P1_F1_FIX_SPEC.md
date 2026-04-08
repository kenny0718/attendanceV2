# P1 F1 Fix Spec — Canonical Pure Calculation Function

> **Document Type**: Fix Specification
> **Phase**: 1 — Option B / F1
> **Purpose**: Define the first-cut canonical pure calculation function without changing current behavior
> **Execution Mode**: Specification only
> **Status**: Draft for human review
> **Inputs**:
> - `docs/attendance/remediation/02_fix/P1_F1_AUDIT_CANONICAL_SOURCE.md`
> - `docs/attendance/remediation/02_fix/P1_F1_GATE.md`
> - `docs/attendance/remediation/02_fix/P1_OPTION_B_FIX_DECOMPOSITION.md`
> - `backend/app/modules/attendance/work_hour_engine.py`
> - `backend/app/modules/attendance/api/break_deduction.py`
> - `backend/app/modules/attendance/api/punch.py`
> **Last Updated**: 2026-04-06

---

# 0. Purpose

本文件的目的，是為 Option B 的 F1 第一刀定義一個**canonical pure calculation function** 的正式規格。

F1 的任務只有：
- 在 non-API pure layer 建立 canonical duration 計算來源
- 為未來 F2 / F3 提供穩定的 semantic owner

F1 **不得**：
- 改變現有 runtime 行為
- 改變 `duration_minutes` 的 persisted semantics
- 改變 policy evaluation input
- 改變 reporting read path
- 改變 API contract

因此本規格文件只定義：
- function purpose
- recommended function signature
- result DTO / model 建議
- compatibility constraints
- acceptance criteria
- implementation boundary

本文件**不做**以下事情：
- 不修改任何 code
- 不產出 diff
- 不設計 runtime 接線
- 不描述 F2 / F3 如何接入現有主鏈

---

# 1. Design Objective

## 1.1 F1 要解決的問題

目前 Attendance 模組內：
- gross duration 可直接計算
- break-aware net duration 也已可由 engine 推導
- 但尚未存在一個**語意清楚、責任單一、由 non-API 層擁有的 canonical public function**

因此 F1 的設計目標不是重寫 calculation engine，而是：
- 為 canonical duration 建立一個明確入口
- 讓未來 F2 / F3 有固定 semantic owner 可依附
- 同時完全不影響當前主鏈

## 1.2 F1 完成後應達成的狀態

F1 完成後，系統應同時滿足：
- 已存在一個 canonical pure calculation function
- 該 function 位於 non-API pure layer
- 該 function 可以表達 net canonical duration
- 現有 gross runtime path 完全不變
- 新 function 尚未被任何現有 flow 使用

---

# 2. Recommended Function Specification

## 2.1 Function Purpose

建議新增的 function，其目的應定義為：

- 根據 session 起訖時間與 break punch inputs
- 輸出一個**canonical duration result**
- 明確表達 gross、break、net（canonical）三者關係
- 只負責 calculation semantics
- 不承擔 integration、persistence、policy、reporting 或 API orchestration 責任

## 2.2 Recommended Function Name

建議 function name：
- `calculate_canonical_work_duration`

命名理由：
- `calculate_...` 可延續現有 engine 命名風格
- `canonical_work_duration` 可明確區分它不是單純 gross，也不是僅 break deduction engine
- 名稱本身即可傳達它是未來 canonical semantic owner 的入口

## 2.3 Recommended Function Signature

以下為**規格用 pseudocode**，僅描述 signature，不代表實作：

```python
def calculate_canonical_work_duration(
    punch_in_time: datetime,
    punch_out_time: datetime,
    break_punches: list[BreakPunchDTO],
) -> CanonicalWorkDurationResult
```

### Signature 說明
- `punch_in_time`
  - session start time
- `punch_out_time`
  - session end time
- `break_punches`
  - break punch inputs，沿用現有 pure DTO 型態
  - 規格上建議直接使用 `BreakPunchDTO`

### Signature 設計原則
- 不接受 ORM session object
- 不接受 repo
- 不接受 db session
- 不接受 logger
- 不接受 policy object
- 不接受 API request / response model

也就是：
- **input 必須只包含 calculation 所需的純資料**

---

# 3. Recommended Result Model / DTO

## 3.1 是否需要新的 result DTO

**Yes — 建議需要新的 result DTO。**

原因：
- `BreakDeductionResult` 的 public 語意是 break deduction engine result
- F1 需要一個語意更穩定、名稱更精準的 canonical result model
- 若直接把 future canonical owner 綁死在 `BreakDeductionResult`，會使 public semantic 不夠清晰

## 3.2 Recommended DTO Name

建議 result DTO 名稱：
- `CanonicalWorkDurationResult`

## 3.3 Recommended DTO Fields

以下為**規格用 pseudocode**，僅描述 result model 欄位，不代表實作：

```python
@dataclass
class CanonicalWorkDurationResult:
    gross_minutes: int
    break_minutes: int
    canonical_minutes: int
    valid_break_pair_count: int
    anomaly_count: int
    anomalies: list[BreakAnomaly]
    was_clamped: bool
    pairing_strategy: str
    rounding_strategy: str
```

## 3.4 欄位語意建議

### 必要欄位
- `gross_minutes`
  - 原始工時，不扣 break
- `break_minutes`
  - break deduction 總分鐘數
- `canonical_minutes`
  - canonical duration
  - 在 Option B 語意下即 net work duration

### 可保留的透明欄位
- `valid_break_pair_count`
- `anomaly_count`
- `anomalies`
- `was_clamped`
- `pairing_strategy`
- `rounding_strategy`

這些欄位保留的價值是：
- 能與既有 `calculate_break_deduction(...)` 的透明度維持一致
- 有助於未來 F2/F3 與測試驗證
- 但 F1 仍不得把這些欄位接入任何 runtime 主鏈

## 3.5 Compatibility Note

在 F1 階段：
- `canonical_minutes` 僅代表**新 canonical source 的輸出**
- **不等於** 系統目前 persisted `duration_minutes`
- 不得在文件或 runtime 上宣稱已完成 semantic cutover

---

# 4. Relationship with Existing Functions

## 4.1 與 `calculate_work_duration(...)` 的關係

建議關係：
- **保留不變**
- 視為 existing gross-only helper
- 不重新命名
- 不改 public semantics

### 規格判定
- `calculate_work_duration(...)` 仍是 gross helper
- 不應被 reinterpret 成 canonical function
- F1 不應讓它承擔 net canonical 語意

## 4.2 與 `calculate_break_deduction(...)` 的關係

建議關係：
- **composition / wrapper relation**

也就是：
- 新 canonical function 應重用 `calculate_break_deduction(...)` 的既有 pure calculation capability
- 不重寫 break pairing / anomaly / clamp 核心邏輯
- 新 function 的角色是把 break-aware result 提升為「canonical semantic result」

### 規格判定
- `calculate_break_deduction(...)` 保持既有責任
- 新 canonical function 站在它之上提供語意更清楚的 public entry

## 4.3 與 `resolve_break_deduction(...)` 的關係

建議關係：
- **無 runtime 相依關係**

原因：
- `resolve_break_deduction(...)` 位於 API helper
- F1 目標是建立 non-API semantic owner
- 因此新 canonical function 不應以 API helper 作為 owner 或主要依賴點

### 規格判定
- `resolve_break_deduction(...)` 保持 API integration helper 身分
- 新 canonical function 不應放在 API helper 裡
- 不應由 API helper 定義 canonical semantic

---

# 5. Responsibility / Non-Responsibility Definition

## 5.1 這個 function 能做什麼

它可以：
- 接受純 calculation input
- 計算 gross / break / canonical net
- 回傳 canonical result DTO
- 延續既有 break deduction engine 的 anomaly 與 clamp 資訊
- 作為 future canonical owner 的唯一 pure calculation 入口

## 5.2 這個 function 不能做什麼

它不能：
- 寫 `session.duration_minutes`
- 修改 ORM session state
- 呼叫 repo
- 呼叫 DB
- 呼叫 policy engine
- 呼叫 reporting service
- 讀寫 API request / response model
- 決定是否要寫入 DB
- 決定是否要替換現行 gross path
- 直接參與 punch-out orchestration

## 5.3 非責任邊界

以下責任明確不屬於這個 function：
- API integration
- repo persistence
- policy evaluation wiring
- reporting read-side interpretation
- anomaly audit persistence
- fallback logging orchestration

---

# 6. Recommended File Placement

## 6.1 首選落點

建議優先放在：
- `backend/app/modules/attendance/work_hour_engine.py`

原因：
- 已是 pure function module
- 無 DB / repo / policy import
- 已擁有 gross 與 break-aware net 的 calculation 基礎
- 最符合 F1 Gate 對 non-API pure layer 的要求

## 6.2 替代落點

若人工判定 `work_hour_engine.py` 責任過重，則替代方案可為：
- 新增一個 attendance 內部的 pure/domain calculation 檔案

但仍必須滿足：
- 不在 API 層
- 不在 repo
- 不在 reporting
- 不在 policy orchestration layer

## 6.3 為什麼不能放在 API 層

不能放在 API 層的原因如下：
- API 層負責 orchestration，不應成為 semantic owner
- 若放在 API 層，未來 F2/F3 仍會與 close flow 強耦合
- F1 的核心目標是把 canonical semantic owner 從 API 外移
- 把新 function 放在 API 層會直接違反前置 Audit / Gate 結論

---

# 7. Compatibility Constraints

## 7.1 Runtime Compatibility Constraints

F1 實作後，以下必須保持不變：
- `api/punch.py` 仍以 gross path 作為主鏈輸入
- `repo.close_session()` 仍寫入 gross semantics
- policy evaluation 仍使用 gross path
- reporting / summary 仍讀現有 persisted semantics

## 7.2 Naming Compatibility Constraints

F1 不得：
- 把現有 gross helper 重新標記為 canonical
- 把現有 `duration_minutes` 文件語意偷換為 net
- 在 API contract 或 reporting contract 上提前聲稱 canonical 已切換

## 7.3 Module Compatibility Constraints

F1 不得新增或修改：
- import path
- runtime wiring
- orchestration entry points
- persistence path
- read-side path

---

# 8. Forbidden Wiring Points

以下是 F1 明確的**禁止接線點**。

## 8.1 API 主鏈禁止接線點

新 canonical function 不得接入：
- `backend/app/modules/attendance/api/punch.py::punch_out()`
- 任何 punch-in / punch-out response shaping path

## 8.2 Policy 主鏈禁止接線點

新 canonical function 不得接入：
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/punch_close_domain.py`
- `backend/app/modules/attendance/policy_engine.py`

## 8.3 Persistence 主鏈禁止接線點

新 canonical function 不得接入：
- `backend/app/modules/attendance/repo.py`
- `repo.close_session(...)` 的寫入值來源

## 8.4 Reporting 主鏈禁止接線點

新 canonical function 不得接入：
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/reporting_service.py`
- `backend/app/modules/attendance/reporting_repo.py`

---

# 9. Allowed Implementation Scope

## 9.1 允許動的檔案

F1 spec 對應的未來實作，允許範圍僅限：
- `backend/app/modules/attendance/work_hour_engine.py`
- 或新增一個 attendance 內部 pure/domain calculation 檔案
- 對應的純測試檔案

## 9.2 禁止動的檔案

F1 spec 對應的未來實作，不得修改：
- `backend/app/modules/attendance/api/punch.py`
- `backend/app/modules/attendance/api/break_deduction.py`（除非是極小化純 mapping 調整，且不得涉及 runtime 接線）
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/punch_close_domain.py`
- `backend/app/modules/attendance/policy_engine.py`
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/reporting_service.py`
- `backend/app/modules/attendance/reporting_repo.py`
- 任何 schema / migration 檔

## 9.3 明確不是 F2 / F3

本 spec 對應的工作仍然**不是**：
- policy semantic switch
- persistence semantic switch
- reporting semantic switch
- migration planning
- historical data handling

---

# 10. Test Specification (Spec Only)

本節只定義測試類型，不要求實作。

## 10.1 Pure Function Tests

應至少規劃：
- 無 break punches 時，`canonical_minutes = gross_minutes`
- 有合法 break pairs 時，`canonical_minutes = gross - break`
- break 超過 gross 時，`canonical_minutes = 0`
- 異常 break sequence 時，anomaly metadata 與既有 engine 一致

## 10.2 Compatibility Tests

應規劃驗證：
- 新 function 的存在不改變 `calculate_work_duration(...)` 既有語意
- 新 function 的存在不改變 `calculate_break_deduction(...)` 既有語意
- 新 function 未被 punch-out 主鏈使用

## 10.3 Non-Wiring Evidence

應規劃驗證或人工審查項目：
- `api/punch.py` 未引入新 canonical function
- `service.py` 未引入新 canonical function
- `punch_close_domain.py` 未引入新 canonical function
- `policy_engine.py` 未引入新 canonical function
- reporting path 未引入新 canonical function

---

# 11. Acceptance Criteria

F1 Fix Spec 若要判定為合格，至少必須滿足以下條件：

1. 已定義一個 non-API pure canonical function 的明確目的
2. 已提供 recommended function signature
3. 已提供明確 result DTO / model 建議
4. 已明確說明與 `calculate_work_duration(...)`、`calculate_break_deduction(...)` 的關係
5. 已明確列出責任與非責任
6. 已明確列出 compatibility constraints
7. 已明確列出 forbidden wiring points
8. 已明確限制允許與禁止修改範圍
9. 已明確說明此工作仍屬 F1，而非 F2 / F3
10. 不包含任何 runtime 接線設計或實作指示

---

# 12. Final Specification Summary

本 spec 的最終結論如下：

- F1 應新增一個 non-API pure canonical function
- 建議名稱：`calculate_canonical_work_duration`
- 建議回傳 DTO：`CanonicalWorkDurationResult`
- 建議落點：`backend/app/modules/attendance/work_hour_engine.py`
- 建議透過 **composition / wrapper** 重用 `calculate_break_deduction(...)`
- F1 只建立 canonical source，不替換任何現有 gross runtime path

一句話總結：

**F1 的正確做法，是在 pure calculation layer 建立 canonical semantic owner，但不讓現有系統任何主鏈使用它。**
