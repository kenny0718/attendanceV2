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
from datetime import date, datetime, time, timedelta
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

TZ_TAIPEI = ZoneInfo("Asia/Taipei")

from app.modules.attendance.models import AttendanceSession, AttendancePolicy
from app.modules.schedule.service import ScheduleBaselineResolver
from app.modules.attendance.policy_rules import (
    calculate_early_leave,
    calculate_early_leave_from_datetime,
    calculate_late,
    calculate_late_from_datetime,
    calculate_overtime,
)

logger = logging.getLogger(__name__)



from app.modules.attendance.policy_schedule_models import (
    DEFAULT_WORK_START_TIME as SHARED_DEFAULT_WORK_START_TIME,
    DEFAULT_WORK_END_TIME as SHARED_DEFAULT_WORK_END_TIME,
    WorkWindow,
    FlexTimeBand,
    WorkSchedule,
)


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
        overtime_threshold_minutes: Optional[int],
        # Schedule-aware extension (non-breaking)
        schedule_violation_flags: Optional[List[str]] = None,
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

        # Schedule-aware extension
        self.schedule_violation_flags = list(schedule_violation_flags or [])
    
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
            },
            "schedule": {
                "violation_flags": self.schedule_violation_flags,
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
    DEFAULT_WORK_START_TIME = SHARED_DEFAULT_WORK_START_TIME  # 09:00
    DEFAULT_WORK_END_TIME = SHARED_DEFAULT_WORK_END_TIME  # 18:00
    
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
        is_late, late_minutes = calculate_late(
            punch_in_time=session.punch_in_time,
            work_start_time=work_start_time,
            grace_period_minutes=grace_period_minutes
        )
        
        # 2. Early leave detection
        is_early_leave, early_leave_minutes = calculate_early_leave(
            punch_out_time=session.punch_out_time,
            work_end_time=work_end_time
        )
        
        # 3. Overtime detection
        is_overtime, overtime_minutes = calculate_overtime(
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
    def _to_business_date(dt: datetime) -> date:
        if dt.tzinfo is not None:
            return dt.astimezone(TZ_TAIPEI).date()
        return dt.date()



    @staticmethod
    def evaluate_with_schedule_v2(
        session: AttendanceSession,
        db: Session,
        policy: Optional[AttendancePolicy] = None,
    ) -> PolicyEvaluationResult:
        if session.status == 'open' or session.punch_out_time is None:
            raise ValueError(
                f"Cannot evaluate open session {session.id}. "
                "Session must be closed (punch_out_time must be set)."
            )

        if policy:
            grace_period_minutes = policy.grace_period_minutes
            overtime_threshold_minutes = policy.overtime_threshold_minutes
            policy_id = policy.id
            policy_name = policy.name
        else:
            grace_period_minutes = AttendancePolicyEngine.DEFAULT_GRACE_PERIOD_MINUTES
            overtime_threshold_minutes = AttendancePolicyEngine.DEFAULT_OVERTIME_THRESHOLD_MINUTES
            policy_id = None
            policy_name = "Default Policy (No Policy Assigned)"

        work_date = AttendancePolicyEngine._to_business_date(session.punch_in_time)
        baseline = ScheduleBaselineResolver(db).resolve(
            company_id=session.company_id,
            user_id=session.user_id,
            work_date=work_date,
        )
        normalized_windows = baseline.normalized_windows

        if not normalized_windows:
            default_start = datetime.combine(work_date, AttendancePolicyEngine.DEFAULT_WORK_START_TIME).replace(tzinfo=TZ_TAIPEI)
            default_end = datetime.combine(work_date, AttendancePolicyEngine.DEFAULT_WORK_END_TIME).replace(tzinfo=TZ_TAIPEI)
            normalized_windows = [(default_start, default_end)]

        first_window_start = normalized_windows[0][0]
        last_window_end = normalized_windows[-1][1]

        is_late, late_minutes = calculate_late_from_datetime(
            punch_in_time=session.punch_in_time,
            expected_start=first_window_start,
            grace_period_minutes=grace_period_minutes,
        )

        # Step 2 scope: missing_segment is deferred to runtime hardening phase.
        violation_flags: List[str] = []
        is_early_leave, early_leave_minutes = calculate_early_leave_from_datetime(
            punch_out_time=session.punch_out_time,
            expected_end=last_window_end,
        )

        work_minutes = session.duration_minutes or 0

        return PolicyEvaluationResult(
            session_id=session.id,
            company_id=session.company_id,
            user_id=session.user_id,
            policy_id=policy_id,
            policy_name=policy_name,
            punch_in_time=session.punch_in_time,
            punch_out_time=session.punch_out_time,
            work_start_time=first_window_start.astimezone(TZ_TAIPEI).time().replace(tzinfo=None),
            work_end_time=last_window_end.astimezone(TZ_TAIPEI).time().replace(tzinfo=None),
            is_late=is_late,
            late_minutes=late_minutes,
            is_early_leave=is_early_leave,
            early_leave_minutes=early_leave_minutes,
            is_overtime=False,
            overtime_minutes=0,
            work_minutes=work_minutes,
            grace_period_minutes=grace_period_minutes,
            overtime_threshold_minutes=overtime_threshold_minutes,
            schedule_violation_flags=violation_flags,
        )




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
        is_late, late_minutes = calculate_late(
            punch_in_time=session.punch_in_time,
            work_start_time=first_window.start_time,
            grace_period_minutes=grace_period_minutes
        )
        
        # 2. Early leave detection (based on last window)
        is_early_leave, early_leave_minutes = calculate_early_leave(
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
        is_overtime, overtime_minutes = calculate_overtime(
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
            # Derive business date in Asia/Taipei for window boundaries
            # P1-01/P1-02 fix: use Taipei local date and mark with TZ_TAIPEI
            if punch_in_time.tzinfo is not None:
                taipei_date = punch_in_time.astimezone(TZ_TAIPEI).date()
            else:
                taipei_date = punch_in_time.date()
            window_start_dt = datetime.combine(taipei_date, window.start_time).replace(tzinfo=TZ_TAIPEI)
            window_end_dt = datetime.combine(taipei_date, window.end_time).replace(tzinfo=TZ_TAIPEI)
            
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
