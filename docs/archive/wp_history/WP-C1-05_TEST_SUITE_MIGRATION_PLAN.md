# WP-C1-05 測試套件遷移計畫

**日期：** 2026-03-11  
**範圍：** `backend/` 全部測試檔案  
**目標：** 將測試套件從 Header-based 驗證遷移至 JWT Actor dependency override

---

## 1. 現況掃描

### 1.1 測試總數

| 項目 | 數量 |
|------|------|
| 測試檔案總數 | 33 個 |
| 測試函數總數 | 257 個 |
| 預估失敗數（Header 驗證） | ~74 個 |

### 1.2 受影響模組分類

#### Category A — WP-C1-03 已遷移模組（需更新測試）

這三個模組已完成 API 遷移至 `get_actor_with_company`，測試仍使用舊 Header。

| 模組 | 測試檔案 | 測試數 | legacy 行數 |
|------|----------|--------|-------------|
| notifications | `tests/test_tenant_isolation.py` | 7 | 5 行 |
| backup | `tests/test_api.py` | 11 | 18 行 |
| audit | `tests/test_audit_api.py` | 11 | 14 行 |
| audit | `tests/test_audit_retention.py` | 13 | 18 行 |
| **小計** | 4 檔案 | **42** | **55 行** |

#### Category B — attendance 模組（API 尚未遷移，測試亦使用舊 Header）

| 測試檔案 | 測試數 | legacy 行數 |
|----------|--------|-------------|
| `tests/test_api.py` | 5 | 6 行 |
| `tests/test_tenant_isolation.py` | 9 | 18 行 |
| `tests/test_phase4.py` | 6 | 16 行 |
| `tests/test_break_out_enforcement.py` | 8 | 16 行 |
| `tests/test_regression.py` | 2 | 4 行 |
| `tests/test_out_checkpoint.py` | - | 2 行 |
| **小計** | 5 檔案 | **30** | **62 行** |

#### Category C — 不需修改（無 Header 依賴）

| 模組 | 測試檔案 | 說明 |
|------|----------|------|
| tenants | `test_entitlements_api.py` | 已使用 `dependency_overrides[get_current_actor]` |
| auth | `test_login_api.py`, `test_repo.py` | 不涉及 company scope |
| core | `test_scope.py`, `test_feature_service.py` | 純 unit test |
| core | `test_tenant_context.py` | 測試 legacy 行為本身，保留 |
| backup | `test_tenant_isolation.py`, `test_validator.py` | 不涉及 API |
| notifications | `test_event_handlers.py` | 不涉及 API |
| attendance | `test_policy_engine.py`, `test_business_invariant.py` | 純 unit test |
| attendance | `test_migration.py`, `test_model_constraints.py` | DB 層測試 |
| attendance | `test_location_policy.py` | location policy 層 |
| root | `test_migration_smoke.py` | alembic 測試 |

---

## 2. 測試驗證輔助工具設計

### 2.1 建立 `tests/utils/auth.py`

路徑：`backend/app/tests/utils/auth.py`（共用）或各模組 `conftest.py`。

設計原則：
- **不產生 JWT token**：直接建立 `Actor` 物件，透過 `dependency_overrides` 注入
- **不依賴資料庫**：Actor 為純 Python 物件，無需 DB 查詢
- **支援多角色**：admin、employee、super_admin、multi-company

```python
# backend/app/tests/utils/auth.py
"""Test authentication helpers for JWT Actor migration (WP-C1-05)"""

from uuid import UUID, uuid4
from typing import Optional
from app.core.scope import Actor, UserRole
from app.core.dependencies import get_actor_with_company
from app.main import app


DEFAULT_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def create_test_actor(
    company_id: str,
    user_id: Optional[UUID] = None,
    role_id: str = "admin",
    platform_role: UserRole = UserRole.COMPANY_USER,
) -> Actor:
    """
    建立測試用 Actor，無需 JWT token 或資料庫查詢。

    Args:
        company_id: 測試公司 ID（對應 active_company_id）
        user_id: 測試使用者 ID（預設固定 UUID）
        role_id: 公司內角色（"admin" / "employee" / "manager"）
        platform_role: 平台層角色

    Returns:
        Actor: 可直接注入 FastAPI dependency 的測試 Actor
    """
    return Actor(
        user_id=user_id or DEFAULT_USER_ID,
        role=platform_role,
        company_memberships={company_id},
        active_company_id=company_id,
        active_role_id=role_id,
    )


def create_super_admin_actor(
    company_id: Optional[str] = None,
    user_id: Optional[UUID] = None,
) -> Actor:
    """建立 super_admin 測試 Actor"""
    return Actor(
        user_id=user_id or DEFAULT_USER_ID,
        role=UserRole.SUPER_ADMIN,
        company_memberships=set(),
        active_company_id=company_id,
        active_role_id="super_admin",
    )


def override_actor_dependency(actor: Actor):
    """
    Context manager：覆寫 get_actor_with_company dependency。

    用法：
        actor = create_test_actor("company-A")
        with override_actor_dependency(actor):
            response = client.get("/api/notifications")

    自動清除 override，避免測試間污染。
    """
    from contextlib import contextmanager

    @contextmanager
    def _override():
        app.dependency_overrides[get_actor_with_company] = lambda: actor
        try:
            yield
        finally:
            app.dependency_overrides.pop(get_actor_with_company, None)

    return _override()
```

