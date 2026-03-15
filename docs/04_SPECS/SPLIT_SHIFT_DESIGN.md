# Split Shift Design Document

**Project**: SaaS Multi-Tenant Attendance System  
**Work Package**: WP-11-03S — Split Shift Support + Flex Time Extension Points  
**Status**: ✅ COMPLETED  
**Date**: 2026-03-04

---

## Executive Summary

WP-11-03S extends the WP-11-03 Policy Engine to support **Split Shift** scenarios where a workday consists of multiple discrete work windows with breaks in between. The implementation also reserves extension points for future **Flex Time** support.

**Key Achievement**: Split shift support implemented without any database schema changes, maintaining full backward compatibility with existing WP-11-03 functionality.

**Test Results**: 24/24 tests passing (12 WP-11-03 + 12 WP-11-03S)

---

## Definitions

### Split Shift (分段工時)

A work schedule consisting of multiple discrete work windows within a single day, with unpaid breaks between them.

**Example**:
- Window 1: 08:00–14:00 (6 hours)
- Break: 14:00–16:00 (2 hours, unpaid)
- Window 2: 16:00–18:00 (2 hours)
- **Total work time**: 8 hours (not 10 hours)

**Use Cases**:
- Restaurant staff (lunch + dinner shifts)
- Retail workers (morning + evening shifts)
- Healthcare workers (split coverage)
- Transportation workers (peak hour coverage)

### Flex Time (彈性工時) - Extension Point Only

A flexible work schedule where employees can vary their arrival/departure times within defined bands, but must be present during core hours.

**Example**:
- Flex arrival: 08:00–10:00 (can arrive anytime)
- Core hours: 10:00–16:00 (must be present)
- Flex departure: 16:00–18:00 (can leave anytime)

**Status**: **NOT IMPLEMENTED** in WP-11-03S. Extension points reserved for future implementation.

---

## Architecture

### Domain Model (WP-11-03S Abstractions)

```
┌─────────────────────────────────────────────────────────┐
│                    WorkSchedule                         │
│  - mode: 'standard' | 'split_shift' | 'flex_time'      │
│  - windows: List[WorkWindow]                            │
│  - core_time_start: Optional[time]  (flex time)        │
│  - core_time_end: Optional[time]    (flex time)        │
│  - flex_bands: Optional[List[FlexTimeBand]]            │
└─────────────────────────────────────────────────────────┘
                     │
                     ├─► WorkWindow
                     │   - start_time: time
                     │   - end_time: time
                     │   - duration_minutes()
                     │   - contains_time()
                     │   - overlaps_with()
                     │
                     └─► FlexTimeBand (extension point)
                         - earliest: time
                         - latest: time
                         - band_type: str
```

### Policy Engine Integration

```
AttendancePolicyEngine
│
├─► evaluate(session, policy)
│   └─► Standard single-window evaluation (WP-11-03)
│
└─► evaluate_with_schedule(session, schedule, policy)  ← NEW (WP-11-03S)
    ├─► Late detection (first window)
    ├─► Early leave detection (last window)
    ├─► Work minutes calculation
    │   ├─► Standard mode: use session.duration_minutes
    │   └─► Split shift mode: _calculate_work_minutes_split_shift()
    └─► Overtime detection
```

---

## Split Shift Calculation Rules

### 1. Late Detection

**Rule**: Based on **first window** start time + grace period

**Example**:
- Windows: 08:00–14:00, 16:00–18:00
- Grace period: 15 minutes
- Punch in at 08:20 → Late by 5 minutes (20 - 15 grace)

### 2. Early Leave Detection

**Rule**: Based on **last window** end time

**Example**:
- Windows: 08:00–14:00, 16:00–18:00
- Punch out at 17:30 → Early leave by 30 minutes

### 3. Work Minutes Calculation (Split Shift Core Logic)

**Rule**: Only count time that falls **within work windows**

**Algorithm**:
```python
total_minutes = 0
for each window in windows:
    effective_start = max(punch_in_time, window_start)
    effective_end = min(punch_out_time, window_end)
    
    if effective_start < effective_end:
        total_minutes += (effective_end - effective_start)

return total_minutes
```

**Example 1**: Full day attendance
- Punch: 08:00–18:00 (10 hours total)
- Windows: 08:00–14:00, 16:00–18:00
- Calculation:
  - Window 1: 08:00–14:00 = 6 hours
  - Break: 14:00–16:00 = **not counted**
  - Window 2: 16:00–18:00 = 2 hours
