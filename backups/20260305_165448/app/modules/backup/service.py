"""Backup 服務層"""

import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.modules.backup.exporter import BackupExporter
from app.modules.backup.importer import BackupImporter
from app.modules.backup.validator import BackupValidator

logger = logging.getLogger(__name__)


class BackupService:
    """備份服務"""
    
    def __init__(self, db: Session):
        """初始化服務
        
        Args:
            db: SQLAlchemy Session
        """
        self.db = db
        self.exporter = BackupExporter(db)
        self.importer = BackupImporter(db)
    
    def export_company(self, company_id: str) -> Dict[str, Any]:
        """匯出公司資料
        
        Args:
            company_id: 公司 ID
        
        Returns:
            Dict: 備份資料（JSON 格式）
        """
        logger.info(f"[Service] 匯出公司資料: company_id={company_id}")
        
        backup_data = self.exporter.export_company_data(company_id)
        
        logger.info(
            f"[Service] 匯出完成: "
            f"tables={len(backup_data['data'])}, "
            f"version={backup_data['metadata']['version']}"
        )
        
        return backup_data
    
    def restore_company(
        self,
        target_company_id: str,
        backup_data: Dict[str, Any],
        clear_existing: bool = False
    ) -> Dict[str, Any]:
        """還原公司資料
        
        流程：
        1. 驗證備份檔（格式、Consistency、FK Closure）
        2. 還原資料（覆寫 company_id）
        3. 回傳統計
        
        Args:
            target_company_id: 目標公司 ID
            backup_data: 備份資料
            clear_existing: 是否清空現有資料
        
        Returns:
            Dict: 還原結果
        
        Raises:
            ValueError: 驗證失敗
            Exception: 還原失敗
        """
        logger.info(
            f"[Service] 還原公司資料: target_company_id={target_company_id}, "
            f"clear_existing={clear_existing}"
        )
        
        # 步驟 1: 驗證備份檔
        BackupValidator.validate_for_restore(backup_data)
        
        # 步驟 2: 還原資料
        summary = self.importer.restore_company_data(
            target_company_id=target_company_id,
            backup_data=backup_data,
            clear_existing=clear_existing
        )
        
        logger.info(f"[Service] 還原完成: summary={summary}")
        
        return {
            "ok": True,
            "target_company_id": target_company_id,
            "summary": summary
        }


def get_backup_service(db: Session) -> BackupService:
    """取得 BackupService 實例（FastAPI Dependency）
    
    Args:
        db: SQLAlchemy Session
    
    Returns:
        BackupService: 服務實例
    """
    return BackupService(db)
