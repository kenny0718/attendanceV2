# WP-11-08 — Leave Request System 實作計畫

**建立日期：** 2026-03-15  
**WP 狀態：** PLANNED → READY FOR IMPLEMENTATION  
**前置條件：** WP-11-07 COMPLETE ✅（2026-03-15）  
**基於：** ATTENDANCE_DEVELOPMENT_ROADMAP.md §4、ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md §6

---

## 1. 系統現況確認

| 項目 | 狀態 |
|------|------|
| WP-11-07 前置條件 | ✅ COMPLETE（2026-03-15）|
| Migration HEAD | `008_wp_11_13`（17 tables）|
| Auth 機制 | JWT via `get_current_actor()`（`backend/app/core/dependencies.py`）|
| Tenant Isolation | 所有查詢強制含 `company_id` |
| Punch Core | 不可修改（最高保護等級）|

---

## 2. 模組架構位置

依 `ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md §6` 規劃：

### Backend

```
backend/app/modules/leave/
├── __init__.py
├── api.py          ← FastAPI router，僅做參數解析與呼叫 service
├── models.py       ← LeaveRequest ORM model
├── schemas.py      ← Pydantic request/response schemas
├── repo.py         ← LeaveRepository（SELECT 含 company_id）
└── service.py      ← 請假業務邏輯（衝突檢查、狀態機）
```

### Frontend

```
frontend/src/
├── views/leave/
│   ├── LeaveRequestPage.vue     ← 員工申請頁
│   └── LeaveApprovalPage.vue    ← 主管審核頁
├── stores/leave.js              ← Pinia store
└── api/leave.js                 ← API client methods
```

### Migration

```
backend/alembic/versions/
└── 009_wp_11_08_create_leave_requests.py
```

---

## 3. API Contract

### Endpoints（prefix: `/api/v1/leave`）

| Method | Path | 角色 | 說明 |
|--------|------|------|------|
| `POST` | `/api/v1/leave/requests` | employee | 提交請假申請 |
| `GET` | `/api/v1/leave/requests` | employee / admin | 查詢請假記錄 |
| `GET` | `/api/v1/leave/requests/{id}` | employee / admin | 查詢單筆詳情 |
| `POST` | `/api/v1/leave/requests/{id}/approve` | admin | 核准請假 |
| `POST` | `/api/v1/leave/requests/{id}/reject` | admin | 拒絕請假 |
| `DELETE` | `/api/v1/leave/requests/{id}` | employee | 撤回申請（僅 pending）|

### Request Schemas

#### POST /api/v1/leave/requests

```json
{
  "leave_type": "annual",
  "start_date": "2026-03-20",
  "end_date": "2026-03-21",
  "reason": "家庭事務"
}
```

`leave_type` 允許值：`annual` / `sick` / `personal` / `unpaid`

#### POST /api/v1/leave/requests/{id}/approve

```json
{
  "note": "已核准"
}
```

#### POST /api/v1/leave/requests/{id}/reject

```json
{
  "note": "人力不足，請調整日期"
}
```

### Response Schema（單筆）

```json
{
  "id": "uuid",
  "company_id": "string",
  "user_id": "uuid",
  "leave_type": "annual",
  "start_date": "2026-03-20",
  "end_date": "2026-03-21",
  "status": "pending",
  "reason": "家庭事務",
  "reviewed_by": null,
  "reviewed_at": null,
  "review_note": null,
  "created_at": "2026-03-15T10:00:00+08:00",
  "updated_at": "2026-03-15T10:00:00+08:00"
}
```

### Response Schema（列表）

```json
{
  "items": [...],
  "total": 10,
  "limit": 20,
  "offset": 0
}
```

---

## 4. 資料模型

### Migration：`009_wp_11_08_create_leave_requests.py`

```
table: leave_requests

Column        Type                  Nullable  說明
──────────────────────────────────────────────────────────────
id            UUID PK               NOT NULL  gen_random_uuid()
company_id    VARCHAR(255)          NOT NULL  Tenant Isolation 鍵
user_id       UUID                  NOT NULL  申請人 user_id
leave_type    VARCHAR(50)           NOT NULL  annual/sick/personal/unpaid
start_date    DATE                  NOT NULL  請假起始日
end_date      DATE                  NOT NULL  請假結束日
status        VARCHAR(50)           NOT NULL  pending/approved/rejected/withdrawn
reason        TEXT                  nullable  申請原因
reviewed_by   UUID                  nullable  審核人 user_id
reviewed_at   TIMESTAMPTZ           nullable  審核時間
review_note   TEXT                  nullable  審核備注
created_at    TIMESTAMPTZ           NOT NULL  建立時間
updated_at    TIMESTAMPTZ           NOT NULL  更新時間

Indexes:
  idx_leave_requests_company_id          (company_id)
  idx_leave_requests_company_user        (company_id, user_id)
  idx_leave_requests_company_status      (company_id, status)
  idx_leave_requests_date_range          (company_id, start_date, end_date)
```

### 狀態機

```
         ┌─────────┐
         │ pending │
         └────┬────┘
    ┌─────────┼──────────┐
    ▼         ▼          ▼
┌──────────┐ ┌──────────┐ ┌───────────┐
│ approved │ │ rejected │ │ withdrawn │
└──────────┘ └──────────┘ └───────────┘

規則：
- pending → approved   （admin 核准）
- pending → rejected   （admin 拒絕）
- pending → withdrawn  （employee 撤回）
- approved / rejected / withdrawn → 不可再變更
```

---

## 5. 核心規則與限制

### 5.1 絕對限制

