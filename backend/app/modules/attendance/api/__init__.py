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

from fastapi import APIRouter
from app.modules.attendance.api.legacy import router
from app.modules.attendance.api.punch import router_v1 as _punch_router_v1
from app.modules.attendance.api.breaks import router_v1 as _breaks_router_v1
from app.modules.attendance.api.checkpoints import router_v1 as _checkpoints_router_v1
from app.modules.attendance.api.reporting import router as reporting_router

# Merged router_v1: all /api/v1/attendance/* endpoints
router_v1 = APIRouter()
router_v1.include_router(_punch_router_v1)
router_v1.include_router(_breaks_router_v1)
router_v1.include_router(_checkpoints_router_v1)
router_v1.include_router(reporting_router)

__all__ = ["router", "router_v1"]
