"""Attendance API 子模組

Phase 1A: Legacy extraction
- legacy.py: 舊版相容層 (Phase 4)

Phase 1B: Reporting extraction
- reporting.py: 報表 API (WP-11-06)

後續 Phase 將拆出：
- punch.py: 核心打卡 API (WP-11-02)
- breaks.py: 外出管理 API (WP-11-11.5)
- checkpoints.py: OUT Checkpoint API (WP-C1-11)
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.core.feature_service import get_feature_service, FeatureDisabledError
from app.core.features import FeatureKeys
from app.modules.attendance.api.legacy import router
from app.modules.attendance.api.punch import router_v1 as _punch_router_v1
from app.modules.attendance.api.breaks import router_v1 as _breaks_router_v1
from app.modules.attendance.api.checkpoints import router_v1 as _checkpoints_router_v1
from app.modules.attendance.api.reporting import (
    router as reporting_router,
    get_sessions as get_sessions_reporting,
)


def _require_attendance_feature(company_id: str, db: Session) -> None:
    """attendance.core Feature Gate - raises 403 if disabled."""
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
            },
        )


router_v1 = APIRouter()
router_v1.include_router(_punch_router_v1)
router_v1.include_router(_breaks_router_v1)
router_v1.include_router(_checkpoints_router_v1)
router_v1.include_router(reporting_router)

__all__ = [
    "router",
    "router_v1",
    "get_sessions_reporting",
    "get_feature_service",
    "_require_attendance_feature",
]
