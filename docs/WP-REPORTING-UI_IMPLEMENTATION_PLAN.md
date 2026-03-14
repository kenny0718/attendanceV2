# WP-REPORTING-UI — Reporting UI Implementation Plan

**建立日期：** 2026-03-13
**類型：** PLANNING DOCUMENT（規劃階段，尚未實作）
**狀態：** Planning Complete / Ready for Implementation
**覆蓋範圍：** Reporting UI 前端實作規劃（MVP-1 / MVP-2 / MVP-3）
**不覆蓋：** Attendance Core 修改、新報表規則、圖表、CSV/PDF 匯出、請假/班表/補打卡整合

---

## 1. 盤點基礎：已確認後端 API 狀態

本次盤點基於 2026-03-13 實際 code scan。

### 1.1 Sessions List API

```
GET /api/v1/attendance/sessions
```

- **實作狀態：** `CODE_COMPLETE`（已在 `api.py` 中實作，`repo.py` 中有 `ReportingRepository`）
- **測試狀態：** `test_reporting_sessions.py` 存在（SES-01 ~ SES-11）
- **Auth 方式：** 仍使用 `get_current_company_id` / `get_current_user_id`（Header auth，未完成 JWT 遷移）
- **是否可用於 UI：** GAP — Auth 尚未完成 JWT 遷移（WP-C1-03 後才安全）；功能邏輯已具備

### 1.2 User Summary API

```
GET /api/v1/attendance/reports/user-summary
```

- **實作狀態：** `CODE_COMPLETE`（已在 `api.py` 中實作）
- **測試狀態：** `test_reporting_user_summary.py` 存在（USR-01 ~ USR-08）
- **Auth 方式：** 同上，Header auth
- **是否可用於 UI：** GAP — 同上

### 1.3 Company Summary API

```
GET /api/v1/attendance/reports/company-summary
```

- **實作狀態：** `CODE_COMPLETE`（已在 `api.py` 中實作）
- **測試狀態：** `test_reporting_company_summary.py` 存在（CMP-01 ~ CMP-07）
- **Auth 方式：** 同上，Header auth
- **是否可用於 UI：** GAP — 同上

---

## 2. API Inventory（契約盤點）

### 2.1 GET /api/v1/attendance/sessions

**Query Parameters：**

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| start_date | datetime (ISO 8601 with tz) | 選填 | punch_in_time 起始（inclusive） |
| end_date | datetime (ISO 8601 with tz) | 選填 | punch_in_time 結束（exclusive） |
| user_id | UUID string | 選填 | 員工只能查自己，傳他人 UUID 回 403 |
| status | string | 選填 | open / closed / 不傳=全部 |
| limit | int | 選填 | 預設 50，最大 100，超出回 400 |
| offset | int | 選填 | 預設 0 |

**Response Schema：**

```json
{
  "sessions": [
    {
      "session_id": "uuid",
      "user_id": "uuid",
      "company_id": "string",
      "punch_in_time": "2026-03-01T09:05:00Z",
      "punch_out_time": "2026-03-01T18:00:00Z",
      "duration_minutes": 535,
      "status": "closed"
    }
  ],
  "total": 220,
  "limit": 50,
  "offset": 0
}
```

**Status 可能值（依據 schemas.py 與測試盤點）：**
- `open` — 已打上班，尚未打下班
- `closed` — 已完整打卡
- `pending` — 政策評估中
- `approved` — 已核准
- `rejected` — 已拒絕
- `missing_punch_out` — 缺下班打卡

**錯誤碼：**
- 400: limit 超出範圍
- 403: 員工查他人
- 422: naive datetime

---

### 2.2 GET /api/v1/attendance/reports/user-summary

**Query Parameters：**

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| start_date | datetime (ISO 8601 with tz) | 選填 | punch_in_time 起始 |
| end_date | datetime (ISO 8601 with tz) | 選填 | punch_in_time 結束（exclusive） |

**Response Schema：**

```json
{
  "user_id": "uuid-string",
  "total_sessions": 22,
  "closed_sessions": 21,
  "open_sessions": 1,
  "total_work_minutes": 10080,
  "average_session_minutes": 480.0,
  "first_session_time": "2026-03-01T01:00:00Z",
  "last_session_time": "2026-03-31T01:00:00Z"
}
```

**注意：** `average_session_minutes` 以 closed_sessions 為分母，0 個 closed session 時回 null。

---

### 2.3 GET /api/v1/attendance/reports/company-summary

**Query Parameters：**

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| start_date | datetime (ISO 8601 with tz) | 選填 | punch_in_time 起始 |
| end_date | datetime (ISO 8601 with tz) | 選填 | punch_in_time 結束（exclusive） |

**Response Schema：**

```json
{
  "company_id": "string",
  "total_users_with_sessions": 15,
  "total_sessions": 330,
  "open_sessions": 3,
  "closed_sessions": 327,
  "total_work_minutes": 156960,
  "average_minutes_per_session": 480.0,
  "average_minutes_per_user": 10464.0,
  "first_session_time": "2026-03-01T01:00:00Z",
  "last_session_time": "2026-03-31T01:00:00Z"
}
```

