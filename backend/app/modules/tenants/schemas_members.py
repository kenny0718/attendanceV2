"""Tenants – Members schemas (split from schemas.py, WP-S1-10B/10C/10D)"""

from pydantic import BaseModel, Field, field_serializer
from typing import List, Optional
from datetime import datetime


class CompanyMemberResponse(BaseModel):
    """Single user+membership record for admin view"""
    # Membership fields
    membership_id: str = Field(..., description="Membership ID")
    user_id: str = Field(..., description="User ID")
    company_id: str = Field(..., description="Company ID")
    role_id: str = Field(..., description="Role ID")
    login_username: str = Field(..., description="Per-company login username")
    membership_is_active: bool = Field(..., description="Membership active status")
    membership_created_at: datetime = Field(..., description="Membership created timestamp")
    # User fields
    display_name: str = Field(..., description="User global display name")
    email: Optional[str] = Field(None, description="User email")
    user_is_active: bool = Field(..., description="User active status")

    @field_serializer('membership_created_at')
    def serialize_membership_created_at(self, dt: datetime, _info):
        return dt.isoformat()


class CompanyMembersResponse(BaseModel):
    """GET /api/admin/companies/{company_id}/members - response"""
    company_id: str = Field(..., description="Company ID")
    members: List[CompanyMemberResponse] = Field(..., description="Members list")
    total: int = Field(..., description="Total member count")


class ToggleMembershipActiveRequest(BaseModel):
    """PATCH /api/admin/companies/{company_id}/members/{membership_id}/active"""
    is_active: bool = Field(..., description="Target active state for membership")


class ToggleMembershipActiveResponse(BaseModel):
    """Response after toggling membership active state"""
    membership_id: str = Field(..., description="Membership ID")
    company_id: str = Field(..., description="Company ID")
    is_active: bool = Field(..., description="New active state")


class CreateMemberRequest(BaseModel):
    """POST /api/admin/companies/{company_id}/members — request body"""
    display_name: str = Field(..., min_length=1, max_length=100, description="User display name")
    email: Optional[str] = Field(None, max_length=255, description="Email for notifications (optional)")
    login_username: str = Field(..., min_length=1, max_length=100, description="Per-company login username")
    password: str = Field(..., min_length=6, max_length=255, description="Initial password (min 6 chars)")
    role_id: str = Field(default="employee", max_length=50, description="Membership role (default: employee)")


class CreateMemberResponse(BaseModel):
    """POST /api/admin/companies/{company_id}/members — response body"""
    membership_id: str = Field(..., description="Membership ID")
    user_id: str = Field(..., description="User ID")
    company_id: str = Field(..., description="Company ID")
    role_id: str = Field(..., description="Role ID")
    login_username: str = Field(..., description="Per-company login username")
    display_name: str = Field(..., description="User display name")
    email: Optional[str] = Field(None, description="User email")
    is_active: bool = Field(..., description="Membership active status")


class UpdateMemberRequest(BaseModel):
    """PATCH /{company_id}/members/{membership_id} — request body (S1-13A1/A2)
    All fields Optional; only provided fields will be updated.
    password is NOT included (separate flow).
    """
    display_name: Optional[str] = Field(None, min_length=1, max_length=100, description="User global display name")
    email: Optional[str] = Field(None, max_length=255, description="Email for notifications (optional, set null to clear)")
    role_id: Optional[str] = Field(None, max_length=50, description="Membership role (e.g. employee / hr_manager / company_admin)")
    # S1-13A2: login_username edit
    login_username: Optional[str] = Field(None, min_length=1, max_length=100, description="Per-company login username (unique within company)")


class UpdateMemberResponse(BaseModel):
    """PATCH /{company_id}/members/{membership_id} — response body (S1-13A1/A2)"""
    membership_id: str = Field(..., description="Membership ID")
    user_id: str = Field(..., description="User ID")
    company_id: str = Field(..., description="Company ID")
    role_id: str = Field(..., description="Role ID after update")
    display_name: str = Field(..., description="User display name after update")
    email: Optional[str] = Field(None, description="User email after update")
    login_username: str = Field(..., description="Per-company login username after update")
    membership_is_active: bool = Field(..., description="Membership active status (unchanged)")


class ResetMemberPasswordRequest(BaseModel):
    """PATCH /{company_id}/members/{membership_id}/password — request body (S1-13A3)
    Admin resets a member password. Not exposed to non-admin roles.
    """
    new_password: str = Field(
        ...,
        min_length=6,
        max_length=255,
        description="New password (min 6 chars). Will be bcrypt-hashed server-side.",
    )


class ResetMemberPasswordResponse(BaseModel):
    """PATCH /{company_id}/members/{membership_id}/password — response body (S1-13A3)
    Does NOT expose password, hash, or any sensitive auth detail.
    """
    membership_id: str = Field(..., description="Membership ID")
    user_id: str = Field(..., description="User ID")
    message: str = Field(default="Password updated successfully", description="Success message")
