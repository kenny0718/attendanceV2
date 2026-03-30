"""Checkpoint Repository（OUT Checkpoint 資料存取層）

Phase R2: Extracted from repo.py as part of attendance module boundary strengthening.

WP-C1-09: OutCheckpointRepository
WP-11-10: OUT Checkpoint API

Tenant Isolation:
- 所有查詢必須強制 WHERE company_id = ?
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.modules.attendance.models import AttendanceOutCheckpoint

logger = logging.getLogger(__name__)


# ============================================
# WP-C1-09: OutCheckpointRepository
# ============================================

class OutCheckpointRepository:
    """OUT checkpoint 資料存取層 (WP-C1-09 / WP-11-10)"""

    def __init__(self, db: Session):
        self.db = db

    def create_checkpoint(
        self,
        company_id: str,
        user_id: UUID,
        device_type: str,
        punch_time: datetime,
        session_id: Optional[UUID] = None,
        gps_lat: Optional[float] = None,
        gps_lng: Optional[float] = None,
        gps_accuracy_m: Optional[float] = None,
        gps_captured_at: Optional[datetime] = None,
        gps_provider: Optional[str] = None,
        client_timezone: Optional[str] = None,
        client_user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """創建 OUT checkpoint"""
        checkpoint = AttendanceOutCheckpoint(
            company_id=company_id,
            user_id=user_id,
            session_id=session_id,
            punch_time=punch_time,
            device_type=device_type,
            gps_lat=gps_lat,
            gps_lng=gps_lng,
            gps_accuracy_m=gps_accuracy_m,
            gps_captured_at=gps_captured_at,
            gps_provider=gps_provider,
            client_timezone=client_timezone,
            client_user_agent=client_user_agent,
            ip_address=ip_address,
            notes=notes
        )

        self.db.add(checkpoint)
        self.db.commit()
        self.db.refresh(checkpoint)

        logger.info(
            f"Created OUT checkpoint: id={checkpoint.id}, "
            f"company_id={company_id}, user_id={user_id}, device_type={device_type}"
        )

        return checkpoint

    def get_recent_checkpoint(
        self,
        company_id: str,
        user_id: UUID,
        within_seconds: int
    ):
        """獲取最近的 checkpoint (用於 de-dup 檢查)

        Tenant Isolation: 強制 WHERE company_id = ?
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=within_seconds)

        return (
            self.db.query(AttendanceOutCheckpoint)
            .filter(
                and_(
                    AttendanceOutCheckpoint.company_id == company_id,
                    AttendanceOutCheckpoint.user_id == user_id,
                    AttendanceOutCheckpoint.punch_time >= cutoff_time
                )
            )
            .order_by(AttendanceOutCheckpoint.punch_time.desc())
            .first()
        )

    def get_checkpoints(
        self,
        company_id: str,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        session_id: Optional[UUID] = None
    ):
        """獲取用戶的 checkpoints (分頁)

        Tenant Isolation: 強制 WHERE company_id = ?
        """
        query = (
            self.db.query(AttendanceOutCheckpoint)
            .filter(
                and_(
                    AttendanceOutCheckpoint.company_id == company_id,
                    AttendanceOutCheckpoint.user_id == user_id
                )
            )
        )

        if session_id:
            query = query.filter(AttendanceOutCheckpoint.session_id == session_id)

        return (
            query
            .order_by(AttendanceOutCheckpoint.punch_time.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def count_checkpoints(
        self,
        company_id: str,
        user_id: UUID,
        session_id: Optional[UUID] = None
    ) -> int:
        """計算用戶的 checkpoints 總數"""
        query = (
            self.db.query(AttendanceOutCheckpoint)
            .filter(
                and_(
                    AttendanceOutCheckpoint.company_id == company_id,
                    AttendanceOutCheckpoint.user_id == user_id
                )
            )
        )

        if session_id:
            query = query.filter(AttendanceOutCheckpoint.session_id == session_id)

        return query.count()

    def get_checkpoints_by_session(
        self,
        session_id: UUID
    ):
        """獲取 session 的所有 checkpoints"""
        return (
            self.db.query(AttendanceOutCheckpoint)
            .filter(AttendanceOutCheckpoint.session_id == session_id)
            .order_by(AttendanceOutCheckpoint.punch_time.asc())
            .all()
        )


def get_out_checkpoint_repository(db: Session) -> OutCheckpointRepository:
    """Factory function for OutCheckpointRepository (WP-C1-09)"""
    return OutCheckpointRepository(db)
