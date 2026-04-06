# P1 F1 Audit — Canonical Source Inventory

> **Document Type**: F1 Audit Ticket
> **Phase**: 1 — Option B First Cut
> **Scope**: Canonical calculation source inventory only
> **Execution Mode**: Read-only
> **Status**: Done
> **Inputs**:
> - `docs/attendance/remediation/02_fix/P1_OPTION_B_FIX_DECOMPOSITION.md`
> - `backend/app/modules/attendance/api/punch.py`
> - `backend/app/modules/attendance/api/break_deduction.py`
> - `backend/app/modules/attendance/work_hour_engine.py`
> - `backend/app/modules/attendance/punch_close_domain.py`
> - `backend/app/modules/attendance/service.py`
> **Last Updated**: 2026-04-06

---

# 0. Purpose

本文件是 Option B 第一刀（F1）的 Audit 工作票。

本票只做一件事：
- 盤點目前 Attendance 模組內所有與 `duration` 計算相關的來源
- 判定哪一層最適合作為未來的 canonical 計算來源
- 提出 F1 階段的責任放置建議

本文件**不做**以下事情：
- 不修改任何 code
- 不改 API / repo
- 不改 DB
- 不產出 diff
- 不切換任何既有行為

---

# 1. Audit Goal

本票要回答三個問題：

1. 目前 `gross_minutes` 在哪裡算？
2. 目前 `break deduction` / `net_work_minutes` 在哪裡算？
3. 若 Option B 要建立 canonical duration source，最適合放在哪個模組？

---

# 2. Scope

## In Scope
- `backend/app/modules/attendance/api/punch.py`
- `backend/app/modules/attendance/api/break_deduction.py`
- `backend/app/modules/attendance/work_hour_engine.py`
- `backend/app/modules/attendance/punch_close_domain.py`
- `backend/app/modules/attendance/service.py`

## Out of Scope
- `repo.py` 實際寫入切換
- reporting read-side 切換
- policy semantic switch
- schema / migration
- 任何 F2 / F3 實作

---

# 3. Inventory Result

## 3.1 Source A — `gross_minutes`

### 目前在哪裡算
目前 `gross_minutes` 是在：
- `backend/app/modules/attendance/api/punch.py`
- `punch_out()` 主鏈路內直接計算

### 計算方式
目前實作為：
- `duration = punch_out_time - session.punch_in_time`
- `gross_minutes = int(duration.total_seconds() / 60)`

### 判定
這代表：
- 目前 gross duration 的主決策點仍在 **API 層**
- 這不符合 F1 對 canonical source 的要求
- 因為 canonical 計算責任不應落在 API orchestration 層

### 結論
- `gross_minutes` **已有既存算法**
- 但目前的**實際使用位置不理想**
- 它應被下沉到 engine/domain 層統一承接

---

## 3.2 Source B — `break deduction`

### 目前在哪裡算
目前 `break deduction` 的整合入口在：
- `backend/app/modules/attendance/api/break_deduction.py`
- 對外函式：`resolve_break_deduction(...)`

但真正的 break deduction 純計算發生在：
- `backend/app/modules/attendance/work_hour_engine.py`
- 函式：`calculate_break_deduction(...)`

### `resolve_break_deduction(...)` 的責任
這個 helper 只負責：
- 過濾 `break_start` / `break_end`
- map 成 `BreakPunchDTO`
- 呼叫 `calculate_break_deduction(...)`
- 在 exception 時 fallback 成 gross

它的邊界明確禁止：
- 寫 `session.duration_minutes`
- 呼叫 `repo.close_session()`
- 決定 gross / net business rule
- shape API response 以外的語意切換

### `calculate_break_deduction(...)` 的能力
`work_hour_engine.py` 已具備以下能力：
- 以 `punch_in_time`、`punch_out_time`、`break_punches` 計算 `gross_minutes`
- 計算 `break_minutes`
- 輸出 `net_work_minutes`
- 處理異常 pairing / clamp / anomaly collection

### 判定
這代表：
- `break deduction` 的**純計算核心已存在**
- 而且已在 **非 API 層**
- 它是目前最接近 canonical duration source 的既有能力

### 限制
但現況仍有兩個限制：

1. 它的 public 語意目前是「break deduction result」
   - 不是明確命名為 canonical work duration calculator

2. 它的整合入口仍由 API helper `resolve_break_deduction(...)` 主導
   - 因此目前主鏈上仍由 API 決定是否使用 net

### 結論
- break-aware net 計算能力**已存在**
- 但 canonical semantic owner **尚未真正成立**

---

## 3.3 Source C — `work_hour_engine` 是否已可產生 canonical（net）

### 現況能力
`work_hour_engine.py` 目前有兩種相關能力：

1. `calculate_work_duration(...)`
   - 輸出 gross only
   - 是純函式
   - 不含 break deduction

2. `calculate_break_deduction(...)`
   - 輸出 `BreakDeductionResult`
   - 內含：
     - `gross_minutes`
     - `break_minutes`
     - `net_work_minutes`

### 能否產生 canonical（net）
**可以，但不是以清晰的 canonical API 形式存在。**

也就是：
- engine 其實已能算出 net
- 只是目前 net 是 `BreakDeductionResult` 的其中一個欄位
- 而不是一個明確、單一責任、可被主鏈直接採用的 canonical 計算入口

