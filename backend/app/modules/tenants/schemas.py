"""Tenants API schemas

WP-11-04A: Added CompanyEntitlement schemas
WP-S1-09A: Added company list / create schemas
"""

from pydantic import BaseModel, Field, field_serializer
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime


# ── WP-S1-09A: Company (Tenant) management schemas ───────────────────

class CreateCompanyRequest(BaseModel):
    """POST /api/admin/companies — request body"""
    id: str = Field(..., min_length=1, max_length=50, description="Company ID (tenant identifier, e.g. 'company-b')")
    name: str = Field(..., min_length=1, max_length=255, description="Company display name")
    timezone: str = Field(default="UTC", max_length=50, description="Company timezone (default: UTC)")


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


# ── WP-11-04A: Entitlement schemas ───────────────────────────────────

class UpdateEntitlementRequest(BaseModel):
    """更新 entitlement 的請求"""
    feature_key: str = Field(..., description="功能 key (e.g., attendance.shift_templates)")
    enabled: bool = Field(..., description="是否啟用")


class ApplyPlanRequest(BaseModel):
    """套用 plan 預設值的請求"""
    plan_code: str = Field(..., description="Plan 代碼 (Basic/Pro)")


class EntitlementResponse(BaseModel):
    """單一 entitlement 回應"""
    company_id: str = Field(..., description="公司 ID")
    feature_key: str = Field(..., description="功能 key")
    enabled: bool = Field(..., description="是否啟用")
    updated_by: Optional[str] = Field(None, description="更新者 user_id")
    updated_at: datetime = Field(..., description="更新時間")

    @field_serializer('updated_at')
    def serialize_datetime(self, dt: datetime, _info):
        """序列化 datetime 為 ISO 8601 字串"""
        return dt.isoformat()


class CompanyEntitlementsResponse(BaseModel):
    """公司所有 entitlements 回應"""
    company_id: str = Field(..., description="公司 ID")
    entitlements: Dict[str, bool] = Field(..., description="feature_key -> enabled 對應")


class ApplyPlanResponse(BaseModel):
    """套用 plan 結果回應"""
    company_id: str = Field(..., description="公司 ID")
    plan_code: str = Field(..., description="Plan 代碼")
    updated_count: int = Field(..., description="更新的 entitlement 數量")
