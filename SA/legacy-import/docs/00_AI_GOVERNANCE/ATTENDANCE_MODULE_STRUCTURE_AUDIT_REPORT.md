# Attendance 模組結構審計報告

**審計範圍**
- `backend/app/modules/attendance`
- `docs/00_AI_GOVERNANCE`

**參考文件**
- `docs/00_AI_GOVERNANCE/CURSOR_EXECUTION_CONTROL.md`
- `docs/00_AI_GOVERNANCE/CURSOR_BACKEND_SAFE_EDIT_RULES.md`
- `docs/00_AI_GOVERNANCE/AI_CONTEXT.md`
- `docs/01_ARCHITECTURE/SA_MODULE_SPEC_v2.1.md`

**審計模式**
- Read-only analysis based
- 不包含程式碼修改
- 不包含修正 diff

**審計日期**
- 2026-04-04

---

# 1. Summary（整體健康度）

## 1.1 總結論
目前 Attendance 模組已明顯從 monolithic `attendance/api.py` 朝子模組化架構前進，`api` 層已拆分為 `punch`、`breaks`、`checkpoints`、`reporting`、`legacy`，並完成 `router_v1` 聚合，整體方向與 SA2.1 的模組分層要求基本一致。

然而，系統仍存在數個關鍵偏差，特別是：

1. `duration_minutes` 的 canonical 語意與 SA2.1 v2.1 不一致。
2. 部分 API handler 仍直接操作 ORM / query，service / repo 邊界未完全收斂。
3. `reporting` 雖已拆層，但未來新增報表時存在擴張失控風險。
4. 部分核心檔案高度集中，若直接修改，風險高且爆炸半徑大。

## 1.2 整體評估
- **架構對齊度**：中等偏高
- **可維護性**：中等
- **擴展性**：中等
- **立即性風險**：中
- **後續開發阻力**：中高

## 1.3 健康度判定
**整體健康度：中等，偏可控，但尚未完全符合 SA2.1 的正式分層與 canonical 計算規範。**

---

# 2. SA2.1 衝突清單

## 2.1 目前 Attendance 模組結構

目前 `backend/app/modules/attendance` 主要結構如下：

- `api/`
  - `__init__.py`
  - `legacy.py`
  - `punch.py`
  - `breaks.py`
  - `checkpoints.py`
  - `reporting.py`
  - `reporting_helpers.py`
  - 其他 API 相關輔助模組
- `service.py`
- `repo.py`
- `checkpoint_repo.py`
- `reporting_repo.py`
- `reporting_service.py`
- `reporting_schemas.py`
- `models.py`
- `schemas.py`
- `policy_engine.py`
- `location_policy_service.py`
- `gps_utils.py`
- `tests/`
- `docs.md`

此結構已符合 SA2.1 對模組基本存在物件的要求：
- `api.py` / API façade（目前轉為 `api/` package）
- `service.py`
- `repo.py`
- `models.py`
- `docs.md`
- `tests/`

## 2.2 與 SA2.1 的主要偏差

### 衝突 A：`duration_minutes` 的 canonical 定義與 SA2.1 v2.1 不一致
- **嚴重度**：HIGH
- **是否影響後續開發**：是

SA2.1 v2.1 規定 `session.duration_minutes` 應代表 canonical 的 `work_duration`，亦即：

- `raw_duration = punch_out_time - punch_in_time`
- `work_duration = raw_duration - break_duration`
- `session.duration_minutes = work_duration`

但目前 `punch-out` 流程中，系統將 `gross_minutes` 寫回 `session.duration_minutes`，並明確標示 break deduction 僅為 derived / informational，不寫回 DB。

### 風險說明
這代表 reporting 雖讀取 `duration_minutes`，但讀到的並非 SA2.1 規範定義的 canonical work duration，而是 gross duration。後續若導入正式 Work Hour Engine、報表月結、加班統計，將出現語意切換與資料一致性問題。

---

### 衝突 B：API / service / repo 邊界未完全收斂
- **嚴重度**：MEDIUM
- **是否影響後續開發**：是

目前 `breaks.py` 仍存在 API handler 直接使用 ORM 查詢與直接更新資料的情況，包含：
- 直接 query `AttendancePunch`
- 直接在 router 中修改 `punch.notes`
- 直接在 API 層執行 DB commit

### 風險說明
這使 API 層同時承擔：
- request parsing
- 資料存取
- domain action
- response shaping

此種責任混用會導致 router 持續膨脹，後續若加入 audit、policy 或 permission 擴充，維護成本會快速上升。

