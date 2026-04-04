# WP-S1-08A — Admin Access Control Audit

**Date**: 2026-03-20

---

## Section 1 — Current Auth State

### 1.1 登入流程

- **端點**: `POST /api/internal/auth/login`
- **請求欄位**: `company_id` + `login_username` + `password`
- **JWT**: HS256, 900 秒 (15 分鐘) 到期
- **JWT Claims**: `sub` (user_id), `company_id`, `role_id`, `iat`, `exp`

### 1.2 登入成功回應

```json
{
  "access_token": "<JWT>",
  "token_type": "bearer",
  "user": { "id": "...", "display_name": "...", "email": "..." },
  "company": { "id": "...", "name": "..." },
  "role": { "id": "...", "name": "..." }
}
```

### 1.3 Frontend 儲存方式 (stores/auth.js)

| 儲存位置 | 內容 |
|---------|------|
| `localStorage['token']` | JWT access_token |
| `localStorage['user']` | JSON.stringify(user) |
| `localStorage['company']` | JSON.stringify(company) |
| `localStorage['role']` | JSON.stringify(role) |
| Pinia state | user, company, role, token |

### 1.4 Session 恢復機制

- `router/index.js` `beforeEach` 中：若 `!authStore.isAuthenticated && localStorage.getItem('token')` → 呼叫 `restoreSession()`
- `restoreSession()` 直接從 localStorage JSON.parse 恢復，**不重新向後端驗證 token**
- `isAuthenticated` getter = `!!state.token && !!state.user`
- **漏洞**: JWT 過期後 localStorage 仍有值，`isAuthenticated` 仍返回 `true`，前端不會強制重新登入

### 1.5 Role 來源判定

- Role **來自後端真實 DB**（`roles` 表 + `Membership.role_id`）
- JWT 包含 `role_id`，後端 `get_current_actor()` 每次請求都驗證
- **非 frontend mock** — backend 每個受保護 endpoint 均呼叫 `Depends(get_current_actor)`
- Frontend `localStorage['role']` 僅作 UI 顯示用途，不影響後端授權

### 1.6 Auth 持久化評估

- ✅ 重新整理後可恢復（localStorage）
- ⚠️ 無 refresh token 機制，900 秒後 API 呼叫將返回 401，但前端不自動重導
- ⚠️ logout() 只清除 localStorage，不呼叫後端 token invalidation

## Section 2 — Route Protection Audit

### 2.1 完整路由清單 (router/index.js)

| 路由 | requiresAuth | requiresAdmin | 元件 |
|------|-------------|--------------|------|
| `/` | ✅ true | ❌ 無 | Home.vue |
| `/login` | ❌ false | ❌ 無 | Login.vue |
| `/attendance/reports/sessions` | ✅ true | ❌ 無 | AttendanceSessionsPage.vue |
| `/attendance/reports/company-summary` | ✅ true | ❌ 無 | CompanySummaryPage.vue |
| `/attendance/reports/user-summary` | ✅ true | ❌ 無 | UserSummaryPage.vue |
| `/schedule` | ✅ true | ❌ 無 | SchedulePage.vue |
| **`/admin`** | **❌ 路由不存在** | ❌ 無 | — |

### 2.2 Global beforeEach 守衛

```javascript
router.beforeEach((to, from, next) => {
  if (!authStore.isAuthenticated && localStorage.getItem('token')) {
    authStore.restoreSession()  // 不驗證 token 有效性
  }
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')  // 未登入 → 導向 /login
    return
  }
  if (to.path === '/login' && authStore.isAuthenticated) {
    next('/')  // 已登入不能回 login
    return
  }
  next()
})
```

**守衛缺失**:
- 無 `requiresAdmin` 或 `requiresRole` 邏輯
- 無 role 比對
- 無 token 有效期檢查

### 2.3 /admin 路由分析

- **`Admin.vue` 存在**於 `src/views/Admin.vue`
- **路由定義中完全找不到 `/admin`**
- 直接瀏覽器訪問 `/admin` → Vue Router 無匹配 → 404 或空白頁
- `Admin.vue` 無法透過任何前端路由訪問
- Admin.vue 本身無 role 檢查邏輯（純 placeholder）

**分類**: 🔴 No protection — 路由根本不存在，功能無法訪問

### 2.4 /schedule 路由分析

