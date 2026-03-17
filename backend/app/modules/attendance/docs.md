# Attendance Module — 技術文件 v2

> **版本**：v2.1（WP-C1-07 router_v1 JWT Migration 更新）  
> **最後更新**：2026-03-17  
> **狀態**：Production-aligned

---

## 目錄

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Tenant & Auth Model](#3-tenant--auth-model)
4. [Feature Gate](#4-feature-gate)
5. [API 行為](#5-api-行為)
6. [Time & Timezone Contract](#6-time--timezone-contract)
7. [Data Flow](#7-data-flow)
8. [Integration Points](#8-integration-points)
9. [Testing](#9-testing)
10. [Deprecated (Do Not Use)](#10-deprecated-do-not-use)

---

## 1. Overview

Attendance Module 是考勤系統的核心業務模組，負責以下功能：

- **打卡管理**：員工上下班打卡（punch-in / punch-out）、外出打卡（break-out / break-in）記錄建立與查詢
- **Session 生命週期**：每次出勤構成一個 Session，從 punch-in 開始至 punch-out 結束，狀態為 `open` → `closed`
- **考勤政策執行**：透過 Policy Engine 在 punch-out 時評估是否遲到、早退、加班
- **GPS 地點驗證**：透過 Location Policy Service 驗證打卡位置是否在公司允許的地理圍欄內（後端 authoritative enforcement）
- **Feature Gate 控管**：依公司訂閱方案或功能開關決定可用功能（`core.features` 模組）
- **多租戶資料隔離**：所有資料操作均依認證 context 中的 `company_id` 進行租戶隔離
- **出勤報表**：提供 Session 清單、用戶摘要、公司摘要等 Reporting Endpoints
- **OUT Checkpoint**：記錄外出事件（不計算時間區間，僅記錄事件點）

本模組採用分層架構（API → Service → Repo），`company_id` 一律從認證 context 注入，不接受從 request body 傳入。

---

## 2. Architecture

```
+--------------------------------------------------------------+
|                        API Layer                             |
|                (api.py + feature_gate_demo.py)               |
|   FastAPI Router -- JWT/Header Auth -- Feature Gate Check    |
+---------------------+----------------------------------------+
                      |
+---------------------v----------------------------------------+
|                     Service Layer (service.py)               |
|   業務邏輯（舊版 approve 流程）-- Event Bus                  |
+----------+---------------------------------------------------+
           |
+----------v---------+  +------------------+  +----------------------+
|     Repo Layer     |  |  Policy Engine   |  |  Location Policy     |
|      (repo.py)     |  |(policy_engine.py)|  |  Service             |
| AttendanceSession  |  | 遲到/早退/加班   |  |(location_policy_     |
| AttendancePunch    |  | 評估（Pure Fn）  |  |  service.py)         |
| ReportingRepo      |  |                  |  | GPS 地理圍欄驗證     |
| OutCheckpointRepo  |  +------------------+  +----------------------+
+----------+---------+
           |
+----------v----------------------------------------------------------+
|                  Database Layer (models.py)                         |
|  AttendanceSession / AttendancePunch / AttendancePolicy             |
|  AttendanceOutCheckpoint / AllowedLocation / AttendanceRecord(舊)  |
|  全部 UTC datetime -- company_id tenant isolation                   |
+---------------------------------------------------------------------+
```

### 2.1 API Layer（`api.py`）

包含兩個 FastAPI Router：

| Router | Prefix | 說明 |
|--------|--------|------|
| `router` | `/api/attendance` | 舊版端點（向後相容） |
| `router_v1` | `/api/v1/attendance` | 新版主要業務端點 |

- 所有 `router_v1` 端點的 `company_id` 透過 `get_actor_with_company` dependency 注入（JWT Actor 模式，WP-C1-07）
- `company_id = actor.active_company_id`；`user_id = str(actor.user_id)`
- 舊版 `router`（`/api/attendance`）仍使用 `get_current_company_id`（向後相容）
- `company_id` 與 `user_id` **不從 request body 讀取**
- datetime 查詢參數若為 naive（無 tzinfo）則回傳 422
- Request / Response 序列化透過 `schemas.py` 中的 Pydantic model
- **`_require_attendance_feature(company_id, db)`（WP-C1-06）**：所有 `router_v1` endpoint 在執行業務邏輯前均呼叫此 helper，檢查 `attendance.core` Feature Gate；未啟用則回傳 403 `FEATURE_DISABLED`

### 2.2 Service Layer（`service.py`）

- `AttendanceService`：處理舊版 `mock_create_attendance` 和 `approve_attendance` 邏輯
- 透過 `get_attendance_repository(db)` 取得 Repo 實例
- 發出 `attendance.approved` 事件至 Event Bus
- **注意**：新版打卡邏輯（punch-in/out、break-out/in）直接在 `api.py` 的 endpoint 中協調，不經過 Service Layer

### 2.3 Repo Layer（`repo.py`）

| 類別 | Factory Function | 用途 |
|------|-----------------|------|
| `AttendanceSessionRepository` | `get_attendance_session_repository()` | Session CRUD、Punch 建立、Policy 查詢、Break Punch 查詢 |
| `AttendanceRepository` | `get_attendance_repository()` | 舊版 AttendanceRecord CRUD（向後相容） |
| `OutCheckpointRepository` | `get_out_checkpoint_repository()` | OUT Checkpoint CRUD |
| `ReportingRepository` | `get_reporting_repository()` | Reporting 查詢（Session 清單、User/Company 摘要） |

**Tenant Isolation 規則**：

- 所有查詢強制加入 `WHERE company_id = ?`
- `ReportingRepository` 的日期過濾僅使用 `punch_in_time`，禁止使用 `punch_out_time` 過濾
- 聚合邏輯在 Python 應用層執行（非 SQL 端）

### 2.4 Policy Engine（`policy_engine.py`）

- `AttendancePolicyEngine`：純函式評估引擎（no side effects，不直接操作 DB）
- 核心方法：
  - `evaluate(session, policy)` — 標準評估，在 punch-out 時呼叫
  - `evaluate_with_schedule(session, schedule, policy)` — 支援 WorkSchedule（standard / split_shift）
- 評估結果：`PolicyEvaluationResult`（遲到、早退、加班 + 各自分鐘數）
- `WorkSchedule` 支援三種模式：`standard`、`split_shift`、`flex_time`（`flex_time` 尚未實作）
- **時區**：遲到/早退判斷使用 `Asia/Taipei` 本地日期（`TZ_TAIPEI = ZoneInfo("Asia/Taipei")`），避免跨日錯誤
- 預設值（無政策時）：grace_period=0、overtime_threshold=480 分鐘、work_start=09:00、work_end=18:00

### 2.5 Location Policy Service（`location_policy_service.py`）

- `AttendanceLocationPolicyService`：GPS 地理圍欄驗證服務
- **後端 authoritative enforcement**（前端 precheck 僅為 UX 提示）
- 驗證邏輯：
  1. 取得公司啟用中的 `AllowedLocation`（`is_active=True`）
  2. 若無任何啟用地點 → 允許任何位置打卡
  3. 若有啟用地點 → 計算距離，命中任一 `radius_meters` 即允許
  4. 全部未命中 → `PolicyCheckResult(allowed=False)` → API 回 403
- 目前整合於 `break-out` endpoint（WP-11-13）
- 距離計算使用 `app.modules.attendance.gps_utils.calculate_distance`

### 2.6 Feature Gate（`core.features` + `core.feature_service`）

- Feature Key 集中定義於 `app.core.features.FeatureKeys`
- Gate 狀態讀取自 `CompanyEntitlement` 資料表（per-company 粒度）
- `FeatureService.require_enabled(company_id, feature_key)` 執行 gate 檢查，失敗拋出 `FeatureDisabledError`
- API 層捕捉 `FeatureDisabledError` 並回傳 403 `FEATURE_DISABLED`
- `router_v1` 所有端點透過 `_require_attendance_feature()` 統一執行 `attendance.core` gate 檢查（WP-C1-06）
- `feature_gate_demo.py` 示範子功能 gate（shift_overrides、shift_templates、split_shift）整合
- 驗證順序：Scope 檢查 → Tenant Isolation → Feature Gate

---

## 3. Tenant & Auth Model

### 3.1 目前認證機制

系統現行使用 Header-based context 注入（JWT Actor migration 進行中）：

| Dependency | 來源 | 說明 |
|-----------|------|------|
| `get_current_company_id()` | `app.core.tenant_context` | 取得當前 company_id |
| `get_current_user_id()` | `app.core.tenant_context` | 取得當前 user_id |
| `get_actor_with_company()` | `app.core.dependencies` | JWT Actor 物件（feature_gate_demo.py 使用） |

`Actor` 物件（JWT path）包含 `actor.active_company_id` 與 `actor.user_id`。

### 3.2 `company_id` 注入規則（強制）

| 規則 | 說明 |
|------|------|
| ✅ 從認證 context 取得 | `company_id` 必須由後端 dependency injection 注入 |
| ✅ `router_v1` 使用 JWT Actor | `actor.active_company_id`（WP-C1-07 完成遷移）|
| ❌ 禁止從 request body 傳入 | 所有 Request Schema 均不含 `company_id` 欄位 |
| ❌ 禁止客戶端自行指定租戶 | 不信任任何來自客戶端的 tenant 聲稱 |
| ❌ 禁止使用 X-Company-ID header（router_v1）| router_v1 所有端點已不依賴此 header |

所有 Pydantic Request Schema 均不含 `company_id` 欄位。Schema docstring 標注：

```
Note: company_id and user_id come from JWT/tenant context, not from request body
```

### 3.3 多租戶資料隔離

- Repo Layer 所有查詢強制加入 `WHERE company_id = :company_id`
- `AttendanceSession`、`AttendancePunch`、`AttendanceOutCheckpoint` 均有 `company_id` 欄位（FK → `tenants.id` + CASCADE DELETE）
- DB Partial Unique Index：`uq_sessions_company_user_open` — 確保每個用戶同時只能有一個 `open` session
- `AttendancePunch.company_id` 為 denormalized 欄位，支援高效 tenant-scoped 查詢

---

## 4. Feature Gate

Attendance Module 透過 `app.core.features.FeatureKeys` 與 `app.core.feature_service.FeatureService` 控制功能開關。

### 4.1 目前定義的 Feature Keys

| Feature Key | 常數名稱 | 說明 | Basic Plan | Pro Plan |
|------------|---------|------|-----------|----------|
| `attendance.core` | `ATTENDANCE_CORE` | 考勤模組核心功能開關（WP-C1-06） | True | True |
| `attendance.shift_templates` | `ATTENDANCE_SHIFT_TEMPLATES` | 班表範本功能 | False | True |
| `attendance.split_shift` | `ATTENDANCE_SPLIT_SHIFT` | 分段班功能 | False | True |
| `attendance.shift_overrides` | `ATTENDANCE_SHIFT_OVERRIDES` | 班表覆寫功能 | False | True |

其他模組層級 Gate（WP-C1-06 新增）：`leave.core`、`audit.core`、`notifications.core`、`backup.core`

### 4.2 `attendance.core` Gate 執行機制（WP-C1-06）

`api.py` 中定義的 `_require_attendance_feature()` helper 在所有 `router_v1` endpoint 執行業務邏輯前統一呼叫：

```python
def _require_attendance_feature(company_id: str, db) -> None:
    """attendance.core Feature Gate - raises 403 if disabled"""
    try:
        feature_service = get_feature_service(db)
        feature_service.require_enabled(company_id, FeatureKeys.ATTENDANCE_CORE)
    except FeatureDisabledError as e:
        raise HTTPException(status_code=403, detail={"code": "FEATURE_DISABLED", ...})
```

### 4.3 Feature Gate 使用流程

```
HTTP Request
    |
    v
認證 Context 注入（company_id, user_id）
    |
    v
_require_attendance_feature(company_id, db)  [router_v1 所有端點]
    |
    +-- attendance.core disabled  ->  403 FEATURE_DISABLED
    |
    v
業務邏輯執行
```

### 4.4 子功能 Gate 使用範例（依 `feature_gate_demo.py`）

```python
feature_service.require_enabled(company_id, FeatureKeys.ATTENDANCE_SHIFT_OVERRIDES)
```

---

## 5. API 行為

> 以下 endpoint 均依 `api.py` 與 `feature_gate_demo.py` 實際定義列出。

### 5.1 舊版端點（`/api/attendance`）

#### `POST /api/attendance/mock-create`

- **說明**：建立 AttendanceRecord（向後相容）
- **行為**：從 context 取得 company_id，呼叫 AttendanceService.mock_create_attendance()
- **Response**：`{ "attendance_record_id": "<uuid>" }`

#### `POST /api/attendance/{attendance_record_id}/approve`

- **說明**：核准考勤記錄，發出 `attendance.approved` 事件
- **Request Body**：`{ "employee_id": "...", "approved_by": "...（選填）" }`
- **錯誤**：404 若記錄不屬於該公司

### 5.2 新版 v1 端點（`/api/v1/attendance`）

> **注意**：以下所有端點在業務邏輯前均先呼叫 `_require_attendance_feature(company_id, db)` 檢查 `attendance.core` gate（WP-C1-06）。

| Endpoint | Method | Feature Gate | 說明 |
|----------|--------|-------------|------|
| `/punch-in` | POST | `attendance.core` | 上班打卡，建立 Session(open) + Punch(in)，409 若已有 open session |
| `/punch-out` | POST | `attendance.core` | 下班打卡，Policy Engine 評估，關閉 Session |
| `/current-status` | GET | `attendance.core` | 查詢當前出勤狀態，含 is_on_break |
| `/history` | GET | `attendance.core` | 歷史出勤記錄（分頁，limit 1-100） |
| `/break-out` | POST | `attendance.core` | 外出打卡，Location Policy 驗證（WP-11-13） |
| `/break-in` | POST | `attendance.core` | 返回打卡 |
| `/break-punches` | GET | `attendance.core` | 今日外出/返回記錄 |
| `/punch/{id}/note` | PATCH | `attendance.core` | 更新打卡備註 |
| `/sessions` | GET | `attendance.core` | Sessions 報表（分頁，僅 punch_in_time 過濾） |
| `/reports/user-summary` | GET | `attendance.core` | 用戶出勤摘要統計 |
| `/reports/company-summary` | GET | `attendance.core` | 全公司出勤摘要統計 |

### 5.3 Feature Gate Demo 端點（`feature_gate_demo.py`）

| Endpoint | Method | Feature Key | 說明 |
|----------|--------|-------------|------|
| `/api/attendance/shift-overrides` | POST | `attendance.shift_overrides` | 建立班表覆寫（stub） |
| `/api/attendance/shift-templates` | GET | `attendance.shift_templates` | 列出班表範本（stub） |
| `/api/attendance/split-shifts` | POST | `attendance.split_shift` | 建立分段班（stub） |

---

## 6. Time & Timezone Contract

- **所有 datetime 儲存為 UTC**（PostgreSQL TIMESTAMPTZ）
- 禁止使用 `datetime.utcnow()`；正確寫法：`datetime.now(timezone.utc)`
- API 接受的 datetime 必須為 timezone-aware；naive datetime → 422
- Policy Engine 遲到/早退判斷使用 `Asia/Taipei` 本地日期（`ZoneInfo("Asia/Taipei")`）
- Reporting 日期過濾：`start_date`/`end_date` 在 API 層正規化為 UTC 後傳入 Repo
- Reporting 日期過濾**僅使用 `punch_in_time`**，禁止 `punch_out_time` 過濾

| 情境 | 格式 | 範例 |
|------|------|------|
| DB 儲存 | UTC TIMESTAMPTZ | `2026-03-17 00:00:00+00` |
| API 回應 | ISO 8601 UTC | `2026-03-17T00:00:00Z` |
| API 輸入 | ISO 8601 with offset | `2026-03-17T08:00:00+08:00` |
| Policy 計算 | Asia/Taipei 本地時間 | `2026-03-17T08:00:00+08:00` |

---

## 7. Data Flow

### 7.1 打卡上班（Punch In）

```
Client POST /api/v1/attendance/punch-in
    v
[API] get_current_company_id() + get_current_user_id()
    v
[API] _require_attendance_feature()  -- disabled --> 403
    v
[API] get_open_session() -- exists --> 409 ALREADY_OPEN_SESSION
    v
[API] create_session(status=open) + create_punch(type=in)
    v
[API] Response: PunchInResponse (201)
```

### 7.2 打卡下班（Punch Out + Policy）

```
Client POST /api/v1/attendance/punch-out
    v
[API] _require_attendance_feature()  -- disabled --> 403
    v
[API] get_open_session() -- none --> 404
    v
[API] create_punch(type=out) + calculate duration_minutes
    v
[API] get_user_policy() --> AttendancePolicy
    v
[PolicyEngine] evaluate(session, policy) --> is_late/is_early_leave/is_overtime
    v
[API] close_session(status=closed) --> PunchOutResponse (含 policy_evaluation)
```

### 7.3 外出打卡（Break Out + Location Policy）

```
Client POST /api/v1/attendance/break-out
    v
[API] _require_attendance_feature()  -- disabled --> 403
    v
[LocationPolicyService] check_location_policy()
    |-- no locations --> allowed
    |-- within radius --> allowed + matched_location_id
    +-- outside all  --> 403 LOCATION_POLICY_VIOLATION
    v
[API] create_punch(type=break_start) --> BreakOutResponse (201)
```

### 7.4 核准流程（舊版）

```
Client POST /api/attendance/{id}/approve
    v
[Service] approve_attendance_record(company_id, record_id)
    v
[EventBus] emit("attendance.approved", payload)
    v
[API] Response: { ok: true, payload: {...} }
```

---

## 8. Integration Points

| 系統 | 狀態 | 說明 |
|------|------|------|
| Event Bus | 已整合 | `attendance.approved` 事件於 approve endpoint 發出 |
| Location Policy | 已整合 | AllowedLocation + AttendanceLocationPolicyService 整合於 break-out（WP-11-13）|
| Leave System | 未整合 | `leave.core` gate 已定義，無直接 API 呼叫 |
| Notifications | 未整合 | `notifications.core` gate 已定義 |
| Audit | 未整合 | `audit.core` gate 已定義 |

---

## 9. Testing

測試位於 `backend/app/modules/attendance/tests/`

| 測試檔案 | 測試範疇 |
|---------|---------| 
| `test_api.py` | 舊版 API（mock-create、approve）|
| `test_punch_api.py` | 新版打卡 API（punch-in/out、status、history）|
| `test_break_out_enforcement.py` | break-out Location Policy 驗證 |
| `test_business_invariant.py` | 每用戶只能有一個 open session |
| `test_feature_gate.py` | Feature Gate 開關測試（6 tests）|
| `test_location_policy.py` | Location Policy Service 單元測試 |
| `test_migration.py` | DB migration 驗證 |
| `test_model_constraints.py` | DB Model 約束測試 |
| `test_out_checkpoint.py` | OUT Checkpoint（使用 `override_all_auth_dependencies`）|
| `test_phase4.py` | 舊版 AttendanceRecord DB 寫入 |
| `test_policy_engine.py` | Policy Engine 單元測試（遲到/早退/加班/WorkSchedule）|
| `test_regression.py` | 回歸測試（使用 `override_all_auth_dependencies`）|
| `test_reporting_sessions.py` | Sessions 報表 endpoint |
| `test_reporting_user_summary.py` | User Summary 報表 endpoint |
| `test_reporting_company_summary.py` | Company Summary 報表 endpoint |
| `test_tenant_isolation.py` | Tenant Isolation P0 |
| `test_tenant_isolation_wp_c1_05.py` | WP-C1-05 Isolation 補充測試 |
| `test_tenant_validation.py` | Tenant 輸入驗證 |
| `conftest.py` | 測試 fixtures |

### 9.1 測試輔助工具（WP-C1-04）

`app.tests.utils.auth` 提供：
- `override_actor_dependency(actor)`：覆寫 JWT Actor dependency（WP-C1-07 後為 router_v1 主要測試工具）
- `override_all_auth_dependencies(actor)`：同時覆寫 JWT Actor + Header-based auth（適用舊版 `router` 端點向後相容測試）

**WP-C1-07 後建議：** router_v1 測試應使用 `override_actor_dependency`，不再需要 `override_all_auth_dependencies`。

### 9.2 執行測試

```bash
pytest backend/app/modules/attendance/tests/ -v
```

### 9.3 重要驗收條件

- Tenant Isolation：A 公司無法存取 B 公司資料
- Business Invariant：每用戶同時只能有一個 open session
- Feature Gate：`attendance.core` 未啟用時所有 v1 端點回傳 403 FEATURE_DISABLED
- Location Policy：不在允許地點 → 403 LOCATION_POLICY_VIOLATION
- Reporting：日期過濾僅使用 punch_in_time；naive datetime → 422

---

## 10. Deprecated (Do Not Use)

> **重要警告**：以下設計已正式淘汰，任何新程式碼禁止參考或復用。

### 10.1 SA_MODULE_SPEC v1.7 — Header-based Tenant Model（已淘汰）

- **說明**：SA_MODULE_SPEC v1.7 中描述的以 X-Company-ID HTTP header 作為主要 tenant 識別機制已廢棄
- **WP-C1-07 完成**：`router_v1` 所有 11 個 endpoint 已完成 JWT Actor 遷移，不再依賴 X-Company-ID
- **禁止**：禁止在新 endpoint 中使用 X-Company-ID 作為主要 tenant 機制
- **保留**：舊版 `router`（`/api/attendance/mock-create`、`/{id}/approve`）仍使用 Header-based auth（向後相容，不影響 router_v1）

### 10.2 Phase 1 Mock API 架構（已淘汰）

- **說明**：Phase 1 的 Mock 實作（無 DB 操作、in-memory 狀態）已全面替換
- **禁止**：禁止新增 mock-only endpoint；禁止在文件中描述 Phase 1 mock 架構

### 10.3 `AttendanceRecord` Model（已淘汰，保留向後相容）

- **說明**：舊版 `AttendanceRecord` 已被 `AttendanceSession` + `AttendancePunch` 取代
- **禁止**：禁止在新功能中使用 `AttendanceRecord`，新功能應使用 `AttendanceSession`

---

*本文件依實際程式碼（api.py、service.py、repo.py、schemas.py、models.py、policy_engine.py、location_policy_service.py、feature_gate_demo.py）產生，所有描述均有對應的程式碼實作。*
