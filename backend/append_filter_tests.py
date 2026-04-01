#!/usr/bin/env python3
"""
S1-09B: Append assignment list filter tests to test_schedule_assignment_api.py
Using append mode - no StrReplace, no full rewrite.
"""

NEW_TEST_CLASS = '''

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
        actor = create_test_actor(SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="admin")
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
        actor = create_test_actor(SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="admin")
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
        actor = create_test_actor(SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="admin")
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
        actor = create_test_actor(SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="admin")
        with override_actor_dependency(actor):
            with _mock_feature_enabled():
                r = client.get(
                    "/api/v1/schedule/shift-assignments",
                    params={"status": "invalid_xyz"},
                )
                assert r.status_code == 422

    def test_filter_on_work_date_path(self, schedule_entitlement):
        """template_id filter applies on work_date path (work_date precedence maintained)."""
        actor = create_test_actor(SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="admin")
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
        actor = create_test_actor(SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="admin")
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
        actor_a = create_test_actor(SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="admin")
        actor_b = create_test_actor(SCHEDULE_COMPANY_B, user_id=TEST_USER_ID, role_id="admin")

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
'''

path = 'app/modules/schedule/tests/test_schedule_assignment_api.py'

# Verify file is not empty before appending
with open(path, 'r') as f:
    existing = f.read()
assert len(existing) > 100, f'File too short before append: {len(existing)} bytes'
print(f'File before append: {existing.count(chr(10))} lines')

# Append new test class
with open(path, 'a') as f:
    f.write(NEW_TEST_CLASS)

# Verify after append
with open(path, 'r') as f:
    final = f.read()
assert len(final) > len(existing), 'File did not grow after append'
print(f'File after append: {final.count(chr(10))} lines')
print('APPEND COMPLETE')
