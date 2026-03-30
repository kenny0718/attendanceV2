"""Reporting API — Shared helper utilities

Extracted from reporting.py (Micro Decomposition Step 2).
Contains only pure utility functions:
- no DB access
- no repo calls
- no actor/permission logic
- no response shaping
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException


def _normalize_to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """將 timezone-aware datetime 轉換為 UTC。
    naive datetime（無 tzinfo）呼叫方不應傳入，應由 validator 在 API 層攔截。
    """
    if dt is None:
        return None
    return dt.astimezone(timezone.utc)


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
