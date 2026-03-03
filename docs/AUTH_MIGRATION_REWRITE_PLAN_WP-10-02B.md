Step 1 — Migration Rewrite Plan
1. Baseline Migration 策略
1.1 Migration 處理方式
刪除舊 migration： backend/alembic/versions/2167a6735c37_create_auth_tables.py
建立新 migration： 使用 alembic revision -m "create auth tables v2 platform-first" 生成新檔案
Revision 接續：
down_revision = '005' (仍接在 notifications migration 之後)
新 revision ID 由 Alembic 自動生成
維持 Gate 4 的位置，但 schema 完全改為 platform-first v2
1.2 Migration 命名
檔名格式：[new_revision_id]_create_auth_tables_v2_platform_first.py
Message："create auth tables v2 platform-first"
1.3 舊 Migration 處理
策略：直接刪除（因為未上線，無需保留歷史）
不移到 archive（保持 versions/ 乾淨）
Git commit message 明確標註 "replace tenant-first with platform-first v2"
2. v2 Schema 設計（依 AUTH_SCHEMA_SPEC_PLATFORM_FIRST_v2.md）
2.1 users 表（Global Identity）
變更：
❌ 移除 company_id 欄位
❌ 移除 username 欄位（登入名改由 membership.login_username 管理）
✅ 保留 email 欄位（通知用，不設 UNIQUE）
✅ 新增 display_name 欄位（全域顯示名稱）
最終欄位：
id (UUID PK)
display_name (VARCHAR 100, NOT NULL) - 全域顯示名稱
email (VARCHAR 255, NULLABLE) - 通知用，可重複
password_hash (VARCHAR 255, NOT NULL)
is_active (BOOLEAN, DEFAULT TRUE)
is_otp (BOOLEAN, DEFAULT FALSE)
must_change_password (BOOLEAN, DEFAULT FALSE)
last_login_at (TIMESTAMP, NULLABLE)
created_at (TIMESTAMP, NOT NULL)
updated_at (TIMESTAMP, NOT NULL)
Constraints：
PK: id
❌ 無 UNIQUE(email)
❌ 無 FK to tenants
Indexes：
idx_users_email on (email) - 查詢用，但不唯一
idx_users_is_active on (is_active)
2.2 user_company_memberships 表（核心新增）
用途：
管理 user ↔ company 關係
承載 per-company 登入識別（login_username）
承載角色（role_id，取代 user_roles）
欄位：
id (UUID PK)
user_id (UUID, NOT NULL, FK → users.id)
company_id (VARCHAR 255, NOT NULL, FK → tenants.id)
role_id (VARCHAR 50, NOT NULL, FK → roles.id)
login_username (VARCHAR 100, NOT NULL) - per-company 登入名
login_email (VARCHAR 255, NULLABLE) - per-company 通知 email（可選）
is_active (BOOLEAN, NOT NULL, DEFAULT TRUE)
created_at (TIMESTAMP, NOT NULL)
updated_at (TIMESTAMP, NOT NULL)
Constraints：
PK: id
UNIQUE: (company_id, login_username) - 同公司內登入名唯一
UNIQUE: (user_id, company_id) - 同 user 在同公司只能一筆 membership
FK: user_id → users.id (ON DELETE CASCADE)
FK: company_id → tenants.id (ON DELETE CASCADE)
FK: role_id → roles.id (ON DELETE CASCADE)
Indexes：
idx_memberships_company_login on (company_id, login_username) - 登入查詢
idx_memberships_user_id on (user_id) - 查詢 user 的所有 memberships
idx_memberships_company_id on (company_id) - 查詢公司的所有成員
idx_memberships_company_email on (company_id, login_email) - 若 login_email 存在
2.3 roles 表（保持不變）
狀態： ✅ 已符合 v2（global, 無 company_id）
欄位：
id (VARCHAR 50 PK)
name (VARCHAR 100)
description (TEXT, NULLABLE)
created_at (TIMESTAMP)
Seed： 保留 4 roles
employee
manager
company_admin
customer_service
2.4 permissions 表（保持不變）
狀態： ✅ 已符合 v2（global, 無 company_id）
欄位：
id (VARCHAR 100 PK)
resource (VARCHAR 50)
action (VARCHAR 50)
description (TEXT, NULLABLE)
created_at (TIMESTAMP)
Constraints：
UNIQUE(resource, action)
Indexes：
idx_permissions_resource on (resource)
Seed： 保留 11 permissions
2.5 role_permissions 表（保持不變）
狀態： ✅ 已符合 v2（global, 無 company_id）
欄位：
id (UUID PK)
role_id (VARCHAR 50, FK → roles.id)
permission_id (VARCHAR 100, FK → permissions.id)
created_at (TIMESTAMP)
Constraints：
UNIQUE(role_id, permission_id)
Indexes：
idx_role_permissions_role_id on (role_id)
Seed： 保留 20 mappings
2.6 user_roles 表（移除）
狀態： ❌ 不再建立此表
原因： 角色管理改由 user_company_memberships.role_id 承載
3. Compatibility Notes
3.1 已知依賴點
Auth Module 內部：
models.py - User model 有 company_id ❌
repo.py - 所有方法需要 company_id 參數 ❌
tests/test_repo.py - 14 個測試依賴 tenant-aware 邏輯 ❌
其他模組（可能受影響）：
tenant_context.py - 可能依賴 user.company_id 驗證 ⚠️
attendance module - 若有直接查詢 user.company_id ⚠️
3.2 最小修補策略
Auth Module（必須改）：
models.py
User: 移除 company_id, 移除 username, 新增 display_name
新增 Membership model
移除 UserRole model
repo.py
create_user() - 改為不需 company_id，只建立 global user
新增 create_membership() - 建立 user-company 關聯
get_user_by_username() - 改為 get_user_by_login(company_id, login_username) 透過 membership 查
新增 get_user_memberships(user_id) - 查詢 user 的所有公司
新增 user_has_company_access(user_id, company_id) - 驗證 membership
tests/test_repo.py
重寫 14 個測試：
改為先建立 user（global）
再建立 membership（含 login_username）
測試 per-company login_username unique
測試 membership 授權邏輯
測試 no membership => 無法查詢
其他模組（最小修補）：
tenant_context.py：若測試爆，只加 membership 驗證邏輯，不改其他
attendance tests：若爆，只調整 fixture 建立 membership，不改業務邏輯
3.3 不允許的變更
❌ 不改 attendance/notifications/backup/audit 的業務邏輯
❌ 不改 API routes（WP-10-04B 才做）
❌ 不改 tenant_context 的核心邏輯（除非測試必須）
❌ 不優化其他模組
4. Migration 執行順序
4.1 Upgrade 順序
建立 roles 表 + seed
建立 permissions 表 + seed
建立 users 表（v2 schema）
建立 user_company_memberships 表
建立 role_permissions 表 + seed
4.2 Downgrade 順序（反向）
Drop role_permissions
Drop user_company_memberships
Drop users
Drop permissions
Drop roles
5. Seed 策略（Idempotent）
保持與舊 migration 相同：
使用 SELECT COUNT(*) WHERE id = :id 檢查存在性
僅在不存在時 INSERT
確保 downgrade/upgrade 可重複執行
Seed 內容：
4 roles
11 permissions
20 role-permission mappings
6. 驗收檢查點
6.1 Migration 驗收
[ ] alembic current 顯示 005
[ ] alembic upgrade head 成功，顯示新 revision
[ ] alembic current 顯示新 revision (head)
[ ] 資料庫有 5 張表：users, roles, permissions, user_company_memberships, role_permissions
[ ] 資料庫無 user_roles 表
[ ] users 表無 company_id 欄位
[ ] users 表無 username 欄位
[ ] users.email 無 UNIQUE constraint
[ ] user_company_memberships 有 UNIQUE(company_id, login_username)
[ ] user_company_memberships 有 UNIQUE(user_id, company_id)
[ ] alembic downgrade -1 成功
[ ] alembic upgrade head 再次成功（idempotent）
6.2 Code 驗收
[ ] backend/app/modules/auth/models.py 有 User, Membership, Role, Permission, RolePermission
[ ] backend/app/modules/auth/repo.py 有 membership 相關方法
[ ] pytest app/modules/auth/tests/ -v 全綠
6.3 Regression 驗收
[ ] pytest app/modules/attendance/tests/ -q 全綠
[ ] pytest app/modules/notifications/tests/ -q 全綠
[ ] pytest app/modules/backup/tests/ -q 全綠
[ ] pytest app/modules/audit/tests/ -q 全綠
7. 風險緩解
7.1 High Risk - Migration 失敗
緩解： 先在 dev DB 測試 upgrade/downgrade 多次
回滾： 若失敗，git revert 並恢復舊 migration
7.2 High Risk - Auth Tests 全爆
緩解： 先改 models/repo，再逐一修復測試
策略： 保留測試意圖，只改資料建立方式
7.3 Medium Risk - Attendance Tests 爆
緩解： 只調整 fixture，不改業務邏輯
策略： 在 fixture 中建立 membership
