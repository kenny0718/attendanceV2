"""Add company_entitlements and support_company_assignments tables

Revision ID: wp_11_04a_entitlements
Revises: 3532deda024c
Create Date: 2026-03-04

WP-11-04A: Company Entitlements + SuperAdmin 管理 + customer_service Scope
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'wp_11_04a_entitlements'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 建立 company_entitlements 表
    op.create_table(
        'company_entitlements',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Entitlement ID (PK)'),
        sa.Column('company_id', sa.String(length=50), nullable=False, comment='Company ID (FK)'),
        sa.Column('feature_key', sa.String(length=100), nullable=False, comment='Feature key'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='false', comment='Is feature enabled'),
        sa.Column('updated_by_user_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Last updated by user ID (FK)'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Last updated timestamp (UTC)'),
        sa.ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'feature_key', name='uq_company_entitlements_company_feature')
    )
    op.create_index('idx_company_entitlements_company_id', 'company_entitlements', ['company_id'])
    op.create_index('idx_company_entitlements_feature_key', 'company_entitlements', ['feature_key'])
    
    # 2. 建立 support_company_assignments 表
    op.create_table(
        'support_company_assignments',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Customer service user ID (FK)'),
        sa.Column('company_id', sa.String(length=50), nullable=False, comment='Company ID (FK)'),
        sa.Column('assigned_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Assignment timestamp (UTC)'),
        sa.Column('assigned_by_user_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Assigned by user ID (FK)'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('user_id', 'company_id')
    )
    op.create_index('idx_support_company_assignments_user_id', 'support_company_assignments', ['user_id'])
    op.create_index('idx_support_company_assignments_company_id', 'support_company_assignments', ['company_id'])


def downgrade():
    # 刪除 support_company_assignments 表
    op.drop_index('idx_support_company_assignments_company_id', table_name='support_company_assignments')
    op.drop_index('idx_support_company_assignments_user_id', table_name='support_company_assignments')
    op.drop_table('support_company_assignments')
    
    # 刪除 company_entitlements 表
    op.drop_index('idx_company_entitlements_feature_key', table_name='company_entitlements')
    op.drop_index('idx_company_entitlements_company_id', table_name='company_entitlements')
    op.drop_table('company_entitlements')
