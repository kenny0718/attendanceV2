"""Attendance policy schedule-aware support and normalization helpers."""

from datetime import date, datetime, time
from typing import List, Tuple
from zoneinfo import ZoneInfo

TZ_TAIPEI = ZoneInfo("Asia/Taipei")


def to_business_date(dt: datetime) -> date:
    """Normalize a datetime to Taipei business date."""
    if dt.tzinfo is not None:
        return dt.astimezone(TZ_TAIPEI).date()
    return dt.date()


def normalize_windows_with_fallback(
    work_date: date,
    normalized_windows: List[Tuple[datetime, datetime]],
    default_work_start_time: time,
    default_work_end_time: time,
) -> List[Tuple[datetime, datetime]]:
    """Provide fallback window when resolver returns no normalized windows."""
    if normalized_windows:
        return normalized_windows

    default_start = datetime.combine(work_date, default_work_start_time).replace(tzinfo=TZ_TAIPEI)
    default_end = datetime.combine(work_date, default_work_end_time).replace(tzinfo=TZ_TAIPEI)
    return [(default_start, default_end)]


def select_expected_window_bounds(
    normalized_windows: List[Tuple[datetime, datetime]],
) -> Tuple[datetime, datetime]:
    """Select first-start and last-end bounds from normalized windows."""
    return normalized_windows[0][0], normalized_windows[-1][1]
