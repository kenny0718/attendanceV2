"""Tenants – Members schemas (split from schemas.py, WP-S1-10B/10C/10D)"""

from pydantic import BaseModel, Field, field_serializer
from typing import List, Optional
from datetime import datetime


class CompanyMemberResponse(BaseModel):
    """Single user+membership record for admin view"""
    membership_id: str = Field(..., description="Membership ID")
    user_id: str = Field(..., description="User ID")
    company_id: str = Field(..., description="Company ID")
    role_id: str = Field(..., description="Role ID")
    login_username: str = Field(..., description="Per-company login username")
    membership_is_active: bool = Field(..., description="Membership active status")
    uses_schedule: bool = Field(..., description="Whether this member should see schedule features")
    membership_created_at: datetime = Field(..., description="Membership created timestamp")
    display_name: str = Field(..., description="User global display name")
    email: Optional[str] = Field(None, description="User email")
    user_is_active: bool = Field(..., description="User active status")

    @field_serializer('membership_created_at')
    def serialize_membership_created_at(self, dt: datetime, _info):
        return dt.isoformat()


class CompanyMembersResponse(BaseModel):
    company_id: str = Field(..., description="Company ID")
    members: List[CompanyMemberResponse] = Field(..., description="Members list")
    total: int = Field(..., description="Total member count")


class ToggleMembershipActiveRequest(BaseModel):
    is_active: bool = Field(..., description="Target active state for membership")


class ToggleMembershipActiveResponse(BaseModel):
    membership_id: str = Field(..., description="Membership ID")
    company_id: str = Field(..., description="Company ID")
    is_active: bool = Field(..., description="New active state")


class CreateMemberRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=100, description="User display name")
    email: Optional[str] = Field(None, max_length=255, description="Email for notifications (optional)")
    login_username: str = Field(..., min_length=1, max_length=100, description="Per-company login username")
    password: str = Field(..., min_length=6, max_length=255, description="Initial password (min 6 chars)")
    role_id: str = Field(default="employee", max_length=50, description="Membership role (default: employee)")
    uses_schedule: bool = Field(default=False, description="Whether this member should see schedule features")


class CreateMemberResponse(BaseModel):
    membership_id: str = Field(..., description="Membership ID")
    user_id: str = Field(..., description="User ID")
    company_id: str = Field(..., description="Company ID")
    role_id: str = Field(..., description="Role ID")
    login_username: str = Field(..., description="Per-company login username")
    uses_schedule: bool = Field(..., description="Whether this member should see schedule features")
    display_name: str = Field(..., description="User display name")
    email: Optional[str] = Field(None, description="User email")
    is_active: bool = Field(..., description="Membership active status")


class UpdateMemberRequest(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User global display name")
    email: Optional[str] = Field(None, max_length=255, description="Email for notifications (optional, set null to clear)")
    role_id: Optional[str] = Field(None, max_length=50, description="Membership role (e.g. employee / hr_manager / company_admin)")
    uses_schedule: Optional[bool] = Field(None, description="Whether this member should see schedule features")
    login_username: Optional[str] = Field(None, min_length=1, max_length=100, description="Per-company login username (unique within company)")


class UpdateMemberResponse(BaseModel):
    membership_id: str = Field(..., description="Membership ID")
    user_id: str = Field(..., description="User ID")
    company_id: str = Field(..., description="Company ID")
    role_id: str = Field(..., description="Role ID after update")
    display_name: str = Field(..., description="User display name after update")
    email: Optional[str] = Field(None, description="User email after update")
    login_username: str = Field(..., description="Per-company login username after update")
    uses_schedule: bool = Field(..., description="Whether this member should see schedule features")
    membership_is_active: bool = Field(..., description="Membership active status (unchanged)")


class ResetMemberPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=255, description="New password (min 6 chars). Will be bcrypt-hashed server-side.")


class ResetMemberPasswordResponse(BaseModel):
    membership_id: str = Field(..., description="Membership ID")
    user_id: str = Field(..., description="User ID")
    message: str = Field(default="Password updated successfully", description="Success message")
