"""Regression Test Suite

WP-11-05C: Test 8 - Cross-midnight work attribution
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app
from app.modules.attendance.models import AttendanceSession, AttendancePolicy
from app.modules.auth.models import User


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


@pytest.fixture
def test_user(db):
    """Create test user"""
    user = User(
        id=uuid4(),
        company_id="company-test",
        username="test_user",
        email="test@example.com",
        hashed_password="dummy",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def night_shift_policy(db, test_user):
    """Create night shift policy"""
    policy = AttendancePolicy(
        id=uuid4(),
        company_id="company-test",
        name="Night Shift Policy",
        work_start_time="22:00:00",
        work_end_time="06:00:00",
        is_active=True
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


class TestRegressionSuite:
    """Regression test suite"""
    
    def test_8_cross_midnight_work_attribution(self, client, test_user, night_shift_policy, db):
        """Test 8: Cross-midnight work attribution
        
        Scenario:
        - Employee punches in at 2026-03-31 23:00 (local time UTC+8)
        - Employee punches out at 2026-04-01 02:00 (local time UTC+8)
        - Work hours = 3 hours (180 minutes)
        - Attribution date = 2026-03-31 (punch_in date in local timezone)
        """
        # Punch in at 23:00 on 2026-03-31 (local time)
        punch_in_time = datetime(2026, 3, 31, 23, 0, 0)
        
        response = client.post(
            "/api/v1/attendance/punch-in",
            headers={
                "X-Company-ID": "company-test",
                "X-User-ID": str(test_user.id)
            },
            json={"punch_time": punch_in_time.isoformat()}
        )
        
        assert response.status_code == 201
        session_id = response.json().get("session_id")
        
        # Punch out at 02:00 on 2026-04-01 (next day, local time)
        punch_out_time = datetime(2026, 4, 1, 2, 0, 0)
        
        response = client.post(
            "/api/v1/attendance/punch-out",
            headers={
                "X-Company-ID": "company-test",
                "X-User-ID": str(test_user.id)
            },
            json={"punch_time": punch_out_time.isoformat()}
        )
        
        assert response.status_code == 200
        
        # Verify
        session = db.query(AttendanceSession).filter(
            AttendanceSession.id == session_id
        ).first()
        
        assert session is not None
        assert session.punch_in_time.date() == datetime(2026, 3, 31).date()
        assert session.punch_out_time.date() == datetime(2026, 4, 1).date()
        assert session.duration_minutes == 180
