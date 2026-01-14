"""Backup 驗證器

提供：
- Company Consistency Check（P0）
- FK Closure Check（P0）
"""

import logging
from typing import Dict, Any, Set

logger = logging.getLogger(__name__)


class BackupValidator:
    """備份檔驗證器"""
    
    @staticmethod
    def validate_backup_format(backup_data: Dict[str, Any]) -> None:
        """驗證備份檔格式
        
        Args:
            backup_data: 備份資料
        
        Raises:
            ValueError: 格式錯誤
        """
        # 檢查必要欄位
        if "metadata" not in backup_data:
            raise ValueError("備份檔缺少 metadata")
        
        if "data" not in backup_data:
            raise ValueError("備份檔缺少 data")
        
        metadata = backup_data["metadata"]
        
        # 檢查 metadata 必要欄位
        required_fields = ["company_id", "exported_at", "version"]
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"metadata 缺少必要欄位: {field}")
        
        logger.info(f"備份檔格式驗證通過: version={metadata['version']}")
    
    @staticmethod
    def check_company_consistency(backup_data: Dict[str, Any]) -> None:
        """Company Consistency Check（P0）
        
        檢查備份檔內的所有 company_id 是否一致：
        1. 所有 Tenant Data 的 company_id 必須相同
        2. 必須與 metadata.company_id 一致
        3. 不可混入其他公司資料
        
        Args:
            backup_data: 備份資料
        
        Raises:
            ValueError: Company Consistency 檢查失敗
        """
        metadata_company_id = backup_data["metadata"]["company_id"]
        company_ids: Set[str] = set()
        
        # 掃描所有資料表
        for table_name, records in backup_data["data"].items():
            if not isinstance(records, list):
                raise ValueError(f"資料表 {table_name} 格式錯誤（應為 list）")
            
            for idx, record in enumerate(records):
                if not isinstance(record, dict):
                    raise ValueError(f"資料表 {table_name}[{idx}] 格式錯誤（應為 dict）")
                
                # 檢查是否有 company_id（Tenant Data 必須有）
                if "company_id" in record:
                    company_ids.add(record["company_id"])
        
        # 檢查：不可為空
        if len(company_ids) == 0:
            logger.warning("備份檔不包含任何 Tenant Data（可能是空備份）")
            return
        
        # 檢查：只能有一個 company_id
        if len(company_ids) > 1:
            raise ValueError(
                f"備份檔包含多個 company_id（違反 Tenant Isolation）: {company_ids}"
            )
        
        # 檢查：必須與 metadata 一致
        backup_company_id = company_ids.pop()
        if backup_company_id != metadata_company_id:
            raise ValueError(
                f"備份檔 company_id 不一致: "
                f"metadata={metadata_company_id}, data={backup_company_id}"
            )
        
        logger.info(f"Company Consistency Check 通過: company_id={backup_company_id}")
    
    @staticmethod
    def check_fk_closure(backup_data: Dict[str, Any]) -> None:
        """FK Closure Check（P0）
        
        檢查外鍵閉包：所有被引用的資料必須存在於備份集內。
        
        Phase 3: notifications 表沒有外鍵，此為 stub 實作。
        Phase 4+: 當有外鍵時（例如 attendance_records.employee_id -> employees.id），
                 必須檢查所有被引用的 employee_id 都在 employees 表內。
        
        Args:
            backup_data: 備份資料
        
        Raises:
            ValueError: FK Closure 檢查失敗
        """
        # Phase 3: notifications 表沒有外鍵，直接通過
        logger.info("FK Closure Check 通過（Phase 3: 無外鍵）")
        
        # Phase 4+ 範例實作：
        # if "attendance_records" in backup_data["data"]:
        #     employee_ids_in_backup = {
        #         emp["id"] for emp in backup_data["data"].get("employees", [])
        #     }
        #     for record in backup_data["data"]["attendance_records"]:
        #         if record["employee_id"] not in employee_ids_in_backup:
        #             raise ValueError(
        #                 f"FK Closure 失敗: attendance_record 引用的 "
        #                 f"employee_id={record['employee_id']} 不在備份集內"
        #             )
    
    @staticmethod
    def validate_for_restore(backup_data: Dict[str, Any]) -> None:
        """還原前完整驗證
        
        執行所有必要的檢查：
        1. 格式驗證
        2. Company Consistency Check
        3. FK Closure Check
        
        Args:
            backup_data: 備份資料
        
        Raises:
            ValueError: 驗證失敗
        """
        logger.info("開始還原前驗證...")
        
        BackupValidator.validate_backup_format(backup_data)
        BackupValidator.check_company_consistency(backup_data)
        BackupValidator.check_fk_closure(backup_data)
        
        logger.info("還原前驗證全部通過")
