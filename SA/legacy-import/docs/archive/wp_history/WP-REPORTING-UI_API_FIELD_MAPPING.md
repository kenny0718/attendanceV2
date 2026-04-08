# WP-REPORTING-UI — API Field Mapping

**建立日期：** 2026-03-13
**類型：** PLANNING DOCUMENT
**狀態：** Planning Complete / Ready for Implementation
**依據：** backend/app/modules/attendance/schemas.py、api.py、repo.py（2026-03-13 code scan）

---

## 說明

本文件定義三個 Reporting API 的 query params、response fields 與前端顯示欄位的完整對照。
所有欄位均以實際後端程式碼為準，不自行假設。

---

## 1. GET /api/v1/attendance/sessions → Sessions List Page

### 1.1 Query Parameters

| 參數名稱 | 後端型別 | 必填 | 預設值 | 前端輸入元件 | 時區/格式注意事項 |
|---------|---------|------|--------|------------|------------------|
| start_date | Optional[datetime] | 否 | None | DateRangeFilter 開始日期 | **必須含 tzinfo**（naive -> 422）；前端以 Asia/Taipei midnight 計算後轉 UTC |
| end_date | Optional[datetime] | 否 | None | DateRangeFilter 結束日期 | 同上；語義為 exclusive（< end_date） |
| user_id | Optional[str] (UUID) | 否 | None（等同自己） | （MVP 不提供員工篩選下拉） | 員工傳他人 UUID -> 403；不傳 -> 查自己 |
| status | Optional[str] | 否 | None（全部） | StatusFilter 下拉 | 可選值：open / closed / 不傳 |
| limit | int | 否 | 50 | PaginationBar | 前端預設 20；後端允許 1~100，超出回 400 |
| offset | int | 否 | 0 | PaginationBar | 前端計算：(page-1) * limit |

### 1.2 Response Fields — sessions 陣列內每個 session 物件

| 後端欄位 | 後端型別 | Nullable | 前端顯示欄位 | 格式處理 | 備註 |
|---------|---------|----------|------------|---------|------|
| session_id | UUID | 否 | （內部 key，不顯示） | String | 用作 v-for :key |
| user_id | UUID | 否 | 員工 ID | String | MVP 不顯示，僅備用 |
| company_id | str | 否 | （不顯示） | — | tenant isolation 用 |
| punch_in_time | datetime (UTC) | 否 | 上班時間 | `dayjs(v).tz('Asia/Taipei').format('YYYY-MM-DD HH:mm')` | 後端回傳 UTC，前端轉 Taipei 顯示 |
| punch_out_time | datetime (UTC) | **是** | 下班時間 | 同上；**null -> 顯示「進行中」** | open session 時為 null |
| duration_minutes | int | **是** | 工時 | `Math.floor(v/60) + '小時' + (v%60) + '分'`；**null -> 顯示「—」** | open session 時為 null |
| status | str | 否 | 狀態 | StatusBadge 元件（見下方 §1.3） | 可能值見 §1.3 |
| punches | list | 是（預設空陣列） | （MVP 不展開顯示） | — | Sessions List 不展示 punches 明細 |

### 1.3 Status 欄位可能值（完整盤點）

依據 `schemas.py` SessionResponse.status field description：

| status 值 | 來源說明 | 前端顯示文字 | Badge 樣式 |
|-----------|---------|------------|------------|
| `open` | 已打上班，尚未打下班 | 進行中 | 藍色 |
| `closed` | 已完整打卡（有 punch_out_time） | 已完成 | 綠色 |
| `pending` | policy engine 評估中 / 待審 | 審核中 | 黃色 |
| `approved` | 已核准 | 已核准 | 深綠色 |
| `rejected` | 已拒絕 | 已拒絕 | 紅色 |
| `missing_punch_out` | 缺下班打卡 | 缺下班卡 | 橘色 |
| (其他/未知) | — | — | 灰色 |

### 1.4 Response 分頁欄位

| 後端欄位 | 後端型別 | 前端用途 |
|---------|---------|----------|
| total | int | 計算總頁數：`Math.ceil(total / limit)` |
| limit | int | 確認後端實際使用的 limit |
| offset | int | 確認目前 offset |

### 1.5 哪些欄位需要 format / 哪些可直接顯示

| 欄位 | 可直接顯示 | 需 format | 備註 |
|------|----------|----------|------|
| session_id | 否 | — | 僅作 key |
| punch_in_time | **否** | 需 dayjs tz 轉換 | UTC -> Taipei |
| punch_out_time | **否** | 需 dayjs tz 轉換 + null 防禦 | — |
| duration_minutes | **否** | 需換算小時分鐘 + null 防禦 | — |
| status | **否** | 需 StatusBadge 元件 | — |
| total | 是 | 顯示總筆數 | — |

---

## 2. GET /api/v1/attendance/reports/user-summary → User Summary Page

### 2.1 Query Parameters

| 參數名稱 | 後端型別 | 必填 | 前端輸入元件 | 注意事項 |
|---------|---------|------|------------|----------|
| start_date | Optional[datetime] | 否 | MonthPicker / DateRangeFilter | 必須含 tzinfo；naive -> 422 |
| end_date | Optional[datetime] | 否 | MonthPicker / DateRangeFilter | exclusive；必須含 tzinfo |

**注意：** 此 endpoint 沒有 user_id 參數（強制查自己，查他人無 endpoint 支援）

### 2.2 Response Fields

