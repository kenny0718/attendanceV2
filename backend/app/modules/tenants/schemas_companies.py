"""Tenants – Companies schemas (split from schemas.py, WP-S1-09A)"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_serializer, field_validator


def _is_valid_taiwan_tax_id(value: str) -> bool:
    if not value.isdigit() or len(value) != 8:
        return False

    weights = [1, 2, 1, 2, 1, 2, 4, 1]
    checksum = 0
    for digit, weight in zip(value, weights):
        product = int(digit) * weight
        checksum += (product // 10) + (product % 10)

    return checksum % 10 == 0 or (value[6] == '7' and (checksum + 1) % 10 == 0)


class CreateCompanyRequest(BaseModel):
    """POST /api/admin/companies — request body"""

    id: str = Field(..., min_length=1, max_length=50, description="Company ID")
    name: str = Field(..., min_length=1, max_length=255, description="Company display name")
    tax_id: Optional[str] = Field(None, min_length=8, max_length=20, description="Company tax ID")
    timezone: str = Field(default="UTC", max_length=50, description="Company timezone")

    @field_validator("tax_id")
    @classmethod
    def normalize_and_validate_tax_id(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        normalized = value.strip()
        if not normalized:
            return None

        if not _is_valid_taiwan_tax_id(normalized):
            raise ValueError("Invalid Taiwan tax ID")

        return normalized


class UpdateCompanyRequest(BaseModel):
    """PATCH /api/admin/companies/{company_id} — request body (S1-11A)"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    tax_id: Optional[str] = Field(None, min_length=8, max_length=20)
    timezone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = Field(None)

    @field_validator("tax_id")
    @classmethod
    def normalize_and_validate_tax_id(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        normalized = value.strip()
        if not normalized:
            return None

        if not _is_valid_taiwan_tax_id(normalized):
            raise ValueError("Invalid Taiwan tax ID")

        return normalized


class CompanyResponse(BaseModel):
    """Single company/tenant summary response"""

    id: str = Field(..., description="Company ID")
    name: str = Field(..., description="Company display name")
    tax_id: Optional[str] = Field(None, description="Company tax ID")
    is_active: bool = Field(..., description="Active status")
    timezone: str = Field(..., description="Company timezone")
    created_at: datetime = Field(..., description="Created timestamp (UTC)")

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime, _info):
        return dt.isoformat()

    model_config = {"from_attributes": True}


class CompanyListResponse(BaseModel):
    """GET /api/admin/companies — response body"""

    companies: List[CompanyResponse] = Field(..., description="List of companies")
    total: int = Field(..., description="Total count returned")
