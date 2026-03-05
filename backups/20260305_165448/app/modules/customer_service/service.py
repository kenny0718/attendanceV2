"""Customer Service Service

WP-11-04A: Customer Service Scope 檢查
"""
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.scope import Actor, ScopeError, assert_company_scope
from app.modules.customer_service.repo import CustomerServiceRepo


class CustomerServiceService:
    """Customer Service Service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = CustomerServiceRepo(db)
    
    def get_assigned_companies(self, actor: Actor) -> List[str]:
        """
        取得客服被指派的公司列表
        
        Args:
            actor: 操作者
            
        Returns:
            List[str]: 公司 ID 列表
            
        Raises:
            ScopeError: 非客服人員
        """
        if not actor.is_customer_service():
            raise ScopeError("Only customer_service can access this endpoint")
        
        return self.repo.get_assigned_companies(actor.user_id)
    
    def assign_company(
        self,
        actor: Actor,
        customer_service_user_id: UUID,
        company_id: str
    ) -> dict:
        """
        指派公司給客服（只有 super_admin 可執行）
        
        Args:
            actor: 操作者
            customer_service_user_id: 客服 user_id
            company_id: 公司 ID
            
        Returns:
            dict: 指派結果
            
        Raises:
            ScopeError: 非 super_admin
        """
        if not actor.is_super_admin():
            raise ScopeError("Only super_admin can manage support assignments")
        
        assignment = self.repo.assign_company(
            user_id=customer_service_user_id,
            company_id=company_id,
            assigned_by_user_id=actor.user_id
        )
        
        return {
            "user_id": str(assignment.user_id),
            "company_id": assignment.company_id,
            "assigned_at": assignment.assigned_at.isoformat()
        }
    
    def unassign_company(
        self,
        actor: Actor,
        customer_service_user_id: UUID,
        company_id: str
    ) -> dict:
        """
        取消客服的公司指派（只有 super_admin 可執行）
        
        Args:
            actor: 操作者
            customer_service_user_id: 客服 user_id
            company_id: 公司 ID
            
        Returns:
            dict: 取消結果
            
        Raises:
            ScopeError: 非 super_admin
        """
        if not actor.is_super_admin():
            raise ScopeError("Only super_admin can manage support assignments")
        
        success = self.repo.unassign_company(customer_service_user_id, company_id)
        
        return {
            "user_id": str(customer_service_user_id),
            "company_id": company_id,
            "status": "unassigned" if success else "not_found"
        }
