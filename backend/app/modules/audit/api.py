"""Audit Log API

提供稽核紀錄的查詢與匯出 API。
Phase 8: 新增 retention policy 與 purge API

WP-C1-03: 遷移至 JWT Actor 驗證
- 移除 get_current_company_id Header 依賴
- 改用 get_actor_with_company()，company_id 從 actor.active_company_id 取得
- GET /export、PUT /retention、POST /purge 加入 admin RBAC（assert_admin_scope）
- GET /logs、GET /retention 不需要 admin（任何公司成員可存取）
"""

import logging
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_actor_with_company
from app.core.feature_service import FeatureDisabledError, get_feature_service
from app.core.features import FeatureKeys
from app.core.scope import Actor, ScopeError, assert_admin_scope
from app.modules.audit.repo import AuditLogRepository
from app.modules.audit.service import AuditLogService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["audit"])


def get_audit_service(db: Session = Depends(get_db)) -> AuditLogService:
    """取得 AuditLogService 實例（FastAPI Dependency）"""
    repo = AuditLogRepository(db)
    return AuditLogService(repo)


def _require_audit_feature(company_id: str, db: Session) -> None:
    """檢查 audit.core feature gate。"""
    feature_service = get_feature_service(db)
    try:
        feature_service.require_enabled(company_id, FeatureKeys.AUDIT_CORE)
    except FeatureDisabledError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FEATURE_DISABLED",
                "feature": e.feature_key,
                "message": str(e),
            },
        )


@router.get("/logs")
def query_audit_logs(
    actor: Actor = Depends(get_actor_with_company),
    event_type: Optional[str] = Query(None, description="事件類型（例如：backup.export）"),
    actor_filter: Optional[str] = Query(None, alias="actor", description="執行者"),
    date_from: Optional[str] = Query(None, description="開始日期（ISO 8601）"),
    date_to: Optional[str] = Query(None, description="結束日期（ISO 8601）"),
    q: Optional[str] = Query(None, description="關鍵字搜尋"),
    page: int = Query(1, ge=1, description="頁碼（從 1 開始）"),
    page_size: int = Query(50, ge=1, le=200, description="每頁筆數（最大 200）"),
    sort: str = Query("-created_at", description="排序欄位（例如：-created_at, created_at, action）"),
    service: AuditLogService = Depends(get_audit_service),
    db: Session = Depends(get_db),
):
    """查詢稽核紀錄。"""
    company_id = actor.active_company_id
    _require_audit_feature(company_id, db)

    try:
        return service.query_logs(
            company_id=company_id,
            event_type=event_type,
            actor=actor_filter,
            date_from=date_from,
            date_to=date_to,
            q=q,
            page=page,
            page_size=page_size,
            sort=sort,
        )
    except Exception as e:
        logger.error(f"查詢稽核紀錄失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")


@router.get("/export")
def export_audit_logs(
    actor: Actor = Depends(get_actor_with_company),
    format: str = Query("json", pattern="^(json|csv)$", description="匯出格式（json 或 csv）"),
    event_type: Optional[str] = Query(None, description="事件類型"),
    actor_filter: Optional[str] = Query(None, alias="actor", description="執行者"),
    date_from: Optional[str] = Query(None, description="開始日期（ISO 8601）"),
    date_to: Optional[str] = Query(None, description="結束日期（ISO 8601）"),
    q: Optional[str] = Query(None, description="關鍵字搜尋"),
    sort: str = Query("-created_at", description="排序欄位"),
    service: AuditLogService = Depends(get_audit_service),
    db: Session = Depends(get_db),
):
    """匯出稽核紀錄。"""
    company_id = actor.active_company_id
    _require_audit_feature(company_id, db)

    try:
        assert_admin_scope(actor, company_id, db)
    except ScopeError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ADMIN_REQUIRED",
                "company_id": company_id,
                "message": str(e),
            },
        )

    try:
        if format == "json":
            return service.export_logs_json(
                company_id=company_id,
                event_type=event_type,
                actor=actor_filter,
                date_from=date_from,
                date_to=date_to,
                q=q,
                sort=sort,
            )

        return Response(
            content=service.export_logs_csv(
                company_id=company_id,
                event_type=event_type,
                actor=actor_filter,
                date_from=date_from,
                date_to=date_to,
                q=q,
                sort=sort,
            ).encode("utf-8"),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{company_id}.csv"
            },
        )
    except ValueError as e:
        logger.warning(f"匯出稽核紀錄失敗: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"匯出稽核紀錄失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"匯出失敗: {str(e)}")


@router.get("/retention")
def get_retention_policy(
    actor: Actor = Depends(get_actor_with_company),
    service: AuditLogService = Depends(get_audit_service),
    db: Session = Depends(get_db),
):
    """取得 audit log 保留政策。"""
    company_id = actor.active_company_id
    _require_audit_feature(company_id, db)

    try:
        return service.get_retention_days(company_id)
    except Exception as e:
        logger.error(f"取得 retention policy 失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"取得失敗: {str(e)}")


class UpdateRetentionRequest(BaseModel):
    retention_days: int = Field(..., ge=7, le=3650, description="保留天數（7 ~ 3650）")
    actor: str = Field(..., min_length=1, max_length=255, description="執行者")


@router.put("/retention")
def update_retention_policy(
    request: UpdateRetentionRequest,
    jwt_actor: Actor = Depends(get_actor_with_company),
    service: AuditLogService = Depends(get_audit_service),
    db: Session = Depends(get_db),
):
    """更新 audit log 保留政策。"""
    company_id = jwt_actor.active_company_id
    _require_audit_feature(company_id, db)

    try:
        assert_admin_scope(jwt_actor, company_id, db)
    except ScopeError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ADMIN_REQUIRED",
                "company_id": company_id,
                "message": str(e),
            },
        )

    try:
        return service.update_retention_days(
            company_id=company_id,
            retention_days=request.retention_days,
            actor=request.actor,
        )
    except ValueError as e:
        logger.warning(f"更新 retention policy 失敗: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新 retention policy 失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新失敗: {str(e)}")


class PurgeRequest(BaseModel):
    actor: str = Field(..., min_length=1, max_length=255, description="執行者")
    dry_run: bool = Field(True, description="是否為 dry run（僅回報，不實際刪除）")
    batch_size: int = Field(1000, ge=1, le=2000, description="批次大小（1 ~ 2000）")
    max_delete: int = Field(10000, ge=1, le=20000, description="單次最大刪除筆數（1 ~ 20000）")


@router.post("/purge")
def purge_old_audit_logs(
    request: PurgeRequest,
    jwt_actor: Actor = Depends(get_actor_with_company),
    service: AuditLogService = Depends(get_audit_service),
    db: Session = Depends(get_db),
):
    """清理過期的 audit logs。"""
    company_id = jwt_actor.active_company_id
    _require_audit_feature(company_id, db)

    try:
        assert_admin_scope(jwt_actor, company_id, db)
    except ScopeError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ADMIN_REQUIRED",
                "company_id": company_id,
                "message": str(e),
            },
        )

    try:
        return service.purge_old_logs(
            company_id=company_id,
            actor=request.actor,
            dry_run=request.dry_run,
            batch_size=request.batch_size,
            max_delete=request.max_delete,
        )
    except ValueError as e:
        logger.warning(f"Purge 失敗: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Purge 失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Purge 失敗: {str(e)}")
