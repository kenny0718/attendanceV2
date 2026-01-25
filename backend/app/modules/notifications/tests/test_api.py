"""Notifications API 測試"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.modules.notifications.repo import NotificationRepository

# 測試用資料庫（in-memory SQLite）
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆寫 get_db dependency（測試用）"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# 建立測試資料表
Base.metadata.create_all(bind=engine)

client = TestClient(app)


class TestNotificationsAPI:
    """Notifications API 基本功能測試"""
    
    def setup_method(self):
        """每個測試前清空資料"""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    
    def test_get_notifications_success(self):
        """測試：成功查詢通知記錄"""
        # 準備資料
        db = TestingSessionLocal()
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
        assert len(data["notifications"]) == 1
        
        # 驗證通知內容
        notification = data["notifications"][0]
        assert notification["company_id"] == "company-test"
        assert notification["event_type"] == "attendance.approved"
        assert notification["event_payload"] == {"test": "data"}
        assert "id" in notification
        assert "created_at" in notification
        
        # 驗證分頁資訊
        assert data["pagination"]["total"] == 1
        assert data["pagination"]["limit"] == 50
        assert data["pagination"]["offset"] == 0
    
    def test_get_notifications_empty(self):
        """測試：查詢空結果"""
        headers = {"X-Company-ID": "company-empty"}
        response = client.get("/api/notifications", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 0
        assert data["pagination"]["total"] == 0
    
    def test_get_notifications_with_pagination(self):
        """測試：分頁查詢"""
        # 準備資料：15 筆
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        for i in range(15):
            repo.create_notification(
                company_id="company-test",
                event_type="test.event",
                event_payload={"index": i}
            )
        db.close()
        
        headers = {"X-Company-ID": "company-test"}
        
        # 第 1 頁（limit=10）
        response = client.get("/api/notifications?limit=10&offset=0", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 10
        assert data["pagination"]["total"] == 15
        
        # 第 2 頁（剩餘 5 筆）
        response = client.get("/api/notifications?limit=10&offset=10", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 5
    
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
        assert response.status_code == 400
        assert response.headers["content-type"] == "application/json"
        
        # 驗證回應是有效的 JSON
        data = response.json()
        assert "detail" in data


class TestIntegrationWithEventBus:
    """與 EventBus 整合測試"""
    
    def setup_method(self):
        """每個測試前清空資料"""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        # 覆寫 SessionLocal（讓 event handler 使用測試 DB）
        import app.modules.notifications.event_handlers as handlers
        handlers.SessionLocal = TestingSessionLocal
    
    def test_attendance_approved_event_creates_notification(self):
        """測試：attendance.approved 事件會建立通知記錄"""
        from app.core.event_bus import get_event_bus
        
        event_bus = get_event_bus()
        
        # 發出事件
        payload = {
            "company_id": "company-integration",
            "employee_id": "emp-001",
            "attendance_record_id": "record-001",
            "approved_at": "2026-01-14T10:00:00.000000Z",
            "approved_by": "manager-001"
        }
        event_bus.emit("attendance.approved", payload)
        
        # 驗證：通知記錄已建立
        headers = {"X-Company-ID": "company-integration"}
        response = client.get("/api/notifications", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 1
        assert data["notifications"][0]["event_type"] == "attendance.approved"
        assert data["notifications"][0]["event_payload"] == payload
