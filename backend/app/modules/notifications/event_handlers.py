"""Notifications 事件處理器

訂閱事件：
- attendance.approved

Tenant Isolation (P0)：
- company_id 從 event payload 取得（已由 attendance 從 tenant_context 注入）
- Fail-fast：payload 必須包含 company_id，否則拒絕處理
"""

import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.modules.notifications.repo import NotificationRepository

logger = logging.getLogger(__name__)


def handle_attendance_approved(payload: Dict[str, Any]) -> None:
    """處理 attendance.approved 事件
    
    Tenant Isolation (P0) - 方案 A + Fail-fast：
    1. 從 payload 取得 company_id（已由 attendance 從 tenant_context 注入）
    2. Fail-fast：若 payload 缺少 company_id 或為空，拒絕處理
    3. 使用 payload.company_id 作為 Source of Truth 寫入 DB
    
    Args:
        payload: 事件 payload，必須包含：
            - company_id (str): 公司 ID（必填）
            - employee_id (str): 員工 ID
            - attendance_record_id (str): 考勤記錄 ID
            - approved_at (str): 核准時間
            - approved_by (str, optional): 核准人 ID
    
    Raises:
        ValueError: 若 payload 缺少 company_id 或為空
    """
    # Fail-fast：檢查 company_id
    company_id = payload.get("company_id")
    if not company_id or not isinstance(company_id, str) or not company_id.strip():
        error_msg = (
            f"事件處理失敗: attendance.approved payload 缺少有效的 company_id. "
            f"payload={payload}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    company_id = company_id.strip()
    
    # 建立資料庫 Session
    db = SessionLocal()
    try:
        repo = NotificationRepository(db)
        
        # 寫入通知記錄（使用 payload.company_id 作為 Source of Truth）
        notification = repo.create_notification(
            company_id=company_id,
            event_type="attendance.approved",
            event_payload=payload
        )
        
        logger.info(
            f"[Event Handler] 處理 attendance.approved 事件成功: "
            f"notification_id={notification.id}, company_id={company_id}, "
            f"attendance_record_id={payload.get('attendance_record_id')}"
        )
        
    except Exception as e:
        logger.error(
            f"[Event Handler] 處理 attendance.approved 事件失敗: {e}",
            exc_info=True
        )
        db.rollback()
        raise
    finally:
        db.close()


def register_event_handlers() -> None:
    """註冊所有事件處理器
    
    應在應用啟動時呼叫（main.py 的 startup event）
    """
    from app.core.event_bus import get_event_bus
    
    event_bus = get_event_bus()
    
    # 訂閱 attendance.approved 事件
    event_bus.subscribe("attendance.approved", handle_attendance_approved)
    
    logger.info("Notifications 事件處理器已註冊: attendance.approved")
