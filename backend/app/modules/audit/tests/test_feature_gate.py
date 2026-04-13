"""WP-C1-06: Feature Gate 測試 - audit module

驗證：
- audit.core enabled -> 正常回應
- audit.core disabled -> 403 FEATURE_DISABLED
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.tests.utils.auth import create_test_actor, override_actor_dependency
from app.core.feature_service import FeatureDisabledError
from app.core.features import FeatureKeys

client = TestClient(app)


class TestAuditFeatureGate:
    """audit.core Feature Gate 測試"""

    def test_audit_logs_feature_enabled(self, test_db):
        """audit.core enabled -> GET /api/audit/logs 正常回應"""
        actor = create_test_actor("company-A", role_id="company_admin")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.audit.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.return_value = None
                response = client.get("/api/audit/logs")
                assert response.status_code == 200
                mock_fs.return_value.require_enabled.assert_called_once_with(
                    "company-A", FeatureKeys.AUDIT_CORE
                )

    def test_audit_logs_feature_disabled(self, test_db):
        """audit.core disabled -> GET /api/audit/logs 回傳 403 FEATURE_DISABLED"""
        actor = create_test_actor("company-A", role_id="company_admin")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.audit.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.AUDIT_CORE, "company-A"
                )
                response = client.get("/api/audit/logs")
                assert response.status_code == 403
                body = response.json()
                assert body["detail"]["code"] == "FEATURE_DISABLED"
                assert body["detail"]["feature"] == FeatureKeys.AUDIT_CORE

    def test_audit_export_feature_disabled(self, test_db):
        """audit.core disabled -> GET /api/audit/export 回傳 403 FEATURE_DISABLED"""
        actor = create_test_actor("company-A", role_id="company_admin")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.audit.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.AUDIT_CORE, "company-A"
                )
                response = client.get("/api/audit/export")
                assert response.status_code == 403
                assert response.json()["detail"]["code"] == "FEATURE_DISABLED"

    def test_audit_retention_feature_disabled(self, test_db):
        """audit.core disabled -> GET /api/audit/retention 回傳 403"""
        actor = create_test_actor("company-A", role_id="company_admin")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.audit.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.AUDIT_CORE, "company-A"
                )
                response = client.get("/api/audit/retention")
                assert response.status_code == 403
                assert response.json()["detail"]["code"] == "FEATURE_DISABLED"

    def test_gate_rejection_schema_consistent(self, test_db):
        """Feature Gate 拒絕 schema 一致性驗證"""
        actor = create_test_actor("company-A", role_id="company_admin")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.audit.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.AUDIT_CORE, "company-A"
                )
                response = client.get("/api/audit/logs")
                assert response.status_code == 403
                body = response.json()
                assert "detail" in body
                detail = body["detail"]
                assert "code" in detail
                assert "feature" in detail
                assert "message" in detail
                assert detail["code"] == "FEATURE_DISABLED"
