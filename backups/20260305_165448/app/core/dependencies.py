"""FastAPI Dependencies

WP-11-04A: Unified Actor dependency for scope checking
統一的 Actor 取得機制，整合 JWT 驗證與資料庫查詢
"""

import logging
from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.scope import Actor, UserRole
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
    
    流程：
    1. 從 Authorization header 取得 JWT token
    2. 解析 JWT 取得 user_id, role_id, company_id
    3. 根據 role 查詢對應的資料：
       - customer_service: 查詢 support_company_assignments
       - company_user: 查詢 user_company_memberships
       - super_admin: 不需額外查詢
    4. 建立並回傳 Actor 物件
    
    Args:
        authorization: Authorization header (Bearer <token>)
        db: Database session
    
    Returns:
        Actor: 操作者資訊
    
    Raises:
        HTTPException 401: Missing or invalid token
        HTTPException 403: User not active
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
        logger.warning(f"Invalid Authorization header format: {authorization}")
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
    
    # 4. 取得 user_id 和 role_id
    user_id_str = payload.get("sub")
    role_id = payload.get("role_id")
    
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
    
    # 6. 判斷 role 並查詢對應資料
    role = _map_role_id_to_user_role(role_id)
    
    company_memberships = set()
    support_company_assignments = set()
    
    if role == UserRole.SUPER_ADMIN:
        # Super Admin 不需額外查詢
        logger.debug(f"Actor is super_admin: user_id={user_id}")
    
    elif role == UserRole.CUSTOMER_SERVICE:
        # 查詢 support_company_assignments
        assignments = db.query(SupportCompanyAssignment).filter(
            SupportCompanyAssignment.user_id == user_id
        ).all()
        support_company_assignments = {a.company_id for a in assignments}
        logger.debug(f"Actor is customer_service: user_id={user_id}, assignments={support_company_assignments}")
    
    elif role == UserRole.COMPANY_USER:
        # 查詢 user_company_memberships
        memberships = auth_repo.get_user_memberships(user_id)
        company_memberships = {m.company_id for m in memberships if m.is_active}
        logger.debug(f"Actor is company_user: user_id={user_id}, memberships={company_memberships}")
    
    else:
        logger.warning(f"Unknown role: role_id={role_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Unknown role: {role_id}"
        )
    
    # 7. 建立 Actor
    actor = Actor(
        user_id=user_id,
        role=role,
        company_memberships=company_memberships,
        support_company_assignments=support_company_assignments
    )
    
    logger.info(f"Actor created: user_id={user_id}, role={role.value}")
    
    return actor


def _map_role_id_to_user_role(role_id: str) -> UserRole:
    """
    將資料庫的 role_id 映射到 UserRole enum
    
    Args:
        role_id: Role ID from database (e.g., 'admin', 'employee')
    
    Returns:
        UserRole: Mapped role
    
    Raises:
        ValueError: If role_id cannot be mapped
    """
    # 定義映射規則
    role_mapping = {
        # Super Admin
        "super_admin": UserRole.SUPER_ADMIN,
        "system_admin": UserRole.SUPER_ADMIN,
        
        # Customer Service
        "customer_service": UserRole.CUSTOMER_SERVICE,
        "support": UserRole.CUSTOMER_SERVICE,
        "cs": UserRole.CUSTOMER_SERVICE,
        
        # Company User (所有其他角色都視為 company_user)
        "admin": UserRole.COMPANY_USER,
        "manager": UserRole.COMPANY_USER,
        "employee": UserRole.COMPANY_USER,
        "hr": UserRole.COMPANY_USER,
    }
    
    mapped_role = role_mapping.get(role_id.lower())
    
    if not mapped_role:
        # 預設視為 company_user
        logger.warning(f"Unknown role_id '{role_id}', defaulting to COMPANY_USER")
        return UserRole.COMPANY_USER
    
    return mapped_role
