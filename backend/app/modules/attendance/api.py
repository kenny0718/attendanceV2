"""Attendance API 路由"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.attendance.service import get_attendance_service

logger = logging.getLogger(__name__)

# 建立路由
router = APIRouter(prefix="/api/attendance", tags=["attendance"])


class MockCreateResponse(BaseModel):
    """Mock 建立考勤記錄回應"""
    attendance_record_id: str = Field(..., description="考勤記錄 ID")


class ApproveRequest(BaseModel):
    """核准考勤請求"""
    company_id: str = Field(..., description="公司 ID（必填，多租戶隔離用）")
    employee_id: str = Field(..., description="員工 ID")
    approved_by: str | None = Field(None, description="核准人 ID（選填）")


class ApproveResponse(BaseModel):
    """核准考勤回應"""
    ok: bool = Field(..., description="操作是否成功")
    payload: Dict[str, Any] = Field(..., description="發出的事件 payload")


@router.post("/mock-create", response_model=MockCreateResponse)
async def mock_create_attendance():
    """建立假的考勤記錄（用於測試）
    
    Returns:
        包含 attendance_record_id 的回應
    """
    service = get_attendance_service()
    attendance_record_id = service.mock_create_attendance()
    
    return MockCreateResponse(attendance_record_id=attendance_record_id)


@router.post("/{attendance_record_id}/approve", response_model=ApproveResponse)
async def approve_attendance(
    attendance_record_id: str,
    request: ApproveRequest
):
    """核准考勤記錄
    
    此端點會：
    1. 組裝 payload
    2. 發出 attendance.approved 事件
    3. 回傳操作結果
    
    Args:
        attendance_record_id: 考勤記錄 ID（路徑參數）
        request: 核准請求（包含 company_id, employee_id, approved_by）
    
    Returns:
        操作結果與發出的 payload
    """
    service = get_attendance_service()
    
    result = service.approve_attendance(
        attendance_record_id=attendance_record_id,
        company_id=request.company_id,
        employee_id=request.employee_id,
        approved_by=request.approved_by
    )
    
    return ApproveResponse(**result)
