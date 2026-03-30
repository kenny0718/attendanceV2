"""Reporting Schemas（Reporting 回應模型層）

P2: Extracted from schemas.py as part of attendance module boundary strengthening.

WP-11-06 Step 1/2/3: Reporting response schemas

Contract freeze:
- 所有欄位名稱、型別、預設值不得在 refactor 過程中變更
- route path 不得變更
- response contract 不得變更
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.modules.attendance.schemas import SessionResponse


# ============================================
# WP-11-06 Step 1: Sessions List Reporting Schema
# ============================================

class SessionsListResponse(BaseModel):
    """Sessions list response for reporting endpoint (WP-11-06 Step 1)"""
    sessions: list[SessionResponse] = Field(..., description="Session 列表")
    total: int = Field(..., description="符合條件的 session 總數（未分頁）")
    limit: int = Field(..., description="每頁筆數")
    offset: int = Field(..., description="偏移量")


# ============================================
# WP-11-06 Step 2: User Summary Reporting Schema
# ============================================

class UserSummaryResponse(BaseModel):
    """Per-user attendance summary response (WP-11-06 Step 2)"""
    user_id: str = Field(..., description="查詢的用戶 ID")
    total_sessions: int = Field(..., description="符合條件的 session 總數（含 open + closed）")
    closed_sessions: int = Field(..., description="已完成的 session 數")
    open_sessions: int = Field(..., description="進行中的 session 數")
    total_work_minutes: int = Field(..., description="總工時（分鐘），讀取 canonical duration_minutes，NULL 計為 0")
    average_session_minutes: Optional[float] = Field(None, description="平均每次 session 工時（分鐘），無 closed session 時為 null")
    first_session_time: Optional[datetime] = Field(None, description="最早 punch_in_time，無 session 時為 null")
    last_session_time: Optional[datetime] = Field(None, description="最近 punch_in_time，無 session 時為 null")


# ============================================
# WP-11-06 Step 3: Company Summary Reporting Schema
# ============================================

class CompanySummaryResponse(BaseModel):
    """Company-level attendance summary response (WP-11-06 Step 3)"""
    company_id: str = Field(..., description="查詢的公司 ID")
    total_users_with_sessions: int = Field(..., description="有出勤記錄的用戶數（Python set 去重）")
    total_sessions: int = Field(..., description="符合條件的 session 總數（含 open + closed）")
    open_sessions: int = Field(..., description="進行中的 session 數")
    closed_sessions: int = Field(..., description="已完成的 session 數")
    total_work_minutes: int = Field(..., description="總工時（分鐘），讀取 canonical duration_minutes，NULL 計為 0")
    average_minutes_per_session: Optional[float] = Field(None, description="平均每次 session 工時，無 closed session 時為 null")
    average_minutes_per_user: Optional[float] = Field(None, description="平均每位用戶工時，無用戶時為 null")
    first_session_time: Optional[datetime] = Field(None, description="最早 punch_in_time，無 session 時為 null")
    last_session_time: Optional[datetime] = Field(None, description="最近 punch_in_time，無 session 時為 null")
