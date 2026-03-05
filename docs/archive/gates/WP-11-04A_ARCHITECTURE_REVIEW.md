# WP-11-04A 架構審查文件

## 1️⃣ Git 狀態

### 最新 Commit
```
Hash: 35e8f63
Message: docs(auth): add WP-10-04A completion report
Branch: master
Status: 與 origin/master 一致
```

### Git Status 摘要

**未追蹤的新檔案（WP-11-04A）：**
```
backend/app/core/features.py
backend/app/core/feature_service.py
backend/app/core/scope.py
backend/app/modules/customer_service/ (整個目錄)
backend/app/modules/tenants/api.py
backend/app/modules/tenants/schemas.py
backend/app/modules/attendance/feature_gate_demo.py
backend/alembic/versions/wp_11_04a_entitlements.py
docs/WP-11-04A_COMPLETION_REPORT.md
docs/WP-11-04A_SUMMARY.md
docs/SA_MODULE_SPECV1.8.md
```

**已修改的檔案（WP-11-04A）：**
```
backend/app/modules/tenants/models.py (新增 CompanyEntitlement)
backend/app/modules/tenants/repo.py (新增 CompanyEntitlementRepository)
backend/app/modules/tenants/service.py (新增 CompanyEntitlementService)
backend/app/modules/tenants/tests/__init__.py
backend/app/core/tests/__init__.py
```

**注意：** 本次實作尚未 commit，所有檔案處於 untracked 或 modified 狀態。

---

## 2️⃣ 新增檔案清單

### Core 模組（3 個檔案）

1. **backend/app/core/features.py** (1.8K)
   - 定義所有 feature keys 常數
   - 提供 key 驗證機制
   - 定義 Plan 預設配置（Basic/Pro）

2. **backend/app/core/feature_service.py** (4.2K)
   - FeatureService 類別
   - FeatureDisabledError 異常類別
   - 快取機制實作

3. **backend/app/core/scope.py** (5.0K)
   - Actor 類別（封裝操作者資訊）
   - UserRole 枚舉
   - ScopeChecker 類別
   - ScopeError 異常類別

### Customer Service 模組（6 個檔案）

4. **backend/app/modules/customer_service/__init__.py** (30 bytes)
5. **backend/app/modules/customer_service/models.py** (1.7K)
   - SupportCompanyAssignment 模型
6. **backend/app/modules/customer_service/repo.py** (3.0K)
   - CustomerServiceRepo 類別
7. **backend/app/modules/customer_service/service.py** (2.9K)
   - CustomerServiceService 類別
8. **backend/app/modules/customer_service/api.py** (2.9K)
   - FastAPI router 定義
9. **backend/app/modules/customer_service/schemas.py** (1.3K)
   - Pydantic schemas

### Tenants 模組擴充（2 個檔案）

10. **backend/app/modules/tenants/api.py**
    - Entitlements 管理 API 端點
11. **backend/app/modules/tenants/schemas.py**
    - Entitlements API schemas

### Attendance 模組示範（1 個檔案）

12. **backend/app/modules/attendance/feature_gate_demo.py**
    - Feature Gate 示範端點（3 個 stub endpoints）

### Migration（1 個檔案）

13. **backend/alembic/versions/wp_11_04a_entitlements.py** (3.5K)
    - 建立 company_entitlements 表
    - 建立 support_company_assignments 表

### 測試框架（3 個檔案）

14. **backend/app/core/tests/__init__.py** (已修改)
15. **backend/app/modules/tenants/tests/__init__.py** (已修改)
16. **backend/app/modules/customer_service/tests/__init__.py** (新增)

### 文件（3 個檔案）

17. **docs/WP-11-04A_COMPLETION_REPORT.md** (9.4K)
18. **docs/WP-11-04A_SUMMARY.md** (2.9K)
19. **docs/SA_MODULE_SPECV1.8.md** (已存在，未修改)

**總計：19 個檔案（13 個新增，6 個修改）**

---

## 3️⃣ 修改檔案清單

### 已修改的檔案

1. **backend/app/modules/tenants/models.py**
   - 新增 `CompanyEntitlement` 模型類別
   - 新增必要的 imports（UUID, ForeignKey, UniqueConstraint）

2. **backend/app/modules/tenants/repo.py**
   - 新增 `CompanyEntitlementRepository` 類別
   - 新增 `get_entitlement_repository()` 函數
   - 擴充 imports

