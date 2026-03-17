"""WP-C1-05: Attendance Module — Tenant Isolation 測試（PostgreSQL 真實 DB）

驗證：
1. Query Isolation — sessions list 只回傳自己 company
2. ID Access Isolation — open session 只屬於自己 company
3. Punch Isolation — 打卡 session 不跨 company
4. Reporting Repo Isolation

使用真實 PostgreSQL（app conftest.py test_db fixture）
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.modules.attendance.models import AttendanceSession, AttendancePunch
from app.modules.attendance.repo import AttendanceSessionRepository
from app.modules.tenants.models import Tenant
from app.modules.auth.models import User

COMPANY_A = "att-iso-a"
COMPANY_B = "att-iso-b"
USER_A = uuid4()
USER_B = uuid4()


def ensure_fixtures(db):
    """建立測試用 tenants 和 users"""
    for cid, cname in [(COMPANY_A, "Att Iso A"), (COMPANY_B, "Att Iso B")]:
        if not db.query(Tenant).filter(Tenant.id == cid).first():
            db.add(Tenant(id=cid, name=cname, is_active=True))

    for uid in [USER_A, USER_B]:
        if not db.query(User).filter(User.id == uid).first():
            db.add(User(
                id=uid,
                display_name=f"User {uid}",
                password_hash="dummy",
                is_active=True,
            ))
    db.commit()


def make_open_session(db, company_id, user_id):
    now = datetime.now(timezone.utc)
    s = AttendanceSession(
        company_id=company_id,
        user_id=user_id,
        punch_in_time=now,
        status="open",
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def make_closed_session(db, company_id, user_id, minutes_ago=60):
    now = datetime.now(timezone.utc)
    punch_in = now - timedelta(minutes=minutes_ago)
    s = AttendanceSession(
        company_id=company_id,
        user_id=user_id,
        punch_in_time=punch_in,
        punch_out_time=now,
        status="closed",
        duration_minutes=minutes_ago,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# ============================================================
# 1. Query Isolation: get_sessions
# ============================================================

class TestAttendanceQueryIsolation:

    def test_get_sessions_only_returns_own_company(self, test_db):
        """get_sessions 強制 company_id 隔離"""
        db = test_db
        ensure_fixtures(db)

        for _ in range(3):
            make_closed_session(db, COMPANY_A, USER_A)
        for _ in range(2):
            make_closed_session(db, COMPANY_B, USER_B)

        repo = AttendanceSessionRepository(db)

        sessions_a = repo.get_sessions(COMPANY_A, USER_A)
        assert len(sessions_a) == 3
        assert all(s.company_id == COMPANY_A for s in sessions_a)

        sessions_b = repo.get_sessions(COMPANY_B, USER_B)
        assert len(sessions_b) == 2
        assert all(s.company_id == COMPANY_B for s in sessions_b)

    def test_get_sessions_cross_company_returns_empty(self, test_db):
        """Company B user 在 COMPANY_A 下沒有資料 → 空"""
        db = test_db
        ensure_fixtures(db)

        for _ in range(3):
            make_closed_session(db, COMPANY_A, USER_A)

        repo = AttendanceSessionRepository(db)
        sessions = repo.get_sessions(COMPANY_A, USER_B)
        assert len(sessions) == 0

    def test_count_sessions_scoped_to_company(self, test_db):
        """count_sessions 只計算自己 company + user"""
        db = test_db
        ensure_fixtures(db)

        for _ in range(4):
            make_closed_session(db, COMPANY_A, USER_A)
        for _ in range(2):
            make_closed_session(db, COMPANY_B, USER_B)

        repo = AttendanceSessionRepository(db)
        assert repo.count_sessions(COMPANY_A, USER_A) == 4
        assert repo.count_sessions(COMPANY_B, USER_B) == 2
        assert repo.count_sessions(COMPANY_A, USER_B) == 0
        assert repo.count_sessions(COMPANY_B, USER_A) == 0


# ============================================================
# 2. ID Access Isolation: get_open_session
# ============================================================

class TestAttendanceOpenSessionIsolation:

    def test_get_open_session_enforces_company_id(self, test_db):
        """get_open_session 同時驗證 company_id + user_id"""
        db = test_db
        ensure_fixtures(db)

        session_a = make_open_session(db, COMPANY_A, USER_A)

        repo = AttendanceSessionRepository(db)

        result = repo.get_open_session(COMPANY_A, USER_A)
        assert result is not None
        assert result.company_id == COMPANY_A
        assert result.id == session_a.id

        result_cross = repo.get_open_session(COMPANY_B, USER_A)
        assert result_cross is None

        result_user_cross = repo.get_open_session(COMPANY_A, USER_B)
        assert result_user_cross is None

    def test_open_session_unique_per_company_user(self, test_db):
        """同一 user 在不同 company 可分別有 open session"""
        db = test_db
        ensure_fixtures(db)

        sess_a = make_open_session(db, COMPANY_A, USER_A)
        sess_b = make_open_session(db, COMPANY_B, USER_A)

        repo = AttendanceSessionRepository(db)

        result_a = repo.get_open_session(COMPANY_A, USER_A)
        result_b = repo.get_open_session(COMPANY_B, USER_A)

        assert result_a is not None
        assert result_b is not None
        assert result_a.id != result_b.id
        assert result_a.company_id == COMPANY_A
        assert result_b.company_id == COMPANY_B


# ============================================================
# 3. Punch Isolation
# ============================================================

class TestAttendancePunchIsolation:

    def test_create_punch_stores_correct_company_id(self, test_db):
        """create_punch 記錄正確的 company_id（punch_type 使用合法值 'in'）"""
        db = test_db
        ensure_fixtures(db)

        session_a = make_open_session(db, COMPANY_A, USER_A)

        repo = AttendanceSessionRepository(db)
        punch = repo.create_punch(
            session_id=session_a.id,
            company_id=COMPANY_A,
            user_id=USER_A,
            punch_type="in",
            punch_time=datetime.now(timezone.utc),
        )

        assert punch.company_id == COMPANY_A
        assert punch.user_id == USER_A

    def test_get_session_punches_scoped_by_session(self, test_db):
        """get_session_punches 只回傳指定 session 的 punches"""
        db = test_db
        ensure_fixtures(db)

        sess_a = make_open_session(db, COMPANY_A, USER_A)
        sess_b = make_open_session(db, COMPANY_B, USER_B)

        now = datetime.now(timezone.utc)
        repo = AttendanceSessionRepository(db)

        repo.create_punch(
            session_id=sess_a.id, company_id=COMPANY_A,
            user_id=USER_A, punch_type="in", punch_time=now,
        )
        repo.create_punch(
            session_id=sess_a.id, company_id=COMPANY_A,
            user_id=USER_A, punch_type="break_start",
            punch_time=now + timedelta(hours=2),
        )
        repo.create_punch(
            session_id=sess_b.id, company_id=COMPANY_B,
            user_id=USER_B, punch_type="in", punch_time=now,
        )

        punches_a = repo.get_session_punches(sess_a.id)
        assert len(punches_a) == 2
        assert all(p.company_id == COMPANY_A for p in punches_a)

        punches_b = repo.get_session_punches(sess_b.id)
        assert len(punches_b) == 1
        assert all(p.company_id == COMPANY_B for p in punches_b)


# ============================================================
# 4. Reporting Repo Isolation
# ============================================================

class TestAttendanceReportingIsolation:

    def test_reporting_sessions_scoped_to_company(self, test_db):
        """ReportingRepository.get_sessions_for_reporting 強制 company_id"""
        from app.modules.attendance.repo import ReportingRepository
        db = test_db
        ensure_fixtures(db)

        for _ in range(5):
            make_closed_session(db, COMPANY_A, USER_A)
        for _ in range(3):
            make_closed_session(db, COMPANY_B, USER_B)

        repo = ReportingRepository(db)

        sessions_a = repo.get_sessions_for_reporting(COMPANY_A)
        assert len(sessions_a) == 5
        assert all(s.company_id == COMPANY_A for s in sessions_a)

        sessions_b = repo.get_sessions_for_reporting(COMPANY_B)
        assert len(sessions_b) == 3
        assert all(s.company_id == COMPANY_B for s in sessions_b)

    def test_count_sessions_for_reporting_scoped(self, test_db):
        """count_sessions_for_reporting 只計算自己 company"""
        from app.modules.attendance.repo import ReportingRepository
        db = test_db
        ensure_fixtures(db)

        for _ in range(6):
            make_closed_session(db, COMPANY_A, USER_A)
        for _ in range(2):
            make_closed_session(db, COMPANY_B, USER_B)

        repo = ReportingRepository(db)
        assert repo.count_sessions_for_reporting(COMPANY_A) == 6
        assert repo.count_sessions_for_reporting(COMPANY_B) == 2
