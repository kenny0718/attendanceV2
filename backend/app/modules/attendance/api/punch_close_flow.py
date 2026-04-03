"""Punch close flow API compatibility shim.

This module re-exports close-flow domain helpers to keep legacy import path stable.
"""

from app.modules.attendance.punch_close_domain import (
    PolicyEvalPayload,
    build_policy_evaluation,
    build_policy_evaluation_with_schedule_v2,
)

__all__ = [
    "PolicyEvalPayload",
    "build_policy_evaluation",
    "build_policy_evaluation_with_schedule_v2",
]
