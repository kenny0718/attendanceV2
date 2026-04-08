# 🔒 Gate 5 Boundary Rules

**Gate:** 5 (Attendance Core APIs)  
**Depends On:** Gate 4 (Auth - FROZEN)  
**Created:** 2026-03-03  
**Status:** Active

---

## ⚠️ CRITICAL WARNING

**🔒 Gate 4 Auth is FROZEN.**

All authentication, authorization schema, and security rules from Gate 4 are **immutable**.

Gate 5 development **MUST NOT** modify any Gate 4 frozen components.

**Violation will result in code review rejection.**

See: `docs/GATE_4_AUTH_DECISION_FREEZE.md` for frozen components.

---

## 1. Gate 5 Scope

### 1.1 What Gate 5 WILL Implement

**Attendance Core APIs:**
- ✅ Attendance record CRUD operations
- ✅ Approval workflow
- ✅ Attendance reports and queries
- ✅ Business logic for attendance rules
- ✅ Integration with existing event bus
- ✅ Tenant-isolated attendance data

**Key Deliverables:**
- Attendance API endpoints
- Attendance service layer
- Attendance repository
- Attendance models (if needed)
- Attendance tests
- API documentation

### 1.2 What Gate 5 WILL NOT Touch

**Frozen Components (Gate 4):**
- ❌ Auth schema (users, memberships, roles)
- ❌ Login API
- ❌ JWT generation/validation
- ❌ Password hashing
- ❌ Anti-enumeration logic
- ❌ Tenant context validation

---

## 2. Gate 4 Frozen Components (DO NOT MODIFY)

### 2.1 Schema (FROZEN - DO NOT MODIFY)

**Tables that MUST NOT be modified:**

```sql
-- FROZEN: Do not alter these tables
users
roles
permissions
role_permissions
user_company_memberships
```

**Forbidden Actions:**
- ❌ Add columns to auth tables
- ❌ Remove columns from auth tables
- ❌ Modify constraints (UNIQUE, FK)
- ❌ Change indexes
- ❌ Rename auth tables

**If you need to reference users:**
- ✅ Use FK to `users.id` (read-only reference)
- ✅ Store user_id in your attendance tables
- ❌ Do NOT duplicate user data
- ❌ Do NOT add user fields to attendance tables

### 2.2 API Endpoints (FROZEN - DO NOT MODIFY)

**Frozen Endpoints:**
```
POST /api/internal/auth/login
```

**Forbidden Actions:**
- ❌ Modify login endpoint
- ❌ Change request/response schema
- ❌ Modify error messages
- ❌ Change HTTP status codes
- ❌ Add parameters to login

**If you need authentication:**
- ✅ Use existing login endpoint
- ✅ Accept JWT tokens from clients
- ✅ Validate JWT using existing utilities
- ❌ Do NOT create alternative login methods

### 2.3 JWT Contract (FROZEN - DO NOT MODIFY)

**Frozen JWT Payload:**
```json
{
  "sub": "user_id",
  "company_id": "string",
  "role_id": "string",
  "iat": 1234567890,
  "exp": 1234568790
}
```

**Forbidden Actions:**
- ❌ Add claims to JWT
- ❌ Remove claims from JWT
- ❌ Change claim names
- ❌ Modify JWT expiry
- ❌ Change JWT algorithm

**If you need JWT validation:**
- ✅ Use `app.core.security.jwt.decode_access_token()`
- ✅ Read claims (sub, company_id, role_id)
- ❌ Do NOT modify JWT utilities
- ❌ Do NOT create custom JWT logic

### 2.4 Security Rules (FROZEN - DO NOT MODIFY)

**Anti-Enumeration (CRITICAL):**

All error responses that could reveal system state MUST remain unchanged:

```python
# FROZEN: Do not modify these error messages
404 -> "Invalid credentials"  # For auth failures
403 -> "Forbidden"            # For permission denials
```

**Forbidden Actions:**
- ❌ Change error messages
- ❌ Add detailed error information
- ❌ Return different errors for different scenarios
- ❌ Expose internal state in errors

**If you need error handling:**
- ✅ Use generic error messages for attendance
- ✅ Follow same anti-enumeration principles
- ❌ Do NOT reveal tenant existence
- ❌ Do NOT reveal user existence

### 2.5 Code Files (FROZEN - DO NOT MODIFY)

**Files that MUST NOT be modified:**

```
backend/app/modules/auth/models.py          # FROZEN
backend/app/modules/auth/repo.py            # FROZEN
backend/app/modules/auth/service.py         # FROZEN
backend/app/modules/auth/api.py             # FROZEN
backend/app/modules/auth/schemas.py         # FROZEN
backend/app/core/security/jwt.py            # FROZEN
backend/app/core/security/password.py       # FROZEN
backend/app/core/tenant_context.py          # FROZEN (read-only use OK)
```

