"""Attendance Punch Repository（資料存取層）

Punch-side repository extracted from repo.py for minimal write-path decomposition.

Scope for P6_F3A_IMPLEMENT:
- create_punch(...)
- get_last_break_punch(...)

No canonical/session semantics live here.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.modules.attendance.models import AttendancePunch

logger = logging.getLogger(__name__)


class AttendancePunchRepository:
    """Punch-side repository for attendance punch persistence/read access."""

    def __init__(self, db: Session):
        self.db = db

    def create_punch(
        self,
        session_id: UUID,
        company_id: str,
        user_id: UUID,
        punch_type: str,
        punch_time: datetime,
        ip_address: Optional[str] = None,
        location_lat: Optional[float] = None,
        location_lng: Optional[float] = None,
        notes: Optional[str] = None,
        location_id: Optional[UUID] = None
    ) -> AttendancePunch:
        """創建打卡記錄"""
        punch = AttendancePunch(
            session_id=session_id,
            company_id=company_id,
            user_id=user_id,
            punch_type=punch_type,
            punch_time=punch_time,
            ip_address=ip_address,
            location_lat=location_lat,
            location_lng=location_lng,
            notes=notes,
            location_id=location_id
        )

        self.db.add(punch)
        self.db.commit()
        self.db.refresh(punch)

        logger.info(
            f"Created punch: id={punch.id}, "
            f"session_id={session_id}, type={punch_type}"
        )

        return punch

    def get_last_break_punch(
        self,
        session_id: UUID
    ) -> Optional[AttendancePunch]:
        """獲取 session 的最後一筆 break punch (WP-11-07 Phase 3B)"""
        return (
            self.db.query(AttendancePunch)
            .filter(
                and_(
                    AttendancePunch.session_id == session_id,
                    AttendancePunch.punch_type.in_(['break_start', 'break_end'])
                )
            )
            .order_by(AttendancePunch.punch_time.desc())
            .first()
        )

    def update_punch_note(
        self,
        company_id: str,
        user_id: UUID,
        punch_id: UUID,
        notes: str
    ) -> Optional[AttendancePunch]:
        """更新打卡備註"""
        punch = self.db.query(AttendancePunch).filter(
            AttendancePunch.id == punch_id,
            AttendancePunch.company_id == company_id,
            AttendancePunch.user_id == user_id
        ).first()

        if not punch:
            return None

        punch.notes = notes
        self.db.commit()

        return punch

    def list_break_punches_for_user_in_range(
        self,
        company_id: str,
        user_id: UUID,
        start_utc: datetime,
        end_utc: datetime,
        limit: int
    ) -> list[AttendancePunch]:
        """列出指定時間區間內的 break punches"""
        return (
            self.db.query(AttendancePunch)
            .filter(
                and_(
                    AttendancePunch.company_id == company_id,
                    AttendancePunch.user_id == user_id,
                    AttendancePunch.punch_type.in_(['break_start', 'break_end']),
                    AttendancePunch.punch_time >= start_utc,
                    AttendancePunch.punch_time < end_utc
                )
            )
            .order_by(AttendancePunch.punch_time.desc())
            .limit(limit)
            .all()
        )
