"""S1-11D: Add hr_manager role to roles seed

Revision ID: 011_s1_11d
Revises: 010_wp_s1_02_create_schedule_tables
Create Date: 2026-03-22

Adds hr_manager as a company-level admin access role alongside company_admin.
This role grants access to admin company/member APIs but not platform-level actions.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '011_s1_11d'
down_revision = '010_wp_s1_02'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Add hr_manager role if not exists
    result = conn.execute(sa.text("SELECT COUNT(*) FROM roles WHERE id = 'hr_manager'"))
    if result.scalar() == 0:
        conn.execute(
            sa.text("INSERT INTO roles (id, name, description) VALUES (:id, :name, :description)"),
            {"id": "hr_manager", "name": "HR Manager", "description": "HR admin access: can manage company members and view company info"}
        )

    # Seed hr_manager permissions (same as company_admin minus audit/backup)
    hr_perms = [
        ('hr_manager', 'attendance:create:self'),
        ('hr_manager', 'notifications:read:self'),
        ('hr_manager', 'tenants:read'),
        ('hr_manager', 'tenants:manage'),
    ]
    for role_id, perm_id in hr_perms:
        result = conn.execute(
            sa.text("SELECT COUNT(*) FROM role_permissions WHERE role_id = :r AND permission_id = :p"),
            {"r": role_id, "p": perm_id}
        )
        if result.scalar() == 0:
            import uuid
            conn.execute(
                sa.text("INSERT INTO role_permissions (id, role_id, permission_id) VALUES (:id, :role_id, :permission_id)"),
                {"id": str(uuid.uuid4()), "role_id": role_id, "permission_id": perm_id}
            )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM role_permissions WHERE role_id = 'hr_manager'"))
    conn.execute(sa.text("DELETE FROM roles WHERE id = 'hr_manager'"))
