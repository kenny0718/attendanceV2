"""Tenant Isolation 測試

驗證 Tenant Isolation (P0) 規則：
- A 公司 context 無法存取 B 公司資料
- company_id 必須由後端注入，不信任 request body

WP-C1-07: JWT Actor Migration - 使用 override_actor_dependency
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.modules.attendance.models import AttendanceRecord
from app.tests.utils.auth import create_test_actor, override_actor_dependency


class DummySession:
    """Mock Session for testing (不連接真實資料庫)"""
    
    def __init__(self):
        self._storage = {}
    
    def add(self, obj):
        if isinstance(obj, AttendanceRecord):
            self._storage[obj.id] = obj
    
    def commit(self):
        pass
    
    def close(self):
        pass
    
    def flush(self):
        pass
    
    def refresh(self, obj):
        pass
    
    def query(self, model):
        return DummyQuery(self._storage, model)


class DummyQuery:
    """Mock Query for testing"""
    
    def __init__(self, storage, model):
        self._storage = storage
        self._model = model
        self._filters = []
    
    def filter(self, *conditions):
        self._filters.extend(conditions)
        return self
    
    def first(self):
        model_name = getattr(self._model, "__name__", str(self._model))
        if model_name == "Tenant":
            class MockTenant:
                id = "company-A"
                name = "Test Company"
                is_active = True
            return MockTenant()
        return None
    
    def count(self):
        model_name = getattr(self._model, "__name__", str(self._model))
        if model_name == "Tenant" or model_name.endswith(".id"):
            return 1
        return 0



def override_get_db():
    db = DummySession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_test_environment():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


client = TestClient(app)

TEST_UUID_A = "11111111-1111-1111-1111-111111111111"
TEST_UUID_B = "22222222-2222-2222-2222-222222222222"
TEST_UUID_C = "33333333-3333-3333-3333-333333333333"


class TestTenantIsolation:
    def test_approve_requires_valid_jwt_actor(self):
        response = client.post(
            f"/api/attendance/{TEST_UUID_A}/approve",
            json={
                "employee_id": "emp-001",
                "approved_by": "approver-001"
            }
        )
        assert response.status_code == 401
    
    def test_approve_with_company_a_context(self):
        actor = create_test_actor("company-A")
        with override_actor_dependency(actor):
            response = client.post(
                f"/api/attendance/{TEST_UUID_A}/approve",
                json={
                    "employee_id": "emp-A-001",
                    "approved_by": "approver-A-001"
                }
            )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]["error"].lower()
    
    def test_approve_with_company_b_context(self):
        actor = create_test_actor("company-B")
        with override_actor_dependency(actor):
            response = client.post(
                f"/api/attendance/{TEST_UUID_B}/approve",
                json={
                    "employee_id": "emp-B-001",
                    "approved_by": "approver-B-001"
                }
            )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]["error"].lower()
    
    def test_company_id_injected_by_backend_not_request_body(self):
        actor = create_test_actor("company-A")
        with override_actor_dependency(actor):
            response = client.post(
                f"/api/attendance/{TEST_UUID_C}/approve",
                json={
                    "company_id": "company-B",
                    "employee_id": "emp-001",
                    "approved_by": "approver-001"
                }
            )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]["error"].lower()
    
    def test_mock_create_requires_valid_jwt_actor(self):
        response = client.post("/api/attendance/mock-create")
        assert response.status_code == 401
    
    def test_mock_create_with_company_context(self):
        actor = create_test_actor("company-A")
        with override_actor_dependency(actor):
            response = client.post("/api/attendance/mock-create")
        assert response.status_code == 200
        data = response.json()
        assert "attendance_record_id" in data
        assert len(data["attendance_record_id"]) > 0
