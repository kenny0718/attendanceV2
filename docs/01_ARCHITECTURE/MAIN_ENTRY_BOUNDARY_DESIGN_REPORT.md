# MAIN ENTRY BOUNDARY DESIGN REPORT

## 1. Summary
本報告針對 `backend/app/main.py` 進行 entry-layer 邊界設計審計。結論是：`main.py` 目前同時承擔應用建立、全域 middleware、例外處理註冊、跨模組 router wiring、startup lifecycle、EventBus demo 訂閱、notifications 事件處理器註冊，以及 test/debug endpoints 暴露等多種責任。作為 FastAPI 入口檔，保留 app instance 建立、必要全域 wiring 與基礎健康檢查是合理的；但 demo/test endpoint 與 startup 內的示範型 subscriber 註冊，已超出純 entry layer 最小責任邊界。

本 repo 現況不適合直接大改 `main.py`。原因是：`app` 物件被 `backend/app/conftest.py` 直接匯入做 dependency override；`main.py` 直接 include 多個 router，其中同時混有 legacy 與 v1 路由；startup 還會註冊 EventBus subscriber 與 notifications handlers，任何直接重構都可能影響整體啟動、測試掛載、路由暴露與事件副作用。本票建議後續拆成多張 no-behavior-change 小票，先做 wiring inventory，再逐步抽離 app factory、router registration map、demo/test endpoint 隔離方案。

## 2. Files Inspected
- `backend/app/main.py`
- `backend/app/conftest.py`
- `backend/app/core/config.py`
- `backend/app/core/database.py`
- `backend/app/core/dependencies.py`
- `backend/app/core/exceptions.py`
- `backend/app/modules/attendance/api/__init__.py`
- `backend/app/modules/attendance/api/legacy.py`
- `backend/app/modules/attendance/api/punch.py`
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/api/checkpoints.py`
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/admin_location_api.py`
- `backend/app/modules/attendance/feature_gate_demo.py`
- `backend/app/modules/schedule/api.py`
- `backend/app/modules/leave/api.py`
- `backend/app/modules/auth/api.py`
- `backend/app/modules/notifications/api.py`
- `backend/app/modules/notifications/event_handlers.py`
- `backend/app/modules/backup/api.py`
- `backend/app/modules/audit/api.py`
- `backend/app/modules/tenants/api.py`
- `backend/app/modules/customer_service/api.py`

Docs read attempt warnings:
- `docs/03_WP_CONTROL/ACTIVE_EXECUTION_ORDER.md`：讀取結果為空
- `docs/01_ARCHITECTURE/SA21_GAP_AUDIT_REPORT.md`：讀取結果為空
- `docs/03_WP_CONTROL/SA21_REALIGNMENT_ROADMAP.md`：讀取結果為空

## 3. Current Responsibilities of main.py

### 3.1 App instance 建立與 OpenAPI metadata
證據：`main.py` 直接建立 `FastAPI(title=settings.app_name, debug=settings.debug)`。

責任判斷：
- 屬於 entry layer 合理責任。
- 這是應用啟動的最上層組裝點，應保留在入口或 app factory。

### 3.2 全域例外處理註冊
證據：`main.py` 呼叫 `register_exception_handlers(app)`。

責任判斷：
- 屬於 entry layer 合理責任。
- 這是 app-level wiring，不是業務邏輯。

### 3.3 全域 HTTP middleware wiring
證據：`main.py` 內宣告 `@app.middleware("http")` 的 `legacy_header_guard`。

責任內容：
- 偵測 retired headers：`x-company-id`、`x-user-id`
- 僅記 log，不阻擋 request

責任判斷：
- middleware 註冊本身屬於 entry layer。
- 但 middleware function 本體直接寫在 `main.py`，使入口檔承擔具體行為細節，屬於可收斂但不應立即重構的區塊。

### 3.4 Cross-module router include / mount
證據：`main.py` 直接 include：
- `attendance_router`
- `attendance_router_v1`
- `attendance_gate_demo_router`
- `admin_location_router`
- `notifications_router`
- `backup_router`
- `audit_router`
- `auth_router`
- `tenants_router`
- `customer_service_router`
- `leave_router_v1`
- `schedule_router`

責任判斷：
- router registration 屬於 entry layer。
- 但目前數量已多，且混合 legacy / v1 / demo / admin 類型 router，導致 `main.py` 成為大型 orchestration 檔案。

### 3.5 Startup lifecycle orchestration
證據：`@app.on_event("startup")` 的 `startup_event()` 內做了：
- 啟動 log
- `get_event_bus()`
- 註冊 `test.event` demo subscriber
- 註冊 `attendance.approved` demo subscriber
- 呼叫 `register_event_handlers()`