3. **backend/app/modules/tenants/service.py**
   - 新增 `CompanyEntitlementService` 類別
   - 新增 `get_entitlement_service()` 函數
   - 擴充 imports（Actor, ScopeError, FeatureKeys, etc.）

4. **backend/app/core/tests/__init__.py**
   - 新增 docstring

5. **backend/app/modules/tenants/tests/__init__.py**
   - 新增 docstring

6. **backend/app/modules/customer_service/tests/__init__.py**
   - 新增檔案

---

## 4️⃣ Migration 詳細內容

### 檔案：wp_11_04a_entitlements.py

**Revision Info:**
```python
revision = 'wp_11_04a_entitlements'
down_revision = '005_create_notifications'
branch_labels = None
depends_on = None
```

### Table 1: company_entitlements

**欄位定義：**
```sql
CREATE TABLE company_entitlements (
    id UUID PRIMARY KEY,
    company_id VARCHAR(50) NOT NULL,
    feature_key VARCHAR(100) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT false,
    updated_by_user_id UUID NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_company FOREIGN KEY (company_id) 
        REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_updated_by FOREIGN KEY (updated_by_user_id) 
        REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT uq_company_entitlements_company_feature 
        UNIQUE (company_id, feature_key)
);
```

**索引：**
- `idx_company_entitlements_company_id` ON (company_id)
- `idx_company_entitlements_feature_key` ON (feature_key)

### Table 2: support_company_assignments

**欄位定義：**
```sql
CREATE TABLE support_company_assignments (
    user_id UUID NOT NULL,
    company_id VARCHAR(50) NOT NULL,
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assigned_by_user_id UUID NULL,
    
    PRIMARY KEY (user_id, company_id),
    CONSTRAINT fk_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_company FOREIGN KEY (company_id) 
        REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT fk_assigned_by FOREIGN KEY (assigned_by_user_id) 
        REFERENCES users(id) ON DELETE SET NULL
);
```

**索引：**
- `idx_support_company_assignments_user_id` ON (user_id)
- `idx_support_company_assignments_company_id` ON (company_id)

**Downgrade 邏輯：**
- 刪除所有索引
- 刪除兩個表（順序：support_company_assignments → company_entitlements）

---

## 5️⃣ Scope 驗證邏輯

### 檔案：backend/app/core/scope.py

### 核心類別

#### 1. UserRole (Enum)
```python
class UserRole(Enum):
    SUPER_ADMIN = "super_admin"
    CUSTOMER_SERVICE = "customer_service"
    COMPANY_USER = "company_user"
```

#### 2. Actor 類別
```python
class Actor:
    def __init__(
        self,
        user_id: UUID,
        role: UserRole,
        company_memberships: Optional[Set[str]] = None,
        support_company_assignments: Optional[Set[str]] = None,
    ):
        self.user_id = user_id
        self.role = role
        self.company_memberships = company_memberships or set()
        self.support_company_assignments = support_company_assignments or set()
```

**方法：**
- `is_super_admin()` → bool
- `is_customer_service()` → bool
- `is_company_user()` → bool

#### 3. ScopeChecker 類別

**核心方法：assert_company_scope()**

```python
def assert_company_scope(self, actor: Actor, company_id: str) -> None:
    # Super Admin：直接通過
    if actor.is_super_admin():
        return
    
    # Customer Service：檢查 support_company_assignments
    if actor.is_customer_service():
        if company_id not in actor.support_company_assignments:
            raise ScopeError(
                f"Customer service user {actor.user_id} is not assigned to company {company_id}"
            )
        return
    
    # Company User：檢查 company_memberships
    if actor.is_company_user():
        if company_id not in actor.company_memberships:
            raise ScopeError(
                f"User {actor.user_id} is not a member of company {company_id}"
            )
        return
    
    # 未知角色：拒絕
    raise ScopeError(f"Unknown role: {actor.role}")
```

**輔助方法：**
- `get_accessible_companies(actor)` → Set[str]
- `_get_all_company_ids()` → Set[str] (查詢 DB)

### 便捷函數

```python
def assert_company_scope(actor: Actor, company_id: str, db: Session) -> None:
    checker = ScopeChecker(db)
    checker.assert_company_scope(actor, company_id)
```

