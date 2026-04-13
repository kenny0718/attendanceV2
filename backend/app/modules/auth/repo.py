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

import logging
import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.modules.auth.models import User, Membership, Role
from app.core.security.password import hash_password, verify_password

logger = logging.getLogger(__name__)


class AuthRepository:
    """Auth data access layer (Platform-First v2)
    
    Design principles:
    - Users are global (no company_id in User table)
    - Login is per-company via Membership (login_username unique per company)
    - Membership links user to company with role
    """
    
    def __init__(self, db: Session):
        """Initialize Repository
        
        Args:
            db: SQLAlchemy Session
        """
        self.db = db
    
    # ========== User CRUD (Global Identity) ==========
    
    def create_user(
        self,
        display_name: str,
        plain_password: str,
        email: Optional[str] = None,
        is_active: bool = True,
        is_otp: bool = False,
        must_change_password: bool = False
    ) -> User:
        """Create a new user (global identity, NO company_id)
        
        Args:
            display_name: Global display name
            plain_password: Plain text password (will be hashed)
            email: Email for notifications (optional, not unique)
            is_active: Active status (default: True)
            is_otp: Is OTP account (default: False)
            must_change_password: Force password change (default: False)
        
        Returns:
            User: Created user
        
        Raises:
            ValueError: If password is invalid
        """
        # Hash password using utility
        password_hash = hash_password(plain_password)
        
        # Create user
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
        """Get user by ID (global, no company_id needed)
        
        Args:
            user_id: User ID
        
        Returns:
            User or None if not found
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        logger.debug(f"Get user by id: user_id={user_id}, found={user is not None}")
        
        return user
    
    def update_password(self, user: User, new_plain_password: str) -> User:
        """Update user password
        
        Args:
            user: User object
            new_plain_password: New plain text password (will be hashed)
        
        Returns:
            User: Updated user
        """
        user.password_hash = hash_password(new_plain_password)
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"Updated password for user: id={user.id}")
        
        return user
    
    def update_last_login(self, user: User) -> User:
        """Update user last login timestamp
        
        Args:
            user: User object
        
        Returns:
            User: Updated user
        """
        user.last_login_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.debug(f"Updated last_login_at for user: id={user.id}")
        
        return user
    
    def verify_user_password(self, user: User, plain_password: str) -> bool:
        """Verify user password
        
        Args:
            user: User object
            plain_password: Plain text password to verify
        
        Returns:
            bool: True if password matches
        """
        return verify_password(plain_password, user.password_hash)
    
    # ========== Membership CRUD (User-Company Relationship) ==========
    
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
        """Create membership (link user to company with role and login credentials)
        
        Args:
            user_id: User ID
            company_id: Company ID
            role_id: Role ID (e.g., 'employee', 'company_admin')
            login_username: Per-company login username (unique per company)
            login_email: Per-company login email (optional)
            is_active: Membership active status (default: True)
        
        Returns:
            Membership: Created membership
        
        Raises:
            IntegrityError: If login_username already exists in company
            IntegrityError: If user already has membership in company
        """
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
        """Create a new user WITHOUT committing.

        Identical to create_user() but uses flush() instead of commit(),
        so the caller controls the transaction boundary.
        Use this for orchestration flows (onboarding, add-member) that
        also create a Membership in the same transaction.

        The caller MUST call db.commit() (or db.rollback()) after all
        related objects are flushed.
        """
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
        self.db.flush()  # write to DB but DO NOT commit
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
        """Create a Membership WITHOUT committing.

        Identical to create_membership() but uses flush() instead of commit().
        Use together with create_user_no_commit() so both objects live in
        the same transaction and can be rolled back atomically on failure.

        The caller MUST call db.commit() (or db.rollback()) after all
        related objects are flushed.
        """
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
        self.db.flush()  # write to DB but DO NOT commit
        logger.info(f"Flushed membership (no-commit): user_id={user_id}, company_id={company_id}, login_username={login_username}")
        return membership

    def get_membership_by_login(self, company_id: str, login_username: str) -> Optional[Membership]:
        """Get membership by company_id + login_username (for login)
        
        Args:
            company_id: Company ID
            login_username: Login username
        
        Returns:
            Membership or None if not found
        """
        membership = self.db.query(Membership).filter(
            and_(
                Membership.company_id == company_id,
                Membership.login_username == login_username
            )
        ).first()
        
        logger.debug(f"Get membership by login: company_id={company_id}, login_username={login_username}, found={membership is not None}")
        
        return membership
    
    def get_user_by_login(self, company_id: str, login_username: str) -> Optional[User]:
        """Get user by company_id + login_username (via membership)
        
        This is the primary login method for platform-first v2.
        
        Args:
            company_id: Company ID
            login_username: Login username
        
        Returns:
            User or None if not found
        """
        membership = self.get_membership_by_login(company_id, login_username)
        
        if not membership:
            logger.debug(f"Get user by login: no membership found for company_id={company_id}, login_username={login_username}")
            return None
        
        user = self.get_user_by_id(membership.user_id)
        
        logger.debug(f"Get user by login: company_id={company_id}, login_username={login_username}, user_id={user.id if user else None}")
        
        return user
    
    def get_user_memberships(self, user_id: uuid.UUID) -> List[Membership]:
        """Get all memberships for a user (all companies user can access)
        
        Args:
            user_id: User ID
        
        Returns:
            List[Membership]: List of memberships
        """
        memberships = self.db.query(Membership).filter(
            Membership.user_id == user_id
        ).all()
        
        logger.debug(f"Get user memberships: user_id={user_id}, count={len(memberships)}")
        
        return memberships
    
    def get_membership(self, user_id: uuid.UUID, company_id: str) -> Optional[Membership]:
        """Get membership for user in specific company
        
        Args:
            user_id: User ID
            company_id: Company ID
        
        Returns:
            Membership or None if not found
        """
        membership = self.db.query(Membership).filter(
            and_(
                Membership.user_id == user_id,
                Membership.company_id == company_id
            )
        ).first()
        
        logger.debug(f"Get membership: user_id={user_id}, company_id={company_id}, found={membership is not None}")
        
        return membership
    
    def user_has_company_access(self, user_id: uuid.UUID, company_id: str) -> bool:
        """Check if user has active membership in company
        
        Args:
            user_id: User ID
            company_id: Company ID
        
        Returns:
            bool: True if user has active membership
        """
        membership = self.get_membership(user_id, company_id)
        
        has_access = membership is not None and membership.is_active
        
        logger.debug(f"User has company access: user_id={user_id}, company_id={company_id}, has_access={has_access}")
        
        return has_access
    
    # ========== Role Queries ==========
    
    def get_role(self, role_id: str) -> Optional[Role]:
        """Get role by ID
        
        Args:
            role_id: Role ID
        
        Returns:
            Role or None if not found
        """
        role = self.db.query(Role).filter(Role.id == role_id).first()
        
        logger.debug(f"Get role: role_id={role_id}, found={role is not None}")
        
        return role


def get_auth_repository(db: Session) -> AuthRepository:
    """Get AuthRepository instance (FastAPI Dependency)
    
    Args:
        db: SQLAlchemy Session
    
    Returns:
        AuthRepository: Repository instance
    """
    return AuthRepository(db)
