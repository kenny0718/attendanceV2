"""
Schedule Module — Pydantic Schemas
===================================
WP-S1-01 Foundation: Minimal schema definitions aligned with ORM models.
WP-S1-02 Alignment: UUID fields corrected to match models.py (company_id: str,
  id / user_id / shift_template_id: UUID).

Schemas defined here:
  - ShiftTemplateBase / Create / Update / Read
  - ShiftAssignmentBase / Create / Update / Read

Out of scope (future tickets):
  - Pagination response wrappers
  - Complex nested serialization
  - Attendance / leave overlay schemas
"""

import enum
from datetime import date, datetime, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations (mirrors models.AssignmentStatus)
# ---------------------------------------------------------------------------

class AssignmentStatusSchema(str, enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# ShiftTemplate schemas
# ---------------------------------------------------------------------------

class ShiftTemplateBase(BaseModel):
    company_id:     str  # String(255), FK to tenants.id (WP-S1-02 alignment)
    code:           str = Field(..., max_length=32)
    name:           str = Field(..., max_length=64)
    start_time:     time
    end_time:       time
    break_minutes:  int = Field(default=0, ge=0)
    is_overnight:   bool = False
    is_active:      bool = True


class ShiftTemplateCreate(ShiftTemplateBase):
    """Schema for creating a new ShiftTemplate."""
    pass


class ShiftTemplateUpdate(BaseModel):
    """Schema for partial update of a ShiftTemplate."""
    name:          Optional[str]  = Field(None, max_length=64)
    start_time:    Optional[time] = None
    end_time:      Optional[time] = None
    break_minutes: Optional[int]  = Field(None, ge=0)
    is_overnight:  Optional[bool] = None
    is_active:     Optional[bool] = None


class ShiftTemplateRead(ShiftTemplateBase):
    """Schema for reading / returning a ShiftTemplate."""
    id:         UUID  # UUID PK (WP-S1-02 alignment)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# ShiftAssignment schemas
# ---------------------------------------------------------------------------

class ShiftAssignmentBase(BaseModel):
    company_id:        str   # String(255), FK to tenants.id (WP-S1-02 alignment)
    user_id:           UUID  # UUID, FK to users.id (WP-S1-02 alignment)
    shift_template_id: UUID  # UUID, FK to shift_templates.id (WP-S1-02 alignment)
    work_date:         date
    status:            AssignmentStatusSchema = AssignmentStatusSchema.SCHEDULED
    notes:             Optional[str] = None


class ShiftAssignmentCreate(ShiftAssignmentBase):
    """Schema for creating a new ShiftAssignment."""
    pass


class ShiftAssignmentUpdate(BaseModel):
    """Schema for partial update of a ShiftAssignment."""
    shift_template_id: Optional[UUID]                  = None  # UUID (WP-S1-02 alignment)
    status:            Optional[AssignmentStatusSchema] = None
    notes:             Optional[str]                  = None


class ShiftAssignmentRead(ShiftAssignmentBase):
    """Schema for reading / returning a ShiftAssignment."""
    id:            UUID  # UUID PK (WP-S1-02 alignment)
    created_at:    datetime
    updated_at:    datetime

    class Config:
        from_attributes = True
