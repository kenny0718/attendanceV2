"""Test fixtures for WP-11-04A

提供測試所需的 database session 和其他 fixtures
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.modules.tenants.models import Tenant, CompanyEntitlement
from app.modules.customer_service.models import SupportCompanyAssignment


@pytest.fixture(scope="function")
def db_session():
    """提供測試用的資料庫 session（使用 in-memory SQLite）"""
    # 使用 in-memory SQLite 進行測試
    engine = create_engine("sqlite:///:memory:")
    
    # 只建立需要的表（避免 JSONB 等 PostgreSQL 特定類型）
    Tenant.__table__.create(engine, checkfirst=True)
    CompanyEntitlement.__table__.create(engine, checkfirst=True)
    SupportCompanyAssignment.__table__.create(engine, checkfirst=True)
    
    # 建立 session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    # 清理
    session.close()
    SupportCompanyAssignment.__table__.drop(engine, checkfirst=True)
    CompanyEntitlement.__table__.drop(engine, checkfirst=True)
    Tenant.__table__.drop(engine, checkfirst=True)
