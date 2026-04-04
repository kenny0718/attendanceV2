# Schema Decomposition Analysis Report

**分析對象：** `backend/app/modules/tenants/schemas.py`  
**分析日期：** 2026-03-22  
**分析類型：** Read-only analysis — 無任何程式碼修改  
**分析人：** AI Audit Session  

---

## 1. Summary

`tenants/schemas.py` 目前已達到**應考慮拆分**的程度：

- 檔案已成長至 **8,752 bytes**，橫跨 5 個不同 WP 的 schema 群組
- 共有 **20 個 classes**，分屬 4 個不同的業務領域
- `api.py` 已達 **17,720 bytes**，兩個檔案都在「高風險區間」（大型 full rewrite 失敗概率高）
- `api.py` 中存在**4 處散落的 import block**（頂部 1 次 + mid-file 3 次），是典型的 append 式開發積累跡象
- 拆分的核心動機：**降低每個檔案的 full-rewrite 體積**，直接減少 0 bytes 事件的發生機率

---

## 2. Current Schema Inventory

### 完整 class 清單（依出現順序）

| # | Class | 所屬 WP | 業務領域 | 用途 |
|---|-------|---------|----------|------|
| 1 | `CreateCompanyRequest` | WP-S1-09A | Companies | POST /api/admin/companies 的 request body |
| 2 | `CompanyResponse` | WP-S1-09A | Companies | 單一公司的 response（含 model_config from_attributes） |
| 3 | `CompanyListResponse` | WP-S1-09A | Companies | GET /api/admin/companies 的 response body |
| 4 | `UpdateEntitlementRequest` | WP-11-04A | Entitlements | PATCH entitlements 的 request body |
| 5 | `ApplyPlanRequest` | WP-11-04A | Entitlements | 套用 plan 的 request body |
| 6 | `EntitlementResponse` | WP-11-04A | Entitlements | 單一 entitlement 的 response |
| 7 | `CompanyEntitlementsResponse` | WP-11-04A | Entitlements | 公司所有 entitlements 的 response |
| 8 | `ApplyPlanResponse` | WP-11-04A | Entitlements | 套用 plan 結果的 response |
| 9 | `OnboardingUserRequest` | WP-S1-09C | Onboarding | 初始 user 的 request 欄位 |
| 10 | `AdminOnboardingRequest` | WP-S1-09C | Onboarding | POST /onboarding 的整體 request（內嵌 CreateCompanyRequest） |
| 11 | `OnboardingCompanyResult` | WP-S1-09C | Onboarding | Onboarding response 中的 company 部分 |
| 12 | `OnboardingUserResult` | WP-S1-09C | Onboarding | Onboarding response 中的 user 部分 |
| 13 | `OnboardingMembershipResult` | WP-S1-09C | Onboarding | Onboarding response 中的 membership 部分 |
| 14 | `AdminOnboardingResponse` | WP-S1-09C | Onboarding | POST /onboarding 的整體 response（組合上述三個 Result） |
| 15 | `CompanyMemberResponse` | WP-S1-10B | Members | 單一 member（user + membership 合併）的 response |
| 16 | `CompanyMembersResponse` | WP-S1-10B | Members | GET /members 的 response body |
| 17 | `ToggleMembershipActiveRequest` | WP-S1-10C | Members | PATCH /members/{id}/active 的 request body |
| 18 | `ToggleMembershipActiveResponse` | WP-S1-10C | Members | PATCH /members/{id}/active 的 response body |
| 19 | `CreateMemberRequest` | WP-S1-10D | Members | POST /members 的 request body |
| 20 | `CreateMemberResponse` | WP-S1-10D | Members | POST /members 的 response body |

### 業務領域分佈

| 領域 | Classes 數 | 佔比 |
|------|-----------|------|
| Companies CRUD | 3 | 15% |
| Entitlements | 5 | 25% |
| Onboarding | 6 | 30% |
| Members（list / toggle / create） | 6 | 30% |

---

## 3. Recommended Split Boundaries

### 分析依據

**高耦合指標：**

- `AdminOnboardingRequest` 內嵌使用了 `CreateCompanyRequest`（跨領域依賴，Onboarding → Companies）
- `api.py` 從 `schemas` 進行了 4 次分散的 import，說明 schema 已超過單一 import block 的設計假設
- `OnboardingUserRequest` 與 `CreateMemberRequest` 有約 80% 欄位重疊（display_name、login_username、password、email、role_id），但語意不同，是隱性耦合

**跨領域依賴圖：**

```
Companies
    └── CreateCompanyRequest
              ↑
         被 AdminOnboardingRequest（Onboarding 領域）內嵌使用

Entitlements  ─── 無外部依賴（最獨立）
Members       ─── 無外部依賴（最獨立）
```

**拆分邊界原則（最小風險）：**

1. **Entitlements** 最獨立：無任何 class 被其他領域 import，可最先拆出
2. **Members** 完全獨立：不被其他領域 import，可單獨拆出
3. **Onboarding** 依賴 `CreateCompanyRequest`（Companies 領域），需在 companies 穩定後再拆
4. **Companies CRUD** 是被依賴的 base，應保留在主 `schemas.py` 或最後才動

