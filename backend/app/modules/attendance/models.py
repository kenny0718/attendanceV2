"""Attendance 資料模型

Phase 4: 定義 AttendanceRecord SQLAlchemy model
"""

from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.core.database import Base


class AttendanceRecord(Base):
    """考勤記錄模型
    
    設計原則（SA_MODULE_SPEC v1.7 第 18 條）：
    1. 主鍵使用 UUID（避免單一租戶還原時 ID 衝突）
    2. 必須包含 company_id（Tenant Isolation P0）
    3. 為 company_id 建立索引（支援高效匯出與查詢）
    """
    
    __tablename__ = "attendance_records"
    
    # 主鍵（UUID）
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, comment="考勤記錄 ID（UUID）")
    
    # Tenant Isolation 必要欄位
    company_id = Column(String(255), nullable=False, index=True, comment="公司 ID（Tenant Isolation）")
    
    # 業務欄位
    employee_id = Column(String(255), nullable=False, comment="員工 ID")
    approved_by = Column(String(255), nullable=True, comment="核准人 ID")
    approved_at = Column(DateTime, nullable=True, comment="核准時間（UTC）")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="建立時間（UTC）")
    
    # 索引（支援單一租戶全量抽取與高效查詢）
    __table_args__ = (
        Index('idx_attendance_company_id', 'company_id'),
        Index('idx_attendance_company_created', 'company_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AttendanceRecord(id={self.id}, company_id={self.company_id}, employee_id={self.employee_id})>"
