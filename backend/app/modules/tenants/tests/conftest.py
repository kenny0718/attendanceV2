"""Test fixtures for tenants module

使用 PostgreSQL Test DB + Transaction Rollback 策略。
並在每個測試 session 內補齊 roles，避免 Membership.role_id FK 失敗。
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.main import app
from app.modules.auth.models import Role


TEST_DATABASE_URL = "postgresql+psycopg2://postgres:Raxcxtjq260!@127.0.0.1:5432/attendance_test_db"


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    roles_data = [
        ("employee", "Employee", "Regular employee"),
        ("manager", "Manager", "Can approve attendance for team members"),
        ("company_admin", "Company Admin", "Full access within company"),
        ("customer_service", "Customer Service", "Can access multiple companies"),
        ("hr_manager", "HR Manager", "HR admin access"),
        ("super_admin", "Super Admin", "Platform super admin"),
    ]
    for role_id, name, description in roles_data:
        if session.query(Role).filter(Role.id == role_id).first() is None:
            session.add(Role(id=role_id, name=name, description=description))
    session.flush()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
