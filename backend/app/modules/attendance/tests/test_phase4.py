"""Phase 4 tests: Attendance DB layer + tenant isolation (JWT actor compatible)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from app.main import app
from app.core.database import get_db
from app.core.event_bus import get_event_bus
from app.tests.utils.auth import create_test_actor, override_actor_dependency


# Test database (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase4.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Test client
client = TestClient(app)


def override_get_db():
    """Override get_db with test database session."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_test_environment():
    """Setup dependency override for DB."""
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Create needed tables per test and cleanup after test."""
    from app.modules.attendance.models import AttendanceRecord
    from app.modules.tenants.models import Tenant

    Tenant.__table__.create(bind=engine, checkfirst=True)
    AttendanceRecord.__table__.create(bind=engine, checkfirst=True)

    db = TestingSessionLocal()
    db.add(Tenant(id="company-a", name="Company A", is_active=True))
    db.add(Tenant(id="company-b", name="Company B", is_active=True))
    db.commit()
    db.close()

    yield

    AttendanceRecord.__table__.drop(bind=engine, checkfirst=True)
    Tenant.__table__.drop(bind=engine, checkfirst=True)


@pytest.fixture
def actor_company_a():
    return create_test_actor("company-a")


@pytest.fixture
def actor_company_b():
    return create_test_actor("company-b")


def post_as(actor, url: str, json: dict | None = None):
    with override_actor_dependency(actor):
        return client.post(url, json=json or {})


def test_company_a_create_and_approve_ok(actor_company_a):
    """A company can create then approve its own record."""
    response = post_as(actor_company_a, "/api/attendance/mock-create")
    assert response.status_code == 200
    record_id = response.json()["attendance_record_id"]

    response = post_as(
        actor_company_a,
        f"/api/attendance/{record_id}/approve",
        json={"employee_id": "emp-001", "approved_by": "approver-001"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["payload"]["company_id"] == "company-a"
    assert data["payload"]["attendance_record_id"] == record_id


def test_company_b_cannot_approve_company_a_record(actor_company_a, actor_company_b):
    """Company B cannot approve Company A record (404)."""
    response = post_as(actor_company_a, "/api/attendance/mock-create")
    assert response.status_code == 200
    record_id = response.json()["attendance_record_id"]

    response = post_as(
        actor_company_b,
        f"/api/attendance/{record_id}/approve",
        json={"employee_id": "emp-001"},
    )

    assert response.status_code == 404
    assert "error" in response.json()["detail"]


def test_missing_actor_returns_401():
    """Without actor dependency override, endpoint should be unauthorized."""
    response = client.post("/api/attendance/mock-create")
    assert response.status_code == 401


def test_approve_emits_event(actor_company_a):
    """Approve should emit attendance.approved event."""
    response = post_as(actor_company_a, "/api/attendance/mock-create")
    assert response.status_code == 200
    record_id = response.json()["attendance_record_id"]

    event_bus = get_event_bus()
    with patch.object(event_bus, "emit", wraps=event_bus.emit) as mock_emit:
        response = post_as(
            actor_company_a,
            f"/api/attendance/{record_id}/approve",
            json={"employee_id": "emp-001", "approved_by": "approver-001"},
        )

        assert response.status_code == 200
        mock_emit.assert_called_once()

        call_args = mock_emit.call_args
        assert call_args[0][0] == "attendance.approved"

        payload = call_args[0][1]
        assert payload["company_id"] == "company-a"
        assert payload["attendance_record_id"] == record_id
        assert payload["employee_id"] == "emp-001"
        assert payload["approved_by"] == "approver-001"
        assert "approved_at" in payload


def test_invalid_record_id_format_returns_400(actor_company_a):
    """Invalid record_id format should return 400."""
    response = post_as(
        actor_company_a,
        "/api/attendance/invalid-uuid/approve",
        json={"employee_id": "emp-001"},
    )

    assert response.status_code == 400
    assert "error" in response.json()["detail"]


def test_tenant_isolation_query_filter(actor_company_a, actor_company_b):
    """Tenant isolation should enforce company-scoped query/update behavior."""
    response_a = post_as(actor_company_a, "/api/attendance/mock-create")
    assert response_a.status_code == 200
    record_id_a = response_a.json()["attendance_record_id"]

    response_b = post_as(actor_company_b, "/api/attendance/mock-create")
    assert response_b.status_code == 200
    record_id_b = response_b.json()["attendance_record_id"]

    response = post_as(
        actor_company_a,
        f"/api/attendance/{record_id_a}/approve",
        json={"employee_id": "emp-001"},
    )
    assert response.status_code == 200

    response = post_as(
        actor_company_a,
        f"/api/attendance/{record_id_b}/approve",
        json={"employee_id": "emp-001"},
    )
    assert response.status_code == 404

    response = post_as(
        actor_company_b,
        f"/api/attendance/{record_id_a}/approve",
        json={"employee_id": "emp-001"},
    )
    assert response.status_code == 404

    response = post_as(
        actor_company_b,
        f"/api/attendance/{record_id_b}/approve",
        json={"employee_id": "emp-001"},
    )
    assert response.status_code == 200
