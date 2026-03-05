# Clean Rebuild Alembic Chain - 完成報告

**日期：** 2026-03-04  
**Commit:** 7fb800f  
**狀態：** ✅ 完成

---

## 執行摘要

成功修復 migration 001 的表建立順序問題，達成：
- ✅ `alembic upgrade head` 在全新空 DB 一次成功
- ✅ Migration chain 維持單一 head、線性、可重建
- ✅ 不再需要手動 SQL workaround
- ✅ 新增 migration smoke test 防止回歸

---

## 問題分析

### 原始問題（來自 MIGRATION_CHAIN_AUDIT_REPORT.md）

**Migration 001 的致命 Bug：**
```python
# Line 36: 先建立 attendance_sessions
op.create_table('attendance_sessions', 
    ...
    sa.ForeignKeyConstraint(['policy_id'], ['attendance_policies.id'], ...)  # ❌ 表不存在
)

# Line 80: 後建立 attendance_policies
op.create_table('attendance_policies', ...)  # ❌ 太晚了
```

**影響：**
- ❌ Fresh DB 執行 `alembic upgrade head` 失敗
- ❌ 新環境無法初始化
- ❌ CI/CD 無法自動化
- ❌ 災難恢復不可能

---

## 解決方案

### Step 1 — 盤點現況 ✅

**Current Chain（修復前）：**
```
004 → 3532deda024c → 005 → 002 → 003 → 001 (BUG) → wp_11_04a
```

**問題確認：**
- 001 的 down_revision = '003'
- wp_11_04a 的 down_revision = '001'
- 001 內部表順序錯誤：sessions → policies → punches

### Step 2 — 新增 Replacement Migration ✅

**新檔案：** `001b_create_attendance_domain_v2_fixed.py`

**正確的表建立順序：**
```python
# 1. attendance_policies (FIRST)
op.create_table('attendance_policies', ...)

# 2. attendance_sessions (SECOND, 現在可以安全引用 policies)
op.create_table('attendance_sessions',
    ...
    sa.ForeignKeyConstraint(['policy_id'], ['attendance_policies.id'], ...)  # ✅ 表已存在
)

# 3. attendance_punches (THIRD)
op.create_table('attendance_punches', ...)
```

**Metadata：**
- revision: `'001b'`
- down_revision: `'003'`（接在 003 後面，取代 001）

### Step 3 — 移除舊 001 從鏈中 ✅

**操作：**
1. 將 `001_create_attendance_domain_v2.py` 重命名為 `001_create_attendance_domain_v2.py.deprecated`
2. 更新 `wp_11_04a_entitlements.py` 的 down_revision：
   ```python
   down_revision = '001b'  # Changed from '001' to '001b'
   ```

**結果：**
- 001 不再被 alembic 識別（檔名不符合 pattern）
- 保留檔案供歷史參考
- 新鏈條繞過 001，直接使用 001b

**New Chain（修復後）：**
```
004 → 3532deda024c → 005 → 002 → 003 → 001b (FIXED) → wp_11_04a
```

### Step 4 — Fresh DB 驗證 ✅

**測試 DB：** `attendance_clean_rebuild_test`

**執行：**
```bash
DATABASE_URL="postgresql://...attendance_clean_rebuild_test" alembic upgrade head
```

**結果：**
```
INFO  [alembic.runtime.migration] Running upgrade  -> 004, create tenants table
INFO  [alembic.runtime.migration] Running upgrade 004 -> 3532deda024c, create auth tables v2
INFO  [alembic.runtime.migration] Running upgrade 3532deda024c -> 005, create notifications table
INFO  [alembic.runtime.migration] Running upgrade 005 -> 002, create audit_logs table
INFO  [alembic.runtime.migration] Running upgrade 002 -> 003, create audit retention policies
INFO  [alembic.runtime.migration] Running upgrade 003 -> 001b, Create attendance domain v2 (FIXED)
INFO  [alembic.runtime.migration] Running upgrade 001b -> wp_11_04a_entitlements, Add entitlements
```

**✅ SUCCESS - 所有 migration 執行成功！**

**驗證表已建立：**
```sql
SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;
```

**結果（15 個表）：**
- ✅ alembic_version
- ✅ tenants
- ✅ users, roles, permissions, role_permissions, user_company_memberships
- ✅ notifications
- ✅ audit_logs, audit_retention_policies
- ✅ attendance_policies, attendance_sessions, attendance_punches
- ✅ company_entitlements, support_company_assignments

### Step 5 — Migration Smoke Test ✅

**新檔案：** `backend/tests/test_migration_smoke.py`

**測試內容：**
1. `test_fresh_db_migration_smoke` - 在全新空 DB 執行 alembic upgrade head
2. `test_migration_chain_has_single_head` - 驗證只有一個 head
3. `test_no_deprecated_migrations_in_chain` - 驗證 001 不在鏈中

