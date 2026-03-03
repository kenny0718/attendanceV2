"""Auth module test fixtures

WP-10-02B: Platform-First v2 test fixtures
"""

import pytest
import uuid
from app.modules.tenants.models import Tenant
from app.modules.auth.models import Role, Permission, RolePermission


@pytest.fixture(scope="function")
def seed_roles(db):
    """Seed roles data (required for FK constraints)"""
    roles_data = [
        ("employee", "Employee", "Regular employee (can create own attendance)"),
        ("manager", "Manager", "Can approve attendance for team members"),
        ("company_admin", "Company Admin", "Full access within company"),
        ("customer_service", "Customer Service", "Can access multiple companies (assigned list)"),
    ]
    
    for role_id, name, description in roles_data:
        role = Role(id=role_id, name=name, description=description)
        db.add(role)
    
    db.commit()


@pytest.fixture(scope="function")
def seed_permissions(db):
    """Seed permissions data"""
    permissions_data = [
        ("attendance:create:self", "attendance", "create:self", "Create own attendance record"),
        ("attendance:approve", "attendance", "approve", "Approve attendance records"),
        ("notifications:read:self", "notifications", "read:self", "Read own notifications"),
        ("backup:export", "backup", "export", "Export company backup"),
        ("backup:restore", "backup", "restore", "Restore company backup"),
        ("audit:read", "audit", "read", "Read audit logs"),
        ("audit:export", "audit", "export", "Export audit logs"),
        ("audit:manage", "audit", "manage", "Manage audit retention policies"),
        ("audit:purge", "audit", "purge", "Purge old audit logs"),
        ("tenants:read", "tenants", "read", "Read tenant information"),
        ("tenants:manage", "tenants", "manage", "Manage tenants"),
    ]
    
    for perm_id, resource, action, description in permissions_data:
        permission = Permission(id=perm_id, resource=resource, action=action, description=description)
        db.add(permission)
    
    db.commit()


@pytest.fixture(scope="function")
def seed_role_permissions(db, seed_roles, seed_permissions):
    """Seed role-permission mappings"""
    role_permissions_data = [
        # employee
        ("employee", "attendance:create:self"),
        ("employee", "notifications:read:self"),
        # manager
        ("manager", "attendance:create:self"),
        ("manager", "attendance:approve"),
        ("manager", "notifications:read:self"),
        ("manager", "audit:read"),
        # company_admin
        ("company_admin", "attendance:create:self"),
        ("company_admin", "attendance:approve"),
        ("company_admin", "notifications:read:self"),
        ("company_admin", "backup:export"),
        ("company_admin", "backup:restore"),
        ("company_admin", "audit:read"),
        ("company_admin", "audit:export"),
        ("company_admin", "audit:manage"),
        ("company_admin", "audit:purge"),
        ("company_admin", "tenants:read"),
        ("company_admin", "tenants:manage"),
        # customer_service
        ("customer_service", "attendance:approve"),
        ("customer_service", "audit:read"),
        ("customer_service", "tenants:read"),
    ]
    
    for role_id, permission_id in role_permissions_data:
        rp = RolePermission(id=uuid.uuid4(), role_id=role_id, permission_id=permission_id)
        db.add(rp)
    
    db.commit()


@pytest.fixture
def test_tenant(db, seed_roles):
    """Create test tenant (company-A)"""
    tenant = Tenant(
        id="company-A",
        name="Company A",
        is_active=True,
        timezone="Asia/Taipei"
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def test_tenant_b(db, seed_roles):
    """Create second test tenant (company-B)"""
    tenant = Tenant(
        id="company-B",
        name="Company B",
        is_active=True,
        timezone="Asia/Taipei"
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant
