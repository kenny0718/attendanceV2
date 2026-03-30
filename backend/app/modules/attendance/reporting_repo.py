"""Reporting Repository（Reporting 資料存取層）

Phase R1: Extracted from repo.py as part of attendance module boundary strengthening.

WP-11-06 Step 1: Sessions Reporting Repository

Query safety rules:
- 所有過濾使用 punch_in_time（禁止 punch_out_time 過濾）
- 所有 datetime 參數必須為 UTC timezone-aware（由 API 層保證）
- 必須強制 WHERE company_id = ?（tenant isolation）
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.modules.attendance.models import AttendanceSession


# ============================================
# WP-11-06 Step 1: Sessions Reporting Repository
# ============================================

class ReportingRepository:
    """Reporting 資料存取層 (WP-11-06 Step 1)

    僅供 reporting endpoints 使用。
    不修改現有 AttendanceSessionRepository。

    Query safety rules:
    - 所有過濾使用 punch_in_time（禁止 punch_out_time 過濾）
    - 所有 datetime 參數必須為 UTC timezone-aware（由 API 層保證）
    - 必須強制 WHERE company_id = ?（tenant isolation）
    """

    def __init__(self, db: Session):
        self.db = db

    def get_sessions_for_reporting(
        self,
        company_id: str,
        user_id: Optional[UUID] = None,
        start_utc: Optional[datetime] = None,
        end_utc: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AttendanceSession]:
        """查詢 sessions（reporting 用途）

        Tenant Isolation: 強制 WHERE company_id = ?
        Date filter: 僅使用 punch_in_time（不使用 punch_out_time）
        索引命中: idx_sessions_company_punch_in (company_id, punch_in_time)
        """
        query = self.db.query(AttendanceSession).filter(
            AttendanceSession.company_id == company_id
        )

        if user_id is not None:
            query = query.filter(AttendanceSession.user_id == user_id)

        if start_utc is not None:
            query = query.filter(AttendanceSession.punch_in_time >= start_utc)

        if end_utc is not None:
            query = query.filter(AttendanceSession.punch_in_time < end_utc)

        if status is not None:
            query = query.filter(AttendanceSession.status == status)

        return (
            query
            .order_by(AttendanceSession.punch_in_time.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def count_sessions_for_reporting(
        self,
        company_id: str,
        user_id: Optional[UUID] = None,
        start_utc: Optional[datetime] = None,
        end_utc: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> int:
        """計算 sessions 總數（reporting 用途，供分頁 total 欄位使用）"""
        query = self.db.query(AttendanceSession).filter(
            AttendanceSession.company_id == company_id
        )

        if user_id is not None:
            query = query.filter(AttendanceSession.user_id == user_id)

        if start_utc is not None:
            query = query.filter(AttendanceSession.punch_in_time >= start_utc)

        if end_utc is not None:
            query = query.filter(AttendanceSession.punch_in_time < end_utc)

        if status is not None:
            query = query.filter(AttendanceSession.status == status)

        return query.count()

    def get_user_summary_sessions(
        self,
        company_id: str,
        user_id: UUID,
        start_utc: Optional[datetime] = None,
        end_utc: Optional[datetime] = None,
    ) -> List[AttendanceSession]:
        """查詢用戶所有 sessions（user-summary 用途，WP-11-06 Step 2）

        user_id 為必填（不同於 get_sessions_for_reporting 的 Optional）。
        不分頁（全量拉取），在應用層聚合。
        過濾僅使用 punch_in_time（禁止 punch_out_time）。
        索引命中: idx_sessions_company_punch_in (company_id, punch_in_time)
        """
        query = self.db.query(AttendanceSession).filter(
            and_(
                AttendanceSession.company_id == company_id,
                AttendanceSession.user_id == user_id,
            )
        )

        if start_utc is not None:
            query = query.filter(AttendanceSession.punch_in_time >= start_utc)

        if end_utc is not None:
            query = query.filter(AttendanceSession.punch_in_time < end_utc)

        return query.order_by(AttendanceSession.punch_in_time.asc()).all()

    def get_company_summary_sessions(
        self,
        company_id: str,
        start_utc: Optional[datetime] = None,
        end_utc: Optional[datetime] = None,
    ) -> List[AttendanceSession]:
        """查詢公司所有 sessions（company-summary 用途，WP-11-06 Step 3）

        不過濾 user_id（查全公司所有用戶）。
        不分頁（全量拉取），在應用層聚合。
        過濾僅使用 punch_in_time（禁止 punch_out_time）。
        索引命中: idx_sessions_company_punch_in (company_id, punch_in_time)
        """
        query = self.db.query(AttendanceSession).filter(
            AttendanceSession.company_id == company_id
        )

        if start_utc is not None:
            query = query.filter(AttendanceSession.punch_in_time >= start_utc)

        if end_utc is not None:
            query = query.filter(AttendanceSession.punch_in_time < end_utc)

        return query.order_by(AttendanceSession.punch_in_time.asc()).all()


def get_reporting_repository(db: Session) -> ReportingRepository:
    """Factory function for ReportingRepository (WP-11-06)"""
    return ReportingRepository(db)
