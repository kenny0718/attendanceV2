# WP-11-02 — Precheck Checklist

**Project**: SaaS Multi-Tenant Attendance System  
**Gate**: 5 (Attendance Core APIs)  
**Work Package**: WP-11-02 — Punch In/Out API  
**Checklist Date**: 2026-03-03  
**Auth Model**: 🔒 FROZEN (Gate 4 closed)

---

## Purpose

This checklist ensures all prerequisites are met before starting WP-11-02 implementation. It identifies critical decisions, risks, and boundary conditions that must be addressed.

---

## Section 1: Endpoint Design Decisions

### 1.1 Punch In Endpoint

**Proposed**: `POST /api/v1/attendance/punch-in`

**Request**:
```json
{
  "notes": "Optional notes"  // Optional
}
```

**Response (Success - 201)**:
```json
{
  "session_id": "uuid",
  "user_id": "uuid",
  "company_id": "string",
  "punch_in_time": "2026-03-03T09:00:00Z",
  "status": "open"
}
```

**Response (Error - 409 Conflict)**:
```json
{
  "error": "User already has an open attendance session",
  "open_session_id": "uuid",
  "punch_in_time": "2026-03-03T08:30:00Z"
}
```

**Decisions Required**:
- [ ] Should `notes` be allowed on punch-in?
- [ ] Should we capture `ip_address`, `user_agent` automatically?
- [ ] Should we support optional `location_lat/lng` in request?
- [ ] Should we create a `punch` record in addition to `session`?

**Recommendation**: 
- ✅ Allow optional `notes`
- ✅ Auto-capture `ip_address`, `user_agent` from request headers
- ✅ Allow optional `location` object in request body
- ✅ Create both `session` and `punch` record (atomic transaction)

---

### 1.2 Punch Out Endpoint

**Proposed**: `POST /api/v1/attendance/punch-out`

**Request**:
```json
{
  "notes": "Optional notes"  // Optional
}
```

**Response (Success - 200)**:
```json
{
  "session_id": "uuid",
  "user_id": "uuid",
  "company_id": "string",
  "punch_in_time": "2026-03-03T09:00:00Z",
  "punch_out_time": "2026-03-03T18:00:00Z",
  "duration_minutes": 540,
  "status": "closed"
}
```

**Response (Error - 404 Not Found)**:
```json
{
  "error": "No open attendance session found"
}
```

**Decisions Required**:
- [ ] Should punch-out require explicit `session_id` or auto-detect open session?
- [ ] Should we allow punch-out for other users (manager override)?
- [ ] Should we validate minimum session duration (e.g., > 1 minute)?

**Recommendation**:
- ✅ Auto-detect open session (no `session_id` in request)
- ❌ No manager override in WP-11-02 (defer to future WP)
- ✅ No minimum duration validation (allow any duration)

---

### 1.3 Current Status Endpoint

**Proposed**: `GET /api/v1/attendance/current-status`

**Response (Open Session - 200)**:
```json
{
  "has_open_session": true,
  "session": {
    "session_id": "uuid",
    "punch_in_time": "2026-03-03T09:00:00Z",
    "elapsed_minutes": 120,
    "status": "open"
  }
}
```

**Response (No Open Session - 200)**:
```json
{
  "has_open_session": false,
  "session": null
}
```

**Decisions Required**:
- [ ] Should we include punch history in this endpoint?
- [ ] Should we include policy information?

**Recommendation**:
- ❌ No punch history (use separate history endpoint)
- ❌ No policy info (defer to WP-11-03)

---

### 1.4 Attendance History Endpoint

**Proposed**: `GET /api/v1/attendance/history`

**Query Parameters**:
- `limit` (default: 50, max: 100)
- `offset` (default: 0)
- `start_date` (optional, ISO 8601)
- `end_date` (optional, ISO 8601)

