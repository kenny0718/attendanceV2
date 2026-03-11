"""Attendance Location Policy Admin API (WP-11-13)

管理端 API，提供 allowed locations 的 CRUD 操作。
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.tenant_context import get_current_company_id, get_current_user_id
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
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """建立允許打卡地點 (WP-11-13)
    
    Args:
        request: 建立請求
        company_id: 公司 ID (from JWT)
        user_id: 使用者 ID (from JWT)
        db: Database session
    
    Returns:
        AllowedLocationResponse
    
    Raises:
        400: 參數錯誤
        401: 未授權
        403: 無管理員權限
    """
    # TODO: 驗證管理員權限
    
    # 建立地點
    location = AllowedLocation(
        company_id=company_id,
        name=request.name,
        description=request.description,
        location_type=request.location_type,
        latitude=request.latitude,
        longitude=request.longitude,
        radius_meters=request.radius_meters,
        is_active=request.is_active,
        created_by=user_id
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
    company_id: str = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """查詢允許打卡地點列表 (WP-11-13)
    
    Args:
        is_active: 過濾啟用狀態
        limit: 每頁筆數
        offset: 偏移量
        company_id: 公司 ID (from JWT)
        db: Database session
    
    Returns:
        AllowedLocationListResponse
    """
    # 建立查詢
    query = db.query(AllowedLocation).filter(
        AllowedLocation.company_id == company_id
    )
    
    # 過濾啟用狀態
    if is_active is not None:
        query = query.filter(AllowedLocation.is_active == is_active)
    
    # 計算總數
    total = query.count()
    
    # 分頁
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
    company_id: str = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """查詢單筆允許打卡地點 (WP-11-13)
    
    Args:
        location_id: 地點 ID
        company_id: 公司 ID (from JWT)
        db: Database session
    
    Returns:
        AllowedLocationResponse
    
    Raises:
        404: 地點不存在
    """
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
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """更新允許打卡地點 (WP-11-13)
    
    Args:
        location_id: 地點 ID
        request: 更新請求
        company_id: 公司 ID (from JWT)
        user_id: 使用者 ID (from JWT)
        db: Database session
    
    Returns:
        AllowedLocationResponse
    
    Raises:
        404: 地點不存在
        403: 無權限
    """
    # TODO: 驗證管理員權限
    
    # 查詢地點
    location = db.query(AllowedLocation).filter(
        AllowedLocation.id == location_id,
        AllowedLocation.company_id == company_id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # 更新欄位
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(location, field, value)
    
    location.updated_by = user_id
    
    db.commit()
    db.refresh(location)
    
    return location


@router.delete("/{location_id}", status_code=204)
async def delete_allowed_location(
    location_id: UUID,
    company_id: str = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """刪除允許打卡地點 (WP-11-13)
    
    Args:
        location_id: 地點 ID
        company_id: 公司 ID (from JWT)
        db: Database session
    
    Raises:
        404: 地點不存在
        403: 無權限
    """
    # TODO: 驗證管理員權限
    
    # 查詢地點
    location = db.query(AllowedLocation).filter(
        AllowedLocation.id == location_id,
        AllowedLocation.company_id == company_id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # 刪除地點
    db.delete(location)
    db.commit()
    
    return None