### 驗證邏輯流程

```
1. 檢查 actor.role
2. 根據角色執行不同邏輯：
   - super_admin: 直接通過
   - customer_service: 檢查 support_company_assignments
   - company_user: 檢查 company_memberships
3. 不通過則拋出 ScopeError (HTTP 403)
```

---

## 6️⃣ Feature Gate 邏輯

### 檔案：backend/app/core/feature_service.py

### 核心類別

#### 1. FeatureDisabledError
```python
class FeatureDisabledError(Exception):
    def __init__(self, feature_key: str):
        self.feature_key = feature_key
        self.message = f"Feature '{feature_key}' is not enabled for this company"
```

#### 2. FeatureService 類別

**初始化：**
```python
def __init__(self, db: Session):
    self.db = db
    self._cache: Dict[tuple, bool] = {}  # (company_id, feature_key) -> enabled
```

**核心方法：is_enabled()**
```python
def is_enabled(self, company_id: str, feature_key: str) -> bool:
    # 1. 驗證 feature_key
    FeatureKeys.validate(feature_key)
    
    # 2. 檢查快取
    cache_key = (company_id, feature_key)
    if cache_key in self._cache:
        return self._cache[cache_key]
    
    # 3. 查詢資料庫
    enabled = self._query_entitlement(company_id, feature_key)
    
    # 4. 更新快取
    self._cache[cache_key] = enabled
    
    return enabled
```

**核心方法：require_enabled()**
```python
def require_enabled(self, company_id: str, feature_key: str) -> None:
    if not self.is_enabled(company_id, feature_key):
        raise FeatureDisabledError(feature_key)
```

**資料庫查詢：**
```python
def _query_entitlement(self, company_id: str, feature_key: str) -> bool:
    from app.modules.tenants.models import CompanyEntitlement
    
    result = self.db.query(CompanyEntitlement).filter(
        CompanyEntitlement.company_id == company_id,
        CompanyEntitlement.feature_key == feature_key
    ).first()
    
    if result:
        return result.enabled
    
    # 未設定時預設為 False
    return False
```

**快取管理：**
```python
def clear_cache(self, company_id: Optional[str] = None, feature_key: Optional[str] = None):
    # 可清除全部、指定公司、或指定 feature
    if company_id is None and feature_key is None:
        self._cache.clear()
    else:
        # 選擇性清除
        keys_to_remove = [...]
        for key in keys_to_remove:
            del self._cache[key]
```

### Feature Gate 流程

```
1. 驗證 feature_key 是否有效（FeatureKeys.validate）
2. 檢查記憶體快取
3. 若快取未命中，查詢 company_entitlements 表
4. 回傳 enabled 狀態（未設定預設 False）
5. 若 require_enabled() 且未啟用，拋出 FeatureDisabledError
```

### Feature Keys 定義

**檔案：backend/app/core/features.py**

```python
class FeatureKeys:
    ATTENDANCE_SHIFT_TEMPLATES = "attendance.shift_templates"
    ATTENDANCE_SPLIT_SHIFT = "attendance.split_shift"
    ATTENDANCE_SHIFT_OVERRIDES = "attendance.shift_overrides"
    
    @classmethod
    def all_keys(cls) -> Set[str]:
        return {
            cls.ATTENDANCE_SHIFT_TEMPLATES,
            cls.ATTENDANCE_SPLIT_SHIFT,
            cls.ATTENDANCE_SHIFT_OVERRIDES,
        }
    
    @classmethod
    def validate(cls, key: str) -> None:
        if not cls.is_valid(key):
            raise ValueError(f"Unknown feature key: {key}")
```

**Plan 預設配置：**
```python
PLAN_DEFAULTS = {
    "Basic": {
        FeatureKeys.ATTENDANCE_SHIFT_TEMPLATES: False,
        FeatureKeys.ATTENDANCE_SPLIT_SHIFT: False,
        FeatureKeys.ATTENDANCE_SHIFT_OVERRIDES: False,
    },
    "Pro": {
        FeatureKeys.ATTENDANCE_SHIFT_TEMPLATES: True,
        FeatureKeys.ATTENDANCE_SPLIT_SHIFT: True,
        FeatureKeys.ATTENDANCE_SHIFT_OVERRIDES: True,
    },
}
```

---

**（續下一部分）**
