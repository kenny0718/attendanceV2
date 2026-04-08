# ATTENDANCE DEVELOPMENT ROADMAP

> **⚠️ 每次開工前必讀本文件**
> 本文件定義 Attendance 系統目前的真實開發位置、各 WP 的正確順序，
> 以及後續所有 AI / Cursor session 的開發依據。

**建立日期：** 2026-03-14
**基於：** repo 實際 code scan + docs 交叉驗證
**當前 WP：** WP-11-07 — Reporting UI Polish / QA / UX Improvements
**下一個 WP：** WP-11-08 — Leave Request System

---

## 1. Purpose（文件目的）

本文件為 Attendance 系統的正式開發 Roadmap，目的如下：

1. **固定目前真實開發位置** — 以 repo 與 docs 為準，不依賴記憶或假設
2. **定義各 WP 的正確順序** — 防止 AI / 開發流程亂跳模組
3. **防止誤判已完成功能** — 特別是 Reporting UI MVP 已存在，不可當作未開始
4. **作為每次新工作開始前的必讀文件** — 讀完本文件才能確認「現在在哪、下一步是什麼」
5. **作為所有後續 WP 開發的順序依據** — 任何新 WP 開始前必須先對照本文件

### 重要聲明

> 本文件不是理論規劃，而是對應真實 repo 狀態的治理文件。
> 若文件間有輕微不一致，以目前實際 repo 狀態與已驗證結果為準。

---

## 2. Current System Status（系統現況）

### 2.1 已完成模組（COMPLETE / STABLE）

| 模組 | 狀態 | 說明 |
|------|------|------|
| **Punch Engine** | ✅ STABLE | punch-in/out、session 建立、跨午夜規則、tenant isolation |
| **Break Engine** | ✅ STABLE | break-out/break-in、GPS 地點條件式驗證 |
| **Session Model** | ✅ STABLE | AttendanceSession 完整資料模型，含 status、duration、breaks、location |
| **Policy Engine** | ✅ STABLE | 遲到/早退/加班計算、Split Shift 支援 |
| **Timezone / Cross-midnight Rules** | ✅ STABLE | Session ownership = punch_in_time 的 Asia/Taipei 日期（SA v2.1 §29.2）|
| **Reporting Backend API** | ✅ COMPLETE | 三支 endpoint 全部實作並驗證，詳見 WP-11-06 |

### 2.2 進行中（IN PROGRESS）

| 模組 | 狀態 | 說明 |
|------|------|------|
| **Reporting UI** | 🔄 MVP COMPLETE，Polish Pending | 三頁 UI 存在且功能可用，WP-11-07 聚焦 polish/QA |

**Reporting UI 現有檔案（已確認存在）：**
- `frontend/src/views/reports/AttendanceSessionsPage.vue`
- `frontend/src/views/reports/CompanySummaryPage.vue`
- `frontend/src/views/reports/UserSummaryPage.vue`
- `frontend/src/stores/reporting.js`
- `frontend/src/api/attendance.js`（含 fetchSessions / fetchCompanySummary / fetchUserSummary）

### 2.3 部分完成（FOUNDATION ONLY）

| 模組 | 狀態 | 說明 |
|------|------|------|
| **GPS / Location** | ⚠️ FOUNDATION ONLY | useLocation.js + location_policy_service.py + gps_utils.py 存在；break-out 條件式驗證；**不是完整 GPS 模組** |

> ⚠️ **重要警告：GPS 僅為 foundation，不得誤判為完整完成。**
> punch-in / punch-out / break-in 均無 location policy check（明確缺口）。
> 完整 GPS / Field Work 為 WP-11-10，屬 Phase 3，目前 NOT STARTED。

### 2.4 尚未開始（NOT STARTED）

