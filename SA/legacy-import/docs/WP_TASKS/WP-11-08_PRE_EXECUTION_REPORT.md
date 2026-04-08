# WP-11-08 Pre-Execution Report
Attendance System - Leave Request Module

**建立日期:** 2026-03-15
**最後更新:** 2026-03-15（users.manager_id missing + strict policy mode 確認）
**WP:** WP-11-08 - Leave Request System
**狀態:** PRE-EXECUTION REPORT COMPLETE - 尚未開始實作
**Readiness:** NOT READY（users.manager_id 尚未存在，Phase 1 必須先建立）
**撰寫依據:** AI_READ_ORDER.md + repo 實際 code scan + users.manager_id existence check

---

## Work Package

| 欄位 | 值 |
|------|-----|
| WP | WP-11-08 |
| 名稱 | Leave Request System |
| 狀態 | PLANNED - 前置設計完成，尚未實作 |
| 前置條件 | WP-11-07 COMPLETE（2026-03-15）|
| Phase | Phase 2 - Core Feature Completion |
| 下一個 WP | WP-11-09 Shift / Schedule |
| Schema Readiness | NOT READY（users.manager_id 缺失）|

---

## Summary

本報告為 WP-11-08 Leave Request System 的前置執行報告。
在任何程式碼實作前，依照 AI_READ_ORDER.md 規定順序讀取所有必要文件，
確認系統現況、模組邊界、架構規範，並完成所有設計決策。

### WP 確認

- 當前 WP: WP-11-08 - Leave Request System
- 前置條件: WP-11-07 COMPLETE（2026-03-15）
- 設計方向: 已確定
- Schema 準備度: NOT READY（詳見下方）

### 整體設計方向（MVP）

**選定審核模型：Manager Chain Approval + Policy Table**

- 審核人由員工的 manager chain（users.manager_id）解析，非通用 admin 角色
- 審核層級由每公司的 leave_approval_policies 設定（依請假天數範圍決定）
- 若公司未設定 leave_approval_policies，員工提交請假申請將被拒絕（Strict Policy Mode）
- 無 fallback 至任何預設審核人或預設層級

**適用場景：台灣中小企業（SME）**
- 組織層級清晰（員工 → 直屬主管 → 更高層）
- 請假天數影響審核層級，由公司管理員自行設定 policy
- 未來擴充至更多層只需更新 policy，不修改核心邏輯

### 目前 Schema 問題（BLOCKING）

> **CRITICAL：users.manager_id 欄位目前不存在**

已確認 users 表（auth/models.py）目前欄位：
id, display_name, email, password_hash, is_active, is_otp,
must_change_password, last_login_at, created_at, updated_at

完全沒有以下任何欄位：
- manager_id
- supervisor_id
- report_to
- parent_user_id
- 任何等效 reporting-line 欄位

所有 migration（001b ~ 008）均未加入此欄位。
backup/validator.py 中有 comment-out 的預留備註，確認此欄位從未實作。

**影響：** Phase 1 必須先新增 users.manager_id，Leave Approval 才能運作。

### Strict Policy Mode（重要設計決策）

WP-11-08 採用嚴格 Policy 模式：

- 公司管理員必須先設定 leave_approval_policies
- 若提交請假時查無匹配 policy，**直接拒絕提交（422）**
- **不允許** fallback 至 Level 1
- **不允許** 任何預設審核行為

理由：強制管理員先完成設定，避免靜默錯誤審核流程。

---

## Documents Read

依照 docs/AI_READ_ORDER.md 規定順序，本次 session 已讀取以下文件：

