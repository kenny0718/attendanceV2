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
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.scope import Actor
from app.core.dependencies import get_actor_with_company
from app.core.database import get_db
from app.modules.attendance.reporting_repo import get_reporting_repository
from app.modules.attendance.schemas import SessionResponse
from app.modules.attendance.reporting_schemas import (
    SessionsListResponse,
    UserSummaryResponse,
    CompanySummaryResponse,
)
from app.modules.attendance.api.helpers import _require_attendance_feature
from app.modules.attendance.api.reporting_helpers import _normalize_to_utc, _validate_datetime_range
from app.modules.attendance.reporting_service import calculate_user_summary, calculate_company_summary
from app.core.user_lookup import get_display_names

logger = logging.getLogger(__name__)

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
    """GET /api/v1/attendance/sessions — Sessions reporting (WP-11-06 Step 1)

    Query rules:
    - 過濾僅使用 punch_in_time（禁止 punch_out_time 過濾）
    - start_date / end_date 必須為 timezone-aware datetime（naive 回傳 422）
    - 月份歸屬 = punch_in_time Asia/Taipei date
    - duration 讀取 canonical 欄位 duration_minutes

    Scope rules:
    - 員工（無特殊角色）：只能查自己的 sessions
    - 管理者（manager/admin）：可查本公司任意 user 的 sessions
    """
    _require_attendance_feature(actor)

    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

    start_utc = None
    end_utc = None

    if start_date is not None:
        if start_date.tzinfo is None:
            raise HTTPException(status_code=400, detail="start_date must be timezone-aware (naive datetime rejected)")
        start_utc = _normalize_to_utc(start_date)

    if end_date is not None:
        if end_date.tzinfo is None:
            raise HTTPException(status_code=400, detail="end_date must be timezone-aware (naive datetime rejected)")
        end_utc = _normalize_to_utc(end_date)

    _validate_datetime_range(start_utc, end_utc)

    # Scope enforcement
    target_user_id: Optional[UUID] = None
    is_manager = actor.role in ("manager", "admin")

    if user_id is not None:
        try:
            target_user_id = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user_id format")
        if not is_manager and target_user_id != actor.user_id:
            raise HTTPException(status_code=403, detail="Employees can only query their own sessions")
    else:
        if not is_manager:
            target_user_id = actor.user_id

    repo = get_reporting_repository(db)

    sessions = repo.get_sessions_for_reporting(
        company_id=actor.company_id,
        user_id=target_user_id,
        start_utc=start_utc,
        end_utc=end_utc,
        status=status,
        limit=limit,
        offset=offset,
    )

    total = repo.count_sessions_for_reporting(
        company_id=actor.company_id,
        user_id=target_user_id,
        start_utc=start_utc,
        end_utc=end_utc,
        status=status,
    )

    user_ids = list({str(s.user_id) for s in sessions})
    display_names = get_display_names(user_ids, db)

    items = []
    for s in sessions:
        items.append(SessionResponse(
            id=s.id,
            user_id=s.user_id,
            display_name=display_names.get(str(s.user_id)),
            punch_in_time=s.punch_in_time,
            punch_out_time=s.punch_out_time,
            status=s.status,
            duration_minutes=s.duration_minutes,
            notes=s.notes,
        ))

    return SessionsListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/reports/user-summary", response_model=UserSummaryResponse)
def get_user_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
):
    """GET /api/v1/attendance/reports/user-summary — Per-user summary (WP-11-06 Step 2), WP-C1-07: JWT Actor

    Returns attendance summary statistics for the current user.

    Query rules:
    - 過濾僅使用 punch_in_time（禁止 punch_out_time）
    - start_date / end_date 必須為 timezone-aware datetime（naive 回傳 422）
    - total_work_minutes 讀取 canonical 欄位 duration_minutes
    - 聚合在 Python 應用層執行（非 SQL 端）

    Scope rules:
    - 員工只能查詢自己的 summary
    - 嘗試查詢他人回傳 403（本 Step 不支援 manager 查他人）
    """
    _require_attendance_feature(actor)

    start_utc = None
    end_utc = None

    if start_date is not None:
        if start_date.tzinfo is None:
            raise HTTPException(status_code=400, detail="start_date must be timezone-aware (naive datetime rejected)")
        start_utc = _normalize_to_utc(start_date)

    if end_date is not None:
        if end_date.tzinfo is None:
            raise HTTPException(status_code=400, detail="end_date must be timezone-aware (naive datetime rejected)")
        end_utc = _normalize_to_utc(end_date)

    _validate_datetime_range(start_utc, end_utc)

    repo = get_reporting_repository(db)

    sessions = repo.get_user_summary_sessions(
        company_id=actor.company_id,
        user_id=actor.user_id,
        start_utc=start_utc,
        end_utc=end_utc,
    )

    closed_sessions = [s for s in sessions if s.status == 'closed']
    open_sessions = [s for s in sessions if s.status == 'open']

    summary = calculate_user_summary(closed_sessions, open_sessions)

    return UserSummaryResponse(
        user_id=actor.user_id,
        company_id=actor.company_id,
        **summary,
    )


@router.get("/reports/company-summary", response_model=CompanySummaryResponse)
def get_company_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
):
    """GET /api/v1/attendance/reports/company-summary — Company-level summary (WP-11-06 Step 3), WP-C1-07: JWT Actor

    Returns attendance summary statistics for the entire company (all users).

    Query rules:
    - 過濾僅使用 punch_in_time（禁止 punch_out_time）
    - start_date / end_date 必須為 timezone-aware datetime（naive 回傳 422）
    - total_work_minutes 讀取 canonical 欄位 duration_minutes
    - 聚合在 Python 應用層執行（非 SQL 端）
    - total_users_with_sessions 使用 Python set() 去重（非 SQL COUNT DISTINCT）

    Tenant isolation:
    - 所有查詢強制 WHERE company_id = ?（從 JWT Actor 取得）
    - 查詢全公司所有用戶，不過濾 user_id
    """
    _require_attendance_feature(actor)

    if actor.role not in ("manager", "admin"):
        raise HTTPException(status_code=403, detail="Company summary requires manager or admin role")

    start_utc = None
    end_utc = None

    if start_date is not None:
        if start_date.tzinfo is None:
            raise HTTPException(status_code=400, detail="start_date must be timezone-aware (naive datetime rejected)")
        start_utc = _normalize_to_utc(start_date)

    if end_date is not None:
        if end_date.tzinfo is None:
            raise HTTPException(status_code=400, detail="end_date must be timezone-aware (naive datetime rejected)")
        end_utc = _normalize_to_utc(end_date)

    _validate_datetime_range(start_utc, end_utc)

    repo = get_reporting_repository(db)

    sessions = repo.get_company_summary_sessions(
        company_id=actor.company_id,
        start_utc=start_utc,
        end_utc=end_utc,
    )

    closed_sessions = [s for s in sessions if s.status == 'closed']
    open_sessions = [s for s in sessions if s.status == 'open']

    summary = calculate_company_summary(closed_sessions, open_sessions)

    return CompanySummaryResponse(
        company_id=actor.company_id,
        **summary,
    )
