"""create auth tables v2 platform-first

Revision ID: 3532deda024c
Revises: 005
Create Date: 2026-03-03 18:49:46.908728

WP-10-02B: Create auth schema v2 (platform-first architecture)
Implements AUTH_SCHEMA_SPEC_PLATFORM_FIRST_v2.md

Key changes from v1 (tenant-first):
- users: removed company_id, removed username, added display_name
- user_company_memberships: new table (replaces user_roles for membership + role)
- user_roles: removed (replaced by memberships.role_id)
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision: str = '3532deda024c'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create auth tables v2 (platform-first) and seed RBAC data"""
    
    # Table 1: roles (System Data, no company_id)
    op.create_table(
        'roles',
        sa.Column('id', sa.String(50), nullable=False, comment='Role ID (PK)'),
        sa.Column('name', sa.String(100), nullable=False, comment='Display name'),
        sa.Column('description', sa.Text(), nullable=True, comment='Role description'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Created timestamp (UTC)'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Table 2: permissions (System Data, no company_id)
    op.create_table(
        'permissions',
        sa.Column('id', sa.String(100), nullable=False, comment='Permission ID (PK)'),
        sa.Column('resource', sa.String(50), nullable=False, comment='Resource name'),
        sa.Column('action', sa.String(50), nullable=False, comment='Action name'),
        sa.Column('description', sa.Text(), nullable=True, comment='Permission description'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Created timestamp (UTC)'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resource', 'action', name='uq_permissions_resource_action')
    )
    op.create_index('idx_permissions_resource', 'permissions', ['resource'])
    
    # Table 3: users (Global Identity - NO company_id)
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='User ID (PK)'),
        sa.Column('display_name', sa.String(100), nullable=False, comment='Global display name'),
        sa.Column('email', sa.String(255), nullable=True, comment='Email for notifications (not unique)'),
        sa.Column('password_hash', sa.String(255), nullable=False, comment='Bcrypt/Argon2 hash'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('TRUE'), comment='Active status'),
        sa.Column('is_otp', sa.Boolean(), nullable=False, server_default=sa.text('FALSE'), comment='Is OTP account'),
        sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default=sa.text('FALSE'), comment='Force password change'),
        sa.Column('last_login_at', sa.DateTime(), nullable=True, comment='Last login (UTC)'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Created timestamp (UTC)'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Updated timestamp (UTC)'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    
    # Table 4: user_company_memberships (User-Company relationship + role)
    op.create_table(
        'user_company_memberships',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Membership ID (PK)'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='User ID (FK)'),
        sa.Column('company_id', sa.String(255), nullable=False, comment='Company ID (FK)'),
        sa.Column('role_id', sa.String(50), nullable=False, comment='Role ID (FK)'),
        sa.Column('login_username', sa.String(100), nullable=False, comment='Per-company login username'),
        sa.Column('login_email', sa.String(255), nullable=True, comment='Per-company login email (optional)'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('TRUE'), comment='Membership active status'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Created timestamp (UTC)'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Updated timestamp (UTC)'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('company_id', 'login_username', name='uq_memberships_company_login'),
        sa.UniqueConstraint('user_id', 'company_id', name='uq_memberships_user_company')
    )
    op.create_index('idx_memberships_company_login', 'user_company_memberships', ['company_id', 'login_username'])
    op.create_index('idx_memberships_user_id', 'user_company_memberships', ['user_id'])
    op.create_index('idx_memberships_company_id', 'user_company_memberships', ['company_id'])
    op.create_index('idx_memberships_company_email', 'user_company_memberships', ['company_id', 'login_email'])
    
    # Table 5: role_permissions (System Data, no company_id)
    op.create_table(
        'role_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Assignment ID (PK)'),
        sa.Column('role_id', sa.String(50), nullable=False, comment='Role ID (FK)'),
        sa.Column('permission_id', sa.String(100), nullable=False, comment='Permission ID (FK)'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Created timestamp (UTC)'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permissions_role_permission')
    )
    op.create_index('idx_role_permissions_role_id', 'role_permissions', ['role_id'])
    
    # Seed data (idempotent - check before insert)
    conn = op.get_bind()
    
    # Seed roles
    roles_data = [
        ('employee', 'Employee', 'Regular employee (can create own attendance)'),
        ('manager', 'Manager', 'Can approve attendance for team members'),
        ('company_admin', 'Company Admin', 'Full access within company'),
        ('customer_service', 'Customer Service', 'Can access multiple companies (assigned list)'),
    ]
    
    for role_id, name, description in roles_data:
        result = conn.execute(sa.text("SELECT COUNT(*) FROM roles WHERE id = :id"), {"id": role_id})
        if result.scalar() == 0:
            conn.execute(
                sa.text("INSERT INTO roles (id, name, description) VALUES (:id, :name, :description)"),
                {"id": role_id, "name": name, "description": description}
            )
    
    # Seed permissions
    permissions_data = [
        ('attendance:create:self', 'attendance', 'create:self', 'Create own attendance record'),
        ('attendance:approve', 'attendance', 'approve', 'Approve attendance records'),
        ('notifications:read:self', 'notifications', 'read:self', 'Read own notifications'),
        ('backup:export', 'backup', 'export', 'Export company backup'),
        ('backup:restore', 'backup', 'restore', 'Restore company backup'),
        ('audit:read', 'audit', 'read', 'Read audit logs'),
        ('audit:export', 'audit', 'export', 'Export audit logs'),
        ('audit:manage', 'audit', 'manage', 'Manage audit retention policies'),
        ('audit:purge', 'audit', 'purge', 'Purge old audit logs'),
        ('tenants:read', 'tenants', 'read', 'Read tenant information'),
        ('tenants:manage', 'tenants', 'manage', 'Manage tenants'),
    ]
    
    for perm_id, resource, action, description in permissions_data:
        result = conn.execute(sa.text("SELECT COUNT(*) FROM permissions WHERE id = :id"), {"id": perm_id})
        if result.scalar() == 0:
            conn.execute(
                sa.text("INSERT INTO permissions (id, resource, action, description) VALUES (:id, :resource, :action, :description)"),
                {"id": perm_id, "resource": resource, "action": action, "description": description}
            )
    
    # Seed role_permissions mappings
    role_permissions_data = [
        # employee
        ('employee', 'attendance:create:self'),
        ('employee', 'notifications:read:self'),
        # manager
        ('manager', 'attendance:create:self'),
        ('manager', 'attendance:approve'),
        ('manager', 'notifications:read:self'),
        ('manager', 'audit:read'),
        # company_admin
        ('company_admin', 'attendance:create:self'),
        ('company_admin', 'attendance:approve'),
        ('company_admin', 'notifications:read:self'),
        ('company_admin', 'backup:export'),
        ('company_admin', 'backup:restore'),
        ('company_admin', 'audit:read'),
        ('company_admin', 'audit:export'),
        ('company_admin', 'audit:manage'),
        ('company_admin', 'audit:purge'),
        ('company_admin', 'tenants:read'),
        ('company_admin', 'tenants:manage'),
        # customer_service
        ('customer_service', 'attendance:approve'),
        ('customer_service', 'audit:read'),
        ('customer_service', 'tenants:read'),
    ]
    
    for role_id, permission_id in role_permissions_data:
        result = conn.execute(
            sa.text("SELECT COUNT(*) FROM role_permissions WHERE role_id = :role_id AND permission_id = :permission_id"),
            {"role_id": role_id, "permission_id": permission_id}
        )
        if result.scalar() == 0:
            conn.execute(
                sa.text("INSERT INTO role_permissions (id, role_id, permission_id) VALUES (:id, :role_id, :permission_id)"),
                {"id": str(uuid.uuid4()), "role_id": role_id, "permission_id": permission_id}
            )


def downgrade() -> None:
    """Drop auth tables v2 (reverse order to handle FK constraints)"""
    op.drop_index('idx_role_permissions_role_id', table_name='role_permissions')
    op.drop_table('role_permissions')
    
    op.drop_index('idx_memberships_company_email', table_name='user_company_memberships')
    op.drop_index('idx_memberships_company_id', table_name='user_company_memberships')
    op.drop_index('idx_memberships_user_id', table_name='user_company_memberships')
    op.drop_index('idx_memberships_company_login', table_name='user_company_memberships')
    op.drop_table('user_company_memberships')
    
    op.drop_index('idx_users_is_active', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
    
    op.drop_index('idx_permissions_resource', table_name='permissions')
    op.drop_table('permissions')
    
    op.drop_table('roles')
