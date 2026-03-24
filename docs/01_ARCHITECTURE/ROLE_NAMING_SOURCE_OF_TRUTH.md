# ROLE_NAMING_SOURCE_OF_TRUTH

## 1) Summary

本文件定義目前專案「角色命名」的唯一基準（Source of Truth），目的為：

- 明確區分 **現行 active role names** 與 **legacy compatibility names**
- 明確定義哪些值可由前端新建/送出
- 明確定義哪些值僅保留於後端相容層，不可再作為新資料輸入
- 提供前後端後續同步與清理治理的統一依據

本文件只基於目前已驗證證據（報告 + 現行程式碼）；未證實處一律標示為不確定，不做推測。

---

## 2) Current Active Role Names

目前專案中的 active role names（以「現行邏輯與字典」為準）：

- `super_admin`
- `company_admin`
- `hr_manager`
- `employee`
- `customer_service`

### 角色狀態（含指定角色）

| role | current status | where it is used | frontend may send? | backend compatibility-only? |
|---|---|---|---|---|
| `super_admin` | Active（平台層） | auth store 的 super admin 判斷；onboarding 頁權限入口；後端平台層映射 | 否（非一般成員新增值） | 否 |
| `company_admin` | Active | Admin Users 新增成員選單；Onboarding 初始 user role；後端 admin scope | 是 | 否 |
| `hr_manager` | Active | Admin Users 新增成員選單；auth store `isAdminAccess`；後端 admin scope | 是 | 否 |
| `employee` | Active | Admin Users 新增成員預設值；登入樣本實際命中 | 是 | 否 |
| `customer_service` | Active（後端平台層） | 後端 `UserRole.CUSTOMER_SERVICE` 與 support assignment 路徑 | 否（目前指定前端頁面未提供） | 否 |

---

## 3) Legacy Compatibility Role Names

目前被歸類為 legacy compatibility names：

- `manager`
- `admin`
- `hr`
- `system_admin`

### 角色狀態（含指定角色）

| role | current status | where it is used | frontend may send? | backend keeps for compatibility? |
|---|---|---|---|---|
| `manager` | Legacy（仍可達/未清理就緒） | 後端 mapping、attendance legacy 分支；live DB `roles` 主表仍存在 | 否（目前指定前端頁面未提供） | 是 |
| `admin` | Legacy（目前資料層未見存量） | 後端 mapping、attendance legacy 分支仍在 | 否 | 是 |
| `hr` | Legacy（目前資料層未見存量） | 後端 mapping、attendance legacy 分支仍在 | 否 | 是 |
| `system_admin` | Legacy alias（高權限相容） | 後端 mapping `system_admin -> SUPER_ADMIN`（auth-critical） | 否 | 是 |

> 說明：`admin/hr/system_admin` 在目前 live DB 主表與 assignment 皆未觀測到；但 runtime 相容映射仍在，因此本階段仍列 compatibility-only，不可直接判定可移除。

---

## 4) Frontend Allowed Input Values

以目前指定前端檔案的「實際送出值」為準：

1. `frontend/src/views/admin/AdminUsersView.vue`（add member）
   - 允許送出：`employee`、`hr_manager`、`company_admin`
   - 預設：`employee`
2. `frontend/src/views/admin/AdminOnboardingView.vue`（onboarding）
   - 目前選單值：`company_admin`
   - 預設：`company_admin`
3. `frontend/src/stores/auth.js`
   - 權限檢查使用：`super_admin`、`company_admin`、`hr_manager`
   - 此檔非建立資料入口，但反映前端目前認可的角色語義

### 前端建立/送出規則（本文件定版）

- **可作為新資料輸入**：`employee`、`hr_manager`、`company_admin`
- **不得作為新資料輸入**：`manager`、`admin`、`hr`、`system_admin`
- `super_admin`、`customer_service`：屬平台/系統治理角色，不在目前指定前端成員新增流程中作為新建值

---

## 5) Backend Compatibility-Only Values

目前後端保留但僅限相容用途（不得作為前端新資料輸入目標）的值：

- `manager`
- `admin`
- `hr`
- `system_admin`

相容保留原因：

- 仍存在 auth/runtime mapping 或 legacy 分支判斷
- `manager` 仍在 live DB `roles` 主表，且 runtime reachability 被評估為可達
- `system_admin` 映射為 `SUPER_ADMIN`，屬 auth-critical，未達可移除證據門檻

---

## 6) Live DB Current Findings

依現有盤點報告：

- `roles` 主表目前可見：
  - `super_admin`、`company_admin`、`hr_manager`、`employee`、`customer_service`、`manager`
- `user_company_memberships.role_id`（live assignment）目前可見：
  - `company_admin`、`employee`
- 目前未見於主表與 assignment：
  - `admin`、`hr`、`system_admin`

結論：

- 資料層仍有 `manager` 足跡（主表）
- `admin/hr/system_admin` 在資料層目前未見存量，但程式相容層仍存在

---

## 7) Cleanup Status / Governance Note

目前治理狀態：**尚未達成可全面移除 legacy 相容層的條件**。

- 2026-03-24 狀態註記（Phase 1 已完成）：\n  - `dependencies.py` 已移除 `admin` / `hr` 顯式 compatibility mapping\n  - `attendance/sessions` 已移除 `admin` / `hr` 分支，僅保留 `manager`\n  - `manager` 與 `system_admin` 仍屬保留（deferred）\n
- `manager`：未達清理就緒（runtime 可達 + 主表仍存在）
- `system_admin`：未達清理就緒（高權限映射仍在，來源未完全證偽）
- `admin` / `hr`：資料層偏低風險，但仍需更多 runtime/token 證據後再決策

因此本文件僅定義命名規則與輸入邊界，不執行任何程式、migration、資料變更。

---

## 8) Recommended Rule for Future Development

後續開發請遵守以下單一規則：

1. **前端所有新建/更新角色輸入**僅可使用：`employee`、`hr_manager`、`company_admin`。
2. **後端新功能/新 API**不得再新增或擴散 `manager/admin/hr/system_admin` 作為新資料輸入值。
3. `manager/admin/hr/system_admin` 僅能存在於明確標註的 compatibility 路徑。
4. 若未來要移除任何 legacy 值，必須先補齊：
   - 真實 token/request 命中統計
   - 外部 token 來源與簽發路徑驗證（特別是 `system_admin`）
   - 資料庫主表與 assignment 清零/遷移證據
5. 本文件視為角色命名治理基準；若與舊報告敘述衝突，以本文件與最新驗證結果為準。
