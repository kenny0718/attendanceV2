# 模組功能清單與 AI 開發指引

> 目的：把系統模組整理成**中文主說明 + 英文關鍵詞保留**的格式，讓你自己看得懂，也讓 AI 寫程式時能有清楚依據。  
> 使用方式：你之後如果要新增或修改功能，先看這份，再直接告訴 AI：  
> 「我要改 `某模組` 的 `某功能`，請依 `SA/模組功能清單與 AI 開發指引.md` 判斷功能歸屬、實作並同步回寫文件。」

---

## 建議閱讀順序

1. `SA/cursor分析模組實際控制.md`
2. `SA/architecture/MODULE_CONTROL_RELATION_SDD.md`
3. `SA/modules/attendance.md`
4. `SA/modules/schedule.md`
5. `SA/modules/tenants.md`
6. 回來看這份，決定功能應放哪裡、AI 應怎麼寫

---

## 這份文件怎麼看

這份文件改成以下格式：

- 先看「模組名稱」
- 再看「功能 1、功能 2、功能 3」
- 每個功能下面都會有：
  - 中文說明
  - 常見檔案位置
  - 不該放進來的內容
  - AI 修改規則

也就是說，你之後不用先理解一大段抽象架構，而是可以直接問：

- 我現在要改的功能是哪一類？
- 它屬於哪個模組？
- AI 應該改哪裡，不應該亂改哪裡？

---

# 1. `core`

> 中文定位：平台核心層  
> 英文定位：platform core

## 功能 1：`Actor` 建立與驗證（actor creation / validation）

- 中文說明：
  - 從 JWT 建立目前請求的操作者資訊
  - 補齊 `active_company_id`、`active_role_id`
  - 驗證 user、membership、support assignment
- 常見檔案：
  - `backend/app/core/dependencies.py`
- 不該放進來的內容：
  - attendance 打卡規則
  - leave 審核規則
  - schedule 班表規則
- AI 修改規則：
  - 只有當這個規則是所有模組共用時，才可以改這裡
  - 若只是單一模組的業務規則，不可塞進 `core`

## 功能 2：公司範圍驗證（company scope validation）

- 中文說明：
  - 驗證某個 actor 是否可操作指定公司
  - 區分 `super_admin`、`customer_service`、`company_user`
- 常見檔案：
  - `backend/app/core/scope.py`
- 不該放進來的內容：
  - tenants 的公司管理流程
  - customer_service 的指派 UI 邏輯
- AI 修改規則：
  - 這裡改動通常會影響全部模組，修改前先判斷影響面

## 功能 3：公司內 RBAC 判斷（company-level RBAC）

- 中文說明：
  - 判斷公司內角色，例如 `company_admin`、`hr_manager`、`employee`
  - 提供 admin scope 檢查
- 常見檔案：
  - `backend/app/core/scope.py`
- 不該放進來的內容：
  - 前端 route guard
  - 某個模組自己的 UI 權限顯示
- AI 修改規則：
  - 這裡是後端權威 RBAC，不要只改前端不改這裡

## 功能 4：功能開關（feature gate）

- 中文說明：
  - 決定某公司能不能使用某功能
  - 由 backend 在 API / service 邊界進行檢查
- 常見檔案：
  - `backend/app/core/features.py`
  - `backend/app/core/feature_service.py`
- 不該放進來的內容：
  - 某個模組自己的業務語意
- AI 修改規則：
  - 若新增的是全系統共用功能開關，放 `core`
  - 若只是單一模組內部流程判斷，不一定要放 `core`

## 功能 5：事件匯流排（event bus）

- 中文說明：
  - 提供模組之間的事件傳遞機制
- 常見檔案：
  - `backend/app/core/event_bus.py`
- 不該放進來的內容：
  - 某模組主業務邏輯本身
- AI 修改規則：
  - `core` 只提供事件機制，不負責事件內容語意

## 功能 6：共用平台能力（shared platform capabilities）

- 中文說明：
  - database、config、exceptions 等共用能力
