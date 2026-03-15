# WP_TEMPLATE.md — Work Package 標準模板

> **用途：** 本文件為 Attendance 系統所有 Work Package 的標準定義模板。
> 每個新 WP 開始前，複製本模板並填入對應內容。
> 模板設計對齊：`AI_DEVELOPMENT_WORKFLOW.md`、`CURSOR_DEVELOPMENT_RULES.md`、`ATTENDANCE_DEVELOPMENT_ROADMAP.md`。

**版本：** 1.0  
**建立日期：** 2026-03-14  
**狀態：** ACTIVE  

---

## 如何使用本模板

1. 複製整份模板，建立新檔案：`docs/WP-[ID]_IMPLEMENTATION_PLAN.md`
2. 填入所有 `[placeholder]` 欄位
3. 確認所有 Out of Scope 明確定義
4. 在 `Pre-Execution Report` 確認 Go / No-Go 後才開始實作
5. 結案時更新 `NEXT_WP_TICKET.md` 與 `GATE_PROGRESS_TRACKER.md`

**對應 AI_DEVELOPMENT_WORKFLOW.md 步驟：**

```
Step 0: Confirm Position  → 填入第 1 節 Header
Step 1: Spec / Planning   → 填入第 2~9 節
Step 2: Pre-Execution     → 填入第 10 節 Pre-Execution Checklist
Step 3: Implementation    → 依第 6 節 Files 實作
Step 4: Audit             → 依第 8 節 QA Verification 審查
Step 5: QA / Acceptance   → 依第 7 節 Acceptance Criteria 驗收
Step 6: Close WP          → 依第 12 節 Closeout Checklist 結案
```

---

## ════════════════════════════════════════
## TEMPLATE START — 複製以下內容建立新 WP
## ════════════════════════════════════════

---

# WP-XX-XX — [Work Package Title]

**Status:** PLANNED / IN PROGRESS / COMPLETE  
**Owner:** Cursor / Developer  
**Created:** YYYY-MM-DD  
**Last Updated:** YYYY-MM-DD  
**Dependencies:** [前置 WP，例如：WP-11-06 COMPLETE]

---

## 1. Goal（目標）

> 說明本 WP 的目的。必須回答三個問題：

**This WP solves:**  
[描述本 WP 解決的問題]

**Why this WP exists:**  
[說明為什麼需要這個 WP，背景與動機]

**What capability the system gains:**  
[本 WP 完成後，系統新增了什麼能力]

### Example

```
This WP solves:
  Reporting UI MVP 已存在但存在已知的 response 解構 bug（BUG-01），
  三個頁面均無法正確渲染 API 回傳資料。

Why this WP exists:
  WP-11-06 Reporting Backend 已 COMPLETE，UI MVP 功能可用但品質不足，
  需要 polish、QA 與 error/empty/loading state 驗收後才能正式上線。

What capability the system gains:
  完整可用的 Reporting UI，三頁均通過 QA 驗收，
  可供主管與員工查詢出勤統計報表。
```

---

## 2. Scope（範圍）

> 明確定義本 WP **包含**的工作項目。

**Scope:**

- [ ] [工作項目 1]
- [ ] [工作項目 2]
- [ ] [工作項目 3]

### Example

```
Scope:
  - 修復 BUG-01：stores/reporting.js response 解構錯誤
  - 手動 QA 三頁 Reporting UI（Sessions / UserSummary / CompanySummary）
  - Error state 驗收：API 錯誤 → 使用者可見訊息
  - Empty state 驗收：無資料 → 適當空狀態顯示
  - Loading state polish
  - 日期 / 時長格式顯示一致性確認
  - 篩選 UX 確認（DateRangeFilter / MonthPicker）
```

---

## 3. Out of Scope（範圍外）

> ⚠️ **必須明確列出本 WP 不做的事，防止 scope 漂移。**

**Out of scope:**

- [不做的項目 1]
- [不做的項目 2]
- [不做的項目 3]

### Example

```
Out of scope:
  - 重建 Reporting Backend（WP-11-06 已 COMPLETE，不可重做）
  - 從零設計 Reporting UI（MVP 已存在）
  - 新增報表類型（未來 WP）
  - CSV / PDF 匯出
  - Leave Request UI（WP-11-08 範疇）
  - Shift / Schedule UI（WP-11-09 範疇）
  - 修改任何 protected core 檔案
```

---

## 4. Architecture Impact（架構影響）

> 描述本 WP 影響系統哪些部分。依層級分類。