---

## 4. Proposed File Structure

建議拆分後的目標結構（採平坦命名，不新增子目錄）：

```
backend/app/modules/tenants/
├── schemas.py               # 只保留 Companies CRUD（3 classes）— 作為 base
├── schemas_entitlements.py  # Entitlement 相關（5 classes）
├── schemas_onboarding.py    # Onboarding 相關（6 classes）
├── schemas_members.py       # Members 相關（6 classes）
├── __init__.py              # 維持現狀，僅 module docstring，不做 re-export
├── api.py
├── service.py
├── models.py
└── repo.py
```

**命名原則：**

- 採用 `schemas_<domain>.py` 而非 `schemas/<domain>.py`（避免新增 sub-package，不需要新的 `__init__.py`）
- 保持平坦結構（flat），降低 import path 複雜度
- `schemas.py` 本身繼續存在，不改名，避免破壞現有 import

---

## 5. Class-to-File Mapping

### `schemas.py`（保留，縮減至 Companies CRUD 核心）

| Class | 理由 |
|-------|------|
| `CreateCompanyRequest` | 被 `AdminOnboardingRequest` 內嵌使用，是被依賴的 base，不能移走 |
| `CompanyResponse` | 公司基本回應，跨 endpoint 使用（list 和 create 都用） |
| `CompanyListResponse` | 使用 `CompanyResponse`，緊密相關 |

---

### `schemas_entitlements.py`（新建）

| Class | 外部依賴 |
|-------|----------|
| `UpdateEntitlementRequest` | 無 |
| `ApplyPlanRequest` | 無 |
| `EntitlementResponse` | 無 |
| `CompanyEntitlementsResponse` | 無 |
| `ApplyPlanResponse` | 無 |

Import 需求：只需 `pydantic`、`typing`、`datetime`，完全無跨 schema 依賴，**最安全**。

---

### `schemas_onboarding.py`（新建）

| Class | 外部依賴 |
|-------|----------|
| `OnboardingUserRequest` | 無 |
| `AdminOnboardingRequest` | 需 `from app.modules.tenants.schemas import CreateCompanyRequest` |
| `OnboardingCompanyResult` | 無 |
| `OnboardingUserResult` | 無 |
| `OnboardingMembershipResult` | 無 |
| `AdminOnboardingResponse` | 組合同檔案內的三個 Result class |

Import 需求：需要跨檔案 import `CreateCompanyRequest`，**是本次拆分最需注意的跨領域依賴**。

---

### `schemas_members.py`（新建）

| Class | 外部依賴 |
|-------|----------|
| `CompanyMemberResponse` | 無 |
| `CompanyMembersResponse` | 同檔案內的 `CompanyMemberResponse` |
| `ToggleMembershipActiveRequest` | 無 |
| `ToggleMembershipActiveResponse` | 無 |
| `CreateMemberRequest` | 無 |
| `CreateMemberResponse` | 無 |

Import 需求：只需 `pydantic`、`typing`、`datetime`，完全無跨 schema 依賴，**最安全**。

---

## 6. Import / Export Strategy

### 建議方案：直接 import（最簡單，推薦）

拆分後，`api.py` 的 import 直接指向各個子檔案，並統一移到頂部成為一個完整的 import block：

```python
# api.py 頂部 — 統一 import block（拆分後）
from app.modules.tenants.schemas import (
    CreateCompanyRequest,
    CompanyResponse,
    CompanyListResponse,
)
from app.modules.tenants.schemas_entitlements import (
    UpdateEntitlementRequest,
    ApplyPlanRequest,
    EntitlementResponse,
    CompanyEntitlementsResponse,
    ApplyPlanResponse,
)
from app.modules.tenants.schemas_onboarding import (
    AdminOnboardingRequest,
    AdminOnboardingResponse,
    OnboardingCompanyResult,
    OnboardingUserResult,
    OnboardingMembershipResult,
)
from app.modules.tenants.schemas_members import (
    CompanyMemberResponse,
    CompanyMembersResponse,
    ToggleMembershipActiveRequest,
    ToggleMembershipActiveResponse,
    CreateMemberRequest,
    CreateMemberResponse,
)
```

**優點：**
- 路徑清晰，來源一目了然
- 不需要中介層或 `__init__.py` 修改
- 同時解決 `api.py` 4 處 mid-file import 分散的問題

### 不建議的方案

| 方案 | 不建議理由 |
|------|------------|
| 透過 `__init__.py` 統一 re-export（`from schemas import *`） | `*` import 會讓 IDE 的 type inference 失效；且 `__init__.py` 目前只有 docstring，改動它屬於額外風險 |
| 建立 `schemas/` sub-package | 需新增目錄、新增 `__init__.py`、更新所有 import path，改動範圍過大 |

---

## 7. Risk Assessment

### 拆分風險清單

| 風險 | 等級 | 說明 |
|------|------|------|
| `AdminOnboardingRequest` 依賴 `CreateCompanyRequest` | 中 | 拆分後需跨檔案 import，若路徑錯誤會 ImportError |
| `api.py` 有 3 處 