Gate 4 Final Acceptance Checklist (Auth)
0. Gate 4 範圍與硬規則

 登入流程固定：company selector → login_username → password

 email 僅通知用途：NOT login identifier

 users 為 global identity：users 無 company_id

 membership 表：user_company_memberships

 UNIQUE(company_id, login_username)

 UNIQUE(user_id, company_id)

 Anti-tenant enumeration：no membership ⇒ 404（視為 tenant 不存在）

 未引入 global email uniqueness

 未順手改動其他模組（非必要變更）

1. 交付物與文件
1.1 設計 / 合約文件（LOCKED）

 docs/AUTH_SCHEMA_SPEC_PLATFORM_FIRST_v2.md 存在且與實作一致

 docs/AUTH_MIGRATION_REWRITE_PLAN_WP-10-02B.md 存在且標記為 implementation baseline

 docs/WP-10-04_LOGIN_API_CONTRACT.md 存在且標記 🔒 Locked（error semantics、JWT claims、request/response schema 清楚）

 docs/GATE_PROGRESS_TRACKER.md 已更新：WP-10-02B、WP-10-03B、WP-10-04A、WP-10-04B 狀態正確

1.2 完成報告（可選但建議）

 WP-10-02B completion report

 WP-10-03B completion report

 WP-10-04A completion report

 WP-10-04B completion report

2. Migration 與資料庫結構驗收
2.1 Alembic 狀態

 alembic current 顯示在預期 head（例：3532deda024c）

 alembic upgrade head 成功

 alembic downgrade -1 成功

 alembic upgrade head 再次成功（可重複）

2.2 表與欄位（Schema）

 存在 5 張表：

 users

 roles

 permissions

 role_permissions

 user_company_memberships

 不存在 user_roles 表

users 表

 無 company_id

 無 username

 有 display_name

 email 不為 UNIQUE（允許重複）

user_company_memberships 表

 有 user_id FK → users.id

 有 company_id FK → tenants.id（型別一致）

 有 role_id FK → roles.id

 有 login_username

 UNIQUE(company_id, login_username)

 UNIQUE(user_id, company_id)

 有 index(company_id, login_username)（login 查詢用）

3. Auth 模組實作驗收
3.1 Models

 backend/app/modules/auth/models.py：

 User：global（無 company_id、無 username）

 Membership：承載 login_username、role_id、company_id

 Role/Permission/RolePermission 為 global（無 company_id）

 不再依賴 UserRole（或已移除）

3.2 Repository

 create_user() 不需要 company_id

 create_membership() 存在且是建立 user-company 關係的唯一入口（或主要入口）

 get_user_by_login(company_id, login_username) 透過 membership 查 user（不走 email）

 user_has_company_access(user_id, company_id) 存在且用於 membership 驗證

4. Tenant Context v2（安全核心）驗收

 backend/app/core/tenant_context.py：

 保留舊 get_current_company_id()（向後相容）

 新增 get_current_company_id_with_membership()（或等效功能）

 membership 驗證規則：

 tenant 不存在/不 active ⇒ 404（或統一 not found）

 membership 不存在 ⇒ 404

 membership inactive ⇒ 404

 錯誤訊息符合 anti-enumeration（不洩漏 tenant 存在性）

5. Login API（JWT）驗收
5.1 Endpoint 與 Router 註冊

 POST /api/internal/auth/login 存在

 backend/app/main.py 已 include auth router

 Path/Prefix 與 contract 一致（不漂移）

5.2 Request/Response 合約

 Request body：company_id, login_username, password

 Success response：access_token, token_type, user, company, role

5.3 JWT 規格

 HS256

 exp = 900 秒

 必要 claims：sub, company_id, role_id, iat, exp

 secret 來源為環境變數（例如 JWT_SECRET_KEY），未 hardcode

5.4 Error Semantics（照 contract）

 company 不存在 ⇒ 404 + "Invalid credentials"

 membership 不存在 ⇒ 404 + "Invalid credentials"

 membership inactive ⇒ 404 + "Invalid credentials"

 password 錯誤 ⇒ 401 + "Invalid credentials"

 缺欄位/空值 ⇒ 422 Validation Error

6. 測試驗收
6.1 Auth 測試

 pytest backend/app/modules/auth/tests/ -v 全綠

 test_login_api.py（13 tests）全綠

6.2 tenant_context 測試

 pytest backend/app/core/tests/test_tenant_context.py -v 全綠

6.3 Regression Suites

 attendance tests 全綠

 notifications tests 全綠

 backup tests 全綠

 audit tests 全綠

 pytest -q 全套全綠（你目前回報 137 passed）

7. 設定與部署安全檢查（最低限度）

 .env / 環境變數已設定 JWT_SECRET_KEY（長度足夠、非預設值）

 JWT_SECRET_KEY 不被 commit（不在 repo 內）

 README / docs 有說明如何設定 JWT secret（不暴露實際值）

8. Gate 4 最終結論（簽核）

 WP-10-02B ✅（platform-first v2 schema/migration）

 WP-10-03B ✅（tenant context membership validation + anti-enum）

 WP-10-04A ✅（contract locked + TDD red）

 WP-10-04B ✅（JWT login green + regression green）

 Gate 4 ✅ 可關閉，允許進入 Gate 5（Attendance 核心 / 後續 API）