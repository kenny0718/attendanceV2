"""
Schedule Module — ORM Models
============================
WP-S1-01 Foundation: Code-level model definition only.
WP-S1-01A: Models Alignment Fix — aligned to project-wide conventions.

No migration is performed in WP-S1-01 / WP-S1-01A.
Migration will be created in WP-S1-02.

Models defined here:
  - ShiftTemplate   : Represents a reusable shift pattern (e.g., Day Shift).
  - ShiftAssignment : Represents a single user's shift on a specific date.

Alignment changes (WP-S1-01A):
  - company_id: Integer → String(255), FK → tenants.id CASCADE
  - user_id: Integer → UUID, FK → users.id CASCADE
  - id (PK): Integer → UUID + gen_random_uuid()
  - FK style: inline ForeignKey → ForeignKeyConstraint in __table_args__
  - timestamps: DateTime → DateTime(timezone=True) + server_default=NOW()
  - AssignmentStatus: SQLAlchemy Enum type → String(20) + CheckConstraint
  - ShiftTemplate: added UniqueConstraint(company_id, code)

Out of scope (future tickets):
  - Alembic migration (WP-S1-02)
  - Rotation / recurring rules
  - Conflict detection
  - Attendance integration
  - Leave integration
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from app.core.database import Base


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# AssignmentStatus values (used in CheckConstraint and application layer)
# WP-S1-01A: Changed from SQLAlchemy Enum type to String(20) + CheckConstraint,
# consistent with attendance session status convention (String + CheckConstraint).
# This avoids PostgreSQL CREATE TYPE complexity in migrations.
ASSIGNMENT_STATUS_SCHEDULED = "scheduled"
ASSIGNMENT_STATUS_CONFIRMED = "confirmed"
ASSIGNMENT_STATUS_CANCELLED = "cancelled"

ASSIGNMENT_STATUS_VALUES = (
    ASSIGNMENT_STATUS_SCHEDULED,
    ASSIGNMENT_STATUS_CONFIRMED,
    ASSIGNMENT_STATUS_CANCELLED,
)


# ---------------------------------------------------------------------------
# ShiftTemplate
# ---------------------------------------------------------------------------

class ShiftTemplate(Base):
    """
    Represents a reusable shift pattern belonging to a company.

    Examples: 「日班」(Day), 「夜班」(Night), 「休假」(Off).

    Tenant Isolation: all queries must filter by company_id.

    Constraints / Rules (WP-S1-01A scope):
      - code is unique per company (UniqueConstraint).
      - is_overnight flag is informational only at this stage.
      - break_minutes is stored but not used in any calculation yet.
      - No migration yet; table does not exist in DB until WP-S1-02.
    """
    __tablename__ = "shift_templates"

    # Primary key — UUID, consistent with attendance/leave models
    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="ShiftTemplate ID (PK)",
    )

    # Tenant isolation — String(255), FK to tenants.id
    company_id = Column(
        String(255),
        nullable=False,
        comment="Company ID (Tenant Isolation, FK to tenants.id)",
    )

    # Identity
    code = Column(
        String(32),
        nullable=False,
        comment="Shift code, unique per company (e.g. DAY, NIGHT)",
    )
    name = Column(
        String(64),
        nullable=False,
        comment="Shift display name (e.g. 日班)",
    )

    # Time definition
    start_time = Column(Time, nullable=False, comment="Shift start time")
    end_time   = Column(Time, nullable=False, comment="Shift end time")
    break_minutes = Column(
        SmallInteger,
        nullable=False,
        server_default="0",
        comment="Break duration in minutes (informational, not deducted yet)",
    )
    is_overnight = Column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="True if shift crosses midnight (informational only at this stage)",
    )

    # Status
    is_active = Column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Soft-delete flag",
    )

    # Timestamps — timezone-aware, consistent with attendance/leave convention
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Created timestamp (UTC)",
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Updated timestamp (UTC)",
    )

    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint(
            "company_id", "code",
            name="uq_shift_templates_company_code",
        ),
        ForeignKeyConstraint(
            ["company_id"], ["tenants.id"],
            ondelete="CASCADE",
        ),
        Index("idx_shift_templates_company", "company_id"),
        Index("idx_shift_templates_company_active", "company_id", "is_active"),
    )

    # Reverse relationship
    assignments = relationship(
        "ShiftAssignment",
        back_populates="shift_template",
        lazy="dynamic",
    )
    segments = relationship(
        "ShiftSegment",
        back_populates="shift_template",
        order_by="ShiftSegment.segment_index",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<ShiftTemplate id={self.id} code={self.code!r}"
            f" company={self.company_id}>"
        )


# ---------------------------------------------------------------------------
# ShiftSegment
# ---------------------------------------------------------------------------

class ShiftSegment(Base):
    """Represents one segment row inside a ShiftTemplate."""
    __tablename__ = "shift_segments"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="ShiftSegment ID (PK)",
    )
    company_id = Column(
        String(255),
        nullable=False,
        comment="Company ID (Tenant Isolation, FK to tenants.id)",
    )
    shift_template_id = Column(
        PGUUID(as_uuid=True),
        nullable=False,
        comment="ShiftTemplate ID (FK to shift_templates.id)",
    )
    segment_index = Column(
        Integer,
        nullable=False,
        comment="Segment order index starting from 1",
    )
    start_time = Column(Time, nullable=False, comment="Segment start time")
    end_time = Column(Time, nullable=False, comment="Segment end time")
    day_offset_start = Column(
        Integer,
        nullable=False,
        server_default="0",
        comment="Start day offset from shift day",
    )
    day_offset_end = Column(
        Integer,
        nullable=False,
        server_default="0",
        comment="End day offset from shift day",
    )
    is_active = Column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Soft-delete flag",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Created timestamp (UTC)",
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Updated timestamp (UTC)",
    )

    __table_args__ = (
        UniqueConstraint(
            "shift_template_id", "segment_index",
            name="uq_shift_segments_template_index",
        ),
        ForeignKeyConstraint(
            ["company_id"], ["tenants.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["shift_template_id"], ["shift_templates.id"],
            ondelete="CASCADE",
        ),
        Index("idx_shift_segments_company", "company_id"),
        Index("idx_shift_segments_template", "shift_template_id"),
        Index("idx_shift_segments_company_template", "company_id", "shift_template_id"),
    )

    shift_template = relationship(
        "ShiftTemplate",
        back_populates="segments",
    )

    def __repr__(self) -> str:
        return (
            f"<ShiftSegment id={self.id} template={self.shift_template_id}"
            f" idx={self.segment_index} company={self.company_id}>"
        )


# ---------------------------------------------------------------------------
# ShiftAssignment
# ---------------------------------------------------------------------------

class ShiftAssignment(Base):
    """
    Assigns a specific ShiftTemplate to a user on a specific calendar date.

    One row = one user, one date, one shift.

    Tenant Isolation: all queries must filter by company_id.

    Constraints / Rules (WP-S1-01A scope):
      - status: scheduled / confirmed / cancelled (String + CheckConstraint).
      - No conflict detection logic at this stage.
      - No automatic leave override at this stage.
      - No attendance record linkage at this stage.
      - No migration yet; table does not exist in DB until WP-S1-02.
    """
    __tablename__ = "shift_assignments"

    # Primary key — UUID, consistent with attendance/leave models
    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="ShiftAssignment ID (PK)",
    )

    # Tenant isolation — String(255), FK to tenants.id
    company_id = Column(
        String(255),
        nullable=False,
        comment="Company ID (Tenant Isolation, FK to tenants.id)",
    )

    # User reference — UUID, FK to users.id
    user_id = Column(
        PGUUID(as_uuid=True),
        nullable=False,
        comment="User ID (FK to users.id)",
    )

    # Shift reference
    shift_template_id = Column(
        PGUUID(as_uuid=True),
        nullable=False,
        comment="ShiftTemplate ID (FK to shift_templates.id)",
    )

    # Assignment date
    work_date = Column(
        Date,
        nullable=False,
        comment="Assigned work date (local date, Asia/Taipei)",
    )

    # Status — String(20) + CheckConstraint (consistent with attendance session)
    status = Column(
        String(20),
        nullable=False,
        server_default="scheduled",
        comment="Assignment status: scheduled / confirmed / cancelled",
    )

    # Notes
    notes = Column(Text, nullable=True, comment="Optional notes")

    # Timestamps — timezone-aware, consistent with attendance/leave convention
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Created timestamp (UTC)",
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Updated timestamp (UTC)",
    )

    # Indexes and constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled', 'confirmed', 'cancelled')",
            name="ck_shift_assignments_status",
        ),
        ForeignKeyConstraint(
            ["company_id"], ["tenants.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["shift_template_id"], ["shift_templates.id"],
            ondelete="RESTRICT",
        ),
        Index("idx_shift_assignments_company", "company_id"),
        Index("idx_shift_assignments_user", "user_id"),
        Index("idx_shift_assignments_company_user", "company_id", "user_id"),
        Index("idx_shift_assignments_company_date", "company_id", "work_date"),
        Index("idx_shift_assignments_template", "shift_template_id"),
    )

    # Relationship to parent template
    shift_template = relationship(
        "ShiftTemplate",
        back_populates="assignments",
    )

    def __repr__(self) -> str:
        return (
            f"<ShiftAssignment id={self.id} user={self.user_id}"
            f" date={self.work_date} template={self.shift_template_id}>"
        )
