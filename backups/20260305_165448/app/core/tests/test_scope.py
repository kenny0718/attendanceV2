"""Tests for Scope Checker

WP-11-04A: Scope validation tests
"""

import pytest
from uuid import uuid4
from app.core.scope import Actor, UserRole, ScopeChecker, ScopeError
from app.modules.tenants.models import Tenant


class TestScopeChecker:
    """Scope Checker 測試"""
    
    def test_super_admin_can_access_any_company(self, db_session):
        """測試：super_admin 可存取任意公司"""
        checker = ScopeChecker(db_session)
        actor = Actor(
            user_id=uuid4(),
            role=UserRole.SUPER_ADMIN
        )
        
        # 不應拋出異常
        checker.assert_company_scope(actor, "any_company_id")
    
    def test_customer_service_can_access_assigned_company(self, db_session):
        """測試：customer_service 可存取被指派的公司"""
        checker = ScopeChecker(db_session)
        company_id = "test_company_1"
        actor = Actor(
            user_id=uuid4(),
            role=UserRole.CUSTOMER_SERVICE,
            support_company_assignments={company_id}
        )
        
        # 不應拋出異常
        checker.assert_company_scope(actor, company_id)
    
    def test_customer_service_cannot_access_unassigned_company(self, db_session):
        """測試：customer_service 不能存取未指派的公司"""
        checker = ScopeChecker(db_session)
        actor = Actor(
            user_id=uuid4(),
            role=UserRole.CUSTOMER_SERVICE,
            support_company_assignments={"company_1", "company_2"}
        )
        
        with pytest.raises(ScopeError) as exc_info:
            checker.assert_company_scope(actor, "company_3")
        
        assert "not assigned to company" in str(exc_info.value)
        assert exc_info.value.company_id == "company_3"
    
    def test_company_user_can_access_member_company(self, db_session):
        """測試：company_user 可存取所屬公司"""
        checker = ScopeChecker(db_session)
        company_id = "test_company_1"
        actor = Actor(
            user_id=uuid4(),
            role=UserRole.COMPANY_USER,
            company_memberships={company_id}
        )
        
        # 不應拋出異常
        checker.assert_company_scope(actor, company_id)
    
    def test_company_user_cannot_access_non_member_company(self, db_session):
        """測試：company_user 不能存取非所屬公司"""
        checker = ScopeChecker(db_session)
        actor = Actor(
            user_id=uuid4(),
            role=UserRole.COMPANY_USER,
            company_memberships={"company_1"}
        )
        
        with pytest.raises(ScopeError) as exc_info:
            checker.assert_company_scope(actor, "company_2")
        
        assert "not a member of company" in str(exc_info.value)
        assert exc_info.value.company_id == "company_2"
    
    def test_get_accessible_companies_for_super_admin(self, db_session):
        """測試：super_admin 可存取所有公司"""
        # 建立測試公司
        tenant1 = Tenant(id="company_1", name="Company 1")
        tenant2 = Tenant(id="company_2", name="Company 2")
        db_session.add_all([tenant1, tenant2])
        db_session.commit()
        
        checker = ScopeChecker(db_session)
        actor = Actor(
            user_id=uuid4(),
            role=UserRole.SUPER_ADMIN
        )
        
        companies = checker.get_accessible_companies(actor)
        
        assert "company_1" in companies
        assert "company_2" in companies
    
    def test_get_accessible_companies_for_customer_service(self, db_session):
        """測試：customer_service 只能存取被指派的公司"""
        checker = ScopeChecker(db_session)
        actor = Actor(
            user_id=uuid4(),
            role=UserRole.CUSTOMER_SERVICE,
            support_company_assignments={"company_1", "company_2", "company_3"}
        )
        
        companies = checker.get_accessible_companies(actor)
        
        assert companies == {"company_1", "company_2", "company_3"}
    
    def test_get_accessible_companies_for_company_user(self, db_session):
        """測試：company_user 只能存取所屬公司"""
        checker = ScopeChecker(db_session)
        actor = Actor(
            user_id=uuid4(),
            role=UserRole.COMPANY_USER,
            company_memberships={"company_1"}
        )
        
        companies = checker.get_accessible_companies(actor)
        
        assert companies == {"company_1"}
    
    def test_customer_service_with_multiple_assignments(self, db_session):
        """測試：客服可存取多個指派的公司"""
        checker = ScopeChecker(db_session)
        actor = Actor(
            user_id=uuid4(),
            role=UserRole.CUSTOMER_SERVICE,
            support_company_assignments={"company_1", "company_2", "company_3"}
        )
        
        # 可存取所有指派的公司
        checker.assert_company_scope(actor, "company_1")
        checker.assert_company_scope(actor, "company_2")
        checker.assert_company_scope(actor, "company_3")
        
        # 不能存取未指派的公司
        with pytest.raises(ScopeError):
            checker.assert_company_scope(actor, "company_4")
