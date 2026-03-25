"""OUT Checkpoint API 測試 (WP-11-10)

Test Coverage:
1. Multi checkpoint allowed (3 checkpoints in succession)
2. Mobile requires GPS (422 if missing)
3. PC allows no GPS (201 success)
4. De-dup: within 30s + within 50m => reject 409
5. GPS validation (invalid coordinates => 422)
6. List checkpoints with pagination
7. Checkpoint without open session (allowed)

WP-C1-07: JWT Actor Migration - 使用 override_actor_dependency
"""

import pytest
import time
from uuid import uuid4

from app.tests.utils.auth import create_test_actor, override_actor_dependency


@pytest.fixture
def test_actor(test_user):
    """Test actor backed by a real user in the database"""
    return create_test_actor("company-test", user_id=test_user.id)


class TestOutCheckpointMultiSubmit:
    """Test 1: Multi checkpoint allowed"""
    
    def test_multi_checkpoint_allowed(self, client, test_actor):
        """Test that multiple checkpoints can be created in succession"""
        with override_actor_dependency(test_actor):
            # Close any existing session first
            client.post("/api/v1/attendance/punch-out", json={})
            
            # Punch in first
            punch_in_response = client.post(
                "/api/v1/attendance/punch-in",
                json={}
            )
            assert punch_in_response.status_code == 201
            
            # Create 3 checkpoints with different coordinates
            for i in range(3):
                response = client.post(
                    "/api/v1/attendance/out-checkpoint",
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
            list_response = client.get("/api/v1/attendance/out-checkpoints")
            assert list_response.status_code == 200
            list_data = list_response.json()
            assert list_data["total"] >= 3


class TestOutCheckpointGPSValidation:
    """Test 2 & 3: GPS validation rules"""
    
    def test_mobile_requires_gps(self, client, test_actor):
        """Test that mobile device without GPS is rejected with 422"""
        with override_actor_dependency(test_actor):
            client.post("/api/v1/attendance/punch-in", json={})
            
            response = client.post(
                "/api/v1/attendance/out-checkpoint",
                json={"device_type": "mobile"}
            )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        detail = data["detail"]
        assert detail["error_code"] == "GPS_REQUIRED"
    
    def test_pc_no_gps_allowed(self, client, test_actor):
        """Test that PC device without GPS is allowed"""
        with override_actor_dependency(test_actor):
            client.post("/api/v1/attendance/punch-in", json={})
            
            response = client.post(
                "/api/v1/attendance/out-checkpoint",
                json={"device_type": "pc", "notes": "PC checkpoint"}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert "checkpoint_id" in data
        assert data["gps"] is None


class TestOutCheckpointDedup:
    """Test 4: De-duplication (30s + 50m)"""
    
    def test_anti_spam_duplicate_checkpoint(self, client, test_actor):
        """Test that duplicate checkpoint within 30s and 50m is rejected"""
        with override_actor_dependency(test_actor):
            client.post("/api/v1/attendance/punch-in", json={})
            
            checkpoint_data = {
                "device_type": "mobile",
                "gps": {"latitude": 25.0330, "longitude": 121.5654, "accuracy": 10.0}
            }
            
            # First checkpoint
            response1 = client.post(
                "/api/v1/attendance/out-checkpoint",
                json=checkpoint_data
            )
            assert response1.status_code == 201
            
            # Immediate duplicate
            response2 = client.post(
                "/api/v1/attendance/out-checkpoint",
                json=checkpoint_data
            )
        
        assert response2.status_code == 409
        data = response2.json()
        assert data["detail"]["error_code"] == "DUPLICATE_CHECKPOINT"


class TestOutCheckpointGPSCoordinates:
    """Test 5: GPS coordinate validation"""
    
    def test_invalid_latitude(self, client, test_actor):
        """Test that invalid latitude is rejected"""
        with override_actor_dependency(test_actor):
            client.post("/api/v1/attendance/punch-in", json={})
            
            response = client.post(
                "/api/v1/attendance/out-checkpoint",
                json={
                    "device_type": "mobile",
                    "gps": {"latitude": 91.0, "longitude": 121.0, "accuracy": 10.0}
                }
            )
        
        assert response.status_code == 422


class TestOutCheckpointList:
    """Test 6: List checkpoints"""
    
    def test_list_checkpoints_pagination(self, client, test_actor):
        """Test checkpoint list with pagination"""
        with override_actor_dependency(test_actor):
            client.post("/api/v1/attendance/punch-in", json={})
            
            # Create 2 checkpoints
            for i in range(2):
                client.post(
                    "/api/v1/attendance/out-checkpoint",
                    json={"device_type": "pc", "notes": f"Test {i+1}"}
                )
                time.sleep(1)
            
            response = client.get(
                "/api/v1/attendance/out-checkpoints?limit=10&offset=0"
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "checkpoints" in data
        assert "total" in data
        assert data["limit"] == 10


class TestOutCheckpointWithoutSession:
    """Test 7: Checkpoint without open session"""
    
    def test_checkpoint_without_session(self, client, test_actor):
        """Test checkpoint creation without open session (should be allowed)"""
        with override_actor_dependency(test_actor):
            response = client.post(
                "/api/v1/attendance/out-checkpoint",
                json={"device_type": "pc", "notes": "No session"}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert "checkpoint_id" in data
