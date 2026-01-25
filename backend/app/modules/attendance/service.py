"""Attendance 服務層

Phase 4: 改為真正寫 DB
"""

import logging
from datetime import datetime
from typing import Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.event_bus import get_event_bus
from app.modules.attendance.repo import get_attendance_repository

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


def get_attendance_service(db: Session) -> AttendanceService:
    """取得 AttendanceService 實例
    
    Args:
        db: SQLAlchemy Session
    
    Returns:
        AttendanceService 實例
    """
    return AttendanceService(db)
