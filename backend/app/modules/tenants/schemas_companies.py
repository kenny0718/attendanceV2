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


class CompanyBaseFields(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Company legal name")
    tax_id: Optional[str] = Field(None, min_length=8, max_length=20, description="Company tax ID")
    display_name: Optional[str] = Field(None, max_length=255, description="Company display name")
    owner_name: Optional[str] = Field(None, max_length=255, description="Company owner name")
    registered_address: Optional[str] = Field(None, max_length=500, description="Company registered address")
    contact_address: Optional[str] = Field(None, max_length=500, description="Company contact address")
    contact_phone: Optional[str] = Field(None, max_length=50, description="Company contact phone")
    contact_email: Optional[str] = Field(None, max_length=255, description="Company contact email")
    timezone: str = Field(default="UTC", max_length=50, description="Company timezone")

    @field_validator(
        "display_name",
        "owner_name",
        "registered_address",
        "contact_address",
        "contact_phone",
        "contact_email",
    )
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        normalized = value.strip()
        if not normalized:
            return None
        return normalized

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


class CreateCompanyRequest(CompanyBaseFields):
    """POST /api/admin/companies — request body"""

    id: str = Field(..., min_length=1, max_length=50, description="Company ID")

    model_config = {"extra": "forbid"}


class UpdateCompanyRequest(BaseModel):
    """PATCH /api/admin/companies/{company_id} — request body (S1-11A)"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    tax_id: Optional[str] = Field(None, min_length=8, max_length=20)
    display_name: Optional[str] = Field(None, max_length=255)
    owner_name: Optional[str] = Field(None, max_length=255)
    registered_address: Optional[str] = Field(None, max_length=500)
    contact_address: Optional[str] = Field(None, max_length=500)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=255)
    timezone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = Field(None)

    @field_validator(
        "display_name",
        "owner_name",
        "registered_address",
        "contact_address",
        "contact_phone",
        "contact_email",
    )
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        normalized = value.strip()
        if not normalized:
            return None
        return normalized

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
    name: str = Field(..., description="Company legal name")
    tax_id: Optional[str] = Field(None, description="Company tax ID")
    display_name: Optional[str] = Field(None, description="Company display name")
    owner_name: Optional[str] = Field(None, description="Company owner name")
    registered_address: Optional[str] = Field(None, description="Company registered address")
    contact_address: Optional[str] = Field(None, description="Company contact address")
    contact_phone: Optional[str] = Field(None, description="Company contact phone")
    contact_email: Optional[str] = Field(None, description="Company contact email")
    is_active: bool = Field(..., description="Active status")
    timezone: str = Field(..., description="Company timezone")
    created_at: datetime = Field(..., description="Created timestamp (UTC)")

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime, _info):
        return dt.isoformat()

    model_config = {"from_attributes": True}


class CompanyMemberSummaryResponse(BaseModel):
    admin_count: int = Field(..., description="Count of company_admin + hr_manager")
    active_admin_count: int = Field(..., description="Active count of company_admin + hr_manager")
    has_company_admin: bool = Field(..., description="Whether company has company_admin")
    has_hr_manager: bool = Field(..., description="Whether company has hr_manager")


class CompanyDetailResponse(BaseModel):
    company: CompanyResponse
    member_summary: CompanyMemberSummaryResponse


class CompanyListResponse(BaseModel):
    """GET /api/admin/companies — response body"""

    companies: List[CompanyResponse] = Field(..., description="List of companies")
    total: int = Field(..., description="Total count returned")


class LookupCompanyByTaxIdRequest(BaseModel):
    tax_id: str = Field(..., min_length=8, max_length=20, description="Taiwan company tax ID")

    @field_validator("tax_id")
    @classmethod
    def normalize_and_validate_tax_id(cls, value: str) -> str:
        normalized = value.strip()
        if not _is_valid_taiwan_tax_id(normalized):
            raise ValueError("Invalid Taiwan tax ID")
        return normalized


class LookupCompanyByTaxIdResponse(BaseModel):
    tax_id: str = Field(..., description="Queried tax ID")
    name: Optional[str] = Field(None, description="Company legal name")
    owner_name: Optional[str] = Field(None, description="Company owner name")
    registered_address: Optional[str] = Field(None, description="Company registered address")
    found: bool = Field(..., description="Whether lookup found a record")
