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
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session

from app.core.scope import Actor
from app.core.dependencies import get_actor_with_company
from app.core.database import get_db
from app.modules.attendance import api as attendance_api
from app.modules.attendance.repo import get_attendance_session_repository
from app.modules.attendance.schemas import (
    BreakOutRequest,
    BreakInRequest,
    BreakOutResponse,
    BreakInResponse,
)
from app.modules.attendance.api.reporting_helpers import get_taipei_today_boundary

logger = logging.getLogger(__name__)
router_v1 = APIRouter(prefix="/api/v1/attendance", tags=["attendance-v1"])


@router_v1.post("/break-out", response_model=BreakOutResponse, status_code=201)
async def break_out(
    request: BreakOutRequest,
    actor: Actor = Depends(get_actor_with_company),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    company_id = actor.active_company_id
    user_id = str(actor.user_id)
    attendance_api._require_attendance_feature(company_id, db)
    repo = get_attendance_session_repository(db)

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    user_uuid = UUID(user_id)
    session = repo.get_open_session(company_id, user_uuid)
    if not session:
        raise HTTPException(status_code=404, detail={"error": "No open session found", "error_code": "NO_OPEN_SESSION"})

    matched_location_id = None
    if request.location:
        from app.modules.attendance.location_policy_service import get_location_policy_service

        policy_service = get_location_policy_service(db)
        policy_check = policy_service.check_location_policy(
            company_id=company_id,
            latitude=request.location.latitude,
            longitude=request.location.longitude,
        )
        if not policy_check.allowed:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": policy_check.reason,
                    "error_code": "LOCATION_POLICY_VIOLATION",
                    "nearest_location": policy_check.nearest_location,
                },
            )
        if policy_check.matched_location:
            matched_location_id = UUID(policy_check.matched_location["id"])

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
        location_id=matched_location_id,
    )

    return BreakOutResponse(
        punch_id=punch.id,
        session_id=session.id,
        punch_time=punch.punch_time,
        message="外出打卡成功",
    )


@router_v1.post("/break-in", response_model=BreakInResponse, status_code=201)
async def break_in(
    request: BreakInRequest,
    actor: Actor = Depends(get_actor_with_company),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    company_id = actor.active_company_id
    user_id = str(actor.user_id)
    attendance_api._require_attendance_feature(company_id, db)
    repo = get_attendance_session_repository(db)

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    user_uuid = UUID(user_id)
    session = repo.get_open_session(company_id, user_uuid)
    if not session:
        raise HTTPException(status_code=404, detail={"error": "No open session found", "error_code": "NO_OPEN_SESSION"})

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
        notes=request.notes,
    )

    return BreakInResponse(
        punch_id=punch.id,
        session_id=session.id,
        punch_time=punch.punch_time,
        message="返回打卡成功",
    )


@router_v1.get("/break-punches")
async def get_break_punches(
    limit: int = 50,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    company_id = actor.active_company_id
    user_id = str(actor.user_id)
    attendance_api._require_attendance_feature(company_id, db)
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    user_uuid = UUID(user_id)
    boundary = get_taipei_today_boundary()
    repo = get_attendance_session_repository(db)
    punches = repo.list_break_punches_for_user_in_range(
        company_id=company_id,
        user_id=user_uuid,
        start_utc=boundary.start_utc,
        end_utc=boundary.end_utc,
        limit=limit,
    )

    punch_list = [
        {
            "punch_id": str(punch.id),
            "punch_type": punch.punch_type,
            "punch_time": punch.punch_time.isoformat(),
            "notes": punch.notes,
            "location_lat": float(punch.location_lat) if punch.location_lat else None,
            "location_lng": float(punch.location_lng) if punch.location_lng else None,
        }
        for punch in punches
    ]
    return {"punches": punch_list, "total": len(punch_list)}


@router_v1.patch("/punch/{punch_id}/note")
async def update_punch_note(
    punch_id: str,
    request: dict,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    company_id = actor.active_company_id
    user_id = str(actor.user_id)
    attendance_api._require_attendance_feature(company_id, db)
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    user_uuid = UUID(user_id)
    punch_uuid = UUID(punch_id)
    repo = get_attendance_session_repository(db)
    notes = request.get('notes', '')
    punch = repo.update_punch_note(
        company_id=company_id,
        user_id=user_uuid,
        punch_id=punch_uuid,
        notes=notes,
    )
    if not punch:
        raise HTTPException(status_code=404, detail={"error": "Punch not found", "error_code": "PUNCH_NOT_FOUND"})

    return {
        "punch_id": str(punch.id),
        "notes": punch.notes,
        "message": "備註更新成功",
    }
