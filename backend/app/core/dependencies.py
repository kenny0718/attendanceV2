"""FastAPI Dependencies

WP-11-04A: Unified Actor dependency for scope checking
統一的 Actor 取得機制，整合 JWT 驗證與資料庫查詢

WP-C1-02 Step 1 變更：
- get_current_actor() 從 JWT claim company_id 解析 active_company_id，
  並從 Membership 查詢 active_role_id，注入 Actor 物件。
- 新增 get_actor_with_company() Dependency：
  直接從 JWT 取得 active_company_id，驗證 membership，
  供 attendance / admin_location endpoints 使用，取代 X-Company-ID Header。
- _map_role_id_to_user_role() 維持平台層三分法；
  公司內部角色（admin/employee）透過 active_role_id 暴露，不影響平台層角色。

SA v2.0 多公司架構原則：
- Actor 不存單一 company_id；active_company_id 來自 JWT，代表本次請求 scope
- 驗證順序：JWT 解析 → User 存在 → Membership 驗證 → active_role_id 注入
- 不再接受 X-Company-ID Header 作為 fallback
"""

import logging
from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.scope import Actor, UserRole, ScopeError
from app.core.security.jwt import decode_access_token
from app.modules.auth.repo import AuthRepository
from app.modules.customer_service.models import SupportCompanyAssignment

logger = logging.getLogger(__name__)


def get_current_actor(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Actor:
    """
    取得當前操作者（統一權威入口）

    WP-C1-02 Step 1 強化流程：
    1. 從 Authorization header 取得 JWT token
    2. 解析 JWT → user_id, role_id, company_id
    3. 驗證 user 存在且 active
    4. 依平台角色查詢 membership / support_assignments
    5. 若 JWT 含 company_id：
       - company_user → 查 Membership 取 active_role_id，注入 Actor
       - customer_service → 驗證 support assignment
       - super_admin → 不需驗證
    6. 回傳完整 Actor（含 active_company_id, active_role_id）

    Args:
        authorization: Authorization header (Bearer <token>)
        db: Database session

    Returns:
        Actor: 操作者資訊（含 active_company_id, active_role_id）

    Raises:
        HTTPException 401: Missing or invalid token
        HTTPException 403: User not active or scope mismatch
    """
    # 1. 驗證 Authorization header
    if not authorization:
        logger.warning("Missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )

    # 2. 解析 Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning(f"Invalid Authorization header format: {authorization[:20]}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format (expected: Bearer <token>)"
        )

    token = parts[1]

    # 3. 解析 JWT
    try:
        payload = decode_access_token(token)
    except Exception as e:
        logger.warning(f"JWT decode failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}"
        )

    # 4. 取得必要 claims
    user_id_str = payload.get("sub")
    role_id = payload.get("role_id")
    # company_id 是 SA v2.0 JWT 的 active scope claim
    jwt_company_id: Optional[str] = payload.get("company_id")

    if not user_id_str or not role_id:
        logger.warning(f"JWT missing required claims: sub={user_id_str}, role_id={role_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing required claims (sub, role_id)"
        )

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        logger.warning(f"Invalid user_id format in JWT: {user_id_str}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: invalid user_id format"
        )

    # 5. 驗證 user 是否存在且 active
    auth_repo = AuthRepository(db)
    user = auth_repo.get_user_by_id(user_id)

    if not user:
        logger.warning(f"User not found: user_id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        logger.warning(f"User not active: user_id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )

    # 6. 判斷平台層角色
    role = _map_role_id_to_user_role(role_id)

    company_memberships: set = set()
    support_company_assignments: set = set()
    active_company_id: Optional[str] = None
    active_role_id: Optional[str] = None

    if role == UserRole.SUPER_ADMIN:
        # Super Admin：不需額外查詢；jwt_company_id 若存在，作為操作 hint 但不強制
        active_company_id = jwt_company_id
        active_role_id = role_id
        logger.debug(f"Actor is super_admin: user_id={user_id}")

    elif role == UserRole.CUSTOMER_SERVICE:
        # 查詢所有被指派的公司
        assignments = db.query(SupportCompanyAssignment).filter(
            SupportCompanyAssignment.user_id == user_id
        ).all()
        support_company_assignments = {a.company_id for a in assignments}

        # 若 JWT 含 company_id，驗證是否在指派名單內
        if jwt_company_id:
            if jwt_company_id not in support_company_assignments:
                logger.warning(
                    f"customer_service JWT company_id {jwt_company_id} not in assignments "
                    f"for user {user_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="JWT company scope not in support assignments"
                )
            active_company_id = jwt_company_id

        active_role_id = role_id
        logger.debug(
            f"Actor is customer_service: user_id={user_id}, "
            f"assignments={support_company_assignments}"
        )

    elif role == UserRole.COMPANY_USER:
        # 查詢所有 active memberships
        memberships = auth_repo.get_user_memberships(user_id)
        company_memberships = {m.company_id for m in memberships if m.is_active}

        # JWT company_id 必須存在且在 memberships 內
        if jwt_company_id:
            if jwt_company_id not in company_memberships:
                logger.warning(
                    f"JWT company_id {jwt_company_id} not in memberships for user {user_id}. "
                    f"Memberships: {company_memberships}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="JWT company scope does not match any active membership"
                )
            active_company_id = jwt_company_id

            # 從 Membership 取得 active_role_id（公司內部角色）
            matching_membership = next(
                (m for m in memberships if m.company_id == jwt_company_id and m.is_active),
                None
            )
            if matching_membership:
                active_role_id = matching_membership.role_id
                logger.debug(
                    f"Actor company_user: user_id={user_id}, "
                    f"active_company_id={active_company_id}, "
                    f"active_role_id={active_role_id}"
                )
            else:
                # 理論上不應到此（已在 company_memberships 驗證），防禦性處理
                logger.error(
                    f"Membership found in set but not in list for user={user_id}, "
                    f"company={jwt_company_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Membership inconsistency: please re-login"
                )
        else:
            # JWT 無 company_id：允許建立 Actor（無 active scope）
            # 此情況僅適用於跨公司查詢型 endpoint（如 super_admin），
            # company_user 若無 active_company_id，attendance endpoints 應拒絕
            logger.warning(
                f"company_user JWT missing company_id claim: user_id={user_id}"
            )

        logger.debug(
            f"Actor is company_user: user_id={user_id}, memberships={company_memberships}"
        )

    else:
        logger.warning(f"Unknown role: role_id={role_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Unknown role: {role_id}"
        )

    # 7. 建立 Actor（含 active_company_id, active_role_id）
    actor = Actor(
        user_id=user_id,
        role=role,
        company_memberships=company_memberships,
        support_company_assignments=support_company_assignments,
        active_company_id=active_company_id,
        active_role_id=active_role_id,
    )

    logger.info(
        f"Actor created: user_id={user_id}, role={role.value}, "
        f"active_company_id={active_company_id}, active_role_id={active_role_id}"
    )

    return actor


def get_actor_with_company(
    actor: Actor = Depends(get_current_actor),
) -> Actor:
    """
    Dependency：取得已驗證公司範圍的 Actor

    用途：
    - 取代所有 attendance / admin_location endpoint 中的
      `company_id: str = Depends(get_current_company_id)`
    - 確保 actor.active_company_id 已從 JWT 驗證並注入
    - 不再依賴 X-Company-ID Header

    設計原則（SA v2.0）：
    - Super Admin 可不帶 active_company_id（保留彈性）
    - company_user / customer_service 必須有 active_company_id，否則拒絕

    Returns:
        Actor: 含有效 active_company_id 的 Actor

    Raises:
        HTTPException 403: 若 actor 無有效公司範圍
    """
    if not actor.has_active_company():
        logger.warning(
            f"Actor {actor.user_id} (role={actor.role.value}) "
            f"has no active_company_id in JWT"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "JWT does not carry a company scope (company_id claim missing). "
                "Please re-login with a specific company context."
            )
        )
    return actor


