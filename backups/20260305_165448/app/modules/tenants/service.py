"""Tenants Service (Business Logic Layer)

WP-11-04A: Added CompanyEntitlement service methods
"""

import logging
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from uuid import UUID

from app.modules.tenants.repo import TenantRepository, CompanyEntitlementRepository
from app.modules.tenants.models import Tenant, CompanyEntitlement
from app.core.scope import Actor, ScopeError, assert_company_scope
from app.core.features import FeatureKeys, PLAN_DEFAULTS
from app.core.feature_service import get_feature_service

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


class CompanyEntitlementService:
    """Company Entitlement business logic layer (WP-11-04A)"""
    
    def __init__(self, db: Session):
        """Initialize Service
        
        Args:
            db: SQLAlchemy Session
        """
        self.db = db
        self.repo = CompanyEntitlementRepository(db)
        self.feature_service = get_feature_service(db)
    
    def list_company_entitlements(self, actor: Actor, company_id: str) -> Dict:
        """列出公司的所有 entitlements
        
        權限：
        - super_admin: 可查看所有公司
        - customer_service: 只能查看被指派的公司
        - company_user: 只能查看所屬公司
        
        Args:
            actor: 操作者
            company_id: 公司 ID
            
        Returns:
            Dict: 包含所有 feature_key 的啟用狀態
            
        Raises:
            ScopeError: 無權限查看該公司（HTTP 403）
        """
        # Step 1: Scope 檢查
        assert_company_scope(actor, company_id, self.db)
        
        # Step 2: Tenant Isolation（查詢時已確保只查該公司）
        # Step 3: Feature Gate（讀取操作不需要 feature gate）
        
        # 查詢該公司的所有 entitlements
        entitlements = self.repo.get_all_entitlements(company_id)
        
        # 確保所有 feature_key 都有值（未設定的顯示為 false）
        result = {}
        for feature_key in FeatureKeys.all_keys():
            result[feature_key] = entitlements.get(feature_key, False)
        
        return {
            "company_id": company_id,
            "entitlements": result,
        }
    
    def update_entitlement(
        self,
        actor: Actor,
        company_id: str,
        feature_key: str,
        enabled: bool,
    ) -> Dict:
        """更新單一 feature 的啟用狀態
        
        權限：只有 super_admin 可以修改
        
        Args:
            actor: 操作者
            company_id: 公司 ID
            feature_key: 功能 key
            enabled: 是否啟用
            
        Returns:
            Dict: 更新後的 entitlement
            
        Raises:
            ScopeError: 非 super_admin（HTTP 403）
            ValueError: 無效的 feature_key
        """
        # 只有 super_admin 可以修改
        if not actor.is_super_admin():
            raise ScopeError("Only super_admin can modify entitlements")
        
        # 驗證 feature_key
        FeatureKeys.validate(feature_key)
        
        # 更新或插入 entitlement
        entitlement = self.repo.upsert_entitlement(
            company_id=company_id,
            feature_key=feature_key,
            enabled=enabled,
            updated_by_user_id=actor.user_id,
        )
        
        # 清除快取
        self.feature_service.clear_cache(company_id, feature_key)
        
        return {
            "company_id": company_id,
            "feature_key": feature_key,
            "enabled": enabled,
            "updated_by": str(actor.user_id),
            "updated_at": entitlement.updated_at.isoformat(),
        }
    
    def apply_plan_defaults(
        self,
        actor: Actor,
        company_id: str,
        plan_code: str,
    ) -> Dict:
        """批次套用 plan 的預設 entitlements
        
        權限：只有 super_admin 可以執行
        
        Args:
            actor: 操作者
            company_id: 公司 ID
            plan_code: Plan 代碼（Basic/Pro）
            
        Returns:
            Dict: 套用結果
            
        Raises:
            ScopeError: 非 super_admin（HTTP 403）
            ValueError: 無效的 plan_code
        """
        # 只有 super_admin 可以執行
        if not actor.is_super_admin():
            raise ScopeError("Only super_admin can apply plan defaults")
        
        # 驗證 plan_code
        if plan_code not in PLAN_DEFAULTS:
            raise ValueError(
                f"Unknown plan_code: {plan_code}. "
                f"Valid plans: {', '.join(PLAN_DEFAULTS.keys())}"
            )
        
        # 批次更新
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
        
        # 清除該公司的所有快取
        self.feature_service.clear_cache(company_id)
        
        return {
            "company_id": company_id,
            "plan_code": plan_code,
            "updated_count": updated_count,
        }


def get_tenant_service(db: Session) -> TenantService:
    """Get TenantService instance (FastAPI Dependency)
    
    Args:
        db: SQLAlchemy Session
    
    Returns:
        TenantService: Service instance
    """
    return TenantService(db)


def get_entitlement_service(db: Session) -> CompanyEntitlementService:
    """Get CompanyEntitlementService instance (FastAPI Dependency)
    
    Args:
        db: SQLAlchemy Session
    
    Returns:
        CompanyEntitlementService: Service instance
    """
    return CompanyEntitlementService(db)
