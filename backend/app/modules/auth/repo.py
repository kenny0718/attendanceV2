"""Auth Repository (Platform-First v2)

WP-10-02B: Auth Repository Rewrite
Implements platform-first architecture with Membership model

Key changes from v1 (tenant-first):
- create_user(): NO company_id parameter (creates global user)
- create_membership(): new method (links user to company with role + login_username)
- get_user_by_login(): replaces get_user_by_username (queries via membership)
- get_user_memberships(): new method (get all companies for a user)
- user_has_company_access(): new method (check if user can access company)
"""

import hashlib
import logging
import uuid
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.config import settings
from app.modules.auth.models import User, Membership, Role, AuthSession
from app.core.security.password import hash_password, verify_password

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AuthRepository:
    """Auth data access layer (Platform-First v2)
    
    Design principles:
    - Users are global (no company_id in User table)
    - Login is per-company via Membership (login_username unique per company)
    - Membership links user to company with role
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(
        self,
        display_name: str,
        plain_password: str,
        email: Optional[str] = None,
        is_active: bool = True,
        is_otp: bool = False,
        must_change_password: bool = False
    ) -> User:
        password_hash = hash_password(plain_password)
        user = User(
            id=uuid.uuid4(),
            display_name=display_name,
            email=email,
            password_hash=password_hash,
            is_active=is_active,
            is_otp=is_otp,
            must_change_password=must_change_password
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        logger.info(f"Created user: id={user.id}, display_name={display_name}")
        return user
    
    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        user = self.db.query(User).filter(User.id == user_id).first()
        logger.debug(f"Get user by id: user_id={user_id}, found={user is not None}")
        return user
    
    def update_password(self, user: User, new_plain_password: str) -> User:
        user.password_hash = hash_password(new_plain_password)
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        logger.info(f"Updated password for user: id={user.id}")
        return user
    
    def update_last_login(self, user: User) -> User:
        user.last_login_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        logger.debug(f"Updated last_login_at for user: id={user.id}")
        return user
    
    def verify_user_password(self, user: User, plain_password: str) -> bool:
        return verify_password(plain_password, user.password_hash)
    
    def create_membership(
        self,
        user_id: uuid.UUID,
        company_id: str,
        role_id: str,
        login_username: str,
        login_email: Optional[str] = None,
        is_active: bool = True,
        uses_schedule: bool = False,
    ) -> Membership:
        membership = Membership(
            id=uuid.uuid4(),
            user_id=user_id,
            company_id=company_id,
            role_id=role_id,
            login_username=login_username,
            login_email=login_email,
            is_active=is_active,
            uses_schedule=uses_schedule,
        )
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        logger.info(f"Created membership: user_id={user_id}, company_id={company_id}, role_id={role_id}, login_username={login_username}")
        return membership
    
    def create_user_no_commit(
        self,
        display_name: str,
        plain_password: str,
        email: Optional[str] = None,
        is_active: bool = True,
        is_otp: bool = False,
        must_change_password: bool = False
    ) -> User:
        password_hash = hash_password(plain_password)
        user = User(
            id=uuid.uuid4(),
            display_name=display_name,
            email=email,
            password_hash=password_hash,
            is_active=is_active,
            is_otp=is_otp,
            must_change_password=must_change_password,
        )
        self.db.add(user)
        self.db.flush()
        logger.info(f"Flushed user (no-commit): id={user.id}, display_name={display_name}")
        return user

    def create_membership_no_commit(
        self,
        user_id: uuid.UUID,
        company_id: str,
        role_id: str,
        login_username: str,
        login_email: Optional[str] = None,
        is_active: bool = True,
        uses_schedule: bool = False,
    ) -> Membership:
        membership = Membership(
            id=uuid.uuid4(),
            user_id=user_id,
            company_id=company_id,
            role_id=role_id,
            login_username=login_username,
            login_email=login_email,
            is_active=is_active,
            uses_schedule=uses_schedule,
        )
        self.db.add(membership)
        self.db.flush()
        logger.info(f"Flushed membership (no-commit): user_id={user_id}, company_id={company_id}, login_username={login_username}")
        return membership

    def get_membership_by_login(self, company_id: str, login_username: str) -> Optional[Membership]:
        membership = self.db.query(Membership).filter(
            and_(Membership.company_id == company_id, Membership.login_username == login_username)
        ).first()
        logger.debug(f"Get membership by login: company_id={company_id}, login_username={login_username}, found={membership is not None}")
        return membership
    
    def get_user_by_login(self, company_id: str, login_username: str) -> Optional[User]:
        membership = self.get_membership_by_login(company_id, login_username)
        if not membership:
            logger.debug(f"Get user by login: no membership found for company_id={company_id}, login_username={login_username}")
            return None
        user = self.get_user_by_id(membership.user_id)
        logger.debug(f"Get user by login: company_id={company_id}, login_username={login_username}, user_id={user.id if user else None}")
        return user
    
    def get_user_memberships(self, user_id: uuid.UUID) -> List[Membership]:
        memberships = self.db.query(Membership).filter(Membership.user_id == user_id).all()
        logger.debug(f"Get user memberships: user_id={user_id}, count={len(memberships)}")
        return memberships
    
    def get_membership(self, user_id: uuid.UUID, company_id: str) -> Optional[Membership]:
        membership = self.db.query(Membership).filter(
            and_(Membership.user_id == user_id, Membership.company_id == company_id)
        ).first()
        logger.debug(f"Get membership: user_id={user_id}, company_id={company_id}, found={membership is not None}")
        return membership
    
    def user_has_company_access(self, user_id: uuid.UUID, company_id: str) -> bool:
        membership = self.get_membership(user_id, company_id)
        has_access = membership is not None and membership.is_active
        logger.debug(f"User has company access: user_id={user_id}, company_id={company_id}, has_access={has_access}")
        return has_access
    
    def get_role(self, role_id: str) -> Optional[Role]:
        role = self.db.query(Role).filter(Role.id == role_id).first()
        logger.debug(f"Get role: role_id={role_id}, found={role is not None}")
        return role

    def hash_refresh_token(self, refresh_token: str) -> str:
        return hashlib.sha256(refresh_token.encode('utf-8')).hexdigest()

    def create_auth_session(
        self,
        *,
        user_id: uuid.UUID,
        company_id: str,
        membership_id: uuid.UUID,
        role_id: str,
        refresh_token: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AuthSession:
        now = utc_now()
        session = AuthSession(
            id=uuid.uuid4(),
            user_id=user_id,
            company_id=company_id,
            membership_id=membership_id,
            role_id=role_id,
            refresh_token_hash=self.hash_refresh_token(refresh_token),
            is_active=True,
            created_at=now,
            updated_at=now,
            last_used_at=now,
            expires_at=now + timedelta(days=settings.refresh_token_days),
            absolute_expires_at=now + timedelta(hours=settings.session_absolute_timeout_hours),
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_auth_session(self, session_id: uuid.UUID) -> Optional[AuthSession]:
        return self.db.query(AuthSession).filter(AuthSession.id == session_id).first()

    def get_active_auth_session(self, session_id: uuid.UUID) -> Optional[AuthSession]:
        return self.db.query(AuthSession).filter(
            AuthSession.id == session_id,
            AuthSession.is_active.is_(True),
        ).first()

    def verify_refresh_token_for_session(self, session: AuthSession, refresh_token: str) -> bool:
        return session.refresh_token_hash == self.hash_refresh_token(refresh_token)

    def touch_auth_session(self, session: AuthSession) -> AuthSession:
        now = utc_now()
        session.last_used_at = now
        session.updated_at = now
        self.db.commit()
        self.db.refresh(session)
        return session

    def rotate_refresh_token(self, session: AuthSession, refresh_token: str) -> AuthSession:
        session.refresh_token_hash = self.hash_refresh_token(refresh_token)
        session.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(session)
        return session

    def revoke_auth_session(self, session: AuthSession, reason: str = "logout") -> AuthSession:
        session.is_active = False
        session.revoked_at = utc_now()
        session.revoke_reason = reason
        session.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(session)
        return session


def get_auth_repository(db: Session) -> AuthRepository:
    return AuthRepository(db)