- **Result**: 8 hours work time

**Example 2**: Punch during break
- Punch: 14:30–15:30 (1 hour total)
- Windows: 08:00–14:00, 16:00–18:00
- Calculation:
  - No overlap with any window
- **Result**: 0 hours work time

**Example 3**: Cross window boundary
- Punch: 13:00–17:00 (4 hours total)
- Windows: 08:00–14:00, 16:00–18:00
- Calculation:
  - Window 1: 13:00–14:00 = 1 hour
  - Break: 14:00–16:00 = **not counted**
  - Window 2: 16:00–17:00 = 1 hour
- **Result**: 2 hours work time

### 4. Overtime Detection

**Rule**: Same as WP-11-03, based on **actual work minutes** (not total session duration)

**Example**:
- Punch: 08:00–19:00 (11 hours total)
- Windows: 08:00–14:00, 16:00–19:00
- Work time: 6h + 3h = 9 hours = 540 minutes
- Overtime threshold: 480 minutes (8 hours)
- **Result**: 60 minutes overtime

---

## Edge Cases Handled

### 1. Windows Not Sorted

**Behavior**: Auto-sort windows by start_time

**Example**:
```python
# Input (wrong order)
windows = [
    WorkWindow(16:00, 18:00),
    WorkWindow(08:00, 14:00)
]

# Auto-sorted to
windows = [
    WorkWindow(08:00, 14:00),
    WorkWindow(16:00, 18:00)
]
```

### 2. Overlapping Windows

**Behavior**: Raise `ValueError` during WorkSchedule creation

**Example**:
```python
# This will raise ValueError
windows = [
    WorkWindow(08:00, 14:00),
    WorkWindow(13:00, 18:00)  # Overlaps with first window!
]
```

### 3. Invalid Window Times

**Behavior**: Raise `ValueError` during WorkWindow creation

**Example**:
```python
# This will raise ValueError
WorkWindow(start_time=14:00, end_time=08:00)  # start >= end
```

### 4. Punch Only in One Window

**Behavior**: Count only that window's time

**Example**:
- Punch: 08:00–13:00
- Windows: 08:00–14:00, 16:00–18:00
- **Result**: 5 hours (only first window)

### 5. Punch Entirely Outside Windows

**Behavior**: 0 work minutes

**Example**:
- Punch: 14:30–15:30
- Windows: 08:00–14:00, 16:00–18:00
- **Result**: 0 hours

---

## Backward Compatibility

### WP-11-03 Compatibility

**Guarantee**: All existing WP-11-03 functionality remains unchanged

**Mechanism**: 
- Original `evaluate(session, policy)` method unchanged
- New `evaluate_with_schedule(session, schedule, policy)` method added
- `WorkSchedule.from_policy(policy)` converts existing policies to standard mode

**Test Verification**: All 12 WP-11-03 tests still pass

### Standard Mode

**Definition**: Single-window schedule (backward compatible with WP-11-03)

**Creation**:
```python
# From existing policy
schedule = WorkSchedule.from_policy(policy)

# Or manually
schedule = WorkSchedule(
    mode='standard',
    windows=[WorkWindow(start_time=time(9,0), end_time=time(18,0))]
)
```

**Behavior**: Identical to WP-11-03 evaluation

---

## Extension Points for Flex Time

### Reserved Fields in WorkSchedule

```python
@dataclass
class WorkSchedule:
    mode: str  # 'standard', 'split_shift', 'flex_time'
    windows: List[WorkWindow]
    
    # Extension points (not used in WP-11-03S)
    core_time_start: Optional[time] = None
    core_time_end: Optional[time] = None
    flex_bands: Optional[List[FlexTimeBand]] = None
```

### FlexTimeBand Abstraction

```python
@dataclass(frozen=True)
class FlexTimeBand:
    """For future Flex Time support"""
    earliest: time
    latest: time
    band_type: str  # 'arrival', 'departure', 'break'
```

### Future Flex Time Implementation

**Proposed Behavior**:
1. **Arrival Flex Band**: Employee can arrive between 08:00–10:00
2. **Core Hours**: Must be present 10:00–16:00
3. **Departure Flex Band**: Can leave between 16:00–18:00

**Late Detection** (flex time):
- Not late if arrived within flex band
- Late if arrived after flex band latest time

**Early Leave Detection** (flex time):
- Not early if left after core hours end
- Early if left before core hours end

