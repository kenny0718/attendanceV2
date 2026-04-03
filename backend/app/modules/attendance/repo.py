"""Attendance Repository（資料存取層）

Tenant Isolation (P0)：
- 所有查詢必須強制 WHERE company_id = ?
- 支援單一 company_id 全量抽取（備份用）

WP-11-02: Added AttendanceSessionRepository for new attendance domain
WP-11-05C: Added policy retrieval methods
WP-11-07 Phase 3B: Added get_last_break_punch method
WP-C1-09: Added OutCheckpointRepository
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.modules.attendance.models import (
    AttendanceSession,
    AttendancePunch,
    AttendancePolicy
)

logger = logging.getLogger(__name__)


def get_current_time() -> datetime:
    """Return current UTC time (timezone-aware)"""
    return datetime.now(timezone.utc)


class AttendanceSessionRepository:
    """出勤 Session 資料存取層 (WP-11-02)"""

    def __init__(self, db: Session):
        self.db = db

    def create_session(
        self,
        company_id: str,
        user_id: UUID,
        punch_in_time: datetime,
        notes: Optional[str] = None
    ) -> AttendanceSession:
        """創建新的出勤 session"""
        session = AttendanceSession(
            company_id=company_id,
            user_id=user_id,
            punch_in_time=punch_in_time,
            status='open',
            notes=notes
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        logger.info(
            f"Created session: id={session.id}, "
            f"company_id={company_id}, user_id={user_id}"
        )

        return session

    def get_open_session(
        self,
        company_id: str,
        user_id: UUID
    ) -> Optional[AttendanceSession]:
        """獲取用戶的 open session

        Tenant Isolation: 強制 WHERE company_id = ?
        """
        return (
            self.db.query(AttendanceSession)
            .filter(
                and_(
                    AttendanceSession.company_id == company_id,
                    AttendanceSession.user_id == user_id,
                    AttendanceSession.status == 'open'
                )
            )
            .first()
        )

    def close_session(
        self,
        session: AttendanceSession,
        punch_out_time: datetime,
        duration_minutes: int,
        policy_id: Optional[UUID] = None
    ) -> AttendanceSession:
        """關閉 session (WP-11-05C: added policy_id and duration)"""
        session.punch_out_time = punch_out_time
        session.status = 'closed'
        session.duration_minutes = duration_minutes
        session.policy_id = policy_id
        session.updated_at = get_current_time()

        self.db.commit()
        self.db.refresh(session)

        logger.info(
            f"Closed session: id={session.id}, "
            f"duration={duration_minutes}m, policy_id={policy_id}"
        )

        return session

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

    def get_sessions(
        self,
        company_id: str,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[AttendanceSession]:
        """獲取用戶的 sessions (分頁)

        Tenant Isolation: 強制 WHERE company_id = ?
        """
        query = (
            self.db.query(AttendanceSession)
            .filter(
                and_(
                    AttendanceSession.company_id == company_id,
                    AttendanceSession.user_id == user_id
                )
            )
        )

        if status:
            query = query.filter(AttendanceSession.status == status)

        return (
            query
            .order_by(AttendanceSession.punch_in_time.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def count_sessions(
        self,
        company_id: str,
        user_id: UUID,
        status: Optional[str] = None
    ) -> int:
        """計算用戶的 sessions 總數"""
        query = (
            self.db.query(AttendanceSession)
            .filter(
                and_(
                    AttendanceSession.company_id == company_id,
                    AttendanceSession.user_id == user_id
                )
            )
        )

        if status:
            query = query.filter(AttendanceSession.status == status)

        return query.count()

    def get_user_policy(
        self,
        company_id: str,
        user_id: UUID
    ) -> Optional[AttendancePolicy]:
        """獲取用戶的考勤政策 (WP-11-05C)

        Tenant Isolation: 強制 WHERE company_id = ?
        """
        return (
            self.db.query(AttendancePolicy)
            .filter(
                and_(
                    AttendancePolicy.company_id == company_id,
                    AttendancePolicy.is_default == True,
                    AttendancePolicy.is_active == True
                )
            )
            .first()
        )

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

    def get_session_punches(
        self,
        session_id: UUID
    ) -> list:
        """獲取 session 的所有 punch 記錄"""
        return (
            self.db.query(AttendancePunch)
            .filter(AttendancePunch.session_id == session_id)
            .order_by(AttendancePunch.punch_time.asc())
            .all()
        )



    def get_sessions_by_company_user_business_date_range(
        self,
        company_id: str,
        user_id: UUID,
        business_day_start: datetime,
        business_day_end: datetime,
    ) -> List[AttendanceSession]:
        """Read-only: 取得 company/user 在 business date 對應區間內的 sessions。

        注意：
        - Tenant Isolation: 強制 WHERE company_id = ?
        - business date -> datetime range 的換算由 service 層決定，repo 不做業務推論
        - 使用 punch_in_time 作為日級 trace read-side 的最小安全查詢基準
        """
        return (
            self.db.query(AttendanceSession)
            .filter(
                and_(
                    AttendanceSession.company_id == company_id,
                    AttendanceSession.user_id == user_id,
                    AttendanceSession.punch_in_time >= business_day_start,
                    AttendanceSession.punch_in_time < business_day_end,
                )
            )
            .order_by(AttendanceSession.punch_in_time.asc())
            .all()
        )

    def get_punches_by_company_user_business_date_range(
        self,
        company_id: str,
        user_id: UUID,
        business_day_start: datetime,
        business_day_end: datetime,
    ) -> List[AttendancePunch]:
        """Read-only: 取得 company/user 在 business date 對應區間內的 punches。

        注意：
        - Tenant Isolation: 強制 WHERE company_id = ?
        - 僅提供 read-side 存取，不做 trace 組裝或規則判定
        """
        return (
            self.db.query(AttendancePunch)
            .filter(
                and_(
                    AttendancePunch.company_id == company_id,
                    AttendancePunch.user_id == user_id,
                    AttendancePunch.punch_time >= business_day_start,
                    AttendancePunch.punch_time < business_day_end,
                )
            )
            .order_by(AttendancePunch.punch_time.asc())
            .all()
        )

    def get_punches_by_company_user_and_session_ids(
        self,
        company_id: str,
        user_id: UUID,
        session_ids: List[UUID],
    ) -> List[AttendancePunch]:
        """Read-only: 依 company/user + session_ids 批次取得 punches。"""
        if not session_ids:
            return []

        return (
            self.db.query(AttendancePunch)
            .filter(
                and_(
                    AttendancePunch.company_id == company_id,
                    AttendancePunch.user_id == user_id,
                    AttendancePunch.session_id.in_(session_ids),
                )
            )
            .order_by(AttendancePunch.punch_time.asc())
            .all()
        )

def get_attendance_session_repository(db: Session) -> AttendanceSessionRepository:
    """Factory function for dependency injection"""
    return AttendanceSessionRepository(db)


# ============================================
# 舊的 Repository (Phase 4) - 保持兼容
# ============================================

class AttendanceRepository:
    """考勤記錄資料存取層 (舊版 - Phase 4)"""

    def __init__(self, db: Session):
        self.db = db

    def create_attendance_record(
        self,
        company_id: str,
        employee_id: str,
        approved_by: Optional[str] = None,
        approved_at: Optional[str] = None
    ):
        """建立考勤記錄 (舊版)"""
        from app.modules.attendance.models import AttendanceRecord

        record = AttendanceRecord(
            company_id=company_id,
            employee_id=employee_id,
            approved_by=approved_by,
            approved_at=approved_at
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return record

    def approve_attendance_record(
        self,
        company_id: str,
        record_id: UUID,
        approved_by: Optional[str] = None
    ):
        """核准考勤記錄 (舊版)"""
        from app.modules.attendance.models import AttendanceRecord

        record = (
            self.db.query(AttendanceRecord)
            .filter(
                and_(
                    AttendanceRecord.id == record_id,
                    AttendanceRecord.company_id == company_id
                )
            )
            .first()
        )

        if not record:
            return None

        record.approved_by = approved_by
        record.approved_at = get_current_time()

        self.db.commit()
        self.db.refresh(record)

        return record


def get_attendance_repository(db: Session) -> AttendanceRepository:
    """Factory function for old repository (Phase 4 compatibility)"""
    return AttendanceRepository(db)