### Frontend

```
[受影響的 Vue components / views]
例如：
  frontend/src/views/reports/AttendanceSessionsPage.vue
  frontend/src/stores/reporting.js
```

### Backend

```
[受影響的 Python 模組 / endpoint]
例如：
  backend/app/modules/attendance/api.py
  backend/app/modules/attendance/repo.py
```

### Database

```
[是否需要 migration]
例如：
  無 migration（本 WP 不改 DB schema）
  或：新增 migration 009_wp_11_08
```

### Shared Components

```
[受影響的共用元件]
例如：
  frontend/src/components/StatusBadge.vue
  frontend/src/components/PaginationBar.vue
```

### No Impact

```
[確認不受影響的核心系統]
例如：
  Punch Engine（service.py / Home.vue）— 無影響
  JWT / Auth（auth.js / jwt.py）— 無影響
  Migration chain — 無影響
```

---

## 5. Files Expected to Change（預計修改檔案）

> ⚠️ **Step 3 實作時，只能修改此清單內的檔案。**

### Files to ADD（新增）

```
[列出所有要新增的檔案]
例如：
  frontend/src/views/leave/LeaveRequestPage.vue    （新增）
  frontend/src/stores/leave.js                      （新增）
  docs/WP-11-08_ACCEPTANCE_REPORT.md               （新增）
```

### Files to MODIFY（修改）

```
[列出所有要修改的既有檔案]
例如：
  frontend/src/stores/reporting.js     （修改 fetchSessions 解構邏輯）
  frontend/src/router/index.js         （新增 leave 路由）
```

### Files FORBIDDEN（禁止觸碰）

> 以下為 protected core，**本 WP 不得修改**：

```
backend/app/modules/attendance/service.py
backend/app/modules/attendance/models.py
backend/app/modules/attendance/policy_engine.py
frontend/src/stores/attendance.js
frontend/src/views/Home.vue
frontend/src/api/client.js
backend/app/core/security/jwt.py
backend/app/core/tenant_context.py
backend/app/core/dependencies.py
[其他本 WP 特定的禁止修改檔案]
```

---

## 6. Acceptance Criteria（驗收標準）

> 定義本 WP 何時算完成。每一條必須是可驗證的事實，不是主觀描述。

### Functional

- [ ] [功能驗收條件 1]
- [ ] [功能驗收條件 2]
- [ ] [功能驗收條件 3]

### UI / UX

- [ ] Loading state：資料載入中顯示 spinner 或 skeleton
- [ ] Empty state：無資料時顯示「[適當文字]」
- [ ] Error state：API 錯誤時顯示使用者可見的錯誤訊息（非空白）
- [ ] Null 欄位顯示「—」而非 undefined 或空字串

### Technical

- [ ] Tenant isolation：所有查詢含 WHERE company_id
- [ ] Timezone：所有 datetime 傳輸含 timezone（ISO 8601 with tz）
- [ ] Response unwrap：store 不對 API response 多取 .data（client.js interceptor 已 unwrap）
- [ ] OpenAPI `/docs` 顯示所有新增 endpoint（若有）

### Example

```
Functional:
  - 員工可查詢自己的 sessions 列表（日期篩選、status 篩選）
  - 主管可查詢公司出勤統計摘要
  - 分頁正確（limit/offset，顯示 total）

UI:
  - Loading：顯示 spinner
  - Empty：顯示「本期間無出勤記錄」
  - Error：顯示 sessionsError 訊息

Technical:
  - 所有查詢含 WHERE company_id
  - datetime 傳輸含 Asia/Taipei offset
```

---

## 7. QA Verification（QA 驗證清單）

> 定義如何測試本 WP 的功能。分靜態、Runtime 與手動三類。

### Static Verification（靜態驗證）

- [ ] OpenAPI `/docs` 確認新 endpoint 存在（若有）
- [ ] Code review：邏輯正確性
- [ ] Schema 一致性確認（Frontend 使用欄位與 Backend response 一致）
- [ ] Audit 通過（見第 10 節）

### Runtime Verification（執行時驗證）

- [ ] 實際 curl API 確認回傳正確資料
- [ ] 錯誤碼正確：403（無授權）/ 404（找不到）/ 422（驗證失敗）
- [ ] Tenant isolation：跨 company_id 無法取得他人資料
- [ ] 服務已 reload / 重啟（若有 Backend code 更新）

### Manual / Browser QA（手動驗收）

- [ ] 