"""create audit_logs table

Revision ID: 002
Revises: 001
Create Date: 2026-01-27

Phase 6C: 建立 audit_logs 表（稽核紀錄）
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """建立 audit_logs 表
    
    用途：
    - 記錄所有備份匯出/還原操作
    - 追蹤誰、何時、對哪家公司、做了什麼、成功/失敗、影響筆數
    """
    op.create_table(
        'audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, comment='稽核紀錄 ID（UUID）'),
        sa.Column('company_id', sa.String(255), nullable=False, comment='目標公司 ID'),
        sa.Column('action', sa.String(255), nullable=False, comment='操作類型（例如：backup.export, backup.restore）'),
        sa.Column('status', sa.String(50), nullable=False, comment='操作狀態（success / fail）'),
        sa.Column('actor', sa.String(255), nullable=False, comment='執行者（從 X-Actor / X-User header 或 fallback 為 system）'),
        sa.Column('request_id', sa.String(255), nullable=True, comment='請求 ID（從 X-Request-ID header）'),
        sa.Column('ip', sa.String(255), nullable=True, comment='來源 IP 位址'),
        sa.Column('user_agent', sa.String(500), nullable=True, comment='User Agent'),
        sa.Column('meta', JSONB, nullable=False, server_default='{}', comment='操作 meta 資料（例如：tables, counts, clear_existing, error_code）'),
        sa.Column('error', sa.Text(), nullable=True, comment='錯誤訊息（失敗時記錄，最多 2000 字）'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'), comment='建立時間（UTC）'),
    )
    
    # 建立索引（支援查詢）
    op.create_index('idx_audit_logs_company_created', 'audit_logs', ['company_id', 'created_at'])
    op.create_index('idx_audit_logs_action_created', 'audit_logs', ['action', 'created_at'])


def downgrade() -> None:
    """刪除 audit_logs 表"""
    op.drop_index('idx_audit_logs_action_created', table_name='audit_logs')
    op.drop_index('idx_audit_logs_company_created', table_name='audit_logs')
    op.drop_table('audit_logs')

