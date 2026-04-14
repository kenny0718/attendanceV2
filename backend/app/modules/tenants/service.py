"""Tenants services

Service layer for companies, onboarding, entitlements, and members.
"""

from __future__ import annotations

import base64
import logging
import uuid
from types import SimpleNamespace
from typing import Any, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.features import FeatureKeys, PLAN_DEFAULTS
from app.core.scope import Actor, ScopeError, assert_company_scope
from app.core.security.password import hash_password
from app.modules.auth.models import Membership as MembershipModel
from app.modules.auth.models import Role as RoleModel
from app.modules.auth.models import User as UserModel
from app.modules.auth.repo import AuthRepository
from app.modules.tenants.models import Tenant as TenantModel
from app.modules.tenants.repo import CompanyEntitlementRepository, TenantRepository

logger = logging.getLogger(__name__)


class TenantService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TenantRepository(db)

    def create_tenant(
        self,
        tenant_id: str,
        name: str,
        timezone: str = "UTC",
        is_active: bool = True,
        tax_id: str | None = None,
        display_name: str | None = None,
        owner_name: str | None = None,
        registered_address: str | None = None,
        contact_address: str | None = None,
        contact_phone: str | None = None,
        contact_email: str | None = None,
    ):
        if self.repo.exists(tenant_id):
            raise ValueError(f"Tenant {tenant_id!r} already exists")
        if tax_id and self.repo.tax_id_exists(tax_id):
            raise ValueError(f"Tax ID {tax_id!r} already exists")
        return self.repo.create(
            tenant_id=tenant_id,
            name=name,
            timezone=timezone,
            is_active=is_active,
            tax_id=tax_id,
            display_name=display_name,
            owner_name=owner_name,
            registered_address=registered_address,
            contact_address=contact_address,
            contact_phone=contact_phone,
            contact_email=contact_email,
        )

    def get_tenant(self, tenant_id: str):
        return self.repo.get_by_id_legacy_compatible(tenant_id)

    def list_tenants(self, limit: int = 50, offset: int = 0):
        return self.repo.list_all_legacy_compatible(limit=limit, offset=offset)

    def update_tenant(self, tenant_id: str, **fields):
        tax_id = fields.get("tax_id")
        if tax_id and self.repo.tax_id_exists(tax_id, exclude_tenant_id=tenant_id):
            raise ValueError(f"Tax ID {tax_id!r} already exists")
        return self.repo.update(tenant_id, **fields)

    def deactivate_tenant(self, tenant_id: str):
        return self.repo.update(tenant_id, is_active=False)

    def activate_tenant(self, tenant_id: str):
        return self.repo.update(tenant_id, is_active=True)

    def tenant_exists(self, tenant_id: str) -> bool:
        return self.repo.exists(tenant_id)

    def tenant_is_active(self, tenant_id: str) -> bool:
        return self.repo.is_active(tenant_id)

    def resolve_company(self, company_input: str):
        company_key = company_input.strip()
        if not company_key:
            return None

        def _to_company_ref(row):
            if row is None:
                return None
            return SimpleNamespace(
                id=row.id,
                name=row.name,
                tax_id=row.tax_id,
                is_active=row.is_active,
            )

        tenant = (
            self.db.query(
                TenantModel.id,
                TenantModel.name,
                TenantModel.tax_id,
                TenantModel.is_active,
            )
            .filter(TenantModel.id == company_key)
            .first()
        )
        if tenant is not None:
            return _to_company_ref(tenant)

        tenant = (
            self.db.query(
                TenantModel.id,
                TenantModel.name,
                TenantModel.tax_id,
                TenantModel.is_active,
            )
            .filter(TenantModel.tax_id == company_key)
            .first()
        )
        return _to_company_ref(tenant)

    def get_company_detail(self, company_id: str) -> Optional[dict[str, Any]]:
        company = self.repo.get_by_id_legacy_compatible(company_id)
        if company is None:
            return None
        return {
            "company": company,
            "member_summary": self.repo.get_member_summary(company_id),
        }

    def lookup_company_by_tax_id(self, tax_id: str) -> dict[str, Any]:
        return {
            "tax_id": tax_id,
            "name": None,
            "owner_name": None,
            "registered_address": None,
            "found": False,
        }

    def upload_company_logo(
        self,
        company_id: str,
        filename: str,
        content_type: str,
        content_base64: str,
    ) -> dict[str, Any]:
        tenant = self.repo.get_by_id(company_id)
        if tenant is None:
            raise FileNotFoundError(company_id)

        allowed_types = {"image/png", "image/jpeg", "image/jpg"}
        if content_type not in allowed_types:
            raise ValueError("Unsupported content_type")

        try:
            base64.b64decode(content_base64, validate=True)
        except Exception as exc:  # pragma: no cover
            raise ValueError("Invalid base64 content") from exc

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
        logo_url = f"/static/company-logos/{company_id}.{ext}"
        tenant = self.repo.update(company_id, logo_url=logo_url)
        return {"company_id": company_id, "logo_url": tenant.logo_url}

    def delete_company_logo(self, company_id: str) -> dict[str, Any]:
        tenant = self.repo.get_by_id(company_id)
        if tenant is None:
            raise FileNotFoundError(company_id)
        self.repo.update(company_id, logo_url=None)
        return {"company_id": company_id, "logo_url": None}

    def create_member(
        self,
        company_id: str,
        display_name: str,
        password: str,
        role_id: str,
        login_username: str,
        email: Optional[str] = None,
        uses_schedule: bool = False,
    ) -> dict[str, Any]:
        if not self.repo.exists(company_id):
            raise ValueError("COMPANY_NOT_FOUND")

        role = self.db.query(RoleModel).filter(RoleModel.id == role_id).first()
        if role is None:
            raise ValueError(f"INVALID_ROLE: role '{role_id}' does not exist")

        auth_repo = AuthRepository(self.db)
        try:
            user = auth_repo.create_user_no_commit(
                display_name=display_name,
                plain_password=password,
                email=email,
            )
            membership = auth_repo.create_membership_no_commit(
                user_id=user.id,
                company_id=company_id,
                role_id=role_id,
                login_username=login_username,
                login_email=email,
                uses_schedule=uses_schedule,
            )
            self.db.commit()
            self.db.refresh(user)
            self.db.refresh(membership)
        except IntegrityError as e:
            self.db.rollback()
            err_str = str(e.orig) if hasattr(e, "orig") else str(e)
            if "uq_memberships_company_login" in err_str:
                raise ValueError("DUPLICATE_LOGIN_USERNAME")
            if "uq_memberships_user_company" in err_str:
                raise ValueError("DUPLICATE_MEMBERSHIP")
            raise ValueError("INTEGRITY_ERROR: " + err_str[:200])

        return {"user": user, "membership": membership}

    def update_member(self, membership_id: str, company_id: str, **fields) -> dict[str, Any]:
        if not self.repo.exists(company_id):
            raise ValueError("COMPANY_NOT_FOUND")
        if not fields:
            raise ValueError("NO_FIELDS_TO_UPDATE")

        try:
            membership_uuid = uuid.UUID(membership_id)
        except ValueError as exc:
            raise ValueError("INVALID_MEMBERSHIP_ID") from exc

        membership = (
            self.db.query(MembershipModel)
            .filter(MembershipModel.id == membership_uuid, MembershipModel.company_id == company_id)
            .first()
        )
        if membership is None:
            raise ValueError("MEMBERSHIP_NOT_FOUND")

        user = self.db.query(UserModel).filter(UserModel.id == membership.user_id).first()
        if user is None:
            raise ValueError("MEMBERSHIP_NOT_FOUND")

        role_id = fields.get("role_id")
        if role_id is not None:
            role = self.db.query(RoleModel).filter(RoleModel.id == role_id).first()
            if role is None:
                raise ValueError(f"INVALID_ROLE: role '{role_id}' does not exist")
            membership.role_id = role_id

        if "display_name" in fields:
            user.display_name = fields["display_name"]
        if "email" in fields:
            user.email = fields["email"]
        if "login_username" in fields:
            membership.login_username = fields["login_username"]
        if "uses_schedule" in fields:
            membership.uses_schedule = fields["uses_schedule"]

        try:
            self.db.commit()
            self.db.refresh(user)
            self.db.refresh(membership)
        except IntegrityError as exc:
            self.db.rollback()
            err_str = str(exc.orig) if hasattr(exc, "orig") else str(exc)
            if "uq_memberships_company_login" in err_str:
                raise ValueError("DUPLICATE_LOGIN_USERNAME")
            raise ValueError("INTEGRITY_ERROR")

        return {"user": user, "membership": membership}

    def reset_member_password(self, membership_id: str, company_id: str, new_plain_password: str) -> dict[str, Any]:
        if not self.repo.exists(company_id):
            raise ValueError("COMPANY_NOT_FOUND")
        if len(new_plain_password) < 6:
            raise ValueError("PASSWORD_TOO_SHORT")

        try:
            membership_uuid = uuid.UUID(membership_id)
        except ValueError as exc:
            raise ValueError("INVALID_MEMBERSHIP_ID") from exc

        membership = (
            self.db.query(MembershipModel)
            .filter(MembershipModel.id == membership_uuid, MembershipModel.company_id == company_id)
            .first()
        )
        if membership is None:
            raise ValueError("MEMBERSHIP_NOT_FOUND")

        user = self.db.query(UserModel).filter(UserModel.id == membership.user_id).first()
        if user is None:
            raise ValueError("MEMBERSHIP_NOT_FOUND")

        user.password_hash = hash_password(new_plain_password)
        self.db.commit()
        self.db.refresh(user)

        return {"membership_id": str(membership.id), "user_id": str(user.id)}


