"""WP-C1-06: Feature Gate 測試 - leave module"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.tests.utils.auth import create_test_actor, override_actor_dependency
from app.core.feature_service import FeatureDisabledError
from app.core.features import FeatureKeys

client = TestClient(app)


class TestLeaveFeatureGate:
    """leave.core Feature Gate 測試"""

    def test_create_request_feature_disabled(self):
        """leave.core disabled -> POST /api/v1/leave/requests 回傳 403"""
        actor = create_test_actor("company-A", role_id="employee")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.leave.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.LEAVE_CORE, "company-A"
                )
                payload = {
                    "leave_type_id": "00000000-0000-0000-0000-000000000001",
                    "start_date": "2026-04-01",
                    "end_date": "2026-04-02",
                    "total_days": 2,
                    "reason": "test"
                }
                response = client.post("/api/v1/leave/requests", json=payload)
                assert response.status_code == 403
                body = response.json()
                assert body["detail"]["code"] == "FEATURE_DISABLED"
                assert body["detail"]["feature"] == FeatureKeys.LEAVE_CORE

    def test_my_requests_feature_disabled(self):
        """leave.core disabled -> GET /api/v1/leave/my-requests 回傳 403"""
        actor = create_test_actor("company-A", role_id="employee")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.leave.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.LEAVE_CORE, "company-A"
                )
                response = client.get("/api/v1/leave/my-requests")
                assert response.status_code == 403
                assert response.json()["detail"]["code"] == "FEATURE_DISABLED"

    def test_pending_feature_disabled(self):
        """leave.core disabled -> GET /api/v1/leave/pending 回傳 403"""
        actor = create_test_actor("company-A", role_id="company_admin")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.leave.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.LEAVE_CORE, "company-A"
                )
                response = client.get("/api/v1/leave/pending")
                assert response.status_code == 403
                assert response.json()["detail"]["code"] == "FEATURE_DISABLED"

    def test_approve_feature_disabled(self):
        """leave.core disabled -> POST /api/v1/leave/requests/{id}/approve 回傳 403"""
        actor = create_test_actor("company-A", role_id="company_admin")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.leave.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.LEAVE_CORE, "company-A"
                )
                req_id = "00000000-0000-0000-0000-000000000099"
                response = client.post(
                    f"/api/v1/leave/requests/{req_id}/approve",
                    json={"comment": "approved"}
                )
                assert response.status_code == 403
                assert response.json()["detail"]["code"] == "FEATURE_DISABLED"

    def test_gate_rejection_schema_consistent(self):
        """Feature Gate 拒絕 schema 一致性"""
        actor = create_test_actor("company-A", role_id="employee")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.leave.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.LEAVE_CORE, "company-A"
                )
                response = client.get("/api/v1/leave/my-requests")
                assert response.status_code == 403
                detail = response.json()["detail"]
                assert "code" in detail and "feature" in detail and "message" in detail
