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

from app.modules.attendance.api.legacy import router
from app.modules.attendance.api.reporting import get_sessions_reporting

__all__ = ["router", "get_sessions_reporting"]
