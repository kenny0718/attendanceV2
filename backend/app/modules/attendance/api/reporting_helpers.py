"""Reporting API — Shared helper utilities

Extracted from reporting.py (Micro Decomposition Step 2).
Contains only pure utility functions:
- no DB access
- no repo calls
- no actor/permission logic
- no response shaping

Phase 2 / F1:
- adds a canonical Taipei business-date normalization owner
- pure/helper only
- not wired into any runtime route yet
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo
from fastapi import HTTPException


TZ_TAIPEI = ZoneInfo("Asia/Taipei")


@dataclass(frozen=True)
class TaipeiBusinessDateBoundary:
    """Canonical UTC query boundary derived from an Asia/Taipei business date."""

    business_date: date
    timezone_name: str
    start_local: datetime
    end_local: datetime
    start_utc: datetime
    end_utc: datetime


def _normalize_to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """將 timezone-aware datetime 轉換為 UTC。
    naive datetime（無 tzinfo）呼叫方不應傳入，應由 validator 在 API 層攔截。
    """
    if dt is None:
        return None
    return dt.astimezone(timezone.utc)


def get_taipei_today(now: Optional[datetime] = None) -> date:
    """Return today's business date in Asia/Taipei.

    Optional ``now`` exists only to keep the helper pure and testable.
    """
    base = now or datetime.now(timezone.utc)
    return base.astimezone(TZ_TAIPEI).date()


def build_taipei_business_date_boundary(
    business_date: date,
) -> TaipeiBusinessDateBoundary:
    """Build canonical UTC query boundary from a Taipei business date.

    Contract:
    - owner = Asia/Taipei
    - local boundary is built in Taipei timezone first
    - UTC range is derived second
    - query shape is [start_utc, end_utc)
    """
    start_local = datetime.combine(business_date, time.min, tzinfo=TZ_TAIPEI)
    end_local = start_local + timedelta(days=1)
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)
    return TaipeiBusinessDateBoundary(
        business_date=business_date,
        timezone_name="Asia/Taipei",
        start_local=start_local,
        end_local=end_local,
        start_utc=start_utc,
        end_utc=end_utc,
    )


def _is_exact_taipei_midnight(dt: datetime) -> bool:
    """Return True when the aware datetime lands exactly on Taipei midnight."""
    local_dt = dt.astimezone(TZ_TAIPEI)
    return (
        local_dt.hour == 0
        and local_dt.minute == 0
        and local_dt.second == 0
        and local_dt.microsecond == 0
    )



def _resolve_reporting_boundary_edge_to_utc(
    dt: Optional[datetime],
) -> Optional[datetime]:
    """Resolve one reporting range edge to canonical UTC.

    Rules:
    - exact Taipei-local midnight edges delegate to the F1 Taipei owner
    - all other aware inputs preserve the existing exact-instant contract
    """
    if dt is None:
        return None

    if _is_exact_taipei_midnight(dt):
        boundary = build_taipei_business_date_boundary(dt.astimezone(TZ_TAIPEI).date())
        return boundary.start_utc

    return _normalize_to_utc(dt)



def resolve_reporting_query_range_to_utc(
    start_date: Optional[datetime],
    end_date: Optional[datetime],
) -> tuple[Optional[datetime], Optional[datetime]]:
    """Resolve reporting query range to canonical UTC boundaries.

    This aligns reporting with the Phase 2 Taipei business-date owner while
    preserving backward compatibility for existing timezone-aware datetime
    callers that provide exact instants instead of Taipei date-boundary edges.
    """
    _validate_datetime_range(start_date, end_date)
    return (
        _resolve_reporting_boundary_edge_to_utc(start_date),
        _resolve_reporting_boundary_edge_to_utc(end_date),
    )



def _validate_datetime_range(
    start_date: Optional[datetime],
    end_date: Optional[datetime],
) -> None:
    """驗證 start_date / end_date 必須為 timezone-aware datetime。
    naive datetime 回傳 422（由三個 reporting endpoint 共用）。
    """
    if start_date is not None and start_date.tzinfo is None:
        raise HTTPException(
            status_code=422,
            detail="start_date must be timezone-aware (naive datetime rejected)"
        )
    if end_date is not None and end_date.tzinfo is None:
        raise HTTPException(
            status_code=422,
            detail="end_date must be timezone-aware (naive datetime rejected)"
        )
