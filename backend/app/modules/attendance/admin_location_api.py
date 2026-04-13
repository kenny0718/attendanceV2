"""Attendance Location Policy Admin API (WP-11-13)

管理端 API，提供 allowed locations 的 CRUD 操作。

WP-C1-02 Step 1 變更：
- POST / PUT / DELETE 三個寫入 endpoint 加入真實 RBAC 檢查
- 改用 get_actor_with_company() 取代 get_current_company_id Header
- 公司 scope 從 actor.active_company_id 取得（來自 JWT，已驗證）
- 讀取端點（GET）維持現狀，僅要求有效公司 scope
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.scope import Actor, ScopeError, assert_admin_scope
from app.core.dependencies import get_actor_with_company
from app.modules.attendance.models import AllowedLocation
from app.modules.attendance.schemas import (
    AllowedLocationCreate,
    AllowedLocationUpdate,
    AllowedLocationResponse,
    AllowedLocationListResponse
)

router = APIRouter(prefix="/api/v1/admin/allowed-locations", tags=["admin-location-policy"])


@router.post("", response_model=AllowedLocationResponse, status_code=201)
async def create_allowed_location(
    request: AllowedLocationCreate,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    """建立允許打卡地點 (WP-11-13)

    權限：需為該公司的管理員（company_admin / hr_manager）或 super_admin

    Args:
        request: 建立請求
        actor: 已驗證的操作者（含 active_company_id）
        db: Database session

    Returns:
        AllowedLocationResponse

    Raises:
        400: 參數錯誤
        401: 未授權
        403: 無管理員權限
    """
    company_id = actor.active_company_id

    # RBAC：只有管理員可建立地點
    try:
        assert_admin_scope(actor, company_id, db)
    except ScopeError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ADMIN_REQUIRED",
                "company_id": company_id,
                "message": str(e)
            }
        )

    location = AllowedLocation(
        company_id=company_id,
        name=request.name,
        description=request.description,
        location_type=request.location_type,
        latitude=request.latitude,
        longitude=request.longitude,
        radius_meters=request.radius_meters,
        is_active=request.is_active,
        created_by=str(actor.user_id)
    )

    db.add(location)
    db.commit()
    db.refresh(location)

    return location


@router.get("", response_model=AllowedLocationListResponse)
async def list_allowed_locations(
    is_active: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    """查詢允許打卡地點列表 (WP-11-13)

    權限：公司任何成員（員工 / 管理員）均可讀取

    Args:
        is_active: 過濾啟用狀態
        limit: 每頁筆數
        offset: 偏移量
        actor: 已驗證的操作者（含 active_company_id）
        db: Database session

    Returns:
        AllowedLocationListResponse
    """
    company_id = actor.active_company_id

    query = db.query(AllowedLocation).filter(
        AllowedLocation.company_id == company_id
    )

    if is_active is not None:
        query = query.filter(AllowedLocation.is_active == is_active)

    total = query.count()
    locations = query.order_by(AllowedLocation.created_at.desc()).offset(offset).limit(limit).all()

    return AllowedLocationListResponse(
        locations=locations,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/{location_id}", response_model=AllowedLocationResponse)
async def get_allowed_location(
    location_id: UUID,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    """查詢單筆允許打卡地點 (WP-11-13)

    權限：公司任何成員均可讀取

    Args:
        location_id: 地點 ID
        actor: 已驗證的操作者（含 active_company_id）
        db: Database session

    Returns:
        AllowedLocationResponse

    Raises:
        404: 地點不存在
    """
    company_id = actor.active_company_id

    location = db.query(AllowedLocation).filter(
        AllowedLocation.id == location_id,
        AllowedLocation.company_id == company_id
    ).first()

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    return location


@router.put("/{location_id}", response_model=AllowedLocationResponse)
async def update_allowed_location(
    location_id: UUID,
    request: AllowedLocationUpdate,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    """更新允許打卡地點 (WP-11-13)

    權限：需為該公司的管理員（company_admin / hr_manager）或 super_admin

    Args:
        location_id: 地點 ID
        request: 更新請求
        actor: 已驗證的操作者（含 active_company_id）
        db: Database session

    Returns:
        AllowedLocationResponse

    Raises:
        403: 無管理員權限
        404: 地點不存在
    """
    company_id = actor.active_company_id

    # RBAC：只有管理員可更新地點
    try:
        assert_admin_scope(actor, company_id, db)
    except ScopeError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ADMIN_REQUIRED",
                "company_id": company_id,
                "message": str(e)
            }
        )

    location = db.query(AllowedLocation).filter(
        AllowedLocation.id == location_id,
        AllowedLocation.company_id == company_id
    ).first()

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(location, field, value)

    location.updated_by = str(actor.user_id)

    db.commit()
    db.refresh(location)

    return location


@router.delete("/{location_id}", status_code=204)
async def delete_allowed_location(
    location_id: UUID,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    """刪除允許打卡地點 (WP-11-13)

    權限：需為該公司的管理員（company_admin / hr_manager）或 super_admin

    Args:
        location_id: 地點 ID
        actor: 已驗證的操作者（含 active_company_id）
        db: Database session

    Raises:
        403: 無管理員權限
        404: 地點不存在
    """
    company_id = actor.active_company_id

    # RBAC：只有管理員可刪除地點
    try:
        assert_admin_scope(actor, company_id, db)
    except ScopeError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ADMIN_REQUIRED",
                "company_id": company_id,
                "message": str(e)
            }
        )

    location = db.query(AllowedLocation).filter(
        AllowedLocation.id == location_id,
        AllowedLocation.company_id == company_id
    ).first()

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    db.delete(location)
    db.commit()

    return None
