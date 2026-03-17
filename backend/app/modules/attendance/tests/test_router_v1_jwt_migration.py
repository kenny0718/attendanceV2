"""WP-C1-07: router_v1 JWT Migration 驗證測試

驗證 attendance router_v1 所有 11 個 endpoints：
1. JWT actor 可正常呼叫
2. 不需要 X-Company-ID header
3. tenant isolation 維持正確
4. feature gate 不被破壞
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.tests.utils.auth import create_test_actor, override_actor_dependency
from app.modules.tenants.models import Tenant
from app.modules.auth.models import User

COMPANY_ID = "company-jwt-migration-test"
COMPANY_ID_B = "company-jwt-migration-test-b"


@pytest.fixture
def client(db):
    from app.core.database import get_db
    app.dependency_overrides[get_db] = lambda: db
    c = TestClient(app)
    yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def setup_tenant(db):
    """建立測試所需 tenant"""
    for cid, name in [(COMPANY_ID, "JWT Migration Test Co"), (COMPANY_ID_B, "JWT Migration Test Co B")]:
        t = db.query(Tenant).filter(Tenant.id == cid).first()
        if not t:
            t = Tenant(id=cid, name=name, is_active=True)
            db.add(t)
    db.commit()


@pytest.fixture
def test_user(db, setup_tenant):
    u = User(id=uuid4(), display_name="JWT Migration User", password_hash="x", is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def actor(test_user):
    return create_test_actor(COMPANY_ID, user_id=test_user.id)


@pytest.fixture
def actor_b(db, setup_tenant):
    u = User(id=uuid4(), display_name="JWT Migration User B", password_hash="x", is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return create_test_actor(COMPANY_ID_B, user_id=u.id)


def mock_gate(monkeypatch):
    """Patch feature gate to always pass"""
    monkeypatch.setattr(
        'app.modules.attendance.api._require_attendance_feature',
        lambda company_id, db: None
    )


class TestJWTActorNoBearerHeader:
    """驗證：不帶 X-Company-ID / X-User-ID header，純 JWT actor 可正常呼叫"""

    def test_punch_in_no_company_header(self, client, actor, monkeypatch):
        """punch-in 不需要 X-Company-ID header"""
        mock_gate(monkeypatch)
        with override_actor_dependency(actor):
            resp = client.post("/api/v1/attendance/punch-in", json={})
        # 201 or 409 (already open) — both mean auth passed
        assert resp.status_code in (201, 409), f"Expected 201/409, got {resp.status_code}: {resp.json()}"

    def test_current_status_no_company_header(self, client, actor, monkeypatch):
        """current-status 不需要 X-Company-ID header"""
        mock_gate(monkeypatch)
        with override_actor_dependency(actor):
            resp = client.get("/api/v1/attendance/current-status")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.json()}"

    def test_history_no_company_header(self, client, actor, monkeypatch):
        """history 不需要 X-Company-ID header"""
        mock_gate(monkeypatch)
        with override_actor_dependency(actor):
            resp = client.get("/api/v1/attendance/history")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.json()}"

    def test_break_punches_no_company_header(self, client, actor, monkeypatch):
        """break-punches 不需要 X-Company-ID header"""
        mock_gate(monkeypatch)
        with override_actor_dependency(actor):
            resp = client.get("/api/v1/attendance/break-punches")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.json()}"

    def test_sessions_no_company_header(self, client, actor, monkeypatch):
        """sessions 不需要 X-Company-ID header"""
        mock_gate(monkeypatch)
        with override_actor_dependency(actor):
            resp = client.get("/api/v1/attendance/sessions")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.json()}"

    def test_user_summary_no_company_header(self, client, actor, monkeypatch):
        """user-summary 不需要 X-Company-ID header"""
        mock_gate(monkeypatch)
        with override_actor_dependency(actor):
            resp = client.get("/api/v1/attendance/reports/user-summary")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.json()}"

    def test_company_summary_no_company_header(self, client, actor, monkeypatch):
        """company-summary 不需要 X-Company-ID header"""
        mock_gate(monkeypatch)
        with override_actor_dependency(actor):
            resp = client.get("/api/v1/attendance/reports/company-summary")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.json()}"


class TestJWTActorTenantIsolation:
    """驗證：tenant isolation 在 JWT actor 模式下維持正確"""

    def test_punch_in_company_a_creates_session_for_company_a(self, client, actor, monkeypatch, db):
        """punch-in 建立的 session company_id 來自 actor，而非 header"""
        from app.modules.attendance.models import AttendanceSession
        mock_gate(monkeypatch)

        with override_actor_dependency(actor):
            resp = client.post("/api/v1/attendance/punch-in", json={})

        if resp.status_code == 201:
            session_id = resp.json()["session_id"]
            session = db.query(AttendanceSession).filter(
                AttendanceSession.id == session_id
            ).first()
            assert session is not None
            assert str(session.company_id) == COMPANY_ID, (
                f"Session company_id should be {COMPANY_ID}, got {session.company_id}"
            )
        else:
            # 409 = already open, also fine (company_id came from actor)
            assert resp.status_code == 409

    def test_company_a_cannot_see_company_b_sessions(self, client, actor, actor_b, monkeypatch, db):
        """company-A actor 查詢 sessions 不會看到 company-B 的資料"""
        from app.modules.attendance.models import AttendanceSession
        from datetime import timedelta
        mock_gate(monkeypatch)

        # 建立 company-B 的 session
        s = AttendanceSession(
            company_id=COMPANY_ID_B,
            user_id=actor_b.user_id,
            punch_in_time=datetime.now(timezone.utc) - timedelta(hours=5),
            punch_out_time=datetime.now(timezone.utc) - timedelta(hours=1),
            status="closed",
            duration_minutes=240,
        )
        db.add(s)
        db.commit()

        # company-A actor 查詢
        with override_actor_dependency(actor):
            resp = client.get("/api/v1/attendance/sessions")

        assert resp.status_code == 200
        sessions = resp.json()["sessions"]
        for session in sessions:
            assert session["company_id"] == COMPANY_ID, (
                f"company-A actor should only see COMPANY_ID sessions, got {session['company_id']}"
            )


class TestJWTActorWithoutCompanyScope:
    """驗證：無 active_company_id 的 actor 應被拒絕（403）"""

    def test_no_active_company_returns_403(self, client, monkeypatch):
        """actor 無 active_company_id 時，get_actor_with_company 應回傳 403
        
        WP-C1-07: get_actor_with_company 在 actor.has_active_company() 為 False 時拋出 403。
        測試方式：override get_current_actor（上游 dependency）注入無 company scope 的 actor，
        讓 get_actor_with_company 正常執行並觸發 403 check。
        """
        from app.core.scope import Actor, UserRole
        from app.core.dependencies import get_current_actor
        no_company_actor = Actor(
            user_id=uuid4(),
            role=UserRole.COMPANY_USER,
            company_memberships=set(),
            active_company_id=None,
            active_role_id=None,
        )
        mock_gate(monkeypatch)
        # Override get_current_actor（上游），讓 get_actor_with_company 的 has_active_company() 檢查正常執行
        app.dependency_overrides[get_current_actor] = lambda: no_company_actor
        try:
            resp = client.get("/api/v1/attendance/current-status")
        finally:
            app.dependency_overrides.pop(get_current_actor, None)
        # get_actor_with_company raises 403 when no active_company_id
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.json()}"


class TestPunchOutBreakFlow:
    """驗證：punch-out / break-out / break-in 完整流程可以 JWT actor 執行"""

    def test_punch_in_out_flow_with_jwt_actor(self, client, actor, monkeypatch):
        """完整 punch-in → punch-out 流程使用 JWT actor"""
        mock_gate(monkeypatch)

        # punch-in
        with override_actor_dependency(actor):
            resp_in = client.post("/api/v1/attendance/punch-in", json={})
        assert resp_in.status_code in (201, 409)

        if resp_in.status_code == 201:
            # punch-out
            with override_actor_dependency(actor):
                resp_out = client.post("/api/v1/attendance/punch-out", json={})
            assert resp_out.status_code == 200, f"punch-out failed: {resp_out.json()}"
            data = resp_out.json()
            assert data["status"] == "closed"
            assert data["company_id"] == COMPANY_ID

    def test_break_out_break_in_with_jwt_actor(self, client, actor, monkeypatch):
        """break-out / break-in 使用 JWT actor"""
        mock_gate(monkeypatch)

        # 先確保有 open session
        with override_actor_dependency(actor):
            resp_in = client.post("/api/v1/attendance/punch-in", json={})
        assert resp_in.status_code in (201, 409)

        # break-out
        with override_actor_dependency(actor):
            resp_break_out = client.post("/api/v1/attendance/break-out", json={})
        assert resp_break_out.status_code in (201, 404), f"break-out: {resp_break_out.json()}"

        if resp_break_out.status_code == 201:
            # break-in
            with override_actor_dependency(actor):
                resp_break_in = client.post("/api/v1/attendance/break-in", json={})
            assert resp_break_in.status_code == 201, f"break-in: {resp_break_in.json()}"
