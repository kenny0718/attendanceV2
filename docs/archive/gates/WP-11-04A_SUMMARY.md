# WP-11-04A 實作總結

## 已完成項目

### ✅ A) Feature Keys 定義
- `app/core/features.py` - 集中定義所有 feature keys
- 支援 `attendance.shift_templates`, `attendance.split_shift`, `attendance.shift_overrides`
- 提供 Plan 預設配置（Basic/Pro）

### ✅ B) Feature Service
- `app/core/feature_service.py` - 唯一的 feature gate 入口
- `is_enabled()` / `require_enabled()` 方法
- 內建快取機制

### ✅ C) Scope 檢查機制
- `app/core/scope.py` - 統一的權限範圍檢查
- 支援 super_admin / customer_service / company_user
- `assert_company_scope()` 便捷函數

### ✅ D) 資料模型
- `CompanyEntitlement` - 公司功能權限（已存在於 tenants/models.py）
- `SupportCompanyAssignment` - 客服公司指派（新增於 customer_service/models.py）

### ✅ E) Repository 層
- `tenants/repo.py` - 新增 `CompanyEntitlementRepository`
- `customer_service/repo.py` - 新增 `CustomerServiceRepo`

### ✅ F) Service 層
- `tenants/service.py` - 新增 `CompanyEntitlementService`
- `customer_service/service.py` - 新增 `CustomerServiceService`

### ✅ G) API 層
- `tenants/api.py` - Entitlements 管理端點
- `customer_service/api.py` - 客服指派管理端點
- `attendance/feature_gate_demo.py` - Feature Gate 示範端點

### ✅ H) Migration
- `alembic/versions/wp_11_04a_entitlements.py` - 已存在且正確

### ✅ I) 文件
- 更新 `SA_MODULE_SPECV1.8.md`（已是最新）
- 建立 `WP-11-04A_COMPLETION_REPORT.md`

### ✅ J) 測試框架
- 建立測試目錄結構
- `core/tests/`, `tenants/tests/`, `customer_service/tests/`

## 核心設計

### 驗證順序（強制）
```
Scope → Tenant Isolation → Feature Gate
```

### 角色權限
- **super_admin**: 可管理所有公司的 entitlements
- **customer_service**: 只能讀取被指派公司的 entitlements
- **company_user**: 只能讀取所屬公司的 entitlements

### 錯誤格式
```json
{
  "code": "FEATURE_DISABLED",
  "feature": "attendance.shift_overrides",
  "message": "..."
}
```

## 下一步

1. 執行 migration: `alembic upgrade head`
2. 實作 `get_current_actor()` dependency
3. 補齊單元測試
4. 前端 UI 整合

## 檔案清單

**Core:**
- app/core/features.py
- app/core/feature_service.py
- app/core/scope.py

**Tenants:**
- app/modules/tenants/models.py (已更新)
- app/modules/tenants/repo.py
- app/modules/tenants/service.py
- app/modules/tenants/api.py
- app/modules/tenants/schemas.py

**Customer Service:**
- app/modules/customer_service/models.py
- app/modules/customer_service/repo.py
- app/modules/customer_service/service.py
- app/modules/customer_service/api.py
- app/modules/customer_service/schemas.py

**Attendance:**
- app/modules/attendance/feature_gate_demo.py

**Migration:**
- alembic/versions/wp_11_04a_entitlements.py

**文件:**
- docs/WP-11-04A_COMPLETION_REPORT.md
- docs/SA_MODULE_SPECV1.8.md (已更新)