### 2.2 conftest.py fixture 設計

在各模組的 `conftest.py` 新增共用 fixture：

```python
# 新增至各模組 conftest.py
import pytest
from app.tests.utils.auth import create_test_actor
from app.core.dependencies import get_actor_with_company
from app.main import app


@pytest.fixture
def actor_company_a():
    """Company A 的 admin actor fixture"""
    return create_test_actor(company_id="company-A", role_id="admin")


@pytest.fixture
def actor_company_b():
    """Company B 的 admin actor fixture"""
    return create_test_actor(company_id="company-B", role_id="admin")


@pytest.fixture
def with_actor_company_a(actor_company_a):
    """自動 override get_actor_with_company 為 company-A actor"""
    app.dependency_overrides[get_actor_with_company] = lambda: actor_company_a
    yield actor_company_a
    app.dependency_overrides.pop(get_actor_with_company, None)
```

---

## 3. FastAPI Dependency Override 機制

### 3.1 原理

FastAPI 的 `app.dependency_overrides` 是一個 dict，key 為原始 dependency 函數，value 為替換函數。測試時直接覆寫，無需 JWT token、無需資料庫驗證。

```python
# 覆寫方式
app.dependency_overrides[get_actor_with_company] = lambda: actor

# 清除（測試後必須執行）
app.dependency_overrides.pop(get_actor_with_company, None)
# 或全部清除
app.dependency_overrides.clear()
```

### 3.2 與現有 get_db override 並存

現有測試已 override `get_db`，新的 actor override 需與其並存：

```python
# conftest.py 中同時存在兩個 override
app.dependency_overrides[get_db] = override_get_db        # 已有
app.dependency_overrides[get_actor_with_company] = lambda: actor  # 新增
```

兩者不衝突，FastAPI 各自獨立解析。

### 3.3 RBAC 測試（admin endpoints）

backup/export、backup/restore、audit/export、audit/retention PUT、audit/purge 需要 admin role：

```python
# 測試 admin 端點
actor_admin = create_test_actor("company-A", role_id="admin")
app.dependency_overrides[get_actor_with_company] = lambda: actor_admin
response = client.post("/api/backup/export")
assert response.status_code == 200

# 測試 non-admin 被拒絕（403）
actor_employee = create_test_actor("company-A", role_id="employee")
app.dependency_overrides[get_actor_with_company] = lambda: actor_employee
response = client.post("/api/backup/export")
assert response.status_code == 403
```

### 3.4 Tenant Isolation 測試

跨公司隔離透過兩個不同 actor 驗證：

```python
# company-A 寫入資料
actor_a = create_test_actor("company-A")
app.dependency_overrides[get_actor_with_company] = lambda: actor_a
client.post("/api/notifications", json={...})

# company-B 讀取，應看不到 company-A 的資料
actor_b = create_test_actor("company-B")
app.dependency_overrides[get_actor_with_company] = lambda: actor_b
response = client.get("/api/notifications")
assert len(response.json()["notifications"]) == 0
```

### 3.5 無授權測試（401/403）

原本測試「缺少 X-Company-ID 回 400」的案例，遷移後改為測試「無 JWT 回 401」或「無 active_company_id 回 403」：

```python
# 舊：測試缺少 Header → 400
# response = client.get("/api/notifications")  # 無 X-Company-ID header
# assert response.status_code == 400

# 新：不 override dependency，FastAPI 會嘗試執行 get_actor_with_company
# 因無 Authorization header → 401
# 或：override 為無 active_company_id 的 actor → 403
actor_no_company = Actor(user_id=uuid4(), role=UserRole.COMPANY_USER)
app.dependency_overrides[get_actor_with_company] = lambda: actor_no_company
# 注意：get_actor_with_company 本身會在 has_active_company() = False 時拋 403
```

---

## 4. 逐檔案遷移計畫

### 4.1 Category A — 優先執行（WP-C1-03 已遷移模組）

