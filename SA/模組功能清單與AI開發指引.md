# 模組功能清單與 AI 開發指引

> 這份文件是正式開發入口索引。  
> 目的不是取代各模組 SDD，而是讓你在開始修改前，先快速判斷：**這個功能應該放哪個模組、先看哪些檔案、哪些內容不該混進去。**

---

## 1. 使用方式

當你準備修改功能時，先回答三件事：

1. 這是平台共用能力，還是某個業務模組功能？
2. 這次改的是身分 / scope / RBAC、公司資料、出勤、排班，還是治理能力？
3. 這次改動的 source of truth 在 `core`、某個 backend module，還是 `frontend`？

若無法立刻回答，先看：
- `SA/architecture/SYSTEM_SDD.md`
- `SA/architecture/MODULE_CONTROL_RELATION_SDD.md`
- 對應 `SA/modules/*.md`

---

## 2. `core`

> 中文定位：平台共用能力模組  
> 英文定位：shared platform capabilities

### 功能 1：Actor / Scope / RBAC
- 中文說明：
  - 從 JWT 建立 `Actor`
  - 驗證 user / membership / active company scope
  - 區分平台角色與公司內角色
  - 提供公司管理層 scope 檢查（`company_admin` / `hr_manager` / `super_admin`）
- 常見檔案：
  - `backend/app/core/dependencies.py`
  - `backend/app/core/scope.py`
- 不該放進來的內容：
  - tenants 的公司管理流程
  - 前端 route guard
  - 某模組自己的 UI 權限顯示
- AI 修改規則：
  - 凡是會影響全部模組的 actor / scope / RBAC，優先檢查 `core`
  - 不要只改前端權限顯示，卻不改 backend 權威驗證

### 功能 2：Feature Gate
- 中文說明：
  - 決定某公司能不能使用某功能
  - 在 API / service 邊界執行 entitlement 檢查
- 常見檔案：
  - `backend/app/core/features.py`
  - `backend/app/core/feature_service.py`
- AI 修改規則：
  - 若新增的是全系統共用功能開關，優先放 `core`
  - 單一模組內部的純流程判斷，不必硬塞進 `core`

### 功能 3：Event Bus
- 中文說明：
  - 提供模組之間的內部同步事件傳遞機制
- 常見檔案：
  - `backend/app/core/event_bus.py`
- AI 修改規則：
  - `core` 只提供事件機制，不負責業務語意本身
  - 不要把 upstream streaming / webhook provider / SSE 概念直接混進目前 event bus

---

## 3. `auth`

> 中文定位：身份與登入模組  
> 英文定位：authentication / identity

### 功能 1：登入（login）
- 中文說明：
  - 使用者輸入 `company_id + login_username + password` 登入
- 常見檔案：
  - `backend/app/modules/auth/api.py`
  - `backend/app/modules/auth/service.py`
- 不該放進來的內容：
  - 公司 CRUD
  - attendance 主流程
- AI 修改規則：
  - 只要是登入入口、帳密驗證、JWT 發放，優先看 `auth`

### 功能 2：JWT / identity lookup
- 中文說明：
  - 產生 access token
  - 決定 token claims
  - 查詢 user / membership / role，支援 actor 建立
- 常見檔案：
  - `backend/app/modules/auth/service.py`
  - `backend/app/modules/auth/repo.py`
  - `backend/app/modules/auth/models.py`
- AI 修改規則：
  - 若 claims 改動，必須同步檢查 `core.dependencies`
  - 若登入後回傳 user / company / role 結構改了，要同步檢查前端 `auth store`

---

## 4. `tenants`

> 中文定位：公司與租戶管理模組  
> 英文定位：tenant management

### 功能 1：公司資料管理（company CRUD）
- 中文說明：
  - 建立、查詢、更新公司資料
  - 管理品牌欄位與公司 detail 資料
- 常見檔案：
  - `backend/app/modules/tenants/api.py`
  - `backend/app/modules/tenants/service.py`
  - `backend/app/modules/tenants/schemas.py`
- AI 修改規則：
  - 凡是「公司這個租戶單位本身的管理」，優先放 `tenants`

### 功能 2：members / onboarding / entitlements
- 中文說明：
  - 公司成員管理
  - onboarding
  - entitlement / feature 管理
- 常見檔案：
  - `backend/app/modules/tenants/api_members.py`
  - `backend/app/modules/tenants/api.py`
- 不該放進來的內容：
  - login token 發放
  - attendance policy
  - leave approval lifecycle
- AI 修改規則：
  - 不要把所有管理後台東西都塞進 `tenants`
  - 若牽涉公司主資料、members、entitlements，先看 `tenants`

---

## 5. `attendance`

> 中文定位：出勤模組  
> 英文定位：attendance / time tracking

### 功能 1：打卡與 session 流程
- 中文說明：
  - punch in / punch out
  - break / checkpoint
  - session close
- 常見檔案：
  - `backend/app/modules/attendance/api.py`
  - `backend/app/modules/attendance/service.py`
  - `backend/app/modules/attendance/repo.py`
- AI 修改規則：
  - 凡是「實際發生的出勤事實」，優先放 `attendance`

