"""
Schedule Module — Pydantic Schemas
===================================
WP-S1-01 Foundation: Minimal schema definitions aligned with ORM models.
WP-S1-02 Alignment: UUID fields corrected to match models.py (company_id: str,
  id / user_id / shift_template_id: UUID).
"""

import enum
from datetime import date, datetime, time
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AssignmentStatusSchema(str, enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class ShiftSegmentBase(BaseModel):
    segment_index: int = Field(..., ge=1)
    start_time: time
    end_time: time
    day_offset_start: int = 0
    day_offset_end: int = 0
    is_active: bool = True


class ShiftSegmentCreate(ShiftSegmentBase):
    pass


class ShiftSegmentRead(ShiftSegmentBase):
    id: Optional[UUID] = None

    class Config:
        from_attributes = True


class ShiftTemplateBase(BaseModel):
    company_id: str
    code: str = Field(..., max_length=32)
    name: str = Field(..., max_length=64)
    start_time: time
    end_time: time
    break_minutes: int = Field(default=0, ge=0)
    is_overnight: bool = False
    is_active: bool = True


class ShiftTemplateCreate(ShiftTemplateBase):
    segments: Optional[List[ShiftSegmentCreate]] = None


class ShiftTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=64)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_minutes: Optional[int] = Field(None, ge=0)
    is_overnight: Optional[bool] = None
    is_active: Optional[bool] = None
    segments: Optional[List[ShiftSegmentCreate]] = None


class ShiftTemplateRead(ShiftTemplateBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    segments: List[ShiftSegmentRead] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ShiftAssignmentBase(BaseModel):
    company_id: str
    user_id: UUID
    shift_template_id: UUID
    work_date: date
    status: AssignmentStatusSchema = AssignmentStatusSchema.SCHEDULED
    notes: Optional[str] = None


class ShiftAssignmentCreate(ShiftAssignmentBase):
    pass


class ShiftAssignmentUpdate(BaseModel):
    shift_template_id: Optional[UUID] = None
    status: Optional[AssignmentStatusSchema] = None
    notes: Optional[str] = None


class ShiftAssignmentRead(ShiftAssignmentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
