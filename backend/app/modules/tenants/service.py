"""Tenants Service (Business Logic Layer)

WP-11-04A: Added CompanyEntitlement service methods
"""

import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.modules.tenants.repo import CompanyEntitlementRepository, TenantRepository
from app.modules.tenants.models import Tenant
from app.core.scope import Actor, ScopeError, assert_company_scope
from app.core.features import FeatureKeys, PLAN_DEFAULTS
from app.core.feature_service import get_feature_service

logger = logging.getLogger(__name__)


class TenantService:
    """Tenant business logic layer"""

    def __init__(self, db: Session):
        self.repo = TenantRepository(db)

    def create_tenant(
        self,
        tenant_id: str,
        name: str,
        timezone: str = "UTC",
        is_active: bool = True,
        tax_id: Optional[str] = None,
    ) -> Tenant:
        if self.repo.exists(tenant_id):
            raise ValueError(f"Tenant {tenant_id} already exists")
        if tax_id and self.repo.exists_by_tax_id(tax_id):
            raise ValueError(f"Tax ID {tax_id} already exists")

        return self.repo.create(
            tenant_id=tenant_id,
            name=name,
            timezone=timezone,
            is_active=is_active,
            tax_id=tax_id,
        )

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self.repo.get_by_id(tenant_id)

    def list_tenants(self, limit: int = 50, offset: int = 0) -> List[Tenant]:
        return self.repo.list_all(limit=limit, offset=offset)

    def update_tenant(self, tenant_id: str, **fields) -> Optional[Tenant]:
        if fields.get("tax_id") and self.repo.exists_by_tax_id(fields["tax_id"], exclude_tenant_id=tenant_id):
            raise ValueError(f"Tax ID {fields['tax_id']} already exists")
        return self.repo.update(tenant_id, **fields)

    def deactivate_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self.repo.update(tenant_id, is_active=False)

    def activate_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self.repo.update(tenant_id, is_active=True)

    def tenant_exists(self, tenant_id: str) -> bool:
        return self.repo.exists(tenant_id)

    def tenant_is_active(self, tenant_id: str) -> bool:
        return self.repo.is_active(tenant_id)

    def resolve_company(self, company_input: str) -> Optional[Tenant]:
        tenant = self.repo.get_by_id(company_input)
        if tenant:
            return tenant
        return self.repo.get_by_tax_id(company_input)

    def update_member(self, membership_id: str, company_id: str, **fields) -> dict:
        from app.modules.auth.models import Membership as MembershipModel, Role as RoleModel, User as UserModel
        import uuid as _uuid

        db = self.repo.db

        try:
            mem_uuid = _uuid.UUID(membership_id)
        except ValueError:
            raise ValueError("INVALID_MEMBERSHIP_ID")

        membership = db.query(MembershipModel).filter(
            MembershipModel.id == mem_uuid,
            MembershipModel.company_id == company_id,
        ).first()
        if membership is None:
            raise ValueError("MEMBERSHIP_NOT_FOUND")

        user = db.query(UserModel).filter(UserModel.id == membership.user_id).first()
        if user is None:
            raise ValueError("USER_NOT_FOUND")

        if "role_id" in fields and fields["role_id"] is not None:
            role = db.query(RoleModel).filter(RoleModel.id == fields["role_id"]).first()
            if role is None:
                raise ValueError(f"INVALID_ROLE: role '{fields['role_id']}' does not exist")
            membership.role_id = fields["role_id"]

        if "display_name" in fields and fields["display_name"] is not None:
            user.display_name = fields["display_name"]

        if "email" in fields:
            user.email = fields["email"]

        if "login_username" in fields and fields["login_username"] is not None:
            new_username = fields["login_username"]
            conflict = db.query(MembershipModel).filter(
                MembershipModel.company_id == company_id,
                MembershipModel.login_username == new_username,
                MembershipModel.id != mem_uuid,
            ).first()
            if conflict is not None:
                raise ValueError("DUPLICATE_LOGIN_USERNAME")
            membership.login_username = new_username

        if "uses_schedule" in fields and fields["uses_schedule"] is not None:
            membership.uses_schedule = fields["uses_schedule"]

        from sqlalchemy.exc import IntegrityError as _IntegrityError

        try:
            db.commit()
        except _IntegrityError as e:
            db.rollback()
            err_str = str(e.orig) if hasattr(e, "orig") else str(e)
            if "uq_memberships_company_login" in err_str:
                raise ValueError("DUPLICATE_LOGIN_USERNAME")
            raise

        db.refresh(user)
        db.refresh(membership)
        return {"user": user, "membership": membership}

    def reset_member_password(self, membership_id: str, company_id: str, new_plain_password: str) -> dict:
        from app.modules.auth.models import Membership as MembershipModel, User as UserModel
        from app.modules.auth.repo import AuthRepository
        import uuid as _uuid

        db = self.repo.db

        if not new_plain_password or len(new_plain_password) < 6:
            raise ValueError("PASSWORD_TOO_SHORT: password must be at least 6 characters")

        try:
            mem_uuid = _uuid.UUID(membership_id)
        except ValueError:
            raise ValueError("INVALID_MEMBERSHIP_ID")

        membership = db.query(MembershipModel).filter(
            MembershipModel.id == mem_uuid,
            MembershipModel.company_id == company_id,
        ).first()
        if membership is None:
            raise ValueError("MEMBERSHIP_NOT_FOUND")

        user = db.query(UserModel).filter(UserModel.id == membership.user_id).first()
        if user is None:
            raise ValueError("USER_NOT_FOUND")

        auth_repo = AuthRepository(db)
        auth_repo.update_password(user, new_plain_password)
        return {"membership_id": str(membership.id), "user_id": str(user.id)}


