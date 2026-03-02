"""Attendance Repository（資料存取層）

Tenant Isolation (P0)：
- 所有查詢必須強制 WHERE company_id = ?
- 支援單一 company_id 全量抽取（備份用）
- Phase 9: 加入 tenant 存在驗證
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.modules.attendance.models import AttendanceRecord
from app.modules.tenants.repo import TenantRepository

logger = logging.getLogger(__name__)


class AttendanceRepository:
    """考勤記錄資料存取層"""
    
    def __init__(self, db: Session):
        """初始化 Repository
        
        Args:
            db: SQLAlchemy Session
        """
        self.db = db
        self.model = AttendanceRecord
        self.tenant_repo = TenantRepository(db)
    
    def create_attendance_record(
        self,
        company_id: str,
        employee_id: str,
        approved_by: Optional[str] = None,
        approved_at: Optional[str] = None
    ) -> AttendanceRecord:
        """建立考勤記錄
        
        Tenant Isolation (P0)：
        - company_id 由呼叫者提供（已從 tenant_context 注入）
        - Phase 9: 驗證 tenant 是否存在
        
        Args:
            company_id: 公司 ID（Source of Truth）
            employee_id: 員工 ID
            approved_by: 核准人 ID（可選）
            approved_at: 核准時間（可選）
        
        Returns:
            AttendanceRecord: 建立的考勤記錄
        
        Raises:
            HTTPException: 404 if tenant does not exist
        """
        # Phase 9: Validate tenant exists
        if not self.tenant_repo.exists(company_id):
            logger.warning(f"Tenant validation failed: company_id={company_id} does not exist")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"Tenant {company_id} does not exist"}
            )
        
        record = AttendanceRecord(
            company_id=company_id,
            employee_id=employee_id,
            approved_by=approved_by,
            approved_at=approved_at
        )
        
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        
        logger.info(
            f"建立考勤記錄: id={record.id}, "
            f"company_id={company_id}, employee_id={employee_id}"
        )
        
        return record
    
    def approve_attendance_record(
        self,
        company_id: str,
        record_id: UUID,
        approved_by: Optional[str] = None
    ) -> Optional[AttendanceRecord]:
        """核准考勤記錄
        
        Tenant Isolation (P0):
        - 只能核准屬於該公司的記錄
        - 若記錄不存在或不屬於該公司 → 返回 None
        
        Args:
            company_id: 公司 ID
            record_id: 考勤記錄 ID
            approved_by: 核准人 ID（可選）
        
        Returns:
            AttendanceRecord or None if not found
        """
        # Query with tenant isolation
        record = (
            self.db.query(AttendanceRecord)
            .filter(
                AttendanceRecord.id == record_id,
                AttendanceRecord.company_id == company_id
            )
            .first()
        )
        
        if not record:
            logger.warning(
                f"Approve failed: record {record_id} not found or "
                f"does not belong to company {company_id}"
            )
            return None
        
        # Update approval fields
        record.approved_by = approved_by
        record.approved_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(record)
        
        logger.info(
            f"核准考勤記錄: id={record_id}, "
            f"company_id={company_id}, approved_by={approved_by}"
        )
        
        return record
    
    def get_attendance_records(
        self,
        company_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[AttendanceRecord]:
        """查詢考勤記錄（分頁）
        
        Tenant Isolation (P0):
        - 強制 WHERE company_id = ?
        
        Args:
            company_id: 公司 ID
            limit: 每頁筆數
            offset: 偏移量
        
        Returns:
            List[AttendanceRecord]: 考勤記錄列表
        """
        records = (
            self.db.query(AttendanceRecord)
            .filter(AttendanceRecord.company_id == company_id)
            .order_by(AttendanceRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        
        logger.debug(
            f"查詢考勤記錄: company_id={company_id}, "
            f"limit={limit}, offset={offset}, count={len(records)}"
        )
        
        return records


def get_attendance_repository(db: Session) -> AttendanceRepository:
    """取得 AttendanceRepository 實例（FastAPI Dependency）
    
    Args:
        db: SQLAlchemy Session
    
    Returns:
        AttendanceRepository: Repository 實例
    """
    return AttendanceRepository(db)
