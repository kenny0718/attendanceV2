"""Work Hour Engine — 工時計算引擎 (Phase 1 + Phase 2B)

Pure function module. No DB access. No repo imports. No policy imports.

Phase 1 scope:
- calculate_work_duration: gross duration only (punch_out - punch_in)

Phase 2B scope:
- BreakPunchDTO, BreakAnomaly, BreakDeductionResult: pure DTOs
- calculate_break_deduction: break-aware deduction engine (no integration yet)

Ownership:
- This module owns the canonical work duration calculation.
- api/punch.py delegates duration calculation here.
- reporting_service.py reads session.duration_minutes (canonical DB value).
- policy_engine.py consumes session.duration_minutes for evaluation.
"""

from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional


# ============================================================
# Phase 1: Gross Work Duration (unchanged)
# ============================================================

def calculate_work_duration(
    punch_in_time: datetime,
    punch_out_time: datetime,
) -> int:
    """Calculate gross work duration in minutes.

    Args:
        punch_in_time: Session punch-in time (UTC, timezone-aware).
        punch_out_time: Session punch-out time (UTC, timezone-aware).

    Returns:
        int: Gross duration in minutes (punch_out - punch_in).
             This is the canonical value written to session.duration_minutes.

    Note:
        Phase 1: gross only. Break deduction is NOT applied.
        Semantics are identical to the original punch.py calculation:
            int((punch_out_time - punch_in_time).total_seconds() / 60)
    """
    return int((punch_out_time - punch_in_time).total_seconds() / 60)


def calculate_work_minutes_by_segments(
    punch_in_time: datetime,
    punch_out_time: datetime,
    normalized_windows: List[tuple[datetime, datetime]],
) -> int:
    """Calculate overlapped work minutes from normalized schedule windows.

    Input windows MUST already be normalized datetimes from ScheduleBaselineResolver.
    """
    total_minutes = 0
    for window_start, window_end in normalized_windows:
        effective_start = max(punch_in_time, window_start)
        effective_end = min(punch_out_time, window_end)
        if effective_start < effective_end:
            total_minutes += int((effective_end - effective_start).total_seconds() / 60)
    return total_minutes


# ============================================================
# Phase 2B: Break Deduction Types
# ============================================================

@dataclass
class BreakPunchDTO:
    """Input DTO representing a single break punch event.

    Consumed by calculate_break_deduction(). Engine does NOT
    touch any ORM model; caller is responsible for mapping.
    """
    punch_type: str          # 'break_start' or 'break_end'
    punch_time: datetime
    punch_id: Optional[str] = None  # UUID str or any identifier; optional


@dataclass
class BreakAnomaly:
    """Describes a single anomaly detected during break pairing.

    anomaly_type values used by this engine:
        orphan_break_end         - break_end with no preceding break_start
        duplicate_break_start    - break_start while already in break
        unclosed_break_at_close  - break_start never paired with break_end
        invalid_pair_order       - pair end <= start (negative/zero duration)
        out_of_session_range     - punch_time outside [punch_in, punch_out]
        break_exceeds_gross      - total break_minutes clamped to gross
        unexpected_punch_type    - punch_type not in {break_start, break_end}
    """
    anomaly_type: str
    related_punch_ids: List[str] = field(default_factory=list)
    related_timestamps: List[datetime] = field(default_factory=list)
    message: str = ""
    session_id: Optional[str] = None


@dataclass
class BreakDeductionResult:
    """Result of calculate_break_deduction().

    gross_minutes  - int((punch_out - punch_in).total_seconds() / 60)
    break_minutes  - sum of floor(each valid pair seconds / 60), clamped to gross
    net_work_minutes - gross_minutes - break_minutes
    was_clamped    - True if break_minutes was clamped to gross_minutes
    """
    gross_minutes: int
    break_minutes: int
    net_work_minutes: int
    valid_break_pair_count: int
    anomaly_count: int
    anomalies: List[BreakAnomaly] = field(default_factory=list)
    was_clamped: bool = False
    pairing_strategy: str = "tolerant_state_machine"
    rounding_strategy: str = "floor_per_segment"


@dataclass
class FallbackDeductionResult:
    """Duck-type fallback for BreakDeductionResult when calculate_break_deduction() raises.

    Used exclusively in the punch-out except block to ensure downstream code
    (write_break_anomaly_audit, response shaping) receives a valid result object.

    anomaly_count=0 guarantees write_break_anomaly_audit() early-returns (no-op).
    anomalies uses default_factory=list to avoid shared-list class attribute risk.
    """
    gross_minutes: int
    net_work_minutes: int
    break_minutes: int = 0
    valid_break_pair_count: int = 0
    anomaly_count: int = 0
    anomalies: List[BreakAnomaly] = field(default_factory=list)
    was_clamped: bool = False
    pairing_strategy: str = "fallback"
    rounding_strategy: str = "floor"


