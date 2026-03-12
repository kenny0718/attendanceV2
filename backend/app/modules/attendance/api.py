"""Attendance API WP-C1-07 JWT + WP-C1-09 OUT Checkpoint"""
import logging
from datetime import datetime, timezone, date, timedelta
from math import radians, sin, cos, sqrt, atan2
from typing import Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.modules.attendance.service import get_attendance_service
from app.core.dependencies import get_actor_with_company
from app.core.scope import Actor
from zoneinfo import ZoneInfo
_TZ_TAIPEI = ZoneInfo("Asia/Taipei")
from app.core.database import get_db
from app.modules.attendance.repo import (
    get_attendance_session_repository,
    get_out_checkpoint_repository,
)
from app.modules.attendance.schemas import (
    BreakOutRequest, BreakInRequest, BreakOutResponse, BreakInResponse,
    PunchInRequest, PunchInResponse, PunchOutRequest, PunchOutResponse,
    CurrentStatusResponse, AttendanceHistoryResponse,
    SessionResponse, PolicyEvaluationResponse, OutCheckpointRequest,
)
from app.modules.attendance.policy_engine import AttendancePolicyEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/attendance", tags=["attendance"])
router_v1 = APIRouter(prefix="/api/v1/attendance", tags=["attendance-v1"])


class MockCreateResponse(BaseModel):
    attendance_record_id: str = Field(...)

class ApproveRequest(BaseModel):
    employee_id: str = Field(...)
    approved_by: str | None = Field(None)

class ApproveResponse(BaseModel):
    ok: bool = Field(...)
    payload: Dict[str, Any] = Field(...)


