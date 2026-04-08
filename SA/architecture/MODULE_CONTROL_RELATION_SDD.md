# 模組控制範圍與關係 SDD 基線

> 目的：根據**現況程式碼**與既有 `SA/` 文件，整理出目前系統各模組實際控制的功能、與其他模組的關係、未來新增/修改功能時的歸屬判斷依據。  
> 這份文件不是歷史藍圖，而是**現況可開發、可驗證、可回寫**的模組控制基線。

---

## 1. 文件定位

這份文件要回答 4 個核心問題：

1. 目前每個模組**實際控制哪些功能**
2. 每個模組和其他模組之間的**依賴與互動關係**
3. 新功能進來時，**應該放哪裡**
4. 哪些地方屬於**未來最容易失守的邊界**

如果你之後要做 SDD 補完、功能驗證、或判斷某段程式要不要搬家，這份文件應作為第一層依據。

---

## 2. 判斷原則

### 2.1 先看「主責任」再看程式位置
不是某功能目前寫在哪裡，就代表它應該永遠放那裡。

判斷順序應是：
1. 該功能的語意主責任是什麼
2. 現況程式是不是只是在過渡期承載它
3. 若現況與主責任不同，是否需要回寫修正或拆分

### 2.2 以現況程式為第一證據
本文件優先根據：
- `backend/app/main.py`
- `backend/app/core/*`
- `backend/app/modules/*`
- `frontend/src/*`

來判斷模組控制範圍。

### 2.3 `SA/` 是正式開發基線
`docs/` 僅作為歷史來源，不再作為當前模組責任判斷的唯一依據。

---

## 3. 系統模組分層

### 3.1 Platform Core
位於：`backend/app/core/`

控制內容：
- JWT actor 建立
- active company scope 注入
- 平台層角色與公司內 RBAC 區分
- feature gate 驗證
- event bus
- database / config / exception

### 3.2 Backend Business / Governance Modules
位於：`backend/app/modules/`

目前實際存在：
- `attendance`
- `schedule`
- `auth`
- `tenants`
- `leave`
- `notifications`
- `audit`
- `backup`
- `customer_service`

### 3.3 Frontend Application Layer
位於：`frontend/src/`

控制內容：
- route guard
- auth store / session restore
- API client
- views / page-level interaction

---

## 4. 系統總體模組關係圖

```mermaid
flowchart TD
    FE[frontend]\n    API[FastAPI routers]\n    CORE[core]\n
    AUTH[auth]
    TENANTS[tenants]
    ATT[attendance]
    SCHEDULE[schedule]
    LEAVE[leave]
    NOTI[notifications]
    AUDIT[audit]
    BACKUP[backup]
    CS[customer_service]

    FE --> API
    API --> CORE

    CORE --> AUTH
    CORE --> TENANTS
    CORE --> ATT
    CORE --> SCHEDULE
    CORE --> LEAVE
    CORE --> NOTI
    CORE --> AUDIT
    CORE --> BACKUP
    CORE --> CS

    SCHEDULE -->|baseline / expected work time| ATT
    ATT -->|domain events| NOTI
    AUTH -->|identity lookup| CORE
    TENANTS -->|company / membership / entitlement basis| CORE
    CS -->|support scope| CORE
    TENANTS --> BACKUP
    TENANTS --> AUDIT
    TENANTS --> LEAVE
```

---

## 5. 模組控制總表

