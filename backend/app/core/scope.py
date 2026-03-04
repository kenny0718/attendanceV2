"""
Scope 檢查機制
統一處理 SuperAdmin / customer_service / company user 的權限範圍
遵守 SA_MODULE_SPEC v1.8 的順序：Scope → Tenant Isolation → Feature Gate

WP-11-04A: Company Entitlements + SuperAdmin 管理 + customer_service Scope
"""
from typing import Optional, Set
from enum import Enum
from sqlalchemy.orm import Session
from uuid import UUID


class UserRole(Enum):
    """使用者角色"""
    SUPER_ADMIN = "super_admin"
    CUSTOMER_SERVICE = "customer_service"
    COMPANY_USER = "company_user"


class ScopeError(Exception):
    """權限範圍錯誤"""
    def __init__(self, message: str, company_id: Optional[str] = None):
        self.message = message
        self.company_id = company_id
        super().__init__(message)


class Actor:
    """
    操作者資訊
    封裝當前使用者的身份和權限資訊
    """
    def __init__(
        self,
        user_id: UUID,
        role: UserRole,
        company_memberships: Optional[Set[str]] = None,
        support_company_assignments: Optional[Set[str]] = None,
    ):
        self.user_id = user_id
        self.role = role
        self.company_memberships = company_memberships or set()
        self.support_company_assignments = support_company_assignments or set()
    
    def is_super_admin(self) -> bool:
        """是否為 Super Admin"""
        return self.role == UserRole.SUPER_ADMIN
    
    def is_customer_service(self) -> bool:
        """是否為客服"""
        return self.role == UserRole.CUSTOMER_SERVICE
    
    def is_company_user(self) -> bool:
        """是否為一般公司使用者"""
        return self.role == UserRole.COMPANY_USER


class ScopeChecker:
    """
    Scope 檢查器
    提供統一的權限範圍檢查邏輯
    """
    
    def __init__(self, db: Session):
        """
        初始化 Scope Checker
        
        Args:
            db: SQLAlchemy Session
        """
        self.db = db
    
    def assert_company_scope(self, actor: Actor, company_id: str) -> None:
        """
        檢查操作者是否有權限操作指定公司
        
        規則：
        - super_admin: 直接通過
        - customer_service: 必須在 support_company_assignments 中
        - company_user: 必須在 user_company_memberships 中
        
        Args:
            actor: 操作者資訊
            company_id: 目標公司 ID
            
        Raises:
            ScopeError: 無權限操作該公司（HTTP 403）
        """
        # Super Admin 可操作所有公司
        if actor.is_super_admin():
            return
        
        # Customer Service 只能操作被指派的公司
        if actor.is_customer_service():
            if company_id not in actor.support_company_assignments:
                raise ScopeError(
                    f"Customer service user {actor.user_id} is not assigned to company {company_id}",
                    company_id=company_id
                )
            return
        
        # Company User 只能操作所屬公司
        if actor.is_company_user():
            if company_id not in actor.company_memberships:
                raise ScopeError(
                    f"User {actor.user_id} is not a member of company {company_id}",
                    company_id=company_id
                )
            return
        
        # 未知角色，拒絕存取
        raise ScopeError(f"Unknown role: {actor.role}")
    
    def get_accessible_companies(self, actor: Actor) -> Set[str]:
        """
        取得操作者可存取的所有公司 ID
        
        Args:
            actor: 操作者資訊
            
        Returns:
            Set[str]: 可存取的公司 ID 集合
        """
        if actor.is_super_admin():
            # Super Admin 可存取所有公司（需從 DB 查詢）
            return self._get_all_company_ids()
        
        if actor.is_customer_service():
            return actor.support_company_assignments
        
        if actor.is_company_user():
            return actor.company_memberships
        
        return set()
    
    def _get_all_company_ids(self) -> Set[str]:
        """
        從資料庫取得所有公司 ID
        
        Returns:
            Set[str]: 所有公司 ID
        """
        from app.modules.tenants.models import Tenant
        
        results = self.db.query(Tenant.id).all()
        return {row[0] for row in results}


def assert_company_scope(actor: Actor, company_id: str, db: Session) -> None:
    """
    便捷函數：檢查公司權限範圍
    
    Args:
        actor: 操作者資訊
        company_id: 目標公司 ID
        db: SQLAlchemy Session
        
    Raises:
        ScopeError: 無權限操作該公司
    """
    checker = ScopeChecker(db)
    checker.assert_company_scope(actor, company_id)


def get_accessible_companies(actor: Actor, db: Session) -> Set[str]:
    """
    便捷函數：取得可存取的公司列表
    
    Args:
        actor: 操作者資訊
        db: SQLAlchemy Session
        
    Returns:
        Set[str]: 可存取的公司 ID 集合
    """
    checker = ScopeChecker(db)
    return checker.get_accessible_companies(actor)
