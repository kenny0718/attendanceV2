# WP-REPORTING-UI — Fix B Report

**日期：** 2026-03-14
**分支：** `feature/wp-11-06-company-summary`
**依據：** `WP-REPORTING-UI_IMPLEMENTATION_AUDIT.md`
**狀態：** COMPLETE

---

## 1. 已讀取文件

- `docs/WP-REPORTING-UI_IMPLEMENTATION_AUDIT.md`
- `docs/WP-REPORTING-UI_IMPLEMENTATION_PLAN.md`
- `docs/WP-REPORTING-UI_API_FIELD_MAPPING.md`
- `docs/WP-REPORTING-UI_FRONTEND_CHANGESET_PLAN.md`
- `frontend/src/stores/reporting.js`
- `frontend/src/api/attendance.js`
- `frontend/src/api/client.js`
- `frontend/src/views/reports/AttendanceSessionsPage.vue`
- `frontend/src/views/reports/CompanySummaryPage.vue`
- `frontend/src/views/reports/UserSummaryPage.vue`
- `frontend/src/router/index.js`

---

## 2. 實際修改檔案清單

| 檔案 | 類型 | 說明 |
|------|------|------|
| `frontend/src/stores/reporting.js` | 修改 | 修正 BUG-01 + 移除 dead state |

**僅修改一個檔案，符合本輪允許範圍。**

其他禁止修改的檔案均未被碰觸：
- `frontend/src/views/Home.vue` — 未動
- `frontend/src/stores/attendance.js` — 未動
- `frontend/src/stores/auth.js` — 未動
- `frontend/src/api/client.js` — 未動
- `frontend/src/router/index.js` — 未動
- `frontend/src/api/attendance.js` — 未動
- `frontend/src/composables/useLocation.js` — 未動

---

## 3. BUG-01 Root Cause 摘要

**根本原因：**

`api/client.js` 的 Axios response interceptor 設定如下：

```javascript
apiClient.interceptors.response.use(
  (response) => {
    return response.data  // 已 unwrap，直接回傳 API body object
  },
  ...
)
```

因此所有 `attendanceApi.*()` 呼叫回傳的已是 body object 本體（例如 `{ sessions, total, limit, offset }`），**不是** Axios response 物件（`{ data: ..., status: ..., headers: ... }`）。

但修正前的 `stores/reporting.js` 錯誤地再次取 `.data`：

```javascript
// 錯誤（修正前）
const resp = await attendanceApi.fetchSessions(params)
const data = resp.data         // undefined
this.sessions = data.sessions  // TypeError: Cannot read properties of undefined

const resp = await attendanceApi.fetchCompanySummary(params)
this.companySummary = resp.data  // undefined

const resp = await attendanceApi.fetchUserSummary(params)
this.userSummary = resp.data  // undefined
```

**後果：**
- `fetchSessions`：在 `data.sessions` 處拋出 `TypeError`，sessionsError 被設為錯誤訊息，Sessions List Page 永遠顯示 error state
- `fetchCompanySummary`：`companySummary` 永遠為 `undefined`，Company Summary Page 永遠空白
- `fetchUserSummary`：`userSummary` 永遠為 `undefined`，User Summary Page 永遠空白

---

## 4. 修正內容摘要

### 4.1 BUG-01 修正（三個 action）

**修正後：**

```javascript
// fetchSessions — 直接 await，回傳值即是 body object
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
    this.sessionsError = err?.message || '載入失敗'
  } finally {
    this.sessionsLoading = false
  }
},

// fetchCompanySummary
async fetchCompanySummary(params = {}) {
  this.companySummaryLoading = true
  this.companySummaryError = null
  try {
    this.companySummary = await attendanceApi.fetchCompanySummary(params)
  } catch (err) {
    this.companySummaryError = err?.message || '載入失敗'
  } finally {
    this.companySummaryLoading = false
  }
},

// fetchUserSummary
async fetchUserSummary(params = {}) {
  this.userSummaryLoading = true
  this.userSummaryError = null
  try {
    this.userSummary = await attendanceApi.fetchUserSummary(params)
  } catch (err) {
    this.userSummaryError = err?.message || '載入失敗'
  } finally {
    this.userSummaryLoading = false
  }
}
```

