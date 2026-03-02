# Attendance Regression Test Specification

**Document Version:** 1.0  
**Created:** 2026-03-02  
**Purpose:** Define the 8 core regression tests for attendance system

---

## Overview

These 8 tests validate the core attendance business logic:
- Status state machine (NO_MATCH, PENDING_APPROVAL, APPROVED)
- IN/OUT pairing and work time calculation
- Day close at 21:00 with missing card detection
- Approval triggers recalculation
- Auth/RBAC enforcement

**All tests must pass before attendance module is considered complete.**

---

## Test 1: NO_MATCH without reason → Rejected

### Given
- Employee creates attendance record
- Record type: `NO_MATCH` (manual entry, no device pairing)
- **No reason provided** (`reason` field is empty or null)

### When
- Employee submits `POST /api/attendance/mock-create`

### Then
- **Response:** 422 Unprocessable Entity
- **Error message:** "NO_MATCH records must include a reason"
- **Record NOT created** in database

### Test Code
```python
def test_no_match_without_reason_rejected(client, employee_token):
    """Test 1: NO_MATCH without reason → 422"""
    payload = {
        "type": "NO_MATCH",
        "timestamp": "2026-03-02T09:00:00Z",
        "reason": None  # or empty string
    }
    headers = {"Authorization": f"Bearer {employee_token}"}
    response = client.post("/api/attendance/mock-create", json=payload, headers=headers)
    
    assert response.status_code == 422
    assert "reason" in response.json()["detail"].lower()
```

---

## Test 2: NO_MATCH with reason → PENDING_APPROVAL

### Given
- Employee creates attendance record
- Record type: `NO_MATCH`
- **Reason provided** (e.g., "Forgot to clock in")

### When
- Employee submits `POST /api/attendance/mock-create`

### Then
- **Response:** 201 Created
- **Record created** with status = `PENDING_APPROVAL`
- **Record NOT included** in inference/day close until approved

### Test Code
```python
def test_no_match_with_reason_pending(client, employee_token):
    """Test 2: NO_MATCH with reason → PENDING_APPROVAL"""
    payload = {
        "type": "NO_MATCH",
        "timestamp": "2026-03-02T09:00:00Z",
        "reason": "Forgot to clock in"
    }
    headers = {"Authorization": f"Bearer {employee_token}"}
    response = client.post("/api/attendance/mock-create", json=payload, headers=headers)
    
    assert response.status_code == 201
    record = response.json()
    assert record["status"] == "PENDING_APPROVAL"
    assert record["reason"] == "Forgot to clock in"
```

---

## Test 3: APPROVED records → Inference correct

### Given
- Employee has 2 APPROVED records on 2026-03-02:
  - IN at 09:00
  - OUT at 18:00

### When
- Run inference: `pair_in_out(records)`

### Then
- **1 pair created:** (IN 09:00, OUT 18:00)
- **Work time:** 9 hours
- **No missing cards**

### Test Code
```python
def test_approved_records_inference(db_session, company_id):
    """Test 3: APPROVED → inference correct"""
    # Create 2 APPROVED records
    in_record = AttendanceRecord(
        id=uuid4(),
        company_id=company_id,
        staff_id="staff-1",
        type="IN",
        timestamp=datetime(2026, 3, 2, 9, 0),
        status="APPROVED"
    )
    out_record = AttendanceRecord(
        id=uuid4(),
        company_id=company_id,
        staff_id="staff-1",
        type="OUT",
        timestamp=datetime(2026, 3, 2, 18, 0),
        status="APPROVED"
    )
    db_session.add_all([in_record, out_record])
    db_session.commit()
    
    # Run inference
    records = [in_record, out_record]
    pairs = pair_in_out(records)
    
    assert len(pairs) == 1
    assert pairs[0].in_record.id == in_record.id
    assert pairs[0].out_record.id == out_record.id
    
    work_time = calculate_work_time(pairs[0])
    assert work_time == timedelta(hours=9)
```

---

## Test 4: PENDING_APPROVAL excluded from inference and day close

### Given
- Employee has 3 records on 2026-03-02:
  - IN at 09:00 (APPROVED)
  - OUT at 18:00 (APPROVED)
  - IN at 20:00 (PENDING_APPROVAL, reason: "Overtime")

### When
- Run day close at 21:00

