# WP-S1-07 — Schedule Frontend Execution Plan

**文件類型:** Execution Plan（執行順序控制文件）  
**建立日期:** 2026-03-19  
**目錄位置:** `docs/03_WP_CONTROL/`（WP 控制文件，非完成報告）  
**狀態:** PLAN — 尚未開始實作  

> ⚠️ 本文件是 **執行計畫**，不是 completion report。  
> 任何 WP-S1-07 的 completion report 或 status audit 屬於 `docs/02_DEVELOPMENT_STATUS/`，  
> 不可將本文件誤放或合併至該目錄。

---

## 1. Objective

WP-S1-07 是 Schedule 模組的 **Frontend（Vue）開發票**。

目標：
- 建立 `frontend/src/modules/schedule/` 或對應 views/stores/api 前端模組
- 串接已完成的 Schedule Backend API（WP-S1-01 ~ WP-S1-06）
- 實現 ShiftTemplate 管理頁面（list / create / update / activate）
- 實現 ShiftAssignment 管理頁面（list / create / cancel）
- 透過真實 JWT + schedule.core feature gate 進行前端驗證

本文件固定：
- 各 phase 的執行順序
- 每 phase 允許修改的檔案範圍
- 每 phase 的驗證標準
- 停止條件
- 文件治理規則

---

## 2. Current Baseline

### 2.1 Backend 狀態（已完成）

| 項目 | 狀態 | 說明 |
|------|------|------|
| WP-S1-01/01A | COMPLETE | Models 定義 + 慣例對齊 |
| WP-S1-02/02B | COMPLETE | Migration 建立 + Alembic 穩定 |
| WP-S1-03 | COMPLETE | repo.py + service.py CRUD Core |
| WP-S1-04A/04B | COMPLETE | API Layer + Router mount + Feature Gate |
| WP-S1-05 | COMPLETE | Integration tests 12/12 PASS |
| WP-S1-06 | COMPLETE | Real JWT E2E 14/14 PASS |

### 2.2 Backend API 可用端點

**ShiftTemplate（6 endpoints）：**
- `POST   /api/v1/schedule/shift-templates`
- `GET    /api/v1/schedule/shift-templates`
- `GET    /api/v1/schedule/shift-templates/{id}`
- `PATCH  /api/v1/schedule/shift-templates/{id}`
- `POST   /api/v1/schedule/shift-templates/{id}/activate`
- `POST   /api/v1/schedule/shift-templates/{id}/deactivate`

**ShiftAssignment（5 endpoints）：**
- `POST   /api/v1/schedule/shift-assignments`
- `GET    /api/v1/schedule/shift-assignments`
- `GET    /api/v1/schedule/shift-assignments/{id}`
- `PATCH  /api/v1/schedule/shift-assignments/{id}`
- `POST   /api/v1/schedule/shift-assignments/{id}/cancel`

**Auth requirements：**
- `Authorization: Bearer <JWT>`（HS256，`sub` + `company_id` + `role_id`）
- `schedule.core` entitlement 必須啟用（否則 403 FEATURE_DISABLED）

### 2.3 Frontend 狀態（尚未開始）

- `frontend/src/` 結構已存在（router / stores / views / api / composables）
- 尚無 schedule 相關 Vue 元件、store、api 呼叫
- 現有前端架構風格參考：`frontend/src/views/reports/`（Reporting UI）

### 2.4 Baseline Tag

```
milestone/wp-s1-06-backend-stabilization-complete
docs-structure-stable-after-s1-06-v2
```

---

## 3. Scope Boundary

### 允許修改
- `frontend/src/` 內與 schedule 模組相關的新增檔案
- 建議新增路徑：`frontend/src/views/schedule/`、`frontend/src/stores/schedule.js`、`frontend/src/api/schedule.js`
- 若需要掛載 router，允許修改 `frontend/src/router/index.js`（最小必要）

### 禁止修改
- `backend/` 任何檔案（backend 已完成，不得為 frontend 需求修改 API）
- `frontend/src/` 內非 schedule 範圍的既有元件（不得無關 refactor）
- `docs/02_DEVELOPMENT_STATUS/` 任何檔案（非本輪任務）
- Migration / alembic / env.py
- 任何既有 WP 的 completion report

