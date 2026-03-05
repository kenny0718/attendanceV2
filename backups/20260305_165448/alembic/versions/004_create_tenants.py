"""create tenants table

Revision ID: 004
Revises: 003
Create Date: 2026-03-02

Phase 9: Create tenants table for tenant existence validation
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tenants table
    
    Design:
    - id (VARCHAR 50) as PK (company_id)
    - name (VARCHAR 255) NOT NULL UNIQUE
    - is_active (BOOLEAN) DEFAULT TRUE
    - timezone (VARCHAR 50) DEFAULT 'UTC'
    - created_at (TIMESTAMP) DEFAULT NOW()
    - updated_at (TIMESTAMP) DEFAULT NOW()
    - Index on is_active for fast active tenant queries
    """
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(50), primary_key=True, comment='Company ID (tenant identifier)'),
        sa.Column('name', sa.String(255), nullable=False, unique=True, comment='Company name'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('TRUE'), comment='Active status'),
        sa.Column('timezone', sa.String(50), nullable=False, server_default=sa.text("'UTC'"), comment='Company timezone'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'), comment='Created timestamp (UTC)'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'), comment='Updated timestamp (UTC)'),
    )
    
    # Index for fast active tenant queries
    op.create_index('idx_tenants_is_active', 'tenants', ['is_active'])


def downgrade() -> None:
    """Drop tenants table"""
    op.drop_index('idx_tenants_is_active', table_name='tenants')
    op.drop_table('tenants')
