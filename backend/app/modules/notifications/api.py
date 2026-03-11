"""Notifications API 路由"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.scope import Actor
from app.core.dependencies import get_actor_with_company
from app.modules.notifications.repo import get_notification_repository
from app.modules.notifications.service import get_notification_service

logger = logging.getLogger(__name__)

# 建立路由
router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    """單一通知記錄回應"""
    id: str = Field(..., description="通知記錄 ID（UUID）")
    company_id: str = Field(..., description="公司 ID")
    event_type: str = Field(..., description="事件類型")
    event_payload: Dict[str, Any] = Field(..., description="完整事件 payload")
    created_at: str = Field(..., description="建立時間（ISO8601 UTC）")


class NotificationListResponse(BaseModel):
    """通知記錄列表回應"""
    notifications: list[NotificationResponse] = Field(..., description="通知記錄列表")
    pagination: Dict[str, int] = Field(..., description="分頁資訊")


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    limit: int = Query(50, ge=1, le=100, description="每頁筆數"),
    offset: int = Query(0, ge=0, description="偏移量"),
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    """查詢通知記錄（分頁）
    
    Tenant Isolation (P0):
    - company_id 從 JWT Actor 強制注入（actor.active_company_id）
    - 只回傳該公司的通知記錄
    - 缺少有效 JWT 公司範圍 → 403 Forbidden
    
    Args:
        limit: 每頁筆數（1-100）
        offset: 偏移量
        actor: 已驗證的操作者（含 active_company_id）
        db: 資料庫 Session
    
    Returns:
        NotificationListResponse: 通知記錄列表與分頁資訊
    """
    company_id = actor.active_company_id

    repo = get_notification_repository(db)
    service = get_notification_service(repo)
    
    result = service.get_notifications(
        company_id=company_id,
        limit=limit,
        offset=offset
    )
    
    logger.info(
        f"查詢通知記錄: company_id={company_id}, "
        f"limit={limit}, offset={offset}, "
        f"count={len(result['notifications'])}"
    )
    
    return NotificationListResponse(**result)
