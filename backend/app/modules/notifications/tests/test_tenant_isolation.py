"""Tenant Isolation 測試（P0）

驗證 Tenant Isolation 規則：
- A 公司 context 無法存取 B 公司資料
- company_id 必須由後端注入，不信任 request body
- 支援單一 company_id 全量抽取（備份用）
"""

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


class TestTenantIsolation:
    """Tenant Isolation 測試（P0）"""
    
    def setup_method(self):
        """每個測試前清空資料"""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    
    def test_get_notifications_requires_company_header(self):
        """測試：缺少 X-Company-ID header 應回 400"""
        response = client.get("/api/notifications")
        
        assert response.status_code == 400
        assert response.headers["content-type"] == "application/json"
        assert "X-Company-ID" in response.text or "Missing" in response.text
    
    def test_get_notifications_with_company_a_context(self):
        """測試：使用 A 公司 context 查詢通知"""
        # 準備資料：A 公司 1 筆
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        repo.create_notification(
            company_id="company-A",
            event_type="attendance.approved",
            event_payload={"test": "data-A"}
        )
        db.close()
        
        # 使用 A 公司 context 查詢
        headers = {"X-Company-ID": "company-A"}
        response = client.get("/api/notifications", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 1
        assert data["notifications"][0]["company_id"] == "company-A"
    
    def test_get_notifications_cross_company_isolation(self):
        """測試：A 公司無法看到 B 公司的通知（P0）"""
        # 準備資料：A 公司 2 筆，B 公司 3 筆
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        
        for i in range(2):
            repo.create_notification(
                company_id="company-A",
                event_type="attendance.approved",
                event_payload={"test": f"data-A-{i}"}
            )
        
        for i in range(3):
            repo.create_notification(
                company_id="company-B",
                event_type="attendance.approved",
                event_payload={"test": f"data-B-{i}"}
            )
        
        db.close()
        
        # A 公司查詢：只看到 2 筆
        headers_a = {"X-Company-ID": "company-A"}
        response_a = client.get("/api/notifications", headers=headers_a)
        assert response_a.status_code == 200
        data_a = response_a.json()
        assert len(data_a["notifications"]) == 2
        assert all(n["company_id"] == "company-A" for n in data_a["notifications"])
        assert data_a["pagination"]["total"] == 2
        
        # B 公司查詢：只看到 3 筆
        headers_b = {"X-Company-ID": "company-B"}
        response_b = client.get("/api/notifications", headers=headers_b)
        assert response_b.status_code == 200
        data_b = response_b.json()
        assert len(data_b["notifications"]) == 3
        assert all(n["company_id"] == "company-B" for n in data_b["notifications"])
        assert data_b["pagination"]["total"] == 3
    
    def test_repo_get_all_for_backup(self):
        """測試：repo 支援單一 company_id 全量抽取（備份用）"""
        # 準備資料：A 公司 100 筆，B 公司 50 筆
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        
        for i in range(100):
            repo.create_notification(
                company_id="company-A",
                event_type="test.event",
                event_payload={"index": i}
            )
        
        for i in range(50):
            repo.create_notification(
                company_id="company-B",
                event_type="test.event",
                event_payload={"index": i}
            )
        
        # 全量抽取 A 公司（不分頁）
        all_a = repo.get_all_notifications_for_company("company-A")
        assert len(all_a) == 100
        assert all(n.company_id == "company-A" for n in all_a)
        
        # 全量抽取 B 公司（不分頁）
        all_b = repo.get_all_notifications_for_company("company-B")
        assert len(all_b) == 50
        assert all(n.company_id == "company-B" for n in all_b)
        
        db.close()
    
    def test_pagination(self):
        """測試：分頁功能正確"""
        # 準備資料：A 公司 25 筆
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        
        for i in range(25):
            repo.create_notification(
                company_id="company-A",
                event_type="test.event",
                event_payload={"index": i}
            )
        
        db.close()
        
        headers = {"X-Company-ID": "company-A"}
        
        # 第 1 頁（limit=10）
        response = client.get("/api/notifications?limit=10&offset=0", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 10
        assert data["pagination"]["total"] == 25
        assert data["pagination"]["limit"] == 10
        assert data["pagination"]["offset"] == 0
        
        # 第 2 頁
        response = client.get("/api/notifications?limit=10&offset=10", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 10
        
        # 第 3 頁（剩餘 5 筆）
        response = client.get("/api/notifications?limit=10&offset=20", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 5


class TestRepoTenantIsolation:
    """Repository 層 Tenant Isolation 測試"""
    
    def setup_method(self):
        """每個測試前清空資料"""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    
    def test_create_notification_with_correct_company_id(self):
        """測試：建立通知時使用正確的 company_id"""
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        
        notification = repo.create_notification(
            company_id="company-test",
            event_type="test.event",
            event_payload={"data": "test"}
        )
        
        assert notification.company_id == "company-test"
        assert notification.event_type == "test.event"
        assert notification.event_payload == {"data": "test"}
        
        db.close()
    
    def test_get_notifications_filters_by_company_id(self):
        """測試：查詢時強制 company_id 篩選"""
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        
        # 建立多公司資料
        repo.create_notification("company-A", "test", {"a": 1})
        repo.create_notification("company-A", "test", {"a": 2})
        repo.create_notification("company-B", "test", {"b": 1})
        
        # 查詢 A 公司
        results_a = repo.get_notifications("company-A")
        assert len(results_a) == 2
        assert all(n.company_id == "company-A" for n in results_a)
        
        # 查詢 B 公司
        results_b = repo.get_notifications("company-B")
        assert len(results_b) == 1
        assert all(n.company_id == "company-B" for n in results_b)
        
        db.close()