class CompanyEntitlementService:
    """Company Entitlement business logic layer (WP-11-04A)"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = CompanyEntitlementRepository(db)
        self.feature_service = get_feature_service(db)

    def list_company_entitlements(self, actor: Actor, company_id: str) -> Dict:
        assert_company_scope(actor, company_id, self.db)
        entitlements = self.repo.get_all_entitlements(company_id)
        result = {}
        for feature_key in FeatureKeys.all_keys():
            result[feature_key] = entitlements.get(feature_key, False)
        return {"company_id": company_id, "entitlements": result}

    def update_entitlement(self, actor: Actor, company_id: str, feature_key: str, enabled: bool) -> Dict:
        if not actor.is_super_admin():
            raise ScopeError("Only super_admin can modify entitlements")

        FeatureKeys.validate(feature_key)
        entitlement = self.repo.upsert_entitlement(
            company_id=company_id,
            feature_key=feature_key,
            enabled=enabled,
            updated_by_user_id=actor.user_id,
        )
        self.feature_service.clear_cache(company_id, feature_key)
        return {
            "company_id": company_id,
            "feature_key": feature_key,
            "enabled": enabled,
            "updated_by": str(actor.user_id),
            "updated_at": entitlement.updated_at.isoformat(),
        }

    def apply_plan_defaults(self, actor: Actor, company_id: str, plan_code: str) -> Dict:
        if not actor.is_super_admin():
            raise ScopeError("Only super_admin can apply plan defaults")

        if plan_code not in PLAN_DEFAULTS:
            raise ValueError(
                f"Unknown plan_code: {plan_code}. Valid plans: {', '.join(PLAN_DEFAULTS.keys())}"
            )

        defaults = PLAN_DEFAULTS[plan_code]
        updated_count = 0
        for feature_key, enabled in defaults.items():
            self.repo.upsert_entitlement(
                company_id=company_id,
                feature_key=feature_key,
                enabled=enabled,
                updated_by_user_id=actor.user_id,
            )
            updated_count += 1

        self.feature_service.clear_cache(company_id)
        return {"company_id": company_id, "plan_code": plan_code, "updated_count": updated_count}


class OnboardingService:
    """Admin Onboarding orchestration service."""

    def __init__(self, db: Session):
        self.db = db
        self.tenant_repo = TenantRepository(db)
        from app.modules.auth.repo import AuthRepository
        self.auth_repo = AuthRepository(db)

    def onboard(
        self,
        company_id: str,
        company_name: str,
        company_timezone: str,
        user_display_name: str,
        user_login_username: str,
        user_password: str,
        user_email: Optional[str],
        user_role_id: str,
        company_tax_id: Optional[str] = None,
    ) -> dict:
        if self.tenant_repo.exists(company_id):
            raise ValueError(f"DUPLICATE_COMPANY: company '{company_id}' already exists")
        if company_tax_id and self.tenant_repo.exists_by_tax_id(company_tax_id):
            raise ValueError(f"DUPLICATE_TAX_ID: tax_id '{company_tax_id}' already exists")

        from app.modules.auth.models import Role

        role = self.db.query(Role).filter(Role.id == user_role_id).first()
        if role is None:
            raise ValueError(f"INVALID_ROLE: role '{user_role_id}' does not exist")

        try:
            company = Tenant(
                id=company_id,
                name=company_name,
                tax_id=company_tax_id,
                timezone=company_timezone,
                is_active=True,
            )
            self.db.add(company)
            self.db.flush()

            user = self.auth_repo.create_user_no_commit(
                display_name=user_display_name,
                plain_password=user_password,
                email=user_email,
                must_change_password=False,
            )
            membership = self.auth_repo.create_membership_no_commit(
                user_id=user.id,
                company_id=company_id,
                role_id=user_role_id,
                login_username=user_login_username,
                login_email=user_email,
            )

            self.db.commit()
            self.db.refresh(company)
            self.db.refresh(user)
            self.db.refresh(membership)
        except Exception:
            self.db.rollback()
            raise

        return {"company": company, "user": user, "membership": membership}


def get_tenant_service(db: Session) -> TenantService:
    return TenantService(db)


def get_entitlement_service(db: Session) -> CompanyEntitlementService:
    return CompanyEntitlementService(db)


def get_onboarding_service(db: Session) -> OnboardingService:
    return OnboardingService(db)
