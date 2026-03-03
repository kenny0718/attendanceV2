# WP-10-04 Login API Contract (Locked)

**Version:** 1.0  
**Date:** 2026-03-03  
**Status:** 🔒 Locked (不可變更)  
**Purpose:** 定義 Gate 4 登入 API 的不可變合約

---

## 🔒 Contract Lock

此文件定義的 API 合約在 Gate 4 完成前**不可變更**。任何變更需要：
1. 建立 DECISION 文件
2. 更新所有相關測試
3. 獲得明確批准

---

## 1. Endpoint

### POST /api/internal/auth/login

**Path:** `/api/internal/auth/login`  
**Method:** `POST`  
**Content-Type:** `application/json`  
**Authentication:** None (public endpoint)

**Rationale:**
- `/api/internal/` prefix: 內部 API（非對外公開）
- `/auth/login`: 標準 RESTful 命名

---

## 2. Request Schema

### Request Body (JSON)

```json
{
  "company_id": "string",
  "login_username": "string",
  "password": "string"
}
```

### Field Specifications

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `company_id` | string | ✅ Yes | Non-empty, max 255 chars | Company ID (tenant selector) |
| `login_username` | string | ✅ Yes | Non-empty, max 100 chars | Per-company login username |
| `password` | string | ✅ Yes | Non-empty, max 255 chars | Plain text password |

### Design Rationale

**Why company_id + login_username?**
- Platform-first v2: login_username is per-company (not global)
- User selects company first, then enters username
- Aligns with `user_company_memberships.login_username`

**Why NOT email?**
- Email is for notifications only (not unique, not for login)
- Prevents email enumeration attacks
- Aligns with AUTH_SCHEMA_SPEC_PLATFORM_FIRST_v2.md

**Why plain password in request?**
- HTTPS encrypts transport layer
- Server hashes password (never stores plaintext)
- Standard practice for login APIs

---

## 3. Response Schema (Success)

