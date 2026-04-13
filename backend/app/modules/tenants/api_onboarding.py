"""Tenants – Onboarding API endpoint (split from api.py, WP-S1-09C)"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.scope import Actor
from app.core.dependencies import get_current_actor
from app.modules.tenants.service import get_onboarding_service
from app.modules.tenants.schemas_onboarding import (
    AdminOnboardingRequest,
    AdminOnboardingResponse,
    OnboardingCompanyResult,
    OnboardingUserResult,
    OnboardingMembershipResult,
)


def register_routes(router: APIRouter) -> None:
    """Register Onboarding endpoint onto the given router."""

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
                company_tax_id=request.company.tax_id,
                display_name=request.company.display_name,
                owner_name=request.company.owner_name,
                registered_address=request.company.registered_address,
                contact_address=request.company.contact_address,
                contact_phone=request.company.contact_phone,
                contact_email=request.company.contact_email,
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
            if msg.startswith("DUPLICATE_TAX_ID"):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"code": "DUPLICATE_TAX_ID", "message": msg},
                )
            if msg.startswith("INVALID_ROLE"):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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
