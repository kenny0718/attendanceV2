"""Attendance 服務層"""

import logging
from datetime import datetime
from typing import Dict, Any
from uuid import uuid4

from app.core.event_bus import get_event_bus

logger = logging.getLogger(__name__)


class AttendanceService:
    """考勤服務"""
    
    def __init__(self):
        """初始化服務"""
        self.event_bus = get_event_bus()
    
    def mock_create_attendance(self) -> str:
        """建立假的考勤記錄（用於測試）
        
        Returns:
            attendance_record_id (UUID string)
        """
        attendance_record_id = str(uuid4())
        logger.info(f"建立假考勤記錄: {attendance_record_id}")
        return attendance_record_id
    
    def approve_attendance(
        self,
        attendance_record_id: str,
        company_id: str,
        employee_id: str,
        approved_by: str | None = None
    ) -> Dict[str, Any]:
        """核准考勤記錄
        
        Args:
            attendance_record_id: 考勤記錄 ID
            company_id: 公司 ID（必填，多租戶隔離用）
            employee_id: 員工 ID
            approved_by: 核准人 ID（選填）
        
        Returns:
            操作結果
        """
        # 組裝 payload
        payload = {
            "company_id": company_id,
            "employee_id": employee_id,
            "attendance_record_id": attendance_record_id,
            "approved_at": datetime.utcnow().isoformat() + "Z",
        }
        
        # 如果有提供核准人，加入 payload
        if approved_by:
            payload["approved_by"] = approved_by
        
        # 發出事件
        logger.info(f"準備發出事件 attendance.approved，payload: {payload}")
        self.event_bus.emit("attendance.approved", payload)
        logger.info(f"事件 attendance.approved 已發出")
        
        return {"ok": True, "payload": payload}


# 全域服務實例
_service_instance: AttendanceService | None = None


def get_attendance_service() -> AttendanceService:
    """取得 AttendanceService 單例
    
    Returns:
        AttendanceService 實例
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = AttendanceService()
    return _service_instance
