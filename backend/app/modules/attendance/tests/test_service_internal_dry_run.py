from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.modules.attendance.api.punch_close_flow import PolicyEvalPayload
from app.modules.attendance.policy_missing_segment import MissingSegmentResult
from app.modules.attendance.service import AttendanceService


def _make_service() -> AttendanceService:
    return AttendanceService(db=MagicMock())


def _make_session() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        company_id="company-test",
        user_id=uuid4(),
        punch_in_time=datetime(2026, 4, 3, 1, 0, 0, tzinfo=timezone.utc),
        punch_out_time=None,
        duration_minutes=None,
        status="open",
    )


def _make_eval() -> SimpleNamespace:
    return SimpleNamespace(
        is_late=False,
        late_minutes=0,
        is_early_leave=False,
        early_leave_minutes=0,
        is_overtime=False,
        overtime_minutes=0,
        work_minutes=480,
        policy_name="Standard Policy",
    )


def _make_punch(punch_type: str, dt: datetime) -> SimpleNamespace:
    return SimpleNamespace(punch_type=punch_type, punch_time=dt)


def test_service_calls_missing_segment_dry_run(monkeypatch):
    service = _make_service()
    session = _make_session()
    repo = MagicMock()
    repo.get_punches_by_company_user_and_session_ids.return_value = [
        _make_punch("in", datetime(2026, 4, 3, 1, 0, 0, tzinfo=timezone.utc)),
        _make_punch("out", datetime(2026, 4, 3, 9, 0, 0, tzinfo=timezone.utc)),
    ]

    dry_run_called = {"count": 0}

    def _fake_dry_run(data):
        dry_run_called["count"] += 1
        return MissingSegmentResult(
            is_decidable=True,
            missing_segment=False,
            reason="fully_covered",
        )

    monkeypatch.setattr(
        "app.modules.attendance.service.evaluate_missing_segment_dry_run",
        _fake_dry_run,
    )
    monkeypatch.setattr(
        "app.modules.attendance.service.build_policy_evaluation",
        lambda **kwargs: PolicyEvalPayload(policy_id=None, evaluation=_make_eval()),
    )

    service.build_punch_out_policy_evaluation(
        session=session,
        repo=repo,
        company_id="company-test",
        user_id=session.user_id,
        punch_out_time=datetime(2026, 4, 3, 9, 0, 0, tzinfo=timezone.utc),
        gross_minutes=480,
    )

    assert dry_run_called["count"] == 1


def test_service_builds_input_from_punches_and_marks_evidence_sufficient(monkeypatch):
    service = _make_service()
    session = _make_session()
    repo = MagicMock()
    repo.get_punches_by_company_user_and_session_ids.return_value = [
        _make_punch("in", datetime(2026, 4, 3, 1, 0, 0, tzinfo=timezone.utc)),
        _make_punch("break_start", datetime(2026, 4, 3, 4, 0, 0, tzinfo=timezone.utc)),
        _make_punch("break_end", datetime(2026, 4, 3, 4, 30, 0, tzinfo=timezone.utc)),
        _make_punch("out", datetime(2026, 4, 3, 9, 0, 0, tzinfo=timezone.utc)),
    ]

    captured = {}

    def _capture_input(data):
        captured["input"] = data
        return MissingSegmentResult(
            is_decidable=True,
            missing_segment=False,
            reason="fully_covered",
        )

    monkeypatch.setattr(
        "app.modules.attendance.service.evaluate_missing_segment_dry_run",
        _capture_input,
    )
    monkeypatch.setattr(
        "app.modules.attendance.service.build_policy_evaluation",
        lambda **kwargs: PolicyEvalPayload(policy_id=None, evaluation=_make_eval()),
    )

    service.build_punch_out_policy_evaluation(
        session=session,
        repo=repo,
        company_id="company-test",
        user_id=session.user_id,
        punch_out_time=datetime(2026, 4, 3, 9, 0, 0, tzinfo=timezone.utc),
        gross_minutes=480,
    )

    data = captured["input"]
    assert len(data.expected_segments) == 1
    assert len(data.actual_segments) == 2
    assert data.evidence_sufficient is True
    assert data.exception_segments == []


