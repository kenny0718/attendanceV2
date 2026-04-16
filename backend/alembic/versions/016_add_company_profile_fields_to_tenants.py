"""add tenant company profile fields

Revision ID: 016_add_company_profile_fields_to_tenants
Revises: 015_remove_legacy_manager_role
Create Date: 2026-04-13 20:40:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision = '016_add_company_profile_fields_to_tenants'
down_revision = '015_remove_legacy_manager_role'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tenants', sa.Column('display_name', sa.String(length=255), nullable=True, comment='Company display name'))
    op.add_column('tenants', sa.Column('owner_name', sa.String(length=255), nullable=True, comment='Company owner name'))
    op.add_column('tenants', sa.Column('registered_address', sa.String(length=500), nullable=True, comment='Company registered address'))
    op.add_column('tenants', sa.Column('contact_address', sa.String(length=500), nullable=True, comment='Company contact address'))
    op.add_column('tenants', sa.Column('contact_phone', sa.String(length=50), nullable=True, comment='Company contact phone'))
    op.add_column('tenants', sa.Column('contact_email', sa.String(length=255), nullable=True, comment='Company contact email'))


def downgrade() -> None:
    op.drop_column('tenants', 'contact_email')
    op.drop_column('tenants', 'contact_phone')
    op.drop_column('tenants', 'contact_address')
    op.drop_column('tenants', 'registered_address')
    op.drop_column('tenants', 'owner_name')
    op.drop_column('tenants', 'display_name')
