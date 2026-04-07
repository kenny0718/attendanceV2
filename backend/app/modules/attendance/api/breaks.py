"""Attendance API — Breaks 層 (WP-11-11.5, WP-11-13)

Breaks endpoints:
- POST /api/v1/attendance/break-out
- POST /api/v1/attendance/break-in
- GET /api/v1/attendance/break-punches
- PATCH /api/v1/attendance/punch/{punch_id}/note

WP-11-11.5: Break Out/In API (Blocker Fix)
WP-11-13: Location Policy Integration
WP-C1-07: JWT Actor Migration
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.scope import Actor
from app.core.dependencies import get_actor_with_company
from app.core.database import get_db
from app.modules.attendance.repo import get_attendance_session_repository
from app.modules.attendance.schemas import (
    BreakOutRequest,
    BreakInRequest,
    BreakOutResponse,
    BreakInResponse,
)
from app.modules.attendance.api.helpers import _require_attendance_feature
from app.modules.attendance.api.reporting_helpers import get_taipei_today_boundary

logger = logging.getLogger(__name__)

# Breaks router
router_v1 = APIRouter(prefix="/api/v1/attendance", tags=["attendance-v1"])


# ============================================
# WP-11-11.5: Break Out/In API (Blocker Fix)
# ============================================

@router_v1.post("/break-out", response_model=BreakOutResponse, status_code=201)
async def break_out(
    request: BreakOutRequest,
    actor: Actor = Depends(get_actor_with_company),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """Break out (外出打卡) - WP-11-11.5 Blocker Fix, WP-11-13 Location Policy, WP-C1-07: JWT Actor
    
    允許連續外出打卡，不需要先返回
    
    WP-11-13: 加入 location policy 後端 authoritative enforcement
    """
    company_id = actor.active_company_id
    user_id = str(actor.user_id)
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
    actor: Actor = Depends(get_actor_with_company),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """Break in (返回打卡) - WP-11-11.5 Blocker Fix, WP-C1-07: JWT Actor"""
    company_id = actor.active_company_id
    user_id = str(actor.user_id)
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
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    """Get today's break punches (今日外出/返回記錄) - WP-11-11.5 Blocker Fix, WP-C1-07: JWT Actor
    
    Returns all break_start and break_end punches for today
    """
    company_id = actor.active_company_id
    user_id = str(actor.user_id)
    # --- Feature Gate (WP-C1-06) ---
    _require_attendance_feature(company_id, db)
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    user_uuid = UUID(user_id)
    
    boundary = get_taipei_today_boundary()

    # Query break punches
    from app.modules.attendance.models import AttendancePunch

    punches = (
        db.query(AttendancePunch)
        .filter(
            and_(
                AttendancePunch.company_id == company_id,
                AttendancePunch.user_id == user_uuid,
                AttendancePunch.punch_type.in_(['break_start', 'break_end']),
                AttendancePunch.punch_time >= boundary.start_utc,
                AttendancePunch.punch_time < boundary.end_utc
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
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    """Update punch note (更新打卡備註) - WP-11-11.5, WP-C1-07: JWT Actor"""
    company_id = actor.active_company_id
    user_id = str(actor.user_id)
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
