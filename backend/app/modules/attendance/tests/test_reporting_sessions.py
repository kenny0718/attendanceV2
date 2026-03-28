"""WP-11-06 Step 1: GET /api/v1/attendance/sessions Tests

SES-01 basic pagination
SES-02 start_date/end_date date filter
SES-03 Taipei midnight punch_in ownership
SES-04 cross-month session ownership
SES-05 status filter
SES-06 tenant isolation
SES-07 user scope
SES-08 open session NULL duration_minutes
SES-09 limit boundary validation
SES-10 total count matches actual count
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
from app.tests.utils.auth import create_test_actor, create_super_admin_actor, override_actor_dependency

TZ_TAIPEI = ZoneInfo("Asia/Taipei")
COMPANY_A = "company-sessions-a"
COMPANY_B = "company-sessions-b"


# --- helpers ---

def make_closed_session(db, company_id, user_id, punch_in_utc, duration_minutes=480):
    punch_out_utc = punch_in_utc + timedelta(minutes=duration_minutes)
    s = AttendanceSession(
        company_id=company_id, user_id=user_id,
        punch_in_time=punch_in_utc, punch_out_time=punch_out_utc,
        status="closed", duration_minutes=duration_minutes,
    )
    db.add(s); db.commit(); db.refresh(s)
    return s

def make_open_session(db, company_id, user_id, punch_in_utc):
    s = AttendanceSession(
        company_id=company_id, user_id=user_id,
        punch_in_time=punch_in_utc, punch_out_time=None,
        status="open", duration_minutes=None,
    )
    db.add(s); db.commit(); db.refresh(s)
    return s

def make_actor(company_id, user_id):
    """WP-C1-07: 建立 JWT Actor 取代 X-Company-ID / X-User-ID header"""
    return create_test_actor(company_id, user_id=user_id)


def make_actor_with_role(company_id, user_id, role_id):
    """建立指定公司內角色的測試 Actor。"""
    return create_test_actor(company_id, user_id=user_id, role_id=role_id)


def make_super_admin_actor(company_id, user_id):
    """建立 super_admin 測試 Actor（帶 active company scope）。"""
    return create_super_admin_actor(company_id=company_id, user_id=user_id)


# --- fixtures ---

@pytest.fixture
def client_a(db):
    """WP-C1-07: override get_db only; auth override done per-test via override_actor_dependency"""
    app.dependency_overrides[get_db] = lambda: db
    c = TestClient(app)
    yield c
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def tenant_a(db):
    t = db.query(Tenant).filter(Tenant.id == COMPANY_A).first()
    if not t:
        t = Tenant(id=COMPANY_A, name="Reporting Test Co A", is_active=True)
        db.add(t); db.commit()
    return t

@pytest.fixture
def tenant_b(db):
    t = db.query(Tenant).filter(Tenant.id == COMPANY_B).first()
    if not t:
        t = Tenant(id=COMPANY_B, name="Reporting Test Co B", is_active=True)
        db.add(t); db.commit()
    return t

@pytest.fixture
def user_a(db, tenant_a):
    u = User(id=uuid4(), display_name="Rpt User A", password_hash="x", is_active=True)
    db.add(u); db.commit(); db.refresh(u)
    u.company_id = COMPANY_A
    return u

@pytest.fixture
def user_b(db, tenant_b):
    u = User(id=uuid4(), display_name="Rpt User B", password_hash="x", is_active=True)
    db.add(u); db.commit(); db.refresh(u)
    u.company_id = COMPANY_B
    return u


# --- SES-01: Basic pagination ---

class TestSES01BasicPagination:
    def test_returns_sessions_list_and_total(self, client_a, db, user_a):
        now = datetime.now(timezone.utc)
        make_closed_session(db, COMPANY_A, user_a.id, now - timedelta(hours=10))
        make_closed_session(db, COMPANY_A, user_a.id, now - timedelta(hours=5))
        resp = client_a.get("/api/v1/attendance/sessions",
            params={"limit": 10, "offset": 0},
            headers=hdr(COMPANY_A, user_a.id))
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "sessions" in data
        assert "total" in data
        assert data["limit"] == 10
        assert data["offset"] == 0
        assert data["total"] >= 2

    def test_pagination_offset_no_overlap(self, client_a, db, user_a):
        now = datetime.now(timezone.utc)
        for i in range(4):
            make_closed_session(db, COMPANY_A, user_a.id, now - timedelta(hours=50+i))
        r1 = client_a.get("/api/v1/attendance/sessions",
            params={"limit": 2, "offset": 0}, headers=hdr(COMPANY_A, user_a.id))
        r2 = client_a.get("/api/v1/attendance/sessions",
            params={"limit": 2, "offset": 2}, headers=hdr(COMPANY_A, user_a.id))
        ids1 = {s["session_id"] for s in r1.json()["sessions"]}
        ids2 = {s["session_id"] for s in r2.json()["sessions"]}
        assert ids1.isdisjoint(ids2)


# --- SES-02: Date filter ---

class TestSES02DateFilter:
    def test_only_returns_sessions_within_range(self, client_a, db, user_a):
        punch_mar = datetime(2026, 3, 15, 1, 0, 0, tzinfo=timezone.utc)
        punch_apr = datetime(2026, 4, 15, 1, 0, 0, tzinfo=timezone.utc)
        make_closed_session(db, COMPANY_A, user_a.id, punch_mar)
        make_closed_session(db, COMPANY_A, user_a.id, punch_apr)
        start = datetime(2026, 3, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        end   = datetime(2026, 4, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        resp = client_a.get("/api/v1/attendance/sessions",
            params={"start_date": start.isoformat(), "end_date": end.isoformat()},
            headers=hdr(COMPANY_A, user_a.id))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for s in data["sessions"]:
            pit = s["punch_in_time"]
            assert pit >= start.isoformat(), f"session {pit} before start"
            assert pit < end.isoformat(), f"session {pit} after end"


# --- SES-03: Taipei midnight ownership ---

class TestSES03TaipeiMidnightOwnership:
    def test_taipei_0030_belongs_to_taipei_date_not_utc_prev_day(self, client_a, db, user_a):
        """punch_in 00:30 Taipei = 16:30 UTC prev day; query Taipei date range should find it"""
        # 2026-03-12 00:30 Taipei = 2026-03-11 16:30 UTC
        punch_in_taipei = datetime(2026, 3, 12, 0, 30, 0, tzinfo=TZ_TAIPEI)
        punch_in_utc = punch_in_taipei.astimezone(timezone.utc)
        make_closed_session(db, COMPANY_A, user_a.id, punch_in_utc)

        # Query 2026-03-12 Taipei day range -> should find it
        day_start = datetime(2026, 3, 12, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        day_end   = datetime(2026, 3, 13, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        resp = client_a.get("/api/v1/attendance/sessions",
            params={"start_date": day_start.isoformat(), "end_date": day_end.isoformat()},
            headers=hdr(COMPANY_A, user_a.id))
        assert resp.status_code == 200
        found = any(
            abs((datetime.fromisoformat(s["punch_in_time"]).astimezone(timezone.utc) - punch_in_utc).total_seconds()) < 5
            for s in resp.json()["sessions"]
        )
        assert found, "punch_in 00:30 Taipei should appear in 2026-03-12 Taipei date query"

        # Query 2026-03-11 Taipei day range -> should NOT find it
        prev_start = datetime(2026, 3, 11, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        prev_end   = datetime(2026, 3, 12, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        resp2 = client_a.get("/api/v1/attendance/sessions",
            params={"start_date": prev_start.isoformat(), "end_date": prev_end.isoformat()},
            headers=hdr(COMPANY_A, user_a.id))
        assert resp2.status_code == 200
        found2 = any(
            abs((datetime.fromisoformat(s["punch_in_time"]).astimezone(timezone.utc) - punch_in_utc).total_seconds()) < 5
            for s in resp2.json()["sessions"]
        )
        assert not found2, "punch_in 00:30 Taipei must NOT appear in UTC-prev-day Taipei date query"


# --- SES-04: Cross-month ownership ---

class TestSES04CrossMonthOwnership:
    def test_punch_in_march_belongs_to_march_not_april(self, client_a, db, user_a):
        """punch_in 3/31 23:50 Taipei: belongs to March, not April"""
        punch_in_taipei = datetime(2026, 3, 31, 23, 50, 0, tzinfo=TZ_TAIPEI)
        punch_in_utc = punch_in_taipei.astimezone(timezone.utc)
        make_closed_session(db, COMPANY_A, user_a.id, punch_in_utc, duration_minutes=70)

        mar_start = datetime(2026, 3, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        apr_start = datetime(2026, 4, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        may_start = datetime(2026, 5, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)

        # March range: should find
        resp_mar = client_a.get("/api/v1/attendance/sessions",
            params={"start_date": mar_start.isoformat(), "end_date": apr_start.isoformat()},
            headers=hdr(COMPANY_A, user_a.id))
        assert resp_mar.status_code == 200
        found = any(
            abs((datetime.fromisoformat(s["punch_in_time"]).astimezone(timezone.utc) - punch_in_utc).total_seconds()) < 5
            for s in resp_mar.json()["sessions"]
        )
        assert found, "punch_in 3/31 23:50 Taipei should be in March query"

        # April range: should NOT find
        resp_apr = client_a.get("/api/v1/attendance/sessions",
            params={"start_date": apr_start.isoformat(), "end_date": may_start.isoformat()},
            headers=hdr(COMPANY_A, user_a.id))
        assert resp_apr.status_code == 200
        found2 = any(
            abs((datetime.fromisoformat(s["punch_in_time"]).astimezone(timezone.utc) - punch_in_utc).total_seconds()) < 5
            for s in resp_apr.json()["sessions"]
        )
        assert not found2, "punch_in 3/31 23:50 Taipei must NOT appear in April query"


# --- SES-05: Status filter ---

class TestSES05StatusFilter:
    def test_status_closed(self, client_a, db, user_a):
        now = datetime.now(timezone.utc)
        make_closed_session(db, COMPANY_A, user_a.id, now - timedelta(hours=30))
        make_open_session(db, COMPANY_A, user_a.id, now - timedelta(hours=1))
        with override_actor_dependency(make_actor(COMPANY_A, user_a.id)):
            resp = client_a.get("/api/v1/attendance/sessions", params={"status": "closed"})
        assert resp.status_code == 200
        for s in resp.json()["sessions"]:
            assert s["status"] == "closed"

    def test_status_open(self, client_a, db, user_a):
        now = datetime.now(timezone.utc)
        make_open_session(db, COMPANY_A, user_a.id, now - timedelta(minutes=30))
        with override_actor_dependency(make_actor(COMPANY_A, user_a.id)):
            resp = client_a.get("/api/v1/attendance/sessions", params={"status": "open"})
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1
        for s in resp.json()["sessions"]:
            assert s["status"] == "open"


# --- SES-06: Tenant isolation ---

class TestSES06TenantIsolation:
    def test_company_a_cannot_see_company_b_sessions(self, client_a, db, user_a, user_b):
        now = datetime.now(timezone.utc)
        make_closed_session(db, COMPANY_B, user_b.id, now - timedelta(hours=5))
        with override_actor_dependency(make_actor(COMPANY_A, user_a.id)):
                resp = client_a.get("/api/v1/attendance/sessions")
        assert resp.status_code == 200
        for s in resp.json()["sessions"]:
            assert s["company_id"] == COMPANY_A


# --- SES-07: User scope ---

class TestSES07UserScope:
    def test_employee_cannot_query_other_user_sessions(self, client_a, db, user_a, tenant_a):
        other = User(id=uuid4(), display_name="Other", password_hash="x", is_active=True)
        db.add(other); db.commit(); db.refresh(other)
        now = datetime.now(timezone.utc)
        make_closed_session(db, COMPANY_A, other.id, now - timedelta(hours=5))
        with override_actor_dependency(make_actor(COMPANY_A, user_a.id)):
                resp = client_a.get("/api/v1/attendance/sessions",
                    params={"user_id": str(other.id)})
        assert resp.status_code == 403

    def test_employee_can_query_own_sessions(self, client_a, db, user_a):
        now = datetime.now(timezone.utc)
        make_closed_session(db, COMPANY_A, user_a.id, now - timedelta(hours=5))
        with override_actor_dependency(make_actor(COMPANY_A, user_a.id)):
                resp = client_a.get("/api/v1/attendance/sessions",
                    params={"user_id": str(user_a.id)})
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1


# --- SES-08: NULL duration_minutes (open session) ---

class TestSES08NullDuration:
    def test_open_session_null_duration_does_not_crash(self, client_a, db, user_a):
        now = datetime.now(timezone.utc)
        make_open_session(db, COMPANY_A, user_a.id, now - timedelta(hours=1))
        with override_actor_dependency(make_actor(COMPANY_A, user_a.id)):
            resp = client_a.get("/api/v1/attendance/sessions", params={"status": "open"})
        assert resp.status_code == 200
        for s in resp.json()["sessions"]:
            if s["status"] == "open":
                assert s["duration_minutes"] is None


# --- SES-09: Limit boundary ---

class TestSES09LimitBoundary:
    def test_limit_zero_returns_400(self, client_a, user_a):
        with override_actor_dependency(make_actor(COMPANY_A, user_a.id)):
            resp = client_a.get("/api/v1/attendance/sessions", params={"limit": 0})
        assert resp.status_code == 400

    def test_limit_101_returns_400(self, client_a, user_a):
        with override_actor_dependency(make_actor(COMPANY_A, user_a.id)):
            resp = client_a.get("/api/v1/attendance/sessions", params={"limit": 101})
        assert resp.status_code == 400

    def test_limit_100_is_valid(self, client_a, user_a):
        with override_actor_dependency(make_actor(COMPANY_A, user_a.id)):
            resp = client_a.get("/api/v1/attendance/sessions", params={"limit": 100})
        assert resp.status_code == 200


# --- SES-10: Total count matches ---

class TestSES10TotalCount:
    def test_total_matches_unpaginated_count(self, client_a, db, user_a):
        now = datetime.now(timezone.utc)
        for i in range(5):
            make_closed_session(db, COMPANY_A, user_a.id, now - timedelta(hours=100+i))
        r_all = client_a.get("/api/v1/attendance/sessions",
            params={"limit": 100, "offset": 0}, headers=hdr(COMPANY_A, user_a.id))
        assert r_all.status_code == 200
        total = r_all.json()["total"]
        sessions_count = len(r_all.json()["sessions"])
        assert total >= 5
        # total should match count when limit is large enough
        r_p1 = client_a.get("/api/v1/attendance/sessions",
            params={"limit": 2, "offset": 0}, headers=hdr(COMPANY_A, user_a.id))
        assert r_p1.json()["total"] == total


# --- SES-11: Naive datetime rejected ---

class TestSES11NaiveDatetimeRejected:
    def test_naive_start_date_returns_422(self, client_a, user_a):
        """API must reject naive datetime (no tzinfo) with 422"""
        with override_actor_dependency(make_actor(COMPANY_A, user_a.id)):
                resp = client_a.get("/api/v1/attendance/sessions",
                    params={"start_date": "2026-03-01T00:00:00"})
        # FastAPI parses naive ISO string as datetime without tz
        # Our endpoint rejects it with 422
        assert resp.status_code == 422


# --- SES-12: Role branch alignment ---

class TestSES12RoleBranchAlignment:
    def test_company_admin_can_query_other_user_sessions(self, client_a, db, user_a, tenant_a):
        other = User(id=uuid4(), display_name="Other Admin Scope", password_hash="x", is_active=True)
        db.add(other); db.commit(); db.refresh(other)
        now = datetime.now(timezone.utc)
        make_closed_session(db, COMPANY_A, other.id, now - timedelta(hours=3))

        with override_actor_dependency(make_actor_with_role(COMPANY_A, user_a.id, "company_admin")):
            resp = client_a.get("/api/v1/attendance/sessions", params={"user_id": str(other.id)})

        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_hr_manager_can_query_other_user_sessions(self, client_a, db, user_a, tenant_a):
        other = User(id=uuid4(), display_name="Other HR Scope", password_hash="x", is_active=True)
        db.add(other); db.commit(); db.refresh(other)
        now = datetime.now(timezone.utc)
        make_closed_session(db, COMPANY_A, other.id, now - timedelta(hours=4))

        with override_actor_dependency(make_actor_with_role(COMPANY_A, user_a.id, "hr_manager")):
            resp = client_a.get("/api/v1/attendance/sessions", params={"user_id": str(other.id)})

        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_super_admin_can_query_other_user_sessions_in_active_company_scope(self, client_a, db, user_a, tenant_a):
        other = User(id=uuid4(), display_name="Other Super Scope", password_hash="x", is_active=True)
        db.add(other); db.commit(); db.refresh(other)
        now = datetime.now(timezone.utc)
        make_closed_session(db, COMPANY_A, other.id, now - timedelta(hours=2))

        with override_actor_dependency(make_super_admin_actor(COMPANY_A, user_a.id)):
            resp = client_a.get("/api/v1/attendance/sessions", params={"user_id": str(other.id)})

        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_employee_cannot_query_other_user_sessions(self, client_a, db, user_a, tenant_a):
        other = User(id=uuid4(), display_name="Other Employee Scope", password_hash="x", is_active=True)
        db.add(other); db.commit(); db.refresh(other)
        now = datetime.now(timezone.utc)
        make_closed_session(db, COMPANY_A, other.id, now - timedelta(hours=5))

        with override_actor_dependency(make_actor_with_role(COMPANY_A, user_a.id, "employee")):
            resp = client_a.get("/api/v1/attendance/sessions", params={"user_id": str(other.id)})

        assert resp.status_code == 403

    def test_company_admin_cross_company_target_user_returns_empty_under_company_scope(self, client_a, db, user_a, user_b):
        now = datetime.now(timezone.utc)
        make_closed_session(db, COMPANY_B, user_b.id, now - timedelta(hours=6))

        with override_actor_dependency(make_actor_with_role(COMPANY_A, user_a.id, "company_admin")):
            resp = client_a.get("/api/v1/attendance/sessions", params={"user_id": str(user_b.id)})

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["total"] == 0
        assert payload["sessions"] == []
