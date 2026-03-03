"""Auth Repository Tests (Platform-First v2)

WP-10-02B: Auth Repository Tests Rewrite
Tests platform-first architecture with Membership model
"""

import pytest
import uuid
from sqlalchemy.orm import Session

from app.modules.auth.repo import AuthRepository
from app.modules.auth.models import User, Membership, Role
from app.core.security.password import verify_password


class TestAuthRepositoryUserCRUD:
    """Test User CRUD operations (global identity, no company_id)"""
    
    def test_create_user_success(self, db: Session):
        """Test creating a user (global identity)"""
        repo = AuthRepository(db)
        
        user = repo.create_user(
            display_name="John Doe",
            plain_password="SecurePass123!",
            email="john@example.com"
        )
        
        assert user.id is not None
        assert user.display_name == "John Doe"
        assert user.email == "john@example.com"
        assert user.password_hash is not None
        assert user.password_hash != "SecurePass123!"  # Should be hashed
        assert user.is_active is True
        assert user.is_otp is False
        assert user.must_change_password is False
        assert verify_password("SecurePass123!", user.password_hash)
    
    def test_create_user_without_email(self, db: Session):
        """Test creating a user without email (email is optional)"""
        repo = AuthRepository(db)
        
        user = repo.create_user(
            display_name="Jane Doe",
            plain_password="SecurePass123!"
        )
        
        assert user.id is not None
        assert user.display_name == "Jane Doe"
        assert user.email is None
    
    def test_create_user_with_otp_flag(self, db: Session):
        """Test creating OTP user"""
        repo = AuthRepository(db)
        
        user = repo.create_user(
            display_name="OTP User",
            plain_password="TempPass123!",
            is_otp=True,
            must_change_password=True
        )
        
        assert user.is_otp is True
        assert user.must_change_password is True
    
    def test_get_user_by_id_success(self, db: Session):
        """Test getting user by ID"""
        repo = AuthRepository(db)
        
        # Create user
        user = repo.create_user(
            display_name="Test User",
            plain_password="Pass123!"
        )
        
        # Get user by ID
        found_user = repo.get_user_by_id(user.id)
        
        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.display_name == "Test User"
    
    def test_get_user_by_id_not_found(self, db: Session):
        """Test getting non-existent user"""
        repo = AuthRepository(db)
        
        non_existent_id = uuid.uuid4()
        user = repo.get_user_by_id(non_existent_id)
        
        assert user is None
    
    def test_update_password(self, db: Session):
        """Test updating user password"""
        repo = AuthRepository(db)
        
        # Create user
        user = repo.create_user(
            display_name="Test User",
            plain_password="OldPass123!"
        )
        
        old_hash = user.password_hash
        
        # Update password
        updated_user = repo.update_password(user, "NewPass456!")
        
        assert updated_user.password_hash != old_hash
        assert verify_password("NewPass456!", updated_user.password_hash)
        assert not verify_password("OldPass123!", updated_user.password_hash)
    
    def test_verify_user_password_correct(self, db: Session):
        """Test verifying correct password"""
        repo = AuthRepository(db)
        
        user = repo.create_user(
            display_name="Test User",
            plain_password="CorrectPass123!"
        )
        
        assert repo.verify_user_password(user, "CorrectPass123!") is True
    
    def test_verify_user_password_incorrect(self, db: Session):
        """Test verifying incorrect password"""
        repo = AuthRepository(db)
        
        user = repo.create_user(
            display_name="Test User",
            plain_password="CorrectPass123!"
        )
        
        assert repo.verify_user_password(user, "WrongPass123!") is False
    
    def test_update_last_login(self, db: Session):
        """Test updating last login timestamp"""
        repo = AuthRepository(db)
        
        user = repo.create_user(
            display_name="Test User",
            plain_password="Pass123!"
        )
        
        assert user.last_login_at is None
        
        updated_user = repo.update_last_login(user)
        
        assert updated_user.last_login_at is not None


