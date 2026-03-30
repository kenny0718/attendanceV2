"""Integration tests for Phase 2C-A: Break Deduction in punch-out flow.

Pure unit tests using mocks -- no DB, no fixtures.

Note: api/__init__.py has a pre-existing broken import
(get_sessions_reporting does not exist in reporting.py).
This test patches sys.modules before importing punch to work around it.

Verifies:
  1. punch-out with no break punches succeeds, duration_minutes = gross
  2. punch-out with valid break punches succeeds, duration_minutes still gross
  3. punch-out with anomaly (unclosed break) succeeds, logger.warning called
  4. logging failure does not block punch-out, logger.error called
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
    """Inject a fake get_sessions_reporting into sys.modules so that
    api/__init__.py's broken import does not raise ImportError.
    """
    reporting_mod_name = "app.modules.attendance.api.reporting"
    # Only patch if module is not yet loaded or lacks the symbol
    if reporting_mod_name not in sys.modules:
        fake = types.ModuleType(reporting_mod_name)
        fake.get_sessions_reporting = MagicMock()
        sys.modules[reporting_mod_name] = fake
    else:
        existing = sys.modules[reporting_mod_name]
        if not hasattr(existing, "get_sessions_reporting"):
            existing.get_sessions_reporting = MagicMock()


_patch_broken_api_init()

# Now it is safe to import punch_module
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


def _default_deduction(anomaly_count=0, anomalies=None):
    return BreakDeductionResult(
        gross_minutes=GROSS_MINUTES,
        break_minutes=0,
        net_work_minutes=GROSS_MINUTES,
        valid_break_pair_count=0,
        anomaly_count=anomaly_count,
        anomalies=anomalies or [],
        was_clamped=False,
    )


def _run(session_punches, deduction_result, warn_side_effect=None):
    """
    Execute punch_out with all dependencies mocked.
    Returns (close_session_call_args, mock_warn, mock_err).
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

    return mock_repo.close_session.call_args, mock_warn, mock_err


# ---------------------------------------------------------------------------
# Test 1: no break punches
# ---------------------------------------------------------------------------

class TestNoBrakesPunchOut:
    def test_no_break_punches_success_gross_written(self):
        """punch-out with no break punches: succeeds, duration_minutes = gross."""
        close_kwargs, mock_warn, mock_err = _run(
            session_punches=[_make_punch("in", 1), _make_punch("out", 9)],
            deduction_result=_default_deduction(),
        )
        assert close_kwargs.kwargs["duration_minutes"] == GROSS_MINUTES
        mock_warn.assert_not_called()
        mock_err.assert_not_called()


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
        close_kwargs, mock_warn, mock_err = _run(
            session_punches=[
                _make_punch("in", 1),
                _make_punch("break_start", 4),
                _make_punch("break_end", 4, 30),
                _make_punch("out", 9),
            ],
            deduction_result=deduction,
        )
        # DB must receive gross (480), NOT net (450)
        assert close_kwargs.kwargs["duration_minutes"] == GROSS_MINUTES
        mock_warn.assert_not_called()


# ---------------------------------------------------------------------------
# Test 3: anomaly -- punch-out succeeds, logger.warning called
# ---------------------------------------------------------------------------

class TestAnomalyLogging:
    def test_anomaly_warning_logged_and_punch_out_succeeds(self):
        """unclosed_break_at_close anomaly: punch-out succeeds, warning logged."""
        bs = _make_punch("break_start", 4)
        anomaly = BreakAnomaly(
            anomaly_type="unclosed_break_at_close",
            related_punch_ids=[str(bs.id)],
            related_timestamps=[bs.punch_time],
            message="break_start never closed",
        )
        deduction = _default_deduction(anomaly_count=1, anomalies=[anomaly])

        close_kwargs, mock_warn, mock_err = _run(
            session_punches=[_make_punch("in", 1), bs, _make_punch("out", 9)],
            deduction_result=deduction,
        )

        assert close_kwargs.kwargs["duration_minutes"] == GROSS_MINUTES
        assert mock_warn.call_count == 1
        logged_msg = mock_warn.call_args[0][0]
        assert "unclosed_break_at_close" in logged_msg
        assert "break_anomaly" in logged_msg
        mock_err.assert_not_called()


# ---------------------------------------------------------------------------
# Test 4: logging failure does not block punch-out
# ---------------------------------------------------------------------------

class TestLoggingFailure:
    def test_logging_failure_does_not_block(self):
        """If logger.warning raises, punch-out still succeeds; logger.error called."""
        bs = _make_punch("break_start", 4)
        anomaly = BreakAnomaly(
            anomaly_type="unclosed_break_at_close",
            related_punch_ids=[],
            related_timestamps=[],
            message="break_start never closed",
        )
        deduction = _default_deduction(anomaly_count=1, anomalies=[anomaly])

        close_kwargs, mock_warn, mock_err = _run(
            session_punches=[_make_punch("in", 1), bs, _make_punch("out", 9)],
            deduction_result=deduction,
            warn_side_effect=RuntimeError("log infra down"),
        )

        assert close_kwargs is not None
        assert close_kwargs.kwargs["duration_minutes"] == GROSS_MINUTES
        mock_err.assert_called_once()
        err_msg = mock_err.call_args[0][0]
        assert "Failed to log break anomaly" in err_msg