**Work Minutes Calculation** (flex time):
- Count from actual arrival to actual departure
- Deduct break time if applicable

---

## Database Schema Considerations

### Current State (WP-11-03S)

**No schema changes required** ✅

- Split shift schedules passed as parameters to `evaluate_with_schedule()`
- No persistence of WorkSchedule objects
- Existing `attendance_policies` table unchanged

### Future Persistence Options

#### Option A: JSON Column (Recommended for MVP)

**Pros**:
- Simple implementation
- No new tables
- Flexible schema evolution

**Cons**:
- Limited query capabilities
- No referential integrity

**Schema**:
```sql
ALTER TABLE attendance_policies 
ADD COLUMN schedule_config JSONB;

-- Example JSON
{
  "mode": "split_shift",
  "windows": [
    {"start_time": "08:00", "end_time": "14:00"},
    {"start_time": "16:00", "end_time": "18:00"}
  ]
}
```

#### Option B: Separate Tables (Recommended for Production)

**Pros**:
- Proper normalization
- Query-friendly
- Referential integrity

**Cons**:
- More complex
- Requires migration

**Schema**:
```sql
CREATE TABLE policy_schedules (
    id UUID PRIMARY KEY,
    policy_id UUID REFERENCES attendance_policies(id),
    mode VARCHAR(20) NOT NULL,  -- 'standard', 'split_shift', 'flex_time'
    core_time_start TIME,
    core_time_end TIME,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE policy_work_windows (
    id UUID PRIMARY KEY,
    schedule_id UUID REFERENCES policy_schedules(id),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    sequence_order INT NOT NULL,
    created_at TIMESTAMP
);

CREATE TABLE policy_flex_bands (
    id UUID PRIMARY KEY,
    schedule_id UUID REFERENCES policy_schedules(id),
    band_type VARCHAR(20) NOT NULL,  -- 'arrival', 'departure', 'break'
    earliest TIME NOT NULL,
    latest TIME NOT NULL,
    created_at TIMESTAMP
);
```

---

## API Integration (Future)

### Proposed CRUD Endpoints

**Not implemented in WP-11-03S** (design only)

```
POST   /api/v1/attendance/policies/{policy_id}/schedule
GET    /api/v1/attendance/policies/{policy_id}/schedule
PUT    /api/v1/attendance/policies/{policy_id}/schedule
DELETE /api/v1/attendance/policies/{policy_id}/schedule
```

### Request/Response Examples

**Create Split Shift Schedule**:
```json
POST /api/v1/attendance/policies/{policy_id}/schedule

{
  "mode": "split_shift",
  "windows": [
    {"start_time": "08:00", "end_time": "14:00"},
    {"start_time": "16:00", "end_time": "18:00"}
  ]
}
```

**Create Flex Time Schedule** (future):
```json
POST /api/v1/attendance/policies/{policy_id}/schedule

{
  "mode": "flex_time",
  "windows": [
    {"start_time": "08:00", "end_time": "18:00"}
  ],
  "core_time_start": "10:00",
  "core_time_end": "16:00",
  "flex_bands": [
    {
      "band_type": "arrival",
      "earliest": "08:00",
      "latest": "10:00"
    },
    {
      "band_type": "departure",
      "earliest": "16:00",
      "latest": "18:00"
    }
  ]
}
```

---

## Testing

### Test Coverage

**Total Tests**: 24 (12 WP-11-03 + 12 WP-11-03S)

**WP-11-03S Split Shift Tests**:
1. ✅ Normal attendance (full day, both windows)
2. ✅ Late (first window)
3. ✅ Early leave (last window)
4. ✅ Punch only first window
5. ✅ Punch only second window
6. ✅ Punch during break (0 work time)
7. ✅ Cross window boundary
8. ✅ WorkWindow validation (invalid times)
9. ✅ WorkSchedule validation (overlapping windows)
10. ✅ Auto-sort windows
11. ✅ Backward compatibility (from_policy)
12. ✅ Tenant isolation (different companies, different schedules)

### Test File

`backend/app/modules/attendance/tests/test_policy_engine.py`

**Classes**:
- `TestSplitShiftBasics` (7 tests)
- `TestSplitShiftEdgeCases` (4 tests)
- `TestSplitShiftTenantIsolation` (1 test)

---

## Performance Considerations

### Calculation Complexity

**Time Complexity**: O(n) where n = number of windows
- Typically n = 2-3 for split shift
- Worst case: O(10) for complex schedules