class TestAuthRepositoryMembership:
    """Test Membership operations (user-company relationship)"""
    
    def test_create_membership_success(self, db: Session, test_tenant):
        """Test creating membership (link user to company with role)"""
        repo = AuthRepository(db)
        
        # Create user
        user = repo.create_user(
            display_name="John Doe",
            plain_password="Pass123!"
        )
        
        # Create membership
        membership = repo.create_membership(
            user_id=user.id,
            company_id=test_tenant.id,
            role_id="employee",
            login_username="john.doe"
        )
        
        assert membership.id is not None
        assert membership.user_id == user.id
        assert membership.company_id == test_tenant.id
        assert membership.role_id == "employee"
        assert membership.login_username == "john.doe"
        assert membership.is_active is True
    
    def test_create_membership_with_login_email(self, db: Session, test_tenant):
        """Test creating membership with login_email"""
        repo = AuthRepository(db)
        
        user = repo.create_user(
            display_name="Jane Doe",
            plain_password="Pass123!"
        )
        
        membership = repo.create_membership(
            user_id=user.id,
            company_id=test_tenant.id,
            role_id="manager",
            login_username="jane.doe",
            login_email="jane@company.com"
        )
        
        assert membership.login_email == "jane@company.com"
    
    def test_create_membership_duplicate_login_username_fails(self, db: Session, test_tenant):
        """Test that duplicate login_username in same company fails"""
        repo = AuthRepository(db)
        
        # Create first user and membership
        user1 = repo.create_user(display_name="User 1", plain_password="Pass123!")
        repo.create_membership(
            user_id=user1.id,
            company_id=test_tenant.id,
            role_id="employee",
            login_username="duplicate.username"
        )
        
        # Create second user and try same login_username
        user2 = repo.create_user(display_name="User 2", plain_password="Pass123!")
        
        with pytest.raises(Exception):  # IntegrityError
            repo.create_membership(
                user_id=user2.id,
                company_id=test_tenant.id,
                role_id="employee",
                login_username="duplicate.username"
            )
    
    def test_create_membership_duplicate_user_company_fails(self, db: Session, test_tenant):
        """Test that same user cannot have multiple memberships in same company"""
        repo = AuthRepository(db)
        
        user = repo.create_user(display_name="Test User", plain_password="Pass123!")
        
        # Create first membership
        repo.create_membership(
            user_id=user.id,
            company_id=test_tenant.id,
            role_id="employee",
            login_username="user.employee"
        )
        
        # Try to create second membership for same user in same company
        with pytest.raises(Exception):  # IntegrityError
            repo.create_membership(
                user_id=user.id,
                company_id=test_tenant.id,
                role_id="manager",
                login_username="user.manager"
            )
    
    def test_get_membership_by_login_success(self, db: Session, test_tenant):
        """Test getting membership by company_id + login_username"""
        repo = AuthRepository(db)
        
        user = repo.create_user(display_name="Test User", plain_password="Pass123!")
        membership = repo.create_membership(
            user_id=user.id,
            company_id=test_tenant.id,
            role_id="employee",
            login_username="test.user"
        )
        
        found_membership = repo.get_membership_by_login(test_tenant.id, "test.user")
        
        assert found_membership is not None
        assert found_membership.id == membership.id
        assert found_membership.user_id == user.id
    
    def test_get_membership_by_login_not_found(self, db: Session, test_tenant):
        """Test getting non-existent membership"""
        repo = AuthRepository(db)
        
        membership = repo.get_membership_by_login(test_tenant.id, "nonexistent.user")
        
        assert membership is None
    
    def test_get_user_by_login_success(self, db: Session, test_tenant):
        """Test getting user by company_id + login_username (via membership)"""
        repo = AuthRepository(db)
        
        user = repo.create_user(display_name="Test User", plain_password="Pass123!")
        repo.create_membership(
            user_id=user.id,
            company_id=test_tenant.id,
            role_id="employee",
            login_username="test.user"
        )
        
        found_user = repo.get_user_by_login(test_tenant.id, "test.user")
        
        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.display_name == "Test User"
    
    def test_get_user_by_login_not_found(self, db: Session, test_tenant):
        """Test getting user with non-existent login"""
        repo = AuthRepository(db)
        
        user = repo.get_user_by_login(test_tenant.id, "nonexistent.user")
        
        assert user is None
    
    def test_get_user_memberships(self, db: Session, test_tenant, test_tenant_b):
        """Test getting all memberships for a user (multi-company)"""
        repo = AuthRepository(db)
        
        user = repo.create_user(display_name="Multi Company User", plain_password="Pass123!")
        
        # Create memberships in two companies
        membership_a = repo.create_membership(
            user_id=user.id,
            company_id=test_tenant.id,
            role_id="employee",
            login_username="user.companyA"
        )
        
        membership_b = repo.create_membership(
            user_id=user.id,
            company_id=test_tenant_b.id,
            role_id="manager",
            login_username="user.companyB"
        )
        
        memberships = repo.get_user_memberships(user.id)
        
        assert len(memberships) == 2
        membership_ids = [m.id for m in memberships]
        assert membership_a.id in membership_ids
        assert membership_b.id in membership_ids
    
    def test_get_membership(self, db: Session, test_tenant):
        """Test getting specific membership for user in company"""
        repo = AuthRepository(db)
        
        user = repo.create_user(display_name="Test User", plain_password="Pass123!")
        membership = repo.create_membership(
            user_id=user.id,
            company_id=test_tenant.id,
            role_id="employee",
            login_username="test.user"
        )
        
        found_membership = repo.get_membership(user.id, test_tenant.id)
        
        assert found_membership is not None
        assert found_membership.id == membership.id
    
    def test_user_has_company_access_true(self, db: Session, test_tenant):
        """Test user has access to company (active membership exists)"""
        repo = AuthRepository(db)
        
        user = repo.create_user(display_name="Test User", plain_password="Pass123!")
        repo.create_membership(
            user_id=user.id,
            company_id=test_tenant.id,
            role_id="employee",
            login_username="test.user"
        )
        
        assert repo.user_has_company_access(user.id, test_tenant.id) is True
    
    def test_user_has_company_access_false_no_membership(self, db: Session, test_tenant):
        """Test user has no access (no membership)"""
        repo = AuthRepository(db)
        
        user = repo.create_user(display_name="Test User", plain_password="Pass123!")
        
        assert repo.user_has_company_access(user.id, test_tenant.id) is False
    
    def test_user_has_company_access_false_inactive_membership(self, db: Session, test_tenant):
        """Test user has no access (inactive membership)"""
        repo = AuthRepository(db)
        
        user = repo.create_user(display_name="Test User", plain_password="Pass123!")
        membership = repo.create_membership(
            user_id=user.id,
            company_id=test_tenant.id,
            role_id="employee",
            login_username="test.user",
            is_active=False
        )
        
        assert repo.user_has_company_access(user.id, test_tenant.id) is False


class TestAuthRepositoryRole:
    """Test Role queries"""
    
    def test_get_role_success(self, db: Session, seed_roles):
        """Test getting role by ID"""
        repo = AuthRepository(db)
        
        role = repo.get_role("employee")
        
        assert role is not None
        assert role.id == "employee"
        assert role.name == "Employee"
    
    def test_get_role_not_found(self, db: Session, seed_roles):
        """Test getting non-existent role"""
        repo = AuthRepository(db)
        
        role = repo.get_role("nonexistent_role")
        
        assert role is None
