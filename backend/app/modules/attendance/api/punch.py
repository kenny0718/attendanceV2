"""Attendance API — Punch 層 (WP-11-02, WP-11-05C, Phase 2C-A)

Punch endpoints:
- POST /api/v1/attendance/punch-in
- POST /api/v1/attendance/punch-out
- GET /api/v1/attendance/current-status
- GET /api/v1/attendance/history

WP-11-02: Punch In/Out API
WP-11-05C: Policy Engine Integration
WP-C1-07: JWT Actor Migration
Phase 2C-A: Break Deduction Integration + Anomaly Logging (Option C)
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session

from app.core.scope import Actor
from app.core.dependencies import get_actor_with_company
from app.core.database import get_db
from app.modules.attendance.repo import get_attendance_session_repository
from app.modules.attendance.schemas import (
    PunchInRequest,
    PunchInResponse,
    PunchOutRequest,
    PunchOutResponse,
    CurrentStatusResponse,
    AttendanceHistoryResponse,
    SessionResponse,
    PolicyEvaluationResponse,
)
from app.modules.attendance.policy_engine import AttendancePolicyEngine
from app.modules.attendance.api.helpers import _require_attendance_feature
from app.modules.attendance.work_hour_engine import (
    calculate_break_deduction,
    BreakPunchDTO,
)

logger = logging.getLogger(__name__)

# Punch router
router_v1 = APIRouter(prefix="/api/v1/attendance", tags=["attendance-v1"])


# ============================================
# 新的 API (WP-11-02, WP-11-05C)
# ============================================

@router_v1.post("/punch-in", response_model=PunchInResponse, status_code=201)
async def punch_in(
    request: PunchInRequest,
    actor: Actor = Depends(get_actor_with_company),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """Punch in (打卡上班) - WP-11-02, WP-C1-07: JWT Actor"""
    company_id = actor.active_company_id
    user_id = str(actor.user_id)
    # --- Feature Gate (WP-C1-06) ---
    _require_attendance_feature(company_id, db)
    repo = get_attendance_session_repository(db)
    
    # Validate user_id
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    user_uuid = UUID(user_id)
    
    # Check for existing open session
    existing_session = repo.get_open_session(company_id, user_uuid)
    if existing_session:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Already have an open session",
                "error_code": "ALREADY_OPEN_SESSION",
                "open_session_id": str(existing_session.id),
                "punch_in_time": existing_session.punch_in_time.isoformat()
            }
        )
    
    # Create new session
    punch_in_time = datetime.now(timezone.utc)
    session = repo.create_session(
        company_id=company_id,
        user_id=user_uuid,
        punch_in_time=punch_in_time,
        notes=request.notes
    )
    
    # Create punch record
    ip_address = http_request.client.host if http_request and http_request.client else None
    repo.create_punch(
        session_id=session.id,
        company_id=company_id,
        user_id=user_uuid,
        punch_type='in',
        punch_time=punch_in_time,
        ip_address=ip_address,
        location_lat=request.location.latitude if request.location else None,
        location_lng=request.location.longitude if request.location else None,
        notes=request.notes
    )
    
    return PunchInResponse(
        session_id=session.id,
        user_id=session.user_id,
        company_id=session.company_id,
        punch_in_time=session.punch_in_time,
        punch_out_time=session.punch_out_time,
        duration_minutes=session.duration_minutes,
        status=session.status
    )


@router_v1.post("/punch-out", response_model=PunchOutResponse)
async def punch_out(
    request: PunchOutRequest,
    actor: Actor = Depends(get_actor_with_company),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """Punch out (打卡下班) - WP-11-02, WP-11-05C: with policy engine, WP-C1-07: JWT Actor
    Phase 2C-A: break deduction integrated (gross only written to DB).
    """
    company_id = actor.active_company_id
    user_id = str(actor.user_id)
    # --- Feature Gate (WP-C1-06) ---
    _require_attendance_feature(company_id, db)
    repo = get_attendance_session_repository(db)
    
    # Validate user_id
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    user_uuid = UUID(user_id)
    
    # Get open session
    session = repo.get_open_session(company_id, user_uuid)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "No open session found",
                "error_code": "NO_OPEN_SESSION"
            }
        )
    
    # Punch out
    punch_out_time = datetime.now(timezone.utc)
    
    # Create punch record
    ip_address = http_request.client.host if http_request and http_request.client else None
    repo.create_punch(
        session_id=session.id,
        company_id=company_id,
        user_id=user_uuid,
        punch_type='out',
        punch_time=punch_out_time,
        ip_address=ip_address,
        location_lat=request.location.latitude if request.location else None,
        location_lng=request.location.longitude if request.location else None,
        notes=request.notes
    )
    
    # Calculate gross duration (canonical value -- written to DB)
    duration = punch_out_time - session.punch_in_time
    gross_minutes = int(duration.total_seconds() / 60)

    # Phase 2C-A: Break deduction (derived only -- NOT written to DB)
    session_punches = repo.get_session_punches(session.id)
    break_punches = [
        p for p in session_punches
        if p.punch_type in ("break_start", "break_end")
    ]
    break_punch_dtos = [
        BreakPunchDTO(
            punch_type=p.punch_type,
            punch_time=p.punch_time,
            punch_id=str(p.id),
        )
        for p in break_punches
    ]
    deduction_result = calculate_break_deduction(
        session.punch_in_time,
        punch_out_time,
        break_punch_dtos,
    )
    # Note: deduction_result.net_work_minutes is derived/informational only.
    # session.duration_minutes must remain gross_minutes.

    # WP-11-05C: Get user's policy and evaluate
    policy = repo.get_user_policy(company_id, user_uuid)
    
    # Temporarily set session fields for evaluation
    session.punch_out_time = punch_out_time
    session.duration_minutes = gross_minutes
    session.status = 'closed'
    
    # Evaluate policy
    policy_engine = AttendancePolicyEngine()
    evaluation = policy_engine.evaluate(session, policy)
    
    # Close session with policy info -- duration_minutes MUST be gross_minutes
    session = repo.close_session(
        session=session,
        punch_out_time=punch_out_time,
        duration_minutes=gross_minutes,
        policy_id=policy.id if policy else None
    )

    # Phase 2C-A: Anomaly logging (Option C) -- non-blocking, isolated try/except
    if deduction_result.anomaly_count > 0:
        try:
            for a in deduction_result.anomalies:
                logger.warning(str({
                    "event": "break_anomaly",
                    "session_id": str(session.id),
                    "company_id": str(company_id),
                    "user_id": str(session.user_id),
                    "anomaly_type": a.anomaly_type,
                    "gross_minutes": deduction_result.gross_minutes,
                    "break_minutes": deduction_result.break_minutes,
                    "net_work_minutes": deduction_result.net_work_minutes,
                    "was_clamped": deduction_result.was_clamped,
                    "anomaly_count": deduction_result.anomaly_count,
                    "related_punch_ids": a.related_punch_ids,
                    "message": a.message,
                }))
        except Exception:
            logger.error("Failed to log break anomaly", exc_info=True)

    # Build response with policy evaluation
    policy_eval_response = PolicyEvaluationResponse(
        is_late=evaluation.is_late,
        late_minutes=evaluation.late_minutes,
        is_early_leave=evaluation.is_early_leave,
        early_leave_minutes=evaluation.early_leave_minutes,
        is_overtime=evaluation.is_overtime,
        overtime_minutes=evaluation.overtime_minutes,
        work_minutes=evaluation.work_minutes,
        policy_name=evaluation.policy_name
    )
    
    return PunchOutResponse(
        session_id=session.id,
        user_id=session.user_id,
        company_id=session.company_id,
        punch_in_time=session.punch_in_time,
        punch_out_time=session.punch_out_time,
        duration_minutes=session.duration_minutes,
        status=session.status,
        policy_evaluation=policy_eval_response
    )


@router_v1.get("/current-status", response_model=CurrentStatusResponse)
async def get_current_status(
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    """Get current attendance status - WP-11-02, WP-C1-07: JWT Actor"""
    company_id = actor.active_company_id
    user_id = str(actor.user_id)
    # --- Feature Gate (WP-C1-06) ---
    _require_attendance_feature(company_id, db)
    repo = get_attendance_session_repository(db)
    
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    user_uuid = UUID(user_id)
    session = repo.get_open_session(company_id, user_uuid)
    
    if session:
        elapsed = datetime.now(timezone.utc) - session.punch_in_time
        elapsed_minutes = int(elapsed.total_seconds() / 60)
        
        session_response = SessionResponse(
            session_id=session.id,
            user_id=session.user_id,
            company_id=session.company_id,
            punch_in_time=session.punch_in_time,
            punch_out_time=session.punch_out_time,
            duration_minutes=session.duration_minutes,
            status=session.status
        )
        
        # WP-11-11.5 Blocker Fix: 計算 is_on_break 狀態
        # 檢查最後一筆 break punch 是 break_start 還是 break_end
        is_on_break = False
        last_break_punch = repo.get_last_break_punch(session.id)
        if last_break_punch and last_break_punch.punch_type == 'break_start':
            is_on_break = True
        
        return CurrentStatusResponse(
            has_open_session=True,
            session=session_response,
            elapsed_minutes=elapsed_minutes,
            is_on_break=is_on_break
        )
    else:
        return CurrentStatusResponse(
            has_open_session=False,
            session=None,
            elapsed_minutes=None
        )


@router_v1.get("/history", response_model=AttendanceHistoryResponse)
async def get_attendance_history(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    """Get attendance history - WP-11-02, WP-C1-07: JWT Actor"""
    company_id = actor.active_company_id
    user_id = str(actor.user_id)
    # --- Feature Gate (WP-C1-06) ---
    _require_attendance_feature(company_id, db)
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    repo = get_attendance_session_repository(db)
    user_uuid = UUID(user_id)
    
    sessions = repo.get_sessions(
        company_id=company_id,
        user_id=user_uuid,
        limit=limit,
        offset=offset,
        status=status
    )
    
    total = repo.count_sessions(
        company_id=company_id,
        user_id=user_uuid,
        status=status
    )
    
    session_responses = [
        SessionResponse(
            session_id=s.id,
            user_id=s.user_id,
            company_id=s.company_id,
            punch_in_time=s.punch_in_time,
            punch_out_time=s.punch_out_time,
            duration_minutes=s.duration_minutes,
            status=s.status
        )
        for s in sessions
    ]
    
    return AttendanceHistoryResponse(
        sessions=session_responses,
        total=total,
        limit=limit,
        offset=offset
    )
