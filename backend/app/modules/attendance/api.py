"""Attendance API 路由"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.modules.attendance.service import get_attendance_service
from app.core.tenant_context import get_current_company_id, get_current_user_id

logger = logging.getLogger(__name__)

# 建立路由
router = APIRouter(prefix="/api/attendance", tags=["attendance"])


class MockCreateResponse(BaseModel):
    """Mock 建立考勤記錄回應"""
    attendance_record_id: str = Field(..., description="考勤記錄 ID")


class ApproveRequest(BaseModel):
    """核准考勤請求
    
    注意：company_id 不在 request body 中，而是從 tenant context 注入
    """
    employee_id: str = Field(..., description="員工 ID")
    approved_by: str | None = Field(None, description="核准人 ID（選填）")


class ApproveResponse(BaseModel):
    """核准考勤回應"""
    ok: bool = Field(..., description="操作是否成功")
    payload: Dict[str, Any] = Field(..., description="發出的事件 payload")


@router.post("/mock-create", response_model=MockCreateResponse)
async def mock_create_attendance(
    current_company_id: str = Depends(get_current_company_id)
):
    """建立假的考勤記錄（用於測試）
    
    Tenant Isolation:
    - company_id 從 Header (X-Company-ID) 注入
    - Phase 2 將改為從 JWT token 解析
    
    Returns:
        包含 attendance_record_id 的回應
    """
    service = get_attendance_service()
    attendance_record_id = service.mock_create_attendance(
        company_id=current_company_id
    )
    
    return MockCreateResponse(attendance_record_id=attendance_record_id)


@router.post("/{attendance_record_id}/approve", response_model=ApproveResponse)
async def approve_attendance(
    attendance_record_id: str,
    request: ApproveRequest,
    current_company_id: str = Depends(get_current_company_id),
    current_user_id: str | None = Depends(get_current_user_id)
):
    """核准考勤記錄
    
    此端點會：
    1. 從 tenant context 注入 company_id（不信任 request body）
    2. 組裝 payload
    3. 發出 attendance.approved 事件
    4. 回傳操作結果
    
    Tenant Isolation (P0):
    - company_id 從 Header (X-Company-ID) 強制注入
    - 不接受 request body 的 company_id
    - Phase 2 將改為從 JWT token 解析
    
    Args:
        attendance_record_id: 考勤記錄 ID（路徑參數）
        request: 核准請求（包含 employee_id, approved_by）
        current_company_id: 當前公司 ID（從 tenant context 注入）
        current_user_id: 當前使用者 ID（從 tenant context 注入，選填）
    
    Returns:
        操作結果與發出的 payload
    """
    service = get_attendance_service()
    
    # company_id 由後端注入，不信任 request body
    result = service.approve_attendance(
        attendance_record_id=attendance_record_id,
        company_id=current_company_id,  # 強制使用注入的 company_id
        employee_id=request.employee_id,
        approved_by=request.approved_by or current_user_id
    )
    
    return ApproveResponse(**result)
