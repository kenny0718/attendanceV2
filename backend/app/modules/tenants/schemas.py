"""Tenants API schemas – façade re-export

This file is kept as a compatibility shim so that all existing callers
(api.py, tests, etc.) can continue importing from this path without change.

Actual class definitions live in:
  - schemas_companies.py   (CreateCompanyRequest, CompanyResponse, CompanyListResponse)
  - schemas_entitlements.py (UpdateEntitlementRequest, ApplyPlanRequest,
                              EntitlementResponse, CompanyEntitlementsResponse, ApplyPlanResponse)
  - schemas_onboarding.py  (OnboardingUserRequest, AdminOnboardingRequest,
                              OnboardingCompanyResult, OnboardingUserResult,
                              OnboardingMembershipResult, AdminOnboardingResponse)
  - schemas_members.py     (CompanyMemberResponse, CompanyMembersResponse,
                              ToggleMembershipActiveRequest, ToggleMembershipActiveResponse,
                              CreateMemberRequest, CreateMemberResponse)

WP-11-04A: Added CompanyEntitlement schemas
WP-S1-09A: Added company list / create schemas
"""

# Companies
from app.modules.tenants.schemas_companies import (
    CreateCompanyRequest,
    CompanyResponse,
    CompanyListResponse,
)

# Entitlements
from app.modules.tenants.schemas_entitlements import (
    UpdateEntitlementRequest,
    ApplyPlanRequest,
    EntitlementResponse,
    CompanyEntitlementsResponse,
    ApplyPlanResponse,
)

# Onboarding
from app.modules.tenants.schemas_onboarding import (
    OnboardingUserRequest,
    AdminOnboardingRequest,
    OnboardingCompanyResult,
    OnboardingUserResult,
    OnboardingMembershipResult,
    AdminOnboardingResponse,
)

# Members
from app.modules.tenants.schemas_members import (
    CompanyMemberResponse,
    CompanyMembersResponse,
    ToggleMembershipActiveRequest,
    ToggleMembershipActiveResponse,
    CreateMemberRequest,
    CreateMemberResponse,
)

__all__ = [
    # Companies
    "CreateCompanyRequest",
    "CompanyResponse",
    "CompanyListResponse",
    # Entitlements
    "UpdateEntitlementRequest",
    "ApplyPlanRequest",
    "EntitlementResponse",
    "CompanyEntitlementsResponse",
    "ApplyPlanResponse",
    # Onboarding
    "OnboardingUserRequest",
    "AdminOnboardingRequest",
    "OnboardingCompanyResult",
    "OnboardingUserResult",
    "OnboardingMembershipResult",
    "AdminOnboardingResponse",
    # Members
    "CompanyMemberResponse",
    "CompanyMembersResponse",
    "ToggleMembershipActiveRequest",
    "ToggleMembershipActiveResponse",
    "CreateMemberRequest",
    "CreateMemberResponse",
]
