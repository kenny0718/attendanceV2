# API Decomposition Analysis Report

**分析對象：** `backend/app/modules/tenants/api.py`  
**分析日期：** 2026-03-22  
**分析類型：** Read-only analysis — 無任何程式碼修改  
**分析人：** AI Audit Session  

---

## 1. Summary

`tenants/api.py` 目前已達到**應立即列入拆分計畫**的程度：

- 檔案已成長至 **525 行、18K bytes**，是整個 backend 中**單一最大的 API 檔案**
- 承載 **5 個業務領域、9 個 endpoints**，職責嚴重過載
- 存在 **4 處分散的 import block**（頂部 1 次 + mid-file 3 次），是 append 式開發積累的直接結構跡象
- `create_company_member` endpoint（WP-S1-10D）內含 **inline import**（`from app.modules.auth.models import Role as _Role`），是業務邏輯直接依賴底層 model 的耦合跡象
- 目前的 0 bytes 問題（已發生 3 次）的根本結構原因之一，就是此檔案過大導致 full rewrite 失敗機率高

**結論：** 拆分不只是程式碼品質問題，也是**檔案完整性風險的直接緩解措施**。

---

## 2. Current Endpoint Inventory

### 完整 endpoint 清單（依行號順序）

| # | Method | Path | Handler | 行號 | 所屬 WP | 業務領域 |
|---|--------|------|---------|------|---------|----------|
| 1 | GET | `/api/admin/companies` | `list_companies` | 35-54 | WP-S1-09A | Companies |
| 2 | POST | `/api/admin/companies` | `create_company` | 57-87 | WP-S1-09A | Companies |
| 3 | GET | `/api/admin/companies/{id}/entitlements` | `get_company_entitlements` | 92-114 | WP-11-04A | Entitlements |
| 4 | PATCH | `/api/admin/companies/{id}/entitlements` | `update_company_entitlement` | 117-147 | WP-11-04A | Entitlements |
| 5 | POST | `/api/admin/companies/{id}/entitlements/apply-plan` | `apply_plan_defaults` | 150-175 | WP-11-04A | Entitlements |
| 6 | POST | `/api/admin/companies/onboarding` | `admin_onboard` | 191-289 | WP-S1-09C | Onboarding |
| 7 | GET | `/api/admin/companies/{id}/members` | `list_company_members` | 298-356 | WP-S1-10B | Members |
| 8 | PATCH | `/api/admin/companies/{id}/members/{mid}/active` | `toggle_membership_active` | 368-434 | WP-S1-10C | Members |
| 9 | POST | `/api/admin/companies/{id}/members` | `create_company_member` | 445-525 | WP-S1-10D | Members |

### 業務領域分佈

| 領域 | Endpoints 數 | 行數（約） | 佔比 |
|------|-------------|-----------|------|
| Companies CRUD | 2 | ~55 行 | 10% |
| Entitlements | 3 | ~86 行 | 16% |
| Onboarding | 1 | ~100 行 | 19% |
| Members（list / toggle / create）| 3 | ~230 行 | 44% |
| Router 定義 + 共用 import | — | ~55 行 | 11% |

### Import Block 分佈（高耦合指標）

| 位置 | 行號 | 說明 |
|------|------|------|
| 頂部 import block | 7-28 | 核心依賴 + Companies + Entitlements schemas |
| Mid-file #1 | 180-188 | Onboarding schemas + service + IntegrityError |
| Mid-file #2 | 294-295 | Members schemas + auth.models |
| Mid-file #3 | 361-365 | Toggle schemas + uuid |
| Mid-file #4 | 440-442 | Create member schemas + auth.repo + IntegrityError alias |

**4 處 mid-file import 是此檔案「append 式成長」的最直接結構證據。**

---

## 3. Recommended Split Boundaries

### 分析依據

**高耦合指標：**

1. **Members 領域（230 行）** 是最大單一業務群，且跨 3 個不同 WP（10B / 10C / 10D）累積，最需要獨立
2. **Onboarding endpoint** 單一 endpoint 佔 100 行（含 IntegrityError 處理），邏輯最複雜，應獨立
3. **Entitlements 領域** 有自己的 service（`CompanyEntitlementService`），天然邊界清晰
4. **Companies CRUD** 是基礎，且被 router prefix 所共享，應保留在主檔案
5. **Router 只有一個**（`prefix="/api/admin/companies"`），所有子檔案都共用這個前綴——這是拆分時的核心約束

**跨檔案依賴分析：**

