"""Unit tests for work_hour_engine.py (Phase 2B)

Pure unit tests -- no DB, no fixtures, no repo, no integration.
Covers:
  1.  gross only baseline (calculate_work_duration unchanged)
  2.  empty break list
  3.  single valid break pair
  4.  multiple valid break pairs
  5.  orphan break_start (unclosed)
  6.  orphan break_end
  7.  duplicate break_start (first-start-wins)
  8.  duplicate break_end discarded with anomaly
  9.  unclosed break at session close
  10. out-of-session-range break punch
  11. invalid pair order / negative duration
  12. break exceeds gross -> clamp
  13. punch_in_time == punch_out_time (gross=0, legal)
  14. punch_in_time > punch_out_time -> ValueError
  15. unexpected punch_type -> anomaly, discard
  16. input order scrambled -> engine sort, correct result
  17. canonical pure calculation wrapper
"""

import pytest
from datetime import datetime, timezone, timedelta

from app.modules.attendance.work_hour_engine import (
    calculate_work_duration,
    calculate_break_deduction,
    calculate_canonical_work_duration,
    BreakPunchDTO,
    BreakAnomaly,
    BreakDeductionResult,
    CanonicalWorkDurationResult,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dt(hour: int, minute: int = 0, second: int = 0) -> datetime:
    """Create a UTC datetime on 2026-03-30 for test use."""
    return datetime(2026, 3, 30, hour, minute, second, tzinfo=timezone.utc)


def _bp(punch_type: str, hour: int, minute: int = 0, pid: str = None) -> BreakPunchDTO:
    """Convenience BreakPunchDTO factory."""
    return BreakPunchDTO(
        punch_type=punch_type,
        punch_time=_dt(hour, minute),
        punch_id=pid,
    )


# ---------------------------------------------------------------------------
# 1. Gross only baseline -- calculate_work_duration unchanged
# ---------------------------------------------------------------------------

class TestCalculateWorkDuration:
    """Verify Phase 1 API is completely unaffected."""

    def test_normal_duration(self):
        result = calculate_work_duration(_dt(9), _dt(18))
        assert result == 540

    def test_zero_duration(self):
        """punch_in == punch_out -> 0 (legal for gross API)"""
        result = calculate_work_duration(_dt(9), _dt(9))
        assert result == 0

    def test_partial_hour(self):
        result = calculate_work_duration(_dt(9, 0), _dt(9, 45))
        assert result == 45

    def test_negative_returns_negative(self):
        """calculate_work_duration has no validation; semantics unchanged."""
        result = calculate_work_duration(_dt(18), _dt(9))
        assert result == -540

    def test_signature_preserved(self):
        """Ensure the function still accepts exactly 2 positional args."""
        import inspect
        sig = inspect.signature(calculate_work_duration)
        params = list(sig.parameters.keys())
        assert params == ["punch_in_time", "punch_out_time"]


# ---------------------------------------------------------------------------
# 2. Empty break list
# ---------------------------------------------------------------------------

class TestEmptyBreakList:
    def test_empty_list_returns_gross(self):
        result = calculate_break_deduction(_dt(9), _dt(18), [])
        assert result.gross_minutes == 540
        assert result.break_minutes == 0
        assert result.net_work_minutes == 540
        assert result.anomaly_count == 0
        assert result.anomalies == []
        assert result.valid_break_pair_count == 0
        assert result.was_clamped is False


# ---------------------------------------------------------------------------
# 3. Single valid break pair
# ---------------------------------------------------------------------------

class TestSingleValidBreakPair:
    def test_single_pair_30_minutes(self):
        punches = [
            _bp("break_start", 12, 0,  "p1"),
            _bp("break_end",   12, 30, "p2"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.gross_minutes == 540
        assert result.break_minutes == 30
        assert result.net_work_minutes == 510
        assert result.valid_break_pair_count == 1
        assert result.anomaly_count == 0
        assert result.was_clamped is False

    def test_floor_rounding_partial_minute(self):
        """Break of 30 min 59 sec -> floor -> 30 minutes."""
        start = datetime(2026, 3, 30, 12, 0, 0,  tzinfo=timezone.utc)
        end   = datetime(2026, 3, 30, 12, 30, 59, tzinfo=timezone.utc)
        punches = [
            BreakPunchDTO(punch_type="break_start", punch_time=start, punch_id="p1"),
            BreakPunchDTO(punch_type="break_end",   punch_time=end,   punch_id="p2"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.break_minutes == 30


# ---------------------------------------------------------------------------
# 4. Multiple valid break pairs
# ---------------------------------------------------------------------------

class TestMultipleValidBreakPairs:
    def test_two_pairs_floor_each(self):
        punches = [
            _bp("break_start", 10, 0,  "p1"),
            _bp("break_end",   10, 15, "p2"),
            _bp("break_start", 12, 0,  "p3"),
            _bp("break_end",   12, 45, "p4"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.break_minutes == 60
        assert result.net_work_minutes == 480
        assert result.valid_break_pair_count == 2
        assert result.anomaly_count == 0

    def test_three_pairs(self):
        punches = [
            _bp("break_start", 10, 0,  "p1"),
            _bp("break_end",   10, 10, "p2"),
            _bp("break_start", 12, 0,  "p3"),
            _bp("break_end",   12, 20, "p4"),
            _bp("break_start", 15, 0,  "p5"),
            _bp("break_end",   15, 5,  "p6"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.break_minutes == 35
        assert result.valid_break_pair_count == 3


# ---------------------------------------------------------------------------
# 5. Orphan break_start (unclosed at session end)
# ---------------------------------------------------------------------------

class TestOrphanBreakStart:
    def test_unclosed_break_start_not_counted(self):
        punches = [
            _bp("break_start", 12, 0, "p1"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.break_minutes == 0
        assert result.net_work_minutes == 540
        assert result.valid_break_pair_count == 0
        assert result.anomaly_count == 1
        assert result.anomalies[0].anomaly_type == "unclosed_break_at_close"


# ---------------------------------------------------------------------------
# 6. Orphan break_end
# ---------------------------------------------------------------------------

class TestOrphanBreakEnd:
    def test_orphan_break_end_not_counted(self):
        punches = [
            _bp("break_end", 12, 30, "p1"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.break_minutes == 0
        assert result.anomaly_count == 1
        assert result.anomalies[0].anomaly_type == "orphan_break_end"

    def test_orphan_end_then_valid_pair(self):
        """Orphan end first; subsequent valid pair still counted."""
        punches = [
            _bp("break_end",   10, 0,  "p0"),
            _bp("break_start", 12, 0,  "p1"),
            _bp("break_end",   12, 30, "p2"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.break_minutes == 30
        assert result.valid_break_pair_count == 1
        assert result.anomaly_count == 1
        assert result.anomalies[0].anomaly_type == "orphan_break_end"


# ---------------------------------------------------------------------------
# 7. Duplicate break_start (first-start-wins)
# ---------------------------------------------------------------------------

class TestDuplicateBreakStart:
    def test_duplicate_start_first_wins(self):
        punches = [
            _bp("break_start", 12, 0,  "p1"),
            _bp("break_start", 12, 10, "p2"),
            _bp("break_end",   12, 30, "p3"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.break_minutes == 30
        assert result.valid_break_pair_count == 1
        assert result.anomaly_count == 1
        assert result.anomalies[0].anomaly_type == "duplicate_break_start"


# ---------------------------------------------------------------------------
# 8. Duplicate break_end (extra end becomes orphan)
# ---------------------------------------------------------------------------

class TestDuplicateBreakEnd:
    def test_extra_end_becomes_orphan(self):
        punches = [
            _bp("break_start", 12, 0,  "p1"),
            _bp("break_end",   12, 30, "p2"),
            _bp("break_end",   12, 45, "p3"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.break_minutes == 30
        assert result.valid_break_pair_count == 1
        assert result.anomaly_count == 1
        assert result.anomalies[0].anomaly_type == "orphan_break_end"


# ---------------------------------------------------------------------------
# 9. Unclosed break at session close
# ---------------------------------------------------------------------------

class TestUnclosedBreakAtClose:
    def test_one_valid_one_unclosed(self):
        punches = [
            _bp("break_start", 10, 0,  "p1"),
            _bp("break_end",   10, 15, "p2"),
            _bp("break_start", 12, 0,  "p3"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.break_minutes == 15
        assert result.valid_break_pair_count == 1
        assert result.anomaly_count == 1
        assert result.anomalies[0].anomaly_type == "unclosed_break_at_close"


# ---------------------------------------------------------------------------
# 10. Out-of-session-range break punch
# ---------------------------------------------------------------------------

class TestOutOfSessionRange:
    def test_break_before_punch_in_discarded(self):
        punches = [
            _bp("break_start", 8, 0,  "p1"),
            _bp("break_end",   8, 30, "p2"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.break_minutes == 0
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert anomaly_types.count("out_of_session_range") == 2

    def test_break_after_punch_out_discarded(self):
        punches = [
            _bp("break_start", 18, 30, "p1"),
            _bp("break_end",   19, 0,  "p2"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.break_minutes == 0
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "out_of_session_range" in anomaly_types

    def test_valid_pair_unaffected_by_out_of_range(self):
        punches = [
            _bp("break_start", 8, 0,  "p0"),
            _bp("break_end",   8, 30, "p00"),
            _bp("break_start", 12, 0,  "p1"),
            _bp("break_end",   12, 30, "p2"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.break_minutes == 30
        assert result.valid_break_pair_count == 1


# ---------------------------------------------------------------------------
# 11. Invalid pair order (end == start -> 0 seconds)
# ---------------------------------------------------------------------------

class TestInvalidPairOrder:
    def test_zero_duration_pair_discarded(self):
        punches = [
            BreakPunchDTO(punch_type="break_start", punch_time=_dt(12, 0), punch_id="p1"),
            BreakPunchDTO(punch_type="break_end",   punch_time=_dt(12, 0), punch_id="p2"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.break_minutes == 0
        assert result.valid_break_pair_count == 0
        assert result.anomaly_count == 1
        assert result.anomalies[0].anomaly_type == "invalid_pair_order"

    def test_scrambled_input_sorted_correctly(self):
        punches = [
            BreakPunchDTO(punch_type="break_start", punch_time=_dt(12, 30), punch_id="p1"),
            BreakPunchDTO(punch_type="break_end",   punch_time=_dt(12, 0),  punch_id="p2"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.break_minutes == 0
        assert result.anomaly_count >= 1


# ---------------------------------------------------------------------------
# 12. Break exceeds gross -> clamp
# ---------------------------------------------------------------------------

class TestBreakExceedsGross:
    def test_break_equals_gross_clamped(self):
        punches = [
            _bp("break_start", 9, 0,  "p1"),
            _bp("break_end",   10, 0, "p2"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(10), punches)
        assert result.gross_minutes == 60
        assert result.break_minutes == 60
        assert result.net_work_minutes == 0
        assert result.was_clamped is True
        anomaly_types = {a.anomaly_type for a in result.anomalies}
        assert "break_exceeds_gross" in anomaly_types

    def test_break_less_than_gross_not_clamped(self):
        punches = [
            _bp("break_start", 9, 0,  "p1"),
            _bp("break_end",   9, 30, "p2"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(11), punches)
        assert result.gross_minutes == 120
        assert result.break_minutes == 30
        assert result.net_work_minutes == 90
        assert result.was_clamped is False

    def test_gross_zero_break_zero_no_clamp(self):
        result = calculate_break_deduction(_dt(9), _dt(9), [])
        assert result.gross_minutes == 0
        assert result.break_minutes == 0
        assert result.net_work_minutes == 0
        assert result.was_clamped is False


# ---------------------------------------------------------------------------
# 13. punch_in_time == punch_out_time (gross=0, legal)
# ---------------------------------------------------------------------------

class TestEqualPunchTimes:
    def test_equal_times_legal_gross_zero(self):
        result = calculate_break_deduction(_dt(9), _dt(9), [])
        assert result.gross_minutes == 0
        assert result.break_minutes == 0
        assert result.net_work_minutes == 0
        assert result.anomaly_count == 0

    def test_equal_times_with_break_punches_all_out_of_range(self):
        punches = [
            _bp("break_start", 8, 0, "p1"),
            _bp("break_end",   10, 0, "p2"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(9), punches)
        assert result.break_minutes == 0
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "out_of_session_range" in anomaly_types


# ---------------------------------------------------------------------------
# 14. punch_in_time > punch_out_time -> ValueError
# ---------------------------------------------------------------------------

class TestInvalidSessionTimes:
    def test_punch_in_after_punch_out_raises(self):
        with pytest.raises(ValueError):
            calculate_break_deduction(_dt(18), _dt(9), [])

    def test_punch_in_one_second_after_raises(self):
        t = _dt(9)
        with pytest.raises(ValueError):
            calculate_break_deduction(t + timedelta(seconds=1), t, [])


# ---------------------------------------------------------------------------
# 15. Unexpected punch_type -> anomaly, discard (no raise)
# ---------------------------------------------------------------------------

class TestUnexpectedPunchType:
    def test_unknown_type_creates_anomaly(self):
        punches = [
            BreakPunchDTO(punch_type="lunch", punch_time=_dt(12, 0), punch_id="p1"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.break_minutes == 0
        assert result.anomaly_count == 1
        assert result.anomalies[0].anomaly_type == "unexpected_punch_type"

    def test_unknown_type_does_not_raise(self):
        punches = [
            BreakPunchDTO(punch_type="in",  punch_time=_dt(10, 0), punch_id="p1"),
            BreakPunchDTO(punch_type="out", punch_time=_dt(11, 0), punch_id="p2"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.break_minutes == 0
        assert result.anomaly_count == 2

    def test_mix_of_valid_and_unknown_type(self):
        punches = [
            BreakPunchDTO(punch_type="lunch",       punch_time=_dt(10, 0), punch_id="p0"),
            BreakPunchDTO(punch_type="break_start", punch_time=_dt(12, 0), punch_id="p1"),
            BreakPunchDTO(punch_type="break_end",   punch_time=_dt(12, 30), punch_id="p2"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.break_minutes == 30
        assert result.valid_break_pair_count == 1
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "unexpected_punch_type" in anomaly_types


# ---------------------------------------------------------------------------
# 16. Input order scrambled -> engine internal sort -> correct result
# ---------------------------------------------------------------------------

class TestInputOrderScrambled:
    def test_reversed_input_sorted_correctly(self):
        punches = [
            _bp("break_end",   12, 30, "p2"),
            _bp("break_start", 12, 0,  "p1"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.break_minutes == 30
        assert result.valid_break_pair_count == 1
        assert result.anomaly_count == 0

    def test_three_pairs_scrambled_order(self):
        punches = [
            _bp("break_end",   15, 5,  "p6"),
            _bp("break_start", 10, 0,  "p1"),
            _bp("break_end",   12, 20, "p4"),
            _bp("break_start", 15, 0,  "p5"),
            _bp("break_end",   10, 10, "p2"),
            _bp("break_start", 12, 0,  "p3"),
        ]
        result = calculate_break_deduction(_dt(9), _dt(18), punches)
        assert result.break_minutes == 35
        assert result.valid_break_pair_count == 3
        assert result.anomaly_count == 0

    def test_metadata_fields_present(self):
        result = calculate_break_deduction(_dt(9), _dt(18), [])
        assert result.pairing_strategy == "tolerant_state_machine"
        assert result.rounding_strategy == "floor_per_segment"


# ---------------------------------------------------------------------------
# 17. Canonical pure calculation wrapper
# ---------------------------------------------------------------------------

class TestCalculateCanonicalWorkDuration:
    def test_no_breaks_canonical_equals_gross(self):
        result = calculate_canonical_work_duration(_dt(9), _dt(18), [])
        assert isinstance(result, CanonicalWorkDurationResult)
        assert result.gross_minutes == 540
        assert result.break_minutes == 0
        assert result.canonical_minutes == 540
        assert result.valid_break_pair_count == 0
        assert result.anomaly_count == 0

    def test_single_break_canonical_equals_gross_minus_break(self):
        punches = [
            _bp("break_start", 12, 0, "p1"),
            _bp("break_end", 12, 30, "p2"),
        ]
        result = calculate_canonical_work_duration(_dt(9), _dt(18), punches)
        assert result.gross_minutes == 540
        assert result.break_minutes == 30
        assert result.canonical_minutes == 510
        assert result.valid_break_pair_count == 1
        assert result.anomaly_count == 0

    def test_multiple_breaks_canonical_uses_engine_result(self):
        punches = [
            _bp("break_start", 10, 0, "p1"),
            _bp("break_end", 10, 15, "p2"),
            _bp("break_start", 12, 0, "p3"),
            _bp("break_end", 12, 45, "p4"),
        ]
        result = calculate_canonical_work_duration(_dt(9), _dt(18), punches)
        assert result.gross_minutes == 540
        assert result.break_minutes == 60
        assert result.canonical_minutes == 480
        assert result.valid_break_pair_count == 2
        assert result.pairing_strategy == "tolerant_state_machine"
        assert result.rounding_strategy == "floor_per_segment"

    def test_signature_preserved_as_pure_function(self):
        import inspect
        sig = inspect.signature(calculate_canonical_work_duration)
        params = list(sig.parameters.keys())
        assert params == ["punch_in_time", "punch_out_time", "break_punches"]
