"""Auth Repository (Data Access Layer)

WP-10-03: Auth Repository + Password Hashing
Implements tenant-aware user queries with password hashing
"""

import logging
import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.modules.auth.models import User, UserRole
from app.core.security.password import hash_password, verify_password

logger = logging.getLogger(__name__)


class AuthRepository:
    """Auth data access layer
    
    Design principles:
    - All user queries are tenant-aware (require company_id)
    - Password hashing is handled automatically via utility
    - Per-tenant uniqueness enforced by DB constraints
    """
    
    def __init__(self, db: Session):
        """Initialize Repository
        
        Args:
            db: SQLAlchemy Session
        """
        self.db = db
    
    def create_user(
        self,
        company_id: str,
        username: str,
        email: str,
        plain_password: str,
        is_active: bool = True,
        is_otp: bool = False,
        must_change_password: bool = False
    ) -> User:
        """Create a new user (tenant-scoped)
        
        Args:
            company_id: Company ID (tenant isolation)
            username: Username for login
            email: Email address
            plain_password: Plain text password (will be hashed)
            is_active: Active status (default: True)
            is_otp: Is OTP account (default: False)
            must_change_password: Force password change (default: False)
        
        Returns:
            User: Created user
        
        Raises:
            ValueError: If password is invalid
            IntegrityError: If username/email already exists in company
        """
        # Hash password using utility
        password_hash = hash_password(plain_password)
        
        # Create user
        user = User(
            id=uuid.uuid4(),
            company_id=company_id,
            username=username,
            email=email,
            password_hash=password_hash,
            is_active=is_active,
            is_otp=is_otp,
            must_change_password=must_change_password
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"Created user: id={user.id}, company_id={company_id}, username={username}")
        
        return user
    
    def get_user_by_id(self, company_id: str, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID (tenant-scoped)
        
        Args:
            company_id: Company ID (tenant isolation)
            user_id: User ID
        
        Returns:
            User or None if not found
        """
        user = self.db.query(User).filter(
            and_(
                User.id == user_id,
                User.company_id == company_id
            )
        ).first()
        
        logger.debug(f"Get user by id: company_id={company_id}, user_id={user_id}, found={user is not None}")
        
        return user
    
    def get_user_by_username(self, company_id: str, username: str) -> Optional[User]:
        """Get user by username (tenant-scoped)
        
        Args:
            company_id: Company ID (tenant isolation)
            username: Username
        
        Returns:
            User or None if not found
        """
        user = self.db.query(User).filter(
            and_(
                User.company_id == company_id,
                User.username == username
            )
        ).first()
        
        logger.debug(f"Get user by username: company_id={company_id}, username={username}, found={user is not None}")
        
        return user
    
    def get_user_by_email(self, company_id: str, email: str) -> Optional[User]:
        """Get user by email (tenant-scoped)
        
        Args:
            company_id: Company ID (tenant isolation)
            email: Email address
        
        Returns:
            User or None if not found
        """
        user = self.db.query(User).filter(
            and_(
                User.company_id == company_id,
                User.email == email
            )
        ).first()
        
        logger.debug(f"Get user by email: company_id={company_id}, email={email}, found={user is not None}")
        
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
        
        logger.info(f"Updated password for user: id={user.id}, company_id={user.company_id}")
        
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
    
    def assign_role(self, company_id: str, user_id: uuid.UUID, role_id: str) -> UserRole:
        """Assign role to user (tenant-scoped)
        
        Args:
            company_id: Company ID (tenant isolation)
            user_id: User ID
            role_id: Role ID
        
        Returns:
            UserRole: Created assignment
        """
        user_role = UserRole(
            id=uuid.uuid4(),
            user_id=user_id,
            role_id=role_id,
            company_id=company_id
        )
        
        self.db.add(user_role)
        self.db.commit()
        self.db.refresh(user_role)
        
        logger.info(f"Assigned role: user_id={user_id}, role_id={role_id}, company_id={company_id}")
        
        return user_role


def get_auth_repository(db: Session) -> AuthRepository:
    """Get AuthRepository instance (FastAPI Dependency)
    
    Args:
        db: SQLAlchemy Session
    
    Returns:
        AuthRepository: Repository instance
    """
    return AuthRepository(db)
