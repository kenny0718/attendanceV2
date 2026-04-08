# WP-11-04A 架構審查文件（第二部分）

## 7️⃣ Actor 來源邏輯

### ⚠️ 重要：get_current_actor() 尚未實作

**狀態：** 🔴 **NOT IMPLEMENTED**

**位置：** 
- `backend/app/modules/tenants/api.py`
- `backend/app/modules/customer_service/api.py`

**目前實作：**
```python
def get_current_actor() -> Actor:
    """取得當前操作者（placeholder）"""
    raise NotImplementedError("get_current_actor needs to be implemented")
```

### 需要實作的邏輯

```python
def get_current_actor(
    request: Request,
    db: Session = Depends(get_db)
) -> Actor:
    """
    從 JWT/Session 取得當前操作者資訊
    
    實作步驟：
    1. 從 request.state 或 JWT token 取得 user_id 和 role
    2. 根據 role 查詢對應的資料：
       - customer_service: 查詢 support_company_assignments
       - company_user: 查詢 user_company_memberships
    3. 建立並回傳 Actor 物件
    """
    # TODO: 實作邏輯
    # 1. 取得 user_id 和 role
    user_id = request.state.user_id  # 或從 JWT 解析
    role_str = request.state.user_role
    role = UserRole(role_str)
    
    # 2. 查詢 memberships/assignments
    if role == UserRole.CUSTOMER_SERVICE:
        assignments = db.query(SupportCompanyAssignment).filter(
            SupportCompanyAssignment.user_id == user_id
        ).all()
        support_company_assignments = {a.company_id for a in assignments}
    else:
        support_company_assignments = set()
    
    if role == UserRole.COMPANY_USER:
        memberships = db.query(Membership).filter(
            Membership.user_id == user_id
        ).all()
        company_memberships = {m.company_id for m in memberships}
    else:
        company_memberships = set()
    
    # 3. 建立 Actor
    return Actor(
        user_id=user_id,
        role=role,
        company_memberships=company_memberships,
        support_company_assignments=support_company_assignments
    )
```

### 依賴項目

**需要整合的模組：**
1. JWT 驗證機制（`app/core/security/jwt.py`）
2. Tenant Context（`app/core/tenant_context.py`）
3. Auth 模組（`app/modules/auth/`）

**需要的資料：**
- `user_id` (UUID)
- `role` (super_admin / customer_service / company_user)
- `company_memberships` (Set[str]) - 從 user_company_memberships 查詢
- `support_company_assignments` (Set[str]) - 從 support_company_assignments 查詢

---

## 8️⃣ 測試案例

### ⚠️ 重要：測試檔案尚未建立

**狀態：** 🔴 **NOT IMPLEMENTED**

**已建立的測試框架：**
- `backend/app/core/tests/__init__.py` ✅
- `backend/app/modules/tenants/tests/__init__.py` ✅
- `backend/app/modules/customer_service/tests/__init__.py` ✅

**需要建立的測試檔案：**

### 1. Core 模組測試

#### test_features.py
```python
# 需要建立的測試案例：

class TestFeatureKeys:
    def test_all_keys_returns_set()
    def test_is_valid_with_valid_key()
    def test_is_valid_with_invalid_key()
    def test_validate_raises_on_invalid_key()
    def test_validate_passes_on_valid_key()

class TestPlanDefaults:
    def test_basic_plan_defaults()
    def test_pro_plan_defaults()

class TestFeatureService:
    def test_is_enabled_returns_false_when_not_set()
    def test_is_enabled_returns_true_when_enabled()
    def test_is_enabled_returns_false_when_disabled()
    def test_is_enabled_validates_feature_key()
    def test_require_enabled_passes_when_enabled()
    def test_require_enabled_raises_when_disabled()
    def test_cache_works()
    def test_clear_cache_works()
    def test_get_all_features()
```

**關鍵 Assert：**
- `assert FeatureKeys.is_valid("attendance.shift_templates") is True`
- `assert feature_service.is_enabled(company_id, feature_key) is True`
- `with pytest.raises(FeatureDisabledError)`
- `assert exc_info.value.feature_key == expected_key`

