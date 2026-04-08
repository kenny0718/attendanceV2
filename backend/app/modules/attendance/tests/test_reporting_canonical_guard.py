from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.modules.attendance.reporting_service import (
    calculate_company_summary,
    calculate_user_summary,
)


def make_session(*, company_id="company-a", user_id=None, status="closed", duration_minutes=None, work_minutes=None):
    base_time = datetime(2026, 4, 8, 9, 0, 0, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        company_id=company_id,
        user_id=user_id or uuid4(),
        status=status,
        punch_in_time=base_time,
        duration_minutes=duration_minutes,
        work_minutes=work_minutes,
    )


class TestReportingCanonicalGuard:
    def test_user_summary_uses_canonical_duration_minutes_not_derived_work_minutes(self):
        session = make_session(duration_minutes=540, work_minutes=480)

        summary = calculate_user_summary([session])

        assert summary["total_work_minutes"] == 540
        assert summary["average_session_minutes"] == 540

    def test_company_summary_ignores_derived_work_minutes_on_open_session(self):
        closed_session = make_session(duration_minutes=540, work_minutes=480)
        open_session = make_session(status="open", duration_minutes=None, work_minutes=300)

        summary = calculate_company_summary([closed_session, open_session])

        assert summary["closed_sessions"] == 1
        assert summary["open_sessions"] == 1
        assert summary["total_work_minutes"] == 540
        assert summary["average_minutes_per_session"] == 540
