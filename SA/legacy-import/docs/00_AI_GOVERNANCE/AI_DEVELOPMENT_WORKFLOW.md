# AI DEVELOPMENT WORKFLOW
> **[GOVERNANCE OVERRIDE]** `docs/00_AI_GOVERNANCE/STOP_GATES.md` has the highest priority across all governance rules. All execution decisions MUST follow STOP_GATES.md. If any conflict exists between this document and STOP_GATES.md, **STOP_GATES.md takes precedence**.

# 🔴 Execution Gate（最高優先）

在任何 Step 之前，必須先完成：

> *(For reference only — overridden by STOP_GATES.md if conflict exists)*

1. 讀 CURSOR_READ_ORDER.md
2. 讀 CURSOR_EXECUTION_CONTROL.md
3. 判斷 Risk Level（LOW / MEDIUM / HIGH）
4. 回報：
   - Risk Level
   - 是否需要停止 frontend dev server
   - 修改計畫

❌ 未經確認：
禁止進入 Step 3 Implementation

---

# 標準開發流程（強制）

1. Step 0 — Confirm Position
2. Step 1 — Spec / Planning
3. Step 2 — Pre-Execution
4. Step 3 — Implementation
5. Step 4 — Audit
6. Step 5 — QA
7. Step 6 — Close

> **⚠️ 每次開始任何 WP 前必讀本文件**
> 本文件定義 Attendance 專案中 Cursor / GPT / Claude 協作開發的標準流程。
> 所有 WP 必須遵循相同步驟，不得跳步驟、亂重構、亂跳 WP。

**建立日期：** 2026-03-14
**適用對象：** Cursor / GPT / Claude AI sessions
**狀態：** ✅ ACTIVE

---

## 1. Purpose（文件目的）

本文件為 Attendance 專案的 AI 開發標準流程文件，目的如下：

1. **固定協作開發流程** — 每個 WP 都走相同的步驟，不因 AI 不同而流程不同
2. **定義完整開發節奏** — 從 Spec → Pre-Execution → 實作 → Audit → QA → 結案
3. **防止 AI 跳步驟** — 規劃未完成不得直接開工；audit 未完成不得驗收
4. **防止 AI 亂跳 WP** — 當前 WP 未完成，不得開始下一個
5. **防止 AI 亂重構** — 沒有明確 WP 授權，不得修改 protected core
6. **讓後續所有 AI session 遵循相同流程** — 任何 AI 接手都能從本文件理解工作方式

### 本文件與其他文件的關係

| 文件 | 角色 |
|------|------|
| `AI_DEVELOPMENT_WORKFLOW.md`（本文件）| **流程規範** — 定義每個 WP 如何執行 |
| `ATTENDANCE_DEVELOPMENT_ROADMAP.md` | **順序規範** — 定義 WP 順序與當前位置 |
| `ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md` | **架構規範** — 定義模組位置與分層 |
| `CURSOR_DEVELOPMENT_RULES.md` | **規則清單** — 定義禁止事項 |
| `NEXT_WP_TICKET.md` | **當前工作** — 定義現在要做什麼 |
| `GATE_PROGRESS_TRACKER.md` | **進度追蹤** — 記錄各 WP 完成狀態 |

---

## 2. Required Pre-Read（必讀文件）

> ⛔ **未完成以下所有文件的閱讀，禁止直接開始任何開發工作。**

每次開始任何 WP 前，AI / Cursor **必須先讀完**以下文件：

### 必讀清單（依優先順序）

| 順序 | 文件 | 目的 |
|------|------|------|
| 1 | `docs/AI_CONTEXT.md` | 系統概覽、當前狀態、protected core 提醒 |
| 2 | `docs/ATTENDANCE_DEVELOPMENT_ROADMAP.md` | 確認當前 WP、下一個 WP、WP 順序 |
| 3 | `docs/ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md` | 確認模組位置、分層規則、protected core 檔案 |
| 4 | `docs/CURSOR_DEVELOPMENT_RULES.md` | 確認禁止事項與強制規則 |
| 5 | `docs/NEXT_WP_TICKET.md` | 確認當前 WP 詳細內容與 scope |
| 6 | `docs/GATE_PROGRESS_TRACKER.md` | 確認整體進度與各 WP 狀態 |

### 閱讀後必須能回答的問題

讀完上述文件後，AI 必須能明確回答：

```
1. Current WP 是什麼？狀態是什麼？
2. 本輪 scope 包含哪些？out of scope 是什麼？
3. 有哪些 protected core 檔案不能動？
4. 依賴的 WP 是否已完成？
5. 這次任務是：規劃 / 實作 / 修 bug / QA，哪一種？
```

若無法回答以上問題，必須先補讀相關文件，再開始工作。

---

## 3. Standard WP Flow（標準 WP 開發流程）