#### test_scope.py
```python
# 需要建立的測試案例：

class TestActor:
    def test_super_admin_role()
    def test_customer_service_role()
    def test_company_user_role()

class TestScopeChecker:
    def test_super_admin_can_access_any_company()
    def test_customer_service_can_access_assigned_company()
    def test_customer_service_cannot_access_unassigned_company()
    def test_company_user_can_access_member_company()
    def test_company_user_cannot_access_non_member_company()
    def test_get_accessible_companies_for_super_admin()
    def test_get_accessible_companies_for_customer_service()
    def test_get_accessible_companies_for_company_user()

class TestMultiCompanyScenarios:
    def test_customer_service_with_multiple_assignments()
    # 測試：客服 A 可看 1,2,3；客服 B 可看 5,6,9
```

**關鍵 Assert：**
- `assert actor.is_super_admin() is True`
- `with pytest.raises(ScopeError)`
- `assert "not assigned to company" in str(exc_info.value)`
- `assert companies == {1, 2, 3}`

### 2. Tenants 模組測試

#### test_entitlements_api.py
```python
# 需要建立的測試案例：

class TestEntitlementsAPI:
    def test_super_admin_can_list_any_company_entitlements()
    def test_customer_service_can_list_assigned_company_entitlements()
    def test_customer_service_cannot_list_unassigned_company_entitlements()
    def test_company_user_can_list_own_company_entitlements()
    def test_list_entitlements_includes_all_feature_keys()
    def test_super_admin_can_update_entitlement()
    def test_customer_service_cannot_update_entitlement()
    def test_company_user_cannot_update_entitlement()
    def test_update_entitlement_validates_feature_key()
    def test_super_admin_can_apply_plan_defaults()
    def test_customer_service_cannot_apply_plan_defaults()
    def test_apply_plan_defaults_validates_plan_code()
    def test_update_entitlement_clears_cache()
```

**關鍵 Assert：**
- `assert result["company_id"] == company_id`
- `assert result["entitlements"][feature_key] is True`
- `with pytest.raises(ScopeError)`
- `assert "Only super_admin" in str(exc_info.value)`
- `assert result["updated_count"] == 3`

### 3. Customer Service 模組測試

#### test_support_company_scope.py
```python
# 需要建立的測試案例：

class TestCustomerServiceScope:
    def test_customer_service_can_get_assigned_companies()
    def test_non_customer_service_cannot_get_assigned_companies()
    def test_customer_service_can_get_assigned_company_info()
    def test_customer_service_cannot_get_unassigned_company_info()
    def test_customer_service_can_list_assigned_company_users()
    def test_customer_service_cannot_list_unassigned_company_users()

class TestMultipleCustomerServiceScenarios:
    def test_customer_service_a_can_access_assigned_companies()
    def test_customer_service_a_cannot_access_unassigned_companies()
    def test_customer_service_b_can_access_assigned_companies()
    def test_customer_service_b_cannot_access_unassigned_companies()

class TestSupportAssignmentAPI:
    def test_super_admin_can_assign_company()
    def test_customer_service_cannot_assign_company()
    def test_super_admin_can_unassign_company()
    def test_customer_service_cannot_unassign_company()
```

**關鍵 Assert：**
- `assert set(companies) == {1, 2, 3}`
- `with pytest.raises(ScopeError)`
- `assert "not assigned to company" in str(exc_info.value)`
- `assert result["status"] == "unassigned"`

### 4. Attendance 模組測試

#### test_feature_gate.py
```python
# 需要建立的測試案例：

class TestAttendanceFeatureGate:
    def test_create_shift_override_requires_feature_enabled()
    def test_create_shift_override_fails_when_feature_disabled()
    def test_list_shift_templates_requires_feature_enabled()
    def test_list_shift_templates_fails_when_feature_disabled()
    def test_create_split_shift_requires_feature_enabled()
    def test_create_split_shift_fails_when_feature_disabled()

class TestValidationOrder:
    def test_scope_checked_before_feature_gate()
    def test_feature_gate_checked_after_scope()

class TestTenantIsolation:
    def test_user_cannot_access_other_company_data()
    def test_customer_service_respects_tenant_isolation()
    def test_super_admin_can_access_all_companies()

class TestFeatureGateErrorFormat:
    def test_feature_disabled_error_contains_feature_key()
```

**關鍵 Assert：**
- `assert result["company_id"] == company_id`
- `with pytest.raises(FeatureDisabledError)`
- `assert exc_info.value.feature_key == FeatureKeys.ATTENDANCE_SHIFT_OVERRIDES`
- `assert "not enabled" in str(exc_info.value)`

---

## 9️⃣ Route 定義與 Middleware

### Tenants API Routes