| 模組 | 目前控制的功能 | 主要輸入/依賴 | 主要輸出 | 未來新增功能判斷 |
|---|---|---|---|---|
| `core` | actor、scope、RBAC、feature gate、event bus | JWT、DB、tenant/member data | 已驗證 actor / scope / feature capability | 凡是跨模組共用平台能力，先看是否屬於 core |
| `auth` | 登入、帳密驗證、JWT 發放、membership/role 查詢 | user、membership、role 資料 | access token、登入後身份資訊 | 凡是「你是誰、怎麼登入、token 帶什麼」都應先看 auth |
| `tenants` | 公司 CRUD、members、onboarding、entitlements | actor、tenant data | company / member / entitlement 管理能力 | 凡是「公司這個租戶單位本身的管理」都優先放 tenants |
| `attendance` | 打卡、break、session、checkpoint、work hour、policy、reporting、location | actor、feature gate、schedule baseline | 出勤事件、session、summary、policy result、events | 凡是「實際發生的出勤事實」都優先放 attendance |
| `schedule` | shift templates、shift assignments、effective schedule lookup、baseline export | actor、feature gate | normalized shift window / expected work time | 凡是「應該怎麼上班」優先放 schedule |
| `leave` | 請假申請、個人列表、待審核、approve/reject | actor、feature gate | leave lifecycle result | 凡是請假生命週期與審核，都先看 leave |
| `notifications` | 事件消費、通知落地、通知查詢 | domain events、actor scope | notification records | 凡是事件轉通知，不是主業務決策，都放 notifications |
| `audit` | audit logs query/export、retention、purge | actor、RBAC、audit repo | audit 查詢與治理結果 | 凡是稽核查詢與保留政策，都放 audit |
| `backup` | 單一公司資料匯出/還原、備份資料驗證 | actor、RBAC、tenant data | backup payload / restore result | 凡是公司級資料搬運與還原，都放 backup |
| `customer_service` | support assignment、assigned companies、客服 scope | actor、support assignment data | 可支援 company 範圍 | 凡是客服跨公司支援邊界，都放 customer_service |
| `frontend` | route guard、session、API 呼叫、頁面互動 | token、API response | UI state / navigation | 凡是畫面流程與使用者互動，都放 frontend |

---

## 6. 各模組詳細 SDD 摘要

## 6.1 `core`

### 控制的功能
- `dependencies.py`
  - 從 Authorization Bearer token 建立 `Actor`
  - 驗證 user、membership、support assignment
  - 注入 `active_company_id`、`active_role_id`
- `scope.py`
  - 定義平台角色：`super_admin` / `customer_service` / `company_user`
  - 區分公司內角色：`company_admin` / `hr_manager` / `employee`
  - 提供 `assert_company_scope`、`assert_admin_scope`
- `features.py` / `feature_service.py`
  - feature gate
- `event_bus.py`
  - 跨模組事件傳遞

### 不應控制的功能
- 任一具體業務模組自己的 domain rule
- 公司 CRUD、打卡規則、請假判定這類模組主責任

### 與其他模組的關係
- 所有 backend 模組都依賴 `core`
- 它是平台規範與共用機制，不是業務 owner

### 新功能歸屬規則
若功能是以下任一種，優先考慮放 `core`：
- 所有模組都會共用的身份驗證
- 所有模組都會共用的 scope / RBAC
- 所有模組都會共用的 feature gate
- 所有模組都會共用的事件機制

---

## 6.2 `auth`

### 現況程式控制的功能
根據 `backend/app/modules/auth/api.py` 與對應 service/repo：
- `POST /api/internal/auth/login`
- 以 `company_id + login_username + password` 做登入
- 驗證 user / membership / role
- 回傳 JWT token、user、company、role

### 實際控制邊界
`auth` 控制的是：
- 登入入口
- 帳密驗證
- token claims 內容
- 身份查詢與建立

### 不應控制
- 公司 CRUD
- entitlements
- attendance / leave / schedule 業務規則

### 與其他模組關係
- `core.dependencies` 透過 `AuthRepository` 補齊 actor 驗證流程
- `frontend` 的 `auth store` 消費其登入回應
- 其他業務模組消費 token 結果，但不應依賴 `auth` 承載業務邏輯

### 未來新增/修改依據
若你要改：
- 登入方式
- JWT claims
- company login identity
- membership / role 取得方式

應先看 `auth`。

---

## 6.3 `tenants`

### 現況程式控制的功能
根據 `backend/app/modules/tenants/api.py` 與子路由：
- 公司清單 / 單一公司 / 建立 / 更新
- entitlements 管理
- onboarding 管理
- members 管理

