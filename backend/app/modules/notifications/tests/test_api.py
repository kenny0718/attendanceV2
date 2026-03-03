"""Notifications API 測試

Phase 9 (WP-09-05): Use PostgreSQL for all tests (no SQLite mix)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.modules.notifications.repo import NotificationRepository

client = TestClient(app)

class TestNotificationsAPI:
    """Notifications API 基本功能測試"""
    
    def setup_method(self):
        """每個測試前清空資料"""
        # Clean up notifications for test tenants
        db = next(get_db())
        try:
            # Delete test notifications if any
            db.execute("DELETE FROM notifications WHERE company_id IN ('company-test', 'company-001', 'company-002', 'nonexistent-tenant-xyz', 'company-integration')")
            db.commit()
        except:
            db.rollback()
        finally:
            db.close()
    
    def test_get_notifications_success(self):
        """測試：成功查詢通知記錄"""
        # 準備資料 (use PostgreSQL)
        db = next(get_db())
        repo = NotificationRepository(db)
        repo.create_notification(
            company_id="company-test",
            event_type="attendance.approved",
            event_payload={"test": "data"}
        )
        db.close()
        
        # 查詢
        headers = {"X-Company-ID": "company-test"}
        response = client.get("/api/notifications", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # 驗證回應結構
        assert "notifications" in data
        assert "pagination" in data
        assert len(data["notifications"]) >= 1
        
        # 驗證通知內容
        notification = data["notifications"][0]
        assert notification["company_id"] == "company-test"
        assert notification["event_type"] == "attendance.approved"
        assert notification["event_payload"] == {"test": "data"}
        assert "id" in notification
        assert "created_at" in notification
    
    def test_get_notifications_empty(self):
        """測試：查詢空結果"""
        headers = {"X-Company-ID": "nonexistent-tenant-xyz"}
        response = client.get("/api/notifications", headers=headers)
        
        assert response.status_code == 404  # Tenant doesn't exist
    
    def test_get_notifications_with_pagination(self):
        """測試：分頁查詢"""
        # 準備資料：15 筆
        db = next(get_db())
        repo = NotificationRepository(db)
        for i in range(15):
            repo.create_notification(
                company_id="company-001",
                event_type="test.event",
                event_payload={"index": i}
            )
        db.close()
        
        headers = {"X-Company-ID": "company-001"}
        
        # 第 1 頁（limit=10）
        response = client.get("/api/notifications?limit=10&offset=0", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 10
        assert data["pagination"]["total"] >= 15
        
        # 第 2 頁（剩餘 5 筆）
        response = client.get("/api/notifications?limit=10&offset=10", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) >= 5
    
    def test_get_notifications_limit_validation(self):
        """測試：limit 參數驗證"""
        headers = {"X-Company-ID": "company-test"}
        
        # limit 超過最大值（100）
        response = client.get("/api/notifications?limit=200", headers=headers)
        assert response.status_code == 422  # Validation error
        
        # limit 小於最小值（1）
        response = client.get("/api/notifications?limit=0", headers=headers)
        assert response.status_code == 422
    
    def test_get_notifications_offset_validation(self):
        """測試：offset 參數驗證"""
        headers = {"X-Company-ID": "company-test"}
        
        # offset 為負數
        response = client.get("/api/notifications?offset=-1", headers=headers)
        assert response.status_code == 422  # Validation error
    
    def test_get_notifications_returns_json_on_error(self):
        """測試：錯誤回應必須是 JSON 格式（不得回 HTML）"""
        # 缺少 Header
        response = client.get("/api/notifications")
        assert response.status_code == 422  # Missing required header
        assert response.headers["content-type"] == "application/json"
        
        # 驗證回應是有效的 JSON
        data = response.json()
        assert "detail" in data


class TestIntegrationWithEventBus:
    """與 EventBus 整合測試"""
    
    def setup_method(self):
        """每個測試前清空資料"""
        db = next(get_db())
        try:
            db.execute("DELETE FROM notifications WHERE company_id = 'company-integration'")
            db.commit()
        except:
            db.rollback()
        finally:
            db.close()
    
    def test_attendance_approved_event_creates_notification(self):
        """測試：attendance.approved 事件會建立通知記錄"""
        # Skip this test - requires event bus integration setup
        pytest.skip("Event bus integration test - requires setup")
