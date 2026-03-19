"""WP-S1-02: Create schedule tables (shift_templates, shift_assignments)

Revision ID: 010_wp_s1_02
Revises: 009_wp_11_08
Create Date: 2026-03-18

Changes:
1. CREATE TABLE shift_templates
2. CREATE TABLE shift_assignments

Based on: WP-S1-02 Schedule Module Migration
Pre-audit: docs/WP-S1-02_PRE_MIGRATION_AUDIT.md
Model alignment: docs/WP-S1-01A_MODELS_ALIGNMENT_FIX_REPORT.md

Design notes:
- company_id: String(255), FK to tenants.id CASCADE (tenant isolation)
- user_id: UUID, FK to users.id CASCADE
- PK: UUID + gen_random_uuid()
- status: String(20) + CheckConstraint (no PostgreSQL CREATE TYPE)
- shift_templates.code: UniqueConstraint per company
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '010_wp_s1_02'
down_revision = '009_wp_11_08'
branch_labels = None
depends_on = None


def upgrade():
    """Create shift_templates and shift_assignments tables."""

    # ------------------------------------------------------------------ #
    # 1. shift_templates
    # ------------------------------------------------------------------ #
    op.create_table(
        'shift_templates',
        sa.Column(
            'id',
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            comment='ShiftTemplate ID (PK)',
        ),
        sa.Column(
            'company_id',
            sa.String(255),
            nullable=False,
            comment='Company ID (Tenant Isolation, FK to tenants.id)',
        ),
        sa.Column(
            'code',
            sa.String(32),
            nullable=False,
            comment='Shift code, unique per company (e.g. DAY, NIGHT)',
        ),
        sa.Column(
            'name',
            sa.String(64),
            nullable=False,
            comment='Shift display name (e.g. \u65e5\u73ed)',
        ),
        sa.Column(
            'start_time',
            sa.Time(),
            nullable=False,
            comment='Shift start time',
        ),
        sa.Column(
            'end_time',
            sa.Time(),
            nullable=False,
            comment='Shift end time',
        ),
        sa.Column(
            'break_minutes',
            sa.SmallInteger(),
            nullable=False,
            server_default='0',
            comment='Break duration in minutes (informational)',
        ),
        sa.Column(
            'is_overnight',
            sa.Boolean(),
            nullable=False,
            server_default='false',
            comment='True if shift crosses midnight (informational)',
        ),
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            server_default='true',
            comment='Soft-delete flag',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('NOW()'),
            comment='Created timestamp (UTC)',
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('NOW()'),
            comment='Updated timestamp (UTC)',
        ),
        # Constraints
        sa.UniqueConstraint(
            'company_id', 'code',
            name='uq_shift_templates_company_code',
        ),
        sa.ForeignKeyConstraint(
            ['company_id'], ['tenants.id'],
            ondelete='CASCADE',
            name='fk_shift_templates_company_id',
        ),
    )

    # Indexes for shift_templates
    op.create_index(
        'idx_shift_templates_company',
        'shift_templates', ['company_id'],
    )
    op.create_index(
        'idx_shift_templates_company_active',
        'shift_templates', ['company_id', 'is_active'],
    )

    # ------------------------------------------------------------------ #
    # 2. shift_assignments
    # ------------------------------------------------------------------ #
    op.create_table(
        'shift_assignments',
        sa.Column(
            'id',
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            comment='ShiftAssignment ID (PK)',
        ),
        sa.Column(
            'company_id',
            sa.String(255),
            nullable=False,
            comment='Company ID (Tenant Isolation, FK to tenants.id)',
        ),
        sa.Column(
            'user_id',
            UUID(as_uuid=True),
            nullable=False,
            comment='User ID (FK to users.id)',
        ),
        sa.Column(
            'shift_template_id',
            UUID(as_uuid=True),
            nullable=False,
            comment='ShiftTemplate ID (FK to shift_templates.id)',
        ),
        sa.Column(
            'work_date',
            sa.Date(),
            nullable=False,
            comment='Assigned work date (local date)',
        ),
        sa.Column(
            'status',
            sa.String(20),
            nullable=False,
            server_default='scheduled',
            comment='Assignment status: scheduled / confirmed / cancelled',
        ),
        sa.Column(
            'notes',
            sa.Text(),
            nullable=True,
            comment='Optional notes',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('NOW()'),
            comment='Created timestamp (UTC)',
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('NOW()'),
            comment='Updated timestamp (UTC)',
        ),
        # Constraints
        sa.CheckConstraint(
            "status IN ('scheduled', 'confirmed', 'cancelled')",
            name='ck_shift_assignments_status',
        ),
        sa.ForeignKeyConstraint(
            ['company_id'], ['tenants.id'],
            ondelete='CASCADE',
            name='fk_shift_assignments_company_id',
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            ondelete='CASCADE',
            name='fk_shift_assignments_user_id',
        ),
        sa.ForeignKeyConstraint(
            ['shift_template_id'], ['shift_templates.id'],
            ondelete='RESTRICT',
            name='fk_shift_assignments_template_id',
        ),
    )

    # Indexes for shift_assignments
    op.create_index(
        'idx_shift_assignments_company',
        'shift_assignments', ['company_id'],
    )
    op.create_index(
        'idx_shift_assignments_user',
        'shift_assignments', ['user_id'],
    )
    op.create_index(
        'idx_shift_assignments_company_user',
        'shift_assignments', ['company_id', 'user_id'],
    )
    op.create_index(
        'idx_shift_assignments_company_date',
        'shift_assignments', ['company_id', 'work_date'],
    )
    op.create_index(
        'idx_shift_assignments_template',
        'shift_assignments', ['shift_template_id'],
    )


def downgrade():
    """Drop shift_assignments then shift_templates (safe order: FK dependency)."""

    # Drop indexes for shift_assignments
    op.drop_index('idx_shift_assignments_template', table_name='shift_assignments')
    op.drop_index('idx_shift_assignments_company_date', table_name='shift_assignments')
    op.drop_index('idx_shift_assignments_company_user', table_name='shift_assignments')
    op.drop_index('idx_shift_assignments_user', table_name='shift_assignments')
    op.drop_index('idx_shift_assignments_company', table_name='shift_assignments')

    # Drop shift_assignments first (has FK to shift_templates)
    op.drop_table('shift_assignments')

    # Drop indexes for shift_templates
    op.drop_index('idx_shift_templates_company_active', table_name='shift_templates')
    op.drop_index('idx_shift_templates_company', table_name='shift_templates')

    # Drop shift_templates
    op.drop_table('shift_templates')
