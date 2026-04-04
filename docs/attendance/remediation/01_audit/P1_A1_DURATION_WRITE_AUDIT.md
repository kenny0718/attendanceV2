# P1_A1 Duration Write Audit

> **Ticket Type**: Audit
> **Phase**: 1
> **Priority**: Highest
> **Execution Mode**: Read-only
> **Status**: Done
> **Audit Date**: 2026-04-04

---

# 1. Goal

定位 `duration_minutes` 目前的**唯一實際寫入點**，並確認其責任層級是否符合 SA2.1 v2.1 的 canonical work duration 定義。

---

# 2. Context

目前已知風險是：`duration_minutes` 可能被寫成 gross duration，而不是扣除 break 後的 canonical work duration。

本票只回答「誰在寫、寫在哪、何時寫」。

本票**不處理**完整資料流，也**不處理**修正方案。

---

# 3. Scope

## In Scope
- `backend/app/modules/attendance/api/punch.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/work_hour_engine.py`
- `backend/app/modules/attendance/api/break_deduction.py`
- 與 `duration_minutes` 寫入直接相關的 tests

## Out of Scope
- reporting 聚合正確性
- Taipei business date
- breaks layer 邊界整理
- 任何 Fix 設計與 diff

---

# 4. Search Targets

本次實際檢查項目：

1. `duration_minutes` 的實際寫入位置
2. `gross_minutes` / `net_work_minutes` / `break_minutes` 在 punch-out 鏈路中的來源
3. session close / persistence 責任鏈
4. `work_hour_engine` 是否直接參與最終 DB 寫入
5. tests 是否明確驗證 `duration_minutes` 目前語意

---

# 5. Evidence Requirements

本次已完成：

1. 列出實際寫入責任鏈
2. 判定唯一 persistence 寫入點
3. 判定該寫入點所屬 layer
4. 說明與 SA2.1 v2.1 canonical 定義之差異
5. 標記是否觸及高風險核心檔

---

# 6. Output File

輸出檔案固定為：
- `docs/attendance/remediation/01_audit/P1_A1_DURATION_WRITE_AUDIT.md`

---

# 7. Prohibited Actions

本次 Audit 遵守以下限制：
- 未修改 backend code
- 未修改 tests
- 未產出 Fix diff
- 未進入完整 duration flow 設計
- 未處理 reporting 讀取端修正

---

# 8. Audit Result

## 8.1 Executive Conclusion

**結論：在本次審計範圍內，`duration_minutes` 的實際 DB 寫入點為單一路徑、且目前被明確寫成 `gross_minutes`。**

也就是說：
- 寫入決策發生在 `api/punch.py` 的 `punch_out()` 主鏈路
- 實際 persistence 寫入發生在 `repo.py` 的 `close_session()`
- `break_deduction` 僅產生 derived 結果，**不寫回** `session.duration_minutes`
- `service.py` 在本鏈路中只參與 policy evaluation orchestration，**不是** `duration_minutes` 的寫入者
- `work_hour_engine.py` 與目前 punch-out 整合下的 canonical 語意，仍被定義為 **gross duration**，與 SA2.1 v2.1 要求的 net/canonical work duration 不一致

## 8.2 Actual Write Path

### Step 1 — gross minutes 在 API 層被決定
`api/punch.py` 在 `punch_out()` 內直接以：
- `punch_out_time - session.punch_in_time`
- `int(total_seconds / 60)`

計算出 `gross_minutes`。

### Step 2 — break deduction 被標示為 derived only
同一條鏈路接著呼叫 `resolve_break_deduction(...)`，但註解與行為都明確表示：
- `deduction_result.net_work_minutes` 僅供 derived / informational 使用
- `session.duration_minutes must remain gross_minutes`

### Step 3 — service 不寫 duration
`service.build_punch_out_policy_evaluation(...)` 雖接收 `gross_minutes`，但用途是 policy evaluation orchestration，沒有 session persistence。

### Step 4 — repo.close_session 為唯一實際寫回點
`repo.close_session(...)` 接收外部傳入的 `duration_minutes`，然後直接做：
- `session.duration_minutes = duration_minutes`
- `commit()`
- `refresh()`

