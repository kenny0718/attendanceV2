"""Punch Close Flow Helper

Responsibility:
- Legacy path: keep `build_policy_evaluation()` behavior unchanged
- Schedule-aware path: `build_policy_evaluation_with_schedule_v2()`
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from app.modules.attendance.policy_engine import AttendancePolicyEngine


@dataclass
class PolicyEvalPayload:
    """Result payload for policy evaluation helpers."""

    policy_id: Optional[UUID]
    evaluation: object


@dataclass
class _ScheduleEvalAdapterResult:
    """Adapter result compatible with PunchOutResponse usage."""

    is_late: bool
    late_minutes: int
    is_early_leave: bool
    early_leave_minutes: int
    is_overtime: bool
    overtime_minutes: int
    work_minutes: int
    policy_name: Optional[str]


def build_policy_evaluation(
    session,
    repo,
    company_id: str,
    user_id: UUID,
    punch_out_time,
    gross_minutes: int,
) -> PolicyEvalPayload:
    """Legacy evaluation path (must remain unchanged)."""
    policy = repo.get_user_policy(company_id, user_id)

    session.punch_out_time = punch_out_time
    session.duration_minutes = gross_minutes
    session.status = "closed"

    policy_engine = AttendancePolicyEngine()
    evaluation = policy_engine.evaluate(session, policy)

    return PolicyEvalPayload(
        policy_id=policy.id if policy else None,
        evaluation=evaluation,
    )


def build_policy_evaluation_with_schedule_v2(
    session,
    repo,
    company_id: str,
    user_id: UUID,
    punch_out_time: datetime,
    work_minutes: int,
    normalized_windows: List[Tuple[datetime, datetime]],
) -> PolicyEvalPayload:
    """Schedule-aware adapter path consuming resolver-normalized windows."""
    if not normalized_windows:
        raise ValueError("normalized_windows must not be empty")

    policy = repo.get_user_policy(company_id, user_id)

    session.punch_out_time = punch_out_time
    session.duration_minutes = work_minutes
    session.status = "closed"

    first_window_start = min(normalized_windows, key=lambda x: x[0])[0]
    last_window_end = max(normalized_windows, key=lambda x: x[1])[1]

    grace = policy.grace_period_minutes if policy else 0
    overtime_threshold = policy.overtime_threshold_minutes if policy else 480

    late_cutoff = first_window_start + timedelta(minutes=grace)
    if session.punch_in_time > late_cutoff:
        is_late = True
        late_minutes = int((session.punch_in_time - late_cutoff).total_seconds() / 60)
    else:
        is_late = False
        late_minutes = 0

    if session.punch_out_time < last_window_end:
        is_early_leave = True
        early_leave_minutes = int((last_window_end - session.punch_out_time).total_seconds() / 60)
    else:
        is_early_leave = False
        early_leave_minutes = 0

    if overtime_threshold is None:
        is_overtime = False
        overtime_minutes = 0
    elif work_minutes > overtime_threshold:
        is_overtime = True
        overtime_minutes = work_minutes - overtime_threshold
    else:
        is_overtime = False
        overtime_minutes = 0

    evaluation = _ScheduleEvalAdapterResult(
        is_late=is_late,
        late_minutes=late_minutes,
        is_early_leave=is_early_leave,
        early_leave_minutes=early_leave_minutes,
        is_overtime=is_overtime,
        overtime_minutes=overtime_minutes,
        work_minutes=work_minutes,
        policy_name=policy.name if policy else "Default Policy (No Policy Assigned)",
    )

    return PolicyEvalPayload(
        policy_id=policy.id if policy else None,
        evaluation=evaluation,
    )
