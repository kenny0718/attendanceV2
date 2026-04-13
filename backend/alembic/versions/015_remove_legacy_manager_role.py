"""remove legacy manager role seed

Revision ID: 015_remove_legacy_manager_role
Revises: 014_add_tax_id_to_tenants
Create Date: 2026-04-13 10:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '015_remove_legacy_manager_role'
down_revision: Union[str, None] = '014_add_tax_id_to_tenants'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM role_permissions WHERE role_id = 'manager'"))
    conn.execute(sa.text("DELETE FROM roles WHERE id = 'manager'"))


def downgrade() -> None:
    conn = op.get_bind()

    result = conn.execute(sa.text("SELECT COUNT(*) FROM roles WHERE id = 'manager'"))
    if result.scalar() == 0:
        conn.execute(
            sa.text("INSERT INTO roles (id, name, description) VALUES (:id, :name, :description)"),
            {
                "id": "manager",
                "name": "Manager",
                "description": "Can approve attendance for team members",
            },
        )

    role_permissions_data = [
        ('manager', 'attendance:create:self'),
        ('manager', 'attendance:approve'),
        ('manager', 'notifications:read:self'),
        ('manager', 'audit:read'),
    ]
    for role_id, permission_id in role_permissions_data:
        result = conn.execute(
            sa.text(
                "SELECT COUNT(*) FROM role_permissions WHERE role_id = :role_id AND permission_id = :permission_id"
            ),
            {"role_id": role_id, "permission_id": permission_id},
        )
        if result.scalar() == 0:
            import uuid

            conn.execute(
                sa.text(
                    "INSERT INTO role_permissions (id, role_id, permission_id) VALUES (:id, :role_id, :permission_id)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "role_id": role_id,
                    "permission_id": permission_id,
                },
            )