class EntitlementService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CompanyEntitlementRepository(db)
        self.tenant_repo = TenantRepository(db)

    def list_company_entitlements(self, actor: Actor, company_id: str) -> dict[str, Any]:
        assert_company_scope(actor, company_id, self.db)
        if not self.tenant_repo.exists(company_id):
            raise ValueError(f"COMPANY_NOT_FOUND: {company_id}")
        return {
            "company_id": company_id,
            "entitlements": self.repo.get_all_entitlements(company_id),
        }

    def update_entitlement(self, actor: Actor, company_id: str, feature_key: str, enabled: bool) -> dict[str, Any]:
        if not actor.is_super_admin():
            raise ScopeError("Only super_admin can update entitlements", company_id=company_id)
        if not self.tenant_repo.exists(company_id):
            raise ValueError(f"COMPANY_NOT_FOUND: {company_id}")

        FeatureKeys.validate(feature_key)
        entitlement = self.repo.upsert_entitlement(company_id, feature_key, enabled, actor.user_id)
        return {
            "company_id": entitlement.company_id,
            "feature_key": entitlement.feature_key,
            "enabled": entitlement.enabled,
            "updated_by": str(entitlement.updated_by_user_id) if entitlement.updated_by_user_id else None,
            "updated_at": entitlement.updated_at,
        }

    def apply_plan_defaults(self, actor: Actor, company_id: str, plan_code: str) -> dict[str, Any]:
        if not actor.is_super_admin():
            raise ScopeError("Only super_admin can apply plan defaults", company_id=company_id)
        if not self.tenant_repo.exists(company_id):
            raise ValueError(f"COMPANY_NOT_FOUND: {company_id}")
        if plan_code not in PLAN_DEFAULTS:
            raise ValueError(f"Unknown plan code: {plan_code}")

        updated_count = 0
        for feature_key, enabled in PLAN_DEFAULTS[plan_code].items():
            self.repo.upsert_entitlement(company_id, feature_key, enabled, actor.user_id)
            updated_count += 1

        return {
            "company_id": company_id,
            "plan_code": plan_code,
            "updated_count": updated_count,
        }


