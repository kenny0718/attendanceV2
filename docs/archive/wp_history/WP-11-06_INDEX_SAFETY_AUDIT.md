# Attendance Index Safety Audit Report

**日期：** 2026-03-13  
**類型：** Analysis Only — No Code Changes

---

## 1. Index Inventory

### attendance_sessions

| Index | Columns | Type | Purpose |
|-------|---------|------|---------|
| `idx_sessions_company_id` | `company_id` | BTree | Tenant isolation |
| `idx_sessions_user_id` | `user_id` | BTree | Per-user queries |
| `idx_sessions_company_user` | `company_id, user_id` | BTree | User history per company |
| `idx_sessions_company_punch_in` | `company_id, punch_in_time` | BTree | **Reporting range queries** |
| `idx_sessions_status_open` | `status` WHERE open | Partial BTree | Open session lookup |
| `uq_sessions_company_user_open` | `company_id, user_id` WHERE open | Unique Partial | Business invariant |

### attendance_punches

| Index | Columns | Type | Purpose |
|-------|---------|------|---------|
| `idx_punches_session_id` | `session_id` | BTree | Session punch lookup |
| `idx_punches_company_id` | `company_id` | BTree | Tenant isolation |
| `idx_punches_user_id` | `user_id` | BTree | Per-user queries |
| `idx_punches_company_time` | `company_id, punch_time` | BTree | Time range queries |
| `idx_punches_type` | `punch_type` | BTree | Type filter |
| `idx_punches_location` | `location_id` | BTree | Location join (WP-11-13) |

### attendance_out_checkpoints

| Index | Columns | Type | Purpose |
|-------|---------|------|---------|
| `idx_checkpoints_company_id` | `company_id` | BTree | Tenant isolation |
| `idx_checkpoints_user_id` | `user_id` | BTree | Per-user queries |
| `idx_checkpoints_company_user_time` | `company_id, user_id, punch_time DESC` | BTree | User checkpoint history |
| `idx_checkpoints_session_id` | `session_id` WHERE NOT NULL | Partial BTree | Session lookup |
| `idx_checkpoints_gps` | `gps_lat, gps_lng` WHERE NOT NULL | Partial BTree | GPS queries |

---

## 2. Safe Query Patterns

| Pattern | Uses Index? | Notes |
|---------|-------------|-------|
| `WHERE company_id = ? AND punch_in_time >= start_utc AND punch_in_time < end_utc` | YES | Hits `idx_sessions_company_punch_in`; Index Range Scan |
| `WHERE company_id = ? AND user_id = ?` | YES | Hits `idx_sessions_company_user` |
| `WHERE company_id = ? AND user_id = ? AND punch_in_time >= ? AND punch_in_time < ?` | YES | Planner picks best of two indexes |
| `WHERE company_id = ? AND status = 'closed'` | YES | `idx_sessions_company_id` + status filter |
| `WHERE company_id = ? AND punch_time >= ? AND punch_time < ?` (punches) | YES | `idx_punches_company_time` |
| `ORDER BY punch_in_time DESC LIMIT n` | YES | `idx_sessions_company_punch_in` covers punch_in_time |

### 現有實作驗證

**GET /break-punches (api.py:282-292):**
```python
today = date.today()
start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
end_of_day = start_of_day + timedelta(days=1)

db.query(AttendancePunch).filter(
    AttendancePunch.company_id == company_id,
    AttendancePunch.user_id == user_uuid,
    AttendancePunch.punch_type.in_(["break_start", "break_end"]),
    AttendancePunch.punch_time >= start_of_day,
    AttendancePunch.punch_time < end_of_day
)
```

- Index: hits `idx_punches_company_time`
- Risk: `date.today()` uses server local time (UTC), not Asia/Taipei. Display correctness issue at midnight, not an index issue.

**GET /history (repo.py:150-180):**
```python
db.query(AttendanceSession).filter(
    AttendanceSession.company_id == company_id,
    AttendanceSession.user_id == user_uuid
).order_by(AttendanceSession.punch_in_time.desc()).limit(limit).offset(offset)
```

- Index: hits `idx_sessions_company_user`
- Safe: no function wrapping

---

## 3. Dangerous Patterns