### 功能 2：policy / work hour / reporting
- 中文說明：
  - attendance policy
  - 工時計算
  - summary / reporting
  - location policy enforcement
- 常見檔案：
  - `backend/app/modules/attendance/policy_*`
  - `backend/app/modules/attendance/work_hour_engine.py`
  - `backend/app/modules/attendance/reporting_*`
- AI 修改規則：
  - 不要把 reporting 當成交易寫入補救層
  - 若碰到 boundary、summary、employee / HR 視圖，先看 `SA/modules/attendance-reporting.md`

---

## 6. `schedule`

> 中文定位：排班模組  
> 英文定位：schedule / shift planning

### 功能 1：Shift templates / assignments
- 中文說明：
  - 管理班表模板
  - 管理排班指派
  - 提供 effective schedule lookup / baseline export
- 常見檔案：
  - `backend/app/modules/schedule/api.py`
  - `backend/app/modules/schedule/service.py`
  - `backend/app/modules/schedule/repo.py`
- AI 修改規則：
  - 凡是「應該怎麼上班」，優先放 `schedule`
  - 不要讓 `schedule` 反向主導 attendance actual event semantic

---

## 7. `notifications`

> 中文定位：通知模組  
> 英文定位：notifications

### 功能 1：事件轉通知
- 中文說明：
  - 消費 domain events
  - 建立通知資料
  - 提供通知查詢
- 常見檔案：
  - `backend/app/modules/notifications/event_handlers.py`
  - `backend/app/modules/notifications/api.py`
- AI 修改規則：
  - 凡是事件轉通知，不是主業務決策，都放 `notifications`

---

## 8. `audit`

> 中文定位：稽核模組  
> 英文定位：audit / governance logging

### 功能 1：查詢 / 匯出 / retention / purge
- 中文說明：
  - audit logs query
  - export
  - retention
  - purge
- 常見檔案：
  - `backend/app/modules/audit/api.py`
  - `backend/app/modules/audit/service.py`
- AI 修改規則：
  - 凡是稽核查詢與保留政策，優先放 `audit`
  - 不要把 audit 做成任何東西都往裡面塞的雜物箱

---

## 9. `backup`

> 中文定位：公司級備份還原模組  
> 英文定位：backup / restore

### 功能 1：單一公司資料匯出 / 還原
- 中文說明：
  - backup export
  - restore
  - consistency / validation
- 常見檔案：
  - `backend/app/modules/backup/api.py`
  - `backend/app/modules/backup/service.py`
  - `backend/app/modules/backup/validator.py`
- AI 修改規則：
  - 凡是公司級資料搬運與 restore validation，優先放 `backup`
  - 不要把 auth / login 流程混進 `backup`

---

## 10. `customer_service`

> 中文定位：客服跨公司支援模組  
> 英文定位：customer service scope

### 功能 1：support assignment / assigned companies
- 中文說明：
  - 管理客服可操作公司範圍
  - 維護 support assignment
- 常見檔案：
  - `backend/app/modules/customer_service/api.py`
  - `backend/app/modules/customer_service/service.py`
- AI 修改規則：
  - 凡是客服跨公司支援邊界，優先放 `customer_service`
  - 不要把 `customer_service` 跟 `company_admin` 混為一談

---

## 11. `frontend`

> 中文定位：前端頁面與互動層  
> 英文定位：frontend UI / navigation

### 功能 1：route guard / session / API 呼叫
- 中文說明：
  - route guard
  - session restore
  - API client
  - UI state / navigation
- 常見檔案：
  - `frontend/src/router/`
  - `frontend/src/stores/`
  - `frontend/src/api/`
  - `frontend/src/views/`
- AI 修改規則：
  - 凡是畫面流程與使用者互動，都放 `frontend`
  - 前端 guard 不能取代 backend scope / RBAC 驗證

---

## 12. 修改前最少檢查清單

在開始改任何功能前，至少先確認：

1. 這個功能的責任模組是哪一個？
2. 這次改的是平台能力，還是業務語意？
3. backend 權威驗證是否也要同步調整？
4. 是否已有正式 SDD / 模組文件可依據？
5. 是否會影響前端 route、auth store、API schema、feature gate 或 audit？

---

## 13. 對應正式文件

- 架構總覽：`SA/architecture/SYSTEM_SDD.md`
- 模組責任與控制邊界：`SA/architecture/MODULE_CONTROL_RELATION_SDD.md`
- 出勤模組：`SA/modules/attendance.md`
- 出勤報表：`SA/modules/attendance-reporting.md`
- 公司 / 租戶：`SA/modules/tenants.md`
- 稽核：`SA/modules/audit.md`
- 備份還原：`SA/modules/backup.md`
- 前端：`SA/modules/frontend.md`

---

## 14. 維護原則

- 這份文件只做「入口索引」與「模組定位」，不取代各模組正式 SDD
- 若模組責任變動，應先更新對應 `SA/modules/*.md` 與架構文件，再回寫這份索引
- 若這份與正式 SDD 衝突，以 `SA/architecture/*` 與 `SA/modules/*` 為準
