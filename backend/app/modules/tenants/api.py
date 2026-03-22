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


# ── WP-S1-10B: Admin read-only members endpoint ──────────────────────

from app.modules.tenants.schemas import CompanyMemberResponse, CompanyMembersResponse
from app.modules.auth.models import Membership as MembershipModel, User as UserModel


@router.get(
    "/{company_id}/members",
    response_model=CompanyMembersResponse,
    tags=["admin", "users"],
)
def list_company_members(
    company_id: str,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
):
    """
    List all members (users + memberships) for a company.

    Permission: super_admin only
    """
    if not actor.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SCOPE_FORBIDDEN", "message": "Only super_admin can view company members"},
        )

    # Verify company exists
    service = get_tenant_service(db)
    if not service.tenant_exists(company_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COMPANY_NOT_FOUND", "message": f"Company '{company_id}' not found"},
        )

    # Query memberships joined with users
    rows = (
        db.query(MembershipModel, UserModel)
        .join(UserModel, MembershipModel.user_id == UserModel.id)
        .filter(MembershipModel.company_id == company_id)
        .order_by(MembershipModel.created_at.asc())
        .all()
    )

    members = [
        CompanyMemberResponse(
            membership_id=str(m.id),
            user_id=str(m.user_id),
            company_id=m.company_id,
            role_id=m.role_id,
            login_username=m.login_username,
            membership_is_active=m.is_active,
            membership_created_at=m.created_at,
            display_name=u.display_name,
            email=u.email,
            user_is_active=u.is_active,
        )
        for m, u in rows
    ]

    return CompanyMembersResponse(
        company_id=company_id,
        members=members,
        total=len(members),
    )


# ── WP-S1-10C: Membership active toggle endpoint ─────────────────────

from app.modules.tenants.schemas import (
    ToggleMembershipActiveRequest,
    ToggleMembershipActiveResponse,
)
import uuid as _uuid


@router.patch(
    "/{company_id}/members/{membership_id}/active",
    response_model=ToggleMembershipActiveResponse,
    tags=["admin", "users"],
)
def toggle_membership_active(
    company_id: str,
    membership_id: str,
    request: ToggleMembershipActiveRequest,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
):
    """
    Toggle membership active state for a company member.

    Permission: super_admin only
    """
    if not actor.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SCOPE_FORBIDDEN", "message": "Only super_admin can toggle membership status"},
        )

    # Verify company exists
    tenant_svc = get_tenant_service(db)
    if not tenant_svc.tenant_exists(company_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COMPANY_NOT_FOUND", "message": f"Company '{company_id}' not found"},
        )

    # Fetch membership by ID
    try:
        mem_uuid = _uuid.UUID(membership_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_MEMBERSHIP_ID", "message": "membership_id must be a valid UUID"},
        )

    membership = db.query(MembershipModel).filter(
        MembershipModel.id == mem_uuid
    ).first()

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MEMBERSHIP_NOT_FOUND", "message": f"Membership '{membership_id}' not found"},
        )

    # Verify membership belongs to this company
    if membership.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "MEMBERSHIP_COMPANY_MISMATCH", "message": "Membership does not belong to this company"},
        )

    # Apply toggle
    membership.is_active = request.is_active
    db.commit()
    db.refresh(membership)

    return ToggleMembershipActiveResponse(
        membership_id=str(membership.id),
        company_id=membership.company_id,
        is_active=membership.is_active,
    )



# ── WP-S1-10D: Create Member endpoint ────────────────────────────────

from app.modules.tenants.schemas import CreateMemberRequest, CreateMemberResponse
from app.modules.auth.repo import AuthRepository
from sqlalchemy.exc import IntegrityError as _IntegrityError


@router.post(
    "/{company_id}/members",
    response_model=CreateMemberResponse,
    status_code=status.HTTP_201_CREATED,
    tags=['admin', 'users'],
)
def create_company_member(
    company_id: str,
    request: CreateMemberRequest,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
):
    if not actor.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={'code': 'SCOPE_FORBIDDEN', 'message': 'Only super_admin can add company members'},
        )

    tenant_svc = get_tenant_service(db)
    if not tenant_svc.tenant_exists(company_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'COMPANY_NOT_FOUND', 'message': f"Company '{company_id}' not found"},
        )

    from app.modules.auth.models import Role as _Role
    role = db.query(_Role).filter(_Role.id == request.role_id).first()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={'code': 'INVALID_ROLE', 'message': f"Role '{request.role_id}' does not exist"},
        )

    auth_repo = AuthRepository(db)
    try:
        # Use no-commit path so user + membership are in the same transaction.
        # If membership flush fails, the rollback removes the user too — no orphan.
        user = auth_repo.create_user_no_commit(
            display_name=request.display_name,
            plain_password=request.password,
            email=request.email,
        )
        membership = auth_repo.create_membership_no_commit(
            user_id=user.id,
            company_id=company_id,
            role_id=request.role_id,
            login_username=request.login_username,
            login_email=request.email,
        )
        # Single atomic commit — both user and membership persist together
        db.commit()
        db.refresh(user)
        db.refresh(membership)
    except _IntegrityError as e:
        db.rollback()
        err_str = str(e.orig) if hasattr(e, 'orig') else str(e)
        if 'uq_memberships_company_login' in err_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={'code': 'DUPLICATE_LOGIN_USERNAME', 'message': 'Login username already exists in this company'},
            )
        if 'uq_memberships_user_company' in err_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={'code': 'DUPLICATE_MEMBERSHIP', 'message': 'User already has membership in this company'},
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={'code': 'INTEGRITY_ERROR', 'message': 'Data conflict: ' + err_str[:200]},
        )

    return CreateMemberResponse(
        membership_id=str(membership.id),
        user_id=str(user.id),
        company_id=company_id,
        role_id=membership.role_id,
        login_username=membership.login_username,
        display_name=user.display_name,
        email=user.email,
        is_active=membership.is_active,
    )