責任判斷：
- lifecycle hook 註冊屬於 entry layer。
- 但 startup function 內混入 demo handler 定義與 subscribe 細節，已超出最小入口責任。

### 3.6 Root / health endpoint 暴露
證據：
- `@app.get("/")`
- `@app.get("/health")`

責任判斷：
- 合理屬於 entry layer。
- 這類 endpoint 屬於全域服務可用性入口。

### 3.7 Test / debug endpoint 暴露
證據：
- `@app.get("/api/test/event")`
- `@app.post("/api/test/event")`

責任內容：
- 直接操作 `event_bus`
- 列出 subscriber 狀態
- 發送 `test.event`

責任判斷：
- 不屬於 production entry layer 的最小責任。
- 屬於高風險混入，因為它讓正式入口同時暴露測試/除錯能力。

### 3.8 可執行腳本入口
證據：`if __name__ == "__main__": uvicorn.run(...)`

責任判斷：
- 屬於 entry layer 合理責任。
- 但若未來導入 app factory，此區塊也需同步調整。

## 4. Entry-Layer Appropriate Responsibilities
以下責任建議保留在 `main.py` 或未來的 app factory / entry composition layer：

1. 建立 `FastAPI` app instance
2. 設定 OpenAPI 基本 metadata（title/debug）
3. 註冊全域 exception handlers
4. 註冊全域 middleware（但 middleware function 可移到獨立 module）
5. include routers / route composition
6. 註冊 startup / shutdown hooks（僅保留 wiring，避免內含 demo 行為）
7. root / health 這類全域基礎 endpoint
8. executable entry (`uvicorn.run`) 或對應 app factory adapter

原因：
這些都屬於「如何組裝 app」而不是「如何執行單一業務流程」。

## 5. Boundary Violations / Overloaded Areas

### 5.1 Demo/test endpoints 混入 production entry
證據：`main.py` 直接宣告 `/api/test/event` GET/POST。

問題：
- 不是系統核心入口必要責任
- 與 EventBus 測試機制耦合
- 容易在 production entry 長期殘留

### 5.2 Startup 內定義 demo handlers
證據：`startup_event()` 內直接定義 `demo_handler()` 與 `attendance_approved_demo_handler()`。

問題：
- 入口檔同時承擔 handler implementation 與 lifecycle wiring
- 導致 `main.py` 不只負責「接線」，還負責「示範邏輯內容」

### 5.3 Router orchestration 過度集中
證據：`main.py` 直接 import 並 include 多個 router，且包含：
- attendance legacy router
- attendance v1 merged router
- feature gate demo router
- admin location router
- notifications / backup / audit / auth / tenants / customer_service / leave / schedule

問題：
- 入口檔膨脹
- legacy 與新路由混掛，增加風險評估難度
- 未來再加模組會讓入口進一步失控

### 5.4 Attendance 子域路由結構本身已有聚合層，main.py 卻仍直接掛多種 attendance-related router
證據：
- `app.modules.attendance.api.__init__` 已聚合 `router_v1`
- 但 `main.py` 仍另外掛 `attendance_gate_demo_router` 與 `admin_location_router`

問題：
- attendance boundary 沒有單一組裝出口
- main.py 需要知道 attendance 模組的多個內部分支

## 6. High-Risk Zones (Do Not Touch Directly)

### 6.1 `app = FastAPI(...)` 與 `register_exception_handlers(app)` 區段
風險：
- 這是應用物件建立核心
- `backend/app/conftest.py` 直接 `from app.main import app`
- 若直接改成不同初始化方式，測試 fixture、dependency override、啟動行為都可能壞掉

### 6.2 `app.include_router(...)` 全區段
風險：
- 任何 include 順序、漏掛、名稱變更，都可能導致 API 消失或 prefix 改變
- 目前同時混有 legacy 與 v1 router，牽涉 API 相容性
- schedule / leave / auth 等模組路由實作實際在 `api.py`，而非 `api/` package，表示 import 結構並不一致，直接整理容易誤傷

### 6.3 `@app.on_event("startup")` 區段
風險：
- 影響 EventBus 初始化與 notifications 事件處理器註冊
- 若錯拆，可能導致事件功能失效但表面 API 仍能啟動
- 內含 demo subscribers，移除或改順序都可能改變觀察行為

### 6.4 `/api/test/event` endpoints
風險：
- 雖然它們本身像 debug endpoint，但直接操作 `event_bus`
- 若粗暴移除，可能破壞現有手動驗證流程或依賴它的測試/操作習慣
- 應先盤點使用者與測試依賴，再隔離