| 後端欄位 | 後端型別 | Nullable | 前端顯示欄位 | 格式處理 |
|---------|---------|----------|------------|----------|
| user_id | str | 否 | （不顯示，確認用） | — |
| total_sessions | int | 否 | 總 Sessions | 直接顯示數字 |
| closed_sessions | int | 否 | 已完成 Sessions | 直接顯示數字 |
| open_sessions | int | 否 | 進行中 Sessions | 直接顯示數字 |
| total_work_minutes | int | 否 | 總工時 | `Math.floor(v/60) + '小時' + (v%60) + '分'`；v=0 顯示「0 分鐘」 |
| average_session_minutes | float | **是** | 平均每次工時 | `null -> 顯示「—」`；非 null 保留一位小數 + '分鐘' |
| first_session_time | datetime (UTC) | **是** | 最早打卡 | `dayjs(v).tz('Asia/Taipei').format('YYYY-MM-DD')`；null -> 顯示「—」 |
| last_session_time | datetime (UTC) | **是** | 最近打卡 | 同上；null -> 顯示「—」 |

### 2.3 哪些欄位需要 format

| 欄位 | 可直接顯示 | 需 format |
|------|----------|----------|
| total_sessions | 是 | — |
| closed_sessions | 是 | — |
| open_sessions | 是 | — |
| total_work_minutes | **否** | 換算小時/分鐘 |
| average_session_minutes | **否** | null 防禦 + 格式化 |
| first_session_time | **否** | dayjs tz 轉換 + null 防禦 |
| last_session_time | **否** | dayjs tz 轉換 + null 防禦 |

### 2.4 空結果時的預期值（無符合 sessions）

```json
{
  "user_id": "uuid",
  "total_sessions": 0,
  "closed_sessions": 0,
  "open_sessions": 0,
  "total_work_minutes": 0,
  "average_session_minutes": null,
  "first_session_time": null,
  "last_session_time": null
}
```

前端需確保 total_sessions=0 時顯示「本期間無出勤記錄」提示，而非空白。

---

## 3. GET /api/v1/attendance/reports/company-summary → Company Summary Page

### 3.1 Query Parameters

| 參數名稱 | 後端型別 | 必填 | 前端輸入元件 | 注意事項 |
|---------|---------|------|------------|----------|
| start_date | Optional[datetime] | 否 | MonthPicker / DateRangeFilter | 必須含 tzinfo；naive -> 422 |
| end_date | Optional[datetime] | 否 | MonthPicker / DateRangeFilter | exclusive；必須含 tzinfo |

**注意：** 此 endpoint 不需要 user_id（查全公司），不需要 current_user_id（任何公司成員可查）

### 3.2 Response Fields

| 後端欄位 | 後端型別 | Nullable | 前端顯示欄位 | 格式處理 |
|---------|---------|----------|------------|----------|
| company_id | str | 否 | （不顯示，確認用） | — |
| total_users_with_sessions | int | 否 | 有出勤記錄人數 | 直接顯示數字 |
| total_sessions | int | 否 | 總 Sessions | 直接顯示數字 |
| open_sessions | int | 否 | 進行中 Sessions | 直接顯示數字 |
| closed_sessions | int | 否 | 已完成 Sessions | 直接顯示數字 |
| total_work_minutes | int | 否 | 總工時 | 換算小時/分鐘顯示 |
| average_minutes_per_session | float | **是** | 平均每次 Session 工時 | null -> 顯示「—」 |
| average_minutes_per_user | float | **是** | 平均每位員工工時 | null -> 顯示「—」 |
| first_session_time | datetime (UTC) | **是** | 最早打卡時間 | dayjs tz 轉換；null -> 顯示「—」 |
| last_session_time | datetime (UTC) | **是** | 最近打卡時間 | dayjs tz 轉換；null -> 顯示「—」 |

### 3.3 哪些欄位需要 format

| 欄位 | 可直接顯示 | 需 format |
|------|----------|----------|
| total_users_with_sessions | 是 | — |
| total_sessions | 是 | — |
| open_sessions | 是 | — |
| closed_sessions | 是 | — |
| total_work_minutes | **否** | 換算小時/分鐘 |
| average_minutes_per_session | **否** | null 防禦 + 格式化 |
| average_minutes_per_user | **否** | null 防禦 + 格式化 |
| first_session_time | **否** | dayjs tz 轉換 + null 防禦 |
| last_session_time | **否** | dayjs tz 轉換 + null 防禦 |

### 3.4 空結果時的預期值

```json
{
  "company_id": "company-abc",
  "total_users_with_sessions": 0,
  "total_sessions": 0,
  "open_sessions": 0,
  "closed_sessions": 0,
  "total_work_minutes": 0,
  "average_minutes_per_session": null,
  "average_minutes_per_user": null,
  "first_session_time": null,
  "last_session_time": null
}
```

---

## 4. 時間欄位格式規範

### 4.1 後端 API 時間格式（依據 API_DOCUMENTATION_v2.1.md §通用規範）

| 規則 | 說明 |
|------|------|
| DB 儲存 | UTC-aware datetime |
| API response 回傳 | UTC，帶 Z suffix（如 `2026-03-01T09:05:00Z`）或 ISO 8601 offset |
| API request 接受 | 必須含 timezone offset（ISO 8601），拒絕 naive datetime（422） |

### 4.2 前端時間格式建議

```javascript
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
dayjs.extend(utc)
dayjs.extend(timezone)

const TZ = 'Asia/Taipei'

// 顯示用（UTC -> Taipei）
const displayTime = (utcStr) =>
  utcStr ? dayjs(utcStr).tz(TZ).format('YYYY-MM-DD HH:mm') : '—'

// 查詢用：月份起始（Taipei midnight -> UTC ISO）
const monthStart = (year, month) 