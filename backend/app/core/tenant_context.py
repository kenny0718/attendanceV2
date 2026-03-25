"""Tenant Context 管理

Phase 1 (legacy): X-Company-ID / X-User-ID header injection — RETIRED (A1-3c)
Phase 2+: JWT Actor via get_current_actor / get_actor_with_company (app.core.dependencies)

All legacy header dependency functions (get_current_company_id,
get_current_company_id_with_membership, get_current_user_id) have been
removed as of A1-3c. Use get_actor_with_company from app.core.dependencies.
"""

# This module is intentionally empty after A1-3c legacy header path retirement.
# See: docs/02_DEVELOPMENT_STATUS/A1-3C_BACKEND_TEST_LEGACY_HEADER_PATH_REMOVAL_COMPLETION_REPORT.md