### 判定
因此本票的保守結論是：
- `work_hour_engine.py` 已具備 **承接 canonical source 的能力基礎**
- 但**尚未具備清晰完成態的 canonical public function**

---

# 4. Reuse Assessment

## 4.1 是否已有可重用 function

### 可直接重用的部分
以下能力可直接視為可重用基礎：

- `calculate_work_duration(...)`
- `calculate_break_deduction(...)`
- `BreakPunchDTO`
- `BreakDeductionResult`

### 不適合作為 canonical owner 的部分
以下函式或模組不適合作為 canonical semantic owner：

- `api/punch.py::punch_out()`
- `api/break_deduction.py::resolve_break_deduction(...)`
- `service.py` 內的 orchestration 入口
- `punch_close_domain.py::build_policy_evaluation(...)`

原因：
- 它們不是純 calculation owner
- 它們主要是 orchestration / integration / evaluation path
- 放在這些層會讓 canonical semantic 再次被主鏈綁死

---

# 5. Canonical Responsibility Recommendation

## 5.1 核心結論

**canonical 計算責任不應放在 API 層。**

這一點已可明確成立，原因如下：
- API 層目前負責 punch-out orchestration、repo interaction、audit helper integration、response shaping
- 若 canonical semantic 繼續由 API 決定，未來 F2 / F3 切換仍會高度耦合 close flow
- 這與 F1「先建立穩定 canonical source、但不影響既有行為」的目標衝突

---

## 5.2 最適合的放置模組

### 首選：`backend/app/modules/attendance/work_hour_engine.py`

本票建議：
- **canonical calculation source 應優先放在 `work_hour_engine.py`**

原因：
- 它已是 pure function module
- 無 DB access
- 無 repo imports
- 無 policy imports
- 已具備 gross 與 break-aware net 的核心計算能力
- 最接近可被 F1 安全擴充的地方

### 次選：新增非 API 的 domain/pure calculation 檔案

若人工認為 `work_hour_engine.py` 的責任已偏重，則次選是：
- 新增一個 attendance 內部的 pure/domain calculation 檔

例如概念上可放在：
- `backend/app/modules/attendance/...` 之下的純 calculation/domain 檔

但原則仍是：
- 不可放在 API 層
- 不可放在 repo
- 不可放在 reporting

---

# 6. Need-New-Function Judgment

## 6.1 是否需要新增 pure calculation function

**Yes — 建議新增。**

理由不是因為目前完全不能算，而是因為：
- 現有 `calculate_work_duration(...)` 只有 gross
- 現有 `calculate_break_deduction(...)` 雖能輸出 net，但其 public 語意是 break deduction engine
- F1 需要的是一個**語意明確、單一責任、可作為 future canonical source 的入口**

## 6.2 新函式應滿足的條件

新 pure calculation function 應滿足：
- 位於 engine / domain 層
- 不接觸 DB
- 不接觸 repo
- 不接觸 policy
- 不接觸 API request / response
- 只根據：
  - `punch_in_time`
  - `punch_out_time`
  - break punches / normalized break inputs
- 輸出可明確表示：
  - gross
  - break
  - canonical net

## 6.3 與既有函式的關係建議

建議模式為：
- 重用 `calculate_break_deduction(...)` 作為 break-aware 計算核心
- 在 engine/domain 層新增一個更高階、語意更明確的 pure canonical wrapper

這樣做的好處是：
- 不需重寫 break pairing 邏輯
- 不需把 canonical semantic owner 留在 API helper
- 可在 F1 階段先建立 canonical source，而不切換任何行為

---

# 7. Final Recommendation

## 7.1 建議的 canonical 計算責任

本票建議：
- **canonical duration owner 應位於 non-API pure calculation layer**
- 最佳位置是：`backend/app/modules/attendance/work_hour_engine.py`

## 7.2 建議的檔案落點

### 建議優先方案
- 放在 `backend/app/modules/attendance/work_hour_engine.py`

### 可接受替代方案
- 新增一個 attendance 內部的 pure/domain calculation 檔案

### 不建議方案
- `backend/app/modules/attendance/api/punch.py`
- `backend/app/modules/attendance/api/break_deduction.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/punch_close_domain.py`

---

# 8. Audit Conclusion

本票結論如下：

1. `gross_minutes` 目前在 `api/punch.py::punch_out()` 直接計算
2. `break deduction` 的 pure engine 已存在於 `work_hour_engine.py`
3. `calculate_break_deduction(...)` 已可產生 `net_work_minutes`
4. 目前尚不存在一個明確命名、由 non-API 層擁有的 canonical public function
5. F1 若要安全落地，應：
   - 不改現有行為
   - 不碰 API / repo / DB
   - 先在 engine/domain 層建立 canonical 計算來源
6. 最適合承接此責任的現有模組是：
   - `backend/app/modules/attendance/work_hour_engine.py`

---

# 9. F1 Gate Suggestion

**Gate Suggestion: Proceedable**

條件是：
- 僅限建立 canonical 計算來源
- 不切換主鏈使用值
- 不修改 persistence semantics
- 不變更 API contract

若超出上述邊界，則已不屬於 F1，而會提前進入 F2 / F3 風險區。