**Response (200)**:
```json
{
  "sessions": [
    {
      "session_id": "uuid",
      "punch_in_time": "2026-03-02T09:00:00Z",
      "punch_out_time": "2026-03-02T18:00:00Z",
      "duration_minutes": 540,
      "status": "closed"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

**Decisions Required**:
- [ ] Should we include punch details (break_start/break_end)?
- [ ] Should we support filtering by status (open/closed)?

**Recommendation**:
- ❌ No punch details in WP-11-02 (defer to WP-11-04 reports)
- ✅ Support `status` query parameter

---

### 1.5 Break Management (Optional)

**Proposed**: `POST /api/v1/attendance/break-start` and `POST /api/v1/attendance/break-end`

**Decisions Required**:
- [ ] Should WP-11-02 include break management?
- [ ] Or defer to future iteration?

**Recommendation**:
- ❌ Defer break management to future WP (out of scope for WP-11-02)
- Focus on core punch-in/punch-out only

---

## Section 2: Error Handling Rules

### 2.1 Already-Open Session Error

**Scenario**: User tries to punch in when already has open session

**HTTP Status**: 409 Conflict

**Error Response**:
```json
{
  "error": "User already has an open attendance session",
  "error_code": "ALREADY_OPEN_SESSION",
  "open_session_id": "uuid",
  "punch_in_time": "2026-03-03T08:30:00Z"
}
```

**Handling**:
- ✅ Return existing session details
- ✅ Client should display "Already clocked in at 08:30" message
- ✅ Client can offer "Clock out" action

---

### 2.2 No-Open Session Error

**Scenario**: User tries to punch out when no open session exists

**HTTP Status**: 404 Not Found

**Error Response**:
```json
{
  "error": "No open attendance session found",
  "error_code": "NO_OPEN_SESSION"
}
```

**Handling**:
- ✅ Return generic error (no session details)
- ✅ Client should display "You haven't clocked in yet" message
- ✅ Client can offer "Clock in" action

---

### 2.3 Invalid Break Error (Future)

**Scenario**: User tries to start break when no open session

**HTTP Status**: 400 Bad Request

**Error Response**:
```json
{
  "error": "Cannot start break without an open session",
  "error_code": "INVALID_BREAK_STATE"
}
```

**Note**: Deferred to future WP (break management out of scope for WP-11-02)

---

### 2.4 Tenant Not Found Error

**Scenario**: JWT contains invalid `company_id`

**HTTP Status**: 404 Not Found

**Error Response**:
```json
{
  "error": "Tenant not found",
  "error_code": "TENANT_NOT_FOUND"
}
```

**Handling**:
- ✅ Use existing `tenant_context.get_current_company_id()` validation
- ✅ Anti-enumeration: Same error for "not found" and "no access"

---

### 2.5 Unauthorized Error

**Scenario**: Missing or invalid JWT

**HTTP Status**: 401 Unauthorized

**Error Response**:
```json
{
  "error": "Authentication required",
  "error_code": "UNAUTHORIZED"
}
```

**Handling**:
- ✅ Use frozen auth middleware (no modifications)
- ✅ JWT validation happens before endpoint logic

---

### 2.6 Forbidden Error

**Scenario**: User tries to access other user's attendance data

**HTTP Status**: 403 Forbidden

**Error Response**:
```json
{
  "error": "Access denied",
  "error_code": "FORBIDDEN"
}
```

**Handling**:
- ✅ Enforce `user_id` from JWT (cannot be overridden)
- ✅ Users can only access their own attendance data

---

## Section 3: Race Condition Risks

### 3.1 Concurrent Punch-In

**Risk**: Two simultaneous punch-in requests from same user

**Scenario**:
```
T1: Request A checks open session → None
T2: Request B checks open session → None
T3: Request A creates session → Success
T4: Request B creates session → IntegrityError
```

**Mitigation**:
- ✅ Database constraint catches race condition
- ✅ Application check provides user-friendly error (99% of cases)
- ⚠️ Edge case: Second request gets IntegrityError (HTTP 500)

**Action Required**:
- [ ] Add exception handler for `IntegrityError` with `uq_sessions_company_user_open`
- [ ] Convert to HTTP 409 with "Already has open session" message
- [ ] Log race condition occurrence for monitoring

**Implementation**:
```python
try:
    session = repo.create_session(...)
