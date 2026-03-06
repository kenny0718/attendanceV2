"""Attendance API 路由

Phase 4: 注入 db Session
WP-11-02: Punch In/Out API
WP-11-05C: Policy Engine Integration
WP-11-07 Phase 3B: Break Out/In API
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Request, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.modules.attendance.service import get_attendance_service
from app.core.tenant_context import get_current_company_id, get_current_user_id
from app.core.database import get_db
from app.core.config import is_testing, TIMEZONE, get_current_time
from app.modules.attendance.repo import get_attendance_session_repository
from app.modules.attendance.models import AttendancePunch
from app.modules.attendance.schemas import (
    PunchInRequest,
    PunchInResponse,
    PunchOutRequest,
    PunchOutResponse,
    BreakOutRequest,
    BreakOutResponse,
    BreakInRequest,
    BreakInResponse,
    CurrentStatusResponse,
    AttendanceHistoryResponse,
    SessionResponse,
    PolicyEvaluationResponse,
    OutCheckpointRequest,
    OutCheckpointResponse,
    OutCheckpointListItem,
    OutCheckpointListResponse,
    GPSData
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
# 新的 API (WP-11-02, WP-11-05C, WP-11-07)
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
    
    # WP-11-05D: Security guard for punch_time parameter
    if request.punch_time and not is_testing():
        logger.warning(f"punch_time parameter rejected in non-test mode: user={user_id}, company={company_id}")
        raise HTTPException(
            status_code=403,
            detail="punch_time parameter is only allowed in test mode"
        )
    
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
    # Use provided punch_time or current time
    if request.punch_time:
        # Treat naive datetime as local timezone (Asia/Taipei UTC+8)
        if request.punch_time.tzinfo:
            punch_in_time = request.punch_time
        else:
            # Naive datetime: treat as local timezone
            # from zoneinfo import ZoneInfo  # 已在 config 中定義
            local_tz = TIMEZONE
            punch_in_time = request.punch_time.replace(tzinfo=local_tz)
    else:
        # Use local time for current time
        # from zoneinfo import ZoneInfo  # 已在 config 中定義
        local_tz = TIMEZONE
        punch_in_time = datetime.now(local_tz)
    
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
    
    # WP-11-05D: Security guard for punch_time parameter
    if request.punch_time and not is_testing():
        logger.warning(f"punch_time parameter rejected in non-test mode: user={user_id}, company={company_id}")
        raise HTTPException(
            status_code=403,
            detail="punch_time parameter is only allowed in test mode"
        )
    
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
    
    # WP-11-XX: 如果在外出狀態下打下班卡，自動補上返回記錄
    last_break_punch = repo.get_last_break_punch(session.id)
    if last_break_punch and last_break_punch.punch_type == 'break_start':
        # 自動創建返回打卡記錄
        logger.info(f"Auto break-in before punch-out: user={user_id}, session={session.id}")
        auto_break_in_time = datetime.now(TIMEZONE)
        repo.create_punch(
            session_id=session.id,
            company_id=company_id,
            user_id=user_uuid,
            punch_type='break_end',
            punch_time=auto_break_in_time,
            ip_address=http_request.client.host if http_request and http_request.client else None,
            notes='自動返回（下班時補）'
        )
    
    # Punch out
    # Use provided punch_time or current time
    if request.punch_time:
        # Treat naive datetime as local timezone (Asia/Taipei UTC+8)
        if request.punch_time.tzinfo:
            punch_out_time = request.punch_time
        else:
            # Naive datetime: treat as local timezone
            # from zoneinfo import ZoneInfo  # 已在 config 中定義
            local_tz = TIMEZONE
            punch_out_time = request.punch_time.replace(tzinfo=local_tz)
    else:
        # Use local time for current time
        # from zoneinfo import ZoneInfo  # 已在 config 中定義
        local_tz = TIMEZONE
        punch_out_time = datetime.now(local_tz)
    
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


@router_v1.post("/break-out", response_model=BreakOutResponse, status_code=201)
async def break_out(
    request: BreakOutRequest,
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """Break out (外出打卡) - WP-11-07 Phase 3B"""
    repo = get_attendance_session_repository(db)
    
    # Validate user_id
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    user_uuid = UUID(user_id)
    
    # WP-11-05D: Security guard for punch_time parameter
    if request.punch_time and not is_testing():
        logger.warning(f"punch_time parameter rejected in non-test mode: user={user_id}, company={company_id}")
        raise HTTPException(
            status_code=403,
            detail="punch_time parameter is only allowed in test mode"
        )
    
    # Get open session
    session = repo.get_open_session(company_id, user_uuid)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "No open session found. Please punch in first.",
                "error_code": "NO_OPEN_SESSION"
            }
        )
    
    # WP-11-XX: 允許連續外出打卡，移除 ALREADY_ON_BREAK 檢查
    #     # Check if already on break (has break_start without break_end)
    #     last_break_punch = repo.get_last_break_punch(session.id)
    #     if last_break_punch and last_break_punch.punch_type == 'break_start':
    #         raise HTTPException(
    #             status_code=409,
    #             detail={
    #                 "error": "Already on break. Please break in first.",
    #                 "error_code": "ALREADY_ON_BREAK",
    #                 "last_break_out_time": last_break_punch.punch_time.isoformat()
    #             }
    #         )
    
    # Create break out punch
    if request.punch_time:
        if request.punch_time.tzinfo:
            break_out_time = request.punch_time
        else:
            # from zoneinfo import ZoneInfo  # 已在 config 中定義
            local_tz = TIMEZONE
            break_out_time = request.punch_time.replace(tzinfo=local_tz)
    else:
        # from zoneinfo import ZoneInfo  # 已在 config 中定義
        local_tz = TIMEZONE
        break_out_time = datetime.now(local_tz)
    
    ip_address = http_request.client.host if http_request and http_request.client else None
    punch = repo.create_punch(
        session_id=session.id,
        company_id=company_id,
        user_id=user_uuid,
        punch_type='break_start',
        punch_time=break_out_time,
        ip_address=ip_address,
        location_lat=request.location.latitude if request.location else None,
        location_lng=request.location.longitude if request.location else None,
        notes=request.notes
    )
    
    return BreakOutResponse(
        punch_id=punch.id,
        session_id=session.id,
        punch_time=punch.punch_time,
        message="Break out successful"
    )


@router_v1.post("/break-in", response_model=BreakInResponse, status_code=201)
async def break_in(
    request: BreakInRequest,
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """Break in (返回打卡) - WP-11-07 Phase 3B"""
    repo = get_attendance_session_repository(db)
    
    # Validate user_id
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    user_uuid = UUID(user_id)
    
    # WP-11-05D: Security guard for punch_time parameter
    if request.punch_time and not is_testing():
        logger.warning(f"punch_time parameter rejected in non-test mode: user={user_id}, company={company_id}")
        raise HTTPException(
            status_code=403,
            detail="punch_time parameter is only allowed in test mode"
        )
    
    # Get open session
    session = repo.get_open_session(company_id, user_uuid)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "No open session found. Please punch in first.",
                "error_code": "NO_OPEN_SESSION"
            }
        )
    
    # Check if on break (has break_start without break_end)
    last_break_punch = repo.get_last_break_punch(session.id)
    if not last_break_punch or last_break_punch.punch_type != 'break_start':
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Not on break. Please break out first.",
                "error_code": "NOT_ON_BREAK"
            }
        )
    
    # Create break in punch
    if request.punch_time:
        if request.punch_time.tzinfo:
            break_in_time = request.punch_time
        else:
            # from zoneinfo import ZoneInfo  # 已在 config 中定義
            local_tz = TIMEZONE
            break_in_time = request.punch_time.replace(tzinfo=local_tz)
    else:
        # from zoneinfo import ZoneInfo  # 已在 config 中定義
        local_tz = TIMEZONE
        break_in_time = datetime.now(local_tz)
    
    ip_address = http_request.client.host if http_request and http_request.client else None
    punch = repo.create_punch(
        session_id=session.id,
        company_id=company_id,
        user_id=user_uuid,
        punch_type='break_end',
        punch_time=break_in_time,
        ip_address=ip_address,
        location_lat=request.location.latitude if request.location else None,
        location_lng=request.location.longitude if request.location else None,
        notes=request.notes
    )
    
    return BreakInResponse(
        punch_id=punch.id,
        session_id=session.id,
        punch_time=punch.punch_time,
        message="Break in successful"
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
        elapsed = get_current_time() - session.punch_in_time
        elapsed_minutes = int(elapsed.total_seconds() / 60)
        
        # Check if user is on break (WP-11-07 Phase 3B)
        is_on_break = False
        last_break_punch = repo.get_last_break_punch(session.id)
        if last_break_punch and last_break_punch.punch_type == 'break_start':
            is_on_break = True
        
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
            elapsed_minutes=elapsed_minutes,
            is_on_break=is_on_break
        )
    else:
        return CurrentStatusResponse(
            has_open_session=False,
            session=None,
            elapsed_minutes=None,
            is_on_break=False
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
    
    session_responses = []
    for s in sessions:
        # 獲取該 session 的所有 punches
        punches = repo.get_session_punches(s.id)
        punch_list = [
            {
                'punch_id': str(p.id),
                'punch_type': p.punch_type,
                'punch_time': p.punch_time,
                'notes': p.notes
            }
            for p in punches
        ]
        
        session_responses.append(
            SessionResponse(
                session_id=s.id,
                user_id=s.user_id,
                company_id=s.company_id,
                punch_in_time=s.punch_in_time,
                punch_out_time=s.punch_out_time,
                duration_minutes=s.duration_minutes,
                status=s.status,
                punches=punch_list
            )
        )
    
    return AttendanceHistoryResponse(
        sessions=session_responses,
        total=total,
        limit=limit,
        offset=offset
    )



@router_v1.patch("/punch/{punch_id}/note", response_model=dict)
async def update_punch_note(
    punch_id: str,
    note_data: dict = Body(...),
    user_id: int = Depends(get_current_user_id),
    company_id: str = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """
    更新打卡記錄的備註
    
    Args:
        punch_id: 打卡記錄 ID (UUID 字符串)
        note_data: 包含 notes 字段的字典
        user_id: 當前用戶 ID
        company_id: 公司 ID
        db: 數據庫會話
    
    Returns:
        更新後的打卡記錄
    """
    # 獲取打卡記錄
    punch = db.query(AttendancePunch).filter(
        AttendancePunch.id == punch_id,
        AttendancePunch.user_id == user_id
    ).first()
    
    if not punch:
        raise HTTPException(status_code=404, detail="打卡記錄不存在")
    
    # 只允許更新外出打卡的備註
    if punch.punch_type not in ['break_start', 'break_end']:
        raise HTTPException(status_code=400, detail="只能編輯外出打卡記錄")
    
    # 更新備註
    punch.notes = note_data.get('notes', '')
    db.commit()
    db.refresh(punch)
    
    return {
        "message": "備註已更新",
        "punch_id": str(punch.id),
        "notes": punch.notes
    }


@router_v1.get("/break-punches", response_model=dict)
async def get_break_punches(
    limit: int = 50,
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get today's break punches (外出打卡記錄)"""
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    from datetime import datetime, time
    from app.modules.attendance.models import AttendancePunch
    
    user_uuid = UUID(user_id)
    repo = get_attendance_session_repository(db)
    
    # Get today's open session
    session = repo.get_open_session(company_id, user_uuid)
    if not session:
        return {"punches": [], "total": 0}
    
    # Get all break punches for this session
    punches = (
        db.query(AttendancePunch)
        .filter(
            AttendancePunch.session_id == session.id,
            AttendancePunch.punch_type.in_(['break_start', 'break_end'])
        )
        .order_by(AttendancePunch.punch_time.desc())
        .limit(limit)
        .all()
    )
    
    punch_list = [
        {
            "punch_id": str(p.id),
            "punch_type": p.punch_type,
            "punch_time": p.punch_time.isoformat(),
            "notes": p.notes,
            "location_lat": p.location_lat,
            "location_lng": p.location_lng
        }
        for p in punches
    ]
    
    return {
        "punches": punch_list,
        "total": len(punch_list),
        "session_id": str(session.id)
    }


