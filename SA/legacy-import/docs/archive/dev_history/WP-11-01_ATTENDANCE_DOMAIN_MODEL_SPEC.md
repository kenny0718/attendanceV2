# WP-11-01 — Attendance Domain Model Specification

**Gate**: 5 (Attendance Core APIs)  
**Status**: Phase A — Specification Only  
**Auth Model**: 🔒 FROZEN (Gate 4 closed)

---

## Step 0 — Inventory Report

### Existing Attendance Infrastructure

#### ✅ Migration Files
- `001_create_attendance_records.py` — **EXISTS** (舊版 schema)
  - Table: `attendance_records`
  - Columns: `id`, `company_id`, `employee_id`, `approved_by`, `approved_at`, `created_at`
  - Indexes: `idx_attendance_company_id`, `idx_attendance_company_created`

#### ✅ Models
- `backend/app/modules/attendance/models.py` — **EXISTS** (舊版 model)
  - Class: `AttendanceRecord`
  - 使用 UUID 主鍵
  - 包含 `company_id` (tenant isolation)
  - **問題**: 缺少 punch in/out 概念，只有 approval 欄位

#### ✅ Repository
- `backend/app/modules/attendance/repo.py` — **EXISTS**
  - Methods: `create_attendance_record()`, `approve_attendance_record()`, `get_attendance_records()`
  - 已實作 tenant isolation (強制 `WHERE company_id = ?`)
  - 已整合 tenant validation (Phase 9)

#### ✅ Tests
- `test_tenant_isolation.py` — 測試跨公司隔離
- `test_tenant_validation.py` — 測試 tenant 驗證
- `test_api.py` — API 端點測試
- `test_phase4.py` — Phase 4 整合測試

### Gap Analysis

#### ❌ 缺少的核心概念

1. **Punch In/Out 機制**
   - 現有 schema 只有 `approved_by`/`approved_at`，沒有打卡時間戳
   - 缺少 punch type (in/out/break_start/break_end)
   - 缺少 punch location (IP, geolocation)

2. **Attendance Session 概念**
   - 缺少「一個員工同時只能有一個 open session」的約束
   - 缺少 session 狀態管理 (open/closed)
   - 缺少 session duration 計算

3. **Policy 關聯**
   - 缺少 attendance policy 表
   - 缺少 policy 與 record 的關聯

4. **Audit Trail**
   - 缺少 punch 操作的 metadata (device, IP, user agent)
   - 缺少 modification history

### Recommendation

**方案**: 重寫 migration 001 (允許，因為未上線)

**理由**:
- 現有 schema 不符合 Gate 5 需求 (缺少 punch 概念)
- 系統尚未上線，無歷史資料
- 重寫比增量修改更清晰

**策略**:
1. 刪除舊 migration `001_create_attendance_records.py`
2. 建立新 migration `001_create_attendance_domain_v2.py`
3. 保留 repo/service 介面 (向後相容)
4. 更新 models.py 以反映新 schema

---

## Step 1 — Domain Model Specification

### Design Principles (Platform-First v2)

1. **Auth is Frozen** 🔒
   - 不修改 `users`, `user_company_memberships`, `roles` 表
   - 使用 FK 引用 frozen auth tables (read-only)
   - Company scope 來自 JWT `company_id` claim

2. **Tenant Isolation (P0)**
   - 所有 attendance tables 必須包含 `company_id`
   - 所有查詢必須強制 `WHERE company_id = ?`
   - 使用 `tenant_context.get_current_company_id()` 注入

3. **User Identity (Global)**
   - 使用 `user_id` (UUID) 引用 `users.id`
   - 不使用 `employee_id` (string) — 改用 `user_id`
   - 透過 `user_company_memberships` 驗證 user 屬於 company

4. **Business Invariant**
   - **核心規則**: 同一 `(company_id, user_id)` 同時只能有一個 open session
   - 必須在 punch in 前檢查是否有 open session
   - Punch out 會關閉 session

---

## Table 1: `attendance_sessions`

### Purpose
記錄員工的出勤 session（一次完整的上班週期：punch in → punch out）

### Schema