except IntegrityError as e:
    if 'uq_sessions_company_user_open' in str(e):
        # Race condition caught by DB
        raise HTTPException(409, detail={
            "error": "User already has an open attendance session",
            "error_code": "ALREADY_OPEN_SESSION"
        })
    raise  # Re-raise other IntegrityErrors
```

---

### 3.2 Concurrent Punch-Out

**Risk**: Two simultaneous punch-out requests from same user

**Scenario**:
```
T1: Request A finds open session → Session X
T2: Request B finds open session → Session X
T3: Request A closes session X → Success
T4: Request B tries to close session X → Not found (already closed)
```

**Mitigation**:
- ✅ Repository returns `None` if session not found or already closed
- ✅ API returns HTTP 404 "No open session found"
- ✅ Idempotent behavior (second request harmless)

**Action Required**:
- [x] No additional action needed (already handled by repository)

---

### 3.3 Transaction Isolation

**Current**: Default isolation level (READ COMMITTED)

**Risk**: Phantom reads in concurrent transactions

**Mitigation**:
- ✅ Partial unique index provides serialization for open sessions
- ✅ No need for SERIALIZABLE (performance overhead)

**Action Required**:
- [x] No change to isolation level needed

---

## Section 4: Tenant Boundary Considerations

### 4.1 Company ID Source

**Rule**: `company_id` MUST come from JWT, never from request body

**Implementation**:
```python
@router.post("/punch-in")
def punch_in(
    company_id: str = Depends(get_current_company_id),  # From JWT
    user_id: UUID = Depends(get_current_user_id),       # From JWT
    request: PunchInRequest,                            # From body
    db: Session = Depends(get_db)
):
    # company_id and user_id are injected, not from request
    ...
