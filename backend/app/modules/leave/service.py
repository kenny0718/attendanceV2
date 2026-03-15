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

import logging
from datetime import date
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.modules.leave.repo import (
    get_leave_type_repository,
    get_leave_approval_policy_repository,
    get_leave_request_repository,
    get_leave_approval_log_repository,
)
from app.modules.leave.schemas import (
    LeaveRequestCreate,
    LeaveApprovalAction,
    LeaveCancelAction,
    LeaveRequestResponse,
    MyLeaveRequestListResponse,
    MyLeaveRequestListItem,
    PendingApprovalListResponse,
    PendingApprovalListItem,
)
from app.modules.leave.models import LeaveRequest
import datetime as _dt

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


# ============================================
# Leave Service
# ============================================

class LeaveService:
    """Leave Request 業務規則服務層"""

    def __init__(self, db: Session):
        self.db = db
        self.leave_type_repo = get_leave_type_repository(db)
        self.policy_repo = get_leave_approval_policy_repository(db)
        self.request_repo = get_leave_request_repository(db)
        self.log_repo = get_leave_approval_log_repository(db)

    # ------------------------------------------
    # Submit Leave Request
    # ------------------------------------------

    def submit_leave_request(
        self,
        company_id: str,
        user_id: UUID,
        payload: LeaveRequestCreate,
    ) -> LeaveRequestResponse:
        """處理請假申請

        業務規則:
        1. leave type 必須存在且屬於同 company，且 is_active=True
        2. date range 必須合法 (end_date >= start_date，由 schema validator 已保證)
        3. 根據 total_days 查找 approval policy (Strict Policy Mode)
        4. 若無匹配 policy，422 拒絕申請
        5. 建立 leave request，status=pending

        Tenant Isolation: company_id 強制帶入
        """
        # 1. 驗證 leave type
        leave_type = self.leave_type_repo.get_leave_type_by_id(
            company_id=company_id,
            leave_type_id=payload.leave_type_id,
        )
        if not leave_type:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Leave type not found or not active for this company",
                    "error_code": "LEAVE_TYPE_NOT_FOUND",
                }
            )
        if not leave_type.is_active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Leave type is inactive",
                    "error_code": "LEAVE_TYPE_INACTIVE",
                }
            )

        # 2. 計算 total_days
        total_days = _calculate_total_days(
            start_date=payload.start_date,
            end_date=payload.end_date,
            is_half_day=payload.is_half_day,
        )

        # 3. 查找 approval policy (Strict Policy Mode)
        policy = self.policy_repo.find_matching_policy(
            company_id=company_id,
            leave_type_id=payload.leave_type_id,
            total_days=total_days,
        )
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "No matching approval policy found for this leave request. "
                             "Please contact your HR administrator.",
                    "error_code": "NO_MATCHING_POLICY",
                }
            )

        # 4. 建立 leave request
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
            approver_id=None,  # approver resolved at submission in future phases
        )

        logger.info(
            f"Leave request submitted: id={leave_request.id}, "
            f"company_id={company_id}, user_id={user_id}, "
            f"total_days={total_days}, approval_level={policy.approval_level}"
        )

        return LeaveRequestResponse.model_validate(leave_request)

    # ------------------------------------------
    # Get My Leave Requests
    # ------------------------------------------

    def get_my_leave_requests(
        self,
        company_id: str,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None,
    ) -> MyLeaveRequestListResponse:
        """依 company_id + user_id 取得自己的請假紀錄

        Tenant Isolation: company_id 強制帶入
        """
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

        items = [
            MyLeaveRequestListItem.model_validate(r)
            for r in requests
        ]

        return MyLeaveRequestListResponse(
            requests=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    # ------------------------------------------
    # Get Pending Leave Requests (for approver)
    # ------------------------------------------

    def get_pending_leave_requests(
        self,
        company_id: str,
        approver_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PendingApprovalListResponse:
        """取得待審批列表

        Tenant Isolation: company_id 強制帶入
        approver_id: 可選，若提供只回傳指派給該審批人的 pending requests
        """
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

        items = [
            PendingApprovalListItem.model_validate(r)
            for r in requests
        ]

        return PendingApprovalListResponse(
            requests=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    # ------------------------------------------
    # Approve Leave Request
    # ------------------------------------------

    def approve_leave_request(
        self,
        company_id: str,
        leave_request_id: UUID,
        actor_user_id: UUID,
        payload: LeaveApprovalAction,
    ) -> LeaveRequestResponse:
        """審批通過請假申請

        業務規則:
        1. request 必須存在，且 company_id 一致
        2. request 狀態必須是 pending（不可重複審批已結案資料）
        3. 更新 request status -> approved
        4. 建立 approval log

        Tenant Isolation: company_id 強制帶入
        """
        leave_request = self._get_request_or_404(
            company_id=company_id,
            leave_request_id=leave_request_id,
        )

        # 狀態驗證：只有 pending 可以 approve
        if leave_request.status != 'pending':
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": f"Cannot approve a leave request with status '{leave_request.status}'. "
                             f"Only 'pending' requests can be approved.",
                    "error_code": "INVALID_STATUS_TRANSITION",
                    "current_status": leave_request.status,
                }
            )

        now = _get_utc_now()

        # 更新 request status
        updated = self.request_repo.update_leave_request_status(
            leave_request=leave_request,
            new_status='approved',
            approved_at=now,
        )

        # 建立 approval log
        self.log_repo.create_log(
            company_id=company_id,
            leave_request_id=leave_request_id,
            actor_user_id=actor_user_id,
            action='approved',
            approval_level=leave_request.required_approval_level,
            comment=payload.comment,
        )

        logger.info(
            f"Leave request approved: id={leave_request_id}, "
            f"actor_user_id={actor_user_id}, company_id={company_id}"
        )

        return LeaveRequestResponse.model_validate(updated)

    # ------------------------------------------
    # Reject Leave Request
    # ------------------------------------------

    def reject_leave_request(
        self,
        company_id: str,
        leave_request_id: UUID,
        actor_user_id: UUID,
        payload: LeaveApprovalAction,
    ) -> LeaveRequestResponse:
        """審批拒絕請假申請

        業務規則:
        1. request 必須存在，且 company_id 一致
        2. request 狀態必須是 pending
        3. 更新 request status -> rejected
        4. 建立 approval log

        Tenant Isolation: company_id 強制帶入
        """
        leave_request = self._get_request_or_404(
            company_id=company_id,
            leave_request_id=leave_request_id,
        )

        # 狀態驗證：只有 pending 可以 reject
        if leave_request.status != 'pending':
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": f"Cannot reject a leave request with status '{leave_request.status}'. "
                             f"Only 'pending' requests can be rejected.",
                    "error_code": "INVALID_STATUS_TRANSITION",
                    "current_status": leave_request.status,
                }
            )

        now = _get_utc_now()

        # 更新 request status
        updated = self.request_repo.update_leave_request_status(
            leave_request=leave_request,
            new_status='rejected',
            rejected_at=now,
        )

        # 建立 approval log
        self.log_repo.create_log(
            company_id=company_id,
            leave_request_id=leave_request_id,
            actor_user_id=actor_user_id,
            action='rejected',
            approval_level=leave_request.required_approval_level,
            comment=payload.comment,
        )

        logger.info(
            f"Leave request rejected: id={leave_request_id}, "
            f"actor_user_id={actor_user_id}, company_id={company_id}"
        )

        return LeaveRequestResponse.model_validate(updated)

    # ------------------------------------------
    # Cancel Leave Request
    # ------------------------------------------

    def cancel_leave_request(
        self,
        company_id: str,
        leave_request_id: UUID,
        actor_user_id: UUID,
        payload: LeaveCancelAction,
    ) -> LeaveRequestResponse:
        """取消請假申請

        業務規則:
        1. request 必須存在，且 company_id 一致
        2. 只有 pending 狀態可以取消
           (approved / rejected / cancelled 皆不可再取消)
        3. 更新 request status -> cancelled
        4. 建立 approval log

        Tenant Isolation: company_id 強制帶入
        """
        leave_request = self._get_request_or_404(
            company_id=company_id,
            leave_request_id=leave_request_id,
        )

        # 狀態驗證：只有 pending 可以 cancel
        if leave_request.status != 'pending':
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": f"Cannot cancel a leave request with status '{leave_request.status}'. "
                             f"Only 'pending' requests can be cancelled.",
                    "error_code": "INVALID_STATUS_TRANSITION",
                    "current_status": leave_request.status,
                }
            )

        now = _get_utc_now()

        # 更新 request status
        updated = self.request_repo.update_leave_request_status(
            leave_request=leave_request,
            new_status='cancelled',
            cancelled_at=now,
        )

        # 建立 approval log
        self.log_repo.create_log(
            company_id=company_id,
            leave_request_id=leave_request_id,
            actor_user_id=actor_user_id,
            action='cancelled',
            approval_level=leave_request.required_approval_level,
            comment=payload.comment,
        )

        logger.info(
            f"Leave request cancelled: id={leave_request_id}, "
            f"actor_user_id={actor_user_id}, company_id={company_id}"
        )

        return LeaveRequestResponse.model_validate(updated)

    # ------------------------------------------
    # Internal Helpers
    # ------------------------------------------

    def _get_request_or_404(
        self,
        company_id: str,
        leave_request_id: UUID,
    ) -> LeaveRequest:
        """查詢 leave request，若不存在或不屬於該 company 則 404

        Tenant Isolation: 強制帶 company_id，不可單靠 id 查詢
        """
        leave_request = self.request_repo.get_leave_request_by_id(
            company_id=company_id,
            leave_request_id=leave_request_id,
        )
        if not leave_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Leave request not found or does not belong to this company",
                    "error_code": "LEAVE_REQUEST_NOT_FOUND",
                }
            )
        return leave_request


def get_leave_service(db: Session) -> LeaveService:
    """Factory function for LeaveService (dependency injection)"""
    return LeaveService(db)