### 實際控制邊界
`tenants` 控制的是：
- company 作為租戶單位本身的資料
- company member 關係
- onboarding
- feature entitlement source of truth

### 不應控制
- JWT 發放
- 實際打卡與出勤計算
- 請假申請本身

### 與其他模組關係
- `auth` 會消費 membership / role 資料
- `core` 的 scope 驗證與 feature gate 會依賴 tenant / member / entitlement 基礎資料
- `backup`、`audit`、`leave`、`attendance` 都會間接受其治理規則影響

### 未來新增/修改依據
若功能是：
- 公司主檔管理
- 公司成員管理
- entitlement 啟閉
- onboarding lifecycle

應優先放 `tenants`。

---

## 6.4 `attendance`

### 現況程式控制的功能
根據 `backend/app/modules/attendance/` 結構與 API：
- `api.py` / `api/*`
  - punch in / punch out
  - break out / break in
  - current status / history / sessions
  - summary / reporting
  - checkpoint
  - legacy compatibility route
- `service.py` / `repo.py`
  - 核心交易流程與資料存取
- `policy_engine.py` / `policy_rules.py` / `work_hour_engine.py`
  - 遲到、早退、加班等政策判定
- `reporting_repo.py` / `reporting_service.py`
  - 報表查詢子域
- `location_policy_service.py` / `admin_location_api.py`
  - 打卡地點限制與管理

### 實際控制邊界
`attendance` 現在實際控制：
- 實際發生的出勤事實
- session lifecycle
- break / checkpoint 事件
- 工時計算
- attendance policy
- attendance reporting
- location policy

### 不應控制
- 公司治理
- JWT 驗證
- shift template / assignment 的 source of truth
- 請假生命週期

### 與其他模組關係
- 依賴 `core`：actor、scope、feature gate
- 消費 `schedule`：取得 baseline / expected work time
- 發事件給 `notifications`
- 受 `tenants` 的 company scope / entitlements 約束
- 可能與 `leave` 在業務上有相鄰語意，但不應互相吞掉主責任

### 未來新增/修改依據
若功能是以下任一種，優先放 `attendance`：
- punch / break / checkpoint
- session 開關閉
- duration persistence
- attendance summary / reporting
- attendance policy
- 出勤位置限制

### 目前最需要注意的邊界風險
- 模組過胖
- reporting 尚未獨立
- location 仍內嵌於 attendance
- legacy 與新 flow 並存

---

## 6.5 `schedule`

### 現況程式控制的功能
根據 `backend/app/modules/schedule/api.py`：
- `POST/GET/PATCH` shift template
- activate / deactivate template
- `POST/GET/PATCH/cancel` shift assignment
- 透過 service/repo 提供 effective schedule lookup 與 baseline export
- 使用 `schedule.core` feature gate

### 實際控制邊界
`schedule` 控制的是：
- 班表模板
- 班別指派
- 預期工作時間定義
- 提供給 `attendance` 的標準化班表基線

### 不應控制
- 實際打卡寫入
- 最終 attendance policy judgement
- JWT / login

### 與其他模組關係
- 依賴 `core` 的 actor 與 feature gate
- 被 `attendance` 消費作為 baseline source
- 不應反向主導 attendance actual event semantic

### 未來新增/修改依據
若功能是：
- shift template lifecycle
- shift assignment lifecycle
- effective schedule lookup
- normalized shift window export

應優先放 `schedule`。

---

## 6.6 `leave`

### 現況程式控制的功能
根據 `backend/app/modules/leave/api.py`：
- `POST /api/v1/leave/requests`
- `GET /api/v1/leave/my-requests`
- `GET /api/v1/leave/pending`
- `POST /api/v1/leave/requests/{id}/approve`
- `POST /api/v1/leave/requests/{id}/reject`
- 使用 `leave.core` feature gate

### 實際控制邊界
`leave` 控制的是：
- 請假申請
- 請假清單
- 待審核流程
- approve / reject 生命周期