```

**Verification**:
- [ ] Ensure `PunchInRequest` DTO does NOT include `company_id` or `user_id` fields
- [ ] Ensure all repository calls pass `company_id` from JWT

---

### 4.2 Cross-Company Access Prevention

**Rule**: User can only access their own company's data

**Enforcement**:
- ✅ All repository methods filter by `company_id`
- ✅ JWT `company_id` claim used for scoping
- ✅ No way to override `company_id` from request

**Test Cases Required**:
- [ ] User A (Company A) cannot see User B (Company B) sessions
- [ ] User A (Company A) cannot punch in/out for Company B
- [ ] Invalid `company_id` in JWT returns 404

---

### 4.3 Multi-Company Users

**Scenario**: User has memberships in multiple companies

**Current Behavior**:
- JWT contains single `company_id` (current active company)
- User can only interact with one company per request
- User must switch company context to access other company's data

**Action Required**:
- [x] No special handling needed (JWT handles company context)

---

## Section 5: Test Plan Overview

### 5.1 Unit Tests

**Repository Layer** (already tested in WP-11-01):
- ✅ `create_session()` with open session check
- ✅ `close_session()` with duration calculation
- ✅ `get_open_session()` tenant-scoped
- ✅ Business invariant enforcement

**New Tests Required**:
- [ ] DTO validation (Pydantic models)
- [ ] Error response formatting

---

### 5.2 Integration Tests

**API Layer** (new in WP-11-02):
- [ ] `POST /punch-in` creates session and punch record
- [ ] `POST /punch-in` returns 409 if already open
- [ ] `POST /punch-out` closes session and calculates duration
- [ ] `POST /punch-out` returns 404 if no open session
- [ ] `GET /current-status` returns open session details
- [ ] `GET /current-status` returns null if no open session
- [ ] `GET /history` returns paginated sessions
- [ ] `GET /history` filters by date range

---

### 5.3 E2E Tests

**Full Flow** (new in WP-11-02):
- [ ] User logs in → gets JWT
- [ ] User punches in → session created
- [ ] User checks status → sees open session
- [ ] User punches out → session closed
- [ ] User checks history → sees closed session

---

### 5.4 Security Tests

**Tenant Isolation** (critical):
- [ ] User A cannot access User B's sessions (different company)
- [ ] User A cannot punch in/out for User B
- [ ] Invalid JWT rejected (401)
- [ ] Missing JWT rejected (401)
- [ ] Expired JWT rejected (401)

---

### 5.5 Concurrency Tests

**Race Conditions**:
- [ ] Concurrent punch-in requests → one succeeds, one gets 409
- [ ] Concurrent punch-out requests → one succeeds, one gets 404

---

## Section 6: Go / No-Go Conditions

### Go Conditions (Must Be Met)

- [ ] **WP-11-01 Phase B completed** ✅ (DONE)
- [ ] **Domain model tested** ✅ (41 tests passing)
- [ ] **Business invariant verified** ✅ (DB + app level)
- [ ] **Tenant isolation verified** ✅ (Repository tests passing)
- [ ] **Endpoint design approved** ⏳ (This checklist)
- [ ] **Error handling rules approved** ⏳ (This checklist)
- [ ] **Race condition mitigation approved** ⏳ (This checklist)
- [ ] **Test plan approved** ⏳ (This checklist)

### No-Go Conditions (Blockers)

- [ ] **Auth frozen boundary violated** ❌ (Would block)
- [ ] **Tenant isolation not enforced** ❌ (Would block)
- [ ] **Business invariant not enforced** ❌ (Would block)
- [ ] **Critical security issue identified** ❌ (Would block)

---

## Section 7: Out of Scope (Deferred)

### Deferred to WP-11-03 (Policy Engine)
- ❌ Late detection
- ❌ Overtime calculation
- ❌ Grace period enforcement
- ❌ Policy evaluation

### Deferred to WP-11-04 (Reports)
- ❌ Daily/weekly/monthly summaries
- ❌ Team-level aggregation
- ❌ Export to CSV/Excel

### Deferred to WP-11-05 (Audit Hooks)
- ❌ Comprehensive audit logging
- ❌ Tamper-proof log design

### Deferred to WP-11-06 (Telegram)
- ❌ Telegram bot integration

### Deferred to Future WP
- ❌ Break management (break_start, break_end)
- ❌ Manager override (punch in/out for other users)
- ❌ Bulk operations
- ❌ Photo upload for punch verification
- ❌ Geofencing validation

---

## Section 8: Dependencies Checklist

### Upstream Dependencies

- [x] **Gate 4 Auth** — FROZEN, will be used via middleware
- [x] **Tenant Context v2** — FROZEN, will be used for company scoping
- [x] **JWT Contract** — FROZEN, will be consumed for user/company identification
- [x] **WP-11-01 Domain Model** — COMPLETED, ready to use

### Downstream Dependencies

- [ ] **WP-11-03 Policy Engine** — Depends on WP-11-02 APIs
- [ ] **WP-11-04 Reports** — Depends on WP-11-02 APIs
- [ ] **WP-11-05 Audit Hooks** — Depends on WP-11-02 APIs

---

## Section 9: Approval

### Technical Review

- [ ] Endpoint design reviewed
- [ ] Error handling rules reviewed
- [ ] Race condition mitigation reviewed
- [ ] Tenant isolation strategy reviewed
- [ ] Test plan reviewed

### Security Review

- [ ] Auth frozen boundary respected
- [ ] Tenant isolation enforced
- [ ] No PII leakage in error messages
- [ ] Anti-enumeration preserved

### Product Review

- [ ] User experience acceptable
- [ ] Error messages user-friendly
- [ ] API design intuitive

---

## Section 10: Sign-Off

**Prepared By**: AI Assistant  
**Date**: 2026-03-03

**Reviewed By**: _________________  
**Date**: _________________

**Approved By**: _________________  
**Date**: _________________

**Status**: ⏳ PENDING APPROVAL

---

## Next Steps After Approval

1. Create WP-11-02 implementation plan
2. Define Pydantic DTOs (request/response models)
3. Implement API route handlers
4. Integrate with frozen auth middleware
5. Write E2E API tests
6. Document APIs with OpenAPI/Swagger
7. Conduct security review
8. Deploy to staging environment

---

**End of Checklist**
