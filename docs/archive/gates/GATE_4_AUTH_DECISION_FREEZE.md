# 🔒 Gate 4 Auth Decision Freeze

**Status:** 🔒 **FROZEN**  
**Freeze Date:** 2026-03-03  
**Gate:** 4 (Auth - Platform-First v2)  
**Version:** 1.0 (Immutable)

---

## ⚠️ CRITICAL NOTICE

**🔒 Gate 4 Auth Decisions are FROZEN.**

Any change to the architecture, schema, or security rules defined in this document requires:
1. Creation of a new Decision Document (`docs/DECISIONS/DECISION_AUTH_CHANGE_<date>.md`)
2. Impact analysis on all dependent modules
3. Explicit approval from project lead
4. Update of this document version

**Violation of frozen rules will be rejected in code review.**

---

## 1. Final Architecture Overview

### 1.1 Architecture Diagram (Text-Based)

```
┌─────────────────────────────────────────────────────────────┐
│                    Platform-First v2 Auth                    │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐
│   Client     │
└──────┬───────┘
       │
       │ POST /api/internal/auth/login
       │ { company_id, login_username, password }
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Auth Service (service.py)                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 1. Validate company exists & active                    │  │
│  │ 2. Get membership by (company_id, login_username)      │  │
│  │ 3. Check membership is active                          │  │
│  │ 4. Verify password (bcrypt)                            │  │
│  │ 5. Generate JWT (sub, company_id, role_id)            │  │
│  │ 6. Return token + user/company/role info              │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Database Schema (Platform-First v2)                         │
│                                                              │
│  ┌─────────────────┐         ┌──────────────────────────┐   │
│  │     users       │         │ user_company_memberships │   │
│  ├─────────────────┤         ├──────────────────────────┤   │
│  │ id (PK)         │◄────────│ user_id (FK)             │   │
│  │ display_name    │         │ company_id (FK)          │   │
│  │ email (nullable)│         │ role_id (FK)             │   │
│  │ password_hash   │         │ login_username           │   │
│  │ is_active       │         │ is_active                │   │
│  └─────────────────┘         └──────────────────────────┘   │
│         ▲                              │                     │
│         │                              │                     │
│         │                              ▼                     │
│         │                    ┌──────────────────┐           │
│         │                    │   tenants        │           │
│         │                    ├──────────────────┤           │
│         │                    │ id (PK)          │           │
│         │                    │ name             │           │
│         │                    │ is_active        │           │
│         │                    └──────────────────┘           │
│         │                                                    │
│         │                    ┌──────────────────┐           │
│         └────────────────────│   roles          │           │
│                              ├──────────────────┤           │
│                              │ id (PK)          │           │
│                              │ name             │           │
│                              └──────────────────┘           │
│                                                              │
│  CONSTRAINTS (FROZEN):                                       │
│  • UNIQUE(company_id, login_username)                        │
│  • UNIQUE(user_id, company_id)                               │
│  • NO UNIQUE on users.email                                  │
│  • NO company_id in users table                              │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Key Architectural Principles (FROZEN)

1. **Global User Identity**
   - Users exist independently of companies
   - One user can have memberships in multiple companies
   - User identity is NOT tied to any single tenant

2. **Per-Company Login Credentials**
   - Login username is per-company (via membership)
   - Same user can have different usernames in different companies
   - Email is for notifications only (NOT for login)

3. **Membership-Based Access Control**
   - Access to company requires active membership
   - Membership links: user ↔ company ↔ role
   - No membership = no access (404 response)

4. **Anti-Enumeration Security**
   - All "not found" scenarios return same error
   - Prevents attackers from discovering valid companies/usernames
   - Timing attacks mitigated by constant-time operations

---

## 2. Locked Rules (IMMUTABLE)

### 2.1 Login Flow (FROZEN)

**The ONLY supported login flow:**

```
Step 1: User selects company (company_id)
Step 2: User enters login_username (per-company)
Step 3: User enters password
Step 4: System validates and returns JWT
```

**🔒 LOCKED:** This flow cannot be changed without a new decision document.

**Forbidden alternatives:**
- ❌ Login with email only (no company selector)
- ❌ Login with global username
- ❌ Login with email + password (bypassing company)
- ❌ OAuth/SSO without company context

### 2.2 Email Usage (FROZEN)

**🔒 LOCKED RULE:** Email is for notifications ONLY.

**Allowed:**
- ✅ Send notifications to user.email
- ✅ Email can be NULL
- ✅ Email can be duplicated across users
- ✅ Email can be updated by user

**Forbidden:**
- ❌ Use email as login identifier
- ❌ Make email UNIQUE globally
- ❌ Require email for user creation
- ❌ Use email for authentication

**Rationale:**
- Prevents email enumeration attacks
- Allows users to share email addresses (e.g., company email)
- Simplifies multi-company scenarios

### 2.3 User Table Schema (FROZEN)

**🔒 LOCKED SCHEMA:**

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),  -- nullable, NOT unique
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    -- NO company_id column
    -- NO username column
    ...
);
```

