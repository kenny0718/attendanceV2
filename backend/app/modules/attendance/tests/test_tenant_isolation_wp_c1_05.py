"""WP-C1-05: Attendance Module — Tenant Isolation 測試（PostgreSQL 真實 DB）

驗證：
1. Query Isolation — sessions list 只回傳自己 company
2. ID Access Isolation — open session 只屬於自己 company
3. Punch Isolation — 打卡 session 不跨 company
4. Reporting Repo Isolation

使用真實 PostgreSQL（app conftest.py test_db fixture）
"""

from datetime import datetime, timezone, timedelta
from uuid import uuid4
from sqlalchemy.orm import Session

from app.modules.attendance.repo import AttendanceSessionRepository
from app.modules.attendance.reporting_repo import ReportingRepository
from app.modules.attendance.models import AttendanceSession
from app.modules.auth.models import User
from app.modules.tenants.models import Tenant


COMPANY_A = "att-iso-a"
COMPANY_B = "att-iso-b"
USER_A = uuid4()
USER_B = uuid4()


def ensure_fixtures(db: Session, *, user_ids=None):
    """建立測試用 tenants 和 users"""
    for company_id, name in (
        (COMPANY_A, "Attendance Isolation A"),
        (COMPANY_B, "Attendance Isolation B"),
    ):
        tenant = db.query(Tenant).filter(Tenant.id == company_id).first()
        if not tenant:
            db.add(Tenant(id=company_id, name=name, is_active=True))

    ids = list(user_ids or [])
    if not ids:
        ids = [USER_A, USER_B]

    for idx, user_id in enumerate(ids, start=1):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            db.add(User(id=user_id, display_name=f"Attendance Isolation User {idx}", password_hash="x", is_active=True))

    db.commit()


