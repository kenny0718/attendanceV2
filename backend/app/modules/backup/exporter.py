"""Backup 匯出器

負責將指定 company_id 的資料匯出為 JSON 格式。
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from uuid import UUID

from app.modules.notifications.models import Notification
from app.modules.attendance.models import AttendanceRecord

logger = logging.getLogger(__name__)

# Phase 5: 支援的 Tenant Data 資料表
TENANT_DATA_TABLES = {
    "notifications": Notification,
    "attendance_records": AttendanceRecord,
}


class BackupExporter:
    """備份匯出器"""
    
    def __init__(self, db: Session):
        """初始化匯出器
        
        Args:
            db: SQLAlchemy Session
        """
        self.db = db
    
    def export_company_data(self, company_id: str) -> Dict[str, Any]:
        """匯出指定公司的所有資料
        
        Tenant Isolation (P0):
        - 所有查詢強制 WHERE company_id = ?
        - 只匯出指定公司的資料
        
        Args:
            company_id: 公司 ID
        
        Returns:
            Dict: 備份資料（JSON 格式）
        """
        logger.info(f"開始匯出公司資料: company_id={company_id}")
        
        # 組裝 metadata
        metadata = {
            "company_id": company_id,
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "version": "1.0",
            "tables": list(TENANT_DATA_TABLES.keys())
        }
        
        # 匯出所有資料表
        data = {}
        total_records = 0
        
        for table_name, model_class in TENANT_DATA_TABLES.items():
            records = self._export_table(company_id, table_name, model_class)
            data[table_name] = records
            total_records += len(records)
            logger.info(f"  - {table_name}: {len(records)} 筆")
        
        logger.info(f"匯出完成: 共 {total_records} 筆資料")
        
        return {
            "metadata": metadata,
            "data": data
        }
    
    def _export_table(
        self,
        company_id: str,
        table_name: str,
        model_class: Any
    ) -> List[Dict[str, Any]]:
        """匯出單一資料表
        
        Tenant Isolation (P0):
        - 強制 WHERE company_id = ?
        
        Args:
            company_id: 公司 ID
            table_name: 資料表名稱
            model_class: SQLAlchemy Model 類別
        
        Returns:
            List[Dict]: 資料列表
        """
        # 查詢資料（強制 company_id 篩選）
        records = (
            self.db.query(model_class)
            .filter(model_class.company_id == company_id)
            .order_by(model_class.created_at.asc())  # 按建立時間排序
            .all()
        )
        
        # 轉換為 dict
        return [self._record_to_dict(record) for record in records]
    
    def _record_to_dict(self, record: Any) -> Dict[str, Any]:
        """將 SQLAlchemy 物件轉換為 dict
        
        處理特殊類型：
        - UUID -> str
        - datetime -> ISO8601 str
        - JSONB -> dict（已是 dict，不需轉換）
        
        Args:
            record: SQLAlchemy 物件
        
        Returns:
            Dict: 資料字典
        """
        result = {}
        
        for column in record.__table__.columns:
            value = getattr(record, column.name)
            
            # 處理 UUID
            if isinstance(value, UUID):
                result[column.name] = str(value)
            # 處理 datetime
            elif isinstance(value, datetime):
                result[column.name] = value.isoformat() + "Z"
            # 其他類型直接使用
            else:
                result[column.name] = value
        
        return result


def get_backup_exporter(db: Session) -> BackupExporter:
    """取得 BackupExporter 實例（FastAPI Dependency）
    
    Args:
        db: SQLAlchemy Session
    
    Returns:
        BackupExporter: 匯出器實例
    """
    return BackupExporter(db)