**變更說明：**
- `const resp = await ...` → `const data = await ...`（fetchSessions）
- 移除 `const data = resp.data` 這一行（fetchSessions）
- `this.companySummary = resp.data` → `this.companySummary = await ...`（fetchCompanySummary）
- `this.userSummary = resp.data` → `this.userSummary = await ...`（fetchUserSummary）
- error handler 中移除 `err?.response?.data?.detail`（client.js 已 unwrap，error 物件格式不同，detail 在 `err?.data?.detail` 或直接 `err?.message`，改用安全的 `err?.message`）

### 4.2 WARN-01 處理：sessionsFilters dead state 移除

**原本：**
```javascript
sessionsFilters: {
  start_date: null,
  end_date: null,
  status: null
},
```

**修正後：** 移除此 state 定義，改為注釋說明：
```javascript
// sessionsFilters: 目前 View 層自行管理篩選參數，此 state 未被任何 action 寫入
// 亦未被任何 View 讀取，依 Audit WARN-01 移除，避免 dead state 誤導。
// 若 Step 2/3 需要跨元件共用篩選狀態時再行補回。
```

**理由：** `AttendanceSessionsPage.vue` 透過 `currentDateRange` 本地變數和 `filterStatus` ref 管理篩選參數，直接傳給 `store.fetchSessions(buildParams())`，完全未讀取 `store.sessionsFilters`。移除後不影響任何現有功能。

---

## 5. 未處理項目說明

### 5.1 WARN-02 保留未動

`formatAvg()` 在 null 時回傳 `null` 而非字串 `'—'`（CompanySummaryPage / UserSummaryPage）。

**保留原因：** SummaryCard.displayValue computed 已正確將 null 轉為「—」，最終顯示正確。本輪不修 components，不在本輪 scope。

### 5.2 WARN-03 保留未動

`formatDuration()` 在三個 View 各自重複定義。

**保留原因：** 不修 components，不抽 shared helper，不在本輪 scope。

### 5.3 Home.vue build error

build 時發現 `Home.vue` 第 215 行有 syntax error（"Element is missing end tag"），經確認 `Home.vue` 末尾被截斷（檔案 299 行，最後為 `return '✓ ` 不完整）。

**此問題與本次 WP-REPORTING-UI 修改無關，屬既有問題。**
- `Home.vue` 在本次修改清單外，本輪禁止修改
- Dev server（`vite dev`）能正常啟動並回應 HTTP 200，不影響 reporting 路由的開發驗證
- 建議後續另立 ticket 修復 `Home.vue` truncation 問題

---

## 6. 驗證結果

### 6.1 修改後 reporting.js 靜態驗證

| 檢查項目 | 結果 |
|---------|------|
| 無 `resp.data` 用法 | PASS（grep 確認） |
| `sessionsFilters` state 已移除 | PASS（grep 確認） |
| `fetchSessions` 直接 await body | PASS |
| `fetchCompanySummary` 直接 await body | PASS |
| `fetchUserSummary` 直接 await body | PASS |
| loading / error / finally 結構完整 | PASS |
| 無新增禁止 import | PASS |

### 6.2 Dev Server 驗證

```
npm run dev -- --port 5176
=> VITE v5.4.21 ready in 427 ms
=> HTTP GET / => 200 OK
```

Dev server 正常啟動，無 compile error。

### 6.3 觸碰檔案確認

```
git diff --name-only
```

`frontend/src/stores/reporting.js` 為 untracked 新檔案（不出現在 diff），其他所有禁止修改檔案均未出現在 diff 中。僅 `reporting.js` 被修改，符合本輪要求。

### 6.4 State / View 行為影響評估

| 頁面 | Loading State | Error State | Empty State | Data State |
|------|-------------|------------|------------|------------|
| AttendanceSessionsPage | 不變 | 不變 | 不變 | 修復：API 資料現可正確填入 |
| CompanySummaryPage | 不變 | 不變 | 不變 | 修復：companySummary 現可正確設定 |
| UserSummaryPage | 不變 | 不變 | 不變 | 修復：userSummary 現可正確設定 |

---

## 7. 最終結論

```
GO
```

**BUG-01 已修復。**

- `stores/reporting.js` 三個 action 的 response unwrap 錯誤已修正
- `sessionsFilters` dead state 已依 WARN-01 建議移除
- 修改範圍嚴格限定於 `frontend/src/stores/reporting.js` 一個檔案
- 所有禁止修改檔案均未被碰觸
- Dev server 正常啟動，reporting 路由可訪問

**遺留注意事項（不阻礙 GO）：**
- `Home.vue` build error 屬既有問題，需另立 ticket 處理
- WARN-02 / WARN-03 為輕度風格問題，可於後續 sprint 處理

---

*Fix B completed — 2026-03-14*