- ✅ 路由已定義，`meta: { requiresAuth: true }`
- ✅ `beforeEach` 攔截未登入者 → redirect `/login`
- ❌ **無 `requiresAdmin` meta**
- ❌ **無 role 驗證** — `employee` 和 `admin` 皆可訪問
- ❌ `SchedulePage.vue` 內部無 role 檢查
- ⚠️ 後端 schedule API 本身有 feature gate（`SCHEDULE_CORE`），但無 role 限制

**分類**: 🟡 UI-only protection — 只擋未登入者，不擋角色

### 2.5 可直接繞過的路由

任何已登入 session（即使是 employee）可直接訪問：
- `/schedule` — 排班管理（應限 admin）
- `/attendance/reports/*` — 所有報表頁面（應限 admin/manager）

## Section 3 — Role Architecture

### 3.1 平台層角色 (UserRole enum — scope.py)

| role_id (DB) | 平台層 UserRole | 說明 |
|-------------|----------------|------|
| `super_admin` | `SUPER_ADMIN` | 系統全域管理員，跨租戶 |
| `system_admin` | `SUPER_ADMIN` | 同上（別名） |
| `customer_service` | `CUSTOMER_SERVICE` | 客服人員，限指派公司 |
| `support` / `cs` | `CUSTOMER_SERVICE` | 同上（別名） |
| `admin` | `COMPANY_USER` | 公司管理員（公司層） |
| `manager` | `COMPANY_USER` | 主管（公司層） |
| `employee` | `COMPANY_USER` | 一般員工（公司層） |
| `hr` | `COMPANY_USER` | HR 人員（公司層） |

### 3.2 公司層 RBAC (Actor.active_role_id)

- `is_admin()` → `active_role_id in ('admin', 'manager', 'hr')` 或 `is_super_admin()`
- `is_employee()` → `active_role_id == 'employee'`
- `active_role_id` 來自 `Membership.role_id`，於 `get_current_actor()` 注入

### 3.3 資料模型架構 (Platform-First v2)

```
User (全域身份)
  id, display_name, email, password_hash, is_active
  ← 無 company_id（跨公司全域）

Membership (user_company_memberships)
  user_id → users.id
  company_id → tenants.id
  role_id → roles.id
  login_username (per-company，唯一)
  is_active
  UNIQUE(company_id, login_username)
  UNIQUE(user_id, company_id)

Role (全域預定義)
  id (PK), name, description
  ← 無 company_id（全域）

Permission / RolePermission
  全域定義，無 company_id
```

### 3.4 JWT 結構

```json
{
  "sub": "<user_id UUID>",
  "company_id": "<active company scope>",
  "role_id": "<membership role_id>",
  "iat": <timestamp>,
  "exp": <timestamp+900>
}
```

### 3.5 System-level User（無 company_id）支援度

- ✅ **架構上支援**：`super_admin` 不需 Membership，`get_current_actor()` 不查 membership for super_admin
- ✅ `Actor.has_active_company()` 對 super_admin 直接返回 True
- ❌ **無 DB seed**：目前無 `super_admin` 角色帳號存在
- ❌ **無建立 API**：無法透過 REST API 建立 system-level user

### 3.6 角色儲存位置總結

| 層次 | 儲存位置 | 誰控制 |
|------|---------|-------|
| 角色定義 | DB `roles` 表 | Migration seed |
| 用戶角色 | DB `user_company_memberships.role_id` | 後端 |
| 請求層角色 | JWT `role_id` claim | 登入時生成 |
| Frontend 顯示 | `localStorage['role']` + Pinia | 登入時快取 |

## Section 4 — Global Admin Capability

### 4.1 super_admin 現有後端能力矩陣

| 能力 | 後端支援 | API 端點 | Frontend UI |
|------|---------|---------|-------------|
| 列出所有租戶 | ✅ `TenantService.list_tenants()` | ❌ 無 | ❌ 無 |
| 建立新租戶 | ✅ `TenantService.create_tenant()` | ❌ 無 | ❌ 無 |
| 啟用/停用租戶 | ✅ `activate/deactivate_tenant()` | ❌ 無 | ❌ 無 |
| 查看租戶詳情 | ✅ `TenantService.get_tenant()` | ❌ 無 | ❌ 無 |
| 管理 entitlements | ✅ `CompanyEntitlementService` | ✅ `/api/admin/companies/{id}/entitlements` | ❌ 無 |
| 套用 plan defaults | ✅ `apply_plan_defaults()` | ✅ `/api/admin/companies/{id}/entitlements/apply-plan` | ❌ 無 |
| 建立第一個 admin user | ✅ `AuthRepository.create_user()` + `create_membership()` | ❌ 無 | ❌ 無 |
| 管理現有 memberships | ✅ Repo 層存在 | ❌ 無 | ❌ 無 |

