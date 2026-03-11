"""Phase 8: Audit Retention & Purge 測試

測試 retention policy 與 purge 功能。

WP-C1-05: 遷移至 JWT Actor dependency override
- 移除 X-Company-ID header
- 使用 create_test_actor + override_actor_dependency
- PUT /retention 與 POST /purge 需要 admin role（WP-C1-03 加入 RBAC）
- GET /retention 一般成員可存取
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.modules.audit.models import AuditLog, AuditRetentionPolicy
from app.modules.audit.repo import DEFAULT_RETENTION_DAYS
from app.tests.utils.auth import create_test_actor, override_actor_dependency


@pytest.fixture
def client():
    """測試客戶端"""
    return TestClient(app)


@pytest.fixture
def company_id():
    """測試公司 ID"""
    return "test-company-retention"


@pytest.fixture
def actor_str():
    """測試執行者字串（request body 用）"""
    return "test-admin"


class TestRetentionPolicy:
    """測試 Retention Policy"""

    def test_get_retention_without_auth_should_fail(self, client):
        """測試：無 Actor（無 JWT）應回 401/403"""
        response = client.get("/api/audit/retention")
        assert response.status_code in (401, 403)

    def test_get_retention_default(self, client, company_id):
        """測試：未設定 retention 應回傳預設值 365（一般成員可存取）"""
        actor = create_test_actor(company_id, role_id="employee")
        with override_actor_dependency(actor):
            response = client.get("/api/audit/retention")

        assert response.status_code == 200
        data = response.json()
        assert data["company_id"] == company_id
        assert data["retention_days"] == DEFAULT_RETENTION_DAYS
        assert data["is_default"] is True
        assert data["created_at"] is None
        assert data["updated_at"] is None

    def test_update_retention_success(self, client, company_id, actor_str):
        """測試：更新 retention 成功（admin actor）"""
        actor = create_test_actor(company_id, role_id="admin")
        with override_actor_dependency(actor):
            response = client.put(
                "/api/audit/retention",
                json={"retention_days": 180, "actor": actor_str}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["company_id"] == company_id
        assert data["retention_days"] == 180
        assert data["is_default"] is False
        assert data["created_at"] is not None
        assert data["updated_at"] is not None

    def test_update_retention_requires_admin(self, client, company_id, actor_str):
        """測試：非 admin 無法更新 retention → 403"""
        actor = create_test_actor(company_id, role_id="employee")
        with override_actor_dependency(actor):
            response = client.put(
                "/api/audit/retention",
                json={"retention_days": 180, "actor": actor_str}
            )
        assert response.status_code == 403

    def test_update_retention_out_of_range(self, client, company_id, actor_str):
        """測試：retention_days 超出範圍應失敗"""
        actor = create_test_actor(company_id, role_id="admin")

        with override_actor_dependency(actor):
            response = client.put(
                "/api/audit/retention",
                json={"retention_days": 5, "actor": actor_str}
            )
        assert response.status_code == 422

        with override_actor_dependency(actor):
            response = client.put(
                "/api/audit/retention",
                json={"retention_days": 4000, "actor": actor_str}
            )
        assert response.status_code == 422

    def test_update_retention_creates_audit_log(self, client, company_id, actor_str, test_db):
        """測試：更新 retention 應寫入 audit log"""
        actor = create_test_actor(company_id, role_id="admin")
        with override_actor_dependency(actor):
            response = client.put(
                "/api/audit/retention",
                json={"retention_days": 90, "actor": actor_str}
            )

        assert response.status_code == 200

        audit_log = test_db.query(AuditLog).filter(
            AuditLog.company_id == company_id,
            AuditLog.action == "audit.retention.update"
        ).order_by(AuditLog.created_at.desc()).first()

        assert audit_log is not None
        assert audit_log.actor == actor_str
        assert audit_log.status == "success"
        assert audit_log.meta["new_retention_days"] == 90


class TestPurge:
    """測試 Purge 功能"""

    def test_purge_without_auth_should_fail(self, client):
        """測試：無 Actor（無 JWT）應回 401/403"""
        response = client.post(
            "/api/audit/purge",
            json={"actor": "admin", "dry_run": True, "batch_size": 1000, "max_delete": 10000}
        )
        assert response.status_code in (401, 403)

    def test_purge_requires_admin(self, client, company_id, actor_str):
        """測試：非 admin 無法執行 purge → 403"""
        actor = create_test_actor(company_id, role_id="employee")
        with override_actor_dependency(actor):
            response = client.post(
                "/api/audit/purge",
                json={"actor": actor_str, "dry_run": True, "batch_size": 1000, "max_delete": 10000}
            )
        assert response.status_code == 403

    def test_purge_dry_run_does_not_delete(self, client, company_id, actor_str, test_db):
        """測試：dry_run 不應實際刪除資料"""
        old_date = datetime.utcnow() - timedelta(days=400)
        for i in range(5):
            log = AuditLog(
                company_id=company_id,
                action="test.action",
                status="success",
                actor="test-user",
                created_at=old_date
            )
            test_db.add(log)
        test_db.commit()

        original_count = test_db.query(AuditLog).filter(
            AuditLog.company_id == company_id
        ).count()

        actor = create_test_actor(company_id, role_id="admin")
        with override_actor_dependency(actor):
            response = client.post(
                "/api/audit/purge",
                json={"actor": actor_str, "dry_run": True, "batch_size": 1000, "max_delete": 10000}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["dry_run"] is True
        assert data["deleted_count"] >= 5
        assert data["batches_executed"] == 0

        old_logs_count = test_db.query(AuditLog).filter(
            AuditLog.company_id == company_id,
            AuditLog.actor == "test-user"
        ).count()
        assert old_logs_count == 5

        current_count = test_db.query(AuditLog).filter(
            AuditLog.company_id == company_id
        ).count()
        assert current_count >= original_count

    def test_purge_actually_deletes(self, client, company_id, actor_str, test_db):
        """測試：purge 實際刪除正確筆數"""
        old_date = datetime.utcnow() - timedelta(days=400)
        old_logs_count = 10
        for i in range(old_logs_count):
            log = AuditLog(
                company_id=company_id,
                action="test.old.action",
                status="success",
                actor="test-user",
                created_at=old_date
            )
            test_db.add(log)

        new_date = datetime.utcnow() - timedelta(days=30)
        new_logs_count = 5
        for i in range(new_logs_count):
            log = AuditLog(
                company_id=company_id,
                action="test.new.action",
                status="success",
                actor="test-user",
                created_at=new_date
            )
            test_db.add(log)
        test_db.commit()

        actor = create_test_actor(company_id, role_id="admin")
        with override_actor_dependency(actor):
            response = client.post(
                "/api/audit/purge",
                json={"actor": actor_str, "dry_run": False, "batch_size": 1000, "max_delete": 10000}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["dry_run"] is False
        assert data["deleted_count"] >= old_logs_count

        remaining_old = test_db.query(AuditLog).filter(
            AuditLog.company_id == company_id,
            AuditLog.action == "test.old.action"
        ).count()
        assert remaining_old == 0

        remaining_new = test_db.query(AuditLog).filter(
            AuditLog.company_id == company_id,
            AuditLog.action == "test.new.action"
        ).count()
        assert remaining_new == new_logs_count

    def test_purge_creates_audit_log(self, client, company_id, actor_str, test_db):
        """測試：purge 行為應寫入 audit log"""
        actor = create_test_actor(company_id, role_id="admin")
        with override_actor_dependency(actor):
            response = client.post(
                "/api/audit/purge",
                json={"actor": actor_str, "dry_run": True, "batch_size": 500, "max_delete": 5000}
            )

        assert response.status_code == 200

        audit_log = test_db.query(AuditLog).filter(
            AuditLog.company_id == company_id,
            AuditLog.action == "audit.purge"
        ).order_by(AuditLog.created_at.desc()).first()

        assert audit_log is not None
        assert audit_log.actor == actor_str
        assert audit_log.status == "success"
        assert "cutoff_date" in audit_log.meta
        assert "deleted_count" in audit_log.meta
        assert audit_log.meta["dry_run"] is True
        assert audit_log.meta["batch_size"] == 500
        assert audit_log.meta["max_delete"] == 5000

    def test_purge_tenant_isolation(self, client, actor_str, test_db):
        """測試：purge 不應跨 tenant"""
        company_a = "company-A"
        company_b = "company-B"
        old_date = datetime.utcnow() - timedelta(days=400)

        for company in [company_a, company_b]:
            for i in range(5):
                log = AuditLog(
                    company_id=company,
                    action="test.action",
                    status="success",
                    actor="test-user",
                    created_at=old_date
                )
                test_db.add(log)
        test_db.commit()

        actor = create_test_actor(company_a, role_id="admin")
        with override_actor_dependency(actor):
            response = client.post(
                "/api/audit/purge",
                json={"actor": actor_str, "dry_run": False, "batch_size": 1000, "max_delete": 10000}
            )

        assert response.status_code == 200

        count_a = test_db.query(AuditLog).filter(
            AuditLog.company_id == company_a,
            AuditLog.action == "test.action"
        ).count()
        assert count_a == 0

        count_b = test_db.query(AuditLog).filter(
            AuditLog.company_id == company_b,
            AuditLog.action == "test.action"
        ).count()
        assert count_b == 5

    def test_purge_batch_size_out_of_range(self, client, company_id, actor_str):
        """測試：batch_size 超出範圍應失敗"""
        actor = create_test_actor(company_id, role_id="admin")
        with override_actor_dependency(actor):
            response = client.post(
                "/api/audit/purge",
                json={"actor": actor_str, "dry_run": True, "batch_size": 3000, "max_delete": 10000}
            )
        assert response.status_code == 422

    def test_purge_max_delete_out_of_range(self, client, company_id, actor_str):
        """測試：max_delete 超出範圍應失敗"""
        actor = create_test_actor(company_id, role_id="admin")
        with override_actor_dependency(actor):
            response = client.post(
                "/api/audit/purge",
                json={"actor": actor_str, "dry_run": True, "batch_size": 1000, "max_delete": 30000}
            )
        assert response.status_code == 422

    def test_purge_respects_custom_retention(self, client, company_id, actor_str, test_db):
        """測試：purge 應遵守自訂的 retention policy"""
        actor = create_test_actor(company_id, role_id="admin")

        with override_actor_dependency(actor):
            client.put(
                "/api/audit/retention",
                json={"retention_days": 30, "actor": actor_str}
            )

        old_date = datetime.utcnow() - timedelta(days=60)
        for i in range(5):
            log = AuditLog(
                company_id=company_id,
                action="test.old",
                status="success",
                actor="test-user",
                created_at=old_date
            )
            test_db.add(log)

        recent_date = datetime.utcnow() - timedelta(days=15)
        for i in range(5):
            log = AuditLog(
                company_id=company_id,
                action="test.recent",
                status="success",
                actor="test-user",
                created_at=recent_date
            )
            test_db.add(log)
        test_db.commit()

        with override_actor_dependency(actor):
            response = client.post(
                "/api/audit/purge",
                json={"actor": actor_str, "dry_run": False, "batch_size": 1000, "max_delete": 10000}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["retention_days"] == 30

        old_count = test_db.query(AuditLog).filter(
            AuditLog.company_id == company_id,
            AuditLog.action == "test.old"
        ).count()
        assert old_count == 0

        recent_count = test_db.query(AuditLog).filter(
            AuditLog.company_id == company_id,
            AuditLog.action == "test.recent"
        ).count()
        assert recent_count == 5