| 模組 | WP | 說明 |
|------|-----|------|
| **Leave Request** | WP-11-08 | 請假申請、審核流程；Phase 2 |
| **Shift / Schedule** | WP-11-09 | 班表管理；Phase 2 |
| **GPS / Field Work（完整）** | WP-11-10 | 外勤打卡完整實作；Phase 3 |
| **Auth 轉換 Batch 2** | WP-C1-03 | audit/notifications/backup 模組 JWT 遷移 |
| **回歸測試真實 DB** | WP-C1-04 | 8 個回歸測試在真實 DB 通過（目前 0/8）|
| **Tenant Isolation 驗證** | WP-C1-05 | 5 個測試在真實 DB 通過（目前 0/5）|
| **Feature Gate 套用** | WP-C1-06 | 所有核心 API 套用 Feature Gate（目前 0%）|


---

## 3. Fixed WP Order（固定開發順序）

以下為 Attendance 系統後續固定執行順序。**不得跳過、不得重排。**

```
[已完成]
WP-11-06  Reporting Backend API              ✅ COMPLETE   (2026-03-14)

[進行中]
WP-11-07  Reporting UI Polish / QA           🔄 IN PROGRESS  ← 現在位置

[已完成的基礎設施 WP，與 Feature WP 並行]
WP-C1-07  Attendance API JWT 遷移            ✅ COMPLETED  (2026-03-12)
WP-C1-08  Test Re-Enable + Fixture           ✅ FIXTURE_COMPLETE (2026-03-12)
WP-C1-09  OUT Checkpoint API                 ✅ DONE       (2026-03-12)

[後續 Feature WP 順序]
WP-11-08  Leave Request System               ⏳ NOT STARTED  (WP-11-07 完成後)
WP-11-09  Shift / Schedule                   ⏳ NOT STARTED  (WP-11-08 完成後)
WP-11-10  GPS / Field Work（完整）           ⏳ NOT STARTED  (Phase 3)

[後續基礎設施 WP]
WP-C1-03  Auth 轉換 Batch 2                  ⏳ NOT STARTED
WP-C1-04  8 個回歸測試（真實 DB）            ⏳ NOT STARTED
WP-C1-05  Tenant Isolation 真實 DB 驗證      ⏳ NOT STARTED
WP-C1-06  Feature Gate 套用                  ⏳ NOT STARTED

[Phase 1 完成里程碑]
→ Gate 5 完成（估計完成度目前 45%）
```

### 3.1 各 WP 摘要表

| WP | 名稱 | Goal | Dependencies | 狀態 |
|----|------|------|-------------|------|
| WP-11-06 | Reporting Backend | 三支 Reporting API | WP-11-01~05 | ✅ COMPLETE |
| WP-11-07 | Reporting UI Polish / QA | UI polish、QA、error/empty/loading state | WP-11-06 | 🔄 IN PROGRESS |
| WP-11-08 | Leave Request System | 請假申請、審核流程 | WP-11-07 | ⏳ NOT STARTED |
| WP-11-09 | Shift / Schedule | 班表管理、指派 | WP-11-08 | ⏳ NOT STARTED |
| WP-11-10 | GPS / Field Work | 外勤打卡完整實作 | WP-11-09 | ⏳ NOT STARTED |

### 3.2 關鍵限制

- WP-11-07 完成前，**不得開始** WP-11-08
- WP-11-08 完成前，**不得開始** WP-11-09
- WP-11-10 是 Phase 3，需等 Phase 2 完成
- GPS Foundation（目前存在）≠ WP-11-10 GPS/Field Work 完整實作


---

## 4. WP Details（各 WP 詳細說明）

---

### WP-11-06 — Reporting Backend API

**狀態：** ✅ COMPLETE（2026-03-14）

**Goal：**
實作 Attendance Reporting 後端 API，提供三支 reporting endpoint。

**Deliverables（已完成）：**

| Endpoint | 狀態 |
|----------|------|
| `GET /api/v1/attendance/sessions` | ✅ COMPLETE |
| `GET /api/v1/attendance/reports/user-summary` | ✅ COMPLETE |
| `GET /api/v1/attendance/reports/company-summary` | ✅ COMPLETE |

