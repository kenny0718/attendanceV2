"""Attendance API Schemas (Request/Response DTOs)

WP-11-02: Punch In/Out API
WP-11-03: Policy Engine Integration
WP-11-05B: Updated status descriptions to include approval workflow states
WP-11-07 Phase 3B: Added Break Out/In schemas
Following WP-11-02_PRECHECK_CHECKLIST.md decisions
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


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


class BreakOutRequest(BaseModel):
    """Break out request (WP-11-07 Phase 3B)

    Note: company_id and user_id come from JWT/tenant context, not from request body
    """
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")
    location: Optional[LocationData] = Field(None, description="Optional GPS location")
    punch_time: Optional[datetime] = Field(None, description="Optional punch time (for testing/admin)")


class BreakInRequest(BaseModel):
    """Break in request (WP-11-07 Phase 3B)

    Note: company_id and user_id come from JWT/tenant context, not from request body
    """
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")
    location: Optional[LocationData] = Field(None, description="Optional GPS location")
    punch_time: Optional[datetime] = Field(None, description="Optional punch time (for testing/admin)")


class PunchResponse(BaseModel):
    """Single punch record response"""
    punch_id: UUID = Field(..., description="Punch ID")
    punch_type: str = Field(..., description="Punch type (in/out/break_start/break_end)")
    punch_time: datetime = Field(..., description="Punch time (UTC+8)")
    notes: Optional[str] = Field(None, description="Notes")

    model_config = ConfigDict(from_attributes=True)


class SessionResponse(BaseModel):
    """Attendance session response"""
    session_id: UUID = Field(..., description="Session ID")
    user_id: UUID = Field(..., description="User ID")
    company_id: str = Field(..., description="Company ID")
    punch_in_time: datetime = Field(..., description="Punch in time (UTC+8)")
    punch_out_time: Optional[datetime] = Field(None, description="Punch out time (UTC+8, null if open)")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes (null if open)")
    status: str = Field(..., description="Session status (open/closed/pending/approved/rejected/missing_punch_out)")
    punches: Optional[list] = Field(default_factory=list, description="All punches in this session (including break_start/break_end)")
    display_name: Optional[str] = Field(None, description="Employee display name (admin view only)")

    model_config = ConfigDict(from_attributes=True)


class PunchInResponse(SessionResponse):
    """Punch in response (201 Created)"""
    pass


class BreakOutResponse(BaseModel):
    """Break out response (WP-11-07 Phase 3B)"""
    punch_id: UUID = Field(..., description="Punch record ID")
    session_id: UUID = Field(..., description="Session ID")
    punch_time: datetime = Field(..., description="Break out time (UTC+8)")
    message: str = Field(..., description="Success message")


class BreakInResponse(BaseModel):
    """Break in response (WP-11-07 Phase 3B)"""
    punch_id: UUID = Field(..., description="Punch record ID")
    session_id: UUID = Field(..., description="Session ID")
    punch_time: datetime = Field(..., description="Break in time (UTC+8)")
    message: str = Field(..., description="Success message")


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
    is_on_break: bool = Field(False, description="Whether user is currently on break")


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


# ============================================
# WP-11-10: OUT Checkpoint Schemas
# ============================================

class GPSData(BaseModel):
    """GPS data for checkpoint events"""
    latitude: float = Field(..., ge=-90, le=90, description="緯度")
    longitude: float = Field(..., ge=-180, le=180, description="經度")
    accuracy: Optional[float] = Field(None, ge=0, description="GPS 精度 (公尺)")
    captured_at: Optional[datetime] = Field(None, description="GPS 擷取時間")
    provider: Optional[str] = Field(None, pattern="^(gps|network|fused)$", description="GPS 提供者")


class OutCheckpointRequest(BaseModel):
    """OUT checkpoint request (WP-11-10)

    Note: company_id and user_id come from JWT/tenant context, not from request body
    """
    device_type: str = Field(..., pattern="^(mobile|pc)$", description="裝置類型 (mobile|pc)")
    gps: Optional[GPSData] = Field(None, description="GPS 資料 (mobile 必填, pc 選填)")
    notes: Optional[str] = Field(None, max_length=500, description="備註")
    client_timezone: Optional[str] = Field(None, max_length=50, description="客戶端時區")

    @field_validator("gps")
    @classmethod
    def validate_gps_for_mobile(cls, v: Optional[GPSData], info: ValidationInfo) -> Optional[GPSData]:
        """Validate that mobile devices provide GPS"""
        if info.data.get("device_type") == "mobile" and not v:
            raise ValueError("請開啟定位後再外出打卡")
        return v


class OutCheckpointResponse(BaseModel):
    """OUT checkpoint response (WP-11-10)"""
    checkpoint_id: UUID = Field(..., description="Checkpoint ID")
    punch_time: datetime = Field(..., description="打卡時間 (UTC+8, server-set)")
    gps: Optional[GPSData] = Field(None, description="GPS 資料")
    message: str = Field(default="Checkpoint recorded successfully", description="成功訊息")


class OutCheckpointListItem(BaseModel):
    """OUT checkpoint list item (WP-11-10)"""
    checkpoint_id: UUID = Field(..., description="Checkpoint ID")
    punch_time: datetime = Field(..., description="打卡時間 (UTC+8)")
    device_type: str = Field(..., description="裝置類型")
    gps: Optional[GPSData] = Field(None, description="GPS 資料")
    notes: Optional[str] = Field(None, description="備註")

    model_config = ConfigDict(from_attributes=True)


class OutCheckpointListResponse(BaseModel):
    """OUT checkpoint list response (WP-11-10)"""
    checkpoints: list[OutCheckpointListItem] = Field(..., description="Checkpoint 列表")
    total: int = Field(..., description="總數")
    limit: int = Field(..., description="每頁筆數")
    offset: int = Field(..., description="偏移量")


class DuplicateCheckpointError(ErrorResponse):
    """Error response for duplicate checkpoint (409)"""
    error_code: str = Field("DUPLICATE_CHECKPOINT", description="Error code")
    last_checkpoint_time: datetime = Field(..., description="上次打卡時間")


# ============================================
# WP-11-13: Location Policy Schemas
# ============================================

class AllowedLocationBase(BaseModel):
    """Allowed location base schema"""
    name: str = Field(..., max_length=255, description="地點名稱")
    description: Optional[str] = Field(None, description="地點描述")
    location_type: str = Field("office", pattern="^(office|construction_site|customer_site|temporary_site)$", description="地點類型")
    latitude: float = Field(..., ge=-90, le=90, description="緯度")
    longitude: float = Field(..., ge=-180, le=180, description="經度")
    radius_meters: int = Field(..., gt=0, description="允許半徑（公尺）")
    is_active: bool = Field(True, description="是否啟用")


class AllowedLocationCreate(AllowedLocationBase):
    """Create allowed location request"""
    pass


class AllowedLocationUpdate(BaseModel):
    """Update allowed location request"""
    name: Optional[str] = Field(None, max_length=255, description="地點名稱")
    description: Optional[str] = Field(None, description="地點描述")
    location_type: Optional[str] = Field(None, pattern="^(office|construction_site|customer_site|temporary_site)$", description="地點類型")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="緯度")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="經度")
    radius_meters: Optional[int] = Field(None, gt=0, description="允許半徑（公尺）")
    is_active: Optional[bool] = Field(None, description="是否啟用")


class AllowedLocationResponse(AllowedLocationBase):
    """Allowed location response"""
    id: UUID = Field(..., description="Location ID")
    company_id: str = Field(..., description="公司 ID")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")
    created_by: Optional[str] = Field(None, description="建立者")
    updated_by: Optional[str] = Field(None, description="更新者")

    model_config = ConfigDict(from_attributes=True)


class AllowedLocationListResponse(BaseModel):
    """Allowed location list response"""
    locations: list[AllowedLocationResponse] = Field(..., description="地點列表")
    total: int = Field(..., description="總數")
    limit: int = Field(..., description="每頁筆數")
    offset: int = Field(..., description="偏移量")


class LocationPolicyCheckResult(BaseModel):
    """Location policy check result"""
    allowed: bool = Field(..., description="是否允許打卡")
    reason: str = Field(..., description="原因說明")
    matched_location: Optional[dict] = Field(None, description="匹配的地點")
    nearest_location: Optional[dict] = Field(None, description="最近的地點")


class LocationPolicyViolationError(ErrorResponse):
    """Location policy violation error (403)"""
    error_code: str = Field("LOCATION_POLICY_VIOLATION", description="錯誤碼")
    nearest_location: Optional[dict] = Field(None, description="最近的地點")
