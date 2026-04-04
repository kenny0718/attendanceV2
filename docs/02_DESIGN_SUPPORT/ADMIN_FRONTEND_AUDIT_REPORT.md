# Admin Frontend Audit Report

**建立日期：** 2026-03-23  
**審計範圍：** AdminUsersView.vue regression check + AdminOnboardingView.vue runtime mismatch  
**審計性質：** 唯讀審計，未修改任何功能檔  
**執行依據：** CURSOR_FRONTEND_SAFE_EDIT_RULES.md

---

## 1. Summary

| 項目 | 結論 |
|------|------|
| AdminUsersView.vue 工作樹狀態 | ⚠ **HIGH RISK — 確認為功能 regression，非故意簡化** |
| AdminOnboardingView.vue `loadCompanies()` | 🔴 **CRITICAL — ReferenceError，runtime 必定崩潰** |
| AdminOnboardingView.vue `role_id` 值 | 🔴 **CRITICAL — 前端送 `admin`，後端無此 role → HTTP 422** |
| AdminOnboardingView.vue error parsing 結構 | ⚠ **High — `err.data` 路徑正確，但 `loadCompanies` bug 會先觸發** |
| `frontend/src/api/admin.js` 路徑對齊 | ✅ **基本對齊，無路徑錯誤** |
| 功能檔是否被修改（本次審計）| ✅ **NO** |

---

## 2. Files Audited

| 檔案 | 審計方法 |
|------|----------|
| `frontend/src/views/admin/AdminUsersView.vue` | `git diff HEAD`、`wc -l`、grep |
| `frontend/src/views/admin/AdminOnboardingView.vue` | grep（loadCompanies / role_id / err.*）|
| `frontend/src/views/admin/AdminCompaniesView.vue` | 作為基線參照（HEAD 版本，未修改）|
| `frontend/src/views/Admin.vue` | `git diff HEAD` |
| `frontend/src/api/admin.js` | 讀取，與後端路徑對比 |
| `frontend/src/api/client.js` | 讀取 error reject 結構 |
| `backend/app/modules/tenants/api.py` | 路徑 / auth 比對 |
| `backend/app/modules/tenants/api_onboarding.py` | schema + role validation 比對 |
| `backend/app/modules/tenants/api_members.py` | member CRUD endpoint 比對 |
| `backend/app/modules/tenants/schemas_onboarding.py` | `role_id` default 值確認 |
| `docs/00_AI_GOVERNANCE/CURSOR_FRONTEND_SAFE_EDIT_RULES.md` | 安全修改規則基準 |

---

## 3. Git Integrity Findings

### 3.1 目前 git status（工作樹 vs HEAD）

```
M  docs/AI_READ_ORDER.md                              (+7  / -7  )  低風險
M  frontend/src/router/index.js                       (+7  / -7  )  低風險（S1-11E.3 修正）
M  frontend/src/views/Admin.vue                       (+4  / -4  )  低風險（icon/title 調整）
M  frontend/src/views/admin/AdminOnboardingView.vue   (+39 / -39 )  中風險（含 runtime bug）
M  frontend/src/views/admin/AdminUsersView.vue        (+22 / -378)  ⚠ HIGH RISK
?? docs/00_AI_GOVERNANCE/CURSOR_FRONTEND_SAFE_EDIT_RULES.md         新增治理文件
?? scripts/safe-edit-guard.sh                                        新增腳本
```

### 3.2 AdminUsersView.vue 行數對比

| 版本 | 行數 | 檔案大小 |
|------|------|----------|
| HEAD（git）| 643 行 | ~30,068 bytes |
| 工作樹（現行）| 303 行 | 14,416 bytes |
| **差異** | **-340 行 (-53%)** | **-15,652 bytes (-52%)** |

CURSOR_FRONTEND_SAFE_EDIT_RULES.md 規定禁止「整份覆蓋」或「根據對話內容重建整頁」。  
本次刪減幅度（-52%，三個主要功能區塊消失）**遠超安全修改範疇**，且無對應 commit 說明。

### 3.3 其他 Admin Vue 檔案完整性

