"""Attendance Repository（資料存取層）

Tenant Isolation (P0)：
- 所有查詢必須強制 WHERE company_id = ?
- 支援單一 company_id 全量抽取（備份用）

WP-11-02: Added AttendanceSessionRepository for new attendance domain
WP-11-05C: Added policy retrieval methods
WP-11-07 Phase 3B: Added get_last_break_punch method
"""

import logging
from datetime import datetime
from app.core.config import get_current_time
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
        """創建新的出勤 session
        
        Args:
            company_id: 公司 ID (tenant isolation)
            user_id: 用戶 ID
            punch_in_time: 打卡上班時間
            notes: 備註
        
        Returns:
            AttendanceSession
        """
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
        
        Args:
            company_id: 公司 ID
            user_id: 用戶 ID
        
        Returns:
            AttendanceSession or None
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
        """關閉 session (WP-11-05C: added policy_id and duration)
        
        Args:
            session: AttendanceSession to close
            punch_out_time: 打卡下班時間
            duration_minutes: 工作時長（分鐘）
            policy_id: 適用的政策 ID
        
        Returns:
            Updated AttendanceSession
        """
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
        location_id: Optional[UUID] = None  # WP-11-13: 允許地點 ID
    ) -> AttendancePunch:
        """創建打卡記錄
        
        Args:
            session_id: Session ID
            company_id: 公司 ID (denormalized)
            user_id: 用戶 ID (denormalized)
            punch_type: 打卡類型 (in/out/break_start/break_end)
            punch_time: 打卡時間
            ip_address: IP 地址
            location_lat: 緯度
            location_lng: 經度
            notes: 備註
        
        Returns:
            AttendancePunch
        """
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
            location_id=location_id  # WP-11-13: 記錄匹配的地點
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
        
        Args:
            company_id: 公司 ID
            user_id: 用戶 ID
            limit: 每頁筆數
            offset: 偏移量
            status: 狀態過濾 (optional)
        
        Returns:
            List[AttendanceSession]
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
        """計算用戶的 sessions 總數
        
        Args:
            company_id: 公司 ID
            user_id: 用戶 ID
            status: 狀態過濾 (optional)
        
        Returns:
            int: 總數
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
        
        return query.count()
    
    def get_user_policy(
        self,
        company_id: str,
        user_id: UUID
    ) -> Optional[AttendancePolicy]:
        """獲取用戶的考勤政策 (WP-11-05C)
        
        目前實現：返回公司的預設政策
        未來：支援用戶級別的政策分配
        
        Tenant Isolation: 強制 WHERE company_id = ?
        
        Args:
            company_id: 公司 ID
            user_id: 用戶 ID (目前未使用，預留給未來)
        
        Returns:
            AttendancePolicy or None
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
        """獲取 session 的最後一筆 break punch (WP-11-07 Phase 3B)
        
        Args:
            session_id: Session ID
        
        Returns:
            AttendancePunch or None
        """
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
        """獲取 session 的所有 punch 記錄
        
        Args:
            session_id: Session ID
        
        Returns:
            List of AttendancePunch
        """
        return (
            self.db.query(AttendancePunch)
            .filter(AttendancePunch.session_id == session_id)
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


# ============================================
# WP-11-10: OUT Checkpoint Repository
# ============================================

class OutCheckpointRepository:
    """OUT checkpoint 資料存取層 (WP-11-10)"""
    
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
        """創建 OUT checkpoint
        
        Args:
            company_id: 公司 ID (tenant isolation)
            user_id: 用戶 ID
            device_type: 裝置類型 (mobile|pc)
            punch_time: 打卡時間 (server-set)
            session_id: Session ID (optional)
            gps_lat: 緯度
            gps_lng: 經度
            gps_accuracy_m: GPS 精度 (公尺)
            gps_captured_at: GPS 擷取時間
            gps_provider: GPS 提供者
            client_timezone: 客戶端時區
            client_user_agent: User Agent
            ip_address: IP 地址
            notes: 備註
        
        Returns:
            AttendanceOutCheckpoint
        """
        from app.modules.attendance.models import AttendanceOutCheckpoint
        
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
        
        Args:
            company_id: 公司 ID
            user_id: 用戶 ID
            within_seconds: 時間範圍 (秒)
        
        Returns:
            AttendanceOutCheckpoint or None
        """
        from app.modules.attendance.models import AttendanceOutCheckpoint
        from datetime import timedelta
        
        cutoff_time = get_current_time() - timedelta(seconds=within_seconds)
        
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
        
        Args:
            company_id: 公司 ID
            user_id: 用戶 ID
            limit: 每頁筆數
            offset: 偏移量
            session_id: Session ID 過濾 (optional)
        
        Returns:
            List[AttendanceOutCheckpoint]
        """
        from app.modules.attendance.models import AttendanceOutCheckpoint
        
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
        """計算用戶的 checkpoints 總數
        
        Args:
            company_id: 公司 ID
            user_id: 用戶 ID
            session_id: Session ID 過濾 (optional)
        
        Returns:
            int: 總數
        """
        from app.modules.attendance.models import AttendanceOutCheckpoint
        
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
        """獲取 session 的所有 checkpoints
        
        Args:
            session_id: Session ID
        
        Returns:
            List[AttendanceOutCheckpoint]
        """
        from app.modules.attendance.models import AttendanceOutCheckpoint
        
        return (
            self.db.query(AttendanceOutCheckpoint)
            .filter(AttendanceOutCheckpoint.session_id == session_id)
            .order_by(AttendanceOutCheckpoint.punch_time.asc())
            .all()
        )


def get_out_checkpoint_repository(db: Session) -> OutCheckpointRepository:
    """Factory function for dependency injection"""
    return OutCheckpointRepository(db)
