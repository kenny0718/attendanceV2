"""Alembic 環境設定

WP-S1-02B: env.py Definitive Fix
本版本為正式版，涵蓋目前專案所有應由 Alembic 管理的 ORM 模組。

Metadata Strategy:
  - 所有模組均使用同一個 Base（app.core.database.Base）
  - 本檔案透過顯式 import 確保所有 ORM models 被登記到 Base.metadata
  - 不依賴中央 base.py（專案目前無此設計）

已納入模組（依 migration chain 順序）：
  - tenants:          Tenant, CompanyEntitlement
  - auth:             User, Membership, Role, Permission, RolePermission
  - notifications:    Notification
  - audit:            AuditRetentionPolicy, AuditLog
  - attendance:       AttendancePolicy, AttendanceSession, AttendancePunch,
                      AttendanceOutCheckpoint, AttendanceRecord, AllowedLocation
  - leave:            LeaveType, LeaveApprovalPolicy, LeaveRequest, LeaveApprovalLog
  - schedule:         ShiftTemplate, ShiftAssignment
  - customer_service: SupportCompanyAssignment

不納入模組：
  - backup: 無 ORM models.py，無 DB table，不屬於 Alembic 管理範圍
"""

from logging.config import fileConfig
import os
import sys
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# ---------------------------------------------------------------------------
# sys.path: 確保 backend/ 目錄在 import 路徑中
# ---------------------------------------------------------------------------
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

# ---------------------------------------------------------------------------
# 匯入 Base 與 settings
# ---------------------------------------------------------------------------
from app.core.database import Base  # noqa: E402
from app.core.config import settings  # noqa: E402

# ---------------------------------------------------------------------------
# 顯式匯入所有 ORM models（確保 Base.metadata 完整登記）
# 順序依 migration chain，方便維護時對照
# ---------------------------------------------------------------------------

# tenants（migration: 004, wp_11_04a）
from app.modules.tenants.models import (  # noqa: E402
    Tenant,
    CompanyEntitlement,
)

# auth（migration: 3532deda024c）
from app.modules.auth.models import (  # noqa: E402
    User,
    Membership,
    Role,
    Permission,
    RolePermission,
)

# notifications（migration: 005）
from app.modules.notifications.models import Notification  # noqa: E402

# audit（migration: 002, 003）
from app.modules.audit.models import (  # noqa: E402
    AuditRetentionPolicy,
    AuditLog,
)

# attendance（migration: 001b, 006, 007, 008）
from app.modules.attendance.models import (  # noqa: E402
    AttendancePolicy,
    AttendanceSession,
    AttendancePunch,
    AttendanceOutCheckpoint,
    AttendanceRecord,
    AllowedLocation,
)

# leave（migration: 009_wp_11_08）
from app.modules.leave.models import (  # noqa: E402
    LeaveType,
    LeaveApprovalPolicy,
    LeaveRequest,
    LeaveApprovalLog,
)

# schedule（migration: 010_wp_s1_02）
from app.modules.schedule.models import (  # noqa: E402
    ShiftTemplate,
    ShiftAssignment,
)

# customer_service（migration: wp_11_04a 含 support_company_assignments）
from app.modules.customer_service.models import SupportCompanyAssignment  # noqa: E402

# ---------------------------------------------------------------------------
# Alembic config
# ---------------------------------------------------------------------------
config = context.config

# 優先順序：
# 1. 呼叫端/測試注入的 DATABASE_URL
# 2. alembic.ini 的 sqlalchemy.url
# 3. settings.database_url 預設值
env_database_url = os.getenv("DATABASE_URL")
if env_database_url:
    config.set_main_option("sqlalchemy.url", env_database_url)
elif not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata：Alembic autogenerate 的依據
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Migration runners
# ---------------------------------------------------------------------------

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