| 檔案 | 大小 | template | script | style | 評估 |
|------|------|----------|--------|-------|------|
| `Admin.vue` | 6,325 bytes | ✅ | ✅ | ✅ | 正常 |
| `AdminCompaniesView.vue` | 38,817 bytes | ✅ | ✅ | ✅ | 正常（未修改）|
| `AdminOnboardingView.vue` | 21,327 bytes | ✅ | ✅ | ✅ | 結構完整，含 runtime bug |
| `AdminUsersView.vue` | 14,416 bytes | ✅ | ✅ | ✅ | 結構完整，**功能遭 regression** |

---

## 4. AdminUsersView.vue Regression Findings

### 判定：⚠ **疑似 Regression（非故意功能降級）**

下列功能區塊在 HEAD（最後 commit `7ef5029`）中存在，在工作樹中全部刪除，且無任何對應 git commit 記錄廢除原因。

### 4.1 Add Member Panel（WP-S1-10D）— 整體刪除

- **Template**：`<div class="panel add-member-panel">` 整個區塊（66 行）移除
  - 顯示名稱、Email、登入帳號、初始密碼、角色下拉選單
  - `addMemberSuccess` / `addMemberError` 訊息顯示
- **Script**：`newMember`、`addMemberLoading`、`addMemberError`、`addMemberSuccess`、`addMemberSuccessName`、`handleAddMember()` 全數移除
  - `handleAddMember()` 含 `adminApi.createCompanyMember()` API 呼叫
- **CSS**：`.add-member-body`、`.add-member-form`、`.form-row`、`.btn-add-member`、`.add-msg-*` 全數移除

### 4.2 Filter / Search Bar（S1-10F）— 整體刪除

- **Template**：`<div class="filter-bar">` 整個區塊（29 行）移除
  - 關鍵字搜尋 input、狀態篩選 select、角色篩選 select、清除篩選按鈕
- **Script**：`searchQuery`、`filterStatus`、`filterRole`、`uniqueRoles`（computed）、`filteredMembers`（computed）、`isFiltered`（computed）、`clearFilters()` 全數移除
  - `import { computed }` 已從 import 移除
- **Template 退化**：`v-for="m in filteredMembers"` 退化為 `v-for="m in members"`（篩選完全失效）
- **CSS**：`.filter-bar`、`.filter-search`、`.filter-input`、`.filter-select`、`.filter-clear`、`.cell-member`、`.cell-sub`、`.link-btn` 全數移除

### 4.3 Toggle Membership Active（S1-10C）— 整體刪除

- **Template**：「操作」欄整欄移除，啟用/停用 button 消失；`toggleError` banner 移除
- **Script**：`togglingId`、`toggleError`、`handleToggle()` 全數移除
  - `handleToggle()` 含 `adminApi.toggleMembershipActive()` API 呼叫
- **Table footer**：`filteredMembers.length / members.length` 退化為純 `members.length`
- **CSS**：`.cell-action`、`.btn-toggle`、`.btn-deactivate`、`.btn-activate`、`.btn-spinner-sm`、`.toggle-error-bar`、`.toggle-error-close` 全數移除

### 4.4 附加發現：HEAD 版本 `handleAddMember` 的 error parsing bug

HEAD 版本使用：
```javascript
const code = err?.response?.data?.detail?.code
```
`api/client.js` 的 reject 回傳結構為 `{ status, message, data }`（已包裝，非 axios 原始 response）。  
正確路徑應為 `err?.data?.detail?.code`（與 AdminOnboardingView 使用的路徑一致）。  
工作樹版本已移除此 function，但**若恢復 HEAD 功能，error parsing 需一併修正**。

### 4.5 CSS Role Badge 調整（合理，非 regression）

| HEAD | 工作樹 | 評估 |
|------|--------|------|
| `.role-admin` | 移除 | `admin` 不是系統有效 role，移除合理 |
| `.role-manager` | 移除 | `manager` 不是系統有效 role，移除合理 |
| （無）| `.role-hr_manager` | 新增，對齊系統 role 名稱，合理 |
| （無）| `.role-super_admin` | 新增，對齊系統 role 名稱，合理 |

**此部分為唯一可確認為「故意修改」的內容。**

---

## 5. Onboarding Runtime Mismatch Findings

### 5.1 `loadCompanies()` ReferenceError — 🔴 CRITICAL

