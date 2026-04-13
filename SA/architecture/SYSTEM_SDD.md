# 系統設計說明書（SDD）

## 1. 文件目的

本文件描述 `/opt/attendance-system` 目前實際系統架構，作為未來開發、重構、維護、交接的正式設計依據。

本文件目標不是記錄工作票歷程，而是回答以下問題：
- 系統由哪些模組構成
- 每個模組負責什麼
- 模組間如何互動
- 哪些邊界已明確，哪些仍有重疊風險
- 未來新增功能時應該放在哪裡

---

## 2. 系統概觀

此系統是一套多租戶 SaaS 出勤管理系統，核心能力包含：
- 身分驗證與 JWT scope
- 多租戶公司管理
- 出勤打卡與工時計算
- 班表模板與班別指派
- 請假流程
- 通知事件紀錄
- 稽核查詢與匯出
- 單一公司備份與還原
- 後台管理與前端操作介面

系統目前採：
- **Backend**：FastAPI + SQLAlchemy
- **Frontend**：Vue 3 + Pinia + Vue Router + Axios + Vite
- **Architecture style**：同庫同表、多租戶 `company_id` 隔離

---

## 3. 系統層級結構

### 3.1 根目錄

- `backend/`：後端 API 與業務邏輯
- `frontend/`：前端單頁應用
- `scripts/`：部署或維運腳本
- `backups/`：備份資料
- `archive/`：舊資產/歷史檔
- `SA/`：正式架構與設計文件中心
- `docs/`：歷史文件區，僅保留追溯用途，不作為正式依據

### 3.2 後端主結構

- `backend/app/main.py`：FastAPI 啟動入口、路由註冊、middleware、startup wiring
- `backend/app/core/`：平台共用能力
- `backend/app/modules/`：業務模組

### 3.3 前端主結構

- `frontend/src/api/`：API 呼叫封裝
- `frontend/src/stores/`：Pinia 狀態管理
- `frontend/src/router/`：前端路由與權限守衛
- `frontend/src/views/`：頁面層
- `frontend/src/components/`：共用元件
- `frontend/src/composables/`：前端可重用行為
- `frontend/src/utils/`：輔助工具

---

## 4. 核心平台層（backend/app/core）

### 4.1 `dependencies.py`
責任：
- 從 JWT 建立 `Actor`
- 驗證 user / membership / scope
- 統一注入 `active_company_id`

意義：
- 是目前多租戶與權限模型的核心入口
- 已取代舊的 header-only tenant context 模式

### 4.2 `scope.py`
責任：
- 定義 `Actor`
- 定義平台層角色與公司層 RBAC
- 提供 company scope / admin scope 驗證

### 4.3 `features.py` + `feature_service.py`
責任：
- 定義 feature keys
- 查詢公司 entitlement
- 在 API 層執行 feature gate

### 4.4 `event_bus.py`
責任：
- 提供 in-memory 同步事件匯流排
- 作為跨模組事件傳遞機制

限制：
- 目前為記憶體內實作，不是持久化事件系統
- 目前不是 `SSE`（server-sent events）、不是 `EventSource` 回應層、也不是外部 upstream streaming gateway
- 適合目前規模，但未來若要做可靠事件投遞或串流型 consumer contract，需先補正式設計

已確認的真實 code inventory（2026-04-09）：
- `backend/app/core/event_bus.py` 只提供 `subscribe()` / `emit()` / registry 查詢，無 HTTP stream response
- `backend/app/modules/debug_event_api.py` 只提供 debug JSON 查詢與手動 emit 端點，不提供 `text/event-stream`
- `backend/app/modules/notifications/event_handlers.py` 以 startup subscribe 方式消費 `attendance.approved`，屬 internal consumer
- `backend/app/main.py` startup 只做 subscriber wiring，未建立 upstream client、webhook provider adapter 或串流 gateway

### 4.5 其他 core 元件
- `config.py`：系統設定
- `database.py`：資料庫連線
- `exceptions.py`：統一例外處理
- `user_lookup.py`：跨模組允許的共用查詢能力
- `tenant_context.py`：舊 header path 已退休，目前為空殼保留說明

---

## 5. 後端模組總覽

### 5.1 attendance
責任：
- 打卡 session 與 punch 流程
- break / out checkpoint
- 工時計算
- policy evaluation
- reporting aggregation
- location policy enforcement

特徵：
- 是目前最肥大、最容易產生邊界重疊的模組
- 同時包含 API façade、domain rule、repo、reporting、policy、location 邏輯
- 已有拆分跡象：`reporting_repo.py`、`reporting_service.py`、`work_hour_engine.py`、`policy_*`