**Exception:**
- ✅ You MAY import from these files (read-only)
- ❌ You MUST NOT modify these files

---

## 3. What Gate 5 MAY Use (Read-Only)

### 3.1 Membership Validation ✅

**You SHOULD use tenant context with membership validation:**

```python
from app.core.tenant_context import get_current_company_id_with_membership

@router.post("/api/attendance/records")
async def create_attendance(
    company_id: str = Depends(get_current_company_id_with_membership),
    db: Session = Depends(get_db)
):
    # company_id is validated with membership
    # User has active membership in this company
    pass
```

**Benefits:**
- ✅ Automatic membership validation
- ✅ Anti-enumeration protection
- ✅ Tenant isolation enforced

**Rules:**
- ✅ Use `get_current_company_id_with_membership()` for new endpoints
- ✅ Use `get_current_company_id()` for backward compatibility only
- ❌ Do NOT bypass membership validation
- ❌ Do NOT create custom validation logic

### 3.2 JWT Claims ✅

**You MAY read JWT claims for authorization:**

```python
from app.core.security.jwt import decode_access_token

# Example: Check user role
token = request.headers.get("Authorization").replace("Bearer ", "")
claims = decode_access_token(token)

user_id = claims["sub"]
company_id = claims["company_id"]
role_id = claims["role_id"]

# Use for authorization decisions
if role_id == "manager":
    # Allow approval
    pass
```

**Rules:**
- ✅ Read claims for authorization
- ✅ Use sub (user_id) for audit trails
- ✅ Use company_id for tenant context
- ✅ Use role_id for RBAC (future)
- ❌ Do NOT modify claims
- ❌ Do NOT create new tokens

### 3.3 Auth Repository ✅

**You MAY use auth repository for read-only queries:**

```python
from app.modules.auth.repo import AuthRepository

# Example: Get user info for display
auth_repo = AuthRepository(db)
user = auth_repo.get_user_by_id(user_id)
membership = auth_repo.get_membership(user_id, company_id)

# Use for display/audit only
```

**Rules:**
- ✅ Read user information
- ✅ Read membership information
- ✅ Check user_has_company_access()
- ❌ Do NOT create users (use auth API)
- ❌ Do NOT modify users
- ❌ Do NOT create memberships

### 3.4 Tenant Context ✅

**You MUST use tenant context for all company-scoped operations:**

```python
from app.core.tenant_context import get_current_company_id_with_membership

# All attendance endpoints MUST use this
@router.get("/api/attendance/records")
async def list_attendance(
    company_id: str = Depends(get_current_company_id_with_membership),
    db: Session = Depends(get_db)
):
    # Guaranteed: user has active membership in company_id
    records = attendance_repo.get_by_company(company_id)
    return records
```

**Rules:**
- ✅ Use for ALL company-scoped endpoints
- ✅ Trust the validated company_id
- ✅ Use for tenant isolation
- ❌ Do NOT bypass tenant context
- ❌ Do NOT accept company_id from request body

---

## 4. Gate 5 Development Guidelines

### 4.1 Database Schema

**Creating Attendance Tables:**

```sql
-- ALLOWED: Create new tables for attendance
CREATE TABLE attendance_records (
    id UUID PRIMARY KEY,
    company_id VARCHAR(255) NOT NULL REFERENCES tenants(id),
    user_id UUID NOT NULL REFERENCES users(id),  -- FK to frozen table (OK)
    -- ... attendance fields ...
    
    -- Tenant isolation
    CONSTRAINT fk_attendance_company FOREIGN KEY (company_id) 
        REFERENCES tenants(id) ON DELETE CASCADE
);

-- REQUIRED: Index for tenant isolation
CREATE INDEX idx_attendance_company 
    ON attendance_records(company_id);
```

**Rules:**
- ✅ Create new tables for attendance domain
- ✅ Reference users.id via FK (read-only)
- ✅ Reference tenants.id via FK
- ✅ Add company_id to all tenant-scoped tables
- ✅ Add indexes for (company_id, ...)
- ❌ Do NOT modify auth tables
- ❌ Do NOT duplicate user data

### 4.2 API Design

**Endpoint Pattern:**

```python
# CORRECT: Use tenant context
@router.post("/api/attendance/records")
async def create_attendance(
    request: AttendanceCreateRequest,
    company_id: str = Depends(get_current_company_id_with_membership),
    db: Session = Depends(get_db)
):
    # company_id from dependency (validated)
    # NOT from request body
    pass

# WRONG: Accept company_id from body
@router.post("/api/attendance/records")
async def create_attendance(
    request: AttendanceCreateRequest,  # contains company_id
    db: Session = Depends(get_db)
):
    # SECURITY RISK: No validation
    company_id = request.company_id  # ❌ WRONG
    pass
```

