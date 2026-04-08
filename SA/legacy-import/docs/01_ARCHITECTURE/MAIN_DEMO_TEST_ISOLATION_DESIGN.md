# MAIN DEMO / TEST ISOLATION DESIGN

## 1. Summary
本報告針對 `backend/app/main.py` 中的 demo / test / debug 行為進行唯讀設計審計，目標是識別哪些內容不應直接留在 production entry，並提出後續可安全拆出的隔離策略與拆票順序，不修改任何 source code。

根據現場程式碼證據，`main.py` 目前混入四類 non-production 元素：
1. 直接暴露的 `/api/test/event` test endpoints。
2. 由 `attendance_gate_demo_router` 掛入的 feature gate 示範 router。
3. `startup_event()` 內部定義與註冊的 demo EventBus subscribers。
4. 與上述項目相連的 EventBus introspection / emit 行為。

其中真正屬於 production legitimate 的是 `register_event_handlers()` 所註冊的 notifications 事件處理器，以及 root / health / 正式業務 routers；而 `/api/test/*`、startup demo subscribers、`feature_gate_demo.py` 中明確標示為示範的 endpoints，皆屬應隔離的 non-production 行為。這些元素目前與 `EventBus`、`startup_event()`、以及既有手動驗證路徑存在依附，因此不適合直接刪除，應先採「保留行為、改變掛載位置或註冊條件」的階段式拆分。

## 2. Files Inspected
必讀 source：
- `backend/app/main.py`
- `backend/app/core/event_bus.py`
- `backend/app/core/config.py`
- `backend/app/modules/attendance/feature_gate_demo.py`
- `backend/app/modules/attendance/admin_location_api.py`
- `backend/app/modules/notifications/event_handlers.py`

