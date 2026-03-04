"""Tests for Tenants Entitlements API

WP-11-04A: Entitlements management API tests
使用 PostgreSQL Test DB + Transaction Rollback
"""

import pytest
from uuid import uuid4
from app.core.scope import Actor, UserRole
from app.core.dependencies import get_current_actor
from app.core.features import FeatureKeys
from app.modules.tenants.models import Tenant, CompanyEntitlement
from app.main import app


class TestEntitlementsAPI:
    """Entitlements API 測試"""
    
    def test_super_admin_can_list_any_company_entitlements(self, db_session, client):
        """測試：super_admin 可列出任意公司的 entitlements"""
        # 建立測試公司
        tenant = Tenant(id="test_company_1", name="Test Company 1")
        db_session.add(tenant)
        db_session.commit()
        
        # Mock actor
        actor = Actor(user_id=uuid4(), role=UserRole.SUPER_ADMIN)
        
        def override_get_current_actor():
            return actor
        
        app.dependency_overrides[get_current_actor] = override_get_current_actor
        
        response = client.get("/api/admin/companies/test_company_1/entitlements")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200
        data = response.json()
        assert data["company_id"] == "test_company_1"
        assert "entitlements" in data
    
    def test_customer_service_can_list_assigned_company_entitlements(self, db_session, client):
        """測試：customer_service 可列出被指派公司的 entitlements"""
        # 建立測試公司
        tenant = Tenant(id="test_company_1", name="Test Company 1")
        db_session.add(tenant)
        db_session.commit()
        
        # Mock actor (已指派)
        actor = Actor(
            user_id=uuid4(),
            role=UserRole.CUSTOMER_SERVICE,
            support_company_assignments={"test_company_1"}
        )
        
        def override_get_current_actor():
            return actor
        
        app.dependency_overrides[get_current_actor] = override_get_current_actor
        
        response = client.get("/api/admin/companies/test_company_1/entitlements")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200
    
    def test_customer_service_cannot_list_unassigned_company_entitlements(self, db_session, client):
        """測試：customer_service 不能列出未指派公司的 entitlements"""
        # 建立測試公司
        tenant = Tenant(id="test_company_1", name="Test Company 1")
        db_session.add(tenant)
        db_session.commit()
        
        # Mock actor (未指派)
        actor = Actor(
            user_id=uuid4(),
            role=UserRole.CUSTOMER_SERVICE,
            support_company_assignments={"other_company"}
        )
        
        def override_get_current_actor():
            return actor
        
        app.dependency_overrides[get_current_actor] = override_get_current_actor
        
        response = client.get("/api/admin/companies/test_company_1/entitlements")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["code"] == "SCOPE_FORBIDDEN"
        assert data["detail"]["company_id"] == "test_company_1"
    
    def test_company_user_can_list_own_company_entitlements(self, db_session, client):
        """測試：company_user 可列出所屬公司的 entitlements"""
        # 建立測試公司
        tenant = Tenant(id="test_company_1", name="Test Company 1")
        db_session.add(tenant)
        db_session.commit()
        
        # Mock actor
        actor = Actor(
            user_id=uuid4(),
            role=UserRole.COMPANY_USER,
            company_memberships={"test_company_1"}
        )
        
        def override_get_current_actor():
            return actor
        
        app.dependency_overrides[get_current_actor] = override_get_current_actor
        
        response = client.get("/api/admin/companies/test_company_1/entitlements")
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200
    
    def test_super_admin_can_update_entitlement(self, db_session, client):
        """測試：super_admin 可更新 entitlement"""
        # 建立測試公司
        tenant = Tenant(id="test_company_1", name="Test Company 1")
        db_session.add(tenant)
        db_session.commit()
        
        # 建立測試 user（for updated_by_user_id FK）
        from app.modules.auth.models import User
        user_id = uuid4()
        user = User(id=user_id, display_name="Test Admin", password_hash="dummy")
        db_session.add(user)
        db_session.commit()
        
        # Mock actor
        actor = Actor(user_id=user_id, role=UserRole.SUPER_ADMIN)
        
        def override_get_current_actor():
            return actor
        
        app.dependency_overrides[get_current_actor] = override_get_current_actor
        
        response = client.patch(
            "/api/admin/companies/test_company_1/entitlements",
            json={
                "feature_key": FeatureKeys.ATTENDANCE_SHIFT_TEMPLATES,
                "enabled": True
            }
        )
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200
        data = response.json()
        assert data["company_id"] == "test_company_1"
        assert data["feature_key"] == FeatureKeys.ATTENDANCE_SHIFT_TEMPLATES
        assert data["enabled"] is True
    
    def test_customer_service_cannot_update_entitlement(self, db_session, client):
        """測試：customer_service 不能更新 entitlement"""
        # 建立測試公司
        tenant = Tenant(id="test_company_1", name="Test Company 1")
        db_session.add(tenant)
        db_session.commit()
        
        # Mock actor
        actor = Actor(
            user_id=uuid4(),
            role=UserRole.CUSTOMER_SERVICE,
            support_company_assignments={"test_company_1"}
        )
        
        def override_get_current_actor():
            return actor
        
        app.dependency_overrides[get_current_actor] = override_get_current_actor
        
        response = client.patch(
            "/api/admin/companies/test_company_1/entitlements",
            json={
                "feature_key": FeatureKeys.ATTENDANCE_SHIFT_TEMPLATES,
                "enabled": True
            }
        )
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 403
        data = response.json()
        assert "Only super_admin" in data["detail"]["message"]
    
    def test_update_entitlement_validates_feature_key(self, db_session, client):
        """測試：更新 entitlement 時驗證 feature key"""
        # 建立測試公司
        tenant = Tenant(id="test_company_1", name="Test Company 1")
        db_session.add(tenant)
        db_session.commit()
        
        # Mock actor
        actor = Actor(user_id=uuid4(), role=UserRole.SUPER_ADMIN)
        
        def override_get_current_actor():
            return actor
        
        app.dependency_overrides[get_current_actor] = override_get_current_actor
        
        response = client.patch(
            "/api/admin/companies/test_company_1/entitlements",
            json={
                "feature_key": "invalid.feature.key",
                "enabled": True
            }
        )
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 400
    
    def test_super_admin_can_apply_plan_defaults(self, db_session, client):
        """測試：super_admin 可套用 plan defaults"""
        # 建立測試公司
        tenant = Tenant(id="test_company_1", name="Test Company 1")
        db_session.add(tenant)
        db_session.commit()
        
        # 建立測試 user（for updated_by_user_id FK）
        from app.modules.auth.models import User
        user_id = uuid4()
        user = User(id=user_id, display_name="Test Admin", password_hash="dummy")
        db_session.add(user)
        db_session.commit()
        
        # Mock actor
        actor = Actor(user_id=user_id, role=UserRole.SUPER_ADMIN)
        
        def override_get_current_actor():
            return actor
        
        app.dependency_overrides[get_current_actor] = override_get_current_actor
        
        response = client.post(
            "/api/admin/companies/test_company_1/entitlements/apply-plan",
            json={"plan_code": "Basic"}
        )
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200
        data = response.json()
        assert data["company_id"] == "test_company_1"
        assert data["plan_code"] == "Basic"
        assert data["updated_count"] > 0
    
    def test_update_entitlement_clears_cache(self, db_session, client):
        """測試：更新 entitlement 後清除快取"""
        # 建立測試 user（for updated_by_user_id FK）
        from app.modules.auth.models import User
        user_id = uuid4()
        user = User(id=user_id, display_name="Test Admin", password_hash="dummy")
        db_session.add(user)
        
        # 建立測試公司
        tenant = Tenant(id="test_company_1", name="Test Company 1")
        db_session.add(tenant)
        db_session.flush()  # 確保 tenant 先寫入，滿足 FK 約束
        
        # 建立初始 entitlement
        entitlement = CompanyEntitlement(
            id=uuid4(),
            company_id="test_company_1",
            feature_key=FeatureKeys.ATTENDANCE_SHIFT_TEMPLATES,
            enabled=False
        )
        db_session.add(entitlement)
        db_session.commit()
        
        # Mock actor
        actor = Actor(user_id=user_id, role=UserRole.SUPER_ADMIN)
        
        def override_get_current_actor():
            return actor
        
        app.dependency_overrides[get_current_actor] = override_get_current_actor
        
        # 更新 entitlement
        response = client.patch(
            "/api/admin/companies/test_company_1/entitlements",
            json={
                "feature_key": FeatureKeys.ATTENDANCE_SHIFT_TEMPLATES,
                "enabled": True
            }
        )
        
        app.dependency_overrides.clear()
        
        assert response.status_code == 200
        
        # 驗證資料庫已更新
        db_session.refresh(entitlement)
        assert entitlement.enabled is True
