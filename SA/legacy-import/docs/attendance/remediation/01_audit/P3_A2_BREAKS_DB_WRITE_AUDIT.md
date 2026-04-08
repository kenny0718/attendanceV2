# P3_A2 Breaks DB Write Audit Report

> **Ticket Type**: Audit  
> **Phase**: 3  
> **Priority**: Medium-High  
> **Execution Mode**: Read-only / Documentation  
> **Status**: Done

---

## 1. Summary（PASS / PASS WITH NOTES / FAIL）

**PASS WITH NOTES**

依已檢查程式碼證據：

- breaks 相關「核心 punch 寫入」大致集中在 `repo.create_punch()`
- 但 breaks 相關 DB write path 不是完全單一入口

已確認存在：

- API 透過 repo 寫 break punches
- API 直接寫 DB 更新 punch note
- punch-out flow 透過 helper 寫 audit log

目前未發現任何 breaks write path 會寫入或覆寫 `session.duration_minutes`。
目前未發現 breaks write path 會呼叫 `repo.close_session()` 來改 canonical。
因此 canonical gross safety 成立。

但 write path centralization 只能判定為**部分集中**，不是完全集中。

---

## 2. Write Entry Table

| entry | file | function | data type | via repo |
|---|---|---|---|---|
| break_start write | `backend/app/modules/attendance/api/breaks.py` | `break_out()` | `AttendancePunch (punch_type='break_start')` | YES |
| break_end write | `backend/app/modules/attendance/api/breaks.py` | `break_in()` | `AttendancePunch (punch_type='break_end')` | YES |
| break note update | `backend/app/modules/attendance/api/breaks.py` | `update_punch_note()` | `punch note (AttendancePunch.notes)` | NO |
| break anomaly audit write | `backend/app/modules/attendance/api/punch.py` → `backend/app/modules/attendance/api/anomaly_audit.py` | `punch_out()` → `write_break_anomaly_audit()` | `audit log` | YES（透過 audit repo） |
| out punch during close-flow | `backend/app/modules/attendance/api/punch.py` | `punch_out()` | `AttendancePunch (punch_type='out')` | YES |
| indirect break deduction write | `backend/app/modules/attendance/api/break_deduction.py` | `resolve_break_deduction()` | 無 DB write | NO WRITE |
| indirect service write | `backend/app/modules/attendance/service.py` | `build_punch_out_policy_evaluation()` | 無 DB write | NO WRITE |

---

## 3. Write Flow Mapping

### break_start

API (`breaks.py::break_out`) → `repo.create_punch()` → DB  
- bypass repo：NO  
- bypass service：YES

### break_end

API (`breaks.py::break_in`) → `repo.create_punch()` → DB  
- bypass repo：NO  
- bypass service：YES

### break note update

API (`breaks.py::update_punch_note`) → `db.query(...)` / field assign / `db.commit()` → DB  
- bypass repo：YES  
- bypass service：YES

### break anomaly audit

API (`punch.py::punch_out`) → helper (`anomaly_audit.py::write_break_anomaly_audit`) → audit repo.`create_log()` → DB  
- bypass repo：attendance repo YES  
- audit repo：NO bypass  
- bypass service：YES

### break deduction helper

API (`punch.py::punch_out`) → helper (`break_deduction.py::resolve_break_deduction`) → `work_hour_engine`  
- DB write：無

### service indirect path

API (`punch.py::punch_out`) → `service.build_punch_out_policy_evaluation()` → `punch_close_domain.build_policy_evaluation()`  
- DB write：無  
- 僅 session in-memory mutation for evaluation preparation，無 commit

---

## 4. Repository Centralization

### 是否集中

**部分集中，非完全集中**

### 證據

- break punch 建立：  
  `break_out()` 與 `break_in()` 都經由 `repo.create_punch()`  
  這部分是集中

- break note update：  
  `update_punch_note()` 直接 `db.query(...)` 後 `db.commit()`  
  未經 repo

- break anomaly audit：  
  不走 attendance repo，而是走 `app.modules.audit.repo.get_audit_log_repository(db).create_log(...)`  
  這是另一條 repo 化 write path

- service：  
  已讀範圍內未發現 service 直接寫 DB

### 判定

