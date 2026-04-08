# P1 Phase Gate Review

> **Document Type**: Phase Gate Review
> **Phase**: 1 — Canonical Work Duration Alignment
> **Purpose**: Provide decision material for human review only
> **Decision Authority**: Human reviewer
> **Execution Rule**: This document does not authorize Fix by itself
> **Audit Inputs**:
> - `docs/attendance/remediation/01_audit/P1_A1_DURATION_WRITE_AUDIT.md`
> - `docs/attendance/remediation/01_audit/P1_A2_DURATION_FLOW_AUDIT.md`
> - `docs/attendance/remediation/00_control/ATTENDANCE_REMEDIATION_GOVERNANCE_CONTROL.md`
> **Last Updated**: 2026-04-04

---

# 0. Purpose

本文件的目的不是替人工做決策，而是把 Phase 1 已完成的 Audit 結論整理成可用於 Gate 判讀的材料。

本文件只做三件事：

1. 整理 Current State
2. 定義 SA2.1 目標語意
3. 提供 Option A / Option B 的影響分析與 Gate 建議材料

本文件**不做**以下事情：
- 不修改任何程式碼
- 不產出 Fix diff
- 不替人工直接選擇 Option A 或 Option B
- 不授權直接進入 Fix

---

# 1. Current State

## 1.1 `duration_minutes` 的實際語意

依 `P1_A1` 與 `P1_A2` 已確認：

- `duration_minutes` 目前在 `punch_out close flow` 中被決定為 `gross_minutes`
- 並於 `repo.close_session()` 的 session close transaction 中寫入 DB
- 因此目前 stored `duration_minutes` 的實際語意是：
  - **gross persisted duration**
  - 不是 net canonical work duration

## 1.2 依賴關係總覽

### API / close flow
- `api/punch.py::punch_out()` 直接計算 `gross_minutes`
- 同一條 close flow 決定把 `gross_minutes` 傳入後續 policy 與 persistence

### Policy
- `service.build_punch_out_policy_evaluation(...)` 以 `gross_minutes` 往下傳
- `punch_close_domain.build_policy_evaluation(...)` 在 evaluation 前先把：
  - `session.duration_minutes = gross_minutes`
- `policy_engine.evaluate()` 再讀：
  - `work_minutes = session.duration_minutes or 0`

結論：
- **policy 目前依賴 gross semantics**

### Repo
- `repo.close_session()` 不自行重算 duration
- 只寫入外部傳入的 `duration_minutes`
- 目前該值是 `gross_minutes`

結論：
- **repo 是 persistence layer，不是 canonical semantic owner**

### Reporting / Summary
- `api/reporting.py` 直接回傳 `s.duration_minutes`
- `reporting_service.py` 直接聚合：
  - `sum(s.duration_minutes or 0 for s in sessions)`

結論：
- **reporting / summary 目前依賴 gross semantics**

## 1.3 Break Deduction 的角色

依 `P1_A2` 已確認：

- `resolve_break_deduction(...)` 會產生：
  - `break_minutes`
  - `net_work_minutes`
- 但 helper 邊界明確禁止：
  - 寫 `session.duration_minutes`
  - 呼叫 `repo.close_session()`
  - 決定 gross / net business rule

因此 break deduction 在現況中的角色是：

- **derived calculation only**
- **informational side-channel only**
- **不參與 persistence**
- **不參與 policy 主輸入**

---

# 2. Target Definition（SA2.1）

本 Phase 的目標語意依治理與先前 Audit 前提可定義為：

## 2.1 Target Canonical Definition

- `raw_duration = punch_out_time - punch_in_time`
- `break_duration = validated break deduction`
- `canonical_duration = raw_duration - break_duration`
- `session.duration_minutes = canonical_duration`

也就是：

**canonical duration 應為 net（raw - break）**

## 2.2 與 Current State 的差異

現況：
- `session.duration_minutes = gross_minutes`

目標：
- `session.duration_minutes = net canonical work duration`

因此 Phase 1 的核心不是單純重命名，而是：

- **canonical semantic change**
- 並且會牽動 policy / reporting / tests 的一致性

---

