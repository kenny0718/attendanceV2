"""Attendance Reporting — Aggregation Service

Pure aggregation helpers extracted from api/reporting.py (Micro Decomposition Step 3).

Rules:
- No DB access
- No repo calls
- No router imports
- No schema imports
- No actor/permission logic
- Input: already-fetched sessions list
- Output: plain dict with calculated values
"""
from typing import Any, Dict, List, Optional


def calculate_user_summary(sessions: List[Any]) -> Dict[str, Any]:
    """Calculate per-user attendance summary from fetched sessions.

    Args:
        sessions: list of AttendanceSession ORM objects (already fetched by repo)

    Returns:
        Plain dict with keys matching UserSummaryResponse fields
        (excluding user_id, which is provided by the router).
    """
    total_sessions = len(sessions)
    closed_sessions = sum(1 for s in sessions if s.status == "closed")
    open_sessions = sum(1 for s in sessions if s.status == "open")

    # canonical duration — duration_minutes IS NULL for open sessions
    total_work_minutes = sum(s.duration_minutes or 0 for s in sessions)

    # average: None when no closed sessions (avoid division by zero)
    average_session_minutes: Optional[float] = (
        total_work_minutes / closed_sessions
        if closed_sessions > 0 else None
    )

    # first / last: application-layer min/max over punch_in_time
    first_session_time = (
        min(s.punch_in_time for s in sessions) if sessions else None
    )
    last_session_time = (
        max(s.punch_in_time for s in sessions) if sessions else None
    )

    return {
        "total_sessions": total_sessions,
        "closed_sessions": closed_sessions,
        "open_sessions": open_sessions,
        "total_work_minutes": total_work_minutes,
        "average_session_minutes": average_session_minutes,
        "first_session_time": first_session_time,
        "last_session_time": last_session_time,
    }


def calculate_company_summary(sessions: List[Any]) -> Dict[str, Any]:
    """Calculate company-level attendance summary from fetched sessions.

    Args:
        sessions: list of AttendanceSession ORM objects (already fetched by repo)

    Returns:
        Plain dict with keys matching CompanySummaryResponse fields
        (excluding company_id, which is provided by the router).
    """
    total_sessions = len(sessions)
    closed_sessions = sum(1 for s in sessions if s.status == "closed")
    open_sessions = sum(1 for s in sessions if s.status == "open")

    # 用戶去重（Python set，禁止 SQL COUNT DISTINCT）
    total_users_with_sessions = len(set(s.user_id for s in sessions))

    # canonical duration — duration_minutes IS NULL for open sessions
    total_work_minutes = sum(s.duration_minutes or 0 for s in sessions)

    # average per session: None when no closed sessions
    average_minutes_per_session: Optional[float] = (
        total_work_minutes / closed_sessions
        if closed_sessions > 0 else None
    )

    # average per user: None when no users with sessions
    average_minutes_per_user: Optional[float] = (
        total_work_minutes / total_users_with_sessions
        if total_users_with_sessions > 0 else None
    )

    # first / last: application-layer min/max over punch_in_time
    first_session_time = (
        min(s.punch_in_time for s in sessions) if sessions else None
    )
    last_session_time = (
        max(s.punch_in_time for s in sessions) if sessions else None
    )

    return {
        "total_users_with_sessions": total_users_with_sessions,
        "total_sessions": total_sessions,
        "open_sessions": open_sessions,
        "closed_sessions": closed_sessions,
        "total_work_minutes": total_work_minutes,
        "average_minutes_per_session": average_minutes_per_session,
        "average_minutes_per_user": average_minutes_per_user,
        "first_session_time": first_session_time,
        "last_session_time": last_session_time,
    }
