"""Tenant Isolation 測試（P0）

驗證 Tenant Isolation 規則：
- A 公司 context 無法存取 B 公司資料
- company_id 必須由後端注入，不信任 request body
- 支援單一 company_id 全量抽取（備份用）

WP-C1-05: 遷移至 JWT Actor dependency override
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.notifications.repo import NotificationRepository
from app.tests.utils.auth import create_test_actor, override_actor_dependency

client = TestClient(app)


class TestTenantIsolation:
    """Tenant Isolation 測試（P0）"""

    def setup_method(self):
        """每個測試前清空資料"""

    def test_get_notifications_requires_auth(self):
        """測試：無 Actor（無 JWT）應回 401"""
        response = client.get("/api/notifications")
        assert response.status_code in (401, 403)

    def test_get_notifications_with_company_a_context(self):
        """測試：使用 A 公司 context 查詢通知"""
        from app.core.database import get_db
        db = next(get_db())
        repo = NotificationRepository(db)
        repo.create_notification(
            company_id="company-A",
            event_type="attendance.approved",
            event_payload={"test": "data-A"}
        )

        actor = create_test_actor("company-A")
        with override_actor_dependency(actor):
            response = client.get("/api/notifications")

        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 1
        assert data["notifications"][0]["company_id"] == "company-A"

    def test_get_notifications_cross_company_isolation(self):
        """測試：A 公司無法看到 B 公司的通知（P0）"""
        from app.core.database import get_db
        db = next(get_db())
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

        # A 公司查詢：只看到 2 筆
        actor_a = create_test_actor("company-A")
        with override_actor_dependency(actor_a):
            response_a = client.get("/api/notifications")
        assert response_a.status_code == 200
        data_a = response_a.json()
        assert len(data_a["notifications"]) == 2
        assert all(n["company_id"] == "company-A" for n in data_a["notifications"])
        assert data_a["pagination"]["total"] == 2

        # B 公司查詢：只看到 3 筆
        actor_b = create_test_actor("company-B")
        with override_actor_dependency(actor_b):
            response_b = client.get("/api/notifications")
        assert response_b.status_code == 200
        data_b = response_b.json()
        assert len(data_b["notifications"]) == 3
        assert all(n["company_id"] == "company-B" for n in data_b["notifications"])
        assert data_b["pagination"]["total"] == 3

    def test_repo_get_all_for_backup(self, test_db):
        """測試：repo 支援單一 company_id 全量抽取（備份用）"""
        db = test_db
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

        all_a = repo.get_all_notifications_for_company("company-A")
        assert len(all_a) == 100
        assert all(n.company_id == "company-A" for n in all_a)

        all_b = repo.get_all_notifications_for_company("company-B")
        assert len(all_b) == 50
        assert all(n.company_id == "company-B" for n in all_b)

    def test_pagination(self):
        """測試：分頁功能正確"""
        from app.core.database import get_db
        db = next(get_db())
        repo = NotificationRepository(db)

        for i in range(25):
            repo.create_notification(
                company_id="company-A",
                event_type="test.event",
                event_payload={"index": i}
            )

        actor = create_test_actor("company-A")

        with override_actor_dependency(actor):
            # 第 1 頁（limit=10）
            response = client.get("/api/notifications?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 10
        assert data["pagination"]["total"] == 25
        assert data["pagination"]["limit"] == 10
        assert data["pagination"]["offset"] == 0

        with override_actor_dependency(actor):
            response = client.get("/api/notifications?limit=10&offset=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 10

        with override_actor_dependency(actor):
            response = client.get("/api/notifications?limit=10&offset=20")
        assert response.status_code == 200
        data = response.json()
        assert len(data["notifications"]) == 5


class TestRepoTenantIsolation:
    """Repository 層 Tenant Isolation 測試"""

    def setup_method(self):
        """每個測試前清空資料"""

    def test_create_notification_with_correct_company_id(self, test_db):
        """測試：建立通知時使用正確的 company_id"""
        db = test_db
        repo = NotificationRepository(db)

        notification = repo.create_notification(
            company_id="company-test",
            event_type="test.event",
            event_payload={"data": "test"}
        )

        assert notification.company_id == "company-test"
        assert notification.event_type == "test.event"
        assert notification.event_payload == {"data": "test"}

    def test_get_notifications_filters_by_company_id(self, test_db):
        """測試：查詢時強制 company_id 篩選"""
        db = test_db
        repo = NotificationRepository(db)

        repo.create_notification("company-A", "test", {"a": 1})
        repo.create_notification("company-A", "test", {"a": 2})
        repo.create_notification("company-B", "test", {"b": 1})

        results_a = repo.get_notifications("company-A")
        assert len(results_a) == 2
        assert all(n.company_id == "company-A" for n in results_a)

        results_b = repo.get_notifications("company-B")
        assert len(results_b) == 1
        assert all(n.company_id == "company-B" for n in results_b)