| 規則 | 說明 |
|------|------|
| 不修改 Punch Core | `leave_requests` 是獨立 table，不寫入 `attendance_sessions` |
| 強制 Tenant Isolation | 所有查詢必須含 `WHERE company_id = ?` |
| 使用現有 JWT Auth | 使用 `get_current_actor()`，不新增 auth 機制 |
| 不可繞過分層架構 | Page → Store → API Client → Backend |

### 5.2 角色權限

| 操作 | employee | admin |
|------|----------|-------|
| 提交申請 | ✅ 自己 | — |
| 查詢申請 | ✅ 自己 | ✅ 全公司 |
| 撤回申請 | ✅ 自己（pending 狀態）| — |
| 核准申請 | ❌ | ✅ |
| 拒絕申請 | ❌ | ✅ |

### 5.3 資料驗證規則

- `start_date <= end_date`（否則 422）
- `leave_type` 必須為允許值之一
- 撤回操作：狀態非 `pending` 時返回 409
- 核准/拒絕：狀態非 `pending` 時返回 409

### 5.4 本 WP 不包含

- Leave balance / 餘額計算
- 班表整合（WP-11-09 範疇）
- 自動扣除出勤時數
- Email / push 通知觸發
- CSV 匯出

---

## 6. 實作步驟順序

依 `ATTENDANCE_DEVELOPMENT_ROADMAP.md §6.5` 規則：`Spec → API Contract → Backend → Frontend → Test → Docs`

### Phase A：Backend

| 步驟 | 工作項目 | 輸出檔案 |
|------|---------|----------|
| A1 | 建立 migration | `alembic/versions/009_wp_11_08_create_leave_requests.py` |
| A2 | 實作 ORM model | `modules/leave/models.py` |
| A3 | 實作 Pydantic schemas | `modules/leave/schemas.py` |
| A4 | 實作 LeaveRepository | `modules/leave/repo.py` |
| A5 | 實作 LeaveService | `modules/leave/service.py` |
| A6 | 實作 FastAPI router | `modules/leave/api.py` |
| A7 | 掛載 router 至主 app | `backend/app/main.py` |

### Phase B：Frontend

| 步驟 | 工作項目 | 輸出檔案 |
|------|---------|----------|
| B1 | 實作 API client | `frontend/src/api/leave.js` |
| B2 | 實作 Pinia store | `frontend/src/stores/leave.js` |
| B3 | 實作員工申請頁 | `frontend/src/views/leave/LeaveRequestPage.vue` |
| B4 | 實作主管審核頁 | `frontend/src/views/leave/LeaveApprovalPage.vue` |
| B5 | 更新 router | `frontend/src/router/index.js`（新增 `/leave`、`/leave/approvals`）|

### Phase C：Test & Docs

| 步驟 | 工作項目 | 輸出檔案 |
|------|---------|----------|
| C1 | 撰寫 backend API tests | `modules/leave/tests/test_leave_api.py` |
| C2 | 撰寫 tenant isolation tests | `modules/leave/tests/test_leave_tenant_isolation.py` |
| C3 | 更新治理文件 | `NEXT_WP_TICKET.md`、`GATE_PROGRESS_TRACKER.md` |

---

## 7. 驗收條件（Completion Definition）

- [ ] `POST /api/v1/leave/requests` — 員工可提交請假申請，返回 201
- [ ] `GET /api/v1/leave/requests` — 員工查詢自己的申請；admin 查詢全公司
- [ ] `GET /api/v1/leave/requests/{id}` — 查詢單筆詳情
- [ ] `POST /api/v1/leave/requests/{id}/approve` — admin 可核准，狀態變更為 approved
- [ ] `POST /api/v1/leave/requests/{id}/reject` — admin 可拒絕，狀態變更為 rejected
- [ ] `DELETE /api/v1/leave/requests/{id}` — 員工可撤回 pending 申請
- [ ] Tenant isolation 驗證通過（不同 company 資料完全隔離）
- [ ] JWT auth 正確（未登入 → 401，employee 存取 admin 操作 → 403）
- [ ] Migration `009` 可正常 `alembic upgrade head` / `downgrade`
- [ ] OpenAPI `/docs` 顯示所有 `/api/v1/leave` endpoints
- [ ] 前端 LeaveRequestPage 可提交申請並顯示申請記錄
- [ ] 前端 LeaveApprovalPage 可顯示待審核申請並執行審核

---

## 8. 關鍵參考文件

| 需要確認 | 閱讀文件 |
|---------|----------|
| 分層架構規則 | `docs/01_ARCHITECTURE/ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md §2` |
| 核心保護區 | `docs/01_ARCHITECTURE/ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md §8` |
| WP 執行順序 | `docs/03_WP_CONTROL/ATTENDANCE_DEVELOPMENT_ROADMAP.md §3` |
| JWT auth 用法 | `backend/app/core/dependencies.py` |
| Tenant isolation 範例 | `backend/app/modules/attendance/repo.py` ReportingRepository |
| Migration 範例 | `backend/alembic/versions/008_wp_11_13_create_allowed_locations.py` |
| Frontend store 範例 | `frontend/src/stores/reporting.js` |
| Frontend API client 範例 | `frontend/src/api/attendance.js` |

---

## 9. 後續 WP

```
WP-11-08（Leave Request System）← 當前 WP
  ↓
WP-11-09（Shift / Schedule Management）
  ↓
WP-11-10（GPS / Field Work 完整實作）← Phase 3
```

---

*本文件由 AI 依據 WP-11-08 設計階段規劃建立，2026-03-15。*  
*權威依據：ATTENDANCE_DEVELOPMENT_ROADMAP.md + ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md + repo 現有結構分析。*
