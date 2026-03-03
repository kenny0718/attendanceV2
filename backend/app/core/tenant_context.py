"""Tenant Context 管理

提供 Tenant Isolation 所需的 company_id 注入機制。

Phase 1: 使用 Header (X-Company-ID) 注入
Phase 2: 將改為從 JWT token 解析
Phase 9 (WP-09-05): 加入 DB 驗證 (tenant exists + is_active)
WP-10-03B: 加入 membership 驗證 (platform-first v2)
"""

import logging
import uuid
from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.tenants.repo import TenantRepository

logger = logging.getLogger(__name__)


def get_current_company_id(
    x_company_id: str = Header(..., alias="X-Company-ID"),
    db: Session = Depends(get_db)
) -> str:
    """取得當前請求的公司 ID（Tenant Context）
    
    Phase 1 實作：從 HTTP Header 取得
    - Header 名稱：X-Company-ID
    - 必填，若缺少則回 400
    
    Phase 9 (WP-09-05) 強化：
    - 驗證 tenant 是否存在於 DB
    - 驗證 tenant 是否為 active 狀態
    - 不存在 → 404
    - 非 active → 403
    
    Phase 2 將改為：
    - 從 JWT token 解析 company_id
    - 驗證 token 有效性
    - 驗證使用者權限
    
    Note: 此函數不驗證 user membership（向後相容）
    新 API 應使用 get_current_company_id_with_membership()
    
    Args:
        x_company_id: HTTP Header 中的 X-Company-ID
        db: Database session
    
    Returns:
        company_id (str)
    
    Raises:
        HTTPException: 若 Header 缺少、tenant 不存在或非 active
    """
    if not x_company_id or not x_company_id.strip():
        logger.warning("請求缺少 X-Company-ID header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Company-ID header"
        )
    
    company_id = x_company_id.strip()
    
    # Phase 9: Validate tenant exists and is active
    tenant_repo = TenantRepository(db)
    
    # Check if tenant exists
    if not tenant_repo.exists(company_id):
        logger.warning(f"Tenant validation failed: {company_id} does not exist")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Tenant {company_id} does not exist"}
        )
    
    # Check if tenant is active
    if not tenant_repo.is_active(company_id):
        logger.warning(f"Tenant validation failed: {company_id} is not active")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": f"Tenant {company_id} is not active"}
        )
    
    logger.debug(f"Current company_id: {company_id} (validated)")
    return company_id


def get_current_company_id_with_membership(
    x_company_id: str = Header(..., alias="X-Company-ID"),
    x_user_id: str = Header(..., alias="X-User-ID"),
    db: Session = Depends(get_db)
) -> str:
    """取得當前請求的公司 ID（含 membership 驗證）
    
    WP-10-03B: Platform-First v2 版本
    
    驗證順序：
    1. Tenant exists
    2. Tenant is_active
    3. User has membership (NEW)
    
    Anti-Enumeration 策略：
    - No membership → 404 (統一回應，不洩漏 tenant 存在性)
    - Inactive membership → 404 (統一回應)
    
    Phase 1 實作：從 HTTP Header 取得 user_id + company_id
    Phase 2 將改為：從 JWT token 解析
    
    Args:
        x_company_id: HTTP Header 中的 X-Company-ID
        x_user_id: HTTP Header 中的 X-User-ID
        db: Database session
    
    Returns:
        company_id (str)
    
    Raises:
        HTTPException 400: Missing headers
        HTTPException 404: Tenant not found OR no membership (anti-enumeration)
        HTTPException 403: Tenant not active
    """
    # Validate headers
    if not x_company_id or not x_company_id.strip():
        logger.warning("請求缺少 X-Company-ID header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Company-ID header"
        )
    
    if not x_user_id or not x_user_id.strip():
        logger.warning("請求缺少 X-User-ID header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-User-ID header"
        )
    
    company_id = x_company_id.strip()
    user_id_str = x_user_id.strip()
    
    # Parse user_id as UUID
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        logger.warning(f"Invalid X-User-ID format: {user_id_str}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-User-ID format (must be UUID)"
        )
    
    # Phase 9: Validate tenant exists and is active
    tenant_repo = TenantRepository(db)
    
    # Check if tenant exists
    if not tenant_repo.exists(company_id):
        logger.warning(f"Tenant validation failed: {company_id} does not exist")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Tenant {company_id} not found"}
        )
    
    # Check if tenant is active
    if not tenant_repo.is_active(company_id):
        logger.warning(f"Tenant validation failed: {company_id} is not active")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": f"Tenant {company_id} is not active"}
        )
    
    # WP-10-03B: Validate user has membership
    from app.modules.auth.repo import AuthRepository
    auth_repo = AuthRepository(db)
    
    if not auth_repo.user_has_company_access(user_id, company_id):
        # Anti-Enumeration: 統一回 404，不洩漏 tenant 存在性
        logger.warning(f"Membership validation failed: user {user_id} has no access to company {company_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Tenant {company_id} not found"}
        )
    
    logger.debug(f"Current company_id: {company_id} (validated with membership)")
    return company_id


def get_current_user_id(
    x_user_id: str = Header(None, alias="X-User-ID")
) -> str | None:
    """取得當前請求的使用者 ID（選填）
    
    Phase 1 實作：從 HTTP Header 取得（選填）
    Phase 2 將改為：從 JWT token 解析
    
    Args:
        x_user_id: HTTP Header 中的 X-User-ID
    
    Returns:
        user_id (str | None)
    """
    if x_user_id:
        return x_user_id.strip()
    return None
