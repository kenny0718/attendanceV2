"""Test Business Invariant: One Open Session Per User

WP-11-01 Phase B: Test Category 3 - Business Invariant
- Test one open session per (company_id, user_id)
- Test database-level enforcement (partial unique index)
- Test application-level guard
- Test cross-company isolation
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.core.database import Base
from app.modules.attendance.models import AttendanceSession
from app.modules.attendance.repo import AttendanceSessionRepository
from app.modules.auth.models import User
from app.modules.tenants.models import Tenant


# Test database setup
TEST_DATABASE_URL = "postgresql://attendance_user:attendance_pass@localhost:5432/attendance_test"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create test database session"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    # Setup: Create test tenants and users
    tenant_a = Tenant(id="company-a", name="Company A", is_active=True)
    tenant_b = Tenant(id="company-b", name="Company B", is_active=True)
    user1 = User(
        id=uuid4(),
        display_name="User 1",
        password_hash="dummy_hash",
        is_active=True
    )
    user2 = User(
        id=uuid4(),
        display_name="User 2",
        password_hash="dummy_hash",
        is_active=True
    )
    session.add_all([tenant_a, tenant_b, user1, user2])
    session.commit()
    
    yield session
    
    # Teardown
    session.close()
    Base.metadata.drop_all(bind=engine)


class TestOneOpenSessionInvariant:
    """Test: One open session per (company_id, user_id)"""
    
    def test_one_open_session_per_user_database_level(self, db):
        """測試：database 層級防止同一 user 有兩個 open session"""
        user_id = db.query(User).first().id
        now = datetime.utcnow()
        
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
                punch_in_time=now + timedelta(minutes=5),
                status="open"
            )
            db.add(session2)
            db.commit()
        
        # Verify it's the unique constraint that failed
        assert "uq_sessions_company_user_open" in str(exc.value)
    
    def test_one_open_session_per_user_application_level(self, db):
        """測試：application 層級防止同一 user 有兩個 open session"""
        user_id = db.query(User).first().id
        repo = AttendanceSessionRepository(db)
        now = datetime.utcnow()
        
        # Create first open session
        session1 = repo.create_session(
            company_id="company-a",
            user_id=user_id,
            punch_in_time=now
        )
        assert session1.status == "open"
        
        # Try to create second open session (should fail at application level)
        with pytest.raises(HTTPException) as exc:
            repo.create_session(
                company_id="company-a",
                user_id=user_id,
                punch_in_time=now + timedelta(minutes=5)
            )
        
        assert exc.value.status_code == 409
        assert "already has an open" in exc.value.detail["error"]
        assert "open_session_id" in exc.value.detail
    
    def test_different_companies_can_have_open_sessions(self, db):
        """測試：同一 user 在不同 company 可以有 open session"""
        user_id = db.query(User).first().id
        now = datetime.utcnow()
        
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
        assert session_a.company_id == "company-a"
        assert session_b.company_id == "company-b"
    
    def test_different_users_can_have_open_sessions(self, db):
        """測試：不同 user 在同一 company 可以有 open session"""
        users = db.query(User).all()
        user1_id = users[0].id
        user2_id = users[1].id
        now = datetime.utcnow()
        
        # User 1 has open session
        session1 = AttendanceSession(
            company_id="company-a",
            user_id=user1_id,
            punch_in_time=now,
            status="open"
        )
        db.add(session1)
        db.commit()
        
        # User 2 can also have open session (different user)
        session2 = AttendanceSession(
            company_id="company-a",
            user_id=user2_id,
            punch_in_time=now,
            status="open"
        )
        db.add(session2)
        db.commit()  # Should succeed
        
        assert session1.id != session2.id
        assert session1.user_id == user1_id
        assert session2.user_id == user2_id
    
    def test_closed_session_allows_new_open_session(self, db):
        """測試：closed session 後可以建立新的 open session"""
        user_id = db.query(User).first().id
        now = datetime.utcnow()
        
        # Create and close first session
        session1 = AttendanceSession(
            company_id="company-a",
            user_id=user_id,
            punch_in_time=now,
            status="open"
        )
        db.add(session1)
        db.commit()
        
        # Close session
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
        assert session1.status == "closed"
        assert session2.status == "open"
    
    def test_multiple_closed_sessions_allowed(self, db):
        """測試：同一 user 可以有多個 closed session"""
        user_id = db.query(User).first().id
        now = datetime.utcnow()
        
        # Create multiple closed sessions
        for i in range(3):
            session = AttendanceSession(
                company_id="company-a",
                user_id=user_id,
                punch_in_time=now + timedelta(days=i),
                punch_out_time=now + timedelta(days=i, hours=8),
                status="closed"
            )
            db.add(session)
        
        db.commit()  # Should succeed
        
        # Verify all sessions were created
        sessions = db.query(AttendanceSession).filter(
            AttendanceSession.company_id == "company-a",
            AttendanceSession.user_id == user_id,
            AttendanceSession.status == "closed"
        ).all()
        
        assert len(sessions) == 3


class TestSessionLifecycle:
    """Test session lifecycle (open → close)"""
    
    def test_punch_in_creates_open_session(self, db):
        """測試：punch in 建立 open session"""
        user_id = db.query(User).first().id
        repo = AttendanceSessionRepository(db)
        now = datetime.utcnow()
        
        session = repo.create_session(
            company_id="company-a",
            user_id=user_id,
            punch_in_time=now
        )
        
        assert session.id is not None
        assert session.status == "open"
        assert session.punch_in_time == now
        assert session.punch_out_time is None
        assert session.duration_minutes is None
    
    def test_punch_out_closes_session(self, db):
        """測試：punch out 關閉 session 並計算 duration"""
        user_id = db.query(User).first().id
        repo = AttendanceSessionRepository(db)
        punch_in = datetime.utcnow()
        punch_out = punch_in + timedelta(hours=8, minutes=30)
        
        # Punch in
        session = repo.create_session(
            company_id="company-a",
            user_id=user_id,
            punch_in_time=punch_in
        )
        
        # Punch out
        closed_session = repo.close_session(
            company_id="company-a",
            session_id=session.id,
            punch_out_time=punch_out
        )
        
        assert closed_session.status == "closed"
        assert closed_session.punch_out_time == punch_out
        assert closed_session.duration_minutes == 510  # 8.5 hours = 510 minutes
    
    def test_cannot_close_already_closed_session(self, db):
        """測試：無法關閉已經 closed 的 session"""
        user_id = db.query(User).first().id
        repo = AttendanceSessionRepository(db)
        punch_in = datetime.utcnow()
        punch_out = punch_in + timedelta(hours=8)
        
        # Punch in and out
        session = repo.create_session(
            company_id="company-a",
            user_id=user_id,
            punch_in_time=punch_in
        )
        repo.close_session(
            company_id="company-a",
            session_id=session.id,
            punch_out_time=punch_out
        )
        
        # Try to close again (should return None)
        result = repo.close_session(
            company_id="company-a",
            session_id=session.id,
            punch_out_time=punch_out + timedelta(hours=1)
        )
        
        assert result is None
    
    def test_after_punch_out_can_punch_in_again(self, db):
        """測試：punch out 後可以再次 punch in"""
        user_id = db.query(User).first().id
        repo = AttendanceSessionRepository(db)
        day1 = datetime.utcnow()
        day2 = day1 + timedelta(days=1)
        
        # Day 1: Punch in and out
        session1 = repo.create_session(
            company_id="company-a",
            user_id=user_id,
            punch_in_time=day1
        )
        repo.close_session(
            company_id="company-a",
            session_id=session1.id,
            punch_out_time=day1 + timedelta(hours=8)
        )
        
        # Day 2: Punch in again (should succeed)
        session2 = repo.create_session(
            company_id="company-a",
            user_id=user_id,
            punch_in_time=day2
        )
        
        assert session2.id != session1.id
        assert session2.status == "open"


class TestTenantIsolation:
    """Test tenant isolation in session operations"""
    
    def test_cannot_close_other_company_session(self, db):
        """測試：無法關閉其他公司的 session"""
        user_id = db.query(User).first().id
        repo = AttendanceSessionRepository(db)
        now = datetime.utcnow()
        
        # Company A creates session
        session = repo.create_session(
            company_id="company-a",
            user_id=user_id,
            punch_in_time=now
        )
        
        # Company B tries to close Company A's session (should return None)
        result = repo.close_session(
            company_id="company-b",
            session_id=session.id,
            punch_out_time=now + timedelta(hours=8)
        )
        
        assert result is None
        
        # Verify session is still open
        db.refresh(session)
        assert session.status == "open"
    
    def test_get_open_session_respects_company_scope(self, db):
        """測試：get_open_session 遵守 company scope"""
        user_id = db.query(User).first().id
        repo = AttendanceSessionRepository(db)
        now = datetime.utcnow()
        
        # Company A creates session
        session_a = repo.create_session(
            company_id="company-a",
            user_id=user_id,
            punch_in_time=now
        )
        
        # Company A can see the session
        found_a = repo.get_open_session("company-a", user_id)
        assert found_a is not None
        assert found_a.id == session_a.id
        
        # Company B cannot see Company A's session
        found_b = repo.get_open_session("company-b", user_id)
        assert found_b is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