def test_service_internal_channel_contains_dry_run_result(monkeypatch):
    service = _make_service()
    session = _make_session()
    repo = MagicMock()
    repo.get_punches_by_company_user_and_session_ids.return_value = [
        _make_punch("in", datetime(2026, 4, 3, 1, 0, 0, tzinfo=timezone.utc)),
        _make_punch("out", datetime(2026, 4, 3, 9, 0, 0, tzinfo=timezone.utc)),
    ]

    expected_result = MissingSegmentResult(
        is_decidable=True,
        missing_segment=False,
        reason="fully_covered",
    )

    monkeypatch.setattr(
        "app.modules.attendance.service.evaluate_missing_segment_dry_run",
        lambda data: expected_result,
    )
    monkeypatch.setattr(
        "app.modules.attendance.service.build_policy_evaluation",
        lambda **kwargs: PolicyEvalPayload(policy_id=None, evaluation=_make_eval()),
    )

    payload = service.build_punch_out_policy_evaluation(
        session=session,
        repo=repo,
        company_id="company-test",
        user_id=session.user_id,
        punch_out_time=datetime(2026, 4, 3, 9, 0, 0, tzinfo=timezone.utc),
        gross_minutes=480,
    )

    assert service._last_internal_missing_segment_dry_run is not None
    assert service._last_internal_missing_segment_dry_run["result"] == expected_result
    assert service._last_internal_missing_segment_dry_run["source"]["exception_segments_count"] == 0
    assert hasattr(payload, "_internal_missing_segment_dry_run")
    assert payload._internal_missing_segment_dry_run["result"] == expected_result


def test_evidence_insufficient_when_actual_segments_empty(monkeypatch):
    service = _make_service()
    session = _make_session()
    repo = MagicMock()
    repo.get_punches_by_company_user_and_session_ids.return_value = []

    captured = {}

    def _capture_input(data):
        captured["input"] = data
        return MissingSegmentResult(
            is_decidable=False,
            missing_segment=False,
            reason="insufficient_evidence",
        )

    monkeypatch.setattr(
        "app.modules.attendance.service.evaluate_missing_segment_dry_run",
        _capture_input,
    )
    monkeypatch.setattr(
        "app.modules.attendance.service.build_policy_evaluation",
        lambda **kwargs: PolicyEvalPayload(policy_id=None, evaluation=_make_eval()),
    )

    service.build_punch_out_policy_evaluation(
        session=session,
        repo=repo,
        company_id="company-test",
        user_id=session.user_id,
        punch_out_time=datetime(2026, 4, 3, 9, 0, 0, tzinfo=timezone.utc),
        gross_minutes=480,
    )

    assert captured["input"].evidence_sufficient is False


def test_missing_segment_true_does_not_change_primary_policy_eval_output(monkeypatch):
    service = _make_service()
    session = _make_session()
    repo = MagicMock()
    repo.get_punches_by_company_user_and_session_ids.return_value = [
        _make_punch("in", datetime(2026, 4, 3, 1, 0, 0, tzinfo=timezone.utc)),
        _make_punch("out", datetime(2026, 4, 3, 9, 0, 0, tzinfo=timezone.utc)),
    ]

    original_eval = _make_eval()
    original_payload = PolicyEvalPayload(policy_id=uuid4(), evaluation=original_eval)

    monkeypatch.setattr(
        "app.modules.attendance.service.evaluate_missing_segment_dry_run",
        lambda data: MissingSegmentResult(
            is_decidable=True,
            missing_segment=True,
            reason="uncovered_expected_segment",
        ),
    )
    monkeypatch.setattr(
        "app.modules.attendance.service.build_policy_evaluation",
        lambda **kwargs: original_payload,
    )

    payload = service.build_punch_out_policy_evaluation(
        session=session,
        repo=repo,
        company_id="company-test",
        user_id=session.user_id,
        punch_out_time=datetime(2026, 4, 3, 9, 0, 0, tzinfo=timezone.utc),
        gross_minutes=480,
    )

    assert payload is original_payload
    assert payload.evaluation is original_eval
    assert payload.evaluation.is_late is False
    assert payload.evaluation.early_leave_minutes == 0
    assert payload.evaluation.overtime_minutes == 0
