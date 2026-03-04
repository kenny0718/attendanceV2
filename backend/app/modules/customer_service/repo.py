"""Customer Service Repository

WP-11-04A: Support Company Assignments Repository
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.modules.customer_service.models import SupportCompanyAssignment


class CustomerServiceRepo:
    """Customer Service Repository"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_assigned_companies(self, user_id: UUID) -> List[str]:
        """
        取得客服被指派的公司列表
        
        Args:
            user_id: 客服 user_id
            
        Returns:
            List[str]: 公司 ID 列表
        """
        results = self.db.query(SupportCompanyAssignment.company_id).filter(
            SupportCompanyAssignment.user_id == user_id
        ).all()
        
        return [row[0] for row in results]
    
    def is_assigned_to_company(self, user_id: UUID, company_id: str) -> bool:
        """
        檢查客服是否被指派到指定公司
        
        Args:
            user_id: 客服 user_id
            company_id: 公司 ID
            
        Returns:
            bool: 是否被指派
        """
        result = self.db.query(SupportCompanyAssignment).filter(
            SupportCompanyAssignment.user_id == user_id,
            SupportCompanyAssignment.company_id == company_id
        ).first()
        
        return result is not None
    
    def assign_company(
        self,
        user_id: UUID,
        company_id: str,
        assigned_by_user_id: UUID
    ) -> SupportCompanyAssignment:
        """
        指派公司給客服
        
        Args:
            user_id: 客服 user_id
            company_id: 公司 ID
            assigned_by_user_id: 指派者 user_id
            
        Returns:
            SupportCompanyAssignment: 指派記錄
        """
        # 檢查是否已存在
        existing = self.db.query(SupportCompanyAssignment).filter(
            SupportCompanyAssignment.user_id == user_id,
            SupportCompanyAssignment.company_id == company_id
        ).first()
        
        if existing:
            return existing
        
        # 建立新指派
        assignment = SupportCompanyAssignment(
            user_id=user_id,
            company_id=company_id,
            assigned_by_user_id=assigned_by_user_id
        )
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        
        return assignment
    
    def unassign_company(self, user_id: UUID, company_id: str) -> bool:
        """
        取消客服的公司指派
        
        Args:
            user_id: 客服 user_id
            company_id: 公司 ID
            
        Returns:
            bool: 是否成功取消
        """
        result = self.db.query(SupportCompanyAssignment).filter(
            SupportCompanyAssignment.user_id == user_id,
            SupportCompanyAssignment.company_id == company_id
        ).delete()
        
        self.db.commit()
        
        return result > 0
