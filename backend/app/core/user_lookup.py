"""app.core — User display name batch lookup utility

Shared utility for fetching display_name from users table.
Placed in app.core per STOP_GATES GATE-CROSS-MODULE rule:
- Only app.core imports are allowed across module boundaries.

Precedent: app/core/dependencies.py already imports from app.modules.auth.repo
"""
from typing import Dict, List
from uuid import UUID
from sqlalchemy.orm import Session


def get_display_names(db: Session, user_ids: List[UUID]) -> Dict[str, str]:
    """Batch-fetch display_name from users table.

    Args:
        db: SQLAlchemy session
        user_ids: list of user UUIDs to look up

    Returns:
        Dict mapping str(user_id) -> display_name (str)
    """
    if not user_ids:
        return {}
    from app.modules.auth.models import User
    users = db.query(User.id, User.display_name).filter(
        User.id.in_(user_ids)
    ).all()
    return {str(u.id): u.display_name for u in users}
