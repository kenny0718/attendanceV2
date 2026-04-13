"""
WP-S1-05: Schedule ShiftAssignment API Integration Tests

Tests:
- Feature gate (enabled / disabled)
- CRUD flow: create / get / list / update / cancel
- Negative cases: double cancel, cross-tenant
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from uuid import uuid4
from datetime import date

from app.main import app
from app.tests.utils.auth import create_test_actor, override_actor_dependency
from app.core.feature_service import FeatureDisabledError
from app.core.features import FeatureKeys
from app.modules.schedule.tests.conftest import (
    SCHEDULE_COMPANY_A,
    SCHEDULE_COMPANY_B,
    TEST_USER_ID,
)

client = TestClient(app)

TEMPLATE_PAYLOAD = {
    "company_id": SCHEDULE_COMPANY_A,
    "code": "ASSIGN_BASE",
    "name": "Assignment Base Shift",
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "break_minutes": 30,
    "is_overnight": False,
    "is_active": True,
}

# A valid-format assignment payload (template_id is a real UUID; will be replaced in CRUD tests)
_DUMMY_TEMPLATE_ID = str(uuid4())
_VALID_ASSIGN_PAYLOAD = {
    "user_id": str(TEST_USER_ID),
    "shift_template_id": _DUMMY_TEMPLATE_ID,
    "work_date": "2026-04-01",
    "company_id": SCHEDULE_COMPANY_A,
}


def _mock_feature_enabled():
    """Patch feature gate to always pass."""
    return patch(
        "app.modules.schedule.api.get_feature_service",
        return_value=type("FS", (), {"require_enabled": lambda self, *a: None})(),
    )


class TestScheduleAssignmentFeatureGate:
    """Feature Gate tests for ShiftAssignment endpoints."""

    def test_list_assignments_feature_disabled(self):
        """schedule.core disabled -> GET /shift-assignments returns 403."""
        actor = create_test_actor(SCHEDULE_COMPANY_A, role_id="company_admin")
        with override_actor_dependency(actor):
            with patch("app.modules.schedule.api.get_feature_service") as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.SCHEDULE_CORE, SCHEDULE_COMPANY_A
                )
                r = client.get("/api/v1/schedule/shift-assignments")
                assert r.status_code == 403
                assert r.json()["detail"]["code"] == "FEATURE_DISABLED"

    def test_create_assignment_feature_disabled(self):
        """schedule.core disabled -> POST /shift-assignments returns 403.

        Uses a structurally-valid payload so Pydantic validation passes
        before the feature gate raises FeatureDisabledError.
        """
        actor = create_test_actor(SCHEDULE_COMPANY_A, role_id="company_admin")
        with override_actor_dependency(actor):
            with patch("app.modules.schedule.api.get_feature_service") as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.SCHEDULE_CORE, SCHEDULE_COMPANY_A
                )
                r = client.post(
                    "/api/v1/schedule/shift-assignments",
                    json=_VALID_ASSIGN_PAYLOAD,
                )
                assert r.status_code == 403
                assert r.json()["detail"]["code"] == "FEATURE_DISABLED"


class TestScheduleAssignmentCRUD:
    """ShiftAssignment CRUD integration tests."""

    def _create_template(self, actor):
        """Helper: create a shift template for assignment tests."""
        code = f"ATPL_{uuid4().hex[:6].upper()}"
        payload = {**TEMPLATE_PAYLOAD, "code": code, "company_id": SCHEDULE_COMPANY_A}
        with override_actor_dependency(actor):
            with _mock_feature_enabled():
                r = client.post("/api/v1/schedule/shift-templates", json=payload)
                assert r.status_code == 201, r.text
                return r.json()["id"]

    def test_full_assignment_crud_flow(self, schedule_entitlement):
        """Full CRUD flow: create -> get -> list -> update -> cancel."""
        actor = create_test_actor(
            SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="company_admin"
        )
        template_id = self._create_template(actor)

        assign_payload = {
            "user_id": str(TEST_USER_ID),
            "shift_template_id": template_id,
            "work_date": "2026-05-01",
            "company_id": SCHEDULE_COMPANY_A,
        }

        with override_actor_dependency(actor):
            with _mock_feature_enabled():
                # 1. Create
                r = client.post("/api/v1/schedule/shift-assignments", json=assign_payload)
                assert r.status_code == 201, r.text
                asgn = r.json()
                assert asgn["work_date"] == "2026-05-01"
                assert asgn["status"] in ("active", "scheduled")
                aid = asgn["id"]

                # 2. Get by id
                r = client.get(f"/api/v1/schedule/shift-assignments/{aid}")
                assert r.status_code == 200
                assert r.json()["id"] == aid

                # 3. List
                r = client.get("/api/v1/schedule/shift-assignments")
                assert r.status_code == 200
                ids = [a["id"] for a in r.json()]
                assert aid in ids

                # 4. Update (note)
                r = client.patch(
                    f"/api/v1/schedule/shift-assignments/{aid}",
                    json={"notes": "Updated note"},
                )
                assert r.status_code == 200

                # 5. Cancel
                r = client.post(f"/api/v1/schedule/shift-assignments/{aid}/cancel")
                assert r.status_code == 200
                assert r.json()["status"] == "cancelled"

    def test_double_cancel_returns_409(self, schedule_entitlement):
        """Cancelling an already-cancelled assignment -> 409."""
        actor = create_test_actor(
            SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="company_admin"
        )
        template_id = self._create_template(actor)

        assign_payload = {
            "user_id": str(TEST_USER_ID),
            "shift_template_id": template_id,
            "work_date": "2026-05-02",
            "company_id": SCHEDULE_COMPANY_A,
        }

        with override_actor_dependency(actor):
            with _mock_feature_enabled():
                r = client.post("/api/v1/schedule/shift-assignments", json=assign_payload)
                assert r.status_code == 201
                aid = r.json()["id"]

                # First cancel
                r = client.post(f"/api/v1/schedule/shift-assignments/{aid}/cancel")
                assert r.status_code == 200

                # Double cancel -> 409
                r = client.post(f"/api/v1/schedule/shift-assignments/{aid}/cancel")
                assert r.status_code == 409

    def test_get_nonexistent_assignment_returns_404(self, schedule_entitlement):
        """Getting non-existent assignment -> 404."""
        actor = create_test_actor(
            SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="company_admin"
        )
        with override_actor_dependency(actor):
            with _mock_feature_enabled():
                r = client.get(f"/api/v1/schedule/shift-assignments/{uuid4()}")
                assert r.status_code == 404

    def test_cross_tenant_assignment_isolation(self, schedule_entitlement):
        """Company B cannot access Company A assignment."""
        actor_a = create_test_actor(
            SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="company_admin"
        )
        actor_b_obj = create_test_actor(
            SCHEDULE_COMPANY_B, user_id=TEST_USER_ID, role_id="company_admin"
        )
        template_id = self._create_template(actor_a)

        assign_payload = {
            "user_id": str(TEST_USER_ID),
            "shift_template_id": template_id,
            "work_date": "2026-05-03",
            "company_id": SCHEDULE_COMPANY_A,
        }

        with _mock_feature_enabled():
            with override_actor_dependency(actor_a):
                r = client.post("/api/v1/schedule/shift-assignments", json=assign_payload)
                assert r.status_code == 201
                aid = r.json()["id"]

            # Company B cannot access Company A's assignment
            with override_actor_dependency(actor_b_obj):
                r = client.get(f"/api/v1/schedule/shift-assignments/{aid}")
                assert r.status_code in (404, 422)


class TestAssignmentListFilter:
    """S1-09B: Assignment list filter enhancement tests.

    Covers:
    - template_id filter (general list path)
    - status filter (general list path)
    - invalid status -> 422
    - work_date path: new filters apply
    - user_id + date range path: new filters apply
    - general list path: new filters apply
    - company isolation not broken
    """

    def _create_template(self, actor, code=None):
        """Helper: create a shift template under SCHEDULE_COMPANY_A."""
        code = code or f"FLT_{uuid4().hex[:6].upper()}"
        payload = {
            **TEMPLATE_PAYLOAD,
            "code": code,
            "company_id": SCHEDULE_COMPANY_A,
        }
        with override_actor_dependency(actor):
            with _mock_feature_enabled():
                r = client.post("/api/v1/schedule/shift-templates", json=payload)
                assert r.status_code == 201, r.text
                return r.json()["id"]

    def _create_assignment(self, actor, template_id, work_date, asg_status="scheduled"):
        """Helper: create an assignment and return its id."""
        payload = {
            "user_id": str(TEST_USER_ID),
            "shift_template_id": template_id,
            "work_date": work_date,
            "company_id": SCHEDULE_COMPANY_A,
            "status": asg_status,
        }
        with override_actor_dependency(actor):
            with _mock_feature_enabled():
                r = client.post("/api/v1/schedule/shift-assignments", json=payload)
                assert r.status_code == 201, r.text
                return r.json()["id"]

    def test_template_id_filter_general_list(self, schedule_entitlement):
        """template_id filter on general list path returns only matching assignments."""
        actor = create_test_actor(SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="company_admin")
        tid_a = self._create_template(actor, code=f"FLTA_{uuid4().hex[:4].upper()}")
        tid_b = self._create_template(actor, code=f"FLTB_{uuid4().hex[:4].upper()}")

        aid_a = self._create_assignment(actor, tid_a, "2026-07-01")
        aid_b = self._create_assignment(actor, tid_b, "2026-07-02")

        with override_actor_dependency(actor):
            with _mock_feature_enabled():
                r = client.get(
                    "/api/v1/schedule/shift-assignments",
                    params={"template_id": tid_a},
                )
                assert r.status_code == 200
                ids = [a["id"] for a in r.json()]
                assert aid_a in ids
                assert aid_b not in ids

    def test_status_filter_scheduled(self, schedule_entitlement):
        """status=scheduled filter returns only scheduled assignments."""
        actor = create_test_actor(SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="company_admin")
        tid = self._create_template(actor, code=f"FLTS_{uuid4().hex[:4].upper()}")

        aid_sched = self._create_assignment(actor, tid, "2026-07-10")
        aid_will_cancel = self._create_assignment(actor, tid, "2026-07-11")

        # Cancel one
        with override_actor_dependency(actor):
            with _mock_feature_enabled():
                client.post(f"/api/v1/schedule/shift-assignments/{aid_will_cancel}/cancel")

        with override_actor_dependency(actor):
            with _mock_feature_enabled():
                r = client.get(
                    "/api/v1/schedule/shift-assignments",
                    params={"status": "scheduled"},
                )
                assert r.status_code == 200
                ids = [a["id"] for a in r.json()]
                assert aid_sched in ids
                assert aid_will_cancel not in ids

    def test_status_filter_cancelled(self, schedule_entitlement):
        """status=cancelled filter returns only cancelled assignments."""
        actor = create_test_actor(SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="company_admin")
        tid = self._create_template(actor, code=f"FLTC_{uuid4().hex[:4].upper()}")

        aid_sched = self._create_assignment(actor, tid, "2026-07-20")
        aid_cancel = self._create_assignment(actor, tid, "2026-07-21")

        with override_actor_dependency(actor):
            with _mock_feature_enabled():
                client.post(f"/api/v1/schedule/shift-assignments/{aid_cancel}/cancel")

        with override_actor_dependency(actor):
            with _mock_feature_enabled():
                r = client.get(
                    "/api/v1/schedule/shift-assignments",
                    params={"status": "cancelled"},
                )
                assert r.status_code == 200
                ids = [a["id"] for a in r.json()]
                assert aid_cancel in ids
                assert aid_sched not in ids

    def test_invalid_status_returns_422(self, schedule_entitlement):
        """Invalid status value -> 422 from FastAPI enum validation."""
        actor = create_test_actor(SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="company_admin")
        with override_actor_dependency(actor):
            with _mock_feature_enabled():
                r = client.get(
                    "/api/v1/schedule/shift-assignments",
                    params={"status": "invalid_xyz"},
                )
                assert r.status_code == 422

    def test_filter_on_work_date_path(self, schedule_entitlement):
        """template_id filter applies on work_date path (work_date precedence maintained)."""
        actor = create_test_actor(SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="company_admin")
        tid_a = self._create_template(actor, code=f"WDPA_{uuid4().hex[:4].upper()}")
        tid_b = self._create_template(actor, code=f"WDPB_{uuid4().hex[:4].upper()}")

        aid_a = self._create_assignment(actor, tid_a, "2026-08-01")
        aid_b = self._create_assignment(actor, tid_b, "2026-08-01")

        with override_actor_dependency(actor):
            with _mock_feature_enabled():
                r = client.get(
                    "/api/v1/schedule/shift-assignments",
                    params={"work_date": "2026-08-01", "template_id": tid_a},
                )
                assert r.status_code == 200
                ids = [a["id"] for a in r.json()]
                assert aid_a in ids
                assert aid_b not in ids

    def test_filter_on_user_date_range_path(self, schedule_entitlement):
        """template_id filter applies on user_id + date range path."""
        actor = create_test_actor(SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="company_admin")
        tid_a = self._create_template(actor, code=f"UDRA_{uuid4().hex[:4].upper()}")
        tid_b = self._create_template(actor, code=f"UDRB_{uuid4().hex[:4].upper()}")

        aid_a = self._create_assignment(actor, tid_a, "2026-09-01")
        aid_b = self._create_assignment(actor, tid_b, "2026-09-02")

        with override_actor_dependency(actor):
            with _mock_feature_enabled():
                r = client.get(
                    "/api/v1/schedule/shift-assignments",
                    params={
                        "user_id": str(TEST_USER_ID),
                        "start_date": "2026-09-01",
                        "end_date": "2026-09-30",
                        "template_id": tid_a,
                    },
                )
                assert r.status_code == 200
                ids = [a["id"] for a in r.json()]
                assert aid_a in ids
                assert aid_b not in ids

    def test_company_isolation_not_broken_by_filter(self, schedule_entitlement):
        """Filter params do not break company isolation.

        Company B cannot see Company A assignments even with valid template_id filter.
        """
        actor_a = create_test_actor(SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="company_admin")
        actor_b = create_test_actor(SCHEDULE_COMPANY_B, user_id=TEST_USER_ID, role_id="company_admin")

        tid = self._create_template(actor_a, code=f"ISOL_{uuid4().hex[:4].upper()}")
        aid = self._create_assignment(actor_a, tid, "2026-10-01")

        with override_actor_dependency(actor_b):
            with _mock_feature_enabled():
                # Company B listing with Company A template_id should return empty
                r = client.get(
                    "/api/v1/schedule/shift-assignments",
                    params={"template_id": tid},
                )
                assert r.status_code == 200
                ids = [a["id"] for a in r.json()]
                assert aid not in ids

    def test_status_filter_on_work_date_path(self, schedule_entitlement):
        """status filter applies on work_date path.

        Two assignments on same work_date with different statuses:
        filtering by status=scheduled returns only the scheduled one.
        """
        actor = create_test_actor(SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="company_admin")
        tid = self._create_template(actor, code=f"WDST_{uuid4().hex[:4].upper()}")

        aid_sched = self._create_assignment(actor, tid, "2026-08-15")
        aid_cancel = self._create_assignment(actor, tid, "2026-08-15")

        # Cancel one
        with override_actor_dependency(actor):
            with _mock_feature_enabled():
                client.post(f"/api/v1/schedule/shift-assignments/{aid_cancel}/cancel")

        with override_actor_dependency(actor):
            with _mock_feature_enabled():
                # work_date path + status=scheduled
                r = client.get(
                    "/api/v1/schedule/shift-assignments",
                    params={"work_date": "2026-08-15", "status": "scheduled"},
                )
                assert r.status_code == 200
                ids = [a["id"] for a in r.json()]
                assert aid_sched in ids
                assert aid_cancel not in ids

                # work_date path + status=cancelled
                r = client.get(
                    "/api/v1/schedule/shift-assignments",
                    params={"work_date": "2026-08-15", "status": "cancelled"},
                )
                assert r.status_code == 200
                ids = [a["id"] for a in r.json()]
                assert aid_cancel in ids
                assert aid_sched not in ids
