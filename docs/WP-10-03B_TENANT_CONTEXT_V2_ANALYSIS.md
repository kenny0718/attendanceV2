# WP-10-03B: Tenant Context v2 Analysis

**Date:** 2026-03-03  
**Purpose:** 分析現有 tenant_context.py 並設計 platform-first v2 membership 驗證

---

## 1. 現況盤點

### 1.1 tenant_context.py 現有實作

**取得 company_id 方式:**
- 從 HTTP Header `X-Company-ID` 取得
- 必填，缺少則回 400

**現有驗證:**
1. ✅ 驗證 tenant 是否存在（`tenant_repo.exists()`）
2. ✅ 驗證 tenant 是否 active（`tenant_repo.is_active()`）
3. ❌ **未驗證 user 是否有該 company 的 membership**

**現有回應:**
- Tenant 不存在 → 404
- Tenant 非 active → 403

### 1.2 識別的安全漏洞

**漏洞:** 任何 user 只要知道 company_id，就可以存取該公司資料

**原因:** 
- 只驗證 tenant 存在，不驗證 user-company membership
- 缺少 `user_has_company_access(user_id, company_id)` 檢查

**影響範圍:**
- `app/modules/attendance/api.py` - 打卡記錄
- `app/modules/notifications/api.py` - 通知
- `app/modules/backup/api.py` - 備份
- `app/modules/audit/api.py` - 稽核日誌

---

## 2. v2 設計：Membership 驗證

### 2.1 驗證點設計

**Input:**
- `user_id`: 從 Header `X-User-ID` 取得（Phase 1）或從 JWT 取得（Phase 2）
- `company_id`: 從 Header `X-Company-ID` 取得（Phase 1）或從 JWT 取得（Phase 2）

**Check:**
```python
auth_repo.user_has_company_access(user_id, company_id)
```

**Rule:**
- No membership → **Treat as tenant not found** → 404
- Inactive membership → **Treat as tenant not found** → 404

**Rationale (Anti-Enumeration):**
- 不回 403 "Access Denied"（會洩漏 tenant 存在）
- 統一回 404 "Not Found"（無法區分 tenant 不存在 vs 無權限）

### 2.2 404 產生層級

**Layer:** `tenant_context.py` (Dependency Injection Layer)

**Why:**
- 在進入 API handler 前就攔截
- 統一處理，不需每個 endpoint 重複驗證
- 符合 FastAPI Depends 機制

**Flow:**
```
Request → tenant_context.get_current_company_id()
  ↓
  1. Validate tenant exists (existing)
  ↓
  2. Validate tenant is_active (existing)
  ↓
  3. Validate user has membership (NEW)
  ↓
  - No membership → HTTPException 404
  ↓
API Handler (只有有權限的 user 才會到達)
```

---

## 3. 實作策略

### 3.1 最小變更原則

**修改檔案:**
- `backend/app/core/tenant_context.py` - 加入 membership 驗證

**不修改:**
- API routes/controllers（除非文件明確要求）
- 其他模組的業務邏輯

### 3.2 新增函數

```python
def get_current_company_id_with_membership(
    x_company_id: str = Header(..., alias="X-Company-ID"),
    x_user_id: str = Header(..., alias="X-User-ID"),
    db: Session = Depends(get_db)
) -> str:
    """
    取得當前公司 ID（含 membership 驗證）
    
    Phase 1: 從 Header 取得 user_id + company_id
    Phase 2: 從 JWT 取得
    
    驗證順序：
    1. Tenant exists
    2. Tenant is_active
    3. User has membership (NEW)
    
    Returns:
        company_id (str)
    
    Raises:
        HTTPException 404: Tenant not found OR no membership (anti-enumeration)
        HTTPException 403: Tenant not active
    """
```

### 3.3 向後相容

**保留舊函數:**
- `get_current_company_id()` - 不加 membership 驗證（向後相容）

**新函數:**
- `get_current_company_id_with_membership()` - 加 membership 驗證

**Migration Path:**
- 新 API 使用 `get_current_company_id_with_membership()`
- 舊 API 逐步遷移（Phase 2）

---

## 4. 測試策略

### 4.1 新增測試

**檔案:** `backend/app/core/tests/test_tenant_context.py`

**測試案例:**
1. ✅ Valid membership → 200
2. ✅ No membership → 404 (anti-enumeration)
3. ✅ Inactive membership → 404 (anti-enumeration)
4. ✅ Tenant not exists → 404
5. ✅ Tenant not active → 403
6. ✅ Missing X-User-ID → 400
7. ✅ Missing X-Company-ID → 400

### 4.2 Regression Tests

**必須全綠:**
- `pytest app/modules/attendance/tests/ -v`
- `pytest app/modules/notifications/tests/ -v`
- `pytest app/modules/backup/tests/ -v`
- `pytest app/modules/audit/tests/ -v`

---

## 5. Anti-Enumeration 說明

### 5.1 為什麼統一回 404？

**場景 1: 回 403 "Access Denied"**
```
Attacker: X-Company-ID: company-secret
Response: 403 Forbidden
→ Attacker 知道 company-secret 存在，但無權限
→ 可以嘗試其他攻擊（社交工程、釣魚等）
```

**場景 2: 回 404 "Not Found"**
```
Attacker: X-Company-ID: company-secret
Response: 404 Not Found
→ Attacker 無法區分：
  - company-secret 不存在？
  - company-secret 存在但我無權限？
→ 無法確認 tenant 存在性，攻擊面縮小
```

### 5.2 實作細節

**統一 404 回應:**
```python
# No membership
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail={"error": f"Tenant {company_id} not found"}
)

# Tenant not exists (existing)
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail={"error": f"Tenant {company_id} does not exist"}
)
```

**注意:** 兩者 detail message 略有不同，但都是 404，外部無法區分

---

## 6. 驗收標準

### 6.1 Code 驗收

- [ ] `tenant_context.py` 加入 membership 驗證
- [ ] 新增 `get_current_company_id_with_membership()` 函數
- [ ] 保留 `get_current_company_id()` 向後相容

### 6.2 Test 驗收

- [ ] 新增 `test_tenant_context.py` 測試檔案
- [ ] 7 個測試案例全部通過
- [ ] Regression tests 全綠

### 6.3 Documentation 驗收

- [ ] 更新 `GATE_PROGRESS_TRACKER.md`
- [ ] 新增 WP-10-03B 行並標記完成

---

**Document End**
