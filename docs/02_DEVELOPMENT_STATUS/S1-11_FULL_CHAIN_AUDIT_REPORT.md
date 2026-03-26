# S1-11_FULL_CHAIN_AUDIT_REPORT

- 日期：2026-03-24
- Branch：`feature/wp-11-09-schedule`
- Audit 深度：中等（聚焦 S1-11 主線，不做跨模組無限制擴查）
- 範圍：Frontend（router/store/views/api）→ Backend（auth/dependencies/tenants/attendance）→ tests/docs 盤點

---

## 1) Executive Summary

### 整體判定
- **整體一致性：部分一致，但存在高風險權限邊界問題**
- **健康燈號：Yellow（偏 Red）**

### 核心結論
1. 前端路由守衛與 auth store 在 S1-11C/S1-11E（admin access + restoreSession）主線上大致一致。  
2. 但 Backend `tenants` admin endpoints 目前允許 `company_admin`/`hr_manager` 直接操作全公司列表與指定公司資料，與「super_admin gating」敘述存在明顯落差。  
3. Legacy cleanup phase 1 已完成 `admin/hr` 指定清理，但 `manager` 仍在 runtime 路徑（`attendance/api.py::get_sessions_reporting`）保留，與 role normalization 的最終收斂目標仍有縫隙。  
4. API 合約整體可通，但存在 docs/註解與實作語義不一致，以及 legacy header 殘留（`X-Company-ID` / `X-User-ID`）現象。

### 是否適合進入 Legacy Cleanup Phase 2
- **結論：暫不建議直接進入（先做最小修補票）**
- 原因：尚有高風險權限邊界與角色語義不一致，若直接進 phase 2 會放大風險。

---

## 2) Findings by Layer

## A. Frontend Router / Auth Store

### Finding A-1
- **Severity：Low**
- **位置：**
  - `frontend/src/main.js`（`useAuthStore()` + `restoreSession()` 初始化）
  - `frontend/src/router/index.js`（`router.beforeEach`）
- **具體節點：**
  - `main.js::authStore.restoreSession()`
  - `router/index.js::beforeEach()` 裡的二次 hydrate 條件：
    - `if (localStorage.getItem('token') && (!authStore.isAuthenticated || !authStore.userRole)) { authStore.restoreSession() }`
- **摘要：** S1-11E.3 的 session restore 補強存在，能處理 pinia hydration 時序問題，行為與 router guard 一致。
- **建議：** 僅記錄（維持現況）。

### Finding A-2
- **Severity：Medium**
- **位置：** `frontend/src/router/index.js`
- **具體節點：**
  - route meta：`requiresAdminAccess` / `requiresSuperAdmin`
  - guard：`if (to.meta.requiresAdminAccess) { ... }`
- **摘要：** 註解仍有「super_admin only」字樣（例如 admin 區塊註解），但實際 guard 已允許 `super_admin || isAdminAccess(company_admin/hr_manager)`。屬文件語義落差。
- **建議：** 可後補（註解/文件同步，不需功能重構）。

### Finding A-3
- **Severity：Low**
- **位置：** `frontend/src/stores/auth.js`, `frontend/src/api/auth.js`, `frontend/src/components/Navbar.vue`
- **具體節點：**
  - `auth.js::logout()`
  - `api/auth.js::logout()`（只做 localStorage 清除）
  - `Navbar.vue::handleLogout()`（登出後 `router.push('/login')`）
- **摘要：** logout 路徑一致且可預期，未見顯著矛盾。
- **建議：** 僅記錄。

---

## B. Frontend Admin Pages / API Calls

### Finding B-1
- **Severity：High**
- **位置：**
  - `frontend/src/views/admin/AdminUsersView.vue`
  - `frontend/src/views/admin/AdminCompaniesView.vue`
  - `frontend/src/api/admin.js`
- **具體節點：**
  - `AdminUsersView.vue::loadCompanies()` → `adminApi.listCompanies()`
  - `AdminUsersView.vue::loadMembers()` → `adminApi.listCompanyMembers(companyId)`
  - `AdminCompaniesView.vue::handleUpdate()` → `adminApi.updateCompany(companyId, payload)`
  - `AdminCompaniesView.vue::handleToggleMembership()` → `adminApi.toggleMembershipActive(...)`
- **摘要：** 前端 admin 頁面已對 `company_admin/hr_manager` 開放（經 route guard），且提供跨公司選取與操作流程；若後端未限制 scope，會形成跨公司可見/可操作風險。
- **建議：** 先修（需配合 backend 權限最小修補）。

