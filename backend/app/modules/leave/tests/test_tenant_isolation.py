"""WP-C1-05: Leave Module — Tenant Isolation 測試（PostgreSQL 真實 DB）"""

import pytest
from datetime import date, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.modules.leave.models import LeaveRequest, LeaveType, LeaveApprovalPolicy
from app.modules.tenants.models import Tenant, CompanyEntitlement
from app.modules.auth.models import User
from app.tests.utils.auth import create_test_actor, override_actor_dependency
from app.core.features import FeatureKeys

client = TestClient(app)

COMPANY_A = "leave-iso-a"
COMPANY_B = "leave-iso-b"
USER_A = uuid4()
USER_B = uuid4()


def setup_leave_fixtures(db):
    """建立 tenants / users / leave_types / policies"""
    # Tenants
    for cid, cname in [(COMPANY_A, "Leave Iso A"), (COMPANY_B, "Leave Iso B")]:
        if not db.query(Tenant).filter(Tenant.id == cid).first():
            db.add(Tenant(id=cid, name=cname, is_active=True))

    # Users（leave_requests 有 FK → users.id）
    for uid in [USER_A, USER_B]:
        if not db.query(User).filter(User.id == uid).first():
            db.add(User(
                id=uid,
                display_name=f"User {uid}",
                password_hash="dummy",
                is_active=True,
            ))
    db.commit()

    # CompanyEntitlements for leave.core feature gate
    for cid in [COMPANY_A, COMPANY_B]:
        if not db.query(CompanyEntitlement).filter(
            CompanyEntitlement.company_id == cid,
            CompanyEntitlement.feature_key == FeatureKeys.LEAVE_CORE
        ).first():
            db.add(CompanyEntitlement(
                id=uuid4(),
                company_id=cid,
                feature_key=FeatureKeys.LEAVE_CORE,
                enabled=True,
            ))
    db.commit()

    # Leave Types
    lt_a = LeaveType(
        id=uuid4(), company_id=COMPANY_A,
        code="annual", name="Annual Leave", is_active=True,
    )
    lt_b = LeaveType(
        id=uuid4(), company_id=COMPANY_B,
        code="annual", name="Annual Leave", is_active=True,
    )
    db.add(lt_a)
    db.add(lt_b)
    db.commit()
    db.refresh(lt_a)
    db.refresh(lt_b)

    # Approval Policies
    db.add(LeaveApprovalPolicy(
        id=uuid4(), company_id=COMPANY_A,
        leave_type_id=None, min_days=0.5, max_days=None,
        approval_level=1, is_active=True,
    ))
    db.add(LeaveApprovalPolicy(
        id=uuid4(), company_id=COMPANY_B,
        leave_type_id=None, min_days=0.5, max_days=None,
        approval_level=1, is_active=True,
    ))
    db.commit()

    return lt_a.id, lt_b.id


