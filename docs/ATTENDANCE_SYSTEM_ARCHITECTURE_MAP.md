# Attendance System — Architecture Map

> **文件目的**：本文件為 Attendance System 的整體架構地圖，供開發者與 AI 協作時作為固定參考基準。
> 所有後續開發必須先對照本文件確認模組位置，不得隨意新增或搬移層級。
>
> **建立日期**：2026-03-14
> **基於**：repo 實際 code scan（2026-03-14）
> **系統現況**：WP-11-06 COMPLETE；WP-11-07 IN PROGRESS

---


> NOTE：本文件只負責 **系統架構說明 (Architecture)**。  
> 開發順序與進度請參考：`docs/ATTENDANCE_DEVELOPMENT_ROADMAP.md`。


## 1. System Overview

### 已完成核心模組

| 模組 | 說明 | 狀態 |
|------|------|------|
| **Punch Engine** | 打卡核心（punch-in/punch-out），含 session 建立、跨午夜規則、tenant isolation | STABLE |
| **Break Engine** | 外出/返回打卡（break-out/break-in），含 GPS 地點驗證（條件式） | STABLE |
| **Session Model** | AttendanceSession 完整資料模型，含 status、duration、breaks、location 欄位 | STABLE |
| **Policy Engine** | 打卡政策評估（遲到/早退/加班計算、Split Shift 支援） | STABLE |
| **GPS / Location Foundation** | AllowedLocation、location_policy_service.py、gps_utils.py；break-out 條件式驗證 | STABLE |
| **Reporting Backend** | 三支 Reporting API（Sessions / User Summary / Company Summary），含 ReportingRepository | COMPLETE |
| **Reporting UI MVP** | 三頁 Reporting UI（AttendanceSessions / CompanySummary / UserSummary）+ stores/reporting.js | IN PROGRESS |

### 目前 WP 位置

    WP-11-06  Reporting Backend API          COMPLETE      (2026-03-14)
    WP-11-07  Reporting UI Polish / QA       IN PROGRESS  <- 現在位置
    WP-C1-03  Auth 轉換 Batch 2              NOT STARTED
    WP-C1-04  8 個回歸測試（真實 DB）        NOT STARTED
    WP-C1-05  Tenant Isolation 真實 DB 驗證  NOT STARTED
    WP-C1-06  Feature Gate 套用              NOT STARTED
    [Phase 1 Complete / Gate 5]              估計完成度 45%

WP-11-08 Leave Request、WP-11-09 Shift/Schedule、WP-11-10 GPS Field Work
均為 Phase 2/3 範疇，目前 NOT STARTED，位置已預留於第 6 節。

---

## 2. Layered Architecture

