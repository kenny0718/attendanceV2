# WP-REPORTING-UI — Frontend Changeset Plan

**建立日期：** 2026-03-13
**類型：** PLANNING DOCUMENT
**狀態：** Planning Complete / Ready for Implementation
**依據：** frontend/src 實際 code scan（2026-03-13）

---

## 重要原則

- 本文件所有「需新增」項目均依據實際 code scan 確認不存在後標記
- 所有「禁止修改」項目均為現有穩定功能，修改風險極高
- 不憑空假設任何元件已存在

---

## 1. 應新增的 View 檔案

| 檔案路徑 | 對應路由 | 對應 API | 狀態 |
|---------|---------|---------|------|
| `frontend/src/views/reports/AttendanceSessionsPage.vue` | `/attendance/reports/sessions` | GET /api/v1/attendance/sessions | **需新增** |
| `frontend/src/views/reports/CompanySummaryPage.vue` | `/attendance/reports/company-summary` | GET /api/v1/attendance/reports/company-summary | **需新增** |
| `frontend/src/views/reports/UserSummaryPage.vue` | `/attendance/reports/user-summary` | GET /api/v1/attendance/reports/user-summary | **需新增** |

**注意：** `frontend/src/views/reports/` 目錄目前不存在，需一併建立。

### 1.1 AttendanceSessionsPage.vue 最小功能需求

```
- DateRangeFilter 元件（日期區間）
- MonthPicker 快捷按鈕（當月/上月）
- status 篩選下拉（全部 / 進行中 / 已完成）
- Sessions 資料表格：
    欄位：上班時間 | 下班時間 | 工時 | 狀態
    每列 status 使用 StatusBadge 元件
    duration_minutes null -> 顯示「—」
    punch_out_time null -> 顯示「進行中」
- PaginationBar 元件（下方分頁）
- 載入中 / 空結果 / 錯誤狀態處理
```

### 1.2 CompanySummaryPage.vue 最小功能需求

```
- MonthPicker 快捷按鈕（當月/上月）
- 摘要數字區塊（使用 SummaryCard 元件）：
    有出勤記錄人數、總 Sessions、已完成、進行中
    總工時、平均每次工時、平均每人工時
    最早/最近打卡時間
- null 值顯示「—」
- 載入中 / 空結果 / 錯誤狀態處理
```

### 1.3 UserSummaryPage.vue 最小功能需求

```
- MonthPicker 快捷按鈕（當月/上月）
- 摘要數字區塊（使用 SummaryCard 元件）：
    總 Sessions、已完成、進行中
    總工時、平均每次工時
    最早/最近打卡時間
- null 值顯示「—」
- 載入中 / 空結果 / 錯誤狀態處理
```

---

## 2. 應新增的共用元件

以下元件均確認目前不存在於 `frontend/src/components/`，需全部新建：

| 元件路徑 | 用途 | 使用於 |
|---------|------|--------|
| `frontend/src/components/DateRangeFilter.vue` | 日期區間選擇（start_date / end_date） | AttendanceSessionsPage |
| `frontend/src/components/MonthPicker.vue` | 月份快捷選擇（自動計算 Taipei 月份邊界） | 三個 reporting pages |
| `frontend/src/components/StatusBadge.vue` | 出勤狀態標籤（open/closed/pending 等） | AttendanceSessionsPage |
| `frontend/src/components/SummaryCard.vue` | 摘要數字卡片（label + value） | CompanySummaryPage, UserSummaryPage |
| `frontend/src/components/PaginationBar.vue` | 分頁控制列（上一頁/下一頁/頁碼） | AttendanceSessionsPage |

### 2.1 可重用的現有元件

| 元件路徑 | 如何重用 |
|---------|----------|
| `frontend/src/components/Card.vue` | 作為 reporting page 的卡片容器 |
| `frontend/src/components/Navbar.vue` | 導覽列（不修改） |

### 2.2 StatusBadge.vue 介面規格

