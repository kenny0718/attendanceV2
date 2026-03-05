"""Attendance Policy Engine

WP-11-03: Policy evaluation logic for attendance sessions.

This module provides pure calculation functions to evaluate attendance sessions
against company policies. It does NOT modify database state.

Design Principles:
- Pure functions (no side effects)
- No direct database access
- Tenant-aware (all calculations scoped to company_id)
- Timezone-aware datetime handling
"""

import logging
from datetime import datetime, time, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID

from app.modules.attendance.models import AttendanceSession, AttendancePolicy

logger = logging.getLogger(__name__)



# ============================================
# WP-11-03S: Work Schedule Abstractions
# ============================================

from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class WorkWindow:
    """Represents a single work time window
    
    Used for split shift scenarios where a day has multiple work periods.
    Example: 08:00-14:00 and 16:00-18:00
    
    Attributes:
        start_time: Window start time (time only, no date)
        end_time: Window end time (time only, no date)
    """
    start_time: time
    end_time: time
    
    def __post_init__(self):
        """Validate window"""
        if self.start_time >= self.end_time:
            raise ValueError(
                f"Invalid WorkWindow: start_time ({self.start_time}) "
                f"must be before end_time ({self.end_time})"
            )
    
    def duration_minutes(self) -> int:
        """Calculate window duration in minutes"""
        start_dt = datetime.combine(datetime.today(), self.start_time)
        end_dt = datetime.combine(datetime.today(), self.end_time)
        delta = end_dt - start_dt
        return int(delta.total_seconds() / 60)
    
    def contains_time(self, check_time: time) -> bool:
        """Check if a time falls within this window"""
        return self.start_time <= check_time < self.end_time
    
    def overlaps_with(self, other: 'WorkWindow') -> bool:
        """Check if this window overlaps with another"""
        return (self.start_time < other.end_time and 
                self.end_time > other.start_time)


@dataclass(frozen=True)
class FlexTimeBand:
    """Represents a flexible time band (WP-11-03S: Extension Point)
    
    For future Flex Time support. Not used in current implementation.
    
    Example: Employees can arrive between 08:00-10:00
    
    Attributes:
        earliest: Earliest allowed time
        latest: Latest allowed time
        band_type: Type of flex band ('arrival', 'departure', 'break')
    """
    earliest: time
    latest: time
    band_type: str  # 'arrival', 'departure', 'break'
    
    def __post_init__(self):
        """Validate flex band"""
        if self.earliest >= self.latest:
            raise ValueError(
                f"Invalid FlexTimeBand: earliest ({self.earliest}) "
                f"must be before latest ({self.latest})"
            )


