Title: Attendance Capture Spec
Author: Johnny Lee
Version: 1.0
Date Created: 2026-04-08
Last Modified: 2026-04-08
spec:id: attendance.capture.v1
status: active
module: attendance
subdomain: capture
source_of_truth: SA/modules/attendance-capture.md
related_code_paths:
  - backend/app/modules/attendance/api/punch.py
  - backend/app/modules/attendance/api/breaks.py
  - backend/app/modules/attendance/api/checkpoints.py
  - backend/app/modules/attendance/repo.py
  - backend/app/modules/attendance/service.py
  - backend/app/modules/attendance/punch_close_domain.py
---

# Attendance Capture 開發規格

> 本文件定義 `attendance` 模組中所有「交易寫入型流程」的正式規格。  
> 只要你要改的是打卡、session、break、checkpoint、note update，應先讀這份，再改程式。

---

## 1. 文件定位

### 1.1 這份文件是給誰看的

- 你自己未來改 attendance 時
- 之後協助你開發的 AI
- 要 review punch / break / session 相關改動的人

### 1.2 什麼情況要先看這份

- 新增或修改 `punch-in`
- 新增或修改 `punch-out`
- 新增或修改 `break-out` / `break-in`
- 修改 `break note`
- 修改 `current-status` / `history`
- 修改 `checkpoint`
- 修改 `session open / close`

### 1.3 它和其他文件的關係

- 主模組總覽：`SA/modules/attendance.md`
- 查詢報表規格：`SA/modules/attendance-reporting.md`
- 規則語意規格：`SA/modules/attendance-policy.md`
- 模板來源：`SA/governance/MODULE_SPEC_TEMPLATE.md`

---

## 2. 目的與範圍

### 2.1 本文件負責的範圍

`attendance.capture` 的責任是：

- 把出勤事件正確寫進系統
- 維護 `AttendanceSession` 的開啟與關閉
- 管理 punch / break / checkpoint 事件落地
- 確保寫入路徑遵守 tenant isolation 與 canonical contract

### 2.2 本文件不負責的範圍

這份文件不處理：

- sessions / summary 報表聚合
- reporting 查詢區間設計
- 遲到 / 早退 / 加班的詳細規則定義
- schedule baseline 主資料管理
- notifications 主流程

### 2.3 一句話理解

> capture 子域只負責「把出勤事實安全且一致地寫入系統」。

---

## 3. 核心原則

| 原則 | 定義 | 可驗證條件 |
|---|---|---|
| Tenant-Scoped Write | 所有寫入都必須受 `company_id` 限制 | 檢查 API / repo 不可信任 body 的 `company_id` |
| Actor-Driven Identity | `company_id` / `user_id` 只能來自 actor | endpoint 透過 actor 注入，不從 body 指定 |
| Single Open Session | 同一使用者不可同時有多個 open session | 建立 session 前必查 open session |
| Canonical Protected | `session.duration_minutes` 是 canonical persisted duration | 不可把 derived net/work 分鐘數寫回 canonical |
| Repo-Owned Persistence | 寫入應透過既定 persistence path 收斂 | 不允許 route-level direct DB write |
| Boundary Consistency | today / business-date boundary 不可各寫一套 | break 相關 query 應對齊單一 boundary owner |

---

## 4. 功能規格

### 4.1 Punch In

**用途**：建立新的 open session，並落一筆 `in` punch。  
**主要檔案**：`api/punch.py`, `repo.py`

**必要行為**：
- 取得 actor 的 `company_id` / `user_id`
- 驗證不得已有 open session
- 建立 `AttendanceSession(status=open)`
- 建立 `AttendancePunch(type=in)`

### 4.2 Punch Out

**用途**：關閉 open session，並完成 close flow。  
**主要檔案**：`api/punch.py`, `punch_close_domain.py`, `repo.py`, `service.py`

**必要行為**：
- 查出 open session
- 建立 `out` punch
- 計算 `gross_minutes`
- 執行 break deduction（derived only）
- 執行 policy evaluation
- close session 時寫入 canonical duration

### 4.3 Break Out / Break In

**用途**：記錄 session 期間的外出與返回事件。  
**主要檔案**：`api/breaks.py`, `repo.py`

**必要行為**：
- 先取得 open session
- break-out 時執行 location policy enforcement
- 建立 `break_start` 或 `break_end` punch

### 4.4 Punch Note Update

**用途**：修改既有 punch 的備註。  
**主要檔案**：`api/breaks.py`, `repo.py`

**必要行為**：
- 依 `company_id + user_id + punch_id` 限制更新範圍
- 維持 repo-owned persistence path

### 4.5 Current Status / History

**用途**：查詢目前 open session 狀態或交易型歷史。  
**主要檔案**：`api/punch.py`, `repo.py`

**備註**：
- 這些查詢靠近交易流，不屬 reporting 子域

### 4.6 Checkpoint

**用途**：記錄 checkpoint 類事件。  
**主要檔案**：`api/checkpoints.py`, `checkpoint_repo.py`

**備註**：
- checkpoint 與 break flow 接近，但語意不同，不可混用

---

## 5. Formalized Semantic Block