| Pattern | Risk | Why |
|---------|------|-----|
| `DATE(punch_in_time AT TIME ZONE 'Asia/Taipei')` in WHERE | HIGH | Function wraps indexed column; PostgreSQL cannot use BTree; full table scan |
| `DATE(punch_in_time)` in WHERE | HIGH | Same; also ignores timezone |
| `EXTRACT(MONTH FROM punch_in_time)` in WHERE | HIGH | Function wraps indexed column; full table scan |
| `CAST(punch_in_time AS DATE)` in WHERE | HIGH | Type cast wraps indexed column; full table scan |
| `func.date(AttendanceSession.punch_in_time)` in SQLAlchemy WHERE | HIGH | Equivalent to SQL DATE(); index skip |
| `punch_out_time BETWEEN start AND end` for reporting | HIGH | (1) NULL for open sessions excluded silently; (2) cross-midnight sessions mis-attributed; (3) no index on punch_out_time alone |
| `DATE(punch_out_time)` for report date | HIGH | Wrong semantics + NULL risk + function wrapping |
| `GROUP BY DATE(punch_in_time AT TIME ZONE ...)` in WHERE | MEDIUM | GROUP BY alone doesn't break WHERE index, but if also used in WHERE it causes index skip |

### Why DATE() breaks BTree indexes

PostgreSQL BTree stores raw column values (`timestamptz`). When a function wraps an indexed column in WHERE, PostgreSQL cannot perform an index range scan because the index does not contain precomputed function results. It must evaluate the function for every row: full table scan.

**Safe equivalent:**
```sql
-- DANGEROUS: function wraps indexed column
WHERE DATE(punch_in_time AT TIME ZONE 'Asia/Taipei') = '2026-03-15'

-- SAFE: precompute UTC boundaries, compare raw column
WHERE punch_in_time >= '2026-03-14 16:00:00+00'
  AND punch_in_time <  '2026-03-15 16:00:00+00'
```

### Why punch_out_time is triple-dangerous for reporting

1. **NULL risk**: open sessions have NULL punch_out_time; BETWEEN silently excludes them
2. **Semantic error**: cross-midnight sessions should belong to punch_in date, not punch_out date
3. **No index**: no `idx_sessions_company_punch_out` exists; forces full table scan

---

## 4. GROUP BY Risk

### Current design: Python-layer grouping

```python
from collections import defaultdict
from zoneinfo import ZoneInfo
TZ_TAIPEI = ZoneInfo("Asia/Taipei")

# WHERE uses UTC boundaries (index-safe)
sessions = db.query(AttendanceSession).filter(
    AttendanceSession.company_id == company_id,
    AttendanceSession.punch_in_time >= month_start_utc,
    AttendanceSession.punch_in_time < month_end_utc
).all()

# GROUP BY in Python (safe; index already used for WHERE)
by_date = defaultdict(list)
for s in sessions:
    by_date[s.punch_in_time.astimezone(TZ_TAIPEI).date()].append(s)
```

- WHERE clause: index-safe
- Python grouping: safe; does not affect SQL index usage

### Scale risk for Python-layer grouping

| Scale | Rows/month | Python grouping | Action |
|-------|-----------|-----------------|--------|
| 50 employees x 22 days | ~1,100 | Safe (<1MB) | No action |
| 500 employees x 22 days | ~11,000 | Safe (<5MB) | Monitor |
| 5,000 employees x 22 days | ~110,000 | Pressure (~50MB) | Consider SQL aggregation |
| 50,000 employees x 22 days | ~1,100,000 | Not acceptable | Needs session_date column |

### Safe SQL GROUP BY (when needed)

```sql
-- SAFE: filter first (index hit), then aggregate by user
SELECT user_id,
       SUM(duration_minutes) AS total_minutes,
       COUNT(*) AS session_count
FROM attendance_sessions
WHERE company_id = ?
  AND punch_in_time >= ?   -- UTC boundary, index hit
  AND punch_in_time <  ?
GROUP BY user_id           -- no function on punch_in_time here

-- DANGEROUS: function in WHERE causes index skip
SELECT DATE(punch_in_time AT TIME ZONE 'Asia/Taipei') AS day, COUNT(*)
FROM attendance_sessions
WHERE DATE(punch_in_time AT TIME ZONE 'Asia/Taipei') BETWEEN ? AND ?
GROUP BY DATE(punch_in_time AT TIME ZONE 'Asia/Taipei')
```

---

## 5. Pagination and Summary Queries