**已驗證事項：**
- OpenAPI `/docs` 顯示三支 endpoint ✅
- UI 三頁（Sessions / User Summary / Company Summary）可正常呼叫 API ✅
- Tenant isolation 強制執行（所有查詢含 WHERE company_id）✅
- ReportingRepository（4 個方法）完整 ✅
- schemas.py（SessionsListResponse / UserSummaryResponse / CompanySummaryResponse）完整 ✅

**Runtime Issue（已解決）：**
初始問題為 uvicorn reloader 孤兒 worker（PID 1856041，2026-03-11 16:58 啟動）導致
`api.py` 修改後未 reload。以 clean restart 解決，無需修改任何程式碼。
詳見：`docs/WP-REPORTING-BACKEND_RUNTIME_MISMATCH_REPORT.md`

**Scope：**
- Sessions 列表 API（含分頁、日期篩選、status 篩選）
- User Summary API（個人出勤聚合統計）
- Company Summary API（公司出勤聚合統計）

**Out of Scope：**
- CSV / PDF 匯出
- 圖表資料 API
- 請假 / 班表整合

**Completion Definition：** ✅ 已滿足所有驗收條件

---

### WP-11-07 — Reporting UI Polish / QA / UX Improvements

**狀態：** 🔄 IN PROGRESS（MVP Complete，Polish Pending）

> ⚠️ **重要：WP-11-07 不是從零開始做 Reporting UI。**
> Reporting UI MVP 已存在且功能可用。本 WP 聚焦在 polish、QA、error/empty/loading state 驗收。

**Goal：**
對已存在的 Reporting UI MVP 進行手動 QA、錯誤狀態修復、UX 改善，達到可驗收的品質標準。

**目前 MVP 已存在的檔案：**
- `frontend/src/views/reports/AttendanceSessionsPage.vue`
- `frontend/src/views/reports/CompanySummaryPage.vue`
- `frontend/src/views/reports/UserSummaryPage.vue`
- `frontend/src/stores/reporting.js`
- Reporting 相關 components：DateRangeFilter.vue、MonthPicker.vue、PaginationBar.vue、StatusBadge.vue、SummaryCard.vue

**Scope（本 WP 工作範圍）：**
- 手動 QA：SessionList、UserSummary、CompanySummary 三頁全部驗收
- Error state 處理（API 錯誤 → 使用者可見訊息）
- Empty state 處理（無資料 → 適當空狀態顯示）
- Loading state polish
- 篩選 UX 改善（日期區間清晰度、filter 互動）
- 日期 / 時長格式顯示一致性
- 權限邊界情況修復（不同角色的存取驗證）
- BUG-01 修復（若尚未完成）：`stores/reporting.js` response 解構確認正確

**Out of Scope：**
- 重建 Reporting Backend（已 COMPLETE，不可重做）
- 從零設計 Reporting UI（MVP 已存在）
- 新增報表類型（未來 WP）
- Shift / Schedule UI
- Leave Request UI

**Dependencies：** WP-11-06 COMPLETE ✅

**Completion Definition：**
- [ ] 三頁 Reporting UI 手動 QA 全部通過
- [ ] Error state：API 錯誤 → 使用者可見訊息
- [ ] Empty state：無資料 → 適當空狀態顯示
- [ ] Loading state polish 完成
- [ ] 日期 / 時長格式顯示一致
- [ ] 篩選 UX 已驗收
- [ ] 所有角色權限存取已驗證

**Blocks：** WP-11-08（Leave Request）必須等本 WP COMPLETE 後才能開始


---

### WP-11-08 — Leave Request System

**狀態：** ⏳ NOT STARTED（等待 WP-11-07 COMPLETE）

**Goal：**
實作員工請假申請與主管審核流程，包含後端 API、資料模型與前端 UI。