### Finding B-2
- **Severity：Low**
- **位置：** `frontend/src/views/admin/AdminOnboardingView.vue`
- **具體節點：**
  - `isSuperAdmin` computed
  - `v-if="isSuperAdmin"` + `handleOnboard()`
- **摘要：** onboarding 前端顯示與行為都限定 super_admin，與後端限制一致。
- **建議：** 僅記錄。

---

## C. Backend Role / Permission Logic

### Finding C-1（最重要）
- **Severity：High**
- **位置：** `backend/app/modules/tenants/api.py`
- **具體節點：**
  - `list_companies()`
  - `get_company(company_id)`
  - `update_company(company_id, request)`
- **問題代碼特徵：**
  - 共同條件為 `if not (actor.is_super_admin() or actor.is_admin()): ...`
  - `actor.is_admin()` 於 `backend/app/core/scope.py::Actor.is_admin()` 對 `company_admin/hr_manager` 回傳 True
- **摘要：** 這三個 endpoint 實際允許 `company_admin/hr_manager`，但 docstring 寫「僅限 super_admin」。且 `list_companies()` 回傳全公司列表，`get/update` 可指定任意 `company_id`，未見 `assert_company_scope` 或 `actor.active_company_id` 綁定。
- **建議：** 先修（最小權限修補票，明確決策是否要回到 super_admin-only 或加 scope 限制）。

### Finding C-2
- **Severity：High**
- **位置：** `backend/app/modules/tenants/api_members.py`
- **具體節點：**
  - `list_company_members(company_id)`
  - `toggle_membership_active(company_id, membership_id, request)`
  - `create_company_member(company_id, request)`
- **摘要：** 同樣使用 `actor.is_super_admin() or actor.is_admin()`，若 `company_admin/hr_manager` 進入 admin 頁，可對指定 `company_id` 執行成員查詢與異動。未見將可操作公司限制到 `actor.active_company_id` 的明確檢查。
- **建議：** 先修（與 C-1 同票處理，統一權限邊界）。

### Finding C-3
- **Severity：Medium**
- **位置：**
  - `backend/app/core/dependencies.py::_map_role_id_to_user_role`
  - `backend/app/core/scope.py::Actor.is_admin`
- **摘要：**
  - phase1 已移除 `admin/hr` 顯式映射（符合 cleanup 目標）
  - 但 `_map_role_id_to_user_role` 仍保留 `manager`，且 unknown role fallback 到 `COMPANY_USER`（`role_mapping.get(...); if not mapped_role: return COMPANY_USER`）
- **建議：** 可後補（先以測試與資料證據收斂，再決定 phase2 清理策略）。

### Finding C-4
- **Severity：Medium**
- **位置：** `backend/app/modules/attendance/api.py::get_sessions_reporting`
- **具體節點：**
  - `is_admin = actor.active_role_id == "manager"`
- **摘要：** 查他人 sessions 的管理分支仍綁定 `manager`，未對齊 `company_admin/hr_manager` normalization 主線。這是 phase1 保留項，但會造成角色語義分裂。
- **建議：** 可後補（列為 phase2 前置清理評估項）。

---

## D. API Contract Alignment

### Finding D-1
- **Severity：Medium**
- **位置：**
  - Frontend：`frontend/src/api/client.js`
  - Backend：`backend/app/core/dependencies.py::get_current_actor`, `get_actor_with_company`
- **具體節點：**
  - `apiClient` request interceptor 仍寫入 `X-Company-ID`, `X-User-ID`
  - backend actor 鏈路已以 JWT claim（`company_id`, `sub`, `role_id`）為主
- **摘要：** API 可運作，但前端仍保留 legacy header path 痕跡，與「JWT actor single source」策略不完全一致。
- **建議：** 可後補（技術債清單，與 phase2/穩定化併單處理）。

### Finding D-2
- **Severity：Low**
- **位置：**
  - Frontend：`frontend/src/api/admin.js`
  - Backend：`backend/app/modules/tenants/api.py`, `api_members.py`, `api_onboarding.py`
- **摘要：** 主要 admin API 路徑與 payload 命名整體對齊（`/api/admin/companies`, `/onboarding`, `/members`, `/active`, `role_id`, `is_active`）。
- **建議：** 僅記錄。

---

## E. Legacy Role Residue

### Finding E-1
- **Severity：Medium**
- **位置：**
  - `backend/app/core/dependencies.py::_map_role_id_to_user_role`
  - `backend/app/modules/attendance/api.py::get_sessions_reporting`
  - `backend/app/core/tests/test_legacy_role_cleanup_phase1.py`
  - `backend/app/modules/attendance/tests/test_legacy_role_cleanup_phase1b.py`
