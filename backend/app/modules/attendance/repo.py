"""Attendance Repository（資料存取層）

Phase 4: 實作資料庫 CRUD 操作
"""

import logging
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.modules.attendance.models import AttendanceRecord

logger = logging.getLogger(__name__)


class AttendanceRepository:
    """考勤資料存取層
    
    Phase 4 實作：
    - create_attendance_record(company_id, ...)
    - get_attendance_record(company_id, record_id)
    - approve_attendance_record(company_id, record_id, approved_by)
    - 所有查詢必須強制 company_id 篩選（Tenant Isolation P0）
    """
    
    def __init__(self, db: Session):
        """初始化 Repository
        
        Args:
            db: SQLAlchemy Session
        """
        self.db = db
    
    def create_attendance_record(
        self,
        company_id: str,
        employee_id: str
    ) -> AttendanceRecord:
        """建立考勤記錄
        
        Args:
            company_id: 公司 ID（Tenant Isolation）
            employee_id: 員工 ID
        
        Returns:
            建立的 AttendanceRecord
        """
        record = AttendanceRecord(
            id=uuid4(),
            company_id=company_id,
            employee_id=employee_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        
        logger.info(f"建立考勤記錄: id={record.id}, company_id={company_id}, employee_id={employee_id}")
        return record
    
    def get_attendance_record(
        self,
        company_id: str,
        record_id: UUID
    ) -> AttendanceRecord | None:
        """取得考勤記錄
        
        Tenant Isolation P0: 必須同時符合 company_id 和 record_id
        
        Args:
            company_id: 公司 ID
            record_id: 記錄 ID
        
        Returns:
            AttendanceRecord 或 None（若不存在或不屬於該公司）
        """
        return self.db.query(AttendanceRecord).filter(
            and_(
                AttendanceRecord.id == record_id,
                AttendanceRecord.company_id == company_id
            )
        ).first()
    
    def approve_attendance_record(
        self,
        company_id: str,
        record_id: UUID,
        approved_by: str | None = None
    ) -> AttendanceRecord | None:
        """核准考勤記錄
        
        Tenant Isolation P0: 只能核准屬於該公司的記錄
        
        Args:
            company_id: 公司 ID
            record_id: 記錄 ID
            approved_by: 核准人 ID（選填）
        
        Returns:
            更新後的 AttendanceRecord 或 None（若不存在或不屬於該公司）
        """
        record = self.get_attendance_record(company_id, record_id)
        
        if record is None:
            logger.warning(f"核准失敗: 記錄不存在或不屬於該公司 (company_id={company_id}, record_id={record_id})")
            return None
        
        # 更新核准資訊
        record.approved_by = approved_by
        record.approved_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(record)
        
        logger.info(f"核准考勤記錄: id={record_id}, company_id={company_id}, approved_by={approved_by}")
        return record


def get_attendance_repository(db: Session) -> AttendanceRepository:
    """取得 AttendanceRepository 實例
    
    Args:
        db: SQLAlchemy Session
    
    Returns:
        AttendanceRepository 實例
    """
    return AttendanceRepository(db)