**Scope（規劃）：**
- 員工申請請假（類型、起訖時間、原因）
- 主管審核（核准 / 拒絕）
- 請假記錄查詢
- Leave balance 查詢（若設計有此需求）
- Tenant isolation 強制執行

**Out of Scope：**
- 不可直接修改 Punch core 或 attendance_sessions table
- 不包含自動扣除出勤計算（由後續 WP 視需求補充）
- 不包含班表整合（WP-11-09 範疇）

**預定架構位置（依 ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md §6）：**

```
Backend:
  modules/leave/
    api.py       -- POST /api/v1/leave/request
                    GET  /api/v1/leave/requests
                    POST /api/v1/leave/requests/{id}/approve
    schemas.py   -- LeaveRequest / LeaveApprovalRequest
    models.py    -- leave_requests table（新 migration）
    repo.py      -- LeaveRepository
    service.py   -- 請假業務邏輯

Frontend:
  views/leave/LeaveRequestPage.vue
  views/leave/LeaveApprovalPage.vue
  stores/leave.js
  api/leave.js
```

**Dependencies：** WP-11-07 COMPLETE

**Completion Definition（初稿，實作前需細化）：**
- 員工可提交請假申請
- 主管可審核申請
- 請假記錄可查詢
- Tenant isolation 驗證通過
- 所有新 API 使用 JWT auth

> 本 WP 目前為 roadmap 規劃。實作前必須先建立完整 Spec 文件，
> 並更新 NEXT_WP_TICKET.md 與 GATE_PROGRESS_TRACKER.md。

---

### WP-11-09 — Shift / Schedule

**狀態：** ⏳ NOT STARTED（等待 WP-11-08 COMPLETE）

**Goal：**
實作班表管理功能，支援班次建立、員工指派與出勤比對。

**Scope（規劃）：**
- 班次定義（上班時間、下班時間、休息規則）
- 員工班表指派
- 班表與出勤記錄比對（遲到/早退依班表計算）
- 班表查詢（月曆視圖）

**Out of Scope：**
- 不可修改 Punch core（只能讀取 attendance_sessions 進行比對）
- 不包含自動排班 AI（手動排班）

**預定架構位置（依 ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md §6）：**

```
Backend:
  modules/shift/
    api.py       -- 班表 CRUD endpoints
    schemas.py   -- ShiftSchedule / ShiftAssignment
    models.py    -- shift_schedules / shift_assignments tables
    repo.py      -- ShiftRepository
    service.py   -- 班表指派、衝突檢查

Frontend:
  views/shift/ShiftCalendarPage.vue
  stores/shift.js
  api/shift.js
```

**Dependencies：** WP-11-08 COMPLETE

**Completion Definition（初稿，實作前需細化）：**
- 班次可建立、修改、刪除
- 員工可指派班次
- 班表月曆頁可顯示
- Tenant isolation 驗證通過

> 本 WP 目前為 roadmap 規劃。實作前必須先建立完整 Spec 文件。

---

### WP-11-10 — GPS / Field Work（完整實作）

**狀態：** ⏳ NOT STARTED（Phase 3，等待 Phase 2 完成）

> ⚠️ **重要警告：目前系統有 GPS Foundation，但這不是 WP-11-10。**
> 現有 GPS 能力：useLocation.js、location_policy_service.py、gps_utils.py、break-out 條件式驗證。
> 這些是 **foundation**，不是完整的 GPS / Field Work 模組。
> 不得將現有 GPS Foundation 誤判為 WP-11-10 已完成。

**現有 GPS Foundation 狀態：**

| 功能 | 狀態 |
|------|------|
| `useLocation.js` composable | ✅ 存在 |
| `location_policy_service.py` | ✅ 存在 |
| `gps_utils.py`（Haversine 距離計算）| ✅ 存在 |
| break-out 條件式 location check | ✅ 部分完成 |
| punch-in location check | ❌ 缺口 |
| punch-out location check | ❌ 缺口 |
| break-in location check | ❌ 缺口 |
| 外勤打卡專屬流程 | ❌ 未實作 |
| Field Work 頁面 | ❌ 未實作 |

