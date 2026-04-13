"""Tenants – Onboarding schemas (split from schemas.py, WP-S1-09C)"""

from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime

from app.modules.tenants.schemas_companies import CreateCompanyRequest


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
    tax_id: Optional[str] = None
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
