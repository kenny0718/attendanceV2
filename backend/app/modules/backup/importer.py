"""Backup 匯入器（還原器）

負責將備份資料還原到指定 company_id。
"""

import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.modules.notifications.models import Notification
from app.modules.attendance.models import AttendanceRecord

logger = logging.getLogger(__name__)

# Phase 5: 支援的 Tenant Data 資料表
TENANT_DATA_TABLES = {
    "notifications": Notification,
    "attendance_records": AttendanceRecord,
}


class BackupImporter:
    """備份匯入器（還原器）"""
    
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
        - 所有寫入的 company_id 強制覆寫為 target_company_id
        - 不信任備份檔內的 company_id
        
        Transaction:
        - 使用 transaction 確保原子性
        - 失敗時完整 rollback
        
        Args:
            target_company_id: 目標公司 ID（Source of Truth）
            backup_data: 備份資料
            clear_existing: 是否清空現有資料（預設 false）
        
        Returns:
            Dict[str, int]: 還原統計（各表還原筆數）
        
        Raises:
            Exception: 還原失敗（會自動 rollback）
        """
        logger.info(
            f"開始還原資料: target_company_id={target_company_id}, "
            f"clear_existing={clear_existing}"
        )
        
        summary = {}
        
        try:
            # 步驟 1: 清空現有資料（如果需要）
            if clear_existing:
                self._clear_existing_data(target_company_id)
            
            # 步驟 2: 還原資料
            for table_name, records in backup_data["data"].items():
                if table_name not in TENANT_DATA_TABLES:
                    logger.warning(f"跳過不支援的資料表: {table_name}")
                    continue
                
                count = self._restore_table(
                    target_company_id,
                    table_name,
                    records
                )
                summary[table_name] = count
                logger.info(f"  - {table_name}: 還原 {count} 筆")
            
            # 步驟 3: 提交 transaction
            self.db.commit()
            
            total = sum(summary.values())
            logger.info(f"還原完成: 共 {total} 筆資料")
            
            return summary
            
        except Exception as e:
            # 回滾 transaction
            self.db.rollback()
            logger.error(f"還原失敗，已回滾: {e}", exc_info=True)
            raise
    
    def _clear_existing_data(self, company_id: str) -> None:
        """清空指定公司的現有資料
        
        Tenant Isolation (P0):
        - 只刪除指定 company_id 的資料
        - 不影響其他公司
        
        Args:
            company_id: 公司 ID
        """
        logger.info(f"清空現有資料: company_id={company_id}")
        
        for table_name, model_class in TENANT_DATA_TABLES.items():
            deleted = (
                self.db.query(model_class)
                .filter(model_class.company_id == company_id)
                .delete()
            )
            logger.info(f"  - {table_name}: 刪除 {deleted} 筆")
    
    def _restore_table(
        self,
        target_company_id: str,
        table_name: str,
        records: list
    ) -> int:
        """還原單一資料表
        
        Tenant Isolation (P0):
        - 強制覆寫 company_id = target_company_id
        - 不信任備份檔內的 company_id
        
        UUID 處理:
        - 保留原始 UUID（避免衝突）
        
        Args:
            target_company_id: 目標公司 ID（Source of Truth）
            table_name: 資料表名稱
            records: 資料列表
        
        Returns:
            int: 還原筆數
        """
        model_class = TENANT_DATA_TABLES[table_name]
        count = 0
        
        for record in records:
            # 覆寫 company_id（Source of Truth）
            record["company_id"] = target_company_id
            
            # 轉換資料類型
            record_obj = self._dict_to_record(model_class, record)
            
            # 寫入資料庫
            self.db.add(record_obj)
            count += 1
        
        return count
    
    def _dict_to_record(self, model_class: Any, data: Dict[str, Any]) -> Any:
        """將 dict 轉換為 SQLAlchemy 物件
        
        處理特殊類型：
        - str -> UUID
        - str -> datetime
        
        Args:
            model_class: SQLAlchemy Model 類別
            data: 資料字典
        
        Returns:
            SQLAlchemy 物件
        """
        converted = {}
        
        for column in model_class.__table__.columns:
            column_name = column.name
            
            if column_name not in data:
                continue
            
            value = data[column_name]
            
            # 處理 UUID
            if column.type.python_type == UUID:
                converted[column_name] = UUID(value) if isinstance(value, str) else value
            # 處理 datetime
            elif column.type.python_type == datetime:
                if isinstance(value, str):
                    # 移除 'Z' 後綴並解析
                    value_str = value.rstrip('Z')
                    converted[column_name] = datetime.fromisoformat(value_str)
                else:
                    converted[column_name] = value
            # 其他類型直接使用
            else:
                converted[column_name] = value
        
        return model_class(**converted)


def get_backup_importer(db: Session) -> BackupImporter:
    """取得 BackupImporter 實例（FastAPI Dependency）
    
    Args:
        db: SQLAlchemy Session
    
    Returns:
        BackupImporter: 匯入器實例
    """
    return BackupImporter(db)
