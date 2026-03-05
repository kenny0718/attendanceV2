"""Audit Log Repository

負責 audit_logs 表的資料存取操作。
Phase 8: 新增 retention policy 與 purge 相關方法
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_, cast, String, delete

from app.modules.audit.models import AuditLog, AuditRetentionPolicy

logger = logging.getLogger(__name__)

# 預設保留天數
DEFAULT_RETENTION_DAYS = 365


class AuditLogRepository:
    """稽核紀錄 Repository"""
    
    def __init__(self, db: Session):
        """初始化 Repository
        
        Args:
            db: SQLAlchemy Session
        """
        self.db = db
    
    def create_log(
        self,
        company_id: str,
        action: str,
        status: str,
        actor: str,
        request_id: Optional[str] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> AuditLog:
        """建立稽核紀錄
        
        Args:
            company_id: 目標公司 ID
            action: 操作類型（例如：backup.export, backup.restore）
            status: 操作狀態（success / fail）
            actor: 執行者
            request_id: 請求 ID（可選）
            ip: 來源 IP（可選）
            user_agent: User Agent（可選）
            meta: Meta 資料（可選）
            error: 錯誤訊息（可選，失敗時記錄，最多 2000 字）
        
        Returns:
            AuditLog: 建立的稽核紀錄
        """
        # 截斷錯誤訊息（最多 2000 字）
        if error and len(error) > 2000:
            error = error[:2000] + "... (truncated)"
        
        # 建立稽核紀錄
        audit_log = AuditLog(
            company_id=company_id,
            action=action,
            status=status,
            actor=actor,
            request_id=request_id,
            ip=ip,
            user_agent=user_agent,
            meta=meta or {},
            error=error
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        logger.info(
            f"建立稽核紀錄: id={audit_log.id}, company_id={company_id}, "
            f"action={action}, status={status}, actor={actor}"
        )
        
        return audit_log
    
    def list_logs(
        self,
        company_id: str,
        filters: Dict[str, Any],
        page: int,
        page_size: int,
        sort: str
    ) -> Tuple[List[AuditLog], int]:
        """查詢稽核紀錄（分頁）
        
        Args:
            company_id: 公司 ID（tenant isolation）
            filters: 篩選條件 dict
                - event_type: 事件類型
                - actor: 執行者
                - date_from: 開始日期
                - date_to: 結束日期
                - q: 關鍵字搜尋
            page: 頁碼（從 1 開始）
            page_size: 每頁筆數
            sort: 排序欄位（例如：-created_at, created_at, action）
        
        Returns:
            Tuple[List[AuditLog], int]: (items, total)
        """
        # 基礎查詢：必須套用 tenant isolation
        query = self.db.query(AuditLog).filter(AuditLog.company_id == company_id)
        
        # 篩選：event_type (對應到 action 欄位)
        if filters.get("event_type"):
            query = query.filter(AuditLog.action == filters["event_type"])
        
        # 篩選：actor
        if filters.get("actor"):
            query = query.filter(AuditLog.actor == filters["actor"])
        
        # 篩選：date_from
        if filters.get("date_from"):
            query = query.filter(AuditLog.created_at >= filters["date_from"])
        
        # 篩選：date_to
        if filters.get("date_to"):
            query = query.filter(AuditLog.created_at <= filters["date_to"])
        
        # 篩選：關鍵字搜尋（搜尋 action, actor, error, meta）
        if filters.get("q"):
            keyword = f"%{filters['q']}%"
            query = query.filter(
                or_(
                    AuditLog.action.ilike(keyword),
                    AuditLog.actor.ilike(keyword),
                    AuditLog.error.ilike(keyword),
                    cast(AuditLog.meta, String).ilike(keyword)
                )
            )
        
        # 計算總數
        total = query.count()
        
        # 排序（allowlist 防止 SQL injection）
        if sort.startswith("-"):
            # 降序
            sort_field = sort[1:]
            if sort_field == "created_at":
                query = query.order_by(desc(AuditLog.created_at))
            elif sort_field == "action":
                query = query.order_by(desc(AuditLog.action))
            else:
                # 預設降序 created_at
                query = query.order_by(desc(AuditLog.created_at))
        else:
            # 升序
            if sort == "created_at":
                query = query.order_by(asc(AuditLog.created_at))
            elif sort == "action":
                query = query.order_by(asc(AuditLog.action))
            else:
                # 預設降序 created_at
                query = query.order_by(desc(AuditLog.created_at))
        
        # 分頁
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        return items, total
    
    def export_logs(
        self,
        company_id: str,
        filters: Dict[str, Any],
        sort: str,
        limit: int = 5000
    ) -> List[AuditLog]:
        """匯出稽核紀錄（不分頁，有筆數限制）
        
        Args:
            company_id: 公司 ID（tenant isolation）
            filters: 篩選條件（同 list_logs）
            sort: 排序欄位
            limit: 最大筆數（預設 5000）
        
        Returns:
            List[AuditLog]: 稽核紀錄列表
        """
        # 基礎查詢：必須套用 tenant isolation
        query = self.db.query(AuditLog).filter(AuditLog.company_id == company_id)
        
        # 篩選：event_type
        if filters.get("event_type"):
            query = query.filter(AuditLog.action == filters["event_type"])
        
        # 篩選：actor
        if filters.get("actor"):
            query = query.filter(AuditLog.actor == filters["actor"])
        
        # 篩選：date_from
        if filters.get("date_from"):
            query = query.filter(AuditLog.created_at >= filters["date_from"])
        
        # 篩選：date_to
        if filters.get("date_to"):
            query = query.filter(AuditLog.created_at <= filters["date_to"])
        
        # 篩選：關鍵字搜尋
        if filters.get("q"):
            keyword = f"%{filters['q']}%"
            query = query.filter(
                or_(
                    AuditLog.action.ilike(keyword),
                    AuditLog.actor.ilike(keyword),
                    AuditLog.error.ilike(keyword),
                    cast(AuditLog.meta, String).ilike(keyword)
                )
            )
        
        # 排序（allowlist）
        if sort.startswith("-"):
            sort_field = sort[1:]
            if sort_field == "created_at":
                query = query.order_by(desc(AuditLog.created_at))
            elif sort_field == "action":
                query = query.order_by(desc(AuditLog.action))
            else:
                query = query.order_by(desc(AuditLog.created_at))
        else:
            if sort == "created_at":
                query = query.order_by(asc(AuditLog.created_at))
            elif sort == "action":
                query = query.order_by(asc(AuditLog.action))
            else:
                query = query.order_by(desc(AuditLog.created_at))
        
        # 限制筆數
        items = query.limit(limit).all()
        
        return items
    
    # ==================== Phase 8: Retention Policy ====================
    
    def get_retention_policy(self, company_id: str) -> Optional[AuditRetentionPolicy]:
        """取得 retention policy
        
        Args:
            company_id: 公司 ID
        
        Returns:
            Optional[AuditRetentionPolicy]: Retention policy（若不存在回傳 None）
        """
        return self.db.query(AuditRetentionPolicy).filter(
            AuditRetentionPolicy.company_id == company_id
        ).first()
    
    def upsert_retention_policy(
        self,
        company_id: str,
        retention_days: int
    ) -> AuditRetentionPolicy:
        """新增或更新 retention policy
        
        Args:
            company_id: 公司 ID
            retention_days: 保留天數（7 ~ 3650）
        
        Returns:
            AuditRetentionPolicy: Retention policy
        """
        policy = self.get_retention_policy(company_id)
        
        if policy:
            # 更新
            policy.retention_days = retention_days
            policy.updated_at = datetime.utcnow()
            logger.info(f"更新 retention policy: company_id={company_id}, retention_days={retention_days}")
        else:
            # 新增
            policy = AuditRetentionPolicy(
                company_id=company_id,
                retention_days=retention_days
            )
            self.db.add(policy)
            logger.info(f"建立 retention policy: company_id={company_id}, retention_days={retention_days}")
        
        self.db.commit()
        self.db.refresh(policy)
        
        return policy
    
    def count_purgeable_logs(
        self,
        company_id: str,
        cutoff_date: datetime
    ) -> int:
        """計算可刪除的 audit logs 筆數
        
        Args:
            company_id: 公司 ID
            cutoff_date: 截止日期（created_at < cutoff_date 的紀錄可刪除）
        
        Returns:
            int: 可刪除筆數
        """
        count = self.db.query(AuditLog).filter(
            AuditLog.company_id == company_id,
            AuditLog.created_at < cutoff_date
        ).count()
        
        return count
    
    def delete_logs_batch(
        self,
        company_id: str,
        cutoff_date: datetime,
        batch_size: int
    ) -> int:
        """刪除一批 audit logs
        
        Args:
            company_id: 公司 ID
            cutoff_date: 截止日期
            batch_size: 批次大小
        
        Returns:
            int: 實際刪除筆數
        """
        # 查詢要刪除的 IDs（限制筆數）
        ids_to_delete = self.db.query(AuditLog.id).filter(
            AuditLog.company_id == company_id,
            AuditLog.created_at < cutoff_date
        ).limit(batch_size).all()
        
        # 提取 ID 列表
        ids = [row[0] for row in ids_to_delete]
        
        if not ids:
            return 0
        
        # 刪除
        stmt = delete(AuditLog).where(AuditLog.id.in_(ids))
        result = self.db.execute(stmt)
        self.db.commit()
        
        deleted_count = result.rowcount
        logger.info(
            f"刪除 audit logs: company_id={company_id}, "
            f"cutoff_date={cutoff_date}, deleted={deleted_count}"
        )
        
        return deleted_count


def get_audit_log_repository(db: Session) -> AuditLogRepository:
    """取得 AuditLogRepository 實例（FastAPI Dependency）
    
    Args:
        db: SQLAlchemy Session
    
    Returns:
        AuditLogRepository: Repository 實例
    """
    return AuditLogRepository(db)
