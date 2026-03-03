"""Auth Repository Tests

WP-10-03: Auth Repository + Password Hashing
Tests tenant-aware queries and password hashing
"""

import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.modules.auth.repo import AuthRepository
from app.core.security.password import hash_password, verify_password


# Test database setup (use real PostgreSQL connection from config)
@pytest.fixture(scope="function")
def db_session():
    """Create test database session using real PostgreSQL"""
    from app.core.config import settings
    from app.modules.tenants.models import Tenant
    
    engine = create_engine(str(settings.database_url))
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Create test tenants
    tenant1 = Tenant(id="test-company-001", name="Test Company 001", is_active=True, timezone="UTC")
    tenant2 = Tenant(id="test-company-002", name="Test Company 002", is_active=True, timezone="UTC")
    session.add(tenant1)
    session.add(tenant2)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()  # Tenants already exist
    
    yield session
    yield session
    
    # Cleanup: delete test data (cascade will delete users)
    try:
        session.rollback()  # Rollback any pending transactions
        session.query(Tenant).filter(Tenant.id.in_(["test-company-001", "test-company-002"])).delete(synchronize_session=False)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()
    yield session
    
    # Cleanup: delete test data (cascade will delete users)
    try:
        session.rollback()  # Rollback any pending transactions
        session.query(Tenant).filter(Tenant.id.in_(["test-company-001", "test-company-002"])).delete(synchronize_session=False)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()
    yield session
    
    # Cleanup: delete test data (cascade will delete users)
    try:
        session.rollback()  # Rollback any pending transactions
        session.query(Tenant).filter(Tenant.id.in_(["test-company-001", "test-company-002"])).delete(synchronize_session=False)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()
    yield session
    
    # Cleanup: delete test data (cascade will delete users)
    try:
        session.rollback()  # Rollback any pending transactions
        session.query(Tenant).filter(Tenant.id.in_(["test-company-001", "test-company-002"])).delete(synchronize_session=False)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()
    yield session
    
    # Cleanup: delete test data (cascade will delete users)
    try:
        session.rollback()  # Rollback any pending transactions
        session.query(Tenant).filter(Tenant.id.in_(["test-company-001", "test-company-002"])).delete(synchronize_session=False)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


@pytest.fixture
def auth_repo(db_session):
    """Create AuthRepository instance"""
    return AuthRepository(db_session)


@pytest.fixture
def sample_company_id():
    """Sample company ID"""
    return "test-company-001"


@pytest.fixture
def another_company_id():
    """Another company ID"""
    return "test-company-002"


# ============================================================================
# Password Hashing Tests
# ============================================================================

def test_create_user_hashes_password(auth_repo, sample_company_id):
    """Test that create_user automatically hashes password"""
    plain_password = "SecurePassword123!"
    
    user = auth_repo.create_user(
        company_id=sample_company_id,
        username="testuser_hash",
        email="testhash@example.com",
        plain_password=plain_password
    )
    
    # Password should be hashed (not plaintext)
    assert user.password_hash != plain_password
    assert len(user.password_hash) > 50  # Bcrypt hashes are long
    assert user.password_hash.startswith("$2b$")  # Bcrypt prefix


def test_verify_password_success(auth_repo, sample_company_id):
    """Test password verification succeeds with correct password"""
    plain_password = "CorrectPassword456"
    
    user = auth_repo.create_user(
        company_id=sample_company_id,
        username="testuser_verify",
        email="testverify@example.com",
        plain_password=plain_password
    )
    
    # Verify correct password
    assert auth_repo.verify_user_password(user, plain_password) is True


def test_verify_password_failure(auth_repo, sample_company_id):
    """Test password verification fails with incorrect password"""
    plain_password = "CorrectPassword456"
    wrong_password = "WrongPassword789"
    
    user = auth_repo.create_user(
        company_id=sample_company_id,
        username="testuser_wrong",
        email="testwrong@example.com",
        plain_password=plain_password
    )
    
    # Verify wrong password fails
    assert auth_repo.verify_user_password(user, wrong_password) is False


def test_hash_password_utility():
    """Test hash_password utility function"""
    plain = "TestPassword123"
    hashed = hash_password(plain)
    
    assert hashed != plain
    assert len(hashed) > 50
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


# ============================================================================
# Tenant-Aware Query Tests
# ============================================================================

def test_get_user_requires_company_id(auth_repo, sample_company_id):
    """Test that all user queries require company_id"""
    # Create user
    user = auth_repo.create_user(
        company_id=sample_company_id,
        username="testuser_query",
        email="testquery@example.com",
        plain_password="password123"
    )
    
    # Get by username requires company_id
    found = auth_repo.get_user_by_username(sample_company_id, "testuser_query")
    assert found is not None
    assert found.id == user.id
    
    # Get by email requires company_id
    found = auth_repo.get_user_by_email(sample_company_id, "testquery@example.com")
    assert found is not None
    assert found.id == user.id
    
    # Get by id requires company_id
    found = auth_repo.get_user_by_id(sample_company_id, user.id)
    assert found is not None
    assert found.id == user.id


