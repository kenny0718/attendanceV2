"""Migration Smoke Test

Tests that alembic upgrade head works on a fresh database.
This is the most important test to prevent migration chain breakage.

WP-11-04A Clean Rebuild: Ensures no manual SQL workarounds are needed.
WP-C1-06: Updated head assertion to 008_wp_11_13, use venv alembic path.
"""

import subprocess
import os
from pathlib import Path
from sqlalchemy import create_engine, text

# Determine backend directory from this file's location
# This ensures the test works regardless of where pytest is invoked from
BACKEND_DIR = Path(__file__).parent.parent.resolve()

# Use venv alembic to avoid FileNotFoundError when alembic is not in PATH
ALEMBIC_BIN = str(BACKEND_DIR / "venv" / "bin" / "alembic")

# Current migration head
EXPECTED_HEAD = "014_add_tax_id_to_tenants"


def test_fresh_db_migration_smoke():
    """
    Test that 'alembic upgrade head' succeeds on a completely empty database.

    This test:
    1. Creates a temporary test database
    2. Runs alembic upgrade head
    3. Verifies all expected tables exist
    4. Cleans up

    This is the PRIMARY defense against migration chain breakage.
    If this test fails, DO NOT merge the PR.
    """
    test_db_name = "attendance_migration_smoke_test"
    base_url = "postgresql+psycopg2://postgres:Raxcxtjq260!@127.0.0.1:5432"
    test_db_url = f"{base_url}/{test_db_name}"

    admin_engine = create_engine(f"{base_url}/postgres")
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
        conn.execute(text(f"CREATE DATABASE {test_db_name}"))
    admin_engine.dispose()

    try:
        env = os.environ.copy()
        env["DATABASE_URL"] = test_db_url

        result = subprocess.run(
            [ALEMBIC_BIN, "upgrade", "head"],
            cwd=str(BACKEND_DIR),
            env=env,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Migration failed:\n{result.stderr}"

        test_engine = create_engine(test_db_url)
        with test_engine.connect() as conn:
            tables_result = conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
            )
            tables = {row[0] for row in tables_result}

            expected_tables = {
                "alembic_version",
                "tenants",
                "users",
                "roles",
                "permissions",
                "role_permissions",
                "user_company_memberships",
                "notifications",
                "audit_logs",
                "audit_retention_policies",
                "attendance_policies",
                "attendance_sessions",
                "attendance_punches",
                "company_entitlements",
                "support_company_assignments",
                "allowed_locations",
                "leave_types",
                "leave_approval_policies",
                "leave_requests",
                "leave_approval_logs",
                "shift_templates",
                "shift_assignments",
                "shift_segments",
            }

            missing_tables = expected_tables - tables
            assert not missing_tables, f"Missing tables: {missing_tables}"

            version_result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = version_result.scalar()
            assert version == EXPECTED_HEAD, f"Expected head '{EXPECTED_HEAD}', got '{version}'"

        test_engine.dispose()

    finally:
        admin_engine = create_engine(f"{base_url}/postgres")
        with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
        admin_engine.dispose()


def test_migration_chain_has_single_head():
    """Verify that alembic heads returns exactly one head."""
    result = subprocess.run(
        [ALEMBIC_BIN, "heads"],
        cwd=str(BACKEND_DIR),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"alembic heads failed:\n{result.stderr}"

    heads = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
    assert len(heads) == 1, f"Expected 1 head, found {len(heads)}: {heads}"
    assert EXPECTED_HEAD in heads[0], f"Expected {EXPECTED_HEAD} head, got: {heads[0]}"


def test_no_deprecated_migrations_in_chain():
    """Verify that deprecated migration 001 is not in the active chain."""
    result = subprocess.run(
        [ALEMBIC_BIN, "history"],
        cwd=str(BACKEND_DIR),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"alembic history failed:\n{result.stderr}"
    assert "001b" in result.stdout, "001b (fixed migration) should be in history"
    assert " -> 001 " not in result.stdout, "001 (deprecated) should NOT be in active chain"