def _map_role_id_to_user_role(role_id: str) -> UserRole:
    """
    將資料庫的 role_id 映射到平台層 UserRole enum

    注意：employee / manager 均屬 COMPANY_USER（平台層）。
    公司內部的管理員 vs 員工區分，由 Actor.active_role_id 和
    Actor.is_admin() / Actor.is_employee() 處理，不在此層決定。

    Args:
        role_id: Role ID from database (e.g., 'admin', 'employee')

    Returns:
        UserRole: Mapped platform-level role
    """
    role_mapping = {
        # 平台層：Super Admin
        "super_admin": UserRole.SUPER_ADMIN,
        "system_admin": UserRole.SUPER_ADMIN,

        # 平台層：Customer Service
        "customer_service": UserRole.CUSTOMER_SERVICE,
        "support": UserRole.CUSTOMER_SERVICE,
        "cs": UserRole.CUSTOMER_SERVICE,

        # 平台層：Company User（含所有公司內部角色）
        # 公司內部角色區分（employee/manager）
        # 由 Membership.role_id → Actor.active_role_id → Actor.is_admin() 決定
        "manager": UserRole.COMPANY_USER,
        "employee": UserRole.COMPANY_USER,
    }

    mapped_role = role_mapping.get(role_id.lower())

    if not mapped_role:
        # 未知 role_id 預設視為 COMPANY_USER（保守處理）
        logger.warning(f"Unknown role_id '{role_id}', defaulting to COMPANY_USER")
        return UserRole.COMPANY_USER

    return mapped_role
