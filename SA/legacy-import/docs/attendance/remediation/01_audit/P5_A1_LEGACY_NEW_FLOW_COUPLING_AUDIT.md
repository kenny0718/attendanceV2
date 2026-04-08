# P5_A1 Legacy / New Flow Coupling Audit Report

Status: Done

## 1. Summary（PASS WITH NOTES）

本次審計結論為 **PASS WITH NOTES**。

Attendance 模組內確實存在 **legacy flow 與 new flow 並存**，但目前可見狀態下，兩者主要是**並列共存**，不是大面積直接互相呼叫。真正的風險不在「直接互撞」，而在以下幾點：

- router / mounting 有 **雙入口與雙組裝面**
- `service.py` 與 `repo.py` 仍同時承載 **legacy 與 new flow 責任**
- `policy_engine.py` 內仍保留 **legacy / schedule-aware / façade 混合歷史層次**
- `breaks.py` 出現 **API 直接碰 ORM / 借用 reporting helper** 的 cross-layer coupling
- tests 對一般 new flow 覆蓋不少，但對 **schedule-aware new flow 幾乎無直接覆蓋**

依照已定案語意基準：

- canonical = `session.duration_minutes`（gross）
- canonical owner = close-flow orchestration
- policy / reporting = consumer only
- break deduction = derived only

目前 coupling **尚未直接推翻 canonical 決議**，但存在 **indirect override risk**：若未來在高風險核心檔上擴寫，很容易再次把 canonical、policy、reporting、break deduction 或 schedule-aware 邏輯混回同一條主流程。

---

## 2. Flow Mapping

### 2.1 Legacy flow（舊流程）

目前可見 legacy flow 主要是：

- `POST /api/attendance/mock-create`
- `POST /api/attendance/{attendance_record_id}/approve`

其路徑為：

- `api/legacy.py`
- `service.py` 的 legacy service methods
- `repo.py` 內 legacy `AttendanceRepository`

特徵：

- 使用舊的 `AttendanceRecord` 型態與 approve 事件流
- 不屬於新的 session/punch/policy/reporting 主線
- 仍為 production contract 相容層
- 仍被測試覆蓋與依賴

### 2.2 New flow（新流程）

目前可見 new flow 主要由以下 endpoint 組成：

#### Punch / Session flow
- `POST /api/v1/attendance/punch-in`
- `POST /api/v1/attendance/punch-out`
- `GET /api/v1/attendance/current-status`
- `GET /api/v1/attendance/history`

主要路徑：

- `api/punch.py`
- `AttendanceSessionRepository`
- `AttendanceService.build_punch_out_policy_evaluation()`
- `punch_close_domain.build_policy_evaluation()`
- `policy_engine.py`

#### Break flow
- `POST /api/v1/attendance/break-out`
- `POST /api/v1/attendance/break-in`
- `GET /api/v1/attendance/break-punches`
- `PATCH /api/v1/attendance/punch/{punch_id}/note`

主要路徑：

- `api/breaks.py`
- `AttendanceSessionRepository`
- 部分 endpoint 直接查 ORM model
- 借用 `api/reporting_helpers.py`

#### Reporting flow
- `GET /api/v1/attendance/sessions`
- `GET /api/v1/attendance/reports/user-summary`
- `GET /api/v1/attendance/reports/company-summary`

主要路徑：

- `api/reporting.py`
- `reporting_repo`
- `reporting_service`

### 2.3 哪些 endpoint 走 legacy

走 legacy：

- `/api/attendance/mock-create`
- `/api/attendance/{attendance_record_id}/approve`

### 2.4 哪些 endpoint 走 new flow

走 new flow：

- `/api/v1/attendance/punch-in`
- `/api/v1/attendance/punch-out`
- `/api/v1/attendance/current-status`
- `/api/v1/attendance/history`
- `/api/v1/attendance/break-out`
- `/api/v1/attendance/break-in`
- `/api/v1/attendance/break-punches`
- `/api/v1/attendance/punch/{punch_id}/note`
- `/api/v1/attendance/sessions`
- `/api/v1/attendance/reports/user-summary`
- `/api/v1/attendance/reports/company-summary`