### 不應控制
- attendance 打卡與工時計算
- 排班 template / assignment
- 公司治理

### 與其他模組關係
- 依賴 `core` 的 actor 與 feature gate
- 受 `tenants` 的 company scope 規則約束
- 與 `attendance` 有相鄰業務語意，但目前仍應保持獨立

### 未來新增/修改依據
若功能是請假申請、審核、請假資料查詢，優先放 `leave`。

---

## 6.7 `notifications`

### 現況程式控制的功能
根據 `backend/app/modules/notifications/`：
- 事件 handler
- 通知資料落地
- `GET /api/notifications`

### 實際控制邊界
`notifications` 控制的是：
- 事件消費
- 通知資料保存
- 通知查詢

### 不應控制
- 主業務決策
- 反向改寫 attendance / leave / schedule 狀態

### 與其他模組關係
- 依賴 `core.event_bus`
- 目前明確消費 `attendance` 事件
- 是 consumer，不是 semantic owner

### 未來新增/修改依據
若功能是：
- 新事件轉通知
- 通知查詢
- 通知格式調整

應放 `notifications`。

---

## 6.8 `audit`

### 現況程式控制的功能
根據 `backend/app/modules/audit/api.py`：
- `GET /api/audit/logs`
- `GET /api/audit/export`
- `GET /api/audit/retention`
- retention policy 更新
- purge
- 匯出與治理操作需 admin RBAC

### 實際控制邊界
`audit` 控制的是：
- audit logs query
- export
- retention
- purge

### 不應控制
- 一般業務流程本身
- 備份還原
- 登入驗證

### 與其他模組關係
- 依賴 `core` scope / actor
- 受 `tenants` 的 company scope 約束
- 與 `backup` 同屬治理能力，但不是同一模組責任

### 未來新增/修改依據
凡是可追蹤紀錄的查詢、匯出、保留規則，優先放 `audit`。

---

## 6.9 `backup`

### 現況程式控制的功能
根據 `backend/app/modules/backup/api.py` 與檔案結構：
- `POST /api/backup/export`
- `POST /api/backup/restore`
- exporter / importer / validator
- admin RBAC 控制

### 實際控制邊界
`backup` 控制的是：
- 單一公司資料匯出
- 單一公司資料還原
- 還原前後的資料一致性與 company scope 驗證

### 不應控制
- 一般業務邏輯
- 稽核查詢本身
- auth / login

### 與其他模組關係
- 依賴 `core` scope / RBAC
- 受 `tenants` 的 company 資料邊界約束
- 與 `audit` 在治理面有關聯，但各自主責任不同

### 未來新增/修改依據
凡是公司級資料搬運、備份格式、restore validation，優先放 `backup`。

---

## 6.10 `customer_service`

### 現況程式控制的功能
根據 `backend/app/modules/customer_service/api.py`：
- `GET /api/customer-service/assigned-companies`
- `POST /api/customer-service/assignments`
- `DELETE /api/customer-service/assignments`

### 實際控制邊界
`customer_service` 控制的是：
- 客服被指派到哪些公司
- 客服可操作 company scope 的來源資料

### 不應控制
- tenant 主資料管理
- attendance / leave 業務
- 一般 company admin 流程

### 與其他模組關係
- `core.dependencies` 會查 `SupportCompanyAssignment`
- 它是 customer_service 平台角色可操作範圍的 source of truth
- 與 `tenants`、`auth`、`core` 有治理層關聯

### 未來新增/修改依據
凡是客服支援範圍、客服跨公司授權，優先放 `customer_service`。

---

## 6.11 `frontend`

### 現況程式控制的功能
根據 `frontend/src/router/index.js` 與 `stores/auth.js`：
- session restore
- token / user / company / role 保持
- route guard
- 頁面權限導向
- attendance reports / schedule / admin / leave 等頁面入口

### 實際控制邊界
`frontend` 控制的是：
- 使用者看到什麼畫面
- 頁面導流與 UI 層限制
- API 呼叫與狀態管理

