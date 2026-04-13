"""Attendance API — Reporting 層 (WP-11-06)

Sessions reporting endpoints:
- GET /api/v1/attendance/sessions
- GET /api/v1/attendance/reports/user-summary
- GET /api/v1/attendance/reports/company-summary

WP-11-06 Step 1/2/3: Reporting endpoints
WP-C1-07: JWT Actor Migration
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from zoneinfo import ZoneInfo
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.scope import Actor
from app.core.dependencies import get_actor_with_company
from app.core.database import get_db
from app.modules.attendance import api as attendance_api
from app.modules.attendance.reporting_repo import get_reporting_repository
from app.modules.attendance.schemas import SessionResponse
from app.modules.attendance.reporting_schemas import (
    SessionsListResponse,
    UserSummaryResponse,
    CompanySummaryResponse,
)
from app.modules.attendance.api.reporting_helpers import _validate_datetime_range, resolve_reporting_query_range_to_utc
from app.modules.attendance.reporting_service import calculate_user_summary, calculate_company_summary
from app.core.user_lookup import get_display_names

logger = logging.getLogger(__name__)
TZ_TAIPEI = ZoneInfo("Asia/Taipei")
router = APIRouter(prefix="/api/v1/attendance", tags=["attendance-v1"])


@router.get("/sessions", response_model=SessionsListResponse)
def get_sessions(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
):
    attendance_api._require_attendance_feature(actor.active_company_id, db)

    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

    _validate_datetime_range(start_date, end_date)
    start_utc, end_utc = resolve_reporting_query_range_to_utc(start_date, end_date)

    target_user_id: Optional[UUID] = None
    is_admin = actor.is_admin()

    if user_id is not None:
        try:
            target_user_id = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user_id format")
        if not is_admin and target_user_id != actor.user_id:
            raise HTTPException(status_code=403, detail="Employees can only query their own sessions")
    else:
        if not is_admin:
            target_user_id = actor.user_id

    repo = get_reporting_repository(db)
    sessions = repo.get_sessions_for_reporting(
        company_id=actor.active_company_id,
        user_id=target_user_id,
        start_utc=start_utc,
        end_utc=end_utc,
        status=status,
        limit=limit,
        offset=offset,
    )
    total = repo.count_sessions_for_reporting(
        company_id=actor.active_company_id,
        user_id=target_user_id,
        start_utc=start_utc,
        end_utc=end_utc,
        status=status,
    )

    user_ids = list({str(s.user_id) for s in sessions})
    display_names = get_display_names(db, user_ids)
    items = []
    for s in sessions:
        items.append(SessionResponse(
            session_id=s.id,
            user_id=s.user_id,
            company_id=s.company_id,
            display_name=display_names.get(str(s.user_id)),
            punch_in_time=s.punch_in_time.astimezone(TZ_TAIPEI),
            punch_out_time=s.punch_out_time.astimezone(TZ_TAIPEI) if s.punch_out_time is not None else None,
            status=s.status,
            duration_minutes=s.duration_minutes,
            notes=s.notes,
        ))

    return SessionsListResponse(sessions=items, total=total, limit=limit, offset=offset)


@router.get("/reports/user-summary", response_model=UserSummaryResponse)
def get_user_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
):
    attendance_api._require_attendance_feature(actor.active_company_id, db)
    _validate_datetime_range(start_date, end_date)
    start_utc, end_utc = resolve_reporting_query_range_to_utc(start_date, end_date)

    repo = get_reporting_repository(db)
    sessions = repo.get_user_summary_sessions(
        company_id=actor.active_company_id,
        user_id=actor.user_id,
        start_utc=start_utc,
        end_utc=end_utc,
    )
    summary = calculate_user_summary(sessions)
    summary["first_session_time"] = summary["first_session_time"].astimezone(TZ_TAIPEI) if summary["first_session_time"] is not None else None
    summary["last_session_time"] = summary["last_session_time"].astimezone(TZ_TAIPEI) if summary["last_session_time"] is not None else None

    return UserSummaryResponse(user_id=str(actor.user_id), **summary)


@router.get("/reports/company-summary", response_model=CompanySummaryResponse)
def get_company_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
):
    attendance_api._require_attendance_feature(actor.active_company_id, db)

    if not actor.is_admin():
        raise HTTPException(status_code=403, detail="Company summary requires company_admin or hr_manager role")

    _validate_datetime_range(start_date, end_date)
    start_utc, end_utc = resolve_reporting_query_range_to_utc(start_date, end_date)

    repo = get_reporting_repository(db)
    sessions = repo.get_company_summary_sessions(
        company_id=actor.active_company_id,
        start_utc=start_utc,
        end_utc=end_utc,
    )
    summary = calculate_company_summary(sessions)
    summary["first_session_time"] = summary["first_session_time"].astimezone(timezone.utc) if summary["first_session_time"] is not None else None
    summary["last_session_time"] = summary["last_session_time"].astimezone(timezone.utc) if summary["last_session_time"] is not None else None

    return CompanySummaryResponse(company_id=actor.active_company_id, **summary)
