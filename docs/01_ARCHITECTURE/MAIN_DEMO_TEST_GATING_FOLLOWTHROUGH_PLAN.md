# MAIN DEMO / TEST GATING FOLLOW-THROUGH PLAN

## 1. Summary
本文件針對已完成 `P0-3C-1 ~ P0-3C-4` 後的現況，設計下一步如何對 demo/test elements 加入 gating（條件掛載 / 條件註冊），使 production entry 未來可不載入 non-production elements，同時維持最小風險。

現場程式碼顯示，demo/test 元素已具備可施作 gating 的獨立 wiring 邊界：
- `debug_event_api.py` 已承接 `/api/test/event`。
- `demo_event_subscribers.py` 已承接 demo subscribers。
- `startup_wiring.py` 已分離 demo 與 production startup wiring。
- `router_wiring.py` 已分離 demo router 的掛載責任。

因此下一階段不應去改 endpoint / handler 本體，而應在 wiring 層進行 gating。最安全的順序是：先 gate `/api/test/event`，再 gate feature gate demo router，最後才 gate demo startup subscribers。原因是 startup subscribers 尤其 `attendance.approved` demo handler 會改變事件流的可觀測性，風險最高。

## 2. Files Inspected
必讀 source：
- `backend/app/main.py`
- `backend/app/modules/debug_event_api.py`
- `backend/app/modules/demo_event_subscribers.py`
- `backend/app/modules/startup_wiring.py`
- `backend/app/modules/router_wiring.py`
- `backend/app/core/config.py`

補充 source：
- `backend/app/modules/notifications/event_handlers.py`
- `backend/app/modules/attendance/feature_gate_demo.py`

Best-effort docs：
- `docs/01_ARCHITECTURE/MAIN_DEMO_TEST_ISOLATION_DESIGN.md`
- `docs/01_ARCHITECTURE/MAIN_ENTRY_BOUNDARY_DESIGN_REPORT.md`

Warnings：
- 無。上述 docs 皆可讀取。

## 3. Gating Candidate Inventory

| candidate | type | location | why it is a gating candidate |
|-----------|------|----------|-------------------------------|
| `/api/test/event` debug router | endpoint surface | `backend/app/modules/debug_event_api.py:7-55` | 路徑直接是 `/api/test/event`，功能為列出事件訂閱狀態與發送 `test.event`，屬明確 test/debug surface。 |
| `register_demo_routers(app)` | router wiring | `backend/app/modules/router_wiring.py:4-5` | 這是 demo router 現在唯一明確的掛載邊界；若要停止載入 feature gate demo router，應從此處條件式 include。 |
| `attendance_gate_demo_router` | demo router | `backend/app/modules/attendance/feature_gate_demo.py:20-155` | 檔名與 docstring 明示為 `feature_gate_demo` / `示範端點`，屬 non-production candidate，但應從 wiring 層 gate，不應改 router 內部。 |
| `register_demo_startup_handlers(event_bus)` | startup wiring | `backend/app/modules/startup_wiring.py:4-9` | 這是 demo startup subscribers 現在唯一明確的註冊邊界；若要避免 production 啟動時註冊 demo subscribers，應從此處條件註冊。 |
| `demo_handler` | subscriber | `backend/app/modules/demo_event_subscribers.py:6-8` | 明確為 `Demo 事件處理器`，只記錄 `test.event` payload，屬非正式觀測邏輯。 |
| `attendance_approved_demo_handler` | subscriber | `backend/app/modules/demo_event_subscribers.py:11-17` | 明確為 `Attendance 核准事件處理器（Demo，用於 log）`，只做 log 觀測，非 production 必要副作用。 |
| `register_demo_event_subscribers(event_bus)` | subscriber registration | `backend/app/modules/demo_event_subscribers.py:20-22` | 這是 demo subscriber 註冊邏輯的集中點；雖可作 candidate，但更適合由 `startup_wiring.py` 這層做 gating。 |

補充對照：production legitimate 對象不是 gating candidate，例如：
- `backend/app/modules/notifications/event_handlers.py:86-98` 的 `register_event_handlers()`，它會註冊 `attendance.approved` 正式 notifications handler。
- `backend/app/main.py:72-84` 仍保留 startup orchestration，但這層更適合保持簡單，不直接承擔細部 gating 判斷。

## 4. Recommended Gating Layer per Candidate

### A. `/api/test/event` debug router
- 建議 gating 層：`main.py` 的 router include / composition 層。
- 原因：`debug_event_api.py` 本身是 endpoint implementation；最乾淨的做法是不在 production entry 掛載這個 router，而不是掛載後再於 endpoint 內判斷。
- 不建議放在 endpoint 內部的原因：會留下 production surface，只是執行期回絕，邊界不乾淨。
- 不建議放在 `debug_event_api.py` 內 module-level 的原因：會讓 implementation 檔承擔 environment decision。

