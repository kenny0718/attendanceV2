# WP-C1-06 Feature Gate Pre-Execution Audit

**建立日期：** 2026-03-17  
**執行者：** AI session (Cursor)  
**前置條件：** WP-C1-05 COMPLETE ✅  

---

## 1. Feature Gate 現有設計摘要

### 1.1 架構設計

系統已有完整的 Feature Gate 基礎架構，設計於 WP-11-04A：

| 元件 | 路徑 | 說明 |
|------|------|------|
| `FeatureKeys` | `app/core/features.py` | 集中定義所有 feature key 常數 |
| `FeatureService` | `app/core/feature_service.py` | DB 查詢、快取、`is_enabled()` / `require_enabled()` |
| `CompanyEntitlement` | `app/modules/tenants/models.py` | DB 模型：`(company_id, feature_key, enabled)` |
| Entitlement CRUD | `app/modules/tenants/api.py` | Super Admin 管理 feature flags 的 API |
| Feature Gate Demo | `app/modules/attendance/feature_gate_demo.py` | 示範端點（shift_overrides / shift_templates / split_shifts） |

### 1.2 現有 FeatureKeys（截至盤點時）

```python
class FeatureKeys:
    ATTENDANCE_SHIFT_TEMPLATES = "attendance.shift_templates"
    ATTENDANCE_SPLIT_SHIFT = "attendance.split_shift"
    ATTENDANCE_SHIFT_OVERRIDES = "attendance.shift_overrides"
```

**問題：** 只定義了 3 個 attendance 子功能的 key，缺乏核心業務模組層級的 gate。

### 1.3 Feature Gate 拒絕行為

已定義的模式（`feature_gate_demo.py`）：
- HTTP 403
- Body: `{"code": "FEATURE_DISABLED", "feature": "<key>", "message": "..."}`
- 透過 `FeatureDisabledError` 例外 + HTTPException 統一拋出

### 1.4 Plan 預設配置

```python
PLAN_DEFAULTS = {
    "Basic": {全部 False},
    "Pro":   {全部 True},
}
```

---

## 2. Phase A 掃描結果：各模組 Feature Gate 現況

### 2.1 已套用 Feature Gate 的端點

| 端點 | 模組 | Gate Key | 套用方式 |
|------|------|----------|----------|
| `POST /api/attendance/shift-overrides` | attendance (demo) | `attendance.shift_overrides` | `require_enabled()` |
| `GET /api/attendance/shift-templates` | attendance (demo) | `attendance.shift_templates` | `require_enabled()` |
| `POST /api/attendance/split-shifts` | attendance (demo) | `attendance.split_shift` | `require_enabled()` |

**注意：** 上述 3 個端點均為「示範端點」（stub 實作），位於 `feature_gate_demo.py`，**未在 `main.py` 中註冊為路由**，因此實際上並不可訪問。

### 2.2 缺少 Feature Gate 的模組（核心業務 API）

#### attendance/api.py（router_v1）

| 端點 | 是否有 Gate |
|------|------------|
| `POST /api/v1/attendance/punch-in` | ❌ 無 |
| `POST /api/v1/attendance/punch-out` | ❌ 無 |
| `GET /api/v1/attendance/current-status` | ❌ 無 |
| `GET /api/v1/attendance/history` | ❌ 無 |
| `POST /api/v1/attendance/break-out` | ❌ 無 |
| `POST /api/v1/attendance/break-in` | ❌ 無 |
| `GET /api/v1/attendance/break-punches` | ❌ 無 |
| `PATCH /api/v1/attendance/punch/{id}/note` | ❌ 無 |
| `GET /api/v1/attendance/sessions` | ❌ 無 |
| `GET /api/v1/attendance/reports/user-summary` | ❌ 無 |
| `GET /api/v1/attendance/reports/company-summary` | ❌ 無 |

**另外：** `attendance/api.py` 的 router（非 router_v1）使用舊的 `get_current_company_id` header 依賴，
但本票不改動 auth 遷移，只需在 router_v1 套用 gate。

#### leave/api.py

