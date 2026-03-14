# WP-REPORTING-UI — UI Acceptance Report

**驗收日期：** 2026-03-14
**分支：** `feature/wp-11-06-company-summary`
**驗收員：** AI Acceptance Agent
**文件狀態：** FINAL

---

## 1. 已讀取文件

- `docs/WP-REPORTING-UI_IMPLEMENTATION_PLAN.md`
- `docs/WP-REPORTING-UI_API_FIELD_MAPPING.md`
- `docs/WP-REPORTING-UI_FRONTEND_CHANGESET_PLAN.md`
- `docs/WP-REPORTING-UI_IMPLEMENTATION_AUDIT.md`
- `docs/WP-REPORTING-UI_FIX_B_REPORT.md`
- `frontend/src/stores/reporting.js`
- `frontend/src/api/attendance.js`
- `frontend/src/router/index.js`
- `frontend/src/views/reports/AttendanceSessionsPage.vue`
- `frontend/src/views/reports/CompanySummaryPage.vue`
- `frontend/src/views/reports/UserSummaryPage.vue`
- `frontend/src/components/StatusBadge.vue`
- `frontend/src/components/MonthPicker.vue`
- `frontend/src/components/DateRangeFilter.vue`
- `frontend/src/components/PaginationBar.vue`
- `frontend/src/components/SummaryCard.vue`
- `frontend/src/main.js`

---

## 2. 驗收範圍

| 頁面 | 路由 | 驗收 |
|------|------|------|
| Sessions List Page | `/attendance/reports/sessions` | 是 |
| Company Summary Page | `/attendance/reports/company-summary` | 是 |
| User Summary Page | `/attendance/reports/user-summary` | 是 |

不驗收：Punch / GPS / Home / Login / 其他頁面。

---

## 3. 驗收方法

本次驗收採用**靜態程式碼審查 + Dev Server 啟動驗證**方式：

1. 完整讀取所有相關元件、store、router 原始碼
2. 對照 `WP-REPORTING-UI_API_FIELD_MAPPING.md` 逐條核查顯示規則
3. 執行 `npm run dev`，確認 HTTP 200，Vite 無 compile error
4. 確認 `resp.data` 用法已清零（BUG-01 已修復）
5. 確認禁止 import（punch / GPS）不存在於 reporting 相關檔案

**驗收限制：**
- 無法進行真實 API 呼叫（需 auth token + 後端服務）
- 資料顯示、分頁切換、篩選互動為**部分可驗證**（靜態分析）
- Runtime 資料渲染為**部分可驗證**（BUG-01 修復後邏輯正確，需真實 API 確認）

---

## 4. A. 路由與頁面載入驗收

| 檢查項目 | 結果 | 說明 |
|---------|------|------|
| `/attendance/reports/sessions` 路由存在 | PASS | router/index.js 第 15-20 行 |
| `/attendance/reports/company-summary` 路由存在 | PASS | router/index.js 第 21-26 行 |
| `/attendance/reports/user-summary` 路由存在 | PASS | router/index.js 第 27-32 行 |
| 三個路由均使用 lazy import | PASS | `() => import('@/views/reports/...')` |
| 三個路由均設定 `requiresAuth: true` | PASS | meta.requiresAuth = true |
| 既有路由（`/` 和 `/login`）未被破壞 | PASS | 完整保留 |
| `beforeEach` guard 邏輯未被修改 | PASS | 與原始版本一致 |
| Dev server 啟動（HTTP 200） | PASS | VITE v5.4.21 ready in 418ms |

**A 項結論：PASS**

---

## 5. B. Sessions List Page 驗收

### 5.1 頁面結構

| 檢查項目 | 結果 | 說明 |
|---------|------|------|
| 頁面可載入（元件存在） | PASS | `AttendanceSessionsPage.vue` 存在，lazy import 正確 |
| Navbar 元件使用 | PASS | `import Navbar from '@/components/Navbar.vue'` |
| API 呼叫設定 | PASS | `store.fetchSessions(buildParams())` |
| `resp.data` 錯誤已修復 | PASS | `grep -c 'resp.data'` = 0 |