**檔案：** `backend/app/modules/tenants/api.py`

```python
router = APIRouter(prefix="/api/admin/companies", tags=["admin", "entitlements"])

@router.get("/{company_id}/entitlements", response_model=CompanyEntitlementsResponse)
def get_company_entitlements(
    company_id: str,
    actor: Actor = Depends(get_current_actor),  # ⚠️ NOT IMPLEMENTED
    db: Session = Depends(get_db),
):
    # 權限：super_admin / customer_service / company_user（只讀）
    pass

@router.patch("/{company_id}/entitlements", response_model=EntitlementResponse)
def update_company_entitlement(
    company_id: str,
    request: UpdateEntitlementRequest,
    actor: Actor = Depends(get_current_actor),  # ⚠️ NOT IMPLEMENTED
    db: Session = Depends(get_db),
):
    # 權限：只有 super_admin
    pass

@router.post("/{company_id}/entitlements/apply-plan", response_model=ApplyPlanResponse)
def apply_plan_defaults(
    company_id: str,
    request: ApplyPlanRequest,
    actor: Actor = Depends(get_current_actor),  # ⚠️ NOT IMPLEMENTED
    db: Session = Depends(get_db),
):
    # 權限：只有 super_admin
    pass
```

**Dependencies：**
- `get_current_actor()` - ⚠️ **NOT IMPLEMENTED**
- `get_db()` - ✅ 已存在（`app/core/database.py`）

**Middleware：**
- ❌ 無額外 middleware
- ❌ 無 rate limiting
- ❌ 無 CORS 設定（需在 main.py 設定）

### Customer Service API Routes

**檔案：** `backend/app/modules/customer_service/api.py`

```python
router = APIRouter(prefix="/api/customer-service", tags=["customer_service"])

@router.get("/assigned-companies", response_model=AssignedCompaniesResponse)
def get_assigned_companies(
    actor: Actor = Depends(get_current_actor),  # ⚠️ NOT IMPLEMENTED
    db: Session = Depends(get_db),
):
    # 權限：只有 customer_service
    pass

@router.post("/assignments", response_model=AssignmentResponse, status_code=201)
def assign_company(
    request: AssignCompanyRequest,
    actor: Actor = Depends(get_current_actor),  # ⚠️ NOT IMPLEMENTED
    db: Session = Depends(get_db),
):
    # 權限：只有 super_admin
    pass

@router.delete("/assignments", response_model=UnassignmentResponse)
def unassign_company(
    request: UnassignCompanyRequest,
    actor: Actor = Depends(get_current_actor),  # ⚠️ NOT IMPLEMENTED
    db: Session = Depends(get_db),
):
    # 權限：只有 super_admin
    pass
```

**Dependencies：**
- `get_current_actor()` - ⚠️ **NOT IMPLEMENTED**
- `get_db()` - ✅ 已存在

### Attendance Feature Gate Demo Routes

**檔案：** `backend/app/modules/attendance/feature_gate_demo.py`

**⚠️ 重要：此檔案尚未註冊到 router**

```python
# 這些端點定義在 feature_gate_demo.py 中，但未註冊到 main.py

@router.post("/shift-overrides", status_code=201)
async def create_shift_override(
    request: Request,
    db: Session = Depends(get_db),
    company_id: str = Depends(get_current_company_id),
    user_id: UUID = Depends(get_current_user_id),
):
    # Feature Gate: attendance.shift_overrides
    pass

@router.get("/shift-templates")
async def list_shift_templates(
    db: Session = Depends(get_db),
    company_id: str = Depends(get_current_company_id),
):
    # Feature Gate: attendance.shift_templates
    pass

@router.post("/split-shifts", status_code=201)
async def create_split_shift(
    request: Request,
    db: Session = Depends(get_db),
    company_id: str = Depends(get_current_company_id),
    user_id: UUID = Depends(get_current_user_id),
):
    # Feature Gate: attendance.split_shift
    pass
```

**Dependencies：**
- `get_db()` - ✅ 已存在
- `get_current_company_id()` - ✅ 已存在（`app/core/tenant_context.py`）
- `get_current_user_id()` - ✅ 已存在（`app/core/tenant_context.py`）
- `get_feature_service()` - ✅ 已實作

**註冊狀態：** ❌ **NOT REGISTERED**

需要在 `backend/app/main.py` 中加入：
```python
from app.modules.attendance.feature_gate_demo import router as attendance_demo_router
app.include_router(attendance_demo_router)
```

