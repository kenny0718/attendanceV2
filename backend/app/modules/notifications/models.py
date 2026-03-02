"""Notifications 資料模型"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Index, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base, JSONB


class Notification(Base):
    """通知記錄（Tenant Data）
    
    設計原則：
    1. 主鍵使用 UUID（Python uuid4()），避免單一租戶還原時 ID 衝突
    2. 必須包含 company_id（Tenant Isolation P0）
    3. 為 company_id 建立索引，支援高效匯出
    4. event_payload 使用 JSONB，保留完整事件資料供稽核
    """
    
    __tablename__ = "notifications"
    
    # 主鍵：UUID（由 Python 生成）
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="通知記錄 ID（UUID）"
    )
    
    # Tenant Isolation（P0）
    company_id = Column(
        String(255),
        nullable=False,
        index=True,
        comment="公司 ID（Tenant Isolation）"
    )
    
    # 事件資訊
    event_type = Column(
        String(255),
        nullable=False,
        comment="事件類型（例如：attendance.approved）"
    )
    
    event_payload = Column(
        JSONB,
        nullable=False,
        comment="完整事件 payload（JSONB 格式，供稽核）"
    )
    
    # 時間戳記
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="建立時間（UTC）"
    )
    
    # 索引：支援單一租戶全量抽取
    __table_args__ = (
        Index("idx_notifications_company_id", "company_id"),
        Index("idx_notifications_company_created", "company_id", "created_at"),
    )
    
    def __repr__(self):
        return f"<Notification(id={self.id}, company_id={self.company_id}, event_type={self.event_type})>"