| Column | Type | Nullable | Default | Constraints | Comment |
|--------|------|----------|---------|-------------|---------|
| `id` | UUID | NOT NULL | `uuid_generate_v4()` | PK | Session ID |
| `company_id` | VARCHAR(255) | NOT NULL | - | FK → `tenants.id` | 公司 ID (tenant isolation) |
| `user_id` | UUID | NOT NULL | - | FK → `users.id` | 員工 ID (global user) |
| `punch_in_time` | TIMESTAMPTZ | NOT NULL | - | - | 打卡上班時間 (UTC) |
| `punch_out_time` | TIMESTAMPTZ | NULL | - | - | 打卡下班時間 (UTC, NULL = open session) |
| `status` | VARCHAR(20) | NOT NULL | `'open'` | CHECK IN ('open', 'closed') | Session 狀態 |
| `duration_minutes` | INTEGER | NULL | - | - | 工作時長 (分鐘, computed on close) |
| `policy_id` | UUID | NULL | - | FK → `attendance_policies.id` | 適用的考勤政策 (可選) |
| `notes` | TEXT | NULL | - | - | 備註 (員工或管理員填寫) |
| `created_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | - | 建立時間 (UTC) |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | - | 更新時間 (UTC) |

### Foreign Keys

```sql
FOREIGN KEY (company_id) REFERENCES tenants(id) ON DELETE CASCADE
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
FOREIGN KEY (policy_id) REFERENCES attendance_policies(id) ON DELETE SET NULL
```

### Indexes

```sql
-- Tenant isolation (P0)
CREATE INDEX idx_sessions_company_id ON attendance_sessions(company_id);

-- Query by user (P0)
CREATE INDEX idx_sessions_user_id ON attendance_sessions(user_id);

-- Query by company + user (P0)
CREATE INDEX idx_sessions_company_user ON attendance_sessions(company_id, user_id);

-- Query by company + date range (P1)
CREATE INDEX idx_sessions_company_punch_in ON attendance_sessions(company_id, punch_in_time);

-- Query open sessions (P0)
CREATE INDEX idx_sessions_status ON attendance_sessions(status) WHERE status = 'open';
```

### Unique Constraints

#### Option A: Partial Unique Index (Recommended)

```sql
-- 同一 (company_id, user_id) 只能有一個 open session
CREATE UNIQUE INDEX uq_sessions_company_user_open 
ON attendance_sessions(company_id, user_id) 
WHERE status = 'open';
```

**優點**:
- Database-level enforcement (最強保證)
- 自動防止 race condition
- 無需額外 application logic

**缺點**:
- PostgreSQL 特定語法 (partial index)
- 需要 PostgreSQL 9.0+

#### Option B: Application-Level Guard

```python
# In service layer
def punch_in(company_id: str, user_id: UUID):
    # Check for open session
    open_session = repo.get_open_session(company_id, user_id)
    if open_session:
        raise HTTPException(409, "User already has an open session")
    
    # Create new session
    return repo.create_session(company_id, user_id)
```

**優點**:
- Database-agnostic
- 可自訂錯誤訊息

**缺點**:
- Race condition risk (需要 transaction isolation)
- 需要額外測試

**Decision**: 使用 **Option A (Partial Unique Index)** + Application-level check (防禦性編程)

---

## Table 2: `attendance_punches`

### Purpose
記錄所有打卡事件（包含 punch in, punch out, break start, break end）

### Schema

| Column | Type | Nullable | Default | Constraints | Comment |
|--------|------|----------|---------|-------------|---------|
| `id` | UUID | NOT NULL | `uuid_generate_v4()` | PK | Punch ID |
| `session_id` | UUID | NOT NULL | - | FK → `attendance_sessions.id` | 所屬 session |
| `company_id` | UUID | NOT NULL | - | FK → `tenants.id` | 公司 ID (denormalized for isolation) |
| `user_id` | UUID | NOT NULL | - | FK → `users.id` | 員工 ID (denormalized for queries) |
| `punch_type` | VARCHAR(20) | NOT NULL | - | CHECK IN ('in', 'out', 'break_start', 'break_end') | 打卡類型 |
| `punch_time` | TIMESTAMPTZ | NOT NULL | `NOW()` | - | 打卡時間 (UTC) |
| `ip_address` | VARCHAR(45) | NULL | - | - | IP 地址 (IPv4/IPv6) |
| `user_agent` | TEXT | NULL | - | - | User Agent (device info) |
| `location_lat` | DECIMAL(10,8) | NULL | - | - | 緯度 (可選) |
| `location_lng` | DECIMAL(11,8) | NULL | - | - | 經度 (可選) |
| `device_id` | VARCHAR(255) | NULL | - | - | 裝置 ID (mobile app) |
| `photo_url` | TEXT | NULL | - | - | 打卡照片 URL (可選) |
| `notes` | TEXT | NULL | - | - | 備註 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | - | 建立時間 (UTC) |

### Foreign Keys

```sql
FOREIGN KEY (session_id) REFERENCES attendance_sessions(id) ON DELETE CASCADE
FOREIGN KEY (company_id) REFERENCES tenants(id) ON DELETE CASCADE
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
```

### Indexes

```sql
-- Query by session (P0)
CREATE INDEX idx_punches_session_id ON attendance_punches(session_id);

