# P6_F3A Repo Decomposition for Write Path

Status: Planning / Documentation-only

## 1. Summary

本規劃票是 `P6_F3 — BREAK_NOTE_WRITE_PATH_REPOIZATION` 的前置治理票。

目的不是直接修 `update_punch_note()`，而是先解決阻擋該票執行的治理限制：

- `backend/app/modules/attendance/repo.py` 目前已超過 400 行
- 依 `STOP_GATES.md` 的 `GATE-FILE-SIZE [P0]`，不得在超過 400 行的 `.py` 檔案中新增 method 或擴張業務邏輯
- 因此，若要把 `update_punch_note()` 從 API direct DB write 收斂回 repo persistence contract，必須先進行 repo decomposition planning

本票只做：
- 拆分規劃
- 邊界定義
- 遷移順序定義
- 風險與非目標定義

本票不做：
- 實際拆分
- 任何程式碼修改
- 任何測試修改
- 任何 route / service / semantic 調整

---

## 2. Why This Ticket Exists

`P6_F3` 的目標原本是：
- 將 `update_punch_note()` 的寫入從 API 層 direct ORM / direct commit
- 收斂為 repo 的單一 persistence contract

但在 Pre-Execution 檢查時，確認：

- `backend/app/modules/attendance/repo.py` = 408 行
- 本票要求在 `repo.py` 新增或明確一個 `update_punch_note(...)` 類型 method
- 這會直接觸發 `GATE-FILE-SIZE [P0]`

因此不能直接進 `P6_F3` 實作。

需要先以一張單獨規劃票，定義：
- repo 應如何拆分
- write path 的最小安全落點在哪裡
- 如何避免拆分過程擴大成 whole-file rewrite 或泛化重構

---

## 3. Current State

### 3.1 API write path 現況
目前 `update_punch_note()` 位於：
- `backend/app/modules/attendance/api/breaks.py`

現況行為：
- API 直接 `db.query(AttendancePunch)`
- 直接取得 punch
- 直接 `punch.notes = notes`
- 直接 `db.commit()`

這代表：
- API 層直接持有 ORM read/write 責任
- write path 沒有經過 attendance repo
- persistence contract 不集中

### 3.2 repo 現況
目前 `backend/app/modules/attendance/repo.py` 同時承載：
- session create / close
- punch create
- session read/query helpers
- policy retrieval
- break punch read helpers
- business-date read-side helpers
- 其他 attendance repo responsibilities

這使得：
- 單檔責任已逐漸累積
- 新增任一 write helper 都可能再擴張高風險核心檔
- 不符合 `STOP_GATES.md` 的 file size gate 要求

### 3.3 與本票直接相關的問題
與本規劃票最直接相關的不是「repo 全面重構」，而是：
- 找出一個最小安全方式
- 讓 `update_punch_note()` 未來可以合法、低風險地回到 repo persistence contract

---

## 4. Planning Goal

本票的規劃目標是：

1. 定義 attendance repo 的最小拆分策略
2. 讓 break note update 的 repoization 有合法落點
3. 避免把 `P6_F3` 擴大成 repo 全面重寫
4. 保持 canonical / policy / reporting semantic 完全不變
5. 為後續 `P6_F3` 與 `P6_F4` 提供可治理的 repo 邊界

---

## 5. Scope

### In Scope
- `backend/app/modules/attendance/repo.py` 的拆分規劃
- attendance write/read responsibility 邊界重新分類（文件層級）
- break note write path 的未來落點規劃
- 與 `P6_F3` / `P6_F4` 的依賴關係說明

### Out of Scope
- 任何程式碼修改
- 任何 import 調整
- 任何 route / service / policy / reporting 修改
- 任何 canonical semantic 調整
- 任何測試實作
- 任何 migration / schema 變更

---

## 6. Decomposition Principles

本票的拆分規劃必須遵守以下原則：

1. **單票單責任**
   - 本票只規劃 repo decomposition，不實作其他修復

2. **write path first, not architecture rewrite**
   - 拆分的直接目的是解除 `P6_F3` gate blocker
   - 不是為了抽象更漂亮或全面重構

3. **最小可行拆分**
   - 僅拆到足以讓後續 write path repoization 合法落地
   - 不追求一次把所有 attendance repo 問題清空

4. **canonical safety**
   - 不碰 `close_session()` semantic
   - 不碰 `duration_minutes`
   - 不碰 break deduction / policy / reporting semantic

5. **責任對齊優先於命名漂亮**
   - 子 repo 命名可以保守
   - 但 responsibility boundary 必須清楚

6. **過渡期相容**
   - 若未來拆分實作採 façade 或委派模式，應以最小 caller 變動為原則

---

## 7. Proposed Target Structure

### Option A — Minimal Write/Session Split（建議方案）

建議將 `repo.py` 未來收斂為三個責任面：

#### A1. `attendance_session_repo.py`
責任：
- `create_session(...)`
- `get_open_session(...)`
- `close_session(...)`
- `get_sessions(...)`
- `count_sessions(...)`
- 其他以 `AttendanceSession` 為主的 persistence/read helpers

特性：
- 保留 canonical persistence 所在邊界
- 不混入 break note write 這種 punch 級細節更新

#### A2. `attendance_punch_repo.py`
責任：
- `create_punch(...)`
- `get_last_break_punch(...)`
- `get_session_punches(...)`
- `get_punches_by_company_user_business_date_range(...)`
- `get_punches_by_company_user_and_session_ids(...)`
- 未來的 `update_punch_note(...)`

特性：
- `AttendancePunch` 的讀寫收斂到同一側
- `P6_F3` 的 break note write path 可自然落在此處
- `P6_F4` 的 break read cleanup 也可依附同一邊界

#### A3. `repo.py`（過渡 façade / assembly surface）
責任：
- 保留既有對外入口
- 暫時提供 `get_attendance_session_repository(...)` 或等價 façade
- 對舊 caller 做最小相容委派

特性：
- 避免一次性改太多 import caller
- 讓拆分能以可控階段遷移

---

## 8. Why Option A Is Preferred

Option A 是最適合 `P6_F3A` 目的的方案，因為：

1. **直接解 blocker**
   - `update_punch_note()` 屬 `AttendancePunch` 級更新
   - 拆出 punch repo 後，可在不碰大檔 gate 的情況下新增 method

2. **對 `P6_F3` 與 `P6_F4` 都有幫助**
   - `P6_F3`：break note write path repoization
   - `P6_F4`：breaks read layer cleanup

3. **避免碰 canonical close path 太多**
   - `close_session()` 仍留在 session repo
   - 降低語意風險

4. **避免把 repo 拆成過多碎片**
   - 若一次拆成太多檔，會超出本次最小治理目的

---

## 9. Methods Likely to Move by Responsibility

### Session-side
預計歸入 session repo：
- `create_session(...)`
- `get_open_session(...)`
- `close_session(...)`
- `get_sessions(...)`
- `count_sessions(...)`
- `get_sessions_by_company_user_business_date_range(...)`
- `get_user_policy(...)` 是否留在 session repo，需在實作票再決定

### Punch-side
預計歸入 punch repo：
- `create_punch(...)`
- `get_last_break_punch(...)`
- `get_session_punches(...)`
- `get_punches_by_company_user_business_date_range(...)`
- `get_punches_by_company_user_and_session_ids(...)`
- 未來新增 `update_punch_note(...)`

### Transitional façade
預計保留在 `repo.py`：
- 工廠函式 / 組裝入口
- 相容性委派入口
- 過渡期 aggregator interface

---

## 10. Proposed Future Method for P6_F3

在 `P6_F3` 真正實作時，建議新增 method：

```python
update_punch_note(
    company_id: str,
    user_id: UUID,
    punch_id: UUID,
    notes: str,
) -> Optional[AttendancePunch]
```

### Responsibility
- 以 company/user/punch 三元條件查找 punch
- 更新 `AttendancePunch.notes`
- `commit`
- `refresh`
- 找不到時回傳 `None`

### Why return Optional[AttendancePunch]
這樣可讓 API 層保留目前既有行為：
- repo 回傳 `None` → API 繼續回 `404`
- repo 回傳 punch → API 照舊組 response