### List queries

```python
# GET /history - repo.get_sessions()
db.query(AttendanceSession).filter(
    AttendanceSession.company_id == company_id,
    AttendanceSession.user_id == user_uuid
).order_by(AttendanceSession.punch_in_time.desc()).limit(limit).offset(offset)
```

- Index: `idx_sessions_company_user` + `idx_sessions_company_punch_in`
- Safe: no function wrapping
- Note: large OFFSET (e.g. 5000) degrades performance; keyset pagination recommended at scale but not urgent now

### Monthly summary queries (planned)

```python
sessions = db.query(AttendanceSession).filter(
    AttendanceSession.company_id == company_id,
    AttendanceSession.punch_in_time >= month_start_utc,
    AttendanceSession.punch_in_time < month_end_utc,
    AttendanceSession.status == 'closed'
).all()
total = sum(s.duration_minutes for s in sessions if s.duration_minutes)
```

- Index: `idx_sessions_company_punch_in`
- Safe: UTC boundary comparison, reads canonical field

### User summary queries (planned)

```python
sessions = db.query(AttendanceSession).filter(
    AttendanceSession.company_id == company_id,
    AttendanceSession.user_id == user_id,
    AttendanceSession.punch_in_time >= month_start_utc,
    AttendanceSession.punch_in_time < month_end_utc
).all()
```

- Index: planner chooses between `idx_sessions_company_user` and `idx_sessions_company_punch_in`
- Safe

---

## 6. Final Verdict

### MINOR RISK — safe now but guardrails required

**Safe because:**
- All existing queries use UTC datetime boundary comparison; indexes are hit
- No `DATE()`, `EXTRACT()`, `AT TIME ZONE` in any WHERE clause
- `duration_minutes` canonical field correctly written on punch_out

**Minor risk because:**
- `GET /break-punches` uses `date.today()` (server UTC, not Asia/Taipei) — display correctness issue at midnight boundary
- Reporting module (WP-11-06) not yet implemented; future developer may introduce function wrapping
- No `session_date` column; SQL-level daily GROUP BY requires function conversion (dangerous) or Python-layer grouping

---

## 7. Guardrails

All future reporting queries must follow these rules:

### Required rules

**Rule 1: Use UTC boundaries for date range filters**
```python
# Correct
month_start_utc = datetime(year, month, 1, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
WHERE punch_in_time >= month_start_utc AND punch_in_time < month_end_utc
```

**Rule 2: Compute month boundaries in Asia/Taipei, then convert to UTC**
```python
from zoneinfo import ZoneInfo
TZ_TAIPEI = ZoneInfo("Asia/Taipei")
month_start_utc = datetime(year, month, 1, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
```

**Rule 3: Read canonical duration_minutes field**
```python
# Correct
total = sum(s.duration_minutes for s in sessions if s.duration_minutes)
# Forbidden
total = sum((s.punch_out_time - s.punch_in_time).total_seconds()/60 for s in sessions)
```

**Rule 4: Daily grouping in Python layer, not SQL function
```python
from collections import defaultdict
by_date = defaultdict(list)
for s in sessions:
    by_date[s.punch_in_time.astimezone(TZ_TAIPEI).date()].append(s)
```

**Rule 5: Use TZ_TAIPEI for today, not date.today()**
```python
# Correct
today_taipei = datetime.now(ZoneInfo("Asia/Taipei")).date()
# Forbidden
today = date.today()  # depends on server local time
```

### Forbidden patterns

```sql
-- Forbidden 1: function wraps indexed column
WHERE DATE(punch_in_time AT TIME ZONE 'Asia/Taipei') = '2026-03-15'

-- Forbidden 2: EXTRACT wraps indexed column
WHERE EXTRACT(MONTH FROM punch_in_time) = 3

-- Forbidden 3: CAST wraps indexed column
WHERE CAST(punch_in_time AS DATE) = '2026-03-15'

-- Forbidden 4: punch_out_time for report ownership
WHERE punch_out_time BETWEEN start AND end

-- Forbidden 5: DATE(punch_out_time)
WHERE DATE(punch_out_time) = '2026-03-15'

-- Forbidden 6: recompute work hours in report layer
SELECT punch_out_time - punch_in_time AS work_hours
```

---

**Audit completed:** 2026-03-13
**Type:** Analysis Only