### 4.2 現有 API 端點（tenants/api.py）

唯一存在的租戶相關 API 是 **entitlement 管理**：

```
GET  /api/admin/companies/{company_id}/entitlements
PATCH /api/admin/companies/{company_id}/entitlements
POST /api/admin/companies/{company_id}/entitlements/apply-plan
```

**全部需要 super_admin 身份**（透過 `get_current_actor()` + `ScopeChecker`）

### 4.3 缺少的 API 層

以下功能**後端 Service/Repo 已實作，但無 REST 端點**：

1. `GET /api/admin/companies` — 列出所有租戶
2. `POST /api/admin/companies` — 建立新租戶
3. `GET /api/admin/companies/{id}` — 查看租戶詳情
4. `PATCH /api/admin/companies/{id}` — 更新租戶（名稱/狀態/時區）
5. `POST /api/admin/companies/{id}/users` — 為租戶建立第一個管理員
6. `GET /api/admin/companies/{id}/users` — 列出租戶成員

### 4.4 前端缺失

- `/admin` 路由不存在（Admin.vue 無法訪問）
- `Admin.vue` 是純 placeholder（6 個「開發中」卡片，無任何功能邏輯）
- 無 super_admin 專屬 UI 元件
- 無 tenant 管理介面
- 無 user 管理介面

### 4.5 結論

系統具備 **super_admin 角色架構**和**底層 Service/Repo**，
但**缺乏完整的 REST API 層和前端管理介面**，
導致 super_admin 能力目前只能透過直接操作 DB 或 seed script 執行。

## Section 5 — Customer Creation Analysis

### 5.1 Tenant/Company 模型存在性

✅ `Tenant` 模型完整定義於 `backend/app/modules/tenants/models.py`：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `id` | String(50) PK | Company ID（tenant identifier） |
| `name` | String(255) NOT NULL | 公司顯示名稱 |
| `is_active` | Boolean NOT NULL | 啟用狀態（軟刪除） |
| `timezone` | String(50) NOT NULL DEFAULT 'UTC' | 公司時區 |
| `created_at` | DateTime | 建立時間（UTC） |
| `updated_at` | DateTime | 更新時間（UTC） |

### 5.2 Option A — 僅建立 Tenant

| 層次 | 狀態 | 位置 |
|------|------|------|
| Model (`Tenant`) | ✅ 完整 | `tenants/models.py` |
| Repo (`TenantRepository.create()`) | ✅ 完整 | `tenants/repo.py` |
| Service (`TenantService.create_tenant()`) | ✅ 完整，含重複 ID 檢查 | `tenants/service.py` |
| API Schema (CreateTenantRequest) | ❌ **不存在** | — |
| API Endpoint (`POST /api/admin/companies`) | ❌ **不存在** | — |

**結論**: 底層已備，只缺 Schema + API endpoint。

### 5.3 Option B — 建立 Tenant + 第一個 Admin User

| 層次 | 狀態 | 位置 |
|------|------|------|
| User 建立 (`AuthRepository.create_user()`) | ✅ 完整 | `auth/repo.py` |
| Membership 建立 (`create_membership()`) | ✅ 完整 | `auth/repo.py` |
| 複合 Service（Tenant + User + Membership） | ❌ **不存在** | — |
| Request Schema (`CreateTenantWithAdminRequest`) | ❌ **不存在** | — |
| API Endpoint | ❌ **不存在** | — |

**所需 request 欄位（推估）**:
```json
{
  "tenant_id": "company-b",
  "tenant_name": "Company B Ltd",
  "timezone": "Asia/Taipei",
  "admin_username": "admin",
  "admin_password": "...",
  "admin_display_name": "Admin User",
  "admin_email": "admin@company-b.com"
}
```

### 5.4 現有 Tenant 相關 Schema 範圍

`tenants/schemas.py` 目前只包含：
- `UpdateEntitlementRequest`
- `ApplyPlanRequest`
- `EntitlementResponse`
- `CompanyEntitlementsResponse`
- `ApplyPlanResponse`

**完全沒有** Tenant CRUD 的 request/response schema。

### 5.5 建立路徑可行性評估

