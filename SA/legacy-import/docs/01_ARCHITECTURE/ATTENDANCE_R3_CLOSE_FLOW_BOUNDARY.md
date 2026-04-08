# ATTENDANCE R3 Close-Flow Dependency Boundary (Source of Truth)

## 1. Summary
R3 完成的是「依賴方向收斂」，不是功能變更。  
核心修正是：解除 `service.py` 對 `api/*` 的直接依賴，將 close-flow 的 domain assembly 移至非 API 檔案。  
因此 R3 的目的在於恢復分層一致性、降低未來耦合風險，而不是改變 punch-out 的業務結果或 API 回傳契約。

## 2. Problem Statement（Before R3）
R3 之前，`service.py` 直接 import `api/punch_close_flow.py`，並使用其中的 `build_policy_evaluation` 與 `PolicyEvalPayload`。  
此狀態形成層向反轉：下層 orchestration/service 依賴上層 API 目錄，導致責任混層（mixed responsibility）。

為何是結構脆弱而非立即 bug：
- 目前流程仍可運行，但維護時 API 層調整可能被動衝擊 service。
- API 檔案承載 domain assembly，長期容易讓 API 與 domain 演進互相綁死。
- 擴充 close-flow 功能時，無法清楚區分「路由責任」與「業務組裝責任」。

## 3. Final Dependency Direction（最重要）
- `service` 可依賴：attendance 模組內的非 API domain/helper、repo、engine（依既有架構規範）。
- `api` 層可依賴：service 與必要 helper；其責任是 entrypoint、request/response orchestration。
- `service` **不得依賴** `api/*`。
- close-flow domain assembly **必須位於非 API 檔案**，不可放回 `api/` 主體。

## 4. New Structure Definition
目前結構定義如下：
- `punch_close_domain.py`：承載 close-flow domain assembly（含 `PolicyEvalPayload`、`build_policy_evaluation*`）。
- `api/punch_close_flow.py`：僅保留相容層（shim）責任，不作主邏輯承載。
- `service.py`：從非 API helper import，維持 orchestration 與 internal channel 邊界。
- `AttendancePolicyEngine` / `policy_rules`：本票不變更其責任與行為，仍分別維持正式規則與 pure calculation。

## 5. Shim Rule（關鍵）
- `api/punch_close_flow.py` 可以作為過渡 shim（re-export / compatibility）。
- shim **不得重新承載** close-flow domain assembly 主邏輯。
- 若 shim 開始長出主邏輯（計算、策略分支、核心組裝），視為違規，必須回到非 API helper。

## 6. Safe Edit Rules（R3 專屬）
R3 類型修正允許（最小必要）：
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/api/punch_close_flow.py`
- `backend/app/modules/attendance/api/punch.py`（僅必要路徑調整）
- 1 個新建非 API close-flow helper 檔

R3 類型修正禁止：
- `repo.py`、`policy_engine.py`、`policy_rules.py`
- tests（本票不修測試）
- docs 以外其他範圍擴張（除 R3 必要檔案）

## 7. Deferred Items
以下項目維持 deferred，且不屬於 R3 本票：
- tests deferred
- docs deferred（若仍有歷史文件待同步）
- R2 deferred（repo `hasattr` fallback）
- legacy test compatibility deferred（含 legacy headers）

## 8. Risk If Violated
若違反本文件邊界，將導致：
- service 再次依賴 `api/*`，層向反轉回流。
- API/domain 混層復發，責任切分失真。
- shim 失控成為真主邏輯承載點，過渡層永久化。
- 版本演進與變更評估成本上升，回歸風險擴大。

## 9. Enforcement Notes（給 Cursor）
- 不得把 close-flow domain assembly 放回 `api/`。
- 不得讓 `service` 直接 import `api/*`。
- 若需新增 close-flow 能力，優先在非 API helper/domain 檔實作，再由 API/service 消費。
- 若要移除 shim，必須另開票，先確認無相容性依賴，再執行收斂。
