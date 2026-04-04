# WP-TEST: Auth Override Alignment Report

**日期**：2026-03-28  
**範圍**：`backend/app/modules/attendance/tests/test_reporting_sessions.py`  
**原則**：不改 production code，只做測試最小修正

---

## 1. Summary

| 項目 | 結果 |
|------|------|
| 修正前失敗數 | 19 failed（原估計 3，實際更多）|
| 修正後結果 | **21 passed, 0 failed** ✅ |
| 修改檔案 | 僅 `test_reporting_sessions.py`（1 個測試檔）|
| Production code 異動 | **無** |

**根本原因（共 3 個）：**

1. **`hdr()` 未定義**：測試檔引用 `hdr(company_id, user_id)` 但此 helper 從未在測試檔或 conftest 中定義，導致 `NameError` → 16 個測試無 auth → 401
2. **Feature Gate 未啟用（403）**：`tenant_a` / `tenant_b` fixture 只建立 `Tenant`，未建立 `CompanyEntitlement(attendance.core)`。Production endpoint 的 `_require_attendance_feature()` 在 feature 未啟用時回傳 403
3. **SES-11 assert 在 `with` 區塊外**：`override_actor_dependency` context manager 結束後，override 已清除，assert 時走真實 JWT auth → 401 → 期望 422 但實際 401

---

## 2. Files Changed

| 檔案 | 異動類型 |
|------|----------|
| `backend/app/modules/attendance/tests/test_reporting_sessions.py` | 測試修正（5 個 patch）|

**未異動：**
- `backend/app/modules/attendance/api.py`（production code）
- `backend/app/core/dependencies.py`
- `backend/app/core/feature_service.py`
- `backend/app/conftest.py`
- 任何其他模組

---

## 3. Failure Audit

### 修正前狀況

| 測試 | 預期 | 實際 | 原因 |
|------|------|------|------|
| SES-01 × 2 | 200 | 401 | `NameError: hdr` + 無 feature entitlement |
| SES-02 | 200 | 401 | 同上 |
| SES-03 | 200 | 401 | 同上 |
| SES-04 | 200 | 401 | 同上 |
| SES-05 × 2 | 200 | 403 | feature gate 未啟用 |
| SES-06 | 403（isolation） | 403（feature gate）| feature gate 干擾 |
| SES-07 | 200 | 403 | feature gate 未啟用 |
| SES-08 | 200 | 403 | feature gate 未啟用 |
| SES-09 × 2 | 400 | 403 | feature gate 未啟用 |
| SES-10 | 200 | 401 | `NameError: hdr` |
| SES-11 | 422 | 403 | assert 在 `with` 外，override 已清除 |
| SES-12 × 4 | 200/403 | 403 | feature gate 未啟用 |

---

## 4. Dependency Alignment Findings

### Endpoint 實際依賴

```python
# backend/app/modules/attendance/api.py
from app.core.dependencies import get_actor_with_company

async def list_attendance_sessions(
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    _require_attendance_feature(actor.active_company_id, db)  # Feature Gate
```

### 測試 override 覆蓋對象

```python
# backend/app/tests/utils/auth.py
from app.core.dependencies import get_actor_with_company
from app.main import app

app.dependency_overrides[get_actor_with_company] = lambda: actor
```

**Override 對象正確**：`override_actor_dependency` 覆蓋的是 `get_actor_with_company`，與 production endpoint 依賴一致。

### 問題差異

| 問題 | 根因 |
|------|------|
| SES-01~04、SES-10 完全無 actor | 沒有包在 `override_actor_dependency` 中，`hdr()` 回傳空 dict，無 JWT → 401 |
| SES-05~09、SES-12 的 403 | override 正確但 `CompanyEntitlement(attendance.core)` 未建立，Feature Gate 擋住 |
| SES-11 的 403 | assert 在 `with` 外，override 已 pop，走真實 auth 路徑 |

### Actor 角色對齊

`make_actor(company_id, user_id)` 使用 `role_id="company_admin"`，`Actor.is_admin()` 判斷：
```python
return self.active_role_id.lower() in ("company_admin", "hr_manager")
```
已對齊，不是 403 原因。

