# WP-10-04A 完成報告

**Date:** 2026-03-03  
**Task:** Login API Contract Lock (JWT) - TDD Red Phase  
**Status:** ✅ Complete

---

## 📋 執行摘要

成功建立 Login API 的不可變合約並完成 TDD red phase（13 個測試全部失敗）。合約已鎖定，測試已定義行為，準備進入 WP-10-04B 實作階段。

---

## 🎯 完成項目

### 1. API Contract 文件（🔒 Locked）

**檔案:** `docs/WP-10-04_LOGIN_API_CONTRACT.md`

**核心定義:**

**Endpoint:**
```
POST /api/internal/auth/login
```

**Request:**
```json
{
  "company_id": "string",
  "login_username": "string",
  "password": "string"
}
```

**Response (Success):**
```json
{
  "access_token": "JWT token",
  "token_type": "bearer",
  "user": {"id": "uuid", "display_name": "string", "email": "string|null"},
  "company": {"id": "string", "name": "string"},
  "role": {"id": "string", "name": "string"}
}
```

**Error Semantics (🔒 Locked):**

| Scenario | Status | Message |
|----------|--------|---------|
| Company not exists | 404 | "Invalid credentials" |
| Membership not exists | 404 | "Invalid credentials" |
| Membership inactive | 404 | "Invalid credentials" |
| Company inactive | 404 | "Invalid credentials" |
| Wrong password | 401 | "Invalid credentials" |
| Missing field | 422 | Validation error |

### 2. TDD Red Phase - 13 Tests

**檔案:** `backend/app/modules/auth/tests/test_login_api.py`

**測試分類:**

**Success Cases (2 tests):**
- ✅ Valid login returns 200 with token
- ✅ JWT token contains required claims

**Anti-Enumeration (4 tests):**
- ✅ Company not exists → 404
- ✅ Membership not exists → 404
- ✅ Membership inactive → 404
- ✅ Company inactive → 404

**Wrong Password (1 test):**
- ✅ Wrong password → 401

**Validation (6 tests):**
- ✅ Missing company_id → 422
- ✅ Missing login_username → 422
- ✅ Missing password → 422
- ✅ Empty company_id → 422
- ✅ Empty login_username → 422
- ✅ Empty password → 422

**Test Results:**
```
13 failed, 2 warnings in 9.33s
✅ All tests failing as expected (TDD red phase)
```

### 3. 文件更新

**更新檔案:**
- ✅ `docs/GATE_PROGRESS_TRACKER.md` - 新增 WP-10-04A 狀態

---

## 🔑 關鍵設計決策

### 1. 為什麼 company_id + login_username？

**Rationale:**
- Platform-first v2: `login_username` 是 per-company（不是 global）
- User 先選擇 company，再輸入 username
- 對應 `user_company_memberships.login_username`

**Why NOT email?**
- Email 僅用於通知（不唯一，不用於登入）
- 防止 email 枚舉攻擊
- 符合 AUTH_SCHEMA_SPEC_PLATFORM_FIRST_v2.md

### 2. Anti-Enumeration 策略

**統一錯誤訊息:**
- Company 不存在 → 404 "Invalid credentials"
- Membership 不存在 → 404 "Invalid credentials"
- Membership 非 active → 404 "Invalid credentials"
- Password 錯誤 → 401 "Invalid credentials"

**Why?**
- 攻擊者無法區分：
  - Company 是否存在
  - Username 是否存在
  - 只是密碼錯誤
- 縮小攻擊面

### 3. JWT Payload

**Required Claims:**
```json
{
  "sub": "user_id (uuid)",
  "company_id": "string",
  "role_id": "string",
  "exp": 1234567890,
  "iat": 1234567890
}
```

**Configuration:**
- Algorithm: HS256
- Expiry: 15 minutes (900 seconds)
- Secret: From `JWT_SECRET_KEY` env var

---

## 📊 TDD Red Phase 驗證

**測試執行結果:**
```bash
$ pytest app/modules/auth/tests/test_login_api.py -v

13 failed, 2 warnings in 9.33s

FAILED test_valid_login_returns_200_with_token
FAILED test_jwt_token_contains_required_claims
FAILED test_company_not_exists_returns_404
FAILED test_membership_not_exists_returns_404
FAILED test_membership_inactive_returns_404
FAILED test_company_inactive_returns_404
FAILED test_wrong_password_returns_401
FAILED test_missing_company_id_returns_422
FAILED test_missing_login_username_returns_422
FAILED test_missing_password_returns_422
FAILED test_empty_company_id_returns_422
FAILED test_empty_login_username_returns_422
FAILED test_empty_password_returns_422
```

**✅ 所有測試正確失敗（endpoint 尚未實作）**

---

## 📁 檔案清單

**新增:**
- `docs/WP-10-04_LOGIN_API_CONTRACT.md` (API 合約，已鎖定)
- `backend/app/modules/auth/tests/test_login_api.py` (13 tests)
- `docs/WP-10-03B_COMPLETION_REPORT.md` (前一個 WP 報告)

**修改:**
- `docs/GATE_PROGRESS_TRACKER.md` (新增 WP-10-04A)

---

## ✅ 驗收標準達成

### Contract Lock
- [x] API endpoint 定義完整
- [x] Request/Response schema 明確
- [x] Error semantics 鎖定（anti-enumeration）
- [x] JWT payload 規格定義

### TDD Red Phase
- [x] 13 個測試全部編寫完成
- [x] 測試覆蓋所有場景（success, error, validation）
- [x] 所有測試正確失敗（endpoint 未實作）

### Documentation
- [x] Contract 文件完整
- [x] GATE_PROGRESS_TRACKER.md 更新
- [x] 設計決策有明確 rationale

---

## 🚫 Stop Condition

**已完成:**
- ✅ 文件完成（Contract locked）
- ✅ 測試寫好（TDD red phase）

**未開始（按計劃）:**
- ❌ Production handler 實作（留給 WP-10-04B）
- ❌ JWT utilities 實作（留給 WP-10-04B）
- ❌ Pydantic schemas 實作（留給 WP-10-04B）

---

## 🚀 下一步

**WP-10-04B — Login API Implementation (TDD Green Phase)**

**需要實作:**
1. `backend/app/modules/auth/schemas.py` - Pydantic models
2. `backend/app/modules/auth/service.py` - Business logic
3. `backend/app/modules/auth/api.py` - FastAPI endpoint
4. `backend/app/core/security/jwt.py` - JWT utilities
5. Register router in `backend/app/main.py`

**目標:** 讓所有 13 個測試通過（TDD green phase）

---

## 📊 Git Commit

```
Commit: 59a97d7
Files: 8 files changed, 987 insertions(+)
Message: docs(auth): lock login API contract and add tests (WP-10-04A)
```

---

**WP-10-04A 完成！準備進入 WP-10-04B（實作階段）** 🎉

**Contract Status:** 🔒 Locked  
**Test Status:** 🔴 Red (13 failed - as expected)  
**Next:** 🟢 Green (Implementation)