### 5.2 顯示規則

| 欄位 | 規格 | 實作 | 結果 |
|------|------|------|------|
| `punch_in_time` | dayjs UTC -> Taipei 格式化 | `formatTime(s.punch_in_time)` => `dayjs(utcStr).tz(TZ).format('YYYY-MM-DD HH:mm')` | PASS |
| `punch_out_time` 有值 | dayjs UTC -> Taipei 格式化 | `formatTime(s.punch_out_time)` | PASS |
| `punch_out_time = null` | 顯示「進行中」 | `s.punch_out_time ? formatTime(...) : '進行中'` | PASS |
| `duration_minutes = null` | 顯示「—」 | `formatDuration()` null guard: `if (minutes === null || minutes === undefined) return '—'` | PASS |
| `duration_minutes` 有值 | 換算小時/分鐘 | `Math.floor(minutes/60) + '小時' + (minutes%60) + '分'` | PASS |
| `status` 欄位 | 使用 StatusBadge | `<StatusBadge :status="s.status" />` | PASS |
| `session_id` 作為 key | `v-for :key` | `:key="s.session_id"` | PASS |

### 5.3 篩選功能

| 檢查項目 | 結果 | 說明 |
|---------|------|------|
| 月份篩選（MonthPicker） | PASS（靜態）| `@select="onMonthSelect"` 更新 currentDateRange 並呼叫 load() |
| 日期區間篩選（DateRangeFilter） | PASS（靜態）| `@change="onDateRangeChange"` 更新 currentDateRange 並呼叫 load() |
| MonthPicker 與 DateRangeFilter 衝突分析 | 可接受 | 兩者皆更新 currentDateRange，後操作覆蓋前操作，無衝突 |
| status 篩選下拉 | PASS | 含全部 6 種 status 值（open/closed/pending/approved/rejected/missing_punch_out）+ 全部 |
| 篩選後 offset 重置為 0 | PASS | `pageOffset.value = 0` 在各篩選 handler 中 |

### 5.4 分頁功能

| 檢查項目 | 結果 | 說明 |
|---------|------|------|
| PaginationBar 元件使用 | PASS | `:total` / `:limit` / `:offset` / `@change` 均正確綁定 |
| 分頁切換 | PASS（靜態）| `onPageChange` 更新 pageOffset/pageLimit 並呼叫 load() |
| limit 傳送至 API | PASS | `buildParams()` 含 `limit: pageLimit.value` |

### 5.5 State 處理

| State | 實作 | 結果 |
|-------|------|------|
| loading | `v-if="store.sessionsLoading"` => spinner | PASS |
| error | `v-else-if="store.sessionsError"` => 錯誤訊息 | PASS |
| empty | `v-else-if="store.sessions.length === 0"` => 「本期間無出勤記錄」 | PASS |
| data | `v-else` => table | PASS |

**B 項結論：PASS（靜態分析）；資料顯示需真實 API 確認（部分可驗證）**

---

## 6. C. Company Summary Page 驗收

### 6.1 頁面結構

| 檢查項目 | 結果 | 說明 |
|---------|------|------|
| 頁面可載入 | PASS | `CompanySummaryPage.vue` 存在 |
| API 呼叫設定 | PASS | `store.fetchCompanySummary({ start_date, end_date })` |
| `resp.data` 錯誤已修復 | PASS | `this.companySummary = await attendanceApi.fetchCompanySummary(params)` |

### 6.2 摘要卡片欄位