- 常見檔案：
  - `backend/app/core/database.py`
  - `backend/app/core/config.py`
  - `backend/app/core/exceptions.py`
- AI 修改規則：
  - 只放跨模組共用能力，不放模組專屬業務規則

---

# 2. `auth`

> 中文定位：身份與登入模組  
> 英文定位：authentication / identity

## 功能 1：登入（login）

- 中文說明：
  - 使用者輸入 `company_id + login_username + password` 登入
- 常見檔案：
  - `backend/app/modules/auth/api.py`
  - `backend/app/modules/auth/service.py`
- 不該放進來的內容：
  - 公司 CRUD
  - attendance 流程
- AI 修改規則：
  - 只要是登入入口與帳密驗證，優先看 `auth`

## 功能 2：JWT 發放（token issuance）

- 中文說明：
  - 產生 access token
  - 決定 token 內含哪些 claims
- 常見檔案：
  - `backend/app/modules/auth/service.py`
- 不該放進來的內容：
  - feature entitlement 邏輯
- AI 修改規則：
  - 若 claims 改動，必須檢查 `core.dependencies` 是否也要同步調整

## 功能 3：身份查詢（identity lookup）

- 中文說明：
  - 查詢 user、membership、role
  - 支援後續 actor 建立
- 常見檔案：
  - `backend/app/modules/auth/repo.py`
  - `backend/app/modules/auth/models.py`
- AI 修改規則：
  - 若會影響登入後返回的 user/company/role，要同步檢查前端 `auth store`

---

# 3. `tenants`

> 中文定位：公司與租戶管理模組  
> 英文定位：tenant management

## 功能 1：公司資料管理（company CRUD）

- 中文說明：
  - 建立、查詢、更新公司資料
- 常見檔案：
  - `backend/app/modules/tenants/api.py`
  - `backend/app/modules/tenants/service.py`
- 不該放進來的內容：
  - auth token 發放
  - attendance policy
- AI 修改規則：
  - 只要是公司本身的主檔資料，優先放 `tenants`

## 功能 2：成員管理（members management）

- 中文說明：
  - 管理公司有哪些成員，以及成員相關設定
- 常見檔案：
  - `backend/app/modules/tenants/api_members.py`
- 不該放進來的內容：
  - leave 審核邏輯
- AI 修改規則：
  - 這裡管 membership 關係，不管登入驗證本身

## 功能 3：公司開通流程（onboarding）

- 中文說明：
  - 處理公司初始設定與開通流程
- 常見檔案：
  - `backend/app/modules/tenants/api_onboarding.py`
- AI 修改規則：
  - onboarding 是租戶初始化，不要混成一般 admin 雜項功能

## 功能 4：功能授權（entitlements）

- 中文說明：
  - 決定公司能不能用某些功能
- 常見檔案：
  - `backend/app/modules/tenants/api_entitlements.py`
- AI 修改規則：
  - `tenants` 管 source of truth，真正執行 gate 的機制在 `core`

---

# 4. `attendance`

> 中文定位：出勤主業務模組  
> 英文定位：attendance domain

## 功能 1：打卡寫入（punch in / punch out）

- 中文說明：
  - 管理上班、下班打卡事件寫入
- 常見檔案：
  - `backend/app/modules/attendance/api/punch.py`
  - `backend/app/modules/attendance/service.py`
  - `backend/app/modules/attendance/repo.py`
- 不該放進來的內容：
  - schedule template CRUD
- AI 修改規則：
  - 這屬於 capture 子域，若改動應優先看 `attendance-capture.md`

## 功能 2：休息流程（break out / break in）

- 中文說明：
  - 管理休息開始與結束
- 常見檔案：
  - `backend/app/modules/attendance/api/breaks.py`
- AI 修改規則：
  - break deduction 是 derived，不要誤改 canonical duration

## 功能 3：出勤狀態與 session（current status / session lifecycle）

- 中文說明：
  - 管理目前出勤狀態、session 開關閉、history
- 常見檔案：
  - `backend/app/modules/attendance/service.py`
  - `backend/app/modules/attendance/repo.py`
