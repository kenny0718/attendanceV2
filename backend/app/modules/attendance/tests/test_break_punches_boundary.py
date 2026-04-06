from datetime import date, datetime, timezone
from uuid import uuid4

from app.modules.attendance.models import AttendancePunch, AttendanceSession
from app.tests.utils.auth import create_test_actor, override_actor_dependency


class TestBreakPunchesTaipeiBoundary:
    def _create_session(self, test_session, test_user):
        session = AttendanceSession(
            id=uuid4(),
            company_id=test_user.company_id,
            user_id=test_user.id,
            punch_in_time=datetime(2026, 4, 5, 14, 0, tzinfo=timezone.utc),
            status="open",
        )
        test_session.add(session)
        test_session.commit()
        return session

    def _create_break_punch(self, test_session, session, test_user, punch_type, punch_time, notes):
        punch = AttendancePunch(
            id=uuid4(),
            session_id=session.id,
            company_id=test_user.company_id,
            user_id=test_user.id,
            punch_type=punch_type,
            punch_time=punch_time,
            notes=notes,
        )
        test_session.add(punch)
        test_session.commit()
        return punch

    def test_taipei_midnight_boundary_assigns_2350_and_0010_correctly(self, client, test_session, test_user, monkeypatch):
        from app.modules.attendance.api import breaks as breaks_module

        monkeypatch.setattr(breaks_module, "get_taipei_today", lambda: date(2026, 4, 6))

        session = self._create_session(test_session, test_user)
        excluded_2350 = self._create_break_punch(
            test_session,
            session,
            test_user,
            "break_start",
            datetime(2026, 4, 5, 15, 50, tzinfo=timezone.utc),
            "Taipei 2026-04-05 23:50",
        )
        included_0010 = self._create_break_punch(
            test_session,
            session,
            test_user,
            "break_end",
            datetime(2026, 4, 5, 16, 10, tzinfo=timezone.utc),
            "Taipei 2026-04-06 00:10",
        )

        actor = create_test_actor(test_user.company_id, user_id=test_user.id)
        with override_actor_dependency(actor):
            response = client.get("/api/v1/attendance/break-punches?limit=50")

        assert response.status_code == 200
        data = response.json()
        returned_ids = {item["punch_id"] for item in data["punches"]}

        assert str(included_0010.id) in returned_ids
        assert str(excluded_2350.id) not in returned_ids

    def test_cross_day_utc_previous_day_is_included_when_taipei_is_current_day(self, client, test_session, test_user, monkeypatch):
        from app.modules.attendance.api import breaks as breaks_module

        monkeypatch.setattr(breaks_module, "get_taipei_today", lambda: date(2026, 4, 6))

        session = self._create_session(test_session, test_user)
        included_prev_utc_day = self._create_break_punch(
            test_session,
            session,
            test_user,
            "break_start",
            datetime(2026, 4, 5, 16, 5, tzinfo=timezone.utc),
            "UTC 2026-04-05 but Taipei 2026-04-06 00:05",
        )

        actor = create_test_actor(test_user.company_id, user_id=test_user.id)
        with override_actor_dependency(actor):
            response = client.get("/api/v1/attendance/break-punches?limit=50")

        assert response.status_code == 200
        data = response.json()
        returned_ids = {item["punch_id"] for item in data["punches"]}

        assert str(included_prev_utc_day.id) in returned_ids

    def test_query_uses_start_utc_inclusive_and_end_utc_exclusive(self, client, test_session, test_user, monkeypatch):
        from app.modules.attendance.api import breaks as breaks_module

        monkeypatch.setattr(breaks_module, "get_taipei_today", lambda: date(2026, 4, 6))

        session = self._create_session(test_session, test_user)
        included_at_start = self._create_break_punch(
            test_session,
            session,
            test_user,
            "break_start",
            datetime(2026, 4, 5, 16, 0, tzinfo=timezone.utc),
            "Exactly start_utc",
        )
        included_before_end = self._create_break_punch(
            test_session,
            session,
            test_user,
            "break_end",
            datetime(2026, 4, 6, 15, 59, 59, tzinfo=timezone.utc),
            "Just before end_utc",
        )
        excluded_at_end = self._create_break_punch(
            test_session,
            session,
            test_user,
            "break_start",
            datetime(2026, 4, 6, 16, 0, tzinfo=timezone.utc),
            "Exactly end_utc",
        )

        actor = create_test_actor(test_user.company_id, user_id=test_user.id)
        with override_actor_dependency(actor):
            response = client.get("/api/v1/attendance/break-punches?limit=50")

        assert response.status_code == 200
        data = response.json()
        returned_ids = {item["punch_id"] for item in data["punches"]}

        assert str(included_at_start.id) in returned_ids
        assert str(included_before_end.id) in returned_ids
        assert str(excluded_at_end.id) not in returned_ids
