"""Leave Request System - Repository Layer (資料存取層)

WP-11-08 Phase 2A: Leave Request Schema + Repo + Service Foundation

Tenant Isolation (P0):
- 所有查詢必須強制 WHERE company_id = ?
- 不可只靠 request id 查資料

Repo 只負責：查、建、更新、log 寫入
業務規則不放 repo，由 service 層處理
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.modules.leave.models import (
    LeaveType,
    LeaveApprovalPolicy,
    LeaveRequest,
    LeaveApprovalLog,
)

logger = logging.getLogger(__name__)


def get_current_time() -> datetime:
    """Return current UTC time (timezone-aware)"""
    return datetime.now(timezone.utc)


# ============================================
# Leave Type Repository
# ============================================

class LeaveTypeRepository:
    """Leave Type 資料存取層"""

    def __init__(self, db: Session):
        self.db = db

    def get_active_leave_types(
        self,
        company_id: str,
    ) -> List[LeaveType]:
        """依 company_id 取得所有啟用的 leave types

        Tenant Isolation: 強制 WHERE company_id = ?
        """
        return (
            self.db.query(LeaveType)
            .filter(
                and_(
                    LeaveType.company_id == company_id,
                    LeaveType.is_active == True,
                )
            )
            .order_by(LeaveType.code.asc())
            .all()
        )

    def get_leave_type_by_id(
        self,
        company_id: str,
        leave_type_id: UUID,
    ) -> Optional[LeaveType]:
        """依 id + company_id 查單一 leave type

        Tenant Isolation: 強制 WHERE company_id = ?
        """
        return (
            self.db.query(LeaveType)
            .filter(
                and_(
                    LeaveType.id == leave_type_id,
                    LeaveType.company_id == company_id,
                )
            )
            .first()
        )


def get_leave_type_repository(db: Session) -> LeaveTypeRepository:
    """Factory function for LeaveTypeRepository"""
    return LeaveTypeRepository(db)


# ============================================
# Leave Approval Policy Repository
# ============================================

class LeaveApprovalPolicyRepository:
    """Leave Approval Policy 資料存取層"""

    def __init__(self, db: Session):
        self.db = db

    def get_active_policies(
        self,
        company_id: str,
    ) -> List[LeaveApprovalPolicy]:
        """依 company_id 取得所有啟用的 approval policies

        Tenant Isolation: 強制 WHERE company_id = ?
        """
        return (
            self.db.query(LeaveApprovalPolicy)
            .filter(
                and_(
                    LeaveApprovalPolicy.company_id == company_id,
                    LeaveApprovalPolicy.is_active == True,
                )
            )
            .order_by(
                LeaveApprovalPolicy.leave_type_id.asc().nullslast(),
                LeaveApprovalPolicy.min_days.asc(),
            )
            .all()
        )

    def get_policy_by_id(
        self,
        company_id: str,
        policy_id: UUID,
    ) -> Optional[LeaveApprovalPolicy]:
        """依 id + company_id 查單一 approval policy

        Tenant Isolation: 強制 WHERE company_id = ?
        """
        return (
            self.db.query(LeaveApprovalPolicy)
            .filter(
                and_(
                    LeaveApprovalPolicy.id == policy_id,
                    LeaveApprovalPolicy.company_id == company_id,
                )
            )
            .first()
        )

    def find_matching_policy(
        self,
        company_id: str,
        leave_type_id: UUID,
        total_days: float,
    ) -> Optional[LeaveApprovalPolicy]:
        """查找符合條件的 approval policy

        Policy lookup order (per WP-11-08 spec):
        1. company_id + leave_type_id + days range  (type-specific)
        2. company_id + leave_type_id IS NULL + days range  (company-wide default)
        3. No match -> None (service 層負責 422 reject)

        Tenant Isolation: 強制 WHERE company_id = ?
        """
        # Step 1: type-specific policy
        type_specific = (
            self.db.query(LeaveApprovalPolicy)
            .filter(
                and_(
                    LeaveApprovalPolicy.company_id == company_id,
                    LeaveApprovalPolicy.leave_type_id == leave_type_id,
                    LeaveApprovalPolicy.is_active == True,
                    LeaveApprovalPolicy.min_days <= total_days,
                    (
                        LeaveApprovalPolicy.max_days.is_(None)
                        | (LeaveApprovalPolicy.max_days >= total_days)
                    ),
                )
            )
            .order_by(LeaveApprovalPolicy.min_days.asc())
            .first()
        )
        if type_specific:
            return type_specific

        # Step 2: company-wide default policy (leave_type_id IS NULL)
        return (
            self.db.query(LeaveApprovalPolicy)
            .filter(
                and_(
                    LeaveApprovalPolicy.company_id == company_id,
                    LeaveApprovalPolicy.leave_type_id.is_(None),
                    LeaveApprovalPolicy.is_active == True,
                    LeaveApprovalPolicy.min_days <= total_days,
                    (
                        LeaveApprovalPolicy.max_days.is_(None)
                        | (LeaveApprovalPolicy.max_days >= total_days)
                    ),
                )
            )
            .order_by(LeaveApprovalPolicy.min_days.asc())
            .first()
        )


def get_leave_approval_policy_repository(db: Session) -> LeaveApprovalPolicyRepository:
    """Factory function for LeaveApprovalPolicyRepository"""
    return LeaveApprovalPolicyRepository(db)


# ============================================
# Leave Request Repository
# ============================================

class LeaveRequestRepository:
    """Leave Request 資料存取層"""

    def __init__(self, db: Session):
        self.db = db

    def create_leave_request(
        self,
        company_id: str,
        user_id: UUID,
        leave_type_id: UUID,
        start_date,
        end_date,
        total_days: float,
        reason: str,
        required_approval_level: int,
        is_half_day: bool = False,
        approver_id: Optional[UUID] = None,
    ) -> LeaveRequest:
        """建立 leave request"""
        leave_request = LeaveRequest(
            company_id=company_id,
            user_id=user_id,
            leave_type_id=leave_type_id,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            reason=reason,
            is_half_day=is_half_day,
            status='pending',
            required_approval_level=required_approval_level,
            approver_id=approver_id,
        )

        self.db.add(leave_request)
        self.db.commit()
        self.db.refresh(leave_request)

        logger.info(
            f"Created leave request: id={leave_request.id}, "
            f"company_id={company_id}, user_id={user_id}, "
            f"leave_type_id={leave_type_id}, status=pending"
        )

        return leave_request

    def get_leave_request_by_id(
        self,
        company_id: str,
        leave_request_id: UUID,
    ) -> Optional[LeaveRequest]:
        """依 id + company_id 查單一 leave request

        Tenant Isolation: 強制 WHERE company_id = ?
        """
        return (
            self.db.query(LeaveRequest)
            .filter(
                and_(
                    LeaveRequest.id == leave_request_id,
                    LeaveRequest.company_id == company_id,
                )
            )
            .first()
        )

    def get_user_leave_requests(
        self,
        company_id: str,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> List[LeaveRequest]:
        """取得某使用者的 leave requests (分頁)

        Tenant Isolation: 強制 WHERE company_id = ?
        """
        query = (
            self.db.query(LeaveRequest)
            .filter(
                and_(
                    LeaveRequest.company_id == company_id,
                    LeaveRequest.user_id == user_id,
                )
            )
        )

        if status:
            query = query.filter(LeaveRequest.status == status)

        return (
            query
            .order_by(LeaveRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def count_user_leave_requests(
        self,
        company_id: str,
        user_id: UUID,
        status: Optional[str] = None,
    ) -> int:
        """計算某使用者的 leave requests 總數"""
        query = (
            self.db.query(LeaveRequest)
            .filter(
                and_(
                    LeaveRequest.company_id == company_id,
                    LeaveRequest.user_id == user_id,
                )
            )
        )

        if status:
            query = query.filter(LeaveRequest.status == status)

        return query.count()

    def get_pending_leave_requests(
        self,
        company_id: str,
        approver_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[LeaveRequest]:
        """取得待審批的 leave requests (分頁)

        Tenant Isolation: 強制 WHERE company_id = ?
        可選擇性過濾 approver_id（審批人自己的 pending list）
        """
        query = (
            self.db.query(LeaveRequest)
            .filter(
                and_(
                    LeaveRequest.company_id == company_id,
                    LeaveRequest.status == 'pending',
                )
            )
        )

        if approver_id:
            query = query.filter(LeaveRequest.approver_id == approver_id)

        return (
            query
            .order_by(LeaveRequest.created_at.asc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def count_pending_leave_requests(
        self,
        company_id: str,
        approver_id: Optional[UUID] = None,
    ) -> int:
        """計算待審批的 leave requests 總數"""
        query = (
            self.db.query(LeaveRequest)
            .filter(
                and_(
                    LeaveRequest.company_id == company_id,
                    LeaveRequest.status == 'pending',
                )
            )
        )

        if approver_id:
            query = query.filter(LeaveRequest.approver_id == approver_id)

        return query.count()

    def update_leave_request_status(
        self,
        leave_request: LeaveRequest,
        new_status: str,
        approved_at: Optional[datetime] = None,
        rejected_at: Optional[datetime] = None,
        cancelled_at: Optional[datetime] = None,
    ) -> LeaveRequest:
        """更新 leave request 狀態

        只做欄位更新，業務狀態合法性驗證由 service 層負責
        """
        leave_request.status = new_status
        leave_request.updated_at = get_current_time()

        if approved_at:
            leave_request.approved_at = approved_at
        if rejected_at:
            leave_request.rejected_at = rejected_at
        if cancelled_at:
            leave_request.cancelled_at = cancelled_at

        self.db.commit()
        self.db.refresh(leave_request)

        logger.info(
            f"Updated leave request status: id={leave_request.id}, "
            f"new_status={new_status}"
        )

        return leave_request


def get_leave_request_repository(db: Session) -> LeaveRequestRepository:
    """Factory function for LeaveRequestRepository"""
    return LeaveRequestRepository(db)


# ============================================
# Leave Approval Log Repository
# ============================================

class LeaveApprovalLogRepository:
    """Leave Approval Log 資料存取層（append-only）"""

    def __init__(self, db: Session):
        self.db = db

    def create_log(
        self,
        company_id: str,
        leave_request_id: UUID,
        actor_user_id: UUID,
        action: str,
        approval_level: int,
        comment: Optional[str] = None,
    ) -> LeaveApprovalLog:
        """寫入 approval log（append-only，不可修改）"""
        log_entry = LeaveApprovalLog(
            company_id=company_id,
            leave_request_id=leave_request_id,
            actor_user_id=actor_user_id,
            action=action,
            approval_level=approval_level,
            comment=comment,
        )

        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)

        logger.info(
            f"Created approval log: id={log_entry.id}, "
            f"leave_request_id={leave_request_id}, "
            f"actor_user_id={actor_user_id}, action={action}"
        )

        return log_entry

    def get_logs_by_request(
        self,
        company_id: str,
        leave_request_id: UUID,
    ) -> List[LeaveApprovalLog]:
        """取得某 leave request 的所有 approval logs

        Tenant Isolation: 強制 WHERE company_id = ?
        """
        return (
            self.db.query(LeaveApprovalLog)
            .filter(
                and_(
                    LeaveApprovalLog.company_id == company_id,
                    LeaveApprovalLog.leave_request_id == leave_request_id,
                )
            )
            .order_by(LeaveApprovalLog.created_at.asc())
            .all()
        )


def get_leave_approval_log_repository(db: Session) -> LeaveApprovalLogRepository:
    """Factory function for LeaveApprovalLogRepository"""
    return LeaveApprovalLogRepository(db)
