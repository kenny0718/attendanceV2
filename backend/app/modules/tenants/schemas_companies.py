"""Tenants – Companies schemas (split from schemas.py, WP-S1-09A)"""

from pydantic import BaseModel, Field, field_serializer
from typing import List, Optional
from datetime import datetime


class CreateCompanyRequest(BaseModel):
    """POST /api/admin/companies — request body"""
    id: str = Field(..., min_length=1, max_length=50, description="Company ID")
    name: str = Field(..., min_length=1, max_length=255, description="Company display name")
    timezone: str = Field(default="UTC", max_length=50, description="Company timezone")


class UpdateCompanyRequest(BaseModel):
    """PATCH /api/admin/companies/{company_id} — request body (S1-11A)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    timezone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = Field(None)


class CompanyResponse(BaseModel):
    """Single company/tenant summary response"""
    id: str = Field(..., description="Company ID")
    name: str = Field(..., description="Company display name")
    is_active: bool = Field(..., description="Active status")
    timezone: str = Field(..., description="Company timezone")
    created_at: datetime = Field(..., description="Created timestamp (UTC)")

    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime, _info):
        return dt.isoformat()

    model_config = {"from_attributes": True}


class CompanyListResponse(BaseModel):
    """GET /api/admin/companies — response body"""
    companies: List[CompanyResponse] = Field(..., description="List of companies")
    total: int = Field(..., description="Total count returned")