---

## 5. Fix Applied

### Patch 1：加入 `CompanyEntitlement` import
```python
from app.modules.tenants.models import Tenant, CompanyEntitlement
from app.core.features import FeatureKeys
```

### Patch 2：加入 `hdr()` stub + `make_entitlement()` helper
```python
def hdr(company_id, user_id):
    """Legacy header helper stub (WP-C1-07: JWT actor migration).
    Returns empty dict; actual auth handled by override_actor_dependency.
    """
    return {}

def make_entitlement(db, company_id):
    """Ensure attendance.core feature is enabled for company_id."""
    existing = db.query(CompanyEntitlement).filter(
        CompanyEntitlement.company_id == company_id,
        CompanyEntitlement.feature_key == FeatureKeys.ATTENDANCE_CORE
    ).first()
    if not existing:
        db.add(CompanyEntitlement(
            id=uuid4(),
            company_id=company_id,
            feature_key=FeatureKeys.ATTENDANCE_CORE,
            enabled=True,
        ))
        db.commit()
```

### Patch 3：`tenant_a` fixture 加入 entitlement
```python
def tenant_a(db):
    ...
    make_entitlement(db, COMPANY_A)  # ← 新增
    return t
```

### Patch 4：`tenant_b` fixture 加入 entitlement
```python
def tenant_b(db):
    ...
    make_entitlement(db, COMPANY_B)  # ← 新增
    return t
```

### Patch 5：SES-11 assert 移入 `with` 區塊
```python
# 修正前（assert 在 with 外）
with override_actor_dependency(make_actor(COMPANY_A, user_a.id)):
    resp = client_a.get(...)
assert resp.status_code == 422  # override 已清除！

# 修正後
with override_actor_dependency(make_actor(COMPANY_A, user_a.id)):
    resp = client_a.get(...)
    assert resp.status_code == 422  # override 仍有效
```

### Patch 6~10：SES-01~04、SES-10 包入 `override_actor_dependency`

所有使用 `headers=hdr(...)` 的請求，移除 `headers=hdr(...)` 參數（stub 回傳空 dict），並將 HTTP 請求包入 `with override_actor_dependency(make_actor(COMPANY_A, user_a.id)):` 區塊。

**為何這是最小修正：**
- 不改 production dependency 鏈
- 不重寫 conftest 架構
- 不觸碰其他測試模組
- 每個 patch 都是最小範圍，只補缺失的 actor override 或 feature entitlement

---

## 6. Validation

### 測試命令
```bash
cd /opt/attendance-system && venv/bin/python3 -m pytest \
  backend/app/modules/attendance/tests/test_reporting_sessions.py \
  -v --tb=short
```

### 結果
```
======================= 21 passed, 19 warnings in 17.17s =======================
```

**進度追蹤：**

| 階段 | 結果 |
|------|------|
| 本輪開始前（AttributeError 已修）| 19 failed, 2 passed |
| Patch 1~5（entitlement + hdr stub + SES-11）| 6 failed, 15 passed |
| Patch 6~10（SES-01~04、SES-10 wrap）| **0 failed, 21 passed** ✅ |

---

## 7. Risks / Follow-up

### 可進入 SES-01~SES-12 完整驗收
- **是**。所有 21 個測試現在 pass，測試基礎設施已對齊現行 JWT actor + Feature Gate 架構。

### 遺留問題

| 項目 | 嚴重度 | 說明 |
|------|--------|------|
| `hdr()` stub 仍保留 | 低 | 返回空 dict，功能無害。可在未來整理時移除 | 
| Pydantic V2 deprecation warnings | 低 | `class Config` → `ConfigDict`，不影響功能，非本輪 scope |
| `on_event` deprecation | 低 | FastAPI lifespan handler，非本輪 scope |

### 注意
- `make_actor()` 在測試檔中已存在（SES-11/12 已使用），使用 `role_id="company_admin"`，`is_admin()` 判斷正確。
- `make_entitlement()` 使用 `if not existing` 防重複，測試間安全。
- `override_actor_dependency` 的 finally block 確保 override 離開 context 後自動清除，測試間無污染。