- **摘要：**
  - `admin/hr` 顯式 mapping 已移除（phase1A 達成）
  - `manager` runtime 行為仍保留（phase1B 設計上保留）
  - 測試目前也在保護「僅 manager 可走該分支」
- **建議：** 可後補（phase2 前需先確認目標角色字典與資料證據）。

### Finding E-2（可能延伸風險）
- **Severity：Low（Potential Extension Risk）**
- **位置：** `docs/02_DEVELOPMENT_STATUS/LIVE_DB_ROLE_VALUE_INVENTORY_REPORT.md`
- **摘要：** live DB 顯示 `manager` 仍在 `roles` 主表（雖未出現在 membership assignment），若未做資料治理即硬刪相容層，可能影響舊資料/外部流程。
- **建議：** 僅記錄（需獨立治理票，不在本次 audit 擴查）。

---

## F. Tests / Docs Gaps

### Finding F-1
- **Severity：High**
- **位置：**
  - 已有測試：
    - `backend/app/core/tests/test_legacy_role_cleanup_phase1.py`
    - `backend/app/modules/attendance/tests/test_legacy_role_cleanup_phase1b.py`
- **摘要：** 現有測試僅保護 phase1 的 mapping/分支字串行為，**未覆蓋** S1-11 核心風險：
  - admin endpoints 權限矩陣（super_admin vs company_admin/hr_manager）
  - 跨公司資料可見性/可操作性
  - router guard + backend 權限的端到端一致性
- **建議：** 先修（最小補測試票，至少補 API permission matrix）。

### Finding F-2
- **Severity：Medium**
- **位置：**
  - `backend/app/modules/tenants/api.py` docstring（多處「僅限 super_admin」）
  - 實作條件為 `actor.is_super_admin() or actor.is_admin()`
- **摘要：** 文件/註解與實作不一致，會誤導後續維護與 audit 判讀。
- **建議：** 可後補（修註解或修權限邏輯，兩者需一致）。

---

## 3) Top 5 Risk Matrix（依優先序）

1. **跨公司 admin 操作邊界不清（可能越權）**  
   - 層：Backend Permission + Frontend Admin Flow  
   - 位置：`tenants/api.py::{list_companies,get_company,update_company}`、`tenants/api_members.py::{list_company_members,toggle_membership_active,create_company_member}`  
   - Severity：**High**

2. **S1-11 role normalization 與 attendance 分支語義分裂**  
   - 層：Backend Role Logic  
   - 位置：`attendance/api.py::get_sessions_reporting`（`active_role_id == "manager"`）  
   - Severity：**High**

3. **缺乏對權限矩陣的測試保護**  
   - 層：Tests Coverage  
   - 位置：`backend/app/core/tests`, `backend/app/modules/attendance/tests`（目前僅 phase1 最小測）  
   - Severity：**High**

4. **實作與註解/文件權限描述不一致**  
   - 層：Docs/Code Consistency  
   - 位置：`backend/app/modules/tenants/api.py` docstring vs condition  
   - Severity：**Medium**

5. **legacy header 殘留（非主授權來源）**  
   - 層：API Contract Hygiene  
   - 位置：`frontend/src/api/client.js`（`X-Company-ID`, `X-User-ID`）  
   - Severity：**Medium**

---

## 4) Recommended Next Action

### 建議選項
- **建議：A + C（先做最小修補票，再補最小測試/文件同步）**

### 不建議直接選 B（立即進入 Legacy Cleanup Phase 2）的理由
1. 權限邊界尚未收斂（尤其 `tenants` admin endpoints 是否應允許 company_admin/hr_manager 跨公司操作）。
2. role normalization 與 runtime (`manager`) 仍有明顯分叉。
3. 缺少足夠測試可防止修補後回歸。

### 建議最小下一步（不在本次 audit 直接改 code）
1. 開一張 **S1-11 Stabilization 最小修補票**：先明確定義 admin endpoints 的角色與公司 scope 規則。  
2. 同票補上 **permission matrix 測試**（super_admin / company_admin / hr_manager / employee）。  
3. 修正對應註解/文件，使權限敘述與實作一致。  
4. 再評估是否進入 Legacy Cleanup Phase 2（含 `manager` 清理決策）。

---

## 5) Audit Boundary & Notes

- 本次刻意限制在 S1-11 主線直接鏈路（frontend router/store/admin views/api、backend core dependencies/scope、tenants admin APIs、auth login、attendance sessions role branch）。
- 對需要更大範圍才能定論的點（例如 `manager` 全系統可達性）僅標記為 **Potential Extension Risk**，未做無限制擴查。
- 本報告為 audit 輸出，未修改 production code / tests。