**Goal（WP-11-10 完整實作）：**
實作完整的 GPS 地點驗證與外勤打卡流程。

**Scope（規劃）：**
- 所有打卡動作的 GPS 地點政策強制驗證
- 外勤打卡專屬頁面與流程
- GPS 邏輯集中（不散落各頁面）

**核心原則：**
- `useLocation.js` 是唯一 Frontend GPS 入口，不可在各頁面重複實作
- `location_policy_service.py` 是唯一後端地點驗證入口
- Field Work 打卡作為新路由，**不修改現有 Home.vue 打卡流程**

**Dependencies：** WP-11-09 COMPLETE（Phase 2 完成）

> 本 WP 目前為 roadmap 規劃。Phase 3 開始前需重新細化 Spec。

---

### WP-11-11 及後續（Future Backlog）

以下為已知的後續規劃方向，目前未有詳細 Spec，列為 Future Backlog：

| WP | 方向 | 說明 |
|----|------|------|
| WP-C1-03 | Auth 轉換 Batch 2 | audit / notifications / backup 模組 JWT 遷移 |
| WP-C1-04 | 回歸測試真實 DB | 8 個核心回歸測試在真實 PostgreSQL 通過 |
| WP-C1-05 | Tenant Isolation 驗證 | 5 個測試在真實 DB 通過 |
| WP-C1-06 | Feature Gate 套用 | 所有核心 API 套用 Feature Gate |
| Phase 4+ | SaaS Platform Completion | 詳見 MASTER_DEVELOPMENT_ROADMAP_v2.md |


---

## 5. Current Position Marker（目前位置標記）

```
╔══════════════════════════════════════════════════════════════╗
║  CURRENT WP  :  WP-11-07                                    ║
║  CURRENT PHASE:  Reporting UI Polish / QA / UX Improvements ║
║  STATUS      :  IN PROGRESS — MVP Complete, Polish Pending  ║
╚══════════════════════════════════════════════════════════════╝
```

### 已完成的事項

- WP-11-06 Reporting Backend API：三支 endpoint 全部 COMPLETE（2026-03-14）
- Reporting UI MVP：三頁 UI 存在且功能可用（AttendanceSessionsPage / CompanySummaryPage / UserSummaryPage）
- stores/reporting.js：存在，API 整合已實作
- Reporting 相關共用元件：DateRangeFilter、MonthPicker、PaginationBar、StatusBadge、SummaryCard 均存在
- JWT Auth 遷移（WP-C1-07）：COMPLETED（2026-03-12）
- Test Fixture Layer（WP-C1-08）：FIXTURE_COMPLETE（2026-03-12）
- OUT Checkpoint API（WP-C1-09）：DONE（2026-03-12）

### 下一步（Next Actions for WP-11-07）

1. 手動 QA 三頁 Reporting UI
2. 驗收 error / empty / loading state
3. 修復 BUG-01（若尚未完成）：確認 stores/reporting.js response 解構正確
4. 日期 / 時長格式顯示一致性
5. 篩選 UX 確認
6. 不同角色權限邊界確認

### 阻塞 / 非阻塞狀態

| 項目 | 狀態 | 說明 |
|------|------|------|
| WP-11-07 進行 | ✅ 未阻塞 | WP-11-06 已 COMPLETE，可繼續 |
| WP-11-13 Manual QA | ⛔ BLOCKED | 需真實瀏覽器 + PostgreSQL 環境 |
| WP-C1-03 Auth Batch 2 | ⏳ 等待安排 | 未阻塞，但尚未開始 |
| WP-11-08 Leave Request | ⛔ 等待 WP-11-07 | 不得提前開始 |

### 給後續 AI 的一句話摘要