- AI 修改規則：
  - 若改 session semantic，要同步看 reporting 與 policy 影響

## 功能 4：checkpoint 事件

- 中文說明：
  - 管理特定出勤 checkpoint
- 常見檔案：
  - `backend/app/modules/attendance/api/checkpoints.py`
  - `backend/app/modules/attendance/checkpoint_repo.py`
- AI 修改規則：
  - checkpoint 不等於 break，不要混寫

## 功能 5：出勤查詢與報表（reporting）

- 中文說明：
  - sessions、user summary、company summary 等查詢
- 常見檔案：
  - `backend/app/modules/attendance/api/reporting.py`
  - `backend/app/modules/attendance/reporting_repo.py`
  - `backend/app/modules/attendance/reporting_service.py`
- AI 修改規則：
  - reporting 是 consumer，不可反向定義 canonical semantic

## 功能 6：工時與政策判定（work hour / policy evaluation）

- 中文說明：
  - 計算工時、遲到、早退、加班
- 常見檔案：
  - `backend/app/modules/attendance/work_hour_engine.py`
  - `backend/app/modules/attendance/policy_engine.py`
  - `backend/app/modules/attendance/policy_rules.py`
- AI 修改規則：
  - 若牽涉排班，先確認是 `schedule` 提供 baseline，`attendance` 負責判定

## 功能 7：地點打卡限制（location policy / geofence）

- 中文說明：
  - 控制打卡位置限制與 allowed locations
- 常見檔案：
  - `backend/app/modules/attendance/location_policy_service.py`
  - `backend/app/modules/attendance/admin_location_api.py`
- AI 修改規則：
  - 目前屬於 attendance 子域，不要假設它是獨立 `locations` 模組

## 功能 8：舊版相容層（legacy compatibility）

- 中文說明：
  - 承接舊版 API 或過渡流程
- 常見檔案：
  - `backend/app/modules/attendance/api/legacy.py`
- AI 修改規則：
  - 新功能不要優先塞進 legacy 路徑

---

# 5. `schedule`

> 中文定位：排班資料來源模組  
> 英文定位：schedule / shift planning

## 功能 1：班別模板管理（shift template management）

- 中文說明：
  - 建立、查詢、更新、啟停班別模板
- 常見檔案：
  - `backend/app/modules/schedule/api.py`
  - `backend/app/modules/schedule/service.py`
  - `backend/app/modules/schedule/repo.py`
- AI 修改規則：
  - template 是排班定義，不是出勤事實

## 功能 2：班表指派管理（shift assignment management）

- 中文說明：
  - 把班別指派給特定人員或日期
- 常見檔案：
  - `backend/app/modules/schedule/api.py`
  - `backend/app/modules/schedule/service.py`
- AI 修改規則：
  - 不可把 assignment 流程寫成 attendance 的實際打卡流程

## 功能 3：有效班表查詢（effective schedule lookup）

- 中文說明：
  - 查某人某日實際應套用哪個班表
- 常見檔案：
  - `backend/app/modules/schedule/service.py`
  - `backend/app/modules/schedule/repo.py`
- AI 修改規則：
  - 有效班表解析應走單一路徑，不要在 attendance 再複製第二套

## 功能 4：基線輸出（baseline export / normalized windows）

- 中文說明：
  - 提供給 attendance 使用的標準化班表資料
- 常見檔案：
  - `backend/app/modules/schedule/service.py`
  - `backend/app/modules/schedule/schemas.py`
- AI 修改規則：
  - 若 contract 變更，必須同步檢查 `attendance` consumer

---

# 6. `leave`

> 中文定位：請假生命週期模組  
> 英文定位：leave management

## 功能 1：請假申請（leave request submission）

- 中文說明：
  - 員工建立請假申請
- 常見檔案：
  - `backend/app/modules/leave/api.py`
  - `backend/app/modules/leave/service.py`
- AI 修改規則：
  - 若只是請假申請流程，優先看 `leave`

## 功能 2：請假清單（leave list / my requests）

