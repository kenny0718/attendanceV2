"""Regression Test Suite

WP-11-05C: Test 8 - Cross-midnight work attribution
WP-C1-07: JWT Actor Migration - 使用 override_actor_dependency (已遷移至純 JWT actor 模式)
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import patch

from app.modules.attendance.models import AttendanceSession, AttendancePolicy
from app.tests.utils.auth import create_test_actor, override_actor_dependency


@pytest.fixture
def night_shift_policy(test_session, test_user):
    """Create night shift policy"""
    company_id = "company-test"

    policy = AttendancePolicy(
        id=uuid4(),
        company_id=company_id,
        name="Night Shift Policy",
        work_start_time="22:00:00",
        work_end_time="06:00:00",
        is_active=True
    )
    test_session.add(policy)
    test_session.commit()
    test_session.refresh(policy)
    return policy


class TestRegressionSuite:
    """Regression test suite"""

    def test_8_cross_midnight_work_attribution(self, client, test_user, night_shift_policy, test_session):
        """Test 8: Cross-midnight work attribution

        Scenario:
        - Employee punches in at 2026-03-31 23:00 (local time UTC+8)
        - Employee punches out at 2026-04-01 02:00 (local time UTC+8)
        - Work hours = 3 hours (180 minutes)
        - Attribution date = 2026-03-31 (punch_in date in local timezone)

        WP-C1-07: 使用 JWT Actor 而非 X-Company-ID / X-User-ID headers
        """
        company_id = "company-test"
        actor = create_test_actor(company_id, user_id=test_user.id)

        punch_in_time = datetime(2026, 3, 31, 23, 0, 0)

        with patch("app.modules.attendance.api._require_attendance_feature") as mock_gate:
            mock_gate.return_value = None
            with override_actor_dependency(actor):
                response = client.post(
                    "/api/v1/attendance/punch-in",
                    json={"punch_time": punch_in_time.isoformat()}
                )

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"
        session_id = response.json().get("session_id")

        punch_out_time = datetime(2026, 4, 1, 2, 0, 0)

        with patch("app.modules.attendance.api._require_attendance_feature") as mock_gate:
            mock_gate.return_value = None
            with override_actor_dependency(actor):
                response = client.post(
                    "/api/v1/attendance/punch-out",
                    json={"punch_time": punch_out_time.isoformat()}
                )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"

        session = test_session.query(AttendanceSession).filter(
            AttendanceSession.id == session_id
        ).first()

        assert session is not None, "Session not found"
        assert session.punch_in_time.date() == datetime(2026, 3, 31).date()
        assert session.punch_out_time.date() == datetime(2026, 4, 1).date()
        assert session.duration_minutes == 180, f"Expected 180 minutes, got {session.duration_minutes}"