| 端點 | 是否有 Gate |
|------|------------|
| `POST /api/v1/leave/requests` | ❌ 無 |
| `GET /api/v1/leave/my-requests` | ❌ 無 |
| `GET /api/v1/leave/pending` | ❌ 無 |
| `POST /api/v1/leave/requests/{id}/approve` | ❌ 無 |
| `POST /api/v1/leave/requests/{id}/reject` | ❌ 無 |

#### audit/api.py

| 端點 | 是否有 Gate |
|------|------------|
| `GET /api/audit/logs` | ❌ 無（有 JWT auth，無 feature gate） |
| `GET /api/audit/export` | ❌ 無（有 admin RBAC，無 feature gate） |
| `GET /api/audit/retention` | ❌ 無 |
| `PUT /api/audit/retention` | ❌ 無（有 admin RBAC，無 feature gate） |
| `POST /api/audit/purge` | ❌ 無（有 admin RBAC，無 feature gate） |

#### notifications/api.py

| 端點 | 是否有 Gate |
|------|------------|
| `GET /api/notifications` | ❌ 無（有 JWT auth，無 feature gate） |

#### backup/api.py

| 端點 | 是否有 Gate |
|------|------------|
| `POST /api/backup/export` | ❌ 無（有 admin RBAC，無 feature gate） |
| `POST /api/backup/restore` | ❌ 無（有 admin RBAC，無 feature gate） |

---

## 3. Phase B 風險評估

### 3.1 已識別風險

| 風險 | 嚴重度 | 說明 |
|------|--------|------|
| 核心 API 完全無 gate | HIGH | punch-in/out 等核心功能無任何 feature 控制 |
| Feature Gate Demo 未掛載路由 | HIGH | demo router 未在 main.py 中 include，feature gate 形同虛設 |
| `FeatureKeys` 只有 attendance 子功能 | MEDIUM | 缺少模組層級的 key（leave / audit / notifications / backup） |
| gate 命名不一致 | LOW | 目前只有 attendance.* 類型，未來可能混亂 |

### 3.2 現有架構的優點

- `FeatureService` 設計完善（含快取、`require_enabled()`、`FeatureDisabledError`）
- 拒絕行為已有一致的 HTTP 403 + JSON schema 模式
- `CompanyEntitlement` DB 模型正確
- `PLAN_DEFAULTS` 提供 Plan 層級管理能力

---

## 4. 本票實作範圍決策

### 4.1 本票要做的事

#### A. 新增 FeatureKeys（`app/core/features.py`）

加入模組層級的 feature key：
- `attendance.core` — 控制整個 attendance 模組（punch-in/out/break/history/status/reporting）
- `leave.core` — 控制整個 leave 模組
- `audit.core` — 控制整個 audit 模組
- `notifications.core` — 控制整個 notifications 模組
- `backup.core` — 控制整個 backup 模組

並更新 `PLAN_DEFAULTS`：
- Basic：所有核心 gate 預設 **True**（讓現有 tenant 不被破壞）
- Pro：所有核心 gate **True**

> **設計決策：** 模組層級 gate 預設 True，不破壞現有功能。  
> 目的是提供「治理基礎設施」，未來可針對特定 tenant 關閉。

#### B. 套用 Feature Gate 到各模組 API

| 模組 | 修改檔案 | Gate Key |
|------|----------|----------|
| attendance (router_v1) | `attendance/api.py` | `attendance.core` |
| leave | `leave/api.py` | `leave.core` |
| audit | `audit/api.py` | `audit.core` |
| notifications | `notifications/api.py` | `notifications.core` |
| backup | `backup/api.py` | `backup.core` |

**套用層級：** 在每個 endpoint 函數內，取得 `company_id` 後立即呼叫 `feature_service.require_enabled()`。

**注意：** `leave/api.py` 目前使用舊的 `get_current_company_id` header dependency，  
本票只在函數內加入 gate check，**不遷移 auth 方式**（auth 遷移非本票範圍）。

**注意：** `attendance/api.py` 的舊 router（非 v1）使用舊 header，  
本票**不套用 gate 到舊 router**（舊 router 為相容性保留，範圍外）。

#### C. 確認 feature_gate_demo.py 路由已掛載

`feature_gate_demo.py` 的 `router` 目前**未在 `main.py` 中 include**。  