**Rules:**
- ✅ Use `Depends(get_current_company_id_with_membership)`
- ✅ Company_id from dependency injection
- ✅ Follow RESTful conventions
- ❌ Do NOT accept company_id from request body
- ❌ Do NOT bypass tenant context

### 4.3 Error Handling

**Follow Anti-Enumeration Principles:**

```python
# CORRECT: Generic error
if not attendance_record:
    raise HTTPException(
        status_code=404,
        detail="Attendance record not found"
    )

# WRONG: Reveals internal state
if not attendance_record:
    raise HTTPException(
        status_code=404,
        detail=f"Attendance record {record_id} does not exist in company {company_id}"
    )
```

**Rules:**
- ✅ Use generic error messages
- ✅ Return 404 for not found
- ✅ Return 403 for permission denied
- ❌ Do NOT reveal tenant existence
- ❌ Do NOT reveal user existence
- ❌ Do NOT expose internal IDs in errors

### 4.4 Testing

**Test Requirements:**

```python
# REQUIRED: Test with tenant context
def test_create_attendance_with_membership(db, test_tenant, seed_roles):
    # Setup: Create user + membership
    auth_repo = AuthRepository(db)
    user = auth_repo.create_user(...)
    membership = auth_repo.create_membership(...)
    
    # Test: Use tenant context
    response = client.post(
        "/api/attendance/records",
        headers={"X-Company-ID": "company-A", "X-User-ID": str(user.id)},
        json={...}
    )
    
    assert response.status_code == 200

# REQUIRED: Test without membership (should fail)
def test_create_attendance_without_membership(db, test_tenant):
    response = client.post(
        "/api/attendance/records",
        headers={"X-Company-ID": "company-A", "X-User-ID": "random-uuid"},
        json={...}
    )
    
    assert response.status_code == 404  # No membership
```