@dataclass
class WorkSchedule:
    """Represents a work schedule with support for split shifts and flex time
    
    WP-11-03S: Core abstraction for schedule modes.
    
    Schedule Modes:
    - STANDARD: Single continuous work period (default, backward compatible)
    - SPLIT_SHIFT: Multiple discrete work windows
    - FLEX_TIME: Flexible arrival/departure with core hours (future)
    
    Attributes:
        mode: Schedule mode ('standard', 'split_shift', 'flex_time')
        windows: List of work windows (1 for standard, 2+ for split shift)
        core_time_start: Core hours start (for flex time, future)
        core_time_end: Core hours end (for flex time, future)
        flex_bands: Flexible time bands (for flex time, future)
    """
    mode: str  # 'standard', 'split_shift', 'flex_time'
    windows: List[WorkWindow]
    
    # Extension points for Flex Time (WP-11-03S: not implemented yet)
    core_time_start: Optional[time] = None
    core_time_end: Optional[time] = None
    flex_bands: Optional[List[FlexTimeBand]] = None
    
    def __post_init__(self):
        """Validate schedule"""
        if not self.windows:
            raise ValueError("WorkSchedule must have at least one window")
        
        if self.mode not in ('standard', 'split_shift', 'flex_time'):
            raise ValueError(
                f"Invalid schedule mode: {self.mode}. "
                "Must be 'standard', 'split_shift', or 'flex_time'"
            )
        
        if self.mode == 'standard' and len(self.windows) != 1:
            raise ValueError("Standard mode must have exactly one window")
        
        if self.mode == 'split_shift' and len(self.windows) < 2:
            raise ValueError("Split shift mode must have at least 2 windows")
        
        # Check for overlapping windows
        for i, window1 in enumerate(self.windows):
            for window2 in self.windows[i+1:]:
                if window1.overlaps_with(window2):
                    raise ValueError(
                        f"Overlapping windows detected: "
                        f"{window1.start_time}-{window1.end_time} and "
                        f"{window2.start_time}-{window2.end_time}"
                    )
        
        # Ensure windows are sorted
        sorted_windows = sorted(self.windows, key=lambda w: w.start_time)
        if self.windows != sorted_windows:
            # Auto-sort windows
            object.__setattr__(self, 'windows', sorted_windows)
            logger.warning(
                f"WorkSchedule windows were not sorted. Auto-sorted to: "
                f"{[f'{w.start_time}-{w.end_time}' for w in sorted_windows]}"
            )
    
    @classmethod
    def from_policy(cls, policy: Optional['AttendancePolicy']) -> 'WorkSchedule':
        """Create WorkSchedule from AttendancePolicy (backward compatibility)
        
        Converts existing policy fields (work_start_time, work_end_time) 
        into a standard single-window schedule.
        
        Args:
            policy: AttendancePolicy or None
        
        Returns:
            WorkSchedule with single window (standard mode)
        """
        if policy:
            window = WorkWindow(
                start_time=policy.work_start_time,
                end_time=policy.work_end_time
            )
        else:
            # Use defaults from AttendancePolicyEngine
            window = WorkWindow(
                start_time=AttendancePolicyEngine.DEFAULT_WORK_START_TIME,
                end_time=AttendancePolicyEngine.DEFAULT_WORK_END_TIME
            )
        
        return cls(mode='standard', windows=[window])
    
    @classmethod
    def create_split_shift(cls, windows: List[WorkWindow]) -> 'WorkSchedule':
        """Create a split shift schedule
        
        Args:
            windows: List of work windows (must be 2 or more)
        
        Returns:
            WorkSchedule in split_shift mode
        """
        return cls(mode='split_shift', windows=windows)
    
    def total_scheduled_minutes(self) -> int:
        """Calculate total scheduled work minutes across all windows"""
        return sum(w.duration_minutes() for w in self.windows)
    
    def first_window(self) -> WorkWindow:
        """Get the first work window (for late detection)"""
        return self.windows[0]
    
    def last_window(self) -> WorkWindow:
        """Get the last work window (for early leave detection)"""
        return self.windows[-1]


class PolicyEvaluationResult:
    """Policy evaluation result for an attendance session"""
    
    def __init__(
        self,
        session_id: UUID,
        company_id: str,
        user_id: UUID,
        policy_id: Optional[UUID],
        policy_name: Optional[str],
        # Timing
        punch_in_time: datetime,
        punch_out_time: Optional[datetime],
        work_start_time: Optional[time],
        work_end_time: Optional[time],
        # Calculations
        is_late: bool,
        late_minutes: int,
        is_early_leave: bool,
        early_leave_minutes: int,
        is_overtime: bool,
        overtime_minutes: int,
        work_minutes: int,
        # Policy settings
        grace_period_minutes: int,
        overtime_threshold_minutes: Optional[int]
    ):
        self.session_id = session_id
        self.company_id = company_id
        self.user_id = user_id
        self.policy_id = policy_id
        self.policy_name = policy_name
        
        # Timing
        self.punch_in_time = punch_in_time
        self.punch_out_time = punch_out_time
        self.work_start_time = work_start_time
        self.work_end_time = work_end_time
        
        # Calculations
        self.is_late = is_late
        self.late_minutes = late_minutes
        self.is_early_leave = is_early_leave
        self.early_leave_minutes = early_leave_minutes
        self.is_overtime = is_overtime
        self.overtime_minutes = overtime_minutes
        self.work_minutes = work_minutes
        
        # Policy settings
        self.grace_period_minutes = grace_period_minutes
        self.overtime_threshold_minutes = overtime_threshold_minutes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "session_id": str(self.session_id),
            "company_id": self.company_id,
            "user_id": str(self.user_id),
            "policy": {
                "policy_id": str(self.policy_id) if self.policy_id else None,
                "policy_name": self.policy_name,
                "work_start_time": self.work_start_time.isoformat() if self.work_start_time else None,
                "work_end_time": self.work_end_time.isoformat() if self.work_end_time else None,
                "grace_period_minutes": self.grace_period_minutes,
                "overtime_threshold_minutes": self.overtime_threshold_minutes
            },
            "timing": {
                "punch_in_time": self.punch_in_time.isoformat(),
                "punch_out_time": self.punch_out_time.isoformat() if self.punch_out_time else None,
                "work_minutes": self.work_minutes
            },
            "evaluation": {
                "is_late": self.is_late,
                "late_minutes": self.late_minutes,
                "is_early_leave": self.is_early_leave,
                "early_leave_minutes": self.early_leave_minutes,
                "is_overtime": self.is_overtime,
                "overtime_minutes": self.overtime_minutes
            }
        }