| 方案 | 可行性 | 缺少工作量 |
|------|--------|----------|
| Option A（僅 Tenant） | ✅ 高 | Schema + 1 API endpoint |
| Option B（Tenant + Admin） | ✅ 高 | Schema + 複合 Service + 1 API endpoint |
| 目前只能透過 DB seed | ✅ 可行但不理想 | — |

## Section 6 — Risk Summary

### 6.1 🔴 高風險項目

| # | 風險項目 | 說明 | 影響 |
|---|---------|------|------|
| R1 | `/admin` 路由不存在 | `Admin.vue` 無路由定義，管理功能完全無法透過 UI 訪問 | 管理員無法使用後台 |
| R2 | Session 恢復不驗證 token | `restoreSession()` 直接從 localStorage 讀取，不呼叫後端驗證；JWT 過期後前端仍視為已登入 | 過期 token 可繞過前端路由保護 |
| R3 | 無 tenant 管理 API | `TenantService` 完整但無 REST endpoint，無法透過 API 建立/管理租戶 | 無法上線新客戶 |
| R4 | 無 admin user 建立 API | 無法透過 API 為新租戶建立第一個管理員帳號 | 新租戶無法登入系統 |

### 6.2 🟡 中風險項目

| # | 風險項目 | 說明 | 影響 |
|---|---------|------|------|
| R5 | `/schedule` 無 role 驗證 | 任何已登入用戶（employee）皆可訪問排班管理，應限 admin | 員工可查看/操作排班 |
| R6 | JWT 15 分鐘過期無 refresh | 900 秒後 API 返回 401，但前端不自動重導登入頁 | 用戶操作中斷，體驗差 |
| R7 | super_admin 無前端入口 | 角色架構支援 super_admin 但前端完全沒有對應 UI | 平台管理無法操作 |
| R8 | localStorage role 可被竄改 | `localStorage['role']` 可被用戶手動修改影響 UI 顯示邏輯 | 前端 UI 顯示誤導（後端仍安全）|
| R9 | 報表頁無 role 保護 | `/attendance/reports/*` 對所有已登入用戶開放，應限 admin/manager | 員工可查看公司報表 |

### 6.3 🟢 已正確實作

| # | 項目 | 說明 |
|---|------|------|
| G1 | 後端 JWT 驗證完整 | `get_current_actor()` 每次請求驗證 JWT + user active + membership |
| G2 | Scope 隔離機制健全 | `ScopeChecker` 三層角色（super_admin / cs / company_user）邏輯正確 |
| G3 | 平台層三角色架構清晰 | UserRole enum 分層明確，公司內部角色透過 active_role_id 獨立 |
| G4 | Tenant 隔離貫穿後端 | 所有 query 均以 company_id 隔離，無跨租戶資料洩漏 |
| G5 | Anti-enumeration 策略 | 登入失敗統一返回 404 "Invalid credentials"，防止帳號枚舉 |
| G6 | Platform-First v2 架構 | User 全域身份設計，支援多公司 membership，架構現代 |
| G7 | Entitlement 管理有 scope 保護 | `PATCH /entitlements` 限 super_admin，`GET` 有公司 scope 驗證 |

### 6.4 風險優先順序

```
立即處理（阻塞上線）:
  R3 無 tenant 管理 API
  R4 無 admin user 建立 API

本 Sprint 處理（安全性）:
  R1 /admin 路由不存在
  R5 /schedule 無 role 驗證
  R2 Session 恢復不驗證 token

下 Sprint 處理（完整性）:
  R7 super_admin 前端入口
  R9 報表頁 role 保護
  R6 refresh token 機制
```

## Section 7 — Recommended Next Tickets

### WP-S1-08B — Route Access Control

**目標**: 修復前端路由保護漏洞，建立 role-based 路由守衛

**範圍**: 僅限前端路由守衛，不觸碰後端

**工作項目**:
1. 在 `router/index.js` 新增 `meta.requiresAdmin` 支援
2. `beforeEach` 加入 role 驗證邏輯：
   - 讀取 `authStore.userRole`
   - `requiresAdmin: true` 路由 → 非 admin 導向 403 或首頁
3. 為 `/schedule` 加入 `meta: { requiresAuth: true, requiresAdmin: true }`
4. 為 `/attendance/reports/*` 加入 `meta: { requiresAuth: true, requiresAdmin: true }`
5. 建立 `/admin` 路由，指向 `Admin.vue`，加入 `meta: { requiresAuth: true, requiresAdmin: true }`
6. 修復 `restoreSession()` — 加入 token 過期檢查（解析 JWT exp claim）
7. 建立簡單 403 Forbidden 頁面

