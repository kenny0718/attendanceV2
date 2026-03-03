"""create auth tables

Revision ID: 2167a6735c37
Revises: 005
Create Date: 2026-03-03 12:33:22.360587

WP-10-02: Create auth schema (users, roles, permissions, user_roles, role_permissions)
Implements AUTH_SCHEMA_SPEC.md exactly as specified
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = '2167a6735c37'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create auth tables and seed RBAC data"""
    
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
    
    # Table 3: users (Tenant Data, has company_id)
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='User ID (PK)'),
        sa.Column('company_id', sa.String(255), nullable=False, comment='Company ID (Tenant Isolation)'),
        sa.Column('username', sa.String(100), nullable=False, comment='Username for login'),
        sa.Column('email', sa.String(255), nullable=False, comment='Email address'),
        sa.Column('password_hash', sa.String(255), nullable=False, comment='Bcrypt/Argon2 hash'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('TRUE'), comment='Active status'),
        sa.Column('is_otp', sa.Boolean(), nullable=False, server_default=sa.text('FALSE'), comment='Is OTP account'),
        sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default=sa.text('FALSE'), comment='Force password change'),
        sa.Column('last_login_at', sa.DateTime(), nullable=True, comment='Last login (UTC)'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Created timestamp (UTC)'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Updated timestamp (UTC)'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('company_id', 'username', name='uq_users_company_username'),
        sa.UniqueConstraint('company_id', 'email', name='uq_users_company_email')
    )
    op.create_index('idx_users_company_id', 'users', ['company_id'])
    op.create_index('idx_users_company_username', 'users', ['company_id', 'username'])
    op.create_index('idx_users_company_email', 'users', ['company_id', 'email'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    
    # Table 4: user_roles (Tenant Data, has company_id)
    op.create_table(
        'user_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Assignment ID (PK)'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='User ID (FK)'),
        sa.Column('role_id', sa.String(50), nullable=False, comment='Role ID (FK)'),
        sa.Column('company_id', sa.String(255), nullable=False, comment='Company ID (Tenant Isolation)'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Created timestamp (UTC)'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'role_id', 'company_id', name='uq_user_roles_user_role_company')
    )
    op.create_index('idx_user_roles_user_id', 'user_roles', ['user_id'])
    op.create_index('idx_user_roles_company_id', 'user_roles', ['company_id'])
    op.create_index('idx_user_roles_user_company', 'user_roles', ['user_id', 'company_id'])
    
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
    """Drop auth tables (reverse order to handle FK constraints)"""
    op.drop_index('idx_role_permissions_role_id', table_name='role_permissions')
    op.drop_table('role_permissions')
    
    op.drop_index('idx_user_roles_user_company', table_name='user_roles')
    op.drop_index('idx_user_roles_company_id', table_name='user_roles')
    op.drop_index('idx_user_roles_user_id', table_name='user_roles')
    op.drop_table('user_roles')
    
    op.drop_index('idx_users_is_active', table_name='users')
    op.drop_index('idx_users_company_email', table_name='users')
    op.drop_index('idx_users_company_username', table_name='users')
    op.drop_index('idx_users_company_id', table_name='users')
    op.drop_table('users')
    
    op.drop_index('idx_permissions_resource', table_name='permissions')
    op.drop_table('permissions')
    
    op.drop_table('roles')
