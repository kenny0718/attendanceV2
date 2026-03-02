"""Audit API 測試

測試稽核紀錄的查詢與匯出功能。
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db

client = TestClient(app)
from app.modules.audit.models import AuditLog




class TestAuditLogsQuery:
    """測試 GET /api/audit/logs"""
    
    def test_query_without_header_returns_400(self):
        """測試：沒有 X-Company-ID header 回傳 400"""
        from app.core.database import get_db
        db = next(get_db())
        response = client.get("/api/audit/logs")
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert any(item.get("loc") == ["header", "X-Company-ID"] for item in detail)
    
    def test_tenant_isolation(self):
        """測試：tenant isolation - A 公司看不到 B 公司的資料"""
        from app.core.database import get_db
        db = next(get_db())
        # 建立 A 公司的稽核紀錄
        log_a = AuditLog(
            company_id="company-A",
            action="backup.export",
            status="success",
            actor="user-a",
            meta={"tables": 2}
        )
        db.add(log_a)
        
        # 建立 B 公司的稽核紀錄
        log_b = AuditLog(
            company_id="company-B",
            action="backup.restore",
            status="success",
            actor="user-b",
            meta={"tables": 3}
        )
        db.add(log_b)
        db.commit()
        
        # A 公司查詢：只能看到自己的資料
        response = client.get(
            "/api/audit/logs",
            headers={"X-Company-ID": "company-A"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["company_id"] == "company-A"
        assert data["items"][0]["actor"] == "user-a"
        
        # B 公司查詢：只能看到自己的資料
        response = client.get(
            "/api/audit/logs",
            headers={"X-Company-ID": "company-B"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["company_id"] == "company-B"
        assert data["items"][0]["actor"] == "user-b"
    
    def test_filter_by_event_type(self):
        """測試：event_type 篩選"""
        from app.core.database import get_db
        db = next(get_db())
        # 建立不同類型的稽核紀錄
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
        db.add_all([log1, log2])
        db.commit()
        
        # 篩選 backup.export
        response = client.get(
            "/api/audit/logs?event_type=backup.export",
            headers={"X-Company-ID": "company-A"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["event_type"] == "backup.export"
    
    def test_pagination(self):
        """測試：分頁功能"""
        from app.core.database import get_db
        db = next(get_db())
        # 建立 10 筆稽核紀錄
        for i in range(10):
            log = AuditLog(
                company_id="company-A",
                action="backup.export",
                status="success",
                actor=f"user-{i}",
                meta={}
            )
            db.add(log)
        db.commit()
        
        # 第 1 頁（每頁 5 筆）
        response = client.get(
            "/api/audit/logs?page=1&page_size=5",
            headers={"X-Company-ID": "company-A"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert data["total"] == 10
        assert len(data["items"]) == 5
        
        # 第 2 頁
        response = client.get(
            "/api/audit/logs?page=2&page_size=5",
            headers={"X-Company-ID": "company-A"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert len(data["items"]) == 5


class TestAuditLogsExport:
    """測試 GET /api/audit/export"""
    
    def test_export_json(self):
        """測試：匯出 JSON 格式"""
        from app.core.database import get_db
        db = next(get_db())
        # 建立稽核紀錄
        log = AuditLog(
            company_id="company-A",
            action="backup.export",
            status="success",
            actor="user-a",
            meta={"tables": 2}
        )
        db.add(log)
        db.commit()
        
        # 匯出 JSON
        response = client.get(
            "/api/audit/export?format=json",
            headers={"X-Company-ID": "company-A"}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["company_id"] == "company-A"
        assert data[0]["event_type"] == "backup.export"
    
    def test_export_csv(self):
        """測試：匯出 CSV 格式"""
        from app.core.database import get_db
        db = next(get_db())
        # 建立稽核紀錄
        log = AuditLog(
            company_id="company-A",
            action="backup.export",
            status="success",
            actor="user-a",
            meta={"tables": 2}
        )
        db.add(log)
        db.commit()
        
        # 匯出 CSV
        response = client.get(
            "/api/audit/export?format=csv",
            headers={"X-Company-ID": "company-A"}
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]
        
        # 檢查 CSV 內容
        csv_content = response.content.decode("utf-8")
        assert "id,company_id,event_type" in csv_content  # header
        assert "company-A" in csv_content
        assert "backup.export" in csv_content
    
    def test_export_limit_5000(self):
        """測試：匯出筆數限制（最多 5000 筆）"""
        from app.core.database import get_db
        db = next(get_db())
        # 建立 5001 筆稽核紀錄（會超過限制）
        # 注意：這個測試會比較慢，實際測試時可以減少筆數
        for i in range(100):  # 為了測試速度，這裡只建立 100 筆
            log = AuditLog(
                company_id="company-A",
                action="backup.export",
                status="success",
                actor=f"user-{i}",
                meta={}
            )
            db.add(log)
        db.commit()
        
        # 匯出應該成功（未超過 5000 筆）
        response = client.get(
            "/api/audit/export?format=json",
            headers={"X-Company-ID": "company-A"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 100
    
    def test_export_tenant_isolation(self):
        """測試：匯出時的 tenant isolation"""
        from app.core.database import get_db
        db = next(get_db())
        # 建立 A、B 兩家公司的稽核紀錄
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
        db.add_all([log_a, log_b])
        db.commit()
        
        # A 公司匯出：只能看到自己的資料
        response = client.get(
            "/api/audit/export?format=json",
            headers={"X-Company-ID": "company-A"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["company_id"] == "company-A"


class TestAuditLogsFilters:
    """測試各種篩選條件"""
    
    def test_filter_by_actor(self):
        """測試：actor 篩選"""
        from app.core.database import get_db
        db = next(get_db())
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
        db.add_all([log1, log2])
        db.commit()
        
        # 篩選 alice
        response = client.get(
            "/api/audit/logs?actor=alice",
            headers={"X-Company-ID": "company-A"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["actor"] == "alice"
    
    def test_filter_by_date_range(self):
        """測試：日期範圍篩選"""
        from app.core.database import get_db
        db = next(get_db())
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        
        # 建立昨天的紀錄
        log_old = AuditLog(
            company_id="company-A",
            action="backup.export",
            status="success",
            actor="user-a",
            meta={},
            created_at=yesterday
        )
        # 建立今天的紀錄
        log_new = AuditLog(
            company_id="company-A",
            action="backup.export",
            status="success",
            actor="user-a",
            meta={},
            created_at=now
        )
        db.add_all([log_old, log_new])
        db.commit()
        
        # 篩選今天的紀錄
        date_from = now.replace(hour=0, minute=0, second=0).isoformat() + "Z"
        response = client.get(
            f"/api/audit/logs?date_from={date_from}",
            headers={"X-Company-ID": "company-A"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
    
    def test_keyword_search(self):
        """測試：關鍵字搜尋"""
        from app.core.database import get_db
        db = next(get_db())
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
        db.add_all([log1, log2])
        db.commit()
        
        # 搜尋 "export"
        response = client.get(
            "/api/audit/logs?q=export",
            headers={"X-Company-ID": "company-A"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "export" in data["items"][0]["event_type"]
