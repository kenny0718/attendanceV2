"""Test authentication helpers for JWT Actor migration (WP-C1-05)

用途：
- 透過 FastAPI dependency_overrides 注入測試用 Actor
- 不需要產生 JWT token，不需要資料庫查詢

使用方式：
    from app.tests.utils.auth import create_test_actor, override_actor_dependency

    actor = create_test_actor("company-A", role_id="company_admin")
    with override_actor_dependency(actor):
        response = client.get("/api/notifications")
        assert response.status_code == 200

A1-3c: override_all_auth_dependencies removed — all production endpoints
have migrated to JWT actor (get_actor_with_company). Use override_actor_dependency.
"""

from contextlib import contextmanager
from typing import Optional
from uuid import UUID

from app.core.dependencies import get_actor_with_company
from app.core.scope import Actor, UserRole
from app.main import app


# 固定測試用 UUID，確保可重現
DEFAULT_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _normalize_test_role_id(role_id: str) -> str:
    """Normalize retired test alias to current role ids."""
    return "company_admin" if role_id == "admin" else role_id


def create_test_actor(
    company_id: str,
    user_id: Optional[UUID] = None,
    role_id: str = "employee",
    platform_role: UserRole = UserRole.COMPANY_USER,
) -> Actor:
    """
    建立測試用 Actor，無需 JWT token 或資料庫查詢。

    Args:
        company_id: 測試公司 ID（對應 active_company_id）
        user_id: 測試使用者 UUID（預設使用固定 UUID）
        role_id: 公司內角色（"company_admin" / "employee" / "hr_manager"）
        platform_role: 平台層角色（預設 COMPANY_USER）

    Returns:
        Actor: 可直接注入 FastAPI dependency 的測試 Actor
    """
    normalized_role_id = _normalize_test_role_id(role_id)
    return Actor(
        user_id=user_id or DEFAULT_USER_ID,
        role=platform_role,
        company_memberships={company_id},
        active_company_id=company_id,
        active_role_id=normalized_role_id,
    )


def create_super_admin_actor(
    company_id: Optional[str] = None,
    user_id: Optional[UUID] = None,
) -> Actor:
    """建立 super_admin 測試 Actor"""
    return Actor(
        user_id=user_id or DEFAULT_USER_ID,
        role=UserRole.SUPER_ADMIN,
        company_memberships=set(),
        active_company_id=company_id,
        active_role_id="super_admin",
    )


@contextmanager
def override_actor_dependency(actor: Actor):
    """
    Context manager：暫時覆寫 get_actor_with_company dependency。
    """
    app.dependency_overrides[get_actor_with_company] = lambda: actor
    try:
        yield actor
    finally:
        app.dependency_overrides.pop(get_actor_with_company, None)
