"""Leave Request System - Data Models

WP-11-08 Phase 1: Leave Request System Backend Foundation
Based on: WP-11-08_PHASE1_SCHEMA_DESIGN.md

Tables created:
- leave_types
- leave_approval_policies
- leave_requests
- leave_approval_logs

Note: users.manager_id is added via migration 009_wp_11_08.
The User model in auth/models.py is updated separately.
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer,
    Text, Date, Numeric, Index, CheckConstraint,
    UniqueConstraint, ForeignKeyConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text

from app.core.database import Base


class LeaveType(Base):
    """Leave Type model

    WP-11-08 Phase 1
    Defines leave categories available to employees per company.
    Fully tenant-isolated: UNIQUE(company_id, code).
    """

    __tablename__ = "leave_types"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text('gen_random_uuid()'),
        comment="Leave Type ID (PK)"
    )

    # Tenant isolation
    company_id = Column(
        String(255),
        nullable=False,
        comment="Company ID (Tenant Isolation, FK to tenants.id)"
    )

    # Identity
    code = Column(
        String(50),
        nullable=False,
        comment="Internal code (annual, sick, personal, etc.) - unique per company"
    )
    name = Column(
        String(100),
        nullable=False,
        comment="Display name shown in UI"
    )
    description = Column(
        Text,
        nullable=True,
        comment="Optional description"
    )

    # Quota
    annual_days = Column(
        Integer,
        nullable=True,
        comment="Annual quota in days (NULL = unlimited)"
    )

    # Status
    is_active = Column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Active status (soft-delete pattern)"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP'),
        comment="Created timestamp (UTC)"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP'),
        comment="Updated timestamp (UTC)"
    )

    __table_args__ = (
        UniqueConstraint('company_id', 'code', name='uq_leave_types_company_code'),
        CheckConstraint('annual_days > 0 OR annual_days IS NULL', name='chk_leave_types_annual_days_positive'),
        ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
        Index('idx_leave_types_company', 'company_id'),
        Index('idx_leave_types_company_active', 'company_id', 'is_active'),
    )

    def __repr__(self):
        return f"<LeaveType(id={self.id}, company_id={self.company_id}, code={self.code})>"


class LeaveApprovalPolicy(Base):
    """Leave Approval Policy model

    WP-11-08 Phase 1
    Defines required approval level based on duration and leave type.

    Strict Policy Mode:
    - If no matching policy is found at submission, leave request is rejected (422).
    - No fallback to Level 1 or generic admin.

    Policy lookup order (service layer, not enforced here):
    1. company_id + leave_type_id + days range  (type-specific)
    2. company_id + leave_type_id IS NULL + days range  (company-wide default)
    3. No match -> 422 reject

    leave_type_id nullable: NULL = company-wide default policy.
    """

    __tablename__ = "leave_approval_policies"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text('gen_random_uuid()'),
        comment="Policy ID (PK)"
    )

    # Tenant isolation
    company_id = Column(
        String(255),
        nullable=False,
        comment="Company ID (Tenant Isolation, FK to tenants.id)"
    )

    # Policy scope (nullable = company-wide default)
    leave_type_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Leave Type ID (FK to leave_types.id). NULL = company-wide default policy."
    )

    # Duration range
    min_days = Column(
        Numeric(4, 1),
        nullable=False,
        comment="Lower bound of duration range (inclusive, days)"
    )
    max_days = Column(
        Numeric(4, 1),
        nullable=True,
        comment="Upper bound of duration range (inclusive, days). NULL = no upper limit."
    )

    # Approval level
    approval_level = Column(
        Integer,
        nullable=False,
        comment="Required approval level: 1 (direct manager) or 2 (manager of manager)"
    )

    # Status
    is_active = Column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Active status"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP'),
        comment="Created timestamp (UTC)"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP'),
        comment="Updated timestamp (UTC)"
    )

    __table_args__ = (
        CheckConstraint('min_days > 0', name='chk_leave_policies_min_days_positive'),
        CheckConstraint('max_days IS NULL OR max_days >= min_days', name='chk_leave_policies_max_gte_min'),
        CheckConstraint('approval_level IN (1, 2)', name='chk_leave_policies_approval_level'),
        ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['leave_type_id'], ['leave_types.id'], ondelete='CASCADE'),
        Index('idx_leave_policies_company', 'company_id'),
        Index('idx_leave_policies_company_active', 'company_id', 'is_active'),
        Index('idx_leave_policies_company_type', 'company_id', 'leave_type_id'),
    )

    def __repr__(self):
        return (
            f"<LeaveApprovalPolicy(id={self.id}, company_id={self.company_id}, "
            f"leave_type_id={self.leave_type_id}, approval_level={self.approval_level})>"
        )


class LeaveRequest(Base):
    """Leave Request model

    WP-11-08 Phase 1
    Stores all leave request submissions from employees.

    Key design points:
    - reason is NOT NULL (required at submission)
    - approver_id is resolved and stored at submission time (not at approval time)
    - status: pending -> approved / rejected / cancelled (terminal states)
    - required_approval_level resolved from policy at submission
    """

    __tablename__ = "leave_requests"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text('gen_random_uuid()'),
        comment="Leave Request ID (PK)"
    )

    # Tenant isolation
    company_id = Column(
        String(255),
        nullable=False,
        comment="Company ID (Tenant Isolation, FK to tenants.id)"
    )

    # Requester
    user_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        comment="Requester user ID (FK to users.id)"
    )

    # Leave type
    leave_type_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        comment="Leave Type ID (FK to leave_types.id)"
    )

    # Duration
    start_date = Column(
        Date,
        nullable=False,
        comment="Leave start date (Asia/Taipei local date)"
    )
    end_date = Column(
        Date,
        nullable=False,
        comment="Leave end date inclusive (Asia/Taipei local date)"
    )
    total_days = Column(
        Numeric(4, 1),
        nullable=False,
        comment="Calculated duration in days (0.5 for half-day)"
    )
    is_half_day = Column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="Half-day flag (reserved, not enforced in Phase 1)"
    )

    # Reason (required)
    reason = Column(
        Text,
        nullable=False,
        comment="Employee-provided reason (required, NOT NULL)"
    )

    # Status
    status = Column(
        String(20),
        nullable=False,
        server_default="pending",
        comment="Request status: pending / approved / rejected / cancelled"
    )

    # Approval chain (resolved at submission)
    required_approval_level = Column(
        Integer,
        nullable=False,
        comment="Required approval level (1 or 2), resolved from policy at submission"
    )
    approver_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Resolved approver user ID (stored at submission, FK to users.id)"
    )

    # Action timestamps
    approved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Approved timestamp (UTC)"
    )
    rejected_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Rejected timestamp (UTC)"
    )
    cancelled_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Cancelled timestamp (UTC)"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP'),
        comment="Created timestamp (UTC)"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP'),
        comment="Updated timestamp (UTC)"
    )

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'rejected', 'cancelled')", name='chk_leave_requests_status'),
        CheckConstraint('end_date >= start_date', name='chk_leave_requests_date_range'),
        CheckConstraint('total_days > 0', name='chk_leave_requests_total_days_positive'),
        CheckConstraint('required_approval_level IN (1, 2)', name='chk_leave_requests_approval_level'),
        ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['leave_type_id'], ['leave_types.id'], ondelete='RESTRICT'),
        ForeignKeyConstraint(['approver_id'], ['users.id'], ondelete='SET NULL'),
        Index('idx_leave_requests_company', 'company_id'),
        Index('idx_leave_requests_company_user', 'company_id', 'user_id'),
        Index('idx_leave_requests_company_status', 'company_id', 'status'),
        Index('idx_leave_requests_approver', 'approver_id'),
        Index('idx_leave_requests_user_dates', 'user_id', 'start_date', 'end_date'),
        Index('idx_leave_requests_leave_type', 'leave_type_id'),
    )

    def __repr__(self):
        return (
            f"<LeaveRequest(id={self.id}, company_id={self.company_id}, "
            f"user_id={self.user_id}, status={self.status})>"
        )


class LeaveApprovalLog(Base):
    """Leave Approval Log model

    WP-11-08 Phase 1
    Immutable audit log of all approval actions on leave requests.
    Append-only: records are never updated or deleted.
    company_id is denormalized for efficient tenant-scoped audit queries.
    """

    __tablename__ = "leave_approval_logs"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text('gen_random_uuid()'),
        comment="Log entry ID (PK)"
    )

    # Tenant isolation (denormalized)
    company_id = Column(
        String(255),
        nullable=False,
        comment="Company ID (Tenant Isolation, denormalized from leave_request)"
    )

    # References
    leave_request_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        comment="Leave Request ID (FK to leave_requests.id)"
    )
    actor_user_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        comment="User who performed the action (FK to users.id)"
    )

    # Action
    action = Column(
        String(20),
        nullable=False,
        comment="Action taken: approved / rejected / cancelled"
    )
    approval_level = Column(
        Integer,
        nullable=False,
        comment="Approval level at which this action was taken (1 or 2)"
    )
    comment = Column(
        Text,
        nullable=True,
        comment="Optional message from approver or requester"
    )

    # Timestamp (no updated_at: append-only)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text('CURRENT_TIMESTAMP'),
        comment="Action timestamp (UTC, immutable)"
    )

    __table_args__ = (
        CheckConstraint("action IN ('approved', 'rejected', 'cancelled')", name='chk_leave_logs_action'),
        CheckConstraint('approval_level IN (1, 2)', name='chk_leave_logs_approval_level'),
        ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['leave_request_id'], ['leave_requests.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='CASCADE'),
        Index('idx_leave_logs_request', 'leave_request_id'),
        Index('idx_leave_logs_company', 'company_id'),
        Index('idx_leave_logs_actor', 'actor_user_id'),
    )

    def __repr__(self):
        return (
            f"<LeaveApprovalLog(id={self.id}, leave_request_id={self.leave_request_id}, "
            f"action={self.action})>"
        )
