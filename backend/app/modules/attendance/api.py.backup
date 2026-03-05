"""Attendance API 路由

Phase 4: 注入 db Session
WP-11-02: Punch In/Out API
WP-11-05C: Policy Engine Integration
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.modules.attendance.service import get_attendance_service
from app.core.tenant_context import get_current_company_id, get_current_user_id
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
    PolicyEvaluationResponse
)
from app.modules.attendance.policy_engine import AttendancePolicyEngine

logger = logging.getLogger(__name__)

# 建立路由 - 保持舊的 prefix 以兼容舊 API
router = APIRouter(prefix="/api/attendance", tags=["attendance"])

# 新的 v1 router
router_v1 = APIRouter(prefix="/api/v1/attendance", tags=["attendance-v1"])


# ============================================
# 舊的 API (Phase 4) - 保持兼容
# ============================================

class MockCreateResponse(BaseModel):
    """Mock 建立考勤記錄回應"""
    attendance_record_id: str = Field(..., description="考勤記錄 ID")


class ApproveRequest(BaseModel):
    """核准考勤請求"""
    employee_id: str = Field(..., description="員工 ID")
    approved_by: str | None = Field(None, description="核准人 ID（選填）")


class ApproveResponse(BaseModel):
    """核准考勤回應"""
    ok: bool = Field(..., description="操作是否成功")
    payload: Dict[str, Any] = Field(..., description="發出的事件 payload")


@router.post("/mock-create", response_model=MockCreateResponse)
async def mock_create_attendance(
    current_company_id: str = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """建立考勤記錄（Phase 4: 真正寫 DB）"""
    service = get_attendance_service(db)
    attendance_record_id = service.mock_create_attendance(
        company_id=current_company_id
    )
    
    return MockCreateResponse(attendance_record_id=attendance_record_id)


@router.post("/{attendance_record_id}/approve", response_model=ApproveResponse)
async def approve_attendance(
    attendance_record_id: str,
    request: ApproveRequest,
    current_company_id: str = Depends(get_current_company_id),
    current_user_id: str | None = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """核准考勤記錄（Phase 4: 真正寫 DB）"""
    service = get_attendance_service(db)
    
    result = service.approve_attendance(
        attendance_record_id=attendance_record_id,
        company_id=current_company_id,
        employee_id=request.employee_id,
        approved_by=request.approved_by or current_user_id
    )
    
    return ApproveResponse(**result)


# ============================================
# 新的 API (WP-11-02, WP-11-05C)
# ============================================

@router_v1.post("/punch-in", response_model=PunchInResponse, status_code=201)
async def punch_in(
    request: PunchInRequest,
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """Punch in (打卡上班) - WP-11-02"""
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
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """Punch out (打卡下班) - WP-11-02, WP-11-05C: with policy engine"""
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
    
    # Calculate duration
    duration = punch_out_time - session.punch_in_time
    duration_minutes = int(duration.total_seconds() / 60)
    
    # WP-11-05C: Get user's policy and evaluate
    policy = repo.get_user_policy(company_id, user_uuid)
    
    # Temporarily set session fields for evaluation
    session.punch_out_time = punch_out_time
    session.duration_minutes = duration_minutes
    session.status = 'closed'
    
    # Evaluate policy
    policy_engine = AttendancePolicyEngine()
    evaluation = policy_engine.evaluate(session, policy)
    
    # Close session with policy info
    session = repo.close_session(
        session=session,
        punch_out_time=punch_out_time,
        duration_minutes=duration_minutes,
        policy_id=policy.id if policy else None
    )
    
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
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current attendance status - WP-11-02"""
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
        
        return CurrentStatusResponse(
            has_open_session=True,
            session=session_response,
            elapsed_minutes=elapsed_minutes
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
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get attendance history - WP-11-02"""
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
