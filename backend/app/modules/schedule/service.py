"""
Schedule Module — Service Layer
=================================
WP-S1-03 CRUD Core: Full implementation replacing WP-S1-01 stubs.

Responsibilities:
  - Business rules for ShiftTemplate management.
  - Business rules for ShiftAssignment CRUD.
  - Tenant isolation enforcement (all ops scoped to company_id).

Tenant Isolation (P0):
  - Every public method receives company_id.
  - Methods do not cross company boundaries.
  - company_id is always passed down to repo layer.

Out of scope (future tickets):
  - Conflict detection / scheduling engine
  - Roster generation / recurring rules
  - Leave overlay / attendance integration
  - Role permission integration
"""

import logging
from datetime import date, datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .models import (
    ASSIGNMENT_STATUS_CANCELLED,
    ASSIGNMENT_STATUS_CONFIRMED,
    ASSIGNMENT_STATUS_SCHEDULED,
    ASSIGNMENT_STATUS_VALUES,
    ShiftAssignment,
    ShiftTemplate,
)
from .repo import ShiftAssignmentRepo, ShiftTemplateRepo
from .schemas import (
    AssignmentStatusSchema,
    ShiftAssignmentCreate,
    ShiftAssignmentRead,
    ShiftAssignmentUpdate,
    ShiftTemplateCreate,
    ShiftTemplateRead,
    ShiftTemplateUpdate,
)

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# ScheduleService
# ---------------------------------------------------------------------------