### 不應控制
- 最終 RBAC
- tenant isolation 的權威判斷
- 後端 canonical business rule

### 與其他模組關係
- 消費 `auth` 登入回應
- 消費各 backend module API
- 以 route guard 輔助 UX，但不取代後端授權

### 未來新增/修改依據
若功能是新頁面、路由保護、store 狀態、API 呼叫行為，優先放 `frontend`。

---

## 7. 跨模組關係規則

## 7.1 允許的主要依賴
- 所有模組可依賴 `core`
- `attendance` 可讀取 `schedule` baseline
- `notifications` 可消費 `attendance` 事件
- `frontend` 可消費 backend API，但不可依賴 backend 實作細節

## 7.2 應避免的依賴
- 模組直接操作其他模組主資料表
- 模組直接承接其他模組 service 主責任
- API 層長期變成跨模組 orchestrator
- 前端私自複製後端權威規則

---

## 8. 新增功能時的歸屬判斷表

| 如果功能是… | 優先歸屬模組 |
|---|---|
| 登入、帳密驗證、JWT claims | `auth` |
| 公司資料、成員、entitlements、onboarding | `tenants` |
| 打卡、break、session、工時、出勤報表、出勤政策 | `attendance` |
| 班別模板、班表指派、預期工作時段 | `schedule` |
| 請假申請、審批、請假列表 | `leave` |
| 事件轉通知、通知記錄 | `notifications` |
| 稽核查詢、匯出、保留、清理 | `audit` |
| 公司級備份、還原、驗證 | `backup` |
| 客服可支援的公司範圍 | `customer_service` |
| 畫面、導頁、store、前端 API client | `frontend` |
| 所有模組共用的 actor/scope/feature/event 機制 | `core` |

---

## 9. 目前最值得優先治理的邊界

### 9.1 `attendance` 過胖
這是目前最需要持續用 SDD 管住的模組。

要特別注意：
- capture
- reporting
- policy
- location
- legacy

這些現在雖都在 `attendance` 內，但應視為不同子域。

### 9.2 `schedule -> attendance` 契約
這是目前系統很重要的邊界：
- `schedule` 定義應上班的基線
- `attendance` 定義實際發生的出勤事實

這條邊界不能模糊。

### 9.3 `frontend` 只能做 UX guard
前端可以擋頁面，但最終權限與 tenant isolation 一律以 backend 為準。

---

## 10. 未來修改時的最低回寫要求

若你未來修改任一模組，至少應同步更新：

- `SA/modules/<module>.md`
- 若有跨模組邊界變更，再更新：
  - `SA/architecture/SYSTEM_SDD.md`
  - `SA/architecture/MODULE_BOUNDARY_MATRIX.md`
  - `SA/architecture/MODULE_CONTROL_RELATION_SDD.md`

---

## 11. 建議使用方式

### 當你要驗證某功能該放哪裡
先看：
1. 本文件第 5 節模組控制總表
2. 本文件第 6 節模組詳細摘要
3. 對應 `SA/modules/<module>.md`

### 當你要判斷某功能是否該搬家
先問：
1. 它的語意主責任是什麼？
2. 它現在所在模組是正式設計還是過渡承載？
3. 搬動後是否破壞 tenant / scope / feature / event 契約？
4. 搬動後是否更清楚模組邊界？

---

## 12. 關聯文件

- `SA/architecture/SYSTEM_SDD.md`
- `SA/architecture/MODULE_BOUNDARY_MATRIX.md`
- `SA/architecture/SYSTEM_ARCHITECTURE_DIAGRAM.md`
- `SA/architecture/PLANNED_VS_IMPLEMENTED_MATRIX.md`
- `SA/modules/attendance.md`
- `SA/modules/schedule.md`
- `SA/modules/auth.md`
- `SA/modules/tenants.md`
- `SA/modules/leave.md`
- `SA/modules/notifications.md`
- `SA/modules/audit.md`
- `SA/modules/backup.md`
- `SA/modules/customer_service.md`
- `SA/modules/frontend.md`
