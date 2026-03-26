"""Tenants API – router aggregator

WP-11-04A: Added CompanyEntitlement management endpoints
WP-S1-09A: Added GET /api/admin/companies and POST /api/admin/companies

This file owns the shared router and the Companies CRUD endpoints.
Domain-specific endpoints are registered via register_routes() from sub-modules:
  - api_entitlements.py  (WP-11-04A)
  - api_onboarding.py    (WP-S1-09C)
  - api_members.py       (WP-S1-10B/10C/10D)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.scope import Actor, ScopeError, assert_company_scope
from app.core.dependencies import get_current_actor
from app.modules.tenants.service import get_tenant_service
from app.modules.tenants.schemas_companies import (
    CreateCompanyRequest,
    UpdateCompanyRequest,
    CompanyResponse,
    CompanyListResponse,
)

router = APIRouter(prefix="/api/admin/companies", tags=["admin", "entitlements"])


def _assert_admin_company_access(actor: Actor, company_id: str, db: Session) -> None:
    """Authorize admin access with company scope boundary.

    - super_admin: any company
    - company_admin/hr_manager: own active company only
    """
    if actor.is_super_admin():
        return

    if not actor.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SCOPE_FORBIDDEN", "message": "Only super_admin, company_admin, or hr_manager can access this endpoint"}
        )

    try:
        assert_company_scope(actor, company_id, db)
    except ScopeError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SCOPE_FORBIDDEN", "message": "company_admin/hr_manager can only operate within their own company scope"}
        )


# ── WP-S1-09A: Company management endpoints (super_admin only) ────────

@router.get("", response_model=CompanyListResponse)
def list_companies(
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
):
    """
    列出公司/租戶

    權限：
    - super_admin：可列出全部公司
    - company_admin/hr_manager：僅可列出自己 active company
    """
    service = get_tenant_service(db)

    if actor.is_super_admin():
        tenants = service.list_tenants(limit=200, offset=0)
        companies = [CompanyResponse.model_validate(t) for t in tenants]
        return CompanyListResponse(companies=companies, total=len(companies))

    if not actor.is_admin() or not actor.active_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SCOPE_FORBIDDEN", "message": "Only super_admin, company_admin, or hr_manager can list companies"}
        )

    _assert_admin_company_access(actor, actor.active_company_id, db)

    tenant = service.get_tenant(actor.active_company_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COMPANY_NOT_FOUND", "message": f"Company {actor.active_company_id!r} not found"}
        )

    company = CompanyResponse.model_validate(tenant)
    return CompanyListResponse(companies=[company], total=1)


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


# ── S1-11A: Company detail / update endpoints (super_admin only) ────

@router.get('/{company_id}', response_model=CompanyResponse)
def get_company(
    company_id: str,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
):
    """
    取得單一公司詳情

    權限：
    - super_admin：可查看任意公司
    - company_admin/hr_manager：僅可查看自己公司
    """
    _assert_admin_company_access(actor, company_id, db)

    service = get_tenant_service(db)
    tenant = service.get_tenant(company_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COMPANY_NOT_FOUND", "message": f"Company {company_id!r} not found"}
        )
    return CompanyResponse.model_validate(tenant)


@router.patch('/{company_id}', response_model=CompanyResponse)
def update_company(
    company_id: str,
    request: UpdateCompanyRequest,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
):
    """
    更新公司基本資訊（name / timezone / is_active）

    權限：
    - super_admin：可更新任意公司
    - company_admin/hr_manager：僅可更新自己公司
    """
    _assert_admin_company_access(actor, company_id, db)

    service = get_tenant_service(db)
    if not service.tenant_exists(company_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COMPANY_NOT_FOUND", "message": f"Company {company_id!r} not found"}
        )

    updates = request.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "NO_FIELDS", "message": "At least one field must be provided"}
        )

    tenant = service.update_tenant(company_id, **updates)
    return CompanyResponse.model_validate(tenant)


# ── Register domain-specific endpoints ───────────────────────────────

from app.modules.tenants.api_entitlements import register_routes as _reg_entitlements
from app.modules.tenants.api_onboarding import register_routes as _reg_onboarding
from app.modules.tenants.api_members import register_routes as _reg_members

_reg_entitlements(router)
_reg_onboarding(router)
_reg_members(router)