def test_cross_tenant_query_returns_none(auth_repo, sample_company_id, another_company_id):
    """Test that querying with wrong company_id returns None"""
    # Create user in company A
    user = auth_repo.create_user(
        company_id=sample_company_id,
        username="testuser_cross",
        email="testcross@example.com",
        plain_password="password123"
    )
    
    # Query with company B should return None
    found = auth_repo.get_user_by_username(another_company_id, "testuser_cross")
    assert found is None
    
    found = auth_repo.get_user_by_email(another_company_id, "testcross@example.com")
    assert found is None
    
    found = auth_repo.get_user_by_id(another_company_id, user.id)
    assert found is None


# ============================================================================
# Per-Tenant Uniqueness Tests
# ============================================================================

def test_same_company_duplicate_username_fails(auth_repo, sample_company_id):
    """Test that duplicate username in same company fails"""
    # Create first user
    auth_repo.create_user(
        company_id=sample_company_id,
        username="duplicate_user",
        email="user1_dup@example.com",
        plain_password="password123"
    )
    
    # Try to create second user with same username in same company
    with pytest.raises(IntegrityError):
        auth_repo.create_user(
            company_id=sample_company_id,
            username="duplicate_user",
            email="user2_dup@example.com",
            plain_password="password456"
        )


def test_same_company_duplicate_email_fails(auth_repo, sample_company_id):
    """Test that duplicate email in same company fails"""
    # Create first user
    auth_repo.create_user(
        company_id=sample_company_id,
        username="user1_email",
        email="duplicate@example.com",
        plain_password="password123"
    )
    
    # Try to create second user with same email in same company
    with pytest.raises(IntegrityError):
        auth_repo.create_user(
            company_id=sample_company_id,
            username="user2_email",
            email="duplicate@example.com",
            plain_password="password456"
        )


def test_different_company_same_username_succeeds(auth_repo, sample_company_id, another_company_id):
    """Test that same username in different companies succeeds"""
    # Create user in company A
    user_a = auth_repo.create_user(
        company_id=sample_company_id,
        username="shared_username",
        email="usera_shared@example.com",
        plain_password="password123"
    )
    
    # Create user with same username in company B (should succeed)
    user_b = auth_repo.create_user(
        company_id=another_company_id,
        username="shared_username",
        email="userb_shared@example.com",
        plain_password="password456"
    )
    
    # Both users should exist
    assert user_a.id != user_b.id
    assert user_a.company_id == sample_company_id
    assert user_b.company_id == another_company_id
    assert user_a.username == user_b.username


def test_different_company_same_email_succeeds(auth_repo, sample_company_id, another_company_id):
    """Test that same email in different companies succeeds"""
    # Create user in company A
    user_a = auth_repo.create_user(
        company_id=sample_company_id,
        username="usera_email",
        email="shared_email@example.com",
        plain_password="password123"
    )
    
    # Create user with same email in company B (should succeed)
    user_b = auth_repo.create_user(
        company_id=another_company_id,
        username="userb_email",
        email="shared_email@example.com",
        plain_password="password456"
    )
    
    # Both users should exist
    assert user_a.id != user_b.id
    assert user_a.company_id == sample_company_id
    assert user_b.company_id == another_company_id
    assert user_a.email == user_b.email


# ============================================================================
# Additional Repository Tests
# ============================================================================

def test_update_password(auth_repo, sample_company_id):
    """Test password update"""
    old_password = "OldPassword123"
    new_password = "NewPassword456"
    
    user = auth_repo.create_user(
        company_id=sample_company_id,
        username="testuser_update",
        email="testupdate@example.com",
        plain_password=old_password
    )
    
    old_hash = user.password_hash
    
    # Update password
    updated_user = auth_repo.update_password(user, new_password)
    
    # Hash should change
    assert updated_user.password_hash != old_hash
    
    # Old password should fail
    assert auth_repo.verify_user_password(updated_user, old_password) is False
    
    # New password should succeed
    assert auth_repo.verify_user_password(updated_user, new_password) is True


def test_update_last_login(auth_repo, sample_company_id):
    """Test last login update"""
    user = auth_repo.create_user(
        company_id=sample_company_id,
        username="testuser_login",
        email="testlogin@example.com",
        plain_password="password123"
    )
    
    assert user.last_login_at is None
    
    # Update last login
    updated_user = auth_repo.update_last_login(user)
    
    assert updated_user.last_login_at is not None


def test_assign_role(auth_repo, sample_company_id):
    """Test role assignment"""
    # Create user
    user = auth_repo.create_user(
        company_id=sample_company_id,
        username="testuser_role",
        email="testrole@example.com",
        plain_password="password123"
    )
    
    # Assign role (note: role must exist in DB from migration)
    user_role = auth_repo.assign_role(
        company_id=sample_company_id,
        user_id=user.id,
        role_id="employee"
    )
    
    assert user_role.user_id == user.id
    assert user_role.role_id == "employee"
    assert user_role.company_id == sample_company_id


def test_user_flags(auth_repo, sample_company_id):
    """Test user status flags"""
    user = auth_repo.create_user(
        company_id=sample_company_id,
        username="testuser_flags",
        email="testflags@example.com",
        plain_password="password123",
        is_active=False,
        is_otp=True,
        must_change_password=True
    )
    
    assert user.is_active is False
    assert user.is_otp is True
    assert user.must_change_password is True
