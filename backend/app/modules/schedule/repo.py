"""
Schedule Module — Repository Layer
====================================
WP-S1-03 CRUD Core: Full implementation replacing WP-S1-01 stubs.

Responsibilities:
  - All direct ORM / DB interactions for ShiftTemplate and ShiftAssignment.
  - CRUD operations scoped by company_id (Tenant Isolation P0).
  - Date-range queries for assignment retrieval.
  - No business logic; only data access.

Tenant Isolation:
  - ALL queries enforce WHERE company_id = ?
  - Never fetch by id alone (always id + company_id).

Out of scope:
  - Bulk upsert
  - Conflict detection queries
  - Pagination (future ticket)
"""

import logging
from datetime import date, datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from .models import ASSIGNMENT_STATUS_CANCELLED, ShiftAssignment, ShiftTemplate

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# ShiftTemplateRepo
# ---------------------------------------------------------------------------

class ShiftTemplateRepo:
    """
    Data-access layer for ShiftTemplate.
    All methods are company-scoped (Tenant Isolation P0).
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Read ---

    def get_by_id(
        self, template_id: UUID, company_id: str
    ) -> Optional[ShiftTemplate]:
        """Fetch a single ShiftTemplate by PK within a company.

        Tenant Isolation: enforces company_id in WHERE clause.
        """
        return (
            self.db.query(ShiftTemplate)
            .filter(
                and_(
                    ShiftTemplate.id == template_id,
                    ShiftTemplate.company_id == company_id,
                )
            )
            .first()
        )

    def get_by_code(
        self, code: str, company_id: str
    ) -> Optional[ShiftTemplate]:
        """Fetch a ShiftTemplate by (company_id, code) — used for uniqueness check.

        Tenant Isolation: enforces company_id in WHERE clause.
        """
        return (
            self.db.query(ShiftTemplate)
            .filter(
                and_(
                    ShiftTemplate.company_id == company_id,
                    ShiftTemplate.code == code,
                )
            )
            .first()
        )

    def list_by_company(
        self, company_id: str, active_only: bool = True
    ) -> List[ShiftTemplate]:
        """List ShiftTemplates for a company.

        Tenant Isolation: enforces company_id in WHERE clause.
        """
        q = self.db.query(ShiftTemplate).filter(
            ShiftTemplate.company_id == company_id
        )
        if active_only:
            q = q.filter(ShiftTemplate.is_active == True)  # noqa: E712
        return q.order_by(ShiftTemplate.code.asc()).all()

    # --- Write ---

    def create(self, obj: ShiftTemplate) -> ShiftTemplate:
        """Persist a new ShiftTemplate and return the saved instance."""
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        logger.info(
            "ShiftTemplate created: id=%s code=%s company=%s",
            obj.id, obj.code, obj.company_id,
        )
        return obj

    def update(self, obj: ShiftTemplate) -> ShiftTemplate:
        """Flush changes on an already-attached ShiftTemplate instance."""
        obj.updated_at = _utcnow()
        self.db.commit()
        self.db.refresh(obj)
        logger.info(
            "ShiftTemplate updated: id=%s company=%s",
            obj.id, obj.company_id,
        )
        return obj

    def set_active(
        self, template_id: UUID, company_id: str, is_active: bool
    ) -> Optional[ShiftTemplate]:
        """Set is_active flag on a ShiftTemplate within a company.

        Returns the updated instance, or None if not found.
        Tenant Isolation: enforces company_id in WHERE clause.
        """
        obj = self.get_by_id(template_id, company_id)
        if obj is None:
            return None
        obj.is_active = is_active
        obj.updated_at = _utcnow()
        self.db.commit()
        self.db.refresh(obj)
        logger.info(
            "ShiftTemplate is_active=%s: id=%s company=%s",
            is_active, obj.id, obj.company_id,
        )
        return obj


def get_shift_template_repo(db: Session) -> ShiftTemplateRepo:
    """Factory function for ShiftTemplateRepo (dependency injection)."""
    return ShiftTemplateRepo(db)


# ---------------------------------------------------------------------------
# ShiftAssignmentRepo
# ---------------------------------------------------------------------------

class ShiftAssignmentRepo:
    """
    Data-access layer for ShiftAssignment.
    All methods are company-scoped (Tenant Isolation P0).
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Read ---

    def get_by_id(
        self, assignment_id: UUID, company_id: str
    ) -> Optional[ShiftAssignment]:
        """Fetch a single ShiftAssignment by PK within a company.

        Tenant Isolation: enforces company_id in WHERE clause.
        """
        return (
            self.db.query(ShiftAssignment)
            .filter(
                and_(
                    ShiftAssignment.id == assignment_id,
                    ShiftAssignment.company_id == company_id,
                )
            )
            .first()
        )

    def list_by_user_date_range(
        self,
        company_id: str,
        user_id: UUID,
        start_date: date,
        end_date: date,
        template_id: Optional[UUID] = None,
        status: Optional[str] = None,
    ) -> List[ShiftAssignment]:
        """List all ShiftAssignments for a user within a date range.

        Tenant Isolation: enforces company_id in WHERE clause.
        Optional filters: template_id, status (S1-09B).
        """
        q = (
            self.db.query(ShiftAssignment)
            .filter(
                and_(
                    ShiftAssignment.company_id == company_id,
                    ShiftAssignment.user_id == user_id,
                    ShiftAssignment.work_date >= start_date,
                    ShiftAssignment.work_date <= end_date,
                )
            )
        )
        if template_id is not None:
            q = q.filter(ShiftAssignment.shift_template_id == template_id)
        if status is not None:
            q = q.filter(ShiftAssignment.status == status)
        return q.order_by(ShiftAssignment.work_date.asc()).all()

    def list_by_company_date(
        self,
        company_id: str,
        work_date: date,
        template_id: Optional[UUID] = None,
        status: Optional[str] = None,
    ) -> List[ShiftAssignment]:
        """List all ShiftAssignments for a company on a specific date.

        Tenant Isolation: enforces company_id in WHERE clause.
        Optional filters: template_id, status (S1-09B).
        """
        q = (
            self.db.query(ShiftAssignment)
            .filter(
                and_(
                    ShiftAssignment.company_id == company_id,
                    ShiftAssignment.work_date == work_date,
                )
            )
        )
        if template_id is not None:
            q = q.filter(ShiftAssignment.shift_template_id == template_id)
        if status is not None:
            q = q.filter(ShiftAssignment.status == status)
        return q.order_by(ShiftAssignment.user_id.asc()).all()

    def list_by_company(
        self,
        company_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        template_id: Optional[UUID] = None,
        status: Optional[str] = None,
    ) -> List[ShiftAssignment]:
        """List all ShiftAssignments for a company, optionally filtered by date range.

        Tenant Isolation: enforces company_id in WHERE clause.
        Optional filters: template_id, status (S1-09B).
        """
        q = self.db.query(ShiftAssignment).filter(
            ShiftAssignment.company_id == company_id
        )
        if start_date is not None:
            q = q.filter(ShiftAssignment.work_date >= start_date)
        if end_date is not None:
            q = q.filter(ShiftAssignment.work_date <= end_date)
        if template_id is not None:
            q = q.filter(ShiftAssignment.shift_template_id == template_id)
        if status is not None:
            q = q.filter(ShiftAssignment.status == status)
        return q.order_by(
            ShiftAssignment.work_date.asc(),
            ShiftAssignment.user_id.asc(),
        ).all()

    # --- Write ---

    def create(self, obj: ShiftAssignment) -> ShiftAssignment:
        """Persist a new ShiftAssignment and return the saved instance."""
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        logger.info(
            "ShiftAssignment created: id=%s user=%s date=%s company=%s",
            obj.id, obj.user_id, obj.work_date, obj.company_id,
        )
        return obj

    def update(self, obj: ShiftAssignment) -> ShiftAssignment:
        """Flush changes on an already-attached ShiftAssignment instance."""
        obj.updated_at = _utcnow()
        self.db.commit()
        self.db.refresh(obj)
        logger.info(
            "ShiftAssignment updated: id=%s status=%s company=%s",
            obj.id, obj.status, obj.company_id,
        )
        return obj

    def cancel(
        self, assignment_id: UUID, company_id: str
    ) -> Optional[ShiftAssignment]:
        """Set assignment status to 'cancelled' within a company.

        Returns the updated instance, or None if not found.
        Tenant Isolation: enforces company_id in WHERE clause.
        """
        obj = self.get_by_id(assignment_id, company_id)
        if obj is None:
            return None
        obj.status = ASSIGNMENT_STATUS_CANCELLED
        obj.updated_at = _utcnow()
        self.db.commit()
        self.db.refresh(obj)
        logger.info(
            "ShiftAssignment cancelled: id=%s company=%s",
            obj.id, obj.company_id,
        )
        return obj


def get_shift_assignment_repo(db: Session) -> ShiftAssignmentRepo:
    """Factory function for ShiftAssignmentRepo (dependency injection)."""
    return ShiftAssignmentRepo(db)
