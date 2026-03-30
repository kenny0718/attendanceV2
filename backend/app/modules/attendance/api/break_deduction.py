"""Break Deduction Integration Helper (Phase 2D Second Cut)

Extracted from api/punch.py Phase 2C-A/2C-C block.

Responsibility:
- Filter break_start / break_end punches from session_punches
- Map to BreakPunchDTO
- Call calculate_break_deduction()
- Defensive fallback to FallbackDeductionResult on engine exception

Boundary (what this helper CANNOT do):
- Cannot call repo.close_session()
- Cannot write session.duration_minutes
- Cannot run policy evaluation
- Cannot write audit logs
- Cannot shape API response
- Cannot make any business rule decisions about gross/net
- Never raises
"""

import logging

from app.modules.attendance.work_hour_engine import (
    calculate_break_deduction,
    BreakPunchDTO,
    FallbackDeductionResult,
)


def resolve_break_deduction(
    session_punches,
    punch_in_time,
    punch_out_time,
    gross_minutes: int,
    logger: logging.Logger,
):
    """Resolve break deduction from session punches.

    Encapsulates the break deduction integration block from punch_out():
      1. Filter break_start / break_end punches
      2. Map to BreakPunchDTO
      3. Call calculate_break_deduction()
      4. On exception: log error and return FallbackDeductionResult

    Returns:
        BreakDeductionResult or FallbackDeductionResult (duck-type compatible).
        anomaly_count=0 in fallback path ensures write_break_anomaly_audit() no-ops.

    Never raises. Punch-out is never blocked by engine failure.
    """
    break_punches = [
        p for p in session_punches
        if p.punch_type in ("break_start", "break_end")
    ]
    break_punch_dtos = [
        BreakPunchDTO(
            punch_type=p.punch_type,
            punch_time=p.punch_time,
            punch_id=str(p.id),
        )
        for p in break_punches
    ]
    try:
        return calculate_break_deduction(
            punch_in_time,
            punch_out_time,
            break_punch_dtos,
        )
    except Exception:
        logger.error("Break deduction failed, fallback to gross", exc_info=True)
        return FallbackDeductionResult(
            gross_minutes=gross_minutes,
            net_work_minutes=gross_minutes,
        )
