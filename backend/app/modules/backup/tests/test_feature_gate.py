"""WP-C1-06: Feature Gate 測試 - backup module"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.tests.utils.auth import create_test_actor, override_actor_dependency
from app.core.feature_service import FeatureDisabledError
from app.core.features import FeatureKeys

client = TestClient(app)


class TestBackupFeatureGate:
    """backup.core Feature Gate 測試"""

    def test_backup_export_feature_disabled(self, test_db):
        """backup.core disabled -> POST /api/backup/export 回傳 403 FEATURE_DISABLED"""
        actor = create_test_actor("company-A", role_id="admin")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.backup.api._require_backup_feature"
            ) as mock_gate:
                mock_gate.side_effect = __import__('fastapi').HTTPException(
                    status_code=403,
                    detail={
                        "code": "FEATURE_DISABLED",
                        "feature": FeatureKeys.BACKUP_CORE,
                        "message": "backup.core is disabled"
                    }
                )
                response = client.post("/api/backup/export")
                assert response.status_code == 403
                body = response.json()
                assert body["detail"]["code"] == "FEATURE_DISABLED"

    def test_backup_export_feature_enabled(self, test_db):
        """backup.core enabled + admin -> POST /api/backup/export 通過 gate"""
        actor = create_test_actor("company-A", role_id="admin")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.backup.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.return_value = None
                with patch(
                    "app.modules.backup.api.assert_admin_scope"
                ) as mock_scope:
                    mock_scope.return_value = None
                    with patch(
                        "app.modules.backup.api.BackupService"
                    ) as mock_svc:
                        mock_svc.return_value.export_company.return_value = {
                            "version": "1.0", "data": {}
                        }
                        response = client.post("/api/backup/export")
                        assert response.status_code == 200

    def test_backup_restore_feature_disabled(self, test_db):
        """backup.core disabled -> POST /api/backup/restore 回傳 403 FEATURE_DISABLED"""
        actor = create_test_actor("company-A", role_id="admin")
        with override_actor_dependency(actor):
            with patch(
                "app.modules.backup.api.get_feature_service"
            ) as mock_fs:
                mock_fs.return_value.require_enabled.side_effect = FeatureDisabledError(
                    FeatureKeys.BACKUP_CORE, "company-A"
                )
                response = client.post("/api/backup/restore", json={"version": "1.0", "data": {}})
                assert response.status_code == 403
                assert response.json()["detail"]["code"] == "FEATURE_DISABLED"
