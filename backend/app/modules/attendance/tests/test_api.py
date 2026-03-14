"""Attendance API 測試

Phase 9 (WP-09-05): 加入 tenant setup fixture
WP-C1-07: JWT Actor Migration - 使用 override_actor_dependency
"""

import pytest
from fastapi.testclient import TestClient
from uuid import UUID

from app.main import app
from app.core.database import get_db
from app.modules.tenants.repo import TenantRepository
from app.tests.utils.auth import create_test_actor, override_actor_dependency

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_test_tenant():
    """Setup test tenant for all tests in this module"""
    db = next(get_db())
    tenant_repo = TenantRepository(db)
    
    # Create test tenant if not exists
    if not tenant_repo.exists("company-test"):
        tenant_repo.create("company-test", "Test Company", is_active=True)
    
    yield
    
    # Cleanup is optional (tenant can persist across tests)


class TestAttendanceAPI:
    """Attendance API 基本功能測試"""
    
    def test_mock_create_attendance(self):
        """測試：建立假考勤記錄"""
        actor = create_test_actor("company-test")
        
        with override_actor_dependency(actor):
            response = client.post("/api/attendance/mock-create")
        
        assert response.status_code == 200
        data = response.json()
        assert "attendance_record_id" in data
        
        # 驗證回傳的是 UUID 格式
        record_id = data["attendance_record_id"]
        assert len(record_id) == 36  # UUID 格式長度
        assert record_id.count("-") == 4  # UUID 有 4 個 dash
    
    def test_approve_attendance_success(self):
        """測試：成功核准考勤記錄"""
        actor = create_test_actor("company-test")
        
        with override_actor_dependency(actor):
            # Step 1: Create a real attendance record first
            create_response = client.post("/api/attendance/mock-create")
            assert create_response.status_code == 200
            record_id = create_response.json()["attendance_record_id"]
            
            # Step 2: Approve the record
            response = client.post(
                f"/api/attendance/{record_id}/approve",
                json={
                    "employee_id": "emp-001",
                    "approved_by": "manager-001"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # 驗證回應結構
        assert data["ok"] is True
        assert "payload" in data
        
        # 驗證 payload 結構
        payload = data["payload"]
        assert payload["company_id"] == "company-test"
        assert payload["employee_id"] == "emp-001"
        assert payload["attendance_record_id"] == record_id
        assert "approved_at" in payload
        assert payload["approved_by"] == "manager-001"
        
        # 驗證 approved_at 是 ISO8601 格式
        assert "T" in payload["approved_at"]
        assert payload["approved_at"].endswith("Z")
    
    def test_approve_attendance_without_approved_by(self):
        """測試：核准考勤記錄（不提供 approved_by）"""
        actor = create_test_actor("company-test")
        
        with override_actor_dependency(actor):
            # Step 1: Create a real attendance record first
            create_response = client.post("/api/attendance/mock-create")
            assert create_response.status_code == 200
            record_id = create_response.json()["attendance_record_id"]
            
            # Step 2: Approve without approved_by
            response = client.post(
                f"/api/attendance/{record_id}/approve",
                json={
                    "employee_id": "emp-002"
                    # 不提供 approved_by
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        payload = data["payload"]
        
        # 應該自動使用 actor.user_id 作為 approved_by
        assert payload["approved_by"] == str(actor.user_id)
    
    def test_approve_attendance_missing_employee_id(self):
        """測試：缺少必填欄位 employee_id 應回 422"""
        actor = create_test_actor("company-test")
        
        with override_actor_dependency(actor):
            # Create a real record first
            create_response = client.post("/api/attendance/mock-create")
            assert create_response.status_code == 200
            record_id = create_response.json()["attendance_record_id"]
            
            response = client.post(
                f"/api/attendance/{record_id}/approve",
                json={
                    "approved_by": "manager-001"
                    # 缺少 employee_id
                }
            )
        
        assert response.status_code == 422  # Validation error


class TestEventEmission:
    """測試事件發出"""
    
    def test_approve_emits_event(self, caplog):
        """測試：核准考勤時應發出 attendance.approved 事件"""
        actor = create_test_actor("company-test")
        
        with override_actor_dependency(actor):
            # Step 1: Create a real attendance record first
            create_response = client.post("/api/attendance/mock-create")
            assert create_response.status_code == 200
            record_id = create_response.json()["attendance_record_id"]
            
            # Step 2: Approve and check event emission
            with caplog.at_level("INFO"):
                response = client.post(
                    f"/api/attendance/{record_id}/approve",
                    json={
                        "employee_id": "emp-004",
                        "approved_by": "manager-004"
                    }
                )
        
        assert response.status_code == 200
        
        # 檢查 log 中是否有事件發出的記錄
        log_messages = [record.message for record in caplog.records]
        assert any("準備發出事件 attendance.approved" in msg for msg in log_messages)
        assert any("事件 attendance.approved 已發出" in msg for msg in log_messages)