### HTTP 200 OK

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "display_name": "string",
    "email": "string | null"
  },
  "company": {
    "id": "string",
    "name": "string"
  },
  "role": {
    "id": "string",
    "name": "string"
  }
}
```

### Field Specifications

| Field | Type | Description |
|-------|------|-------------|
| `access_token` | string | JWT access token |
| `token_type` | string | Always "bearer" |
| `user.id` | uuid | User ID (global identity) |
| `user.display_name` | string | User display name |
| `user.email` | string \| null | User email (optional) |
| `company.id` | string | Company ID |
| `company.name` | string | Company name |
| `role.id` | string | Role ID (e.g., "employee", "manager") |
| `role.name` | string | Role display name |

### JWT Payload (access_token)

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

**Optional Claims:**

```json
{
  "display_name": "string",
  "email": "string | null"
}
```

**JWT Configuration:**
- Algorithm: HS256 (HMAC with SHA-256)
- Expiry: 15 minutes (900 seconds)
- Secret: From environment variable `JWT_SECRET_KEY`

---

## 4. Error Semantics (🔒 Locked)

### 4.1 Anti-Enumeration Strategy

**Core Principle:** 統一回應，不洩漏 company/membership 存在性

| Scenario | HTTP Status | Response | Rationale |
|----------|-------------|----------|-----------|
| Company not exists | 404 | `{"detail": "Invalid credentials"}` | Anti-enumeration |
| Membership not exists | 404 | `{"detail": "Invalid credentials"}` | Anti-enumeration |
| Membership inactive | 404 | `{"detail": "Invalid credentials"}` | Anti-enumeration |
| Password incorrect | 401 | `{"detail": "Invalid credentials"}` | Standard auth error |
| Missing field | 422 | `{"detail": [...]}` | Validation error |
| Invalid JSON | 422 | `{"detail": "Invalid JSON"}` | Validation error |

### 4.2 Error Response Examples

#### 404 Not Found (Anti-Enumeration)

```json
{
  "detail": "Invalid credentials"
}
```

**Triggers:**
- Company does not exist
- Membership does not exist (user not in company)
- Membership is inactive

**Why 404 instead of 401?**
- 401 implies "authentication failed" (user exists but wrong password)
- 404 implies "resource not found" (ambiguous: company? membership?)
- Attacker cannot distinguish between scenarios

#### 401 Unauthorized (Wrong Password)

```json
{
  "detail": "Invalid credentials"
}
```

**Triggers:**
- Membership exists and active
- Password is incorrect

**Why same message as 404?**
- Prevents timing attacks
- Prevents enumeration of valid usernames
- Standard security practice

#### 422 Unprocessable Entity (Validation Error)

```json
{
  "detail": [
    {
      "loc": ["body", "company_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Triggers:**
- Missing required field
- Invalid field type
- Invalid JSON format

---

## 5. Authentication Flow

### 5.1 Login Flow (Locked)

```
1. Client sends POST /api/internal/auth/login
   {
     "company_id": "company-A",
     "login_username": "john.doe",
     "password": "SecurePass123!"
   }

2. Server validates request schema
   - Missing field → 422

3. Server checks company exists
   - Not exists → 404 "Invalid credentials"

4. Server checks company is active
   - Not active → 404 "Invalid credentials"

5. Server queries membership by (company_id, login_username)
   - Not found → 404 "Invalid credentials"
   - Inactive → 404 "Invalid credentials"

6. Server verifies password
   - Incorrect → 401 "Invalid credentials"

7. Server generates JWT token
   - Claims: sub, company_id, role_id, exp, iat

8. Server returns 200 with token + user info
```

### 5.2 Security Considerations

**Timing Attack Prevention:**
- Always hash password (even if membership not found)
- Use constant-time comparison for password verification
- Consistent response time across error scenarios

**Rate Limiting (Future):**
- Limit login attempts per IP
- Limit login attempts per username
- Exponential backoff on failures

**Password Policy (Future):**
- Minimum length: 8 characters
- Complexity requirements: TBD
- Password expiry: TBD

---

## 6. Test Cases (Locked)

### 6.1 Success Cases

| Test Case | Input | Expected Output |
|-----------|-------|-----------------|
| Valid login | Valid company + username + password | 200 + JWT token |
| JWT contains claims | Valid login | Token has sub, company_id, role_id |
| User info returned | Valid login | Response has user, company, role |

### 6.2 Error Cases (Anti-Enumeration)

| Test Case | Input | Expected Output |
|-----------|-------|-----------------|
| Company not exists | Invalid company_id | 404 "Invalid credentials" |
| Membership not exists | Valid company, invalid username | 404 "Invalid credentials" |
| Membership inactive | Valid company + username, inactive membership | 404 "Invalid credentials" |
| Wrong password | Valid company + username, wrong password | 401 "Invalid credentials" |

### 6.3 Validation Cases

| Test Case | Input | Expected Output |
|-----------|-------|-----------------|
| Missing company_id | No company_id | 422 validation error |
| Missing login_username | No login_username | 422 validation error |
| Missing password | No password | 422 validation error |
| Invalid JSON | Malformed JSON | 422 "Invalid JSON" |

---

## 7. Implementation Checklist

### 7.1 Backend (WP-10-04B)

- [ ] Create `backend/app/modules/auth/api.py`
- [ ] Create `backend/app/modules/auth/schemas.py` (Pydantic models)
- [ ] Create `backend/app/modules/auth/service.py` (business logic)
- [ ] Create `backend/app/core/security/jwt.py` (JWT utilities)
- [ ] Register router in `backend/app/main.py`

### 7.2 Tests (WP-10-04A)

- [ ] Create `backend/app/modules/auth/tests/test_login_api.py`
- [ ] Implement all test cases from Section 6
- [ ] Tests should FAIL initially (TDD red phase)

### 7.3 Documentation

- [ ] Update `GATE_PROGRESS_TRACKER.md`
- [ ] Create `WP-10-04_COMPLETION_REPORT.md` (after implementation)

---

## 8. Non-Goals (Out of Scope)

**Not in WP-10-04:**
- ❌ Refresh token mechanism
- ❌ Token revocation / blacklist
- ❌ Multi-factor authentication (MFA)
- ❌ Password reset flow
- ❌ OAuth / SSO integration
- ❌ Rate limiting
- ❌ CAPTCHA

**Future WPs:**
- WP-10-05: RBAC Logic + Permission Checks
- WP-10-06: Auth Transition (Migrate existing endpoints)
- WP-10-07: Refresh Token (if needed)

---

## 9. Breaking Changes Policy

**This contract is LOCKED for Gate 4.**

Any proposed changes must:
1. Create `docs/DECISIONS/DECISION_LOGIN_API_CHANGE_<date>.md`
2. Document rationale and impact
3. Update all tests
4. Get explicit approval
5. Update this document version

**Version History:**
- v1.0 (2026-03-03): Initial locked contract

---

**Document End**

**Status:** 🔒 Locked  
**Next:** WP-10-04A (Write tests first - TDD red phase)