### 6.5 `if __name__ == "__main__"` 區段
風險：
- 若未來改 app factory，啟動命令與載入方式會一起受影響
- 不應單獨修改而不同步考慮 ASGI import path / test imports

## 7. Recommended Safe Decomposition Strategy

### 策略 1：先做 router wiring inventory，不做行為變更
目標：
- 先列出 `main.py` 目前所有 router 來源、prefix、用途、是否 legacy / demo / admin / v1

理由：
- 先掌握 wiring，才能安全判斷哪些可以抽 registration map

### 策略 2：抽離 app factory 設計，但先不落地重構
目標：
- 設計 `create_app()` 的責任邊界
- 明確規範哪些東西在 factory 內做，哪些仍由 `main.py` 呼叫

理由：
- `conftest.py` 直接 import `app`，若沒先設計相容方案，直接抽 factory 風險太高

### 策略 3：把 middleware / startup wiring 與 handler implementation 分離
目標：
- `main.py` 只保留 `register_middlewares(app)` / `register_startup_hooks(app)` 類型的接線點
- 具體 middleware function 與 startup subscriber 定義移到專門 module

理由：
- 這屬於 no-behavior-change extraction 的典型安全拆法

### 策略 4：先做 demo/test endpoint isolation plan，再決定是否移出 production entry
目標：
- 盤點 `/api/test/event` 與 `attendance_gate_demo_router` 的用途
- 判斷應改成 debug-only router、dev-only mount，或完全抽成獨立模組

理由：
- 目前看起來是邊界違規，但不能在未盤點依賴前直接刪

### 策略 5：以 attendance boundary 為優先試點
目標：
- 先把 attendance 相關非核心 router（demo/admin）做組裝面盤點
- 評估是否建立單一 attendance router composition 出口

理由：
- 目前 attendance 是 main.py 中最複雜、最容易膨脹的來源

## 8. Proposed Ticket Breakdown

### P0-3A main.py router wiring inventory
範圍：
- 只盤點 `main.py` include 的所有 router
- 建立 prefix / source file / category / risk 對照表

不做：
- 不改 import
- 不改 include order

### P0-3B app factory extraction design
範圍：
- 設計 `create_app()` 介面
- 設計與 `conftest.py` 相容的遷移方式
- 明確列出 no-behavior-change 遷移步驟

不做：
- 不直接實作 factory

### P0-3C demo/test endpoint isolation plan
範圍：
- 盤點 `/api/test/event`、`attendance_gate_demo_router`、startup demo subscribers
- 判斷 dev-only / demo-only / removable 的分類

不做：
- 不直接移除 endpoint

### P0-3D lifecycle / middleware separation review
範圍：
- 盤點 `legacy_header_guard`、`startup_event`、`register_event_handlers()`
- 設計獨立 registration module 的拆法

不做：
- 不改 middleware 或 startup 行為

### P0-3E attendance composition boundary review
範圍：
- 檢視 attendance 模組哪些 router 已聚合、哪些仍散落在 main.py
- 設計單一 composition 出口可能性

不做：
- 不變更現有 API prefix

## 9. Stop Conditions / Why Direct Refactor Is Unsafe
直接重構 `main.py` 現在不安全，原因如下：

1. `conftest.py` 直接依賴 `from app.main import app`
   - 任何 app 建立方式變動都會波及測試啟動與 dependency override。

2. `main.py` 是全系統 router 掛載中心
   - 少掛任何一個 router 就會造成 API contract 變動。

3. startup 邏輯有隱性副作用
   - EventBus 訂閱與 notifications handler 註冊不是純設定，會影響執行時事件行為。

4. 混有 legacy / v1 / demo / admin 路由
   - 若沒有先做 inventory，無法安全判斷哪些能移、哪些必須原地保留。

5. 模組 API 結構不一致
   - 有些模組用 `api.py`，有些用 `api/__init__.py` 或多檔 router；直接統一重構成本高且易誤判。

因此必須拆成多張小票，且每一張都應以 no-behavior-change 為優先原則。

## 10. Final Recommendation
最保守且安全的建議順序是：

1. 先完成 `P0-3A` router wiring inventory
2. 再做 `P0-3C` demo/test endpoint isolation 設計
3. 接著做 `P0-3D` lifecycle / middleware separation review
4. 最後才進入 `P0-3B` app factory extraction design

原因：
- 先盤點接線，再隔離高風險 demo/test 混入，再拆 wiring，最後才碰 app factory
- 這能降低一次同時碰觸 app 建立、router 掛載、startup 副作用三種風險的可能性
- 對目前 repo 來說，這比直接「重構 main.py」安全得多