**Space Complexity**: O(1)
- No additional data structures
- In-place calculations

### Optimization Opportunities

1. **Window Caching**: Cache sorted windows per schedule
2. **Batch Evaluation**: Process multiple sessions with same schedule
3. **Parallel Evaluation**: Evaluate sessions in parallel for reports

---

## Migration Path

### Phase 1: WP-11-03S (Current) ✅

- Split shift support via code
- No DB changes
- Test-driven implementation

### Phase 2: WP-11-04 (Proposed)

**Scope**: Policy Schedule CRUD APIs

**Deliverables**:
- Add `schedule_config` JSONB column to `attendance_policies`
- Create CRUD endpoints for schedule management
- Update policy repository to load/save schedules
- Integrate with punch-out API (auto-load schedule)

**Migration**:
```sql
-- Add column
ALTER TABLE attendance_policies 
ADD COLUMN schedule_config JSONB DEFAULT NULL;

-- Migrate existing policies to standard mode
UPDATE attendance_policies
SET schedule_config = jsonb_build_object(
    'mode', 'standard',
    'windows', jsonb_build_array(
        jsonb_build_object(
            'start_time', work_start_time::text,
            'end_time', work_end_time::text
        )
    )
);
```

### Phase 3: Flex Time Support (Future)

**Scope**: Implement flex time evaluation logic

**Deliverables**:
- Implement `_calculate_late_flex_time()`
- Implement `_calculate_early_leave_flex_time()`
- Add flex time tests
- Update schedule CRUD to support flex bands

---

## Compliance Verification

### Auth Frozen Boundary ✅

- ✅ No auth schema modifications
- ✅ No JWT contract changes
- ✅ Uses existing tenant context
- ✅ No anti-enumeration violations

### Tenant Isolation ✅

- ✅ All evaluations scoped to company_id
- ✅ Different companies can have different schedules
- ✅ Test verifies cross-company isolation

### No Schema Changes ✅

- ✅ No new tables
- ✅ No new columns
- ✅ No migrations required
- ✅ Pure code implementation

### Backward Compatibility ✅

- ✅ All WP-11-03 tests still pass
- ✅ Original `evaluate()` method unchanged
- ✅ `WorkSchedule.from_policy()` provides compatibility layer

---

## Known Limitations

### 1. No Cross-Day Support

**Current**: Assumes all windows are within same day

**Impact**: Night shifts spanning midnight not supported

**Future**: Add date handling for 24-hour operations

### 2. No Break Deduction

**Current**: Breaks between windows not counted (correct)

**Impact**: Paid breaks within windows still counted

**Future**: Add explicit break periods within windows

### 3. No Holiday/Weekend Handling

**Current**: No special handling for holidays/weekends

**Impact**: Same schedule applied every day

**Future**: Add calendar-based schedule variations

### 4. No User-Specific Schedules

**Current**: Schedule tied to policy (company-wide)

**Impact**: Cannot assign different schedules to different users

**Future**: Add user/department schedule assignments

---

## Recommendations

### For Next WP (WP-11-04 or WP-11-05)

**Priority 1**: Policy Schedule CRUD APIs
- Add `schedule_config` JSONB column
- Create REST endpoints for schedule management
- Auto-load schedule in punch-out API

**Priority 2**: Schedule Assignment
- Allow assigning schedules to users/departments
- Override company default schedule

**Priority 3**: Flex Time Implementation
- Implement flex time evaluation logic
- Add flex time tests
- Update CRUD APIs

### For Production Deployment

1. **Monitor Performance**: Track evaluation time for complex schedules
2. **Add Caching**: Cache schedules per policy_id
3. **Add Logging**: Log split shift calculations for debugging
4. **Add Metrics**: Track split shift usage across companies

---

## Conclusion

WP-11-03S successfully extends the Policy Engine to support split shift scenarios without any database schema changes. The implementation maintains full backward compatibility with WP-11-03 while providing a solid foundation for future flex time support.

**Key Achievements**:
- ✅ Split shift support (2+ windows per day)
- ✅ Zero schema modifications
- ✅ 24/24 tests passing
- ✅ Backward compatible
- ✅ Extension points for flex time
- ✅ Tenant isolation maintained

**Next Steps**: Implement Policy Schedule CRUD APIs (WP-11-04) to enable configuration via UI/API instead of code.

---

**Document Prepared By**: AI Assistant  
**Date**: 2026-03-04  
**Status**: ✅ COMPLETED
