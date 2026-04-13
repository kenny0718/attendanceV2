"""Test Migration Upgrade/Downgrade

WP-11-01 Phase B: Test Category 2 - Migration Tests
- Test migration upgrade creates all tables
- Test migration downgrade removes all tables
- Test indexes are created
- Test constraints are created
"""

import pytest
from sqlalchemy import create_engine, inspect, text
from alembic.config import Config
from alembic import command


# Test database setup
TEST_DATABASE_URL = "postgresql://attendance_user:attendance_pass@localhost:5432/attendance_test"
engine = create_engine(TEST_DATABASE_URL)
ATTENDANCE_DOMAIN_PRE_REVISION = "003"


@pytest.fixture(scope="function")
def alembic_config():
    """Create Alembic config for testing"""
    config = Config("/opt/attendance-system/backend/alembic.ini")
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    return config


@pytest.fixture(scope="function")
def clean_database():
    """Clean database before and after test"""
    # Drop all tables before test
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()
    
    yield
    
    # Drop all tables after test
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()


class TestMigrationUpgrade:
    """Test migration upgrade"""
    
    def test_migration_upgrade_creates_tables(self, alembic_config, clean_database):
        """測試：migration upgrade 成功建立所有 tables"""
        # Run upgrade to head
        command.upgrade(alembic_config, "head")
        
        # Verify tables exist
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        assert "attendance_sessions" in tables
        assert "attendance_punches" in tables
        assert "attendance_policies" in tables
    
    def test_migration_creates_sessions_table_columns(self, alembic_config, clean_database):
        """測試：attendance_sessions 表有正確的欄位"""
        command.upgrade(alembic_config, "head")
        
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('attendance_sessions')}
        
        # Verify required columns exist
        assert 'id' in columns
        assert 'company_id' in columns
        assert 'user_id' in columns
        assert 'punch_in_time' in columns
        assert 'punch_out_time' in columns
        assert 'status' in columns
        assert 'duration_minutes' in columns
        assert 'policy_id' in columns
        assert 'notes' in columns
        assert 'created_at' in columns
        assert 'updated_at' in columns
        
        # Verify nullable constraints
        assert columns['company_id']['nullable'] is False
        assert columns['user_id']['nullable'] is False
        assert columns['punch_in_time']['nullable'] is False
        assert columns['punch_out_time']['nullable'] is True
        assert columns['status']['nullable'] is False
    
    def test_migration_creates_punches_table_columns(self, alembic_config, clean_database):
        """測試：attendance_punches 表有正確的欄位"""
        command.upgrade(alembic_config, "head")
        
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('attendance_punches')}
        
        # Verify required columns exist
        assert 'id' in columns
        assert 'session_id' in columns
        assert 'company_id' in columns
        assert 'user_id' in columns
        assert 'punch_type' in columns
        assert 'punch_time' in columns
        assert 'ip_address' in columns
        assert 'user_agent' in columns
        assert 'location_lat' in columns
        assert 'location_lng' in columns
        assert 'device_id' in columns
        assert 'photo_url' in columns
        assert 'notes' in columns
        assert 'created_at' in columns
        
        # Verify nullable constraints
        assert columns['session_id']['nullable'] is False
        assert columns['company_id']['nullable'] is False
        assert columns['user_id']['nullable'] is False
        assert columns['punch_type']['nullable'] is False
        assert columns['punch_time']['nullable'] is False
        assert columns['ip_address']['nullable'] is True
    
    def test_migration_creates_policies_table_columns(self, alembic_config, clean_database):
        """測試：attendance_policies 表有正確的欄位"""
        command.upgrade(alembic_config, "head")
        
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('attendance_policies')}
        
        # Verify required columns exist
        assert 'id' in columns
        assert 'company_id' in columns
        assert 'name' in columns
        assert 'description' in columns
        assert 'work_start_time' in columns
        assert 'work_end_time' in columns
        assert 'grace_period_minutes' in columns
        assert 'overtime_threshold_minutes' in columns
        assert 'is_active' in columns
        assert 'is_default' in columns
        assert 'created_at' in columns
        assert 'updated_at' in columns
        
        # Verify nullable constraints
        assert columns['company_id']['nullable'] is False
        assert columns['name']['nullable'] is False
        assert columns['work_start_time']['nullable'] is False
        assert columns['work_end_time']['nullable'] is False
    
    def test_migration_creates_indexes(self, alembic_config, clean_database):
        """測試：migration 建立所有必要的 indexes"""
        command.upgrade(alembic_config, "head")
        
        inspector = inspect(engine)
        
        # Check attendance_sessions indexes
        sessions_indexes = {idx['name']: idx for idx in inspector.get_indexes('attendance_sessions')}
        assert 'idx_sessions_company_id' in sessions_indexes
        assert 'idx_sessions_user_id' in sessions_indexes
        assert 'idx_sessions_company_user' in sessions_indexes
        assert 'idx_sessions_company_punch_in' in sessions_indexes
        assert 'uq_sessions_company_user_open' in sessions_indexes
        
        # Verify unique constraint
        assert sessions_indexes['uq_sessions_company_user_open']['unique'] is True
        
        # Check attendance_punches indexes
        punches_indexes = {idx['name']: idx for idx in inspector.get_indexes('attendance_punches')}
        assert 'idx_punches_session_id' in punches_indexes
        assert 'idx_punches_company_id' in punches_indexes
        assert 'idx_punches_user_id' in punches_indexes
        assert 'idx_punches_company_time' in punches_indexes
        
        # Check attendance_policies indexes
        policies_indexes = {idx['name']: idx for idx in inspector.get_indexes('attendance_policies')}
        assert 'idx_policies_company_id' in policies_indexes
        assert 'idx_policies_company_active' in policies_indexes
        assert 'uq_policies_company_default' in policies_indexes
        
        # Verify unique constraint
        assert policies_indexes['uq_policies_company_default']['unique'] is True
    
    def test_migration_creates_foreign_keys(self, alembic_config, clean_database):
        """測試：migration 建立所有 foreign keys"""
        command.upgrade(alembic_config, "head")
        
        inspector = inspect(engine)
        
        # Check attendance_sessions foreign keys
        sessions_fks = inspector.get_foreign_keys('attendance_sessions')
        fk_tables = [fk['referred_table'] for fk in sessions_fks]
        assert 'tenants' in fk_tables
        assert 'users' in fk_tables
        assert 'attendance_policies' in fk_tables
        
        # Check attendance_punches foreign keys
        punches_fks = inspector.get_foreign_keys('attendance_punches')
        fk_tables = [fk['referred_table'] for fk in punches_fks]
        assert 'attendance_sessions' in fk_tables
        assert 'tenants' in fk_tables
        assert 'users' in fk_tables
        
        # Check attendance_policies foreign keys
        policies_fks = inspector.get_foreign_keys('attendance_policies')
        fk_tables = [fk['referred_table'] for fk in policies_fks]
        assert 'tenants' in fk_tables
    
    def test_migration_creates_check_constraints(self, alembic_config, clean_database):
        """測試：migration 建立 check constraints"""
        command.upgrade(alembic_config, "head")
        
        inspector = inspect(engine)
        
        # Check attendance_sessions check constraints
        sessions_checks = inspector.get_check_constraints('attendance_sessions')
        check_names = [ck['name'] for ck in sessions_checks]
        assert 'ck_sessions_status' in check_names
        
        # Check attendance_punches check constraints
        punches_checks = inspector.get_check_constraints('attendance_punches')
        check_names = [ck['name'] for ck in punches_checks]
        assert 'ck_punches_type' in check_names