### 2.5 是否混用

結論：**有共存，但主流程層面屬「並存多流」，不是單一路徑內的大量 legacy/new 互叫。**

但有三種混用風險：

1. **檔案級混用**
   - `service.py` 同時放 legacy service 與 new close-flow orchestration
   - `repo.py` 同時放 legacy repository 與 new session repository

2. **入口級混用**
   - `api.py` 與 `api/__init__.py` 都在扮演組裝入口角色

3. **policy 層歷史混用**
   - `policy_engine.py` 同時保留 `evaluate()`、`evaluate_with_schedule()`、`evaluate_with_schedule_v2()`
   - 顯示舊 façade 與新 schedule-aware façade 歷史層次仍同檔共存

---

## 3. Coupling Findings

### 3.1 API 呼叫 service 又直接碰 repo

**存在。**

代表情況：

- `api/punch.py`
  - `punch-out` 先直接使用 `AttendanceSessionRepository`
  - 再呼叫 `AttendanceService.build_punch_out_policy_evaluation()`
  - 屬於 API 同時掌握 repo 與 service 的 orchestration

這種耦合代表：

- close-flow orchestration 並未完全收斂到單一 service boundary
- API 端仍掌握 session close 前後多個步驟
- canonical 寫入雖然目前正確維持 gross，但 owner boundary 容易被再次拉回 API

### 3.2 API 直接碰 ORM / query

**存在。**

在 `api/breaks.py`：

- `GET /break-punches` 直接查 `AttendancePunch`
- `PATCH /punch/{punch_id}/note` 直接查 `AttendancePunch`、直接 commit

這是明確 cross-layer coupling：

- API 不只呼叫 repo，還直接進 ORM read/write
- 造成 breaks flow 一部分走 repository，一部分繞過 repository
- 會讓 repo contract 難以成為單一 owner

### 3.3 API 借用 API 層 helper 承擔別的責任

**存在。**

在 `api/breaks.py`：

- 使用 `api/reporting_helpers.py` 的 date boundary helper

這不是最重的問題，但表示：

- breaks flow 對 reporting 命名空間產生依賴
- helper 放置位置帶來語意耦合
- read-side boundary 工具沒有穩定中立落點

### 3.4 service 依賴 API helper

**目前審計範圍內未見 service 直接依賴 API helper。**

這一點相對乾淨。

### 3.5 policy 被 API / service 控制流程

**存在，但屬目前主線設計的一部分；風險在於控制權邊界仍不夠集中。**

表現為：

- API `punch-out` 先算 gross / break deduction，再呼叫 service
- service 再呼叫 `punch_close_domain.build_policy_evaluation()`
- `punch_close_domain` 再呼叫 `AttendancePolicyEngine`

這表示 policy 並非純 consumer 型被動讀取，而是被夾在 close-flow orchestration 中被調度。

風險不是「policy 被使用」，而是：

- orchestration 被拆散在 API / service / domain helper 三處
- 一旦新增 schedule-aware、missing segment、break deduction 相關需求，容易再次互相穿透

### 3.6 reporting 反向影響主流程

**目前未見 reporting 直接反向控制主流程。**

`api/reporting.py` 主要為 consumer：

- 用 `reporting_repo`
- 用 `reporting_service`
- 讀取 canonical `duration_minutes`

此部分與正式語意基準一致。

### 3.7 policy engine 與主流程的歷史耦合

**存在。**

`policy_engine.py` 同時持有：

- `evaluate()`
- `evaluate_with_schedule_v2()`
- `evaluate_with_schedule()`

這不是單純 API/service coupling，而是 **policy façade 自身仍承載 legacy/new/schedule-aware 多種歷史演化層次**。

### 3.8 router / module 組裝耦合

**存在。**