### B. `register_demo_routers(app)` / `attendance_gate_demo_router`
- 建議 gating 層：`router_wiring.py`。
- 原因：`router_wiring.py` 已是 demo router registration 的專門邊界。條件式 include 應放在這一層，避免污染 `feature_gate_demo.py` 內 endpoint 本體。
- 不建議直接改 `feature_gate_demo.py` 的原因：這會把 environment concern 混進 endpoint module。
- 不建議直接把判斷堆在 `main.py` 的原因：雖然可行，但會讓 entry 再次知道 demo router 細節，違反前面 `3C-4` 剛完成的隔離成果。

### C. `register_demo_startup_handlers(event_bus)` / demo subscribers
- 建議 gating 層：`startup_wiring.py`。
- 原因：`startup_wiring.py` 已將 demo startup wiring 與 production startup wiring 命名分離，最適合在這層控制是否註冊 demo subscribers。
- 不建議直接改 `demo_event_subscribers.py` 的原因：那會讓 handler module 同時承擔 behavior 與 environment concern。
- 不建議直接把 gating 放在 `main.py` 的原因：會讓 startup orchestration 再次膨脹，且不利後續觀察 production-vs-demo wiring 差異。

### D. `register_demo_event_subscribers(event_bus)`
- 建議 gating 層：不作為首選直接 gating 點。
- 原因：它是 demo subscribe 的內部註冊函式，但 `startup_wiring.py` 已提供更外層、更清楚的 startup boundary。從更外層 gate 較安全，也更符合 composition root 原則。

## 5. Current Config Capability Review

`backend/app/core/config.py` 現況提供兩個可見候選：
- `settings.debug` (`config.py:41-42`)
- `is_testing()` (`config.py:9-25`)

### `settings.debug` 是否可作為 gating 依據
- 可以作為 debug-only surface 的第一階段 gating 候選，尤其是 `/api/test/event`。
- 原因：`/api/test/event` 是最純粹的 debug/test API surface，用 `debug` 控制是否掛載，語意相對直觀。
- 侷限：`debug` 通常代表除錯模式，不一定等於「允許 demo router」；若未來 staging 需要 demo router 但不想開整體 debug，單靠 `debug` 不一定足夠。

### `is_testing()` 是否可作為 gating 依據
- 可以作為測試環境特定的補充依據，但不適合作為唯一 gating source。
- 原因：`is_testing()` 主要檢查 pytest 與 `TESTING` env，適合控制測試專用載入，但不能覆蓋一般開發 / staging demo 驗證場景。
- 侷限：若只用 `is_testing()`，dev 手動測試不一定能載入 demo/test elements。

### 哪些元素適合吃 `debug`
- `/api/test/event`：適合。因為它是最明顯的 debug surface。
- `register_demo_routers(app)`：部分適合，但要注意 demo router 不一定只服務 debug；若現場仍用於 feature gate 展示，單靠 `debug` 可能過窄。

### 哪些元素適合吃 `testing`
- `/api/test/event`：可作為測試環境補充條件。
- demo subscribers：理論上可，但若 dev / staging 需要事件觀測，單靠 testing 會不夠。

### 哪些情境無法只靠現有 config 安全覆蓋
- `feature_gate_demo_router` 的載入策略。
- `attendance_approved_demo_handler` 的觀測性保留策略。

原因：這兩者可能存在「非 production 但也不等於 debug/testing」的 staging / internal demo 場景。現有 `debug` 與 `is_testing()` 可以支撐第一階段設計，但是否足夠成為最終 gating source，仍有 evidence gap。

## 6. Risk Ranking

### LOW
1. `/api/test/event` debug router
   - 原因：最明確的 test/debug surface，不屬正式業務 API。條件掛載只影響 debug 能力，不直接碰正式事件寫入或 tenant 邏輯。

### MEDIUM
1. `register_demo_routers(app)` / `attendance_gate_demo_router`
   - 原因：雖是 demo router，但它仍使用真實 JWT actor / DB / feature gate service，可能被 dev/staging 作為示範或驗證入口。條件關閉會移除 API surface，但不直接影響核心事件流。

### HIGH
1. `register_demo_startup_handlers(event_bus)`
2. `demo_handler`
3. `attendance_approved_demo_handler`
4. `register_demo_event_subscribers(event_bus)`
   - 原因：這些項目會直接影響 startup 註冊結果與 `attendance.approved` 的可觀測性。
   - 尤其 `attendance_approved_demo_handler` 雖只是 log，但與 production notifications handler 共用同一事件名稱；若 gating 設計不清楚，會讓排錯、手動驗證、`/api/test/event` 回傳的 subscriber 名稱觀測一起變化。

## 7. Safe Gating Strategy (Design Only)

