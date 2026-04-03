"""Missing segment dry-run pure computation module (Step 3 split entry)."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple


@dataclass(frozen=True)
class NormalizedSegment:
    """A normalized time segment for expected/actual/exception input."""

    start_at: datetime
    end_at: datetime

    def duration_seconds(self) -> int:
        if self.end_at <= self.start_at:
            return 0
        return int((self.end_at - self.start_at).total_seconds())


@dataclass(frozen=True)
class MissingSegmentInput:
    """Input for missing-segment dry-run evaluation.

    Notes:
    - expected_segments / actual_segments / exception_segments must be pre-normalized.
    - This module does not perform trace building or database access.
    """

    expected_segments: List[NormalizedSegment]
    actual_segments: List[NormalizedSegment]
    exception_segments: List[NormalizedSegment]
    evidence_sufficient: bool
    boundary_tolerance_seconds: int = 0


@dataclass(frozen=True)
class MissingSegmentResult:
    """Minimal deterministic dry-run output."""

    is_decidable: bool
    missing_segment: bool
    reason: str


def evaluate_missing_segment_dry_run(data: MissingSegmentInput) -> MissingSegmentResult:
    """Evaluate missing_segment in dry-run mode using normalized inputs only."""
    if not data.evidence_sufficient:
        return MissingSegmentResult(
            is_decidable=False,
            missing_segment=False,
            reason="insufficient_evidence",
        )

    expected_seconds = _sum_seconds(data.expected_segments)
    if expected_seconds == 0:
        return MissingSegmentResult(
            is_decidable=True,
            missing_segment=False,
            reason="fully_covered",
        )

    actual_covered_seconds = _covered_expected_seconds(
        expected_segments=data.expected_segments,
        coverage_segments=data.actual_segments,
    )
    combined_covered_seconds = _covered_expected_seconds(
        expected_segments=data.expected_segments,
        coverage_segments=data.actual_segments + data.exception_segments,
    )

    if combined_covered_seconds >= expected_seconds:
        if actual_covered_seconds >= expected_seconds:
            return MissingSegmentResult(
                is_decidable=True,
                missing_segment=False,
                reason="fully_covered",
            )
        return MissingSegmentResult(
            is_decidable=True,
            missing_segment=False,
            reason="covered_by_exception",
        )

    uncovered_seconds = expected_seconds - combined_covered_seconds
    if uncovered_seconds <= max(0, data.boundary_tolerance_seconds):
        return MissingSegmentResult(
            is_decidable=True,
            missing_segment=False,
            reason="tolerated_boundary_gap",
        )

    return MissingSegmentResult(
        is_decidable=True,
        missing_segment=True,
        reason="uncovered_expected_segment",
    )


def _sum_seconds(segments: List[NormalizedSegment]) -> int:
    return sum(segment.duration_seconds() for segment in segments)


def _covered_expected_seconds(
    expected_segments: List[NormalizedSegment],
    coverage_segments: List[NormalizedSegment],
) -> int:
    total = 0
    for expected in expected_segments:
        overlaps = _collect_overlaps(expected, coverage_segments)
        total += _merged_length_seconds(overlaps)
    return total


def _collect_overlaps(
    expected: NormalizedSegment,
    coverage_segments: List[NormalizedSegment],
) -> List[Tuple[datetime, datetime]]:
    overlaps: List[Tuple[datetime, datetime]] = []
    for source in coverage_segments:
        start_at = max(expected.start_at, source.start_at)
        end_at = min(expected.end_at, source.end_at)
        if end_at > start_at:
            overlaps.append((start_at, end_at))
    return overlaps


def _merged_length_seconds(intervals: List[Tuple[datetime, datetime]]) -> int:
    if not intervals:
        return 0

    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    merged_seconds = 0
    current_start, current_end = sorted_intervals[0]

    for start_at, end_at in sorted_intervals[1:]:
        if start_at <= current_end:
            if end_at > current_end:
                current_end = end_at
        else:
            merged_seconds += int((current_end - current_start).total_seconds())
            current_start, current_end = start_at, end_at

    merged_seconds += int((current_end - current_start).total_seconds())
    return merged_seconds