**Rules:**
- ✅ Test with valid membership
- ✅ Test without membership (should fail)
- ✅ Test tenant isolation
- ✅ Test regression (don't break auth tests)
- ❌ Do NOT mock tenant context
- ❌ Do NOT bypass membership validation in tests

---

## 5. Integration Points

### 5.1 User References

**How to reference users in attendance:**

```python
# CORRECT: Store user_id, query when needed
class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey('users.id'), nullable=False)
    # ... other fields ...

# Query user info when needed
def get_attendance_with_user(record_id, db):
    record = db.query(AttendanceRecord).filter_by(id=record_id).first()
    user = db.query(User).filter_by(id=record.user_id).first()
    
    return {
        "record": record,
        "user": {
            "id": user.id,
            "display_name": user.display_name
        }
    }
```

**Rules:**
- ✅ Store user_id as FK
- ✅ Query User table when needed
- ✅ Use display_name for UI
- ❌ Do NOT duplicate user data
- ❌ Do NOT store username (doesn't exist)
- ❌ Do NOT store email in attendance tables

### 5.2 Role-Based Logic

**How to check user roles:**

```python
# CORRECT: Use membership.role_id
from app.modules.auth.repo import AuthRepository

def can_approve_attendance(user_id: UUID, company_id: str, db: Session) -> bool:
    auth_repo = AuthRepository(db)
    membership = auth_repo.get_membership(user_id, company_id)
    
    if not membership or not membership.is_active:
        return False
    
    # Check role
    return membership.role_id in ["manager", "company_admin"]
```

**Rules:**
- ✅ Query membership for role
- ✅ Check role_id for authorization
- ✅ Respect is_active flag
- ❌ Do NOT hardcode role logic in attendance
- ❌ Do NOT bypass membership check
- ❌ Do NOT cache roles indefinitely

### 5.3 Audit Trails

**How to log user actions:**

```python
# CORRECT: Use JWT claims for audit
from app.core.security.jwt import decode_access_token

@router.post("/api/attendance/approve")
async def approve_attendance(
    record_id: UUID,
    token: str = Depends(oauth2_scheme),
    company_id: str = Depends(get_current_company_id_with_membership),
    db: Session = Depends(get_db)
):
    # Get user from JWT
    claims = decode_access_token(token)
    user_id = claims["sub"]
    
    # Create audit log
    audit_log = AuditLog(
        action="attendance.approve",
        user_id=user_id,
        company_id=company_id,
        resource_id=record_id,
        timestamp=datetime.utcnow()
    )
    db.add(audit_log)
    
    # ... approval logic ...
```

**Rules:**
- ✅ Use JWT sub for user_id
- ✅ Use company_id from tenant context
- ✅ Log all state changes
- ❌ Do NOT log passwords
- ❌ Do NOT log JWT tokens
- ❌ Do NOT expose audit logs to users

---

## 6. Forbidden Patterns

### 6.1 DO NOT Create Alternative Auth

```python
# ❌ FORBIDDEN: Custom login
@router.post("/api/attendance/login")
async def attendance_login(...):
    # WRONG: Use existing auth API
    pass

# ❌ FORBIDDEN: Bypass membership
@router.get("/api/attendance/records")
async def list_attendance(
    company_id: str,  # From query param
    db: Session = Depends(get_db)
):
    # WRONG: No membership validation
    pass

# ❌ FORBIDDEN: Custom JWT
def create_custom_token(user_id):
    # WRONG: Use existing JWT utilities
    pass
```

### 6.2 DO NOT Modify Auth Schema

```python
# ❌ FORBIDDEN: Add column to users
ALTER TABLE users ADD COLUMN attendance_role VARCHAR(50);

# ❌ FORBIDDEN: Modify membership
ALTER TABLE user_company_memberships 
    DROP CONSTRAINT uq_memberships_company_login;

# ❌ FORBIDDEN: Create user directly
user = User(id=uuid4(), display_name="Test")
db.add(user)  # WRONG: Use auth API
```

### 6.3 DO NOT Bypass Security

```python
# ❌ FORBIDDEN: Skip membership check
@router.get("/api/attendance/records")
async def list_attendance(
    company_id: str,  # No validation
    db: Session = Depends(get_db)
):
    # SECURITY RISK
    pass

# ❌ FORBIDDEN: Detailed errors
if not record:
    raise HTTPException(
        status_code=404,
        detail=f"Record {id} not found in company {company_id}"
    )  # WRONG: Reveals tenant info
```

---

## 7. Checklist for Gate 5 Developers

### Before Starting Development

- [ ] Read `docs/GATE_4_AUTH_DECISION_FREEZE.md`
- [ ] Understand frozen components
- [ ] Review this boundary rules document
- [ ] Understand tenant context usage

### During Development

- [ ] Use `get_current_company_id_with_membership()` for all endpoints
- [ ] Reference users via FK (read-only)
- [ ] Follow anti-enumeration principles
- [ ] Test with and without membership
- [ ] Do NOT modify auth files

### Before Code Review

- [ ] No modifications to frozen files
- [ ] All endpoints use tenant context
- [ ] Tests include membership validation
- [ ] Error messages are generic
- [ ] Regression tests still pass (137/137)

### Code Review Rejection Criteria

**Automatic rejection if:**
- ❌ Modified any frozen file
- ❌ Bypassed membership validation
- ❌ Created alternative auth mechanism
- ❌ Changed error messages (anti-enumeration)
- ❌ Modified auth schema
- ❌ Broke regression tests

---

## 8. Getting Help

### If You Need To...

**...modify auth schema:**
- ❌ STOP: This requires unfreezing Gate 4
- Create decision document first
- Get approval before proceeding

**...add JWT claims:**
- ❌ STOP: JWT contract is frozen
- Consider alternative approaches
- Discuss with tech lead

**...bypass membership validation:**
- ❌ STOP: This is a security violation
- Explain use case to tech lead
- There is likely a better approach

**...change error messages:**
- ❌ STOP: Anti-enumeration is critical
- Review security requirements
- Discuss with security team

### Contact

**Questions about:**
- Frozen components → See `docs/GATE_4_AUTH_DECISION_FREEZE.md`
- Tenant context → See `backend/app/core/tenant_context.py`
- JWT usage → See `backend/app/core/security/jwt.py`
- Membership validation → See `backend/app/modules/auth/repo.py`

---

## 9. Summary

### Gate 5 MUST

- ✅ Use tenant context with membership validation
- ✅ Reference users via FK (read-only)
- ✅ Follow anti-enumeration principles
- ✅ Test tenant isolation
- ✅ Maintain regression tests

### Gate 5 MUST NOT

- ❌ Modify auth schema
- ❌ Modify auth code files
- ❌ Bypass membership validation
- ❌ Create alternative auth
- ❌ Change error semantics

### Gate 5 MAY

- ✅ Create attendance tables
- ✅ Use JWT claims (read-only)
- ✅ Query auth repository (read-only)
- ✅ Implement attendance business logic
- ✅ Add attendance-specific features

---

**Document Version:** 1.0  
**Created:** 2026-03-03  
**Status:** Active  
**Gate 4 Freeze:** `docs/GATE_4_AUTH_DECISION_FREEZE.md`

---

**🔒 Remember: Gate 4 Auth is FROZEN. Do not modify frozen components.**
