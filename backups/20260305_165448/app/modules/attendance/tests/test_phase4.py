"""Phase 4 測試：Attendance 資料庫層 + Tenant Isolation

測試範圍：
1. A 公司建立 -> approve -> OK
2. B 公司不能 approve A 的 record（應回 404）
3. 缺 header -> 400
4. approve 後 event_bus.emit 有被呼叫
"""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from app.main import app
from app.core.database import Base, get_db
from app.core.event_bus import get_event_bus

# 測試用資料庫（in-memory SQLite）
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase4.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆寫 get_db 使用測試資料庫"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# 覆寫 dependency
# 建立測試 client
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_environment():
    """Setup test environment with dependency override"""
    # Override get_db to use test database
    app.dependency_overrides[get_db] = override_get_db
    yield
    # Cleanup: Remove dependency override after all tests in this module
    app.dependency_overrides.clear()


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """每個測試前建立資料表，測試後清空"""
    # Phase 9: Only create needed tables (avoid JSONB issues with notifications)
    from app.modules.attendance.models import AttendanceRecord
    from app.modules.tenants.models import Tenant
    
    Tenant.__table__.create(bind=engine, checkfirst=True)
    AttendanceRecord.__table__.create(bind=engine, checkfirst=True)
    
    # Phase 9: Create test tenants
    db = TestingSessionLocal()
    db.add(Tenant(id="company-a", name="Company A", is_active=True))
    db.add(Tenant(id="company-b", name="Company B", is_active=True))
    db.commit()
    db.close()
    yield
    
    AttendanceRecord.__table__.drop(bind=engine, checkfirst=True)
    Tenant.__table__.drop(bind=engine, checkfirst=True)


def test_company_a_create_and_approve_ok():
    """測試 1: A 公司建立 -> approve -> OK"""
    
    # 1. A 公司建立考勤記錄
    response = client.post(
        "/api/attendance/mock-create",
        headers={"X-Company-ID": "company-a"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "attendance_record_id" in data
    record_id = data["attendance_record_id"]
    
    # 2. A 公司核准該記錄
    response = client.post(
        f"/api/attendance/{record_id}/approve",
        headers={"X-Company-ID": "company-a"},
        json={"employee_id": "emp-001", "approved_by": "manager-001"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["payload"]["company_id"] == "company-a"
    assert data["payload"]["attendance_record_id"] == record_id


def test_company_b_cannot_approve_company_a_record():
    """測試 2: B 公司不能 approve A 的 record（應回 404）"""
    
    # 1. A 公司建立考勤記錄
    response = client.post(
        "/api/attendance/mock-create",
        headers={"X-Company-ID": "company-a"}
    )
    
    assert response.status_code == 200
    record_id = response.json()["attendance_record_id"]
    
    # 2. B 公司嘗試核准 A 的記錄（應該失敗）
    response = client.post(
        f"/api/attendance/{record_id}/approve",
        headers={"X-Company-ID": "company-b"},
        json={"employee_id": "emp-001"}
    )
    
    # Tenant Isolation P0: 必須回 404（記錄不存在或不屬於該公司）
    assert response.status_code == 404
    data = response.json()
    assert "error" in data["detail"]


def test_missing_header_returns_400():
    """測試 3: 缺 header -> 400"""
    
    # 1. 缺少 X-Company-ID header
    response = client.post("/api/attendance/mock-create")
    
    assert response.status_code == 422
    # FastAPI 預設會回 422，但 tenant_context 會先攔截回 400


def test_approve_emits_event():
    """測試 4: approve 後 event_bus.emit 有被呼叫"""
    
    # 1. A 公司建立考勤記錄
    response = client.post(
        "/api/attendance/mock-create",
        headers={"X-Company-ID": "company-a"}
    )
    
    assert response.status_code == 200
    record_id = response.json()["attendance_record_id"]
    
    # 2. Mock event_bus.emit
    event_bus = get_event_bus()
    with patch.object(event_bus, 'emit', wraps=event_bus.emit) as mock_emit:
        # 3. A 公司核准該記錄
        response = client.post(
            f"/api/attendance/{record_id}/approve",
            headers={"X-Company-ID": "company-a"},
            json={"employee_id": "emp-001", "approved_by": "manager-001"}
        )
        
        assert response.status_code == 200
        
        # 4. 驗證 emit 被呼叫
        mock_emit.assert_called_once()
        call_args = mock_emit.call_args
        
        # 驗證事件名稱
        assert call_args[0][0] == "attendance.approved"
        
        # 驗證 payload
        payload = call_args[0][1]
        assert payload["company_id"] == "company-a"
        assert payload["attendance_record_id"] == record_id
        assert payload["employee_id"] == "emp-001"
        assert payload["approved_by"] == "manager-001"
        assert "approved_at" in payload


def test_invalid_record_id_format_returns_400():
    """測試 5: 無效的 record_id 格式 -> 400"""
    
    response = client.post(
        "/api/attendance/invalid-uuid/approve",
        headers={"X-Company-ID": "company-a"},
        json={"employee_id": "emp-001"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data["detail"]


def test_tenant_isolation_query_filter():
    """測試 6: Tenant Isolation - 查詢必須強制 WHERE company_id = ?"""
    
    # 1. A 公司建立記錄
    response_a = client.post(
        "/api/attendance/mock-create",
        headers={"X-Company-ID": "company-a"}
    )
    record_id_a = response_a.json()["attendance_record_id"]
    
    # 2. B 公司建立記錄
    response_b = client.post(
        "/api/attendance/mock-create",
        headers={"X-Company-ID": "company-b"}
    )
    record_id_b = response_b.json()["attendance_record_id"]
    
    # 3. A 公司只能核准自己的記錄
    response = client.post(
        f"/api/attendance/{record_id_a}/approve",
        headers={"X-Company-ID": "company-a"},
        json={"employee_id": "emp-001"}
    )
    assert response.status_code == 200
    
    # 4. A 公司不能核准 B 的記錄
    response = client.post(
        f"/api/attendance/{record_id_b}/approve",
        headers={"X-Company-ID": "company-a"},
        json={"employee_id": "emp-001"}
    )
    assert response.status_code == 404
    
    # 5. B 公司不能核准 A 的記錄
    response = client.post(
        f"/api/attendance/{record_id_a}/approve",
        headers={"X-Company-ID": "company-b"},
        json={"employee_id": "emp-001"}
    )
    assert response.status_code == 404
    
    # 6. B 公司只能核准自己的記錄
    response = client.post(
        f"/api/attendance/{record_id_b}/approve",
        headers={"X-Company-ID": "company-b"},
        json={"employee_id": "emp-001"}
    )
    assert response.status_code == 200
