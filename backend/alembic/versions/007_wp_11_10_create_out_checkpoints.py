"""WP-11-10: Create attendance_out_checkpoints table

Revision ID: 007_wp_11_10
Revises: 006_expand_session_status
Create Date: 2026-03-05

Design: OUT checkpoint events are standalone events (not paired intervals)
- Multiple OUT checkpoints allowed per session
- Mobile device MUST provide GPS
- PC device MAY provide GPS (optional)
- device_type MUST be recorded (mobile|pc)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_wp_11_10'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    """Create attendance_out_checkpoints table"""
    
    op.create_table(
        'attendance_out_checkpoints',
        
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, 
                  server_default=sa.text('gen_random_uuid()'),
                  comment='Checkpoint ID (PK)'),
        
        # Tenant Isolation (MANDATORY per SA v1.9)
        sa.Column('company_id', sa.String(255), nullable=False, 
                  comment='公司 ID (tenant isolation)'),
        
        # User & Session
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, 
                  comment='員工 ID (global user)'),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True, 
                  comment='所屬 session (nullable: allow checkpoints without open session)'),
        
        # Timestamp (server-set, NOT from client)
        sa.Column('punch_time', sa.DateTime(timezone=True), nullable=False, 
                  server_default=sa.text('NOW()'),
                  comment='打卡時間 (UTC, server-set)'),
        
        # Device Info (MANDATORY)
        sa.Column('device_type', sa.String(20), nullable=False, 
                  comment='裝置類型 (mobile|pc)'),
        
        # GPS Data (MANDATORY for mobile, OPTIONAL for pc)
        sa.Column('gps_lat', sa.Numeric(10, 8), nullable=True, 
                  comment='緯度 (required for mobile)'),
        sa.Column('gps_lng', sa.Numeric(11, 8), nullable=True, 
                  comment='經度 (required for mobile)'),
        sa.Column('gps_accuracy_m', sa.Numeric(8, 2), nullable=True, 
                  comment='GPS 精度 (公尺)'),
        sa.Column('gps_captured_at', sa.DateTime(timezone=True), nullable=True, 
                  comment='GPS 擷取時間 (client-side timestamp)'),
        sa.Column('gps_provider', sa.String(20), nullable=True, 
                  comment='GPS 提供者 (gps|network|fused)'),
        
        # Client Context (optional, for debugging)
        sa.Column('client_timezone', sa.String(50), nullable=True, 
                  comment='客戶端時區'),
        sa.Column('client_user_agent', sa.Text, nullable=True, 
                  comment='User Agent'),
        sa.Column('ip_address', sa.String(45), nullable=True, 
                  comment='IP 地址 (IPv4/IPv6)'),
        
        # Notes
        sa.Column('notes', sa.Text, nullable=True, 
                  comment='備註'),
        
        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, 
                  server_default=sa.text('NOW()'),
                  comment='建立時間 (UTC)'),
        
        # Constraints
        sa.CheckConstraint("device_type IN ('mobile', 'pc')", 
                          name='ck_checkpoints_device_type'),
        sa.CheckConstraint("gps_provider IN ('gps', 'network', 'fused') OR gps_provider IS NULL", 
                          name='ck_checkpoints_gps_provider'),
        
        # Foreign Keys
        sa.ForeignKeyConstraint(['company_id'], ['tenants.id'], 
                               ondelete='CASCADE', 
                               name='fk_checkpoints_company'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], 
                               ondelete='CASCADE', 
                               name='fk_checkpoints_user'),
        sa.ForeignKeyConstraint(['session_id'], ['attendance_sessions.id'], 
                               ondelete='SET NULL', 
                               name='fk_checkpoints_session'),
    )
    
    # Create indexes
    # Tenant isolation (MANDATORY per SA v1.9 section 13)
    op.create_index('idx_checkpoints_company_id', 
                    'attendance_out_checkpoints', 
                    ['company_id'])
    
    # User queries
    op.create_index('idx_checkpoints_user_id', 
                    'attendance_out_checkpoints', 
                    ['user_id'])
    
    # Composite for user history queries (most common query pattern)
    op.create_index('idx_checkpoints_company_user_time', 
                    'attendance_out_checkpoints', 
                    ['company_id', 'user_id', sa.text('punch_time DESC')])
    
    # Session queries
    op.create_index('idx_checkpoints_session_id', 
                    'attendance_out_checkpoints', 
                    ['session_id'],
                    postgresql_where=sa.text('session_id IS NOT NULL'))
    
    # GPS queries (for geofence/location analysis)
    op.create_index('idx_checkpoints_gps', 
                    'attendance_out_checkpoints', 
                    ['gps_lat', 'gps_lng'],
                    postgresql_where=sa.text('gps_lat IS NOT NULL'))


def downgrade():
    """Drop attendance_out_checkpoints table"""
    op.drop_table('attendance_out_checkpoints')
