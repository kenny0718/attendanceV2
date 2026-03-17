"""WP-C1-06: Feature Gate 測試 - attendance module"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.tests.utils.auth import create_test_actor, override_actor_dependency
from app.core.feature_service import FeatureDisabledError
from app.core.features import FeatureKeys

client = TestClient(app)


class TestAttendanceFeatureGate:
    """attendance.core Feature Gate 測試"""

    def test_punch_in_feature_disabled(self):
        """attendance.core disabled -> POST /api/v1/attendance/punch-in 回傳 403"""
        actor = create_test_actor("company-A", role_id="employee")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.attendance.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.ATTENDANCE_CORE, "company-A"
                )
                response = client.post("/api/v1/attendance/punch-in", json={"notes": None})
                assert response.status_code == 403
                body = response.json()
                assert body["detail"]["code"] == "FEATURE_DISABLED"
                assert body["detail"]["feature"] == FeatureKeys.ATTENDANCE_CORE

    def test_punch_out_feature_disabled(self):
        """attendance.core disabled -> POST /api/v1/attendance/punch-out 回傳 403"""
        actor = create_test_actor("company-A", role_id="employee")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.attendance.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.ATTENDANCE_CORE, "company-A"
                )
                response = client.post("/api/v1/attendance/punch-out", json={"notes": None})
                assert response.status_code == 403
                assert response.json()["detail"]["code"] == "FEATURE_DISABLED"

    def test_current_status_feature_disabled(self):
        """attendance.core disabled -> GET /api/v1/attendance/current-status 回傳 403"""
        actor = create_test_actor("company-A", role_id="employee")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.attendance.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.ATTENDANCE_CORE, "company-A"
                )
                response = client.get("/api/v1/attendance/current-status")
                assert response.status_code == 403
                assert response.json()["detail"]["code"] == "FEATURE_DISABLED"

    def test_history_feature_disabled(self):
        """attendance.core disabled -> GET /api/v1/attendance/history 回傳 403"""
        actor = create_test_actor("company-A", role_id="employee")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.attendance.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.ATTENDANCE_CORE, "company-A"
                )
                response = client.get("/api/v1/attendance/history")
                assert response.status_code == 403
                assert response.json()["detail"]["code"] == "FEATURE_DISABLED"

    def test_sessions_reporting_feature_disabled(self):
        """attendance.core disabled -> GET /api/v1/attendance/sessions 回傳 403"""
        actor = create_test_actor("company-A", role_id="employee")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.attendance.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.ATTENDANCE_CORE, "company-A"
                )
                response = client.get("/api/v1/attendance/sessions")
                assert response.status_code == 403
                assert response.json()["detail"]["code"] == "FEATURE_DISABLED"

    def test_gate_rejection_schema_consistent(self):
        """Feature Gate 拒絕 schema 一致性 (code/feature/message)"""
        actor = create_test_actor("company-A", role_id="employee")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.attendance.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.ATTENDANCE_CORE, "company-A"
                )
                response = client.post("/api/v1/attendance/punch-in", json={})
                assert response.status_code == 403
                detail = response.json()["detail"]
                assert "code" in detail
                assert "feature" in detail
                assert "message" in detail
                assert detail["code"] == "FEATURE_DISABLED"
