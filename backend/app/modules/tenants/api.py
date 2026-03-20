"""Tenants API endpoints

WP-11-04A: Added CompanyEntitlement management endpoints
WP-S1-09A: Added GET /api/admin/companies and POST /api/admin/companies
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.scope import Actor, ScopeError
from app.core.dependencies import get_current_actor
from app.modules.tenants.service import (
    get_entitlement_service,
    get_tenant_service,
    CompanyEntitlementService,
    TenantService,
)
from app.modules.tenants.schemas import (
    UpdateEntitlementRequest,
    ApplyPlanRequest,
    EntitlementResponse,
    CompanyEntitlementsResponse,
    ApplyPlanResponse,
    CreateCompanyRequest,
    CompanyResponse,
    CompanyListResponse,
)

router = APIRouter(prefix="/api/admin/companies", tags=["admin", "entitlements"])


# ── WP-S1-09A: Company management endpoints (super_admin only) ────────

@router.get("", response_model=CompanyListResponse)
def list_companies(
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
):
    """
    列出所有公司/租戶

    權限：僅限 super_admin
    """
    if not actor.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SCOPE_FORBIDDEN", "message": "Only super_admin can list companies"}
        )

    service = get_tenant_service(db)
    tenants = service.list_tenants(limit=200, offset=0)
    companies = [CompanyResponse.model_validate(t) for t in tenants]
    return CompanyListResponse(companies=companies, total=len(companies))


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    request: CreateCompanyRequest,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
):
    """
    建立新公司/租戶

    權限：僅限 super_admin
    """
    if not actor.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SCOPE_FORBIDDEN", "message": "Only super_admin can create companies"}
        )

    service = get_tenant_service(db)
    try:
        tenant = service.create_tenant(
            tenant_id=request.id,
            name=request.name,
            timezone=request.timezone,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DUPLICATE_COMPANY", "message": str(e)}
        )

    return CompanyResponse.model_validate(tenant)


# ── WP-11-04A: Entitlement management endpoints ───────────────────────

@router.get("/{company_id}/entitlements", response_model=CompanyEntitlementsResponse)
def get_company_entitlements(
    company_id: str,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
):
    """
    列出公司的所有 entitlements

    權限：
    - super_admin: 可查看任意公司
    - customer_service: 只能查看被指派的公司
    - company_user: 只能查看所屬公司
    """
    try:
        service = get_entitlement_service(db)
        result = service.list_company_entitlements(actor, company_id)
        return CompanyEntitlementsResponse(**result)
    except ScopeError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SCOPE_FORBIDDEN", "company_id": company_id, "message": str(e)}
        )


@router.patch("/{company_id}/entitlements", response_model=EntitlementResponse)
def update_company_entitlement(
    company_id: str,
    request: UpdateEntitlementRequest,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
):
    """
    更新單一 feature 的啟用狀態

    權限：只有 super_admin 可以修改
    """
    try:
        service = get_entitlement_service(db)
        result = service.update_entitlement(
            actor,
            company_id,
            request.feature_key,
            request.enabled
        )
        return EntitlementResponse(**result)
    except ScopeError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SCOPE_FORBIDDEN", "company_id": company_id, "message": str(e)}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{company_id}/entitlements/apply-plan", response_model=ApplyPlanResponse)
def apply_plan_defaults(
    company_id: str,
    request: ApplyPlanRequest,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
):
    """
    批次套用 plan 的預設 entitlements

    權限：只有 super_admin 可以執行
    """
    try:
        service = get_entitlement_service(db)
        result = service.apply_plan_defaults(actor, company_id, request.plan_code)
        return ApplyPlanResponse(**result)
    except ScopeError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SCOPE_FORBIDDEN", "company_id": company_id, "message": str(e)}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ── WP-S1-09C: Admin Onboarding endpoint ─────────────────────────────

from app.modules.tenants.schemas import (
    AdminOnboardingRequest,
    AdminOnboardingResponse,
    OnboardingCompanyResult,
    OnboardingUserResult,
    OnboardingMembershipResult,
)
from app.modules.tenants.service import get_onboarding_service
from sqlalchemy.exc import IntegrityError


@router.post(
    "/onboarding",
    response_model=AdminOnboardingResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["admin", "onboarding"],
)
def admin_onboard(
    request: AdminOnboardingRequest,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
):
    """
    建立公司 + 初始使用者 + Membership（原子操作）

    此 endpoint 由 super_admin 呼叫，一次完成：
    1. 建立 company (tenant)
    2. 建立 global user
    3. 建立 user-company membership (含登入憑證與角色)

    任何步驟失敗都會整體 rollback，不留下髒資料。

    權限：僅限 super_admin
    """
    if not actor.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SCOPE_FORBIDDEN", "message": "Only super_admin can perform onboarding"},
        )

    svc = get_onboarding_service(db)
    try:
        result = svc.onboard(
            company_id=request.company.id,
            company_name=request.company.name,
            company_timezone=request.company.timezone,
            user_display_name=request.initial_user.display_name,
            user_login_username=request.initial_user.login_username,
            user_password=request.initial_user.password,
            user_email=request.initial_user.email,
            user_role_id=request.initial_user.role_id,
        )
    except ValueError as e:
        msg = str(e)
        if msg.startswith("DUPLICATE_COMPANY"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "DUPLICATE_COMPANY", "message": msg},
            )
        if msg.startswith("DUPLICATE_LOGIN_USERNAME"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "DUPLICATE_LOGIN_USERNAME", "message": msg},
            )
        if msg.startswith("INVALID_ROLE"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "INVALID_ROLE", "message": msg},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ONBOARDING_ERROR", "message": msg},
        )
    except IntegrityError as e:
        db.rollback()
        err_str = str(e.orig) if hasattr(e, "orig") else str(e)
        if "uq_memberships_company_login" in err_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "DUPLICATE_LOGIN_USERNAME", "message": "Login username already exists in this company"},
            )
        if "tenants_pkey" in err_str or "duplicate key" in err_str.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "DUPLICATE_COMPANY", "message": "Company ID already exists"},
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "INTEGRITY_ERROR", "message": "Data conflict: " + err_str[:200]},
        )

    company = result["company"]
    user = result["user"]
    membership = result["membership"]

    return AdminOnboardingResponse(
        company=OnboardingCompanyResult.model_validate(company),
        user=OnboardingUserResult(
            id=str(user.id),
            display_name=user.display_name,
            email=user.email,
        ),
        membership=OnboardingMembershipResult(
            id=str(membership.id),
            user_id=str(membership.user_id),
            company_id=membership.company_id,
            role_id=membership.role_id,
            login_username=membership.login_username,
        ),
    )
