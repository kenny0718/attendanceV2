"""Backup 匯入器

負責將備份資料還原到指定 company_id。
"""

import logging
from datetime import datetime
from typing import Dict, Any
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


class BackupImporter:
    """備份匯入器"""
    
    def __init__(self, db: Session):
        """初始化匯入器
        
        Args:
            db: SQLAlchemy Session
        """
        self.db = db
    
    def restore_company_data(
        self,
        target_company_id: str,
        backup_data: Dict[str, Any],
        clear_existing: bool = False
    ) -> Dict[str, int]:
        """還原公司資料
        
        Tenant Isolation (P0):
        - 所有資料的 company_id 強制覆寫為 target_company_id
        - 不信任備份檔內的 company_id
        
        Args:
            target_company_id: 目標公司 ID
            backup_data: 備份資料
            clear_existing: 是否清空現有資料
        
        Returns:
            Dict[str, int]: 還原統計（各表筆數）
        """
        logger.info(
            f"開始還原公司資料: target_company_id={target_company_id}, "
            f"clear_existing={clear_existing}"
        )
        
        summary = {}
        
        # 步驟 1: 清空現有資料（如果需要）
        if clear_existing:
            self._clear_existing_data(target_company_id)
        
        # 步驟 2: 還原所有資料表
        for table_name, model_class in TENANT_DATA_TABLES.items():
            if table_name in backup_data["data"]:
                records = backup_data["data"][table_name]
                count = self._restore_table(
                    target_company_id,
                    table_name,
                    model_class,
                    records
                )
                summary[table_name] = count
                logger.info(f"  - {table_name}: {count} 筆")
            else:
                summary[table_name] = 0
        
        logger.info(f"還原完成: summary={summary}")
        
        return summary
    
    def _clear_existing_data(self, company_id: str) -> None:
        """清空指定公司的現有資料
        
        Tenant Isolation (P0):
        - 強制 WHERE company_id = ?
        
        Args:
            company_id: 公司 ID
        """
        logger.info(f"清空現有資料: company_id={company_id}")
        
        for table_name, model_class in TENANT_DATA_TABLES.items():
            deleted_count = (
                self.db.query(model_class)
                .filter(model_class.company_id == company_id)
                .delete()
            )
            logger.info(f"  - {table_name}: 刪除 {deleted_count} 筆")
        
        self.db.commit()
    
    def _restore_table(
        self,
        target_company_id: str,
        table_name: str,
        model_class: Any,
        records: list
    ) -> int:
        """還原單一資料表
        
        Tenant Isolation (P0):
        - 強制覆寫所有 company_id 為 target_company_id
        
        Args:
            target_company_id: 目標公司 ID
            table_name: 資料表名稱
            model_class: SQLAlchemy Model 類別
            records: 資料列表
        
        Returns:
            int: 還原筆數
        """
        for record_data in records:
            # 強制覆寫 company_id（Tenant Isolation P0）
            record_data["company_id"] = target_company_id
            
            # 轉換特殊類型
            record_data = self._convert_types(record_data)
            
            # 建立物件
            record = model_class(**record_data)
            self.db.add(record)
        
        self.db.commit()
        
        return len(records)
    
    def _convert_types(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """轉換資料類型
        
        處理：
        - str -> UUID
        - str -> datetime
        
        Args:
            record_data: 資料字典
        
        Returns:
            Dict: 轉換後的資料字典
        """
        result = {}
        
        for key, value in record_data.items():
            if value is None:
                result[key] = None
            # UUID 欄位（id）
            elif key == "id" and isinstance(value, str):
                result[key] = UUID(value)
            # datetime 欄位（created_at, approved_at）
            elif key in ["created_at", "approved_at"] and isinstance(value, str):
                # 移除尾部的 'Z'
                if value.endswith("Z"):
                    value = value[:-1]
                result[key] = datetime.fromisoformat(value)
            else:
                result[key] = value
        
        return result


def get_backup_importer(db: Session) -> BackupImporter:
    """取得 BackupImporter 實例（FastAPI Dependency）
    
    Args:
        db: SQLAlchemy Session
    
    Returns:
        BackupImporter: 匯入器實例
    """
    return BackupImporter(db)