**不需要**:
- 修改後端任何程式碼
- 修改 Admin.vue 內容（留給後續 ticket）
- 實作 refresh token（獨立 ticket）

**驗收條件**:
- employee 無法直接訪問 `/schedule`、`/admin`、`/attendance/reports/*`
- 過期 token 重整頁面後自動導向 `/login`
- admin 可正常訪問所有路由

---

### WP-S1-08C — Admin Test Account / Seed

**目標**: 建立 super_admin 測試帳號與公司 admin seed，使管理功能可測試

**工作項目**:
1. 建立 Alembic seed migration 或獨立 seed script：
   - 建立 `super_admin` role（若不存在）
   - 建立 system-level super_admin user（無 company_id，無 Membership）
   - 建立測試租戶 `company-a`（若不存在）
   - 建立 `company-a` 的 admin Membership
2. 確認 `roles` 表已有以下 role seeded：
   - `super_admin`, `admin`, `employee`, `manager`, `hr`, `customer_service`
3. 提供測試帳號清單文件

**驗收條件**:
- `POST /api/internal/auth/login` 可用 super_admin 帳號登入
- JWT 包含 `role_id: "super_admin"`
- `GET /api/admin/companies/{id}/entitlements` 可用 super_admin token 訪問

---

### WP-S1-09A — Tenant / Customer Creation Foundation

**目標**: 建立完整的租戶管理 API，支援 Option B（Tenant + 第一個 Admin User）

**工作項目**:

**Backend**:
1. `tenants/schemas.py` 新增：
   - `CreateTenantRequest`: `tenant_id`, `name`, `timezone`
   - `CreateTenantWithAdminRequest`: 上述 + `admin_username`, `admin_password`, `admin_display_name`, `admin_email`
   - `TenantResponse`: `id`, `name`, `is_active`, `timezone`, `created_at`
2. `tenants/service.py` 新增複合 Service：
   - `create_tenant_with_admin()`: 事務性建立 Tenant + User + Membership
3. `tenants/api.py` 新增端點：
   - `GET /api/admin/companies` — 列出所有租戶（super_admin only）
   - `POST /api/admin/companies` — 建立租戶（super_admin only）
   - `POST /api/admin/companies/{id}/users` — 建立租戶第一個 admin（super_admin only）
   - `GET /api/admin/companies/{id}` — 查看租戶詳情（super_admin / cs）

**Frontend**（可延後）:
- Admin.vue 實作租戶列表與建立表單
- 需要 WP-S1-08B 先完成（路由保護）

**驗收條件**:
- `POST /api/admin/companies` 可建立新租戶
- `POST /api/admin/companies/{id}/users` 可建立 admin Membership
- 新建立的 admin 可成功登入系統
- 所有端點限 super_admin 訪問，非 super_admin 返回 403

---

## Final Recommendation

### WP-S1-08A 完成狀態

✅ **WP-S1-08A 可標記為 COMPLETE**

所有審計範圍（Auth State / Route Protection / Role Architecture /
Global Admin / Customer Creation / Risk Summary / Next Tickets）
均已完整分析並記錄。

### 下一張工單建議

**優先開始**: **WP-S1-08C — Admin Test Account / Seed**

理由：
- WP-S1-08B 需要 role 驗證，但 super_admin / admin role 目前無 seed 帳號可測試
- WP-S1-09A 的 API 端點需要 super_admin token 才能測試
- WP-S1-08C 是最小工作量、最高解鎖價值的 ticket
- 完成 08C 後，08B 和 09A 可並行開發

**建議執行順序**:
```
WP-S1-08C（Seed）→ WP-S1-08B（Route Guard）
                 ↘ WP-S1-09A（Tenant API）
```

### WP-S1-08B 範圍建議

✅ **WP-S1-08B 應限定為前端路由守衛 only**

理由：
- 後端 scope/permission 機制已正確實作（G1-G7 均通過）
- 後端不需修改即可支援 role-based 訪問控制
- 前端路由保護是獨立的 UI 層問題
- 混入後端修改會擴大範圍、增加風險
- 後端 API 保護（schedule、reports）可在 WP-S1-09A 或獨立 ticket 處理

---

*報告生成時間: 2026-03-20*
*審計執行: READ-ONLY，未修改任何程式碼*
