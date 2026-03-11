"""WP-11-13: Create allowed_locations table and extend attendance_punches

Revision ID: 008_wp_11_13
Revises: 007_wp_11_10_create_out_checkpoints
Create Date: 2026-03-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '008_wp_11_13'
down_revision = '007_wp_11_10'
branch_labels = None
depends_on = None


def upgrade():
    """Create allowed_locations table and extend attendance_punches"""
    
    # Create allowed_locations table
    op.create_table(
        'allowed_locations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, 
                  server_default=sa.text('gen_random_uuid()'),
                  comment='Location ID (PK)'),
        sa.Column('company_id', sa.String(255), nullable=False, 
                  comment='公司 ID (Tenant Isolation)'),
        sa.Column('name', sa.String(255), nullable=False, 
                  comment='地點名稱，例如：台北101工地'),
        sa.Column('description', sa.Text, nullable=True, 
                  comment='地點描述'),
        sa.Column('location_type', sa.String(50), nullable=False, 
                  server_default='office',
                  comment='地點類型: office, construction_site, customer_site, temporary_site'),
        sa.Column('latitude', sa.Numeric(10, 7), nullable=False, 
                  comment='緯度 (Decimal for precision)'),
        sa.Column('longitude', sa.Numeric(10, 7), nullable=False, 
                  comment='經度 (Decimal for precision)'),
        sa.Column('radius_meters', sa.Integer, nullable=False, 
                  comment='允許半徑（公尺）'),
        sa.Column('is_active', sa.Boolean, nullable=False, 
                  server_default='true',
                  comment='是否啟用'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, 
                  server_default=sa.text('CURRENT_TIMESTAMP'),
                  comment='建立時間'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, 
                  server_default=sa.text('CURRENT_TIMESTAMP'),
                  comment='更新時間'),
        sa.Column('created_by', sa.String(255), nullable=True, 
                  comment='建立者 user_id'),
        sa.Column('updated_by', sa.String(255), nullable=True, 
                  comment='更新者 user_id'),
        
        # Constraints
        sa.CheckConstraint('radius_meters > 0', name='chk_allowed_locations_radius_positive'),
        sa.CheckConstraint('latitude >= -90 AND latitude <= 90', name='chk_allowed_locations_latitude_range'),
        sa.CheckConstraint('longitude >= -180 AND longitude <= 180', name='chk_allowed_locations_longitude_range'),
        sa.ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('idx_allowed_locations_company', 'allowed_locations', ['company_id'])
    op.create_index('idx_allowed_locations_active', 'allowed_locations', ['company_id', 'is_active'])
    
    # Add comment to table
    op.execute("COMMENT ON TABLE allowed_locations IS 'WP-11-13: 允許打卡地點'")
    
    # Extend attendance_punches table
    op.add_column('attendance_punches', 
                  sa.Column('location_id', UUID(as_uuid=True), nullable=True,
                           comment='WP-11-13: 匹配的允許地點 ID'))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_punches_location',
        'attendance_punches', 'allowed_locations',
        ['location_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create index
    op.create_index('idx_punches_location', 'attendance_punches', ['location_id'])


def downgrade():
    """Drop allowed_locations table and remove location_id from attendance_punches"""
    
    # Remove from attendance_punches
    op.drop_index('idx_punches_location', table_name='attendance_punches')
    op.drop_constraint('fk_punches_location', 'attendance_punches', type_='foreignkey')
    op.drop_column('attendance_punches', 'location_id')
    
    # Drop allowed_locations table
    op.drop_index('idx_allowed_locations_active', table_name='allowed_locations')
    op.drop_index('idx_allowed_locations_company', table_name='allowed_locations')
    op.drop_table('allowed_locations')
