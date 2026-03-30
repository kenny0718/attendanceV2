"""Integration tests for Phase 2C-A/C/2D: Break Deduction + AuditLog in punch-out flow.

Pure unit tests using mocks -- no DB, no fixtures.

Note: api/__init__.py has a pre-existing broken import
(get_sessions_reporting does not exist in reporting.py).
This test patches sys.modules before importing punch to work around it.

Verifies:
  1. punch-out with no break punches succeeds, duration_minutes = gross
  2. punch-out with valid break punches succeeds, duration_minutes still gross
  3. anomaly present, AuditLog write succeeds -> warning NOT called
  4. AuditLog write failure -> fallback warning called, punch-out still succeeds
  5. [Phase 2C-C] clamp: was_clamped=True, DB gross, AuditLog meta correct
  6. [Phase 2D] no anomaly -> AuditLog NOT written
  7. [Phase 2D] anomaly -> create_log called with correct fields
  8. [Phase 2D] AuditLog write failure -> fallback warning, punch-out ok
  9. [Phase 2D] clamp anomaly -> AuditLog meta has was_clamped=True
"""

import sys
import types
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from uuid import uuid4
import asyncio


# ---------------------------------------------------------------------------
# Patch broken api/__init__.py import BEFORE importing anything from api
# ---------------------------------------------------------------------------

def _patch_broken_api_init():
    reporting_mod_name = "app.modules.attendance.api.reporting"
    if reporting_mod_name not in sys.modules:
        fake = types.ModuleType(reporting_mod_name)
        fake.get_sessions_reporting = MagicMock()
        sys.modules[reporting_mod_name] = fake
    else:
        existing = sys.modules[reporting_mod_name]
        if not hasattr(existing, "get_sessions_reporting"):
            existing.get_sessions_reporting = MagicMock()


_patch_broken_api_init()

import app.modules.attendance.api.punch as punch_module  # noqa: E402

