"""Customer Service API endpoints

WP-11-04A: Support Company Assignments API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.scope import Actor, ScopeError
from app.core.dependencies import get_current_actor
from app.modules.customer_service.service import CustomerServiceService
from app.modules.customer_service.schemas import (
    AssignCompanyRequest,
    UnassignCompanyRequest,
    AssignmentResponse,
    UnassignmentResponse,
    AssignedCompaniesResponse,
)

router = APIRouter(prefix="/api/customer-service", tags=["customer_service"])


@router.get("/assigned-companies", response_model=AssignedCompaniesResponse)
def get_assigned_companies(
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
):
    """
    取得客服被指派的公司列表
    
    權限：只有 customer_service 可存取
    """
    try:
        service = CustomerServiceService(db)
        companies = service.get_assigned_companies(actor)
        return AssignedCompaniesResponse(companies=companies)
    except ScopeError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SCOPE_FORBIDDEN", "message": str(e)}
        )


@router.post("/assignments", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def assign_company(
    request: AssignCompanyRequest,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
):
    """
    指派公司給客服
    
    權限：只有 super_admin 可執行
    """
    try:
        service = CustomerServiceService(db)
        result = service.assign_company(
            actor,
            request.customer_service_user_id,
            request.company_id
        )
        return AssignmentResponse(**result)
    except ScopeError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SCOPE_FORBIDDEN", "message": str(e)}
        )


@router.delete("/assignments", response_model=UnassignmentResponse)
def unassign_company(
    request: UnassignCompanyRequest,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db),
):
    """
    取消客服的公司指派
    
    權限：只有 super_admin 可執行
    """
    try:
        service = CustomerServiceService(db)
        result = service.unassign_company(
            actor,
            request.customer_service_user_id,
            request.company_id
        )
        return UnassignmentResponse(**result)
    except ScopeError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "SCOPE_FORBIDDEN", "message": str(e)}
        )
