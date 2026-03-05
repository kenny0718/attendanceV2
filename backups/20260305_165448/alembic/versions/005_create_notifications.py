"""create notifications table

Revision ID: 005
Revises: 004
Create Date: 2026-03-03

Gate 3 (G3-02): Add notifications table migration
- Replaces Base.metadata.create_all() for notifications
- Idempotent: checks if table exists before creating
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '3532deda024c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create notifications table with indexes"""
    # Check if table exists (idempotent)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'notifications' not in inspector.get_table_names():
        # Create notifications table
        op.create_table(
            'notifications',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='通知記錄 ID（UUID）'),
            sa.Column('company_id', sa.String(length=255), nullable=False, comment='公司 ID（Tenant Isolation）'),
            sa.Column('event_type', sa.String(length=255), nullable=False, comment='事件類型（例如：attendance.approved）'),
            sa.Column('event_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='完整事件 payload（JSONB 格式，供稽核）'),
            sa.Column('created_at', sa.DateTime(), nullable=False, comment='建立時間（UTC）'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes
        op.create_index('idx_notifications_company_id', 'notifications', ['company_id'], unique=False)
        op.create_index('idx_notifications_company_created', 'notifications', ['company_id', 'created_at'], unique=False)


def downgrade() -> None:
    """Drop notifications table and indexes"""
    # Drop indexes first
    op.drop_index('idx_notifications_company_created', table_name='notifications')
    op.drop_index('idx_notifications_company_id', table_name='notifications')
    
    # Drop table
    op.drop_table('notifications')