1. **先在 composition / wiring 層做 gating，不改 endpoint 與 handler 本體**
   - `/api/test/event`：在 `main.py` 的 debug router include 點做條件掛載。
   - demo router：在 `router_wiring.py` 的 `register_demo_routers(app)` 做條件 include。
   - demo subscribers：在 `startup_wiring.py` 的 `register_demo_startup_handlers(event_bus)` 做條件註冊。

2. **第一階段優先使用現有 config，避免新增設定項**
   - 對 `/api/test/event`：可優先評估 `settings.debug or is_testing()`。
   - 對 demo router 與 demo subscribers：可先做設計比較，但不急著立刻實作，因為現有 config 是否足夠仍有 evidence gap。

3. **不要在 individual module 內部加 if/else gating**
   - 不要在 `debug_event_api.py` endpoint 裡判斷環境。
   - 不要在 `feature_gate_demo.py` endpoint 裡判斷環境。
   - 不要在 `demo_event_subscribers.py` handler 內判斷環境。
   - 理由：這會讓 demo/test implementation 本體承擔 environment concern，破壞剛完成的結構隔離。

4. **先接受「已隔離、未關閉」的中間狀態，不追求一次完成所有 gating**
   - 目前最安全的方向是逐步把非 production surfaces 轉為 conditional registration，而不是一次全面關閉。

## 8. Step-by-Step Rollout Plan

### Step 1: gate debug event router
- 目標：讓 `/api/test/event` 成為條件式掛載。
- 建議位置：`main.py` 對 `debug_event_router` 的 include。
- 為什麼先做：最明確、最低風險、對 production surface 改善最直接。
- 主要驗證點：
  - 非 gating 條件下，`GET/POST /api/test/event` 仍存在。
  - gating 條件關閉時，這兩個 route 不再出現在 app routes 中。

### Step 2: gate feature gate demo router
- 目標：讓 `register_demo_routers(app)` 成為條件式掛載。
- 建議位置：`router_wiring.py`。
- 為什麼第二步做：已完成 `3C-4` 的 registration isolation，現成邊界可用；但它比 `/api/test/event` 風險更高，因為會移除一整組 demo API。
- 主要驗證點：
  - gating 開啟時，`/api/attendance/shift-overrides`、`/shift-templates`、`/split-shifts` 仍存在。
  - gating 關閉時，這三個 demo routes 不再掛載。

### Step 3: gate demo startup subscribers
- 目標：讓 `register_demo_startup_handlers(event_bus)` 成為條件式註冊。
- 建議位置：`startup_wiring.py`。
- 為什麼最後做：這一步會改變事件觀測與 `/api/test/event` 的 subscriber 名稱回傳結果，且與 `attendance.approved` 的 runtime 可觀測性直接相關，風險最高。
- 主要驗證點：
  - gating 開啟時，`demo_handler` 與 `attendance_approved_demo_handler` 仍在 subscriber list 中。
  - gating 關閉時，production notifications handler 仍存在，而 demo subscribers 消失。
  - `register_event_handlers()` 仍不受影響。

## 9. Why All-at-Once Gating Is Unsafe

1. **三類對象風險不同**
   - `/api/test/event` 是單純 debug surface。
   - `attendance_gate_demo_router` 是一組 demo API surface。
   - demo startup subscribers 會影響 event flow 可觀測性。
   一次同改，難以判斷是哪一層造成問題。

2. **rollback 會變困難**
   - 若同時對 routes、demo router、startup subscribers 加 gating，一旦出現 event flow 或手動驗證問題，很難精準回退單一變更。

3. **驗證維度不同**
   - route gating 重點是 API surface 有無掛載。
   - startup subscriber gating 重點是 runtime 事件註冊狀態。
   - 兩者需要不同驗證方式，不應混成一次大變更。

4. **現有 config 能力是否足夠仍有 evidence gap**
   - 對 `/api/test/event`，`debug/testing` 已較合理。
   - 對 demo router 與 demo subscribers，是否應共用同一 gating source 還未有足夠現場證據。一次全做會把設計不確定性帶入實作。

## 10. Proposed Follow-up Tickets

### P0-3C-5A debug event router gating
- 範圍：僅對 `/api/test/event` 的 router include 做條件掛載。
- 風險：LOW。

### P0-3C-5B feature gate demo router gating
- 範圍：對 `register_demo_routers(app)` 做條件式 include。
- 風險：MEDIUM。

### P0-3C-5C demo startup subscriber gating
- 範圍：對 `register_demo_startup_handlers(event_bus)` 做條件式註冊。
- 風險：HIGH。

### P0-3C-5D gating source adequacy review
- 範圍：若 `debug` / `is_testing()` 無法覆蓋 staging/internal demo 需求，再單獨設計是否需要專用 demo flag。
- 風險：MEDIUM，且必須在前述 design evidence 基礎上進行。
