"""Auth data models (Platform-First v2)

WP-10-02B: Auth Models Rewrite
Implements AUTH_SCHEMA_SPEC_PLATFORM_FIRST_v2.md

Key changes from v1 (tenant-first):
- User: removed company_id, removed username, added display_name
- Membership: new model (user-company relationship + role)
- UserRole: removed (replaced by Membership.role_id)
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class User(Base):
    """User model (Global Identity)
    
    Design principles (v2 platform-first):
    - Global identity: NO company_id (user exists across all companies)
    - NO username: login username is per-company (in Membership)
    - display_name: global display name for UI
    - email: for notifications only (not unique, not for login)
    """
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, comment="User ID (PK)")
    display_name = Column(String(100), nullable=False, comment="Global display name")
    email = Column(String(255), nullable=True, comment="Email for notifications (not unique)")
    password_hash = Column(String(255), nullable=False, comment="Bcrypt/Argon2 hash")
    is_active = Column(Boolean, nullable=False, default=True, comment="Active status")
    is_otp = Column(Boolean, nullable=False, default=False, comment="Is OTP account")
    must_change_password = Column(Boolean, nullable=False, default=False, comment="Force password change")
    last_login_at = Column(DateTime, nullable=True, comment="Last login (UTC)")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Created timestamp (UTC)")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Updated timestamp (UTC)")
    
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_is_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, display_name={self.display_name})>"


class Membership(Base):
    """User-Company Membership model (replaces UserRole)"""
    
    __tablename__ = "user_company_memberships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, comment="Membership ID (PK)")
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment="User ID (FK)")
    company_id = Column(String(255), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, comment="Company ID (FK)")
    role_id = Column(String(50), ForeignKey('roles.id', ondelete='CASCADE'), nullable=False, comment="Role ID (FK)")
    login_username = Column(String(100), nullable=False, comment="Per-company login username")
    login_email = Column(String(255), nullable=True, comment="Per-company login email (optional)")
    is_active = Column(Boolean, nullable=False, default=True, comment="Membership active status")
    uses_schedule = Column(Boolean, nullable=False, default=False, comment="Whether this member should see schedule features")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Created timestamp (UTC)")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Updated timestamp (UTC)")
    
    __table_args__ = (
        UniqueConstraint('company_id', 'login_username', name='uq_memberships_company_login'),
        UniqueConstraint('user_id', 'company_id', name='uq_memberships_user_company'),
        Index('idx_memberships_company_login', 'company_id', 'login_username'),
        Index('idx_memberships_user_id', 'user_id'),
        Index('idx_memberships_company_id', 'company_id'),
        Index('idx_memberships_company_email', 'company_id', 'login_email'),
    )
    
    def __repr__(self):
        return f"<Membership(user_id={self.user_id}, company_id={self.company_id}, role_id={self.role_id})>"


class Role(Base):
    __tablename__ = "roles"
    
    id = Column(String(50), primary_key=True, comment="Role ID (PK)")
    name = Column(String(100), nullable=False, comment="Display name")
    description = Column(String, nullable=True, comment="Role description")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Created timestamp (UTC)")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(String(100), primary_key=True, comment="Permission ID (PK)")
    resource = Column(String(50), nullable=False, comment="Resource name")
    action = Column(String(50), nullable=False, comment="Action name")
    description = Column(String, nullable=True, comment="Permission description")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Created timestamp (UTC)")
    
    __table_args__ = (
        UniqueConstraint('resource', 'action', name='uq_permissions_resource_action'),
        Index('idx_permissions_resource', 'resource'),
    )
    
    def __repr__(self):
        return f"<Permission(id={self.id}, resource={self.resource}, action={self.action})>"


class RolePermission(Base):
    __tablename__ = "role_permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, comment="Assignment ID (PK)")
    role_id = Column(String(50), ForeignKey('roles.id', ondelete='CASCADE'), nullable=False, comment="Role ID (FK)")
    permission_id = Column(String(100), ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False, comment="Permission ID (FK)")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Created timestamp (UTC)")
    
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='uq_role_permissions_role_permission'),
        Index('idx_role_permissions_role_id', 'role_id'),
    )
    
    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"
