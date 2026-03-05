"""Customer Service API schemas

WP-11-04A: Support Company Assignments schemas
"""

from pydantic import BaseModel, Field
from datetime import datetime


class AssignCompanyRequest(BaseModel):
    """指派公司給客服的請求"""
    customer_service_user_id: str = Field(..., description="客服 user_id (UUID)")
    company_id: str = Field(..., description="公司 ID")


class UnassignCompanyRequest(BaseModel):
    """取消客服公司指派的請求"""
    customer_service_user_id: str = Field(..., description="客服 user_id (UUID)")
    company_id: str = Field(..., description="公司 ID")


class AssignmentResponse(BaseModel):
    """指派結果回應"""
    user_id: str = Field(..., description="客服 user_id")
    company_id: str = Field(..., description="公司 ID")
    assigned_at: str = Field(..., description="指派時間 (ISO 8601)")


class UnassignmentResponse(BaseModel):
    """取消指派結果回應"""
    user_id: str = Field(..., description="客服 user_id")
    company_id: str = Field(..., description="公司 ID")
    status: str = Field(..., description="狀態 (unassigned/not_found)")


class AssignedCompaniesResponse(BaseModel):
    """客服被指派的公司列表回應"""
    companies: list[str] = Field(..., description="公司 ID 列表")