**Forbidden changes:**
- ❌ Add company_id to users table
- ❌ Add username to users table
- ❌ Make email UNIQUE
- ❌ Make email NOT NULL

### 2.4 Membership Table Schema (FROZEN)

**🔒 LOCKED SCHEMA:**

```sql
CREATE TABLE user_company_memberships (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    company_id VARCHAR(255) NOT NULL REFERENCES tenants(id),
    role_id VARCHAR(50) NOT NULL REFERENCES roles(id),
    login_username VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- FROZEN CONSTRAINTS:
    CONSTRAINT uq_memberships_company_login 
        UNIQUE (company_id, login_username),
    CONSTRAINT uq_memberships_user_company 
        UNIQUE (user_id, company_id)
);

-- FROZEN INDEX:
CREATE INDEX idx_memberships_company_login 
    ON user_company_memberships(company_id, login_username);
```

**Forbidden changes:**
- ❌ Remove UNIQUE(company_id, login_username)
- ❌ Remove UNIQUE(user_id, company_id)
- ❌ Remove login_username column
- ❌ Make login_username nullable

### 2.5 JWT Claims Schema (FROZEN)

**🔒 LOCKED JWT PAYLOAD:**

```json
{
  "sub": "user_id (UUID)",
  "company_id": "string",
  "role_id": "string",
  "iat": 1234567890,
  "exp": 1234568790
}
```

**Required claims (cannot be removed):**
- ✅ `sub` - User ID (global identity)
- ✅ `company_id` - Tenant context
- ✅ `role_id` - User's role in this company
- ✅ `iat` - Issued at timestamp
- ✅ `exp` - Expiry timestamp

**JWT Configuration (FROZEN):**
- Algorithm: HS256
- Expiry: 900 seconds (15 minutes)
- Secret: From environment variable `JWT_SECRET_KEY`

**Forbidden changes:**
- ❌ Remove any required claim
- ❌ Change algorithm without security review
- ❌ Hardcode JWT secret
- ❌ Increase expiry beyond 1 hour without review

---

## 3. Security Invariants (MUST NEVER BE VIOLATED)

### 3.1 Anti-Enumeration (CRITICAL)

**🔒 FROZEN RULE:** All authentication failures that could reveal system state MUST return the same error.

**Error Semantics (IMMUTABLE):**

| Scenario | HTTP Status | Response | Rationale |
|----------|-------------|----------|-----------|
| Company not exists | 404 | "Invalid credentials" | Hide company existence |
| Membership not exists | 404 | "Invalid credentials" | Hide username validity |
| Membership inactive | 404 | "Invalid credentials" | Hide membership state |
| Password incorrect | 401 | "Invalid credentials" | Standard auth error |

**🔒 CRITICAL:** These error responses MUST remain identical to prevent enumeration attacks.

**Forbidden changes:**
- ❌ Return "Company not found" (reveals company existence)
- ❌ Return "User not found" (reveals username validity)
- ❌ Return "Account disabled" (reveals membership state)
- ❌ Different response times for different scenarios

**Implementation requirement:**
- Password verification MUST occur even if membership doesn't exist (timing attack prevention)
- All error paths MUST take similar time to execute

### 3.2 Membership Validation (CRITICAL)

**🔒 FROZEN RULE:** Access to any company resource REQUIRES active membership.

**Validation Flow (IMMUTABLE):**

```
1. Check tenant exists → 404 if not
2. Check tenant is_active → 403 if not
3. Check membership exists → 404 if not
4. Check membership is_active → 404 if not
5. Grant access
```

**Forbidden bypasses:**
- ❌ Allow access without membership check
- ❌ Skip membership validation for "admin" users
- ❌ Cache membership status indefinitely
- ❌ Trust client-provided company_id without validation