---

## 3. 前端現況盤點（2026-03-13 code scan）

### 3.1 有效路由

| 路徑 | 元件 | 狀態 |
|------|------|------|
| `/` | `Home.vue` | 存在 |
| `/login` | `Login.vue` | 存在 |
| `/attendance/reports/sessions` | 無 | **不存在，需新增** |
| `/attendance/reports/user-summary` | 無 | **不存在，需新增** |
| `/attendance/reports/company-summary` | 無 | **不存在，需新增** |

### 3.2 現有 Views

| 檔案 | 功能 | 可重用程度 |
|------|------|------------|
| `Home.vue` | 打卡主頁（3-Card 佈局） | 不可修改，但可參考佈局模式 |
| `Login.vue` | 登入頁 | 不相關 |

### 3.3 現有 Stores

| 檔案 | 功能 | 可重用程度 |
|------|------|------------|
| `stores/attendance.js` | 打卡狀態管理 | 可參考 pattern，不可修改現有 actions |
| `stores/auth.js` | 認證狀態 | 可直接使用 useAuthStore()（取得 companyId/userId/userRole） |

### 3.4 現有 API Service

| 檔案 | 覆蓋的 endpoint | 缺口 |
|------|----------------|------|
| `api/attendance.js` | punch-in/out, break-out/in, current-status, history, break-punches, out-checkpoint | **缺少 reporting 三個 endpoint** |
| `api/client.js` | Axios instance（Bearer token + X-Company-ID + X-User-ID headers） | 可直接重用 |

### 3.5 現有共用元件

| 元件 | 功能 | 可重用狀態 |
|------|------|------------|
| `components/Card.vue` | 卡片容器 | 可重用 |
| `components/Navbar.vue` | 導覽列 | 可重用 |
| `components/StatusCard.vue` | 狀態卡片 | 需確認介面是否通用 |
| `components/PunchButton.vue` | 打卡按鈕 | 不相關 |
| `components/attendance/*` | 打卡相關區塊元件 | 不相關 |

**缺少的共用元件（需新增）：**
- `components/DateRangeFilter.vue` — 日期區間選擇器
- `components/MonthPicker.vue` — 月份選擇器
- `components/StatusBadge.vue` — 出勤狀態標籤
- `components/SummaryCard.vue` — 摘要數字區塊
- `components/PaginationBar.vue` — 分頁控制列

### 3.6 現有 Composables

| 檔案 | 功能 |
|------|------|
| `composables/useLocation.js` | GPS 定位（與 reporting 無關） |

---

## 4. UI 頁面切分（MVP 範圍）

### MVP-1：Sessions List Page（個人出勤查詢）

**路由：** `/attendance/reports/sessions`
**後端 API：** `GET /api/v1/attendance/sessions`
**功能：**
- 日期區間篩選（start_date / end_date，Asia/Taipei 邊界）
- 月份快捷按鈕（自動計算當月 start/end）
- status 篩選（全部 / open / closed）
- Sessions 列表（punch_in_time、punch_out_time、duration_minutes、status）
- 基本分頁（limit/offset，顯示 total）
- 員工預設查詢自己（user_id 從 auth store 取得）

**注意事項：**
- 日期傳送至後端時必須帶 timezone（ISO 8601 with +08:00 或 Z）
- duration_minutes 為 null 時顯示「進行中」

---

### MVP-2：Company Summary Page（公司出勤摘要）

**路由：** `/attendance/reports/company-summary`
**後端 API：** `GET /api/v1/attendance/reports/company-summary`
**功能：**
- 月份/日期區間篩選
- 摘要數字卡片：
  - total_users_with_sessions（有出勤記錄人數）
  - total_sessions（總 sessions）
  - closed_sessions（已完成）
  - open_sessions（進行中）
  - total_work_minutes（總工時）
  - average_minutes_per_session（平均每次）
  - average_minutes_per_user（平均每人）
- first_session_time / last_session_time

**注意事項：**
- 此頁面不顯示個人明細，只有公司聚合數字
- average 欄位為 null 時顯示「—」

---

### MVP-3：User Summary Page（個人出勤摘要）

**路由：** `/attendance/reports/user-summary`
**後端 API：** `GET /api/v1/attendance/reports/user-summary`
**功能：**
- 月份/日期區間篩選
- 個人摘要數字卡片：
  - total_sessions / closed_sessions / open_sessions
  - total_work_minutes（可換算小時顯示）
  - average_session_minutes
  - first_session_time / last_session_time

**注意事項：**
- 員工只能查詢自己（user_id 強制 = current_user_id）
- average_session_minutes 為 null 時顯示「—」

---

## 5. 資料流設計

```
View (.vue)
  -> 呼叫 store action
Store (stores/reporting.js — 需新建)
  -> 呼叫 API service method
API Service (api/attendance.js — 需新增 3 個方法)
  -> Axios (api/client.js — 已含 Bearer + X-Company-ID + X-User-ID)
Backend API (已完成，CODE_COMPLETE)
```

**時區處理流程：**
1. UI 顯示使用 `dayjs().tz('Asia/Taipei')` 格式化
2. 傳送至後端時計算 Taipei 