```yaml
scope:
  module: attendance
  subdomain: capture
  responsibility:
    - punch_in
    - punch_out
    - break_out
    - break_in
    - note_update
    - checkpoint_write
    - session_open_close
  non_responsibility:
    - reporting_aggregation
    - summary_calculation
    - schedule_source_of_truth
    - notification_persistence

contracts:
  tenant_isolation:
    source: actor.active_company_id
    body_override_allowed: false
  actor_identity:
    company_id_source: actor.active_company_id
    user_id_source: actor.user_id
  session_rules:
    max_open_sessions_per_user: 1
    open_status: open
    closed_status: closed
  write_authority:
    persistence_owner: repo
    api_direct_db_write: false
  canonical_contract:
    canonical_field: session.duration_minutes
    canonical_semantic: gross
    derived_fields:
      - deduction_result.net_work_minutes
      - evaluation.work_minutes

validation_rules:
  - rule: open_session_uniqueness
    description: create session 前必須先查 open session
    verification: test open session conflict returns 409
  - rule: canonical_protection
    description: derived minutes 不可覆寫 canonical persisted duration
    verification: punch-out regression test checks duration_minutes remains gross
  - rule: location_policy_on_break_out
    description: break-out 若有 location policy，後端必須強制驗證
    verification: invalid geofence returns 403
  - rule: repo_owned_note_update
    description: note update 不可在 route 直接寫 DB
    verification: update path goes through repo method

change_triggers:
  update_spec_when:
    - punch_api_changed
    - break_flow_changed
    - session_close_contract_changed
    - checkpoint_behavior_changed
    - note_update_path_changed
```

---

## 6. 開發與驗證流程

### 6.1 開發步驟

1. 先判斷這次改動是不是 capture 子域
2. 若有碰到 canonical / policy / boundary，先同步讀：
   - `attendance-policy.md`
   - `attendance-reporting.md`
3. 在既有檔案中修改，不要先新增新層級 abstraction
4. 改完後補對應測試
5. 回寫本文件與主模組文件（若邊界有變）

### 6.2 最低驗證清單

#### Punch In 驗證
- 無 open session 時可建立成功
- 有 open session 時回 409
- 寫入 user/company scope 正確

#### Punch Out 驗證
- 無 open session 時回 404
- gross duration 計算正確
- canonical duration 沒被 derived minutes 覆蓋
- policy evaluation 正常執行

#### Break 驗證
- break-out / break-in 成功寫入 punch
- break-out 遇 location violation 回 403
- break query boundary 與 shared owner 一致

#### Note Update 驗證
- 只能更新自己公司/自己範圍內的 punch
- update path 維持透過 repo

#### Checkpoint 驗證
- checkpoint 可正常建立
- 不與 break flow 混用

---

## 7. 依賴與共用元件

### 7.1 可依賴
- `app.core.dependencies`
- `app.core.scope`
- `app.core.feature_service`
- `attendance.repo`
- `attendance.service`
- `attendance.punch_close_domain`
- `attendance.location_policy_service`

### 7.2 不應承擔
- reporting aggregation
- policy semantic owner
- schedule CRUD
- notifications direct persistence

### 7.3 共用元件

| 元件 | 功能 | 強制性 |
|---|---|---|
| `get_actor_with_company()` | 注入 actor scope | ✅ |
| `_require_attendance_feature()` | `attendance.core` gate 檢查 | ✅ |
| `get_attendance_session_repository()` | session / punch persistence path | ✅ |
| `get_taipei_today_boundary()` | shared boundary owner | break query 需要時使用 |
| `AttendanceLocationPolicyService` | geofence 驗證 | break-out 需要時使用 |

---

## 8. Do / Don’t

### Do
- 用 actor 取得 `company_id` / `user_id`
- 讓 persistence path 經過 repo
- 保護 canonical duration contract
- 將 break / punch / checkpoint 分開理解
- 改高風險 close flow 時同步檢查 policy 文件

### Don’t
- 不要在 API route 直接寫 DB
- 不要把 `work_minutes` / `net_work_minutes` 寫回 canonical 欄位
- 不要在 break flow 自己再寫一套 boundary 規則
- 不要把 checkpoint 當 break event 使用
- 不要把 reporting 補救邏輯塞回交易流

### 最容易踩雷的錯誤
1. API 層越改越像 orchestration service
2. breaks flow 出現 direct ORM / direct DB write 回流
3. 將 derived minutes 當 canonical 使用
4. break query boundary 與 reporting boundary 漸漸分岔

---

## 9. 回寫規則

當發生以下任一情況，必須更新本文件：

- punch-in / punch-out API 契約改變
- break flow 改變
- close session contract 改變
- checkpoint 行為改變
- note update path 改變

---

## 10. 已依目前 baseline 回寫的正式結論（2026-04-08）

- `attendance.capture`（出勤交易寫入子域）是出勤事實的 write-side owner
- `company_id` / `user_id` 應由 actor 注入，不可信任 request body
- `location policy`（地點限制規則）若適用，必須由後端強制執行，前端只能做 `precheck`（預檢）
- `NO_MATCH`（未命中合法條件）若無原因應拒絕；有原因才可進入待處理流程
- `PENDING`（待處理 / 待審）不應直接參與正式推導與日結
- `session.duration_minutes` 必須維持 canonical = gross，不可被 derived `work_minutes` / `net_work_minutes` 覆寫
