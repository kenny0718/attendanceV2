from datetime import datetime
from zoneinfo import ZoneInfo

from app.modules.attendance.policy_missing_segment import (
    MissingSegmentInput,
    NormalizedSegment,
    evaluate_missing_segment_dry_run,
)


TZ = ZoneInfo("Asia/Taipei")


def _dt(hour: int, minute: int = 0, second: int = 0) -> datetime:
    return datetime(2026, 3, 4, hour, minute, second, tzinfo=TZ)


def test_insufficient_evidence_returns_not_decidable():
    data = MissingSegmentInput(
        expected_segments=[NormalizedSegment(start_at=_dt(9), end_at=_dt(18))],
        actual_segments=[NormalizedSegment(start_at=_dt(9), end_at=_dt(18))],
        exception_segments=[],
        evidence_sufficient=False,
    )

    result = evaluate_missing_segment_dry_run(data)

    assert result.is_decidable is False
    assert result.missing_segment is False
    assert result.reason == "insufficient_evidence"


def test_full_coverage_returns_not_missing():
    data = MissingSegmentInput(
        expected_segments=[NormalizedSegment(start_at=_dt(9), end_at=_dt(18))],
        actual_segments=[NormalizedSegment(start_at=_dt(9), end_at=_dt(18))],
        exception_segments=[],
        evidence_sufficient=True,
    )

    result = evaluate_missing_segment_dry_run(data)

    assert result.is_decidable is True
    assert result.missing_segment is False
    assert result.reason == "fully_covered"


def test_no_coverage_no_exception_returns_missing():
    data = MissingSegmentInput(
        expected_segments=[NormalizedSegment(start_at=_dt(9), end_at=_dt(18))],
        actual_segments=[],
        exception_segments=[],
        evidence_sufficient=True,
    )

    result = evaluate_missing_segment_dry_run(data)

    assert result.is_decidable is True
    assert result.missing_segment is True
    assert result.reason == "uncovered_expected_segment"


def test_exception_fully_covers_gap_returns_not_missing_with_reason():
    data = MissingSegmentInput(
        expected_segments=[NormalizedSegment(start_at=_dt(9), end_at=_dt(18))],
        actual_segments=[NormalizedSegment(start_at=_dt(9), end_at=_dt(12))],
        exception_segments=[NormalizedSegment(start_at=_dt(12), end_at=_dt(18))],
        evidence_sufficient=True,
    )

    result = evaluate_missing_segment_dry_run(data)

    assert result.is_decidable is True
    assert result.missing_segment is False
    assert result.reason == "covered_by_exception"


def test_multiple_actual_segments_fully_cover_expected_returns_not_missing():
    data = MissingSegmentInput(
        expected_segments=[NormalizedSegment(start_at=_dt(9), end_at=_dt(18))],
        actual_segments=[
            NormalizedSegment(start_at=_dt(9), end_at=_dt(12)),
            NormalizedSegment(start_at=_dt(12), end_at=_dt(15)),
            NormalizedSegment(start_at=_dt(15), end_at=_dt(18)),
        ],
        exception_segments=[],
        evidence_sufficient=True,
    )

    result = evaluate_missing_segment_dry_run(data)

    assert result.is_decidable is True
    assert result.missing_segment is False
    assert result.reason == "fully_covered"


def test_multiple_actual_segments_still_have_gap_returns_missing():
    data = MissingSegmentInput(
        expected_segments=[NormalizedSegment(start_at=_dt(9), end_at=_dt(18))],
        actual_segments=[
            NormalizedSegment(start_at=_dt(9), end_at=_dt(12)),
            NormalizedSegment(start_at=_dt(13), end_at=_dt(18)),
        ],
        exception_segments=[],
        evidence_sufficient=True,
    )

    result = evaluate_missing_segment_dry_run(data)

    assert result.is_decidable is True
    assert result.missing_segment is True
    assert result.reason == "uncovered_expected_segment"


def test_tolerated_tiny_boundary_gap_returns_not_missing():
    data = MissingSegmentInput(
        expected_segments=[NormalizedSegment(start_at=_dt(9), end_at=_dt(10))],
        actual_segments=[
            NormalizedSegment(start_at=_dt(9), end_at=_dt(9, 29, 59)),
            NormalizedSegment(start_at=_dt(9, 30, 0), end_at=_dt(10)),
        ],
        exception_segments=[],
        evidence_sufficient=True,
        boundary_tolerance_seconds=1,
    )

    result = evaluate_missing_segment_dry_run(data)

    assert result.is_decidable is True
    assert result.missing_segment is False
    assert result.reason == "tolerated_boundary_gap"
