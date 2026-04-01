#!/usr/bin/env python3
"""
S1-09B: Append one more filter test - status on work_date path.
"""

NEW_TEST = '''
    def test_status_filter_on_work_date_path(self, schedule_entitlement):
        """status filter applies on work_date path.

        Two assignments on same work_date with different statuses:
        filtering by status=scheduled returns only the scheduled one.
        """
        actor = create_test_actor(SCHEDULE_COMPANY_A, user_id=TEST_USER_ID, role_id="admin")
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
'''

path = 'app/modules/schedule/tests/test_schedule_assignment_api.py'

with open(path, 'r') as f:
    existing = f.read()
assert len(existing) > 100, f'File too short: {len(existing)} bytes'
print(f'File before append: {existing.count(chr(10))} lines')

# Insert new method inside TestAssignmentListFilter class, before the last closing line
# We append to end of file - the class has no explicit close marker in Python
with open(path, 'a') as f:
    f.write(NEW_TEST)

with open(path, 'r') as f:
    final = f.read()
assert len(final) > len(existing), 'File did not grow'
print(f'File after append: {final.count(chr(10))} lines')
assert 'test_status_filter_on_work_date_path' in final
print('APPEND COMPLETE: test_status_filter_on_work_date_path added')