@dataclass
class CanonicalWorkDurationResult:
    """Pure canonical work duration result for future Option B adoption.

    canonical_minutes represents net work duration (gross - break).
    This DTO is introduced in F1 only and is intentionally not wired to any
    existing runtime flow, persistence path, policy path, or reporting path.
    """
    gross_minutes: int
    break_minutes: int
    canonical_minutes: int
    valid_break_pair_count: int
    anomaly_count: int
    anomalies: List[BreakAnomaly] = field(default_factory=list)
    was_clamped: bool = False
    pairing_strategy: str = "tolerant_state_machine"
    rounding_strategy: str = "floor_per_segment"


# ============================================================
# Phase 2B: Break Deduction Engine
# ============================================================

_VALID_BREAK_TYPES = {"break_start", "break_end"}

# Internal state machine states
_STATE_IDLE = "IDLE"
_STATE_IN_BREAK = "IN_BREAK"


def calculate_break_deduction(
    punch_in_time: datetime,
    punch_out_time: datetime,
    break_punches: List[BreakPunchDTO],
) -> BreakDeductionResult:
    """Calculate break deduction from a list of break punch events.

    Pure function — no DB access, no side effects, no logging.

    Args:
        punch_in_time:  Session start time.
        punch_out_time: Session end time.
        break_punches:  List of BreakPunchDTO.  May be empty.
                        Engine sorts internally by punch_time ASC.

    Returns:
        BreakDeductionResult

    Raises:
        ValueError: Only when punch_in_time > punch_out_time (invalid session).
                    punch_in_time == punch_out_time is legal (gross = 0).

    Pairing strategy: tolerant state machine
        IDLE     + break_start -> IN_BREAK
        IDLE     + break_end   -> discard + anomaly orphan_break_end
        IN_BREAK + break_end   -> close pair
        IN_BREAK + break_start -> discard new start + anomaly duplicate_break_start
        end-of-scan in IN_BREAK -> discard + anomaly unclosed_break_at_close

    Rounding: floor(segment_seconds / 60) per segment, then sum.
    Clamping: if break_minutes >= gross_minutes, clamp to gross, net = 0.
    """
    # ------------------------------------------------------------------
    # 1. Input validation
    # ------------------------------------------------------------------
    if punch_in_time > punch_out_time:
        raise ValueError(
            f"punch_in_time ({punch_in_time}) must not be later than "
            f"punch_out_time ({punch_out_time})"
        )

    gross_minutes: int = int(
        (punch_out_time - punch_in_time).total_seconds() / 60
    )

    anomalies: List[BreakAnomaly] = []

    # ------------------------------------------------------------------
    # 2. Short-circuit: empty list
    # ------------------------------------------------------------------
    if not break_punches:
        return BreakDeductionResult(
            gross_minutes=gross_minutes,
            break_minutes=0,
            net_work_minutes=gross_minutes,
            valid_break_pair_count=0,
            anomaly_count=0,
            anomalies=[],
            was_clamped=False,
        )

    # ------------------------------------------------------------------
    # 3. Sort by punch_time ASC (engine owns ordering)
    # ------------------------------------------------------------------
    sorted_punches = sorted(break_punches, key=lambda p: p.punch_time)

    # ------------------------------------------------------------------
    # 4. Tolerant pairing state machine
    # ------------------------------------------------------------------
    state = _STATE_IDLE
    current_start: Optional[BreakPunchDTO] = None
    valid_pairs: List[tuple] = []  # list of (start_dto, end_dto)

    for punch in sorted_punches:
        punch_id_str = str(punch.punch_id) if punch.punch_id is not None else ""

        # --- defensive: unexpected punch_type ---
        if punch.punch_type not in _VALID_BREAK_TYPES:
            anomalies.append(BreakAnomaly(
                anomaly_type="unexpected_punch_type",
                related_punch_ids=[punch_id_str],
                related_timestamps=[punch.punch_time],
                message=(
                    f"Unexpected punch_type '{punch.punch_type}'; "
                    "expected break_start or break_end. Event discarded."
                ),
            ))
            continue  # discard, do not raise

        # --- out-of-session-range check ---
        if not (punch_in_time <= punch.punch_time <= punch_out_time):
            anomalies.append(BreakAnomaly(
                anomaly_type="out_of_session_range",
                related_punch_ids=[punch_id_str],
                related_timestamps=[punch.punch_time],
                message=(
                    f"punch_time {punch.punch_time} is outside session range "
                    f"[{punch_in_time}, {punch_out_time}]. Event discarded."
                ),
            ))
            continue

        # --- state machine ---
        if punch.punch_type == "break_start":
            if state == _STATE_IDLE:
                state = _STATE_IN_BREAK
                current_start = punch
            else:  # IN_BREAK
                anomalies.append(BreakAnomaly(
                    anomaly_type="duplicate_break_start",
                    related_punch_ids=[punch_id_str],
                    related_timestamps=[punch.punch_time],
                    message=(
                        f"break_start received while already in break "
                        f"(started at {current_start.punch_time}). "
                        "New start discarded; first-start-wins."
                    ),
                ))
                # discard new start; current_start unchanged

        else:  # break_end
            if state == _STATE_IN_BREAK:
                # Close the pair
                valid_pairs.append((current_start, punch))
                state = _STATE_IDLE
                current_start = None
            else:  # IDLE
                anomalies.append(BreakAnomaly(
                    anomaly_type="orphan_break_end",
                    related_punch_ids=[punch_id_str],
                    related_timestamps=[punch.punch_time],
                    message=(
                        f"break_end at {punch.punch_time} has no preceding "
                        "break_start. Event discarded."
                    ),
                ))

    # --- end-of-scan: still IN_BREAK ---
    if state == _STATE_IN_BREAK and current_start is not None:
        start_id = str(current_start.punch_id) if current_start.punch_id is not None else ""
        anomalies.append(BreakAnomaly(
            anomaly_type="unclosed_break_at_close",
            related_punch_ids=[start_id],
            related_timestamps=[current_start.punch_time],
            message=(
                f"break_start at {current_start.punch_time} was never closed "
                "before session end. Segment discarded."
            ),
        ))
        # discard unclosed segment (do not count it)

    # ------------------------------------------------------------------
    # 5. Calculate break_minutes from valid pairs
    # ------------------------------------------------------------------
    total_break_minutes = 0
    final_valid_pairs = []

    for start_dto, end_dto in valid_pairs:
        start_id = str(start_dto.punch_id) if start_dto.punch_id is not None else ""
        end_id = str(end_dto.punch_id) if end_dto.punch_id is not None else ""

        segment_seconds = (end_dto.punch_time - start_dto.punch_time).total_seconds()

        # invalid_pair_order: end <= start
        if segment_seconds <= 0:
            anomalies.append(BreakAnomaly(
                anomaly_type="invalid_pair_order",
                related_punch_ids=[start_id, end_id],
                related_timestamps=[start_dto.punch_time, end_dto.punch_time],
                message=(
                    f"Break pair end ({end_dto.punch_time}) is not after "
                    f"start ({start_dto.punch_time}). Pair discarded."
                ),
            ))
            continue

        segment_minutes = int(segment_seconds / 60)  # floor per segment
        total_break_minutes += segment_minutes
        final_valid_pairs.append((start_dto, end_dto))

    # ------------------------------------------------------------------
    # 6. Clamp break_minutes to gross_minutes
    # ------------------------------------------------------------------
    was_clamped = False
    if total_break_minutes >= gross_minutes:
        if total_break_minutes > gross_minutes or (total_break_minutes == gross_minutes and gross_minutes > 0):
            anomalies.append(BreakAnomaly(
                anomaly_type="break_exceeds_gross",
                related_punch_ids=[],
                related_timestamps=[],
                message=(
                    f"Total break_minutes ({total_break_minutes}) >= "
                    f"gross_minutes ({gross_minutes}). "
                    "Clamped to gross; net_work_minutes = 0."
                ),
            ))
        total_break_minutes = gross_minutes
        was_clamped = True

    net_work_minutes = gross_minutes - total_break_minutes

    return BreakDeductionResult(
        gross_minutes=gross_minutes,
        break_minutes=total_break_minutes,
        net_work_minutes=net_work_minutes,
        valid_break_pair_count=len(final_valid_pairs),
        anomaly_count=len(anomalies),
        anomalies=anomalies,
        was_clamped=was_clamped,
    )


def calculate_canonical_work_duration(
    punch_in_time: datetime,
    punch_out_time: datetime,
    break_punches: List[BreakPunchDTO],
) -> CanonicalWorkDurationResult:
    """Calculate canonical work duration as net work duration.

    F1 constraints:
    - pure composition only
    - no runtime wiring
    - no DB, repo, session, policy, API, or reporting logic
    - does not alter existing calculate_work_duration/calculate_break_deduction behavior
    """
    gross_minutes = calculate_work_duration(punch_in_time, punch_out_time)
    deduction_result = calculate_break_deduction(
        punch_in_time,
        punch_out_time,
        break_punches,
    )

    return CanonicalWorkDurationResult(
        gross_minutes=gross_minutes,
        break_minutes=deduction_result.break_minutes,
        canonical_minutes=deduction_result.net_work_minutes,
        valid_break_pair_count=deduction_result.valid_break_pair_count,
        anomaly_count=deduction_result.anomaly_count,
        anomalies=deduction_result.anomalies,
        was_clamped=deduction_result.was_clamped,
        pairing_strategy=deduction_result.pairing_strategy,
        rounding_strategy=deduction_result.rounding_strategy,
    )
