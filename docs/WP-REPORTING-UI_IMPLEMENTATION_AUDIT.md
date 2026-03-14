# WP-REPORTING-UI — Implementation Audit Report

**審計日期：** 2026-03-14
**審計分支：** `feature/wp-11-06-company-summary`
**審計員：** AI Audit Agent
**文件狀態：** FINAL

---

## 1. 實際修改檔案審計

**修改檔案（2 個，與 ChangeSet Plan 一致）：**
- `frontend/src/api/attendance.js`
- `frontend/src/router/index.js`

**新增檔案（9 個，與 ChangeSet Plan 一致）：**
- `frontend/src/components/DateRangeFilter.vue`
- `frontend/src/components/MonthPicker.vue`
- `frontend/src/components/PaginationBar.vue`
- `frontend/src/components/StatusBadge.vue`
- `frontend/src/components/SummaryCard.vue`
- `frontend/src/stores/reporting.js`
- `frontend/src/views/reports/AttendanceSessionsPage.vue`
- `frontend/src/views/reports/CompanySummaryPage.vue`
- `frontend/src/views/reports/UserSummaryPage.vue`

**結論：PASS**

---

## 2. 禁止修改檔案檢查

以下檔案均未被修改：
Home.vue / Login.vue / stores/attendance.js / stores/auth.js /
api/client.js / api/auth.js / components/attendance/* /
PunchButton.vue / useLocation.js / locationAdapter.js

**結論：PASS**

---

## 3. Reporting UI 架構檢查

Views / Components / Store 結構均存在且正確。
Pinia defineStore 使用正確，store id = 'reporting'，無 circular import。

### [BUG-01 嚴重] stores/reporting.js response 解構錯誤

api/client.js response interceptor 已 unwrap response.data，attendanceApi.*() 直接回傳 body object。
但 reporting.js 再次取 .data，導致 undefined。

**現況（錯誤）：**
```javascript
const resp = await attendanceApi.fetchSessions(params)
const data = resp.data         // undefined！
this.sessions = data.sessions  // TypeError crash

this.companySummary = resp.data  // undefined
this.userSummary    = resp.data  // undefined
```

**修正：**
```javascript
const data = await attendanceApi.fetchSessions(params)
this.sessions       = data.sessions
this.sessionsTotal  = data.total
this.sessionsLimit  = data.limit
this.sessionsOffset = data.offset

this.companySummary = await attendanceApi.fetchCompanySummary(params)
this.userSummary    = await attendanceApi.fetchUserSummary(params)
```

---

## 4. Router 安全檢查

新增路由：
- `/attendance/reports/sessions` — requiresAuth: true
- `/attendance/reports/company-summary` — requiresAuth: true
- `/attendance/reports/user-summary` — requiresAuth: true

既有路由（/ 和 /login）及 beforeEach guard 完整未動（diff 僅有 whitespace 清理）。

**結論：PASS**

---

## 5. API Service 檢查

新增方法：
- `fetchSessions` → GET /v1/attendance/sessions
- `fetchCompanySummary` → GET /v1/attendance/reports/company-summary
- `fetchUserSummary` → GET /v1/attendance/reports/user-summary

所有既有方法（punchIn/punchOut/breakOut/breakIn/getCurrentStatus/
getHistory/getRecentLogs/getBreakPunches/updatePunchNote）均未被修改。
api/client.js 未被修改，Authorization headers 完整。

附記：本次 diff 同時含 createOutCheckpoint/listOutCheckpoints（其他 WP 遺留），
不影響 Reporting UI，不影響既有 Punch flow。

**結論：PASS**

---

## 6. 顯示規則一致性檢查

- punch_out_time null → 顯示「進行中」：PASS
- duration_minutes null → 顯示「—」：PASS
- StatusBadge 支援 open/closed/pending/approved/rejected/missing_punch_out：PASS
- Summary null 值顯示「—」：PASS

[WARN-02 輕度] formatAvg() null 時回傳 null 而非字串，SummaryCard 補救正確，
最終顯示正確，但函數語義不一致。

**結論：PASS**

---

## 7. Timezone 檢查

main.js 全域設定：
```javascript
dayjs.extend(utc)
dayjs.extend(timezone)
dayjs.tz.setDefault('Asia/Taipei')
```

各元件均正確使用 dayjs(utcStr).tz(TZ).format(...)，
MonthPicker / DateRangeFilter 送出 ISO8601 含 timezone offset，422 風險排除。
各元件不重複呼叫 dayjs.extend()（正確做法）。

**結論：PASS**

---

## 8. Runtime 檢查

Dev server：VITE v5.4.21 ready in 3148 ms，HTTP GET / 200 OK。
三個 route 均可解析（lazy import 指向存在的元件）。

[BUG-01 嚴重] 真實 API 呼叫後：
- fetchSessions：TypeError crash
- fetchCompanySummary：companySummary = undefined，頁面空白
- fetchUserSummary：userSummary = undefined，頁面空白

Loading / Empty / Error State 均已正確實作。

**結論：FAIL（BUG-01 是 blocker）**

---

## 9. Dead Code 檢查

[WARN-01 輕度] reporting.js 的 sessionsFilters state 未被使用（dead state）
[WARN-03 輕度] formatDuration() 在三個 View 各自重複定義
無未使用元件，無過度抽象。

**結論：輕度問題，不影響功能。**

---

## 10. Punch 系統安全檢查

所有 Reporting 相關檔案均無 import：
- stores/attendance.js / useAttendanceStore
- punch API 方法
- GPS composables（useLocation / locationAdapter）

Reporting UI 與 Punch flow 完全解耦。

**結論：PASS**

---

## 11. 最終 Audit Summary

| 項目 | 結果 |
|------|------|
| 檔案變更一致性 | PASS |
| 禁止修改檔案 | PASS |
| Reporting UI 架構 | PASS（含 BUG-01 警告）|
| Router 安全 | PASS |
| API Service | PASS |
| 顯示規則一致性 | PASS |
| Timezone | PASS |
| Runtime | FAIL |
| Dead Code | 輕度問題 |
| Punch 系統安全 | PASS |

---

## 12. 問題清單

### 嚴重（必須修復後才能 UI 驗收）

**BUG-01：stores/reporting.js response 解構錯誤**
- 位置：frontend/src/stores/reporting.js 第 34、51、64 行
- 原因：client.js 已 unwrap response.data，reporting.js 再取 .data 得到 undefined
- 影響：三頁面資料全部無法渲染，fetchSessions 觸發 TypeError crash
- 修正：移除 const resp =，直接 await attendanceApi.*() 取 body（見第 3.4 節）

### 輕度（不阻礙驗收，建議修復）

**WARN-01：sessionsFilters state 未使用**
- stores/reporting.js 的 sessionsFilters 物件為 dead state
- 建議移除或接入 View 篩選邏輯

**WARN-02：formatAvg() null 時回傳 null 而非字串**
- CompanySummaryPage / UserSummaryPage
- 最終顯示正確，建議改為 return '—'

**WARN-03：formatDuration() 三個 View 重複定義**
- 建議提取為 src/utils/formatDuration.js

---

## 13. 最終判定

```
NO-GO
```

**原因：BUG-01（stores/reporting.js response 解構錯誤）是必須修復的 blocker。**

修復內容僅需修改 reporting.js 的 3 個 action，共約 6 行。
修復後所有其他審計項目均為 PASS，可立即進入 UI 驗收。
WARN-01/02/03 為輕度問題，可在驗收後處理。

---

*Audit completed — 2026-03-14*
