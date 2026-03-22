"""Tenants API schemas

WP-11-04A: Added CompanyEntitlement schemas
WP-S1-09A: Added company list / create schemas
"""

from pydantic import BaseModel, Field, field_serializer
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime


# ── WP-S1-09A: Company (Tenant) management schemas ───────────────────

class CreateCompanyRequest(BaseModel):
    """POST /api/admin/companies — request body"""
    id: str = Field(..., min_length=1, max_length=50, description="Company ID (tenant identifier, e.g. 'company-b')")
    name: str = Field(..., min_length=1, max_length=255, description="Company display name")
    timezone: str = Field(default="UTC", max_length=50, description="Company timezone (default: UTC)")


class CompanyResponse(BaseModel):
    """Single company/tenant summary response"""
    id: str = Field(..., description="Company ID")
    name: str = Field(..., description="Company display name")
    is_active: bool = Field(..., description="Active status")
    timezone: str = Field(..., description="Company timezone")
    created_at: datetime = Field(..., description="Created timestamp (UTC)")

    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime, _info):
        return dt.isoformat()

    model_config = {"from_attributes": True}


class CompanyListResponse(BaseModel):
    """GET /api/admin/companies — response body"""
    companies: List[CompanyResponse] = Field(..., description="List of companies")
    total: int = Field(..., description="Total count returned")


# ── WP-11-04A: Entitlement schemas ───────────────────────────────────

class UpdateEntitlementRequest(BaseModel):
    """更新 entitlement 的請求"""
    feature_key: str = Field(..., description="功能 key (e.g., attendance.shift_templates)")
    enabled: bool = Field(..., description="是否啟用")


class ApplyPlanRequest(BaseModel):
    """套用 plan 預設值的請求"""
    plan_code: str = Field(..., description="Plan 代碼 (Basic/Pro)")


class EntitlementResponse(BaseModel):
    """單一 entitlement 回應"""
    company_id: str = Field(..., description="公司 ID")
    feature_key: str = Field(..., description="功能 key")
    enabled: bool = Field(..., description="是否啟用")
    updated_by: Optional[str] = Field(None, description="更新者 user_id")
    updated_at: datetime = Field(..., description="更新時間")

    @field_serializer('updated_at')
    def serialize_datetime(self, dt: datetime, _info):
        """序列化 datetime 為 ISO 8601 字串"""
        return dt.isoformat()


class CompanyEntitlementsResponse(BaseModel):
    """公司所有 entitlements 回應"""
    company_id: str = Field(..., description="公司 ID")
    entitlements: Dict[str, bool] = Field(..., description="feature_key -> enabled 對應")


class ApplyPlanResponse(BaseModel):
    """套用 plan 結果回應"""
    company_id: str = Field(..., description="公司 ID")
    plan_code: str = Field(..., description="Plan 代碼")
    updated_count: int = Field(..., description="更新的 entitlement 數量")


# ── WP-S1-09C: Admin Onboarding schemas ─────────────────────────────

class OnboardingUserRequest(BaseModel):
    """Initial user to create during onboarding"""
    display_name: str = Field(..., min_length=1, max_length=100, description="User display name")
    login_username: str = Field(..., min_length=1, max_length=100, description="Per-company login username")
    password: str = Field(..., min_length=6, max_length=255, description="Initial password (min 6 chars)")
    email: Optional[str] = Field(None, max_length=255, description="Email for notifications (optional)")
    role_id: str = Field(default="company_admin", max_length=50, description="Membership role (default: company_admin)")


class AdminOnboardingRequest(BaseModel):
    """POST /api/admin/onboarding — create company + initial user + membership atomically"""
    company: CreateCompanyRequest = Field(..., description="Company to create")
    initial_user: OnboardingUserRequest = Field(..., description="Initial user to create and attach")


class OnboardingCompanyResult(BaseModel):
    """Company creation result within onboarding response"""
    id: str
    name: str
    timezone: str
    is_active: bool
    created_at: datetime

    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime, _info):
        return dt.isoformat()

    model_config = {"from_attributes": True}


class OnboardingUserResult(BaseModel):
    """User creation result within onboarding response"""
    id: str
    display_name: str
    email: Optional[str] = None


class OnboardingMembershipResult(BaseModel):
    """Membership creation result within onboarding response"""
    id: str
    user_id: str
    company_id: str
    role_id: str
    login_username: str


class AdminOnboardingResponse(BaseModel):
    """POST /api/admin/onboarding — response: company + user + membership results"""
    company: OnboardingCompanyResult
    user: OnboardingUserResult
    membership: OnboardingMembershipResult


# ── WP-S1-10B: Admin read-only members view schemas ──────────────────

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


# ── WP-S1-10C: Membership toggle schemas ─────────────────────────────

class ToggleMembershipActiveRequest(BaseModel):
    """PATCH /api/admin/companies/{company_id}/members/{membership_id}/active"""
    is_active: bool = Field(..., description="Target active state for membership")


class ToggleMembershipActiveResponse(BaseModel):
    """Response after toggling membership active state"""
    membership_id: str = Field(..., description="Membership ID")
    company_id: str = Field(..., description="Company ID")
    is_active: bool = Field(..., description="New active state")



# ── WP-S1-10D: Create Member schemas ─────────────────────────────────

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
