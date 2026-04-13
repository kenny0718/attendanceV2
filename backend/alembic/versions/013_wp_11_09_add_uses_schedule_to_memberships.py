"""add uses_schedule to memberships

Revision ID: 013_wp_11_09_sched_members
Revises: 012_wp_s1_xx
Create Date: 2026-04-10 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '013_wp_11_09_sched_members'
down_revision: Union[str, None] = '012_wp_s1_xx'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'user_company_memberships',
        sa.Column('uses_schedule', sa.Boolean(), nullable=False, server_default=sa.text('FALSE'), comment='Whether this member should see schedule features')
    )


def downgrade() -> None:
    op.drop_column('user_company_memberships', 'uses_schedule')
