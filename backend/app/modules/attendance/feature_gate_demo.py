"""
WP-11-04A: Feature Gate 示範端點

這些端點展示如何在 attendance 模組中使用 Feature Gate 機制
WP-C1-07: JWT Actor Migration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_actor_with_company
from app.core.scope import Actor
from app.core.features import FeatureKeys
from app.core.feature_service import get_feature_service, FeatureDisabledError
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/attendance", tags=["attendance"])


@router.post("/shift-overrides", status_code=status.HTTP_201_CREATED)
async def create_shift_override(
    request: Request,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
):
    """
    建立 Shift Override（需要 feature gate）
    
    驗證順序：Scope → Tenant Isolation → Feature Gate
    
    WP-11-04A: 示範 Feature Gate 使用
    WP-C1-07: 使用 JWT Actor 驗證
    """
    company_id = actor.active_company_id
    user_id = actor.user_id
    
    # Step 1: Scope 檢查（已由 get_actor_with_company 處理）
    # Step 2: Tenant Isolation（company_id 已注入）
    
    # Step 3: Feature Gate
    feature_service = get_feature_service(db)
    try:
        feature_service.require_enabled(company_id, FeatureKeys.ATTENDANCE_SHIFT_OVERRIDES)
    except FeatureDisabledError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FEATURE_DISABLED",
                "feature": e.feature_key,
                "message": str(e)
            }
        )
    
    # 實際業務邏輯（目前只是 stub）
    logger.info(f"Creating shift override for company={company_id}, user={user_id}")
    
    return {
        "id": "stub-override-id",
        "company_id": company_id,
        "message": "Shift override created (stub implementation)",
        "feature_enabled": True
    }


@router.get("/shift-templates")
async def list_shift_templates(
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
):
    """
    列出 Shift Templates（需要 feature gate）
    
    WP-11-04A: 示範 Feature Gate 使用
    WP-C1-07: 使用 JWT Actor 驗證
    """
    company_id = actor.active_company_id
    
    # Step 1: Scope 檢查（已由 get_actor_with_company 處理）
    # Step 2: Tenant Isolation（company_id 已注入）
    
    # Step 3: Feature Gate
    feature_service = get_feature_service(db)
    try:
        feature_service.require_enabled(company_id, FeatureKeys.ATTENDANCE_SHIFT_TEMPLATES)
    except FeatureDisabledError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FEATURE_DISABLED",
                "feature": e.feature_key,
                "message": str(e)
            }
        )
    
    # 實際業務邏輯（目前只是 stub）
    logger.info(f"Listing shift templates for company={company_id}")
    
    return {
        "templates": [
            {
                "id": "stub-template-1",
                "company_id": company_id,
                "name": "Morning Shift",
                "start_time": "09:00",
                "end_time": "17:00"
            }
        ],
        "feature_enabled": True
    }


@router.post("/split-shifts", status_code=status.HTTP_201_CREATED)
async def create_split_shift(
    request: Request,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
):
    """
    建立 Split Shift（需要 feature gate）
    
    WP-11-04A: 示範 Feature Gate 使用
    WP-C1-07: 使用 JWT Actor 驗證
    """
    company_id = actor.active_company_id
    user_id = actor.user_id
    
    # Step 1: Scope 檢查（已由 get_actor_with_company 處理）
    # Step 2: Tenant Isolation（company_id 已注入）
    
    # Step 3: Feature Gate
    feature_service = get_feature_service(db)
    try:
        feature_service.require_enabled(company_id, FeatureKeys.ATTENDANCE_SPLIT_SHIFT)
    except FeatureDisabledError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FEATURE_DISABLED",
                "feature": e.feature_key,
                "message": str(e)
            }
        )
    
    # 實際業務邏輯（目前只是 stub）
    logger.info(f"Creating split shift for company={company_id}, user={user_id}")
    
    return {
        "id": "stub-split-shift-id",
        "company_id": company_id,
        "message": "Split shift created (stub implementation)",
        "feature_enabled": True
    }
