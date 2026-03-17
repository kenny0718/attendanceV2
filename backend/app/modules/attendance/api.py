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
from app.modules.attendance.repo import get_attendance_session_repository, get_reporting_repository
from app.modules.attendance.schemas import (
    BreakOutRequest,
    BreakInRequest,
    BreakOutResponse,
    BreakInResponse,
    PunchInRequest,
    PunchInResponse,
    PunchOutRequest,
    PunchOutResponse,
    CurrentStatusResponse,
    AttendanceHistoryResponse,
    SessionResponse,
    PolicyEvaluationResponse,
    SessionsListResponse,
    UserSummaryResponse,
    CompanySummaryResponse
)
from app.modules.attendance.policy_engine import AttendancePolicyEngine
from app.core.features import FeatureKeys
from app.core.feature_service import get_feature_service, FeatureDisabledError

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


# ============================================
# Feature Gate Helper (WP-C1-06)
# ============================================

def _require_attendance_feature(company_id: str, db) -> None:
    """attendance.core Feature Gate - raises 403 if disabled"""
    try:
        feature_service = get_feature_service(db)
        feature_service.require_enabled(company_id, FeatureKeys.ATTENDANCE_CORE)
    except FeatureDisabledError as e:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "FEATURE_DISABLED",
                "feature": e.feature_key,
                "message": str(e),
            }
        )

