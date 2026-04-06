# P1 F1 Gate — Canonical Source First-Cut Readiness Review

> **Document Type**: Phase Gate Review
> **Phase**: 1 — Option B / F1
> **Purpose**: Determine whether Phase F1 can safely begin
> **Execution Rule**: Human review material only; not an implementation authorization by itself
> **Inputs**:
> - `docs/attendance/remediation/02_fix/P1_F1_AUDIT_CANONICAL_SOURCE.md`
> - `docs/attendance/remediation/02_fix/P1_OPTION_B_FIX_DECOMPOSITION.md`
> **Last Updated**: 2026-04-06

---

# 0. Purpose

本文件的目的，是確認 **Option B 的 F1 第一刀** 是否可以安全開始。

F1 的定義已明確：
- 引入 canonical 計算來源
- canonical 目標語意為 net duration
- 但 **F1 不得改變現有系統行為**
- 現況仍必須維持：`duration_minutes = gross_minutes`

因此本 Gate 文件只回答：

1. F1 是否有足夠低的實作風險
2. 需要遵守哪些不可破壞的限制
3. 第一刀允許改哪些範圍
4. 是否准入 F1 Fix

本文件**不做**以下事情：
- 不修改任何 code
- 不產出 diff
- 不設計 F2 / F3 實作
- 不授權直接切換 persistence 或 reporting semantics

---

# 1. Current Gate Context

依前置文件，現況已可確定：

- `duration_minutes` 現在是 gross semantics
- policy evaluation 目前依賴 gross
- reporting / summary 目前依賴 gross
- `work_hour_engine.py` 已有 break-aware 純計算能力
- 但目前尚未存在一個**清楚命名、由 non-API 層擁有的 canonical public function**

因此 F1 的任務不是切換主鏈，而是：

- **建立 canonical source**
- 同時確保主鏈完全不採用它

這也是 F1 是否安全的核心判準。

---

# 2. Risk Assessment

## 2.1 風險一：新 canonical function 被誤用

### 風險描述
一旦新增 canonical function，最直接的風險不是它算錯，而是：
- 被 `api/punch.py` 提前接入主鏈
- 被 `service.py` 或 `punch_close_domain.py` 拿來替換 gross input
- 被後續開發者誤認為已經完成 Option B 切換

### 風險等級
**Medium**

原因：
- F1 本身應是 low-risk
- 但「誤接線」會立刻把 F1 變成 F2 / F3
- 風險主要來自整合錯誤，不是純函式本身

### Gate 判定
此風險**可控**，前提是：
- canonical function 必須明確標示為 F1-only introduction
- 不可被現有 flow 使用
- 不可替換 `gross_minutes` 現行來源

---

## 2.2 風險二：影響 policy evaluation

### 風險描述
目前 policy evaluation 在 close flow 中使用的是 gross semantics。
若 F1 階段不慎把 canonical net 接入：
- `work_minutes` 會改變
- overtime calculation 可能改變
- policy 行為將在未經 Gate 的情況下提前切換

### 風險等級
**High if miswired, Low if isolated**

### Gate 判定
這不是禁止進 F1 的理由，但必須加上明確隔離條件：
- F1 不得修改 `service.py` 的 policy input 語意
- F1 不得修改 `punch_close_domain.py` 目前的 gross evaluation path
- F1 不得修改 `policy_engine.py` 的 consumption semantics

換句話說：
- **只要 canonical function 不進 policy path，風險可接受**

---

## 2.3 風險三：被 reporting 誤讀

### 風險描述
若 F1 階段讓 reporting 側誤以為 canonical 已完成切換，可能造成：
- `duration_minutes` 語意被錯誤重述
- summary 文件或 read-side 設計提前對齊 net
- F3 前出現文件與系統不一致

### 風險等級
**Medium**

### Gate 判定
此風險可透過範圍限制消除：
- F1 不得修改 `api/reporting.py`
- F1 不得修改 `reporting_service.py`
- F1 不得修改任何 read-side contract 說明，使其看起來像已完成 net cutover

也就是：
- **F1 只能建立計算能力，不能傳遞已切換的訊號**

---

# 3. Non-Negotiable Constraints

F1 若要成立，以下限制不可破壞：

## 3.1 不可改 API contract

F1 不得造成以下變化：
- `PunchOutResponse.duration_minutes` 語意改變
- `/sessions` 或各類 summary response 語意改變
- API 對外欄位新增/刪除以表示 canonical 已啟用

## 3.2 不可改 DB

F1 不得：
- 修改 schema
- 修改 migration
- 修改 persisted `duration_minutes` 寫入值
- 引入任何資料修補或資料回填

