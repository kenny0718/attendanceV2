"""WP-11-13: BREAK_OUT Location Policy Enforcement Tests

測試 BREAK_OUT endpoint 的 location policy enforcement
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skip(reason="attendance API not yet migrated to JWT Actor (WP-C1-attendance)")



class TestBreakOutLocationPolicyEnforcement:
    """BREAK_OUT Location Policy Enforcement 測試"""
    
    def test_break_out_without_location_no_policy_succeeds(self, client, test_session, test_user):
        """測試：無 location + 無 policy → 成功"""
        # 先 punch in
        response = client.post(
            "/api/v1/attendance/punch-in",
            json={},
            headers={"X-Company-ID": test_user.company_id, "X-User-ID": str(test_user.id)}
        )
        assert response.status_code == 201
        
        # Break out without location
        response = client.post(
            "/api/v1/attendance/break-out",
            json={"notes": "外出辦事"},
            headers={"X-Company-ID": test_user.company_id, "X-User-ID": str(test_user.id)}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "外出打卡成功"
    
    def test_break_out_with_location_no_policy_succeeds(self, client, test_session, test_user):
        """測試：有 location + 無 policy → 成功（向後相容）"""
        # 先 punch in
        response = client.post(
            "/api/v1/attendance/punch-in",
            json={},
            headers={"X-Company-ID": test_user.company_id, "X-User-ID": str(test_user.id)}
        )
        assert response.status_code == 201
        
        # Break out with location
        response = client.post(
            "/api/v1/attendance/break-out",
            json={
                "notes": "外出辦事",
                "location": {
                    "latitude": 25.0330,
                    "longitude": 121.5654
                }
            },
            headers={"X-Company-ID": test_user.company_id, "X-User-ID": str(test_user.id)}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "外出打卡成功"
    
    def test_break_out_within_allowed_location_succeeds(self, client, test_session, test_user, test_allowed_location):
        """測試：有 location + 在範圍內 → 成功，記錄 location_id"""
        # 先 punch in
        response = client.post(
            "/api/v1/attendance/punch-in",
            json={},
            headers={"X-Company-ID": test_user.company_id, "X-User-ID": str(test_user.id)}
        )
        assert response.status_code == 201
        
        # Break out within allowed location (距離約 50 公尺)
        response = client.post(
            "/api/v1/attendance/break-out",
            json={
                "notes": "外出辦事",
                "location": {
                    "latitude": 25.0335,
                    "longitude": 121.5654
                }
            },
            headers={"X-Company-ID": test_user.company_id, "X-User-ID": str(test_user.id)}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "外出打卡成功"
        
        # 驗證 punch 記錄有 location_id
        from app.modules.attendance.models import AttendancePunch
        punch = test_session.query(AttendancePunch).filter(
            AttendancePunch.id == data["punch_id"]
        ).first()
        assert punch is not None
        assert punch.location_id == test_allowed_location.id
    
    def test_break_out_outside_allowed_location_fails(self, client, test_session, test_user, test_allowed_location):
        """測試：有 location + 超出範圍 → 403 + LOCATION_POLICY_VIOLATION"""
        # 先 punch in
        response = client.post(
            "/api/v1/attendance/punch-in",
            json={},
            headers={"X-Company-ID": test_user.company_id, "X-User-ID": str(test_user.id)}
        )
        assert response.status_code == 201
        
        # Break out outside allowed location (距離約 500 公尺)
        response = client.post(
            "/api/v1/attendance/break-out",
            json={
                "notes": "外出辦事",
                "location": {
                    "latitude": 25.0380,
                    "longitude": 121.5654
                }
            },
            headers={"X-Company-ID": test_user.company_id, "X-User-ID": str(test_user.id)}
        )
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error_code"] == "LOCATION_POLICY_VIOLATION"
        assert "不在允許的打卡範圍內" in data["detail"]["error"]
        assert data["detail"]["nearest_location"] is not None
    
    def test_break_out_tenant_isolation(self, client, test_session, test_user, test_user2, test_allowed_location):
        """測試：不同公司的 allowed locations 不能互相影響"""
        # test_user2 屬於不同公司
        # 先 punch in
        response = client.post(
            "/api/v1/attendance/punch-in",
            json={},
            headers={"X-Company-ID": test_user2.company_id, "X-User-ID": str(test_user2.id)}
        )
        assert response.status_code == 201
        
        # test_user2 在 test_user 的 allowed location 範圍內打卡
        # 但因為 tenant isolation，應該允許（因為 test_user2 的公司沒有設定 policy）
        response = client.post(
            "/api/v1/attendance/break-out",
            json={
                "notes": "外出辦事",
                "location": {
                    "latitude": 25.0335,
                    "longitude": 121.5654
                }
            },
            headers={"X-Company-ID": test_user2.company_id, "X-User-ID": str(test_user2.id)}
        )
        assert response.status_code == 201  # 應該成功，因為 test_user2 的公司沒有 policy
    
    def test_break_out_multiple_locations_matches_any(self, client, test_session, test_user):
        """測試：多個地點，命中其中一個即可"""
        from app.modules.attendance.models import AllowedLocation
        
        # 建立兩個 allowed locations
        location1 = AllowedLocation(
            company_id=test_user.company_id,
            name="台北101工地",
            latitude=25.0330,
            longitude=121.5654,
            radius_meters=100,
            is_active=True
        )
        location2 = AllowedLocation(
            company_id=test_user.company_id,
            name="信義辦公室",
            latitude=25.0400,
            longitude=121.5700,
            radius_meters=100,
            is_active=True
        )
        test_session.add_all([location1, location2])
        test_session.commit()
        
        # 先 punch in
        response = client.post(
            "/api/v1/attendance/punch-in",
            json={},
            headers={"X-Company-ID": test_user.company_id, "X-User-ID": str(test_user.id)}
        )
        assert response.status_code == 201
        
        # Break out 在 location2 範圍內
        response = client.post(
            "/api/v1/attendance/break-out",
            json={
                "notes": "外出辦事",
                "location": {
                    "latitude": 25.0405,
                    "longitude": 121.5700
                }
            },
            headers={"X-Company-ID": test_user.company_id, "X-User-ID": str(test_user.id)}
        )
        assert response.status_code == 201


# Fixtures
@pytest.fixture
def test_allowed_location(test_session, test_user):
    """測試用 allowed location"""
    from app.modules.attendance.models import AllowedLocation
    
    location = AllowedLocation(
        company_id=test_user.company_id,
        name="台北101工地",
        latitude=25.0330,
        longitude=121.5654,
        radius_meters=100,
        is_active=True
    )
    test_session.add(location)
    test_session.commit()
    test_session.refresh(location)
    return location


@pytest.fixture
def test_user2(test_session):
    """測試用第二個使用者（不同公司）"""
    from app.modules.auth.models import User
    from app.modules.tenants.models import Tenant
    
    # 建立第二個公司
    company2 = Tenant(id="test-company-2", name="Test Company 2")
    test_session.add(company2)
    test_session.commit()
    
    # 建立第二個使用者
    user2 = User(
        id=uuid4(),
        company_id="test-company-2",
        email="test2@example.com",
        username="testuser2"
    )
    test_session.add(user2)
    test_session.commit()
    test_session.refresh(user2)
    return user2
