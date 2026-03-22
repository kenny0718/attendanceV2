"""Scope 檢查機制

統一處理 SuperAdmin / customer_service / company user 的權限範圍。
遵守 SA_MODULE_SPEC v2.0 的順序：Scope → Tenant Isolation → Feature Gate

WP-11-04A: Company Entitlements + SuperAdmin 管理 + customer_service Scope
WP-C1-02 Step 1: Actor 加入 active_company_id（JWT company scope），
               並新增 is_admin() / is_employee() RBAC 輔助方法。

架構原則（SA v2.0 多公司）：
- Actor 不儲存「唯一」company_id；User 天生是跨公司的 Global Identity
- active_company_id 代表「本次請求」的公司範圍，來自 JWT claim company_id
- 每次請求都必須以 active_company_id 對照 company_memberships / support_company_assignments 驗證
- admin / employee 區分來自 Membership.role_id，儲存在 active_role_id
"""
from typing import Optional, Set
from enum import Enum
from sqlalchemy.orm import Session
from uuid import UUID


class UserRole(Enum):
    """平台層級角色（Platform-level role）

    注意：這三個值代表平台身份，不代表公司內部職位（admin / employee）。
    公司內部職位由 Membership.role_id 決定，透過 Actor.active_role_id 暴露。
    """
    SUPER_ADMIN = "super_admin"
    CUSTOMER_SERVICE = "customer_service"
    COMPANY_USER = "company_user"


class ScopeError(Exception):
    """權限範圍錯誤"""
    def __init__(self, message: str, company_id: Optional[str] = None):
        self.message = message
        self.company_id = company_id
        super().__init__(message)


class Actor:
    """操作者資訊

    封裝當前使用者的身份和權限資訊。

    WP-C1-02 Step 1 變更：
    - 新增 active_company_id：本次請求的公司範圍（來自 JWT claim company_id）
    - 新增 active_role_id：本次請求公司內部角色（來自 Membership.role_id）
    - 新增 is_admin() / is_employee()：公司內部 RBAC 輔助方法
    - Actor 不儲存全局 company_id；active_company_id 僅代表此次請求的 scope

    SA v2.0 多公司設計：
    - User 是 Global Identity（可屬於多個公司）
    - 每次請求透過 JWT company_id 鎖定當前操作範圍
    - company_memberships 存放所有公司 ID（用於跨請求驗證）
    """

    def __init__(
        self,
        user_id: UUID,
        role: UserRole,
        company_memberships: Optional[Set[str]] = None,
        support_company_assignments: Optional[Set[str]] = None,
        # WP-C1-02 Step 1：新增欄位
        active_company_id: Optional[str] = None,
        active_role_id: Optional[str] = None,
    ):
        self.user_id = user_id
        self.role = role
        self.company_memberships = company_memberships or set()
        self.support_company_assignments = support_company_assignments or set()
        # 本次請求的公司範圍（由 JWT company_id 決定，經 membership 驗證）
        self.active_company_id = active_company_id
        # 本次請求在 active_company_id 公司內的角色 ID（如 'admin', 'employee'）
        self.active_role_id = active_role_id

    # ── 平台層級角色查詢 ──────────────────────────────────────────────

    def is_super_admin(self) -> bool:
        """是否為 Super Admin（平台層）"""
        return self.role == UserRole.SUPER_ADMIN

    def is_customer_service(self) -> bool:
        """是否為客服（平台層）"""
        return self.role == UserRole.CUSTOMER_SERVICE

    def is_company_user(self) -> bool:
        """是否為一般公司使用者（平台層）"""
        return self.role == UserRole.COMPANY_USER

    # ── 公司內部 RBAC（依 active_role_id）────────────────────────────

    def is_admin(self) -> bool:
        """是否為所在公司的管理員

        判斷依據：active_role_id in ('admin', 'manager', 'hr')
        Super Admin 一律視為 admin。

        Returns:
            bool
        """
        if self.is_super_admin():
            return True
        if self.active_role_id is None:
            return False
        return self.active_role_id.lower() in ("admin", "manager", "hr", "company_admin", "hr_manager")

    def is_employee(self) -> bool:
        """是否為一般員工（非管理員）

        Returns:
            bool
        """
        if self.active_role_id is None:
            return False
        return self.active_role_id.lower() == "employee"

    def has_active_company(self) -> bool:
        """是否持有有效的公司範圍

        Super Admin 不需要 membership，直接回傳 True。
        其他角色必須有 active_company_id 才算有效。

        Returns:
            bool
        """
        if self.is_super_admin():
            return True
        return self.active_company_id is not None