已知風險：
- API 層仍承擔過多協調
- 舊 flow 與新 flow 並存
- 報表、政策、打卡、地點驗證都仍掛在同一模組下，未來要持續收斂子域

### 5.2 schedule
責任：
- Shift template 管理
- Shift assignment 管理
- 提供排班 baseline 給 attendance policy / work 計算使用

狀態：
- 已實作 API / service / repo / models
- 已註冊主路由
- 與 attendance 有業務互動，但目前仍維持獨立模組

### 5.3 auth
責任：
- 登入驗證
- JWT token 發放
- user / membership / role 查詢支援

說明：
- auth 是整個平台 identity 入口
- 目前 login API 位於 `/api/internal/auth/login`

### 5.4 tenants
責任：
- 公司（tenant）管理
- entitlement 管理
- onboarding
- members 管理

說明：
- 是多租戶管理主模組
- 承載公司 CRUD、會員管理與 feature entitlement

### 5.5 leave
責任：
- 請假申請
- 個人請假清單
- 待審核清單
- 核准/拒絕流程

說明：
- 已使用 JWT actor 與 `leave.core` feature gate

### 5.6 notifications
責任：
- 接收事件（目前重點是 `attendance.approved`）
- 將事件轉為可查詢通知記錄

說明：
- 是事件消費者模組
- 與 EventBus 整合清楚

### 5.7 audit
責任：
- 稽核記錄查詢
- 匯出
- retention policy
- purge

說明：
- 功能邊界相對清楚
- 文件內容與實際 JWT 模式曾有落差，已列為文件治理風險

### 5.8 backup
責任：
- 單一公司資料匯出/還原
- 需配合 tenant isolation 與 admin RBAC

說明：
- 屬平台維運能力
- 與 audit、tenants、auth 有治理關聯

### 5.9 customer_service
責任：
- 客服跨公司支援指派
- 管理 support assignment scope

說明：
- 承接 `customer_service` 平台角色的可操作公司範圍

### 5.10 其他 wiring / demo 元件
- `router_wiring.py`：demo router 註冊
- `startup_wiring.py`：startup handler 註冊
- `demo_event_subscribers.py`：debug/demo 事件訂閱者
- `debug_event_api.py`：debug 用事件端點

這些元件應視為平台啟動與測試支援層，不應承擔正式業務流程。

---

## 6. 前端架構

### 6.1 前端責任
前端負責：
- 登入狀態維持
- 頁面路由與權限控制
- API 呼叫
- 畫面展示與互動

### 6.2 主要區塊

#### `src/api/`
目前已包含：
- `auth.js`
- `attendance.js`
- `schedule.js`
- `leave.js`
- `admin.js`
- `client.js`

其中 `client.js` 統一處理：
- Authorization Bearer token
- 錯誤處理
- 401 後 session 清理與導回登入
- 目前屬一般 request/response client，未見 `SSE` / `EventSource` / `event-stream` consume path

#### `src/stores/`
- `auth.js`：登入狀態、角色、公司資訊、session restore
- `attendance.js`：出勤狀態
- `reporting.js`：報表狀態

#### `src/router/index.js`
前端 RBAC：
- `/schedule`：company_admin only
- `/admin`：super_admin / company_admin / hr_manager
- `/leave`：登入即可
- 報表頁：登入即可

#### `src/views/`
目前主要功能頁：
- `Home.vue`
- `Login.vue`
- `LeaveRequestView.vue`
- `reports/*`
- `schedule/SchedulePage.vue`
- `admin/*`

---

## 7. 系統主要流程

### 7.1 登入流程
1. 前端送出 company_id / login_username / password
2. `auth` 模組驗證 tenant、membership、password
3. 後端發 JWT
4. 前端將 token 與 user/company/role 寫入 localStorage
5. router guard 依角色控制頁面存取

### 7.2 出勤事件流程
1. 使用者呼叫 attendance API
2. API 由 `get_actor_with_company()` 取得 actor scope
3. 進行 feature gate 與 tenant isolation
4. attendance repo / service / engine 執行計算與寫入
5. 部分流程會 emit `attendance.approved`
6. notifications 訂閱事件後落 DB

### 7.3 班表與政策關聯
1. schedule 維護 shift template / assignment
2. attendance policy engine 透過 `ScheduleBaselineResolver` 讀取排班基準
3. 用於遲到、早退、工時計算與時段 normalization

