"""Notifications API 路由"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_actor_with_company
from app.core.feature_service import FeatureDisabledError, get_feature_service
from app.core.features import FeatureKeys
from app.core.scope import Actor
from app.modules.notifications.repo import get_notification_repository
from app.modules.notifications.service import get_notification_service

logger = logging.getLogger(__name__)

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


def _require_notifications_feature(company_id: str, db: Session) -> None:
    """檢查 notifications.core feature gate。"""
    feature_service = get_feature_service(db)
    try:
        feature_service.require_enabled(company_id, FeatureKeys.NOTIFICATIONS_CORE)
    except FeatureDisabledError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FEATURE_DISABLED",
                "feature": e.feature_key,
                "message": str(e),
            },
        )


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    limit: int = Query(50, ge=1, le=100, description="每頁筆數"),
    offset: int = Query(0, ge=0, description="偏移量"),
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
):
    """查詢通知記錄（分頁）。"""
    company_id = actor.active_company_id
    _require_notifications_feature(company_id, db)

    repo = get_notification_repository(db)
    service = get_notification_service(repo)
    result = service.get_notifications(company_id=company_id, limit=limit, offset=offset)

    logger.info(
        "查詢通知記錄: company_id=%s, limit=%s, offset=%s, count=%s",
        company_id,
        limit,
        offset,
        len(result["notifications"]),
    )

    return NotificationListResponse(**result)