補充依附證據：
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/notifications/tests/test_event_handlers.py`
- `backend/app/modules/notifications/tests/test_tenant_isolation.py`

Best-effort docs：
- `docs/01_ARCHITECTURE/MAIN_ENTRY_BOUNDARY_DESIGN_REPORT.md`
- `docs/01_ARCHITECTURE/MAIN_ROUTER_WIRING_INVENTORY.md`
- `docs/03_WP_CONTROL/ACTIVE_EXECUTION_ORDER.md`

Warnings：
- 無。上述 docs 皆可讀取。

## 3. Demo/Test Element Inventory

| type | location | source_module | description |
|------|----------|---------------|-------------|
| router import | `main.py:12` | `app.modules.attendance.feature_gate_demo` | `attendance_gate_demo_router` 由檔名與註解 `feature_gate_demo` / `WP-C1-06` 可識別為 demo router。 |
| router wiring | `main.py:62` | `app.modules.attendance.feature_gate_demo` | `app.include_router(attendance_gate_demo_router)` 將 demo router 直接掛入 production entry。 |
| lifecycle handler definition | `main.py:83-85` | `main.py` local | `demo_handler()` 明確標示 `Demo 事件處理器`，僅記錄 `test.event` payload。 |
| lifecycle handler definition | `main.py:87-95` | `main.py` local | `attendance_approved_demo_handler()` 明確標示 `Demo，用於 log`，僅做 log 展示。 |
| lifecycle subscription | `main.py:96` | `main.py` + `app.core.event_bus` | `event_bus.subscribe("test.event", demo_handler)` 在 startup 註冊 demo subscriber。 |
| lifecycle subscription | `main.py:97` | `main.py` + `app.core.event_bus` | `event_bus.subscribe("attendance.approved", attendance_approved_demo_handler)` 在 startup 註冊 demo subscriber。 |
| endpoint | `main.py:124-141` | `main.py` + `app.core.event_bus` | `GET /api/test/event` 用於列出事件與訂閱者狀態，docstring 明寫「用於測試/除錯」。 |
| endpoint | `main.py:144-168` | `main.py` + `app.core.event_bus` | `POST /api/test/event` 用於發出 `test.event`，docstring 明寫「用於測試」。 |
| router endpoint | `feature_gate_demo.py:23-65` | `app.modules.attendance.feature_gate_demo` | `POST /api/attendance/shift-overrides`，docstring 與檔頭明寫「Feature Gate 示範端點」。 |
| router endpoint | `feature_gate_demo.py:68-112` | `app.modules.attendance.feature_gate_demo` | `GET /api/attendance/shift-templates`，docstring 明寫「示範 Feature Gate 使用」。 |
| router endpoint | `feature_gate_demo.py:115-155` | `app.modules.attendance.feature_gate_demo` | `POST /api/attendance/split-shifts`，docstring 明寫「示範 Feature Gate 使用」。 |
| debug support API | `event_bus.py:58-75` | `app.core.event_bus` | `get_subscribers()` / `list_events()` docstring 明寫「用於測試/除錯」，被 `/api/test/event` 直接使用。 |

補充辨識說明：
- `admin_location_api.py` 雖名稱含 `admin_`，但其 CRUD 權限、JWT actor、RBAC 與正式業務模型一致，沒有 demo/test 命名或用途證據，因此不列為 non-production 元素。
- `register_event_handlers()` 雖在 startup 中被註冊，但其對應 `notifications.event_handlers.handle_attendance_approved()` 會寫入通知資料庫，屬 production legitimate，而非 demo/test 元素。

## 4. Classification (Prod vs Non-Prod)

### Production Legitimate（可留）

1. `main.py:99-100` → `register_event_handlers()`
   - 理由：`notifications/event_handlers.py:21-83` 的 `handle_attendance_approved()` 會將 `attendance.approved` 事件寫入通知資料庫，且有對應測試 `notifications/tests/test_event_handlers.py:30-155` 驗證成功與 fail-fast 行為。
   - 這是正式事件流的一部分，不是展示用途。

2. `main.py:106-121` → `/` 與 `/health`
   - 理由：屬於一般 production entry 基礎 endpoint，無 demo/test 命名，也不直接暴露內部測試能力。

3. `main.py:60-71` 中除 `attendance_gate_demo_router` 之外的正式 routers
   - 理由：來源模組皆為正式 API，像 `admin_location_api.py` 具 RBAC 與資料庫操作，並無「示範 / 測試」證據。

### Non-Production（應隔離）

1. `main.py:124-168` → `/api/test/event` GET / POST
   - 理由：路徑直接以 `/api/test/` 命名；docstring 分別標示「用於測試/除錯」與「用於測試」；功能是列出 subscriber 狀態與人工 emit `test.event`。

2. `main.py:83-97` → `demo_handler`、`attendance_approved_demo_handler` 與其 startup subscriptions
   - 理由：函式註解與 log 前綴均明示 `Demo Handler`，且其中一個只做 log 展示，另一個僅觀察 `attendance.approved` payload，不承載正式業務副作用。

3. `main.py:12,62` + `feature_gate_demo.py:1-155` → `attendance_gate_demo_router`
   - 理由：檔名為 `feature_gate_demo.py`，檔頭與各 endpoint docstring 均明寫「示範端點」與「示範 Feature Gate 使用」；回傳內容仍是 `stub implementation`，不屬成熟 production 功能。

4. `event_bus.py:58-75` 被 `/api/test/event` 使用的 introspection API
   - 理由：`get_subscribers()` / `list_events()` 在 docstring 中明寫「用於測試/除錯」；它們本身是支援能力，不一定要刪，但目前直接透過 production entry 暴露成 test API，應與 test endpoint 一併隔離。

## 5. Dependency Mapping

### A. `/api/test/event` GET (`main.py:124-141`)
- EventBus 依賴：有。呼叫 `get_event_bus()`、`list_events()`、`get_subscribers()`。
- Router 依賴：無獨立 router，直接綁在 `app`。
- Startup lifecycle 註冊依賴：間接有。若未先執行 `startup_event()`，列出的 subscriber 狀態將缺少 demo subscriber 與 notifications handler。
- 其他模組引用：未在 backend 搜尋到其他程式碼直接引用此 endpoint；但它依賴所有已註冊 subscriber 的狀態作為輸出。
- 文字依附圖：`main.py GET /api/test/event` → `get_event_bus()` → `EventBus.list_events/get_subscribers()` → 顯示 startup 已註冊 handlers 狀態。

### B. `/api/test/event` POST (`main.py:144-168`)
- EventBus 依賴：有。呼叫 `get_event_bus().emit("test.event", payload)`。
- Router 依賴：無獨立 router，直接綁在 `app`。
- Startup lifecycle 註冊依賴：有。沒有 `startup_event()` 中的 `event_bus.subscribe("test.event", demo_handler)`，此 endpoint emit 後不會有 demo log subscriber。
- 其他模組引用：未看到其他 Python module 呼叫此 endpoint；但它會觸發 `test.event` 的所有訂閱者。
- 文字依附圖：`main.py POST /api/test/event` → `EventBus.emit("test.event")` → `demo_handler`（目前唯一可見 subscriber）。

### C. `demo_handler` (`main.py:83-85`) + subscription (`main.py:96`)
- EventBus 依賴：有。透過 `event_bus.subscribe("test.event", demo_handler)` 掛載。
- Router 依賴：不依賴 router。
- Startup lifecycle 註冊依賴：有，完全依附於 `startup_event()`。
- 其他模組引用：未找到其他模組引用；僅由 startup 定義後立即註冊。
- 文字依附圖：`startup_event()` → local `demo_handler` → subscribe `test.event` → 被 `POST /api/test/event` 或任何 `emit("test.event")` 觸發。

### D. `attendance_approved_demo_handler` (`main.py:87-95`) + subscription (`main.py:97`)
- EventBus 依賴：有。透過 `event_bus.subscribe("attendance.approved", attendance_approved_demo_handler)` 掛載。
- Router 依賴：不依賴 router。
- Startup lifecycle 註冊依賴：有，完全依附於 `startup_event()`。
- 其他模組引用：被 `attendance/service.py:108-123` 的 `AttendanceService.approve_attendance()` 發出的 `attendance.approved` 事件間接觸發。
- 文字依附圖：`AttendanceService.approve_attendance()` → `EventBus.emit("attendance.approved")` → `attendance_approved_demo_handler` + `handle_attendance_approved` 同時收到事件。

### E. `attendance_gate_demo_router` (`main.py:12,62`, `feature_gate_demo.py:1-155`)
- EventBus 依賴：無。
- Router 依賴：有。`main.py` 直接 `include_router(attendance_gate_demo_router)`；router 自身 prefix 為 `/api/attendance`。
- Startup lifecycle 註冊依賴：無。
- 其他模組引用：依賴 `get_actor_with_company`、`get_db`、`get_feature_service`、`FeatureKeys`；與正式 attendance 模組共用 JWT actor / DB / feature gate 基礎設施。
- 文字依附圖：`main.py include_router(attendance_gate_demo_router)` → `/api/attendance/*` demo endpoints → JWT actor + DB + feature service → stub response。

### F. EventBus introspection methods (`event_bus.py:58-75`)
- EventBus 依賴：它們是 EventBus 本身的方法。
- Router 依賴：目前被 `/api/test/event` GET 使用；未見其他 production router 使用。
- Startup lifecycle 註冊依賴：輸出結果依賴 startup 時已註冊事件名稱與 subscriber。
- 其他模組引用：在本次搜尋範圍內未看到其他直接引用。
- 文字依附圖：`EventBus.list_events/get_subscribers` ← `/api/test/event` GET ← 觀察 startup wiring 結果。

## 6. High-Risk Isolation Points

### HIGH

1. `main.py:87-97` 的 `attendance_approved_demo_handler` 與其 subscription
   - 原因：它與正式事件 `attendance.approved` 共用同一條 event flow。`attendance/service.py:121-123` 在核准流程中會 emit 此事件；`notifications/event_handlers.py:86-98` 也在 startup 註冊同名正式 handler。若直接刪除或錯改 startup wiring，容易連帶影響對 `attendance.approved` 事件流的可觀測性，甚至誤傷正式 notifications handler 的註冊順序。

2. `main.py:99-100` 附近的 startup wiring 邊界
   - 原因：demo subscriptions 與 `register_event_handlers()` 置於同一個 `startup_event()` 中。隔離 demo 行為時若直接重寫整段 startup，會碰到 production legitimate 的 notifications wiring。

3. `main.py:124-168` 的 `/api/test/event` endpoints
   - 原因：雖屬 test/debug，但直接操作全域 EventBus。若現場有人依賴它檢查 `attendance.approved` 訂閱狀態或手動打事件，直接移除會中斷既有手動驗證流程。

### MEDIUM

1. `main.py:12,62` + `feature_gate_demo.py:1-155`
   - 原因：檔名與內容顯示為示範用途，但它已經是正式掛載路由，且使用真實 JWT actor / DB / feature service。若直接拿掉，可能影響目前用它進行 feature gate 驗證或示範的流程。

2. `event_bus.py:58-75` 的 introspection methods
   - 原因：這些方法支援 `/api/test/event`，不是正式公開 API，但可能也被測試或手動檢查工具使用。適合隨 test endpoint 一起搬移，不建議孤立刪除。

### LOW

1. `main.py:83-85` 的 `demo_handler` + `main.py:96` 的 `test.event` subscription
   - 原因：目前只做 log，且未看到其他模組發出 `test.event` 以外的正式依賴。它仍應隔離，但相較 `attendance.approved` demo handler，與正式業務耦合較低。

## 7. Isolation Strategy (Design Only)

1. **將 `/api/test/event` 從 `main.py` 直接綁定改為獨立 debug/test router 組件**
   - 保留 GET/POST 行為與路徑 contract，先不要刪 API。
   - 目標是讓 production entry 不再直接內嵌 test endpoint 定義；後續可由獨立 registration 決定是否掛載。
   - 初期可先做「搬家不改路徑」，之後再評估是否加上 dev/test gating。

2. **將 startup demo subscribers 從正式 startup wiring 拆成單獨 demo registration 單元**
   - `startup_event()` 僅保留必要 wiring 呼叫點；demo handler 定義與 subscribe 細節移到獨立 module。
   - 拆分時先保持預設仍會註冊，以達成 no-behavior-change；後續票再加入條件式 gating。

3. **將 `attendance_gate_demo_router` 改成條件式 include 的候選對象**
   - 設計上應與正式 attendance routers 分離，避免 `main.py` 同時知道 attendance 正式與示範子域。
   - 第一階段先抽成明確的 demo router registration 函式或 registration map；第二階段才考慮以 feature flag / env gating 控制是否掛載。

4. **保留 `register_event_handlers()` 為正式 startup wiring，不與 demo isolation 混拆**
   - Notifications event handlers 已屬 production legitimate，應在設計上與 demo subscriber 分開描述、分開拆票。
   - 也就是「先把 demo wiring 從 startup_event 剝離」，不是「重寫所有 startup 行為」。

5. **將 EventBus introspection 能力視為 debug support，不視為 production public API 的內建部分**
   - `EventBus.list_events()` / `get_subscribers()` 本體可先保留；但不應再由 `main.py` 直接公開成 production entry 的 `/api/test/*`。
   - 隔離重點在暴露面，不在於立刻移除底層方法。

6. **利用既有 `config.py` 的 testing / debug 設定作為未來 gating 候選，但本票不實作**
   - `config.py` 已有 `is_testing()` 與 `settings.debug` 可供後續設計使用。
   - 後續票可評估以 `TESTING` / `settings.debug` 控制 demo router 與 test endpoints 掛載，但這一步應在先完成結構隔離後再做，避免一次改動掛載與條件判斷兩種風險。

## 8. Step-by-Step Safe Decomposition Plan

### Step 1: isolate `/api/test/event` endpoint definitions（不改行為）
- 將 `GET/POST /api/test/event` 從 `main.py` 直接定義改為獨立 test/debug router 模組。
- 保持 path、method、payload contract 不變。
- 這一步只做結構搬移，不加 gating、不刪 endpoint。

### Step 2: isolate startup demo handler definitions（不改行為）
- 將 `demo_handler` 與 `attendance_approved_demo_handler` 的函式內容移出 `main.py`。
- `startup_event()` 只保留呼叫 demo registration 的 wiring。
- 預設仍註冊，確保行為與目前一致。

### Step 3: split production startup wiring from demo startup wiring（最小風險）
- 將 `register_event_handlers()` 與 demo subscriber registration 分成兩個明確步驟或兩個 registration function。
- 這樣後續若要關閉 demo wiring，不會碰到 production notifications wiring。

### Step 4: isolate `attendance_gate_demo_router` registration（不改 endpoint contract）
- 把 demo router 掛載規則抽成獨立 registration map / function。
- 繼續保留原本路徑 `/api/attendance/*`，避免影響現場使用者。

### Step 5: introduce explicit dev/test/demo gating（可選的下一階段）
- 在完成前四步、確認沒有行為回歸後，再引入 `settings.debug`、`is_testing()` 或新 env flag 做條件式掛載 / 註冊。
- 這一步才開始讓 production entry 有能力不載入 non-production 元素。

### Step 6: evaluate deprecation / removal ticket（最後一步）
- 只有在確認 `/api/test/event`、demo router、demo subscribers 沒有運維、手動驗證、測試流程依賴後，才可考慮刪除票。
- 移除必須是獨立 ticket，不應與結構隔離混在同一步。

## 9. Why Direct Removal Is Unsafe

1. **`/api/test/event` 直接操作全域 EventBus**
   - `main.py:124-168` 不是單純靜態測試頁，而是能列出目前訂閱者與直接 emit `test.event` 的入口。直接刪除會使現場失去觀察 EventBus wiring 與人工發送 test event 的手段。

2. **demo subscribers 與正式 notifications wiring 共處同一個 startup_event**
   - `main.py:74-102` 同時處理 demo 與正式 handler 註冊。若直接刪除整段或粗暴重寫，可能連 `register_event_handlers()` 一起受影響，造成 `attendance.approved` 不再寫入通知資料。

3. **`attendance.approved` demo handler 與正式事件流共用同一事件名稱**
   - `attendance/service.py:121-123` 會 emit `attendance.approved`；這個事件同時驅動 demo log 與 notifications DB 寫入。雖然 demo handler 本身可隔離，但不能在未拆開 wiring 前直接動整條事件註冊流程。

4. **`attendance_gate_demo_router` 雖為示範，但已掛在正式 API 空間 `/api/attendance`**
   - 使用者或測試若目前依賴這些 endpoint 進行 feature gate 驗證，直接刪除會造成 API surface 消失。

5. **EventBus introspection 能力可能被現有測試/人工排錯使用**
   - `event_bus.py:58-75` 明寫供測試/除錯使用；即便目前未找到所有外部依賴，也不能在證據不足時假設可安全移除。

因此，本票結論不是「直接刪掉 demo/test code」，而是「先把它們從 production entry 的核心 wiring 中分離，再決定是否以條件掛載或後續移除」。

## 10. Proposed Follow-up Tickets

### P0-3C-1 test event endpoint extraction
- 範圍：將 `main.py` 中 `/api/test/event` GET/POST 抽到獨立 debug router 模組。
- 限制：不得改 path / method / response contract。

### P0-3C-2 startup demo subscriber extraction
- 範圍：將 `demo_handler`、`attendance_approved_demo_handler` 與其 subscribe 邏輯移出 `main.py`，改為獨立 demo registration 單元。
- 限制：預設行為不變，`register_event_handlers()` 不得受影響。

### P0-3C-3 production-vs-demo startup split
- 範圍：將 production event handler wiring 與 demo subscriber wiring 明確分離。
- 限制：不得改變 `attendance.approved` 正式通知流程。

### P0-3C-4 feature gate demo router registration isolation
- 範圍：將 `attendance_gate_demo_router` 改為獨立 registration 邏輯，從 `main.py` 直掛中抽離。
- 限制：先不改 endpoint contract，不加新功能。

### P0-3C-5 demo/test gating design follow-through
- 範圍：評估並導入 `settings.debug` / `is_testing()` / env flag 作為 demo/test endpoint 與 subscriber 的掛載條件。
- 限制：必須在前述結構拆分完成後才可開始。
