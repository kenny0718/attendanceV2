"""Attendance policy schedule domain models and value objects."""

import logging
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import List, Optional

DEFAULT_WORK_START_TIME = time(9, 0)
DEFAULT_WORK_END_TIME = time(18, 0)

logger = logging.getLogger(__name__)

# ============================================
# WP-11-03S: Work Schedule Abstractions
# ============================================

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
        start_dt = datetime.combine(date.min, self.start_time)
        end_dt = datetime.combine(date.min, self.end_time)
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
            # Use shared default work time constants
            window = WorkWindow(
                start_time=DEFAULT_WORK_START_TIME,
                end_time=DEFAULT_WORK_END_TIME
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