- 中文說明：
  - 查自己的請假記錄
- 常見檔案：
  - `backend/app/modules/leave/api.py`
- AI 修改規則：
  - 查詢規則改動要注意 tenant scope 與 pagination

## 功能 3：待審核清單（pending approvals）

- 中文說明：
  - 查需要審批的請假申請
- 常見檔案：
  - `backend/app/modules/leave/api.py`
- AI 修改規則：
  - 若未來 approval engine 獨立，再重新評估邊界；目前仍屬 `leave`

## 功能 4：審核動作（approve / reject）

- 中文說明：
  - 核准或拒絕請假申請
- 常見檔案：
  - `backend/app/modules/leave/api.py`
  - `backend/app/modules/leave/service.py`
- AI 修改規則：
  - 不要把 attendance 異常或排班規則硬塞到這裡

---

# 7. `notifications`

> 中文定位：事件轉通知模組  
> 英文定位：notifications / event consumer

## 功能 1：事件訂閱（event subscription）

- 中文說明：
  - 接收來自其他模組的事件
- 常見檔案：
  - `backend/app/modules/notifications/event_handlers.py`
- AI 修改規則：
  - 它是 consumer，不是主業務 orchestrator

## 功能 2：通知落地（notification persistence）

- 中文說明：
  - 把事件轉成通知資料並保存
- 常見檔案：
  - `backend/app/modules/notifications/service.py`
  - `backend/app/modules/notifications/repo.py`
- AI 修改規則：
  - 不可直接跨模組改別人的主資料

## 功能 3：通知查詢（notification query）

- 中文說明：
  - 提供通知列表查詢
- 常見檔案：
  - `backend/app/modules/notifications/api.py`
- AI 修改規則：
  - 若調整回傳欄位，要同步檢查前端 consumer

---

# 8. `audit`

> 中文定位：稽核治理模組  
> 英文定位：audit / compliance

## 功能 1：稽核查詢（audit log query）

- 中文說明：
  - 查詢 audit logs
- 常見檔案：
  - `backend/app/modules/audit/api.py`
  - `backend/app/modules/audit/service.py`
- AI 修改規則：
  - 任何查詢都必須維持 company scope

## 功能 2：匯出（export JSON / CSV）

- 中文說明：
  - 匯出 audit 紀錄
- 常見檔案：
  - `backend/app/modules/audit/api.py`
- AI 修改規則：
  - 匯出需 admin RBAC，不可只做前端限制

## 功能 3：保留政策（retention policy）

- 中文說明：
  - 控制 audit 資料保留時間
- 常見檔案：
  - `backend/app/modules/audit/api.py`
  - `backend/app/modules/audit/service.py`
- AI 修改規則：
  - 改 retention 時要同步檢查 purge 規則

## 功能 4：清理（purge）

- 中文說明：
  - 清除過期 audit 紀錄
- 常見檔案：
  - `backend/app/modules/audit/api.py`
- AI 修改規則：
  - purge 是治理操作，需維持嚴格權限與審計語意

---

# 9. `backup`

> 中文定位：公司級備份還原模組  
> 英文定位：backup / restore

## 功能 1：資料匯出（company export）

- 中文說明：
  - 匯出某公司的資料備份
- 常見檔案：
  - `backend/app/modules/backup/api.py`
  - `backend/app/modules/backup/service.py`
  - `backend/app/modules/backup/exporter.py`
- AI 修改規則：
  - company scope 必須由 actor 決定，不可信任 request body

## 功能 2：資料還原（company restore）

- 中文說明：
  - 將備份資料還原到目標公司
- 常見檔案：
  - `backend/app/modules/backup/api.py`
  - `backend/app/modules/backup/importer.py`
- AI 修改規則：
  - restore 很敏感，修改時要先確認 tenant isolation 不被破壞

## 功能 3：備份驗證（backup validation）

- 中文說明：
  - 驗證備份資料格式與一致性
- 常見檔案：
  - `backend/app/modules/backup/validator.py`
