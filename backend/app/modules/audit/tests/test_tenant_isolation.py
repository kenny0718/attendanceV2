"""WP-C1-05: Audit Module — Tenant Isolation 測試

驗證 Audit Log 的多租戶隔離：
1. Query Isolation — GET list 只回傳自己 company 的 logs
2. Repo Layer Isolation — 直接驗證 repo 查詢帶 company_id
3. Purge Isolation — purge 只影響自己 company 的資料
4. Retention Policy Isolation — retention policy 只存取自己 company

使用真實 PostgreSQL（app conftest.py test_db fixture）
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.modules.audit.models import AuditLog, AuditRetentionPolicy
from app.modules.tenants.models import Tenant
from app.modules.audit.repo import AuditLogRepository
from app.tests.utils.auth import create_test_actor, override_actor_dependency

client = TestClient(app)

COMPANY_A = "audit-iso-a"
COMPANY_B = "audit-iso-b"


# ============================================================
# Helpers
# ============================================================

def ensure_tenants(db):
    for cid, cname in [(COMPANY_A, "Audit Iso A"), (COMPANY_B, "Audit Iso B")]:
        if not db.query(Tenant).filter(Tenant.id == cid).first():
            db.add(Tenant(id=cid, name=cname, is_active=True))
    db.commit()


def make_audit_log(db, company_id, action="test.action", status="success", actor="user"):
    log = AuditLog(
        company_id=company_id,
        action=action,
        status=status,
        actor=actor,
        meta={}
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


# ============================================================
# 1️⃣  Query Isolation：GET /api/audit/logs
# ============================================================

class TestAuditQueryIsolation:
    """GET /api/audit/logs — 不得回傳其他 company 資料"""

    def test_list_logs_only_returns_own_company(self, test_db):
        """Company B 查詢 audit logs，不得看到 Company A 的記錄"""
        db = test_db
        ensure_tenants(db)

        # Company A 建立 3 筆 logs
        for i in range(3):
            make_audit_log(db, COMPANY_A, action=f"action.a.{i}", actor="user-a")
        # Company B 建立 2 筆 logs
        for i in range(2):
            make_audit_log(db, COMPANY_B, action=f"action.b.{i}", actor="user-b")

        # Company A 查詢：只看到 3 筆
        actor_a = create_test_actor(COMPANY_A)
        with override_actor_dependency(actor_a):
            resp = client.get("/api/audit/logs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        for item in data["items"]:
            assert item["company_id"] == COMPANY_A

        # Company B 查詢：只看到 2 筆
        actor_b = create_test_actor(COMPANY_B)
        with override_actor_dependency(actor_b):
            resp = client.get("/api/audit/logs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        for item in data["items"]:
            assert item["company_id"] == COMPANY_B

    def test_list_logs_requires_auth(self, test_db):
        """無 JWT actor → 401/403"""
        resp = client.get("/api/audit/logs")
        assert resp.status_code in (401, 403)

    def test_filter_event_type_scoped_to_company(self, test_db):
        """event_type 篩選仍只在自己 company 內搜尋"""
        db = test_db
        ensure_tenants(db)

        make_audit_log(db, COMPANY_A, action="backup.export", actor="user-a")
        make_audit_log(db, COMPANY_A, action="backup.restore", actor="user-a")
        make_audit_log(db, COMPANY_B, action="backup.export", actor="user-b")

        actor_a = create_test_actor(COMPANY_A)
        with override_actor_dependency(actor_a):
            resp = client.get("/api/audit/logs?event_type=backup.export")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["company_id"] == COMPANY_A
        assert data["items"][0]["event_type"] == "backup.export"


# ============================================================
# 2️⃣  Repo Layer Isolation
# ============================================================

class TestAuditRepoIsolation:
    """AuditLogRepository 直接驗證 company_id filter"""

    def test_list_logs_repo_enforces_company_id(self, test_db):
        """repo.list_logs 強制 company_id 隔離"""
        db = test_db
        ensure_tenants(db)

        for i in range(4):
            make_audit_log(db, COMPANY_A, actor=f"user-a-{i}")
        for i in range(2):
            make_audit_log(db, COMPANY_B, actor=f"user-b-{i}")

        repo = AuditLogRepository(db)

        items_a, total_a = repo.list_logs(
            company_id=COMPANY_A, filters={}, page=1, page_size=50, sort="-created_at"
        )
        assert total_a == 4
        assert all(item.company_id == COMPANY_A for item in items_a)

        items_b, total_b = repo.list_logs(
            company_id=COMPANY_B, filters={}, page=1, page_size=50, sort="-created_at"
        )
        assert total_b == 2
        assert all(item.company_id == COMPANY_B for item in items_b)

    def test_export_logs_repo_enforces_company_id(self, test_db):
        """repo.export_logs 強制 company_id 隔離"""
        db = test_db
        ensure_tenants(db)

        for i in range(5):
            make_audit_log(db, COMPANY_A)
        for i in range(3):
            make_audit_log(db, COMPANY_B)

        repo = AuditLogRepository(db)

        exported_a = repo.export_logs(company_id=COMPANY_A, filters={}, sort="-created_at")
        assert len(exported_a) == 5
        assert all(r.company_id == COMPANY_A for r in exported_a)

        exported_b = repo.export_logs(company_id=COMPANY_B, filters={}, sort="-created_at")
        assert len(exported_b) == 3
        assert all(r.company_id == COMPANY_B for r in exported_b)


# ============================================================
# 3️⃣  Purge Isolation：purge 只刪自己 company 的資料
# ============================================================

class TestAuditPurgeIsolation:
    """purge 操作只影響自己 company 的 audit logs"""

    def test_purge_dry_run_only_counts_own_company(self, test_db):
        """dry_run purge 計算只包含自己 company 的記錄"""
        db = test_db
        ensure_tenants(db)

        # 建立超過 retention 天數的舊記錄
        old_time = datetime.utcnow() - timedelta(days=400)

        for i in range(5):
            log = AuditLog(
                company_id=COMPANY_A,
                action="old.action",
                status="success",
                actor="user-a",
                meta={},
                created_at=old_time,
            )
            db.add(log)
        for i in range(3):
            log = AuditLog(
                company_id=COMPANY_B,
                action="old.action",
                status="success",
                actor="user-b",
                meta={},
                created_at=old_time,
            )
            db.add(log)
        db.commit()

        repo = AuditLogRepository(db)
        cutoff = datetime.utcnow() - timedelta(days=365)

        count_a = repo.count_purgeable_logs(COMPANY_A, cutoff)
        count_b = repo.count_purgeable_logs(COMPANY_B, cutoff)

        # 各自只計算自己的記錄
        assert count_a == 5
        assert count_b == 3

    def test_delete_logs_batch_only_deletes_own_company(self, test_db):
        """delete_logs_batch 只刪除自己 company 的記錄，不觸及其他 company"""
        db = test_db
        ensure_tenants(db)

        old_time = datetime.utcnow() - timedelta(days=400)
        cutoff = datetime.utcnow() - timedelta(days=365)

        for i in range(4):
            log = AuditLog(
                company_id=COMPANY_A, action="old",
                status="success", actor="user-a", meta={},
                created_at=old_time,
            )
            db.add(log)
        for i in range(3):
            log = AuditLog(
                company_id=COMPANY_B, action="old",
                status="success", actor="user-b", meta={},
                created_at=old_time,
            )
            db.add(log)
        db.commit()

        repo = AuditLogRepository(db)

        # 只刪 Company A 的舊記錄
        deleted = repo.delete_logs_batch(COMPANY_A, cutoff, batch_size=10)
        assert deleted == 4

        # Company B 的記錄完整保留
        remaining_b = db.query(AuditLog).filter(
            AuditLog.company_id == COMPANY_B
        ).count()
        assert remaining_b == 3


# ============================================================
# 4️⃣  Retention Policy Isolation
# ============================================================

class TestAuditRetentionPolicyIsolation:
    """Retention policy 只存取自己 company"""

    def test_retention_policy_scoped_to_company(self, test_db):
        """每個 company 有獨立的 retention policy"""
        db = test_db
        ensure_tenants(db)

        repo = AuditLogRepository(db)

        # Company A 設定 180 天
        repo.upsert_retention_policy(COMPANY_A, 180)
        # Company B 設定 730 天
        repo.upsert_retention_policy(COMPANY_B, 730)

        policy_a = repo.get_retention_policy(COMPANY_A)
        policy_b = repo.get_retention_policy(COMPANY_B)

        assert policy_a.retention_days == 180
        assert policy_b.retention_days == 730
        assert policy_a.company_id == COMPANY_A
        assert policy_b.company_id == COMPANY_B

    def test_get_retention_policy_api_scoped_to_actor_company(self, test_db):
        """GET /api/audit/retention 只回傳自己 company 的 policy"""
        db = test_db
        ensure_tenants(db)

        repo = AuditLogRepository(db)
        repo.upsert_retention_policy(COMPANY_A, 90)
        repo.upsert_retention_policy(COMPANY_B, 365)

        actor_a = create_test_actor(COMPANY_A, role_id="admin")
        with override_actor_dependency(actor_a):
            resp = client.get("/api/audit/retention")
        assert resp.status_code == 200
        data = resp.json()
        assert data["retention_days"] == 90
        assert data["company_id"] == COMPANY_A

        actor_b = create_test_actor(COMPANY_B, role_id="admin")
        with override_actor_dependency(actor_b):
            resp = client.get("/api/audit/retention")
        assert resp.status_code == 200
        data = resp.json()
        assert data["retention_days"] == 365
        assert data["company_id"] == COMPANY_B
