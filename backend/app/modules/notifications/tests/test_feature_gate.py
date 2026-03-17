"""WP-C1-06: Feature Gate 測試 - notifications module"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.tests.utils.auth import create_test_actor, override_actor_dependency
from app.core.feature_service import FeatureDisabledError
from app.core.features import FeatureKeys

client = TestClient(app)


class TestNotificationsFeatureGate:
    """notifications.core Feature Gate 測試"""

    def test_notifications_feature_enabled(self, test_db):
        """notifications.core enabled -> GET /api/notifications 正常回應"""
        actor = create_test_actor("company-A", role_id="admin")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.notifications.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.return_value = None
                with patch(
                    "app.modules.notifications.api.get_notification_repository"
                ) as mock_repo:
                    with patch(
                        "app.modules.notifications.api.get_notification_service"
                    ) as mock_svc:
                        mock_svc.return_value.get_notifications.return_value = {
                            "notifications": [],
                            "pagination": {"limit": 50, "offset": 0, "total": 0}
                        }
                        response = client.get("/api/notifications")
                        assert response.status_code == 200
                        mock_fs.return_value.require_enabled.assert_called_once_with(
                            "company-A", FeatureKeys.NOTIFICATIONS_CORE
                        )

    def test_notifications_feature_disabled(self, test_db):
        """notifications.core disabled -> GET /api/notifications 回傳 403 FEATURE_DISABLED"""
        actor = create_test_actor("company-A", role_id="admin")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.notifications.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.NOTIFICATIONS_CORE, "company-A"
                )
                response = client.get("/api/notifications")
                assert response.status_code == 403
                body = response.json()
                assert body["detail"]["code"] == "FEATURE_DISABLED"
                assert body["detail"]["feature"] == FeatureKeys.NOTIFICATIONS_CORE

    def test_gate_rejection_schema_consistent(self, test_db):
        """Feature Gate 拒絕 schema 一致性"""
        actor = create_test_actor("company-A", role_id="employee")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.notifications.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.NOTIFICATIONS_CORE, "company-A"
                )
                response = client.get("/api/notifications")
                assert response.status_code == 403
                detail = response.json()["detail"]
                assert "code" in detail and "feature" in detail and "message" in detail
