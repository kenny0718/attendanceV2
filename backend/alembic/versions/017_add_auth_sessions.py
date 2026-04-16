"""add auth sessions for sliding session management

Revision ID: 017_add_auth_sessions
Revises: 016_add_company_profile_fields_to_tenants
Create Date: 2026-04-15 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '017_add_auth_sessions'
down_revision = '016_add_company_profile_fields_to_tenants'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'auth_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Auth session ID (PK)'),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='User ID (FK)'),
        sa.Column('company_id', sa.String(length=255), nullable=False, comment='Active company scope'),
        sa.Column('membership_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Membership ID (FK)'),
        sa.Column('role_id', sa.String(length=50), nullable=False, comment='Role ID in this session'),
        sa.Column('refresh_token_hash', sa.String(length=255), nullable=False, comment='Hashed refresh token'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('TRUE'), comment='Session active state'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', CURRENT_TIMESTAMP)"), comment='Created timestamp (UTC)'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', CURRENT_TIMESTAMP)"), comment='Updated timestamp (UTC)'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text("TIMEZONE('utc', CURRENT_TIMESTAMP)"), comment='Last authenticated activity timestamp (UTC)'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, comment='Refresh token expiry (UTC)'),
        sa.Column('absolute_expires_at', sa.DateTime(timezone=True), nullable=False, comment='Absolute session expiry (UTC)'),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True, comment='Revoked timestamp (UTC)'),
        sa.Column('revoke_reason', sa.String(length=100), nullable=True, comment='Why this session was revoked'),
        sa.Column('user_agent', sa.String(length=500), nullable=True, comment='User agent snapshot'),
        sa.Column('ip_address', sa.String(length=64), nullable=True, comment='IP address snapshot'),
        sa.ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['membership_id'], ['user_company_memberships.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_auth_sessions_user_id', 'auth_sessions', ['user_id'])
    op.create_index('idx_auth_sessions_membership_id', 'auth_sessions', ['membership_id'])
    op.create_index('idx_auth_sessions_company_id', 'auth_sessions', ['company_id'])
    op.create_index('idx_auth_sessions_is_active', 'auth_sessions', ['is_active'])
    op.create_index('idx_auth_sessions_expires_at', 'auth_sessions', ['expires_at'])


def downgrade() -> None:
    op.drop_index('idx_auth_sessions_expires_at', table_name='auth_sessions')
    op.drop_index('idx_auth_sessions_is_active', table_name='auth_sessions')
    op.drop_index('idx_auth_sessions_company_id', table_name='auth_sessions')
    op.drop_index('idx_auth_sessions_membership_id', table_name='auth_sessions')
    op.drop_index('idx_auth_sessions_user_id', table_name='auth_sessions')
    op.drop_table('auth_sessions')
