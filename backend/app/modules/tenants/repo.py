"""Tenants Repository (Data Access Layer)"""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from app.modules.tenants.models import Tenant

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
        is_active: bool = True
    ) -> Tenant:
        """Create a new tenant
        
        Args:
            tenant_id: Company ID (PK)
            name: Company name
            timezone: Company timezone (default: UTC)
            is_active: Active status (default: True)
        
        Returns:
            Tenant: Created tenant
        """
        tenant = Tenant(
            id=tenant_id,
            name=name,
            timezone=timezone,
            is_active=is_active
        )
        
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        
        logger.info(f"Created tenant: id={tenant_id}, name={name}")
        
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
            **fields: Fields to update (name, is_active, timezone)
        
        Returns:
            Tenant or None if not found
        """
        tenant = self.get_by_id(tenant_id)
        
        if not tenant:
            logger.warning(f"Update failed: tenant {tenant_id} not found")
            return None
        
        # Update allowed fields
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
    
    def is_active(self, tenant_id: str) -> bool:
        """Check if tenant is active
        
        Args:
            tenant_id: Company ID
        
        Returns:
            bool: True if active (False if not found or inactive)
        """
        tenant = self.get_by_id(tenant_id)
        return tenant.is_active if tenant else False


def get_tenant_repository(db: Session) -> TenantRepository:
    """Get TenantRepository instance (FastAPI Dependency)
    
    Args:
        db: SQLAlchemy Session
    
    Returns:
        TenantRepository: Repository instance
    """
    return TenantRepository(db)
