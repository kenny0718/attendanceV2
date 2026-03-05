"""Auth API Routes (WP-10-04B)

FastAPI endpoints for authentication.
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.schemas import LoginRequest, LoginResponse
from app.modules.auth.service import AuthService, get_auth_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/internal/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
) -> LoginResponse:
    """Login endpoint (POST /api/internal/auth/login)
    
    Authenticates user with company_id + login_username + password.
    Returns JWT token and user information.
    
    Request Body:
        - company_id: Company ID (tenant selector)
        - login_username: Per-company login username
        - password: Plain text password
    
    Response (200):
        - access_token: JWT token (HS256, 900s expiry)
        - token_type: "bearer"
        - user: User information (id, display_name, email)
        - company: Company information (id, name)
        - role: Role information (id, name)
    
    Errors:
        - 404: Company/membership not found or inactive (anti-enumeration)
        - 401: Wrong password
        - 422: Validation error (missing/invalid fields)
    
    See: docs/WP-10-04_LOGIN_API_CONTRACT.md
    """
    auth_service = get_auth_service(db)
    return auth_service.login(request)