-- Tenant isolation (P0)
CREATE INDEX idx_punches_company_id ON attendance_punches(company_id);

-- Query by user (P1)
CREATE INDEX idx_punches_user_id ON attendance_punches(user_id);

-- Query by company + time range (P1)
CREATE INDEX idx_punches_company_time ON attendance_punches(company_id, punch_time);

-- Query by punch type (P2)
CREATE INDEX idx_punches_type ON attendance_punches(punch_type);
```

### Design Notes

**Why denormalize `company_id` and `user_id`?**
- Performance: 避免 JOIN `attendance_sessions` 才能過濾 company
- Tenant Isolation: 直接在 `attendance_punches` 上強制 `WHERE company_id = ?`
- Audit: 即使 session 被刪除，punch 記錄仍保留完整 context

---

## Table 3: `attendance_policies`

### Purpose
定義公司的考勤政策（工作時間、遲到寬限、加班規則等）

### Schema

| Column | Type | Nullable | Default | Constraints | Comment |
|--------|------|----------|---------|-------------|---------|
| `id` | UUID | NOT NULL | `uuid_generate_v4()` | PK | Policy ID |
| `company_id` | VARCHAR(255) | NOT NULL | - | FK → `tenants.id` | 公司 ID |
| `name` | VARCHAR(255) | NOT NULL | - | - | 政策名稱 (e.g., "標準工時") |
| `description` | TEXT | NULL | - | - | 政策說明 |
| `work_start_time` | TIME | NOT NULL | - | - | 標準上班時間 (e.g., 09:00) |
| `work_end_time` | TIME | NOT NULL | - | - | 標準下班時間 (e.g., 18:00) |
| `grace_period_minutes` | INTEGER | NOT NULL | `0` | - | 遲到寬限時間 (分鐘) |
| `overtime_threshold_minutes` | INTEGER | NULL | - | - | 加班認定門檻 (分鐘) |
| `is_active` | BOOLEAN | NOT NULL | `true` | - | 是否啟用 |
| `is_default` | BOOLEAN | NOT NULL | `false` | - | 是否為預設政策 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | - | 建立時間 (UTC) |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | - | 更新時間 (UTC) |

### Foreign Keys

```sql
FOREIGN KEY (company_id) REFERENCES tenants(id) ON DELETE CASCADE
```

### Indexes

```sql
-- Tenant isolation (P0)
CREATE INDEX idx_policies_company_id ON attendance_policies(company_id);

-- Query active policies (P0)
CREATE INDEX idx_policies_company_active ON attendance_policies(company_id, is_active);