- `api/__init__.py` 組裝 merged `router_v1`
- `api.py` 也仍存在 router 組裝與大量匯入痕跡
- `api.py` 還直接匯入 `api.legacy.router`

這形成「組裝權限不只一個地方」的 coupling。

---

## 4. Responsibility Overlap

### 4.1 Close-flow orchestration 責任重疊

**存在。**

責任分散於：

- `api/punch.py`
- `service.py`
- `punch_close_domain.py`
- `policy_engine.py`

其中：

- API 負責 session open 查找、punch write、gross minutes 計算、close call
- service 負責 missing segment dry-run 與 policy evaluation entry
- domain helper 負責 policy payload adapter
- policy engine 負責 evaluation façade

這表示同一條 close-flow 不是單一 owner 完整持有，而是多層共同擁有。

### 4.2 Repository ownership 重疊

**存在。**

`repo.py` 內同時有：

- `AttendanceSessionRepository`（new flow）
- `AttendanceRepository`（legacy flow）

同一個檔案內承載兩代 persistence contract，導致：

- 檔案風險集中
- 容易在後續修改時誤觸另一條 flow

### 4.3 Service ownership 重疊

**存在。**

`service.py` 同時有：

- legacy `mock_create_attendance()`
- legacy `approve_attendance()`
- new `build_punch_out_policy_evaluation()`
- new missing-segment internal dry-run support

這是典型雙重 owner：

- 舊 attendance record 流程 owner
- 新 session close-flow orchestration owner

### 4.4 Policy responsibility overlap

**存在，但集中在 policy engine 歷史層次重疊。**

`policy_engine.py` 同時扮演：

- basic evaluation façade
- schedule-aware façade
- result assembly
- fallback glue

雖然 pure rule 已部分拆出，但 façade 仍非單純單責任。

### 4.5 Break flow ownership overlap

**存在。**

`api/breaks.py` 內同時混合：

- endpoint orchestration
- location policy enforcement
- repository write
- ORM direct read/write
- Taipei date boundary helper 使用

breaks flow 沒有穩定收斂到單一中介層。

---

## 5. High-Risk Core Files

### 5.1 `backend/app/modules/attendance/api.py`

**高風險原因：**

- 仍保留大檔 façade 歷史角色
- 匯入 legacy router、新 repo、新 service、policy engine、checkpoint repo 等多個責任面
- 與 `api/__init__.py` 形成雙組裝面

**是否多責任集中：是。**

風險判定：

- 容易成為舊新路由、依賴、掛載規則的殘留聚合點
- 未來開發者若在此加功能，極容易重新把已拆分責任拉回單檔

### 5.2 `backend/app/modules/attendance/api/__init__.py`

**高風險原因：**

- 扮演 `router_v1` 實際 merge 點
- 把 punch、breaks、checkpoints、reporting 都集中掛入
- 屬於全模組 v1 route assembly 核心

**是否多責任集中：中度。**

主要不是業務邏輯集中，而是：

- mounting contract 集中
- 任一子 router prefix / export 變動都會牽動全域

### 5.3 `backend/app/modules/attendance/api/reporting.py`

**高風險原因：**

- 屬 canonical consumer 主出口
- summary semantics 完全依賴 persisted `duration_minutes`
- 只要有人把 reporting 變成 reinterpretation layer，就會直接碰 canonical

**是否多責任集中：中低。**

相較其他檔案，這支目前責任較清楚，但因為它是 canonical consumer，**語意風險高於結構風險**。

### 5.4 `backend/app/modules/attendance/service.py`

**高風險原因：**

- legacy flow 與 new flow 並存
- 同時承載 event flow、legacy approve、close-flow policy evaluation、missing-segment dry-run
- 已成為 service 層跨世代責任疊加點

**是否多責任集中：是，且明顯。**

### 5.5 `backend/app/modules/attendance/repo.py`

**高風險原因：**

- 同檔同時放 legacy repository 與 new session repository
- session/punch read-write 與 legacy attendance record read-write 共檔
- 屬 persistence contract 的雙系統共居點