class ScopeChecker:
    """Scope 檢查器

    提供統一的權限範圍檢查邏輯。
    """

    def __init__(self, db: Session):
        self.db = db

    def assert_company_scope(self, actor: Actor, company_id: str) -> None:
        """檢查操作者是否有權限操作指定公司

        規則：
        - super_admin: 直接通過
        - customer_service: 必須在 support_company_assignments 中
        - company_user: 必須在 company_memberships 中，
                        且若 actor 有 active_company_id，必須與 company_id 一致

        Args:
            actor: 操作者資訊
            company_id: 目標公司 ID

        Raises:
            ScopeError: 無權限操作該公司（HTTP 403）
        """
        # Super Admin 可操作所有公司
        if actor.is_super_admin():
            return

        # Customer Service 只能操作被指派的公司
        if actor.is_customer_service():
            if company_id not in actor.support_company_assignments:
                raise ScopeError(
                    f"Customer service user {actor.user_id} is not assigned to company {company_id}",
                    company_id=company_id
                )
            return

        # Company User：membership 驗證 + active scope 一致性驗證
        if actor.is_company_user():
            if company_id not in actor.company_memberships:
                raise ScopeError(
                    f"User {actor.user_id} is not a member of company {company_id}",
                    company_id=company_id
                )
            # 若 actor 攜帶 active_company_id（來自 JWT），必須與請求的 company_id 一致
            if (
                actor.active_company_id is not None
                and actor.active_company_id != company_id
            ):
                raise ScopeError(
                    f"JWT company scope ({actor.active_company_id}) does not match "
                    f"requested company ({company_id})",
                    company_id=company_id
                )
            return

        # 未知角色，拒絕存取
        raise ScopeError(f"Unknown role: {actor.role}")

    def assert_admin_scope(self, actor: Actor, company_id: str) -> None:
        """檢查操作者是否為指定公司的管理員

        用於 admin_location_api.py 等需要 RBAC 的端點。

        Raises:
            ScopeError: 非管理員角色
        """
        # 先通過公司範圍驗證
        self.assert_company_scope(actor, company_id)

        # Super Admin 免 admin 角色驗證
        if actor.is_super_admin():
            return

        if not actor.is_admin():
            raise ScopeError(
                f"User {actor.user_id} does not have admin role in company {company_id} "
                f"(active_role_id={actor.active_role_id})",
                company_id=company_id
            )

    def get_accessible_companies(self, actor: Actor) -> Set[str]:
        """取得操作者可存取的所有公司 ID

        Args:
            actor: 操作者資訊

        Returns:
            Set[str]: 可存取的公司 ID 集合
        """
        if actor.is_super_admin():
            return self._get_all_company_ids()

        if actor.is_customer_service():
            return actor.support_company_assignments

        if actor.is_company_user():
            return actor.company_memberships

        return set()

    def _get_all_company_ids(self) -> Set[str]:
        """從資料庫取得所有公司 ID"""
        from app.modules.tenants.models import Tenant
        results = self.db.query(Tenant.id).all()
        return {row[0] for row in results}


# ── 便捷函數 ──────────────────────────────────────────────────────────

def assert_company_scope(actor: Actor, company_id: str, db: Session) -> None:
    """便捷函數：檢查公司權限範圍

    Args:
        actor: 操作者資訊
        company_id: 目標公司 ID
        db: SQLAlchemy Session

    Raises:
        ScopeError: 無權限操作該公司
    """
    checker = ScopeChecker(db)
    checker.assert_company_scope(actor, company_id)


def assert_admin_scope(actor: Actor, company_id: str, db: Session) -> None:
    """便捷函數：檢查管理員權限範圍

    Args:
        actor: 操作者資訊
        company_id: 目標公司 ID
        db: SQLAlchemy Session

    Raises:
        ScopeError: 非管理員角色
    """
    checker = ScopeChecker(db)
    checker.assert_admin_scope(actor, company_id)


def get_accessible_companies(actor: Actor, db: Session) -> Set[str]:
    """便捷函數：取得可存取的公司列表

    Args:
        actor: 操作者資訊
        db: SQLAlchemy Session

    Returns:
        Set[str]: 可存取的公司 ID 集合
    """
    checker = ScopeChecker(db)
    return checker.get_accessible_companies(actor)
