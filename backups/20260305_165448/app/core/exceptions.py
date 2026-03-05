"""統一錯誤處理機制

WP-11-04A: Unified exception handling for scope and feature gate errors
"""

from typing import Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class ScopeForbiddenError(Exception):
    """Scope 權限錯誤（HTTP 403）"""
    
    def __init__(self, message: str, company_id: Optional[str] = None):
        self.message = message
        self.company_id = company_id
        super().__init__(message)


class FeatureDisabledError(Exception):
    """Feature 未啟用錯誤（HTTP 403）"""
    
    def __init__(self, feature_key: str, company_id: str, message: Optional[str] = None):
        self.feature_key = feature_key
        self.company_id = company_id
        self.message = message or f"Feature '{feature_key}' is not enabled for company '{company_id}'"
        super().__init__(self.message)


async def scope_forbidden_handler(request: Request, exc: ScopeForbiddenError) -> JSONResponse:
    """處理 ScopeForbiddenError"""
    content = {
        "code": "SCOPE_FORBIDDEN",
        "message": exc.message
    }
    
    if exc.company_id:
        content["company_id"] = exc.company_id
    
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=content
    )


async def feature_disabled_handler(request: Request, exc: FeatureDisabledError) -> JSONResponse:
    """處理 FeatureDisabledError"""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "code": "FEATURE_DISABLED",
            "feature": exc.feature_key,
            "company_id": exc.company_id,
            "message": exc.message
        }
    )


def register_exception_handlers(app):
    """註冊所有 exception handlers 到 FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(ScopeForbiddenError, scope_forbidden_handler)
    app.add_exception_handler(FeatureDisabledError, feature_disabled_handler)
