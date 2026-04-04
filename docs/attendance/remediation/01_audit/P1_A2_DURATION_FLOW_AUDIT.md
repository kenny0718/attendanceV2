# P1_A2 Duration Flow Audit

> **Ticket Type**: Audit
> **Phase**: 1
> **Priority**: High
> **Execution Mode**: Read-only
> **Status**: Done
> **Audit Date**: 2026-04-04

---

# 1. Goal

釐清 `duration_minutes`、`gross_minutes`、`net_work_minutes`、`break deduction` 在 Attendance 模組中的完整資料流與責任邊界。

---

# 2. Context

在 `P1_A1` 確認單一寫入點後，仍需追蹤上游與下游流向，才能知道 canonical duration 的真正計算責任是否落在正確層。

本票聚焦在 **flow**，不是單點寫入定位。

---

# 3. Scope

## In Scope
- `backend/app/modules/attendance/api/punch.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/work_hour_engine.py`
- `backend/app/modules/attendance/api/break_deduction.py`
- `backend/app/modules/attendance/punch_close_domain.py`
- `backend/app/modules/attendance/policy_engine.py`
- `backend/app/modules/attendance/reporting_service.py`
- `backend/app/modules/attendance/reporting_repo.py`
- `backend/app/modules/attendance/api/reporting.py`
- 與 duration semantics 相關 tests

## Out of Scope
- 實際 Fix 實作
- Taipei date ownership
- breaks API 責任重分配

---

# 4. Search Targets

本次實際檢查項目：

1. punch-out close flow 的 duration 來源
2. break deduction 如何計入或不計入最終結果
3. policy evaluation 使用哪個 duration 語意
4. `duration_minutes` 被哪些 read path 依賴
5. reporting 是否直接依賴該欄位
6. 是否已有可承接 canonical 責任的純計算層

---

# 5. Evidence Requirements

本次已完成：

1. 從 input 到 DB persistence 的 flow 摘要
2. gross / net / break deduction 的語意切分
3. policy evaluation 與 final persistence 的先後關係
4. reporting read path 清單
5. work hour engine 的現況能力判定

---

# 6. Output File

輸出檔案固定為：
- `docs/attendance/remediation/01_audit/P1_A2_DURATION_FLOW_AUDIT.md`

---

# 7. Prohibited Actions

本次 Audit 遵守以下限制：
- 未修改任何程式碼
- 未產出 Fix diff
- 未變更任何 backend contract
- 未提前改 Gate Result

---

# 8. Audit Result

## 8.1 Executive Conclusion

**依實際 code flow 可確認：`duration_minutes` 在 `punch_out close flow` 中先被決定為 `gross_minutes`，之後於 `session close transaction` 時寫入 `AttendanceSession.duration_minutes`。`break deduction` 雖會產生 `net_work_minutes`，但它只停留在 derived 結果，沒有進入 policy 主輸入，也沒有進入 DB persistence；reporting / summary 下游則直接讀取已寫入的 `duration_minutes`。**

因此目前主鏈事實上是：

- close flow decision = gross
- policy evaluation input = gross
- repo persistence value = gross
- reporting / summary read value = gross
- net 只存在於 break deduction derived result

---

## 8.2 Evidence 1 — Punch-out Flow（gross 計算）

### 實際 code flow
在 `backend/app/modules/attendance/api/punch.py` 的 `punch_out()` 中：

1. 先取得 open session
2. 建立 `punch_out_time = datetime.now(timezone.utc)`
3. 建立 out punch record
4. 直接做：
   - `duration = punch_out_time - session.punch_in_time`
   - `gross_minutes = int(duration.total_seconds() / 60)`

### 審計判定
這裡沒有呼叫其他 canonical calculator 來決定最終 close value。

也就是說：

- **gross 的原始決策點就在 punch-out close flow 本身**
- 這不是推測，而是 `punch_out()` 內直接計算出 `gross_minutes`

---

## 8.3 Evidence 2 — Break Deduction（net 僅 derived）

### 實際 code flow
同一個 `punch_out()` 內，gross 算完之後才會：

- 讀取 `session_punches = repo.get_session_punches(session.id)`
- 呼叫 `resolve_break_deduction(...)`

而 `backend/app/modules/attendance/api/break_deduction.py` 的 helper 邊界明確寫出：

