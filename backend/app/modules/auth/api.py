"""Auth API Routes (WP-10-04B)

FastAPI endpoints for authentication.
"""

import logging
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.modules.auth.schemas import LoginRequest, LoginResponse, RefreshResponse, LogoutResponse
from app.modules.auth.service import get_auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/internal/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    http_response: Response,
    db: Session = Depends(get_db)
) -> LoginResponse:
    auth_service = get_auth_service(db)
    return auth_service.login(request, http_request, http_response)


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    http_request: Request,
    http_response: Response,
    db: Session = Depends(get_db)
) -> RefreshResponse:
    auth_service = get_auth_service(db)
    refresh_token = http_request.cookies.get(settings.refresh_cookie_name)
    return auth_service.refresh(refresh_token, http_response)


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    http_request: Request,
    http_response: Response,
    db: Session = Depends(get_db)
) -> LogoutResponse:
    auth_service = get_auth_service(db)
    refresh_token = http_request.cookies.get(settings.refresh_cookie_name)
    return auth_service.logout(refresh_token, http_response)
