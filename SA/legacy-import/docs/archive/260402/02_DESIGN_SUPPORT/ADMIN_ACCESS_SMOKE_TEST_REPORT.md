# ADMIN_ACCESS_SMOKE_TEST_REPORT

- 日期：2026-03-23
- 範圍：`f740d77` 之 Admin 前端角色存取對齊 smoke test
- 性質：前端靜態檢查 + build 驗證（不修改程式碼）

---

## 1) 測試目標與方法

### 目標
驗證三種角色在 Admin 相關路由與頁面可見性的對齊情況：
- `super_admin`
- `company_admin`
- `hr_manager`

### 方法
1. 檢查 `f740d77` 及目前前端檔案：
   - `frontend/src/router/index.js`
   - `frontend/src/views/Admin.vue`
   - `frontend/src/views/admin/AdminCompaniesView.vue`
   - `frontend/src/views/admin/AdminOnboardingView.vue`
   - `frontend/src/views/admin/AdminUsersView.vue`
   - `frontend/src/stores/auth.js`
2. 依 router guard + template `v-if` 建立角色存取矩陣。
3. 檢查「可見但不可進 / 可進但可能後端拒絕 / 意外阻擋」風險。
4. 執行前端 build smoke：`cd frontend && npm run build`。

---

## 2) 核心存取規則（前端）

1. `/admin`、`/admin/companies`、`/admin/users` 使用 `requiresAdminAccess: true`
   - 允許：`super_admin` 或 `isAdminAccess`
   - `isAdminAccess` = `company_admin` 或 `hr_manager`
2. `/admin/onboarding` 額外使用 `requiresSuperAdmin: true`
   - 非 `super_admin` 直接導向 `/admin`
3. `Admin.vue` 內：
   - Onboarding 卡片 `v-if="authStore.isSuperAdmin"`
   - `company_admin` / `hr_manager` 看不到 Onboarding 入口卡
4. `AdminOnboardingView.vue` 內有 page-level gate：`v-if="isSuperAdmin"`（防禦性）
5. `AdminCompaniesView.vue`：建立公司表單 `v-if="isSuperAdmin"`
   - 非 super_admin 可進頁，但看不到建立表單

---

## 3) Access Matrix（Smoke）

| 角色 \ 項目 | Admin 入口可見性（/admin 內卡片） | `/admin` | `AdminCompaniesView` `/admin/companies` | `AdminOnboardingView` `/admin/onboarding` | `AdminUsersView` `/admin/users` |
|---|---|---|---|---|---|
| `super_admin` | PASS（公司管理/新公司開通/使用者） | PASS | PASS（可見建立公司表單） | PASS | PASS |
| `company_admin` | PASS（公司管理/使用者；無 onboarding 卡） | PASS | PASS（可進頁；建立公司表單隱藏） | PASS（預期被導向 `/admin`，無法進入頁面） | PASS |
| `hr_manager` | PASS（公司管理/使用者；無 onboarding 卡） | PASS | PASS（可進頁；建立公司表單隱藏） | PASS（預期被導向 `/admin`，無法進入頁面） | PASS |

---

## 4) PASS / FAIL / RISK Findings

## PASS
1. `super_admin / company_admin / hr_manager` 三者都可進 `/admin`（符合 S1-11C admin access）。
2. Onboarding 路由與入口一致：
   - 非 `super_admin` 看不到入口卡，且直打路由會被 guard 擋回 `/admin`。
3. `AdminCompaniesView` 已把「建立公司」UI 限縮到 `super_admin`。
4. `AdminOnboardingView` 有頁面層級二次防護（`v-if="isSuperAdmin"`）。
5. 前端 build smoke 通過：`vite build` 成功。

## FAIL
- 本次 smoke（針對角色路由與可見性）未發現直接 FAIL。

## RISK
1. **可進頁但可能後端拒絕（403）**
   - `company_admin` / `hr_manager` 可進 `/admin/companies`，但若觸發後端僅 super_admin 允許的操作（例如建立公司）可能被拒絕。
   - 前端目前以「隱藏表單」降低風險，屬可接受但需持續關注 API 權限一致性。
2. **`AdminUsersView` 角色選單風險（非本次路由 gating 主軸）**
   - 畫面中新增成員角色選項仍見 `manager`，若後端不接受該 role，可能回 422（`INVALID_ROLE`）。
   - 這是資料/角色字典對齊風險，不是本次 admin route gate 失效。

---

## 5) 額外檢查題目對應

### A. 是否存在「看得到入口但進不去路由」
- Onboarding：**否（設計一致）**。非 super_admin 根本看不到入口；直打也會被擋。

### B. 是否存在「進得去路由但可能後端 403」
- **有可能**：`company_admin` / `hr_manager` 在 `/admin/companies` 觸發 super_admin-only API 時。

### C. 是否存在「角色被意外阻擋」
- 本次 smoke 未發現三個目標角色在既定可進路由遭意外阻擋。

---

## 6) Build 驗證

- 指令：`cd frontend && npm run build`
- 結果：✅ PASS（`vite build` completed）

---

## 7) 結論

`f740d77` 在 **Admin 角色路由與可見性對齊** 上整體為 **PASS**：
- `super_admin`：完整 admin 能力與入口
- `company_admin` / `hr_manager`：可使用 admin 主入口與主要頁，Onboarding 正確限制

目前主要是 **RISK（非阻斷）**：
- 前端可見性與後端最終授權仍有局部寬窄差（尤其 companies 操作層）
- `AdminUsersView` 角色選項字典仍需持續留意
