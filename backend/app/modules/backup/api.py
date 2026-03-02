"""Backup API

備份模組的 API 端點。
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.tenant_context import get_current_company_id
from app.modules.backup.service import BackupService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backup", tags=["backup"])


@router.post("/export")
def export_backup(
    current_company_id: str = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """匯出公司備份資料
    
    Args:
        current_company_id: 當前公司 ID（從 tenant_context 注入）
        db: 資料庫 Session
    
    Returns:
        Dict: 備份資料（JSON 格式）
    """
    try:
        service = BackupService(db)
        backup_data = service.export_company(current_company_id)
        
        logger.info(
            f"匯出備份成功: company_id={current_company_id}, "
            f"tables={len(backup_data.get('data', {}))}"
        )
        
        return backup_data
        
    except Exception as e:
        logger.error(f"匯出備份失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/restore")
def restore_backup(
    backup_data: Dict[str, Any] = Body(...),
    current_company_id: str = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    """還原公司備份資料
    
    Args:
        backup_data: 備份資料（直接從 request body）
        current_company_id: 當前公司 ID（從 tenant_context 注入）
        db: 資料庫 Session
    
    Returns:
        Dict: 還原結果
    """
    try:
        service = BackupService(db)
        result = service.restore_company(
            target_company_id=current_company_id,
            backup_data=backup_data
        )
        
        logger.info(
            f"還原備份成功: company_id={current_company_id}, "
            f"restored={result.get('restored_count', 0)}"
        )
        
        return result
        
    except ValueError as e:
        # 驗證錯誤
        logger.warning(f"還原備份驗證失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"還原備份失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/")
def backup_placeholder():
    """備份 API 佔位符"""
    return {"status": "ok", "message": "Backup API placeholder"}
