"""
WP-S1-05: Schedule ShiftTemplate API Integration Tests

Tests:
- Feature gate (enabled / disabled)
- CRUD flow: create / get / list / update / activate / deactivate
- Negative cases: duplicate code, not found, cross-tenant
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from uuid import uuid4
from datetime import time as t

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

TEMPLATE_BASE = {
    "company_id": SCHEDULE_COMPANY_A,
    "code": "IT_DAY",
    "name": "Integration Day Shift",
    "start_time": "09:00:00",
    "end_time": "18:00:00",
    "break_minutes": 60,
    "is_overnight": False,
    "is_active": True,
}


class TestScheduleTemplateFeatureGate:
    """Feature Gate tests for ShiftTemplate endpoints."""

    def test_list_templates_feature_disabled(self):
        """schedule.core disabled -> GET /shift-templates returns 403"""
        actor = create_test_actor(SCHEDULE_COMPANY_A, role_id="admin")
        with override_actor_dependency(actor):
            with patch("app.modules.schedule.api.get_feature_service") as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.SCHEDULE_CORE, SCHEDULE_COMPANY_A
                )
                r = client.get("/api/v1/schedule/shift-templates")
                assert r.status_code == 403
                assert r.json()["detail"]["code"] == "FEATURE_DISABLED"
                assert r.json()["detail"]["feature"] == FeatureKeys.SCHEDULE_CORE

    def test_create_template_feature_disabled(self):
        """schedule.core disabled -> POST /shift-templates returns 403"""
        actor = create_test_actor(SCHEDULE_COMPANY_A, role_id="admin")
        with override_actor_dependency(actor):
            with patch("app.modules.schedule.api.get_feature_service") as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.SCHEDULE_CORE, SCHEDULE_COMPANY_A
                )
                r = client.post("/api/v1/schedule/shift-templates", json=TEMPLATE_BASE)
                assert r.status_code == 403
                assert r.json()["detail"]["code"] == "FEATURE_DISABLED"


class TestScheduleTemplateCRUD:
    """ShiftTemplate CRUD integration tests with feature gate enabled."""

    def _mock_feature_enabled(self):
        """Helper: patch feature gate to always pass."""
        return patch(
            "app.modules.schedule.api.get_feature_service",
            return_value=type("FS", (), {"require_enabled": lambda self, *a: None})(),
        )

    def test_full_template_crud_flow(self, schedule_entitlement):
        """Full CRUD flow: create -> get -> list -> update -> deactivate -> activate."""
        actor = create_test_actor(SCHEDULE_COMPANY_A, role_id="admin")
        code = f"CRUD_{uuid4().hex[:6].upper()}"
        payload = {**TEMPLATE_BASE, "code": code, "company_id": SCHEDULE_COMPANY_A}

        with override_actor_dependency(actor):
            with self._mock_feature_enabled():
                # 1. Create
                r = client.post("/api/v1/schedule/shift-templates", json=payload)
                assert r.status_code == 201, r.text
                tmpl = r.json()
                assert tmpl["code"] == code
                assert tmpl["company_id"] == SCHEDULE_COMPANY_A
                tid = tmpl["id"]

                # 2. Get by id
                r = client.get(f"/api/v1/schedule/shift-templates/{tid}")
                assert r.status_code == 200
                assert r.json()["id"] == tid

                # 3. List
                r = client.get("/api/v1/schedule/shift-templates")
                assert r.status_code == 200
                ids = [t["id"] for t in r.json()]
                assert tid in ids

                # 4. Update
                r = client.patch(
                    f"/api/v1/schedule/shift-templates/{tid}",
                    json={"name": "Updated Name"},
                )
                assert r.status_code == 200
                assert r.json()["name"] == "Updated Name"

                # 5. Deactivate
                r = client.post(f"/api/v1/schedule/shift-templates/{tid}/deactivate")
                assert r.status_code == 200
                assert r.json()["is_active"] is False

                # 6. Activate
                r = client.post(f"/api/v1/schedule/shift-templates/{tid}/activate")
                assert r.status_code == 200
                assert r.json()["is_active"] is True

    def test_duplicate_code_returns_409(self, schedule_entitlement):
        """Creating template with duplicate code -> 409 Conflict."""
        actor = create_test_actor(SCHEDULE_COMPANY_A, role_id="admin")
        code = f"DUP_{uuid4().hex[:6].upper()}"
        payload = {**TEMPLATE_BASE, "code": code, "company_id": SCHEDULE_COMPANY_A}

        with override_actor_dependency(actor):
            with self._mock_feature_enabled():
                r = client.post("/api/v1/schedule/shift-templates", json=payload)
                assert r.status_code == 201

                # Second create with same code
                r = client.post("/api/v1/schedule/shift-templates", json=payload)
                assert r.status_code == 409

    def test_get_nonexistent_returns_404(self, schedule_entitlement):
        """Getting non-existent template -> 404."""
        actor = create_test_actor(SCHEDULE_COMPANY_A, role_id="admin")
        fake_id = str(uuid4())

        with override_actor_dependency(actor):
            with self._mock_feature_enabled():
                r = client.get(f"/api/v1/schedule/shift-templates/{fake_id}")
                assert r.status_code == 404

    def test_cross_tenant_isolation(self, schedule_entitlement):
        """Company B cannot see Company A templates."""
        actor_a = create_test_actor(SCHEDULE_COMPANY_A, role_id="admin")
        actor_b_obj = create_test_actor(SCHEDULE_COMPANY_B, role_id="admin")
        code = f"ISO_{uuid4().hex[:6].upper()}"
        payload = {**TEMPLATE_BASE, "code": code, "company_id": SCHEDULE_COMPANY_A}

        with self._mock_feature_enabled():
            # Create as Company A
            with override_actor_dependency(actor_a):
                r = client.post("/api/v1/schedule/shift-templates", json=payload)
                assert r.status_code == 201
                tid = r.json()["id"]

            # Company B cannot access Company A's template
            with override_actor_dependency(actor_b_obj):
                r = client.get(f"/api/v1/schedule/shift-templates/{tid}")
                assert r.status_code == 404
