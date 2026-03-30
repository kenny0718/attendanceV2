"""Attendance API 路由 — Façade 層

Phase 1A: Legacy extraction
- 舊版 endpoint 已移至 api/legacy.py
- 新版 endpoint 保留在此（待後續拆分）

WP-11-02: Punch In/Out API
WP-11-05C: Policy Engine Integration
WP-C1-07: JWT Actor Migration - router_v1 全面遷移至 get_actor_with_company
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.modules.attendance.service import get_attendance_service
from app.core.scope import Actor
from app.core.dependencies import get_actor_with_company
from app.core.database import get_db
from app.modules.attendance.repo import get_attendance_session_repository
from app.modules.attendance.checkpoint_repo import get_out_checkpoint_repository
from app.modules.attendance.schemas import (
    BreakOutRequest,
    BreakInRequest,
    BreakOutResponse,
    BreakInResponse,
    PunchInRequest,
    PunchInResponse,
    PunchOutRequest,
    PunchOutResponse,
    CurrentStatusResponse,
    AttendanceHistoryResponse,
    SessionResponse,
    PolicyEvaluationResponse,
    SessionsListResponse,
    UserSummaryResponse,
    CompanySummaryResponse,
    OutCheckpointRequest,
    OutCheckpointResponse,
    OutCheckpointListItem,
    OutCheckpointListResponse,
)
from app.modules.attendance.policy_engine import AttendancePolicyEngine
from app.core.features import FeatureKeys
from app.core.feature_service import get_feature_service, FeatureDisabledError
from app.modules.attendance.api.legacy import router
from app.modules.attendance.api.helpers import _require_attendance_feature

logger = logging.getLogger(__name__)

# 新的 v1 router（主要業務邏輯）
router_v1 = APIRouter(prefix="/api/v1/attendance", tags=["attendance-v1"])


# ============================================
# 新的 API (WP-11-02, WP-11-05C)
# ============================================


