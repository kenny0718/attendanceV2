"""Attendance API Schemas (Request/Response DTOs)

WP-11-02: Punch In/Out API
WP-11-03: Policy Engine Integration
WP-11-05B: Updated status descriptions to include approval workflow states
Following WP-11-02_PRECHECK_CHECKLIST.md decisions
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ============================================
# Punch In/Out Schemas
# ============================================

class LocationData(BaseModel):
    """Location data for punch events"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")


class PunchInRequest(BaseModel):
    """Punch in request
    
    Note: company_id and user_id come from JWT/tenant context, not from request body
    """
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")
    location: Optional[LocationData] = Field(None, description="Optional GPS location")
    punch_time: Optional[datetime] = Field(None, description="Optional punch time (for testing/admin)")


class PunchOutRequest(BaseModel):
    """Punch out request
    
    Note: company_id and user_id come from JWT/tenant context, not from request body
    """
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")
    location: Optional[LocationData] = Field(None, description="Optional GPS location")
    punch_time: Optional[datetime] = Field(None, description="Optional punch time (for testing/admin)")


class SessionResponse(BaseModel):
    """Attendance session response"""
    session_id: UUID = Field(..., description="Session ID")
    user_id: UUID = Field(..., description="User ID")
    company_id: str = Field(..., description="Company ID")
    punch_in_time: datetime = Field(..., description="Punch in time (UTC)")
    punch_out_time: Optional[datetime] = Field(None, description="Punch out time (UTC, null if open)")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes (null if open)")
    status: str = Field(..., description="Session status (open/closed/pending/approved/rejected/missing_punch_out)")
    
    class Config:
        from_attributes = True


class PunchInResponse(SessionResponse):
    """Punch in response (201 Created)"""
    pass


# ============================================
# WP-11-03: Policy Evaluation Schemas
# ============================================

class PolicyEvaluationResponse(BaseModel):
    """Policy evaluation result (WP-11-03)"""
    is_late: bool = Field(..., description="Whether punch-in was late")
    late_minutes: int = Field(..., description="Minutes late (0 if not late)")
    is_early_leave: bool = Field(..., description="Whether punch-out was early")
    early_leave_minutes: int = Field(..., description="Minutes early (0 if not early)")
    is_overtime: bool = Field(..., description="Whether work duration qualifies as overtime")
    overtime_minutes: int = Field(..., description="Overtime minutes (0 if no overtime)")
    work_minutes: int = Field(..., description="Total work minutes")
    policy_name: Optional[str] = Field(None, description="Applied policy name")


class PunchOutResponse(SessionResponse):
    """Punch out response (200 OK)
    
    WP-11-03: Includes policy evaluation result
    """
    policy_evaluation: Optional[PolicyEvaluationResponse] = Field(None, description="Policy evaluation result (WP-11-03)")


# ============================================
# Current Status Schemas
# ============================================

class CurrentStatusResponse(BaseModel):
    """Current attendance status response"""
    has_open_session: bool = Field(..., description="Whether user has an open session")
    session: Optional[SessionResponse] = Field(None, description="Open session details (null if no open session)")
    elapsed_minutes: Optional[int] = Field(None, description="Elapsed minutes since punch in (null if no open session)")


# ============================================
# History Schemas
# ============================================

class AttendanceHistoryRequest(BaseModel):
    """Attendance history query parameters"""
    limit: int = Field(50, ge=1, le=100, description="Number of records per page")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    start_date: Optional[datetime] = Field(None, description="Start date filter (ISO 8601)")
    end_date: Optional[datetime] = Field(None, description="End date filter (ISO 8601)")
    status: Optional[str] = Field(None, description="Filter by status (open/closed/pending/approved/rejected/missing_punch_out)")


class AttendanceHistoryResponse(BaseModel):
    """Attendance history response"""
    sessions: list[SessionResponse] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions")
    limit: int = Field(..., description="Limit used")
    offset: int = Field(..., description="Offset used")


# ============================================
# Error Schemas
# ============================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")


class AlreadyOpenSessionError(ErrorResponse):
    """Error response for already open session (409)"""
    error_code: str = Field("ALREADY_OPEN_SESSION", description="Error code")
    open_session_id: UUID = Field(..., description="Existing open session ID")
    punch_in_time: datetime = Field(..., description="Existing session punch in time")


class NoOpenSessionError(ErrorResponse):
    """Error response for no open session (404)"""
    error_code: str = Field("NO_OPEN_SESSION", description="Error code")