# ============================================
# WP-11-10: OUT Checkpoint API
# ============================================

@router_v1.post("/out-checkpoint", response_model=OutCheckpointResponse, status_code=201)
async def create_out_checkpoint(
    request: OutCheckpointRequest,
    req: Request,
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create OUT checkpoint - WP-11-10
    
    Rules:
    - Mobile device MUST provide GPS
    - PC device MAY provide GPS (optional)
    - Multiple checkpoints allowed per session
    - De-dup: reject if within 30s AND within 50m
    """
    from app.modules.attendance.repo import get_out_checkpoint_repository
    from app.modules.attendance.gps_utils import is_within_distance
    
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    user_uuid = UUID(user_id)
    repo = get_attendance_session_repository(db)
    checkpoint_repo = get_out_checkpoint_repository(db)
    
    # Validation: Mobile requires GPS
    if request.device_type == 'mobile' and not request.gps:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "請開啟定位後再外出打卡",
                "error_code": "GPS_REQUIRED",
                "field": "gps"
            }
        )
    
    # Anti-spam: Check for duplicate within 30s + 50m
    recent_checkpoint = checkpoint_repo.get_recent_checkpoint(
        company_id=company_id,
        user_id=user_uuid,
        within_seconds=30
    )
    
    if recent_checkpoint and request.gps and recent_checkpoint.gps_lat:
        # Both have GPS, check distance
        if is_within_distance(
            (request.gps.latitude, request.gps.longitude),
            (float(recent_checkpoint.gps_lat), float(recent_checkpoint.gps_lng)),
            max_distance_m=50
        ):
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "請勿重複打卡",
                    "error_code": "DUPLICATE_CHECKPOINT",
                    "last_checkpoint_time": recent_checkpoint.punch_time.isoformat()
                }
            )
    
    # Get open session (optional - allow checkpoint without session)
    session = repo.get_open_session(company_id, user_uuid)
    session_id = session.id if session else None
    
    # Get client info
    ip_address = req.client.host if req.client else None
    user_agent = req.headers.get("user-agent")
    
    # Server-set punch time
    punch_time = get_current_time()
    
    # Create checkpoint
    checkpoint = checkpoint_repo.create_checkpoint(
        company_id=company_id,
        user_id=user_uuid,
        device_type=request.device_type,
        punch_time=punch_time,
        session_id=session_id,
        gps_lat=request.gps.latitude if request.gps else None,
        gps_lng=request.gps.longitude if request.gps else None,
        gps_accuracy_m=request.gps.accuracy if request.gps else None,
        gps_captured_at=request.gps.captured_at if request.gps else None,
        gps_provider=request.gps.provider if request.gps else None,
        client_timezone=request.client_timezone,
        client_user_agent=user_agent,
        ip_address=ip_address,
        notes=request.notes
    )
    
    # Build response
    gps_response = None
    if checkpoint.gps_lat and checkpoint.gps_lng:
        gps_response = GPSData(
            latitude=float(checkpoint.gps_lat),
            longitude=float(checkpoint.gps_lng),
            accuracy=float(checkpoint.gps_accuracy_m) if checkpoint.gps_accuracy_m else None,
            captured_at=checkpoint.gps_captured_at,
            provider=checkpoint.gps_provider
        )
    
    return OutCheckpointResponse(
        checkpoint_id=checkpoint.id,
        punch_time=checkpoint.punch_time,
        gps=gps_response,
        message="Checkpoint recorded successfully"
    )


@router_v1.get("/out-checkpoints", response_model=OutCheckpointListResponse)
async def get_out_checkpoints(
    limit: int = 50,
    offset: int = 0,
    session_id: Optional[str] = None,
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get OUT checkpoints list - WP-11-10"""
    from app.modules.attendance.repo import get_out_checkpoint_repository
    
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    user_uuid = UUID(user_id)
    session_uuid = UUID(session_id) if session_id else None
    
    checkpoint_repo = get_out_checkpoint_repository(db)
    
    checkpoints = checkpoint_repo.get_checkpoints(
        company_id=company_id,
        user_id=user_uuid,
        limit=limit,
        offset=offset,
        session_id=session_uuid
    )
    
    total = checkpoint_repo.count_checkpoints(
        company_id=company_id,
        user_id=user_uuid,
        session_id=session_uuid
    )
    
    # Build response
    checkpoint_items = []
    for cp in checkpoints:
        gps_data = None
        if cp.gps_lat and cp.gps_lng:
            gps_data = GPSData(
                latitude=float(cp.gps_lat),
                longitude=float(cp.gps_lng),
                accuracy=float(cp.gps_accuracy_m) if cp.gps_accuracy_m else None,
                captured_at=cp.gps_captured_at,
                provider=cp.gps_provider
            )
        
        checkpoint_items.append(OutCheckpointListItem(
            checkpoint_id=cp.id,
            punch_time=cp.punch_time,
            device_type=cp.device_type,
            gps=gps_data,
            notes=cp.notes
        ))
    
    return OutCheckpointListResponse(
        checkpoints=checkpoint_items,
        total=total,
        limit=limit,
        offset=offset
    )
