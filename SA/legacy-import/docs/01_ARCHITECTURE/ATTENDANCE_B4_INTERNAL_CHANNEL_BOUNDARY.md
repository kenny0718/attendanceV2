# ATTENDANCE B4 Internal Channel Boundary (Source of Truth)

## 1. Summary
B4 修正了一個關鍵邊界風險：`internal dry-run` 資料不應再附掛到任何正式 payload/result object。  
在 B4 前，service 會把 internal dry-run 結果動態掛到正式回傳物件，這在目前流程未必會外洩，但會造成未來序列化與除錯管道的高風險不確定性。  
B4 的必要性在於：把 internal channel 與正式輸出做結構性隔離，讓規則邊界可長期維持、可審計、可驗證。

## 2. Problem Statement（Before B4）
Before B4，service 在正式流程結束後，曾使用動態附掛方式把 dry-run 結果掛到正式 payload object（例如 `setattr(payload, "_internal_xxx", ...)` 類型模式）。

此模式的風險：
- **序列化風險**：若未來某層序列化器使用泛化規則（含 `__dict__` 掃描），internal 欄位可能被誤輸出。
- **外洩風險**：debug / logging / telemetry 若對物件做反射式採集，可能帶出 internal 資訊。
- **契約漂移風險**：payload object 的隱性欄位使對外 contract 行為不穩定，增加前後端誤依賴機率。

B4 的修正方向是：internal 資料只留在 service 內部通道，不再依附正式物件生命週期。

## 3. Final Boundary Definition（最重要）
### service
- 允許：orchestration、input 組裝、pure rule 呼叫、internal channel 保留。
- 禁止：把 internal data attach 到任何可能成為對外輸出的 result/payload object。

### policy_engine
- 是正式 late/early/overtime 等結果的唯一規則來源。
- 不得接收 internal dry-run side channel。
- 不承擔 B4 internal channel 的資料承載責任。

### policy_rules
- pure calculation only。
- 不得包含 orchestration、state 持有、動態附掛、輸出通道管理。

## 4. Internal Channel Rules（關鍵規則）
internal data（包含 dry-run 結果與其 input/source metadata）必須遵守：
- 只存在於 service 層。
- 不可附掛到 payload/result object。
- 不可出現在 API response。
- 不可透過 `__dict__` 或反射式輸出暴露。

明確禁止模式（禁止重新引入）：
- `setattr(payload, "_internal_xxx", ...)`
- `setattr(result, "_internal_xxx", ...)`
- 任意動態附掛 internal 屬性到正式回傳物件

## 5. Safe Edit Rules（B4 專屬）
B4 類型邊界收斂，只允許：
- 修改 `backend/app/modules/attendance/service.py`

明確禁止：
- 修改 `backend/app/modules/attendance/policy_engine.py`
- 修改 `backend/app/modules/attendance/policy_rules.py`
- 修改 `backend/app/modules/attendance/api/*`

理由：B4 目的是收斂 internal channel 邊界，而非重構正式規則核心或 API contract。

## 6. Deferred Items
以下項目在 B4 明確維持 deferred：
- **R2**：repo `hasattr` fallback 介面穩定性議題（deferred）
- **R3**：service import API layer 的層向依賴議題（deferred）
- **test compatibility（legacy headers）**：舊測試與現行 auth gate 不相容（deferred）

以上項目需未來獨立票處理，不屬 B4 交付範圍。

## 7. Risk If Violated
若違反本文件邊界，可能造成：
- internal data 洩漏到 API（直接或經由序列化路徑）
- debug / log / telemetry 洩漏 internal context
- payload contract 不穩定，導致跨層誤依賴
- 前端或外部系統誤用非契約欄位，造成回歸風險

## 8. Enforcement Notes（給 Cursor）
對 AI/自動化修改的強制約束：
- 不得重新引入 internal attach 到 payload/result object。
- 不得把 internal data 放入 DTO/schema/response model。
- 若未來需要 expose internal trace，必須走新票設計（例如正式 trace framework），先定義 schema、邊界與安全策略，再實作。
- B4 以後任何涉及 internal channel 的改動，需先檢查是否違反本文件第 3、4、5 節。