```vue
<!-- Props -->
<StatusBadge :status="session.status" />

<!-- status prop 對應表 -->
open           -> 「進行中」  藍色
closed         -> 「已完成」  綠色
pending        -> 「審核中」  黃色
approved       -> 「已核准」  深綠色
rejected       -> 「已拒絕」  紅色
missing_punch_out -> 「缺下班卡」 橘色
(其他)         -> 「—」      灰色
```

### 2.3 SummaryCard.vue 介面規格

```vue
<!-- Props -->
<SummaryCard label="總工時" :value="formattedTotalWork" />
<SummaryCard label="有出勤人數" :value="summary.total_users_with_sessions" />
```

### 2.4 PaginationBar.vue 介面規格

```vue
<!-- Props -->
<PaginationBar
  :total="sessions.total"
  :limit="20"
  :offset="currentOffset"
  @change="onPageChange"
/>
```

### 2.5 MonthPicker.vue 介面規格

```vue
<!-- Emits: { start_date: string (ISO), end_date: string (ISO) } -->
<MonthPicker @select="onMonthSelect" />

<!-- 內部計算（時區處理） -->
import dayjs from 'dayjs'
const TZ = 'Asia/Taipei'
const getMonthRange = (year, month) => ({
  start_date: dayjs.tz(`${year}-${month}-01`, TZ).startOf('month').toISOString(),
  end_date:   dayjs.tz(`${year}-${month}-01`, TZ).add(1, 'month').startOf('month').toISOString()
})
```

---

## 3. 應新增或修改的 Store

### 3.1 需新建的 Store

| 檔案路徑 | 用途 | 狀態 |
|---------|------|------|
| `frontend/src/stores/reporting.js` | Reporting 狀態管理 | **需新增** |

### 3.2 reporting.js Store 最小結構

```javascript
import { defineStore } from 'pinia'
import { attendanceApi } from '@/api/attendance'

export const useReportingStore = defineStore('reporting', {
  state: () => ({
    // Sessions List
    sessions: [],
    sessionsTotal: 0,
    sessionsLimit: 20,
    sessionsOffset: 0,
    sessionsLoading: false,
    sessionsError: null,
    sessionsFilters: {
      start_date: null,
      end_date: null,
      status: null
    },

    // Company Summary
    companySummary: null,
    companySummaryLoading: false,
    companySummaryError: null,

    // User Summary
    userSummary: null,
    userSummaryLoading: false,
    userSummaryError: null
  }),

  actions: {
    async fetchSessions(params = {}) {
      this.sessionsLoading = true
      this.sessionsError = null
      try {
        const data = await attendanceApi.fetchSessions(params)
        this.sessions = data.sessions
        this.sessionsTotal = data.total
        this.sessionsLimit = data.limit
        this.sessionsOffset = data.offset
      } catch (err) {
        this.sessionsError = err
      } finally {
        this.sessionsLoading = false
      }
    },

    async fetchCompanySummary(params = {}) {
      this.companySummaryLoading = true
      this.companySummaryError = null
      try {
        this.companySummary = await attendanceApi.fetchCompanySummary(params)
      } catch (err) {
        this.companySummaryError = err
      } finally {
        this.companySummaryLoading = false
      }
    },

    async fetchUserSummary(params = {}) {
      this.userSummaryLoading = true
      this.userSummaryError = null
      try {
        this.userSummary = await attendanceApi.fetchUserSummary(params)
      } catch (err) {
        this.userSummaryError = err
      } finally {
        this.userSummaryLoading = false
      }
    }
  }
})
```

### 3.3 不可修改的現有 Store

| 檔案路徑 | 原因 |
|---------|------|
| `frontend/src/stores/attendance.js` | 打卡核心狀態；修改可能影響 punch/break flow |
| `frontend/src/stores/auth.js` | 認證狀態；僅允許 **讀取**（useAuthStore().userId / companyId） |

---

## 4. 應新增或修改的 API Service 方法

### 4.1 修改檔案：`frontend/src/api/attendance.js`

**修改方式：** 在現有 `attendanceApi` 物件中**新增三個方法**，不修改現有方法。

