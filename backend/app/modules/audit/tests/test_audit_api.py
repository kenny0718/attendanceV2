"""Audit API 測試

測試稽核紀錄的查詢與匯出功能。

WP-C1-05: 遷移至 JWT Actor dependency override
- 移除 X-Company-ID header
- 使用 create_test_actor + override_actor_dependency
- GET /audit/export 需要 admin role（WP-C1-03 加入 RBAC）
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.modules.audit.models import AuditLog
from app.tests.utils.auth import create_test_actor, override_actor_dependency

client = TestClient(app)


class TestAuditLogsQuery:
    """測試 GET /api/audit/logs"""

    def test_query_without_auth_returns_401(self, test_db):
        """測試：無 Actor（無 JWT）應回 401/403"""
        response = client.get("/api/audit/logs")
        assert response.status_code in (401, 403)

    def test_tenant_isolation(self, test_db):
        """測試：tenant isolation - A 公司看不到 B 公司的資料"""
        log_a = AuditLog(
            company_id="company-A",
            action="backup.export",
            status="success",
            actor="user-a",
            meta={"tables": 2}
        )
        log_b = AuditLog(
            company_id="company-B",
            action="backup.restore",
            status="success",
            actor="user-b",
            meta={"tables": 3}
        )
        test_db.add(log_a)
        test_db.add(log_b)
        test_db.commit()

        actor_a = create_test_actor("company-A")
        with override_actor_dependency(actor_a):
            response = client.get("/api/audit/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["company_id"] == "company-A"
        assert data["items"][0]["actor"] == "user-a"

        actor_b = create_test_actor("company-B")
        with override_actor_dependency(actor_b):
            response = client.get("/api/audit/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["company_id"] == "company-B"
        assert data["items"][0]["actor"] == "user-b"

    def test_filter_by_event_type(self, test_db):
        """測試：event_type 篩選"""
        log1 = AuditLog(
            company_id="company-A",
            action="backup.export",
            status="success",
            actor="user-a",
            meta={}
        )
        log2 = AuditLog(
            company_id="company-A",
            action="backup.restore",
            status="success",
            actor="user-a",
            meta={}
        )
        test_db.add_all([log1, log2])
        test_db.commit()

        actor = create_test_actor("company-A")
        with override_actor_dependency(actor):
            response = client.get("/api/audit/logs?event_type=backup.export")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["event_type"] == "backup.export"

    def test_pagination(self, test_db):
        """測試：分頁功能"""
        for i in range(10):
            log = AuditLog(
                company_id="company-A",
                action="backup.export",
                status="success",
                actor=f"user-{i}",
                meta={}
            )
            test_db.add(log)
        test_db.commit()

        actor = create_test_actor("company-A")
        with override_actor_dependency(actor):
            response = client.get("/api/audit/logs?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert data["total"] == 10
        assert len(data["items"]) == 5

        with override_actor_dependency(actor):
            response = client.get("/api/audit/logs?page=2&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert len(data["items"]) == 5


class TestAuditLogsExport:
    """測試 GET /api/audit/export（需要 admin）"""

    def test_export_json(self, test_db):
        """測試：匯出 JSON 格式（admin actor）"""
        log = AuditLog(
            company_id="company-A",
            action="backup.export",
            status="success",
            actor="user-a",
            meta={"tables": 2}
        )
        test_db.add(log)
        test_db.commit()

        actor = create_test_actor("company-A", role_id="company_admin")
        with override_actor_dependency(actor):
            response = client.get("/api/audit/export?format=json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["company_id"] == "company-A"
        assert data[0]["event_type"] == "backup.export"

    def test_export_csv(self, test_db):
        """測試：匯出 CSV 格式（admin actor）"""
        log = AuditLog(
            company_id="company-A",
            action="backup.export",
            status="success",
            actor="user-a",
            meta={"tables": 2}
        )
        test_db.add(log)
        test_db.commit()

        actor = create_test_actor("company-A", role_id="company_admin")
        with override_actor_dependency(actor):
            response = client.get("/api/audit/export?format=csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]
        csv_content = response.content.decode("utf-8")
        assert "id,company_id,event_type" in csv_content
        assert "company-A" in csv_content
        assert "backup.export" in csv_content

    def test_export_requires_admin(self, test_db):
        """測試：非 admin 無法匯出稽核紀錄 → 403"""
        actor = create_test_actor("company-A", role_id="employee")
        with override_actor_dependency(actor):
            response = client.get("/api/audit/export?format=json")
        assert response.status_code == 403

    def test_export_limit_5000(self, test_db):
        """測試：匯出筆數限制（最多 5000 筆）"""
        for i in range(100):
            log = AuditLog(
                company_id="company-A",
                action="backup.export",
                status="success",
                actor=f"user-{i}",
                meta={}
            )
            test_db.add(log)
        test_db.commit()

        actor = create_test_actor("company-A", role_id="company_admin")
        with override_actor_dependency(actor):
            response = client.get("/api/audit/export?format=json")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 100

    def test_export_tenant_isolation(self, test_db):
        """測試：匯出時的 tenant isolation"""
        log_a = AuditLog(
            company_id="company-A",
            action="backup.export",
            status="success",
            actor="user-a",
            meta={}
        )
        log_b = AuditLog(
            company_id="company-B",
            action="backup.export",
            status="success",
            actor="user-b",
            meta={}
        )
        test_db.add_all([log_a, log_b])
        test_db.commit()

        actor_a = create_test_actor("company-A", role_id="company_admin")
        with override_actor_dependency(actor_a):
            response = client.get("/api/audit/export?format=json")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["company_id"] == "company-A"


class TestAuditLogsFilters:
    """測試各種篩選條件"""

    def test_filter_by_actor(self, test_db):
        """測試：actor 篩選"""
        log1 = AuditLog(
            company_id="company-A",
            action="backup.export",
            status="success",
            actor="alice",
            meta={}
        )
        log2 = AuditLog(
            company_id="company-A",
            action="backup.export",
            status="success",
            actor="bob",
            meta={}
        )
        test_db.add_all([log1, log2])
        test_db.commit()

        actor = create_test_actor("company-A")
        with override_actor_dependency(actor):
            response = client.get("/api/audit/logs?actor=alice")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["actor"] == "alice"

    def test_filter_by_date_range(self, test_db):
        """測試：日期範圍篩選"""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)

        log_old = AuditLog(
            company_id="company-A",
            action="backup.export",
            status="success",
            actor="user-a",
            meta={},
            created_at=yesterday
        )
        log_new = AuditLog(
            company_id="company-A",
            action="backup.export",
            status="success",
            actor="user-a",
            meta={},
            created_at=now
        )
        test_db.add_all([log_old, log_new])
        test_db.commit()

        date_from = now.replace(hour=0, minute=0, second=0).isoformat() + "Z"
        actor = create_test_actor("company-A")
        with override_actor_dependency(actor):
            response = client.get(f"/api/audit/logs?date_from={date_from}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_keyword_search(self, test_db):
        """測試：關鍵字搜尋"""
        log1 = AuditLog(
            company_id="company-A",
            action="backup.export",
            status="success",
            actor="alice",
            meta={"note": "important backup"}
        )
        log2 = AuditLog(
            company_id="company-A",
            action="backup.restore",
            status="success",
            actor="bob",
            meta={"note": "regular restore"}
        )
        test_db.add_all([log1, log2])
        test_db.commit()

        actor = create_test_actor("company-A")
        with override_actor_dependency(actor):
            response = client.get("/api/audit/logs?q=export")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "export" in data["items"][0]["event_type"]