---

## 🔟 尚未完成項目（TODO List）

### 🔴 Critical（必須完成）

1. **實作 get_current_actor()**
   - 位置：`app/core/` 或 `app/modules/auth/`
   - 需要整合 JWT 驗證
   - 需要查詢 memberships 和 assignments
   - 預估工時：2-4 小時

2. **註冊 Router 到 main.py**
   - 註冊 `tenants.api.router`
   - 註冊 `customer_service.api.router`
   - 註冊 `attendance.feature_gate_demo.router`（可選）
   - 預估工時：30 分鐘

3. **執行 Migration**
   - 執行 `alembic upgrade head`
   - 驗證表結構正確
   - 預估工時：15 分鐘

4. **建立測試檔案**
   - `test_features.py` (約 150 行)
   - `test_scope.py` (約 200 行)
   - `test_entitlements_api.py` (約 250 行)
   - `test_support_company_scope.py` (約 300 行)
   - `test_feature_gate.py` (約 280 行)
   - 預估工時：8-12 小時

### 🟡 Important（建議完成）

5. **補充 API 文件**
   - OpenAPI/Swagger 註解
   - Request/Response 範例
   - 預估工時：2 小時

6. **錯誤處理統一化**
   - 建立統一的 exception handler
   - 確保錯誤格式一致
   - 預估工時：1 小時

7. **快取策略優化**
   - 考慮使用 Redis
   - 設定 TTL
   - 預估工時：4 小時

### 🟢 Nice to Have（可選）

8. **Logging 增強**
   - 加入結構化日誌
   - 記錄 scope 檢查結果
   - 預估工時：2 小時

9. **Metrics 收集**
   - Feature gate 使用統計
   - Scope 檢查失敗統計
   - 預估工時：3 小時

10. **前端整合**
    - UI 隱藏未啟用功能
    - 顯示 feature disabled 提示
    - 預估工時：4-6 小時

---

## 📊 完成度統計

### 實作完成度

| 項目 | 狀態 | 完成度 |
|------|------|--------|
| Feature Keys 定義 | ✅ 完成 | 100% |
| Feature Service | ✅ 完成 | 100% |
| Scope 檢查機制 | ✅ 完成 | 100% |
| 資料模型 | ✅ 完成 | 100% |
| Repository 層 | ✅ 完成 | 100% |
| Service 層 | ✅ 完成 | 100% |
| API 層 | ✅ 完成 | 100% |
| Migration | ✅ 完成 | 100% |
| get_current_actor() | ❌ 未實作 | 0% |
| Router 註冊 | ❌ 未完成 | 0% |
| 測試檔案 | ❌ 未建立 | 0% |
| 文件 | ✅ 完成 | 100% |

**總體完成度：** 約 75%

### 可立即使用的功能

✅ Feature Keys 驗證  
✅ Feature Service（需要 DB 連線）  
✅ Scope 檢查（需要 Actor 物件）  
✅ Repository 和 Service 層邏輯  
❌ API 端點（需要實作 get_current_actor）  
❌ 完整的端到端流程（需要 router 註冊）

---

## 📝 架構審查建議

### 優點

1. ✅ 遵守 SA_MODULE_SPEC v1.8 規範
2. ✅ 清晰的模組分離（core / tenants / customer_service）
3. ✅ 統一的驗證順序（Scope → Tenant Isolation → Feature Gate）
4. ✅ 完整的錯誤處理機制
5. ✅ 良好的快取設計
6. ✅ 詳細的文件

### 需要改進

1. ❌ 缺少 get_current_actor() 實作
2. ❌ 缺少測試檔案
3. ❌ Router 未註冊到 main.py
4. ❌ 缺少 API 文件（OpenAPI）
5. ⚠️ 快取策略可能需要 Redis（目前使用記憶體）
6. ⚠️ 缺少 rate limiting

### 風險評估

| 風險 | 等級 | 說明 |
|------|------|------|
| get_current_actor() 未實作 | 🔴 High | API 無法使用 |
| 測試覆蓋率不足 | 🔴 High | 無法驗證正確性 |
| Router 未註冊 | 🟡 Medium | 端點無法存取 |
| 快取使用記憶體 | 🟢 Low | 單機可用，叢集需 Redis |

---

**審查日期：** 2026-03-04  
**審查者：** AI Assistant (Claude Sonnet 4)  
**建議：** 完成 Critical 項目後即可進入測試階段
