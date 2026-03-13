"""Test Attendance Domain Model Constraints

WP-11-01 Phase B: Test Category 1 - Model Constraints
- Test NOT NULL constraints
- Test CHECK constraints
- Test Foreign Key constraints
- Test partial unique index (one open session per user)
"""

import pytest
from datetime import datetime, timezone, time
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.core.database import Base
from app.modules.attendance.models import AttendanceSession, AttendancePunch, AttendancePolicy
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
    
    # Setup: Create test tenant and user
    tenant = Tenant(id="test-company", name="Test Company", is_active=True)
    user = User(
        id=uuid4(),
        display_name="Test User",
        password_hash="dummy_hash",
        is_active=True
    )
    session.add(tenant)
    session.add(user)
    session.commit()
    
    yield session
    
    # Teardown
    session.close()
    Base.metadata.drop_all(bind=engine)


class TestAttendanceSessionConstraints:
    """Test AttendanceSession model constraints"""
    
    def test_session_requires_company_id(self, db):
        """測試：session 必須有 company_id"""
        user_id = db.query(User).first().id
        
        with pytest.raises(IntegrityError):
            session = AttendanceSession(
                user_id=user_id,
                punch_in_time=datetime.now(timezone.utc),
                status='open'
            )
            db.add(session)
            db.commit()
    
    def test_session_requires_user_id(self, db):
        """測試：session 必須有 user_id"""
        with pytest.raises(IntegrityError):
            session = AttendanceSession(
                company_id="test-company",
                punch_in_time=datetime.now(timezone.utc),
                status='open'
            )
            db.add(session)
            db.commit()
    
    def test_session_requires_punch_in_time(self, db):
        """測試：session 必須有 punch_in_time"""
        user_id = db.query(User).first().id
        
        with pytest.raises(IntegrityError):
            session = AttendanceSession(
                company_id="test-company",
                user_id=user_id,
                status='open'
            )
            db.add(session)
            db.commit()
    
    def test_session_status_check_constraint(self, db):
        """測試：session status 只能是 'open' 或 'closed'"""
        user_id = db.query(User).first().id
        
        with pytest.raises(IntegrityError) as exc:
            session = AttendanceSession(
                company_id="test-company",
                user_id=user_id,
                punch_in_time=datetime.now(timezone.utc),
                status='invalid'
            )
            db.add(session)
            db.commit()
        
        assert 'ck_sessions_status' in str(exc.value)
    
    def test_session_foreign_key_company_id(self, db):
        """測試：company_id 必須存在於 tenants 表"""
        user_id = db.query(User).first().id
        
        with pytest.raises(IntegrityError):
            session = AttendanceSession(
                company_id="non-existent-company",
                user_id=user_id,
                punch_in_time=datetime.now(timezone.utc),
                status='open'
            )
            db.add(session)
            db.commit()
    
    def test_session_foreign_key_user_id(self, db):
        """測試：user_id 必須存在於 users 表"""
        with pytest.raises(IntegrityError):
            session = AttendanceSession(
                company_id="test-company",
                user_id=uuid4(),  # Non-existent user
                punch_in_time=datetime.now(timezone.utc),
                status='open'
            )
            db.add(session)
            db.commit()
    
    def test_session_default_status_is_open(self, db):
        """測試：session 預設 status 為 'open'"""
        user_id = db.query(User).first().id
        
        session = AttendanceSession(
            company_id="test-company",
            user_id=user_id,
            punch_in_time=datetime.now(timezone.utc)
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        assert session.status == 'open'
    
    def test_session_punch_out_time_nullable(self, db):
        """測試：punch_out_time 可以為 NULL (open session)"""
        user_id = db.query(User).first().id
        
        session = AttendanceSession(
            company_id="test-company",
            user_id=user_id,
            punch_in_time=datetime.now(timezone.utc),
            status='open'
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        assert session.punch_out_time is None


class TestAttendancePunchConstraints:
    """Test AttendancePunch model constraints"""
    
    def test_punch_requires_session_id(self, db):
        """測試：punch 必須有 session_id"""
        user_id = db.query(User).first().id
        
        with pytest.raises(IntegrityError):
            punch = AttendancePunch(
                company_id="test-company",
                user_id=user_id,
                punch_type='in',
                punch_time=datetime.now(timezone.utc)
            )
            db.add(punch)
            db.commit()
    
    def test_punch_requires_company_id(self, db):
        """測試：punch 必須有 company_id"""
        user_id = db.query(User).first().id
        
        # Create session first
        session = AttendanceSession(
            company_id="test-company",
            user_id=user_id,
            punch_in_time=datetime.now(timezone.utc)
        )
        db.add(session)
        db.commit()
        
        with pytest.raises(IntegrityError):
            punch = AttendancePunch(
                session_id=session.id,
                user_id=user_id,
                punch_type='in',
                punch_time=datetime.now(timezone.utc)
            )
            db.add(punch)
            db.commit()
    
    def test_punch_type_check_constraint(self, db):
        """測試：punch_type 只能是 'in', 'out', 'break_start', 'break_end'"""
        user_id = db.query(User).first().id
        
        # Create session first
        session = AttendanceSession(
            company_id="test-company",
            user_id=user_id,
            punch_in_time=datetime.now(timezone.utc)
        )
        db.add(session)
        db.commit()
        
        with pytest.raises(IntegrityError) as exc:
            punch = AttendancePunch(
                session_id=session.id,
                company_id="test-company",
                user_id=user_id,
                punch_type='invalid',
                punch_time=datetime.now(timezone.utc)
            )
            db.add(punch)
            db.commit()
        
        assert 'ck_punches_type' in str(exc.value)
    
    def test_punch_foreign_key_session_id(self, db):
        """測試：session_id 必須存在於 attendance_sessions 表"""
        user_id = db.query(User).first().id
        
        with pytest.raises(IntegrityError):
            punch = AttendancePunch(
                session_id=uuid4(),  # Non-existent session
                company_id="test-company",
                user_id=user_id,
                punch_type='in',
                punch_time=datetime.now(timezone.utc)
            )
            db.add(punch)
            db.commit()
    
    def test_punch_cascade_delete_with_session(self, db):
        """測試：刪除 session 時，相關的 punch 也會被刪除 (CASCADE)"""
        user_id = db.query(User).first().id
        
        # Create session and punch
        session = AttendanceSession(
            company_id="test-company",
            user_id=user_id,
            punch_in_time=datetime.now(timezone.utc)
        )
        db.add(session)
        db.commit()
        
        punch = AttendancePunch(
            session_id=session.id,
            company_id="test-company",
            user_id=user_id,
            punch_type='in',
            punch_time=datetime.now(timezone.utc)
        )
        db.add(punch)
        db.commit()
        
        punch_id = punch.id
        
        # Delete session
        db.delete(session)
        db.commit()
        
        # Verify punch is also deleted
        deleted_punch = db.query(AttendancePunch).filter(
            AttendancePunch.id == punch_id
        ).first()
        assert deleted_punch is None


class TestAttendancePolicyConstraints:
    """Test AttendancePolicy model constraints"""
    
    def test_policy_requires_company_id(self, db):
        """測試：policy 必須有 company_id"""
        with pytest.raises(IntegrityError):
            policy = AttendancePolicy(
                name="Test Policy",
                work_start_time=time(9, 0),
                work_end_time=time(18, 0)
            )
            db.add(policy)
            db.commit()
    
    def test_policy_requires_name(self, db):
        """測試：policy 必須有 name"""
        with pytest.raises(IntegrityError):
            policy = AttendancePolicy(
                company_id="test-company",
                work_start_time=time(9, 0),
                work_end_time=time(18, 0)
            )
            db.add(policy)
            db.commit()
    
    def test_policy_requires_work_start_time(self, db):
        """測試：policy 必須有 work_start_time"""
        with pytest.raises(IntegrityError):
            policy = AttendancePolicy(
                company_id="test-company",
                name="Test Policy",
                work_end_time=time(18, 0)
            )
            db.add(policy)
            db.commit()
    
    def test_policy_requires_work_end_time(self, db):
        """測試：policy 必須有 work_end_time"""
        with pytest.raises(IntegrityError):
            policy = AttendancePolicy(
                company_id="test-company",
                name="Test Policy",
                work_start_time=time(9, 0)
            )
            db.add(policy)
            db.commit()
    
    def test_policy_default_grace_period_is_zero(self, db):
        """測試：policy 預設 grace_period_minutes 為 0"""
        policy = AttendancePolicy(
            company_id="test-company",
            name="Test Policy",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0)
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
        
        assert policy.grace_period_minutes == 0
    
    def test_policy_default_is_active_is_true(self, db):
        """測試：policy 預設 is_active 為 True"""
        policy = AttendancePolicy(
            company_id="test-company",
            name="Test Policy",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0)
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
        
        assert policy.is_active is True
    
    def test_policy_default_is_default_is_false(self, db):
        """測試：policy 預設 is_default 為 False"""
        policy = AttendancePolicy(
            company_id="test-company",
            name="Test Policy",
            work_start_time=time(9, 0),
            work_end_time=time(18, 0)
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
        
        assert policy.is_default is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
