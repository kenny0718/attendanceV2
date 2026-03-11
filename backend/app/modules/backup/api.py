"""Backup API

備份模組的 API 端點。

WP-C1-03: 遷移至 JWT Actor 驗證
- 移除 get_current_company_id Header 依賴
- 改用 get_actor_with_company()，company_id 從 actor.active_company_id 取得
- POST /export 與 POST /restore 加入 admin RBAC（assert_admin_scope）
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.scope import Actor, ScopeError, assert_admin_scope
from app.core.dependencies import get_actor_with_company
from app.modules.backup.service import BackupService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backup", tags=["backup"])


@router.post("/export")
def export_backup(
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    """匯出公司備份資料

    權限：需為該公司的管理員（admin / manager / hr）或 super_admin

    Args:
        actor: 已驗證的操作者（含 active_company_id）
        db: 資料庫 Session

    Returns:
        Dict: 備份資料（JSON 格式）
    """
    company_id = actor.active_company_id

    # RBAC：只有管理員可匯出備份
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

    try:
        service = BackupService(db)
        backup_data = service.export_company(company_id)

        logger.info(
            f"匯出備份成功: company_id={company_id}, "
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
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    """還原公司備份資料

    權限：需為該公司的管理員（admin / manager / hr）或 super_admin

    Args:
        backup_data: 備份資料（直接從 request body）
        actor: 已驗證的操作者（含 active_company_id）
        db: 資料庫 Session

    Returns:
        Dict: 還原結果
    """
    company_id = actor.active_company_id

    # RBAC：只有管理員可還原備份
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

    try:
        service = BackupService(db)
        result = service.restore_company(
            target_company_id=company_id,
            backup_data=backup_data
        )

        logger.info(
            f"還原備份成功: company_id={company_id}, "
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