class ScheduleService:
    """
    Business-logic layer for the schedule module.

    Tenant Isolation contract:
      - Every public method MUST receive company_id.
      - Methods must not cross company boundaries.
      - company_id is always passed down to repo layer.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.template_repo = ShiftTemplateRepo(db)
        self.assignment_repo = ShiftAssignmentRepo(db)

    # ------------------------------------------------------------------
    # ShiftTemplate operations
    # ------------------------------------------------------------------

    def create_shift_template(
        self, company_id: str, payload: ShiftTemplateCreate
    ) -> ShiftTemplateRead:
        """Validate and persist a new ShiftTemplate.

        Business rules:
          - company_id in payload must match the caller's company_id.
          - code must be unique within the company.

        Tenant Isolation: company_id enforced.
        """
        # Ensure payload company_id matches caller's scope
        if payload.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="company_id mismatch: cannot create template for another company.",
            )

        # Uniqueness check: code per company
        existing = self.template_repo.get_by_code(
            code=payload.code, company_id=company_id
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"ShiftTemplate code '{payload.code}' already exists in this company.",
            )

        obj = ShiftTemplate(
            company_id=company_id,
            code=payload.code,
            name=payload.name,
            start_time=payload.start_time,
            end_time=payload.end_time,
            break_minutes=payload.break_minutes,
            is_overnight=payload.is_overnight,
            is_active=payload.is_active,
        )
        saved = self.template_repo.create(obj)
        return ShiftTemplateRead.model_validate(saved)

    def get_shift_template(
        self, company_id: str, template_id: UUID
    ) -> ShiftTemplateRead:
        """Get a single ShiftTemplate by id within a company.

        Raises 404 if not found or belongs to another company.
        Tenant Isolation: repo enforces company_id.
        """
        obj = self.template_repo.get_by_id(template_id, company_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ShiftTemplate {template_id} not found.",
            )
        return ShiftTemplateRead.model_validate(obj)

    def list_shift_templates(
        self, company_id: str, active_only: bool = True
    ) -> List[ShiftTemplateRead]:
        """List ShiftTemplates for a company.

        Tenant Isolation: repo enforces company_id.
        """
        objs = self.template_repo.list_by_company(
            company_id=company_id, active_only=active_only
        )
        return [ShiftTemplateRead.model_validate(o) for o in objs]

    def update_shift_template(
        self,
        company_id: str,
        template_id: UUID,
        payload: ShiftTemplateUpdate,
    ) -> ShiftTemplateRead:
        """Partially update an existing ShiftTemplate.

        Raises 404 if not found.
        Tenant Isolation: repo enforces company_id.
        """
        obj = self.template_repo.get_by_id(template_id, company_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ShiftTemplate {template_id} not found.",
            )

        # Apply partial updates
        if payload.name is not None:
            obj.name = payload.name
        if payload.start_time is not None:
            obj.start_time = payload.start_time
        if payload.end_time is not None:
            obj.end_time = payload.end_time
        if payload.break_minutes is not None:
            obj.break_minutes = payload.break_minutes
        if payload.is_overnight is not None:
            obj.is_overnight = payload.is_overnight
        if payload.is_active is not None:
            obj.is_active = payload.is_active

        saved = self.template_repo.update(obj)
        return ShiftTemplateRead.model_validate(saved)

    def deactivate_shift_template(
        self, company_id: str, template_id: UUID
    ) -> ShiftTemplateRead:
        """Soft-deactivate a ShiftTemplate (set is_active=False).

        Raises 404 if not found.
        Tenant Isolation: repo enforces company_id.
        """
        obj = self.template_repo.set_active(template_id, company_id, is_active=False)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ShiftTemplate {template_id} not found.",
            )
        return ShiftTemplateRead.model_validate(obj)

    def activate_shift_template(
        self, company_id: str, template_id: UUID
    ) -> ShiftTemplateRead:
        """Re-activate a ShiftTemplate (set is_active=True).

        Raises 404 if not found.
        Tenant Isolation: repo enforces company_id.
        """
        obj = self.template_repo.set_active(template_id, company_id, is_active=True)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ShiftTemplate {template_id} not found.",
            )
        return ShiftTemplateRead.model_validate(obj)

    # ------------------------------------------------------------------
    # ShiftAssignment operations
    # ------------------------------------------------------------------

    def create_shift_assignment(
        self, company_id: str, payload: ShiftAssignmentCreate
    ) -> ShiftAssignmentRead:
        """Validate and persist a new ShiftAssignment.

        Business rules:
          - company_id in payload must match caller's company_id.
          - shift_template_id must belong to the same company and be active.
          - user_id must not be empty (enforced by UUID type).
          - Initial status defaults to 'scheduled'.

        Tenant Isolation: company_id enforced throughout.
        """
        # Ensure payload company_id matches caller's scope
        if payload.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="company_id mismatch: cannot create assignment for another company.",
            )

        # Validate shift_template belongs to same company
        template = self.template_repo.get_by_id(
            payload.shift_template_id, company_id
        )
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"ShiftTemplate {payload.shift_template_id} not found "
                    "in this company."
                ),
            )
        if not template.is_active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"ShiftTemplate {payload.shift_template_id} is not active.",
            )

        obj = ShiftAssignment(
            company_id=company_id,
            user_id=payload.user_id,
            shift_template_id=payload.shift_template_id,
            work_date=payload.work_date,
            status=payload.status.value if payload.status else ASSIGNMENT_STATUS_SCHEDULED,
            notes=payload.notes,
        )
        saved = self.assignment_repo.create(obj)
        return ShiftAssignmentRead.model_validate(saved)

    def get_shift_assignment(
        self, company_id: str, assignment_id: UUID
    ) -> ShiftAssignmentRead:
        """Get a single ShiftAssignment by id within a company.

        Raises 404 if not found or belongs to another company.
        Tenant Isolation: repo enforces company_id.
        """
        obj = self.assignment_repo.get_by_id(assignment_id, company_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ShiftAssignment {assignment_id} not found.",
            )
        return ShiftAssignmentRead.model_validate(obj)

    def list_assignments_for_user(
        self,
        company_id: str,
        user_id: UUID,
        start_date: date,
        end_date: date,
        template_id=None,
        status: str = None,
    ) -> List[ShiftAssignmentRead]:
        """List ShiftAssignments for a specific user over a date range.

        Tenant Isolation: repo enforces company_id.
        Optional filters: template_id, status (S1-09B).
        """
        objs = self.assignment_repo.list_by_user_date_range(
            company_id=company_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            template_id=template_id,
            status=status,
        )
        return [ShiftAssignmentRead.model_validate(o) for o in objs]

    def list_assignments_for_date(
        self,
        company_id: str,
        work_date: date,
        template_id=None,
        status: str = None,
    ) -> List[ShiftAssignmentRead]:
        """List all ShiftAssignments for a company on a given date.

        Tenant Isolation: repo enforces company_id.
        Optional filters: template_id, status (S1-09B).
        """
        objs = self.assignment_repo.list_by_company_date(
            company_id=company_id,
            work_date=work_date,
            template_id=template_id,
            status=status,
        )
        return [ShiftAssignmentRead.model_validate(o) for o in objs]

    def list_assignments(
        self,
        company_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        template_id=None,
        status: str = None,
    ) -> List[ShiftAssignmentRead]:
        """List all ShiftAssignments for a company, optionally filtered by date range.

        Tenant Isolation: repo enforces company_id.
        Optional filters: template_id, status (S1-09B).
        """
        objs = self.assignment_repo.list_by_company(
            company_id=company_id,
            start_date=start_date,
            end_date=end_date,
            template_id=template_id,
            status=status,
        )
        return [ShiftAssignmentRead.model_validate(o) for o in objs]

    def update_shift_assignment(
        self,
        company_id: str,
        assignment_id: UUID,
        payload: ShiftAssignmentUpdate,
    ) -> ShiftAssignmentRead:
        """Partially update status, notes, or shift_template on a ShiftAssignment.

        Business rules:
          - Cannot update a cancelled assignment.
          - If updating shift_template_id, new template must belong to same company
            and be active.

        Raises 404 if not found.
        Tenant Isolation: repo enforces company_id.
        """
        obj = self.assignment_repo.get_by_id(assignment_id, company_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ShiftAssignment {assignment_id} not found.",
            )

        if obj.status == ASSIGNMENT_STATUS_CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot update a cancelled assignment.",
            )

        # If updating shift_template, validate it belongs to same company
        if payload.shift_template_id is not None:
            template = self.template_repo.get_by_id(
                payload.shift_template_id, company_id
            )
            if template is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"ShiftTemplate {payload.shift_template_id} not found "
                        "in this company."
                    ),
                )
            if not template.is_active:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"ShiftTemplate {payload.shift_template_id} is not active.",
                )
            obj.shift_template_id = payload.shift_template_id

        if payload.status is not None:
            obj.status = payload.status.value

        if payload.notes is not None:
            obj.notes = payload.notes

        saved = self.assignment_repo.update(obj)
        return ShiftAssignmentRead.model_validate(saved)

    def cancel_shift_assignment(
        self, company_id: str, assignment_id: UUID
    ) -> ShiftAssignmentRead:
        """Set assignment status to 'cancelled'.

        Business rules:
          - Already-cancelled assignment: raises 409 (idempotency guard).

        Raises 404 if not found.
        Tenant Isolation: repo enforces company_id.
        """
        obj = self.assignment_repo.get_by_id(assignment_id, company_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ShiftAssignment {assignment_id} not found.",
            )
        if obj.status == ASSIGNMENT_STATUS_CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Assignment is already cancelled.",
            )

        cancelled = self.assignment_repo.cancel(assignment_id, company_id)
        return ShiftAssignmentRead.model_validate(cancelled)


def get_schedule_service(db: Session) -> ScheduleService:
    """Factory function for ScheduleService (dependency injection)."""
    return ScheduleService(db)
