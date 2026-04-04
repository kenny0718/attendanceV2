# SA21_GAP_AUDIT_REPORT

## purpose

本文件為 SA2.1 對齊審計正式報告，目的在於：

1. 以 `docs/01_ARCHITECTURE/SA_MODULE_SPEC_v2.1.md` 為唯一架構規範基準。
2. 以實際程式碼（backend/frontend）為 reality source，校正文檔與現況落差。
3. 明確標示高風險模組與責任邊界衝突，供後續 Step 3 / runtime hardening phase 拆票執行。
4. 建立新的 SA2.1 對齊 Source of Truth（SOT）文件組。

---

## audit scope

### code scope（reality source）

- `backend/app/main.py`
- `backend/app/modules/attendance/`（含 `api.py`, `api/reporting.py`, `service.py`, `repo.py`, `reporting_*`, `policy_*`）
- `backend/app/modules/leave/`
- `backend/app/modules/schedule/`
- `frontend/src/router/index.js`
- `frontend/src/api/`（`client.js`, `attendance.js`, `leave.js`, `schedule.js`）
- `frontend/src/stores/reporting.js`
- `frontend/src/views/reports/*`
- `frontend/src/views/schedule/SchedulePage.vue`
- `frontend/src/views/LeaveRequestView.vue`

### docs baseline scope

- `docs/00_AI_GOVERNANCE/*`（治理規範）
- `docs/01_ARCHITECTURE/SA_MODULE_SPEC_v2.1.md`
- `docs/01_ARCHITECTURE/ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md`（已歸檔）
- `docs/01_ARCHITECTURE/REPORTING_MODULE_ARCHITECTURE.md`
- `docs/03_WP_CONTROL/*` 主要控制文件（多份已歸檔）

---

## files/modules inspected

### backend