- Cannot call `repo.close_session()`
- Cannot write `session.duration_minutes`
- Cannot run policy evaluation
- Cannot make any business rule decisions about gross/net

helper 內部只會：

1. 過濾 `break_start` / `break_end`
2. map 成 `BreakPunchDTO`
3. 呼叫 `calculate_break_deduction(...)`
4. 回傳 `BreakDeductionResult` 或 fallback result

而 `punch_out()` 本身也有明確註解：

- `deduction_result.net_work_minutes is derived/informational only`
- `session.duration_minutes must remain gross_minutes`

### 審計判定
這表示：

- `break_minutes` / `net_work_minutes` 確實有被算出來
- 但它們**沒有進入 canonical write path**
- net 目前只是 derived side-channel，不是 session close transaction 的輸入

---

## 8.4 Evidence 3 — Policy Evaluation 使用的 duration

### 實際 code flow
`punch_out()` 在 break deduction 後，呼叫：

- `service.build_punch_out_policy_evaluation(..., gross_minutes=gross_minutes)`

接著在 `backend/app/modules/attendance/service.py`，`build_punch_out_policy_evaluation()` 會再委派到：

- `build_policy_evaluation(..., gross_minutes=gross_minutes)`

而 `backend/app/modules/attendance/punch_close_domain.py` 的 `build_policy_evaluation()` 內，實際動作是：

- `session.punch_out_time = punch_out_time`
- `session.duration_minutes = gross_minutes`
- `session.status = "closed"`
- 然後才呼叫 `AttendancePolicyEngine().evaluate(session, policy)`

接著 `backend/app/modules/attendance/policy_engine.py` 的 `evaluate()` 內又明確做：

- `work_minutes = session.duration_minutes or 0`

並以這個 `work_minutes` 做 overtime calculation。

### 審計判定
所以 policy evaluation 使用的 duration 不是 net，也不是另外重算值，而是：

- **在 evaluation 前先塞進 session object 的 gross_minutes**

也就是：

- **policy evaluation 目前依賴 gross semantics**

---

## 8.5 Evidence 4 — Repo Persistence 寫入

### 實際 code flow
在 `backend/app/modules/attendance/api/punch.py` 中，policy evaluation 完成之後，才會呼叫：

- `repo.close_session(..., duration_minutes=gross_minutes, policy_id=policy_eval.policy_id)`

而 `backend/app/modules/attendance/repo.py` 的 `close_session()` 內實際執行：

- `session.punch_out_time = punch_out_time`
- `session.status = 'closed'`
- `session.duration_minutes = duration_minutes`
- `session.policy_id = policy_id`
- `self.db.commit()`
- `self.db.refresh(session)`

### 審計判定
因此 persistence evidence 很清楚：

- repo 寫入的是外部傳入值
- 這次傳入值是 `gross_minutes`
- repo 本身不重算 net，也不做 gross/net 判斷

所以精準說法是：

- **`duration_minutes` 在 close flow 中被決定為 gross**
- **並於 `repo.close_session()` 的 session close transaction 中寫入 DB**

---

## 8.6 Evidence 5 — Reporting / Summary Read Path

### 實際 code flow
在 `backend/app/modules/attendance/api/reporting.py`：

- `/sessions` endpoint 直接把 `s.duration_minutes` 放入 `SessionResponse`
- `/reports/user-summary` 取得 sessions 後，交給 `calculate_user_summary(sessions)`
- `/reports/company-summary` 取得 sessions 後，交給 `calculate_company_summary(sessions)`

而 `backend/app/modules/attendance/reporting_service.py` 內：

- `total_work_minutes = sum(s.duration_minutes or 0 for s in sessions)`
- user summary 與 company summary 都直接聚合 `duration_minutes`

### 審計判定
這代表 reporting / summary read path：

- 不自行重算 duration
- 不讀 `BreakDeductionResult.net_work_minutes`
- 直接信任 DB 中的 `session.duration_minutes`

所以目前 reporting / summary 下游依賴的是：

- **已持久化的 gross semantics**

---

## 8.7 End-to-End Flow Map

依實際 code，可整理成以下主鏈：

1. `api/punch.py::punch_out()`
   - 計算 `gross_minutes`
2. `api/break_deduction.py::resolve_break_deduction()`
   - 產生 `break_minutes` / `net_work_minutes`（derived only）
3. `service.py::build_punch_out_policy_evaluation()`
   - 把 `gross_minutes` 往下傳