---

### 衝突 C：業務日期邊界與 SA2.1 v2.1 時區規則不完全一致
- **嚴重度**：HIGH
- **是否影響後續開發**：是

SA2.1 v2.1 規定：
- 業務日邊界必須以 `Asia/Taipei` 為準
- 今天 / 本週 / 本月 不得直接以 UTC 日期視為業務日期

但 `break-punches` 查詢目前使用：
- `date.today()`
- `datetime.combine(...).replace(tzinfo=timezone.utc)`

此作法實際上是以 UTC 日界線處理，而不是以 Taipei 業務日界線處理。

### 風險說明
此偏差將導致：
- 凌晨時段查詢錯日
- break list 與 reporting 邊界不一致
- 後續 trace / audit / 月報查詢出現體感錯誤

---

### 衝突 D：`service.py` / `repo.py` 同時承載 legacy 與新架構責任
- **嚴重度**：MEDIUM
- **是否影響後續開發**：是

目前：
- `repo.py` 同時包含新版 `AttendanceSessionRepository` 與舊版 `AttendanceRepository`
- `service.py` 同時包含 legacy attendance record flow 與新版 punch-out orchestration

### 風險說明
此種混存短期可維持兼容，但中期會造成：
- 檔案中心化
- 模組語意不純
- 易形成 unsafe edit 高風險核心檔

---

### 衝突 E：reporting company summary 採全量拉取聚合
- **嚴重度**：MEDIUM
- **是否影響後續開發**：是

`company-summary` 目前將全公司符合條件的 sessions 全量拉回應用層，再由 `reporting_service.py` 進行聚合。

### 風險說明
此作法在資料量小時可接受，但未來若增加：
- daily summary
- abnormal summary
- overtime summary
- location analytics
- department summary

則 reporting 會快速遭遇效能與複雜度問題。

---

## 2.3 SA2.1 對齊狀態總評

| 項目 | 狀態 | 評語 |
|---|---|---|
| 模組拆分方向 | 基本符合 | 已從 monolithic 走向子模組結構 |
| API 分層 | 部分符合 | reporting 分層較好，breaks 邊界仍鬆散 |
| service / repo 邊界 | 部分符合 | 仍有 API 直接碰 ORM 的情況 |
| Reporting read-only 原則 | 基本符合 | 未寫資料，但 canonical 值本身有語意偏差 |
| canonical work hour 規則 | 不符合 | `duration_minutes` 寫入 gross_minutes |
| 時區 / 業務日規則 | 部分不符合 | break-punches 與 Taipei 業務日規則不一致 |

---

# 3. reporting.py 風險結論

## 3.1 reporting.py 目前責任清單

目前 `api/reporting.py` 承擔以下責任：

1. request query 參數接收
2. actor / scope 驗證
3. feature gate 檢查
4. datetime range 驗證與 UTC normalization
5. 呼叫 reporting repository 查詢資料
6. 呼叫 reporting service 執行 summary aggregation
7. response shaping
8. display name lookup（sessions list）

## 3.2 是否包含過多 orchestration
**結論：有一些，但尚未失控。**

評估如下：
- `GET /sessions`：中度 orchestration
- `GET /reports/user-summary`：低到中
- `GET /reports/company-summary`：中

原因是 reporting.py 已將純工具與純聚合邏輯分出：
- `reporting_helpers.py`
- `reporting_repo.py`
- `reporting_service.py`
- `reporting_schemas.py`

因此它目前仍屬於可接受的 API orchestration 層，而不是嚴重肥大 controller。

## 3.3 response shaping 是否過重
**結論：中等，可接受，但已接近預警線。**

目前 `sessions` endpoint 仍在 router 內逐筆組裝 `SessionResponse`，並查詢 `display_name`。這種 response shaping 現階段合理，但若未來報表欄位持續增加，router 會逐步膨脹。

## 3.4 是否混入 domain logic
**結論：少量，但不嚴重。**

summary 計算已被放入 `reporting_service.py`，此部分屬於 reporting 的 read-model aggregation，放在 service 層可接受。真正風險不在 domain logic 混入，而在於：
- service 所讀取的 canonical 欄位目前語意不完全符合 SA2.1

## 3.5 行數 / 複雜度評估

目前主要 reporting 檔案行數：
- `api/reporting.py`：214 行
- `reporting_repo.py`：165 行
- `reporting_service.py`：109 行

### 判定
- `reporting.py` 本身尚未達到失控巨檔程度
- 已進入「未來再擴 2~3 類報表就會開始不穩」的區間

