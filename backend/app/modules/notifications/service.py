"""Notifications 服務層"""

import logging
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.modules.notifications.repo import NotificationRepository

logger = logging.getLogger(__name__)


class NotificationService:
    """通知服務"""
    
    def __init__(self, repo: NotificationRepository):
        """初始化服務
        
        Args:
            repo: NotificationRepository 實例
        """
        self.repo = repo
    
    def create_notification(
        self,
        company_id: str,
        event_type: str,
        event_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """建立通知記錄
        
        Args:
            company_id: 公司 ID（Source of Truth）
            event_type: 事件類型
            event_payload: 完整事件 payload
        
        Returns:
            Dict: 通知記錄資訊
        """
        notification = self.repo.create_notification(
            company_id=company_id,
            event_type=event_type,
            event_payload=event_payload
        )
        
        return {
            "id": str(notification.id),
            "company_id": notification.company_id,
            "event_type": notification.event_type,
            "event_payload": notification.event_payload,
            "created_at": notification.created_at.isoformat() + "Z"
        }
    
    def get_notifications(
        self,
        company_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """查詢通知記錄（分頁）
        
        Tenant Isolation (P0):
        - 只回傳指定 company_id 的記錄
        
        Args:
            company_id: 公司 ID
            limit: 每頁筆數
            offset: 偏移量
        
        Returns:
            Dict: 包含通知列表與分頁資訊
        """
        notifications = self.repo.get_notifications(
            company_id=company_id,
            limit=limit,
            offset=offset
        )
        
        total = self.repo.count_notifications(company_id)
        
        return {
            "notifications": [
                {
                    "id": str(n.id),
                    "company_id": n.company_id,
                    "event_type": n.event_type,
                    "event_payload": n.event_payload,
                    "created_at": n.created_at.isoformat() + "Z"
                }
                for n in notifications
            ],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }


def get_notification_service(repo: NotificationRepository) -> NotificationService:
    """取得 NotificationService 實例（FastAPI Dependency）
    
    Args:
        repo: NotificationRepository 實例
    
    Returns:
        NotificationService: Service 實例
    """
    return NotificationService(repo)
