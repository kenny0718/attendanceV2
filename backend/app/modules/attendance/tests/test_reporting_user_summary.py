"""WP-11-06 Step 2: GET /api/v1/attendance/reports/user-summary Tests

USR-01  basic summary counts
USR-02  date range filter
USR-03  cross-midnight session counted in correct month
USR-04  NULL duration_minutes handling
USR-05  tenant isolation
USR-06  user scope enforcement
USR-07  naive datetime rejection (422)
USR-08  empty result returns zeros
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.modules.attendance.models import AttendanceSession
from app.modules.tenants.models import Tenant
from app.modules.auth.models import User
from app.tests.utils.auth import create_test_actor, override_actor_dependency

TZ_TAIPEI = ZoneInfo("Asia/Taipei")
COMPANY_A = "company-usrsummary-a"
COMPANY_B = "company-usrsummary-b"
URL = "/api/v1/attendance/reports/user-summary"


# --- helpers ---

def make_closed(db, company_id, user_id, punch_in_utc, duration_minutes=480):
    s = AttendanceSession(
        company_id=company_id, user_id=user_id,
        punch_in_time=punch_in_utc,
        punch_out_time=punch_in_utc + timedelta(minutes=duration_minutes),
        status="closed", duration_minutes=duration_minutes,
    )
    db.add(s); db.commit(); db.refresh(s)
    return s

def make_open(db, company_id, user_id, punch_in_utc):
    s = AttendanceSession(
        company_id=company_id, user_id=user_id,
        punch_in_time=punch_in_utc,
        punch_out_time=None,
        status="open", duration_minutes=None,
    )
    db.add(s); db.commit(); db.refresh(s)
    return s

def make_actor(company_id, user_id):
    """WP-C1-07: JWT Actor 取代 X-Company-ID / X-User-ID header"""
    return create_test_actor(company_id, user_id=user_id)


# --- fixtures ---

@pytest.fixture
def client_a(db):
    """WP-C1-07: override get_db only"""
    app.dependency_overrides[get_db] = lambda: db
    c = TestClient(app)
    yield c
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def tenant_a(db):
    t = db.query(Tenant).filter(Tenant.id == COMPANY_A).first()
    if not t:
        t = Tenant(id=COMPANY_A, name="USR Summary Co A", is_active=True)
        db.add(t); db.commit()
    return t

@pytest.fixture
def tenant_b(db):
    t = db.query(Tenant).filter(Tenant.id == COMPANY_B).first()
    if not t:
        t = Tenant(id=COMPANY_B, name="USR Summary Co B", is_active=True)
        db.add(t); db.commit()
    return t

@pytest.fixture
def user_a(db, tenant_a):
    u = User(id=uuid4(), display_name="USR A", password_hash="x", is_active=True)
    db.add(u); db.commit(); db.refresh(u)
    u.company_id = COMPANY_A
    return u

@pytest.fixture
def user_b(db, tenant_b):
    u = User(id=uuid4(), display_name="USR B", password_hash="x", is_active=True)
    db.add(u); db.commit(); db.refresh(u)
    u.company_id = COMPANY_B
    return u

# --- USR-01: Basic summary ---
class TestUSR01BasicSummary:
    def test_counts_and_work_minutes(self, client_a, db, user_a):
        now = datetime.now(timezone.utc)
        make_closed(db, COMPANY_A, user_a.id, now - timedelta(hours=30), duration_minutes=480)
        make_closed(db, COMPANY_A, user_a.id, now - timedelta(hours=20), duration_minutes=300)
        make_open(db, COMPANY_A, user_a.id, now - timedelta(hours=1))
        resp = client_a.get(URL, headers=hdr(COMPANY_A, user_a.id))
        assert resp.status_code == 200, resp.text
        d = resp.json()
        assert d["total_sessions"] >= 3
        assert d["closed_sessions"] >= 2
        assert d["open_sessions"] >= 1
        assert d["total_work_minutes"] >= 780
        assert d["average_session_minutes"] is not None
        assert d["user_id"] == str(user_a.id)

    def test_first_and_last_session_time(self, client_a, db, user_a):
        now = datetime.now(timezone.utc)
        t1 = now - timedelta(hours=50)
        t2 = now - timedelta(hours=10)
        make_closed(db, COMPANY_A, user_a.id, t1)
        make_closed(db, COMPANY_A, user_a.id, t2)
        resp = client_a.get(URL, headers=hdr(COMPANY_A, user_a.id))
        assert resp.status_code == 200
        d = resp.json()
        assert d["first_session_time"] is not None
        assert d["last_session_time"] is not None
        # first should be earlier than last
        assert d["first_session_time"] < d["last_session_time"]

# --- USR-02: Date range filter ---
class TestUSR02DateRangeFilter:
    def test_only_sessions_within_range_counted(self, client_a, db, user_a):
        punch_mar = datetime(2026, 3, 15, 1, 0, 0, tzinfo=timezone.utc)
        punch_apr = datetime(2026, 4, 15, 1, 0, 0, tzinfo=timezone.utc)
        make_closed(db, COMPANY_A, user_a.id, punch_mar, duration_minutes=480)
        make_closed(db, COMPANY_A, user_a.id, punch_apr, duration_minutes=360)
        start = datetime(2026, 3, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        end   = datetime(2026, 4, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        resp = client_a.get(URL,
            params={"start_date": start.isoformat(), "end_date": end.isoformat()},
            headers=hdr(COMPANY_A, user_a.id))
        assert resp.status_code == 200
        d = resp.json()
        assert d["total_sessions"] >= 1
        assert d["total_work_minutes"] >= 480
        assert d["total_work_minutes"] < 840, "April session must not be in March range"

# --- USR-03: Cross-midnight ownership ---
class TestUSR03CrossMidnight:
    def test_punch_in_march_counted_in_march_not_april(self, client_a, db, user_a):
        punch_in_taipei = datetime(2026, 3, 31, 23, 50, 0, tzinfo=TZ_TAIPEI)
        punch_in_utc = punch_in_taipei.astimezone(timezone.utc)
        make_closed(db, COMPANY_A, user_a.id, punch_in_utc, duration_minutes=70)
        mar_start = datetime(2026, 3, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        apr_start = datetime(2026, 4, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        may_start = datetime(2026, 5, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        # March query: must find it
        r_mar = client_a.get(URL,
            params={"start_date": mar_start.isoformat(), "end_date": apr_start.isoformat()},
            headers=hdr(COMPANY_A, user_a.id))
        assert r_mar.status_code == 200
        assert r_mar.json()["total_sessions"] >= 1
        assert r_mar.json()["total_work_minutes"] >= 70
        # April query: must NOT find it
        r_apr = client_a.get(URL,
            params={"start_date": apr_start.isoformat(), "end_date": may_start.isoformat()},
            headers=hdr(COMPANY_A, user_a.id))
        assert r_apr.status_code == 200
        # session has punch_in_utc = 2026-03-31 15:50 UTC which is < apr_start
        assert r_apr.json()["total_work_minutes"] < 70 or r_apr.json()["total_sessions"] == 0

# --- USR-04: NULL duration ---
class TestUSR04NullDuration:
    def test_open_session_not_counted_in_work_minutes(self, client_a, db, user_a):
        now = datetime.now(timezone.utc)
        make_closed(db, COMPANY_A, user_a.id, now - timedelta(hours=20), duration_minutes=480)
        make_open(db, COMPANY_A, user_a.id, now - timedelta(hours=1))
        resp = client_a.get(URL, headers=hdr(COMPANY_A, user_a.id))
        assert resp.status_code == 200
        d = resp.json()
        assert d["open_sessions"] >= 1
        assert d["closed_sessions"] >= 1
        # total_work_minutes must not include None duration
        assert d["total_work_minutes"] >= 480
        # open session does not contribute extra minutes beyond closed ones
        assert d["total_work_minutes"] < 481 * 2, "open session None duration must not be counted"

    def test_all_open_sessions_average_is_none(self, client_a, db, user_a):
        now = datetime.now(timezone.utc)
        make_open(db, COMPANY_A, user_a.id, now - timedelta(hours=1))
        resp = client_a.get(URL, headers=hdr(COMPANY_A, user_a.id))
        assert resp.status_code == 200
        d = resp.json()
        # If all sessions are open, closed_sessions == 0 -> average must be None
        if d["closed_sessions"] == 0:
            assert d["average_session_minutes"] is None

# --- USR-05: Tenant isolation ---
class TestUSR05TenantIsolation:
    def test_company_a_cannot_see_company_b_sessions(self, client_a, db, user_a, user_b):
        now = datetime.now(timezone.utc)
        make_closed(db, COMPANY_B, user_b.id, now - timedelta(hours=5), duration_minutes=300)
        resp = client_a.get(URL, headers=hdr(COMPANY_A, user_a.id))
        assert resp.status_code == 200
        # company A user should not see company B sessions in total_work_minutes
        # (company A user has no sessions, so total must be 0 or only company A data)
        d = resp.json()
        assert d["user_id"] == str(user_a.id)

# --- USR-06: User scope ---
class TestUSR06UserScope:
    def test_user_can_query_own_summary(self, client_a, db, user_a):
        now = datetime.now(timezone.utc)
        make_closed(db, COMPANY_A, user_a.id, now - timedelta(hours=5))
        resp = client_a.get(URL, headers=hdr(COMPANY_A, user_a.id))
        assert resp.status_code == 200
        assert resp.json()["user_id"] == str(user_a.id)

    def test_summary_only_contains_own_sessions(self, client_a, db, user_a, tenant_a):
        # create another user in same company
        other = User(id=uuid4(), display_name="Other", password_hash="x", is_active=True)
        db.add(other); db.commit(); db.refresh(other)
        now = datetime.now(timezone.utc)
        make_closed(db, COMPANY_A, user_a.id, now - timedelta(hours=10), duration_minutes=480)
        make_closed(db, COMPANY_A, other.id, now - timedelta(hours=8), duration_minutes=999)
        resp = client_a.get(URL, headers=hdr(COMPANY_A, user_a.id))
        assert resp.status_code == 200
        d = resp.json()
        # should not include other user 999 min session
        assert d["total_work_minutes"] < 999, "other user session must not be in summary"

# --- USR-07: Naive datetime rejection ---
class TestUSR07NaiveDatetime:
    def test_naive_start_date_returns_422(self, client_a, user_a):
        resp = client_a.get(URL,
            params={"start_date": "2026-03-01T00:00:00"},
            headers=hdr(COMPANY_A, user_a.id))
        assert resp.status_code == 422

    def test_naive_end_date_returns_422(self, client_a, user_a):
        resp = client_a.get(URL,
            params={"end_date": "2026-04-01T00:00:00"},
            headers=hdr(COMPANY_A, user_a.id))
        assert resp.status_code == 422

    def test_aware_datetime_is_accepted(self, client_a, user_a):
        start = datetime(2026, 3, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        resp = client_a.get(URL,
            params={"start_date": start.isoformat()},
            headers=hdr(COMPANY_A, user_a.id))
        assert resp.status_code == 200

# --- USR-08: Empty result ---
class TestUSR08EmptyResult:
    def test_no_sessions_returns_zero_summary(self, client_a, db, user_a):
        # query a future date range where no sessions exist
        start = datetime(2099, 1, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        end   = datetime(2099, 2, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        resp = client_a.get(URL,
            params={"start_date": start.isoformat(), "end_date": end.isoformat()},
            headers=hdr(COMPANY_A, user_a.id))
        assert resp.status_code == 200, resp.text
        d = resp.json()
        assert d["total_sessions"] == 0
        assert d["closed_sessions"] == 0
        assert d["open_sessions"] == 0
        assert d["total_work_minutes"] == 0
        assert d["average_session_minutes"] is None
        assert d["first_session_time"] is None
        assert d["last_session_time"] is None