每個 WP 必須依照以下 6 個步驟執行，**不得跳步驟**。

---

### Step 0 — Confirm Current Position（確認當前位置）

**目的：** 確保 AI 知道現在在哪，避免做錯事。

**必須確認：**

```
✅ Current WP：從 ATTENDANCE_DEVELOPMENT_ROADMAP.md 第 5 節讀取
✅ Current Phase：本輪是 規劃 / 實作 / QA / 結案 哪個階段
✅ Next WP：下一個 WP 是什麼（但本輪不做）
✅ Scope：本輪要做什麼
✅ Out of Scope：本輪明確不做什麼
✅ Dependencies：前置 WP 是否已 COMPLETE
```

**輸出：** 在 session 開始時口頭確認，或建立 Confirm 清單。

**禁止：**
- 不得在未確認 current WP 的情況下直接開始寫 code
- 不得假設 scope，必須從 NEXT_WP_TICKET.md 讀取

---

### Step 1 — Spec / Planning（規劃）

**目的：** 在動手前完整理解需求，避免實作方向錯誤。

**必須完成：**

```
✅ 需求整理：確認 user story / acceptance criteria
✅ API 盤點：哪些 endpoint 需要新增 / 修改 / 不得碰
✅ UI 盤點：哪些 views / components 需要新增 / 修改
✅ Data Model 盤點：是否需要新 migration / 是否可重用現有 table
✅ Changeset Plan：列出「要新增的檔案」與「要修改的檔案」
✅ 風險盤點：是否有 protected core 衝突、migration 影響、runtime 問題
✅ Out of Scope 明確化：明確列出本輪不做的項目
```

**輸出文件（建議）：**
- `docs/WP-[ID]_IMPLEMENTATION_PLAN.md`
- `docs/WP-[ID]_CHANGESET_PLAN.md`（若規模較大）

**禁止：**
- 不得在規劃未完成的情況下直接開始實作
- 不得在規劃階段修改任何程式碼

---

### Step 2 — Pre-Execution Report（執行前報告）

**目的：** 最後一次確認，確保實作前已知道所有影響範圍。

**必須確認：**

```
✅ Files to Add：本次要新增哪些檔案
✅ Files to Modify：本次要修改哪些檔案
✅ Files Forbidden：本次絕對不可碰的檔案（protected core）
✅ Impact Assessment：修改是否影響現有功能
✅ Migration Impact：是否需要新 migration
✅ Runtime Risk：是否有 runtime reload / deployment 風險
✅ Go / No-Go 決定：確認可以開始實作
```

**輸出文件（建議）：**
- `docs/WP-[ID]_PRE_EXECUTION_REPORT.md`

**禁止：**
- 不得在 Pre-Execution Report 中出現 No-Go 條件卻繼續實作
- 不得跳過此步驟直接進入實作

---

### Step 3 — Implementation（實作）

**目的：** 按照 Step 1-2 定義的 scope 實作，不多不少。

**實作順序（依 CURSOR_DEVELOPMENT_RULES.md §10）：**

```
Spec（已完成）
  → API Contract 確認
  → Backend Implementation
  → Frontend Integration
  → Test
  → Docs
```

**必須遵守：**

```
✅ 只改 scope 內的檔案
✅ 不改 protected core（除非有明確 WP 授權）
✅ 每次修改盡量小（targeted changes，避免大重構）
✅ Backend 先於 Frontend（Frontend 依賴 Backend API）
✅ 若 API response 有 interceptor unwrap，Frontend 不可多取 .data
✅ 所有 query 必須含 company_id（tenant isolation）
✅ 所有 datetime 傳輸必須帶 timezone（ISO 8601 with tz）
```

**禁止：**
- 不得順手做下一個 WP 的功能
- 不得重構 Punch / Session / Policy core
- 不得因為「覺得更好」就修改現有可運作的邏輯
- 不得在 Backend 未上線的情況下先做 Frontend

---

### Step 4 — Audit / Safety Check（審查）

**目的：** 在 QA 之前，確認實作符合規範，沒有破壞任何現有功能。

**必須檢查：**

```
✅ Touched Files Review：確認只動了 scope 內的檔案
✅ Protected Core Check：確認沒有修改 protected core
✅ API Contract Check：Frontend 呼叫的 endpoint / 參數與 Backend 一致
✅ Response Unwrap Check：確認 client.js interceptor 與 store 的解構方式一致
✅ Tenant Isolation Check：所有 query 確認有 WHERE company_id
✅ Timezone Check：datetime 傳輸確認帶 timezone
✅ Null Handling Check：nullable 欄位在 UI 有適當顯示（不顯示 undefined）
✅ Runtime Risk Check：是否需要重啟服務 / reload
✅ Migration Check：若有新 migration，確認 chain 無分叉
```

