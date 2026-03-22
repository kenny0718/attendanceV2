"""Tenants – Entitlement schemas (split from schemas.py, WP-11-04A)"""

from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime


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
    entitlements: dict = Field(..., description="feature_key -> enabled 對應")


class ApplyPlanResponse(BaseModel):
    """套用 plan 結果回應"""
    company_id: str = Field(..., description="公司 ID")
    plan_code: str = Field(..., description="Plan 代碼")
    updated_count: int = Field(..., description="更新的 entitlement 數量")
