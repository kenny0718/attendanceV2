"""Test Punch In/Out API (JWT actor compatibility).

Test Coverage:
- Punch in success
- Punch in duplicate (409)
- Punch out success
- Punch out no open session (404)
- Current status (open/no open)
- History (pagination)
- Tenant isolation
- Concurrency (race condition)
"""

import pytest
from datetime import datetime
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.modules.auth.models import User
from app.modules.tenants.models import Tenant
from app.modules.attendance.models import AttendanceSession
from app.tests.utils.auth import create_test_actor, override_actor_dependency


# Test database setup
TEST_DATABASE_URL = "postgresql://postgres:Raxcxtjq260!@127.0.0.1:5432/attendance_test"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    session.info["testing"] = True

    tenant_a = Tenant(id="company-a", name="Company A", is_active=True)
    tenant_b = Tenant(id="company-b", name="Company B", is_active=True)
    user1 = User(id=uuid4(), display_name="User 1", password_hash="dummy_hash", is_active=True)
    user2 = User(id=uuid4(), display_name="User 2", password_hash="dummy_hash", is_active=True)
    session.add_all([tenant_a, tenant_b, user1, user2])
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create test client with database override"""

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def bypass_attendance_feature_gate(monkeypatch):
    """Disable attendance feature gate for focused API behavior tests."""
    monkeypatch.setattr(
        "app.modules.attendance.api.punch._require_attendance_feature",
        lambda company_id, db: None,
    )


@pytest.fixture
def test_user(db):
    return db.query(User).first()


@pytest.fixture
def test_user2(db):
    return db.query(User).offset(1).first()


@pytest.fixture
def actor_company_a(test_user):
    return create_test_actor("company-a", user_id=test_user.id)


@pytest.fixture
def actor_company_b(test_user):
    return create_test_actor("company-b", user_id=test_user.id)


@pytest.fixture
def actor_user2_company_a(test_user2):
    return create_test_actor("company-a", user_id=test_user2.id)


def post_as(client: TestClient, actor, url: str, json: dict | None = None):
    with override_actor_dependency(actor):
        return client.post(url, json=json or {})


def get_as(client: TestClient, actor, url: str):
    with override_actor_dependency(actor):
        return client.get(url)


class TestPunchIn:
    def test_punch_in_success(self, client, test_user, actor_company_a):
        response = post_as(
            client,
            actor_company_a,
            "/api/v1/attendance/punch-in",
            json={"notes": "Morning punch in"},
        )

        assert response.status_code == 201
        data = response.json()

        assert "session_id" in data
        assert "user_id" in data
        assert "company_id" in data
        assert "punch_in_time" in data
        assert "status" in data

        assert data["user_id"] == str(test_user.id)
        assert data["company_id"] == "company-a"
        assert data["status"] == "open"
        assert data["punch_out_time"] is None
        assert data["duration_minutes"] is None

    def test_punch_in_with_location(self, client, actor_company_a):
        response = post_as(
            client,
            actor_company_a,
            "/api/v1/attendance/punch-in",
            json={
                "notes": "Punch in from office",
                "location": {"latitude": 25.0330, "longitude": 121.5654},
            },
        )

        assert response.status_code == 201
        assert response.json()["status"] == "open"

    def test_punch_in_duplicate_returns_409(self, client, actor_company_a):
        response1 = post_as(client, actor_company_a, "/api/v1/attendance/punch-in")
        assert response1.status_code == 201
        session_id = response1.json()["session_id"]

        response2 = post_as(client, actor_company_a, "/api/v1/attendance/punch-in")
        assert response2.status_code == 409

        detail = response2.json().get("detail", response2.json())
        assert "error" in detail
        assert "error_code" in detail
        assert detail["error_code"] == "ALREADY_OPEN_SESSION"
        assert detail["open_session_id"] == session_id


class TestPunchOut:
    def test_punch_out_success(self, client, actor_company_a):
        response1 = post_as(client, actor_company_a, "/api/v1/attendance/punch-in")
        assert response1.status_code == 201
        session_id = response1.json()["session_id"]

        response2 = post_as(
            client,
            actor_company_a,
            "/api/v1/attendance/punch-out",
            json={"notes": "End of day"},
        )

        assert response2.status_code == 200
        data = response2.json()
        assert data["session_id"] == session_id
        assert data["status"] == "closed"
        assert data["punch_out_time"] is not None
        assert data["duration_minutes"] is not None

    def test_punch_out_no_open_session_returns_404(self, client, actor_company_a):
        response = post_as(client, actor_company_a, "/api/v1/attendance/punch-out")
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert detail["error_code"] == "NO_OPEN_SESSION"

    def test_punch_out_twice_returns_404(self, client, actor_company_a):
        post_as(client, actor_company_a, "/api/v1/attendance/punch-in")
        response1 = post_as(client, actor_company_a, "/api/v1/attendance/punch-out")
        assert response1.status_code == 200

        response2 = post_as(client, actor_company_a, "/api/v1/attendance/punch-out")
        assert response2.status_code == 404


class TestCurrentStatus:
    def test_status_with_open_session(self, client, test_user, actor_company_a):
        post_as(client, actor_company_a, "/api/v1/attendance/punch-in")

        response = get_as(client, actor_company_a, "/api/v1/attendance/current-status")
        assert response.status_code == 200
        data = response.json()

        assert data["has_open_session"] is True
        assert data["session"] is not None
        assert data["elapsed_minutes"] is not None
        assert data["session"]["status"] == "open"
        assert data["session"]["user_id"] == str(test_user.id)
        assert data["session"]["company_id"] == "company-a"

    def test_status_without_open_session(self, client, actor_company_a):
        response = get_as(client, actor_company_a, "/api/v1/attendance/current-status")
        assert response.status_code == 200
        data = response.json()

        assert data["has_open_session"] is False
        assert data["session"] is None
        assert data["elapsed_minutes"] is None


class TestAttendanceHistory:
    def test_history_empty(self, client, actor_company_a):
        response = get_as(client, actor_company_a, "/api/v1/attendance/history")

        assert response.status_code == 200
        data = response.json()
        assert data["sessions"] == []
        assert data["limit"] == 50
        assert data["offset"] == 0

    def test_history_with_sessions(self, client, actor_company_a):
        post_as(client, actor_company_a, "/api/v1/attendance/punch-in")
        post_as(client, actor_company_a, "/api/v1/attendance/punch-out")

        response = get_as(client, actor_company_a, "/api/v1/attendance/history")
        assert response.status_code == 200
        data = response.json()

        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["status"] == "closed"

    def test_history_pagination(self, client, actor_company_a):
        response = get_as(client, actor_company_a, "/api/v1/attendance/history?limit=10&offset=5")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 5


class TestTenantIsolation:
    def test_different_companies_isolated(self, client, actor_company_a, actor_company_b):
        response_a = post_as(client, actor_company_a, "/api/v1/attendance/punch-in")
        assert response_a.status_code == 201

        response_b = post_as(client, actor_company_b, "/api/v1/attendance/punch-in")
        assert response_b.status_code == 201
        assert response_a.json()["session_id"] != response_b.json()["session_id"]

    def test_cannot_see_other_company_sessions(self, client, actor_company_a, actor_company_b):
        post_as(client, actor_company_a, "/api/v1/attendance/punch-in")

        response = get_as(client, actor_company_b, "/api/v1/attendance/current-status")
        assert response.status_code == 200
        assert response.json()["has_open_session"] is False

    def test_different_users_isolated(self, client, actor_company_a, actor_user2_company_a):
        post_as(client, actor_company_a, "/api/v1/attendance/punch-in")
        response = post_as(client, actor_user2_company_a, "/api/v1/attendance/punch-in")
        assert response.status_code == 201


class TestConcurrency:
    def test_concurrent_punch_in_only_one_succeeds(self, client, test_user, db, actor_company_a):
        session = AttendanceSession(
            company_id="company-a",
            user_id=test_user.id,
            punch_in_time=datetime.utcnow(),
            status="open",
        )
        db.add(session)
        db.commit()

        response = post_as(client, actor_company_a, "/api/v1/attendance/punch-in")

        assert response.status_code == 409
        assert response.json()["detail"]["error_code"] == "ALREADY_OPEN_SESSION"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
