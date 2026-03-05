"""create audit retention policies table

Revision ID: 003
Revises: 002
Create Date: 2026-01-28

Phase 8: 新增 audit_retention_policies 表
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """升級：建立 audit_retention_policies 表"""
    op.create_table(
        'audit_retention_policies',
        sa.Column('company_id', sa.String(length=255), nullable=False, comment='公司 ID'),
        sa.Column('retention_days', sa.Integer(), nullable=False, comment='保留天數（7 ~ 3650）'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='建立時間（UTC）'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), comment='更新時間（UTC）'),
        sa.PrimaryKeyConstraint('company_id'),
        comment='稽核紀錄保留政策'
    )


def downgrade():
    """降級：刪除 audit_retention_policies 表"""
    op.drop_table('audit_retention_policies')