| 項目 | 內容 |
|------|------|
| 檔案 | `frontend/src/views/admin/AdminOnboardingView.vue` |
| 位置 | 第 175 行 |
| 程式碼 | `await loadCompanies()` |
| 問題 | `loadCompanies` **未在此檔案定義**（grep 確認無任何定義）|
| 此函式所在 | 只存在於 `AdminCompaniesView.vue`，屬不同頁面局部函式 |
| Runtime 影響 | `handleOnboard()` 的 `try` 區塊執行到此行時拋出 `ReferenceError` |
| 使用者可見效果 | `obSuccess` 雖在第 173 行設定，但 `loadCompanies()` 在第 175 行拋出 ReferenceError，被 `catch` 捕獲，`obError` 被覆寫為錯誤訊息，**成功畫面不顯示，UI 顯示「Onboarding 失敗」** |
| 資料層影響 | Onboarding 資料（公司 + 使用者 + Membership）實際上**已成功建立**於資料庫，但 UI 不顯示成功 |
| 嚴重程度 | 🔴 **Critical — 每次 Onboarding 提交成功後 UI 一定顯示錯誤** |

### 5.2 `role_id` 值不一致 — 🔴 CRITICAL

| 項目 | 內容 |
|------|------|
| 前端預設值 | `role_id: 'admin'`（第 127 行 reactive 初始化）|
| 前端 reset 值 | `obForm.initial_user.role_id = 'admin'`（第 224 行）|
| 前端 select option | `<option value="admin">admin（公司管理員）</option>`（第 101 行）|
| 後端 schema 預設 | `role_id: str = Field(default="company_admin", ...)` |
| 後端 role 驗證 | `db.query(RoleModel).filter(RoleModel.id == request.role_id).first()` → 找不到則 HTTP 422 `INVALID_ROLE` |
| 系統有效 role 清單 | `employee`、`company_admin`、`hr_manager`、`super_admin` |
| **`admin` 是否為有效 role** | **否** — `admin` 不存在於系統 roles 資料表 |
| 影響 | 使用者送出 Onboarding 表單時，後端回傳 HTTP 422 `INVALID_ROLE`，Onboarding **一定失敗** |
| 嚴重程度 | 🔴 **Critical — 所有從頁面發出的 Onboarding 請求都會因 role 驗證失敗而被後端拒絕** |

### 5.3 Error Parsing 結構 — ⚠ High（目前正確，但需確認）

`AdminOnboardingView.vue` 的 error 解析使用：
```javascript
const detail = err.data?.detail
const code = detail?.code
```
`api/client.js` 的 error reject 結構為：
```javascript
return Promise.reject({ status, message: data?.detail || data?.message || '請求失敗', data })
```
- `err.data` → axios `error.response.data`（原始 response body）✅ 正確
- `err.data?.detail` → FastAPI 的 detail 物件 ✅ 正確
- `err.status` → HTTP status code ✅ 正確
- **整體 error parsing 路徑正確**，與後端 `{ code, message }` 結構對齊

注意：此 parsing 因 `loadCompanies()` bug（5.1）在多數情況下不會被執行到。

### 5.4 Onboarding Timezone 選項縮減

- HEAD 版本：提供 9 個 timezone 選項（UTC、Asia/Taipei、Tokyo、Shanghai 等）
- 工作樹版本：僅剩 2 個（UTC、Asia/Taipei）
- 後端 `CreateCompanyRequest` 接受任意 `timezone: str`（無 enum 限制）
- **評估：低風險，縮減為合理範圍，與系統 Asia/Taipei 規範一致**

---

## 6. API Alignment Findings

### 6.1 `frontend/src/api/admin.js` 路徑對比後端

| 前端呼叫 | 後端 Endpoint | 對齊狀態 |
|----------|--------------|----------|
| `GET /admin/companies` | `GET /api/admin/companies` | ✅ 對齊（baseURL = `/api`）|
| `POST /admin/companies` | `POST /api/admin/companies` | ✅ 對齊 |
| `GET /admin/companies/{id}` | `GET /api/admin/companies/{company_id}` | ✅ 對齊 |
| `PATCH /admin/companies/{id}` | `PATCH /api/admin/companies/{company_id}` | ✅ 對齊 |
| `POST /admin/companies/onboarding` | `POST /api/admin/companies/onboarding` | ✅ 對齊 |
| `GET /admin/companies/{id}/members` | `GET /api/admin/companies/{company_id}/members` | ✅ 對齊 |
| `POST /admin/companies/{id}/members` | `POST /api/admin/companies/{company_id}/members` | ✅ 對齊 |
| `PATCH /admin/companies/{id}/members/{mid}/active` | `PATCH /api/admin/companies/{id}/members/{membership_id}/active` | ✅ 對齊 |

