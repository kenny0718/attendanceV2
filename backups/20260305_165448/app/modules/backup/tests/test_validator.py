"""Backup Validator 測試

測試：
- Company Consistency Check（P0）
- FK Closure Check（P0）
- 格式驗證
"""

import pytest
from app.modules.backup.validator import BackupValidator


class TestBackupValidator:
    """備份檔驗證器測試"""
    
    def test_validate_backup_format_success(self):
        """測試：正確的備份檔格式"""
        backup_data = {
            "metadata": {
                "company_id": "company-test",
                "exported_at": "2026-01-14T12:00:00.000000Z",
                "version": "1.0"
            },
            "data": {
                "notifications": []
            }
        }
        
        # 應該不拋出錯誤
        BackupValidator.validate_backup_format(backup_data)
    
    def test_validate_backup_format_missing_metadata(self):
        """測試：缺少 metadata"""
        backup_data = {
            "data": {}
        }
        
        with pytest.raises(ValueError) as exc_info:
            BackupValidator.validate_backup_format(backup_data)
        
        assert "metadata" in str(exc_info.value)
    
    def test_validate_backup_format_missing_data(self):
        """測試：缺少 data"""
        backup_data = {
            "metadata": {
                "company_id": "test",
                "exported_at": "2026-01-14T12:00:00Z",
                "version": "1.0"
            }
        }
        
        with pytest.raises(ValueError) as exc_info:
            BackupValidator.validate_backup_format(backup_data)
        
        assert "data" in str(exc_info.value)
    
    def test_company_consistency_check_success(self):
        """測試：Company Consistency Check 通過"""
        backup_data = {
            "metadata": {
                "company_id": "company-A"
            },
            "data": {
                "notifications": [
                    {"company_id": "company-A", "data": "test1"},
                    {"company_id": "company-A", "data": "test2"}
                ]
            }
        }
        
        # 應該不拋出錯誤
        BackupValidator.check_company_consistency(backup_data)
    
    def test_company_consistency_check_mixed_company_ids(self):
        """測試：備份檔混入多個 company_id → fail fast（P0）"""
        backup_data = {
            "metadata": {
                "company_id": "company-A"
            },
            "data": {
                "notifications": [
                    {"company_id": "company-A", "data": "test1"},
                    {"company_id": "company-B", "data": "test2"}  # 混入 B 公司
                ]
            }
        }
        
        with pytest.raises(ValueError) as exc_info:
            BackupValidator.check_company_consistency(backup_data)
        
        assert "多個 company_id" in str(exc_info.value)
        assert "Tenant Isolation" in str(exc_info.value)
    
    def test_company_consistency_check_mismatch_metadata(self):
        """測試：data 的 company_id 與 metadata 不一致 → fail fast"""
        backup_data = {
            "metadata": {
                "company_id": "company-A"
            },
            "data": {
                "notifications": [
                    {"company_id": "company-B", "data": "test"}  # 與 metadata 不一致
                ]
            }
        }
        
        with pytest.raises(ValueError) as exc_info:
            BackupValidator.check_company_consistency(backup_data)
        
        assert "不一致" in str(exc_info.value)
    
    def test_company_consistency_check_empty_backup(self):
        """測試：空備份（無 Tenant Data）"""
        backup_data = {
            "metadata": {
                "company_id": "company-A"
            },
            "data": {
                "notifications": []  # 空資料
            }
        }
        
        # 應該不拋出錯誤（只是警告）
        BackupValidator.check_company_consistency(backup_data)
    
    def test_fk_closure_check_phase3(self):
        """測試：FK Closure Check（Phase 3 為 stub）"""
        backup_data = {
            "metadata": {"company_id": "test"},
            "data": {"notifications": []}
        }
        
        # Phase 3: 應該直接通過（無外鍵）
        BackupValidator.check_fk_closure(backup_data)
    
    def test_validate_for_restore_success(self):
        """測試：還原前完整驗證通過"""
        backup_data = {
            "metadata": {
                "company_id": "company-test",
                "exported_at": "2026-01-14T12:00:00Z",
                "version": "1.0"
            },
            "data": {
                "notifications": [
                    {"company_id": "company-test", "data": "test"}
                ]
            }
        }
        
        # 應該不拋出錯誤
        BackupValidator.validate_for_restore(backup_data)
    
    def test_validate_for_restore_fails_on_invalid_format(self):
        """測試：格式錯誤 → 驗證失敗"""
        backup_data = {
            "metadata": {}  # 缺少必要欄位
        }
        
        with pytest.raises(ValueError):
            BackupValidator.validate_for_restore(backup_data)
    
    def test_validate_for_restore_fails_on_mixed_companies(self):
        """測試：混入其他公司 → 驗證失敗（P0）"""
        backup_data = {
            "metadata": {
                "company_id": "company-A",
                "exported_at": "2026-01-14T12:00:00Z",
                "version": "1.0"
            },
            "data": {
                "notifications": [
                    {"company_id": "company-A"},
                    {"company_id": "company-B"}  # 混入
                ]
            }
        }
        
        with pytest.raises(ValueError) as exc_info:
            BackupValidator.validate_for_restore(backup_data)
        
        assert "多個 company_id" in str(exc_info.value)
