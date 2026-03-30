"""Break Anomaly Audit Helper (Phase 2D Decomposition)

Extracted from api/punch.py Phase 2D block.

Responsibility:
- Build anomaly payload list from BreakDeductionResult
- Persist a single AuditLog record per punch-out (action=attendance.break_anomaly)
- Three-tier non-blocking fallback:
    1. AuditLog write success -> logger.info, no per-anomaly warning
    2. AuditLog write failure -> logger.error + fallback per-anomaly logger.warning
    3. Fallback warning failure -> logger.error
- Never raises; never blocks punch-out

Boundary (what this helper CANNOT do):
- Cannot call repo.close_session()
- Cannot write session.duration_minutes
- Cannot run policy evaluation
- Cannot run break deduction calculation
- Cannot shape API response
- Cannot make any business rule decisions about gross/net
"""

import logging
from sqlalchemy.orm import Session

from app.modules.audit.repo import get_audit_log_repository


def write_break_anomaly_audit(
    db: Session,
    session,
    company_id: str,
    deduction_result,
    logger: logging.Logger,
) -> None:
    """Persist break anomalies to audit_logs table (non-blocking side-effect).

    Single AuditLog record per punch-out; meta.anomalies = [...] contains
    one entry per anomaly from deduction_result.

    status='success' means the audit record was written successfully.
    It does NOT mean there are no anomalies -- anomaly_count > 0 is the
    anomaly indicator.

    Args:
        db:               SQLAlchemy Session (passed from punch-out handler)
        session:          Closed AttendanceSession (provides id, user_id)
        company_id:       str -- tenant scope
        deduction_result: BreakDeductionResult (or duck-type _FallbackResult)
        logger:           logging.Logger from caller module

    Returns:
        None (always)

    Raises:
        Never. All exceptions are caught internally.
    """
    if deduction_result.anomaly_count == 0:
        return

    # Build anomaly payload list (same format as Phase 2C-C logger.warning)
    anomaly_payloads = [
        {
            "event": "break_anomaly",
            "session_id": str(session.id),
            "company_id": str(company_id),
            "user_id": str(session.user_id),
            "anomaly_type": a.anomaly_type,
            "gross_minutes": deduction_result.gross_minutes,
            "break_minutes": deduction_result.break_minutes,
            "net_work_minutes": deduction_result.net_work_minutes,
            "was_clamped": deduction_result.was_clamped,
            "anomaly_count": deduction_result.anomaly_count,
            "related_punch_ids": a.related_punch_ids,
            "message": a.message,
            "pairing_strategy": getattr(deduction_result, "pairing_strategy", None),
            "rounding_strategy": getattr(deduction_result, "rounding_strategy", None),
        }
        for a in deduction_result.anomalies
    ]

    _audit_write_ok = False
    try:
        # Primary path: write single AuditLog record via factory
        audit_repo = get_audit_log_repository(db)
        audit_repo.create_log(
            company_id=str(company_id),
            action="attendance.break_anomaly",
            status="success",  # 'success' = audit record written OK
            actor=str(session.user_id),
            meta={
                "session_id": str(session.id),
                "anomaly_count": deduction_result.anomaly_count,
                "gross_minutes": deduction_result.gross_minutes,
                "break_minutes": deduction_result.break_minutes,
                "net_work_minutes": deduction_result.net_work_minutes,
                "was_clamped": deduction_result.was_clamped,
                "pairing_strategy": getattr(deduction_result, "pairing_strategy", None),
                "rounding_strategy": getattr(deduction_result, "rounding_strategy", None),
                "anomalies": anomaly_payloads,
            },
        )
        _audit_write_ok = True
        logger.info(
            "break_anomaly audit record written: session_id=%s anomaly_count=%d",
            str(session.id),
            deduction_result.anomaly_count,
        )
    except Exception:
        logger.error("Failed to write break anomaly audit log", exc_info=True)

    if not _audit_write_ok:
        # Fallback path: AuditLog write failed, revert to per-anomaly logger.warning
        # Preserves non-blocking behaviour from Phase 2C-A/C.
        try:
            for payload in anomaly_payloads:
                logger.warning(payload)
        except Exception:
            logger.error("Failed to log break anomaly (fallback)", exc_info=True)
