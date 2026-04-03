"""
Schedule Module — Service Layer
=================================
WP-S1-03 CRUD Core: Full implementation replacing WP-S1-01 stubs.

Responsibilities:
  - Business rules for ShiftTemplate management.
  - Business rules for ShiftAssignment CRUD.
  - Tenant isolation enforcement (all ops scoped to company_id).
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .models import (
    ASSIGNMENT_STATUS_CANCELLED,
    ASSIGNMENT_STATUS_SCHEDULED,
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
    ShiftSegmentRead,
    ShiftTemplateCreate,
    ShiftTemplateRead,
    ShiftTemplateUpdate,
)

logger = logging.getLogger(__name__)
TZ_TAIPEI = ZoneInfo("Asia/Taipei")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


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
    normalized_windows: List[Tuple[datetime, datetime]]
    metadata: Dict[str, object]


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
    ) -> List[Tuple[datetime, datetime]]:
        windows: List[Tuple[datetime, datetime]] = []
        for seg in sorted(segments, key=lambda x: x.segment_index):
            start_local = datetime.combine(
                work_date + timedelta(days=seg.day_offset_start),
                seg.start_time,
                tzinfo=TZ_TAIPEI,
            )
            end_local = datetime.combine(
                work_date + timedelta(days=seg.day_offset_end),
                seg.end_time,
                tzinfo=TZ_TAIPEI,
            )
            windows.append((start_local, end_local))
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
        assignment = self.assignment_repo.get_effective_assignment(
            company_id=company_id,
            user_id=user_id,
            work_date=work_date,
        )

        if assignment is None:
            segments = self._default_segments()
            return ScheduleBaseline(
                segments=segments,
                normalized_windows=self._normalize_windows(work_date, segments),
                metadata={"template_id": None, "assignment_id": None, "source": "default_fallback"},
            )

        template = self.template_repo.get_by_id(assignment.shift_template_id, company_id)
        if template is None:
            segments = self._default_segments()
            return ScheduleBaseline(
                segments=segments,
                normalized_windows=self._normalize_windows(work_date, segments),
                metadata={"template_id": None, "assignment_id": assignment.id, "source": "default_fallback"},
            )

        seg_rows = self.template_repo.list_segments(template.id, company_id, active_only=True)
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
            source = "assignment_segments"
        else:
            segments = self._fallback_from_template(template)
            source = "assignment_template_fallback"

        segments = sorted(segments, key=lambda x: x.segment_index)
        return ScheduleBaseline(
            segments=segments,
            normalized_windows=self._normalize_windows(work_date, segments),
            metadata={"template_id": template.id, "assignment_id": assignment.id, "source": source},
        )


class ScheduleService:
    """Business-logic layer for schedule module."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.template_repo = ShiftTemplateRepo(db)
        self.assignment_repo = ShiftAssignmentRepo(db)

    # ------------------------------------------------------------------
    # ShiftTemplate operations
    # ------------------------------------------------------------------

    def _segment_to_absolute_minutes(self, day_offset: int, t: time) -> int:
        return day_offset * 1440 + (t.hour * 60 + t.minute)

    def _validate_segments_payload(self, segments: List[ShiftSegmentCreate]) -> None:
        if not segments:
            return

        indexes = [s.segment_index for s in segments]
        if len(indexes) != len(set(indexes)):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="segment_index must be unique within the same template.",
            )

        ordered = sorted(segments, key=lambda s: s.segment_index)
        ranges = []
        for seg in ordered:
            start_abs = self._segment_to_absolute_minutes(seg.day_offset_start, seg.start_time)
            end_abs = self._segment_to_absolute_minutes(seg.day_offset_end, seg.end_time)
            if end_abs < start_abs:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="segment end must be greater than or equal to start in absolute timeline.",
                )
            ranges.append((seg.segment_index, start_abs, end_abs))

        by_start = sorted(ranges, key=lambda x: (x[1], x[2], x[0]))
        for i in range(1, len(by_start)):
            prev_idx, _, prev_end = by_start[i - 1]
            curr_idx, curr_start, _ = by_start[i]
            if curr_start < prev_end:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"segments overlap: segment {prev_idx} and {curr_idx}.",
                )

    def _serialize_segments_for_repo(self, segments: List[ShiftSegmentCreate]) -> List[dict]:
        return [
            {
                "segment_index": s.segment_index,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "day_offset_start": s.day_offset_start,
                "day_offset_end": s.day_offset_end,
                "is_active": s.is_active,
            }
            for s in sorted(segments, key=lambda x: x.segment_index)
        ]

    def _build_fallback_segments(self, template: ShiftTemplate) -> List[ShiftSegmentRead]:
        day_offset_end = 1 if bool(template.is_overnight) else 0
        return [
            ShiftSegmentRead(
                id=None,
                segment_index=1,
                start_time=template.start_time,
                end_time=template.end_time,
                day_offset_start=0,
                day_offset_end=day_offset_end,
                is_active=True,
            )
        ]

    def _compose_template_read(self, template: ShiftTemplate) -> ShiftTemplateRead:
        seg_objs = self.template_repo.list_segments(template.id, template.company_id, active_only=True)
        if seg_objs:
            segments = [ShiftSegmentRead.model_validate(s) for s in seg_objs]
        else:
            segments = self._build_fallback_segments(template)

        return ShiftTemplateRead(
            id=template.id,
            company_id=template.company_id,
            code=template.code,
            name=template.name,
            start_time=template.start_time,
            end_time=template.end_time,
            break_minutes=template.break_minutes,
            is_overnight=template.is_overnight,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at,
            segments=segments,
        )

    def create_shift_template(self, company_id: str, payload: ShiftTemplateCreate) -> ShiftTemplateRead:
        if payload.company_id != company_id:
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

        segments_payload = payload.segments or []
        self._validate_segments_payload(segments_payload)

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

        if segments_payload:
            try:
                self.db.add(obj)
                self.db.flush()
                rows = self._serialize_segments_for_repo(segments_payload)
                self.template_repo.replace_segments_no_commit(obj.id, company_id, rows)
                self.db.commit()
                self.db.refresh(obj)
            except Exception:
                self.db.rollback()
                raise
        else:
            obj = self.template_repo.create(obj)

        return self._compose_template_read(obj)

    def get_shift_template(self, company_id: str, template_id: UUID) -> ShiftTemplateRead:
        obj = self.template_repo.get_by_id(template_id, company_id)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ShiftTemplate {template_id} not found.",
            )
        return self._compose_template_read(obj)

    def list_shift_templates(self, company_id: str, active_only: bool = True) -> List[ShiftTemplateRead]:
        objs = self.template_repo.list_by_company(company_id=company_id, active_only=active_only)
        return [self._compose_template_read(o) for o in objs]

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

        if payload.segments is not None:
            self._validate_segments_payload(payload.segments)
            try:
                obj.updated_at = _utcnow()
                rows = self._serialize_segments_for_repo(payload.segments)
                self.template_repo.replace_segments_no_commit(template_id, company_id, rows)
                self.db.commit()
                self.db.refresh(obj)
            except Exception:
                self.db.rollback()
                raise
            saved = obj
        else:
            saved = self.template_repo.update(obj)

        return self._compose_template_read(saved)

    def deactivate_shift_template(self, company_id: str, template_id: UUID) -> ShiftTemplateRead:
        obj = self.template_repo.set_active(template_id, company_id, is_active=False)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ShiftTemplate {template_id} not found.",
            )
        return self._compose_template_read(obj)

    def activate_shift_template(self, company_id: str, template_id: UUID) -> ShiftTemplateRead:
        obj = self.template_repo.set_active(template_id, company_id, is_active=True)
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ShiftTemplate {template_id} not found.",
            )
        return self._compose_template_read(obj)

    # ------------------------------------------------------------------
    # ShiftAssignment operations
    # ------------------------------------------------------------------

    def create_shift_assignment(self, company_id: str, payload: ShiftAssignmentCreate) -> ShiftAssignmentRead:
        if payload.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="company_id mismatch: cannot create assignment for another company.",
            )

        template = self.template_repo.get_by_id(payload.shift_template_id, company_id)
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

    def get_shift_assignment(self, company_id: str, assignment_id: UUID) -> ShiftAssignmentRead:
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
            template = self.template_repo.get_by_id(payload.shift_template_id, company_id)
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

    def cancel_shift_assignment(self, company_id: str, assignment_id: UUID) -> ShiftAssignmentRead:
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
    return ScheduleService(db)


def get_schedule_baseline_resolver(db: Session) -> ScheduleBaselineResolver:
    return ScheduleBaselineResolver(db)
