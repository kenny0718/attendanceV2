"""Attendance API — Legacy 相容層 (Phase 4)

舊版 endpoint 保持兼容：
- POST /api/attendance/mock-create
- POST /api/attendance/{attendance_record_id}/approve

WP-C1-10: JWT Actor migration 完成
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.modules.attendance.service import get_attendance_service
from app.core.scope import Actor
from app.core.dependencies import get_actor_with_company
from app.core.database import get_db

logger = logging.getLogger(__name__)

# 建立路由 - 保持舊的 prefix 以兼容舊 API
router = APIRouter(prefix="/api/attendance", tags=["attendance"])


# ============================================
# Legacy Models (Phase 4)
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


# ============================================
# Legacy Endpoints (Phase 4)
# ============================================

@router.post("/mock-create", response_model=MockCreateResponse)
async def mock_create_attendance(
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    """建立考勤記錄（Phase 4: 真正寫 DB）WP-C1-10: JWT Actor migration"""
    service = get_attendance_service(db)
    attendance_record_id = service.mock_create_attendance(
        company_id=actor.active_company_id
    )
    
    return MockCreateResponse(attendance_record_id=attendance_record_id)


@router.post("/{attendance_record_id}/approve", response_model=ApproveResponse)
async def approve_attendance(
    attendance_record_id: str,
    request: ApproveRequest,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    """核准考勤記錄（Phase 4: 真正寫 DB）WP-C1-10: JWT Actor migration"""
    service = get_attendance_service(db)
    
    result = service.approve_attendance(
        attendance_record_id=attendance_record_id,
        company_id=actor.active_company_id,
        employee_id=request.employee_id,
        approved_by=request.approved_by or str(actor.user_id)
    )
    
    return ApproveResponse(**result)