class TestMigrationDowngrade:
    """Test migration downgrade"""
    
    def test_migration_downgrade_removes_tables(self, alembic_config, clean_database):
        """測試：migration downgrade 成功刪除 attendance domain tables"""
        # Run upgrade first
        command.upgrade(alembic_config, "head")
        
        # Verify tables exist
        inspector = inspect(engine)
        tables_before = inspector.get_table_names()
        assert "attendance_sessions" in tables_before
        assert "attendance_punches" in tables_before
        assert "attendance_policies" in tables_before
        
        # Run downgrade to before attendance domain was introduced
        command.downgrade(alembic_config, ATTENDANCE_DOMAIN_PRE_REVISION)
        
        # Verify attendance tables removed
        inspector = inspect(engine)
        tables_after = inspector.get_table_names()
        assert "attendance_sessions" not in tables_after
        assert "attendance_punches" not in tables_after
        assert "attendance_policies" not in tables_after
    
    def test_migration_upgrade_downgrade_idempotent(self, alembic_config, clean_database):
        """測試：migration upgrade/downgrade 可以重複執行"""
        # Upgrade
        command.upgrade(alembic_config, "head")
        inspector = inspect(engine)
        assert "attendance_sessions" in inspector.get_table_names()
        
        # Downgrade to before attendance domain was introduced
        command.downgrade(alembic_config, ATTENDANCE_DOMAIN_PRE_REVISION)
        inspector = inspect(engine)
        assert "attendance_sessions" not in inspector.get_table_names()
        
        # Upgrade again
        command.upgrade(alembic_config, "head")
        inspector = inspect(engine)
        assert "attendance_sessions" in inspector.get_table_names()
        
        # Downgrade again
        command.downgrade(alembic_config, ATTENDANCE_DOMAIN_PRE_REVISION)
        inspector = inspect(engine)
        assert "attendance_sessions" not in inspector.get_table_names()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
