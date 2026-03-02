"""Phase 8: Audit Retention & Purge 測試

測試 retention policy 與 purge 功能。
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.modules.audit.models import AuditLog, AuditRetentionPolicy
from app.modules.audit.repo import DEFAULT_RETENTION_DAYS



@pytest.fixture
def client():
    """測試客戶端"""
    return TestClient(app)


@pytest.fixture
def company_id():
    """測試公司 ID"""
    return "test-company-retention"


@pytest.fixture
def actor():
    """測試執行者"""
    return "test-admin"


class TestRetentionPolicy:
    """測試 Retention Policy"""
    
    def test_get_retention_without_header_should_fail(self, client):
        """測試：缺少 X-Company-ID header 應該失敗"""
        response = client.get("/api/audit/retention")
        assert response.status_code == 422
    
    def test_get_retention_default(self, client, company_id):
        """測試：未設定 retention 應回傳預設值 365"""
        response = client.get(
            "/api/audit/retention",
            headers={"X-Company-ID": company_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["company_id"] == company_id
        assert data["retention_days"] == DEFAULT_RETENTION_DAYS
        assert data["is_default"] is True
        assert data["created_at"] is None
        assert data["updated_at"] is None
    
    def test_update_retention_success(self, client, company_id, actor):
        """測試：更新 retention 成功"""
        response = client.put(
            "/api/audit/retention",
            headers={"X-Company-ID": company_id},
            json={
                "retention_days": 180,
                "actor": actor
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["company_id"] == company_id
        assert data["retention_days"] == 180
        assert data["is_default"] is False
        assert data["created_at"] is not None
        assert data["updated_at"] is not None
    
    def test_update_retention_out_of_range(self, client, company_id, actor):
        """測試：retention_days 超出範圍應失敗"""
        # 小於 7
        response = client.put(
            "/api/audit/retention",
            headers={"X-Company-ID": company_id},
            json={
                "retention_days": 5,
                "actor": actor
            }
        )
        assert response.status_code == 422
        
        # 大於 3650
        response = client.put(
            "/api/audit/retention",
            headers={"X-Company-ID": company_id},
            json={
                "retention_days": 4000,
                "actor": actor
            }
        )
        assert response.status_code == 422
    
    def test_update_retention_creates_audit_log(self, client, company_id, actor, db: Session):
        """測試：更新 retention 應寫入 audit log"""
        # 更新 retention
        response = client.put(
            "/api/audit/retention",
            headers={"X-Company-ID": company_id},
            json={
                "retention_days": 90,
                "actor": actor
            }
        )
        
        assert response.status_code == 200
        
        # 檢查 audit log
        audit_log = db.query(AuditLog).filter(
            AuditLog.company_id == company_id,
            AuditLog.action == "audit.retention.update"
        ).order_by(AuditLog.created_at.desc()).first()
        
        assert audit_log is not None
        assert audit_log.actor == actor
        assert audit_log.status == "success"
        assert audit_log.meta["new_retention_days"] == 90


class TestPurge:
    """測試 Purge 功能"""
    
    def test_purge_without_header_should_fail(self, client):
        """測試：缺少 X-Company-ID header 應該失敗"""
        response = client.post(
            "/api/audit/purge",
            json={
                "actor": "admin",
                "dry_run": True,
                "batch_size": 1000,
                "max_delete": 10000
            }
        )
        assert response.status_code == 422
    
    def test_purge_dry_run_does_not_delete(self, client, company_id, actor, db: Session):
        """測試：dry_run 不應實際刪除資料"""
        # 建立一些舊的 audit logs
        old_date = datetime.utcnow() - timedelta(days=400)
        for i in range(5):
            log = AuditLog(
                company_id=company_id,
                action="test.action",
                status="success",
                actor="test-user",
                created_at=old_date
            )
            db.add(log)
        db.commit()
        
        # 記錄原始筆數
        original_count = db.query(AuditLog).filter(
            AuditLog.company_id == company_id
        ).count()
        
        # 執行 dry_run purge
        response = client.post(
            "/api/audit/purge",
            headers={"X-Company-ID": company_id},
            json={
                "actor": actor,
                "dry_run": True,
                "batch_size": 1000,
                "max_delete": 10000
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["dry_run"] is True
        assert data["deleted_count"] >= 5
        assert data["batches_executed"] == 0
        
        # 確認資料沒有被刪除
        current_count = db.query(AuditLog).filter(
            AuditLog.company_id == company_id
        ).count()
        assert current_count == original_count
    
    def test_purge_actually_deletes(self, client, company_id, actor, db: Session):
        """測試：purge 實際刪除正確筆數"""
        # 建立一些舊的 audit logs（超過預設 365 天）
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
            db.add(log)
        
        # 建立一些新的 audit logs（不應被刪除）
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
            db.add(log)
        
        db.commit()
        
        # 執行實際 purge
        response = client.post(
            "/api/audit/purge",
            headers={"X-Company-ID": company_id},
            json={
                "actor": actor,
                "dry_run": False,
                "batch_size": 1000,
                "max_delete": 10000
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["dry_run"] is False
        assert data["deleted_count"] >= old_logs_count
        
        # 確認舊資料被刪除
        remaining_old = db.query(AuditLog).filter(
            AuditLog.company_id == company_id,
            AuditLog.action == "test.old.action"
        ).count()
        assert remaining_old == 0
        
        # 確認新資料沒被刪除
        remaining_new = db.query(AuditLog).filter(
            AuditLog.company_id == company_id,
            AuditLog.action == "test.new.action"
        ).count()
        assert remaining_new == new_logs_count
    
    def test_purge_creates_audit_log(self, client, company_id, actor, db: Session):
        """測試：purge 行為應寫入 audit log"""
        # 執行 purge
        response = client.post(
            "/api/audit/purge",
            headers={"X-Company-ID": company_id},
            json={
                "actor": actor,
                "dry_run": True,
                "batch_size": 500,
                "max_delete": 5000
            }
        )
        
        assert response.status_code == 200
        
        # 檢查 audit log
        audit_log = db.query(AuditLog).filter(
            AuditLog.company_id == company_id,
            AuditLog.action == "audit.purge"
        ).order_by(AuditLog.created_at.desc()).first()
        
        assert audit_log is not None
        assert audit_log.actor == actor
        assert audit_log.status == "success"
        assert "cutoff_date" in audit_log.meta
        assert "deleted_count" in audit_log.meta
        assert audit_log.meta["dry_run"] is True
        assert audit_log.meta["batch_size"] == 500
        assert audit_log.meta["max_delete"] == 5000
    
    def test_purge_tenant_isolation(self, client, actor, db: Session):
        """測試：purge 不應跨 tenant"""
        company_a = "company-A-purge"
        company_b = "company-B-purge"
        
        # 為兩個公司建立舊資料
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
                db.add(log)
        db.commit()
        
        # 只 purge company_a
        response = client.post(
            "/api/audit/purge",
            headers={"X-Company-ID": company_a},
            json={
                "actor": actor,
                "dry_run": False,
                "batch_size": 1000,
                "max_delete": 10000
            }
        )
        
        assert response.status_code == 200
        
        # 確認 company_a 的資料被刪除
        count_a = db.query(AuditLog).filter(
            AuditLog.company_id == company_a,
            AuditLog.action == "test.action"
        ).count()
        assert count_a == 0
        
        # 確認 company_b 的資料沒被刪除
        count_b = db.query(AuditLog).filter(
            AuditLog.company_id == company_b,
            AuditLog.action == "test.action"
        ).count()
        assert count_b == 5
    
    def test_purge_batch_size_out_of_range(self, client, company_id, actor):
        """測試：batch_size 超出範圍應失敗"""
        # 超過 2000
        response = client.post(
            "/api/audit/purge",
            headers={"X-Company-ID": company_id},
            json={
                "actor": actor,
                "dry_run": True,
                "batch_size": 3000,
                "max_delete": 10000
            }
        )
        assert response.status_code == 422
    
    def test_purge_max_delete_out_of_range(self, client, company_id, actor):
        """測試：max_delete 超出範圍應失敗"""
        # 超過 20000
        response = client.post(
            "/api/audit/purge",
            headers={"X-Company-ID": company_id},
            json={
                "actor": actor,
                "dry_run": True,
                "batch_size": 1000,
                "max_delete": 30000
            }
        )
        assert response.status_code == 422
    
    def test_purge_respects_custom_retention(self, client, company_id, actor, db: Session):
        """測試：purge 應遵守自訂的 retention policy"""
        # 設定 retention 為 30 天
        client.put(
            "/api/audit/retention",
            headers={"X-Company-ID": company_id},
            json={
                "retention_days": 30,
                "actor": actor
            }
        )
        
        # 建立 60 天前的資料（應被刪除）
        old_date = datetime.utcnow() - timedelta(days=60)
        for i in range(5):
            log = AuditLog(
                company_id=company_id,
                action="test.old",
                status="success",
                actor="test-user",
                created_at=old_date
            )
            db.add(log)
        
        # 建立 15 天前的資料（不應被刪除）
        recent_date = datetime.utcnow() - timedelta(days=15)
        for i in range(5):
            log = AuditLog(
                company_id=company_id,
                action="test.recent",
                status="success",
                actor="test-user",
                created_at=recent_date
            )
            db.add(log)
        
        db.commit()
        
        # 執行 purge
        response = client.post(
            "/api/audit/purge",
            headers={"X-Company-ID": company_id},
            json={
                "actor": actor,
                "dry_run": False,
                "batch_size": 1000,
                "max_delete": 10000
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["retention_days"] == 30
        
        # 確認 60 天前的資料被刪除
        old_count = db.query(AuditLog).filter(
            AuditLog.company_id == company_id,
            AuditLog.action == "test.old"
        ).count()
        assert old_count == 0
        
        # 確認 15 天前的資料沒被刪除
        recent_count = db.query(AuditLog).filter(
            AuditLog.company_id == company_id,
            AuditLog.action == "test.recent"
        ).count()
        assert recent_count == 5

