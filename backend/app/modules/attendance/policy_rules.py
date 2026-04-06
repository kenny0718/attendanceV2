"""Attendance policy pure rule calculation functions."""

from datetime import datetime, timedelta, time
from typing import List, Optional
from zoneinfo import ZoneInfo

from app.modules.attendance.policy_schedule_models import WorkWindow

TZ_TAIPEI = ZoneInfo("Asia/Taipei")


def calculate_late(
    punch_in_time: datetime,
    work_start_time: time,
    grace_period_minutes: int,
) -> tuple[bool, int]:
    """Calculate if punch-in is late."""
    # Derive business date in Asia/Taipei, then combine with work_start_time
    # P1-01/P1-02 fix: use Taipei local date (not UTC date) and mark with TZ_TAIPEI
    if punch_in_time.tzinfo is not None:
        taipei_date = punch_in_time.astimezone(TZ_TAIPEI).date()
    else:
        taipei_date = punch_in_time.date()
    expected_start = datetime.combine(taipei_date, work_start_time).replace(tzinfo=TZ_TAIPEI)

    # Add grace period
    expected_start_with_grace = expected_start + timedelta(minutes=grace_period_minutes)

    # Calculate late minutes
    if punch_in_time > expected_start_with_grace:
        late_delta = punch_in_time - expected_start_with_grace
        late_minutes = int(late_delta.total_seconds() / 60)
        return True, late_minutes
    else:
        return False, 0


def calculate_early_leave(
    punch_out_time: datetime,
    work_end_time: time,
) -> tuple[bool, int]:
    """Calculate if punch-out is early leave."""
    # Derive business date in Asia/Taipei, then combine with work_end_time
    # P1-01/P1-02 fix: use Taipei local date (not UTC date) and mark with TZ_TAIPEI
    if punch_out_time.tzinfo is not None:
        taipei_date = punch_out_time.astimezone(TZ_TAIPEI).date()
    else:
        taipei_date = punch_out_time.date()
    expected_end = datetime.combine(taipei_date, work_end_time).replace(tzinfo=TZ_TAIPEI)

    # Calculate early leave minutes
    if punch_out_time < expected_end:
        early_delta = expected_end - punch_out_time
        early_leave_minutes = int(early_delta.total_seconds() / 60)
        return True, early_leave_minutes
    else:
        return False, 0


def calculate_overtime(
    work_minutes: int,
    overtime_threshold_minutes: Optional[int],
) -> tuple[bool, int]:
    """Calculate if work duration qualifies as overtime."""
    if overtime_threshold_minutes is None:
        # No overtime threshold defined
        return False, 0

    if work_minutes > overtime_threshold_minutes:
        overtime_minutes = work_minutes - overtime_threshold_minutes
        return True, overtime_minutes
    else:
        return False, 0


def calculate_late_from_datetime(
    punch_in_time: datetime,
    expected_start: datetime,
    grace_period_minutes: int,
) -> tuple[bool, int]:
    """Calculate late minutes from a resolved expected-start datetime."""
    expected_start_with_grace = expected_start + timedelta(minutes=grace_period_minutes)
    if punch_in_time > expected_start_with_grace:
        late_delta = punch_in_time - expected_start_with_grace
        return True, int(late_delta.total_seconds() / 60)
    return False, 0


def calculate_early_leave_from_datetime(
    punch_out_time: datetime,
    expected_end: datetime,
) -> tuple[bool, int]:
    """Calculate early-leave minutes from a resolved expected-end datetime."""
    if punch_out_time < expected_end:
        early_delta = expected_end - punch_out_time
        return True, int(early_delta.total_seconds() / 60)
    return False, 0


def calculate_work_minutes_split_shift(
    punch_in_time: datetime,
    punch_out_time: datetime,
    windows: List[WorkWindow],
    logger,
) -> int:
    """Calculate work minutes for split shift."""
    total_minutes = 0

    for window in windows:
        # Derive business date in Asia/Taipei for window boundaries
        # P1-01/P1-02 fix: use Taipei local date and mark with TZ_TAIPEI
        if punch_in_time.tzinfo is not None:
            taipei_date = punch_in_time.astimezone(TZ_TAIPEI).date()
        else:
            taipei_date = punch_in_time.date()
        window_start_dt = datetime.combine(taipei_date, window.start_time).replace(tzinfo=TZ_TAIPEI)
        window_end_dt = datetime.combine(taipei_date, window.end_time).replace(tzinfo=TZ_TAIPEI)

        # Calculate overlap between punch times and this window
        effective_start = max(punch_in_time, window_start_dt)
        effective_end = min(punch_out_time, window_end_dt)

        # Only count if there's actual overlap
        if effective_start < effective_end:
            delta = effective_end - effective_start
            window_minutes = int(delta.total_seconds() / 60)
            total_minutes += window_minutes

            logger.debug(
                f"Window {window.start_time}-{window.end_time}: "
                f"counted {window_minutes} minutes "
                f"(effective: {effective_start.time()}-{effective_end.time()})"
            )

    return total_minutes