- `backend/app/main.py`
- `backend/app/modules/attendance/api.py`
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/api/reporting_helpers.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/reporting_repo.py`
- `backend/app/modules/attendance/reporting_service.py`
- `backend/app/modules/attendance/reporting_schemas.py`
- `backend/app/modules/attendance/policy_engine.py`
- `backend/app/modules/attendance/policy_rules.py`
- `backend/app/modules/attendance/policy_schedule_models.py`
- `backend/app/modules/leave/api.py`
- `backend/app/modules/schedule/api.py`

### frontend

- `frontend/src/router/index.js`
- `frontend/src/api/client.js`
- `frontend/src/api/attendance.js`
- `frontend/src/api/leave.js`
- `frontend/src/api/schedule.js`
- `frontend/src/stores/reporting.js`
- `frontend/src/views/reports/AttendanceSessionsPage.vue`
- `frontend/src/views/reports/UserSummaryPage.vue`
- `frontend/src/views/reports/CompanySummaryPage.vue`
- `frontend/src/views/schedule/SchedulePage.vue`
- `frontend/src/views/LeaveRequestView.vue`

---

## SA2.1 gap summary

### overall alignment

- **符合度：中高（約 70~80%）**
- 已符合：Platform-first + JWT actor + tenant isolation 主幹路徑大致到位。
- 主要落差：文檔治理失真、模組邊界滲漏、前後端 contract 不一致、入口層過重。

### core conflicts (top)

1. **SOT 文檔群互相衝突**：多份控制文件的當前 WP 與模組狀態互斥。
2. **`main.py` 責任過重**：router 掛載 + middleware + startup demo 訂閱 + test event endpoint 混入。
3. **attendance 模組邊界過寬**：`service.py` 已含 policy missing segment dry-run 與 punch 段推導，易持續膨脹。
4. **routing split 不一致**：`attendance/api.py` 已 façade 化，但 reporting 走 `api/reporting.py`，主入口聚合策略未統一治理。
5. **frontend API base path drift**：`attendance.js` 用 `/v1/...`，`schedule.js` 用 `/api/v1/...`，同一 `apiClient(baseURL=/api)` 下存在雙規格。
6. **leave frontend/backed contract 弱對齊**：前端 `leave_type` 只做 UI 選項，實際提交依賴手動 `leave_type_id(UUID)`。
7. **報表聚合責任雖已拆層，但仍需防膨脹**：`api/reporting.py` 現已精簡，但流程控制仍在 router 層持有部分細節。
8. **高風險大頁已出現**：`SchedulePage.vue` 體量與責任密度偏高，具複合 CRUD + inline edit + state 協調。

### most deviated modules

- `backend/app/main.py`
- `backend/app/modules/attendance/service.py`
- `frontend/src/api/schedule.js`（相對於全域 API base 規則）
- `frontend/src/views/schedule/SchedulePage.vue`
- `docs/03_WP_CONTROL/*`（舊 SOT 集合）

---

## module conflict matrix

| module/file | current responsibility | SA2.1 expected responsibility | gap/conflict | risk | action suggestion |
|---|---|---|---|---|---|
| `backend/app/main.py` | app init + middleware + startup handlers + test event endpoints + all router mounts | app composition root，保持薄層，避免業務/示範邏輯混入 | startup demo / test event 路徑混入 production entry | high | split required |
| `attendance/api.py` | façade + legacy import + v1 router 聚合入口 | 路由層僅做 parse/scope/dispatch | 與 `api/reporting.py` 並存，邊界治理不一致 | medium | boundary clarification required |
| `attendance/api/reporting.py` | reporting routes + scope + repo call + response mapping | route thin, orchestration 下放 service | 仍持有較多流程組裝與 mapping 細節 | medium | refactor later |
| `attendance/reporting_service.py` | pure aggregation（無 DB） | orchestration/aggregation core | 與規範方向一致，尚可 | low | keep |
| `attendance/reporting_repo.py` | reporting query + tenant filter | read-only query layer | 與規範方向一致，尚可 | low | keep |
| `attendance/service.py` | core attendance service + missing segment dry-run input 組裝 | service 聚焦單一業務流程，避免跨子域推導擴張 | 內含額外段推導責任，演進易膨脹 | high | split required |
| `attendance/repo.py` | attendance + policy + punch + 部分多責任聚合 | repo 單責任資料存取 | 方法面向漸增，邊界趨模糊 | medium | refactor later |
| `frontend/src/api/client.js` | axios base + auth interceptor + error normalize | 全域 API contract 樞紐 | 與個別 api 模組的 path 規格未完全一致 | medium | boundary clarification required |
| `frontend/src/api/attendance.js` | attendance/reporting API wrappers | feature-domain API wrapper | 與 baseURL 規則一致（`/v1/...`） | low | keep |
| `frontend/src/api/schedule.js` | schedule API wrappers | feature-domain API wrapper | 路徑使用 `/api/v1/...`，與 baseURL 重複前綴風險 | high | boundary clarification required |
| `frontend/src/views/schedule/SchedulePage.vue` | template CRUD + assignment CRUD + inline edit + UI state orchestration | view 層應保持可讀性與中等複雜度 | 單頁責任過多，屬持續膨脹熱點 | high | split required |
| `frontend/src/views/LeaveRequestView.vue` | leave create + partial list preview | 單頁單流程可接受 | 與後端 leave type contract 對齊偏弱（UUID 手輸） | medium | refactor later |
| `docs/03_WP_CONTROL` 舊控制文件群 | 歷史狀態混雜 | SOT 單線、可追溯、低歧義 | 多份文件互斥、易誤導開發順序 | high | split required（已改為歸檔 + 新SOT） |

---

## high-risk files

### 1) `backend/app/main.py`

**why high-risk**
- 入口層聚合過多責任，任何調整都可能影響整體啟動與路由掛載。
- 含 startup demo / test event endpoint，與 production composition root 混雜。

**what should NOT be changed now**
- 不應在本階段直接做大規模重構或直接移除既有端點。

**ticketing direction**
- 先拆出「startup wiring / demo hooks / debug endpoints」治理票，再做最小掛載清理。

### 2) `backend/app/modules/attendance/service.py`

**why high-risk**
- service 層責任已擴至 missing-segment dry-run input 建模與 punch 片段推導。
- 隨後續 runtime hardening，極易繼續吸入判定邏輯，造成超大型 service。

**what should NOT be changed now**
- 不在本輪直接搬動 policy 邏輯到 engine 或 repo（避免邏輯漂移）。

**ticketing direction**
- 先定義 attendance close-flow 子域邊界，再逐步拆出 segment inference adapter。

### 3) `frontend/src/views/schedule/SchedulePage.vue`

**why high-risk**
- 單頁承擔模板/指派雙子域 CRUD，並含 inline edit、同步狀態與錯誤處理。
- 變更容易引發非預期 UI regression。

**what should NOT be changed now**
- 不應直接重寫整頁或一口氣重組所有表格交互。

**ticketing direction**
- 先按 template/assignment 分離子元件，再拆 composable/store 邏輯。

### 4) `frontend/src/api/schedule.js`

**why high-risk**
- 與 `apiClient` 的 baseURL 規則不一致，易造成路徑重複與環境切換錯誤。

**what should NOT be changed now**
- 不在本輪直接改 endpoint contract。

**ticketing direction**
- 先做 API path contract 對齊票（只做 path normalization，不改業務邏輯）。

---

## boundary / logic conflicts

### document vs implementation

1. 多份 `03_WP_CONTROL` 文件對「當前 WP、完成度、模組狀態」描述互斥。
2. `ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md` 的描述與現行程式碼演進有時序落差。
3. `API_DOCUMENTATION_v2.1.md` 標記 Draft/Partially Implemented，已不足以當現行 SOT。

### test vs implementation

1. policy baseline 先前存在 UTC vs Taipei business semantic drift（本次前一輪已在指定測試檔收斂）。
2. leave 模組自動化測試覆蓋資訊與實際發展節奏存在缺口（屬技術債，不阻塞本次文檔收斂）。

### API/service/repo boundary cleanliness

1. reporting 子域已有 `reporting_repo` / `reporting_service`，方向正確；但 router 仍保留部分組裝責任。
2. attendance `service.py` 與 `repo.py` 責任線正在變寬，需提前控制。

### frontend/backend contract drift

1. API 路徑規格不一致：`attendance.js`（`/v1/...`） vs `schedule.js`（`/api/v1/...`）。
2. leave create 畫面與後端 leave type model 間缺少「可選清單」契約，暫以 UUID 手輸。

### acceptable temporary debt vs must-fix structural

- **可接受暫存債（可進 P2）**：UI 文案一致性、小型 formatting 差異、手動輸入 UX 不佳但可用。
- **必須先處理（P0/P1）**：SOT 文件衝突、入口與大模組責任過寬、API path contract 不一致。

---

## superseded documents

以下文件已不再作為現行 SA2.1 對齊 SOT，已移動至 `docs/archive/260402/`：

- `docs/03_WP_CONTROL/CURRENT_SYSTEM_STATE.md`
- `docs/03_WP_CONTROL/SYSTEM_DEVELOPMENT_STATUS_SNAPSHOT.md`
- `docs/03_WP_CONTROL/MODULE_STATUS_MATRIX.md`
- `docs/03_WP_CONTROL/GATE_PROGRESS_TRACKER.md`
- `docs/03_WP_CONTROL/CURRENT_DEVELOPMENT_STATUS_AUDIT_2026-03-17.md`
- `docs/03_WP_CONTROL/ATTENDANCE_DEVELOPMENT_ROADMAP.md`
- `docs/01_ARCHITECTURE/ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md`

### needs manual review（保留於現路徑，暫不搬移）

- `docs/01_ARCHITECTURE/REPORTING_MODULE_ARCHITECTURE.md`
- `docs/01_ARCHITECTURE/API_DOCUMENTATION_v2.1.md`
- `docs/03_WP_CONTROL/NEXT_WP_TICKET.md`
- `docs/03_WP_CONTROL/WORKSTREAM_STATUS_LEDGER.md`

---

## current source of truth statement

自本次審計後，SA2.1 對齊與後續重整的主要依據為：

1. `docs/01_ARCHITECTURE/SA21_GAP_AUDIT_REPORT.md`（本文件）
2. `docs/03_WP_CONTROL/SA21_REALIGNMENT_ROADMAP.md`

說明：
- 上述兩份文件負責「現況-規範差距」與「後續執行順序」。
- 既有歷史文件改為參考用途，不再作為開發啟動時的主 SOT。
