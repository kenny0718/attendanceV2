# SA21_REALIGNMENT_ROADMAP

## goal

以 SA2.1 為核心規範，將現行專案從「文件/邊界/流程漂移狀態」拉回可持續治理狀態，並建立可執行的 P0/P1/P2 路線。

---

## guiding principles

1. **Code Reality First**：實際程式碼優先於歷史文件敘述。
2. **Boundary First, Feature Second**：先修正邊界，再擴增功能。
3. **Small Safe Steps**：用小票拆分，禁止一次大改核心模組。
4. **SOT Single Line**：同時期只能有一組主 SOT。
5. **No Hidden Refactor**：每張票僅處理單一責任，不挾帶範圍外重構。

---

## P0 / P1 / P2 development order

## P0（必須先對齊的結構/邊界）

1. **SOT 對齊完成**
   - 以 `SA21_GAP_AUDIT_REPORT.md` + 本文件作為主 SOT。
   - 歷史控制文件改以 archive 參照，不再主導執行決策。

2. **API path contract 對齊治理**
   - 清點 frontend 各 API wrapper 路徑規格。
   - 消除 `baseURL + absolute path` 混用規則漂移。

3. **入口層責任收斂治理（設計與票分解）**
   - `main.py` 的 startup/demo/debug endpoint 責任拆票，先定邊界後實作。

## P1（應優先拆分或補強）

1. **attendance service 邊界拆分**
   - 把 segment 推導相關責任從主 service 主流程中抽離為可控子層（先設計後實作）。

2. **reporting router 輕量化**
   - 維持 `repo/service` 分層，進一步下放 router 組裝責任。

3. **schedule view 去單點過載**
   - 將 `SchedulePage.vue` 以 template/assignment 子域拆分元件與狀態責任。

## P2（可在後續功能開發時逐步處理）

1. leave type UX 對齊（避免 UUID 手輸）
2. 報表顯示層細節一致性
3. 舊文件補註與索引導覽優化

---

## suggested split/refactor tickets

### Ticket P0-1: SOT Lock
- 目標：將新 SOT 文件加入開工讀取順序並鎖定。
- 交付：治理讀取順序更新、舊文件標記 archived/superseded。

### Ticket P0-2: Frontend API Path Contract Alignment
- 目標：統一路徑規則（相對 baseURL）。
- 範圍：`frontend/src/api/*`。
- 非目標：不變更 backend endpoint。

### Ticket P0-3: Main Entry Boundary Plan
- 目標：拆出 `main.py` 責任地圖與遷移步驟。
- 範圍：僅設計與切票，不直接重寫入口。

### Ticket P1-1: Attendance Service Boundary Split Plan
- 目標：把 missing-segment dry-run 周邊邏輯從主 service 解耦。
- 範圍：先完成 interface/flow 設計與風險評估。

### Ticket P1-2: Reporting Router Thin-Layer Refine
- 目標：router 僅保留 request parse/scope check/dispatch。
- 範圍：不變更 response contract。

### Ticket P1-3: SchedulePage Decomposition
- 目標：拆分 `SchedulePage.vue`，降低單頁責任密度。
- 範圍：先拆展示與操作區塊，再拆狀態編排。

### Ticket P2-1: Leave Type Contract UX Alignment
- 目標：提供 leave type 可選資料來源，移除手動 UUID 輸入依賴。

---

## module-by-module next actions

### backend/main
- next: 先建立 composition 邊界草圖與掛載清單，避免直接改碼。
- watchout: 啟動流程與 router mount 順序不可破壞。

### attendance
- next: 先做 close-flow / segment-flow 責任圖，再決定拆分點。
- watchout: policy 計算語意不可在拆分中漂移。

### reporting
- next: 確認 router/service/repo 契約邊界，避免回流為單一大檔。
- watchout: response schema 與 query filter 規則不可改變。

### schedule (frontend)
- next: 規劃拆分子元件與 state ownership。
- watchout: 不可一次重寫整頁。

### leave (frontend/backend contract)
- next: 定義 leave type 來源契約（只先定義，不先擴功能）。
- watchout: 不可破壞既有 create request flow。

---

## stop conditions / risk notes

1. 任一票若涉及跨層改動（router + service + repo 同步）必須中止，改為分票。
2. 任一票若需要 whole-file rewrite，必須中止並重新切分。
3. 任一票若無法保持既有 API contract，必須先產生契約差異報告再決策。
4. 若 runtime 證據不足，先標示 evidence gap，不可推測定論。

---

## what must not be touched early

1. 不可先動核心打卡語意（punch ownership / policy baseline semantics）。
2. 不可先做 `main.py` 大重構。
3. 不可先做跨模組大型搬遷（attendance ↔ schedule ↔ reporting 混改）。
4. 不可在 P0 未完成前啟動新大功能擴張。

---

## superseded and archive references

本 roadmap 所依據的 superseded 文件已移動至：

- `docs/archive/260402/03_WP_CONTROL/*`
- `docs/archive/260402/01_ARCHITECTURE/ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md`

目前 SA2.1 對齊主依據：

1. `docs/01_ARCHITECTURE/SA21_GAP_AUDIT_REPORT.md`
2. `docs/03_WP_CONTROL/SA21_REALIGNMENT_ROADMAP.md`
