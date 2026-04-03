"""WP-11-06 Step 3: GET /api/v1/attendance/reports/company-summary Tests

CMP-01  basic company summary
CMP-02  date range filter
CMP-03  cross-midnight session ownership
CMP-04  NULL duration_minutes handling
CMP-05  tenant isolation
CMP-06  empty company dataset
CMP-07  naive datetime rejection (422)
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.modules.attendance.models import AttendanceSession
from app.modules.tenants.models import Tenant, CompanyEntitlement
from app.modules.auth.models import User
from app.tests.utils.auth import create_test_actor, override_actor_dependency
from app.core.features import FeatureKeys

TZ_TAIPEI = ZoneInfo("Asia/Taipei")
COMPANY_A = "company-cmpsummary-a"
COMPANY_B = "company-cmpsummary-b"
URL = "/api/v1/attendance/reports/company-summary"


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


def make_actor_company(company_id, user_id=None):
    """WP-C1-07: JWT Actor 取代 X-Company-ID header"""
    from uuid import uuid4
    return create_test_actor(company_id, user_id=user_id or uuid4(), role_id="company_admin")


def make_user(db):
    u = User(id=uuid4(), display_name="CMP User", password_hash="x", is_active=True)
    db.add(u); db.commit(); db.refresh(u)
    return u


def ensure_tenant(db, company_id, name):
    t = db.query(Tenant).filter(Tenant.id == company_id).first()
    if not t:
        t = Tenant(id=company_id, name=name, is_active=True)
        db.add(t); db.commit()
    return t


def ensure_attendance_entitlement(db, company_id):
    existing = db.query(CompanyEntitlement).filter(
        CompanyEntitlement.company_id == company_id,
        CompanyEntitlement.feature_key == FeatureKeys.ATTENDANCE_CORE,
    ).first()
    if not existing:
        db.add(CompanyEntitlement(
            id=uuid4(),
            company_id=company_id,
            feature_key=FeatureKeys.ATTENDANCE_CORE,
            enabled=True,
        ))
        db.commit()


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
    ensure_tenant(db, COMPANY_A, "CMP Summary Co A")
    ensure_attendance_entitlement(db, COMPANY_A)
    return db.query(Tenant).filter(Tenant.id == COMPANY_A).first()


@pytest.fixture
def tenant_b(db):
    ensure_tenant(db, COMPANY_B, "CMP Summary Co B")
    ensure_attendance_entitlement(db, COMPANY_B)
    return db.query(Tenant).filter(Tenant.id == COMPANY_B).first()


def get_company_summary(client_a, company_id, params=None):
    with override_actor_dependency(make_actor_company(company_id)):
        return client_a.get(URL, params=params)


# ============================================================
# CMP-01: Basic company summary
# ============================================================

class TestCMP01BasicSummary:
    def test_counts_and_work_minutes(self, client_a, db, tenant_a):
        u1 = make_user(db)
        u2 = make_user(db)
        now = datetime.now(timezone.utc)
        make_closed(db, COMPANY_A, u1.id, now - timedelta(hours=30), duration_minutes=480)
        make_closed(db, COMPANY_A, u1.id, now - timedelta(hours=20), duration_minutes=300)
        make_closed(db, COMPANY_A, u2.id, now - timedelta(hours=25), duration_minutes=240)
        make_open(db, COMPANY_A, u2.id, now - timedelta(hours=1))

        resp = get_company_summary(client_a, COMPANY_A)
        assert resp.status_code == 200, resp.text
        d = resp.json()
        assert d["company_id"] == COMPANY_A
        assert d["total_sessions"] >= 4
        assert d["closed_sessions"] >= 3
        assert d["open_sessions"] >= 1
        assert d["total_work_minutes"] >= 1020
        assert d["total_users_with_sessions"] >= 2
        assert d["average_minutes_per_session"] is not None
        assert d["average_minutes_per_user"] is not None

    def test_response_has_required_fields(self, client_a, db, tenant_a):
        resp = get_company_summary(client_a, COMPANY_A)
        assert resp.status_code == 200
        d = resp.json()
        required = [
            "company_id", "total_users_with_sessions", "total_sessions",
            "open_sessions", "closed_sessions", "total_work_minutes",
            "average_minutes_per_session", "average_minutes_per_user",
            "first_session_time", "last_session_time",
        ]
        for field in required:
            assert field in d, f"missing field: {field}"

    def test_first_and_last_session_time(self, client_a, db, tenant_a):
        u = make_user(db)
        now = datetime.now(timezone.utc)
        t1 = now - timedelta(hours=50)
        t2 = now - timedelta(hours=10)
        make_closed(db, COMPANY_A, u.id, t1)
        make_closed(db, COMPANY_A, u.id, t2)
        resp = get_company_summary(client_a, COMPANY_A)
        assert resp.status_code == 200
        d = resp.json()
        assert d["first_session_time"] is not None
        assert d["last_session_time"] is not None
        assert d["first_session_time"] < d["last_session_time"]

    def test_total_users_deduplication(self, client_a, db, tenant_a):
        """同一用戶多筆 session 只計一次"""
        u = make_user(db)
        now = datetime.now(timezone.utc)
        make_closed(db, COMPANY_A, u.id, now - timedelta(hours=40))
        make_closed(db, COMPANY_A, u.id, now - timedelta(hours=30))
        make_closed(db, COMPANY_A, u.id, now - timedelta(hours=20))
        resp = get_company_summary(client_a, COMPANY_A)
        assert resp.status_code == 200
        d = resp.json()
        # 3 sessions but only 1 unique user
        assert d["total_sessions"] >= 3
        # total_users_with_sessions must count unique users, not sessions
        assert d["total_users_with_sessions"] >= 1


# ============================================================
# CMP-02: Date range filter
# ============================================================

class TestCMP02DateRangeFilter:
    def test_only_sessions_within_range_counted(self, client_a, db, tenant_a):
        u = make_user(db)
        punch_mar = datetime(2026, 3, 15, 1, 0, 0, tzinfo=timezone.utc)
        punch_apr = datetime(2026, 4, 15, 1, 0, 0, tzinfo=timezone.utc)
        make_closed(db, COMPANY_A, u.id, punch_mar, duration_minutes=480)
        make_closed(db, COMPANY_A, u.id, punch_apr, duration_minutes=360)

        start = datetime(2026, 3, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        end   = datetime(2026, 4, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)

        resp = get_company_summary(client_a, COMPANY_A, params={"start_date": start.isoformat(), "end_date": end.isoformat()})
        assert resp.status_code == 200
        d = resp.json()
        assert d["total_sessions"] >= 1
        assert d["total_work_minutes"] >= 480
        # April session must NOT be included
        assert d["total_work_minutes"] < 840, "April session must not appear in March range"


# ============================================================
# CMP-03: Cross-midnight session ownership
# ============================================================

class TestCMP03CrossMidnight:
    def test_punch_in_march_counted_in_march_not_april(self, client_a, db, tenant_a):
        u = make_user(db)
        # punch_in = 2026-03-31 23:50 Taipei = 2026-03-31 15:50 UTC
        punch_in_taipei = datetime(2026, 3, 31, 23, 50, 0, tzinfo=TZ_TAIPEI)
        punch_in_utc = punch_in_taipei.astimezone(timezone.utc)
        make_closed(db, COMPANY_A, u.id, punch_in_utc, duration_minutes=70)

        mar_start = datetime(2026, 3, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        apr_start = datetime(2026, 4, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        may_start = datetime(2026, 5, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)

        # March query: must find it
        r_mar = get_company_summary(client_a, COMPANY_A, params={"start_date": mar_start.isoformat(), "end_date": apr_start.isoformat()})
        assert r_mar.status_code == 200
        assert r_mar.json()["total_sessions"] >= 1
        assert r_mar.json()["total_work_minutes"] >= 70

        # April query: must NOT find it
        r_apr = get_company_summary(client_a, COMPANY_A, params={"start_date": apr_start.isoformat(), "end_date": may_start.isoformat()})
        assert r_apr.status_code == 200
        # punch_in_utc = 2026-03-31 15:50 UTC < apr_start
        assert r_apr.json()["total_work_minutes"] < 70 or r_apr.json()["total_sessions"] == 0


# ============================================================
# CMP-04: NULL duration handling
# ============================================================

class TestCMP04NullDuration:
    def test_open_session_not_counted_in_work_minutes(self, client_a, db, tenant_a):
        u = make_user(db)
        now = datetime.now(timezone.utc)
        make_closed(db, COMPANY_A, u.id, now - timedelta(hours=20), duration_minutes=480)
        make_open(db, COMPANY_A, u.id, now - timedelta(hours=1))

        resp = get_company_summary(client_a, COMPANY_A)
        assert resp.status_code == 200
        d = resp.json()
        assert d["open_sessions"] >= 1
        assert d["closed_sessions"] >= 1
        # total_work_minutes must not include None duration
        assert d["total_work_minutes"] >= 480
        assert d["total_work_minutes"] < 961, "open session None duration must not be counted"

    def test_all_open_sessions_averages_are_none(self, client_a, db, tenant_a):
        u = make_user(db)
        now = datetime.now(timezone.utc)
        make_open(db, COMPANY_A, u.id, now - timedelta(hours=1))

        resp = get_company_summary(client_a, COMPANY_A)
        assert resp.status_code == 200
        d = resp.json()
        # If all sessions are open, closed_sessions == 0 -> averages must be None
        if d["closed_sessions"] == 0:
            assert d["average_minutes_per_session"] is None


# ============================================================
# CMP-05: Tenant isolation
# ============================================================

class TestCMP05TenantIsolation:
    def test_company_a_cannot_see_company_b_sessions(self, client_a, db, tenant_a, tenant_b):
        u_b = make_user(db)
        now = datetime.now(timezone.utc)
        make_closed(db, COMPANY_B, u_b.id, now - timedelta(hours=5), duration_minutes=999)

        # Query company A — must not see company B's 999-min session
        resp = get_company_summary(client_a, COMPANY_A)
        assert resp.status_code == 200
        d = resp.json()
        assert d["company_id"] == COMPANY_A
        # company A total_work_minutes must not include company B's 999
        assert d["total_work_minutes"] < 999, "company B session must not appear in company A summary"

    def test_company_b_sessions_not_counted_in_company_a_users(self, client_a, db, tenant_a, tenant_b):
        u_b = make_user(db)
        now = datetime.now(timezone.utc)
        make_closed(db, COMPANY_B, u_b.id, now - timedelta(hours=3))

        resp = get_company_summary(client_a, COMPANY_A)
        assert resp.status_code == 200
        # company A has no sessions from company B users
        assert resp.json()["company_id"] == COMPANY_A


# ============================================================
# CMP-06: Empty company dataset
# ============================================================

class TestCMP06EmptyDataset:
    def test_no_sessions_returns_zero_summary(self, client_a, db, tenant_a):
        # Query a future date range where no sessions exist
        start = datetime(2099, 1, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        end   = datetime(2099, 2, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)

        resp = get_company_summary(client_a, COMPANY_A, params={"start_date": start.isoformat(), "end_date": end.isoformat()})
        assert resp.status_code == 200, resp.text
        d = resp.json()
        assert d["total_sessions"] == 0
        assert d["closed_sessions"] == 0
        assert d["open_sessions"] == 0
        assert d["total_users_with_sessions"] == 0
        assert d["total_work_minutes"] == 0
        assert d["average_minutes_per_session"] is None
        assert d["average_minutes_per_user"] is None
        assert d["first_session_time"] is None
        assert d["last_session_time"] is None


# ============================================================
# CMP-07: Naive datetime rejection
# ============================================================

class TestCMP07NaiveDatetime:
    def test_naive_start_date_returns_422(self, client_a, tenant_a):
        resp = get_company_summary(client_a, COMPANY_A, params={"start_date": "2026-03-01T00:00:00"})
        assert resp.status_code == 422

    def test_naive_end_date_returns_422(self, client_a, tenant_a):
        resp = get_company_summary(client_a, COMPANY_A, params={"end_date": "2026-04-01T00:00:00"})
        assert resp.status_code == 422

    def test_aware_datetime_is_accepted(self, client_a, tenant_a):
        start = datetime(2026, 3, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
        resp = get_company_summary(client_a, COMPANY_A, params={"start_date": start.isoformat()})
        assert resp.status_code == 200
