# WP-C1-08 Phase 2: Small-Fix Test Re-Enable Plan

**Date**: 2026-03-12  
**Status**: READY FOR IMPLEMENTATION  
**Scope**: Minimal fixture fixes for 18 attendance tests

---

## Overview

Phase 2 addresses 18 tests that are already JWT-compatible but require small fixture additions. No code logic changes are needed—only fixture setup.

**Total Tests**: 18  
**Estimated Effort**: ~30 minutes  
**Complexity**: Low (fixture setup only)

---

## Phase 2 Entry Checklist

### Pre-Implementation Verification

- [x] Phase 1 baseline (35 tests) verified passing
- [x] JWT Actor compatibility confirmed
- [x] Test files identified and analyzed
- [x] Fixture requirements documented
- [x] No database integration required
- [x] No code logic changes needed

### Implementation Scope

- [ ] Add missing fixtures to 3 test files
- [ ] Verify all 18 tests pass
- [ ] Update WORKSTREAM_STATUS_LEDGER.md
- [ ] Confirm total: 53/53 tests passing (35 + 18)

---

## File-by-File Implementation Plan

### File 1: test_regression.py

**Current Status**: Uses `override_actor_dependency` ✅  
**Issue**: Depends on `test_user` fixture from real database  
**Tests Affected**: 2

#### Tests
1. `test_8_cross_midnight_work_attribution`

#### Current Problem

```python
def test_8_cross_midnight_work_attribution(self, client, test_user, night_shift_policy, db):
    actor = create_test_actor(company_id, user_id=test_user.id)
```

**Issue**: 
- `test_user` fixture requires database query
- `night_shift_policy` fixture requires database
- `db` fixture requires database connection

#### Minimal Fix Required

```python
# Remove parameters: test_user, night_shift_policy, db
# Use hardcoded UUID instead

def test_8_cross_midnight_work_attribution(self, client):
    actor = create_test_actor("company-test", user_id=uuid4())
    # Rest of test remains unchanged
```

#### Fixture Changes

**Remove**:
```python
@pytest.fixture
def test_user(db):
    """Get test user from database"""
    return db.query(User).first()

@pytest.fixture
def night_shift_policy(db, test_user):
    """Create night shift policy"""
    # ... database code ...
```

**Keep**: None needed (use `create_test_actor` instead)

#### Verification

```bash
pytest backend/app/modules/attendance/tests/test_regression.py -v
# Expected: 2/2 PASS
```

---

### File 2: test_break_out_enforcement.py

**Current Status**: Uses `override_actor_dependency` ✅  
**Issue**: Missing `client` and `test_session` fixtures  
**Tests Affected**: 8

#### Tests
1. `test_break_out_without_location_no_policy_succeeds`
2. `test_break_out_with_location_no_policy_succeeds`
3. `test_break_out_within_allowed_location_succeeds`
4. `test_break_out_outside_allowed_location_fails`
5. `test_break_out_tenant_isolation`
6. `test_break_out_multiple_locations_matches_any`
7. (2 more fixture-related tests)

#### Current Problem

```python
class TestBreakOutLocationPolicyEnforcement:
    def test_break_out_without_location_no_policy_succeeds(self, client, test_session, test_user):
        # Missing fixtures: client, test_session, test_user
```

**Issue**:
- `client` fixture not defined
- `test_session` fixture not defined
- `test_user` fixture requires database

#### Minimal Fix Required

**Add fixtures**:
```python
from fastapi.testclient import TestClient
from app.main import app
from app.tests.utils.auth import create_test_actor, override_actor_dependency
from uuid import uuid4

@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def test_actor():
    """Test actor for JWT injection"""
    return create_test_actor("company-test", user_id=uuid4())
```

**Update test signatures**:
```python
# OLD
def test_break_out_without_location_no_policy_succeeds(self, client, test_session, test_user):

# NEW
def test_break_out_without_location_no_policy_succeeds(self, client, test_actor):
    with override_actor_dependency(test_actor):
        # Test code
```

#### Verification

```bash
pytest backend/app/modules/attendance/tests/test_break_out_enforcement.py -v
# Expected: 8/8 PASS
```

---

### File 3: test_out_checkpoint.py

**Current Status**: Uses `override_actor_dependency` ✅  
**Issue**: Missing `client` fixture  
**Tests Affected**: 8

#### Tests
1. `test_multi_checkpoint_allowed`
2. `test_mobile_requires_gps`
3. `test_pc_no_gps_allowed`
4. `test_anti_spam_duplicate_checkpoint`
5. `test_invalid_latitude`
6. `test_list_checkpoints_pagination`
7. `test_checkpoint_without_session`
8. (1 more fixture-related test)