**是否多責任集中：是，且明顯。**

### 5.6 `backend/app/modules/attendance/policy_engine.py`

**高風險原因：**

- 已被治理文件明確標示為高風險膨脹檔
- 同時保留 basic evaluation、schedule-aware façade、result assembly、fallback glue
- 屬 legacy/new schedule-aware 路徑的歷史聚合點

**是否多責任集中：是。**

### 5.7 `backend/app/modules/attendance/punch_close_domain.py`

**高風險原因：**

- 名稱上是 domain helper，但實際承擔 close-flow evaluation adapter
- 夾在 service 與 policy engine 中間
- 容易成為「為了方便再多塞一點」的擴張點

**是否多責任集中：中度。**

### 5.8 `backend/app/modules/attendance/api/breaks.py`

**高風險原因：**

- API 內直接碰 repo、ORM、location policy、reporting helper
- break flow 未明確收斂到單一中介層

**是否多責任集中：是。**

---

## 6. Router / Mounting Findings

### 6.1 router_v1 merge

`api/__init__.py` 目前是可見的 `router_v1` merge 中心：

- include punch router
- include breaks router
- include checkpoints router
- include reporting router

這種做法本身可接受，但風險在於：

- 所有 v1 route export 集中於單一 assembly 面
- 子模組只要 export 名稱、prefix、router 型態改動，就會影響整體掛載

### 6.2 `api/__init__.py` 組裝風險

有兩個主要風險：

1. **掛載集中風險**
   - 單一 merge 點造成全局耦合

2. **與 `api.py` 並存的裝配歧義**
   - `api.py` 與 `api/__init__.py` 都像 assembly surface
   - 增加維護者判斷成本：真正權威掛載點是哪一個

### 6.3 隱性耦合

**存在。**

隱性耦合主要來自：

- `api.py` 仍保留大量與新/舊 API 都有關的 import 痕跡
- `api/__init__.py` 是實際 merged export
- tests 中可見對 router/import 結構曾出現歷史脆弱點的註記

結論：

- routing contract 並非只有單一清晰入口
- mounting 風險屬真實存在，不只是命名問題

---

## 7. Canonical Safety

### 7.1 coupling 是否可能影響 canonical

**會，屬間接風險；目前未見直接覆寫。**

目前 canonical 仍符合既定決議：

- `punch-out` 以 gross minutes 計算
- `session.duration_minutes` 寫入 gross
- break deduction 只做 derived/informational
- reporting 讀 persisted canonical 欄位
- policy evaluation 消費 canonical work minutes

### 7.2 indirect override risk 是否存在

**存在。**

來源如下：

1. **API orchestration 與 service orchestration 未完全單一 owner 化**
   - 若未來有人在 API 直接補 policy / net minutes / reporting shaping，可能繞過 canonical owner 邊界

2. **policy engine 歷史層次仍混合**
   - 若 schedule-aware / fallback / result assembly 被擴寫，可能重新吸入非 consumer 責任

3. **breaks flow 的 layer 穿透**
   - API 直接碰 ORM / helper，表示 boundary discipline 不穩
   - 這種風格若外溢到 punch-out close flow，canonical 會先暴露風險

4. **service / repo 舊新共檔**
   - 同檔雙流存在，會提高誤改 canonical 路徑的機率

### 7.3 Canonical safety 結論

結論：**Canonical 目前安全，但安全性依賴開發紀律，不是由結構完全保證。**

---

## 8. Test Coverage

### 8.1 測試是否覆蓋 new flow

**有，且覆蓋面不小。**

可見覆蓋包含：

- `test_punch_api.py`
  - punch-in / punch-out / current-status / history / tenant isolation
- `test_router_v1_jwt_migration.py`
  - router_v1 JWT flow、breaks、sessions、summary
- `test_reporting_sessions.py`
- `test_reporting_user_summary.py`
- `test_reporting_company_summary.py`
- `test_punch_break_integration.py`
  - punch-out + break deduction / anomaly audit 整合
