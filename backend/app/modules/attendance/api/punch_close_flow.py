"""Punch Close Flow Helper (Phase 3 — Third Cut, Correct Version)

Builds on second-cut baseline. resolve_break_deduction() is the sole
break deduction entry point and is NOT touched here.

Responsibility:
- Fetch user policy from repo
- Temporarily populate session fields for policy evaluation
- Run AttendancePolicyEngine.evaluate()
- Return structured PolicyEvalPayload for punch.py to finalise the close

Boundary (what this helper CANNOT do):
- Cannot call calculate_break_deduction() directly
- Cannot define _FallbackResult or any fallback class
- Cannot replace resolve_break_deduction()
- Cannot re-filter break punches or re-map DTOs
- Cannot call repo.close_session()
- Cannot write audit logs
- Cannot shape API response
- Cannot make DB commits
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.modules.attendance.policy_engine import AttendancePolicyEngine


@dataclass
class PolicyEvalPayload:
    """Result of build_policy_evaluation().

    policy_id   - UUID of the matched policy, or None
    evaluation  - PolicyEvaluationResult from AttendancePolicyEngine
    """
    policy_id: Optional[UUID]
    evaluation: object


def build_policy_evaluation(
    session,
    repo,
    company_id: str,
    user_id: UUID,
    punch_out_time,
    gross_minutes: int,
) -> PolicyEvalPayload:
    """Fetch policy, temporarily set session fields, and run policy evaluation.

    Inputs:
        session:        Open AttendanceSession (will have punch_out_time /
                        duration_minutes / status set temporarily for evaluate())
        repo:           AttendanceSessionRepository
        company_id:     str tenant scope
        user_id:        UUID of the user
        punch_out_time: datetime of punch-out event
        gross_minutes:  int -- canonical gross duration (already computed by caller)

    Returns:
        PolicyEvalPayload(policy_id, evaluation)

    Note:
        This helper mutates session.punch_out_time, session.duration_minutes,
        and session.status temporarily so that AttendancePolicyEngine can
        evaluate them. The actual DB write is done by repo.close_session()
        in punch.py after this call returns.
    """
    policy = repo.get_user_policy(company_id, user_id)

    # Temporarily set session fields for evaluation
    session.punch_out_time = punch_out_time
    session.duration_minutes = gross_minutes
    session.status = 'closed'

    policy_engine = AttendancePolicyEngine()
    evaluation = policy_engine.evaluate(session, policy)

    return PolicyEvalPayload(
        policy_id=policy.id if policy else None,
        evaluation=evaluation,
    )