### 6.2 Auth / Role Guard 對齊

| Endpoint | 後端要求 | Router Guard | 對齊狀態 |
|----------|----------|-------------|----------|
| 所有 `/admin/*` 路由 | JWT Bearer Token | `requiresAdminAccess: true` → `isSuperAdmin \|\| isAdminAccess` | ✅ 對齊 |
| `POST /admin/companies`（建立公司）| `is_super_admin()` only | 路由 guard 允許 `company_admin`/`hr_manager` 進入頁面 | ⚠ 前端 guard 比後端寬鬆（company_admin 可進入頁面但 API 會被後端拒絕）|
| `POST /admin/companies/onboarding` | `is_super_admin()` only | 路由 guard 允許 `company_admin`/`hr_manager` 進入頁面 | ⚠ 同上 |

### 6.3 `createCompany` Payload 對比

前端（`AdminCompaniesView.vue handleCreate`）：
```javascript
await adminApi.createCompany({ id: form.id, name: form.name, timezone: 'Asia/Taipei' })
```
後端 `CreateCompanyRequest`：`id`（必填）、`name`（必填）、`timezone`（選填，預設 UTC）
- ✅ 欄位完全對齊，timezone 固定為 `Asia/Taipei` 符合規範

### 6.4 `updateCompany` Payload 對比

前端（`AdminCompaniesView.vue handleUpdate`）：`{ name, timezone }`  
前端（`handleToggleActive`）：`{ is_active: target }`  
後端 `UpdateCompanyRequest`：`name`（Optional）、`timezone`（Optional）、`is_active`（Optional）
- ✅ 完全對齊

### 6.5 `createCompanyMember` Payload 對比

前端（`AdminCompaniesView.vue handleAddMember`）：
```javascript
{ display_name, email, login_username, password, role_id }
```
後端 `CreateMemberRequest`：`display_name`（必填）、`email`（Optional）、`login_username`（必填）、`password`（必填，≥6）、`role_id`（預設 `employee`）
- ✅ 完全對齊

---

## 7. Risk Classification

### 🔴 Critical

| # | 問題 | 檔案 | 影響 |
|---|------|------|------|
| C1 | `loadCompanies()` ReferenceError | `AdminOnboardingView.vue:175` | Onboarding 成功後 UI 顯示失敗，每次觸發 |
| C2 | `role_id: 'admin'` 後端不接受 | `AdminOnboardingView.vue:101,127,224` | 所有 Onboarding 請求被後端以 HTTP 422 拒絕 |

### ⚠ High

| # | 問題 | 檔案 | 影響 |
|---|------|------|------|
| H1 | AdminUsersView.vue 功能 regression（Add Member、Filter、Toggle 全刪）| `AdminUsersView.vue`（工作樹）| WP-S1-10C/10D/10F 已完成功能全部失效 |
| H2 | HEAD 版 `handleAddMember` error parsing 路徑錯誤（`err.response.data` 而非 `err.data`）| HEAD `AdminUsersView.vue:380` | Add Member 錯誤訊息永遠無法正確顯示 |

### 🟡 Medium

| # | 問題 | 檔案 | 影響 |
|---|------|------|------|
| M1 | Router guard 允許 `company_admin`/`hr_manager` 進入 `/admin/companies`，但 POST/Onboarding API 後端只接受 `super_admin` | `router/index.js`、`tenants/api.py` | 非 super_admin 可見建立表單但送出會 403 |
| M2 | `AdminUsersView.vue` HEAD 版角色選單含 `manager`，此 role 不存在系統中 | HEAD `AdminUsersView.vue:100` | 選 manager 送出後 API 回 422 |

### 🟢 Low

| # | 問題 | 檔案 | 影響 |
|---|------|------|------|
| L1 | AdminOnboardingView timezone 選項縮減至 2 個 | `AdminOnboardingView.vue` | 功能受限但 Asia/Taipei 需求覆蓋 |
| L2 | `Admin.vue` icon SVG path 更換（非功能性）| `Admin.vue` | 無功能影響 |