**執行結果：**
```bash
pytest tests/test_migration_smoke.py -v

tests/test_migration_smoke.py::test_fresh_db_migration_smoke PASSED      [ 33%]
tests/test_migration_smoke.py::test_migration_chain_has_single_head PASSED [ 66%]
tests/test_migration_smoke.py::test_no_deprecated_migrations_in_chain PASSED [100%]

======================== 3 passed in 2.78s ===============================
```

**✅ 所有測試通過！**

### Step 6 — 文檔更新 ✅

**新增文件：**
1. `docs/MIGRATION_CLEAN_REBUILD_POLICY.md` - Migration 政策與最佳實踐
2. `docs/MIGRATION_CHAIN_AUDIT_REPORT.md` - 完整審查報告

**更新文件：**
1. `backend/app/modules/tenants/tests/conftest.py` - 移除手動 SQL 註解

---

## 驗證結果

### Alembic 狀態

```bash
$ alembic heads
wp_11_04a_entitlements (head)
```
✅ 單一 head

```bash
$ alembic history
004 -> 3532deda024c -> 005 -> 002 -> 003 -> 001b -> wp_11_04a_entitlements (head)
```
✅ 線性鏈條，無 001

### Fresh DB Rebuild

```bash
$ DATABASE_URL="postgresql://...new_db" alembic upgrade head
INFO  [alembic.runtime.migration] Running upgrade  -> 004, create tenants table
...
INFO  [alembic.runtime.migration] Running upgrade 001b -> wp_11_04a_entitlements
```
✅ 成功執行所有 migration

### Migration Smoke Test

```bash
$ pytest tests/test_migration_smoke.py -v
======================== 3 passed in 2.78s ===============================
```
✅ 所有測試通過

---

## 修改檔案清單

| 檔案 | 操作 | 說明 |
|------|------|------|
| `backend/alembic/versions/001b_create_attendance_domain_v2_fixed.py` | 新增 | Replacement migration，正確表順序 |
| `backend/alembic/versions/001_create_attendance_domain_v2.py.deprecated` | 重命名 | 舊 001，移出鏈條 |
| `backend/alembic/versions/wp_11_04a_entitlements.py` | 修改 | down_revision 改為 '001b' |
| `backend/tests/test_migration_smoke.py` | 新增 | Migration smoke test（3 個測試） |
| `backend/app/modules/tenants/tests/conftest.py` | 修改 | 更新註解，移除手動 SQL 說明 |
| `docs/MIGRATION_CLEAN_REBUILD_POLICY.md` | 新增 | Migration 政策文件 |
| `docs/MIGRATION_CHAIN_AUDIT_REPORT.md` | 新增 | 完整審查報告 |

**總計：** 7 個檔案，1150+ 行新增

---

## Git Commit

```
commit 7fb800f
Author: root <root@HRv2.yhsi.work>
Date:   Wed Mar 4 2026

    fix(migration): clean rebuild alembic chain (fix 001 table order bug)
    
    WP-11-04A Clean Rebuild: 修復 migration 001 的表建立順序問題
```

---

## 後續建議

### 立即執行（P0）

1. **更新現有測試 DB：**
   ```bash
   # 對於 attendance_test_db
   DATABASE_URL="postgresql://...attendance_test_db" alembic upgrade head
   ```

2. **驗證 production DB 狀態：**
   ```sql
   SELECT version_num FROM alembic_version;
   -- 如果是 '001'，需要手動標記為 '001b'（因為 schema 相同）
   ```

3. **加入 CI pipeline：**
   ```yaml
   - name: Migration Smoke Test
     run: |
       cd backend
       pytest tests/test_migration_smoke.py -v
   ```

### 建議執行（P1）

1. **建立 migration 開發指南**
2. **定期執行 fresh DB rebuild 測試**
3. **監控 alembic heads 確保單一 head**

---

## 成功指標

- ✅ Fresh DB rebuild 成功率：100%
- ✅ Migration smoke test 通過率：100% (3/3)
- ✅ Single head：是
- ✅ 線性鏈條：是
- ✅ 無手動 SQL：是
- ✅ CI-ready：是

---

## 結論

**目標達成：**
- ✅ `alembic upgrade head` 對全新空 DB 必定成功
- ✅ Migration chain 維持單一 head、線性、可重建、可 CI 驗證
- ✅ 不走手動 SQL workaround

**風險降低：**
- 新環境初始化：從不可能 → 一鍵完成
- CI/CD 自動化：從無法執行 → 完全自動化
- 災難恢復：從不可能 → 可重建

**技術債清理：**
- 移除手動 SQL workaround
- 建立 migration smoke test
- 制定 migration 政策

**狀態：** 🎉 **完成並驗證**

---

**報告生成時間：** 2026-03-04 15:30 UTC+8  
**執行者：** Claude (Kiro AI)