## 3.6 未來新增報表是否會導致失控
**結論：有中高風險。**

原因：
1. 所有 reporting endpoint 仍集中於單一 `api/reporting.py`
2. company summary 採全量載入聚合
3. scope / feature gate / datetime validation 在新報表中很可能重複擴散
4. response shaping 會隨報表數量持續增加

## 3.7 是否已達必須拆分門檻
**結論：NO**

### 理由
- 目前 `reporting.py` 雖有成長壓力，但尚未超出可維護範圍
- 真正優先問題不是檔案行數，而是：
  - canonical work duration 定義不一致
  - company summary 聚合策略未準備好面對未來資料量

### 最終判定
- **是否必須拆分**：NO
- **是否接近拆分預警線**：YES

---

# 4. Router 完整性結論

## 4.1 `attendance/api/__init__.py` router 組裝結構

目前 `attendance/api/__init__.py` 已完成 v1 router 聚合：
- legacy router
- punch router
- breaks router
- checkpoints router
- reporting router

### 結論
**router 組裝結構完整。**

## 4.2 `router_v1` / `router` 掛載狀態

`main.py` 目前已掛載：
- `attendance_router`
- `attendance_router_v1`

因此：
- `/api/attendance/*` legacy 路由可達
- `/api/v1/attendance/*` v1 路由可達

### 結論
**掛載鏈路完整。**

## 4.3 `main.py` 掛載鏈路

Attendance 路由鏈路為：

1. `main.py`
2. `app.modules.attendance.api`
3. `attendance/api/__init__.py`
4. `legacy / punch / breaks / checkpoints / reporting`

### 結論
**主鏈路完整，未見遺漏。**

## 4.4 所有 endpoint 可達性盤點

### Legacy
1. `POST /api/attendance/mock-create`
2. `POST /api/attendance/{attendance_record_id}/approve`

### V1 Punch
3. `POST /api/v1/attendance/punch-in`
4. `POST /api/v1/attendance/punch-out`
5. `GET /api/v1/attendance/current-status`
6. `GET /api/v1/attendance/history`

### V1 Breaks
7. `POST /api/v1/attendance/break-out`
8. `POST /api/v1/attendance/break-in`
9. `GET /api/v1/attendance/break-punches`
10. `PATCH /api/v1/attendance/punch/{punch_id}/note`

### V1 Checkpoints
11. `POST /api/v1/attendance/out-checkpoint`
12. `GET /api/v1/attendance/out-checkpoints`

### V1 Reporting
13. `GET /api/v1/attendance/sessions`
14. `GET /api/v1/attendance/reports/user-summary`
15. `GET /api/v1/attendance/reports/company-summary`

### 可達性總結
**目前從靜態掛載檢查判定，Attendance 共 15 個 endpoint 皆可達。**

## 4.5 是否存在未掛載 router
**結論：未見正式 router 漏掛。**

## 4.6 是否存在 import 錯誤風險
**結論：有，中等。**

雖然目前鏈路完整，但以下因素使其仍有 import 脆弱性：
- `attendance/api/__init__.py` 為集中式 eager import
- `main.py` 為集中依賴入口
- 任一子 router import 失效，都可能使整個 attendance API 載入失敗

## 4.7 是否存在重複或遺漏路由
**結論：未見明顯重複 prefix 衝突，也未見遺漏。**

補充觀察：
- `reporting.py` 使用 `router`
- 其他子模組多使用 `router_v1`

此命名不一致不是功能錯誤，但增加維護認知成本。

---

# 5. 高風險檔案清單（含分級）

以下以檔案中心性、體積、依賴爆炸半徑、unsafe edit 後果為基準進行分級。

## 5.1 P0（禁止動）

### 1. `backend/app/main.py`
- **分級**：P0
- **風險原因**：FastAPI 入口、集中匯入多模組 router、任一 import 失誤即可使整體應用無法啟動
- **是否接近或超過 size gate**：否
- **是否建議禁止直接修改**：是

### 2. `backend/app/modules/attendance/api/__init__.py`
- **分級**：P0
- **風險原因**：Attendance 全部 router 的聚合點，任一 include 或 import 損壞即可導致整體 attendance v1 失效
- **是否接近或超過 size gate**：否
- **是否建議禁止直接修改**：是

### 3. `backend/app/modules/attendance/repo.py`
- **分級**：P0
- **風險原因**：同時承載新版 session/punch repo 與舊版 legacy repo，且為多個核心流程共用的資料層中心檔
- **是否接近或超過 size gate**：是（408 行）
- **是否建議禁止直接修改**：是