# 3. Decision Options

本 Gate Review 僅提供兩個決策選項，供人工判斷。

## Option A

### 定義
- 維持 gross 為 canonical
- 不修改現有系統

### 實際含義
這代表接受目前系統狀態：
- `duration_minutes = gross_minutes`
- `net_work_minutes` 只維持 derived/informational 身分
- policy / reporting / summary 持續依賴 gross semantics

## Option B

### 定義
- 改為 net canonical duration
- 調整 API / policy / reporting / tests

### 實際含義
這代表要把 canonical 語意切換成：
- `duration_minutes = raw - break`

並且讓：
- close flow
- policy input
- persistence
- reporting / summary
- tests

都共同對齊同一個 net canonical 定義

---

# 4. Option Analysis

# 4.1 Option A — 維持 gross 為 canonical

## 4.1.1 影響範圍

### API
- 不需修改 `api/punch.py`
- 現有 close flow 保持不變

### Service
- 不需修改 `service.py`
- policy orchestration 保持現狀

### Repo
- 不需修改 `repo.py`
- `close_session()` 持續寫入 gross

### Policy
- 不需修改 `policy_engine.py`
- `work_minutes` 繼續等於 gross persisted duration

### Reporting
- 不需修改 `api/reporting.py`
- 不需修改 `reporting_service.py`
- summary totals 持續反映 gross semantics

### Tests
- 多數既有 tests 可維持不變
- 不需大規模重寫驗證前提

## 4.1.2 風險等級

**Risk Level: Medium**

原因：
- 短期變更風險低，因為幾乎不動系統
- 但中長期語意風險仍存在，因為這代表：
  - 與 SA2.1 目標不一致
  - 未來 overtime / paid hours / analytics 可能持續建在 gross semantics 上

## 4.1.3 是否需要 migration

**No**

因為不做 semantic change，也不改 stored value。

## 4.1.4 是否影響既有資料

**No**

既有資料保持不變。

## 4.1.5 是否影響對外 API contract

**No immediate contract change**

但需注意：
- 若文件或外部理解已把 `duration_minutes` 視為 canonical net work duration，則會存在語意文件債

## 4.1.6 適用情境

Option A 比較像：
- 接受現況為正式業務定義
- 或決定先延後 SA2.1 對齊

---

# 4.2 Option B — 改為 net canonical duration

## 4.2.1 影響範圍

### API
- `api/punch.py` 不能再直接把 gross 當最終 close value
- close flow 需要改為使用 net canonical duration
- 可能需要縮小 API 層的 semantic ownership

### Service
- `service.build_punch_out_policy_evaluation(...)` 的上游輸入與責任邊界需要同步調整
- 若 policy 需吃 canonical 值，則該 canonical 值必須在 service/domain 層就已完成

### Repo
- `repo.close_session()` 本身可能只需維持 persistence 行為
- 但它會接收到不同的 `duration_minutes` 語意
- 若涉及舊資料與新資料混存，需注意 read-side 解釋一致性

### Policy
- `punch_close_domain.build_policy_evaluation()` 不能再把 gross 塞入 session 作為主輸入
- `policy_engine.evaluate()` 目前直接讀 `session.duration_minutes`
- 因此 overtime / work_minutes 結果可能改變

### Reporting
- `api/reporting.py` 與 `reporting_service.py` 雖可維持讀 `duration_minutes`
- 但聚合結果會因 stored value 從 gross 改為 net 而改變
- user-summary / company-summary 的 totals 會受影響

### Tests
- `test_punch_break_integration.py` 需更新
- `test_policy_engine.py` 需重新確認 `work_minutes` 假設
- reporting summary 相關 tests 需更新 totals 前提
- 其他依賴 gross semantics 的測試可能需要補盤點

## 4.2.2 風險等級

**Risk Level: High**

原因：
- 這不是單一欄位修補，而是 canonical semantic shift
- 會影響 persistence、policy、reporting、tests
- 若沒有 decomposition，極容易在高風險核心檔形成擴散修改

## 4.2.3 是否需要 migration

**Likely Yes / At least migration plan required**

