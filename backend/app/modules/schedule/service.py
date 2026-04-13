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
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
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
    ShiftSegmentCreate,
    ShiftTemplateCreate,
    ShiftTemplateRead,
    ShiftTemplateUpdate,
)

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def _segment_window(seg: ShiftSegmentCreate) -> tuple[int, int]:
    start_minutes = seg.day_offset_start * 1440 + seg.start_time.hour * 60 + seg.start_time.minute
    end_minutes = seg.day_offset_end * 1440 + seg.end_time.hour * 60 + seg.end_time.minute
    if end_minutes <= start_minutes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Shift segment end must be after start.",
        )
    return start_minutes, end_minutes


def _normalize_segments(segments: Optional[List[ShiftSegmentCreate]]) -> Optional[List[dict]]:
    if segments is None:
        return None

    normalized: List[dict] = []
    seen_indexes = set()
    windows: List[tuple[int, int, int]] = []

    for seg in sorted(segments, key=lambda s: s.segment_index):
        if seg.segment_index in seen_indexes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Duplicate shift segment index.",
            )
        seen_indexes.add(seg.segment_index)

        start_minutes, end_minutes = _segment_window(seg)
        for existing_start, existing_end, existing_index in windows:
            if start_minutes < existing_end and end_minutes > existing_start:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=(
                        f"Shift segments overlap: segment {seg.segment_index} overlaps "
                        f"with segment {existing_index}."
                    ),
                )
        windows.append((start_minutes, end_minutes, seg.segment_index))
        normalized.append(
            {
                "segment_index": seg.segment_index,
                "start_time": seg.start_time,
                "end_time": seg.end_time,
                "day_offset_start": seg.day_offset_start,
                "day_offset_end": seg.day_offset_end,
                "is_active": seg.is_active,
            }
        )

    return normalized


@dataclass(frozen=True)
class ScheduleBaselineSegment:
    segment_index: int
    start_time: time
    end_time: time
    day_offset_start: int
    day_offset_end: int


@dataclass(frozen=True)
class ScheduleBaseline:
    segments: List[ScheduleBaselineSegment]
    normalized_windows: List[tuple[datetime, datetime]]
    metadata: dict[str, object]