### 完整分層架構圖

    +==================================================================+
    |                      FRONTEND LAYER                              |
    |                                                                  |
    |  Views / Pages  (frontend/src/views/)                            |
    |  | Home.vue                <- 主打卡頁 [核心保護區]           |  |
    |  | Login.vue               <- 登入頁                          |  |
    |  | reports/AttendanceSessionsPage.vue   <- Reporting          |  |
    |  | reports/CompanySummaryPage.vue       <- Reporting          |  |
    |  | reports/UserSummaryPage.vue          <- Reporting          |  |
    |  +------------------------+-----------------------------------+  |
    |                           | reads / dispatches actions           |
    |  Pinia Stores  (frontend/src/stores/)                            |
    |  | attendance.js  <- 打卡狀態 [核心保護區，不可動]            |  |
    |  | auth.js        <- JWT / userRole / companyId [保護區]      |  |
    |  | reporting.js   <- Reporting 頁面狀態                       |  |
    |  +------------------------+-----------------------------------+  |
    |                           | calls                                |
    |  API Client  (frontend/src/api/)                                 |
    |  | client.js       <- Axios base instance [核心保護區]        |  |
    |  |                    Bearer + X-Company-ID headers           |  |
    |  |                    response interceptor unwraps .data      |  |
    |  | attendance.js   <- Punch/Break + Reporting methods         |  |
    |  | auth.js         <- 登入 API                                |  |
    |  +------------------------+-----------------------------------+  |
    |  Router: / | /login | /attendance/reports/* + beforeEach      |  |
    |  Composables: useLocation.js  <- GPS 定位（僅供 Location）    |  |
    +==================================================================+
                          | HTTP/REST JSON
                          | Authorization: Bearer <JWT>
                          | X-Company-ID / X-User-ID headers
    +==================================================================+
    |                      BACKEND LAYER                               |
    |                                                                  |
    |  FastAPI Routers  (backend/app/modules/attendance/)              |
    |  | api.py  router（/api/attendance）                          |  |
    |  |   POST /mock-create   POST /{id}/approve                   |  |
    |  | api.py  router_v1（/api/v1/attendance）                    |  |
    |  |   POST /punch-in        POST /punch-out                    |  |
    |  |   GET  /current-status  GET  /history                      |  |
    |  |   POST /break-out       POST /break-in                     |  |
    |  |   GET  /break-punches   PATCH /punch/{id}/note             |  |
    |  |   GET  /sessions                   <- Reporting API        |  |
    |  |   GET  /reports/user-summary       <- Reporting API        |  |
    |  |   GET  /reports/company-summary    <- Reporting API        |  |
    |  | admin_location_api.py（/api/v1/admin/allowed-locations）           |  |
    |  |   POST / GET / GET/{id} / PUT/{id} / DELETE/{id}           |  |
    |  +------------------------+-----------------------------------+  |
    |  Core Layer  (backend/app/core/)                                 |
    |  | tenant_context.py    <- get_current_company_id() Header    |  |
    |  | dependencies.py      <- get_current_actor() JWT DI         |  |
    |  | security/jwt.py      <- JWT 簽發 / 驗證                   |  |
    |  | features.py + feature_service.py <- Feature Gate           |  |
    |  | scope.py             <- Scope / RBAC 邏輯                  |  |
    |  +------------------------+-----------------------------------+  |
    |  Service / Policy Layer                                          |
    |  | service.py                 <- Punch/Break 業務邏輯          |  |
    |  | policy_engine.py           <- 遲到/加班/Split Shift 計算    |  |
    |  | location_policy_service.py <- GPS 地點政策驗證             |  |
    |  | gps_utils.py               <- Haversine 距離計算            |  |
    |  +------------------------+-----------------------------------+  |
    |  Repository Layer                                                |
    |  | repo.py  AttendanceRepository  <- Punch/Session CRUD       |  |
    |  | repo.py  ReportingRepository   <- 報表專用查詢（4 方法）   |  |
    |  |   get_sessions_for_reporting()  count_sessions_for_...()   |  |
    |  |   get_user_summary_sessions()   get_company_summary_...()  |  |
    |  +------------------------+-----------------------------------+  |
    |  Database Layer  (PostgreSQL)                                    |
    |  | attendance_sessions  attendance_breaks  attendance_punches |  |
    |  | attendance_policies  allowed_locations  location_policies  |  |
    |  | users  tenants  company_entitlements  audit_logs           |  |
    |  | HEAD migration: 008_wp_11_13 (17 tables total)             |  |
    +==================================================================+

### 其他 Backend 模組

    backend/app/modules/
    ├── auth/            JWT 簽發；已完成
    ├── tenants/         entitlements CRUD（已用 JWT）
    ├── customer_service/ 指派公司管理（已用 JWT）
    ├── audit/           audit logs（仍用 Header auth，待 WP-C1-03）
    ├── backup/          export/restore（仍用 Header auth，待 WP-C1-03）
    └── notifications/   通知（仍用 Header auth，待 WP-C1-03）

### 簡化資料流

    Frontend Page -> Pinia Store -> api/attendance.js -> api/client.js
      -> FastAPI Router -> Core (auth/tenant) -> Service/Policy
      -> Repository -> PostgreSQL

---

## 3. Current Implemented Modules

### 3.1 Frontend 模組（真實檔案結構）

    frontend/src/
    ├── router/index.js
    │     路由: /  |  /login
    │           /attendance/reports/sessions
    │           /attendance/reports/company-summary
    │           /attendance/reports/user-summary
    │
    ├── stores/
    │   ├── attendance.js       [核心保護區] Punch/Break/Session 狀態
    │   ├── auth.js             [保護區] JWT token / userRole / companyId
    │   └── reporting.js        Reporting 頁面狀態（BUG-01 已修正）
    │
    ├── api/
    │   ├── client.js           [核心保護區] Axios instance
    │   │                       response interceptor unwraps .data
    │   ├── attendance.js       Punch/Break methods + Reporting methods
    │   │     fetchSessions()       -> GET /v1/attendance/sessions
    │   │     fetchCompanySummary() -> GET /v1/attendance/reports/company-summary
    │   │     fetchUserSummary()    -> GET /v1/attendance/reports/user-summary
    │   └── auth.js             登入 API
    │
    ├── views/
    │   ├── Home.vue            [核心保護區] 主打卡頁
    │   ├── Login.vue           登入頁
    │   └── reports/
    │       ├── AttendanceSessionsPage.vue  Sessions 列表 + 日期篩選 + 分頁
    │       ├── CompanySummaryPage.vue      公司出勤彙總摘要卡
    │       └── UserSummaryPage.vue         個人出勤彙總摘要卡
    │
    ├── components/
    │   ├── attendance/         [保護區] 打卡相關區塊元件，不可修改
    │   │     AttendanceOverviewCard.vue / OutActionsSection.vue
    │   │     OutingOverviewCard.vue / OutLogsSection.vue
    │   │     OutReasonSection.vue / PunchActionsSection.vue
    │   │     RecentPunchLogsSection.vue / TodayStatusSection.vue
    │   ├── Card.vue / Navbar.vue
    │   ├── DateRangeFilter.vue  月份選擇器（Reporting 用）
    │   ├── MonthPicker.vue      月份選擇器（Reporting 用）
    │   ├── PaginationBar.vue    分頁控制（Reporting 用）
    │   ├── StatusBadge.vue      出勤狀態標籤（Reporting 用）
    │   └── SummaryCard.vue      摘要數字卡片（Reporting 用）
    │
    ├── composables/useLocation.js   GPS 定位 composable（僅供 Location 模組）
    └── utils/locationAdapter.js     GPS 座標轉換工具

### 3.2 Backend 模組（真實檔案結構）

    backend/app/
    ├── main.py                             FastAPI app 入口，include_router 掛載
    ├── core/
    │   ├── config.py / database.py / dependencies.py / exceptions.py
    │   ├── tenant_context.py               get_current_company_id() — 現為 Header auth
    │   ├── security/jwt.py + password.py
    │   ├── features.py + feature_service.py  Feature Gate（基礎完整，未套用生產）
    │   └── scope.py + event_bus.py
    └── modules/
        ├── attendance/                     [核心模組]
        │   ├── api.py                      router + router_v1（所有 endpoint）
        │   ├── schemas.py                  Pydantic request/response models
        │   ├── models.py                   SQLAlchemy ORM models
        │   ├── repo.py                     AttendanceRepository + ReportingRepository
        │   ├── service.py                  Punch/Break 業務邏輯
        │   ├── policy_engine.py            政策評估（遲到/加班/Split Shift）
        │   ├── location_policy_service.py  GPS 地點政策驗證
        │   ├── gps_utils.py                Haversine 距離計算
        │   ├── admin_location_api.py       地點管理 admin API（無 RBAC，待修復）
        │   ├── feature_gate_demo.py        Feature Gate 示範（非生產用）
        │   └── tests/
        │       ├── test_api.py / test_business_invariant.py
        │       ├── test_model_constraints.py / test_policy_engine.py
        │       ├── test_punch_api.py
        │       ├── test_regression.py          8 個回歸測試（1/8 骨架，0/8 通過）
        │       ├── test_reporting_sessions.py
        │       ├── test_reporting_user_summary.py
        │       ├── test_reporting_company_summary.py
        │       ├── test_tenant_isolation.py
        │       └── test_location_policy.py / test_break_out_enforcement.py
        ├── auth/           JWT 簽發模組
        ├── tenants/        Entitlements 管理（已用 JWT）
        ├── customer_service/ 指派公司管理（已用 JWT）
        ├── audit/          Audit logs（仍用 Header auth）
        ├── backup/         Export / Restore（仍用 Header auth）
        └── notifications/  通知（仍用 Header auth）

---

## 4. Reporting Module Map

### 架構圖

    +------------------------------------------------------------------+
    |                      REPORTING MODULE                            |
    |  Frontend Pages                                                  |
    |    AttendanceSessionsPage.vue                                    |
    |      日期篩選 / status 篩選 / Sessions 列表 / 分頁               |
    |    CompanySummaryPage.vue  -> 月份選擇 / 7 個摘要數字卡片        |
    |    UserSummaryPage.vue     -> 月份選擇 / 個人 6 個摘要卡片       |
    |                           |  dispatch actions                    |
    |  Pinia Store: stores/reporting.js                                |
    |    state: sessions / sessionsTotal / sessionsLoading             |
    |    state: companySummary / userSummary + loading/error           |
    |    action: fetchSessions(params)                                 |
    |    action: fetchCompanySummary(params)                           |
    |    action: fetchUserSummary(params)                              |
    |                           |  calls                               |
    |  API Service: api/attendance.js                                  |
    |    fetchSessions()       -> GET /api/v1/attendance/sessions       |
    |    fetchCompanySummary() -> GET /api/v1/attendance/reports/       |
    |                              company-summary                     |
    |    fetchUserSummary()    -> GET /api/v1/attendance/reports/       |
    |                              user-summary                        |
    |  api/client.js Axios  response interceptor unwraps .data         |
    +------------------------------------------------------------------+
                          | HTTP GET（含日期範圍 / status / 分頁）
    +------------------------------------------------------------------+
    |  Backend                                                         |
    |  attendance/api.py router_v1                                     |
    |    GET /sessions             -> SessionsListResponse             |
    |    GET /reports/user-summary -> UserSummaryResponse              |
    |    GET /reports/company-summary -> CompanySummaryResponse        |
    |  attendance/schemas.py                                           |
    |    SessionsListResponse（sessions[] + total/limit/offset）       |
    |    UserSummaryResponse（8 欄位，含 nullable）                    |
    |    CompanySummaryResponse（10 欄位，含 nullable）                |
    |  attendance/repo.py  ReportingRepository                         |
    |    全部強制 WHERE company_id（tenant isolation）                 |
    |  PostgreSQL: attendance_sessions JOIN attendance_breaks          |
    +------------------------------------------------------------------+

### Reporting 資料流

    UI 選擇日期區間
      -> reporting.js store.fetchSessions(params)
      -> api/attendance.js.fetchSessions(params)
      -> Axios GET /api/v1/attendance/sessions?start_date=...
      -> FastAPI router_v1 GET /sessions
      -> ReportingRepository.get_sessions_for_reporting(company_id, ...)
      -> PostgreSQL SELECT FROM attendance_sessions WHERE company_id = ?
      -> response { sessions: [...], total, limit, offset }
      -> client.js interceptor unwraps .data
      -> store.sessions = data.sessions  (直接賦值，不可再取 .data)

### 注意事項

- api/client.js response interceptor 已 unwrap response.data
- Store 的 fetch 方法回傳值直接是 body object，不可再取 .data
- 日期傳至後端必須帶 timezone（ISO 8601 with +08:00 or Z）
- punch_out_time = null 時 UI 顯示「進行中」；duration_minutes = null 時 UI 顯示「—」」
- average_* 欄位為 null 時 UI 顯示「—」

---

## 5. GPS / Location Module Map

### 目前實作位置

    Frontend:
      composables/useLocation.js
        getCurrentPosition() -- 封裝 browser Geolocation API
        使用於 Home.vue (break-out 時取得座標)
      utils/locationAdapter.js -- GPS 座標格式轉換工具

    Backend:
      attendance/gps_utils.py
        calculate_distance() -- Haversine 公式
      attendance/location_policy_service.py
        get_active_allowed_locations(company_id)
        check_location_policy(company_id, lat, lng)
        -- 若無地點配置則允許所有位置（fallback）
      attendance/admin_location_api.py
        POST/GET/PUT/DELETE /api/v1/admin/allowed-locations
        [WARNING] 3 個寫入 endpoint 無 RBAC（待 WP-C1-02 修復）
      Database:
        allowed_locations -- 每個 tenant 的許可地點清單
        location_policies -- 地點政策設定

### 目前 Location Policy 覆蓋狀況

    punch-in   -- 無 location policy check  [缺口，待 WP-C2-01]
    punch-out  -- 無 location policy check  [缺口，待 WP-C2-01]
    break-in   -- 無 location policy check  [缺口，待 WP-C2-01]
    break-out  -- 條件式 check（有傳 location 才驗證）[部分完成]

### 未來 GPS / Field Work 接入位置（WP-11-10，Phase 3）

    Frontend:
      composables/useLocation.js      -- 擴展（不可重複實作）
      views/fieldwork/                -- 新增 Field Work 打卡頁
      stores/location.js              -- 新增 GPS 狀態 store
      api/location.js                 -- 新增 Location API 方法

    Backend:
      attendance/api.py router_v1     -- 新增 field-work punch endpoints
      attendance/location_policy_service.py -- 擴展強制驗證邏輯

    規則：GPS 邏輯必須集中在 useLocation.js + location_policy_service.py，
          不可散落在各頁面或各 endpoint 重複實作。

---

## 6. Future Modules Placement

以下為未來模組的預定掛載位置（目前 NOT STARTED，不得提前實作）。

### WP-11-08 Leave Request（Phase 2）

    Backend 新增:
      modules/leave/
        api.py       -- POST /api/v1/leave/request
                        GET  /api/v1/leave/requests
                        POST /api/v1/leave/requests/{id}/approve
        schemas.py   -- LeaveRequest / LeaveApprovalRequest
        models.py    -- LeaveRequest table（新 migration）
        repo.py      -- LeaveRepository
        service.py   -- 請假業務邏輯（扣除、衝突檢查）

    Frontend 新增:
      views/leave/LeaveRequestPage.vue    -- 員工申請頁
      views/leave/LeaveApprovalPage.vue   -- 主管審核頁
      stores/leave.js                     -- 請假狀態
      api/leave.js                        -- Leave API 方法
      router/index.js 新增路由: /leave /approvals

    規則：Leave 模組不可直接修改 Punch core 或 attendance_sessions table。

### WP-11-09 Shift / Schedule（Phase 2）

    Backend 新增:
      modules/shift/
        api.py       -- 班表 CRUD endpoints
        schemas.py   -- ShiftSchedule / ShiftAssignment
        models.py    -- shift_schedules / shift_assignments tables
        repo.py      -- ShiftRepository
        service.py   -- 班表指派、衝突檢查

    Frontend 新增:
      views/shift/ShiftCalendarPage.vue   -- 班表月曆頁
      stores/shift.js                     -- 班表狀態
      api/shift.js                        -- Shift API 方法

    規則：Shift 可讀取 attendance_sessions 進行比對，不可修改 Punch core。

### WP-11-10 GPS / Field Work（Phase 3）

    詳見第 5 節「未來 GPS / Field Work 接入位置」。
    核心原則：
      - GPS 邏輯集中，不散落
      - useLocation.js 是唯一 Frontend GPS 入口
      - location_policy_service.py 是唯一後端地點驗證入口
      - Field Work 打卡作為新路由，不修改現有 Home.vue 打卡流程

---

## 7. Dependency Rules

### 7.1 Frontend 規則

| 規則 | 說明 |
|------|------|
| Page 不可直接碰 DB | 只能透過 Store -> API Client -> Backend |
| Store 不可含業務規則 | 業務邏輯必須在 Backend Service 層 |
| useLocation.js 是唯一 GPS 入口 | 不可在各頁面重複實作 GPS 取得邏輯 |
| Reporting 不可影響 Punch flow | stores/reporting.js 與 stores/attendance.js 完全獨立 |
| 新功能必須新增路由 | 不可把新功能塞進 Home.vue |

### 7.2 Backend 規則

| 規則 | 說明 |
|------|------|
| Router 不可含業務邏輯 | api.py 只做參數解析、呼叫 Service/Repo |
| Reporting 不可影響 Punch flow | ReportingRepository 只做 SELECT，不可修改 sessions 資料 |
| GPS 模組必須集中 | location_policy_service.py 是唯一後端地點驗證入口 |
| Leave / Shift 不可改 Punch core | 新模組只能透過 Service 層讀取出勤資料 |
| 所有查詢必須含 company_id | Tenant isolation 是強制要求，沒有例外 |

### 7.3 開發流程規則

    新功能必須走：
    Spec -> API Contract -> Backend (Service/Repo/Schema)
         -> Frontend (Store/View) -> Test -> Docs

    不得跳過任何步驟。
    不得在未完成當前 WP 前切去下個模組。
    所有新 WP 都必須先更新 NEXT_WP_TICKET.md 和 GATE_PROGRESS_TRACKER.md。

---

## 8. Protected Core Areas

以下為系統核心保護區。沒有明確 WP 需求時，不可隨意修改這些檔案。

### 8.1 Punch Core（最高保護等級）

| 檔案 | 保護原因 |
|------|----------|
| `backend/app/modules/attendance/service.py` | Punch/Break 業務邏輯核心，跨午夜規則、session 狀態機 |
| `backend/app/modules/attendance/models.py` | ORM 模型定義，改動會影響 migration chain |
| `backend/app/modules/attendance/repo.py` AttendanceRepository 部分 | Punch/Session CRUD，tenant isolation 查詢 pattern |
| `backend/app/modules/attendance/policy_engine.py` | 政策計算核心，Split Shift 邏輯 |
| `frontend/src/stores/attendance.js` | 前端打卡狀態機，Punch/Break flow |
| `frontend/src/views/Home.vue` | 主打卡頁，3-Card 佈局與打卡主流程 |
| `frontend/src/api/client.js` | Axios base instance，response interceptor |

### 8.2 Auth / Tenant Isolation（高保護等級）

| 檔案 | 保護原因 |
|------|----------|
| `frontend/src/stores/auth.js` | JWT token 管理、userRole、companyId |
| `backend/app/core/tenant_context.py` | Tenant isolation 依賴層 |
| `backend/app/core/dependencies.py` | JWT DI 依賴注入 |
| `backend/app/core/security/jwt.py` | JWT 簽發 / 驗證邏輯 |

### 8.3 Timezone / Cross-midnight Rules

- Session ownership date = punch_in_time 的 Asia/Taipei 日期（SA v2.1 §29.2）
- 月報歸屬 = punch_in_time 所在月份（SA v2.1 §29.3）
- 所有 datetime 傳輸必須 timezone-aware（ISO 8601 with tz）
- 這些規則不得在未完成正式 SA 變更前修改

### 8.4 Migration Chain

- 目前 HEAD：`008_wp_11_13`（17 tables）
- Migration chain 為單一線性結構，無分叉
- 新功能需要新 table 時，必須新增 migration 而非修改現有 migration
- 不得 squash 或刪除現有 migration

---

## 9. Current Roadmap Position

    [Gate 5 - Frontend UI Phase]

    Phase 1 - Security Baseline Repair           IN PROGRESS (45%)
      WP-C1-01  PostgreSQL 環境 + Migration      VERIFIED  (2026-03-11)
      WP-C1-07  Attendance API JWT 遷移          COMPLETED (2026-03-12)
      WP-C1-08  Test Re-Enable + Fixture         FIXTURE_COMPLETE (2026-03-12)
      WP-C1-09  OUT Checkpoint API               DONE (2026-03-12)
      WP-C1-03  Auth 轉換 Batch 2               NOT STARTED
      WP-C1-04  8 個回歸測試（真實 DB）          NOT STARTED
      WP-C1-05  Tenant Isolation 真實 DB         NOT STARTED
      WP-C1-06  Feature Gate 套用                NOT STARTED

    Attendance Feature WPs
      WP-11-06  Reporting Backend API            COMPLETE  (2026-03-14)
      WP-11-07  Reporting UI Polish / QA         IN PROGRESS  <- 現在
      WP-11-13  Location Policy + Manual QA      BLOCKED（需真實瀏覽器環境）

    Phase 2 - Core Feature Completion            NOT STARTED
      WP-C2-01  Location Policy 擴展至所有打卡    NOT STARTED
      WP-11-08  Leave Request                    NOT STARTED
      WP-11-09  Shift / Schedule                 NOT STARTED

    Phase 3 - Frontend Expansion                 NOT STARTED
      WP-11-10  GPS / Field Work                 NOT STARTED

    Phase 4 - SaaS Platform Completion           NOT STARTED

### Gate 5 完成條件（估計完成度 45%）

- [x] WP-C1-01 PostgreSQL 環境建立（VERIFIED 2026-03-11）
- [x] WP-11-06 Reporting Backend API（COMPLETE 2026-03-14）
- [x] WP-C1-07 Attendance API JWT 遷移（COMPLETED 2026-03-12）
- [ ] Phase 1 基線修正完成（WP-C1-02 ~ WP-C1-06）
- [ ] WP-11-13 Manual QA 通過
- [ ] 8 個回歸測試在真實 DB 通過（目前 0/8）
- [ ] 5 個 Tenant Isolation 測試在真實 DB 通過
- [ ] 所有模組使用 JWT auth（目前 2/7）
- [ ] Feature Gate 套用至所有核心 API（目前 0%）

---

## 10. Final Development Guidance

### 10.1 強制規則

| 規則 | 說明 |
|------|------|
| 不得跳票開發 | 不得在未完成當前 WP 前切去下個模組 |
| 不得誤判 UI MVP 狀態 | Reporting UI MVP 已存在（CODE_COMPLETE），不代表模組未開始 |
| 不得因新功能重構核心 | 不得因 Leave/Shift/GPS 需求重構 Punch core / Policy Engine |
| 不得繞過層級 | 新功能必須走 Spec -> API -> Backend -> Frontend -> Test -> Docs |
| 不得無聲失敗 | 遇到阻塞立即記錄在 WORKSTREAM_STATUS_LEDGER.md |

### 10.2 每次開始新 WP 前必須執行

1. 讀取本文件（ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md）確認模組位置
2. 讀取 NEXT_WP_TICKET.md 確認當前 WP 與前置條件
3. 讀取 GATE_PROGRESS_TRACKER.md 確認整體進度
4. 確認新功能的 Backend / Frontend 掛載層符合第 2 節分層規則
5. 確認不會修改第 8 節列出的核心保護區檔案

### 10.3 完成每個 WP 後必須執行

1. 更新 NEXT_WP_TICKET.md（當前 WP 狀態、下一個 WP）
2. 更新 GATE_PROGRESS_TRACKER.md（WP 完成記錄）
3. 更新 WORKSTREAM_STATUS_LEDGER.md（執行細節記錄）
4. 更新 MODULE_STATUS_MATRIX.md（若模組狀態有變化）
5. 若有架構異動，同步更新本文件

### 10.4 本文件使用方式

| 需要確認的事項 | 閱讀章節 |
|---------------|----------|
| 模組位置 / 分層規則 | §2 Layered Architecture |
| 已實作模組與真實檔案 | §3 Current Implemented Modules |
| Reporting 資料流與注意事項 | §4 Reporting Module Map |
| GPS / Location 現況與未來位置 | §5 GPS / Location Module Map |
| 未來模組應掛在哪裡 | §6 Future Modules Placement |
| 哪些檔案不能動 | §8 Protected Core Areas |
| 目前系統在哪個階段 | §9 Current Roadmap Position |
| AI / 開發者行為規範 | §10 Final Development Guidance |

---

*本文件由 AI 依據 2026-03-14 實際 code scan 建立。*
*權威基礎：docs/SYSTEM_GROUND_TRUTH.md + docs/GATE_PROGRESS_TRACKER.md + repo 真實結構。*
*每次重大架構異動後必須同步更新本文件。*

**END OF ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md**


---


### Development Track Clarification

- **WP-11-xx**：Attendance 功能 roadmap（Reporting、Leave、Shift、GPS 等功能開發）  
- **WP-C1-xx**：平台 / 安全 / infrastructure 修復任務（Security baseline、migration、tenant isolation 等）  

兩條線可以並行，但 **Attendance 功能開發仍以 WP-11 roadmap 為主線**。
