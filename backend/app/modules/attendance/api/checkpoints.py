"""Attendance API — OUT Checkpoint 層 (WP-C1-11)

OUT Checkpoint endpoints:
- POST /api/v1/attendance/out-checkpoint
- GET /api/v1/attendance/out-checkpoints

WP-C1-11: OUT Checkpoint API
WP-C1-07: JWT Actor Migration
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
from app.modules.attendance.checkpoint_repo import get_out_checkpoint_repository
from app.modules.attendance.repo import get_attendance_session_repository
from app.modules.attendance.schemas import (
    OutCheckpointRequest,
    OutCheckpointResponse,
    OutCheckpointListResponse,
    OutCheckpointListItem,
    GPSData,
)
from app.modules.attendance.api.helpers import _require_attendance_feature
from app.modules.attendance.gps_utils import is_within_distance

logger = logging.getLogger(__name__)

# Checkpoint router
router_v1 = APIRouter(prefix="/api/v1/attendance", tags=["attendance-v1"])


# ============================================
# WP-C1-11: OUT Checkpoint API
# ============================================

@router_v1.post("/out-checkpoint", response_model=OutCheckpointResponse, status_code=201)
async def create_out_checkpoint(
    request: OutCheckpointRequest,
    actor: Actor = Depends(get_actor_with_company),
    http_request: Request = None,
    db: Session = Depends(get_db)
):
    """OUT Checkpoint (外出打卡) - WP-C1-11"""
    company_id = actor.active_company_id
    user_id = str(actor.user_id)

    _require_attendance_feature(company_id, db)

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    # GPS validation: mobile device must provide GPS
    if request.device_type == "mobile" and not request.gps:
        raise HTTPException(
            status_code=422,
            detail={"error": "GPS is required for mobile devices", "error_code": "GPS_REQUIRED"}
        )

    user_uuid = UUID(user_id)
    punch_time = datetime.now(timezone.utc)
    ip_address = http_request.client.host if http_request and http_request.client else None

    repo = get_out_checkpoint_repository(db)
    session_repo = get_attendance_session_repository(db)

    open_session = session_repo.get_open_session(company_id, user_uuid)
    session_id = open_session.id if open_session else None

    # De-dup: 30s + 50m
    recent = repo.get_recent_checkpoint(company_id, user_uuid, within_seconds=30)
    if recent:
        within_distance = True
        if request.gps and recent.gps_lat is not None and recent.gps_lng is not None:
            within_distance = is_within_distance(
                (request.gps.latitude, request.gps.longitude),
                (float(recent.gps_lat), float(recent.gps_lng)),
                max_distance_m=50.0
            )
        if within_distance:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "Duplicate checkpoint detected",
                    "error_code": "DUPLICATE_CHECKPOINT",
                    "last_checkpoint_time": recent.punch_time.isoformat()
                }
            )

    gps = request.gps
    checkpoint = repo.create_checkpoint(
        company_id=company_id,
        user_id=user_uuid,
        device_type=request.device_type,
        punch_time=punch_time,
        session_id=session_id,
        gps_lat=gps.latitude if gps else None,
        gps_lng=gps.longitude if gps else None,
        gps_accuracy_m=gps.accuracy if gps else None,
        gps_captured_at=gps.captured_at if gps else None,
        gps_provider=gps.provider if gps else None,
        client_timezone=request.client_timezone,
        ip_address=ip_address,
        notes=request.notes
    )

    gps_response = None
    if checkpoint.gps_lat is not None and checkpoint.gps_lng is not None:
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
async def list_out_checkpoints(
    limit: int = 50,
    offset: int = 0,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    """List OUT Checkpoints - WP-C1-11"""
    company_id = actor.active_company_id
    user_id = str(actor.user_id)

    _require_attendance_feature(company_id, db)

    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    user_uuid = UUID(user_id)
    repo = get_out_checkpoint_repository(db)

    checkpoints = repo.get_checkpoints(company_id, user_uuid, limit=limit, offset=offset)
    total = repo.count_checkpoints(company_id, user_uuid)

    items = []
    for cp in checkpoints:
        gps_data = None
        if cp.gps_lat is not None and cp.gps_lng is not None:
            gps_data = GPSData(
                latitude=float(cp.gps_lat),
                longitude=float(cp.gps_lng),
                accuracy=float(cp.gps_accuracy_m) if cp.gps_accuracy_m else None,
                captured_at=cp.gps_captured_at,
                provider=cp.gps_provider
            )
        items.append(OutCheckpointListItem(
            checkpoint_id=cp.id,
            punch_time=cp.punch_time,
            device_type=cp.device_type,
            gps=gps_data,
            notes=cp.notes
        ))

    return OutCheckpointListResponse(
        checkpoints=items,
        total=total,
        limit=limit,
        offset=offset
    )
