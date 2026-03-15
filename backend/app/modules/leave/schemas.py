"""Leave Request System - Pydantic Schemas (Request/Response DTOs)

WP-11-08 Phase 2A: Leave Request Schema + Repo + Service Foundation

Schemas:
- LeaveType / LeaveApprovalPolicy read schemas
- LeaveRequest create / read / list schemas
- Approval action schemas
"""

from datetime import date, datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ============================================
# Leave Type Schemas
# ============================================

class LeaveTypeResponse(BaseModel):
    """Leave Type read schema"""
    id: UUID = Field(..., description="Leave Type ID")
    company_id: str = Field(..., description="Company ID (Tenant)")
    code: str = Field(..., description="Internal code (e.g. annual, sick)")
    name: str = Field(..., description="Display name")
    description: Optional[str] = Field(None, description="Optional description")
    annual_days: Optional[int] = Field(None, description="Annual quota in days (None = unlimited)")
    is_active: bool = Field(..., description="Active status")
    created_at: datetime = Field(..., description="Created timestamp (UTC)")
    updated_at: datetime = Field(..., description="Updated timestamp (UTC)")

    class Config:
        from_attributes = True


class LeaveTypeListResponse(BaseModel):
    """Leave Type list response"""
    leave_types: List[LeaveTypeResponse] = Field(..., description="Leave type list")
    total: int = Field(..., description="Total count")


# ============================================
# Leave Approval Policy Schemas
# ============================================

class LeaveApprovalPolicyResponse(BaseModel):
    """Leave Approval Policy read schema"""
    id: UUID = Field(..., description="Policy ID")
    company_id: str = Field(..., description="Company ID (Tenant)")
    leave_type_id: Optional[UUID] = Field(None, description="Leave Type ID (None = company-wide default)")
    min_days: float = Field(..., description="Lower bound of duration range (inclusive)")
    max_days: Optional[float] = Field(None, description="Upper bound of duration range (None = no upper limit)")
    approval_level: int = Field(..., description="Required approval level (1 or 2)")
    is_active: bool = Field(..., description="Active status")
    created_at: datetime = Field(..., description="Created timestamp (UTC)")
    updated_at: datetime = Field(..., description="Updated timestamp (UTC)")

    class Config:
        from_attributes = True


# ============================================
# Leave Request Create Schema
# ============================================

