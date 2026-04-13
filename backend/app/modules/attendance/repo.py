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
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.attendance.attendance_punch_repo import AttendancePunchRepository
from app.modules.attendance.models import AttendancePolicy, AttendancePunch, AttendanceSession
from app.modules.tenants.repo import TenantRepository

logger = logging.getLogger(__name__)


def get_current_time() -> datetime:
    """Return current UTC time (timezone-aware)"""
    return datetime.now(timezone.utc)


class AttendanceSessionRepository:
    """出勤 Session 資料存取層 (WP-11-02)"""

    def __init__(self, db: Session):
        self.db = db
        self._punch_repo = AttendancePunchRepository(db)

    def create_session(
        self,
        company_id: str,
        user_id: UUID,
        punch_in_time: datetime,
        notes: Optional[str] = None,
    ) -> AttendanceSession:
        """創建新的出勤 session"""
        existing_session = self.get_open_session(company_id=company_id, user_id=user_id)
        if existing_session is not None:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": f"User already has an open session in company {company_id}",
                    "error_code": "ALREADY_OPEN_SESSION",
                    "open_session_id": str(existing_session.id),
                },
            )

        session = AttendanceSession(
            company_id=company_id,
            user_id=user_id,
            punch_in_time=punch_in_time,
            status="open",
            notes=notes,
        )

        self.db.add(session)
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            if "uq_sessions_company_user_open" in str(e):
                existing_session = self.get_open_session(company_id=company_id, user_id=user_id)
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": f"User already has an open session in company {company_id}",
                        "error_code": "ALREADY_OPEN_SESSION",
                        "open_session_id": str(existing_session.id) if existing_session else None,
                    },
                ) from e
            raise

        self.db.refresh(session)

        logger.info(
            f"Created session: id={session.id}, "
            f"company_id={company_id}, user_id={user_id}"
        )

        return session

    def get_open_session(self, company_id: str, user_id: UUID) -> Optional[AttendanceSession]:
        """獲取用戶的 open session

        Tenant Isolation: 強制 WHERE company_id = ?
        """
        return (
            self.db.query(AttendanceSession)
            .filter(
                and_(
                    AttendanceSession.company_id == company_id,
                    AttendanceSession.user_id == user_id,
                    AttendanceSession.status == "open",
                )
            )
            .first()
        )

    def close_session(
        self,
        session: Optional[AttendanceSession] = None,
        punch_out_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
        policy_id: Optional[UUID] = None,
        *,
        company_id: Optional[str] = None,
        session_id: Optional[UUID] = None,
    ) -> Optional[AttendanceSession]:
        """關閉 session。

        支援兩種呼叫方式：
        1. 新版：傳入 session 物件 + duration_minutes
        2. 舊版測試相容：傳入 company_id + session_id + punch_out_time，自動查詢並計算 duration
        """
        target_session = session
        if target_session is None:
            if company_id is None or session_id is None or punch_out_time is None:
                raise TypeError("close_session requires either session or company_id/session_id/punch_out_time")
            target_session = (
                self.db.query(AttendanceSession)
                .filter(
                    and_(
                        AttendanceSession.company_id == company_id,
                        AttendanceSession.id == session_id,
                    )
                )
                .first()
            )
            if target_session is None or target_session.status != "open":
                return None
            duration_minutes = int((punch_out_time - target_session.punch_in_time).total_seconds() / 60)

        if target_session.status != "open":
            return None
        if punch_out_time is None or duration_minutes is None:
            raise TypeError("punch_out_time and duration_minutes are required when closing a session")

        target_session.punch_out_time = punch_out_time
        target_session.status = "closed"
        target_session.duration_minutes = duration_minutes
        target_session.policy_id = policy_id
        target_session.updated_at = get_current_time()

        self.db.commit()
        self.db.refresh(target_session)

        logger.info(
            f"Closed session: id={target_session.id}, "
            f"duration={duration_minutes}m, policy_id={policy_id}"
        )

        return target_session

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
        location_id: Optional[UUID] = None,
    ) -> AttendancePunch:
        """創建打卡記錄"""
        return self._punch_repo.create_punch(
            session_id=session_id,
            company_id=company_id,
            user_id=user_id,
            punch_type=punch_type,
            punch_time=punch_time,
            ip_address=ip_address,
            location_lat=location_lat,
            location_lng=location_lng,
            notes=notes,
            location_id=location_id,
        )

    def get_sessions(
        self,
        company_id: str,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> List[AttendanceSession]:
        """獲取用戶的 sessions (分頁)

        Tenant Isolation: 強制 WHERE company_id = ?
        """
        query = (
            self.db.query(AttendanceSession)
            .filter(
                and_(
                    AttendanceSession.company_id == company_id,
                    AttendanceSession.user_id == user_id,
                )
            )
        )

        if status:
            query = query.filter(AttendanceSession.status == status)

        return (
            query.order_by(AttendanceSession.punch_in_time.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def count_sessions(self, company_id: str, user_id: UUID, status: Optional[str] = None) -> int:
        """計算用戶的 sessions 總數"""
        query = (
            self.db.query(AttendanceSession)
            .filter(
                and_(
                    AttendanceSession.company_id == company_id,
                    AttendanceSession.user_id == user_id,
                )
            )
        )

        if status:
            query = query.filter(AttendanceSession.status == status)

        return query.count()

    def get_user_policy(self, company_id: str, user_id: UUID) -> Optional[AttendancePolicy]:
        """獲取用戶的考勤政策 (WP-11-05C)

        Tenant Isolation: 強制 WHERE company_id = ?
        """
        return (
            self.db.query(AttendancePolicy)
            .filter(
                and_(
                    AttendancePolicy.company_id == company_id,
                    AttendancePolicy.is_default == True,
                    AttendancePolicy.is_active == True,
                )
            )
            .first()
        )

    def get_last_break_punch(self, session_id: UUID) -> Optional[AttendancePunch]:
        """獲取 session 的最後一筆 break punch (WP-11-07 Phase 3B)"""
        return self._punch_repo.get_last_break_punch(session_id)

    def update_punch_note(
        self,
        company_id: str,
        user_id: UUID,
        punch_id: UUID,
        notes: str,
    ) -> Optional[AttendancePunch]:
        """更新打卡備註"""
        return self._punch_repo.update_punch_note(
            company_id=company_id,
            user_id=user_id,
            punch_id=punch_id,
            notes=notes,
        )

    def list_break_punches_for_user_in_range(
        self,
        company_id: str,
        user_id: UUID,
        start_utc: datetime,
        end_utc: datetime,
        limit: int,
    ) -> list[AttendancePunch]:
        """列出指定時間區間內的 break punches。"""
        return self._punch_repo.list_break_punches_for_user_in_range(
            company_id=company_id,
            user_id=user_id,
            start_utc=start_utc,
            end_utc=end_utc,
            limit=limit,
        )

    def get_session_punches(self, session_id: UUID) -> list:
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
        """Read-only: 取得 company/user 在 business date 對應區間內的 sessions。"""
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
        """Read-only: 取得 company/user 在 business date 對應區間內的 punches。"""
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


class AttendanceRepository:
    """考勤記錄資料存取層 (舊版 - Phase 4)"""

    def __init__(self, db: Session):
        self.db = db
        self.tenant_repo = TenantRepository(db)

    def create_attendance_record(
        self,
        company_id: str,
        employee_id: str,
        approved_by: Optional[str] = None,
        approved_at: Optional[str] = None,
    ):
        """建立考勤記錄 (舊版)"""
        from app.modules.attendance.models import AttendanceRecord

        if not self.tenant_repo.exists(company_id):
            raise HTTPException(
                status_code=404,
                detail={"error": f"Tenant {company_id} does not exist"},
            )

        record = AttendanceRecord(
            company_id=company_id,
            employee_id=employee_id,
            approved_by=approved_by,
            approved_at=approved_at,
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return record

    def approve_attendance_record(
        self,
        company_id: str,
        record_id: UUID,
        approved_by: Optional[str] = None,
    ):
        """核准考勤記錄 (舊版)"""
        from app.modules.attendance.models import AttendanceRecord

        record = (
            self.db.query(AttendanceRecord)
            .filter(
                and_(
                    AttendanceRecord.id == record_id,
                    AttendanceRecord.company_id == company_id,
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

    def get_attendance_records(self, company_id: str):
        """取得公司下所有舊版 attendance records。"""
        from app.modules.attendance.models import AttendanceRecord

        return (
            self.db.query(AttendanceRecord)
            .filter(AttendanceRecord.company_id == company_id)
            .order_by(AttendanceRecord.created_at.asc())
            .all()
        )


def get_attendance_repository(db: Session) -> AttendanceRepository:
    """Factory function for old repository (Phase 4 compatibility)"""
    return AttendanceRepository(db)
