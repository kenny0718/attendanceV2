"""Auth Service (WP-10-04B)

Business logic for authentication operations.
Implements login flow according to WP-10-04_LOGIN_API_CONTRACT.md
"""

import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.modules.auth.repo import AuthRepository
from app.modules.auth.schemas import LoginRequest, LoginResponse, UserInfo, CompanyInfo, RoleInfo, MembershipInfo
from app.modules.tenants.repo import TenantRepository
from app.core.security.jwt import create_access_token

logger = logging.getLogger(__name__)


class AuthService:
    """Auth business logic layer"""

    def __init__(self, db: Session):
        self.db = db
        self.auth_repo = AuthRepository(db)
        self.tenant_repo = TenantRepository(db)

    def login(self, request: LoginRequest) -> LoginResponse:
        company_id = request.company_id
        login_username = request.login_username
        password = request.password

        if not self.tenant_repo.exists(company_id):
            logger.warning(f"Login failed: company {company_id} does not exist")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")

        if not self.tenant_repo.is_active(company_id):
            logger.warning(f"Login failed: company {company_id} is not active")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")

        membership = self.auth_repo.get_membership_by_login(company_id, login_username)
        if not membership:
            logger.warning(f"Login failed: no membership found for {company_id}/{login_username}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")

        if not membership.is_active:
            logger.warning(f"Login failed: membership inactive for {company_id}/{login_username}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")

        user = self.auth_repo.get_user_by_id(membership.user_id)
        if not user:
            logger.error(f"Login failed: user {membership.user_id} not found (data integrity issue)")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")

        if not self.auth_repo.verify_user_password(user, password):
            logger.warning(f"Login failed: wrong password for {company_id}/{login_username}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        token_claims = {
            "sub": str(user.id),
            "company_id": company_id,
            "role_id": membership.role_id,
        }
        access_token = create_access_token(token_claims, expires_in=900)

        tenant = self.tenant_repo.get_by_id(company_id)
        role = self.auth_repo.get_role(membership.role_id)
        if not tenant or not role:
            logger.error(f"Login failed: tenant or role not found (data integrity issue)")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

        self.auth_repo.update_last_login(user)
        logger.info(f"Login successful: user={user.id}, company={company_id}, role={membership.role_id}")

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
        )


def get_auth_service(db: Session) -> AuthService:
    return AuthService(db)
