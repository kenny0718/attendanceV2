"""Phase 1A legacy role cleanup regression tests."""

import inspect

from app.core.dependencies import _map_role_id_to_user_role
from app.core.scope import UserRole


def test_phase1a_removed_admin_hr_explicit_company_user_mappings():
    src = inspect.getsource(_map_role_id_to_user_role)
    assert '"admin": UserRole.COMPANY_USER' not in src
    assert '"hr": UserRole.COMPANY_USER' not in src


def test_phase1a_admin_hr_still_resolve_to_company_user_via_default_path():
    assert _map_role_id_to_user_role("admin") == UserRole.COMPANY_USER
    assert _map_role_id_to_user_role("hr") == UserRole.COMPANY_USER


def test_phase1a_manager_and_system_admin_mapping_remain_intact():
    assert _map_role_id_to_user_role("manager") == UserRole.COMPANY_USER
    assert _map_role_id_to_user_role("system_admin") == UserRole.SUPER_ADMIN