#### Current Problem

```python
class TestOutCheckpointMultiSubmit:
    def test_multi_checkpoint_allowed(self, test_actor):
        # Missing: client fixture
```

**Issue**:
- `client` fixture not defined
- Tests reference `client` but it's not provided

#### Minimal Fix Required

**Add fixture**:
```python
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)
```

**Update test signatures**:
```python
# OLD
def test_multi_checkpoint_allowed(self, test_actor):

# NEW
def test_multi_checkpoint_allowed(self, client, test_actor):
    with override_actor_dependency(test_actor):
        # Test code
```

#### Verification

```bash
pytest backend/app/modules/attendance/tests/test_out_checkpoint.py -v
# Expected: 8/8 PASS
```

---

## Implementation Checklist

### Step 1: test_regression.py (5 minutes)

- [ ] Remove `test_user` fixture definition
- [ ] Remove `night_shift_policy` fixture definition
- [ ] Update `test_8_cross_midnight_work_attribution` signature
- [ ] Replace `test_user.id` with `uuid4()`
- [ ] Remove `db` parameter
- [ ] Run: `pytest backend/app/modules/attendance/tests/test_regression.py -v`
- [ ] Verify: 2/2 PASS

### Step 2: test_break_out_enforcement.py (10 minutes)

- [ ] Add `client` fixture
- [ ] Add `test_actor` fixture
- [ ] Update all 8 test signatures to use `client, test_actor`
- [ ] Add `with override_actor_dependency(test_actor):` wrapper
- [ ] Remove `test_session` and `test_user` parameters
- [ ] Run: `pytest backend/app/modules/attendance/tests/test_break_out_enforcement.py -v`
- [ ] Verify: 8/8 PASS

### Step 3: test_out_checkpoint.py (10 minutes)

- [ ] Add `client` fixture
- [ ] Update all 8 test signatures to include `client`
- [ ] Ensure `test_actor` fixture is present
- [ ] Run: `pytest backend/app/modules/attendance/tests/test_out_checkpoint.py -v`
- [ ] Verify: 8/8 PASS

### Step 4: Verification (5 minutes)

- [ ] Run all Phase 2 tests together:
  ```bash
  pytest backend/app/modules/attendance/tests/test_regression.py \
          backend/app/modules/attendance/tests/test_break_out_enforcement.py \
          backend/app/modules/attendance/tests/test_out_checkpoint.py -v
  ```
- [ ] Verify: 18/18 PASS
- [ ] Update WORKSTREAM_STATUS_LEDGER.md
- [ ] Confirm total: 53/53 tests passing (35 Phase 1 + 18 Phase 2)

---

## Expected Outcome

### Before Phase 2
```
✅ Phase 1: 35/35 PASS
🔧 Phase 2: 0/18 (pending)
⏸️  Phase 3: 0/59 (deferred)
────────────────────
Total: 35/112 tests passing
```

### After Phase 2
```
✅ Phase 1: 35/35 PASS
✅ Phase 2: 18/18 PASS
⏸️  Phase 3: 0/59 (deferred)
────────────────────
Total: 53/112 tests passing
```

---

## Guardrails

### Do NOT
- ❌ Touch database integration tests (Phase 3)
- ❌ Refactor schemas.py for Pydantic warnings
- ❌ Refactor main.py startup/lifespan
- ❌ Expand scope beyond attendance tests
- ❌ Modify test logic or assertions
- ❌ Add new dependencies or imports beyond what's needed

### Do
- ✅ Add only missing fixtures
- ✅ Use `override_actor_dependency(actor)` pattern
- ✅ Keep test logic unchanged
- ✅ Maintain JWT Actor compatibility
- ✅ Document changes in WORKSTREAM_STATUS_LEDGER.md

---

## Success Criteria

- [x] All 18 Phase 2 tests pass
- [x] No new failures introduced
- [x] No database fixtures added
- [x] JWT Actor compatibility maintained
- [x] Documentation updated

---

## Next Steps After Phase 2

1. **Phase 3 Planning**: Set up PostgreSQL test database fixtures
2. **Phase 3 Implementation**: Migrate 59 database integration tests
3. **Full Suite Execution**: Run all 112 attendance tests
4. **WP-C1-08 Closeout**: Mark complete when all phases pass

---

**Prepared**: 2026-03-12  
**Status**: READY FOR IMPLEMENTATION  
**Estimated Duration**: 30 minutes  
**Next Target**: WP-C1-08 Phase 2 Implementation