@router_v1.post("/punch-in", response_model=PunchInResponse, status_code=201)
async def punch_in(
    request: PunchInRequest,
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """Punch in (打卡上班) - WP-11-02"""
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
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """Punch out (打卡下班) - WP-11-02, WP-11-05C: with policy engine"""
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
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get attendance history - WP-11-02"""
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


# ============================================
# WP-11-11.5: Break Out/In API (Blocker Fix)
# ============================================

@router_v1.post("/break-out", response_model=BreakOutResponse, status_code=201)
async def break_out(
    request: BreakOutRequest,
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """Break out (外出打卡) - WP-11-11.5 Blocker Fix, WP-11-13 Location Policy
    
    允許連續外出打卡，不需要先返回
    
    WP-11-13: 加入 location policy 後端 authoritative enforcement
    """
    # --- Feature Gate (WP-C1-06) ---
    _require_attendance_feature(company_id, db)
    repo = get_attendance_session_repository(db)
    
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
    
    # WP-11-13: Location policy enforcement (後端 authoritative)
    matched_location_id = None
    if request.location:
        from app.modules.attendance.location_policy_service import get_location_policy_service
        
        policy_service = get_location_policy_service(db)
        policy_check = policy_service.check_location_policy(
            company_id=company_id,
            latitude=request.location.latitude,
            longitude=request.location.longitude
        )
        
        if not policy_check.allowed:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": policy_check.reason,
                    "error_code": "LOCATION_POLICY_VIOLATION",
                    "nearest_location": policy_check.nearest_location
                }
            )
        
        # 記錄匹配的 location_id
        if policy_check.matched_location:
            matched_location_id = UUID(policy_check.matched_location["id"])
    
    # Create break_start punch
    punch_time = request.punch_time or datetime.now(timezone.utc)
    ip_address = http_request.client.host if http_request and http_request.client else None
    
    punch = repo.create_punch(
        session_id=session.id,
        company_id=company_id,
        user_id=user_uuid,
        punch_type='break_start',
        punch_time=punch_time,
        ip_address=ip_address,
        location_lat=request.location.latitude if request.location else None,
        location_lng=request.location.longitude if request.location else None,
        notes=request.notes,
        location_id=matched_location_id  # WP-11-13: 記錄匹配的地點
    )
    
    return BreakOutResponse(
        punch_id=punch.id,
        session_id=session.id,
        punch_time=punch.punch_time,
        message="外出打卡成功"
    )


@router_v1.post("/break-in", response_model=BreakInResponse, status_code=201)
async def break_in(
    request: BreakInRequest,
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """Break in (返回打卡) - WP-11-11.5 Blocker Fix"""
    repo = get_attendance_session_repository(db)
    # --- Feature Gate (WP-C1-06) ---
    _require_attendance_feature(company_id, db)
    
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
    
    # Create break_end punch
    punch_time = request.punch_time or datetime.now(timezone.utc)
    ip_address = http_request.client.host if http_request and http_request.client else None
    
    punch = repo.create_punch(
        session_id=session.id,
        company_id=company_id,
        user_id=user_uuid,
        punch_type='break_end',
        punch_time=punch_time,
        ip_address=ip_address,
        location_lat=request.location.latitude if request.location else None,
        location_lng=request.location.longitude if request.location else None,
        notes=request.notes
    )
    
    return BreakInResponse(
        punch_id=punch.id,
        session_id=session.id,
        punch_time=punch.punch_time,
        message="返回打卡成功"
    )


@router_v1.get("/break-punches")
async def get_break_punches(
    limit: int = 50,
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get today's break punches (今日外出/返回記錄) - WP-11-11.5 Blocker Fix
    
    Returns all break_start and break_end punches for today
    """
    # --- Feature Gate (WP-C1-06) ---
    _require_attendance_feature(company_id, db)
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    user_uuid = UUID(user_id)
    
    # Get today's date range (UTC+8)
    from datetime import date, timedelta
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_of_day = start_of_day + timedelta(days=1)
    
    # Query break punches
    from app.modules.attendance.models import AttendancePunch
    from sqlalchemy import and_
    
    punches = (
        db.query(AttendancePunch)
        .filter(
            and_(
                AttendancePunch.company_id == company_id,
                AttendancePunch.user_id == user_uuid,
                AttendancePunch.punch_type.in_(['break_start', 'break_end']),
                AttendancePunch.punch_time >= start_of_day,
                AttendancePunch.punch_time < end_of_day
            )
        )
        .order_by(AttendancePunch.punch_time.desc())
        .limit(limit)
        .all()
    )
    
    # Format response
    punch_list = [
        {
            "punch_id": str(punch.id),
            "punch_type": punch.punch_type,
            "punch_time": punch.punch_time.isoformat(),
            "notes": punch.notes,
            "location_lat": float(punch.location_lat) if punch.location_lat else None,
            "location_lng": float(punch.location_lng) if punch.location_lng else None
        }
        for punch in punches
    ]
    
    return {
        "punches": punch_list,
        "total": len(punch_list)
    }


@router_v1.patch("/punch/{punch_id}/note")
async def update_punch_note(
    punch_id: str,
    request: dict,
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update punch note (更新打卡備註) - WP-11-11.5"""
    # --- Feature Gate (WP-C1-06) ---
    _require_attendance_feature(company_id, db)
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    user_uuid = UUID(user_id)
    punch_uuid = UUID(punch_id)
    
    # Get punch record
    from app.modules.attendance.models import AttendancePunch
    punch = db.query(AttendancePunch).filter(
        AttendancePunch.id == punch_uuid,
        AttendancePunch.company_id == company_id,
        AttendancePunch.user_id == user_uuid
    ).first()
    
    if not punch:
        raise HTTPException(status_code=404, detail="Punch record not found")
    
    # Update notes
    notes = request.get('notes', '')
    punch.notes = notes
    db.commit()
    
    return {
        "success": True,
        "punch_id": str(punch.id),
        "notes": punch.notes
    }


# ============================================
# WP-11-06 Step 1: Sessions Reporting Endpoint
# ============================================

def _normalize_to_utc(dt):
    """將 timezone-aware datetime 轉換為 UTC。
    naive datetime（無 tzinfo）呼叫方不應傳入，應由 validator 在 API 層攔截。
    """
    from datetime import timezone as _tz
    if dt is None:
        return None
    return dt.astimezone(_tz.utc)


@router_v1.get("/sessions", response_model=SessionsListResponse)
async def get_sessions_reporting(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    company_id: str = Depends(get_current_company_id),
    current_user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
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
    # --- Feature Gate (WP-C1-06) ---
    _require_attendance_feature(company_id, db)
    # --- 驗證 limit 範圍 ---
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

    # --- 驗證 datetime 為 timezone-aware ---
    if start_date is not None and start_date.tzinfo is None:
        raise HTTPException(
            status_code=422,
            detail="start_date must be timezone-aware (naive datetime rejected)"
        )
    if end_date is not None and end_date.tzinfo is None:
        raise HTTPException(
            status_code=422,
            detail="end_date must be timezone-aware (naive datetime rejected)"
        )

    # --- 確認 current_user_id 存在 ---
    if not current_user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    # --- User scope 解析 ---
    # 目前系統使用 Header auth，無 role 欄位可查
    # 規則：若 user_id 查詢參數傳入且與 current_user_id 不同，視為管理者操作
    # 員工只能查自己（user_id 參數若為 None 或等於自己，允許）
    # 若 user_id 參數傳入且不等於自己，且非管理者，回傳 403
    # 為安全起見：當 user_id 未傳入時，預設查詢者本身
    from uuid import UUID
    target_user_uuid: Optional[UUID] = None

    if user_id is not None:
        try:
            requested_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user_id format")

        current_uuid = UUID(current_user_id)
        if requested_uuid != current_uuid:
            # 查詢他人：需要管理者身份
            # 目前 Header auth 無 role，暫以 X-User-ID == requested 不同者禁止
            # manager 可透過不傳 user_id 查全公司，或傳入自己 user_id
            # 此處嚴格：查他人一律 403（等 JWT migration 後可解鎖）
            raise HTTPException(
                status_code=403,
                detail="Employees can only query their own sessions"
            )
        target_user_uuid = requested_uuid
    else:
        # user_id 未傳入：查詢者本身
        target_user_uuid = UUID(current_user_id)

    # --- 正規化 datetime 至 UTC ---
    start_utc = _normalize_to_utc(start_date)
    end_utc = _normalize_to_utc(end_date)

    # --- 查詢 ---
    repo = get_reporting_repository(db)

    sessions = repo.get_sessions_for_reporting(
        company_id=company_id,
        user_id=target_user_uuid,
        start_utc=start_utc,
        end_utc=end_utc,
        status=status,
        limit=limit,
        offset=offset,
    )

    total = repo.count_sessions_for_reporting(
        company_id=company_id,
        user_id=target_user_uuid,
        start_utc=start_utc,
        end_utc=end_utc,
        status=status,
    )

    session_responses = [
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
    ]

    return SessionsListResponse(
        sessions=session_responses,
        total=total,
        limit=limit,
        offset=offset,
    )


# ============================================
# WP-11-06 Step 2: User Summary Reporting Endpoint
# ============================================

@router_v1.get("/reports/user-summary", response_model=UserSummaryResponse)
async def get_user_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    company_id: str = Depends(get_current_company_id),
    current_user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """GET /api/v1/attendance/reports/user-summary — Per-user summary (WP-11-06 Step 2)

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
    # --- Feature Gate (WP-C1-06) ---
    _require_attendance_feature(company_id, db)
    # --- 確認 current_user_id 存在 ---
    if not current_user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    # --- 驗證 datetime 為 timezone-aware ---
    if start_date is not None and start_date.tzinfo is None:
        raise HTTPException(
            status_code=422,
            detail="start_date must be timezone-aware (naive datetime rejected)"
        )
    if end_date is not None and end_date.tzinfo is None:
        raise HTTPException(
            status_code=422,
            detail="end_date must be timezone-aware (naive datetime rejected)"
        )

    # --- User scope：只允許查自己 ---
    from uuid import UUID
    try:
        target_user_uuid = UUID(current_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid User ID format")

    # --- 正規化 datetime 至 UTC ---
    start_utc = _normalize_to_utc(start_date)
    end_utc = _normalize_to_utc(end_date)

    # --- 查詢原始 sessions ---
    repo = get_reporting_repository(db)
    sessions = repo.get_user_summary_sessions(
        company_id=company_id,
        user_id=target_user_uuid,
        start_utc=start_utc,
        end_utc=end_utc,
    )

    # --- 應用層聚合 ---
    total_sessions = len(sessions)
    closed_sessions = sum(1 for s in sessions if s.status == "closed")
    open_sessions = sum(1 for s in sessions if s.status == "open")

    # canonical duration — duration_minutes IS NULL for open sessions
    total_work_minutes = sum(s.duration_minutes or 0 for s in sessions)

    # average: None when no closed sessions (avoid division by zero)
    average_session_minutes = (
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

    return UserSummaryResponse(
        user_id=str(target_user_uuid),
        total_sessions=total_sessions,
        closed_sessions=closed_sessions,
        open_sessions=open_sessions,
        total_work_minutes=total_work_minutes,
        average_session_minutes=average_session_minutes,
        first_session_time=first_session_time,
        last_session_time=last_session_time,
    )


# ============================================
# WP-11-06 Step 3: Company Summary Reporting Endpoint
# ============================================

@router_v1.get("/reports/company-summary", response_model=CompanySummaryResponse)
async def get_company_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    company_id: str = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """GET /api/v1/attendance/reports/company-summary — Company-level summary (WP-11-06 Step 3)

    Returns attendance summary statistics for the entire company (all users).

    Query rules:
    - 過濾僅使用 punch_in_time（禁止 punch_out_time）
    - start_date / end_date 必須為 timezone-aware datetime（naive 回傳 422）
    - total_work_minutes 讀取 canonical 欄位 duration_minutes
    - 聚合在 Python 應用層執行（非 SQL 端）
    - total_users_with_sessions 使用 Python set() 去重（非 SQL COUNT DISTINCT）

    Tenant isolation:
    - 所有查詢強制 WHERE company_id = ?（從 Header 取得）
    - 查詢全公司所有用戶，不過濾 user_id
    """
    # --- Feature Gate (WP-C1-06) ---
    _require_attendance_feature(company_id, db)
    # --- 驗證 datetime 為 timezone-aware ---
    if start_date is not None and start_date.tzinfo is None:
        raise HTTPException(
            status_code=422,
            detail="start_date must be timezone-aware (naive datetime rejected)"
        )
    if end_date is not None and end_date.tzinfo is None:
        raise HTTPException(
            status_code=422,
            detail="end_date must be timezone-aware (naive datetime rejected)"
        )

    # --- 正規化 datetime 至 UTC ---
    start_utc = _normalize_to_utc(start_date)
    end_utc = _normalize_to_utc(end_date)

    # --- 查詢原始 sessions（全公司，不過濾 user_id）---
    repo = get_reporting_repository(db)
    sessions = repo.get_company_summary_sessions(
        company_id=company_id,
        start_utc=start_utc,
        end_utc=end_utc,
    )

    # --- 應用層聚合 ---
    total_sessions = len(sessions)
    closed_sessions = sum(1 for s in sessions if s.status == "closed")
    open_sessions = sum(1 for s in sessions if s.status == "open")

    # 用戶去重（Python set，禁止 SQL COUNT DISTINCT）
    total_users_with_sessions = len(set(s.user_id for s in sessions))

    # canonical duration — duration_minutes IS NULL for open sessions
    total_work_minutes = sum(s.duration_minutes or 0 for s in sessions)

    # average per session: None when no closed sessions
    average_minutes_per_session = (
        total_work_minutes / closed_sessions
        if closed_sessions > 0 else None
    )

    # average per user: None when no users with sessions
    average_minutes_per_user = (
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

    return CompanySummaryResponse(
        company_id=company_id,
        total_users_with_sessions=total_users_with_sessions,
        total_sessions=total_sessions,
        open_sessions=open_sessions,
        closed_sessions=closed_sessions,
        total_work_minutes=total_work_minutes,
        average_minutes_per_session=average_minutes_per_session,
        average_minutes_per_user=average_minutes_per_user,
        first_session_time=first_session_time,
        last_session_time=last_session_time,
    )