```
所有 endpoint 共用：
  - router（prefix="/api/admin/companies"）
  - get_current_actor
  - get_db
  - Actor / ScopeError

Members 領域額外依賴：
  - get_tenant_service（company existence check）
  - MembershipModel / UserModel（直接 DB query）
  - AuthRepository（create member）
  - Role model（inline import）

Onboarding 額外依賴：
  - get_onboarding_service
  - IntegrityError

Entitlements 額外依賴：
  - get_entitlement_service
  - CompanyEntitlementService
```

**拆分邊界原則（最小風險）：**

1. **單一 router 物件必須維持**：`main.py` 的 `app.include_router(tenants_router)` 只接受一個 router，拆分後子檔案的 endpoint 必須掛回同一個 router
2. **Members 最優先拆**：體積最大，且測試檔（`test_members_api.py` 18.7K）已獨立存在
3. **Onboarding 次之**：邏輯最複雜，獨立後主檔案大幅縮減
4. **Entitlements 第三**：有明確 service 邊界，但 schema / service 改動風險低
5. **Companies CRUD 保留在主檔案**：是 router 定義的宿主，維持穩定

---

## 4. Proposed File Structure

建議拆分後的目標結構：

```
backend/app/modules/tenants/
├── api.py                    # 保留：router 定義 + Companies CRUD（2 endpoints）
├── api_entitlements.py       # 新建：Entitlements（3 endpoints）
├── api_onboarding.py         # 新建：Onboarding（1 endpoint）
├── api_members.py            # 新建：Members list + toggle + create（3 endpoints）
├── schemas.py                # 現有（待分析後拆分）
├── schemas_entitlements.py   # 現有分析已規劃
├── schemas_onboarding.py     # 現有分析已規劃
├── schemas_members.py        # 現有分析已規劃
├── service.py
├── models.py
├── repo.py
├── __init__.py
└── tests/
    ├── conftest.py
    ├── test_companies_api.py
    ├── test_entitlements_api.py
    ├── test_members_api.py
    ├── test_onboarding_api.py
    ├── test_toggle_membership.py
    └── ...
```

**命名原則：**
- 採用 `api_<domain>.py` 平坦命名，不新增子目錄
- `api.py` 本身繼續存在，不改名，`main.py` 的 import 不變
- 子檔案不對外 export router，只提供 `register_routes(router)` 函式供 `api.py` 呼叫

---

## 5. Endpoint-to-File Mapping

### `api.py`（保留，縮減至 Companies CRUD + router 定義）

| Endpoint | Method | Path |
|----------|--------|------|
| `list_companies` | GET | `/api/admin/companies` |
| `create_company` | POST | `/api/admin/companies` |

保留理由：
- Router 物件（`prefix="/api/admin/companies"`）在此定義
- Companies CRUD 是基礎功能，維持在入口檔穩定
- 拆分後預計縮減至約 80-100 行

---

### `api_entitlements.py`（新建）

| Endpoint | Method | Path |
|----------|--------|------|
| `get_company_entitlements` | GET | `/{company_id}/entitlements` |
| `update_company_entitlement` | PATCH | `/{company_id}/entitlements` |
| `apply_plan_defaults` | POST | `/{company_id}/entitlements/apply-plan` |

預計行數：~100 行（含 import + 3 endpoints）

---

### `api_onboarding.py`（新建）

| Endpoint | Method | Path |
|----------|--------|------|
| `admin_onboard` | POST | `/onboarding` |

預計行數：~120 行（含 import + 1 endpoint，邏輯最複雜）

---

### `api_members.py`（新建）

| Endpoint | Method | Path |
|----------|--------|------|
| `list_company_members` | GET | `/{company_id}/members` |
| `toggle_membership_active` | PATCH | `/{company_id}/members/{membership_id}/active` |
| `create_company_member` | POST | `/{company_id}/members` |

預計行數：~230 行（含 import + 3 endpoints）

---

## 6. Router Integration Strategy

### 核心約束

`main.py` 目前只 import 一個 router：

```python
# main.py（現有，不可改動）
from app.modules.tenants.api import router as tenants_router
app.include_router(tenants_router)
```

**這個 import 和 include_router 呼叫不能改變。**

### 建議整合方案：`register_routes` 函式模式

子檔案不自己建立 router，而是定義一個接受 router 參數的函式：

```python
# api_members.py（示意，非實際程式碼）
def register_routes(router):
    @router.get("/{company_id}/members", ...)
    def list_company_members(...):
        ...

    @router.patch("/{company_id}/members/{membership_id}/active", ...)
    def toggle_membership_active(...):
        ...

    