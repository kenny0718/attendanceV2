"""Audit Log 資料模型

Phase 6C: 稽核紀錄（記錄所有備份匯出/還原操作）
Phase 8: 新增 Retention Policy（保留政策）
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Index, Text, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


class AuditRetentionPolicy(Base):
    """稽核紀錄保留政策模型
    
    用途：
    - 為每個 company_id 設定 audit log 保留天數
    - 支援 purge 功能計算 cutoff date
    
    設計原則：
    1. company_id 為主鍵（每個公司一筆設定）
    2. retention_days 範圍：7 ~ 3650 天
    3. 預設值：365 天（在 Service 層處理）
    """
    
    __tablename__ = "audit_retention_policies"
    
    # 主鍵：公司 ID
    company_id = Column(
        String(255),
        primary_key=True,
        comment="公司 ID"
    )
    
    # 保留天數
    retention_days = Column(
        Integer,
        nullable=False,
        comment="保留天數（7 ~ 3650）"
    )
    
    # 建立時間
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="建立時間（UTC）"
    )
    
    # 更新時間
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新時間（UTC）"
    )
    
    def __repr__(self):
        return (
            f"<AuditRetentionPolicy(company_id={self.company_id}, "
            f"retention_days={self.retention_days})>"
        )


class AuditLog(Base):
    """稽核紀錄模型
    
    用途：
    - 記錄所有備份匯出/還原操作
    - 追蹤誰、何時、對哪家公司、做了什麼、成功/失敗、影響筆數
    
    設計原則：
    1. 主鍵使用 UUID
    2. 包含 company_id（記錄目標公司）
    3. 使用 JSONB 儲存 meta 資料（彈性擴充）
    4. 建立索引支援查詢
    """
    
    __tablename__ = "audit_logs"
    
    # 主鍵：UUID（由 Python 生成）
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="稽核紀錄 ID（UUID）"
    )
    
    # 目標公司（從 X-Company-ID 解析）
    company_id = Column(
        String(255),
        nullable=False,
        index=True,
        comment="目標公司 ID"
    )
    
    # 操作類型
    action = Column(
        String(255),
        nullable=False,
        comment="操作類型（例如：backup.export, backup.restore）"
    )
    
    # 操作狀態
    status = Column(
        String(50),
        nullable=False,
        comment="操作狀態（success / fail）"
    )
    
    # 執行者
    actor = Column(
        String(255),
        nullable=False,
        comment="執行者（從 X-Actor / X-User header 或 fallback 為 system）"
    )
    
    # 請求 ID（可選）
    request_id = Column(
        String(255),
        nullable=True,
        comment="請求 ID（從 X-Request-ID header）"
    )
    
    # IP 位址
    ip = Column(
        String(255),
        nullable=True,
        comment="來源 IP 位址"
    )
    
    # User Agent
    user_agent = Column(
        String(500),
        nullable=True,
        comment="User Agent"
    )
    
    # Meta 資料（JSONB）
    meta = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="操作 meta 資料（例如：tables, counts, clear_existing, error_code）"
    )
    
    # 錯誤訊息（失敗時記錄）
    error = Column(
        Text,
        nullable=True,
        comment="錯誤訊息（失敗時記錄，最多 2000 字）"
    )
    
    # 建立時間
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="建立時間（UTC）"
    )
    
    # 索引：支援查詢
    __table_args__ = (
        Index("idx_audit_logs_company_created", "company_id", "created_at"),
        Index("idx_audit_logs_action_created", "action", "created_at"),
    )
    
    def __repr__(self):
        return (
            f"<AuditLog(id={self.id}, company_id={self.company_id}, "
            f"action={self.action}, status={self.status}, actor={self.actor})>"
        )

