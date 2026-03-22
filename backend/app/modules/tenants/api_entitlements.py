"""Tenants – Entitlements API endpoints (split from api.py, WP-11-04A)"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.scope import Actor, ScopeError
from app.core.dependencies import get_current_actor
from app.modules.tenants.service import get_entitlement_service
from app.modules.tenants.schemas_entitlements import (
    UpdateEntitlementRequest,
    ApplyPlanRequest,
    EntitlementResponse,
    CompanyEntitlementsResponse,
    ApplyPlanResponse,
)


def register_routes(router: APIRouter) -> None:
    """Register all Entitlement endpoints onto the given router."""

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