@router.post("/mock-create", response_model=MockCreateResponse)
async def mock_create_attendance(
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    service = get_attendance_service(db)
    rid = service.mock_create_attendance(company_id=actor.active_company_id)
    return MockCreateResponse(attendance_record_id=rid)


@router.post("/{attendance_record_id}/approve", response_model=ApproveResponse)
async def approve_attendance(
    attendance_record_id: str,
    request: ApproveRequest,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    service = get_attendance_service(db)
    result = service.approve_attendance(
        attendance_record_id=attendance_record_id,
        company_id=actor.active_company_id,
        employee_id=request.employee_id,
        approved_by=request.approved_by or str(actor.user_id)
    )
    return ApproveResponse(**result)


@router_v1.post("/punch-in", response_model=PunchInResponse, status_code=201)
async def punch_in(
    request: PunchInRequest,
    actor: Actor = Depends(get_actor_with_company),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    repo = get_attendance_session_repository(db)
    if not actor.user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    company_id = actor.active_company_id
    user_uuid = actor.user_id
    existing = repo.get_open_session(company_id, user_uuid)
    if existing:
        raise HTTPException(status_code=409, detail={
            "error": "Already have an open session",
            "error_code": "ALREADY_OPEN_SESSION",
            "open_session_id": str(existing.id),
            "punch_in_time": existing.punch_in_time.isoformat()
        })
    if request.punch_time:
        if request.punch_time.tzinfo:
            punch_in_time = request.punch_time.astimezone(timezone.utc)
        else:
            punch_in_time = request.punch_time.replace(tzinfo=_TZ_TAIPEI).astimezone(timezone.utc)
    else:
        punch_in_time = datetime.now(timezone.utc)
    session = repo.create_session(company_id=company_id, user_id=user_uuid,
        punch_in_time=punch_in_time, notes=request.notes)
    ip = http_request.client.host if http_request and http_request.client else None
    repo.create_punch(session_id=session.id, company_id=company_id, user_id=user_uuid,
        punch_type="in", punch_time=punch_in_time, ip_address=ip,
        location_lat=request.location.latitude if request.location else None,
        location_lng=request.location.longitude if request.location else None,
        notes=request.notes)
    return PunchInResponse(session_id=session.id, user_id=session.user_id,
        company_id=session.company_id, punch_in_time=session.punch_in_time,
        punch_out_time=session.punch_out_time, duration_minutes=session.duration_minutes,
        status=session.status)


@router_v1.post("/punch-out", response_model=PunchOutResponse)
async def punch_out(
    request: PunchOutRequest,
    actor: Actor = Depends(get_actor_with_company),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    repo = get_attendance_session_repository(db)
    if not actor.user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    user_uuid = actor.user_id
    company_id = actor.active_company_id
    session = repo.get_open_session(company_id, user_uuid)
    if not session:
        raise HTTPException(status_code=404, detail={"error": "No open session found", "error_code": "NO_OPEN_SESSION"})
    if request.punch_time:
        if request.punch_time.tzinfo:
            punch_out_time = request.punch_time.astimezone(timezone.utc)
        else:
            punch_out_time = request.punch_time.replace(tzinfo=_TZ_TAIPEI).astimezone(timezone.utc)
    else:
        punch_out_time = datetime.now(timezone.utc)
    ip = http_request.client.host if http_request and http_request.client else None
    repo.create_punch(session_id=session.id, company_id=company_id, user_id=user_uuid,
        punch_type="out", punch_time=punch_out_time, ip_address=ip,
        location_lat=request.location.latitude if request.location else None,
        location_lng=request.location.longitude if request.location else None,
        notes=request.notes)
    duration_minutes = int((punch_out_time - session.punch_in_time).total_seconds() / 60)
    policy = repo.get_user_policy(company_id, user_uuid)
    session.punch_out_time = punch_out_time
    session.duration_minutes = duration_minutes
    session.status = "closed"
    evaluation = AttendancePolicyEngine().evaluate(session, policy)
    session = repo.close_session(session=session, punch_out_time=punch_out_time,
        duration_minutes=duration_minutes, policy_id=policy.id if policy else None)
    pe = PolicyEvaluationResponse(
        is_late=evaluation.is_late, late_minutes=evaluation.late_minutes,
        is_early_leave=evaluation.is_early_leave, early_leave_minutes=evaluation.early_leave_minutes,
        is_overtime=evaluation.is_overtime, overtime_minutes=evaluation.overtime_minutes,
        work_minutes=evaluation.work_minutes, policy_name=evaluation.policy_name)
    return PunchOutResponse(session_id=session.id, user_id=session.user_id,
        company_id=session.company_id, punch_in_time=session.punch_in_time,
        punch_out_time=session.punch_out_time, duration_minutes=session.duration_minutes,
        status=session.status, policy_evaluation=pe)


@router_v1.get("/current-status", response_model=CurrentStatusResponse)
async def get_current_status(
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    repo = get_attendance_session_repository(db)
    if not actor.user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    user_uuid = actor.user_id
    company_id = actor.active_company_id
    session = repo.get_open_session(company_id, user_uuid)
    if session:
        elapsed_minutes = int((datetime.now(timezone.utc) - session.punch_in_time).total_seconds() / 60)
        sr = SessionResponse(session_id=session.id, user_id=session.user_id,
            company_id=session.company_id, punch_in_time=session.punch_in_time,
            punch_out_time=session.punch_out_time, duration_minutes=session.duration_minutes,
            status=session.status)
        last_bp = repo.get_last_break_punch(session.id)
        is_on_break = bool(last_bp and last_bp.punch_type == "break_start")
        return CurrentStatusResponse(has_open_session=True, session=sr,
            elapsed_minutes=elapsed_minutes, is_on_break=is_on_break)
    return CurrentStatusResponse(has_open_session=False, session=None, elapsed_minutes=None)


@router_v1.get("/history", response_model=AttendanceHistoryResponse)
async def get_attendance_history(
    limit: int = 50, offset: int = 0, status: Optional[str] = None,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    if not actor.user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    repo = get_attendance_session_repository(db)
    user_uuid = actor.user_id
    company_id = actor.active_company_id
    sessions = repo.get_sessions(company_id=company_id, user_id=user_uuid,
        limit=limit, offset=offset, status=status)
    total = repo.count_sessions(company_id=company_id, user_id=user_uuid, status=status)
    sr_list = [SessionResponse(session_id=s.id, user_id=s.user_id, company_id=s.company_id,
        punch_in_time=s.punch_in_time, punch_out_time=s.punch_out_time,
        duration_minutes=s.duration_minutes, status=s.status) for s in sessions]
    return AttendanceHistoryResponse(sessions=sr_list, total=total, limit=limit, offset=offset)


@router_v1.post("/break-out", response_model=BreakOutResponse, status_code=201)
async def break_out(
    request: BreakOutRequest,
    actor: Actor = Depends(get_actor_with_company),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """Break out - WP-11-13 Location Policy"""
    repo = get_attendance_session_repository(db)
    if not actor.user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    user_uuid = actor.user_id
    company_id = actor.active_company_id
    session = repo.get_open_session(company_id, user_uuid)
    if not session:
        raise HTTPException(status_code=404, detail={"error": "No open session found", "error_code": "NO_OPEN_SESSION"})
    matched_location_id = None
    if request.location:
        from app.modules.attendance.location_policy_service import get_location_policy_service
        policy_service = get_location_policy_service(db)
        policy_check = policy_service.check_location_policy(
            company_id=company_id, latitude=request.location.latitude,
            longitude=request.location.longitude)
        if not policy_check.allowed:
            raise HTTPException(status_code=403, detail={
                "error": policy_check.reason, "error_code": "LOCATION_POLICY_VIOLATION",
                "nearest_location": policy_check.nearest_location})
        if policy_check.matched_location:
            matched_location_id = UUID(policy_check.matched_location["id"])
    punch_time = request.punch_time or datetime.now(timezone.utc)
    ip = http_request.client.host if http_request and http_request.client else None
    punch = repo.create_punch(session_id=session.id, company_id=company_id, user_id=user_uuid,
        punch_type="break_start", punch_time=punch_time, ip_address=ip,
        location_lat=request.location.latitude if request.location else None,
        location_lng=request.location.longitude if request.location else None,
        notes=request.notes, location_id=matched_location_id)
    return BreakOutResponse(punch_id=punch.id, session_id=session.id,
        punch_time=punch.punch_time, message="外出打卡成功")


@router_v1.post("/break-in", response_model=BreakInResponse, status_code=201)
async def break_in(
    request: BreakInRequest,
    actor: Actor = Depends(get_actor_with_company),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    repo = get_attendance_session_repository(db)
    if not actor.user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    user_uuid = actor.user_id
    company_id = actor.active_company_id
    session = repo.get_open_session(company_id, user_uuid)
    if not session:
        raise HTTPException(status_code=404, detail={"error": "No open session found", "error_code": "NO_OPEN_SESSION"})
    punch_time = request.punch_time or datetime.now(timezone.utc)
    ip = http_request.client.host if http_request and http_request.client else None
    punch = repo.create_punch(session_id=session.id, company_id=company_id, user_id=user_uuid,
        punch_type="break_end", punch_time=punch_time, ip_address=ip,
        location_lat=request.location.latitude if request.location else None,
        location_lng=request.location.longitude if request.location else None,
        notes=request.notes)
    return BreakInResponse(punch_id=punch.id, session_id=session.id,
        punch_time=punch.punch_time, message="返回打卡成功")


@router_v1.get("/break-punches")
async def get_break_punches(
    limit: int = 50,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    if not actor.user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    user_uuid = actor.user_id
    company_id = actor.active_company_id
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_of_day = start_of_day + timedelta(days=1)
    from app.modules.attendance.models import AttendancePunch
    from sqlalchemy import and_
    punches = (db.query(AttendancePunch).filter(and_(
        AttendancePunch.company_id == company_id,
        AttendancePunch.user_id == user_uuid,
        AttendancePunch.punch_type.in_(["break_start", "break_end"]),
        AttendancePunch.punch_time >= start_of_day,
        AttendancePunch.punch_time < end_of_day
    )).order_by(AttendancePunch.punch_time.desc()).limit(limit).all())
    punch_list = [{"punch_id": str(p.id), "punch_type": p.punch_type,
        "punch_time": p.punch_time.isoformat(), "notes": p.notes,
        "location_lat": float(p.location_lat) if p.location_lat else None,
        "location_lng": float(p.location_lng) if p.location_lng else None} for p in punches]
    return {"punches": punch_list, "total": len(punch_list)}


@router_v1.patch("/punch/{punch_id}/note")
async def update_punch_note(
    punch_id: str, request: dict,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    if not actor.user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    user_uuid = actor.user_id
    company_id = actor.active_company_id
    from app.modules.attendance.models import AttendancePunch
    punch = db.query(AttendancePunch).filter(
        AttendancePunch.id == UUID(punch_id),
        AttendancePunch.company_id == company_id,
        AttendancePunch.user_id == user_uuid
    ).first()
    if not punch:
        raise HTTPException(status_code=404, detail="Punch record not found")
    punch.notes = request.get("notes", "")
    db.commit()
    return {"success": True, "punch_id": str(punch.id), "notes": punch.notes}


# ============================================
# WP-C1-09: OUT Checkpoint API
# ============================================

@router_v1.post("/out-checkpoint", status_code=201)
async def create_out_checkpoint(
    request: OutCheckpointRequest,
    actor: Actor = Depends(get_actor_with_company),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """OUT checkpoint (WP-C1-09): mobile requires GPS, dedup 30s+50m"""
    if not actor.user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    user_uuid = actor.user_id
    company_id = actor.active_company_id

    if request.device_type == "mobile" and not request.gps:
        raise HTTPException(status_code=422, detail={
            "error": "請開啟定位後再外出打卡",
            "error_code": "GPS_REQUIRED"
        })

    ck_repo = get_out_checkpoint_repository(db)
    s_repo = get_attendance_session_repository(db)

    recent = ck_repo.get_recent_checkpoint(company_id=company_id, user_id=user_uuid, within_seconds=30)
    if recent:
        is_dup = True
        if request.gps and recent.gps_lat is not None and recent.gps_lng is not None:
            R = 6371000.0
            lat1, lat2 = radians(float(recent.gps_lat)), radians(request.gps.latitude)
            dlat = radians(request.gps.latitude - float(recent.gps_lat))
            dlng = radians(request.gps.longitude - float(recent.gps_lng))
            a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlng/2)**2
            dist_m = R * 2 * atan2(sqrt(a), sqrt(1-a))
            is_dup = dist_m <= 50.0
        if is_dup:
            raise HTTPException(status_code=409, detail={
                "error": "重複打卡，請稍後再試",
                "error_code": "DUPLICATE_CHECKPOINT",
                "last_checkpoint_time": recent.punch_time.isoformat()
            })

    open_session = s_repo.get_open_session(company_id, user_uuid)
    session_id = open_session.id if open_session else None
    punch_time = datetime.now(timezone.utc)
    ip = http_request.client.host if http_request and http_request.client else None
    ua = http_request.headers.get("user-agent") if http_request else None
    cp = ck_repo.create_checkpoint(
        company_id=company_id, user_id=user_uuid,
        device_type=request.device_type, punch_time=punch_time,
        session_id=session_id,
        gps_lat=request.gps.latitude if request.gps else None,
        gps_lng=request.gps.longitude if request.gps else None,
        gps_accuracy_m=request.gps.accuracy if request.gps else None,
        gps_captured_at=request.gps.captured_at if request.gps else None,
        gps_provider=request.gps.provider if request.gps else None,
        client_timezone=request.client_timezone,
        client_user_agent=ua, ip_address=ip, notes=request.notes)
    gps_out = None
    if cp.gps_lat is not None:
        gps_out = {"latitude": float(cp.gps_lat), "longitude": float(cp.gps_lng),
            "accuracy": float(cp.gps_accuracy_m) if cp.gps_accuracy_m else None,
            "captured_at": cp.gps_captured_at.isoformat() if cp.gps_captured_at else None,
            "provider": cp.gps_provider}
    return {"checkpoint_id": str(cp.id), "punch_time": cp.punch_time.isoformat(),
        "gps": gps_out, "message": "Checkpoint recorded successfully"}


@router_v1.get("/out-checkpoints")
async def list_out_checkpoints(
    limit: int = 50, offset: int = 0,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    if not actor.user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    user_uuid = actor.user_id
    company_id = actor.active_company_id
    ck_repo = get_out_checkpoint_repository(db)
    cps = ck_repo.get_checkpoints(company_id=company_id, user_id=user_uuid, limit=limit, offset=offset)
    total = ck_repo.count_checkpoints(company_id=company_id, user_id=user_uuid)
    items = []
    for cp in cps:
        gps_out = None
        if cp.gps_lat is not None:
            gps_out = {"latitude": float(cp.gps_lat), "longitude": float(cp.gps_lng),
                "accuracy": float(cp.gps_accuracy_m) if cp.gps_accuracy_m else None,
                "captured_at": cp.gps_captured_at.isoformat() if cp.gps_captured_at else None,
                "provider": cp.gps_provider}
        items.append({"checkpoint_id": str(cp.id), "punch_time": cp.punch_time.isoformat(),
            "device_type": cp.device_type, "gps": gps_out, "notes": cp.notes})
    return {"checkpoints": items, "total": total, "limit": limit, "offset": offset}
