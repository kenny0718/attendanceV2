"""Audit Log API

提供稽核紀錄的查詢與匯出 API。
Phase 8: 新增 retention policy 與 purge API

WP-C1-03: 遷移至 JWT Actor 驗證
- 移除 get_current_company_id Header 依賴
- 改用 get_actor_with_company()，company_id 從 actor.active_company_id 取得
- GET /export、PUT /retention、POST /purge 加入 admin RBAC（assert_admin_scope）
- GET /logs、GET /retention 不需要 admin（任何公司成員可存取）
- PUT /retention、POST /purge 的 request body 中 actor 欄位保持不變
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.scope import Actor, ScopeError, assert_admin_scope
from app.core.dependencies import get_actor_with_company
from app.modules.audit.repo import AuditLogRepository
from app.modules.audit.service import AuditLogService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["audit"])


def get_audit_service(db: Session = Depends(get_db)) -> AuditLogService:
    """取得 AuditLogService 實例（FastAPI Dependency）"""
    repo = AuditLogRepository(db)
    return AuditLogService(repo)


# ==================== Phase 7: Query & Export ====================

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
    service: AuditLogService = Depends(get_audit_service)
):
    """查詢稽核紀錄

    支援篩選、分頁、排序功能。

    **權限規則：**
    - 需有效 JWT 公司範圍（actor.active_company_id）
    - 只能查詢該公司的稽核紀錄（tenant isolation）

    **Query 參數：**
    - event_type: 事件類型（例如：backup.export, backup.restore）
    - actor: 執行者
    - date_from: 開始日期（ISO 8601 格式）
    - date_to: 結束日期（ISO 8601 格式）
    - q: 關鍵字搜尋（搜尋 action, actor, error, metadata）
    - page: 頁碼（預設 1）
    - page_size: 每頁筆數（預設 50，最大 200）
    - sort: 排序欄位（預設 -created_at，支援 created_at, action）

    **回應格式：**
    ```json
    {
        "page": 1,
        "page_size": 50,
        "total": 123,
        "items": [
            {
                "id": "uuid",
                "company_id": "company-A",
                "event_type": "backup.export",
                "action": "export",
                "actor": "boss",
                "target": "company-A",
                "status": "success",
                "message": "操作成功",
                "metadata": {"tables": 2, "version": "1.0"},
                "created_at": "2026-01-28T10:00:00Z"
            }
        ]
    }
    ```
    """
    company_id = actor.active_company_id

    try:
        result = service.query_logs(
            company_id=company_id,
            event_type=event_type,
            actor=actor_filter,
            date_from=date_from,
            date_to=date_to,
            q=q,
            page=page,
            page_size=page_size,
            sort=sort
        )
        return result
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
    db: Session = Depends(get_db)
):
    """匯出稽核紀錄

    支援 JSON 和 CSV 兩種格式。

    **權限規則：**
    - 需為該公司的管理員（admin / manager / hr）或 super_admin

    **Query 參數：**
    - format: 匯出格式（json 或 csv，預設 json）
    - event_type, actor, date_from, date_to, q: 篩選條件（同 /api/audit/logs）
    - sort: 排序欄位

    **限制：**
    - 最多匯出 5000 筆
    - 若超過 5000 筆，回傳 400 錯誤並提示縮小條件

    **JSON 格式：**
    - Content-Type: application/json
    - 回傳 items 陣列

    **CSV 格式：**
    - Content-Type: text/csv; charset=utf-8
    - 第一列為 header
    - UTF-8 編碼（含 BOM，讓 Excel 正確識別）
    """
    company_id = actor.active_company_id

    # RBAC：只有管理員可匯出稽核紀錄
    try:
        assert_admin_scope(actor, company_id, db)
    except ScopeError as e:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "ADMIN_REQUIRED",
                "company_id": company_id,
                "message": str(e)
            }
        )

    try:
        if format == "json":
            # JSON 格式
            items = service.export_logs_json(
                company_id=company_id,
                event_type=event_type,
                actor=actor_filter,
                date_from=date_from,
                date_to=date_to,
                q=q,
                sort=sort
            )
            return items

        elif format == "csv":
            # CSV 格式
            csv_content = service.export_logs_csv(
                company_id=company_id,
                event_type=event_type,
                actor=actor_filter,
                date_from=date_from,
                date_to=date_to,
                q=q,
                sort=sort
            )

            # 回傳 CSV（含 UTF-8 BOM）
            return Response(
                content=csv_content.encode("utf-8"),
                media_type="text/csv; charset=utf-8",
                headers={
                    "Content-Disposition": f"attachment; filename=audit_logs_{company_id}.csv"
                }
            )

        else:
            raise HTTPException(status_code=400, detail="不支援的格式，請使用 json 或 csv")

    except ValueError as e:
        # 超過 5000 筆限制
        logger.warning(f"匯出稽核紀錄失敗: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"匯出稽核紀錄失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"匯出失敗: {str(e)}")


# ==================== Phase 8: Retention Policy & Purge ====================

@router.get("/retention")
def get_retention_policy(
    actor: Actor = Depends(get_actor_with_company),
    service: AuditLogService = Depends(get_audit_service)
):
    """取得 audit log 保留政策

    **權限規則：**
    - 需有效 JWT 公司範圍（actor.active_company_id）

    **回應格式：**
    ```json
    {
        "company_id": "company-A",
        "retention_days": 365,
        "is_default": true,
        "created_at": null,
        "updated_at": null
    }
    ```

    **說明：**
    - `retention_days`: 保留天數（7 ~ 3650）
    - `is_default`: 是否使用預設值（true = 使用預設 365 天）
    - `created_at`: 建立時間（若未設定則為 null）
    - `updated_at`: 更新時間（若未設定則為 null）
    """
    company_id = actor.active_company_id

    try:
        result = service.get_retention_days(company_id)
        return result
    except Exception as e:
        logger.error(f"取得 retention policy 失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"取得失敗: {str(e)}")


class UpdateRetentionRequest(BaseModel):
    """更新 retention policy 請求"""
    retention_days: int = Field(..., ge=7, le=3650, description="保留天數（7 ~ 3650）")
    actor: str = Field(..., min_length=1, max_length=255, description="執行者")


@router.put("/retention")
def update_retention_policy(
    request: UpdateRetentionRequest,
    jwt_actor: Actor = Depends(get_actor_with_company),
    service: AuditLogService = Depends(get_audit_service),
    db: Session = Depends(get_db)
):
    """更新 audit log 保留政策

    **權限規則：**
    - 需為該公司的管理員（admin / manager / hr）或 super_admin

    **Body 參數：**
    ```json
    {
        "retention_days": 180,
        "actor": "admin"
    }
    ```

    **回應格式：**
    ```json
    {
        "company_id": "company-A",
        "retention_days": 180,
        "is_default": false,
        "created_at": "2026-01-28T10:00:00Z",
        "updated_at": "2026-01-28T10:00:00Z"
    }
    ```

    **注意：**
    - 更新行為會寫入 audit log（event_type: audit.retention.update）
    - retention_days 必須在 7 ~ 3650 之間
    - request.actor 欄位為執行者識別字串，與 JWT actor 分開
    """
    company_id = jwt_actor.active_company_id

    # RBAC：只有管理員可更新 retention policy
    try:
        assert_admin_scope(jwt_actor, company_id, db)
    except ScopeError as e:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "ADMIN_REQUIRED",
                "company_id": company_id,
                "message": str(e)
            }
        )

    try:
        result = service.update_retention_days(
            company_id=company_id,
            retention_days=request.retention_days,
            actor=request.actor
        )
        return result
    except ValueError as e:
        logger.warning(f"更新 retention policy 失敗: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新 retention policy 失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新失敗: {str(e)}")


class PurgeRequest(BaseModel):
    """Purge 請求"""
    actor: str = Field(..., min_length=1, max_length=255, description="執行者")
    dry_run: bool = Field(True, description="是否為 dry run（僅回報，不實際刪除）")
    batch_size: int = Field(1000, ge=1, le=2000, description="批次大小（1 ~ 2000）")
    max_delete: int = Field(10000, ge=1, le=20000, description="單次最大刪除筆數（1 ~ 20000）")


@router.post("/purge")
def purge_old_audit_logs(
    request: PurgeRequest,
    jwt_actor: Actor = Depends(get_actor_with_company),
    service: AuditLogService = Depends(get_audit_service),
    db: Session = Depends(get_db)
):
    """清理過期的 audit logs

    **權限規則：**
    - 需為該公司的管理員（admin / manager / hr）或 super_admin

    **Body 參數：**
    ```json
    {
        "actor": "admin",
        "dry_run": true,
        "batch_size": 1000,
        "max_delete": 10000
    }
    ```

    **回應格式：**
    ```json
    {
        "company_id": "company-A",
        "cutoff_date": "2025-01-28T10:00:00Z",
        "retention_days": 365,
        "deleted_count": 1234,
        "total_purgeable": 1234,
        "dry_run": true,
        "batch_size": 1000,
        "max_delete": 10000,
        "batches_executed": 0,
        "duration_ms": 123
    }
    ```

    **說明：**
    - `cutoff_date`: 截止日期（created_at < cutoff_date 的紀錄會被刪除）
    - `deleted_count`: 刪除筆數（dry_run=true 時為預估值）
    - `total_purgeable`: 總共可刪除筆數
    - `dry_run`: 是否為 dry run
    - `batches_executed`: 執行的批次數（dry_run=true 時為 0）
    - `duration_ms`: 執行時間（毫秒）

    **注意：**
    - 建議先用 `dry_run=true` 測試
    - Purge 行為會寫入 audit log（event_type: audit.purge）
    - 刪除條件：`created_at < now - retention_days`
    - 分批刪除，避免 DB lock
    - request.actor 欄位為執行者識別字串，與 JWT actor 分開
    """
    company_id = jwt_actor.active_company_id

    # RBAC：只有管理員可執行 purge
    try:
        assert_admin_scope(jwt_actor, company_id, db)
    except ScopeError as e:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "ADMIN_REQUIRED",
                "company_id": company_id,
                "message": str(e)
            }
        )

    try:
        result = service.purge_old_logs(
            company_id=company_id,
            actor=request.actor,
            dry_run=request.dry_run,
            batch_size=request.batch_size,
            max_delete=request.max_delete
        )
        return result
    except ValueError as e:
        logger.warning(f"Purge 失敗: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Purge 失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Purge 失敗: {str(e)}")