因此能滿足：
- 不改 API response
- 不改 exception 行為
- 不改權限檢查
- 不改欄位名稱

---

## 11. Migration Strategy

### Phase 1 — Decomposition Ticket（本票規劃，後續另開實作）
- 實作 session/punch repo split
- 保留 façade 或相容入口
- 不改 route behavior
- 不改 semantic

### Phase 2 — P6_F3
- 將 `update_punch_note()` 改為呼叫 punch repo method
- 移除 API direct ORM write / direct commit
- 保持 response/exception 不變

### Phase 3 — P6_F4
- 再評估是否把 `get_break_punches()` 的 direct ORM read 收斂到 punch repo
- 僅處理 read path，不混入 write path

這個順序可避免：
- 一次同時拆 repo + 改 write path + 改 read path
- 導致 diff 過大、風險過高

---

## 12. Risks

### R1. 過度擴大為 repo 全面重構
風險：
- 會偏離 `P6_F3` 的實際目的
- 變成高風險治理重構

控制方式：
- 僅做 session/punch 二分
- 不處理與本次 write path 無關的抽象優化

### R2. 破壞既有 import callers
風險：
- repo 被多個 attendance path 引用
- 若一次性改所有 caller，風險高

控制方式：
- 保留 `repo.py` façade / factory 相容入口
- 實作票中採漸進式委派

### R3. 誤碰 canonical close path
風險：
- `close_session()` 與 canonical persistence 高敏感

控制方式：
- canonical 相關 session persistence 與 punch write 拆開
- 在 `P6_F3A` / 後續實作中，不變更 `close_session()` semantic

### R4. 把 F3 與 F4 混票
風險：
- write repoization 與 read cleanup 同時做，diff 擴張

控制方式：
- 明確切票：
  - `P6_F3` 只管 write
  - `P6_F4` 只管 read

---

## 13. Non-Goals

本規劃明確不授權以下事項：

- 不改 `service.py`
- 不改 `reporting.py`
- 不改 `policy_engine.py`
- 不改 `punch_close_domain.py`
- 不改 canonical semantic
- 不改 break deduction logic
- 不改 route contract
- 不做 break read path cleanup
- 不做 repo 命名全面美化
- 不做 whole-file rewrite

---

## 14. Ticket Dependencies

### Upstream
- `P6_F2` 已完成 boundary realignment，與本票無直接程式依賴，但共同屬 breaks risk reduction 序列

### This Ticket Enables
- `P6_F3 — BREAK_NOTE_WRITE_PATH_REPOIZATION`
- `P6_F4 — BREAKS_READ_LAYER_CLEANUP`

### Recommended Order
1. `P6_F3A_REPO_DECOMPOSITION_FOR_WRITE_PATH`（先做拆分）
2. `P6_F3_BREAK_NOTE_WRITE_PATH_REPOIZATION`
3. `P6_F4_BREAKS_READ_LAYER_CLEANUP`

---

## 15. Execution Guidance for Future Implementation Ticket

若未來開實作票，建議遵守：

1. 先做唯讀盤點與 method mapping
2. 先建立 `.bak_safe_edit`
3. 僅做 patch-style edit
4. 每檔使用 `.tmp -> validate -> rename`
5. 每步確認非 0 bytes
6. 每步執行 `python -m py_compile`
7. 先做拆分，再做 route caller 收斂
8. 不可在同一票中順手整理其他 repo debt

---

## 16. Decision Statement

本規劃票結論如下：

- `P6_F3` 目前被 `GATE-FILE-SIZE [P0]` 合法阻擋，不能直接在 `backend/app/modules/attendance/repo.py` 新增 write method
- 若要在不違反治理規則的前提下完成 break note write path repoization，必須先進行 repo decomposition
- 最小可行且風險最低的拆分方案，是將 attendance repo 分成：
  - session-side repo
  - punch-side repo
  - 過渡 façade / assembly surface
- `update_punch_note()` 的未來合法落點，應位於 punch-side repo
- 本票只授權規劃，不授權任何程式碼修改
