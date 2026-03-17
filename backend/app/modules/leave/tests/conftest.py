"""Leave module tests configuration

WP-C1-05: Tenant Isolation 測試 conftest
- 使用真實 PostgreSQL（app conftest.py 的 test_db fixture）
- 建立測試用 tenants / leave_types / leave_approval_policies
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.modules.tenants.models import Tenant
from app.modules.leave.models import LeaveType, LeaveApprovalPolicy


COMPANY_A = "leave-iso-company-a"
COMPANY_B = "leave-iso-company-b"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def leave_test_db(test_db):
    """在 test_db（PostgreSQL）中建立 leave 測試所需的 tenants / leave_types / policies"""
    db = test_db

    # 建立 tenants
    for cid, cname in [(COMPANY_A, "Leave ISO Company A"), (COMPANY_B, "Leave ISO Company B")]:
        existing = db.query(Tenant).filter(Tenant.id == cid).first()
        if not existing:
            db.add(Tenant(id=cid, name=cname, is_active=True))
    db.commit()

    # 建立 leave_types（Company A）
    lt_a = LeaveType(
        id=uuid4(),
        company_id=COMPANY_A,
        code="annual",
        name="Annual Leave",
        is_active=True,
    )
    # 建立 leave_types（Company B）
    lt_b = LeaveType(
        id=uuid4(),
        company_id=COMPANY_B,
        code="annual",
        name="Annual Leave",
        is_active=True,
    )
    db.add(lt_a)
    db.add(lt_b)
    db.commit()
    db.refresh(lt_a)
    db.refresh(lt_b)

    # 建立 approval policies（Company A）
    policy_a = LeaveApprovalPolicy(
        id=uuid4(),
        company_id=COMPANY_A,
        leave_type_id=None,  # company-wide default
        min_days=0.5,
        max_days=None,
        approval_level=1,
        is_active=True,
    )
    # 建立 approval policies（Company B）
    policy_b = LeaveApprovalPolicy(
        id=uuid4(),
        company_id=COMPANY_B,
        leave_type_id=None,
        min_days=0.5,
        max_days=None,
        approval_level=1,
        is_active=True,
    )
    db.add(policy_a)
    db.add(policy_b)
    db.commit()

    return {
        "db": db,
        "leave_type_a_id": lt_a.id,
        "leave_type_b_id": lt_b.id,
        "company_a": COMPANY_A,
        "company_b": COMPANY_B,
    }