**Implementation locations:**
- `tenant_context.py::get_current_company_id_with_membership()`
- `auth/service.py::login()`

### 3.3 Password Security (CRITICAL)

**🔒 FROZEN RULES:**

1. **Hashing Algorithm:** bcrypt (with auto-salt)
2. **Storage:** NEVER store plain passwords
3. **Verification:** Use constant-time comparison
4. **Transmission:** HTTPS only (plain password in request body)

**Forbidden changes:**
- ❌ Store passwords in plain text
- ❌ Use weak hashing (MD5, SHA1, SHA256 without salt)
- ❌ Implement custom crypto (use bcrypt library)
- ❌ Log passwords (even in debug mode)

### 3.4 Unique Constraints (CRITICAL)

**🔒 FROZEN CONSTRAINTS:**

1. **UNIQUE(company_id, login_username)**
   - Prevents duplicate usernames within a company
   - Enables reliable login lookup
   - MUST NOT be removed

2. **UNIQUE(user_id, company_id)**
   - Prevents duplicate memberships
   - Ensures one role per user per company
   - MUST NOT be removed

**Forbidden changes:**
- ❌ Remove these constraints
- ❌ Make them non-unique indexes
- ❌ Add exceptions or bypass logic

---

## 4. Forbidden Future Changes

### 4.1 Schema Changes (FORBIDDEN)

**❌ DO NOT:**

1. **Add company_id to users table**
   - Violates global user identity principle
   - Breaks multi-company support
   - Requires full architecture rewrite

2. **Add username to users table**
   - Violates per-company username principle
   - Conflicts with membership.login_username
   - Breaks tenant isolation

3. **Make email UNIQUE globally**
   - Prevents email sharing across users
   - Breaks legitimate use cases (shared company emails)
   - Enables email enumeration attacks

4. **Remove user_company_memberships table**
   - Breaks entire platform-first architecture
   - No alternative for multi-company support

### 4.2 API Changes (FORBIDDEN)

**❌ DO NOT:**

1. **Add email-based login endpoint**
   - Bypasses company selector
   - Enables email enumeration
   - Violates frozen login flow

2. **Remove company_id from login request**
   - Breaks tenant isolation
   - Requires global username uniqueness
   - Violates architecture principles

3. **Change error messages to be more specific**
   - Breaks anti-enumeration
   - Security vulnerability
   - Violates frozen error semantics

4. **Add "remember me" without security review**
   - Extends token lifetime
   - Requires new security analysis
   - May violate compliance requirements

### 4.3 Security Changes (FORBIDDEN)

**❌ DO NOT:**

1. **Bypass membership validation**
   - Even for "admin" or "support" users
   - Creates security backdoor
   - Violates tenant isolation

2. **Cache membership indefinitely**
   - Stale data security risk
   - User may lose access but still authenticated
   - Max cache: 5 minutes (if implemented)

3. **Remove anti-enumeration protections**
   - Security regression
   - Enables reconnaissance attacks
   - Violates frozen security invariants

4. **Hardcode JWT secret**
   - Security vulnerability
   - Prevents secret rotation
   - Violates configuration principles

---

## 5. Allowed Future Enhancements

### 5.1 Additive Changes (ALLOWED)

**✅ These changes are ALLOWED without unfreezing:**

1. **Add refresh token mechanism**
   - Does not change login flow
   - Additive feature
   - Requires new endpoint

2. **Add password reset flow**
   - Does not change authentication
   - Additive feature
   - Must maintain anti-enumeration

3. **Add MFA/2FA**
   - Enhances security
   - Does not change core flow
   - Requires new decision document for implementation

4. **Add OAuth/SSO**
   - Must preserve company_id requirement
   - Must create membership on first login
   - Requires new decision document

5. **Add rate limiting**
   - Security enhancement
   - Does not change API contract
   - Recommended implementation

6. **Add audit logging**
   - Security enhancement
   - Does not change functionality
   - Must not log passwords

### 5.2 Configuration Changes (ALLOWED)

**✅ These can be changed via configuration:**

1. JWT expiry time (within 15min - 1hour range)
2. Password complexity requirements
3. Rate limiting thresholds
4. Session timeout values
5. Bcrypt work factor (cost parameter)

**⚠️ Requires security review:**
- JWT expiry > 1 hour
- Weaker password requirements
- Disabling rate limiting