#### `notifications/tests/test_tenant_isolation.py`（7 tests）

| 測試 | 遷移動作 |
|------|----------|
| `test_get_notifications_requires_company_header` | 改為測試無 actor override → 401，或 actor 無 company → 403 |
| `test_get_notifications_with_company_a_context` | 移除 `X-Company-ID` header，改用 `actor_company_a` fixture |
| `test_get_notifications_cross_company_isolation` | 用兩個不同 actor 分別呼叫 |
| `test_pagination` | 移除 `X-Company-ID` header，改用 actor fixture |
| `test_repo_get_all_for_backup` | 不涉及 API，無需修改 |
| `test_create_notification_with_correct_company_id` | 不涉及 API，無需修改 |
| `test_get_notifications_filters_by_company_id` | 不涉及 API，無需修改 |

#### `backup/tests/test_api.py`（11 tests）

所有測試均使用 `headers={"X-Company-ID": ...}`，全部改用 actor override。

新增注意點：`test_export_success`、`test_restore_success` 等需 admin actor（因 export/restore 加了 RBAC）。

| 測試 | 遷移動作 | RBAC |
|------|----------|------|
| `test_export_success` | actor override (company-test) | admin |
| `test_export_empty_company` | actor override (company-empty) | admin |
| `test_export_returns_json_on_error` | actor override | admin |
| `test_restore_success` | actor override (company-target) | admin |
| `test_restore_invalid_format` | actor override | admin |
| `test_restore_mixed_company_ids` | 兩個 actor（source/target） | admin |
| `test_restore_returns_json_on_error` | actor override | admin |
| `test_export_and_restore_roundtrip` | actor override | admin |
| `test_export_includes_attendance_records` | actor override | admin |
| `test_restore_attendance_records_success` | actor override | admin |
| `test_export_and_restore_attendance_records_roundtrip` | actor override | admin |

#### `audit/tests/test_audit_api.py`（11 tests）

| 測試 | 遷移動作 | RBAC |
|------|----------|------|
| `test_no_company_id_returns_400` | 改為 403 測試（無 active_company_id actor） | - |
| `test_query_logs_*` | actor override (company-A/B) | 一般成員 |
| `test_export_logs_*` | actor override (company-A) | **admin** |

#### `audit/tests/test_audit_retention.py`（13 tests）

| 測試 | 遷移動作 | RBAC |
|------|----------|------|
| `test_missing_header_*` | 改為 403 測試 | - |
| `test_get_retention_*` | actor override | 一般成員 |
| `test_update_retention_*` | actor override | **admin** |
| `test_purge_*` | actor override | **admin** |

### 4.2 Category B — 次要執行（attendance 模組）

attendance API 尚未遷移至 JWT Actor，Category B 的測試修復需等待 attendance API 遷移完成後再處理。

**建議：** 以 `@pytest.mark.skip(reason="WP-C1-attendance: pending API migration")` 暫時跳過，避免阻塞 CI。

---

## 5. 執行順序

```
Step 1: 建立 backend/app/tests/utils/__init__.py
Step 2: 建立 backend/app/tests/utils/auth.py
Step 3: 更新 notifications/tests/conftest.py（新增 actor fixtures）
Step 4: 更新 notifications/tests/test_tenant_isolation.py
Step 5: 更新 backup/tests/conftest.py（新增 actor fixtures）
Step 6: 更新 backup/tests/test_api.py
Step 7: 更新 audit/tests/conftest.py（新增 actor fixtures）
Step 8: 更新 audit/tests/test_audit_api.py
Step 9: 更新 audit/tests/test_audit_retention.py
Step 10: 執行測試確認全數通過
```

---

## 6. 驗證指令

```bash
# 執行 Category A 全部測試
/opt/attendance-system/backend/venv/bin/pytest \
  backend/app/modules/notifications/tests/ \
  backend/app/modules/backup/tests/ \
  backend/app/modules/audit/tests/ \
  -v --tb=short

# 執行全部測試（含 skip）
/opt/attendance-system/backend/venv/bin/pytest \
  backend/ \
  -v --tb=short 2>&1 | tail -30
```

---

## 7. 不修改的項目

| 項目 | 理由 |
|------|------|
| service / repo 層邏輯 | 測試不應修改業務邏輯 |
| `test_tenant_context.py` | 測試 legacy tenant_context 行為本身，屬正確測試 |
| `test_migration_smoke.py` | alembic 測試，與驗證無關 |
| Category C 所有測試 | 已正確或與 Header 無關 |
| attendance 模組 API | 尚未列入 WP-C1-03 範圍 |

---

*計畫產出：WP-C1-05，執行實作請開立 WP-C1-06 ticket*
