"""Backup API 路由"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.tenant_context import get_current_company_id
from app.modules.backup.service import get_backup_service

logger = logging.getLogger(__name__)

# 建立路由
router = APIRouter(prefix="/api/backup", tags=["backup"])


class ExportResponse(BaseModel):
    """匯出回應"""
    metadata: Dict[str, Any] = Field(..., description="備份 metadata")
    data: Dict[str, Any] = Field(..., description="備份資料")


class RestoreRequest(BaseModel):
    """還原請求"""
    metadata: Dict[str, Any] = Field(..., description="備份 metadata")
    data: Dict[str, Any] = Field(..., description="備份資料")


class RestoreResponse(BaseModel):
    """還原回應"""
    ok: bool = Field(..., description="操作是否成功")
    target_company_id: str = Field(..., description="目標公司 ID")
    summary: Dict[str, int] = Field(..., description="還原統計（各表筆數）")


@router.post("/export", response_model=ExportResponse)
async def export_company_backup(
    current_company_id: str = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """匯出公司資料（單一租戶備份）
    
    Tenant Isolation (P0):
    - company_id 從 Header (X-Company-ID) 強制注入
    - 只匯出該公司的資料
    - 缺少 Header → 400 Bad Request
    
    匯出格式：
    - JSON 格式（不壓縮）
    - 包含 metadata 和 data
    - 所有 UUID 轉為字串
    - 所有 datetime 轉為 ISO8601 字串
    
    Args:
        current_company_id: 當前公司 ID（從 tenant_context 注入）
        db: 資料庫 Session
    
    Returns:
        ExportResponse: 備份資料（JSON）
    """
    try:
        service = get_backup_service(db)
        backup_data = service.export_company(current_company_id)
        
        logger.info(
            f"匯出成功: company_id={current_company_id}, "
            f"tables={len(backup_data['data'])}"
        )
        
        return ExportResponse(**backup_data)
        
    except Exception as e:
        logger.error(f"匯出失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"匯出失敗: {str(e)}"
        )


@router.post("/restore", response_model=RestoreResponse)
async def restore_company_backup(
    request: RestoreRequest,
    clear_existing: bool = Query(
        False,
        description="是否清空現有資料（預設 false，Merge 模式）"
    ),
    current_company_id: str = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """還原公司資料（單一租戶還原）
    
    Tenant Isolation (P0):
    - target_company_id 從 Header (X-Company-ID) 強制注入
    - 所有資料的 company_id 強制覆寫為 target_company_id
    - 不信任備份檔內的 company_id
    
    還原策略：
    - clear_existing=false（預設）：Merge 模式，保留現有資料
    - clear_existing=true：Replace 模式，清空後還原
    
    驗證：
    - Company Consistency Check（P0）
    - FK Closure Check（P0）
    - 格式驗證
    
    Transaction：
    - 使用 transaction 確保原子性
    - 失敗時完整 rollback
    
    Args:
        request: 還原請求（備份資料）
        clear_existing: 是否清空現有資料
        current_company_id: 目標公司 ID（從 tenant_context 注入）
        db: 資料庫 Session
    
    Returns:
        RestoreResponse: 還原結果
    
    Raises:
        HTTPException: 驗證失敗或還原失敗
    """
    try:
        # 組裝備份資料
        backup_data = {
            "metadata": request.metadata,
            "data": request.data
        }
        
        # 執行還原
        service = get_backup_service(db)
        result = service.restore_company(
            target_company_id=current_company_id,
            backup_data=backup_data,
            clear_existing=clear_existing
        )
        
        logger.info(
            f"還原成功: target_company_id={current_company_id}, "
            f"clear_existing={clear_existing}, "
            f"summary={result['summary']}"
        )
        
        return RestoreResponse(**result)
        
    except ValueError as e:
        # 驗證失敗（Company Consistency, FK Closure 等）
        logger.warning(f"還原驗證失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"驗證失敗: {str(e)}"
        )
    except Exception as e:
        # 其他錯誤（資料庫錯誤等）
        logger.error(f"還原失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"還原失敗: {str(e)}"
        )
