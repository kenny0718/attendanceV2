"""WP-11-13: Location Policy Service Tests

測試 location policy 評估邏輯
"""

import pytest
from app.modules.attendance.location_policy_service import (
    AttendanceLocationPolicyService,
    PolicyCheckResult
)
from app.modules.attendance.models import AllowedLocation


class TestLocationPolicyService:
    """Location Policy Service 測試"""
    
    def test_no_allowed_locations_allows_any(self, db_session, test_company):
        """測試：沒有 allowed locations 時允許任何地點"""
        service = AttendanceLocationPolicyService(db_session)
        
        result = service.check_location_policy(
            company_id=test_company.id,
            latitude=25.0330,
            longitude=121.5654
        )
        
        assert result.allowed is True
        assert "允許任何地點" in result.reason
        assert result.matched_location is None
    
    def test_within_radius_allows(self, db_session, test_company):
        """測試：在範圍內允許打卡"""
        # 建立 allowed location
        location = AllowedLocation(
            company_id=test_company.id,
            name="台北101工地",
            latitude=25.0330,
            longitude=121.5654,
            radius_meters=100,
            is_active=True
        )
        db_session.add(location)
        db_session.commit()
        
        service = AttendanceLocationPolicyService(db_session)
        
        # 在範圍內（距離約 50 公尺）
        result = service.check_location_policy(
            company_id=test_company.id,
            latitude=25.0335,
            longitude=121.5654
        )
        
        assert result.allowed is True
        assert "在允許的打卡範圍內" in result.reason
        assert result.matched_location is not None
        assert result.matched_location["name"] == "台北101工地"
    
    def test_outside_radius_denies(self, db_session, test_company):
        """測試：超出範圍拒絕打卡"""
        # 建立 allowed location
        location = AllowedLocation(
            company_id=test_company.id,
            name="台北101工地",
            latitude=25.0330,
            longitude=121.5654,
            radius_meters=100,
            is_active=True
        )
        db_session.add(location)
        db_session.commit()
        
        service = AttendanceLocationPolicyService(db_session)
        
        # 超出範圍（距離約 500 公尺）
        result = service.check_location_policy(
            company_id=test_company.id,
            latitude=25.0380,
            longitude=121.5654
        )
        
        assert result.allowed is False
        assert "不在允許的打卡範圍內" in result.reason
        assert result.matched_location is None
        assert result.nearest_location is not None
        assert result.nearest_location["name"] == "台北101工地"
    
    def test_multiple_locations_matches_any(self, db_session, test_company):
        """測試：多個地點，命中其中一個即可"""
        # 建立多個 allowed locations
        location1 = AllowedLocation(
            company_id=test_company.id,
            name="台北101工地",
            latitude=25.0330,
            longitude=121.5654,
            radius_meters=100,
            is_active=True
        )
        location2 = AllowedLocation(
            company_id=test_company.id,
            name="信義辦公室",
            latitude=25.0400,
            longitude=121.5700,
            radius_meters=100,
            is_active=True
        )
        db_session.add_all([location1, location2])
        db_session.commit()
        
        service = AttendanceLocationPolicyService(db_session)
        
        # 在 location2 範圍內
        result = service.check_location_policy(
            company_id=test_company.id,
            latitude=25.0405,
            longitude=121.5700
        )
        
        assert result.allowed is True
        assert result.matched_location["name"] == "信義辦公室"
    
    def test_inactive_location_ignored(self, db_session, test_company):
        """測試：停用的地點不被考慮"""
        # 建立停用的 allowed location
        location = AllowedLocation(
            company_id=test_company.id,
            name="台北101工地",
            latitude=25.0330,
            longitude=121.5654,
            radius_meters=100,
            is_active=False  # 停用
        )
        db_session.add(location)
        db_session.commit()
        
        service = AttendanceLocationPolicyService(db_session)
        
        # 在範圍內，但地點已停用
        result = service.check_location_policy(
            company_id=test_company.id,
            latitude=25.0335,
            longitude=121.5654
        )
        
        # 應該允許（因為沒有啟用的地點）
        assert result.allowed is True
        assert "允許任何地點" in result.reason
    
    def test_tenant_isolation(self, db_session, test_company, test_company2):
        """測試：Tenant isolation"""
        # 為 company1 建立 allowed location
        location = AllowedLocation(
            company_id=test_company.id,
            name="台北101工地",
            latitude=25.0330,
            longitude=121.5654,
            radius_meters=100,
            is_active=True
        )
        db_session.add(location)
        db_session.commit()
        
        service = AttendanceLocationPolicyService(db_session)
        
        # company2 查詢，應該看不到 company1 的地點
        result = service.check_location_policy(
            company_id=test_company2.id,
            latitude=25.0335,
            longitude=121.5654
        )
        
        # 應該允許（因為 company2 沒有設定地點）
        assert result.allowed is True
        assert "允許任何地點" in result.reason


class TestDistanceCalculation:
    """距離計算測試"""
    
    def test_haversine_distance(self):
        """測試 Haversine 距離計算"""
        from app.modules.attendance.gps_utils import calculate_distance
        
        # 台北101 到 台北車站（約 2.5 公里）
        distance = calculate_distance(
            (25.0330, 121.5654),  # 台北101
            (25.0478, 121.5170)   # 台北車站
        )
        
        # 應該約 2500 公尺（允許 10% 誤差）
        assert 2250 <= distance <= 2750
    
    def test_same_location_zero_distance(self):
        """測試相同位置距離為 0"""
        from app.modules.attendance.gps_utils import calculate_distance
        
        distance = calculate_distance(
            (25.0330, 121.5654),
            (25.0330, 121.5654)
        )
        
        assert distance < 1  # 應該非常接近 0


# Fixtures
@pytest.fixture
def test_company(db_session):
    """測試公司"""
    from app.modules.tenants.models import Tenant
    company = Tenant(id="test-company-1", name="Test Company 1")
    db_session.add(company)
    db_session.commit()
    return company


@pytest.fixture
def test_company2(db_session):
    """測試公司 2"""
    from app.modules.tenants.models import Tenant
    company = Tenant(id="test-company-2", name="Test Company 2")
    db_session.add(company)
    db_session.commit()
    return company