### 若 Backend 需要修正
若前端審計發現 backend contract 與預期不一致，**必須停止**，回報後另開獨立 WP 修正，不得在 WP-S1-07 內順手修改。

---

## 4. Planned Execution Phases

```
Phase 0 — Frontend Audit Only
  ↓
Phase 1 — API Connection Layer Only
  ↓
Phase 2 — Basic Page Scaffold
  ↓
Phase 3 — Data Fetch（read-only list）
  ↓
Phase 4 — Create Schedule UI
  ↓
Phase 5 — Update/Delete UI
```

每個 phase 必須通過驗證後才能進入下一階段。**不得跳 phase。**

---

## 5. Phase-by-Phase Allowed Change Scope

### Phase 0 — Frontend Audit Only

**目標：** 了解 frontend 目前架構，確認掛載點、auth flow、store 結構，不寫任何功能程式碼。

**允許：**
- 讀取 `frontend/src/` 任何現有檔案
- 讀取 `frontend/src/router/index.js`
- 讀取 `frontend/src/stores/`
- 讀取 `frontend/src/api/`
- 產出 Phase 0 Audit Summary（文字回報，不建立新檔）

**禁止：**
- 建立任何 `.vue` / `.js` 檔案
- 修改任何既有檔案
- 開始任何實作

**驗證標準：**
- 回報：router 掛載方式確認
- 回報：auth token 注入方式（axios interceptor 或 fetch header）
- 回報：store 狀態管理方式（Pinia / Vuex）
- 回報：是否有 feature gate 前端判斷機制
- 確認：schedule 前端可安全掛載的路徑

---

### Phase 1 — API Connection Layer Only

**目標：** 建立 schedule API 呼叫函式，不含 UI。

**允許新增：**
- `frontend/src/api/schedule.js`（或對應路徑）

**禁止：**
- 建立任何 `.vue` 元件
- 修改 router
- 修改 store
- 修改任何既有 api 檔案

**驗證標準：**
- `schedule.js` 內函式可被 browser console 或 unit test 呼叫
- API 回傳結構與 backend contract 一致
- Authorization header 正確注入

---

### Phase 2 — Basic Page Scaffold

**目標：** 建立最小 schedule 頁面骨架，掛入 router，可導航但無資料。

**允許新增：**
- `frontend/src/views/schedule/ScheduleTemplatePage.vue`（骨架）
- `frontend/src/views/schedule/ScheduleAssignmentPage.vue`（骨架）

**允許修改：**
- `frontend/src/router/index.js`（最小：新增 schedule 路由）

**禁止：**
- 修改非 schedule 的 views
- 修改 store
- 加入任何 API 呼叫

**驗證標準：**
- 可在瀏覽器導航至 schedule 頁面
- 頁面顯示 placeholder 內容（無錯誤）
- router 掛載正確（無 404）

---

### Phase 3 — Data Fetch（read-only list）

**目標：** 從 API 讀取資料並顯示 ShiftTemplate 列表。

**允許新增/修改：**
- `frontend/src/stores/schedule.js`（Pinia store，read actions）
- `frontend/src/views/schedule/ScheduleTemplatePage.vue`（加入 list 顯示）

**禁止：**
- 建立 create / update / delete UI
- 修改非 schedule 範圍

**驗證標準：**
- 登入後，schedule 頁面顯示 ShiftTemplate 列表
- API call 帶有正確 Authorization header
- 無 entitlement 時顯示對應錯誤（403 handling）
- 無資料時顯示 empty state

---

### Phase 4 — Create Schedule UI

**目標：** 實作建立 ShiftTemplate 和 ShiftAssignment 的表單 UI。

**允許新增/修改：**
- `frontend/src/views/schedule/ScheduleTemplatePage.vue`（加入 create form）
- `frontend/src/views/schedule/ScheduleAssignmentPage.vue`（加入 create form）
- `frontend/src/stores/schedule.js`（加入 create actions）

**禁止：**
- 修改 backend
- 修改非 schedule 範圍

**驗證標準：**
- 表單送出後 API 回傳 201
- 新增成功後列表自動更新
- 錯誤狀態（409 duplicate / 422 invalid）有對應 UI 處理

---

### Phase 5 — Update/Delete UI

**目標：** 實作更新、停用、取消功能。

**允許新增/修改：**
- 