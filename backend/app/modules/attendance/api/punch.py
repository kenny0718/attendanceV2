"""Attendance API — Punch 層 (WP-11-02, WP-11-05C, Phase 2C-A, Phase 2C-C, Phase 2D)

Punch endpoints:
- POST /api/v1/attendance/punch-in
- POST /api/v1/attendance/punch-out
- GET /api/v1/attendance/current-status
- GET /api/v1/attendance/history
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_actor_with_company
from app.core.scope import Actor
from app.modules.attendance.api.anomaly_audit import write_break_anomaly_audit
from app.modules.attendance.api.break_deduction import resolve_break_deduction
from app.modules.attendance.api.punch_close_flow import build_policy_evaluation
from app.modules.attendance.repo import get_attendance_session_repository
from app.modules.attendance.schemas import (
    AttendanceHistoryResponse,
    CurrentStatusResponse,
    PolicyEvaluationResponse,
    PunchInRequest,
    PunchInResponse,
    PunchOutRequest,
    PunchOutResponse,
    SessionResponse,
)

logger = logging.getLogger(__name__)
router_v1 = APIRouter(prefix="/api/v1/attendance", tags=["attendance-v1"])
TZ_TAIPEI = ZoneInfo("Asia/Taipei")


def _normalize_request_datetime(value: Optional[datetime]) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=TZ_TAIPEI)
    return value


# Backward-compatible wrapper for tests / legacy monkeypatch targets.
def _require_attendance_feature(company_id: str, db: Session) -> None:
    from app.modules.attendance import api as attendance_api

    attendance_api._require_attendance_feature(company_id, db)


@router_v1.post("/punch-in", response_model=PunchInResponse, status_code=201)
async def punch_in(
    request: PunchInRequest,
    actor: Actor = Depends(get_actor_with_company),
    http_request: Request = None,
    db: Session = Depends(get_db),
):
    company_id = actor.active_company_id
    user_id = str(actor.user_id)
    _require_attendance_feature(company_id, db)
    repo = get_attendance_session_repository(db)

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    user_uuid = UUID(user_id)
    existing_session = repo.get_open_session(company_id, user_uuid)
    if existing_session:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Already have an open session",
                "error_code": "ALREADY_OPEN_SESSION",
                "open_session_id": str(existing_session.id),
                "punch_in_time": existing_session.punch_in_time.isoformat(),
            },
        )

    punch_in_time = _normalize_request_datetime(request.punch_time)
    session = repo.create_session(
        company_id=company_id,
        user_id=user_uuid,
        punch_in_time=punch_in_time,
        notes=request.notes,
    )

    ip_address = http_request.client.host if http_request and http_request.client else None
    repo.create_punch(
        session_id=session.id,
        company_id=company_id,
        user_id=user_uuid,
        punch_type="in",
        punch_time=punch_in_time,
        ip_address=ip_address,
        location_lat=request.location.latitude if request.location else None,
        location_lng=request.location.longitude if request.location else None,
        notes=request.notes,
    )

    return PunchInResponse(
        session_id=session.id,
        user_id=session.user_id,
        company_id=session.company_id,
        punch_in_time=session.punch_in_time,
        punch_out_time=session.punch_out_time,
        duration_minutes=session.duration_minutes,
        status=session.status,
    )


@router_v1.post("/punch-out", response_model=PunchOutResponse)
async def punch_out(
    request: PunchOutRequest,
    actor: Actor = Depends(get_actor_with_company),
    http_request: Request = None,
    db: Session = Depends(get_db),
):
    company_id = actor.active_company_id
    user_id = str(actor.user_id)
    _require_attendance_feature(company_id, db)
    repo = get_attendance_session_repository(db)

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    user_uuid = UUID(user_id)
    session = repo.get_open_session(company_id, user_uuid)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={"error": "No open session found", "error_code": "NO_OPEN_SESSION"},
        )

    punch_out_time = _normalize_request_datetime(request.punch_time)
    ip_address = http_request.client.host if http_request and http_request.client else None
    repo.create_punch(
        session_id=session.id,
        company_id=company_id,
        user_id=user_uuid,
        punch_type="out",
        punch_time=punch_out_time,
        ip_address=ip_address,
        location_lat=request.location.latitude if request.location else None,
        location_lng=request.location.longitude if request.location else None,
        notes=request.notes,
    )

    gross_minutes = int((punch_out_time - session.punch_in_time).total_seconds() / 60)
    session_punches = repo.get_session_punches(session.id)
    deduction_result = resolve_break_deduction(
        session_punches=session_punches,
        punch_in_time=session.punch_in_time,
        punch_out_time=punch_out_time,
        gross_minutes=gross_minutes,
        logger=logger,
    )
    policy_eval = build_policy_evaluation(
        session=session,
        repo=repo,
        company_id=company_id,
        user_id=user_uuid,
        punch_out_time=punch_out_time,
        gross_minutes=gross_minutes,
    )

    session = repo.close_session(
        session=session,
        punch_out_time=punch_out_time,
        duration_minutes=gross_minutes,
        policy_id=policy_eval.policy_id,
    )

    write_break_anomaly_audit(
        db=db,
        session=session,
        company_id=str(company_id),
        deduction_result=deduction_result,
        logger=logger,
    )

    policy_eval_response = PolicyEvaluationResponse(
        is_late=policy_eval.evaluation.is_late,
        late_minutes=policy_eval.evaluation.late_minutes,
        is_early_leave=policy_eval.evaluation.is_early_leave,
        early_leave_minutes=policy_eval.evaluation.early_leave_minutes,
        is_overtime=policy_eval.evaluation.is_overtime,
        overtime_minutes=policy_eval.evaluation.overtime_minutes,
        work_minutes=policy_eval.evaluation.work_minutes,
        policy_name=policy_eval.evaluation.policy_name,
    )

    return PunchOutResponse(
        session_id=session.id,
        user_id=session.user_id,
        company_id=session.company_id,
        punch_in_time=session.punch_in_time,
        punch_out_time=session.punch_out_time,
        duration_minutes=session.duration_minutes,
        status=session.status,
        policy_evaluation=policy_eval_response,
    )


@router_v1.get("/current-status", response_model=CurrentStatusResponse)
async def get_current_status(
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
):
    company_id = actor.active_company_id
    user_id = str(actor.user_id)
    _require_attendance_feature(company_id, db)
    repo = get_attendance_session_repository(db)

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    user_uuid = UUID(user_id)
    session = repo.get_open_session(company_id, user_uuid)

    if session:
        return CurrentStatusResponse(
            has_open_session=True,
            session=SessionResponse(
                session_id=session.id,
                user_id=session.user_id,
                company_id=session.company_id,
                punch_in_time=session.punch_in_time,
                punch_out_time=session.punch_out_time,
                duration_minutes=session.duration_minutes,
                status=session.status,
            ),
            elapsed_minutes=int((datetime.now(timezone.utc) - session.punch_in_time).total_seconds() / 60),
        )

    return CurrentStatusResponse(has_open_session=False, session=None, elapsed_minutes=None)


@router_v1.get("/history", response_model=AttendanceHistoryResponse)
async def get_history(
    limit: int = 50,
    offset: int = 0,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
):
    company_id = actor.active_company_id
    user_id = str(actor.user_id)
    _require_attendance_feature(company_id, db)
    repo = get_attendance_session_repository(db)

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    user_uuid = UUID(user_id)
    sessions = repo.get_sessions(company_id=company_id, user_id=user_uuid, limit=limit, offset=offset)
    total = repo.count_sessions(company_id=company_id, user_id=user_uuid)

    return AttendanceHistoryResponse(
        sessions=[
            SessionResponse(
                session_id=s.id,
                user_id=s.user_id,
                company_id=s.company_id,
                punch_in_time=s.punch_in_time,
                punch_out_time=s.punch_out_time,
                duration_minutes=s.duration_minutes,
                status=s.status,
            )
            for s in sessions
        ],
        total=total,
        limit=limit,
        offset=offset,
    )