---

## 8. Recommended Next Action

### 優先順序

#### 步驟 1（必須先執行）— 確認 AdminUsersView.vue regression 意圖

```
建議：向開發者確認工作樹 AdminUsersView.vue 是否為故意替換。
若為意外：執行 git restore frontend/src/views/admin/AdminUsersView.vue
          恢復 HEAD 版本後，再單獨修正 error parsing bug（H2）。
若為故意：需補齊 role_id CSS（已完成）並記錄功能降級原因於 NEXT_WP_TICKET.md。
```

#### 步驟 2（Critical — 必須修復）— AdminOnboardingView.vue 兩個 bug

**C2：role_id 修正**
```
修改範圍：AdminOnboardingView.vue 第 101、127、224 行
修改內容：將 'admin' 改為 'company_admin'
- <option value="company_admin">company_admin（公司管理員）</option>
- role_id: 'company_admin'（初始化）
- obForm.initial_user.role_id = 'company_admin'（reset）
```

**C1：移除 loadCompanies() 呼叫**
```
修改範圍：AdminOnboardingView.vue 第 175 行
修改內容：移除 await loadCompanies()
說明：此頁面為獨立頁面，不需維護公司列表快取。
      Onboarding 完成後已有 obSuccess 卡片顯示結果，不需刷新列表。
```

#### 步驟 3（若恢復 HEAD AdminUsersView）— 修正 error parsing

```
修改範圍：AdminUsersView.vue handleAddMember() 錯誤處理
修改內容：
  err?.response?.data?.detail?.code  →  err?.data?.detail?.code
  err?.response?.data?.detail?.message  →  err?.data?.detail?.message
```

#### 步驟 4（Medium — 後續 WP）— Router guard 收緊

```
考慮：/admin/companies 頁面的「建立公司」與「Onboarding」表單
      對 company_admin / hr_manager 應隱藏或顯示「無權限」提示，
      避免使用者填寫後被後端 403 拒絕。
```

### 修復順序建議

```
1. [確認意圖] AdminUsersView.vue regression → restore 或 document
2. [C2] AdminOnboardingView role_id: 'admin' → 'company_admin'
3. [C1] AdminOnboardingView 移除 loadCompanies() 呼叫
4. [H2] 若恢復 HEAD，修正 handleAddMember error parsing
5. [M1] 後續 WP 處理 router guard 精細化
```

---

## 附錄：工作樹 AdminUsersView.vue 保留的功能

以下功能在工作樹版本中**仍然存在**（未被 regression


### 5.2 `role_id` 值不一致（續）
後端驗證邏輯（`api_members.py`）：
```python
role = db.query(RoleModel).filter(RoleModel.id == request.role_id).first()
if role is None:
    raise HTTPException(422, {"code": "INVALID_ROLE", ...})
```
系統有效 role：`employee`、`company_admin`、`hr_manager`、`super_admin`  
`admin` 不在此清單，**後端一定回傳 HTTP 422 INVALID_ROLE**。

---

## 6. API Alignment Findings

### 6.1 frontend/src/api/admin.js 路徑對比後端

| 前端呼叫 | 後端 Endpoint | 對齊 |
|----------|--------------|------|
| GET /admin/companies | GET /api/admin/companies | OK |
| POST /admin/companies | POST /api/admin/companies | OK |
| GET /admin/companies/{id} | GET /api/admin/companies/{company_id} | OK |
| PATCH /admin/companies/{id} | PATCH /api/admin/companies/{company_id} | OK |
| POST /admin/companies/onboarding | POST /api/admin/companies/onboarding | OK |
| GET /admin/companies/{id}/members | GET /api/admin/companies/{id}/members | OK |
| POST /admin/companies/{id}/members | POST /api/admin/companies/{id}/members | OK |
| PATCH .../members/{mid}/active | PATCH .../members/{membership_id}/active | OK |

**結論：所有 API 路徑完全對齊，無路徑錯誤。**

### 6.2 Auth Guard 對齊分析

