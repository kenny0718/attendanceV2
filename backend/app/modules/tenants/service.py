"""Tenants Service (Business Logic Layer)"""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from app.modules.tenants.repo import TenantRepository
from app.modules.tenants.models import Tenant

logger = logging.getLogger(__name__)


class TenantService:
    """Tenant business logic layer"""
    
    def __init__(self, db: Session):
        """Initialize Service
        
        Args:
            db: SQLAlchemy Session
        """
        self.repo = TenantRepository(db)
    
    def create_tenant(
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
        
        Raises:
            ValueError: If tenant already exists
        """
        # Check if tenant already exists
        if self.repo.exists(tenant_id):
            raise ValueError(f"Tenant {tenant_id} already exists")
        
        return self.repo.create(
            tenant_id=tenant_id,
            name=name,
            timezone=timezone,
            is_active=is_active
        )
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID
        
        Args:
            tenant_id: Company ID
        
        Returns:
            Tenant or None if not found
        """
        return self.repo.get_by_id(tenant_id)
    
    def list_tenants(self, limit: int = 50, offset: int = 0) -> List[Tenant]:
        """List all tenants (with pagination)
        
        Args:
            limit: Max number of results
            offset: Offset for pagination
        
        Returns:
            List[Tenant]: List of tenants
        """
        return self.repo.list_all(limit=limit, offset=offset)
    
    def update_tenant(self, tenant_id: str, **fields) -> Optional[Tenant]:
        """Update tenant fields
        
        Args:
            tenant_id: Company ID
            **fields: Fields to update (name, is_active, timezone)
        
        Returns:
            Tenant or None if not found
        """
        return self.repo.update(tenant_id, **fields)
    
    def deactivate_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Deactivate tenant (soft delete)
        
        Args:
            tenant_id: Company ID
        
        Returns:
            Tenant or None if not found
        """
        return self.repo.update(tenant_id, is_active=False)
    
    def activate_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Activate tenant
        
        Args:
            tenant_id: Company ID
        
        Returns:
            Tenant or None if not found
        """
        return self.repo.update(tenant_id, is_active=True)
    
    def tenant_exists(self, tenant_id: str) -> bool:
        """Check if tenant exists
        
        Args:
            tenant_id: Company ID
        
        Returns:
            bool: True if exists
        """
        return self.repo.exists(tenant_id)
    
    def tenant_is_active(self, tenant_id: str) -> bool:
        """Check if tenant is active
        
        Args:
            tenant_id: Company ID
        
        Returns:
            bool: True if active (False if not found or inactive)
        """
        return self.repo.is_active(tenant_id)


def get_tenant_service(db: Session) -> TenantService:
    """Get TenantService instance (FastAPI Dependency)
    
    Args:
        db: SQLAlchemy Session
    
    Returns:
        TenantService: Service instance
    """
    return TenantService(db)