def create_leave_request_direct(db, company_id, user_id, leave_type_id):
    req = LeaveRequest(
        id=uuid4(),
        company_id=company_id,
        user_id=user_id,
        leave_type_id=leave_type_id,
        start_date=date.today() + timedelta(days=7),
        end_date=date.today() + timedelta(days=8),
        total_days=2.0,
        reason="Test leave",
        status="pending",
        required_approval_level=1,
        is_half_day=False,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


# ============================================================
# 1. Query Isolation
# ============================================================

class TestLeaveQueryIsolation:

    def test_my_requests_only_returns_own_company_data(self, test_db):
        """Company B 查詢 my-requests，不得看到 Company A 的資料"""
        db = test_db
        lt_a_id, lt_b_id = setup_leave_fixtures(db)

        create_leave_request_direct(db, COMPANY_A, USER_A, lt_a_id)
        create_leave_request_direct(db, COMPANY_B, USER_B, lt_b_id)
        create_leave_request_direct(db, COMPANY_B, USER_B, lt_b_id)
        db.flush()

        actor_b = create_test_actor(COMPANY_B, user_id=USER_B)
        with override_actor_dependency(actor_b):
            resp = client.get("/api/v1/leave/my-requests")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert all(item["company_id"] == COMPANY_B for item in data["requests"])

        actor_a = create_test_actor(COMPANY_A, user_id=USER_A)
        with override_actor_dependency(actor_a):
            resp = client.get("/api/v1/leave/my-requests")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert all(item["company_id"] == COMPANY_A for item in data["requests"])

    def test_pending_list_only_returns_own_company_data(self, test_db):
        """pending list 不得含其他 company 的 pending requests"""
        db = test_db
        lt_a_id, lt_b_id = setup_leave_fixtures(db)

        for _ in range(3):
            create_leave_request_direct(db, COMPANY_A, USER_A, lt_a_id)
        for _ in range(2):
            create_leave_request_direct(db, COMPANY_B, USER_B, lt_b_id)
        db.flush()

        actor_a = create_test_actor(COMPANY_A, user_id=USER_A)
        with override_actor_dependency(actor_a):
            resp = client.get("/api/v1/leave/pending")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert all(item["company_id"] == COMPANY_A for item in data["requests"])

        actor_b = create_test_actor(COMPANY_B, user_id=USER_B)
        with override_actor_dependency(actor_b):
            resp = client.get("/api/v1/leave/pending")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert all(item["company_id"] == COMPANY_B for item in data["requests"])


# ============================================================
# 2. ID Access Isolation
# ============================================================

class TestLeaveIdAccessIsolation:

    def test_company_b_cannot_approve_company_a_request(self, test_db):
        """Company B 無法 approve Company A 的 leave request"""
        db = test_db
        lt_a_id, lt_b_id = setup_leave_fixtures(db)

        req_a = create_leave_request_direct(db, COMPANY_A, USER_A, lt_a_id)
        db.flush()

        actor_b = create_test_actor(COMPANY_B, user_id=USER_B)
        with override_actor_dependency(actor_b):
            resp = client.post(
                f"/api/v1/leave/requests/{req_a.id}/approve",
                json={"comment": "cross-tenant attempt"}
            )
        assert resp.status_code == 404

    def test_company_b_cannot_reject_company_a_request(self, test_db):
        """Company B 無法 reject Company A 的 leave request"""
        db = test_db
        lt_a_id, lt_b_id = setup_leave_fixtures(db)

        req_a = create_leave_request_direct(db, COMPANY_A, USER_A, lt_a_id)
        db.flush()

        actor_b = create_test_actor(COMPANY_B, user_id=USER_B)
        with override_actor_dependency(actor_b):
            resp = client.post(
                f"/api/v1/leave/requests/{req_a.id}/reject",
                json={"comment": "cross-tenant reject"}
            )
        assert resp.status_code == 404


# ============================================================
# 3. Submit Isolation
# ============================================================

class TestLeaveSubmitIsolation:

    def test_cannot_use_other_company_leave_type(self, test_db):
        """Company B 無法使用 Company A 的 leave_type_id"""
        db = test_db
        lt_a_id, lt_b_id = setup_leave_fixtures(db)
        db.flush()

        actor_b = create_test_actor(COMPANY_B, user_id=USER_B)
        with override_actor_dependency(actor_b):
            resp = client.post(
                "/api/v1/leave/requests",
                json={
                    "leave_type_id": str(lt_a_id),
                    "start_date": str(date.today() + timedelta(days=10)),
                    "end_date": str(date.today() + timedelta(days=11)),
                    "reason": "cross-tenant leave attempt",
                    "is_half_day": False,
                }
            )
        assert resp.status_code == 422

    def test_submit_with_own_company_leave_type_succeeds(self, test_db):
        """使用自己 company 的 leave_type 申請請假應成功"""
        db = test_db
        lt_a_id, lt_b_id = setup_leave_fixtures(db)
        db.flush()

        actor_a = create_test_actor(COMPANY_A, user_id=USER_A)
        with override_actor_dependency(actor_a):
            resp = client.post(
                "/api/v1/leave/requests",
                json={
                    "leave_type_id": str(lt_a_id),
                    "start_date": str(date.today() + timedelta(days=5)),
                    "end_date": str(date.today() + timedelta(days=6)),
                    "reason": "valid annual leave",
                    "is_half_day": False,
                }
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["company_id"] == COMPANY_A


# ============================================================
# 4. Repo Layer Isolation
# ============================================================

class TestLeaveRepoIsolation:

    def test_get_leave_request_by_id_enforces_company_id(self, test_db):
        """get_leave_request_by_id 必須同時驗證 company_id"""
        from app.modules.leave.repo import LeaveRequestRepository
        db = test_db
        lt_a_id, lt_b_id = setup_leave_fixtures(db)

        req_a = create_leave_request_direct(db, COMPANY_A, USER_A, lt_a_id)
        repo = LeaveRequestRepository(db)

        result = repo.get_leave_request_by_id(COMPANY_A, req_a.id)
        assert result is not None
        assert result.company_id == COMPANY_A

        result_b = repo.get_leave_request_by_id(COMPANY_B, req_a.id)
        assert result_b is None

    def test_get_user_leave_requests_enforces_company_id(self, test_db):
        """get_user_leave_requests 按 company_id 隔離"""
        from app.modules.leave.repo import LeaveRequestRepository
        db = test_db
        lt_a_id, lt_b_id = setup_leave_fixtures(db)

        shared_user = USER_A
        create_leave_request_direct(db, COMPANY_A, shared_user, lt_a_id)
        create_leave_request_direct(db, COMPANY_A, shared_user, lt_a_id)
        create_leave_request_direct(db, COMPANY_B, USER_B, lt_b_id)

        repo = LeaveRequestRepository(db)

        results_a = repo.get_user_leave_requests(COMPANY_A, shared_user)
        assert len(results_a) == 2
        assert all(r.company_id == COMPANY_A for r in results_a)

        results_b = repo.get_user_leave_requests(COMPANY_B, USER_B)
        assert len(results_b) == 1
        assert results_b[0].company_id == COMPANY_B

    def test_get_leave_type_by_id_enforces_company_id(self, test_db):
        """get_leave_type_by_id 必須驗證 company_id"""
        from app.modules.leave.repo import LeaveTypeRepository
        db = test_db
        lt_a_id, lt_b_id = setup_leave_fixtures(db)

        repo = LeaveTypeRepository(db)

        result = repo.get_leave_type_by_id(COMPANY_A, lt_a_id)
        assert result is not None
        assert result.company_id == COMPANY_A

        result_cross = repo.get_leave_type_by_id(COMPANY_B, lt_a_id)
        assert result_cross is None