> **目前不是從頭做 Reporting，也不是等待 Backend。**
> **Reporting Backend 已 COMPLETE，Reporting UI MVP 已存在。**
> **現在的任務是 WP-11-07：對已存在的 UI 進行 polish、QA、error state 修復。**


---

## 6. Development Rules（開發規則）

以下規則適用於所有後續開發工作，AI 與人類開發者均須遵守。

### 6.1 順序規則

1. **不得跳票開發** — 未完成當前 WP，不得切去下一個核心模組
2. **不得超前實作** — 未到該 WP，不得預先實作其功能
3. **不得並行核心模組** — 同一時間只能有一個 Feature WP 進行中

### 6.2 狀態判斷規則

4. **不得把 MVP Complete 的功能誤判為 not started**
   - Reporting UI 已有 MVP，不是從零開始
   - GPS Foundation 已存在，但不代表 WP-11-10 已完成
5. **不得把 CODE_COMPLETE 視為 VERIFIED**
   - 程式碼存在 ≠ 在真實環境驗證通過
   - 詳見 MODULE_STATUS_MATRIX.md 的狀態定義

### 6.3 核心保護規則

6. **不得為了新功能重構 Punch / Session / Policy 核心**
   - Leave Request、Shift、GPS 均不可修改 Punch core
   - 若真有必要，必須先建立正式 WP 並說明原因
7. **不得繞過層級架構**
   - Page → Store → API Client → Backend（不可跳層）

### 6.4 文件規則

8. **所有新 WP 必須先更新狀態文件**
   - 開始前：更新 NEXT_WP_TICKET.md
   - 完成後：更新 GATE_PROGRESS_TRACKER.md + WORKSTREAM_STATUS_LEDGER.md
9. **遇到阻塞立即記錄**
   - 記錄位置：WORKSTREAM_STATUS_LEDGER.md

### 6.5 開發流程規則

10. **所有開發必須遵循：**
    ```
    Spec → API Contract → Backend → Frontend → Test → Docs
    ```
    不得跳過任何步驟。

---

## 7. Protected Core Reminder（核心保護區提醒）

以下檔案為系統核心保護區。**沒有明確 WP 需求時，不可隨意修改。**

### 7.1 Punch Core（最高保護等級）

| 檔案 | 保護原因 |
|------|----------|
| `backend/app/modules/attendance/service.py` | Punch/Break 業務邏輯核心，跨午夜規則 |
| `backend/app/modules/attendance/models.py` | ORM 模型定義，改動影響 migration chain |
| `backend/app/modules/attendance/policy_engine.py` | 政策計算核心，Split Shift 邏輯 |
| `frontend/src/stores/attendance.js` | 前端打卡狀態機 |
| `frontend/src/views/Home.vue` | 主打卡頁，3-Card 佈局與打卡主流程 |
| `frontend/src/api/client.js` | Axios base instance，response interceptor |

### 7.2 Auth / Tenant Isolation（高保護等級）

| 檔案 | 保護原因 |
|------|----------|
| `frontend/src/stores/auth.js` | JWT token 管理、userRole、companyId |
| `backend/app/core/tenant_context.py` | Tenant isolation 依賴層 |
| `backend/app/core/dependencies.py` | JWT DI 依賴注入 |
| `backend/app/core/security/jwt.py` | JWT 簽發 / 驗證邏輯 |

### 7.3 Timezone / Cross-midnight Rules

- Session ownership date = punch_in_time 的 **Asia/Taipei** 日期（SA v2.1 §29.2）
- 月報歸屬 = punch_in_time 所在月份（SA v2.1 §29.3）
- 所有 datetime 傳輸必須 timezone-aware（ISO 8601 with tz）
- **這些規則不得在未完成正式 SA 變更前修改**

### 7.4 Tenant Isolation Query Pattern

- 所有查詢必須含 `WHERE company_id = ?`
- ReportingRepository 強制 tenant isolation，不可移除
- 新增 Repo 方法時必須延續此 pattern

