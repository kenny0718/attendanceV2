"""Audit Log Service

負責稽核紀錄的業務邏輯層。
"""

import logging
import json
import csv
from io import StringIO
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.modules.audit.repo import AuditLogRepository
from app.modules.audit.models import AuditLog

logger = logging.getLogger(__name__)


class AuditLogService:
    """稽核紀錄 Service"""
    
    def __init__(self, repo: AuditLogRepository):
        """初始化 Service
        
        Args:
            repo: AuditLogRepository 實例
        """
        self.repo = repo
    
    def query_logs(
        self,
        company_id: str,
        event_type: Optional[str] = None,
        actor: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        sort: str = "-created_at"
    ) -> Dict[str, Any]:
        """查詢稽核紀錄
        
        Args:
            company_id: 公司 ID（tenant isolation）
            event_type: 事件類型（可選）
            actor: 執行者（可選）
            date_from: 開始日期（可選，ISO 8601）
            date_to: 結束日期（可選，ISO 8601）
            q: 關鍵字搜尋（可選）
            page: 頁碼（預設 1）
            page_size: 每頁筆數（預設 50，最大 200）
            sort: 排序欄位（預設 -created_at）
        
        Returns:
            Dict: 包含 page, page_size, total, items
        """
        # 驗證 page_size
        if page_size > 200:
            page_size = 200
        if page_size < 1:
            page_size = 1
        
        # 驗證 page
        if page < 1:
            page = 1
        
        # 組裝 filters
        filters = {}
        if event_type:
            filters["event_type"] = event_type
        if actor:
            filters["actor"] = actor
        if date_from:
            try:
                filters["date_from"] = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            except ValueError:
                logger.warning(f"無效的 date_from: {date_from}")
        if date_to:
            try:
                filters["date_to"] = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            except ValueError:
                logger.warning(f"無效的 date_to: {date_to}")
        if q:
            filters["q"] = q
        
        # 查詢
        items, total = self.repo.list_logs(
            company_id=company_id,
            filters=filters,
            page=page,
            page_size=page_size,
            sort=sort
        )
        
        # 轉換為 dict
        items_dict = [self._audit_log_to_dict(item) for item in items]
        
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": items_dict
        }
    
    def export_logs_json(
        self,
        company_id: str,
        event_type: Optional[str] = None,
        actor: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        q: Optional[str] = None,
        sort: str = "-created_at"
    ) -> List[Dict[str, Any]]:
        """匯出稽核紀錄（JSON 格式）
        
        Args:
            company_id: 公司 ID
            event_type: 事件類型（可選）
            actor: 執行者（可選）
            date_from: 開始日期（可選）
            date_to: 結束日期（可選）
            q: 關鍵字搜尋（可選）
            sort: 排序欄位
        
        Returns:
            List[Dict]: 稽核紀錄列表
        
        Raises:
            ValueError: 若結果超過 5000 筆
        """
        # 組裝 filters
        filters = {}
        if event_type:
            filters["event_type"] = event_type
        if actor:
            filters["actor"] = actor
        if date_from:
            try:
                filters["date_from"] = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            except ValueError:
                pass
        if date_to:
            try:
                filters["date_to"] = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            except ValueError:
                pass
        if q:
            filters["q"] = q
        
        # 匯出（限制 5000 筆）
        items = self.repo.export_logs(
            company_id=company_id,
            filters=filters,
            sort=sort,
            limit=5001  # 多查 1 筆來檢查是否超過限制
        )
        
        # 檢查是否超過限制
        if len(items) > 5000:
            raise ValueError("匯出結果超過 5000 筆，請縮小查詢條件")
        
        # 轉換為 dict
        return [self._audit_log_to_dict(item) for item in items]
    
    def export_logs_csv(
        self,
        company_id: str,
        event_type: Optional[str] = None,
        actor: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        q: Optional[str] = None,
        sort: str = "-created_at"
    ) -> str:
        """匯出稽核紀錄（CSV 格式）
        
        Args:
            company_id: 公司 ID
            event_type: 事件類型（可選）
            actor: 執行者（可選）
            date_from: 開始日期（可選）
            date_to: 結束日期（可選）
            q: 關鍵字搜尋（可選）
            sort: 排序欄位
        
        Returns:
            str: CSV 內容（含 UTF-8 BOM）
        
        Raises:
            ValueError: 若結果超過 5000 筆
        """
        # 取得資料
        items_dict = self.export_logs_json(
            company_id=company_id,
            event_type=event_type,
            actor=actor,
            date_from=date_from,
            date_to=date_to,
            q=q,
            sort=sort
        )
        
        # 產生 CSV
        output = StringIO()
        
        # 定義欄位
        fieldnames = [
            "id", "company_id", "event_type", "action", "actor",
            "target", "status", "message", "metadata", "created_at"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in items_dict:
            # 將 metadata 轉為 JSON 字串
            row = {
                "id": item["id"],
                "company_id": item["company_id"],
                "event_type": item["event_type"],
                "action": item.get("action", ""),
                "actor": item["actor"],
                "target": item.get("target", ""),
                "status": item["status"],
                "message": item.get("message", ""),
                "metadata": json.dumps(item.get("metadata", {}), ensure_ascii=False),
                "created_at": item["created_at"]
            }
            writer.writerow(row)
        
        # 加上 UTF-8 BOM（讓 Excel 正確識別）
        csv_content = "\ufeff" + output.getvalue()
        
        return csv_content
    
    def _audit_log_to_dict(self, log: AuditLog) -> Dict[str, Any]:
        """將 AuditLog 模型轉換為 dict
        
        Args:
            log: AuditLog 實例
        
        Returns:
            Dict: 包含所有欄位的 dict
        """
        return {
            "id": str(log.id),
            "company_id": log.company_id,
            "event_type": log.action,
            "action": log.action,
            "actor": log.actor,
            "target": log.company_id,
            "status": log.status,
            "message": log.error if log.status == "fail" else "操作成功",
            "metadata": log.meta,
            "created_at": log.created_at.isoformat() + "Z" if log.created_at else None
        }

