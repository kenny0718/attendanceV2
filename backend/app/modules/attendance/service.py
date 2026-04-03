"""Attendance 服務層

Phase 4: 改為真正寫 DB
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.event_bus import get_event_bus
from app.modules.attendance.repo import get_attendance_repository
from app.modules.attendance.punch_close_domain import build_policy_evaluation, PolicyEvalPayload
from app.modules.attendance.policy_missing_segment import (
    MissingSegmentInput,
    NormalizedSegment,
    evaluate_missing_segment_dry_run,
)

logger = logging.getLogger(__name__)


class AttendanceService:
    """考勤服務"""
    
    def __init__(self, db: Session):
        """初始化服務
        
        Args:
            db: SQLAlchemy Session
        """
        self.db = db
        self.repo = get_attendance_repository(db)
        self.event_bus = get_event_bus()
        self._last_internal_missing_segment_dry_run: Optional[Dict[str, Any]] = None
    
    def mock_create_attendance(self, company_id: str) -> str:
        """建立考勤記錄（Phase 4: 真正寫 DB）
        
        Tenant Isolation P0:
        - company_id 由 tenant_context 注入
        - 不信任 request body 的 company_id
        
        Args:
            company_id: 公司 ID（由 tenant context 注入）
        
        Returns:
            attendance_record_id (UUID string)
        """
        # Phase 4: 真正寫入資料庫
        record = self.repo.create_attendance_record(
            company_id=company_id,
            employee_id="emp-mock-001"  # Phase 4 暫用固定值，Phase 5+ 從 request 取得
        )
        
        logger.info(f"建立考勤記錄: {record.id}, company_id: {company_id}")
        return str(record.id)
    
    def approve_attendance(
        self,
        attendance_record_id: str,
        company_id: str,
        employee_id: str,
        approved_by: str | None = None
    ) -> Dict[str, Any]:
        """核准考勤記錄（Phase 4: 真正寫 DB）
        
        Tenant Isolation P0:
        - 只能核准屬於該公司的記錄
        - 若記錄不存在或不屬於該公司 → 404
        
        Args:
            attendance_record_id: 考勤記錄 ID
            company_id: 公司 ID（必填，多租戶隔離用）
            employee_id: 員工 ID
            approved_by: 核准人 ID（選填）
        
        Returns:
            操作結果
        
        Raises:
            HTTPException: 404 若記錄不存在或不屬於該公司
        """
        # Phase 4: 真正更新資料庫
        try:
            record_id = UUID(attendance_record_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Invalid attendance_record_id format"}
            )
        
        record = self.repo.approve_attendance_record(
            company_id=company_id,
            record_id=record_id,
            approved_by=approved_by
        )
        
        # Tenant Isolation P0: 若記錄不存在或不屬於該公司 → 404
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Attendance record not found or does not belong to this company"}
            )
        
        # 組裝 payload
        payload = {
            "company_id": company_id,
            "employee_id": employee_id,
            "attendance_record_id": attendance_record_id,
            "approved_at": record.approved_at.isoformat() + "Z",
        }
        
        # 如果有提供核准人，加入 payload
        if approved_by:
            payload["approved_by"] = approved_by
        
        # 發出事件
        logger.info(f"準備發出事件 attendance.approved，payload: {payload}")
        self.event_bus.emit("attendance.approved", payload)
        logger.info(f"事件 attendance.approved 已發出")
        
        return {"ok": True, "payload": payload}

    def _to_segment(self, start_at: datetime, end_at: datetime) -> Optional[NormalizedSegment]:
        if end_at <= start_at:
            return None
        return NormalizedSegment(start_at=start_at, end_at=end_at)

    def _collect_session_punches_for_dry_run(
        self,
        repo,
        company_id: str,
        user_id: UUID,
        session_id: UUID,
    ) -> list:
        if hasattr(repo, "get_punches_by_company_user_and_session_ids"):
            punches = repo.get_punches_by_company_user_and_session_ids(
                company_id=company_id,
                user_id=user_id,
                session_ids=[session_id],
            )
            if isinstance(punches, list):
                return punches

        if hasattr(repo, "get_session_punches"):
            punches = repo.get_session_punches(session_id)
            if isinstance(punches, list):
                return punches

        return []

    def _build_actual_segments_from_punches(
        self,
        punches: list,
        fallback_end: datetime,
    ) -> list[NormalizedSegment]:
        actual: list[NormalizedSegment] = []
        sorted_punches = sorted(
            punches,
            key=lambda p: getattr(p, "punch_time", datetime.min.replace(tzinfo=fallback_end.tzinfo)),
        )

        current_start: Optional[datetime] = None
        for punch in sorted_punches:
            punch_type = getattr(punch, "punch_type", None)
            punch_time = getattr(punch, "punch_time", None)
            if punch_time is None:
                continue

            if punch_type == "in":
                current_start = punch_time
            elif punch_type == "break_start":
                if current_start is not None:
                    segment = self._to_segment(current_start, punch_time)
                    if segment is not None:
                        actual.append(segment)
                    current_start = None
            elif punch_type == "break_end":
                if current_start is None:
                    current_start = punch_time
            elif punch_type == "out":
                if current_start is not None:
                    segment = self._to_segment(current_start, punch_time)
                    if segment is not None:
                        actual.append(segment)
                    current_start = None

        if current_start is not None:
            segment = self._to_segment(current_start, fallback_end)
            if segment is not None:
                actual.append(segment)

        return actual

    def _build_missing_segment_input(
        self,
        session,
        repo,
        company_id: str,
        user_id: UUID,
        punch_out_time: datetime,
    ) -> MissingSegmentInput:
        expected_segments: list[NormalizedSegment] = []
        expected = self._to_segment(session.punch_in_time, punch_out_time)
        if expected is not None:
            expected_segments.append(expected)

        session_punches = self._collect_session_punches_for_dry_run(
            repo=repo,
            company_id=company_id,
            user_id=user_id,
            session_id=session.id,
        )
        actual_segments = self._build_actual_segments_from_punches(
            punches=session_punches,
            fallback_end=punch_out_time,
        )

        evidence_sufficient = bool(expected_segments) and bool(actual_segments)

        return MissingSegmentInput(
            expected_segments=expected_segments,
            actual_segments=actual_segments,
            exception_segments=[],
            evidence_sufficient=evidence_sufficient,
            boundary_tolerance_seconds=0,
        )

    def build_punch_out_policy_evaluation(
        self,
        session,
        repo,
        company_id: str,
        user_id: UUID,
        punch_out_time: datetime,
        gross_minutes: int,
    ) -> PolicyEvalPayload:
        """Punch-out close flow orchestration entry with internal dry-run hook."""
        missing_input = self._build_missing_segment_input(
            session=session,
            repo=repo,
            company_id=company_id,
            user_id=user_id,
            punch_out_time=punch_out_time,
        )
        missing_result = evaluate_missing_segment_dry_run(missing_input)

        self._last_internal_missing_segment_dry_run = {
            "input": missing_input,
            "result": missing_result,
            "source": {
                "expected_segments_count": len(missing_input.expected_segments),
                "actual_segments_count": len(missing_input.actual_segments),
                "exception_segments_count": len(missing_input.exception_segments),
            },
        }

        policy_eval = build_policy_evaluation(
            session=session,
            repo=repo,
            company_id=company_id,
            user_id=user_id,
            punch_out_time=punch_out_time,
            gross_minutes=gross_minutes,
        )

        return policy_eval


def get_attendance_service(db: Session) -> AttendanceService:
    """取得 AttendanceService 實例
    
    Args:
        db: SQLAlchemy Session
    
    Returns:
        AttendanceService 實例
    """
    return AttendanceService(db)