-- Query default policy (P1)
CREATE INDEX idx_policies_company_default ON attendance_policies(company_id, is_default) WHERE is_default = true;
```

### Unique Constraints

```sql
-- 每個公司只能有一個預設政策
CREATE UNIQUE INDEX uq_policies_company_default 
ON attendance_policies(company_id) 
WHERE is_default = true;
```

### Design Notes

**Scope for WP-11-01**:
- 只建立 table schema
- 不實作 policy evaluation engine (deferred to WP-11-03)
- 不實作 policy CRUD APIs (deferred to WP-11-03)

---

## Core Business Invariant

### Invariant 1: One Open Session Per User Per Company

**Rule**: 同一 `(company_id, user_id)` 同時只能有一個 `status = 'open'` 的 session

**Enforcement Method**: Partial Unique Index (Database-level)

```sql
CREATE UNIQUE INDEX uq_sessions_company_user_open 
ON attendance_sessions(company_id, user_id) 
WHERE status = 'open';
```

**Application-Level Guard** (防禦性編程):

```python
def punch_in(company_id: str, user_id: UUID, db: Session):
    # Check for open session
    open_session = db.query(AttendanceSession).filter(
        AttendanceSession.company_id == company_id,
        AttendanceSession.user_id == user_id,
        AttendanceSession.status == 'open'
    ).first()
    
    if open_session:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "User already has an open attendance session",
                "open_session_id": str(open_session.id),
                "punch_in_time": open_session.punch_in_time.isoformat()
            }
        )
    
    # Create new session
    session = AttendanceSession(
        company_id=company_id,
        user_id=user_id,
        punch_in_time=datetime.utcnow(),
        status='open'
    )
    db.add(session)
    db.commit()
    return session
```

**Test Plan**:

```python
def test_one_open_session_per_user():
    """測試：同一 user 不能同時有兩個 open session"""
    # 1. User punches in (creates open session)
    session1 = punch_in(company_id="company-a", user_id=user_id)
    assert session1.status == "open"
    
    # 2. User tries to punch in again (should fail)
    with pytest.raises(HTTPException) as exc:
        punch_in(company_id="company-a", user_id=user_id)
    assert exc.value.status_code == 409
    
    # 3. User punches out (closes session)
    punch_out(company_id="company-a", user_id=user_id, session_id=session1.id)
    
    # 4. User can now punch in again
    session2 = punch_in(company_id="company-a", user_id=user_id)
    assert session2.status == "open"
    assert session2.id != session1.id
```

### Invariant 2: Punch Out Requires Open Session

**Rule**: 只能對 `status = 'open'` 的 session 執行 punch out

**Enforcement Method**: Application-level check

```python
def punch_out(company_id: str, user_id: UUID, session_id: UUID, db: Session):
    # Find open session
    session = db.query(AttendanceSession).filter(
        AttendanceSession.id == session_id,
        AttendanceSession.company_id == company_id,
        AttendanceSession.user_id == user_id,
        AttendanceSession.status == 'open'
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail={"error": "No open session found"}
        )
    
    # Close session
    session.punch_out_time = datetime.utcnow()
    session.status = 'closed'
    session.duration_minutes = int(
        (session.punch_out_time - session.punch_in_time).total_seconds() / 60
    )
    db.commit()
    return session
```

### Invariant 3: Tenant Isolation

**Rule**: 所有查詢必須強制 `WHERE company_id = ?`

**Enforcement Method**: Repository pattern + tenant_context

```python
class AttendanceSessionRepository:
    def get_sessions(self, company_id: str, user_id: UUID):
        # MUST include company_id filter
        return self.db.query(AttendanceSession).filter(
            AttendanceSession.company_id == company_id,
            AttendanceSession.user_id == user_id
        ).all()
    
    def get_session_by_id(self, company_id: str, session_id: UUID):
        # MUST include company_id filter
        return self.db.query(AttendanceSession).filter(
            AttendanceSession.id == session_id,
            AttendanceSession.company_id == company_id
        ).first()
