"""Phase 1B legacy role cleanup regression tests for attendance sessions."""

import inspect

from app.modules.attendance.api import get_sessions_reporting


def test_phase1b_sessions_branch_only_allows_manager():
    src = inspect.getsource(get_sessions_reporting)
    assert 'actor.active_role_id == "manager"' in src
    assert 'active_role_id in ("admin", "manager", "hr")' not in src


def test_phase1b_admin_and_hr_not_in_sessions_admin_like_branch():
    src = inspect.getsource(get_sessions_reporting)
    assert '"admin", "manager", "hr"' not in src
    assert '"admin"' not in src.split('is_admin =', 1)[1].split('\\n', 1)[0]
    assert '"hr"' not in src.split('is_admin =', 1)[1].split('\\n', 1)[0]