**輸出文件（建議）：**
- `docs/WP-[ID]_IMPLEMENTATION_AUDIT.md`

**禁止：**
- 不得跳過 audit 直接進 QA
- 不得在 audit 發現問題後繼續驗收

---

### Step 5 — QA / Acceptance（驗收）

**目的：** 確認實作結果符合驗收標準，且使用者體驗正確。

**驗收類型：**

```
Static Verification（靜態驗證）
  ✅ code review：邏輯正確性
  ✅ OpenAPI 驗證：endpoint 出現在 /docs
  ✅ schema 一致性確認

Runtime Verification（執行時驗證）
  ✅ API 實際呼叫並回傳正確資料
  ✅ 錯誤碼正確（403 / 404 / 422 情境）
  ✅ Tenant isolation 驗證（跨 company_id 無法取得資料）
  ✅ 服務確認已 reload / 重啟（若有 code 更新）

UI / Manual QA（手動驗收）
  ✅ 三種 state 確認：loading / empty / error
  ✅ 正常資料顯示確認
  ✅ 篩選 / 分頁功能驗證
  ✅ 不同角色權限確認（admin / manager / employee）
  ✅ 日期 / 時長格式顯示一致
  ✅ null 值顯示「—」或「進行中」等適當文字
```

**輸出文件（建議）：**
- `docs/WP-[ID]_ACCEPTANCE_REPORT.md`

**禁止：**
- 不得在 runtime 未驗證的情況下宣告 COMPLETE
- 不得在 error / empty state 未驗收的情況下宣告 UI 完成

---

### Step 6 — Close WP（結案）

**目的：** 正式結束本 WP，為下一個 WP 做準備。

**必須完成：**

```
✅ 更新 docs/NEXT_WP_TICKET.md
   - 當前 WP 標記為 COMPLETE
   - 下一個 WP 更新為 current
   - 每次完成 WP / phase / fix 後必須同步更新（不可延後到下次補）

⚠️ 禁止只改 code 不更新當前票據狀態（至少必須更新 NEXT_WP_TICKET.md）

✅ 交付回報必填欄位
   - `NEXT_WP_TICKET.md updated: YES/NO`

✅ 更新 docs/GATE_PROGRESS_TRACKER.md
   - WP 狀態 → COMPLETE
   - 完成日期記錄
   - deliverables 記錄

✅ 更新 docs/ATTENDANCE_DEVELOPMENT_ROADMAP.md
   - 第 2 節狀態表更新
   - 第 5 節 Current Position Marker 更新

✅ 更新 docs/WORKSTREAM_STATUS_LEDGER.md
   - 新增 WP 完成記錄段落

✅ Git commit
   - 格式見第 8 節

✅ Git tag（若為里程碑 WP）
   - 格式見第 8 節

✅ 確認下一個 WP 的前置條件已滿足
```

**禁止：**
- 不得在文件未更新的情況下宣告結案
- 不得在尚有未解決 bug 的情況下宣告結案

---

## 4. Development Flow Diagram（開發流程圖）

```
┌─────────────────────────────────────────────────────────────┐
│                    WP 開始前必讀文件                         │
│  AI_CONTEXT → ROADMAP → ARCH_MAP → RULES → NEXT_WP_TICKET  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │  Step 0          │
              │  Confirm Position│  ← 確認 Current WP / Phase / Scope
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │  Step 1          │
              │  Spec / Planning │  ← 需求、API、UI、Data Model、Changeset
              │  （不動 code）   │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │  Step 2          │
              │  Pre-Execution   │  ← Files to add/modify/forbid、Go/No-Go
              │  Report          │
              └────────┬─────────┘
                       │
                  Go ──┤── No-Go → 回到 Step 1
                       │
                       ▼
              ┌──────────────────┐
              │  Step 3          │
              │  Implementation  │  ← Backend → Frontend → Test
              │                  │    僅改 scope 內檔案
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │  Step 4          │
              │  Audit /         │  ← Touched files、API contract、
              │  Safety Check    │    tenant isolation、timezone、null
              └────────┬─────────┘
                       │
              Pass ────┤── Fail → 回到 Step 3 修復
                       │
                       ▼
              ┌──────────────────┐
              │  Step 5          │
              │  QA / Acceptance │  ← Static + Runtime + Manual QA
              │                  │    error/empty/loading state
              └────────┬─────────┘
                       │
              Pass ────┤── Fail → 回到 Step 3/4 修復
                       │
                       ▼
              ┌──────────────────┐
              │  Step 6          │
              │  Close WP        │  ← 更新文件、Git commit/tag
              │                  │    標記下一個 WP
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │  Next WP         │
              │  → 回到 Step 0   │
              └──────────────────┘
```

---

## 5. Rules Per Stage（各階段規則）