```

---

## Migration Strategy

### Phase A: Specification (Current)
- ✅ Document domain model
- ✅ Define tables, columns, indexes, constraints
- ✅ Define business invariants
- ✅ Define test plan

### Phase B: Implementation (Next)
1. Delete old migration `001_create_attendance_records.py`
2. Create new migration `001_create_attendance_domain_v2.py`
   - Create `attendance_sessions` table
   - Create `attendance_punches` table
   - Create `attendance_policies` table
   - Create indexes and constraints
3. Update `models.py`
   - Define `AttendanceSession` model
   - Define `AttendancePunch` model
   - Define `AttendancePolicy` model
4. Update `repo.py`
   - Implement session CRUD
   - Implement punch CRUD
   - Implement policy CRUD (basic)
5. Write tests
   - Model constraint tests
   - Migration upgrade/downgrade tests
   - Business invariant tests

---

## Test Plan

### Test Category 1: Model Constraints

```python
def test_session_requires_company_id():
    """測試：session 必須有 company_id"""
    with pytest.raises(IntegrityError):
        session = AttendanceSession(user_id=user_id, punch_in_time=now)
        db.add(session)
        db.commit()

def test_session_requires_user_id():
    """測試：session 必須有 user_id"""
    with pytest.raises(IntegrityError):
        session = AttendanceSession(company_id="company-a", punch_in_time=now)
        db.add(session)
        db.commit()

def test_session_status_check_constraint():
    """測試：session status 只能是 'open' 或 'closed'"""
    with pytest.raises(IntegrityError):
        session = AttendanceSession(
            company_id="company-a",
            user_id=user_id,
            punch_in_time=now,
            status="invalid"
        )
        db.add(session)
        db.commit()
```

### Test Category 2: Migration Upgrade/Downgrade

```python
def test_migration_upgrade():
    """測試：migration upgrade 成功建立所有 tables"""
    # Run upgrade
    alembic_upgrade("head")
    
    # Verify tables exist
    assert table_exists("attendance_sessions")
    assert table_exists("attendance_punches")
    assert table_exists("attendance_policies")
    
    # Verify indexes exist
    assert index_exists("idx_sessions_company_id")
    assert index_exists("uq_sessions_company_user_open")

def test_migration_downgrade():
    """測試：migration downgrade 成功刪除所有 tables"""
    # Run upgrade first
    alembic_upgrade("head")
    
    # Run downgrade
    alembic_downgrade("-1")
    
    # Verify tables removed
    assert not table_exists("attendance_sessions")
    assert not table_exists("attendance_punches")
    assert not table_exists("attendance_policies")
```

### Test Category 3: Business Invariant

```python
def test_one_open_session_per_user_database_level():
    """測試：database 層級防止同一 user 有兩個 open session"""
    # Create first open session
    session1 = AttendanceSession(
        company_id="company-a",
        user_id=user_id,
        punch_in_time=now,
        status="open"
    )
    db.add(session1)
    db.commit()
    
    # Try to create second open session (should fail at DB level)
    with pytest.raises(IntegrityError) as exc:
        session2 = AttendanceSession(
            company_id="company-a",
            user_id=user_id,
            punch_in_time=now,
            status="open"
        )
        db.add(session2)
        db.commit()
    
    assert "uq_sessions_company_user_open" in str(exc.value)

def test_different_companies_can_have_open_sessions():
    """測試：同一 user 在不同 company 可以有 open session"""
    # User has open session in company A
    session_a = AttendanceSession(
        company_id="company-a",
        user_id=user_id,
        punch_in_time=now,
        status="open"
    )
    db.add(session_a)
    db.commit()
    
    # User can have open session in company B (different company)
    session_b = AttendanceSession(
        company_id="company-b",
        user_id=user_id,
        punch_in_time=now,
        status="open"
    )
    db.add(session_b)
    db.commit()  # Should succeed
    
    assert session_a.id != session_b.id

def test_closed_session_allows_new_open_session():
    """測試：closed session 後可以建立新的 open session"""
    # Create and close first session
    session1 = AttendanceSession(
        company_id="company-a",
        user_id=user_id,
        punch_in_time=now,
        status="open"
    )
    db.add(session1)
    db.commit()
    
    session1.status = "closed"
    session1.punch_out_time = now + timedelta(hours=8)
    db.commit()
    
    # Create new open session (should succeed)
    session2 = AttendanceSession(
        company_id="company-a",
        user_id=user_id,
        punch_in_time=now + timedelta(days=1),
        status="open"
    )
    db.add(session2)
    db.commit()  # Should succeed
    
    assert session2.id != session1.id
