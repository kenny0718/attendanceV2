"""Auth data models

WP-10-03: Auth Repository + Password Hashing
Implements AUTH_SCHEMA_SPEC.md exactly as specified
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class User(Base):
    """User model (Tenant Data)
    
    Design principles:
    - Tenant-scoped: company_id is required for all queries
    - Per-tenant uniqueness: UNIQUE(company_id, username) and UNIQUE(company_id, email)
    - Password stored as hash only (never plaintext)
    """
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, comment="User ID (PK)")
    
    # Tenant isolation
    company_id = Column(
        String(255),
        ForeignKey('tenants.id', ondelete='CASCADE'),
        nullable=False,
        comment="Company ID (Tenant Isolation)"
    )
    
    # Authentication
    username = Column(String(100), nullable=False, comment="Username for login")
    email = Column(String(255), nullable=False, comment="Email address")
    password_hash = Column(String(255), nullable=False, comment="Bcrypt/Argon2 hash")
    
    # Status flags
    is_active = Column(Boolean, nullable=False, default=True, comment="Active status")
    is_otp = Column(Boolean, nullable=False, default=False, comment="Is OTP account")
    must_change_password = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Force password change"
    )
    
    # Timestamps
    last_login_at = Column(DateTime, nullable=True, comment="Last login (UTC)")
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Created timestamp (UTC)"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Updated timestamp (UTC)"
    )
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_users_company_id', 'company_id'),
        Index('idx_users_company_username', 'company_id', 'username'),
        Index('idx_users_company_email', 'company_id', 'email'),
        Index('idx_users_is_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, company_id={self.company_id}, username={self.username})>"


class Role(Base):
    """Role model (System Data)
    
    Design principles:
    - Global roles (no company_id)
    - Predefined roles seeded in migration
    """
    
    __tablename__ = "roles"
    
    id = Column(String(50), primary_key=True, comment="Role ID (PK)")
    name = Column(String(100), nullable=False, comment="Display name")
    description = Column(String, nullable=True, comment="Role description")
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Created timestamp (UTC)"
    )
    
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


class Permission(Base):
    """Permission model (System Data)
    
    Design principles:
    - Global permissions (no company_id)
    - Predefined permissions seeded in migration
    """
    
    __tablename__ = "permissions"
    
    id = Column(String(100), primary_key=True, comment="Permission ID (PK)")
    resource = Column(String(50), nullable=False, comment="Resource name")
    action = Column(String(50), nullable=False, comment="Action name")
    description = Column(String, nullable=True, comment="Permission description")
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Created timestamp (UTC)"
    )
    
    __table_args__ = (
        Index('idx_permissions_resource', 'resource'),
    )
    
    def __repr__(self):
        return f"<Permission(id={self.id}, resource={self.resource}, action={self.action})>"


class UserRole(Base):
    """User-Role assignment (Tenant Data)
    
    Design principles:
    - Tenant-scoped: company_id required
    - Links users to roles within a company
    """
    
    __tablename__ = "user_roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, comment="Assignment ID (PK)")
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        comment="User ID (FK)"
    )
    role_id = Column(
        String(50),
        ForeignKey('roles.id', ondelete='CASCADE'),
        nullable=False,
        comment="Role ID (FK)"
    )
    company_id = Column(
        String(255),
        ForeignKey('tenants.id', ondelete='CASCADE'),
        nullable=False,
        comment="Company ID (Tenant Isolation)"
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Created timestamp (UTC)"
    )
    
    __table_args__ = (
        Index('idx_user_roles_user_id', 'user_id'),
        Index('idx_user_roles_company_id', 'company_id'),
        Index('idx_user_roles_user_company', 'user_id', 'company_id'),
    )
    
    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id}, company_id={self.company_id})>"


class RolePermission(Base):
    """Role-Permission mapping (System Data)
    
    Design principles:
    - Global mappings (no company_id)
    - Defines which permissions each role has
    """
    
    __tablename__ = "role_permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, comment="Assignment ID (PK)")
    role_id = Column(
        String(50),
        ForeignKey('roles.id', ondelete='CASCADE'),
        nullable=False,
        comment="Role ID (FK)"
    )
    permission_id = Column(
        String(100),
        ForeignKey('permissions.id', ondelete='CASCADE'),
        nullable=False,
        comment="Permission ID (FK)"
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Created timestamp (UTC)"
    )
    
    __table_args__ = (
        Index('idx_role_permissions_role_id', 'role_id'),
    )
    
    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"
