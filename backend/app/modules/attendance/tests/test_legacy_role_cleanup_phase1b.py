"""Phase 1B legacy role cleanup regression tests for attendance sessions."""

import inspect

from app.modules.attendance.api import get_sessions_reporting


def test_phase1b_sessions_branch_uses_normalized_admin_check():
    src = inspect.getsource(get_sessions_reporting)
    assert 'is_admin = actor.is_admin()' in src
    assert 'actor.active_role_id == "manager"' not in src


def test_phase1b_sessions_branch_has_no_legacy_admin_hr_manager_tuple():
    src = inspect.getsource(get_sessions_reporting)
    assert 'active_role_id in ("admin", "manager", "hr")' not in src
    assert '"admin", "manager", "hr"' not in src