- 若只看 break punch create：集中
- 若看全部 breaks-related writes：分散

---

## 5. Direct DB Access Findings

### 5.1 `backend/app/modules/attendance/api/breaks.py`

**pattern: `db.query(...)`**
- 出現在 `get_break_punches()`
- 出現在 `update_punch_note()`

**pattern: `db.commit()`**
- 出現在 `update_punch_note()`

**是否越界**
- `get_break_punches()`：  
  本票聚焦 DB write path。`db.query(...)` 為 direct DB read，不屬 write，但顯示 API 直接接 ORM。
- `update_punch_note()`：  
  屬 direct DB write。  
  是越界現象，因為 API 直接 query + commit，未經 repo / service。

### 5.2 `backend/app/modules/attendance/repo.py`

**pattern:**
- `self.db.add(...)`
- `self.db.commit(...)`
- `self.db.refresh(...)`

出現在：
- `create_session()`
- `close_session()`
- `create_punch()`

**是否越界**
- 否  
  repo 層直接 add / commit / refresh 屬正常 persistence 職責。

### 5.3 `backend/app/modules/attendance/api/anomaly_audit.py`

已讀檔案中未直接看到 `db.add(...)` / `db.commit(...)`。  
寫入動作是透過 `audit_repo.create_log(...)`。

**是否越界**
- 否  
  helper 沒有直接 ORM write；是委派給 audit repo。

### 5.4 `backend/app/modules/attendance/service.py`

已讀範圍內未看到 `db.query(...)` / `db.add(...)` / `db.commit(...)`。

**是否越界**
- 未發現

### 5.5 `backend/app/modules/attendance/api/break_deduction.py`

已讀範圍內未看到 `db.query(...)` / `db.add(...)` / `db.commit(...)`。

**是否越界**
- 未發現

---

## 6. Canonical Safety

### 是否安全

**YES**

### 證據

#### `api/breaks.py::break_out()`
- 僅呼叫 `repo.create_punch(..., punch_type='break_start')`
- 未呼叫 `close_session()`
- 未寫 `session.duration_minutes`

#### `api/breaks.py::break_in()`
- 僅呼叫 `repo.create_punch(..., punch_type='break_end')`
- 未呼叫 `close_session()`
- 未寫 `session.duration_minutes`

#### `api/breaks.py::update_punch_note()`
- 僅更新 `AttendancePunch.notes`
- 沒有碰 `AttendanceSession.duration_minutes`

#### `api/break_deduction.py::resolve_break_deduction()`
檔案 boundary 明確寫：
- Cannot call `repo.close_session()`
- Cannot write `session.duration_minutes`

實作中也只有回傳 deduction result / fallback result。

#### `api/anomaly_audit.py::write_break_anomaly_audit()`
檔案 boundary 明確寫：
- Cannot call `repo.close_session()`
- Cannot write `session.duration_minutes`

實作中只寫 audit log。

#### `api/punch.py::punch_out()`
- break deduction 是 derived only
- close session 時明確傳入 `duration_minutes=gross_minutes`
- breaks-related side effects 沒有覆寫 canonical

### 結論

在已審計 write path 中：

- 未發現 breaks 寫入會影響 `session.duration_minutes`
- 未發現 breaks 寫入會觸發 `close_session()` 去改 canonical
- 未發現 indirect write 會改 canonical gross

---

## 7. Consistency Findings

### break_start / break_end 是否走同一條寫入邏輯

**YES**

兩者都在 API 層執行 request handling 後，直接呼叫 `repo.create_punch()`；transaction control 也一致，皆由 repo commit。

### 是否存在 A 用 repo、B 用 direct DB

**YES**

- `break_out()` / `break_in()`：用 repo
- `update_punch_note()`：direct DB

### 是否存在 inconsistent transaction control

**YES**

- break punch create：repo commit
- note update：API commit
- anomaly audit：audit repo path

### 結論

- break create path 一致
- 但 breaks-related 全體 write path 不一致

---

## 8. Transaction Boundary Findings

### break_start

transaction boundary 位於 `repo.create_punch()`  
repo 內 `self.db.add()` → `self.db.commit()` → `self.db.refresh()`

### break_end

