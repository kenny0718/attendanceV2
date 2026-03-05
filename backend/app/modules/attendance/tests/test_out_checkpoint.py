"""OUT Checkpoint API 測試 (WP-11-10)

Test Coverage:
1. Multi checkpoint allowed (3 checkpoints in succession)
2. Mobile requires GPS (422 if missing)
3. PC allows no GPS (201 success)
4. De-dup: within 30s + within 50m => reject 409
5. GPS validation (invalid coordinates => 422)
6. List checkpoints with pagination
7. Checkpoint without open session (allowed)
"""

import pytest
import time
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.modules.tenants.repo import TenantRepository

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_test_tenant():
    """Setup test tenant for all tests in this module"""
    db = next(get_db())
    tenant_repo = TenantRepository(db)
    
    # Create test tenant if not exists
    if not tenant_repo.exists("company-test"):
        tenant_repo.create("company-test", "Test Company", is_active=True)
    
    yield


@pytest.fixture
def auth_headers():
    """Auth headers for testing (using existing test user)"""
    return {
        "X-Company-ID": "company-test",
        "X-User-ID": "11bda10d-7541-4230-b1f3-842afab2cea5"  # testuser from seed data
    }


class TestOutCheckpointMultiSubmit:
    """Test 1: Multi checkpoint allowed"""
    
    def test_multi_checkpoint_allowed(self, auth_headers):
        """Test that multiple checkpoints can be created in succession"""
        # Punch in first
        punch_in_response = client.post(
            "/api/v1/attendance/punch-in",
            headers=auth_headers,
            json={}
        )
        assert punch_in_response.status_code == 201
        
        # Create 3 checkpoints with different coordinates
        for i in range(3):
            response = client.post(
                "/api/v1/attendance/out-checkpoint",
                headers=auth_headers,
                json={
                    "device_type": "mobile",
                    "gps": {
                        "latitude": 25.0330 + i * 0.001,
                        "longitude": 121.5654 + i * 0.001,
                        "accuracy": 10.0
                    },
                    "notes": f"Checkpoint {i+1}"
                }
            )
            assert response.status_code == 201
            data = response.json()
            assert "checkpoint_id" in data
            assert "punch_time" in data
            
            # Wait 1 second to avoid de-dup
            time.sleep(1)
        
        # Verify all 3 exist
        list_response = client.get(
            "/api/v1/attendance/out-checkpoints",
            headers=auth_headers
        )
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert list_data["total"] >= 3


class TestOutCheckpointGPSValidation:
    """Test 2 & 3: GPS validation rules"""
    
    def test_mobile_requires_gps(self, auth_headers):
        """Test that mobile device without GPS is rejected with 422"""
        client.post("/api/v1/attendance/punch-in", headers=auth_headers, json={})
        
        response = client.post(
            "/api/v1/attendance/out-checkpoint",
            headers=auth_headers,
            json={"device_type": "mobile"}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        detail = data["detail"]
        assert detail["error_code"] == "GPS_REQUIRED"
    
    def test_pc_no_gps_allowed(self, auth_headers):
        """Test that PC device without GPS is allowed"""
        client.post("/api/v1/attendance/punch-in", headers=auth_headers, json={})
        
        response = client.post(
            "/api/v1/attendance/out-checkpoint",
            headers=auth_headers,
            json={"device_type": "pc", "notes": "PC checkpoint"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "checkpoint_id" in data
        assert data["gps"] is None


class TestOutCheckpointDedup:
    """Test 4: De-duplication (30s + 50m)"""
    
    def test_anti_spam_duplicate_checkpoint(self, auth_headers):
        """Test that duplicate checkpoint within 30s and 50m is rejected"""
        client.post("/api/v1/attendance/punch-in", headers=auth_headers, json={})
        
        checkpoint_data = {
            "device_type": "mobile",
            "gps": {"latitude": 25.0330, "longitude": 121.5654, "accuracy": 10.0}
        }
        
        # First checkpoint
        response1 = client.post(
            "/api/v1/attendance/out-checkpoint",
            headers=auth_headers,
            json=checkpoint_data
        )
        assert response1.status_code == 201
        
        # Immediate duplicate
        response2 = client.post(
            "/api/v1/attendance/out-checkpoint",
            headers=auth_headers,
            json=checkpoint_data
        )
        
        assert response2.status_code == 409
        data = response2.json()
        assert data["detail"]["error_code"] == "DUPLICATE_CHECKPOINT"


class TestOutCheckpointGPSCoordinates:
    """Test 5: GPS coordinate validation"""
    
    def test_invalid_latitude(self, auth_headers):
        """Test that invalid latitude is rejected"""
        client.post("/api/v1/attendance/punch-in", headers=auth_headers, json={})
        
        response = client.post(
            "/api/v1/attendance/out-checkpoint",
            headers=auth_headers,
            json={
                "device_type": "mobile",
                "gps": {"latitude": 91.0, "longitude": 121.0, "accuracy": 10.0}
            }
        )
        
        assert response.status_code == 422


class TestOutCheckpointList:
    """Test 6: List checkpoints"""
    
    def test_list_checkpoints_pagination(self, auth_headers):
        """Test checkpoint list with pagination"""
        client.post("/api/v1/attendance/punch-in", headers=auth_headers, json={})
        
        # Create 2 checkpoints
        for i in range(2):
            client.post(
                "/api/v1/attendance/out-checkpoint",
                headers=auth_headers,
                json={"device_type": "pc", "notes": f"Test {i+1}"}
            )
            time.sleep(1)
        
        response = client.get(
            "/api/v1/attendance/out-checkpoints?limit=10&offset=0",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "checkpoints" in data
        assert "total" in data
        assert data["limit"] == 10


class TestOutCheckpointWithoutSession:
    """Test 7: Checkpoint without open session"""
    
    def test_checkpoint_without_session(self, auth_headers):
        """Test checkpoint creation without open session (should be allowed)"""
        response = client.post(
            "/api/v1/attendance/out-checkpoint",
            headers=auth_headers,
            json={"device_type": "pc", "notes": "No session"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "checkpoint_id" in data
