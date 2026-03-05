"""Notifications Repository（資料存取層）

Tenant Isolation (P0)：
- 所有查詢必須強制 WHERE company_id = ?
- 支援單一 company_id 全量抽取（備份用）
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.modules.notifications.models import Notification

logger = logging.getLogger(__name__)


class NotificationRepository:
    """通知記錄資料存取層"""
    
    def __init__(self, db: Session):
        """初始化 Repository
        
        Args:
            db: SQLAlchemy Session
        """
        self.db = db
    
    def create_notification(
        self,
        company_id: str,
        event_type: str,
        event_payload: Dict[str, Any]
    ) -> Notification:
        """建立通知記錄
        
        Tenant Isolation (P0):
        - company_id 由呼叫者提供（已從 tenant_context 注入）
        - 不信任 event_payload 內的 company_id
        
        Args:
            company_id: 公司 ID（Source of Truth）
            event_type: 事件類型
            event_payload: 完整事件 payload
        
        Returns:
            Notification: 建立的通知記錄
        """
        notification = Notification(
            company_id=company_id,
            event_type=event_type,
            event_payload=event_payload
        )
        
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        logger.info(
            f"建立通知記錄: id={notification.id}, "
            f"company_id={company_id}, event_type={event_type}"
        )
        
        return notification
    
    def get_notifications(
        self,
        company_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """查詢通知記錄（分頁）
        
        Tenant Isolation (P0):
        - 強制 WHERE company_id = ?
        
        Args:
            company_id: 公司 ID
            limit: 每頁筆數
            offset: 偏移量
        
        Returns:
            List[Notification]: 通知記錄列表
        """
        notifications = (
            self.db.query(Notification)
            .filter(Notification.company_id == company_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        
        logger.debug(
            f"查詢通知記錄: company_id={company_id}, "
            f"limit={limit}, offset={offset}, count={len(notifications)}"
        )
        
        return notifications
    
    def get_notification_by_id(
        self,
        company_id: str,
        notification_id: UUID
    ) -> Optional[Notification]:
        """查詢單一通知記錄
        
        Tenant Isolation (P0):
        - 強制 WHERE company_id = ? AND id = ?
        
        Args:
            company_id: 公司 ID
            notification_id: 通知記錄 ID
        
        Returns:
            Optional[Notification]: 通知記錄（若不存在或不屬於該公司則回 None）
        """
        notification = (
            self.db.query(Notification)
            .filter(
                Notification.company_id == company_id,
                Notification.id == notification_id
            )
            .first()
        )
        
        return notification
    
    def get_all_notifications_for_company(
        self,
        company_id: str
    ) -> List[Notification]:
        """取得指定公司的所有通知記錄（全量抽取，備份用）
        
        Tenant Isolation (P0):
        - 強制 WHERE company_id = ?
        - 不分頁，全量回傳
        
        用途：
        - 單一租戶備份
        - 資料匯出
        
        Args:
            company_id: 公司 ID
        
        Returns:
            List[Notification]: 該公司的所有通知記錄
        """
        notifications = (
            self.db.query(Notification)
            .filter(Notification.company_id == company_id)
            .order_by(Notification.created_at.asc())
            .all()
        )
        
        logger.info(
            f"全量抽取通知記錄: company_id={company_id}, "
            f"total_count={len(notifications)}"
        )
        
        return notifications
    
    def count_notifications(
        self,
        company_id: str
    ) -> int:
        """計算通知記錄數量
        
        Tenant Isolation (P0):
        - 強制 WHERE company_id = ?
        
        Args:
            company_id: 公司 ID
        
        Returns:
            int: 通知記錄數量
        """
        count = (
            self.db.query(Notification)
            .filter(Notification.company_id == company_id)
            .count()
        )
        
        return count


def get_notification_repository(db: Session) -> NotificationRepository:
    """取得 NotificationRepository 實例（FastAPI Dependency）
    
    Args:
        db: SQLAlchemy Session
    
    Returns:
        NotificationRepository: Repository 實例
    """
    return NotificationRepository(db)
