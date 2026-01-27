"""Backup API 測試"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.notifications.repo import NotificationRepository
from app.modules.attendance.repo import AttendanceRepository

client = TestClient(app)

class TestBackupExportAPI:
    """Backup Export API 測試"""
    
    def setup_method(self):
        """每個測試前清空資料"""    
    def test_export_success(self, test_db):
        """測試：成功匯出"""
        # 準備資料
        db = test_db
        repo = NotificationRepository(db)
        repo.create_notification(
            company_id="company-test",
            event_type="test.event",
            event_payload={"test": "data"}
        )        
        # 匯出
        headers = {"X-Company-ID": "company-test"}
        response = client.post("/api/backup/export", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # 驗證 metadata
        assert "metadata" in data
        assert data["metadata"]["company_id"] == "company-test"
        assert "exported_at" in data["metadata"]
        assert data["metadata"]["version"] == "1.0"
        assert "tables" in data["metadata"]
        
        # 驗證 data
        assert "data" in data
        assert "notifications" in data["data"]
        assert len(data["data"]["notifications"]) == 1
        
        # 驗證資料內容
        notification = data["data"]["notifications"][0]
        assert notification["company_id"] == "company-test"
        assert notification["event_type"] == "test.event"
        assert notification["event_payload"] == {"test": "data"}
    
    def test_export_empty_company(self):
        """測試：匯出空公司（無資料）"""
        headers = {"X-Company-ID": "company-empty"}
        response = client.post("/api/backup/export", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # 應該回傳空資料
        assert data["metadata"]["company_id"] == "company-empty"
        assert len(data["data"]["notifications"]) == 0
    
    def test_export_returns_json_on_error(self):
        """測試：錯誤回應必須是 JSON"""
        # 缺少 Header
        response = client.post("/api/backup/export")
        
        assert response.status_code == 400
        assert response.headers["content-type"] == "application/json"

class TestBackupRestoreAPI:
    """Backup Restore API 測試"""
    
    def setup_method(self):
        """每個測試前清空資料"""    
    def test_restore_success(self):
        """測試：成功還原"""
        backup_data = {
            "metadata": {
                "company_id": "company-source",
                "exported_at": "2026-01-14T12:00:00Z",
                "version": "1.0"
            },
            "data": {
                "notifications": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "company_id": "company-source",
                        "event_type": "test",
                        "event_payload": {"test": "data"},
                        "created_at": "2026-01-14T10:00:00Z"
                    }
                ]
            }
        }
        
        # 還原
        headers = {"X-Company-ID": "company-target"}
        response = client.post(
            "/api/backup/restore",
            headers=headers,
            json=backup_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 驗證回應
        assert result["ok"] is True
        assert result["target_company_id"] == "company-target"
        assert "summary" in result
        assert result["summary"]["notifications"] == 1
    
    def test_restore_invalid_format(self):
        """測試：備份檔格式錯誤 → 400"""
        invalid_backup = {
            "invalid": "format"
        }
        
        headers = {"X-Company-ID": "company-test"}
        response = client.post(
            "/api/backup/restore",
            headers=headers,
            json=invalid_backup
        )
        
        assert response.status_code == 400
        assert response.headers["content-type"] == "application/json"
        assert "驗證失敗" in response.json()["detail"]
    
    def test_restore_mixed_company_ids(self):
        """測試：混入其他公司 → 400"""
        backup_data = {
            "metadata": {
                "company_id": "company-A",
                "exported_at": "2026-01-14T12:00:00Z",
                "version": "1.0"
            },
            "data": {
                "notifications": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "company_id": "company-A",
                        "event_type": "test",
                        "event_payload": {},
                        "created_at": "2026-01-14T10:00:00Z"
                    },
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440002",
                        "company_id": "company-B",  # 混入
                        "event_type": "test",
                        "event_payload": {},
                        "created_at": "2026-01-14T10:01:00Z"
                    }
                ]
            }
        }
        
        headers = {"X-Company-ID": "company-test"}
        response = client.post(
            "/api/backup/restore",
            headers=headers,
            json=backup_data
        )
        
        assert response.status_code == 400
        assert "多個 company_id" in response.json()["detail"]
    
    def test_restore_returns_json_on_error(self):
        """測試：所有錯誤回應必須是 JSON"""
        # 缺少 Header
        response = client.post(
            "/api/backup/restore",
            json={"metadata": {}, "data": {}}
        )
        
        assert response.status_code == 400
        assert response.headers["content-type"] == "application/json"

class TestBackupIntegration:
    """Backup 整合測試（Export → Restore）"""
    
    def setup_method(self):
        """每個測試前清空資料"""    
    def test_export_and_restore_roundtrip(self, test_db):
        """測試：匯出 → 還原 → 資料正確"""
        # 步驟 1: 準備原始資料
        db = test_db
        repo = NotificationRepository(db)
        
        for i in range(5):
            repo.create_notification(
                company_id="company-source",
                event_type=f"event-{i}",
                event_payload={"index": i}
            )        
        # 步驟 2: 匯出
        headers_source = {"X-Company-ID": "company-source"}
        export_response = client.post("/api/backup/export", headers=headers_source)
        assert export_response.status_code == 200
        backup_data = export_response.json()
        
        # 步驟 3: 還原到新公司
        headers_target = {"X-Company-ID": "company-target"}
        restore_response = client.post(
            "/api/backup/restore",
            headers=headers_target,
            json=backup_data
        )
        assert restore_response.status_code == 200
        
        # 步驟 4: 驗證資料
        db = test_db
        repo = NotificationRepository(db)
        
        # 目標公司有 5 筆資料
        notifications = repo.get_notifications("company-target", limit=100)
        assert len(notifications) == 5
        
        # 所有資料的 company_id 都是 target
        for n in notifications:
            assert n.company_id == "company-target"
        
        # 事件類型正確
        event_types = {n.event_type for n in notifications}
        assert event_types == {f"event-{i}" for i in range(5)}

class TestBackupAttendanceRecordsAPI:
    """Backup API 測試（Attendance Records，Phase 5）"""
    
    def setup_method(self):
        """每個測試前清空資料"""    
    def test_export_includes_attendance_records(self, test_db):
        """測試：匯出包含 attendance_records"""
        # 準備資料
        db = test_db
        attendance_repo = AttendanceRepository(db)
        
        attendance_repo.create_attendance_record(
            company_id="company-test",
            employee_id="emp-001"
        )        
        # 匯出
        headers = {"X-Company-ID": "company-test"}
        response = client.post("/api/backup/export", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # 驗證：包含 attendance_records
        assert "attendance_records" in data["data"]
        assert len(data["data"]["attendance_records"]) == 1
        
        # 驗證資料內容
        record = data["data"]["attendance_records"][0]
        assert record["company_id"] == "company-test"
        assert record["employee_id"] == "emp-001"
        assert "id" in record
        assert "created_at" in record
    
    def test_restore_attendance_records_success(self):
        """測試：成功還原 attendance_records"""
        backup_data = {
            "metadata": {
                "company_id": "company-source",
                "exported_at": "2026-01-27T12:00:00Z",
                "version": "1.0"
            },
            "data": {
                "attendance_records": [
                    {
                        "id": "660e8400-e29b-41d4-a716-446655440001",
                        "company_id": "company-source",
                        "employee_id": "emp-001",
                        "approved_by": "manager-001",
                        "approved_at": "2026-01-27T11:00:00Z",
                        "created_at": "2026-01-27T10:00:00Z"
                    }
                ]
            }
        }
        
        # 還原
        headers = {"X-Company-ID": "company-target"}
        response = client.post(
            "/api/backup/restore",
            headers=headers,
            json=backup_data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # 驗證回應
        assert result["ok"] is True
        assert result["target_company_id"] == "company-target"
        assert "attendance_records" in result["summary"]
        assert result["summary"]["attendance_records"] == 1
    
    def test_export_and_restore_attendance_records_roundtrip(self, test_db):
        """測試：attendance_records 匯出 → 還原 → 資料正確"""
        # 步驟 1: 準備原始資料
        db = test_db
        attendance_repo = AttendanceRepository(db)
        
        for i in range(3):
            attendance_repo.create_attendance_record(
                company_id="company-source",
                employee_id=f"emp-{i:03d}"
            )        
        # 步驟 2: 匯出
        headers_source = {"X-Company-ID": "company-source"}
        export_response = client.post("/api/backup/export", headers=headers_source)
        assert export_response.status_code == 200
        backup_data = export_response.json()
        
        # 步驟 3: 還原到新公司
        headers_target = {"X-Company-ID": "company-target"}
        restore_response = client.post(
            "/api/backup/restore",
            headers=headers_target,
            json=backup_data
        )
        assert restore_response.status_code == 200
        
        # 步驟 4: 驗證資料
        db = test_db
        attendance_repo = AttendanceRepository(db)
        
        # 目標公司有 3 筆資料
        records = db.query(attendance_repo.model).filter(
            attendance_repo.model.company_id == "company-target"
        ).all()
        assert len(records) == 3
        
        # 所有資料的 company_id 都是 target
        for record in records:
            assert record.company_id == "company-target"
        
        # employee_id 正確
        employee_ids = {r.employee_id for r in records}
        assert employee_ids == {f"emp-{i:03d}" for i in range(3)}