| Endpoint | 後端要求 | 前端 guard | 狀態 |
|----------|----------|-----------|------|
| 所有 /admin/* | JWT Bearer | requiresAdminAccess | OK |
| POST /admin/companies（建立）| super_admin only | company_admin/hr_manager 可進入頁面 | WARN — 前端 guard 比後端寬鬆 |
| POST /admin/companies/onboarding | super_admin only | company_admin/hr_manager 可進入頁面 | WARN — 同上 |

### 6.3 createCompany Payload 對比

前端固定送 timezone: 'Asia/Taipei'，後端接受任意 string，對齊 OK。

### 6.4 createCompanyMember Payload 對比

前端：{ display_name, email, login_username, password, role_id }  
後端 CreateMemberRequest：同上欄位，完全對齊 OK。

---

## 7. Risk Classification

### CRITICAL

| # | 問題 | 位置 | 影響 |
|---|------|------|------|
| C1 | loadCompanies() ReferenceError | AdminOnboardingView.vue:175 | Onboarding 成功後 UI 一定顯示失敗 |
| C2 | role_id: 'admin' 後端不接受 | AdminOnboardingView.vue:101,127,224 | 所有 Onboarding 請求被後端 422 拒絕 |

### HIGH

| # | 問題 | 位置 | 影響 |
|---|------|------|------|
| H1 | AdminUsersView.vue 功能 regression | 工作樹全檔 | WP-S1-10C/10D/10F 已完成功能全部失效 |
| H2 | HEAD handleAddMember error parsing 路徑錯誤 | HEAD AdminUsersView.vue:380 | 錯誤訊息永遠無法正確顯示 |

### MEDIUM

| # | 問題 | 位置 | 影響 |
|---|------|------|------|
| M1 | Router guard 比後端 auth 寬鬆（company_admin 可見建立表單但 API 403）| router/index.js | UX 混亂 |
| M2 | AdminUsersView HEAD 版角色選單含 manager（系統無此 role）| HEAD AdminUsersView.vue | 選 manager 送出 API 422 |

### LOW

| # | 問題 | 位置 | 影響 |
|---|------|------|------|
| L1 | AdminOnboarding timezone 選項縮減 | AdminOnboardingView.vue | 功能受限但 Asia/Taipei 覆蓋需求 |
| L2 | Admin.vue icon SVG path 更換 | Admin.vue | 無功能影響 |

---

## 8. Recommended Next Action

### 優先順序

**步驟 1（先確認意圖）**
```
AdminUsersView.vue 工作樹版本 regression 是否為故意？
- 若非故意 → git restore frontend/src/views/admin/AdminUsersView.vue
  恢復 HEAD 後，單獨修正 H2（error parsing）
- 若故意降級 → 記錄原因，補齊 NEXT_WP_TICKET.md
```

**步驟 2（Critical，必須修復，小範圍 patch）**
```
C2：AdminOnboardingView.vue
  - 第 101 行：value="admin" → value="company_admin"
  - 第 127 行：role_id: 'admin' → role_id: 'company_admin'
  - 第 224 行：role_id = 'admin' → role_id = 'company_admin'

C1：AdminOnboardingView.vue
  - 第 175 行：移除 await loadCompanies()
  （此頁面不維護公司列表，Onboarding 完成由 obSuccess card 顯示結果）
```

**步驟 3（若恢復 HEAD AdminUsersView）**
```
修正 handleAddMember error parsing：
  err?.response?.data?.detail?.code → err?.data?.detail?.code
  err?.response?.data?.detail?.message → err?.data?.detail?.message
```

**步驟 4（Medium，後續 WP）**
```
/admin/companies 頁面對 company_admin/hr_manager
「建立公司」與「Onboarding」區塊應隱藏或顯示「需要 super_admin 權限」提示
```

---

## 附錄：工作樹 AdminUsersView.vue 保留的功能

以下功能在工作樹版本中仍然正常存在：

- 公司下拉選單（selector panel）+ loadCompanies()
- 成員列表讀取（GET members API）
- Loading / Error / Empty state 顯示
- 成員資料表格（顯示名稱、登入帳號、角色、Email、帳號狀態、成員狀態、加入時間）
- formatDate() 工具函式
- Role badge CSS（已更新為正確 role 名稱）

---

**報告結束**  
**功能檔是否被修改：NO**  
**審計工具：git diff、grep、wc -l、Shell 唯讀指令**