- AI 修改規則：
  - 如果資料範圍有改，需同步檢查 audit / tenants 相關影響

---

# 10. `customer_service`

> 中文定位：客服跨公司支援範圍模組  
> 英文定位：customer service scope

## 功能 1：客服可支援公司查詢（assigned companies query）

- 中文說明：
  - 查客服目前被指派到哪些公司
- 常見檔案：
  - `backend/app/modules/customer_service/api.py`
- AI 修改規則：
  - 這裡管 scope，不是 tenant 主資料

## 功能 2：公司指派（support assignment create）

- 中文說明：
  - 將某客服綁定到某公司
- 常見檔案：
  - `backend/app/modules/customer_service/service.py`
  - `backend/app/modules/customer_service/repo.py`
- AI 修改規則：
  - 這是平台角色範圍管理，不是公司內部 admin 流程

## 功能 3：取消指派（support assignment removal）

- 中文說明：
  - 移除客服對某公司的支援範圍
- 常見檔案：
  - `backend/app/modules/customer_service/service.py`
- AI 修改規則：
  - 若影響 scope 規則，要同步檢查 `core.dependencies`

---

# 11. `frontend`

> 中文定位：前端操作介面模組  
> 英文定位：frontend application

## 功能 1：登入狀態管理（auth store / session restore）

- 中文說明：
  - 保存 token、user、company、role
  - 頁面刷新後恢復登入狀態
- 常見檔案：
  - `frontend/src/stores/auth.js`
- AI 修改規則：
  - 若後端登入回應格式改動，要同步調整這裡

## 功能 2：路由守衛（route guard）

- 中文說明：
  - 控制哪些角色能進哪些頁面
- 常見檔案：
  - `frontend/src/router/index.js`
- AI 修改規則：
  - 前端 guard 只是 UX 輔助，不能取代後端權限

## 功能 3：API 呼叫（API client）

- 中文說明：
  - 封裝 API 呼叫與 token 傳遞
- 常見檔案：
  - `frontend/src/api/*`
- AI 修改規則：
  - 若 API 契約改動，要同步檢查 store 與 views

## 功能 4：頁面與互動（views / UI interaction）

- 中文說明：
  - attendance reports、schedule、admin、leave 等頁面
- 常見檔案：
  - `frontend/src/views/*`
- AI 修改規則：
  - UI 可調整，但不可自行定義後端權威規則

---

# 12. 之後你怎麼跟 AI 下指令

你之後如果要新增或修改功能，建議直接用這個句型：

## 指令模板 1：單模組功能新增
我要修改 `模組名稱` 的 `功能名稱`。  
請先依 `SA/模組功能清單與 AI 開發指引.md` 判斷功能歸屬，  
再依對應 `SA/modules/<module>.md` 與 `SA/architecture/MODULE_CONTROL_RELATION_SDD.md` 實作。  
改完程式後，請同步回寫相關 SA 文件。

## 指令模板 2：不確定功能放哪裡
我要新增 `某功能`，但我不確定要放 `哪個模組`。  
請先依 `SA/模組功能清單與 AI 開發指引.md` 幫我判斷模組歸屬，  
說明原因後再開始改程式。

## 指令模板 3：跨模組功能調整
我要修改 `A 功能`，它可能會影響 `B 模組`。  
請先依 `SA/模組功能清單與 AI 開發指引.md` 與  
`SA/architecture/MODULE_CONTROL_RELATION_SDD.md` 分析邊界，  
確認哪些該改、哪些不該改，再實作。

---

# 13. 這份文件的維護規則

只要發生下面任一種情況，就應更新這份文件：

- 某模組新增主要功能類別
- 某模組責任發生改變
- 某功能從 A 模組搬到 B 模組
- 新增重要子域
- AI 常常把某功能寫錯地方

---

# 14. 對應文件

- `SA/cursor分析模組實際控制.md`
- `SA/architecture/MODULE_CONTROL_RELATION_SDD.md`
- `SA/modules/attendance.md`
- `SA/modules/schedule.md`
- `SA/modules/tenants.md`
