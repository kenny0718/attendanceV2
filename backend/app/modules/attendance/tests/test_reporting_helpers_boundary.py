from datetime import date, datetime, timezone

from app.modules.attendance.api.reporting_helpers import (
    TZ_TAIPEI,
    TaipeiBusinessDateBoundary,
    build_taipei_business_date_boundary,
    get_taipei_today,
)


class TestTaipeiBoundaryOwner:
    def test_get_taipei_today_uses_taipei_owner(self):
        now_utc = datetime(2026, 3, 11, 16, 30, 0, tzinfo=timezone.utc)
        assert get_taipei_today(now_utc) == date(2026, 3, 12)

    def test_business_date_builds_canonical_utc_range(self):
        boundary = build_taipei_business_date_boundary(date(2026, 3, 12))
        assert isinstance(boundary, TaipeiBusinessDateBoundary)
        assert boundary.business_date == date(2026, 3, 12)
        assert boundary.timezone_name == "Asia/Taipei"
        assert boundary.start_local == datetime(2026, 3, 12, 0, 0, 0, tzinfo=TZ_TAIPEI)
        assert boundary.end_local == datetime(2026, 3, 13, 0, 0, 0, tzinfo=TZ_TAIPEI)
        assert boundary.start_utc == datetime(2026, 3, 11, 16, 0, 0, tzinfo=timezone.utc)
        assert boundary.end_utc == datetime(2026, 3, 12, 16, 0, 0, tzinfo=timezone.utc)
        assert boundary.start_utc < boundary.end_utc

    def test_cross_month_boundary_is_derived_from_taipei_local_day(self):
        boundary = build_taipei_business_date_boundary(date(2026, 3, 31))
        assert boundary.start_local.date() == date(2026, 3, 31)
        assert boundary.end_local.date() == date(2026, 4, 1)
        assert boundary.start_utc == datetime(2026, 3, 30, 16, 0, 0, tzinfo=timezone.utc)
        assert boundary.end_utc == datetime(2026, 3, 31, 16, 0, 0, tzinfo=timezone.utc)

    def test_helper_is_pure_and_has_no_route_repo_dependency(self):
        boundary = build_taipei_business_date_boundary(date(2026, 4, 1))
        boundary_again = build_taipei_business_date_boundary(date(2026, 4, 1))
        assert boundary == boundary_again
