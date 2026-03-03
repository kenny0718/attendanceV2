"""Tenant Context Tests

WP-10-03B: Test membership validation in tenant context
"""

import pytest
import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.tenant_context import (
    get_current_company_id,
    get_current_company_id_with_membership
)
from app.modules.tenants.models import Tenant
from app.modules.auth.models import User, Membership, Role


@pytest.fixture
def test_tenant(db: Session):
    """Create test tenant"""
    tenant = Tenant(
        id="company-test",
        name="Test Company",
        is_active=True,
        timezone="Asia/Taipei"
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def inactive_tenant(db: Session):
    """Create inactive tenant"""
    tenant = Tenant(
        id="company-inactive",
        name="Inactive Company",
        is_active=False,
        timezone="Asia/Taipei"
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def test_role(db: Session):
    """Create test role"""
    role = Role(
        id="employee",
        name="Employee",
        description="Regular employee"
    )
    db.add(role)
    db.commit()
    return role


@pytest.fixture
def test_user(db: Session):
    """Create test user"""
    user = User(
        id=uuid.uuid4(),
        display_name="Test User",
        password_hash="hashed_password",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_membership(db: Session, test_user, test_tenant, test_role):
    """Create test membership"""
    membership = Membership(
        id=uuid.uuid4(),
        user_id=test_user.id,
        company_id=test_tenant.id,
        role_id=test_role.id,
        login_username="testuser",
        is_active=True
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


class TestGetCurrentCompanyId:
    """Test get_current_company_id (without membership validation)"""
    
    def test_valid_tenant(self, db: Session, test_tenant):
        """Test with valid tenant"""
        company_id = get_current_company_id(
            x_company_id=test_tenant.id,
            db=db
        )
        assert company_id == test_tenant.id
    
    def test_missing_header(self, db: Session):
        """Test with missing X-Company-ID header"""
        with pytest.raises(HTTPException) as exc_info:
            get_current_company_id(x_company_id="", db=db)
        
        assert exc_info.value.status_code == 400
        assert "Missing X-Company-ID header" in str(exc_info.value.detail)
    
    def test_tenant_not_exists(self, db: Session):
        """Test with non-existent tenant"""
        with pytest.raises(HTTPException) as exc_info:
            get_current_company_id(x_company_id="nonexistent", db=db)
        
        assert exc_info.value.status_code == 404
        assert "does not exist" in str(exc_info.value.detail)
    
    def test_tenant_not_active(self, db: Session, inactive_tenant):
        """Test with inactive tenant"""
        with pytest.raises(HTTPException) as exc_info:
            get_current_company_id(x_company_id=inactive_tenant.id, db=db)
        
        assert exc_info.value.status_code == 403
        assert "not active" in str(exc_info.value.detail)


class TestGetCurrentCompanyIdWithMembership:
    """Test get_current_company_id_with_membership (with membership validation)"""
    
    def test_valid_membership(self, db: Session, test_user, test_tenant, test_membership):
        """Test with valid membership"""
        company_id = get_current_company_id_with_membership(
            x_company_id=test_tenant.id,
            x_user_id=str(test_user.id),
            db=db
        )
        assert company_id == test_tenant.id
    
    def test_missing_company_id_header(self, db: Session, test_user):
        """Test with missing X-Company-ID header"""
        with pytest.raises(HTTPException) as exc_info:
            get_current_company_id_with_membership(
                x_company_id="",
                x_user_id=str(test_user.id),
                db=db
            )
        
        assert exc_info.value.status_code == 400
        assert "Missing X-Company-ID header" in str(exc_info.value.detail)
    
    def test_missing_user_id_header(self, db: Session, test_tenant):
        """Test with missing X-User-ID header"""
        with pytest.raises(HTTPException) as exc_info:
            get_current_company_id_with_membership(
                x_company_id=test_tenant.id,
                x_user_id="",
                db=db
            )
        
        assert exc_info.value.status_code == 400
        assert "Missing X-User-ID header" in str(exc_info.value.detail)
    
    def test_invalid_user_id_format(self, db: Session, test_tenant):
        """Test with invalid UUID format"""
        with pytest.raises(HTTPException) as exc_info:
            get_current_company_id_with_membership(
                x_company_id=test_tenant.id,
                x_user_id="not-a-uuid",
                db=db
            )
        
        assert exc_info.value.status_code == 400
        assert "Invalid X-User-ID format" in str(exc_info.value.detail)
    
    def test_tenant_not_exists(self, db: Session, test_user):
        """Test with non-existent tenant"""
        with pytest.raises(HTTPException) as exc_info:
            get_current_company_id_with_membership(
                x_company_id="nonexistent",
                x_user_id=str(test_user.id),
                db=db
            )
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)
    
    def test_tenant_not_active(self, db: Session, test_user, inactive_tenant):
        """Test with inactive tenant"""
        with pytest.raises(HTTPException) as exc_info:
            get_current_company_id_with_membership(
                x_company_id=inactive_tenant.id,
                x_user_id=str(test_user.id),
                db=db
            )
        
        assert exc_info.value.status_code == 403
        assert "not active" in str(exc_info.value.detail)
    
    def test_no_membership_returns_404(self, db: Session, test_user, test_tenant):
        """Test anti-enumeration: no membership returns 404 (not 403)"""
        # User exists, tenant exists, but no membership
        with pytest.raises(HTTPException) as exc_info:
            get_current_company_id_with_membership(
                x_company_id=test_tenant.id,
                x_user_id=str(test_user.id),
                db=db
            )
        
        # Anti-enumeration: should return 404, not 403
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)
    
    def test_inactive_membership_returns_404(self, db: Session, test_user, test_tenant, test_role):
        """Test anti-enumeration: inactive membership returns 404"""
        # Create inactive membership
        membership = Membership(
            id=uuid.uuid4(),
            user_id=test_user.id,
            company_id=test_tenant.id,
            role_id=test_role.id,
            login_username="testuser",
            is_active=False  # Inactive
        )
        db.add(membership)
        db.commit()
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_company_id_with_membership(
                x_company_id=test_tenant.id,
                x_user_id=str(test_user.id),
                db=db
            )
        
        # Anti-enumeration: should return 404, not 403
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)
    
    def test_nonexistent_user_returns_404(self, db: Session, test_tenant):
        """Test with non-existent user"""
        fake_user_id = uuid.uuid4()
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_company_id_with_membership(
                x_company_id=test_tenant.id,
                x_user_id=str(fake_user_id),
                db=db
            )
        
        # Should return 404 (no membership)
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)
