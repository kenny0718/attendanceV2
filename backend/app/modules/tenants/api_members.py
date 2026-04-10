"""Tenants – Members API endpoints (split from api.py, WP-S1-10B/10C/10D)"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import uuid as _uuid

from app.core.database import get_db
from app.core.scope import Actor, ScopeError, assert_company_scope
from app.core.dependencies import get_current_actor
from app.modules.tenants.service import get_tenant_service
from app.modules.tenants.schemas_members import (
    CompanyMemberResponse,
    CompanyMembersResponse,
    ToggleMembershipActiveRequest,
    ToggleMembershipActiveResponse,
    CreateMemberRequest,
    CreateMemberResponse,
    UpdateMemberRequest,
    UpdateMemberResponse,
    ResetMemberPasswordRequest,
    ResetMemberPasswordResponse,
)
from app.modules.auth.models import Membership as MembershipModel, User as UserModel, Role as RoleModel
from app.modules.auth.repo import AuthRepository


def _assert_admin_company_access(actor: Actor, company_id: str, db: Session) -> None:
    if actor.is_super_admin():
        return
    if not actor.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SCOPE_FORBIDDEN", "message": "Only super_admin, company_admin, or hr_manager can access members endpoints"},
        )
    try:
        assert_company_scope(actor, company_id, db)
    except ScopeError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SCOPE_FORBIDDEN", "message": "company_admin/hr_manager can only operate members within their own company scope"},
        )


def register_routes(router: APIRouter) -> None:
    @router.get("/{company_id}/members", response_model=CompanyMembersResponse, tags=["admin", "users"])
    def list_company_members(company_id: str, actor: Actor = Depends(get_current_actor), db: Session = Depends(get_db)):
        _assert_admin_company_access(actor, company_id, db)

        service = get_tenant_service(db)
        if not service.tenant_exists(company_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "COMPANY_NOT_FOUND", "message": f"Company '{company_id}' not found"})

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
                uses_schedule=m.uses_schedule,
                membership_created_at=m.created_at,
                display_name=u.display_name,
                email=u.email,
                user_is_active=u.is_active,
            )
            for m, u in rows
        ]

        return CompanyMembersResponse(company_id=company_id, members=members, total=len(members))

    @router.patch("/{company_id}/members/{membership_id}/active", response_model=ToggleMembershipActiveResponse, tags=["admin", "users"])
    def toggle_membership_active(company_id: str, membership_id: str, request: ToggleMembershipActiveRequest, actor: Actor = Depends(get_current_actor), db: Session = Depends(get_db)):
        _assert_admin_company_access(actor, company_id, db)

        tenant_svc = get_tenant_service(db)
        if not tenant_svc.tenant_exists(company_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "COMPANY_NOT_FOUND", "message": f"Company '{company_id}' not found"})

        try:
            mem_uuid = _uuid.UUID(membership_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "INVALID_MEMBERSHIP_ID", "message": "membership_id must be a valid UUID"})

        membership = db.query(MembershipModel).filter(MembershipModel.id == mem_uuid).first()
        if membership is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "MEMBERSHIP_NOT_FOUND", "message": f"Membership '{membership_id}' not found"})
        if membership.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "MEMBERSHIP_COMPANY_MISMATCH", "message": "Membership does not belong to this company"})

        membership.is_active = request.is_active
        db.commit()
        db.refresh(membership)

        return ToggleMembershipActiveResponse(membership_id=str(membership.id), company_id=membership.company_id, is_active=membership.is_active)

    @router.post("/{company_id}/members", response_model=CreateMemberResponse, status_code=status.HTTP_201_CREATED, tags=["admin", "users"])
    def create_company_member(company_id: str, request: CreateMemberRequest, actor: Actor = Depends(get_current_actor), db: Session = Depends(get_db)):
        _assert_admin_company_access(actor, company_id, db)

        tenant_svc = get_tenant_service(db)
        if not tenant_svc.tenant_exists(company_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "COMPANY_NOT_FOUND", "message": f"Company '{company_id}' not found"})

        role = db.query(RoleModel).filter(RoleModel.id == request.role_id).first()
        if role is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "INVALID_ROLE", "message": f"Role '{request.role_id}' does not exist"})

        auth_repo = AuthRepository(db)
        try:
            user = auth_repo.create_user_no_commit(display_name=request.display_name, plain_password=request.password, email=request.email)
            membership = auth_repo.create_membership_no_commit(
                user_id=user.id,
                company_id=company_id,
                role_id=request.role_id,
                login_username=request.login_username,
                login_email=request.email,
                uses_schedule=request.uses_schedule,
            )
            db.commit()
            db.refresh(user)
            db.refresh(membership)
        except IntegrityError as e:
            db.rollback()
            err_str = str(e.orig) if hasattr(e, 'orig') else str(e)
            if 'uq_memberships_company_login' in err_str:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "DUPLICATE_LOGIN_USERNAME", "message": "Login username already exists in this company"})
            if 'uq_memberships_user_company' in err_str:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "DUPLICATE_MEMBERSHIP", "message": "User already has membership in this company"})
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "INTEGRITY_ERROR", "message": "Data conflict: " + err_str[:200]})

        return CreateMemberResponse(
            membership_id=str(membership.id),
            user_id=str(user.id),
            company_id=company_id,
            role_id=membership.role_id,
            login_username=membership.login_username,
            uses_schedule=membership.uses_schedule,
            display_name=user.display_name,
            email=user.email,
            is_active=membership.is_active,
        )

    @router.patch("/{company_id}/members/{membership_id}", response_model=UpdateMemberResponse, tags=["admin", "users"])
    def update_company_member(company_id: str, membership_id: str, request: UpdateMemberRequest, actor: Actor = Depends(get_current_actor), db: Session = Depends(get_db)):
        _assert_admin_company_access(actor, company_id, db)

        tenant_svc = get_tenant_service(db)
        if not tenant_svc.tenant_exists(company_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "COMPANY_NOT_FOUND", "message": f"Company '{company_id}' not found"})

        update_fields = {}
        if request.display_name is not None:
            update_fields['display_name'] = request.display_name
        if request.role_id is not None:
            update_fields['role_id'] = request.role_id
        if 'email' in request.model_fields_set:
            update_fields['email'] = request.email
        if request.login_username is not None:
            update_fields['login_username'] = request.login_username
        if request.uses_schedule is not None:
            update_fields['uses_schedule'] = request.uses_schedule

        if not update_fields:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "NO_FIELDS_TO_UPDATE", "message": "At least one field must be provided"})

        try:
            result = tenant_svc.update_member(membership_id=membership_id, company_id=company_id, **update_fields)
        except ValueError as e:
            err = str(e)
            if 'MEMBERSHIP_NOT_FOUND' in err:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "MEMBERSHIP_NOT_FOUND", "message": f"Membership '{membership_id}' not found in company '{company_id}'"})
            if 'INVALID_ROLE' in err:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "INVALID_ROLE", "message": str(e)})
            if 'INVALID_MEMBERSHIP_ID' in err:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "INVALID_MEMBERSHIP_ID", "message": "membership_id must be a valid UUID"})
            if 'DUPLICATE_LOGIN_USERNAME' in err:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "DUPLICATE_LOGIN_USERNAME", "message": "此登入帳號在該公司已被使用，請換一個"})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"code": "INTERNAL_ERROR", "message": str(e)})

        user = result['user']
        membership = result['membership']
        return UpdateMemberResponse(
            membership_id=str(membership.id),
            user_id=str(user.id),
            company_id=membership.company_id,
            role_id=membership.role_id,
            display_name=user.display_name,
            email=user.email,
            login_username=membership.login_username,
            uses_schedule=membership.uses_schedule,
            membership_is_active=membership.is_active,
        )

    @router.patch("/{company_id}/members/{membership_id}/password", response_model=ResetMemberPasswordResponse, tags=["admin", "users"])
    def reset_member_password(company_id: str, membership_id: str, request: ResetMemberPasswordRequest, actor: Actor = Depends(get_current_actor), db: Session = Depends(get_db)):
        _assert_admin_company_access(actor, company_id, db)

        tenant_svc = get_tenant_service(db)
        if not tenant_svc.tenant_exists(company_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "COMPANY_NOT_FOUND", "message": f"Company '{company_id}' not found"})

        try:
            result = tenant_svc.reset_member_password(membership_id=membership_id, company_id=company_id, new_plain_password=request.new_password)
        except ValueError as e:
            err = str(e)
            if 'MEMBERSHIP_NOT_FOUND' in err:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "MEMBERSHIP_NOT_FOUND", "message": f"Membership '{membership_id}' not found in company '{company_id}'"})
            if 'PASSWORD_TOO_SHORT' in err:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "PASSWORD_TOO_SHORT", "message": "Password must be at least 6 characters"})
            if 'INVALID_MEMBERSHIP_ID' in err:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "INVALID_MEMBERSHIP_ID", "message": "membership_id must be a valid UUID"})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"})

        return ResetMemberPasswordResponse(membership_id=result['membership_id'], user_id=result['user_id'], message='密碼已成功重設')
