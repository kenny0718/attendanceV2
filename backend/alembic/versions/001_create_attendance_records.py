"""create attendance_records table

Revision ID: 001
Revises: 
Create Date: 2026-01-25

Phase 4: 建立 attendance_records 表（符合 SA_MODULE_SPEC v1.7）
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """建立 attendance_records 表
    
    設計原則（SA_MODULE_SPEC v1.7 第 18 條）：
    1. 主鍵使用 UUID（避免單一租戶還原時 ID 衝突）
    2. 必須包含 company_id（Tenant Isolation P0）
    3. 為 company_id 建立索引（支援高效匯出與查詢）
    """
    op.create_table(
        'attendance_records',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, comment='考勤記錄 ID（UUID）'),
        sa.Column('company_id', sa.String(255), nullable=False, index=True, comment='公司 ID（Tenant Isolation）'),
        sa.Column('employee_id', sa.String(255), nullable=False, comment='員工 ID'),
        sa.Column('approved_by', sa.String(255), nullable=True, comment='核准人 ID'),
        sa.Column('approved_at', sa.DateTime(), nullable=True, comment='核准時間（UTC）'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'), comment='建立時間（UTC）'),
    )
    
    # 建立索引（支援單一租戶全量抽取與高效查詢）
    op.create_index('idx_attendance_company_id', 'attendance_records', ['company_id'])
    op.create_index('idx_attendance_company_created', 'attendance_records', ['company_id', 'created_at'])


def downgrade() -> None:
    """刪除 attendance_records 表"""
    op.drop_index('idx_attendance_company_created', table_name='attendance_records')
    op.drop_index('idx_attendance_company_id', table_name='attendance_records')
    op.drop_table('attendance_records')
