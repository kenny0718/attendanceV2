"""Leave Request System - API Layer

WP-11-08 Phase 2B: Leave Request API Layer

Endpoints:
  POST   /api/v1/leave/requests              - 建立請假申請
  GET    /api/v1/leave/my-requests           - 取得自己的請假列表
  GET    /api/v1/leave/pending               - 取得待審批列表
  POST   /api/v1/leave/requests/{id}/approve - 審批通過
  POST   /api/v1/leave/requests/{id}/reject  - 審批拒絕

API layer only: 不含業務規則，所有邏輯交給 service 層。
"""

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.tenant_context import get_current_company_id, get_current_user_id
from app.modules.leave.service import get_leave_service
from app.modules.leave.schemas import (
    LeaveRequestCreate,
    LeaveRequestResponse,
    LeaveApprovalAction,
    MyLeaveRequestListResponse,
    PendingApprovalListResponse,
)

logger = logging.getLogger(__name__)

router_v1 = APIRouter(prefix="/api/v1/leave", tags=["leave-v1"])


# ============================================
# POST /api/v1/leave/requests
# ============================================

@router_v1.post("/requests", response_model=LeaveRequestResponse, status_code=201)
async def create_leave_request(
    payload: LeaveRequestCreate,
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """建立請假申請

    - leave_type_id 必須屬於同 company 且 is_active
    - start_date <= end_date (schema validator 保證)
    - 依 total_days 查找 approval policy (Strict Policy Mode)
    - 無匹配 policy -> 422
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid User ID format")

    service = get_leave_service(db)
    return service.submit_leave_request(
        company_id=company_id,
        user_id=user_uuid,
        payload=payload,
    )


# ============================================
# GET /api/v1/leave/my-requests
# ============================================

@router_v1.get("/my-requests", response_model=MyLeaveRequestListResponse)
async def get_my_leave_requests(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """取得目前登入使用者自己的請假列表

    Query parameters:
    - status: 可選過濾 (pending / approved / rejected / cancelled)
    - limit: 每頁筆數 (1-100, 預設 50)
    - offset: 偏移量 (預設 0)
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid User ID format")

    # 驗證 status 值
    valid_statuses = {'pending', 'approved', 'rejected', 'cancelled'}
    if status and status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(sorted(valid_statuses))}"
        )

    service = get_leave_service(db)
    return service.get_my_leave_requests(
        company_id=company_id,
        user_id=user_uuid,
        limit=limit,
        offset=offset,
        status_filter=status,
    )


# ============================================
# GET /api/v1/leave/pending
# ============================================

@router_v1.get("/pending", response_model=PendingApprovalListResponse)
async def get_pending_leave_requests(
    approver_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """取得待審批請假列表

    Query parameters:
    - approver_id: 可選，過濾指派給特定審批人的 pending requests
    - limit: 每頁筆數 (1-100, 預設 50)
    - offset: 偏移量 (預設 0)

    Note: 目前無完整 RBAC，approver_id 為 optional filter。
    後續 JWT migration 後可加入 manager 身份驗證。
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

    # 解析 approver_id
    approver_uuid: Optional[UUID] = None
    if approver_id:
        try:
            approver_uuid = UUID(approver_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid approver_id format")

    service = get_leave_service(db)
    return service.get_pending_leave_requests(
        company_id=company_id,
        approver_id=approver_uuid,
        limit=limit,
        offset=offset,
    )


# ============================================
# POST /api/v1/leave/requests/{request_id}/approve
# ============================================

@router_v1.post("/requests/{request_id}/approve", response_model=LeaveRequestResponse)
async def approve_leave_request(
    request_id: str,
    payload: LeaveApprovalAction,
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """審批通過請假申請

    - request 必須存在且屬於同 company
    - request 必須為 pending 狀態
    - 重複審批已結案 request -> 409
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    try:
        request_uuid = UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request_id format")

    try:
        actor_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid User ID format")

    service = get_leave_service(db)
    return service.approve_leave_request(
        company_id=company_id,
        leave_request_id=request_uuid,
        actor_user_id=actor_uuid,
        payload=payload,
    )


# ============================================
# POST /api/v1/leave/requests/{request_id}/reject
# ============================================

@router_v1.post("/requests/{request_id}/reject", response_model=LeaveRequestResponse)
async def reject_leave_request(
    request_id: str,
    payload: LeaveApprovalAction,
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """審批拒絕請假申請

    - request 必須存在且屬於同 company
    - request 必須為 pending 狀態
    - 重複拒絕已結案 request -> 409
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    try:
        request_uuid = UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request_id format")

    try:
        actor_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid User ID format")

    service = get_leave_service(db)
    return service.reject_leave_request(
        company_id=company_id,
        leave_request_id=request_uuid,
        actor_user_id=actor_uuid,
        payload=payload,
    )