class ScheduleBaselineResolver:
    """Resolve schedule baseline from assignment/template with normalized windows."""

    DEFAULT_START = time(9, 0)
    DEFAULT_END = time(18, 0)

    def __init__(self, db: Session) -> None:
        self.db = db
        self.template_repo = ShiftTemplateRepo(db)
        self.assignment_repo = ShiftAssignmentRepo(db)

    def _normalize_windows(
        self,
        work_date: date,
        segments: List[ScheduleBaselineSegment],
    ) -> List[tuple[datetime, datetime]]:
        windows: List[tuple[datetime, datetime]] = []
        for seg in sorted(segments, key=lambda x: x.segment_index):
            start_dt = datetime.combine(
                work_date + timedelta(days=seg.day_offset_start),
                seg.start_time,
            )
            end_dt = datetime.combine(
                work_date + timedelta(days=seg.day_offset_end),
                seg.end_time,
            )
            windows.append((start_dt, end_dt))
        return windows

    def _fallback_from_template(self, template: ShiftTemplate) -> List[ScheduleBaselineSegment]:
        day_offset_end = 1 if bool(template.is_overnight) else 0
        return [
            ScheduleBaselineSegment(
                segment_index=1,
                start_time=template.start_time,
                end_time=template.end_time,
                day_offset_start=0,
                day_offset_end=day_offset_end,
            )
        ]

    def _default_segments(self) -> List[ScheduleBaselineSegment]:
        return [
            ScheduleBaselineSegment(
                segment_index=1,
                start_time=self.DEFAULT_START,
                end_time=self.DEFAULT_END,
                day_offset_start=0,
                day_offset_end=0,
            )
        ]

    def resolve(self, company_id: str, user_id: UUID, work_date: date) -> ScheduleBaseline:
        assignment = self.assignment_repo.get_effective_assignment(company_id, user_id, work_date)
        if assignment is None:
            segments = self._default_segments()
            return ScheduleBaseline(
                segments=segments,
                normalized_windows=self._normalize_windows(work_date, segments),
                metadata={"source": "default"},
            )

        template = self.template_repo.get_by_id(assignment.shift_template_id, company_id)
        if template is None:
            segments = self._default_segments()
            return ScheduleBaseline(
                segments=segments,
                normalized_windows=self._normalize_windows(work_date, segments),
                metadata={"source": "default_missing_template", "assignment_id": assignment.id},
            )

        seg_rows = self.template_repo.list_segments(template.id, template.company_id, active_only=True)
        if seg_rows:
            segments = [
                ScheduleBaselineSegment(
                    segment_index=s.segment_index,
                    start_time=s.start_time,
                    end_time=s.end_time,
                    day_offset_start=s.day_offset_start,
                    day_offset_end=s.day_offset_end,
                )
                for s in seg_rows
            ]
            source = "template_segments"
        else:
            segments = self._fallback_from_template(template)
            source = "template_fallback"

        return ScheduleBaseline(
            segments=sorted(segments, key=lambda x: x.segment_index),
            normalized_windows=self._normalize_windows(work_date, segments),
            metadata={
                "template_id": template.id,
                "assignment_id": assignment.id,
                "source": source,
            },
        )


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

    def create_shift_template(
        self, company_id: str, payload: ShiftTemplateCreate
    ) -> ShiftTemplateRead:
        if payload.company_id is not None and payload.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="company_id mismatch: cannot create template for another company.",
            )

        existing = self.template_repo.get_by_code(code=payload.code, company_id=company_id)
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
        self.db.add(obj)
        self.db.flush()

        normalized_segments = _normalize_segments(payload.segments)
        if normalized_segments is not None:
            self.template_repo.replace_segments_no_commit(obj.id, company_id, normalized_segments)

        self.db.commit()
        self.db.refresh(obj)
        return ShiftTemplateRead.model_validate(obj)

    def get_shift_template(
        self, company_id: str, template_id: UUID
    ) -> ShiftTemplateRead:
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
        obj = self.template_repo.get_by_id(template_id, company_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ShiftTemplate {template_id} not found.",
            )

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

        normalized_segments = _normalize_segments(payload.segments)
        if normalized_segments is not None:
            self.template_repo.replace_segments_no_commit(obj.id, company_id, normalized_segments)

        obj.updated_at = _utcnow()
        self.db.commit()
        self.db.refresh(obj)
        return ShiftTemplateRead.model_validate(obj)

    def deactivate_shift_template(
        self, company_id: str, template_id: UUID
    ) -> ShiftTemplateRead:
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
        obj = self.template_repo.set_active(template_id, company_id, is_active=True)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ShiftTemplate {template_id} not found.",
            )
        return ShiftTemplateRead.model_validate(obj)

    def create_shift_assignment(
        self, company_id: str, payload: ShiftAssignmentCreate
    ) -> ShiftAssignmentRead:
        if payload.company_id is not None and payload.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="company_id mismatch: cannot create assignment for another company.",
            )

        template = self.template_repo.get_by_id(
            payload.shift_template_id, company_id
        )
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"ShiftTemplate {payload.shift_template_id} not found "
                    "in this company."
                ),
            )
        if not template.is_active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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

        if payload.shift_template_id is not None:
            template = self.template_repo.get_by_id(
                payload.shift_template_id, company_id
            )
            if template is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=(
                        f"ShiftTemplate {payload.shift_template_id} not found "
                        "in this company."
                    ),
                )
            if not template.is_active:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"ShiftTemplate {payload.shift_template_id} is not active.",
                )
            obj.shift_template_id = payload.shift_template_id

        if payload.status is not None:
            new_status = payload.status.value
            if new_status not in ASSIGNMENT_STATUS_VALUES:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Invalid status '{new_status}'.",
                )
            obj.status = new_status

        if payload.notes is not None:
            obj.notes = payload.notes

        saved = self.assignment_repo.update(obj)
        return ShiftAssignmentRead.model_validate(saved)

    def cancel_shift_assignment(
        self,
        company_id: str,
        assignment_id: UUID,
    ) -> ShiftAssignmentRead:
        obj = self.assignment_repo.get_by_id(assignment_id, company_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ShiftAssignment {assignment_id} not found.",
            )

        if obj.status == ASSIGNMENT_STATUS_CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Assignment already cancelled.",
            )

        obj.status = ASSIGNMENT_STATUS_CANCELLED
        saved = self.assignment_repo.update(obj)
        return ShiftAssignmentRead.model_validate(saved)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_schedule_service(db: Session) -> ScheduleService:
    return ScheduleService(db)