4. `punch_close_domain.py::build_policy_evaluation()`
   - 先把 `session.duration_minutes = gross_minutes`
5. `policy_engine.py::evaluate()`
   - 讀 `session.duration_minutes`
6. `repo.py::close_session()`
   - transaction 中寫入 `duration_minutes=gross_minutes`
7. `api/reporting.py` + `reporting_service.py`
   - 讀取並聚合 stored `duration_minutes`

---

## 8.8 明確回答

### Q1. canonical responsibility 應在哪層？

**應在非 API 的 domain / pure calculation layer。**

依實際 flow 判斷，canonical duration 是一個會同時影響：

- policy evaluation
- session persistence
- reporting / summary read path

的核心語意值。

因此它不適合繼續由 `api/punch.py` 這種 router close flow 直接決定。較合理的責任層應該是：

- **純計算層或 domain calculation layer**

也就是一個能在 close 前輸出單一 canonical duration 的地方，再由：

- policy 使用同一值
- repo 寫入同一值
- reporting 讀取同一值

### Q2. 哪裡造成 gross / net 偏移？

**偏移發生在 close flow 的決策段，不是在 repo transaction。**

實際偏移點有兩個連續位置：

1. `api/punch.py::punch_out()`
   - 已經先把主鏈值決定成 `gross_minutes`
   - 並明確註解 `net_work_minutes` 僅 derived

2. `punch_close_domain.py::build_policy_evaluation()`
   - 在 policy evaluation 前，又把 `session.duration_minutes = gross_minutes`

因此 net 雖然存在，但被降級為 side-channel；gross 則被提升成：

- policy 主輸入
- repo 持久化值
- reporting 讀值來源

### Q3. downstream 是否依賴錯誤語意？

**若 SA2.1 v2.1 要求 canonical work duration = raw - break，則 downstream 目前確實依賴了錯誤語意。**

依實際 code：

- `policy_engine.py` 以 `session.duration_minutes` 當 `work_minutes`
- `reporting_service.py` 以 `session.duration_minutes` 聚合 `total_work_minutes`
- `api/reporting.py` 直接回傳 / 使用 `duration_minutes`

而這個 stored value 現在是 gross，不是 net。

所以若 canonical 定義應為 net：

- **policy downstream 依賴的是錯誤語意**
- **reporting / summary downstream 依賴的是錯誤語意**

---

## 8.9 Final Audit Judgment

本票依實際 code flow 的最終判定為：

1. `gross_minutes` 是目前 close flow 的主值
2. `net_work_minutes` 只存在於 break deduction derived result
3. policy evaluation 使用 gross
4. repo persistence 寫入 gross
5. reporting / summary 讀取 gross

因此目前系統中的 `duration_minutes` 主鏈語意是：

- **gross persisted duration**

而不是：

- **net canonical work duration**

---

# 9. Risk Level

**HIGH**

原因：
1. 這不是單點欄位問題，而是整條 close-flow + downstream read model 問題
2. policy 與 reporting 已共同依賴 gross semantics
3. 若直接切換 canonical 語意，影響範圍會跨 API / domain / reporting / tests

---

# 10. Open Questions

1. 是否存在 reporting 以外的模組也把 `duration_minutes` 視為 canonical 工時？
2. overtime / paid hours 的正式業務定義是否本來就應採 net？
3. `build_policy_evaluation_with_schedule_v2()` 是否已代表未來可接受的責任方向？
4. 是否需要先引入單一 canonical duration calculator，才能安全進 Fix？

---

# 11. Gate Recommendation

**Gate Recommendation: NO for direct Fix right now.**

原因：
- 雖然 `P1_A1` 與 `P1_A2` 都已定位問題
- 但目前已確認 downstream 依賴面包含 policy + reporting + tests
- 若不先定義 canonical responsibility 與影響面，就直接修，風險過高

## Required Before Any Fix

至少需先補以下其中一項：

1. 一份更小範圍的 Fix decomposition
2. 明確指定 canonical duration 應由哪個非 API 層決定
3. 明確列出 policy / reporting / tests 的同步調整邊界

因此本票的治理建議是：

- ✅ Phase 1 的 Audit 資訊已足夠進入人工 Gate 判讀
- ❌ 不建議直接進 Fix
- ❌ Gate 目前不應直接判定為 YES
