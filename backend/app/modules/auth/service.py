"""Auth Service (WP-10-04B)

Business logic for authentication operations.
Implements login flow according to WP-10-04_LOGIN_API_CONTRACT.md
"""

import logging
from datetime import timedelta
from uuid import UUID
from fastapi import HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security.jwt import create_access_token, create_refresh_token, decode_refresh_token
from app.modules.auth.repo import AuthRepository
from app.modules.auth.schemas import LoginRequest, LoginResponse, UserInfo, CompanyInfo, RoleInfo, MembershipInfo, RefreshResponse, LogoutResponse
from app.modules.tenants.service import get_tenant_service

logger = logging.getLogger(__name__)


class AuthService:
    """Auth business logic layer"""

    def __init__(self, db: Session):
        self.db = db
        self.auth_repo = AuthRepository(db)
        self.tenant_service = get_tenant_service(db)

    def login(self, request: LoginRequest, http_request: Request, http_response: Response) -> LoginResponse:
        company_input = request.company_id
        login_username = request.login_username
        password = request.password

        tenant = self.tenant_service.resolve_company(company_input)
        if not tenant:
            logger.warning(f"Login failed: company/tax_id {company_input} does not exist")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")

        company_id = tenant.id
        if not tenant.is_active:
            logger.warning(f"Login failed: company {company_id} is not active")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")

        membership = self.auth_repo.get_membership_by_login(company_id, login_username)
        if not membership or not membership.is_active:
            logger.warning(f"Login failed: no active membership found for {company_id}/{login_username}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")

        user = self.auth_repo.get_user_by_id(membership.user_id)
        if not user:
            logger.error(f"Login failed: user {membership.user_id} not found (data integrity issue)")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")

        if not self.auth_repo.verify_user_password(user, password):
            logger.warning(f"Login failed: wrong password for {company_id}/{login_username}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        refresh_token_placeholder = create_refresh_token({
            "sub": str(user.id),
            "session_id": "pending",
            "type": "refresh",
        })
        auth_session = self.auth_repo.create_auth_session(
            user_id=user.id,
            company_id=company_id,
            membership_id=membership.id,
            role_id=membership.role_id,
            refresh_token=refresh_token_placeholder,
            user_agent=http_request.headers.get("user-agent"),
            ip_address=http_request.client.host if http_request.client else None,
        )

        refresh_token = create_refresh_token({
            "sub": str(user.id),
            "session_id": str(auth_session.id),
            "type": "refresh",
        })
        self.auth_repo.rotate_refresh_token(auth_session, refresh_token)

        access_token = create_access_token({
            "sub": str(user.id),
            "company_id": company_id,
            "role_id": membership.role_id,
            "session_id": str(auth_session.id),
            "type": "access",
        })

        role = self.auth_repo.get_role(membership.role_id)
        if not role:
            logger.error(f"Login failed: role not found for membership {membership.id} (data integrity issue)")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

        self.auth_repo.update_last_login(user)
        self._set_refresh_cookie(http_response, refresh_token)
        logger.info(f"Login successful: user={user.id}, company={company_id}, role={membership.role_id}, session={auth_session.id}")

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserInfo(id=str(user.id), display_name=user.display_name, email=user.email),
            company=CompanyInfo(id=tenant.id, name=tenant.name),
            role=RoleInfo(id=role.id, name=role.name),
            membership=MembershipInfo(
                membership_id=str(membership.id),
                company_id=membership.company_id,
                role_id=membership.role_id,
                login_username=membership.login_username,
                is_active=membership.is_active,
                uses_schedule=membership.uses_schedule,
            ),
            idle_timeout_minutes=settings.session_idle_timeout_minutes,
            absolute_timeout_hours=settings.session_absolute_timeout_hours,
        )

    def refresh(self, refresh_token: str | None, http_response: Response) -> RefreshResponse:
        if not refresh_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

        try:
            payload = decode_refresh_token(refresh_token)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid refresh token: {str(e)}")

        try:
            session_id = UUID(payload["session_id"])
            user_id = UUID(payload["sub"])
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid refresh token claims: {exc}")

        auth_session = self.auth_repo.get_active_auth_session(session_id)
        if not auth_session or auth_session.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found or revoked")

        if not self.auth_repo.verify_refresh_token_for_session(auth_session, refresh_token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token mismatch")

        now = auth_session.updated_at.tzinfo and auth_session.updated_at or auth_session.updated_at
        current_time = auth_session.last_used_at.__class__.now(auth_session.last_used_at.tzinfo) if auth_session.last_used_at.tzinfo else None
        from datetime import datetime, timezone
        current = datetime.now(timezone.utc)

        if auth_session.expires_at <= current:
            self.auth_repo.revoke_auth_session(auth_session, reason="refresh_expired")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

        if auth_session.absolute_expires_at <= current:
            self.auth_repo.revoke_auth_session(auth_session, reason="absolute_timeout")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session absolute lifetime exceeded")

        idle_delta = current - auth_session.last_used_at
        if idle_delta > timedelta(minutes=settings.session_idle_timeout_minutes):
            self.auth_repo.revoke_auth_session(auth_session, reason="idle_timeout")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session idle timeout exceeded")

        user = self.auth_repo.get_user_by_id(auth_session.user_id)
        if not user or not user.is_active:
            self.auth_repo.revoke_auth_session(auth_session, reason="user_inactive")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")

        membership = self.auth_repo.get_membership(user.id, auth_session.company_id)
        if not membership or not membership.is_active:
            self.auth_repo.revoke_auth_session(auth_session, reason="membership_inactive")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Membership inactive")

        new_refresh_token = create_refresh_token({
            "sub": str(user.id),
            "session_id": str(auth_session.id),
            "type": "refresh",
        })
        self.auth_repo.rotate_refresh_token(auth_session, new_refresh_token)
        self.auth_repo.touch_auth_session(auth_session)

        access_token = create_access_token({
            "sub": str(user.id),
            "company_id": auth_session.company_id,
            "role_id": membership.role_id,
            "session_id": str(auth_session.id),
            "type": "access",
        })
        self._set_refresh_cookie(http_response, new_refresh_token)

        return RefreshResponse(
            access_token=access_token,
            token_type="bearer",
            idle_timeout_minutes=settings.session_idle_timeout_minutes,
            absolute_timeout_hours=settings.session_absolute_timeout_hours,
        )

    def logout(self, refresh_token: str | None, http_response: Response) -> LogoutResponse:
        if refresh_token:
            try:
                payload = decode_refresh_token(refresh_token)
                session_id = UUID(payload["session_id"])
                auth_session = self.auth_repo.get_active_auth_session(session_id)
                if auth_session:
                    self.auth_repo.revoke_auth_session(auth_session, reason="logout")
            except Exception:
                logger.warning("Logout called with invalid refresh token")
        self._clear_refresh_cookie(http_response)
        return LogoutResponse(success=True)

    def _set_refresh_cookie(self, response: Response, refresh_token: str) -> None:
        response.set_cookie(
            key=settings.refresh_cookie_name,
            value=refresh_token,
            httponly=True,
            secure=settings.refresh_cookie_secure,
            samesite=settings.refresh_cookie_samesite,
            max_age=settings.refresh_token_days * 86400,
            expires=settings.refresh_token_days * 86400,
            path='/',
        )

    def _clear_refresh_cookie(self, response: Response) -> None:
        response.delete_cookie(
            key=settings.refresh_cookie_name,
            path='/',
            samesite=settings.refresh_cookie_samesite,
        )


def get_auth_service(db: Session) -> AuthService:
    return AuthService(db)
