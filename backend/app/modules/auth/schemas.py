"""Auth API Schemas (WP-10-04B)

Pydantic models for login API request/response.
"""

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    """Login request schema"""
    company_id: str = Field(..., min_length=1, max_length=255, description="Company ID")
    login_username: str = Field(..., min_length=1, max_length=100, description="Login username")
    password: str = Field(..., min_length=1, max_length=255, description="Password")
    
    @field_validator("company_id", "login_username", "password")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate fields are not empty or whitespace only"""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class UserInfo(BaseModel):
    """User information in login response"""
    id: str = Field(..., description="User ID")
    display_name: str = Field(..., description="Display name")
    email: str | None = Field(None, description="Email (optional)")


class CompanyInfo(BaseModel):
    """Company information in login response"""
    id: str = Field(..., description="Company ID")
    name: str = Field(..., description="Company name")


class RoleInfo(BaseModel):
    """Role information in login response"""
    id: str = Field(..., description="Role ID")
    name: str = Field(..., description="Role name")


class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserInfo = Field(..., description="User information")
    company: CompanyInfo = Field(..., description="Company information")
    role: RoleInfo = Field(..., description="Role information")