class LeaveRequestCreate(BaseModel):
    """Leave Request create schema

    Note: company_id and user_id come from JWT/tenant context, not from request body
    """
    leave_type_id: UUID = Field(..., description="Leave Type ID")
    start_date: date = Field(..., description="Leave start date (local date, Asia/Taipei)")
    end_date: date = Field(..., description="Leave end date inclusive (local date, Asia/Taipei)")
    reason: str = Field(..., min_length=1, max_length=1000, description="Reason for leave (required)")
    is_half_day: bool = Field(False, description="Half-day flag (reserved, Phase 1 not enforced)")

    @validator('reason')
    def reason_must_not_be_blank(cls, v):
        if not v or not v.strip():
            raise ValueError('Reason must not be blank')
        return v.strip()

    @validator('end_date')
    def end_date_must_not_be_before_start(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must not be earlier than start_date')
        return v


# ============================================
# Leave Request Read Schema
# ============================================

class LeaveRequestResponse(BaseModel):
    """Leave Request read schema"""
    id: UUID = Field(..., description="Leave Request ID")
    company_id: str = Field(..., description="Company ID (Tenant)")
    user_id: UUID = Field(..., description="Requester user ID")
    leave_type_id: UUID = Field(..., description="Leave Type ID")
    start_date: date = Field(..., description="Leave start date")
    end_date: date = Field(..., description="Leave end date inclusive")
    total_days: float = Field(..., description="Calculated duration in days")
    is_half_day: bool = Field(..., description="Half-day flag")
    reason: str = Field(..., description="Reason for leave")
    status: str = Field(..., description="Status: pending / approved / rejected / cancelled")
    required_approval_level: int = Field(..., description="Required approval level (1 or 2)")
    approver_id: Optional[UUID] = Field(None, description="Resolved approver user ID")
    approved_at: Optional[datetime] = Field(None, description="Approved timestamp (UTC)")
    rejected_at: Optional[datetime] = Field(None, description="Rejected timestamp (UTC)")
    cancelled_at: Optional[datetime] = Field(None, description="Cancelled timestamp (UTC)")
    created_at: datetime = Field(..., description="Created timestamp (UTC)")
    updated_at: datetime = Field(..., description="Updated timestamp (UTC)")

    class Config:
        from_attributes = True


# ============================================
# Approval Action Schema
# ============================================

class LeaveApprovalAction(BaseModel):
    """Approval action input schema (approve / reject)

    Note: actor_user_id comes from JWT context, not request body
    """
    comment: Optional[str] = Field(None, max_length=500, description="Optional comment from approver")

    @validator('comment')
    def trim_comment(cls, v):
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


class LeaveCancelAction(BaseModel):
    """Cancel action input schema

    Note: actor_user_id comes from JWT context, not request body
    """
    comment: Optional[str] = Field(None, max_length=500, description="Optional comment from requester")

    @validator('comment')
    def trim_comment(cls, v):
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


# ============================================
# Leave Approval Log Read Schema
# ============================================

class LeaveApprovalLogResponse(BaseModel):
    """Leave Approval Log read schema"""
    id: UUID = Field(..., description="Log entry ID")
    company_id: str = Field(..., description="Company ID (Tenant)")
    leave_request_id: UUID = Field(..., description="Leave Request ID")
    actor_user_id: UUID = Field(..., description="User who performed the action")
    action: str = Field(..., description="Action: approved / rejected / cancelled")
    approval_level: int = Field(..., description="Approval level at which action was taken")
    comment: Optional[str] = Field(None, description="Optional message")
    created_at: datetime = Field(..., description="Action timestamp (UTC, immutable)")

    class Config:
        from_attributes = True


# ============================================
# List / Summary Schemas
# ============================================

class MyLeaveRequestListItem(BaseModel):
    """My leave request list item (for requester's own list)"""
    id: UUID = Field(..., description="Leave Request ID")
    leave_type_id: UUID = Field(..., description="Leave Type ID")
    start_date: date = Field(..., description="Leave start date")
    end_date: date = Field(..., description="Leave end date inclusive")
    total_days: float = Field(..., description="Duration in days")
    reason: str = Field(..., description="Reason for leave")
    status: str = Field(..., description="Status: pending / approved / rejected / cancelled")
    created_at: datetime = Field(..., description="Submitted at (UTC)")

    class Config:
        from_attributes = True


class MyLeaveRequestListResponse(BaseModel):
    """My leave request list response"""
    requests: List[MyLeaveRequestListItem] = Field(..., description="Leave request list")
    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Limit used")
    offset: int = Field(..., description="Offset used")


class PendingApprovalListItem(BaseModel):
    """Pending approval list item (for approver)"""
    id: UUID = Field(..., description="Leave Request ID")
    company_id: str = Field(..., description="Company ID (Tenant)")
    user_id: UUID = Field(..., description="Requester user ID")
    leave_type_id: UUID = Field(..., description="Leave Type ID")
    start_date: date = Field(..., description="Leave start date")
    end_date: date = Field(..., description="Leave end date inclusive")
    total_days: float = Field(..., description="Duration in days")
    reason: str = Field(..., description="Reason for leave")
    required_approval_level: int = Field(..., description="Required approval level")
    created_at: datetime = Field(..., description="Submitted at (UTC)")

    class Config:
        from_attributes = True


class PendingApprovalListResponse(BaseModel):
    """Pending approval list response"""
    requests: List[PendingApprovalListItem] = Field(..., description="Pending approval list")
    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Limit used")
    offset: int = Field(..., description="Offset used")


# ============================================
# Error Schemas
# ============================================

class LeaveErrorResponse(BaseModel):
    """Standard leave error response"""
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
