"""Tenants Repository (Data Access Layer)

WP-11-04A: Added CompanyEntitlement repository methods
"""

import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
import uuid
from datetime import datetime

from app.modules.auth.models import Membership
from app.modules.tenants.models import Tenant, CompanyEntitlement

logger = logging.getLogger(__name__)


class TenantRepository:
    """Tenant data access layer"""

    def __init__(self, db: Session):
        """Initialize Repository

        Args:
            db: SQLAlchemy Session
        """
        self.db = db
        self.model = Tenant

    def create(
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
        logo_url: str | None = None,
    ) -> Tenant:
        """Create a new tenant

        Args:
            tenant_id: Company ID (PK)
            name: Company name
            timezone: Company timezone (default: UTC)
            is_active: Active status (default: True)
            tax_id: Company tax ID (optional)

        Returns:
            Tenant: Created tenant
        """
        tenant = Tenant(
            id=tenant_id,
            name=name,
            tax_id=tax_id,
            display_name=display_name,
            owner_name=owner_name,
            registered_address=registered_address,
            contact_address=contact_address,
            contact_phone=contact_phone,
            contact_email=contact_email,
            logo_url=logo_url,
            timezone=timezone,
            is_active=is_active,
        )

        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)

        logger.info(f"Created tenant: id={tenant_id}, name={name}, tax_id={tax_id}")

        return tenant

    def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID

        Args:
            tenant_id: Company ID

        Returns:
            Tenant or None if not found
        """
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()

        logger.debug(f"Get tenant by id: {tenant_id}, found={tenant is not None}")

        return tenant

    def get_by_tax_id(self, tax_id: str) -> Optional[Tenant]:
        """Get tenant by tax ID."""
        tenant = self.db.query(Tenant).filter(Tenant.tax_id == tax_id).first()
        logger.debug(f"Get tenant by tax_id: {tax_id}, found={tenant is not None}")
        return tenant

    def list_all(self, limit: int = 50, offset: int = 0) -> List[Tenant]:
        """List all tenants (with pagination)

        Args:
            limit: Max number of results
            offset: Offset for pagination

        Returns:
            List[Tenant]: List of tenants
        """
        tenants = (
            self.db.query(Tenant)
            .order_by(Tenant.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        logger.debug(f"List tenants: limit={limit}, offset={offset}, count={len(tenants)}")

        return tenants

    def update(self, tenant_id: str, **fields) -> Optional[Tenant]:
        """Update tenant fields

        Args:
            tenant_id: Company ID
            **fields: Fields to update (name, is_active, timezone, tax_id)

        Returns:
            Tenant or None if not found
        """
        tenant = self.get_by_id(tenant_id)

        if not tenant:
            logger.warning(f"Update failed: tenant {tenant_id} not found")
            return None

        for key, value in fields.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)

        self.db.commit()
        self.db.refresh(tenant)

        logger.info(f"Updated tenant: id={tenant_id}, fields={list(fields.keys())}")

        return tenant

    def exists(self, tenant_id: str) -> bool:
        """Check if tenant exists

        Args:
            tenant_id: Company ID

        Returns:
            bool: True if exists
        """
        count = self.db.query(Tenant).filter(Tenant.id == tenant_id).count()
        return count > 0

    def exists_by_tax_id(self, tax_id: str, exclude_tenant_id: str | None = None) -> bool:
        """Check if tax ID already exists."""
        return self.tax_id_exists(tax_id, exclude_tenant_id)

    def tax_id_exists(self, tax_id: str, exclude_tenant_id: str | None = None) -> bool:
        """Check if tax ID already exists."""
        query = self.db.query(Tenant).filter(Tenant.tax_id == tax_id)
        if exclude_tenant_id is not None:
            query = query.filter(Tenant.id != exclude_tenant_id)
        return query.count() > 0

    def is_active(self, tenant_id: str) -> bool:
        """Check if tenant is active

        Args:
            tenant_id: Company ID

        Returns:
            bool: True if active (False if not found or inactive)
        """
        tenant = self.get_by_id(tenant_id)
        return tenant.is_active if tenant else False

    def get_member_summary(self, tenant_id: str) -> Dict[str, int | bool]:
        """Get admin-role summary for a tenant."""
        admin_roles = ("company_admin", "hr_manager")
        base_query = self.db.query(Membership).filter(Membership.company_id == tenant_id)
        admin_query = base_query.filter(Membership.role_id.in_(admin_roles))

        admin_count = admin_query.count()
        active_admin_count = admin_query.filter(Membership.is_active.is_(True)).count()
        has_company_admin = base_query.filter(Membership.role_id == "company_admin").count() > 0
        has_hr_manager = base_query.filter(Membership.role_id == "hr_manager").count() > 0

        return {
            "admin_count": admin_count,
            "active_admin_count": active_admin_count,
            "has_company_admin": has_company_admin,
            "has_hr_manager": has_hr_manager,
        }


class CompanyEntitlementRepository:
    """Company Entitlement data access layer (WP-11-04A)"""

    def __init__(self, db: Session):
        """Initialize Repository

        Args:
            db: SQLAlchemy Session
        """
        self.db = db
        self.model = CompanyEntitlement

    def get_entitlement(self, company_id: str, feature_key: str) -> Optional[CompanyEntitlement]:
        """Get entitlement by company_id and feature_key

        Args:
            company_id: Company ID
            feature_key: Feature key

        Returns:
            CompanyEntitlement or None if not found
        """
        return self.db.query(CompanyEntitlement).filter(
            CompanyEntitlement.company_id == company_id,
            CompanyEntitlement.feature_key == feature_key,
        ).first()

    def get_all_entitlements(self, company_id: str) -> Dict[str, bool]:
        """Get all entitlements for a company

        Args:
            company_id: Company ID

        Returns:
            Dict[str, bool]: feature_key -> enabled mapping
        """
        results = self.db.query(CompanyEntitlement).filter(
            CompanyEntitlement.company_id == company_id
        ).all()

        return {ent.feature_key: ent.enabled for ent in results}

    def upsert_entitlement(
        self,
        company_id: str,
        feature_key: str,
        enabled: bool,
        updated_by_user_id: UUID,
    ) -> CompanyEntitlement:
        """Create or update entitlement

        Args:
            company_id: Company ID
            feature_key: Feature key
            enabled: Is enabled
            updated_by_user_id: Updated by user ID

        Returns:
            CompanyEntitlement: Created or updated entitlement
        """
        existing = self.get_entitlement(company_id, feature_key)

        if existing:
            existing.enabled = enabled
            existing.updated_by_user_id = updated_by_user_id
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            logger.info(f"Updated entitlement: company={company_id}, feature={feature_key}, enabled={enabled}")
            return existing
        else:
            entitlement = CompanyEntitlement(
                id=uuid.uuid4(),
                company_id=company_id,
                feature_key=feature_key,
                enabled=enabled,
                updated_by_user_id=updated_by_user_id,
            )
            self.db.add(entitlement)
            self.db.commit()
            self.db.refresh(entitlement)
            logger.info(f"Created entitlement: company={company_id}, feature={feature_key}, enabled={enabled}")
            return entitlement

    def delete_entitlement(self, company_id: str, feature_key: str) -> bool:
        """Delete entitlement

        Args:
            company_id: Company ID
            feature_key: Feature key

        Returns:
            bool: True if deleted
        """
        result = self.db.query(CompanyEntitlement).filter(
            CompanyEntitlement.company_id == company_id,
            CompanyEntitlement.feature_key == feature_key,
        ).delete()

        self.db.commit()

        logger.info(f"Deleted entitlement: company={company_id}, feature={feature_key}, deleted={result > 0}")

        return result > 0