class AttendancePolicyEngine:
    """Attendance Policy Engine
    
    Evaluates attendance sessions against company policies.
    
    Evaluation Rules:
    1. Late: punch_in_time > work_start_time + grace_period
    2. Early Leave: punch_out_time < work_end_time
    3. Overtime: work_minutes > overtime_threshold
    
    Fallback Behavior (no policy):
    - No late/early leave detection (returns False)
    - Overtime based on 8-hour standard (480 minutes)
    - Grace period = 0
    """
    
    # Default fallback values when no policy is provided
    DEFAULT_GRACE_PERIOD_MINUTES = 0
    DEFAULT_OVERTIME_THRESHOLD_MINUTES = 480  # 8 hours
    DEFAULT_WORK_START_TIME = time(9, 0)  # 09:00
    DEFAULT_WORK_END_TIME = time(18, 0)  # 18:00
    
    @staticmethod
    def evaluate(
        session: AttendanceSession,
        policy: Optional[AttendancePolicy] = None
    ) -> PolicyEvaluationResult:
        """Evaluate an attendance session against a policy
        
        Args:
            session: AttendanceSession to evaluate
            policy: AttendancePolicy to apply (optional, uses defaults if None)
        
        Returns:
            PolicyEvaluationResult with all calculations
        
        Raises:
            ValueError: If session is still open (punch_out_time is None)
        """
        if session.status == 'open' or session.punch_out_time is None:
            raise ValueError(
                f"Cannot evaluate open session {session.id}. "
                "Session must be closed (punch_out_time must be set)."
            )
        
        # Extract policy settings (or use defaults)
        if policy:
            work_start_time = policy.work_start_time
            work_end_time = policy.work_end_time
            grace_period_minutes = policy.grace_period_minutes
            overtime_threshold_minutes = policy.overtime_threshold_minutes
            policy_id = policy.id
            policy_name = policy.name
        else:
            work_start_time = AttendancePolicyEngine.DEFAULT_WORK_START_TIME
            work_end_time = AttendancePolicyEngine.DEFAULT_WORK_END_TIME
            grace_period_minutes = AttendancePolicyEngine.DEFAULT_GRACE_PERIOD_MINUTES
            overtime_threshold_minutes = AttendancePolicyEngine.DEFAULT_OVERTIME_THRESHOLD_MINUTES
            policy_id = None
            policy_name = "Default Policy (No Policy Assigned)"
        
        # Calculate work duration
        work_minutes = session.duration_minutes or 0
        
        # 1. Late detection
        is_late, late_minutes = AttendancePolicyEngine._calculate_late(
            punch_in_time=session.punch_in_time,
            work_start_time=work_start_time,
            grace_period_minutes=grace_period_minutes
        )
        
        # 2. Early leave detection
        is_early_leave, early_leave_minutes = AttendancePolicyEngine._calculate_early_leave(
            punch_out_time=session.punch_out_time,
            work_end_time=work_end_time
        )
        
        # 3. Overtime detection
        is_overtime, overtime_minutes = AttendancePolicyEngine._calculate_overtime(
            work_minutes=work_minutes,
            overtime_threshold_minutes=overtime_threshold_minutes
        )
        
        logger.info(
            f"Policy evaluation: session_id={session.id}, "
            f"late={is_late} ({late_minutes}m), "
            f"early_leave={is_early_leave} ({early_leave_minutes}m), "
            f"overtime={is_overtime} ({overtime_minutes}m)"
        )
        
        return PolicyEvaluationResult(
            session_id=session.id,
            company_id=session.company_id,
            user_id=session.user_id,
            policy_id=policy_id,
            policy_name=policy_name,
            punch_in_time=session.punch_in_time,
            punch_out_time=session.punch_out_time,
            work_start_time=work_start_time,
            work_end_time=work_end_time,
            is_late=is_late,
            late_minutes=late_minutes,
            is_early_leave=is_early_leave,
            early_leave_minutes=early_leave_minutes,
            is_overtime=is_overtime,
            overtime_minutes=overtime_minutes,
            work_minutes=work_minutes,
            grace_period_minutes=grace_period_minutes,
            overtime_threshold_minutes=overtime_threshold_minutes
        )
    
    @staticmethod
    def _calculate_late(
        punch_in_time: datetime,
        work_start_time: time,
        grace_period_minutes: int
    ) -> tuple[bool, int]:
        """Calculate if punch-in is late
        
        Args:
            punch_in_time: Actual punch-in time (datetime with timezone)
            work_start_time: Expected work start time (time only)
            grace_period_minutes: Grace period in minutes
        
        Returns:
            (is_late, late_minutes)
        """
        # Combine work_start_time with punch_in_time's date
        expected_start = datetime.combine(
            punch_in_time.date(),
            work_start_time
        )
        
        # Make timezone-aware if punch_in_time is timezone-aware
        if punch_in_time.tzinfo is not None:
            expected_start = expected_start.replace(tzinfo=punch_in_time.tzinfo)
        
        # Add grace period
        expected_start_with_grace = expected_start + timedelta(minutes=grace_period_minutes)
        
        # Calculate late minutes
        if punch_in_time > expected_start_with_grace:
            late_delta = punch_in_time - expected_start_with_grace
            late_minutes = int(late_delta.total_seconds() / 60)
            return True, late_minutes
        else:
            return False, 0
    
    @staticmethod
    def _calculate_early_leave(
        punch_out_time: datetime,
        work_end_time: time
    ) -> tuple[bool, int]:
        """Calculate if punch-out is early leave
        
        Args:
            punch_out_time: Actual punch-out time (datetime with timezone)
            work_end_time: Expected work end time (time only)
        
        Returns:
            (is_early_leave, early_leave_minutes)
        """
        # Combine work_end_time with punch_out_time's date
        expected_end = datetime.combine(
            punch_out_time.date(),
            work_end_time
        )
        
        # Make timezone-aware if punch_out_time is timezone-aware
        if punch_out_time.tzinfo is not None:
            expected_end = expected_end.replace(tzinfo=punch_out_time.tzinfo)
        
        # Calculate early leave minutes
        if punch_out_time < expected_end:
            early_delta = expected_end - punch_out_time
            early_leave_minutes = int(early_delta.total_seconds() / 60)
            return True, early_leave_minutes
        else:
            return False, 0
    
    @staticmethod
    def _calculate_overtime(
        work_minutes: int,
        overtime_threshold_minutes: Optional[int]
    ) -> tuple[bool, int]:
        """Calculate if work duration qualifies as overtime
        
        Args:
            work_minutes: Actual work duration in minutes
            overtime_threshold_minutes: Overtime threshold (None = no overtime detection)
        
        Returns:
            (is_overtime, overtime_minutes)
        """
        if overtime_threshold_minutes is None:
            # No overtime threshold defined
            return False, 0
        
        if work_minutes > overtime_threshold_minutes:
            overtime_minutes = work_minutes - overtime_threshold_minutes
            return True, overtime_minutes
        else:
            return False, 0



    @staticmethod
    def evaluate_with_schedule(
        session: AttendanceSession,
        schedule: WorkSchedule,
        policy: Optional[AttendancePolicy] = None
    ) -> PolicyEvaluationResult:
        """Evaluate an attendance session against a work schedule (WP-11-03S)
        
        Supports split shift scenarios with multiple work windows.
        
        Args:
            session: AttendanceSession to evaluate
            schedule: WorkSchedule defining work windows
            policy: AttendancePolicy for grace period and overtime threshold
        
        Returns:
            PolicyEvaluationResult with all calculations
        
        Raises:
            ValueError: If session is still open
        """
        if session.status == 'open' or session.punch_out_time is None:
            raise ValueError(
                f"Cannot evaluate open session {session.id}. "
                "Session must be closed (punch_out_time must be set)."
            )
        
        # Extract policy settings
        if policy:
            grace_period_minutes = policy.grace_period_minutes
            overtime_threshold_minutes = policy.overtime_threshold_minutes
            policy_id = policy.id
            policy_name = f"{policy.name} ({schedule.mode})"
        else:
            grace_period_minutes = AttendancePolicyEngine.DEFAULT_GRACE_PERIOD_MINUTES
            overtime_threshold_minutes = AttendancePolicyEngine.DEFAULT_OVERTIME_THRESHOLD_MINUTES
            policy_id = None
            policy_name = f"Default Policy ({schedule.mode})"
        
        # Get first and last windows for late/early detection
        first_window = schedule.first_window()
        last_window = schedule.last_window()
        
        # 1. Late detection (based on first window)
        is_late, late_minutes = AttendancePolicyEngine._calculate_late(
            punch_in_time=session.punch_in_time,
            work_start_time=first_window.start_time,
            grace_period_minutes=grace_period_minutes
        )
        
        # 2. Early leave detection (based on last window)
        is_early_leave, early_leave_minutes = AttendancePolicyEngine._calculate_early_leave(
            punch_out_time=session.punch_out_time,
            work_end_time=last_window.end_time
        )
        
        # 3. Calculate actual work minutes within windows (WP-11-03S: split shift logic)
        if schedule.mode == 'split_shift':
            work_minutes = AttendancePolicyEngine._calculate_work_minutes_split_shift(
                punch_in_time=session.punch_in_time,
                punch_out_time=session.punch_out_time,
                windows=schedule.windows
            )
        else:
            # Standard mode: use session duration
            work_minutes = session.duration_minutes or 0
        
        # 4. Overtime detection
        is_overtime, overtime_minutes = AttendancePolicyEngine._calculate_overtime(
            work_minutes=work_minutes,
            overtime_threshold_minutes=overtime_threshold_minutes
        )
        
        logger.info(
            f"Policy evaluation (schedule mode={schedule.mode}): session_id={session.id}, "
            f"late={is_late} ({late_minutes}m), "
            f"early_leave={is_early_leave} ({early_leave_minutes}m), "
            f"overtime={is_overtime} ({overtime_minutes}m), "
            f"work_minutes={work_minutes}"
        )
        
        return PolicyEvaluationResult(
            session_id=session.id,
            company_id=session.company_id,
            user_id=session.user_id,
            policy_id=policy_id,
            policy_name=policy_name,
            punch_in_time=session.punch_in_time,
            punch_out_time=session.punch_out_time,
            work_start_time=first_window.start_time,
            work_end_time=last_window.end_time,
            is_late=is_late,
            late_minutes=late_minutes,
            is_early_leave=is_early_leave,
            early_leave_minutes=early_leave_minutes,
            is_overtime=is_overtime,
            overtime_minutes=overtime_minutes,
            work_minutes=work_minutes,
            grace_period_minutes=grace_period_minutes,
            overtime_threshold_minutes=overtime_threshold_minutes
        )
    
    @staticmethod
    def _calculate_work_minutes_split_shift(
        punch_in_time: datetime,
        punch_out_time: datetime,
        windows: List[WorkWindow]
    ) -> int:
        """Calculate work minutes for split shift (WP-11-03S)
        
        Only counts time that falls within work windows.
        Time outside windows (breaks/gaps) is not counted.
        
        Args:
            punch_in_time: Actual punch-in time
            punch_out_time: Actual punch-out time
            windows: List of work windows (sorted)
        
        Returns:
            Total work minutes within windows
        """
        total_minutes = 0
        
        for window in windows:
            # Convert window times to datetime on the same date as punches
            window_start_dt = datetime.combine(
                punch_in_time.date(),
                window.start_time
            )
            window_end_dt = datetime.combine(
                punch_in_time.date(),
                window.end_time
            )
            
            # Make timezone-aware if needed
            if punch_in_time.tzinfo is not None:
                window_start_dt = window_start_dt.replace(tzinfo=punch_in_time.tzinfo)
                window_end_dt = window_end_dt.replace(tzinfo=punch_in_time.tzinfo)
            
            # Calculate overlap between punch times and this window
            effective_start = max(punch_in_time, window_start_dt)
            effective_end = min(punch_out_time, window_end_dt)
            
            # Only count if there's actual overlap
            if effective_start < effective_end:
                delta = effective_end - effective_start
                window_minutes = int(delta.total_seconds() / 60)
                total_minutes += window_minutes
                
                logger.debug(
                    f"Window {window.start_time}-{window.end_time}: "
                    f"counted {window_minutes} minutes "
                    f"(effective: {effective_start.time()}-{effective_end.time()})"
                )
        
        return total_minutes


def get_policy_engine() -> AttendancePolicyEngine:
    """Factory function for dependency injection (FastAPI)"""
    return AttendancePolicyEngine()
