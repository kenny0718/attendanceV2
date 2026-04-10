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

    def update_member(self, membership_id: str, company_id: str, **fields) -> dict:
        """Update member display_name / email / role_id (S1-13A1)

        Business rules:
        - Only updates User.display_name / User.email and/or Membership.role_id
        - Does NOT touch login_username / password (separate flow)
        - Validates role_id exists before commit
        - Returns dict with updated user and membership objects
        - Raises ValueError for invalid role_id or not-found membership

        Args:
            membership_id: UUID string of the membership
            company_id: Company scope (for tenant isolation guard)
            **fields: Any of display_name, email, role_id
        """
        from app.modules.auth.models import Membership as MembershipModel, User as UserModel, Role as RoleModel
        import uuid as _uuid
        db = self.repo.db  # TenantService stores db via self.repo

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

        # Validate role_id before any write
        if "role_id" in fields and fields["role_id"] is not None:
            role = db.query(RoleModel).filter(RoleModel.id == fields["role_id"]).first()
            if role is None:
                raise ValueError(f"INVALID_ROLE: role '{fields['role_id']}' does not exist")
            membership.role_id = fields["role_id"]

        if "display_name" in fields and fields["display_name"] is not None:
            user.display_name = fields["display_name"]

        if "email" in fields:
            user.email = fields["email"]  # allows None to clear

        # S1-13A2: login_username update with pre-check + IntegrityError fallback
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
            raise  # re-raise unexpected IntegrityError

        db.refresh(user)
        db.refresh(membership)

        return {"user": user, "membership": membership}


    def reset_member_password(self, membership_id: str, company_id: str, new_plain_password: str) -> dict:
        """Reset a member password (S1-13A3)

        Password policy (minimum):
        - Must be non-empty
        - Length >= 6 characters

        Security:
        - Uses AuthRepository.update_password() which calls bcrypt hash_password()
        - Does NOT log or return the plain password or hash
        - Existing JWT sessions remain valid until expiry (no token blacklist)

        Args:
            membership_id: UUID string of the membership
            company_id: Company scope (for tenant isolation guard)
            new_plain_password: New plain-text password (will be hashed)

        Raises:
            ValueError: MEMBERSHIP_NOT_FOUND / INVALID_MEMBERSHIP_ID / PASSWORD_TOO_SHORT
        """
        from app.modules.auth.models import Membership as MembershipModel, User as UserModel
        from app.modules.auth.repo import AuthRepository
        import uuid as _uuid
        db = self.repo.db

        # Server-side password policy validation
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
        auth_repo.update_password(user, new_plain_password)  # bcrypt hash, commit, refresh
        # Note: plain password is NOT logged or returned

        return {"membership_id": str(membership.id), "user_id": str(user.id)}


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


class OnboardingService:
    """Admin Onboarding orchestration service (WP-S1-09C)

    Atomically creates:
      1. Company (Tenant)
      2. Global User
      3. Membership (user <-> company + role + login credentials)

    Transaction safety: all three steps run inside a single DB transaction.
    If any step fails the whole operation is rolled back — no dirty data.
    """

    def __init__(self, db: Session):
        self.db = db
        self.tenant_repo = TenantRepository(db)
        # Import here to avoid circular imports at module level
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
    ) -> dict:
        """Create company + user + membership in one atomic operation.

        Args:
            company_id: Desired company ID (must be unique)
            company_name: Company display name
            company_timezone: Timezone string (default 'UTC')
            user_display_name: Global display name for the initial user
            user_login_username: Per-company login username (unique within company)
            user_password: Plain text password (will be hashed)
            user_email: Optional email for notifications
            user_role_id: Role to assign in membership (e.g. 'company_admin')

        Returns:
            dict with keys: company, user, membership

        Raises:
            ValueError: DUPLICATE_COMPANY or DUPLICATE_LOGIN_USERNAME
            sqlalchemy.exc.IntegrityError: unexpected DB constraint violations
        """
        # ── Step 0: pre-flight validation (before touching DB) ──────────
        if self.tenant_repo.exists(company_id):
            raise ValueError(f"DUPLICATE_COMPANY: company '{company_id}' already exists")

        # Check login_username uniqueness within this company
        # (company doesn't exist yet so no conflict possible on login_username;
        #  but we verify role_id exists to fail fast before any write)
        from app.modules.auth.models import Role
        role = self.db.query(Role).filter(Role.id == user_role_id).first()
        if role is None:
            raise ValueError(f"INVALID_ROLE: role '{user_role_id}' does not exist")

        # ── Step 1-3: all writes inside a savepoint ─────────────────────
        # We use a nested transaction (SAVEPOINT) so that a failure in step 2
        # or 3 rolls back steps 1+2 without affecting the outer session.
        try:
            # Step 1: create company
            company = Tenant(
                id=company_id,
                name=company_name,
                timezone=company_timezone,
                is_active=True,
            )
            self.db.add(company)
            self.db.flush()  # write to DB but do NOT commit yet

            # Step 2: create global user (no-commit — stays in same transaction)
            user = self.auth_repo.create_user_no_commit(
                display_name=user_display_name,
                plain_password=user_password,
                email=user_email,
                must_change_password=False,
            )

            # Step 3: create membership (no-commit — same transaction)
            membership = self.auth_repo.create_membership_no_commit(
                user_id=user.id,
                company_id=company_id,
                role_id=user_role_id,
                login_username=user_login_username,
                login_email=user_email,
            )

            # Step 4: single atomic commit — if anything above failed, nothing is persisted
            self.db.commit()
            self.db.refresh(company)
            self.db.refresh(user)
            self.db.refresh(membership)

        except Exception:
            self.db.rollback()
            raise

        return {
            "company": company,
            "user": user,
            "membership": membership,
        }


def get_onboarding_service(db: Session) -> "OnboardingService":
    """FastAPI Dependency factory for OnboardingService."""
    return OnboardingService(db)