from app.modules.attendance.work_hour_engine import (  # noqa: E402
    BreakDeductionResult,
    BreakAnomaly,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PUNCH_IN_TIME = datetime(2026, 3, 30, 1, 0, 0, tzinfo=timezone.utc)
PUNCH_OUT_TIME = datetime(2026, 3, 30, 9, 0, 0, tzinfo=timezone.utc)
GROSS_MINUTES = 480  # 8 hours


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_session():
    s = MagicMock()
    s.id = uuid4()
    s.user_id = uuid4()
    s.company_id = "company-test"
    s.punch_in_time = PUNCH_IN_TIME
    s.punch_out_time = None
    s.duration_minutes = None
    s.status = "open"
    s.policy_id = None
    return s


def _make_punch(punch_type, hour, minute=0):
    p = MagicMock()
    p.id = uuid4()
    p.punch_type = punch_type
    p.punch_time = datetime(2026, 3, 30, hour, minute, 0, tzinfo=timezone.utc)
    return p


def _make_actor():
    actor = MagicMock()
    actor.active_company_id = "company-test"
    actor.user_id = uuid4()
    return actor


def _make_closed_session(session):
    closed = MagicMock()
    closed.id = session.id
    closed.user_id = session.user_id
    closed.company_id = session.company_id
    closed.punch_in_time = session.punch_in_time
    closed.punch_out_time = PUNCH_OUT_TIME
    closed.duration_minutes = GROSS_MINUTES
    closed.status = "closed"
    return closed


def _make_policy_evaluation():
    ev = MagicMock()
    ev.is_late = False
    ev.late_minutes = 0
    ev.is_early_leave = False
    ev.early_leave_minutes = 0
    ev.is_overtime = False
    ev.overtime_minutes = 0
    ev.work_minutes = GROSS_MINUTES
    ev.policy_name = None
    return ev


def _default_deduction(anomaly_count=0, anomalies=None, was_clamped=False,
                       break_minutes=0, net_work_minutes=None):
    return BreakDeductionResult(
        gross_minutes=GROSS_MINUTES,
        break_minutes=break_minutes,
        net_work_minutes=net_work_minutes if net_work_minutes is not None else GROSS_MINUTES,
        valid_break_pair_count=0,
        anomaly_count=anomaly_count,
        anomalies=anomalies or [],
        was_clamped=was_clamped,
    )


def _run(
    session_punches,
    deduction_result,
    warn_side_effect=None,
    audit_create_log_side_effect=None,
):
    """
    Execute punch_out with all dependencies mocked.
    Phase 2D: also mocks get_audit_log_repository.
    Returns (close_session_call_args, mock_warn, mock_err, mock_audit_repo).
    """
    session = _make_session()
    actor = _make_actor()
    closed_session = _make_closed_session(session)

    mock_repo = MagicMock()
    mock_repo.get_open_session.return_value = session
    mock_repo.create_punch.return_value = MagicMock()
    mock_repo.get_session_punches.return_value = session_punches
    mock_repo.get_user_policy.return_value = None
    mock_repo.close_session.return_value = closed_session

    mock_policy_engine_instance = MagicMock()
    mock_policy_engine_instance.evaluate.return_value = _make_policy_evaluation()

    mock_audit_repo = MagicMock()
    if audit_create_log_side_effect is not None:
        mock_audit_repo.create_log.side_effect = audit_create_log_side_effect

    request = MagicMock()
    request.notes = None
    request.location = None
    http_request = MagicMock()
    http_request.client = None
    db = MagicMock()

    mock_warn = MagicMock(side_effect=warn_side_effect)
    mock_err = MagicMock()

    with patch.object(
        punch_module, "get_attendance_session_repository", return_value=mock_repo
    ), patch.object(
        punch_module, "get_audit_log_repository", return_value=mock_audit_repo
    ), patch.object(
        punch_module, "AttendancePolicyEngine", return_value=mock_policy_engine_instance
    ), patch.object(
        punch_module, "calculate_break_deduction", return_value=deduction_result
    ), patch.object(
        punch_module, "_require_attendance_feature"
    ), patch.object(
        punch_module, "datetime"
    ) as mock_dt, patch.object(
        punch_module.logger, "warning", mock_warn
    ), patch.object(
        punch_module.logger, "error", mock_err
    ):
        mock_dt.now.return_value = PUNCH_OUT_TIME
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        asyncio.get_event_loop().run_until_complete(
            punch_module.punch_out(
                request=request,
                actor=actor,
                http_request=http_request,
                db=db,
            )
        )

    return mock_repo.close_session.call_args, mock_warn, mock_err, mock_audit_repo


# ---------------------------------------------------------------------------
# Test 1: no break punches
# ---------------------------------------------------------------------------

class TestNoBrakesPunchOut:
    def test_no_break_punches_success_gross_written(self):
        """punch-out with no break punches: succeeds, duration_minutes = gross."""
        close_kwargs, mock_warn, mock_err, mock_audit_repo = _run(
            session_punches=[_make_punch("in", 1), _make_punch("out", 9)],
            deduction_result=_default_deduction(),
        )
        assert close_kwargs.kwargs["duration_minutes"] == GROSS_MINUTES
        mock_warn.assert_not_called()
        mock_err.assert_not_called()
        mock_audit_repo.create_log.assert_not_called()


# ---------------------------------------------------------------------------
# Test 2: valid break punches -- duration_minutes still gross
# ---------------------------------------------------------------------------

class TestValidBreakPunchesPunchOut:
    def test_valid_break_gross_preserved(self):
        """punch-out with valid break pair: duration_minutes written to DB is gross."""
        deduction = BreakDeductionResult(
            gross_minutes=GROSS_MINUTES,
            break_minutes=30,
            net_work_minutes=450,
            valid_break_pair_count=1,
            anomaly_count=0,
            anomalies=[],
            was_clamped=False,
        )
        close_kwargs, mock_warn, mock_err, mock_audit_repo = _run(
            session_punches=[
                _make_punch("in", 1),
                _make_punch("break_start", 4),
                _make_punch("break_end", 4, 30),
                _make_punch("out", 9),
            ],
            deduction_result=deduction,
        )
        assert close_kwargs.kwargs["duration_minutes"] == GROSS_MINUTES
        mock_warn.assert_not_called()
        mock_audit_repo.create_log.assert_not_called()


# ---------------------------------------------------------------------------
# Test 3: anomaly -- AuditLog written, logger.warning NOT called (success path)
# ---------------------------------------------------------------------------

class TestAnomalyLogging:
    def test_anomaly_audit_log_written_no_warning_on_success(self):
        """Phase 2D: anomaly present, AuditLog write succeeds.
        create_log called once; logger.warning NOT called.
        punch-out succeeds, duration_minutes = gross.
        """
        bs = _make_punch("break_start", 4)
        anomaly = BreakAnomaly(
            anomaly_type="unclosed_break_at_close",
            related_punch_ids=[str(bs.id)],
            related_timestamps=[bs.punch_time],
            message="break_start never closed",
        )
        deduction = _default_deduction(anomaly_count=1, anomalies=[anomaly])

        close_kwargs, mock_warn, mock_err, mock_audit_repo = _run(
            session_punches=[_make_punch("in", 1), bs, _make_punch("out", 9)],
            deduction_result=deduction,
        )

        assert close_kwargs.kwargs["duration_minutes"] == GROSS_MINUTES
        mock_audit_repo.create_log.assert_called_once()
        call_kw = mock_audit_repo.create_log.call_args.kwargs
        assert call_kw["action"] == "attendance.break_anomaly"
        assert call_kw["status"] == "success"
        assert call_kw["meta"]["anomaly_count"] == 1
        assert len(call_kw["meta"]["anomalies"]) == 1
        assert call_kw["meta"]["anomalies"][0]["anomaly_type"] == "unclosed_break_at_close"
        mock_warn.assert_not_called()
        mock_err.assert_not_called()


# ---------------------------------------------------------------------------
# Test 4: AuditLog write failure -> fallback warning, punch-out succeeds
# ---------------------------------------------------------------------------

class TestLoggingFailure:
    def test_audit_write_failure_fallback_warning_punch_out_succeeds(self):
        """Phase 2D: AuditLog.create_log raises -> fallback per-anomaly logger.warning.
        punch-out still succeeds; logger.error called for the audit failure.
        """
        bs = _make_punch("break_start", 4)
        anomaly = BreakAnomaly(
            anomaly_type="unclosed_break_at_close",
            related_punch_ids=[],
            related_timestamps=[],
            message="break_start never closed",
        )
        deduction = _default_deduction(anomaly_count=1, anomalies=[anomaly])

        close_kwargs, mock_warn, mock_err, mock_audit_repo = _run(
            session_punches=[_make_punch("in", 1), bs, _make_punch("out", 9)],
            deduction_result=deduction,
            audit_create_log_side_effect=RuntimeError("DB unavailable"),
        )

        assert close_kwargs is not None
        assert close_kwargs.kwargs["duration_minutes"] == GROSS_MINUTES
        mock_audit_repo.create_log.assert_called_once()
        assert mock_err.call_count >= 1
        err_msgs = [str(c.args[0]) for c in mock_err.call_args_list]
        assert any("Failed to write break anomaly audit log" in m for m in err_msgs)
        assert mock_warn.call_count == 1
        fallback_payload = mock_warn.call_args[0][0]
        assert isinstance(fallback_payload, dict)
        assert fallback_payload["event"] == "break_anomaly"
        assert fallback_payload["anomaly_type"] == "unclosed_break_at_close"


# ---------------------------------------------------------------------------
# Test 5: [Phase 2C-C / 2D] clamp path -- was_clamped=True, gross preserved
# ---------------------------------------------------------------------------

class TestClampIntegration:
    def test_clamp_does_not_affect_gross_written(self):
        """Phase 2C-C/2D: when break_minutes >= gross_minutes engine clamps to 0.
        DB receives gross; AuditLog meta has was_clamped=True.
        """
        bs = _make_punch("break_start", 1, 30)
        be = _make_punch("break_end", 9, 0)

        clamp_anomaly = BreakAnomaly(
            anomaly_type="break_exceeds_gross",
            related_punch_ids=[str(bs.id), str(be.id)],
            related_timestamps=[bs.punch_time, be.punch_time],
            message="break_minutes clamped to gross",
        )
        clamped_deduction = BreakDeductionResult(
            gross_minutes=GROSS_MINUTES,
            break_minutes=GROSS_MINUTES,
            net_work_minutes=0,
            valid_break_pair_count=1,
            anomaly_count=1,
            anomalies=[clamp_anomaly],
            was_clamped=True,
        )

        close_kwargs, mock_warn, mock_err, mock_audit_repo = _run(
            session_punches=[
                _make_punch("in", 1), bs, be, _make_punch("out", 9),
            ],
            deduction_result=clamped_deduction,
        )

        assert close_kwargs is not None
        assert close_kwargs.kwargs["duration_minutes"] == GROSS_MINUTES
        assert clamped_deduction.was_clamped is True
        mock_audit_repo.create_log.assert_called_once()
        meta = mock_audit_repo.create_log.call_args.kwargs["meta"]
        assert meta["was_clamped"] is True
        assert meta["net_work_minutes"] == 0
        assert meta["gross_minutes"] == GROSS_MINUTES
        assert meta["anomalies"][0]["was_clamped"] is True
        mock_warn.assert_not_called()
        mock_err.assert_not_called()


# ---------------------------------------------------------------------------
# Test 6: [Phase 2D] no anomaly -> AuditLog NOT written
# ---------------------------------------------------------------------------

class TestNoAnomalyNoAuditLog:
    def test_no_anomaly_no_audit_log_written(self):
        """Phase 2D: anomaly_count == 0 -> create_log must not be invoked."""
        close_kwargs, mock_warn, mock_err, mock_audit_repo = _run(
            session_punches=[_make_punch("in", 1), _make_punch("out", 9)],
            deduction_result=_default_deduction(anomaly_count=0),
        )
        assert close_kwargs.kwargs["duration_minutes"] == GROSS_MINUTES
        mock_audit_repo.create_log.assert_not_called()
        mock_warn.assert_not_called()
        mock_err.assert_not_called()


# ---------------------------------------------------------------------------
# Test 7: [Phase 2D] anomaly -> create_log called with correct fields
# ---------------------------------------------------------------------------

class TestAuditLogFields:
    def test_audit_log_fields_correct(self):
        """Phase 2D: verify AuditLog create_log receives all required fields."""
        bs = _make_punch("break_start", 4)
        anomaly = BreakAnomaly(
            anomaly_type="unclosed_break_at_close",
            related_punch_ids=[str(bs.id)],
            related_timestamps=[bs.punch_time],
            message="break_start never closed",
        )
        deduction = _default_deduction(anomaly_count=1, anomalies=[anomaly])

        close_kwargs, mock_warn, mock_err, mock_audit_repo = _run(
            session_punches=[_make_punch("in", 1), bs, _make_punch("out", 9)],
            deduction_result=deduction,
        )

        mock_audit_repo.create_log.assert_called_once()
        kw = mock_audit_repo.create_log.call_args.kwargs
        assert kw["action"] == "attendance.break_anomaly"
        assert kw["status"] == "success"
        assert isinstance(kw["company_id"], str)
        assert isinstance(kw["actor"], str)

        meta = kw["meta"]
        assert "session_id" in meta
        assert meta["anomaly_count"] == 1
        assert meta["gross_minutes"] == GROSS_MINUTES
        assert "break_minutes" in meta
        assert "net_work_minutes" in meta
        assert "was_clamped" in meta
        assert isinstance(meta["anomalies"], list)
        assert len(meta["anomalies"]) == 1

        entry = meta["anomalies"][0]
        assert entry["event"] == "break_anomaly"
        assert entry["anomaly_type"] == "unclosed_break_at_close"
        assert entry["gross_minutes"] 