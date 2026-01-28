"""Audit Log API

提供稽核紀錄的查詢與匯出 API。
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.tenant_context import get_current_company_id
from app.modules.audit.repo import AuditLogRepository
from app.modules.audit.service import AuditLogService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["audit"])


def get_audit_service(db: Session = Depends(get_db)) -> AuditLogService:
    """取得 AuditLogService 實例（FastAPI Dependency）"""
    repo = AuditLogRepository(db)
    return AuditLogService(repo)


@router.get("/logs")
def query_audit_logs(
    company_id: str = Depends(get_current_company_id),
    event_type: Optional[str] = Query(None, description="事件類型（例如：backup.export）"),
    actor: Optional[str] = Query(None, description="執行者"),
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
    - 必須提供 X-Company-ID header
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
    try:
        result = service.query_logs(
            company_id=company_id,
            event_type=event_type,
            actor=actor,
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
    company_id: str = Depends(get_current_company_id),
    format: str = Query("json", pattern="^(json|csv)$", description="匯出格式（json 或 csv）"),
    event_type: Optional[str] = Query(None, description="事件類型"),
    actor: Optional[str] = Query(None, description="執行者"),
    date_from: Optional[str] = Query(None, description="開始日期（ISO 8601）"),
    date_to: Optional[str] = Query(None, description="結束日期（ISO 8601）"),
    q: Optional[str] = Query(None, description="關鍵字搜尋"),
    sort: str = Query("-created_at", description="排序欄位"),
    service: AuditLogService = Depends(get_audit_service)
):
    """匯出稽核紀錄
    
    支援 JSON 和 CSV 兩種格式。
    
    **權限規則：**
    - 必須提供 X-Company-ID header
    - 只能匯出該公司的稽核紀錄（tenant isolation）
    
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
    try:
        if format == "json":
            # JSON 格式
            items = service.export_logs_json(
                company_id=company_id,
                event_type=event_type,
                actor=actor,
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
                actor=actor,
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
