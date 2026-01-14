"""Tenant Context 管理

提供 Tenant Isolation 所需的 company_id 注入機制。

Phase 1: 使用 Header (X-Company-ID) 注入
Phase 2: 將改為從 JWT token 解析
"""

import logging
from fastapi import Header, HTTPException, status

logger = logging.getLogger(__name__)


def get_current_company_id(
    x_company_id: str = Header(..., alias="X-Company-ID")
) -> str:
    """取得當前請求的公司 ID（Tenant Context）
    
    Phase 1 實作：從 HTTP Header 取得
    - Header 名稱：X-Company-ID
    - 必填，若缺少則回 400
    
    Phase 2 將改為：
    - 從 JWT token 解析 company_id
    - 驗證 token 有效性
    - 驗證使用者權限
    
    Args:
        x_company_id: HTTP Header 中的 X-Company-ID
    
    Returns:
        company_id (str)
    
    Raises:
        HTTPException: 若 Header 缺少或無效
    """
    if not x_company_id or not x_company_id.strip():
        logger.warning("請求缺少 X-Company-ID header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Company-ID header"
        )
    
    logger.debug(f"Current company_id: {x_company_id}")
    return x_company_id.strip()


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
