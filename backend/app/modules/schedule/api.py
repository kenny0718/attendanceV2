"""
Schedule Module — API Router
==============================
WP-S1-04A: API Layer implementation (router ready, not mounted).

Endpoints:
  ShiftTemplate:
    POST   /api/v1/schedule/shift-templates                  - 建立班別模板
    GET    /api/v1/schedule/shift-templates                  - 列出班別模板
    GET    /api/v1/schedule/shift-templates/{template_id}    - 取得班別模板
    PATCH  /api/v1/schedule/shift-templates/{template_id}    - 更新班別模板
    POST   /api/v1/schedule/shift-templates/{template_id}/activate   - 啟用
    POST   /api/v1/schedule/shift-templates/{template_id}/deactivate - 停用

  ShiftAssignment:
    POST   /api/v1/schedule/shift-assignments                - 建立指派
    GET    /api/v1/schedule/shift-assignments                - 列出指派
    GET    /api/v1/schedule/shift-assignments/{assignment_id} - 取得指派
    PATCH  /api/v1/schedule/shift-assignments/{assignment_id} - 更新指派
    POST   /api/v1/schedule/shift-assignments/{assignment_id}/cancel - 取消指派

API layer only:
  - 不含業務規則，所有邏輯交給 service 層
  - Tenant Isolation: company_id 從 JWT actor 取得
  - Feature Gate: 本輪不加（schedule.core 尚未定義於 FeatureKeys）
  - Router 尚未掛入 main.py（WP-S1-04B 執行）

NOTE: Router is NOT registered in main.py in this ticket (WP-S1-04A).
"""

import logging
from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_actor_with_company
from app.core.scope import Actor
from app.modules.schedule.schemas import (
    AssignmentStatusSchema,
    ShiftAssignmentCreate,
    ShiftAssignmentRead,
    ShiftAssignmentUpdate,
    ShiftTemplateCreate,
    ShiftTemplateRead,
    ShiftTemplateUpdate,
)
from app.core.features import FeatureKeys
from app.core.feature_service import get_feature_service, FeatureDisabledError
from app.modules.schedule.service import get_schedule_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Router definition
# Router is NOT registered in main.py in WP-S1-04A.
# Registration happens in WP-S1-04B.
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/api/v1/schedule",
    tags=["schedule"],
)


def _require_schedule_feature(company_id: str, db: Session) -> None:
    """WP-S1-04B: 檢查 schedule.core Feature Gate

    Raises:
        HTTPException 403: 若 schedule.core 未啟用
    """
    feature_service = get_feature_service(db)
    try:
        feature_service.require_enabled(company_id, FeatureKeys.SCHEDULE_CORE)
    except FeatureDisabledError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FEATURE_DISABLED",
                "feature": e.feature_key,
                "message": str(e),
            },
        )


# ===========================================================================
# ShiftTemplate Endpoints
# ===========================================================================

@router.post(
    "/shift-templates",
    response_model=ShiftTemplateRead,
    status_code=status.HTTP_201_CREATED,
    summary="建立班別模板",
)
def create_shift_template(
    payload: ShiftTemplateCreate,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
) -> ShiftTemplateRead:
    """建立新的 ShiftTemplate。

    - code 在同 company 內必須唯一（重複 → 409）
    - Tenant Isolation: company_id 強制來自 JWT actor
    """
    company_id = actor.active_company_id
    _require_schedule_feature(company_id, db)
    svc = get_schedule_service(db)
    return svc.create_shift_template(company_id, payload)


@router.get(
    "/shift-templates",
    response_model=List[ShiftTemplateRead],
    summary="列出班別模板",
)
def list_shift_templates(
    active_only: bool = Query(True, description="只列出 is_active=True 的模板"),
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
) -> List[ShiftTemplateRead]:
    """列出公司的所有班別模板。

    - 預設只回傳 active 模板
    - Tenant Isolation: 強制 company scope
    """
    company_id = actor.active_company_id
    _require_schedule_feature(company_id, db)
    svc = get_schedule_service(db)
    return svc.list_shift_templates(company_id, active_only=active_only)


@router.get(
    "/shift-templates/{template_id}",
    response_model=ShiftTemplateRead,
    summary="取得班別模板",
)
def get_shift_template(
    template_id: UUID,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
) -> ShiftTemplateRead:
    """依 ID 取得單一班別模板。

    - 不存在或不屬於此 company → 404
    - Tenant Isolation: 強制 company scope
    """
    company_id = actor.active_company_id
    _require_schedule_feature(company_id, db)
    svc = get_schedule_service(db)
    return svc.get_shift_template(company_id, template_id)


@router.patch(
    "/shift-templates/{template_id}",
    response_model=ShiftTemplateRead,
    summary="更新班別模板",
)
def update_shift_template(
    template_id: UUID,
    payload: ShiftTemplateUpdate,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
) -> ShiftTemplateRead:
    """部分更新班別模板（name / times / break_minutes / is_overnight / is_active / segments）。

    - 若 payload 提供 segments，採 replace-all（service 層處理）
    - 不存在或不屬於此 company → 404
    - Tenant Isolation: 強制 company scope
    """
    company_id = actor.active_company_id
    _require_schedule_feature(company_id, db)
    svc = get_schedule_service(db)
    return svc.update_shift_template(company_id, template_id, payload)


@router.post(
    "/shift-templates/{template_id}/activate",
    response_model=ShiftTemplateRead,
    summary="啟用班別模板",
)
def activate_shift_template(
    template_id: UUID,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
) -> ShiftTemplateRead:
    """將班別模板設為啟用（is_active=True）。

    - 不存在或不屬於此 company → 404
    """
    company_id = actor.active_company_id
    _require_schedule_feature(company_id, db)
    svc = get_schedule_service(db)
    return svc.activate_shift_template(company_id, template_id)