```

---

## Downgrade Strategy

### Rollback Plan

If Gate 5 needs to be rolled back:

1. **Migration Downgrade**
   ```bash
   alembic downgrade -1  # Remove attendance domain tables
   ```

2. **Code Rollback**
   - Revert `models.py` changes
   - Revert `repo.py` changes
   - Revert API changes (WP-11-02)

3. **Data Loss**
   - ⚠️ All attendance sessions/punches will be lost
   - Acceptable: System not in production yet

### Forward Compatibility

If we need to extend the schema later:

- Add new columns with `NULL` or `DEFAULT` values
- Add new tables (no impact on existing tables)
- Add new indexes (no data migration needed)

---

## Rationale

### Why Separate `attendance_sessions` and `attendance_punches`?

**Option A: Single Table (Rejected)**
```sql
CREATE TABLE attendance_records (
    id UUID PRIMARY KEY,
    punch_in_time TIMESTAMPTZ,
    punch_out_time TIMESTAMPTZ,
    break_start_time TIMESTAMPTZ,
    break_end_time TIMESTAMPTZ,
    ...
);
```

**Problems**:
- Difficult to handle multiple breaks
- Difficult to store punch metadata (IP, location) per event
- Difficult to audit individual punch events

**Option B: Two Tables (Selected)**
```sql
CREATE TABLE attendance_sessions (...);  -- One row per work day
CREATE TABLE attendance_punches (...);   -- Multiple rows per session
```

**Benefits**:
- Clear separation: session = business entity, punch = audit event
- Easy to add new punch types (break_start, break_end, etc.)
- Easy to store per-punch metadata
- Easy to query "all punches for a session"

### Why Denormalize `company_id` in `attendance_punches`?

**Normalized Approach (Rejected)**:
```sql
-- Query punches for company A
SELECT * FROM attendance_punches p
JOIN attendance_sessions s ON p.session_id = s.id
WHERE s.company_id = 'company-a';
```

**Denormalized Approach (Selected)**:
```sql
-- Query punches for company A (no JOIN needed)
SELECT * FROM attendance_punches
WHERE company_id = 'company-a';
```

**Benefits**:
- Performance: No JOIN needed for tenant isolation
- Security: Tenant isolation enforced at punch level
- Audit: Punch records retain company context even if session deleted

**Trade-off**:
- Storage: Extra 255 bytes per punch (acceptable)
- Consistency: Must ensure `punch.company_id == session.company_id` (enforced in application)

### Why Use Partial Unique Index?

**Alternative: Application-Level Check Only (Rejected)**
```python
# Race condition possible!
if has_open_session(user_id):
    raise Exception("Already has open session")
create_session(user_id)  # Another request might create session here
```

**Selected: Partial Unique Index**
```sql
CREATE UNIQUE INDEX uq_sessions_company_user_open 
ON attendance_sessions(company_id, user_id) 
WHERE status = 'open';
```

**Benefits**:
- Database-level enforcement (no race condition)
- Automatic error on violation
- No need for transaction isolation level tuning

**Trade-off**:
- PostgreSQL-specific (not portable to MySQL)
- Acceptable: We use PostgreSQL

---

## Non-Goals (Out of Scope for WP-11-01)

- ❌ API endpoints (deferred to WP-11-02)
- ❌ Policy evaluation engine (deferred to WP-11-03)
- ❌ Reports and aggregation (deferred to WP-11-04)
- ❌ Audit log integration (deferred to WP-11-05)
- ❌ Telegram bot (deferred to WP-11-06)
- ❌ Leave management integration (future gate)
- ❌ Shift scheduling (future gate)
- ❌ Overtime approval workflow (future gate)

---

## Next Steps

1. ✅ Review and approve this specification
2. ⏳ Proceed to Phase B: Implementation
   - Create migration `001_create_attendance_domain_v2.py`
   - Update models
   - Update repository
   - Write tests
3. ⏳ Proceed to WP-11-02: Punch In/Out API

---

## Approval

- [ ] Architecture Review
- [ ] Security Review (Tenant Isolation)
- [ ] Database Review (Indexes, Constraints)
- [ ] Product Review (Business Logic)

**Approved By**: _________________  
**Date**: _________________
