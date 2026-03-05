"""Expand session status for approval workflow

Revision ID: 006
Revises: wp_11_04a_entitlements
Create Date: 2026-03-05

WP-11-05B: Session Status Expansion

Extends attendance_sessions.status constraint to support approval workflow:
- Existing: 'open', 'closed'
- New: 'pending', 'approved', 'rejected', 'missing_punch_out'

This enables:
- Manager approval queue (pending sessions)
- Approval workflow states (approved/rejected)
- Missing punch-out detection (missing_punch_out)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = 'wp_11_04a_entitlements'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Expand session status constraint to include approval workflow states"""
    
    # Drop old constraint
    op.drop_constraint('ck_sessions_status', 'attendance_sessions', type_='check')
    
    # Create new constraint with expanded status values
    op.create_check_constraint(
        'ck_sessions_status',
        'attendance_sessions',
        "status IN ('open', 'closed', 'pending', 'approved', 'rejected', 'missing_punch_out')"
    )


def downgrade() -> None:
    """Revert to original status constraint (open/closed only)"""
    
    # Drop expanded constraint
    op.drop_constraint('ck_sessions_status', 'attendance_sessions', type_='check')
    
    # Restore original constraint
    op.create_check_constraint(
        'ck_sessions_status',
        'attendance_sessions',
        "status IN ('open', 'closed')"
    )