原因：
- 既有資料中的 `duration_minutes` 目前是 gross semantics
- 若未來新資料改為 net semantics，將出現同欄位跨時期語意不一致

即使最終不做資料回填，也至少需要：
- 一份 migration plan
- 或一份明確的 historical data handling decision

## 4.2.4 是否影響既有資料

**Yes**

至少會影響對既有資料的解讀方式；若選擇實際回填，則會直接影響 stored historical data。

## 4.2.5 是否影響對外 API contract

**Possibly Yes**

即使欄位名稱不變，API 對外回傳的 `duration_minutes` 數值語意會改變。

因此可能影響：
- 客戶端期待
- 報表結果解讀
- 下游整合方對 `duration_minutes` 的認知

## 4.2.6 適用情境

Option B 比較像：
- 明確要求與 SA2.1 對齊
- 願意接受 semantic migration 成本
- 願意同步處理 policy / reporting / tests / 資料處理計畫

---

# 5. Canonical Responsibility Definition

## 5.1 不可由哪一層負責

依本次 Gate Review 與已完成 Audit：

- **不可由 API layer 直接負責 canonical duration 決策**

原因：
1. canonical duration 是 domain semantics，不只是 request orchestration
2. policy / repo / reporting 都依賴此值
3. 若繼續由 router 決定，未來 semantic change 會持續外溢到多層

## 5.2 建議責任層

**建議責任層：domain / calculation layer**

理想責任應為：
- 在 close 前輸出單一 canonical duration
- 可同時供 policy、persistence、reporting 對齊
- 不混入 router / response shaping / DB transaction 責任

## 5.3 實務上可接受的形式

可接受的責任形式應接近：

- pure calculation layer
- domain calculator
- canonical duration resolver

但本文件**不指定具體實作方案**，只定義責任方向：

- **責任應在非 API 的 domain / calculation layer**

---

# 6. Gate Review Summary

## 6.1 Current State Summary

目前實際狀態：
- `duration_minutes = gross_minutes`
- policy 依賴 gross
- reporting / summary 依賴 gross
- `net_work_minutes` 僅為 derived
- repo 只做寫入，不擁有 semantic decision

## 6.2 Decision Tension

本 Phase 的人工決策核心不是「有沒有 bug」而已，而是：

- 是否接受 gross 作為正式 canonical 語意
- 或要求系統改為 SA2.1 的 net canonical 語意

這是一個：
- architecture decision
- semantic decision
- migration decision

不是單純 patch 級別的 bug fix

---

# 7. Gate Recommendation Material

## 7.1 是否可以直接進 Fix？

**NO**

原因：
- 目前尚未做 Option A / B 的人工決策
- 若選 Option B，影響面會跨 API / service / repo / policy / reporting / tests
- 直接進 Fix 會違反 governance 中的 decomposition 與 scope control 原則

## 7.2 是否必須先做 decomposition？

**YES**

原因：
- 若要改 canonical semantic，不能一次在高風險檔案中混合修改
- 至少需要先拆出：
  - canonical decision owner
  - policy alignment scope
  - reporting alignment scope
  - test alignment scope

## 7.3 是否需要 migration plan？

**If Option B, YES**

原因：
- 現有 historical `duration_minutes` 是 gross semantics
- 若未來改成 net semantics，至少需要先定義：
  - 歷史資料是否回填
  - 歷史資料是否保留 gross
  - reporting 如何解讀舊資料與新資料

若最後選 Option A，則 migration plan 可不需要。

---

# 8. Human Review Questions

人工 Gate Review 時，至少應回答：

1. 是否接受目前 gross semantics 成為正式 canonical 定義？
2. 是否要求與 SA2.1 對齊為 net canonical duration？
3. 若選 Option B，是否接受 semantic migration 成本？
4. 若選 Option B，是否先要求 decomposition 與 migration plan？
5. 是否允許在未完成這些前提前直接進入 Fix？

---

# 9. Non-Decision Statement

本文件不替人工選擇：
- Option A
- 或 Option B

本文件只提供：
- 現況整理
- 目標定義
- 影響分析
- Gate 前置條件

最終決策必須由人工做出。