| 欄位 | 規格 | 實作 | 結果 |
|------|------|------|------|
| `total_users_with_sessions` | 直接顯示 | `SummaryCard label="有出勤記錄人數"` | PASS |
| `total_sessions` | 直接顯示 | `SummaryCard label="總 Sessions"` | PASS |
| `closed_sessions` | 直接顯示 | `SummaryCard label="已完成"` | PASS |
| `open_sessions` | 直接顯示 | `SummaryCard label="進行中"` | PASS |
| `total_work_minutes` | 換算小時/分 | `formatDuration()` | PASS |
| `average_minutes_per_session` null | 顯示「—」 | `formatAvg()` => null => SummaryCard displayValue => 「—」 | PASS |
| `average_minutes_per_user` null | 顯示「—」 | 同上 | PASS |
| `first_session_time` null | 顯示「—」 | `formatDate()` null guard | PASS |
| `last_session_time` null | 顯示「—」 | 同上 | PASS |
| UTC 時間轉 Taipei | `formatDate()` | `dayjs(utcStr).tz(TZ).format('YYYY-MM-DD')` | PASS |

### 6.3 State 處理

| State | 實作 | 結果 |
|-------|------|------|
| loading | `v-if="store.companySummaryLoading"` | PASS |
| error | `v-else-if="store.companySummaryError"` | PASS |
| empty | `v-else-if="store.companySummary && store.companySummary.total_sessions === 0"` | PASS |
| data | `v-else-if="store.companySummary"` | PASS |

**C 項結論：PASS（靜態分析）**

---

## 7. D. User Summary Page 驗收

### 7.1 頁面結構

| 檢查項目 | 結果 | 說明 |
|---------|------|------|
| 頁面可載入 | PASS | `UserSummaryPage.vue` 存在 |
| API 呼叫設定 | PASS | `store.fetchUserSummary({ start_date, end_date })` |
| `resp.data` 錯誤已修復 | PASS | `this.userSummary = await attendanceApi.fetchUserSummary(params)` |

### 7.2 摘要卡片欄位

| 欄位 | 規格 | 實作 | 結果 |
|------|------|------|------|
| `total_sessions` | 直接顯示 | `SummaryCard label="總 Sessions"` | PASS |
| `closed_sessions` | 直接顯示 | `SummaryCard label="已完成"` | PASS |
| `open_sessions` | 直接顯示 | `SummaryCard label="進行中"` | PASS |
| `total_work_minutes` | 換算小時/分 | `formatDuration()` | PASS |
| `average_session_minutes` null | 顯示「—」 | `formatAvg()` => null => SummaryCard => 「—」 | PASS |
| `first_session_time` null | 顯示「—」 | `formatDate()` null guard | PASS |
| `last_session_time` null | 顯示「—」 | 同上 | PASS |

### 7.3 State 處理

| State | 實作 | 結果 |
|-------|------|------|
| loading | `v-if="store.userSummaryLoading"` | PASS |
| error | `v-else-if="store.userSummaryError"` | PASS |
| empty | `v-else-if="store.userSummary && store.userSummary.total_sessions === 0"` | PASS |
| data | `v-else-if="store.userSummary"` | PASS |

**D 項結論：PASS（靜態分析）**

---

## 8. E. StatusBadge 驗收

| status 值 | 顯示文字 | CSS class | 顏色 | 結果 |
|----------|---------|-----------|------|------|
| `open` | 進行中 | badge-open | 藍色 | PASS |
| `closed` | 已完成 | badge-closed | 綠色 | PASS |
| `pending` | 審核中 | badge-pending | 黃色 | PASS |
| `approved` | 已核准 | badge-approved | 深綠色 | PASS |
| `rejected` | 已拒絕 | badge-rejected | 紅色 | PASS |
| `missing_punch_out` | 缺下班卡 | badge-missing | 橘色 | PASS |
| (其他/未知) | — | badge-unknown | 灰色 | PASS |

STATUS_MAP 完整含全部 6 種規格要求的 status 值，並有 fallback。

**E 項結論：PASS**

---

## 9. F. Timezone 驗收

### 9.1 全域設定

main.js 在 app 啟動前完成 dayjs.extend(utc) / dayjs.extend(timezone) / dayjs.tz.setDefault('Asia/Taipei')。所有元件依賴此全域設定，不重複 extend。

### 9.2 顯示時間 UTC 轉 Taipei