### Then
- **Only APPROVED records processed**
- **1 pair:** (IN 09:00, OUT 18:00)
- **PENDING record ignored** (not in pairs, not in missing cards)
- **No missing cards detected** (PENDING doesn't count)

### Test Code
```python
def test_pending_excluded_from_day_close(db_session, company_id):
    """Test 4: PENDING excluded from inference/day close"""
    records = [
        AttendanceRecord(
            id=uuid4(),
            company_id=company_id,
            staff_id="staff-1",
            type="IN",
            timestamp=datetime(2026, 3, 2, 9, 0),
            status="APPROVED"
        ),
        AttendanceRecord(
            id=uuid4(),
            company_id=company_id,
            staff_id="staff-1",
            type="OUT",
            timestamp=datetime(2026, 3, 2, 18, 0),
            status="APPROVED"
        ),
        AttendanceRecord(
            id=uuid4(),
            company_id=company_id,
            staff_id="staff-1",
            type="IN",
            timestamp=datetime(2026, 3, 2, 20, 0),
            status="PENDING_APPROVAL",
            reason="Overtime"
        ),
    ]
    db_session.add_all(records)
    db_session.commit()
    
    # Run day close
    result = close_day(company_id, date(2026, 3, 2), cutoff_time=time(21, 0))
    
    assert len(result.pairs) == 1
    assert result.pairs[0].in_record.timestamp.hour == 9
    assert result.pairs[0].out_record.timestamp.hour == 18
    assert len(result.missing_cards) == 0  # PENDING not counted
```

---

## Test 5: Day close at 21:00 → Missing cards detected

### Given
- Employee has 1 record on 2026-03-02:
  - IN at 09:00 (APPROVED)
  - **No OUT record**

### When
- Run day close at 21:00

### Then
- **1 unpaired IN detected**
- **Missing card:** "Missing OUT for IN at 09:00"
- **Work time:** 0 (cannot calculate without OUT)

### Test Code
```python
def test_day_close_missing_out(db_session, company_id):
    """Test 5: Day close → missing OUT detected"""
    in_record = AttendanceRecord(
        id=uuid4(),
        company_id=company_id,
        staff_id="staff-1",
        type="IN",
        timestamp=datetime(2026, 3, 2, 9, 0),
        status="APPROVED"
    )
    db_session.add(in_record)
    db_session.commit()
    
    # Run day close
    result = close_day(company_id, date(2026, 3, 2), cutoff_time=time(21, 0))
    
    assert len(result.pairs) == 0
    assert len(result.missing_cards) == 1
    assert result.missing_cards[0].type == "MISSING_OUT"
    assert result.missing_cards[0].record_id == in_record.id
```

---

## Test 6: Approve PENDING → Day recalculated

### Given
- Employee has 3 records on 2026-03-02:
  - IN at 09:00 (APPROVED)
  - OUT at 13:00 (APPROVED)
  - IN at 14:00 (PENDING_APPROVAL, reason: "Afternoon shift")

### When
- Manager approves the PENDING record: `POST /api/attendance/{id}/approve`

### Then
- **Record status:** PENDING_APPROVAL → APPROVED
- **Day recalculated:**
  - Before: 1 pair (09:00-13:00), work time = 4 hours
  - After: 1 pair (09:00-13:00) + 1 unpaired IN (14:00), missing OUT detected
- **Event emitted:** `attendance.approved`

### Test Code
```python
def test_approve_pending_recalculates_day(client, manager_token, db_session, company_id):
    """Test 6: Approve PENDING → day recalculated"""
    # Create records
    in1 = AttendanceRecord(
        id=uuid4(),
        company_id=company_id,
        staff_id="staff-1",
        type="IN",
        timestamp=datetime(2026, 3, 2, 9, 0),
        status="APPROVED"
    )
    out1 = AttendanceRecord(
        id=uuid4(),
        company_id=company_id,
        staff_id="staff-1",
        type="OUT",
        timestamp=datetime(2026, 3, 2, 13, 0),
        status="APPROVED"
    )
    in2 = AttendanceRecord(
        id=uuid4(),
        company_id=company_id,
        staff_id="staff-1",
        type="IN",
        timestamp=datetime(2026, 3, 2, 14, 0),
        status="PENDING_APPROVAL",
        reason="Afternoon shift"
    )
    db_session.add_all([in1, out1, in2])
    db_session.commit()
    
    # Approve PENDING
    headers = {"Authorization": f"Bearer {manager_token}"}
    response = client.post(f"/api/attendance/{in2.id}/approve", headers=headers)
    
    assert response.status_code == 200
    
    # Check status changed
    db_session.refresh(in2)
    assert in2.status == "APPROVED"
    
    # Check day recalculated
    result = close_day(company_id, date(2026, 3, 2))
    assert len(result.pairs) == 1  # 09:00-13:00
    assert len(result.missing_cards) == 1  # Missing OUT for 14:00 IN
```

---

## Test 7: customer_service unassigned company → 403

### Given
- User with role `customer_service`
- JWT claims: `assigned_companies = ["company-A", "company-B"]`
- User tries to access `company-C` (not assigned)

### When
- User sends request with `X-Company-ID: company-C` or JWT claim `company_id=company-C`

### Then
- **Response:** 403 Forbidden
- **Error message:** "Access denied: company not assigned to customer service"

### Test Code
```python
def test_customer_service_unassigned_company_403(client, customer_service_token):
    """Test 7: customer_service unassigned company → 403"""
    # customer_service_token has assigned_companies=["company-A", "company-B"]
    # Try to access company-C
    headers = {
        "Authorization": f"Bearer {customer_service_token}",
        "X-Company-ID": "company-C"
    }
    response = client.get("/api/attendance/records", headers=headers)
    
    assert response.status_code == 403
    assert "not assigned" in response.json()["detail"].lower()
```

---

## Test 8: OTP one-time use + force password change

### Given
- Admin creates user with OTP (one-time password)
- User logs in with OTP

### When
- User tries to access protected endpoint

### Then
- **First login with OTP:** Success, but `must_change_password=True` flag set
- **Protected endpoint access:** 403 with message "Password change required"
- **User changes password:** Success
- **OTP reuse:** 401 "Invalid credentials" (OTP invalidated after first use)

### Test Code
```python
def test_otp_one_time_use_and_force_change(client, db_session):
    """Test 8: OTP one-time use + force password change"""
    # Admin creates user with OTP
    user = User(
        id=uuid4(),
        company_id="company-A",
        username="newuser",
        email="newuser@example.com",
        password_hash=hash_password("OTP-123456"),
        is_otp=True,
        must_change_password=True,
        roles=["employee"]
    )
    db_session.add(user)
    db_session.commit()
    
    # First login with OTP
    response = client.post("/api/auth/login", json={
        "username": "newuser",
        "password": "OTP-123456"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Try to access protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/attendance/records", headers=headers)
    assert response.status_code == 403
    assert "password change required" in response.json()["detail"].lower()
    
    # Change password
    response = client.post("/api/auth/change-password", json={
        "old_password": "OTP-123456",
        "new_password": "NewSecurePass123!"
    }, headers=headers)
    assert response.status_code == 200
    
    # Try OTP again (should fail)
    response = client.post("/api/auth/login", json={
        "username": "newuser",
        "password": "OTP-123456"
    })
    assert response.status_code == 401
    
    # New password works
    response = client.post("/api/auth/login", json={
        "username": "newuser",
        "password": "NewSecurePass123!"
    })
    assert response.status_code == 200
```

---

## Summary Table

| # | Test Name | Status Field | Inference | Day Close | Auth |
|---|-----------|--------------|-----------|-----------|------|
| 1 | NO_MATCH no reason → reject | - | - | - | ❌ |
| 2 | NO_MATCH with reason → PENDING | PENDING_APPROVAL | ❌ | ❌ | ❌ |
| 3 | APPROVED → inference correct | APPROVED | ✅ | ✅ | ❌ |
| 4 | PENDING excluded | PENDING_APPROVAL | ❌ | ❌ | ❌ |
| 5 | Day close → missing cards | APPROVED | ✅ | ✅ | ❌ |
| 6 | Approve → recalculate | PENDING→APPROVED | ✅ | ✅ | ✅ |
| 7 | customer_service 403 | - | - | - | ✅ |
| 8 | OTP one-time + force change | - | - | - | ✅ |

---

## Implementation Order

1. **WP-11-01:** Define status enum + state machine (doc)
2. **WP-11-02:** Implement IN/OUT pairing (Test 3 partial)
3. **WP-11-03:** Implement work time calculation (Test 3 complete)
4. **WP-11-04:** Implement day close + missing cards (Test 4, 5)
5. **WP-11-05:** Implement approve → recalculate (Test 6)
6. **WP-11-06:** Implement all 8 tests (Test 1, 2, 7, 8)

---

**Done. These tests will be implemented in WP-11-06.**
