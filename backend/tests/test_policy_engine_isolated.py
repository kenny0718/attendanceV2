from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.modules.attendance.policy_engine import AttendancePolicyEngine


class _FakeBaseline:
    def __init__(self, windows):
        self.normalized_windows = windows


class _FakeResolver:
    def __init__(self, _db):
        pass

    def resolve(self, company_id, user_id, work_date):
        del company_id, user_id, work_date
        tz = ZoneInfo("Asia/Taipei")
        return _FakeBaseline([
            (datetime(2026, 3, 4, 8, 0, 0, tzinfo=tz), datetime(2026, 3, 4, 12, 0, 0, tzinfo=tz)),
            (datetime(2026, 3, 4, 13, 0, 0, tzinfo=tz), datetime(2026, 3, 4, 17, 0, 0, tzinfo=tz)),
            (datetime(2026, 3, 4, 18, 0, 0, tzinfo=tz), datetime(2026, 3, 4, 20, 0, 0, tzinfo=tz)),
        ])


def _make_session(punch_in, punch_out, duration_minutes=0):
    return SimpleNamespace(
        id=uuid4(),
        company_id="company-a",
        user_id=uuid4(),
        punch_in_time=punch_in,
        punch_out_time=punch_out,
        status="closed",
        duration_minutes=duration_minutes,
    )


def test_evaluate_with_schedule_v2_isolated_late_first_window(monkeypatch):
    import app.modules.attendance.policy_engine as pe

    monkeypatch.setattr(pe, "ScheduleBaselineResolver", _FakeResolver)

    session = _make_session(
        punch_in=datetime(2026, 3, 4, 8, 20, 0, tzinfo=ZoneInfo("Asia/Taipei")),
        punch_out=datetime(2026, 3, 4, 20, 0, 0, tzinfo=ZoneInfo("Asia/Taipei")),
        duration_minutes=700,
    )

    policy = SimpleNamespace(
        id=uuid4(),
        name="Schedule Policy",
        grace_period_minutes=15,
        overtime_threshold_minutes=540,
    )

    result = AttendancePolicyEngine.evaluate_with_schedule_v2(session=session, db=object(), policy=policy)

    assert result.is_late is True
    assert result.late_minutes == 5
    assert result.schedule_violation_flags == []


def test_evaluate_with_schedule_v2_isolated_early_leave_last_window(monkeypatch):
    import app.modules.attendance.policy_engine as pe

    monkeypatch.setattr(pe, "ScheduleBaselineResolver", _FakeResolver)

    session = _make_session(
        punch_in=datetime(2026, 3, 4, 8, 0, 0, tzinfo=ZoneInfo("Asia/Taipei")),
        punch_out=datetime(2026, 3, 4, 19, 30, 0, tzinfo=ZoneInfo("Asia/Taipei")),
        duration_minutes=690,
    )

    result = AttendancePolicyEngine.evaluate_with_schedule_v2(session=session, db=object(), policy=None)

    assert result.is_early_leave is True
    assert result.early_leave_minutes == 30
    assert result.schedule_violation_flags == []
