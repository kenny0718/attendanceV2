"""WP-S1-XX: Create shift_segments table

Revision ID: 012_wp_s1_xx
Revises: 011_s1_11d
Create Date: 2026-04-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '012_wp_s1_xx'
down_revision = '011_s1_11d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'shift_segments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.String(255), nullable=False),
        sa.Column('shift_template_id', UUID(as_uuid=True), nullable=False),
        sa.Column('segment_index', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('day_offset_start', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('day_offset_end', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shift_template_id'], ['shift_templates.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('shift_template_id', 'segment_index', name='uq_shift_segments_template_index'),
    )
    op.create_index('idx_shift_segments_company', 'shift_segments', ['company_id'])
    op.create_index('idx_shift_segments_template', 'shift_segments', ['shift_template_id'])
    op.create_index('idx_shift_segments_company_template', 'shift_segments', ['company_id', 'shift_template_id'])


def downgrade() -> None:
    op.drop_index('idx_shift_segments_company_template', table_name='shift_segments')
    op.drop_index('idx_shift_segments_template', table_name='shift_segments')
    op.drop_index('idx_shift_segments_company', table_name='shift_segments')
    op.drop_table('shift_segments')