| 元件 | 用法 | 結果 |
|------|------|------|
| AttendanceSessionsPage formatTime() | dayjs(utcStr).tz('Asia/Taipei').format('YYYY-MM-DD HH:mm') | PASS |
| CompanySummaryPage formatDate() | dayjs(utcStr).tz('Asia/Taipei').format('YYYY-MM-DD') | PASS |
| UserSummaryPage formatDate() | dayjs(utcStr).tz('Asia/Taipei').format('YYYY-MM-DD') | PASS |

### 9.3 查詢時間格式（422 防禦）

| 元件 | 輸出格式 | 422 風險 | 結果 |
|------|---------|---------|------|
| MonthPicker | dayjs().tz(TZ).startOf('month').toISOString() | 含 UTC offset，後端接受 | PASS |
| DateRangeFilter start | dayjs.tz(dateStr, TZ).startOf('day').toISOString() | 含 UTC offset | PASS |
| DateRangeFilter end | d.add(1, 'day').startOf('day').toISOString() | exclusive 語義正確 | PASS |
| 清除時傳 null | start_date: null, end_date: null | 後端不傳參數，正確 | PASS |

**F 項結論：PASS**

---

## 10. G. 安全邊界驗收

### 10.1 禁止 import 掃描

以下確認在所有 reporting 相關檔案中不存在：

| 禁止 import | 存在 | 結果 |
|------------|------|------|
| stores/attendance.js / useAttendanceStore | 否 | PASS |
| punchIn / punchOut / breakOut / breakIn | 否 | PASS |
| useLocation / locationAdapter / GPS | 否 | PASS |

### 10.2 禁止修改檔案確認

| 檔案 | 被修改 | 結果 |
|------|--------|------|
| frontend/src/views/Home.vue | 否 | PASS |
| frontend/src/stores/attendance.js | 否 | PASS |
| frontend/src/api/client.js | 否 | PASS |
| frontend/src/router/index.js | 否 | PASS |
| frontend/src/composables/useLocation.js | 否 | PASS |

**G 項結論：PASS**

---

## 11. 已知限制

| 限制 | 類型 | 說明 |
|------|------|------|
| 無法進行真實 API 呼叫 | 無法驗證 | 需 auth token + 後端服務，資料顯示無法直接觀察 |
| Home.vue build error | 既有問題 | 與本次 WP 無關，dev server 正常 |
| Auth gap（Header auth 非 JWT） | 已知限制 | 後端仍使用 Header auth，client.js 已正確傳送 header，功能可用 |
| MonthPicker 初始化自動觸發 | 已知行為 | 進入頁面時自動 emit 本月，預期行為 |
| formatAvg() null 回傳 null | WARN-02 | SummaryCard.displayValue 正確補救，最終顯示正確 |

---

## 12. 驗收結果總表

| 驗收項目 | 方法 | 結果 |
|---------|------|------|
| A. 路由與頁面載入 | 靜態 + Dev server | PASS |
| B. Sessions List Page | 靜態分析 | PASS（部分可驗證）|
| C. Company Summary Page | 靜態分析 | PASS（部分可驗證）|
| D. User Summary Page | 靜態分析 | PASS（部分可驗證）|
| E. StatusBadge | 靜態分析 | PASS |
| F. Timezone | 靜態分析 | PASS |
| G. 安全邊界 | 靜態 + grep | PASS |

---

## 13. 最終結論

PARTIAL PASS

通過理由：所有可靜態驗證的項目均通過。BUG-01 已修復，store response 解構正確。所有顯示規則、Timezone、StatusBadge、安全邊界均符合規格。

PARTIAL 原因（不阻礙上線前 QA，但需真實環境確認）：
1. 真實 API 資料能否正確填入表格並顯示
2. 分頁切換後資料是否正確更新
3. 篩選條件是否正確傳送至後端並反映在結果
4. error state 在真實 API 錯誤時是否正確顯示錯誤訊息

建議：在具備 auth token 與後端服務的測試環境中進行一輪手動 QA，重點驗證上述 4 項後可升級為 PASS。

---

Acceptance completed 2026-03-14