## 5.2 P1（只能局部改）

### 4. `backend/app/modules/attendance/api/punch.py`
- **分級**：P1
- **風險原因**：涵蓋 punch-in / punch-out / history / current-status，且直接關聯 canonical 工時語意與 policy evaluation
- **是否接近或超過 size gate**：是（352 行）
- **是否建議禁止直接修改**：是，僅能局部改

### 5. `backend/app/modules/attendance/service.py`
- **分級**：P1
- **風險原因**：同時承載 legacy flow 與新版 close-flow orchestration，修改易影響舊新流程
- **是否接近或超過 size gate**：接近（282 行）
- **是否建議禁止直接修改**：是，僅能局部改

### 6. `backend/app/modules/attendance/api/breaks.py`
- **分級**：P1
- **風險原因**：邏輯集中、時區規則偏差、API 直接碰 ORM，屬明顯膨脹風險檔
- **是否接近或超過 size gate**：接近（284 行）
- **是否建議禁止直接修改**：是，僅能局部改

### 7. `backend/app/modules/attendance/api/reporting.py`
- **分級**：P1
- **風險原因**：為所有 reporting endpoint 集中入口，未來新增報表時容易膨脹
- **是否接近或超過 size gate**：中度接近（214 行）
- **是否建議禁止直接修改**：是，僅能局部改

## 5.3 P2（可安全改）

### 8. `backend/app/modules/attendance/reporting_service.py`
- **分級**：P2
- **風險原因**：純聚合層，無 DB access，爆炸半徑較小
- **是否接近或超過 size gate**：否
- **是否建議禁止直接修改**：否

### 9. `backend/app/modules/attendance/reporting_repo.py`
- **分級**：P2
- **風險原因**：責任單純，但需留意 tenant isolation 與全量拉取策略
- **是否接近或超過 size gate**：否
- **是否建議禁止直接修改**：否

### 10. `backend/app/modules/attendance/checkpoint_repo.py`
- **分級**：P2
- **風險原因**：責任清楚，單一用途
- **是否接近或超過 size gate**：否
- **是否建議禁止直接修改**：否

### 11. `backend/app/modules/router_wiring.py`
- **分級**：P2
- **風險原因**：檔案小，但關聯 demo router 掛載
- **是否接近或超過 size gate**：否
- **是否建議禁止直接修改**：否

### 12. `backend/app/modules/startup_wiring.py`
- **分級**：P2
- **風險原因**：檔案小，但影響 startup handler 註冊
- **是否接近或超過 size gate**：否
- **是否建議禁止直接修改**：否

---

# 6. 建議優先修正區（不提供修改內容）

以下為建議優先修正順序，僅列方向，不提供實作內容。

## 優先級 1
### 修正 `duration_minutes` canonical 語意與 SA2.1 v2.1 對齊
此項為最高優先。若不先處理，後續 reporting、工時計算、加班判定都會建立在錯誤語意之上。

## 優先級 2
### 修正 break 查詢的 Taipei 業務日邊界規則
應統一使用 SA2.1 v2.1 的時區規則，避免 break list、reporting、trace 在凌晨時段發生對齊錯誤。

## 優先級 3
### 收斂 `breaks.py` 的 API / service / repo 邊界
應減少 API handler 直接 query ORM 或直接 commit 的情況，避免 router 持續膨脹。

## 優先級 4
### 提前規劃 reporting 擴展策略
在新增更多報表前，應先確定 reporting 的擴展方式，避免 `api/reporting.py` 變成下一個 monolithic 熱點。

## 優先級 5
### 拆解 `repo.py` / `service.py` 中 legacy 與新流程混存問題
這不是最急迫的立即 bug，但它已明顯形成高風險中心檔，應納入中期治理計畫。

---

# 最終結論

Attendance 模組目前已完成第一階段拆模與 router 聚合，方向正確，且 endpoint 掛載基本完整；但仍未完全符合 SA2.1 對 canonical 工時計算、業務日邊界、與 API/service/repo 邊界的正式要求。

目前最大架構風險不是 router 漏掛，也不是 `reporting.py` 已經過胖，而是：

1. canonical 工時欄位語意尚未真正對齊 SA2.1 v2.1
2. 部分 API 邊界仍未收斂
3. 核心中心檔過於集中，存在 unsafe edit 風險

**結論判定：**
- **SA2.1 對齊狀態**：部分符合
- **reporting.py 是否必須立即拆分**：否
- **router 完整性**：完整
- **高風險核心檔**：已明確存在，應納入保護名單
