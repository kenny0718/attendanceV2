"""Audit Log Service

負責稽核紀錄的業務邏輯層。
Phase 8: 新增 retention policy 與 purge 相關業務邏輯
"""

import logging
import json
import csv
import time
from io import StringIO
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.modules.audit.repo import AuditLogRepository, DEFAULT_RETENTION_DAYS
from app.modules.audit.models import AuditLog

logger = logging.getLogger(__name__)

# Purge 限制
MAX_BATCH_SIZE = 2000
MAX_DELETE_LIMIT = 20000


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
    
    # ==================== Phase 8: Retention Policy ====================
    
    def get_retention_days(self, company_id: str) -> Dict[str, Any]:
        """取得 retention policy
        
        Args:
            company_id: 公司 ID
        
        Returns:
            Dict: 包含 retention_days, is_default, created_at, updated_at
        """
        policy = self.repo.get_retention_policy(company_id)
        
        if policy:
            return {
                "company_id": company_id,
                "retention_days": policy.retention_days,
                "is_default": False,
                "created_at": policy.created_at.isoformat() + "Z",
                "updated_at": policy.updated_at.isoformat() + "Z"
            }
        else:
            return {
                "company_id": company_id,
                "retention_days": DEFAULT_RETENTION_DAYS,
                "is_default": True,
                "created_at": None,
                "updated_at": None
            }
    
    def update_retention_days(
        self,
        company_id: str,
        retention_days: int,
        actor: str
    ) -> Dict[str, Any]:
        """更新 retention policy
        
        Args:
            company_id: 公司 ID
            retention_days: 保留天數（7 ~ 3650）
            actor: 執行者
        
        Returns:
            Dict: 更新後的 retention policy
        
        Raises:
            ValueError: 若 retention_days 超出範圍
        """
        # 驗證範圍
        if retention_days < 7 or retention_days > 3650:
            raise ValueError("retention_days 必須在 7 ~ 3650 之間")
        
        # 取得舊值（用於 audit log）
        old_policy = self.repo.get_retention_policy(company_id)
        old_retention_days = old_policy.retention_days if old_policy else DEFAULT_RETENTION_DAYS
        
        # 更新
        policy = self.repo.upsert_retention_policy(company_id, retention_days)
        
        # 寫入 audit log
        self.repo.create_log(
            company_id=company_id,
            action="audit.retention.update",
            status="success",
            actor=actor,
            meta={
                "old_retention_days": old_retention_days,
                "new_retention_days": retention_days
            }
        )
        
        logger.info(
            f"更新 retention policy: company_id={company_id}, "
            f"old={old_retention_days}, new={retention_days}, actor={actor}"
        )
        
        return {
            "company_id": company_id,
            "retention_days": policy.retention_days,
            "is_default": False,
            "created_at": policy.created_at.isoformat() + "Z",
            "updated_at": policy.updated_at.isoformat() + "Z"
        }
    
    def purge_old_logs(
        self,
        company_id: str,
        actor: str,
        dry_run: bool = True,
        batch_size: int = 1000,
        max_delete: int = 10000
    ) -> Dict[str, Any]:
        """清理過期的 audit logs
        
        Args:
            company_id: 公司 ID
            actor: 執行者
            dry_run: 是否為 dry run（僅回報，不實際刪除）
            batch_size: 批次大小（預設 1000，最大 2000）
            max_delete: 單次最大刪除筆數（預設 10000，最大 20000）
        
        Returns:
            Dict: Purge report
                - company_id
                - cutoff_date
                - deleted_count
                - dry_run
                - batches_executed
                - duration_ms
        
        Raises:
            ValueError: 若參數超出範圍
        """
        start_time = time.time()
        
        # 驗證參數
        if batch_size < 1 or batch_size > MAX_BATCH_SIZE:
            raise ValueError(f"batch_size 必須在 1 ~ {MAX_BATCH_SIZE} 之間")
        
        if max_delete < 1 or max_delete > MAX_DELETE_LIMIT:
            raise ValueError(f"max_delete 必須在 1 ~ {MAX_DELETE_LIMIT} 之間")
        
        # 取得 retention policy
        policy = self.repo.get_retention_policy(company_id)
        retention_days = policy.retention_days if policy else DEFAULT_RETENTION_DAYS
        
        # 計算 cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # 計算可刪除筆數
        total_purgeable = self.repo.count_purgeable_logs(company_id, cutoff_date)
        
        # 實際刪除筆數（受 max_delete 限制）
        target_delete_count = min(total_purgeable, max_delete)
        
        deleted_count = 0
        batches_executed = 0
        
        if not dry_run and target_delete_count > 0:
            # 實際刪除
            while deleted_count < target_delete_count:
                # 計算本批次要刪除的筆數
                current_batch_size = min(batch_size, target_delete_count - deleted_count)
                
                # 刪除一批
                batch_deleted = self.repo.delete_logs_batch(
                    company_id=company_id,
                    cutoff_date=cutoff_date,
                    batch_size=current_batch_size
                )
                
                if batch_deleted == 0:
                    # 沒有更多可刪除的紀錄
                    break
                
                deleted_count += batch_deleted
                batches_executed += 1
                
                logger.info(
                    f"Purge batch {batches_executed}: deleted={batch_deleted}, "
                    f"total_deleted={deleted_count}/{target_delete_count}"
                )
        else:
            # Dry run：只回報，不刪除
            deleted_count = target_delete_count
        
        # 計算執行時間
        duration_ms = int((time.time() - start_time) * 1000)
        
        # 寫入 audit log
        self.repo.create_log(
            company_id=company_id,
            action="audit.purge",
            status="success",
            actor=actor,
            meta={
                "cutoff_date": cutoff_date.isoformat() + "Z",
                "retention_days": retention_days,
                "deleted_count": deleted_count,
                "total_purgeable": total_purgeable,
                "dry_run": dry_run,
                "batch_size": batch_size,
                "max_delete": max_delete,
                "batches_executed": batches_executed,
                "duration_ms": duration_ms
            }
        )
        
        logger.info(
            f"Purge 完成: company_id={company_id}, dry_run={dry_run}, "
            f"deleted={deleted_count}, batches={batches_executed}, duration={duration_ms}ms"
        )
        
        return {
            "company_id": company_id,
            "cutoff_date": cutoff_date.isoformat() + "Z",
            "retention_days": retention_days,
            "deleted_count": deleted_count,
            "total_purgeable": total_purgeable,
            "dry_run": dry_run,
            "batch_size": batch_size,
            "max_delete": max_delete,
            "batches_executed": batches_executed,
            "duration_ms": duration_ms
        }
    
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