class OnboardingService:
    def __init__(self, db: Session):
        self.db = db
        self.tenant_service = TenantService(db)
        self.auth_repo = AuthRepository(db)

    def onboard(
        self,
        company_id: str,
        company_name: str,
        company_timezone: str,
        company_tax_id: str | None,
        display_name: str | None,
        owner_name: str | None,
        registered_address: str | None,
        contact_address: str | None,
        contact_phone: str | None,
        contact_email: str | None,
        user_display_name: str,
        user_login_username: str,
        user_password: str,
        user_email: str | None,
        user_role_id: str,
    ) -> dict[str, Any]:
        if self.tenant_service.tenant_exists(company_id):
            raise ValueError(f"DUPLICATE_COMPANY: company '{company_id}' already exists")
        if company_tax_id and self.tenant_service.repo.tax_id_exists(company_tax_id):
            raise ValueError(f"DUPLICATE_TAX_ID: tax_id '{company_tax_id}' already exists")

        role = self.db.query(RoleModel).filter(RoleModel.id == user_role_id).first()
        if role is None:
            raise ValueError(f"INVALID_ROLE: role '{user_role_id}' does not exist")

        try:
            company = self.tenant_service.repo.create(
                tenant_id=company_id,
                name=company_name,
                timezone=company_timezone,
                is_active=True,
                tax_id=company_tax_id,
                display_name=display_name,
                owner_name=owner_name,
                registered_address=registered_address,
                contact_address=contact_address,
                contact_phone=contact_phone,
                contact_email=contact_email,
            )
            user = self.auth_repo.create_user_no_commit(
                display_name=user_display_name,
                plain_password=user_password,
                email=user_email,
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
        except IntegrityError as exc:
            self.db.rollback()
            err_str = str(exc.orig) if hasattr(exc, "orig") else str(exc)
            if "uq_memberships_company_login" in err_str:
                raise ValueError("DUPLICATE_LOGIN_USERNAME")
            if "tenants_pkey" in err_str or "duplicate key" in err_str.lower():
                raise ValueError("DUPLICATE_COMPANY")
            raise

        return {
            "company": company,
            "user": user,
            "membership": membership,
        }


def get_tenant_service(db: Session) -> TenantService:
    return TenantService(db)


def get_entitlement_service(db: Session) -> EntitlementService:
    return EntitlementService(db)


def get_onboarding_service(db: Session) -> OnboardingService:
    return OnboardingService(db)
