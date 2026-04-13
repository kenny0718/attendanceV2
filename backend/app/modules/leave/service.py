"""Leave Request System - Service Layer (業務規則層)

WP-11-08 Phase 2A: Leave Request Schema + Repo + Service Foundation

業務規則:
- submit_leave_request: 請假申請
- get_my_leave_requests: 取得自己的請假紀錄
- get_pending_leave_requests: 取得待審批列表
- approve_leave_request: 審批通過
- reject_leave_request: 審批拒絕
- cancel_leave_request: 取消請假

Tenant Isolation (P0): 所有操作強制帶 company_id
"""

import datetime as _dt
import logging
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.leave.models import LeaveRequest
from app.modules.leave.repo import (
    get_leave_approval_log_repository,
    get_leave_approval_policy_repository,
    get_leave_request_repository,
    get_leave_type_repository,
)
from app.modules.leave.schemas import (
    LeaveApprovalAction,
    LeaveCancelAction,
    LeaveRequestCreate,
    LeaveRequestResponse,
    MyLeaveRequestListItem,
    MyLeaveRequestListResponse,
    PendingApprovalListItem,
    PendingApprovalListResponse,
)

logger = logging.getLogger(__name__)


def _get_utc_now():
    """Return current UTC time (timezone-aware)"""
    return _dt.datetime.now(_dt.timezone.utc)


def _calculate_total_days(start_date: date, end_date: date, is_half_day: bool) -> float:
    """計算請假天數

    Phase 1 簡單計算：(end_date - start_date).days + 1
    is_half_day reserved for future half-day logic
    """
    delta = (end_date - start_date).days + 1
    if is_half_day and delta == 1:
        return 0.5
    return float(delta)


