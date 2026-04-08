# P3_A1 Breaks Layer Audit Report

> **Ticket Type**: Audit  
> **Phase**: 3  
> **Priority**: Medium-High  
> **Execution Mode**: Read-only / Documentation  
> **Status**: Done

---

## 1. Summary（PASS / PASS WITH NOTES / FAIL）

**PASS WITH NOTES**

結論依程式碼證據如下：

- breaks layer 未發現直接改寫 `session.duration_minutes` 的路徑
- break deduction 目前維持在 derived layer
- policy / reporting 目前仍以 canonical `session.duration_minutes` 為主

但存在幾個責任邊界上的備註事項：

- `api/breaks.py` 的 `get_break_punches()` 與 `update_punch_note()` 直接使用 `db.query(...)` / `db.commit()`，未完全走 repo 集中存取
- `service.py` 的 missing-segment dry-run 會把 `break_start` / `break_end` 當作 actual segment 分段訊號使用，屬於間接互動，但未改變 canonical
- `punch_close_domain.py` 的 schedule-aware path 會把 `work_minutes` 寫進 `session.duration_minutes`，其變數命名與 canonical gross semantic 之間存在語意漂移風險；但在本票 breaks 審計範圍內，未見 break deduction 值進入該路徑

---

## 2. Files Inspected

已檢查：

- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/api/break_deduction.py`
- `backend/app/modules/attendance/api/punch.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/punch_close_domain.py`
- `backend/app/modules/attendance/policy_engine.py`
- `backend/app/modules/attendance/reporting_service.py`
- `backend/app/modules/attendance/api/reporting.py`

已抽查 tests：

- `backend/app/modules/attendance/tests/test_punch_break_integration.py`
- `backend/app/modules/attendance/tests/test_break_out_enforcement.py`
- `backend/app/modules/attendance/tests/test_break_punches_boundary.py`
- `backend/app/modules/attendance/tests/test_work_hour_engine.py`
- `backend/app/modules/attendance/tests/test_reporting_user_summary.py`

---

## 3. Layer Responsibility Matrix

### API layer — `api/breaks.py`

**responsibility:**
- 接收 break-out / break-in / break-punches / note update request
- 驗證 open session 是否存在
- 進行 feature gate 與 actor scope 控制
- 建立 break punch 寫入
- break-out 進行 location policy enforcement

**judgment:**
- `break_out()` / `break_in()` 主要是 orchestration + request boundary 處理，整體合理
- `get_break_punches()` 直接查 `AttendancePunch`
- `update_punch_note()` 直接查 `AttendancePunch` 並 `db.commit()`

**violation:**
- 有輕度越界
- 證據：API 層直接做 ORM query 與 commit，未完全經由 repo 集中
- 但此越界未涉及 canonical duration

### API helper layer — `api/break_deduction.py`

**responsibility:**
- 過濾 `break_start` / `break_end`
- 映射 `BreakPunchDTO`
- 呼叫 `calculate_break_deduction()`
- 發生例外時回傳 fallback derived result

**judgment:**
- 符合 helper / integration 邊界
- 檔案註解明確禁止寫 `session.duration_minutes`、禁止 close session、禁止 policy evaluation

**violation:**
- 未發現

### Service layer — `service.py`

**responsibility:**
- `build_punch_out_policy_evaluation()` 作為 punch-out close flow orchestration entry
- 建立 missing-segment dry-run input
- 後續委派 `build_policy_evaluation()`

**judgment:**
- service 沒有直接做 break deduction
- 但 `_build_actual_segments_from_punches()` 會將 `break_start` / `break_end` 當作 actual work segments 的切分訊號

**violation:**
- 未發現 canonical 越界
- 備註：存在 breaks 與 missing-segment 的跨責任互動，但證據只顯示它影響 dry-run input，不影響 canonical persistence

### Repo layer — `repo.py`

**responsibility:**
- `create_punch()` 建立 break punches
- `get_last_break_punch()` / `get_session_punches()` 讀取 break punches
- `close_session()` 持久化 canonical duration

**judgment:**
- repo 本身只做 persistence / retrieval
- `close_session()` 接收外部傳入的 `duration_minutes`，未自行重算 break-adjusted value

**violation:**
- 未發現

### Domain / close-flow layer — `punch_close_domain.py`

**responsibility:**
- 將 session 設為 closed 狀態
- 將 duration 值放進 session object
- 呼叫 policy engine

**judgment:**
- legacy path `build_policy_evaluation()` 將 `gross_minutes` 放入 `session.duration_minutes`
- schedule-aware path `build_policy_evaluation_with_schedule_v2()` 將 `work_minutes` 放入 `session.duration_minutes`

**violation:**
- 本票範圍內未見 breaks deduction 值進入
- 但存在命名與 semantic drift 風險，詳見第 9 節

### Policy layer — `policy_engine.py`

**responsibility:**
- 依 session / policy 做 late / early leave / overtime evaluation
- `evaluate()` 與 `evaluate_with_schedule_v2()` 讀取 `session.duration_minutes`

**judgment:**
- policy 直接吃 canonical persisted/assigned duration
- 未直接呼叫 break deduction，也未直接處理 break punches

**violation:**
- 未發現 breaks 邏輯塞回 policy engine

---

## 4. Canonical Boundary Check

### 是否有 violation

未發現直接 violation。

### 結論

在已檢查檔案中，breaks 沒有直接或間接把 break-adjusted 值寫回 canonical `session.duration_minutes`。

### 證據（file + 行為）

#### `api/break_deduction.py`

檔頭 boundary 明確寫：
- Cannot call `repo.close_session()`
- Cannot write `session.duration_minutes`
- Cannot run policy evaluation

實作中僅回傳 `calculate_break_deduction(...)` 結果或 `FallbackDeductionResult`。

#### `api/punch.py`

- `gross_minutes = int(duration.total_seconds() / 60)`
- `resolve_break_deduction(...)` 在 gross 算完後執行
- 註解明確寫：
  - `deduction_result.net_work_minutes is derived/informational only`
  - `session.duration_minutes must remain gross_minutes`
- `repo.close_session(..., duration_minutes=gross_minutes, ...)`

#### `repo.py`

`close_session()` 直接：
- `session.duration_minutes = duration_minutes`

repo 未以 break punches 或 net minutes 重算。

#### `punch_close_domain.py`

legacy path 將 `gross_minutes` 寫入 `session.duration_minutes`，未使用 break deduction 結果。

### 補充判定

- `service.py` 雖使用 `break_start` / `break_end` 建 actual segments，但沒有把 net 或 break-adjusted duration 寫回 canonical
- `policy_engine.py` 讀 `session.duration_minutes or 0`，不是讀 `net_work_minutes`

---

## 5. Break Deduction Position

### 是否完全為 derived

**YES（依目前已讀證據）**

### 證據

#### `api/break_deduction.py`
- 僅建立 DTO、呼叫 engine、回傳 deduction result / fallback result

#### `api/punch.py`
- break deduction 在 punch-out 流程中被明確標註為 derived only
- close session 仍使用 `gross_minutes`

#### `test_punch_break_integration.py`
測試明確驗證：
- valid break punches 時，`duration_minutes` 仍寫 gross
- `net_work_minutes` 存在但不覆寫 DB canonical

#### `test_work_hour_engine.py`
- 將 `calculate_break_deduction()` 與 `calculate_work_duration()` 區分
- deduction result 內有 `gross_minutes`、`break_minutes`、`net_work_minutes`

### 是否存在越界

- 回寫 DB：未發現
- 改 session model：未發現由 break deduction helper 改寫 canonical session model
- 被 policy 當 canonical 使用：未發現
- policy 吃的是 `session.duration_minutes`，不是 deduction result

---

## 6. Write Path Findings（為 P3_A2 前置）

### write entry points

- `api/breaks.py::break_out()`
  - 呼叫 `repo.create_punch(..., punch_type='break_start', ...)`
- `api/breaks.py::break_in()`
  - 呼叫 `repo.create_punch(..., punch_type='break_end', ...)`
- `api/breaks.py::update_punch_note()`
  - 直接 `db.query(AttendancePunch)...`
  - 直接修改 `punch.notes`
  - 直接 `db.commit()`
- `api/punch.py::punch_out()`
  - 呼叫 `write_break_anomaly_audit(...)`
  - 此為 anomaly audit persistence，非 canonical duration write path

### 是否集中

部分集中，部分未集中。

- break punch creation：
  - 經由 `repo.create_punch()`，屬集中
- break note update：
  - 不經 repo，API 直接寫 DB，不集中
- break anomaly audit：
  - 經 helper 另一路 persistence，與 punch repo 分離；但寫的是 audit log，不是 session canonical

### 是否存在多個 write entry

**YES**

但需區分資料類型：

- break punches 本身：有 `break_out()` / `break_in()` 兩個 entry
- punch note：有 `update_punch_note()` 直接更新 entry
- anomaly audit：另有 audit log write path

### 是否存在 API 直接寫 DB

**YES**

證據：
- `api/breaks.py::get_break_punches()` 直接 query
- `api/breaks.py::update_punch_note()` 直接 query + commit

---

## 7. Policy Interaction Findings

### policy_engine 是否直接或間接依賴 break deduction

- 直接依賴：**NO**
- 間接依賴：在本票已讀證據中未發現

### 證據

- `policy_engine.py::evaluate()` 只讀 `session.duration_minutes`
- `evaluate_with_schedule_v2()` 也只讀 `session.duration_minutes`
- 未見 `net_work_minutes` / `break_minutes` / `resolve_break_deduction` 引用

### breaks 是否影響 late / early / overtime / work_minutes

- late：未發現 breaks 直接影響
- early_leave：未發現 breaks 直接影響
- overtime：未發現 breaks deduction 直接影響
- work_minutes：
  - policy 的 `work_minutes` 來源為 `session.duration_minutes`
  - 目前 canonical 已定義為 gross
  - break deduction 沒有改寫這個值

### 補充

`service.py` 的 missing-segment dry-run 會利用 `break_start` / `break_end` 重建 actual segments。這是 breaks 與另一條分析邏輯的互動，不是 policy engine 直接使用 break deduction。

### 是否破壞「policy 只吃 canonical」原則

未發現破壞。目前 policy 仍只吃 `session.duration_minutes`。

---

## 8. Reporting Interaction Findings

### reporting 是否使用 break-adjusted 值當 canonical

未發現。

### 證據

#### `api/reporting.py`
- `/sessions` 直接輸出 `duration_minutes=s.duration_minutes`
- `/reports/user-summary` 註解明確寫：
  - `total_work_minutes` 讀取 canonical 欄位 `duration_minutes`
- `/reports/company-summary` 同樣明確以 `duration_minutes` 為 canonical

#### `reporting_service.py`
- `total_work_minutes = sum(s.duration_minutes or 0 for s in sessions)`

#### `test_reporting_user_summary.py`
- summary tests 直接以 `duration_minutes` 作為統計基礎

### 是否存在語意混用

在已檢查 reporting 檔案中未發現 break-adjusted canonical 混用。reporting 依賴 canonical persisted duration，非 break-adjusted value。

---

## 9. Semantic Drift Findings

已發現以下語意漂移 / 命名風險：

1. `punch_close_domain.py` 的 schedule-aware path 使用 `work_minutes` 寫入 `session.duration_minutes`
   - 依 P1 semantic decision，canonical 必須是 gross
   - `work_minutes` 這個名稱本身不保證 gross semantic
   - 在 breaks 審計角度，這構成語意風險，但本票未看到 break deduction 值進入該參數
   - 結論：risk noted, no direct breaks violation evidence

2. `api/break_deduction.py` fallback message 使用 fallback to gross
   - 這反而支持 gross canonical
   - 未構成 drift，但顯示 gross/net distinction 需靠註解與命名維持

3. `test_work_hour_engine.py` 存在 `calculate_canonical_work_duration` 命名
   - 在目前正式基準下，canonical = gross persisted `session.duration_minutes`
   - 若該 wrapper 在 engine 層語意不是 persisted canonical，則命名有混淆風險
   - 本票只記錄命名風險，不延伸推論

4. `work_minutes` / `duration_minutes` / `net_work_minutes` 共存
   - 系統內同時存在三組相近語意名稱
   - 目前靠註解與流程維持邊界
   - 對 breaks 相關審計而言，這屬 semantic drift risk，不是已證實 violation

---

## 10. Freeze Compatibility

### 是否違反 `POLICY_ENGINE_FREEZE.md`

未發現。

### 檢查結果

- `policy_engine.py` 內未見 break deduction 邏輯回塞
- 未見 `break_start` / `break_end` 過濾邏輯進入 policy engine
- 未見 API request / repo query / reporting shaping 因 breaks 而直接塞入 policy engine
- `policy_engine.py` 目前仍是讀 `session.duration_minutes` 做 evaluation 的 façade

### 是否把邏輯塞回 `policy_engine.py`

未發現。

### 是否破壞 orchestration façade 原則

在 breaks 角度未發現新增破壞。但 `policy_engine.py` 本身依治理文件仍屬高風險膨脹檔，這是既有狀態，不是 breaks 新增造成。

---

## 11. Risk Classification

**Medium**

### 原因

- canonical boundary 本身目前守住，未發現 break deduction 覆寫 `duration_minutes`
- policy / reporting 仍以 canonical gross 為消費者，未見 break-adjusted 混入
- 但 breaks write/read responsibility 未完全集中
- API 直接 query / commit 仍存在
- 存在 semantic drift risk
  - `work_minutes`、`duration_minutes`、`net_work_minutes` 命名並存
  - schedule-aware path 將 `work_minutes` 寫到 `session.duration_minutes` 的語意風險仍在
- service 與 missing-segment dry-run 對 `break_start` / `break_end` 有跨層互動，雖未影響 canonical，但後續審計需持續注意

---

## 12. Audit Conclusion

### 是否允許進入 P3_A2

**YES**

### 是否需要先修復

**NO，依本票證據不需要先修復才能進入 P3_A2**

### 理由

本票主要目標是確認 breaks 是否越界影響 canonical gross duration。已檢查檔案中，未發現：

- break deduction 回寫 `session.duration_minutes`
- break deduction 被 policy 當 canonical 使用
- reporting 使用 break-adjusted 值當 canonical

已找到 P3_A2 所需的 write-path 前置資訊：

- break punches 的寫入入口
- API 直接寫 DB 的存在
- 是否集中

### 最終結論

- P3_A1 結果：**PASS WITH NOTES**
- breaks 目前未破壞 canonical = gross 的正式定案
- 可進入 P3_A2
- 本票僅記錄責任邊界與語意風險，不授權任何修復行為
