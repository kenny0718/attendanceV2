"""add tax_id to tenants

Revision ID: 014_add_tax_id_to_tenants
Revises: 013_wp_11_09_sched_members
Create Date: 2026-04-10 00:30:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '014_add_tax_id_to_tenants'
down_revision: Union[str, None] = '013_wp_11_09_sched_members'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tenants', sa.Column('tax_id', sa.String(length=20), nullable=True, comment='Company tax ID'))
    op.create_index('idx_tenants_tax_id', 'tenants', ['tax_id'], unique=False)
    op.create_unique_constraint('uq_tenants_tax_id', 'tenants', ['tax_id'])


def downgrade() -> None:
    op.drop_constraint('uq_tenants_tax_id', 'tenants', type_='unique')
    op.drop_index('idx_tenants_tax_id', table_name='tenants')
    op.drop_column('tenants', 'tax_id')
