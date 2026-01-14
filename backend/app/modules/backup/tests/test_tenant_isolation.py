"""Tenant Isolation 測試（P0）

驗證 Tenant Isolation 規則：
- A 公司匯出只包含 A 公司資料
- A 公司還原到 B 公司時，company_id 被覆寫為 B
- 備份檔混入其他公司資料時，還原失敗
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


class TestBackupTenantIsolation:
    """Backup Tenant Isolation 測試（P0）"""
    
    def setup_method(self):
        """每個測試前清空資料"""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    
    def test_export_requires_company_header(self):
        """測試：缺少 X-Company-ID header 應回 400"""
        response = client.post("/api/backup/export")
        
        assert response.status_code == 400
        assert response.headers["content-type"] == "application/json"
    
    def test_export_only_exports_target_company(self):
        """測試：匯出時只匯出指定公司資料（P0）"""
        # 準備資料：A 公司 2 筆，B 公司 3 筆
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        
        for i in range(2):
            repo.create_notification(
                company_id="company-A",
                event_type="test.event",
                event_payload={"index": i}
            )
        
        for i in range(3):
            repo.create_notification(
                company_id="company-B",
                event_type="test.event",
                event_payload={"index": i}
            )
        
        db.close()
        
        # 匯出 A 公司
        headers = {"X-Company-ID": "company-A"}
        response = client.post("/api/backup/export", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # 驗證：只有 A 公司的 2 筆資料
        assert data["metadata"]["company_id"] == "company-A"
        assert len(data["data"]["notifications"]) == 2
        
        # 驗證：所有資料都是 A 公司
        for record in data["data"]["notifications"]:
            assert record["company_id"] == "company-A"
    
    def test_restore_overwrites_company_id(self):
        """測試：還原時覆寫 company_id（P0）"""
        # 準備備份檔（A 公司的資料）
        backup_data = {
            "metadata": {
                "company_id": "company-A",
                "exported_at": "2026-01-14T12:00:00.000000Z",
                "version": "1.0",
                "tables": ["notifications"]
            },
            "data": {
                "notifications": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "company_id": "company-A",  # 原始是 A 公司
                        "event_type": "test.event",
                        "event_payload": {"test": "data"},
                        "created_at": "2026-01-14T10:00:00.000000Z"
                    }
                ]
            }
        }
        
        # 還原到 B 公司
        headers = {"X-Company-ID": "company-B"}
        response = client.post(
            "/api/backup/restore",
            headers=headers,
            json=backup_data
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["ok"] is True
        assert result["target_company_id"] == "company-B"
        assert result["summary"]["notifications"] == 1
        
        # 驗證：資料的 company_id 已被覆寫為 B
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        notifications = repo.get_notifications("company-B")
        
        assert len(notifications) == 1
        assert notifications[0].company_id == "company-B"  # 已覆寫
        
        # 驗證：A 公司沒有資料
        notifications_a = repo.get_notifications("company-A")
        assert len(notifications_a) == 0
        
        db.close()
    
    def test_restore_preserves_uuid(self):
        """測試：還原時保留 UUID（避免衝突）"""
        original_uuid = "550e8400-e29b-41d4-a716-446655440000"
        
        backup_data = {
            "metadata": {
                "company_id": "company-A",
                "exported_at": "2026-01-14T12:00:00Z",
                "version": "1.0"
            },
            "data": {
                "notifications": [
                    {
                        "id": original_uuid,
                        "company_id": "company-A",
                        "event_type": "test",
                        "event_payload": {},
                        "created_at": "2026-01-14T10:00:00Z"
                    }
                ]
            }
        }
        
        # 還原
        headers = {"X-Company-ID": "company-test"}
        response = client.post(
            "/api/backup/restore",
            headers=headers,
            json=backup_data
        )
        
        assert response.status_code == 200
        
        # 驗證：UUID 保持不變
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        notifications = repo.get_notifications("company-test")
        
        assert len(notifications) == 1
        assert str(notifications[0].id) == original_uuid
        
        db.close()
    
    def test_restore_fails_on_mixed_company_ids(self):
        """測試：備份檔混入其他 company_id → fail fast（P0）"""
        backup_data = {
            "metadata": {
                "company_id": "company-A",
                "exported_at": "2026-01-14T12:00:00Z",
                "version": "1.0"
            },
            "data": {
                "notifications": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "company_id": "company-A",
                        "event_type": "test",
                        "event_payload": {},
                        "created_at": "2026-01-14T10:00:00Z"
                    },
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440002",
                        "company_id": "company-B",  # 混入 B 公司
                        "event_type": "test",
                        "event_payload": {},
                        "created_at": "2026-01-14T10:01:00Z"
                    }
                ]
            }
        }
        
        # 嘗試還原
        headers = {"X-Company-ID": "company-test"}
        response = client.post(
            "/api/backup/restore",
            headers=headers,
            json=backup_data
        )
        
        # 應該失敗（400 Bad Request）
        assert response.status_code == 400
        assert response.headers["content-type"] == "application/json"
        assert "多個 company_id" in response.json()["detail"]
    
    def test_restore_with_clear_existing(self):
        """測試：clear_existing=true 清空現有資料"""
        # 準備現有資料
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        repo.create_notification(
            company_id="company-test",
            event_type="existing",
            event_payload={"old": "data"}
        )
        db.close()
        
        # 準備備份檔
        backup_data = {
            "metadata": {
                "company_id": "company-A",
                "exported_at": "2026-01-14T12:00:00Z",
                "version": "1.0"
            },
            "data": {
                "notifications": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "company_id": "company-A",
                        "event_type": "new",
                        "event_payload": {"new": "data"},
                        "created_at": "2026-01-14T10:00:00Z"
                    }
                ]
            }
        }
        
        # 還原（clear_existing=true）
        headers = {"X-Company-ID": "company-test"}
        response = client.post(
            "/api/backup/restore?clear_existing=true",
            headers=headers,
            json=backup_data
        )
        
        assert response.status_code == 200
        
        # 驗證：只有新資料，舊資料已清空
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        notifications = repo.get_notifications("company-test")
        
        assert len(notifications) == 1
        assert notifications[0].event_type == "new"
        
        db.close()
    
    def test_restore_merge_mode_by_default(self):
        """測試：預設為 Merge 模式（保留現有資料）"""
        # 準備現有資料
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        repo.create_notification(
            company_id="company-test",
            event_type="existing",
            event_payload={"old": "data"}
        )
        db.close()
        
        # 準備備份檔
        backup_data = {
            "metadata": {
                "company_id": "company-A",
                "exported_at": "2026-01-14T12:00:00Z",
                "version": "1.0"
            },
            "data": {
                "notifications": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "company_id": "company-A",
                        "event_type": "new",
                        "event_payload": {"new": "data"},
                        "created_at": "2026-01-14T10:00:00Z"
                    }
                ]
            }
        }
        
        # 還原（不指定 clear_existing，預設 false）
        headers = {"X-Company-ID": "company-test"}
        response = client.post(
            "/api/backup/restore",
            headers=headers,
            json=backup_data
        )
        
        assert response.status_code == 200
        
        # 驗證：新舊資料都存在（Merge）
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        notifications = repo.get_notifications("company-test")
        
        assert len(notifications) == 2  # 1 舊 + 1 新
        event_types = {n.event_type for n in notifications}
        assert "existing" in event_types
        assert "new" in event_types
        
        db.close()


class TestBackupCrossCompanyIsolation:
    """跨公司隔離測試"""
    
    def setup_method(self):
        """每個測試前清空資料"""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    
    def test_export_a_restore_to_b(self):
        """測試：A 公司匯出 → B 公司還原 → 資料屬於 B"""
        # 步驟 1: 準備 A 公司資料
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        repo.create_notification(
            company_id="company-A",
            event_type="test",
            event_payload={"source": "A"}
        )
        db.close()
        
        # 步驟 2: 匯出 A 公司
        headers_a = {"X-Company-ID": "company-A"}
        export_response = client.post("/api/backup/export", headers=headers_a)
        assert export_response.status_code == 200
        backup_data = export_response.json()
        
        # 步驟 3: 還原到 B 公司
        headers_b = {"X-Company-ID": "company-B"}
        restore_response = client.post(
            "/api/backup/restore",
            headers=headers_b,
            json=backup_data
        )
        assert restore_response.status_code == 200
        
        # 步驟 4: 驗證資料屬於 B 公司
        db = TestingSessionLocal()
        repo = NotificationRepository(db)
        
        # B 公司有 1 筆資料
        notifications_b = repo.get_notifications("company-B")
        assert len(notifications_b) == 1
        assert notifications_b[0].company_id == "company-B"
        
        # A 公司仍有 1 筆資料（不受影響）
        notifications_a = repo.get_notifications("company-A")
        assert len(notifications_a) == 1
        assert notifications_a[0].company_id == "company-A"
        
        db.close()
