"""WP-11-08 Phase 1: Add users.manager_id and create leave tables

Revision ID: 009_wp_11_08
Revises: 008_wp_11_13
Create Date: 2026-03-15

Changes:
1. ALTER TABLE users ADD COLUMN manager_id (self-referencing FK, ON DELETE SET NULL)
2. CREATE TABLE leave_types
3. CREATE TABLE leave_approval_policies
4. CREATE TABLE leave_requests
5. CREATE TABLE leave_approval_logs

Based on: WP-11-08_PHASE1_SCHEMA_DESIGN.md
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '009_wp_11_08'
down_revision = '008_wp_11_13'
branch_labels = None
depends_on = None


def upgrade():
    """Add manager_id to users and create all leave tables."""

    # ------------------------------------------------------------------ #
    # 0. users.manager_id  (prerequisite for Manager Chain)
    # ------------------------------------------------------------------ #
    op.add_column(
        'users',
        sa.Column(
            'manager_id',
            UUID(as_uuid=True),
            nullable=True,
            comment='Direct manager user_id (self-referencing FK, Manager Chain - WP-11-08)'
        )
    )
    op.create_foreign_key(
        'fk_users_manager_id',
        'users', 'users',
        ['manager_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index(
        'idx_users_manager_id',
        'users', ['manager_id'],
        postgresql_where=sa.text('manager_id IS NOT NULL')
    )

    # ------------------------------------------------------------------ #
    # 1. leave_types
    # ------------------------------------------------------------------ #
    op.create_table(
        'leave_types',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()'),
                  comment='Leave Type ID (PK)'),
        sa.Column('company_id', sa.String(255), nullable=False,
                  comment='Company ID (Tenant Isolation)'),
        sa.Column('code', sa.String(50), nullable=False,
                  comment='Internal code - unique per company'),
        sa.Column('name', sa.String(100), nullable=False,
                  comment='Display name'),
        sa.Column('description', sa.Text, nullable=True,
                  comment='Optional description'),
        sa.Column('annual_days', sa.Integer, nullable=True,
                  comment='Annual quota in days (NULL = unlimited)'),
        sa.Column('is_active', sa.Boolean, nullable=False,
                  server_default='true',
                  comment='Active status'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP'),
                  comment='Created timestamp (UTC)'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP'),
                  comment='Updated timestamp (UTC)'),
        sa.UniqueConstraint('company_id', 'code', name='uq_leave_types_company_code'),
        sa.CheckConstraint('annual_days > 0 OR annual_days IS NULL',
                           name='chk_leave_types_annual_days_positive'),
        sa.ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_leave_types_company', 'leave_types', ['company_id'])
    op.create_index('idx_leave_types_company_active', 'leave_types', ['company_id', 'is_active'])
    op.execute("COMMENT ON TABLE leave_types IS 'WP-11-08: Leave type definitions per company'")

    # ------------------------------------------------------------------ #
    # 2. leave_approval_policies
    # ------------------------------------------------------------------ #
    op.create_table(
        'leave_approval_policies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()'),
                  comment='Policy ID (PK)'),
        sa.Column('company_id', sa.String(255), nullable=False,
                  comment='Company ID (Tenant Isolation)'),
        sa.Column('leave_type_id', UUID(as_uuid=True), nullable=True,
                  comment='Leave Type ID (nullable = company-wide default)'),
        sa.Column('min_days', sa.Numeric(4, 1), nullable=False,
                  comment='Lower bound of duration range (inclusive)'),
        sa.Column('max_days', sa.Numeric(4, 1), nullable=True,
                  comment='Upper bound of duration range (NULL = no upper limit)'),
        sa.Column('approval_level', sa.Integer, nullable=False,
                  comment='Required approval level: 1 or 2'),
        sa.Column('is_active', sa.Boolean, nullable=False,
                  server_default='true',
                  comment='Active status'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP'),
                  comment='Created timestamp (UTC)'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP'),
                  comment='Updated timestamp (UTC)'),
        sa.CheckConstraint('min_days > 0',
                           name='chk_leave_policies_min_days_positive'),
        sa.CheckConstraint('max_days IS NULL OR max_days >= min_days',
                           name='chk_leave_policies_max_gte_min'),
        sa.CheckConstraint('approval_level IN (1, 2)',
                           name='chk_leave_policies_approval_level'),
        sa.ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['leave_type_id'], ['leave_types.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_leave_policies_company', 'leave_approval_policies', ['company_id'])
    op.create_index('idx_leave_policies_company_active', 'leave_approval_policies',
                    ['company_id', 'is_active'])
    op.create_index('idx_leave_policies_company_type', 'leave_approval_policies',
                    ['company_id', 'leave_type_id'])
    op.execute("COMMENT ON TABLE leave_approval_policies IS 'WP-11-08: Leave approval policies (Strict Policy Mode)'")

    # ------------------------------------------------------------------ #
    # 3. leave_requests
    # ------------------------------------------------------------------ #
    op.create_table(
        'leave_requests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()'),
                  comment='Leave Request ID (PK)'),
        sa.Column('company_id', sa.String(255), nullable=False,
                  comment='Company ID (Tenant Isolation)'),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False,
                  comment='Requester user ID'),
        sa.Column('leave_type_id', UUID(as_uuid=True), nullable=False,
                  comment='Leave Type ID'),
        sa.Column('start_date', sa.Date, nullable=False,
                  comment='Leave start date (Asia/Taipei local date)'),
        sa.Column('end_date', sa.Date, nullable=False,
                  comment='Leave end date inclusive (Asia/Taipei local date)'),
        sa.Column('total_days', sa.Numeric(4, 1), nullable=False,
                  comment='Calculated duration in days (0.5 for half-day)'),
        sa.Column('is_half_day', sa.Boolean, nullable=False,
                  server_default='false',
                  comment='Half-day flag (reserved, not enforced in Phase 1)'),
        sa.Column('reason', sa.Text, nullable=False,
                  comment='Employee-provided reason (required, NOT NULL)'),
        sa.Column('status', sa.String(20), nullable=False,
                  server_default='pending',
                  comment='Status: pending/approved/rejected/cancelled'),
        sa.Column('required_approval_level', sa.Integer, nullable=False,
                  comment='Approval level (1 or 2), resolved from policy at submission'),
        sa.Column('approver_id', UUID(as_uuid=True), nullable=True,
                  comment='Resolved approver user ID (stored at submission)'),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True,
                  comment='Approved timestamp (UTC)'),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True,
                  comment='Rejected timestamp (UTC)'),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True,
                  comment='Cancelled timestamp (UTC)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP'),
                  comment='Created timestamp (UTC)'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP'),
                  comment='Updated timestamp (UTC)'),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected', 'cancelled')",
                           name='chk_leave_requests_status'),
        sa.CheckConstraint('end_date >= start_date',
                           name='chk_leave_requests_date_range'),
        sa.CheckConstraint('total_days > 0',
                           name='chk_leave_requests_total_days_positive'),
        sa.CheckConstraint('required_approval_level IN (1, 2)',
                           name='chk_leave_requests_approval_level'),
        sa.ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['leave_type_id'], ['leave_types.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['approver_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_leave_requests_company', 'leave_requests', ['company_id'])
    op.create_index('idx_leave_requests_company_user', 'leave_requests', ['company_id', 'user_id'])
    op.create_index('idx_leave_requests_company_status', 'leave_requests', ['company_id', 'status'])
    op.create_index('idx_leave_requests_approver', 'leave_requests', ['approver_id'])
    op.create_index('idx_leave_requests_user_dates', 'leave_requests',
                    ['user_id', 'start_date', 'end_date'])
    op.create_index('idx_leave_requests_leave_type', 'leave_requests', ['leave_type_id'])
    op.execute("COMMENT ON TABLE leave_requests IS 'WP-11-08: Leave request submissions'")

    # ------------------------------------------------------------------ #
    # 4. leave_approval_logs
    # ------------------------------------------------------------------ #
    op.create_table(
        'leave_approval_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()'),
                  comment='Log entry ID (PK)'),
        sa.Column('company_id', sa.String(255), nullable=False,
                  comment='Company ID (Tenant Isolation, denormalized)'),
        sa.Column('leave_request_id', UUID(as_uuid=True), nullable=False,
                  comment='Leave Request ID'),
        sa.Column('actor_user_id', UUID(as_uuid=True), nullable=False,
                  comment='User who performed the action'),
        sa.Column('action', sa.String(20), nullable=False,
                  comment='Action: approved/rejected/cancelled'),
        sa.Column('approval_level', sa.Integer, nullable=False,
                  comment='Level at which action was taken (1 or 2)'),
        sa.Column('comment', sa.Text, nullable=True,
                  comment='Optional message from approver or requester'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP'),
                  comment='Action timestamp (UTC, immutable, no updated_at)'),
        sa.CheckConstraint("action IN ('approved', 'rejected', 'cancelled')",
                           name='chk_leave_logs_action'),
        sa.CheckConstraint('approval_level IN (1, 2)',
                           name='chk_leave_logs_approval_level'),
        sa.ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['leave_request_id'], ['leave_requests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_leave_logs_request', 'leave_approval_logs', ['leave_request_id'])
    op.create_index('idx_leave_logs_company', 'leave_approval_logs', ['company_id'])
    op.create_index('idx_leave_logs_actor', 'leave_approval_logs', ['actor_user_id'])
    op.execute("COMMENT ON TABLE leave_approval_logs IS 'WP-11-08: Immutable leave approval audit log'")


def downgrade():
    """Drop all leave tables and remove users.manager_id."""

    # Drop in reverse FK dependency order
    op.drop_index('idx_leave_logs_actor', table_name='leave_approval_logs')
    op.drop_index('idx_leave_logs_company', table_name='leave_approval_logs')
    op.drop_index('idx_leave_logs_request', table_name='leave_approval_logs')
    op.drop_table('leave_approval_logs')

    op.drop_index('idx_leave_requests_leave_type', table_name='leave_requests')
    op.drop_index('idx_leave_requests_user_dates', table_name='leave_requests')
    op.drop_index('idx_leave_requests_approver', table_name='leave_requests')
    op.drop_index('idx_leave_requests_company_status', table_name='leave_requests')
    op.drop_index('idx_leave_requests_company_user', table_name='leave_requests')
    op.drop_index('idx_leave_requests_company', table_name='leave_requests')
    op.drop_table('leave_requests')

    op.drop_index('idx_leave_policies_company_type', table_name='leave_approval_policies')
    op.drop_index('idx_leave_policies_company_active', table_name='leave_approval_policies')
    op.drop_index('idx_leave_policies_company', table_name='leave_approval_policies')
    op.drop_table('leave_approval_policies')

    op.drop_index('idx_leave_types_company_active', table_name='leave_types')
    op.drop_index('idx_leave_types_company', table_name='leave_types')
    op.drop_table('leave_types')

    op.drop_index('idx_users_manager_id', table_name='users')
    op.drop_constraint('fk_users_manager_id', 'users', type_='foreignkey')
    op.drop_column('users', 'manager_id')
