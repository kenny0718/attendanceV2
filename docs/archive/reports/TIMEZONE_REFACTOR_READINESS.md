# Timezone Refactor Readiness Report

**Date:** 2026-03-10  
**Status:** Pre-refactor audit complete — issues identified, ready to plan  
**Stable tag:** `attendance-stable-before-timezone-refactor`

---

## Time Source Inventory

### Backend

| Location | Current Usage | Issue |
|----------|--------------|-------|
| `api.py:136` | `datetime.now(timezone.utc)` — punch_in | Mixed: business time stored as UTC |
| `api.py:198` | `datetime.now(timezone.utc)` — punch_out | Mixed: business time stored as UTC |
| `api.py:278` | `datetime.now(timezone.utc)` — elapsed calc | OK for duration calc |
| `api.py:429` | `datetime.now(timezone.utc)` — break_out | Mixed |
| `api.py:481` | `datetime.now(timezone.utc)` — break_in | Mixed |
| `api.py:522` | `date.today()` — break punches query | CRITICAL BUG |
| `api.py:523` | `.replace(tzinfo=timezone.utc)` — range start | Wrong timezone for daily boundary |
| `repo.py:122` | `get_current_time()` — session updated_at | Asia/Taipei OK |
| `repo.py:399` | `get_current_time()` — approval timestamp | Asia/Taipei OK |
| `repo.py:511` | `get_current_time()` — duplicate check cutoff | Asia/Taipei OK |
| `models.py:280` | `get_current_time` — AllowedLocation timestamps | Asia/Taipei OK |
| `config.py:69` | `get_current_time()` returns `datetime.now(TIMEZONE)` | Asia/Taipei (UTC+8) OK |

### Frontend

| Location | Current Usage | Issue |
|----------|--------------|-------|
| `attendance.js` | `import dayjs` — no timezone plugin | No explicit timezone control |
| `attendance.js:59-62` | `dayjs(ts).format('HH:mm')` — display | Relies on browser local time |
| `attendance.js:445` | `dayjs().startOf('day')` — today check | Uses browser local time |
| `attendance.js:289` | `new Date()` — checkpoint date comparison | Browser local time |
| `attendance.js:332` | `new Date().toISOString()` — GPS captured_at | UTC ISO string OK |

---

## Critical Bug: `api.py:522-524`

```python
# CURRENT (BUGGY):
today = date.today()           # Server local date (UTC on server)
start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
# Result: 2026-03-10 00:00:00+00:00  (UTC midnight)
# Taiwan midnight = 2026-03-09 16:00:00+00:00
# Break punches from 00:00-08:00 Taiwan time are MISSED!
```

**Fix:**
```python
from app.core.config import TIMEZONE
from datetime import timedelta
taiwan_now = datetime.now(TIMEZONE)
start_of_day = taiwan_now.replace(hour=0, minute=0, second=0, microsecond=0)
end_of_day = start_of_day + timedelta(days=1)
```

---

## Mixed UTC vs Asia/Taipei Analysis

Punch times use `datetime.now(timezone.utc)` (UTC),
while audit timestamps use `get_current_time()` (Asia/Taipei).

**This currently works** because:
- DB uses `DateTime(timezone=True)` — PostgreSQL stores as UTC internally
- FastAPI serializes with timezone offset
- dayjs parses ISO strings with offset correctly

**Risk:** The `date.today()` bug proves this mixed approach causes real issues.
**Recommendation:** Standardize all business event times to `get_current_time()`.

---

## DB/Schema Risk Assessment

| Aspect | State | Risk |
|--------|-------|------|
| Session columns | `DateTime(timezone=True)` | Safe |
| Punch columns | `DateTime(timezone=True)` | Safe |
| AllowedLocation timestamps | `DateTime` (no timezone) | Low risk |
| Daily query boundary | Uses UTC midnight | CRITICAL BUG in break-punches |
| History sort | `punch_in_time DESC` | Safe |

---

## Risk Areas by Feature

| Feature | Risk | Reason |
|---------|------|--------|
| Break punch daily query | HIGH | `date.today()` + UTC midnight boundary wrong |
| Punch-in/out display | Low | dayjs parses offset correctly |
| Cross-midnight session | Low | Fixed by `isTodaySession` check |
| Elapsed time calc | Low | UTC diff is correct |
| Policy engine late/early calc | Medium | UTC times used, thresholds may need TZ review |
| Test fixtures `datetime.utcnow()` | Low | Deprecated but functional |

---

## Refactor Prerequisites

1. Create root `.gitignore` (pyc / logs / backups)
2. Fix `api.py:522-524` daily boundary bug — use `TIMEZONE`-aware today
3. Standardize backend `datetime.now()` to `get_current_time()`
4. Add `dayjs-plugin-utc` + `dayjs-plugin-timezone` to frontend
5. Replace `datetime.utcnow()` in tests (deprecated Python 3.12+)

---

## Recommended Implementation Order

### Phase 1 — Quick wins (no schema change, low risk)
1. Create root `.gitignore`
2. Fix `api.py:522-524` daily boundary (use Asia/Taipei today)
3. Replace `datetime.utcnow()` in test fixtures

### Phase 2 — Backend standardization (medium risk)
4. Standardize all `datetime.now(timezone.utc)` in business events to `get_current_time()`
5. Add explicit timezone to `AllowedLocation` DateTime columns

### Phase 3 — Frontend (low risk)
6. Install dayjs timezone plugin
7. Add explicit `tz('Asia/Taipei')` to all `dayjs()` calls
8. Replace `new Date()` with dayjs equivalents

### Phase 4 — Validation
9. Run full test suite
10. Manual QA for break punches around midnight
11. Cross-midnight session display test
