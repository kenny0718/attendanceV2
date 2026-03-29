"""Attendance API 共用 Helper

Phase 1A: 只放 legacy 和後續多個子模組都會用的 helper
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.feature_service import get_feature_service, FeatureDisabledError
from app.core.features import FeatureKeys


def _require_attendance_feature(company_id: str, db: Session) -> None:
    """attendance.core Feature Gate - raises 403 if disabled
    
    被使用於：所有 router_v1 endpoints
    """
    try:
        feature_service = get_feature_service(db)
        feature_service.require_enabled(company_id, FeatureKeys.ATTENDANCE_CORE)
    except FeatureDisabledError as e:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "FEATURE_DISABLED",
                "feature": e.feature_key,
                "message": str(e),
            }
        )
