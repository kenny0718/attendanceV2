# WP-S1-12B Admin x Attendance — Security & Scope Validation Audit

**文件類型：** Security & Scope Validation Audit Report  
**稽核日期：** 2026-03-27  
**稽核對象：** S1-12 Admin x Attendance（B版）實作  
**執行者：** AI Audit Session  
**狀態：** FINAL

---

## 1. Summary（總結）

S1-12 B版整體**條件可接受**，安全性無高風險問題，但存在兩個必須修正的功能性問題：

| ID | 問題 | 風險等級 | 是否阻塞 |
|----|------|---------|--------|
| RISK-01 | 員工名稱欄位永遠顯示 `—`（SessionResponse 無 display_name） | High | ✅ 阻塞（核心欄位失效）|
| RISK-02 | 所有日期查詢必然失敗 422（前端傳 naive 日期字串，backend 要求 timezone-aware）| Medium | ✅ 阻塞（頁面完全無法使用）|
| RISK-03 | super_admin 使用頁面時永遠空白（active_company_id=null）| Medium | ⚠️ 功能失效，非安全問題 |
| RISK-04 | 日期邊界 off-by-one（UTC vs Asia/Taipei 午夜）| Low | ❌ 不阻塞 |
| RISK-05 | 進階 session status 未處理（pending/missing_punch_out 等）| Low | ❌ 不阻塞 |

**安全性判定：無跨公司資料洩漏、無越權查詢、無 JWT bypass。**  
主要問題為功能層面，修正 RISK-01 + RISK-02 後頁面可進入可用狀態。

---

## 2. Files Inspected（已檢查的檔案）

### Frontend
- `frontend/src/api/attendance.js`
- `frontend/src/views/admin/AdminAttendanceView.vue`
- `frontend/src/router/index.js`（從 git HEAD 取得）
- `frontend/src/views/Admin.vue`（從 git HEAD 取得）
- `frontend/src/api/client.js`
- `frontend/src/stores/auth.js`
- `frontend/.env.development` / `frontend/.env.production`
- `frontend/vite.config.js`

### Backend
- `backend/app/modules/attendance/api.py`（完整閱讀）
- `backend/app/modules/attendance/repo.py`（ReportingRepository 段落）
- `backend/app/modules/attendance/schemas.py`（SessionResponse 定義）
- `backend/app/core/dependencies.py`（get_actor_with_company 完整邏輯）
- `backend/app/core/scope.py`（Actor、is_admin()、has_active_company()）
- `backend/app/modules/attendance/docs.md`（節錄）

### Docs
- `docs/00_AI_GOVERNANCE/AI_CONTEXT.md`
- `docs/00_AI_GOVERNANCE/CURSOR_DEVELOPMENT_RULES.md`
- `docs/01_ARCHITECTURE/ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md`
- `docs/01_ARCHITECTURE/ROLE_NAMING_SOURCE_OF_TRUTH.md`
- `docs/03_WP_CONTROL/NEXT_WP_TICKET.md`
- `docs/03_WP_CONTROL/ATTENDANCE_DEVELOPMENT_ROADMAP.md`

---

## 3. API Path Verification（API 路徑驗證）

### 前端呼叫路徑

```js
// frontend/src/api/attendance.js
getAdminAttendanceSessions: (params = {}) =>
  apiClient.get('/v1/attendance/sessions', { params })
```

### apiClient baseURL 設定

```js
// frontend/src/api/client.js
baseURL: import.meta.env.VITE_API_BASE || '/api'
// .env.development: VITE_API_BASE=/api
// .env.production:  VITE_API_BASE=/api
```

實際請求 URL = `/api` + `/v1/attendance/sessions` = **`/api/v1/attendance/sessions`**

### Backend 路由

```python
# backend/app/modules/attendance/api.py
router_v1 = APIRouter(prefix="/api/v1/attendance")

@router_v1.get("/sessions", response_model=SessionsListResponse)
async def get_sessions_reporting(...):
```

最終掛載路徑 = `/api/v1/attendance/sessions`

### vite.config.js proxy（dev）

```js
proxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true } }
```

### 判定：✅ API Path 完全一致

frontend `/v1/...` + baseURL `/api` = `/api/v1/attendance/sessions` = backend router_v1 prefix，dev proxy 正確轉發。無不一致問題。

---

## 4. Authorization Verification（授權鏈驗證）

### Backend 完整權限控制鏈