- `test_service_internal_dry_run.py`
  - service internal missing-segment dry-run

### 8.2 legacy flow 是否仍被測試依賴

**是。**

legacy flow 仍被下列測試依賴：

- `test_api.py`
- `test_phase4.py`

代表：

- legacy API 仍不是完全死亡路徑
- 仍屬保留中的 production/testing contract

### 8.3 測試是否覆蓋 schedule-aware new flow

**目前可見覆蓋偏弱。**

審計範圍內可見：

- `policy_engine.py` 有 `evaluate_with_schedule()` 與 `evaluate_with_schedule_v2()`
- `punch_close_domain.py` 有 `build_policy_evaluation_with_schedule_v2()`

但在本次讀到的主要 API / service / tests 中：

- 沒看到對 schedule-aware close-flow 的主線 endpoint 使用證據
- 也沒看到相應明確整合測試作為主力覆蓋

這表示：

- new flow 的「一般 v1 路徑」有測
- 但 new flow 中更進一步的 schedule-aware 變體不是主要測試重心

### 8.4 測試覆蓋結論

結論：

- **legacy flow 仍被測試依賴**
- **一般 new flow 有覆蓋**
- **schedule-aware new flow 覆蓋不足，是未來耦合風險盲區**

---

## 9. Future Risk

- **High**

### 9.1 未來新增功能最容易壞在哪

最容易壞在以下區域：

1. `punch-out` close flow
   - API / service / domain helper / policy engine 共同持有
   - 任何新需求最容易在這條路徑塞入額外責任

2. `breaks.py`
   - 已有 API 直碰 ORM 與 helper 的跨層模式
   - 最容易持續膨脹成例外聚集區

3. router / mounting surface
   - `api.py` 與 `api/__init__.py` 並存
   - 最容易出現掛載認知錯位

### 9.2 哪個 layer 會先失控

**最先失控的層很可能是 API 層，其次是 service façade 層。**

原因：

- API 層目前已經承擔過多 orchestration 與直接資料存取
- service 層則承擔 legacy/new 雙責任
- 若需求持續疊加，最先膨脹的不是 reporting，而是 API + service 邊界

### 9.3 是否存在「不可控擴張點」

**存在。**

主要不可控擴張點：

- `service.py`
- `repo.py`
- `policy_engine.py`
- `api/breaks.py`
- `api.py`

原因共同點：

- 都是「為了方便最容易再多放一點」的檔案
- 都已承載多代 flow 或多層責任
- 都不是單一純 consumer 檔

### 9.4 最大風險敘述

未來最大的風險不是某一個 bug，而是：

- legacy/new flow 雖未正面互撞，但已在核心檔內形成**共居耦合**
- 一旦未來在 close-flow 或 breaks flow 上持續擴寫，將很容易重新出現
  - owner 不清
  - canonical 邊界模糊
  - policy / reporting / break deduction 責任回滲

---

## 10. Audit Conclusion

本票審計結論如下：

1. **legacy flow 與 new flow 確實共存。**
2. **目前以並列共存為主，不是大量直接互叫，但存在明顯檔案級與裝配級耦合。**
3. **`service.py`、`repo.py`、`policy_engine.py`、`api.py`、`api/breaks.py` 已構成高風險核心檔群。**
4. **reporting 目前仍維持 consumer-only 角色，與 canonical 決議一致。**
5. **canonical 目前未被 coupling 直接破壞，但 indirect override risk 真實存在。**
6. **tests 仍同時依賴 legacy 與 new flow；一般 new flow 有測，但 schedule-aware 新路徑覆蓋不足。**
7. **未來最容易破壞的區域是 close-flow orchestration 與 breaks flow。**

最終判定：

- 結構狀態為 **可運作，但耦合風險偏高**
- 審計等級建議視為 **High future risk**
- 本票完成後應將此結論視為後續所有 close-flow / breaks / router 掛載相關開發的前置風險基準