## 3.3 不可改 `duration_minutes` semantics

F1 完成後，系統仍必須維持：
- `duration_minutes = gross_minutes`
- `repo.close_session()` 寫入語意不變
- policy / reporting 觀察到的 stored semantics 不變

---

# 4. Required Safety Conditions

若要准入 F1，至少必須同時滿足以下條件。

## 4.1 canonical function 必須是 pure function

必須滿足：
- 無 DB access
- 無 repo imports
- 無 policy imports
- 無 API request / response dependency
- 無 side effects
- 不寫 session state

這一條是 F1 的核心安全條件。

## 4.2 不可被現有 flow 使用

F1 新增的 canonical function：
- 不可接到 `api/punch.py::punch_out()` 的現行 close path
- 不可接到 policy evaluation path
- 不可接到 reporting read path
- 不可接到 repo persistence path

也就是：
- **可以存在，但不能成為現行 runtime semantic owner**

## 4.3 不可替換現有 gross 邏輯

F1 不得：
- 移除現有 gross calculation path
- 改寫 gross 為 canonical net
- 把 `gross_minutes` 命名或語意偷換為 canonical

F1 的本質是 introduction，不是 substitution。

## 4.4 canonical owner 必須位於 non-API 層

依前置 Audit，最適合的落點是：
- `backend/app/modules/attendance/work_hour_engine.py`

或：
- 新增一個 attendance 內部的 pure/domain calculation 檔案

但不得位於：
- `api/punch.py`
- `api/break_deduction.py`
- `service.py`
- `punch_close_domain.py`

---

# 5. Allowed Change Scope for F1 First Cut

若本 Gate 准入 F1，第一刀允許修改範圍如下。

## 5.1 允許修改

### 優先允許
- `backend/app/modules/attendance/work_hour_engine.py`

### 條件式允許
- 新增一個 attendance 內部 pure/domain calculation 檔案
- 對應的純測試檔案

### 可接受但應極小化
- `backend/app/modules/attendance/api/break_deduction.py`
  - 僅在必要時做最小限度的純 mapping / wrapper 對齊
  - 不可引入主鏈語意切換

## 5.2 禁止修改

F1 第一刀不得修改：
- `backend/app/modules/attendance/api/punch.py`
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/punch_close_domain.py`
- `backend/app/modules/attendance/policy_engine.py`
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/reporting_service.py`
- 任何 schema / migration 檔

---

# 6. Gate Decision

## 6.1 是否可進 F1 Fix

**YES**

## 6.2 准入理由

可以進 F1 的原因是：

1. 現有系統已具備 net calculation 的純計算基礎
2. canonical source 的責任落點已被明確盤定
3. F1 的修改可以被限制在 pure calculation layer
4. 只要嚴格禁止主鏈接線，F1 不會影響：
   - API contract
   - DB
   - `duration_minutes` semantics
   - policy evaluation
   - reporting read path

因此：
- **F1 具有可隔離、可回退、低風險的前提**
- 可以安全進入第一刀

---

# 7. Conditions Attached to YES

本 Gate 的 YES 不是無條件 YES，而是附帶條件的 YES。

## 7.1 實作邊界條件

F1 實作必須同時滿足：
- 只建立 canonical pure calculation source
- 不替換現行 gross path
- 不接入任何現行 runtime 主鏈
- 不改 response contract
- 不改 persistence semantics

## 7.2 驗收條件

F1 完成後必須能證明：
- canonical function 已存在
- 該 function 位於 non-API pure layer
- 該 function 尚未被現有 flow 使用
- 現有 gross 行為完全不變

若無法證明上述四點，則 F1 視為越界。

---

# 8. What Would Turn This Gate to NO

以下情況若發生，本 Gate 應立即轉為 **NO**：

1. 計畫修改 `api/punch.py` 主鏈來接入 canonical function
2. 計畫修改 policy evaluation 使其讀 canonical
3. 計畫修改 repo 寫入值
4. 計畫修改 reporting 讀值或對外說明
5. 計畫新增 schema / migration
6. 計畫把 F1 與 F2/F3 混成同一刀

也就是：
- 任何會改變 runtime semantics 的行為，都不再屬於 F1

---

# 9. Final Gate Summary

本文件最終結論如下：

- **F1 Gate Result: YES**
- 但僅限於：
  - 在 non-API pure layer 引入 canonical 計算來源
  - 不改 API contract
  - 不改 DB
  - 不改 `duration_minutes` semantics
  - 不讓現有 flow 使用新 canonical function

一句話總結：

**可以進 F1，但只能做「建立 canonical source」這一刀，不能做任何接線切換。**