transaction boundary 位於 `repo.create_punch()`  
repo 內 `self.db.add()` → `self.db.commit()` → `self.db.refresh()`

### break note update

transaction boundary 位於 API `update_punch_note()`  
`db.query(...)` → field mutation → `db.commit()`  
這是 API commit。

### break anomaly audit

transaction boundary 不在 `api/punch.py` 本身，是 helper 委派到 audit repo 的 `create_log(...)`。  
具體 commit 細節本票未進一步展開到 audit repo 檔案之外。  
因此僅能確認：

- write path 存在
- 透過 audit repo 實作

更內層 transaction 細節在本票審計範圍外。

### partial commit

現況可見多個獨立 commit 邊界：

- `repo.create_punch()` 單次 commit
- `update_punch_note()` API 單次 commit
- audit log 另一路 write

本票只描述現況，不對設計做延伸判斷。

### API commit / service commit / repo commit

- API commit：有  
  `update_punch_note()`
- service commit：未發現
- repo commit：有  
  `create_punch()`  
  `close_session()`（雖非 breaks write entry，但屬 close path）  
  audit repo `create_log()`（另一個 repo）

---

## 9. Test Coverage

### 有覆蓋的 write path

#### break_start / break_end write
- `backend/app/modules/attendance/tests/test_break_out_enforcement.py`  
  覆蓋 `/break-out`，驗證 break-out 成功與 location policy 下的寫入結果
- `backend/app/modules/attendance/tests/test_break_punches_boundary.py`  
  雖主軸偏讀取，但資料準備中直接建立 `break_start` / `break_end` punches，間接反映此資料型態存在
- `backend/app/modules/attendance/tests/test_punch_break_integration.py`  
  使用 break punches 驗證 punch-out close flow

#### break anomaly audit write
- `backend/app/modules/attendance/tests/test_punch_break_integration.py`  
  明確覆蓋：
  - anomaly present → `create_log` 被呼叫
  - audit write failure fallback
  - no anomaly → `create_log` 不被呼叫

#### canonical safety around breaks write interaction
- `backend/app/modules/attendance/tests/test_punch_break_integration.py`  
  明確驗證：
  - valid break punches 時 `duration_minutes` 仍為 gross
  - anomaly / clamp 情況下 punch-out 仍成功，DB 寫入 gross

#### break deduction no-write semantics
- `backend/app/modules/attendance/tests/test_work_hour_engine.py`  
  覆蓋 deduction result 內容  
  雖不是 DB write test，但支持 deduction 只是 calculation layer

### 未明確看到覆蓋的 write path

#### `update_punch_note()` direct DB write
在本次已讀測試中，未看到明確對應測試檔。  
因此本票判定：coverage not found in inspected tests。

#### `break_in()` endpoint
本次已讀測試中未看到一個明確以 `/break-in` 為主體的專門測試檔。  
可能存在其他檔案覆蓋，但在本次已讀證據中：**UNKNOWN / not confirmed**。

---

## 10. Risk Classification

**Medium**

### 原因

- canonical safety 已確認成立，風險不是 canonical 被 breaks 覆寫
- break punch create path 本身相對清楚，透過 repo 集中
- 但 breaks-related 全部 DB writes 並非單一路徑
- API direct write (`update_punch_note()`) 存在
- audit log 另一路 repo 存在
- transaction boundary 分散於 API / attendance repo / audit repo
- write-path consistency 非完全一致
- 部分路徑測試覆蓋不足或本票內無法確認

---

## 11. Audit Conclusion

### 是否需要 P3 fix

**YES**，若 P3 的目標包含 breaks DB write centralization / controllability，則需要後續 fix 票。

### 理由

- 已確認 `update_punch_note()` 為 API direct DB write
- breaks-related write path 非完全集中

### 是否可以進 P4

**YES, WITH NOTES**

### 理由

本票聚焦的核心安全條件已成立：
- breaks write path 未影響 canonical gross

但若 P4 需要建立更嚴格的 persistence governance，則應帶著本票註記前進。

### 最終結論

- breaks DB write path：
  - 可控性：部分成立
  - 集中性：部分成立
  - canonical safety：成立

因此本票結果為：

**PASS WITH NOTES**

本票到此結束，不延伸修正建議。