```javascript
// 在 attendanceApi 物件末尾新增：

// Reporting: Sessions List (WP-REPORTING-UI Step 1)
fetchSessions: (params = {}) =>
  apiClient.get('/v1/attendance/sessions', { params }),

// Reporting: Company Summary (WP-REPORTING-UI Step 2)
fetchCompanySummary: (params = {}) =>
  apiClient.get('/v1/attendance/reports/company-summary', { params }),

// Reporting: User Summary (WP-REPORTING-UI Step 3)
fetchUserSummary: (params = {}) =>
  apiClient.get('/v1/attendance/reports/user-summary', { params }),
```

**不修改現有方法：**
- `punchIn`、`punchOut`、`breakOut`、`breakIn` — 打卡核心，禁止動
- `getCurrentStatus`、`getHistory`、`getBreakPunches` — 首頁依賴，禁止動
- `updatePunchNote`、`createOutCheckpoint`、`listOutCheckpoints` — 保持不動

### 4.2 不修改的 API 檔案

| 檔案路徑 | 原因 |
|---------|------|
| `frontend/src/api/client.js` | Axios instance 已含 Bearer + X-Company-ID + X-User-ID；不需修改 |
| `frontend/src/api/auth.js` | 認證 API；與 reporting 無關 |

---

## 5. Router 修改計畫

### 5.1 修改檔案：`frontend/src/router/index.js`

**修改方式：** 在現有 `routes` 陣列中**新增三個路由**，不修改現有路由。

```javascript
// 在現有 routes 陣列中新增：
{
  path: '/attendance/reports/sessions',
  name: 'AttendanceSessions',
  component: () => import('@/views/reports/AttendanceSessionsPage.vue'),
  meta: { requiresAuth: true }
},
{
  path: '/attendance/reports/company-summary',
  name: 'CompanySummary',
  component: () => import('@/views/reports/CompanySummaryPage.vue'),
  meta: { requiresAuth: true }
},
{
  path: '/attendance/reports/user-summary',
  name: 'UserSummary',
  component: () => import('@/views/reports/UserSummaryPage.vue'),
  meta: { requiresAuth: true }
},
```

**不修改現有路由：**
- `/` (Home) — 打卡主頁，禁止動
- `/login` (Login) — 登入頁，禁止動
- router.beforeEach guard — 禁止動

---

## 6. 目錄結構變更摘要

### 需新建的目錄

```
frontend/src/views/reports/          (新目錄)
```

### 需新建的檔案（完整清單）

```
frontend/src/views/reports/
  AttendanceSessionsPage.vue          (新建)
  CompanySummaryPage.vue              (新建)
  UserSummaryPage.vue                 (新建)

frontend/src/components/
  DateRangeFilter.vue                 (新建)
  MonthPicker.vue                     (新建)
  StatusBadge.vue                     (新建)
  SummaryCard.vue                     (新建)
  PaginationBar.vue                   (新建)

frontend/src/stores/
  reporting.js                        (新建)
```

### 需修改的現有檔案（最小改動）

```
frontend/src/api/attendance.js        (新增 3 個方法，不動現有方法)
frontend/src/router/index.js          (新增 3 個路由，不動現有路由)
```

---

## 7. 禁止修改的檔案清單

以下檔案在本 WP 中**絕對禁止修改**，避免影響現有打卡流程：

| 檔案 | 原因 |
|------|------|
| `frontend/src/views/Home.vue` | 打卡主頁；修改可能破壞 punch/break flow |
| `frontend/src/views/Login.vue` | 認證頁；禁止改動 |
| `frontend/src/stores/attendance.js` | 打卡核心狀態；任何修改都可能破壞現有功能 |
| `frontend/src/stores/auth.js` | 認證狀態；僅允許讀取 |
| `frontend/src/api/client.js` | Axios 設定；修改影響全部 API 呼叫 |
| `frontend/src/api/auth.js` | 認證 API |
| `frontend/src/components/attendance/*` | 打卡相關元件 |
| `frontend/src/components/PunchButton.vue` | 打卡按鈕 |
| `frontend/src/composables/useLocation.js` | GPS 定位；與 reporting 無關 |
| `frontend/src/utils/locationAdapter.js` | GPS 