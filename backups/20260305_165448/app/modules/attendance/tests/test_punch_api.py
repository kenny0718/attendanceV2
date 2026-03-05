"""Test Punch In/Out API (WP-11-02)

Tests for attendance punch API endpoints following WP-11-02_PRECHECK_CHECKLIST.md

Test Coverage:
- Punch in success
- Punch in duplicate (409)
- Punch out success
- Punch out no open session (404)
- Current status (open/no open)
- History (pagination)
- Tenant isolation
- Concurrency (race condition)
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.modules.auth.models import User
from app.modules.tenants.models import Tenant
from app.modules.attendance.models import AttendanceSession, AttendancePunch


# Test database setup
TEST_DATABASE_URL = "postgresql://postgres:Raxcxtjq260!@127.0.0.1:5432/attendance_test"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create test database session"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    # Mark session as testing mode (for deterministic punch_time)
    session.info["testing"] = True
    
    # Setup: Create test tenants and users
    tenant_a = Tenant(id="company-a", name="Company A", is_active=True)
    tenant_b = Tenant(id="company-b", name="Company B", is_active=True)
    user1 = User(
        id=uuid4(),
        display_name="User 1",
        password_hash="dummy_hash",
        is_active=True
    )
    user2 = User(
        id=uuid4(),
        display_name="User 2",
        password_hash="dummy_hash",
        is_active=True
    )
    session.add_all([tenant_a, tenant_b, user1, user2])
    session.commit()
    
    yield session
    
    # Teardown
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create test client with database override"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    """Get test user"""
    return db.query(User).first()


@pytest.fixture
def test_user2(db):
    """Get second test user"""
    return db.query(User).offset(1).first()


class TestPunchIn:
    """Test punch in endpoint"""
    
    def test_punch_in_success(self, client, test_user):
        """測試：punch in 成功建立 session 和 punch 記錄"""
        response = client.post(
            "/api/v1/attendance/punch-in",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            },
            json={"notes": "Morning punch in"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "session_id" in data
        assert "user_id" in data
        assert "company_id" in data
        assert "punch_in_time" in data
        assert "status" in data
        
        # Verify values
        assert data["user_id"] == str(test_user.id)
        assert data["company_id"] == "company-a"
        assert data["status"] == "open"
        assert data["punch_out_time"] is None
        assert data["duration_minutes"] is None
    
    def test_punch_in_with_location(self, client, test_user):
        """測試：punch in 帶 GPS 位置"""
        response = client.post(
            "/api/v1/attendance/punch-in",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            },
            json={
                "notes": "Punch in from office",
                "location": {
                    "latitude": 25.0330,
                    "longitude": 121.5654
                }
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "open"
    
    def test_punch_in_duplicate_returns_409(self, client, test_user):
        """測試：重複 punch in 回傳 409"""
        # First punch in
        response1 = client.post(
            "/api/v1/attendance/punch-in",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            },
            json={}
        )
        assert response1.status_code == 201
        session_id = response1.json()["session_id"]
        
        # Second punch in (should fail)
        response2 = client.post(
            "/api/v1/attendance/punch-in",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            },
            json={}
        )
        
        assert response2.status_code == 409
        data = response2.json()
        
        # Verify error structure
        detail = data.get("detail", data)
        assert "error" in detail
        assert "error_code" in detail
        assert "open_session_id" in detail
        assert "punch_in_time" in detail
        
        # Verify error details
        assert detail["error_code"] == "ALREADY_OPEN_SESSION"
        assert detail["open_session_id"] == session_id
    def test_punch_in_missing_company_header(self, client, test_user):
        """測試：缺少 X-Company-ID header 回傳 422"""
        response = client.post(
            "/api/v1/attendance/punch-in",
            headers={
                "X-User-ID": str(test_user.id)
            },
            json={}
        )
        
        assert response.status_code in [400, 422]
    
    def test_punch_in_missing_user_header(self, client, test_user):
        """測試：缺少 X-User-ID header 回傳 422"""
        response = client.post(
            "/api/v1/attendance/punch-in",
            headers={
                "X-Company-ID": "company-a"
            },
            json={}
        )
        
        assert response.status_code in [400, 422]


class TestPunchOut:
    """Test punch out endpoint"""
    
    def test_punch_out_success(self, client, test_user):
        """測試：punch out 成功關閉 session"""
        # First punch in
        response1 = client.post(
            "/api/v1/attendance/punch-in",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            },
            json={}
        )
        assert response1.status_code == 201
        session_id = response1.json()["session_id"]
        
        # Then punch out
        response2 = client.post(
            "/api/v1/attendance/punch-out",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            },
            json={"notes": "End of day"}
        )
        
        assert response2.status_code == 200
        data = response2.json()
        
        # Verify response structure
        assert data["session_id"] == session_id
        assert data["status"] == "closed"
        assert data["punch_out_time"] is not None
        assert data["duration_minutes"] is not None
        assert data["duration_minutes"] >= 0
    
    def test_punch_out_no_open_session_returns_404(self, client, test_user):
        """測試：沒有 open session 時 punch out 回傳 404"""
        response = client.post(
            "/api/v1/attendance/punch-out",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            },
            json={}
        )
        
        assert response.status_code == 404
        data = response.json()
        
        # Verify error structure
        assert "detail" in data
        detail = data["detail"]
        assert "error" in detail
        assert "error_code" in detail
        assert data["detail"]["error_code"] == "NO_OPEN_SESSION"
    
    def test_punch_out_twice_returns_404(self, client, test_user):
        """測試：重複 punch out 回傳 404"""
        # Punch in
        client.post(
            "/api/v1/attendance/punch-in",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            },
            json={}
        )
        
        # First punch out
        response1 = client.post(
            "/api/v1/attendance/punch-out",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            },
            json={}
        )
        assert response1.status_code == 200
        
        # Second punch out (should fail)
        response2 = client.post(
            "/api/v1/attendance/punch-out",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            },
            json={}
        )
        assert response2.status_code == 404


class TestCurrentStatus:
    """Test current status endpoint"""
    
    def test_status_with_open_session(self, client, test_user):
        """測試：有 open session 時回傳 session 資訊"""
        # Punch in
        client.post(
            "/api/v1/attendance/punch-in",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            },
            json={}
        )
        
        # Get status
        response = client.get(
            "/api/v1/attendance/current-status",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert data["has_open_session"] is True
        assert data["session"] is not None
        assert data["elapsed_minutes"] is not None
        
        # Verify session details
        assert data["session"]["status"] == "open"
        assert data["session"]["user_id"] == str(test_user.id)
        assert data["session"]["company_id"] == "company-a"
    
    def test_status_without_open_session(self, client, test_user):
        """測試：沒有 open session 時回傳 null"""
        response = client.get(
            "/api/v1/attendance/current-status",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert data["has_open_session"] is False
        assert data["session"] is None
        assert data["elapsed_minutes"] is None


class TestAttendanceHistory:
    """Test attendance history endpoint"""
    
    def test_history_empty(self, client, test_user):
        """測試：沒有記錄時回傳空列表"""
        response = client.get(
            "/api/v1/attendance/history",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["sessions"] == []
        assert data["limit"] == 50
        assert data["offset"] == 0
    
    def test_history_with_sessions(self, client, test_user):
        """測試：有記錄時回傳 session 列表"""
        # Create a closed session
        client.post(
            "/api/v1/attendance/punch-in",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            },
            json={}
        )
        client.post(
            "/api/v1/attendance/punch-out",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            },
            json={}
        )
        
        # Get history
        response = client.get(
            "/api/v1/attendance/history",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["status"] == "closed"
    
    def test_history_pagination(self, client, test_user):
        """測試：分頁參數正確運作"""
        response = client.get(
            "/api/v1/attendance/history?limit=10&offset=5",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["limit"] == 10
        assert data["offset"] == 5


class TestTenantIsolation:
    """Test tenant isolation"""
    
    def test_different_companies_isolated(self, client, test_user):
        """測試：不同公司的 session 互相隔離"""
        # Company A punch in
        response_a = client.post(
            "/api/v1/attendance/punch-in",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            },
            json={}
        )
        assert response_a.status_code == 201
        
        # Company B can also punch in (different company)
        response_b = client.post(
            "/api/v1/attendance/punch-in",
            headers={
                "X-Company-ID": "company-b",
                "X-User-ID": str(test_user.id)
            },
            json={}
        )
        assert response_b.status_code == 201
        
        # Verify different session IDs
        assert response_a.json()["session_id"] != response_b.json()["session_id"]
    
    def test_cannot_see_other_company_sessions(self, client, test_user):
        """測試：無法看到其他公司的 session"""
        # Company A punch in
        client.post(
            "/api/v1/attendance/punch-in",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            },
            json={}
        )
        
        # Company B checks status (should not see Company A's session)
        response = client.get(
            "/api/v1/attendance/current-status",
            headers={
                "X-Company-ID": "company-b",
                "X-User-ID": str(test_user.id)
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_open_session"] is False
    
    def test_different_users_isolated(self, client, test_user, test_user2):
        """測試：不同使用者的 session 互相隔離"""
        # User 1 punch in
        client.post(
            "/api/v1/attendance/punch-in",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            },
            json={}
        )
        
        # User 2 can also punch in
        response = client.post(
            "/api/v1/attendance/punch-in",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user2.id)
            },
            json={}
        )
        assert response.status_code == 201


class TestConcurrency:
    """Test concurrency and race conditions"""
    
    def test_concurrent_punch_in_only_one_succeeds(self, client, test_user, db):
        """測試：並發 punch in 只有一個成功"""
        # This test simulates race condition by creating session directly in DB
        # then trying to punch in via API
        
        from app.modules.attendance.models import AttendanceSession
        from datetime import datetime
        
        # Create open session directly in DB (simulating first request)
        session = AttendanceSession(
            company_id="company-a",
            user_id=test_user.id,
            punch_in_time=datetime.utcnow(),
            status="open"
        )
        db.add(session)
        db.commit()
        
        # Try to punch in via API (should fail with 409)
        response = client.post(
            "/api/v1/attendance/punch-in",
            headers={
                "X-Company-ID": "company-a",
                "X-User-ID": str(test_user.id)
            },
            json={}
        )
        
        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["error_code"] == "ALREADY_OPEN_SESSION"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