def make_open_session(db: Session, company_id: str, user_id) -> AttendanceSession:
    ensure_fixtures(db, user_ids=[user_id])
    session = AttendanceSession(
        company_id=company_id,
        user_id=user_id,
        punch_in_time=datetime.now(timezone.utc),
        status="open",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def make_closed_session(db: Session, company_id: str, user_id, minutes_ago: int = 60) -> AttendanceSession:
    ensure_fixtures(db, user_ids=[user_id])
    punch_in = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    punch_out = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago // 2)
    session = AttendanceSession(
        company_id=company_id,
        user_id=user_id,
        punch_in_time=punch_in,
        punch_out_time=punch_out,
        status="closed",
        duration_minutes=minutes_ago // 2,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


class TestAttendanceQueryIsolation:
    def test_get_sessions_only_returns_own_company(self, test_db):
        db = test_db
        user_a = uuid4()
        user_b = uuid4()

        make_closed_session(db, COMPANY_A, user_a)
        make_closed_session(db, COMPANY_B, user_b)

        repo = AttendanceSessionRepository(db)
        sessions_a = repo.get_sessions(company_id=COMPANY_A, user_id=user_a)
        assert len(sessions_a) >= 1
        assert all(s.company_id == COMPANY_A for s in sessions_a)

        sessions_b = repo.get_sessions(company_id=COMPANY_A, user_id=user_b)
        assert len(sessions_b) == 0

    def test_get_sessions_cross_company_returns_empty(self, test_db):
        db = test_db
        user_b = uuid4()
        make_closed_session(db, COMPANY_B, user_b)

        repo = AttendanceSessionRepository(db)
        sessions = repo.get_sessions(company_id=COMPANY_A, user_id=user_b)
        assert len(sessions) == 0

    def test_count_sessions_scoped_to_company(self, test_db):
        db = test_db
        user_a = uuid4()
        user_b = uuid4()

        make_closed_session(db, COMPANY_A, user_a)
        make_closed_session(db, COMPANY_B, user_b)

        repo = AttendanceSessionRepository(db)
        count_a = repo.count_sessions(company_id=COMPANY_A, user_id=user_a)
        count_b = repo.count_sessions(company_id=COMPANY_B, user_id=user_b)

        assert count_a >= 1
        assert count_b >= 1
        assert repo.count_sessions(company_id=COMPANY_A, user_id=user_b) == 0
        assert repo.count_sessions(company_id=COMPANY_B, user_id=user_a) == 0


class TestAttendanceOpenSessionIsolation:
    def test_get_open_session_enforces_company_id(self, test_db):
        db = test_db
        user_a = uuid4()
        user_b = uuid4()

        session_a = make_open_session(db, COMPANY_A, user_a)

        repo = AttendanceSessionRepository(db)
        result = repo.get_open_session(company_id=COMPANY_A, user_id=user_a)
        assert result is not None
        assert result.company_id == COMPANY_A
        assert result.id == session_a.id

        assert repo.get_open_session(company_id=COMPANY_B, user_id=user_a) is None
        assert repo.get_open_session(company_id=COMPANY_A, user_id=user_b) is None

    def test_open_session_unique_per_company_user(self, test_db):
        db = test_db
        user_shared = uuid4()

        make_open_session(db, COMPANY_A, user_shared)
        make_open_session(db, COMPANY_B, user_shared)

        repo = AttendanceSessionRepository(db)
        result_a = repo.get_open_session(company_id=COMPANY_A, user_id=user_shared)
        result_b = repo.get_open_session(company_id=COMPANY_B, user_id=user_shared)

        assert result_a is not None
        assert result_b is not None
        assert result_a.company_id == COMPANY_A
        assert result_b.company_id == COMPANY_B


class TestAttendancePunchIsolation:
    def test_create_punch_stores_correct_company_id(self, test_db):
        db = test_db
        user_a = uuid4()
        session_a = make_open_session(db, COMPANY_A, user_a)

        repo = AttendanceSessionRepository(db)
        punch = repo.create_punch(
            session_id=session_a.id,
            company_id=COMPANY_A,
            user_id=user_a,
            punch_type="in",
            punch_time=datetime.now(timezone.utc),
        )
        assert punch.company_id == COMPANY_A
        assert punch.user_id == user_a

    def test_get_session_punches_scoped_by_session(self, test_db):
        db = test_db
        user_a = uuid4()
        user_b = uuid4()
        session_a = make_open_session(db, COMPANY_A, user_a)
        session_b = make_open_session(db, COMPANY_B, user_b)

        repo = AttendanceSessionRepository(db)
        repo.create_punch(
            session_id=session_a.id,
            company_id=COMPANY_A,
            user_id=user_a,
            punch_type="in",
            punch_time=datetime.now(timezone.utc),
        )
        repo.create_punch(
            session_id=session_a.id,
            company_id=COMPANY_A,
            user_id=user_a,
            punch_type="break_start",
            punch_time=datetime.now(timezone.utc),
        )

        punches_a = repo.get_session_punches(session_id=session_a.id)
        punches_b = repo.get_session_punches(session_id=session_b.id)

        assert len(punches_a) >= 1
        assert all(p.session_id == session_a.id for p in punches_a)
        assert len(punches_b) == 0


class TestAttendanceReportingIsolation:
    def test_reporting_sessions_scoped_to_company(self, test_db):
        db = test_db
        user_a = uuid4()
        user_b = uuid4()

        make_closed_session(db, COMPANY_A, user_a)
        make_closed_session(db, COMPANY_B, user_b)

        repo = ReportingRepository(db)
        sessions_a = repo.get_sessions_for_reporting(company_id=COMPANY_A)
        assert len(sessions_a) >= 1
        assert all(s.company_id == COMPANY_A for s in sessions_a)

        sessions_b = repo.get_sessions_for_reporting(company_id=COMPANY_B)
        assert all(s.company_id == COMPANY_B for s in sessions_b)

    def test_count_sessions_for_reporting_scoped(self, test_db):
        db = test_db
        user_a = uuid4()
        user_b = uuid4()

        make_closed_session(db, COMPANY_A, user_a)
        make_closed_session(db, COMPANY_B, user_b)

        repo = ReportingRepository(db)
        count_a = repo.count_sessions_for_reporting(company_id=COMPANY_A)
        count_b = repo.count_sessions_for_reporting(company_id=COMPANY_B)

        assert count_a >= 1
        assert count_b >= 1