### 7.5 Migration Chain

- 目前 HEAD：`008_wp_11_13`（17 tables）
- Migration chain 為單一線性結構，無分叉
- 新功能需要新 table 時，**必須新增 migration，不可修改現有 migration**
- 不得 squash 或刪除現有 migration

---

## 8. Handoff Guidance for Future Cursor Sessions（交接說明）

### 8.1 每次開始新 WP 前，必須執行以下步驟

1. **讀取本文件**（ATTENDANCE_DEVELOPMENT_ROADMAP.md）確認當前 WP 與順序
2. **讀取 NEXT_WP_TICKET.md** 確認當前 WP 狀態與前置條件
3. **讀取 GATE_PROGRESS_TRACKER.md** 確認整體進度
4. **讀取 ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md** 確認模組位置與分層規則
5. **確認不會修改第 7 節列出的核心保護區檔案**

### 8.2 關鍵注意事項（給後續 AI）

**❌ 不要做的事：**

- 不要自行跳去 Leave Request / Shift / GPS 實作
- 不要把 Reporting UI MVP 當成「還沒做」
- 不要把 GPS Foundation 當成「WP-11-10 已完成」
- 不要在未完成 WP-11-07 前開始 WP-11-08
- 不要因為 Leave / Shift / GPS 需求重構 Punch core
- 不要重新實作已有的 Reporting Backend
- 不要在 stores/reporting.js 中對 API response 多取一層 .data（client.js interceptor 已 unwrap）

**✅ 應該做的事：**

- 每次 session 開始先確認 current WP
- 若 UI 已有 MVP，從 polish / QA 角度接手，不是從零開始
- 若要改核心模組，必須先說明原因並確認有明確 WP 授權
- 遇到阻塞立即記錄，不要靜默跳過
- 完成 WP 後立即更新 NEXT_WP_TICKET.md + GATE_PROGRESS_TRACKER.md

### 8.3 快速定位指引

| 需要確認的事項 | 閱讀文件 |
|---------------|----------|
| 目前在哪個 WP | 本文件第 5 節 |
| 各 WP 順序 | 本文件第 3 節 |
| 模組位置 / 分層規則 | ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md §2 |
| 哪些檔案不能動 | 本文件第 7 節 / ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md §8 |
| 整體進度 | GATE_PROGRESS_TRACKER.md |
| 當前 WP 詳細 | NEXT_WP_TICKET.md |
| Reporting 資料流 | ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md §4 |
| GPS 現況 | ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md §5 |

### 8.4 一句話總結

> Attendance 系統目前在 **WP-11-07（Reporting UI Polish / QA）**。
> Reporting Backend 已 COMPLETE，Reporting UI MVP 已存在。
> 下一個大模組是 WP-11-08 Leave Request，但必須等 WP-11-07 完成後才能開始。
> GPS 只有 Foundation，完整實作（WP-11-10）是 Phase 3 的事。

---

## 9. Document Version & Update Rules

| 欄位 | 值 |
|------|----|
| **文件版本** | 1.0 |
| **建立日期** | 2026-03-14 |
| **基於** | repo code scan（2026-03-14）+ docs 交叉驗證 |
| **狀態** | ✅ ACTIVE |

### 何時更新本文件

- 每完成一個 WP → 更新第 2 節狀態表 + 第 5 節 Current Position Marker
- 有新 WP 加入規劃 → 更新第 3 節順序表 + 第 4 節 WP Details
- 有架構異動 → 同步更新相關章節
- **本文件與 ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md 須保持一致**

---

*本文件由 AI 依據 2026-03-14 實際 repo 狀態與 docs 交叉驗證建立。*
*權威基礎：GATE_PROGRESS_TRACKER.md + NEXT_WP_TICKET.md + repo 真實結構。*

**END OF ATTENDANCE_DEVELOPMENT_ROADMAP.md**