### 5.1 規劃階段（Step 0-2）規則

| 規則 | 說明 |
|------|------|
| 不直接開工 | 未完成 Step 0-2，不得進入 Step 3 |
| 先讀後做 | 必須讀完 Required Pre-Read 才能開始 Step 0 |
| 先盤點 API / repo / views | 不假設現況，必須實際 code scan |
| 先定 MVP / out of scope | 明確定義本輪邊界，避免 scope 漂移 |
| 規劃不動 code | Step 1-2 只產出文件，不修改任何程式碼 |
| No-Go 必須停止 | Pre-Execution Report 有 No-Go 條件，必須解決後再繼續 |

---

## 6. Common Failure Modes（常見 AI 開發失敗模式）

以下為 Attendance 專案中實際發生過或高風險的 AI 開發失敗模式。

---

### FM-01：直接開工，跳過規劃

**症狀：** AI 收到任務後立刻開始寫 code，未讀文件、未確認 scope。

**原因：** 未強制執行 Required Pre-Read 與 Step 0-2。

**正確處理：**
1. 強制先讀 Required Pre-Read 文件
2. 完成 Step 0 確認 current WP / scope
3. 完成 Step 1 Spec / Planning 後才開始實作

---

### FM-06：Backend code 在 repo，但 runtime 沒 reload

**症狀：** code 已更新，但 API 呼叫仍回傳舊結果或 404。

**原因：** 服務未重啟（uvicorn --reload 未成功偵測變更，或 systemd service 已 FAILED）。

**正確處理：**
1. 每次更新 Backend code 後，確認服務重啟
2. 用 curl 或 OpenAPI /docs 確認新 endpoint 出現
3. 若 systemd service 已 FAILED，用手動 uvicorn 重啟
4. 遇到 runtime mismatch，先查 deployment，不要直接重寫 code

**診斷步驟：**
```bash
# 確認服務是否載入最新 code
curl http://127.0.0.1:8000/openapi.json | grep '新endpoint路徑'
# 若不存在，重啟服務
kill $(pgrep -f 'uvicorn') && cd /opt/attendance-system/backend && \
  /opt/attendance-system/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

---

## 7. Git / Tag Closeout Standard（結案標準）

### 7.1 何時 Commit

```
✅ 每完成一個有意義的實作單元
✅ 每完成一個 Step（如：Step 3 Backend 完成後 commit 一次）
✅ WP 結案時最終 commit
❌ 不要累積大量修改後一次 commit
❌ 不要在 audit 失敗時 commit
```

### 7.2 Commit Message 規範

```
格式：
[WP-ID] 簡短說明（英文，動詞開頭）

範例：
[WP-11-07] Fix reporting store response unwrap in reporting.js
[WP-11-07] Add error state handling to AttendanceSessionsPage
[WP-11-07] Polish loading state for CompanySummaryPage
[WP-11-06] Complete reporting backend API (sessions/user-summary/company-summary)
[WP-C1-09] Implement OUT checkpoint API with GPS de-dup logic
```

**規則：**
- 必須包含 WP ID
- 動詞開頭（Add / Fix / Update / Remove / Implement / Complete）
- 不超過 72 字元
- 若有多項修改，使用 bullet points 在 commit body 說明

---

## 8. Final Principles（最高原則）

以下為 Attendance 專案 AI 協作開發的最高規則。任何流程和規則都必須符合這幾条原則。

### P1 — 先確認位置，再動手

> 不知道 current WP 就動手 = 最大的浪費。
> 每次 session 開始，先讀 ROADMAP 第 5 節，確認位置。

### P2 — 先規劃，再實作

> 未完成 Step 1-2，不得進入 Step 3。
> 規劃階段不動 code。

### P3 — 先 audit，再驗收

> 未完成 Step 4 Audit，不得進入 Step 5 QA。
> 發現問題回到 Step 3 修復。

### P4 — 文件必須反映真實 repo 狀態

> 文件內容必須與 repo 實際狀態一致。
> 不得寫「希望完成」的狀態，只寫「已驗證」的狀態。
> 結案前必須更新所有相關文件。

### P5 — AI 是受控開發者，不是自由發溮的架構師

> AI 必須遵從：
> - Roadmap 定義的順序
> - Architecture Map 定義的層級
> - Protected Core 定義的邊界
>
> AI 不得自行：
> - 重新訓層架構
> - 自行跳到下一個 WP
> - 修改 protected core（無明確 WP 授權）

---

*本文件由 AI 依據 2026-03-14 Attendance 專案實際開發經驗建立。*
*權威基礎：CURSOR_DEVELOPMENT_RULES.md + ATTENDANCE_DEVELOPMENT_ROADMAP.md + 實際 WP 執行紀錄。*

**END OF AI_DEVELOPMENT_WORKFLOW.md**
