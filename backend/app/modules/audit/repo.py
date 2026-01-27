"""Audit Log Repository

負責 audit_logs 表的資料存取操作。
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditLog

logger = logging.getLogger(__name__)


class AuditLogRepository:
    """稽核紀錄 Repository"""
    
    def __init__(self, db: Session):
        """初始化 Repository
        
        Args:
            db: SQLAlchemy Session
        """
        self.db = db
    
    def create_log(
        self,
        company_id: str,
        action: str,
        status: str,
        actor: str,
        request_id: Optional[str] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> AuditLog:
        """建立稽核紀錄
        
        Args:
            company_id: 目標公司 ID
            action: 操作類型（例如：backup.export, backup.restore）
            status: 操作狀態（success / fail）
            actor: 執行者
            request_id: 請求 ID（可選）
            ip: 來源 IP（可選）
            user_agent: User Agent（可選）
            meta: Meta 資料（可選）
            error: 錯誤訊息（可選，失敗時記錄，最多 2000 字）
        
        Returns:
            AuditLog: 建立的稽核紀錄
        """
        # 截斷錯誤訊息（最多 2000 字）
        if error and len(error) > 2000:
            error = error[:2000] + "... (truncated)"
        
        # 建立稽核紀錄
        audit_log = AuditLog(
            company_id=company_id,
            action=action,
            status=status,
            actor=actor,
            request_id=request_id,
            ip=ip,
            user_agent=user_agent,
            meta=meta or {},
            error=error
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        logger.info(
            f"建立稽核紀錄: id={audit_log.id}, company_id={company_id}, "
            f"action={action}, status={status}, actor={actor}"
        )
        
        return audit_log


def get_audit_log_repository(db: Session) -> AuditLogRepository:
    """取得 AuditLogRepository 實例（FastAPI Dependency）
    
    Args:
        db: SQLAlchemy Session
    
    Returns:
        AuditLogRepository: Repository 實例
    """
    return AuditLogRepository(db)