@router.post(
    "/shift-templates/{template_id}/deactivate",
    response_model=ShiftTemplateRead,
    summary="停用班別模板",
)
def deactivate_shift_template(
    template_id: UUID,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
) -> ShiftTemplateRead:
    """將班別模板軟刪除（is_active=False）。

    - 不存在或不屬於此 company → 404
    """
    company_id = actor.active_company_id
    _require_schedule_feature(company_id, db)
    svc = get_schedule_service(db)
    return svc.deactivate_shift_template(company_id, template_id)


# ===========================================================================
# ShiftAssignment Endpoints
# ===========================================================================

@router.post(
    "/shift-assignments",
    response_model=ShiftAssignmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="建立班別指派",
)
def create_shift_assignment(
    payload: ShiftAssignmentCreate,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
) -> ShiftAssignmentRead:
    """將使用者指派到某一班別模板（特定日期）。

    - shift_template_id 必須屬於同 company 且 is_active（不符合 → 422）
    - Tenant Isolation: company_id 強制來自 JWT actor
    """
    company_id = actor.active_company_id
    _require_schedule_feature(company_id, db)
    svc = get_schedule_service(db)
    return svc.create_shift_assignment(company_id, payload)


@router.get(
    "/shift-assignments",
    response_model=List[ShiftAssignmentRead],
    summary="列出班別指派",
)
def list_shift_assignments(
    user_id: Optional[UUID] = Query(None, description="依使用者 UUID 過濾"),
    start_date: Optional[date] = Query(None, description="起始日期（inclusive）"),
    end_date: Optional[date] = Query(None, description="結束日期（inclusive）"),
    work_date: Optional[date] = Query(None, description="單一指定日期（優先於 date range）"),
    template_id: Optional[UUID] = Query(None, description="依班別模板 UUID 過濾（S1-09B）"),
    assignment_status: Optional[AssignmentStatusSchema] = Query(None, alias="status", description="依狀態過濾：scheduled / confirmed / cancelled（S1-09B）"),
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
) -> List[ShiftAssignmentRead]:
    """列出班別指派，支援多種過濾方式。

    過濾優先順序：
    1. work_date（單日）+ user_id（若有）
    2. user_id + start_date / end_date
    3. start_date / end_date（全公司日期範圍）
    4. 無條件（列出全公司）

    可選 filter（各路徑均支援，S1-09B）：
    - template_id：精確匹配班別模板
    - status：精確匹配狀態（scheduled / confirmed / cancelled）

    Tenant Isolation: 強制 company scope
    """
    company_id = actor.active_company_id
    _require_schedule_feature(company_id, db)
    svc = get_schedule_service(db)
    _status = assignment_status.value if assignment_status is not None else None

    # work_date 優先
    if work_date is not None:
        if user_id is not None:
            # 單日 + 單 user
            return svc.list_assignments_for_user(
                company_id, user_id,
                start_date=work_date, end_date=work_date,
                template_id=template_id, status=_status,
            )
        return svc.list_assignments_for_date(
            company_id, work_date,
            template_id=template_id, status=_status,
        )

    # user + date range
    if user_id is not None:
        if start_date is None or end_date is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id 過濾時必須同時提供 start_date 和 end_date。",
            )
        return svc.list_assignments_for_user(
            company_id, user_id,
            start_date=start_date, end_date=end_date,
            template_id=template_id, status=_status,
        )

    # 全公司（可選 date range）
    return svc.list_assignments(
        company_id,
        start_date=start_date,
        end_date=end_date,
        template_id=template_id,
        status=_status,
    )


@router.get(
    "/shift-assignments/{assignment_id}",
    response_model=ShiftAssignmentRead,
    summary="取得班別指派",
)
def get_shift_assignment(
    assignment_id: UUID,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
) -> ShiftAssignmentRead:
    """依 ID 取得單一班別指派。

    - 不存在或不屬於此 company → 404
    - Tenant Isolation: 強制 company scope
    """
    company_id = actor.active_company_id
    _require_schedule_feature(company_id, db)
    svc = get_schedule_service(db)
    return svc.get_shift_assignment(company_id, assignment_id)


@router.patch(
    "/shift-assignments/{assignment_id}",
    response_model=ShiftAssignmentRead,
    summary="更新班別指派",
)
def update_shift_assignment(
    assignment_id: UUID,
    payload: ShiftAssignmentUpdate,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
) -> ShiftAssignmentRead:
    """部分更新班別指派（shift_template_id / status / notes）。

    - 已取消的指派不可更新（→ 409）
    - 若更新 shift_template_id，新模板必須屬於同 company 且 is_active（→ 422）
    - Tenant Isolation: 強制 company scope
    """
    company_id = actor.active_company_id
    _require_schedule_feature(company_id, db)
    svc = get_schedule_service(db)
    return svc.update_shift_assignment(company_id, assignment_id, payload)


@router.post(
    "/shift-assignments/{assignment_id}/cancel",
    response_model=ShiftAssignmentRead,
    summary="取消班別指派",
)
def cancel_shift_assignment(
    assignment_id: UUID,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
) -> ShiftAssignmentRead:
    """將班別指派狀態設為 cancelled。

    - 已取消的指派再次取消 → 409
    - 不存在或不屬於此 company → 404
    - Tenant Isolation: 強制 company scope
    """
    company_id = actor.active_company_id
    _require_schedule_feature(company_id, db)
    svc = get_schedule_service(db)
    return svc.cancel_shift_assignment(company_id, assignment_id)