---

## 6. Migration Path (If Unfreeze Required)

### 6.1 When to Unfreeze

**Valid reasons to unfreeze Gate 4 decisions:**

1. **Security vulnerability discovered**
   - Critical security flaw in architecture
   - New attack vector identified
   - Compliance requirement change

2. **Business requirement change**
   - Fundamental business model shift
   - Legal/regulatory requirement
   - Acquisition/merger scenario

3. **Technology obsolescence**
   - bcrypt deprecated (unlikely)
   - JWT standard updated
   - Database technology change

### 6.2 Unfreeze Process

**Required steps:**

1. **Create Decision Document**
   - File: `docs/DECISIONS/DECISION_AUTH_UNFREEZE_<date>.md`
   - Include: Rationale, impact analysis, migration plan

2. **Impact Analysis**
   - List all affected modules
   - Estimate migration effort
   - Identify breaking changes

3. **Approval Process**
   - Technical lead review
   - Security review
   - Project stakeholder approval

4. **Migration Plan**
   - Backward compatibility strategy
   - Data migration scripts
   - Rollback plan

5. **Update This Document**
   - Increment version (2.0)
   - Document changes
   - Update freeze date

---

## 7. Compliance & Audit

### 7.1 Audit Trail

**All changes to frozen components must be logged:**

| Date | Component | Change | Reason | Approver |
|------|-----------|--------|--------|----------|
| 2026-03-03 | Initial | Gate 4 frozen | Baseline | System |

### 7.2 Review Schedule

**Frozen decisions should be reviewed:**
- Annually (security review)
- After major incidents
- Before major releases
- When new compliance requirements emerge

### 7.3 Compliance Notes

**This architecture supports:**
- ✅ GDPR (data isolation per tenant)
- ✅ SOC 2 (audit trails, access control)
- ✅ Multi-tenancy (tenant isolation)
- ✅ Security best practices (anti-enumeration, bcrypt)

---

## 8. References

### 8.1 Source Documents

1. `docs/AUTH_SCHEMA_SPEC_PLATFORM_FIRST_v2.md` - Schema specification
2. `docs/WP-10-04_LOGIN_API_CONTRACT.md` - API contract (locked)
3. `docs/GATE_4_FINAL_VALIDATION_REPORT.md` - Validation results
4. `docs/AUTH_MIGRATION_REWRITE_PLAN_WP-10-02B.md` - Migration plan

### 8.2 Implementation Files

**Schema:**
- `backend/alembic/versions/3532deda024c_*.py` - Migration

**Models:**
- `backend/app/modules/auth/models.py` - User, Membership, Role

**Business Logic:**
- `backend/app/modules/auth/repo.py` - Repository layer
- `backend/app/modules/auth/service.py` - Service layer
- `backend/app/core/tenant_context.py` - Membership validation

**API:**
- `backend/app/modules/auth/api.py` - Login endpoint
- `backend/app/core/security/jwt.py` - JWT utilities
- `backend/app/core/security/password.py` - Password hashing

**Tests:**
- `backend/app/modules/auth/tests/test_login_api.py` - 13 tests

---

## 9. Freeze Metadata

**Freeze Information:**
- **Freeze Date:** 2026-03-03
- **Freeze Version:** 1.0
- **Gate:** 4 (Auth - Platform-First v2)
- **Status:** 🔒 FROZEN
- **Next Review:** 2027-03-03 (annual)

**Frozen Components:**
- Schema: users, user_company_memberships
- API: POST /api/internal/auth/login
- Security: Anti-enumeration, membership validation
- JWT: Claims schema, algorithm, expiry

**Checksum (for integrity):**
- Migration: `3532deda024c`
- Tests: 13 passing
- Regression: 137 passing

---

## 10. Sign-off

**Frozen By:** Automated System  
**Date:** 2026-03-03  
**Gate Status:** CLOSED & FROZEN  
**Validation Report:** `docs/GATE_4_FINAL_VALIDATION_REPORT.md`

**Acknowledgment:**

By proceeding past Gate 4, all developers acknowledge:
1. They have read this freeze document
2. They understand the frozen rules
3. They will not modify frozen components without approval
4. They will create a decision document for any proposed changes

---

**🔒 END OF FROZEN DOCUMENT 🔒**

**Version:** 1.0 (Immutable)  
**Status:** FROZEN  
**Last Updated:** 2026-03-03