class LeaveService:
    """Leave Request 業務規則服務層"""

    def __init__(self, db: Session):
        self.db = db
        self.leave_type_repo = get_leave_type_repository(db)
        self.policy_repo = get_leave_approval_policy_repository(db)
        self.request_repo = get_leave_request_repository(db)
        self.log_repo = get_leave_approval_log_repository(db)

    def submit_leave_request(
        self,
        company_id: str,
        user_id: UUID,
        payload: LeaveRequestCreate,
    ) -> LeaveRequestResponse:
        """處理請假申請"""
        leave_type = self.leave_type_repo.get_leave_type_by_id(
            company_id=company_id,
            leave_type_id=payload.leave_type_id,
        )
        if not leave_type:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "error": "Leave type not found or not active for this company",
                    "error_code": "LEAVE_TYPE_NOT_FOUND",
                },
            )
        if not leave_type.is_active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "error": "Leave type is inactive",
                    "error_code": "LEAVE_TYPE_INACTIVE",
                },
            )

        total_days = _calculate_total_days(
            start_date=payload.start_date,
            end_date=payload.end_date,
            is_half_day=payload.is_half_day,
        )

        policy = self.policy_repo.find_matching_policy(
            company_id=company_id,
            leave_type_id=payload.leave_type_id,
            total_days=total_days,
        )
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "error": "No matching approval policy found for this leave request. Please contact your HR administrator.",
                    "error_code": "NO_MATCHING_POLICY",
                },
            )

        leave_request = self.request_repo.create_leave_request(
            company_id=company_id,
            user_id=user_id,
            leave_type_id=payload.leave_type_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            total_days=total_days,
            reason=payload.reason,
            is_half_day=payload.is_half_day,
            required_approval_level=policy.approval_level,
            approver_id=None,
        )

        logger.info(
            f"Leave request submitted: id={leave_request.id}, "
            f"company_id={company_id}, user_id={user_id}, "
            f"total_days={total_days}, approval_level={policy.approval_level}"
        )

        return LeaveRequestResponse.model_validate(leave_request)

    def get_my_leave_requests(
        self,
        company_id: str,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None,
    ) -> MyLeaveRequestListResponse:
        requests = self.request_repo.get_user_leave_requests(
            company_id=company_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
            status=status_filter,
        )
        total = self.request_repo.count_user_leave_requests(
            company_id=company_id,
            user_id=user_id,
            status=status_filter,
        )

        items = [MyLeaveRequestListItem.model_validate(r) for r in requests]

        return MyLeaveRequestListResponse(
            requests=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    def get_pending_leave_requests(
        self,
        company_id: str,
        approver_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PendingApprovalListResponse:
        requests = self.request_repo.get_pending_leave_requests(
            company_id=company_id,
            approver_id=approver_id,
            limit=limit,
            offset=offset,
        )
        total = self.request_repo.count_pending_leave_requests(
            company_id=company_id,
            approver_id=approver_id,
        )

        items = [PendingApprovalListItem.model_validate(r) for r in requests]

        return PendingApprovalListResponse(
            requests=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    def approve_leave_request(
        self,
        company_id: str,
        leave_request_id: UUID,
        actor_user_id: UUID,
        payload: LeaveApprovalAction,
    ) -> LeaveRequestResponse:
        leave_request = self.request_repo.get_leave_request_by_id(company_id, leave_request_id)
        if not leave_request:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "Leave request not found", "error_code": "LEAVE_REQUEST_NOT_FOUND"})
        if leave_request.status != "pending":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": "Leave request is not pending", "error_code": "LEAVE_REQUEST_NOT_PENDING"})

        updated = self.request_repo.update_leave_request_status(
            leave_request=leave_request,
            new_status="approved",
            approved_at=_get_utc_now(),
        )
        self.log_repo.create_log(
            company_id=company_id,
            leave_request_id=leave_request_id,
            actor_user_id=actor_user_id,
            action="approved",
            approval_level=leave_request.required_approval_level,
            comment=payload.comment,
        )
        return LeaveRequestResponse.model_validate(updated)

    def reject_leave_request(
        self,
        company_id: str,
        leave_request_id: UUID,
        actor_user_id: UUID,
        payload: LeaveApprovalAction,
    ) -> LeaveRequestResponse:
        leave_request = self.request_repo.get_leave_request_by_id(company_id, leave_request_id)
        if not leave_request:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "Leave request not found", "error_code": "LEAVE_REQUEST_NOT_FOUND"})
        if leave_request.status != "pending":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": "Leave request is not pending", "error_code": "LEAVE_REQUEST_NOT_PENDING"})

        updated = self.request_repo.update_leave_request_status(
            leave_request=leave_request,
            new_status="rejected",
            rejected_at=_get_utc_now(),
        )
        self.log_repo.create_log(
            company_id=company_id,
            leave_request_id=leave_request_id,
            actor_user_id=actor_user_id,
            action="rejected",
            approval_level=leave_request.required_approval_level,
            comment=payload.comment,
        )
        return LeaveRequestResponse.model_validate(updated)

    def cancel_leave_request(
        self,
        company_id: str,
        leave_request_id: UUID,
        actor_user_id: UUID,
        payload: LeaveCancelAction,
    ) -> LeaveRequestResponse:
        leave_request = self.request_repo.get_leave_request_by_id(company_id, leave_request_id)
        if not leave_request:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "Leave request not found", "error_code": "LEAVE_REQUEST_NOT_FOUND"})
        if leave_request.status != "pending":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": "Only pending leave request can be cancelled", "error_code": "LEAVE_REQUEST_NOT_CANCELLABLE"})
        if leave_request.user_id != actor_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "Only requester can cancel leave request", "error_code": "NOT_REQUEST_OWNER"})

        updated = self.request_repo.update_leave_request_status(
            leave_request=leave_request,
            new_status="cancelled",
            cancelled_at=_get_utc_now(),
        )
        self.log_repo.create_log(
            company_id=company_id,
            leave_request_id=leave_request_id,
            actor_user_id=actor_user_id,
            action="cancelled",
            approval_level=leave_request.required_approval_level,
            comment=payload.comment,
        )
        return LeaveRequestResponse.model_validate(updated)


def get_leave_service(db: Session) -> LeaveService:
    return LeaveService(db)