### 7.4 備份與稽核流程
- backup 提供公司級 export/restore
- audit 提供查詢、匯出、retention、purge
- 兩者都屬治理/維運域，而非一般員工功能域

---

## 8. 目前已觀察到的設計風險

### 8.1 文件權威來源分裂
問題：
- `docs/`、模組內 `docs.md`、工作票、修復紀錄並存
- 有些內容仍停留在舊 header-based 說法，與實際 JWT 架構不一致

策略：
- 以 `SA/` 取代 `docs/` 成為唯一權威文件區

### 8.2 attendance 模組過胖
問題：
- attendance 同時包含打卡、報表、政策、工時計算、地點驗證
- 易造成邏輯重複與責任模糊

策略：
- 以子域思維持續拆分：
  - punch flow
  - reporting
  - policy
  - location policy
  - work hour engine

### 8.3 舊流程與新流程混用
問題：
- legacy endpoint、demo wiring、過渡期文件仍存在
- 容易造成 AI 或維護者誤判正式路徑

策略：
- 在模組文件中明確標記：正式路徑 / 過渡路徑 / 已退休路徑

### 8.4 文件未隨程式回寫
問題：
- 新功能完成後只留在程式碼，沒有形成可累積設計資產

策略：
- 強制每次改動回寫 `SA/`

### 8.5 串流與 upstream 語意漂移風險
問題：
- 目前系統內只有 internal EventBus，沒有正式 upstream client、provider adapter、SSE gateway
- 若未先定義 owner，未來容易把 event bus、debug API、notifications subscriber 誤判成串流架構基礎

策略：
- EventBus 維持 internal synchronous event bus 定位
- 若未來新增 upstream 整合，先定義 transport owner、provider contract、retry / auth / observability 邊界
- 若未來新增前端串流，先定義 consumer contract，不得直接從既有 debug/event wiring 擴寫

---

## 9. 正式文件維護原則

1. `SA/` 是正式文件入口
2. `docs/` 僅保留歷史匯入，不再更新
3. 所有新功能都必須同步更新：
   - 總體架構文件
   - 模組 SDD
   - 文件治理規範（若流程改變）

---

## 10. 下一步建議

1. 以 `SA/modules/attendance.md` 為基礎，逐步拆出 attendance 子域責任
2. 讓每個新工作票完成時都附帶文件回寫清單
3. 後續若要真正降低重疊，優先檢查：
   - attendance API 是否過度協調
   - reporting 是否應獨立子模組
   - policy engine 是否需要正式 domain boundary
   - location policy 是否應持續留在 attendance 或成為獨立能力
4. 若未來要導入 upstream：
   - 先決定放在 `core` 還是新平台整合模組
   - 再決定哪些業務模組只負責 domain mapping
   - 最後才實作 HTTP client / webhook / streaming response

---

## 11. 已依目前 baseline 回寫的系統級結論（2026-04-09）

### 11.1 多租戶底板
- 系統採 `multi-tenant architecture`（多租戶架構）
- Tenant Data 必須受 `company_id`（公司識別）隔離
- `company_id` 不可信任前端 request body
- `request context`（請求上下文）應建立 `current_user_id` 與 `current_company_id`

### 11.2 平台與 scope
- `platform-first identity`（平台優先身份）為正式基線
- `auth`（身分驗證）與 `scope validation`（操作範圍驗證）應分開理解
- 客服 `customer_service` 僅能操作被指派公司，不是全域萬能角色

### 11.3 attendance / reporting
- `attendance` 是核心語意 owner
- `reporting` 是唯讀 consumer，不是核心規則 owner
- 員工端 P0 是手機查看自己當月紀錄
- 正式列印、勞檢備查、異常檢查由 `HR / 管理端` 使用

### 11.4 治理能力
- `feature gate`（功能閘門）、`audit`（稽核）、`backup / restore`（備份 / 還原）屬 SaaS 核心治理能力
- `backup / restore` 需包含 `company consistency check`（公司一致性檢查）與 `FK closure check`（外鍵閉包檢查）

### 11.5 streaming / upstream inventory 結論
- 前端目前是 `Axios request/response` consume，不是串流前端
- 後端目前沒有對外 upstream HTTP client / provider adapter / webhook verification layer 的正式 owner
- 現況最接近事件流能力的是 `backend/app/core/event_bus.py`，但它只屬 internal synchronous event delivery
- 若未來需要導入 `SSE`、upstream provider、streaming gateway，應先新增正式 owner spec，再進 code
