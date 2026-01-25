"""Attendance API 測試"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestAttendanceAPI:
    """Attendance API 基本功能測試"""
    
    def test_mock_create_attendance(self):
        """測試：建立假考勤記錄"""
        headers = {"X-Company-ID": "company-test"}
        
        response = client.post(
            "/api/attendance/mock-create",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "attendance_record_id" in data
        
        # 驗證回傳的是 UUID 格式
        record_id = data["attendance_record_id"]
        assert len(record_id) == 36  # UUID 格式長度
        assert record_id.count("-") == 4  # UUID 有 4 個 dash
    
    def test_approve_attendance_success(self):
        """測試：成功核准考勤記錄"""
        headers = {"X-Company-ID": "company-test"}
        
        response = client.post(
            "/api/attendance/test-record-001/approve",
            headers=headers,
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
        assert payload["attendance_record_id"] == "test-record-001"
        assert "approved_at" in payload
        assert payload["approved_by"] == "manager-001"
        
        # 驗證 approved_at 是 ISO8601 格式
        assert "T" in payload["approved_at"]
        assert payload["approved_at"].endswith("Z")
    
    def test_approve_attendance_without_approved_by(self):
        """測試：核准考勤記錄（不提供 approved_by）"""
        headers = {
            "X-Company-ID": "company-test",
            "X-User-ID": "user-001"  # 提供 user_id，應該自動填入 approved_by
        }
        
        response = client.post(
            "/api/attendance/test-record-002/approve",
            headers=headers,
            json={
                "employee_id": "emp-002"
                # 不提供 approved_by
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        payload = data["payload"]
        
        # 應該自動使用 X-User-ID 作為 approved_by
        assert payload["approved_by"] == "user-001"
    
    def test_approve_attendance_missing_employee_id(self):
        """測試：缺少必填欄位 employee_id 應回 422"""
        headers = {"X-Company-ID": "company-test"}
        
        response = client.post(
            "/api/attendance/test-record-003/approve",
            headers=headers,
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
        headers = {"X-Company-ID": "company-test"}
        
        with caplog.at_level("INFO"):
            response = client.post(
                "/api/attendance/test-record-004/approve",
                headers=headers,
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