```
GET /api/v1/attendance/sessions
  |
  v
get_actor_with_company (dependencies.py)
  |-- get_current_actor()：JWT decode -> user 存在驗證 -> role mapping
  |-- actor.has_active_company()：
  |     super_admin -> True（不強制 active_company_id）
  |     company_user / cs -> 需要 active_company_id
  v
_require_attendance_feature(company_id, db)
  |-- Feature Gate 驗證（attendance.core）
  v
user scope 解析：
  |-- actor.is_admin() -> True（super_admin / company_admin / hr_manager）
  |     -> 可傳 user_id 查詢任意員工
  |-- actor.is_admin() -> False（employee）
        -> 只能查自己（傳入他人 user_id -> 403）
  v
ReportingRepository.get_sessions_for_reporting(
  company_id = actor.active_company_id,  <- 來自 JWT，非前端傳入
  user_id    = target_user_uuid,
  ...
)
  |-- 強制 WHERE company_id = ? AND user_id = ?
```

### 前端 Router Guard

```js
// router/index.js — step 5
if (to.meta.requiresAdminAccess) {
  if (!authStore.isSuperAdmin && !authStore.isAdminAccess) {
    next('/')
    return
  }
}
// auth.js
isSuperAdmin:  role?.id === 'super_admin'
isAdminAccess: ['company_admin', 'hr_manager'].includes(role?.id)
```

允許：`super_admin`、`company_admin`、`hr_manager`  
拒絕：`employee`、未登入

### 前後端角色判斷一致性

| 角色 | Frontend guard | Backend is_admin() | 結果 |
|------|---------------|-------------------|------|
| super_admin | 允許進入 | True（is_super_admin()）| 一致 |
| company_admin | 允許進入 | True（active_role_id）| 一致 |
| hr_manager | 允許進入 | True（active_role_id）| 一致 |
| employee | 拒絕進入 | False | 一致 |

### 判定：✅ 授權鏈正確，前後端一致

---

## 5. Tenant Scope Verification（租戶隔離驗證）

### company_id 來源追蹤

```python
# api.py
company_id = actor.active_company_id  # 來自 JWT claim，由 get_actor_with_company 驗證

# repo.py
query = self.db.query(AttendanceSession).filter(
    AttendanceSession.company_id == company_id  # 強制 WHERE
)
```

`company_id` 完全從 JWT 取得，前端無法偽造。

### user_id filter 跨公司風險分析

**Case 1：company_admin / hr_manager 傳入他人 user_id**

```python
# api.py
target_user_uuid = requested_uuid  # 允許傳入任意 user_id

# repo.py
query.filter(AttendanceSession.company_id == company_id)  # 先過濾公司
     .filter(AttendanceSession.user_id == user_id)         # 再過濾用戶
```

即使 user_id 屬於其他公司的員工，`WHERE company_id = ?` 確保只返回本公司資料 -> **無跨公司洩漏**。

**Case 2：super_admin 的 active_company_id**

`scope.py` 中：
```python
def has_active_company(self) -> bool:
    if self.is_super_admin():
        return True  # 不強制驗證 active_company_id
    return self.active_company_id is not None
```

- JWT 帶 company_id：`active_company_id` = 指定公司，查詢正常。
- JWT 無 company_id：`active_company_id = None`，repo `WHERE company_id = NULL` 返回空集合（無報錯，功能失效但不洩漏）。

**此為 RISK-03，功能問題而非安全問題。**

### 判定：✅ 無 cross-company 洩漏風險。repo 層 WHERE company_id = ? 是安全底線。

---

## 6. Timezone / Date Semantics Verification（時區與日期語義驗證）

### 前端日期產生方式

```js
// AdminAttendanceView.vue
const today       = new Date().toISOString().slice(0, 10)              // "2026-03-27"（UTC 基準）
const sevenDaysAgo = new Date(Date.now() - 6 * 86400000).toISOString().slice(0, 10)  // "2026-03-21"

const params = {
  start_date: filters.value.start_date,  // 純日期字串，例："2026-03-21"
  end_date:   filters.value.end_date      // 純日期字串，例："2026-03-27"
}
```

### Backend 對日期參數的要求

```python
# api.py — GET /sessions
if start_date is not None and start_date.tzinfo is None:
    raise HTTPException(
        status_code=422,
        detail="start_date must be timezone-aware (naive datetime rejected)"
    )
```

FastAPI 收到 `"2026-03-21"` -> 解析為 naive datetime -> **422 拒絕**。

這意味著 AdminAttendanceView 的 `onMounted` 自動查詢必然失敗，頁面顯示 error 狀態。

### 系統既有時區政策

`ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md §8.3`：
> Session ownership date = punch_in_time 的 Asia/Taipei 日期

`WP-11-07 Completion Notes`：
> Timezone display confirmed（Asia/Taipei，dayjs.tz 