| 順序 | 文件路徑 | 目的 |
|------|---------|------|
| 1 | docs/AI_READ_ORDER.md | 讀取順序入口 |
| 2 | docs/00_AI_GOVERNANCE/AI_CONTEXT.md | 文件優先級與 AI 工作流程規範 |
| 3 | docs/00_AI_GOVERNANCE/CURSOR_DEVELOPMENT_RULES.md | 開發規則、保護區定義 |
| 4 | docs/01_ARCHITECTURE/ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md | 系統架構地圖、§6 預定掛載點 |
| 5 | docs/03_WP_CONTROL/ATTENDANCE_DEVELOPMENT_ROADMAP.md | WP 順序、依賴關係 |
| 6 | docs/03_WP_CONTROL/NEXT_WP_TICKET.md | 當前 WP 確認 |
| 7 | docs/02_DEVELOPMENT_STATUS/CURRENT_SYSTEM_STATE.md | 系統現況 SSoT |
| 8 | backend/app/modules/attendance/models.py | ORM 模式參考 |
| 9 | backend/app/modules/attendance/schemas.py | Pydantic schema 模式 |
| 10 | backend/app/modules/attendance/repo.py | Repository tenant isolation 模式 |
| 11 | backend/app/core/dependencies.py | get_actor_with_company、JWT DI 模式 |
| 12 | backend/app/core/scope.py | Actor、is_admin()、is_employee() RBAC |
| 13 | backend/app/modules/attendance/api.py | Router 結構模式 |
| 14 | backend/alembic/versions/008_wp_11_13_create_allowed_locations.py | Migration 撰寫模式 |
| 15 | backend/app/modules/auth/models.py | users 表結構確認（manager_id 存在性檢查）|
| 16 | backend/alembic/versions/*.py（全部 8 個）| Migration chain 確認（無 manager_id）|
| 17 | backend/app/modules/backup/validator.py | manager_id comment-out 備註確認 |

### Schema Analysis Findings

| 檢查項目 | 結果 |
|---------|------|
| users.manager_id 存在？ | 否 |
| 等效 supervisor/report_to 欄位？ | 否 |
| Migration 中是否有相關欄位？ | 否（所有 8 個 migration 均無）|
| Membership 表中是否有 manager 關係？ | 否（僅有 role_id）|
| backup/validator.py 備註？ | 有 comment-out 的預留（Phase 6+），從未實作 |
| Manager chain readiness | NOT READY |

---

## Proposed Module Scope

### Leave 模組邊界（全新獨立模組，不觸碰現有保護區）

新增 Backend 檔案：

    backend/app/modules/leave/
      __init__.py
      api.py          FastAPI router (prefix: /api/v1/leave)
      schemas.py      Pydantic request/response DTOs
      models.py       SQLAlchemy ORM
                      (LeaveType, LeaveRequest, LeaveApprovalLog, LeaveApprovalPolicy)
      repo.py         LeaveRepository (強制 tenant isolation)
      service.py      業務邏輯 (Manager Chain 審核、strict policy、餘額計算)
      tests/
        __init__.py
        conftest.py
        test_leave_api.py
        test_leave_service.py
        test_leave_tenant_isolation.py
        test_leave_approval_policy.py

新增 Migration（Phase 1，含 users.manager_id）：

    backend/alembic/versions/009_wp_11_08_create_leave_tables.py
    步驟 1：ALTER TABLE users ADD COLUMN manager_id（self-ref FK）
    步驟 2：CREATE TABLE leave_types
    步驟 3：CREATE TABLE leave_requests
    步驟 4：CREATE TABLE leave_approval_logs
    步驟 5：CREATE TABLE leave_approval_policies

修改現有檔案（最小範圍）：

    backend/app/main.py         掛載 leave router
    backend/app/modules/auth/models.py   新增 manager_id 欄位至 User model

新增 Frontend 檔案（Phase 2，暫不實作）：

    frontend/src/views/leave/LeaveRequestPage.vue
    frontend/src/views/leave/LeaveApprovalPage.vue
    frontend/src/stores/leave.js
    frontend/src/api/leave.js

### 不可修改的保護區

| 檔案 | 保護原因 |
|------|----------|
| backend/app/modules/attendance/service.py | Punch/Break 業務邏輯核心 |
| backend/app/modules/attendance/models.py | ORM 模型，改動影響 migration chain |
| backend/app/modules/attendance/policy_engine.py | 政策計算核心 |
| frontend/src/stores/attendance.js | 前端打卡狀態機 |
| frontend/src/views/Home.vue | 主打卡頁 |
| frontend/src/api/client.js | Axios base instance |
| backend/app/core/dependencies.py | JWT DI（只使用，不修改）|
| backend/app/core/scope.py | RBAC（只使用，不修改）|
| backend/app/core/tenant_context.py | Tenant isolation 依賴層 |

---

## Design Decisions

### 決策 1：Leave Request Status Flow

**選擇：4 狀態模型（不含 draft）**

    pending → approved    （授權主管核准）
    pending → rejected    （授權主管拒絕）
    pending → cancelled   （員工自取消，僅限 pending）

| 狀態 | 說明 | 誰可操作 |
|------|------|----------|
| pending | 申請已送出，待審核 | 系統自動（建立時設定）|
| approved | 授權主管已核准 | 依 Manager Chain + Policy 決定的 approver_id |
| rejected | 授權主管已拒絕 | 依 Manager Chain + Policy 決定的 approver_id |
| cancelled | 員工自行取消 | 申請人本人，且 status = pending |

不採用 draft：MVP 員工填寫完直接送出為 pending。

---

### 決策 2：Leave Time Model

**選擇：Option A - start_date / end_date（全天制）**

    start_date: date   請假開始日期（Asia/Taipei 本地日期）
    end_date:   date   請假結束日期（含當天）

理由：
- MVP 主流請假類型（年假、病假、事假）均為全天制
- 避免與 Attendance UTC 儲存規則的複雜度衝突
- 與現有系統的 work_date（date 型別）模式一致

半日假預留：is_half_day: bool 欄位（預設 false），MVP 不強制使用。

---

### 決策 3：Leave Balance Model

**選擇：動態計算（不建立獨立 leave_balances table）**

    可用天數 = annual_days - SUM(approved requests 天數，本年度，同 leave_type, 同 user)

扣除時機：狀態改為 approved 時才視為消耗。pending / rejected / cancelled 均不計入。

---

### 決策 4：Approval Model

**選擇：Manager Chain Approval + Policy Table（Strict Mode）**

#### 4.1 設計概覽

審核層級由 leave_approval_policies 設定，依請假天數範圍決定。
審核人由 users.manager_id chain 解析。
Policy 未設定 → 提交直接被拒絕（Strict Policy Mode）。

#### 4.2 Manager Chain 解析邏輯

    Level 1 Approver：employee.manager_id
              （員工的直屬主管）

    Level 2 Approver：employee.manager_id.manager_id
              （直屬主管的主管）

    Level 3（未來擴充）：company owner

Manager chain 前提條件：
- users.manager_id 欄位必須存在（Phase 1 新增）
- 員工必須有有效的 manager_id，否則提交時回傳 422
- manager_id 必須屬於同一 company_id（tenant isolation）
- Level 2 若 manager.manager_id IS NULL，提交時回傳 422（Strict Mode，不 fallback）

#### 4.3 Policy Table 設定範例

| min_days | max_days | approval_level | 說明 |
|----------|----------|----------------|------|
| 1 | 2 | 1 | 1-2 天：直屬主管審核 |
| 3 | 4 | 2 | 3-4 天：主管的主管審核 |
| 5 | NULL | 2 | 5 天以上：主管的主管審核 |

#### 4.4 Strict Policy Mode（嚴格模式）

> IMPORTANT: 無 fallback，無預設審核人

提交請假時的 policy 查詢：

    SELECT approval_level FROM leave_approval_policies
    WHERE company_id = :company_id
      AND is_active = true
      AND min_days <= :total_days
      AND (max_days IS NULL OR max_days >= :total_days)
    LIMIT 1

結果處理：
- 查到 policy → 繼續解析 approver_id
- 查無 policy → 立即回傳 422（公司尚未設定請假審核政策）
- 不允許 fallback 至 Level 1
- 不允許任何預設審核行為

#### 4.5 完整審核流程

    員工提交請假（total_days 計算完成）
       ↓
    [CHECK 1] employee.manager_id IS NULL?
       → 是：422（員工無直屬主管）
       ↓
    [CHECK 2] 查詢 leave_approval_policies
       → 查無：422（公司未設定審核政策）
       ↓
    [CHECK 3] 解析 approver_id（依 approval_level）
       Level 1 → employee.manager_id
       Level 2 → employee.manager_id.manager_id
         → manager.manager_id IS NULL：422（審核鏈不完整）
       ↓
    建立 leave_requests（status=pending, approver_id=resolved）
       ↓
    授權 approver 呼叫 /approve 或 /reject
       → 驗證：actor.user_id == leave_request.approver_id
       ↓
    寫入 leave_approval_logs，更新 status

#### 4.6 與「通用 Admin 審核」的差異

| 方向 | Manager Chain + Policy（本設計）| 通用 Admin 審核（已排除）|
|------|--------------------------------|--------------------------|
| 審核人 | 由 manager_id chain 解析 | 任何 is_admin() 用戶 |
| 審核層級 | Policy Table 設定 | 固定 1 層 |
| 無 policy | 422 拒絕 | 允許（無設定需求）|
| 適用場景 | SME 組織架構 | 無組織層級的小型系統 |

---

### 決策 5：Attendance Integration Rules

MVP 整合原則（安全優先）：

| 問題 | MVP 決策 |
|------|----------|
| 已核准請假是否出現在報表？ | 暫不整合（Phase 2 後期評估）|
| 請假是否與出勤 session 重疊？ | 允許重疊，不做衝突檢查 |
| 請假是否阻擋打卡？ | 否，打卡系統完全獨立運作 |
| 報表中缺勤是否自動填入請假？ | 否（MVP 不做自動關聯）|

核心安全規則：
- Leave 模組不可直接修改 attendance_sessions table
- Leave 模組不可修改任何 Punch core 邏輯

---

## Data Model Proposal

> 注意：所有 Leave 表格的 manager chain 功能依賴 users.manager_id。
> 此欄位目前不存在，Phase 1 migration 必須先新增。

### 前置依賴：users.manager_id（Phase 1 新增）

| 欄位 | 型別 | 說明 |
|------|------|------|
| manager_id | UUID NULLABLE | 直屬主管 user_id（self-referencing FK → users.id）|

Migration 動作：

    ALTER TABLE users
    ADD COLUMN manager_id UUID REFERENCES users(id) ON DELETE SET NULL;

ORM 新增欄位（auth/models.py User class）：

    manager_id = Column(
        UUID(as_uuid=True),
        ForeignKey(users.id, ondelete=SET NULL),
        nullable=True,
        comment=直屬主管 user_id（Manager Chain，自參照）
    )

Index：idx_users_manager_id(manager_id) WHERE manager_id IS NOT NULL

### Table 1：leave_types（假別設定）

| 欄位 | 型別 | 說明 |
|------|------|------|
| id | UUID PK | gen_random_uuid() |
| company_id | VARCHAR(255) NOT NULL | Tenant Isolation |
| name | VARCHAR(100) NOT NULL | 假別名稱（年假、病假、事假）|
| code | VARCHAR(50) NOT NULL | 代碼（annual, sick, personal）|
| description | TEXT | 說明 |
| annual_days | INTEGER | 年度配額（NULL = 無限制）|
| is_active | BOOLEAN NOT NULL DEFAULT true | 是否啟用 |
| created_at | TIMESTAMPTZ NOT NULL | 建立時間（UTC）|
| updated_at | TIMESTAMPTZ NOT NULL | 更新時間（UTC）|

Constraints：UNIQUE(company_id, code)；FK company_id → tenants(id) ON DELETE CASCADE

### Table 2：leave_requests（請假申請）

| 欄位 | 型別 | 說明 |
|------|------|------|
| id | UUID PK | gen_random_uuid() |
| company_id | VARCHAR(255) NOT NULL | Tenant Isolation |
| user_id | UUID NOT NULL | 申請人（FK → users.id）|
| leave_type_id | UUID NOT NULL | 假別（FK → leave_types.id）|
| start_date | DATE NOT NULL | 請假開始日（Asia/Taipei 本地日期）|
| end_date | DATE NOT NULL | 請假結束日（含當天）|
| total_days | NUMERIC(4,1) NOT NULL | 總天數 |
| is_half_day | BOOLEAN NOT NULL DEFAULT false | 半日假旗標（MVP 預留）|
| reason | TEXT | 請假原因 |
| status | VARCHAR(20) NOT NULL DEFAULT pending | 申請狀態 |
| required_approval_level | INTEGER NOT NULL | 所需審核層級（由 policy 決定，1 or 2）|
| approver_id | UUID | 系統解析的授權審核人（manager chain 解析結果）|
| created_at | TIMESTAMPTZ NOT NULL | 建立時間（UTC）|
| updated_at | TIMESTAMPTZ NOT NULL | 更新時間（UTC）|

Constraints：
- CHECK status IN (pending, approved, rejected, cancelled)
- CHECK end_date >= start_date, CHECK total_days > 0
- CHECK required_approval_level IN (1, 2)
- FK company_id → tenants(id), user_id → users(id), leave_type_id → leave_types(id)
- FK approver_id → users(id) ON DELETE SET NULL

Indexes：
- idx_leave_requests_company, idx_leave_requests_company_user
- idx_leave_requests_company_status, idx_leave_requests_approver
- idx_leave_requests_user_dates(user_id, start_date, end_date)

### Table 3：leave_approval_logs（審核記錄）

| 欄位 | 型別 | 說明 |
|------|------|------|
| id | UUID PK | gen_random_uuid() |
| leave_request_id | UUID NOT NULL | 對應的請假申請（FK → leave_requests.id）|
| company_id | VARCHAR(255) NOT NULL | Tenant Isolation（denormalized）|
| actor_id | UUID NOT NULL | 實際執行審核的 user_id |
| action | VARCHAR(20) NOT NULL | approved / rejected / cancelled |
| approval_level | INTEGER NOT NULL | 此次審核的層級（1 or 2）|
| comment | TEXT | 審核意見 |
| created_at | TIMESTAMPTZ NOT NULL | 建立時間（UTC）|

Constraints：
- CHECK action IN (approved, rejected, cancelled)
- CHECK approval_level IN (1, 2)
- FK leave_request_id → leave_requests(id) ON DELETE CASCADE
- FK company_id → tenants(id), actor_id → users(id)

### Table 4：leave_approval_policies（審核層級政策）

> 此表為 Manager Chain Approval 的核心設定表。
> 每公司獨立設定。未設定時員工無法提交請假（Strict Policy Mode）。

| 欄位 | 型別 | 說明 |
|------|------|------|
| id | UUID PK | gen_random_uuid() |
| company_id | VARCHAR(255) NOT NULL | Tenant Isolation |
| min_days | NUMERIC(4,1) NOT NULL | 天數範圍下限（含）|
| max_days | NUMERIC(4,1) | 天數範圍上限（含，NULL = 無上限）|
| approval_level | INTEGER NOT NULL | 所需審核層級（1 or 2）|
| is_active | BOOLEAN NOT NULL DEFAULT true | 是否啟用 |
| created_at | TIMESTAMPTZ NOT NULL | 建立時間（UTC）|
| updated_at | TIMESTAMPTZ NOT NULL | 更新時間（UTC）|

Constraints：
- CHECK min_days > 0
- CHECK max_days IS NULL OR max_days >= min_days
- CHECK approval_level IN (1, 2)
- FK company_id → tenants(id) ON DELETE CASCADE

Indexes：
- idx_leave_approval_policies_company(company_id)
- idx_leave_approval_policies_company_active(company_id, is_active)

### Entity 關係摘要

    users（現有）
      + manager_id（Phase 1 新增）→ self-ref FK → users.id
      |
      ├── leave_requests.user_id（申請人）
      ├── leave_requests.approver_id（授權審核人，由 manager chain 解析）
      └── leave_approval_logs.actor_id（實際審核人）

    leave_types（每公司設定）
      └── leave_requests.leave_type_id

    leave_approval_policies（每公司設定，Strict Mode 必須存在）
      → 決定 required_approval_level
      → 決定 approver_id 解析層級

---

## API Design Proposal

### Router Prefix: /api/v1/leave

| Method | Endpoint | 說明 | 權限 |
|--------|----------|------|------|
| POST | /api/v1/leave/types | 建立假別 | is_admin() |
| GET | /api/v1/leave/types | 列出假別 | 所有登入用戶 |
| POST | /api/v1/leave/policies | 設定審核層級 policy | is_admin() |
| GET | /api/v1/leave/policies | 查詢審核 policy | is_admin() |
| POST | /api/v1/leave | 員工提交請假申請 | 所有登入用戶 |
| GET | /api/v1/leave/my | 員工查詢自己的申請 | 所有登入用戶 |
| GET | /api/v1/leave | 查詢待審核申請（主管視角）| 授權審核人 |
| GET | /api/v1/leave/{id} | 查詢單筆申請 | 申請人本人 or 授權審核人 |
| POST | /api/v1/leave/{id}/approve | 核准請假 | approver_id 比對 |
| POST | /api/v1/leave/{id}/reject | 拒絕請假 | approver_id 比對 |
| POST | /api/v1/leave/{id}/cancel | 員工取消（pending 中）| 申請人本人 |
| GET | /api/v1/leave/balance | 查詢個人假別餘額 | 所有登入用戶 |

### 認證模式

所有 endpoint 使用：actor: Actor = Depends(get_actor_with_company)
company_id 從 actor.active_company_id 取得，不從 request body 傳入。

### 審核授權驗證邏輯（Service 層）

    if leave_request.approver_id != actor.user_id:
        raise HTTPException(403)  # Not the authorized approver

### 提交請假 Response 201 摘要

    id: UUID
    status: pending
    leave_type: {id, name, code}
    start_date, end_date, total_days
    required_approval_level: int  (1 or 2)
    approver_id: UUID  (manager chain 解析結果)
    created_at: datetime (UTC)

### 提交失敗情境（422 Unprocessable Entity）

| 情境 | 錯誤訊息 |
|------|----------|
| 員工無 manager_id | Employee has no direct manager assigned |
| 公司無 leave_approval_policies | No leave approval policy configured for this company |
| Level 2 但 manager.manager_id IS NULL | Approval chain incomplete: manager has no manager assigned |
| leave_type 不存在或未啟用 | Leave type not found or inactive |

---

## Attendance Integration Rules

Leave 模組與 attendance_sessions 的關係：
- Leave 模組不寫入、不修改 attendance_sessions
- 現有三支 Reporting API 不修改
- 未來整合透過 JOIN 查詢，不修改核心資料
- 已核准請假期間員工仍可正常打卡（不阻擋）
- LeaveRepository 所有查詢強制 WHERE company_id = actor.active_company_id
- Manager chain 解析時，必須驗證 manager.company_id == employee.company_id

---

## File Change Plan

### Phase 1 - Backend Only（本次實作範圍）

| 檔案 | 類型 | 說明 |
|------|------|------|
| backend/alembic/versions/009_wp_11_08_create_leave_tables.py | 新增 | Migration：新增 users.manager_id + 四張 leave 表 |
| backend/app/modules/auth/models.py | 修改 | User model 新增 manager_id 欄位 |
| backend/app/modules/leave/__init__.py | 新增 | 模組初始化 |
| backend/app/modules/leave/models.py | 新增 | ORM（LeaveType, LeaveRequest, LeaveApprovalLog, LeaveApprovalPolicy）|
| backend/app/modules/leave/schemas.py | 新增 | Pydantic DTOs |
| backend/app/modules/leave/repo.py | 新增 | LeaveRepository（tenant isolation）|
| backend/app/modules/leave/service.py | 新增 | 業務邏輯（Manager Chain、Strict Policy、餘額）|
| backend/app/modules/leave/api.py | 新增 | FastAPI Router（/api/v1/leave）|
| backend/app/modules/leave/tests/__init__.py | 新增 | 測試套件初始化 |
| backend/app/modules/leave/tests/conftest.py | 新增 | 測試 fixtures |
| backend/app/modules/leave/tests/test_leave_api.py | 新增 | API 層測試 |
| backend/app/modules/leave/tests/test_leave_service.py | 新增 | Service 層測試 |
| backend/app/modules/leave/tests/test_leave_tenant_isolation.py | 新增 | Tenant isolation 測試 |
| backend/app/modules/leave/tests/test_leave_approval_policy.py | 新增 | Policy + Manager Chain 測試 |
| backend/app/main.py | 修改 | 掛載 leave router |

### Phase 2 - Frontend（待 Phase 1 完成後）

| 檔案 | 說明 |
|------|------|
| frontend/src/api/leave.js | Leave API 方法 |
| frontend/src/stores/leave.js | 請假狀態 Pinia store |
| frontend/src/views/leave/LeaveRequestPage.vue | 員工申請頁（含顯示 approver 資訊）|
| frontend/src/views/leave/LeaveApprovalPage.vue | 主管審核頁（僅顯示 approver_id = 自己）|
| frontend/src/router/index.js | 新增路由 /leave, /leave/approval |

---

## Risks / Assumptions

### 風險

| 風險 | 等級 | 說明 | 緩解措施 |
|------|------|------|----------|
| users.manager_id 缺失 | 高 | 目前 users 表無此欄位，Manager Chain 完全無法運作 | Phase 1 migration 優先新增 |
| Policy 未設定（Strict Mode）| 高 | 公司若未設定 leave_approval_policies，所有員工無法提交請假 | 系統上線前管理員必須先設定 policy |
| Manager chain 斷鏈 | 中 | 員工無 manager_id 或 Level 2 無 manager.manager_id | 提交時驗證，422 明確告知 |
| Migration chain 衝突 | 中 | 新 migration 必須接在 008_wp_11_13 之後 | 嚴格設定 down_revision = 008_wp_11_13 |
| auth/models.py 修改 | 中 | User model 新增欄位需同步 migration | migration 與 model 同步進行，不可分離 |
| 假別餘額計算效能 | 低 | 動態計算在大量資料時可能較慢 | MVP 規模足夠；未來可加 cache |
| 請假與出勤重疊 | 低 | 同日有出勤記錄又有請假 | MVP 不整合，兩者獨立存在 |

### 假設

1. users.manager_id 缺失：目前 NOT READY，Phase 1 必須先新增
2. Manager chain 必須完整：員工必須有 manager_id；Level 2 時 manager 也必須有 manager_id
3. Policy 必須預先設定：公司管理員必須在員工開始使用前設定 leave_approval_policies
4. 無 policy fallback：若 leave_approval_policies 查無結果，提交直接 422，無任何預設行為
5. 無通用 admin 審核：審核人完全由 manager chain 決定，is_admin() 角色不參與審核
6. Tenant isolation：manager_id 必須屬於同一 company_id，不得跨公司
7. 年度計算：以 start_date 的年份判斷是否屬於本年度配額
8. Migration HEAD：下一個 migration 接在 008_wp_11_13 之後

### 已排除的設計方向

| 排除項目 | 排除原因 |
|---------|----------|
| 通用 admin 審核（任何 is_admin() 可審核）| 不符合 SME 組織架構需求 |
| Policy fallback 至 Level 1 | Strict Mode 下不允許靜默行為 |
| 獨立 org-chart / department 表 | 過度設計，MVP 不需要 |
| draft 狀態 | 增加複雜度，MVP 無需求 |
| 多層審核（3 層以上）| Phase 3 再評估 |

---

## Recommended Implementation Phases

### Phase 1: Backend Foundation

目標：建立 manager chain 基礎 + leave 資料表 + API + Strict Policy 邏輯 + 測試

**Step 1: Migration (009_wp_11_08_create_leave_tables.py)**

    down_revision = 008_wp_11_13

    1a. ALTER TABLE users ADD COLUMN manager_id
        UUID NULLABLE, FK to users.id, ON DELETE SET NULL
        Index: idx_users_manager_id WHERE manager_id IS NOT NULL

    1b. CREATE TABLE leave_types
    1c. CREATE TABLE leave_requests (含 required_approval_level, approver_id)
    1d. CREATE TABLE leave_approval_logs (含 approval_level)
    1e. CREATE TABLE leave_approval_policies

**Step 2: Models**

    - auth/models.py User class: 新增 manager_id 欄位
    - leave/models.py: LeaveType, LeaveRequest, LeaveApprovalLog, LeaveApprovalPolicy
    - 遵循 attendance/models.py 模式 (UUID PK, company_id, Index, FK)

**Step 3: Schemas**

    - LeaveTypeCreate / LeaveTypeResponse
    - LeaveRequestCreate / LeaveRequestResponse (含 required_approval_level, approver_id)
    - LeaveApprovalRequest / LeaveApprovalResponse (含 approval_level)
    - LeaveApprovalPolicyCreate / LeaveApprovalPolicyResponse
    - LeaveBalanceResponse

**Step 4: Repository (repo.py)**

    LeaveRepository (所有方法強制 WHERE company_id = ?):
    - get_approval_policy_for_days(company_id, total_days) → approval_level or None
    - get_user_with_manager(user_id, company_id) → User or None
    - create_leave_type / get_leave_types
    - create_leave_request / get_leave_request_by_id
    - get_leave_requests_by_company / get_leave_requests_by_user
    - get_leave_requests_pending_for_approver
    - update_leave_request_status
    - get_used_days_for_year
    - create_approval_log

**Step 5: Service (service.py)**

    - resolve_approver_id(employee, approval_level, company_id):
        Level 1: employee.manager_id
        Level 2: employee.manager_id.manager_id
        Either NULL: raise 422 (Strict Mode, no fallback)

    - lookup_approval_level(company_id, total_days):
        Query leave_approval_policies
        No match: raise 422 (Strict Policy Mode)

    - submit_leave_request():
        1. Validate employee.manager_id exists
        2. lookup_approval_level() - 422 if no policy
        3. resolve_approver_id() - 422 if chain incomplete
        4. Create leave_request with approver_id

    - approve_leave_request(): validate approver_id, transition status, write log
    - reject_leave_request(): validate approver_id, transition status, write log
    - cancel_leave_request(): pending only, requester only
    - calculate_leave_balance(): dynamic calculation

**Step 6: API (api.py)**

    - router_leave = APIRouter(prefix=/api/v1/leave)
    - 12 endpoints (含 policy CRUD)
    - Depends(get_actor_with_company)

**Step 7: main.py**

    - app.include_router(leave_router)

**Step 8: Tests**

    conftest.py:
        - user_with_manager fixture
        - manager_user fixture
        - leave_type fixture
        - leave_approval_policy fixture
        - user_without_manager fixture (for error tests)

    test_leave_approval_policy.py:
        - test policy lookup returns correct level
        - test no policy returns 422 (Strict Mode)
        - test policy boundary conditions

    test_leave_service.py:
        - test resolve_approver_id Level 1
        - test resolve_approver_id Level 2
        - test 422 when employee has no manager
        - test 422 when Level 2 but manager has no manager
        - test 422 when no matching policy

    test_leave_api.py:
        - test submit success
        - test approve by correct approver
        - test reject by correct approver
        - test 403 when wrong user tries to approve
        - test cancel by requester

    test_leave_tenant_isolation.py:
        - test cross-company query blocked
        - test manager from different company rejected

### Phase 2: Frontend (Phase 1 完成後)

    1. api/leave.js: API 方法
    2. stores/leave.js: Pinia store
    3. views/leave/LeaveRequestPage.vue: 申請頁 (顯示 approver 資訊)
    4. views/leave/LeaveApprovalPage.vue: 主管審核頁 (approver_id = 自己)
    5. router/index.js: 新增路由

### Phase 3: Integration (後續 WP 評估)

    - 請假資料整合至出勤報表
    - 請假衝突檢查 (與出勤 session 比對)
    - Level 3 審核層級擴充 (company owner)

---

## Readiness Confirmation

| 確認項目 | 狀態 | 備註 |
|---------|------|------|
| WP-11-07 COMPLETE | 是（2026-03-15）| 前置條件已滿足 |
| 文件讀取完成（AI_READ_ORDER.md 順序）| 是（17 份文件）| 含 users.manager_id 存在性檢查 |
| 現有保護區確認 | 是 | 9 個保護檔案列出 |
| Architecture Map 掛載位置確認 | 是 | modules/leave/ 預定位置 |
| Migration HEAD 確認 | 是 | 008_wp_11_13，下一個為 009_wp_11_08 |
| Tenant isolation 模式確認 | 是 | WHERE company_id 強制執行 |
| JWT Auth 模式確認 | 是 | get_actor_with_company |
| Approval Model 確認 | 是 | Manager Chain + Policy Table |
| Strict Policy Mode 確認 | 是 | 無 policy → 422，無 fallback |
| users.manager_id 存在性確認 | 否 | NOT READY - 欄位不存在，Phase 1 必須先新增 |
| leave_approval_policies 設計完成 | 是 | Table 4 已完整定義 |
| 5 大設計決策已定 | 是 | Status / Time / Balance / Manager Chain / Integration |
| Schema 整體準備度 | NOT READY | users.manager_id 缺失是唯一 blocking 項目 |

### Schema Readiness Assessment

    Leave 模組設計方向：正確且完整
    選定的 Manager Chain + Policy 模型：適合台灣 SME 場景
    目前系統 Schema：NOT READY

    Blocking item：
    users.manager_id 欄位不存在於 users 表
    所有 migration（001b ~ 008）均未包含此欄位
    backup/validator.py 中有 comment-out 預留備註，從未實作

    解決方案：
    在 Phase 1 的 009_wp_11_08 migration 中，優先執行：
    ALTER TABLE users ADD COLUMN manager_id UUID
    REFERENCES users(id) ON DELETE SET NULL;

    此為最小範圍變更，不引入獨立 org-chart 表，不重新設計 HR 架構。

---

**END OF WP-11-08_PRE_EXECUTION_REPORT.md**

*建立者：AI（Cursor session，2026-03-15）*
*最後更新：2026-03-15（users.manager_id missing 確認 + Strict Policy Mode）*
*基於：AI_READ_ORDER.md 規定的 17 份文件 + repo code scan + schema existence check*

**Conclusion: NOT READY**
users.manager_id 欄位不存在。Phase 1 必須先新增此欄位，Leave Approval 才能運作。