因此：

**唯一實際 DB 寫入點 = `AttendanceSessionRepository.close_session()`**

但：

**真正的寫入值決策者 = `api/punch.py::punch_out()`**

## 8.3 Layer Ownership Judgment

### Primary decision layer
- **API layer (`api/punch.py`)**

原因：
- `gross_minutes` 在這裡被直接計算
- break deduction 在這裡被整合
- 寫入參數在這裡被明確指定為 `gross_minutes`

### Persistence layer
- **Repo layer (`repo.py`)**

原因：
- `close_session()` 是最終把值寫進 `session.duration_minutes` 的地方
- repo 本身不重新計算，也不改寫語意，只執行 persistence

### Non-writer layers
- **Service layer (`service.py`)**：不寫 `duration_minutes`
- **Break deduction helper (`api/break_deduction.py`)**：明確禁止寫 `session.duration_minutes`
- **Work hour engine (`work_hour_engine.py`)**：目前提供 gross duration 計算與 break deduction engine，但未在本鏈路中作為 net canonical writer

## 8.4 Single Writer Determination

在本次已讀範圍內，沒有看到第二條主鏈路會在 close flow 中競寫 `session.duration_minutes`。

本票可做的保守結論是：

- **單一 persistence writer：YES**
- **單一主鏈路決策者：YES（目前定位在 `api/punch.py::punch_out()`）**
- **多路徑競寫證據：本次審計範圍內未發現**

## 8.5 Evidence from Tests

測試也支持目前語意：

1. `test_punch_break_integration.py`
   - 明確驗證有 break punches 時，`duration_minutes` 仍寫入 gross
2. `test_work_hour_engine.py`
   - `calculate_work_duration()` 的說明與測試都維持 gross semantics
3. `test_punch_api.py`
   - 只驗證 punch-out 後 `duration_minutes` 非空，未主張 net semantics

因此目前 code + tests 是一致的：

**系統現況的 canonical 實作其實是 gross，不是 net。**

## 8.6 SA2.1 v2.1 Gap

若依先前治理基準：
- SA2.1 v2.1 期望 `session.duration_minutes = work_duration = raw_duration - break_duration`

則目前實作存在明確偏差：
- 現況：`session.duration_minutes = gross_minutes`
- break deduction：只做 derived informational result，不回寫 DB

所以本票結論是：

**目前 `duration_minutes` 的寫入點雖然單一且可控，但其寫入語意與目標 canonical 定義不一致。**

---

# 9. Risk Level

**HIGH**

原因：
1. 這是 Attendance 模組最上游的工時語意入口
2. reporting / summary / policy 之後都可能讀取這個欄位
3. 現在若以 gross 當 canonical，後續修整將涉及語意遷移風險
4. 主要決策點落在 `api/punch.py`，而非更穩定的 domain/service 計算責任層

---

# 10. Open Questions

1. 是否存在本票範圍外的 legacy 路徑也會寫 `session.duration_minutes`？
2. `policy_engine` / `build_policy_evaluation()` 對 gross semantics 的依賴程度多高？
3. `reporting` 是否已全面把 `duration_minutes` 視為 canonical work duration？
4. 若改為 net canonical，是否會影響既有 API response contract / tests / summary totals？

---

# 11. Gate Recommendation

**Gate Recommendation: Pending, but audit supports Phase 1 continuing to `P1_A2 Duration Flow Audit`.**

原因：
- 本票已證明寫入點單一且可控
- 但尚未完成完整 flow 審查
- 尚未盤清下游 read path、policy dependence、與更完整的 canonical responsibility boundary

因此目前建議：

- ✅ 允許進入下一張 Audit：`P1_A2 Duration Flow Audit`
- ❌ 尚不建議直接進入 Fix
- ❌ 尚不能對 Phase 1 給出 Gate = YES

---

# 12. Summary Statement

本票最重要的結論只有一句：

**`duration_minutes` 目前是由 `api/punch.py` 決定為 `gross_minutes`，再經 `repo.close_session()` 單一路徑寫回 DB；寫入點可控，但語意與 SA2.1 v2.1 目標 canonical 定義不一致。**
