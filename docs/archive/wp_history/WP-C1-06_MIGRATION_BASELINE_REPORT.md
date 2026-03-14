# WP-C1-06 Migration Baseline 報告

**日期：** 2026-03-11  
**執行人：** WP-C1-06 自動驗證  

---

## A. Alembic Heads 驗證

```
$ alembic heads
008_wp_11_13 (head)
```

**結果：** ✅ 恰好一個 head：`008_wp_11_13`

---

## B. Migration Chain（alembic history）

```
007_wp_11_10 -> 008_wp_11_13 (head), WP-11-13: Create allowed_locations table and extend attendance_punches
006 -> 007_wp_11_10, WP-11-10: Create attendance_out_checkpoints table
wp_11_04a_entitlements -> 006, Expand session status for approval workflow
001b -> wp_11_04a_entitlements, Add company_entitlements and support_company_assignments tables
003 -> 001b, Create attendance domain v2 (FIXED: correct table order)
002 -> 003, create audit retention policies table
005 -> 002, create audit_logs table
3532deda024c -> 005, create notifications table
004 -> 3532deda024c, create auth tables v2 platform-first
<base> -> 004, create tenants table
```

**鏈節數：** 10  
**起點：** `<base> -> 004`（tenants）  
**終點：** `008_wp_11_13`（allowed_locations）  
**結果：** ✅ 單一連續鏈，無分支

---

## C. Head 確認

| 項目 | 期望值 | 實際值 | 狀態 |
|------|--------|--------|------|
| head revision | `008_wp_11_13` | `008_wp_11_13` | ✅ |
| head 數量 | 1 | 1 | ✅ |
| deprecated `001` 不在鏈中 | true | true | ✅ |
| `001b` 存在於鏈中 | true | true | ✅ |

---

## D. Migration Smoke Test 結果

```
$ pytest tests/test_migration_smoke.py -v

tests/test_migration_smoke.py::test_fresh_db_migration_smoke        PASSED
tests/test_migration_smoke.py::test_migration_chain_has_single_head PASSED
tests/test_migration_smoke.py::test_no_deprecated_migrations_in_chain PASSED

3 passed in 3.00s
```

### test_fresh_db_migration_smoke 驗證項目

對全新空資料庫執行 `alembic upgrade head`，確認以下表格均存在：

| 表格名稱 | 來源 Migration |
|----------|----------------|
| `tenants` | 004 |
| `users`, `roles`, `permissions`, `role_permissions`, `user_company_memberships` | 3532deda024c |
| `notifications` | 005 |
| `audit_logs` | 002 |
| `audit_retention_policies` | 003 |
| `attendance_policies`, `attendance_sessions`, `attendance_punches` | 001b |
| `company_entitlements`, `support_company_assignments` | wp_11_04a |
| `allowed_locations` | 008_wp_11_13 |
| `alembic_version` | alembic 內建 |

**alembic_version 驗證：** `008_wp_11_13` ✅

---

## E. 修正項目（既存問題，非 WP-C1 引入）

`tests/test_migration_smoke.py` 有兩個既存問題在本次修正：

| 問題 | 修正方式 |
|------|----------|
| `['alembic', ...]` 使用裸指令，`alembic` 不在 PATH → `FileNotFoundError` | 改用 `BACKEND_DIR/venv/bin/alembic` 完整路徑 |
| head 斷言為舊版 `wp_11_04a_entitlements` | 更新為當前 head `008_wp_11_13` |
| expected_tables 未含 `allowed_locations` | 新增 `allowed_locations`（migration 008 建立）|

---

## F. 現行 DB 狀態確認

```
$ alembic current
008_wp_11_13 (head)
```

生產資料庫已在最新 head，無待套用的 migration。

---

## G. 結論

- Migration chain 完整，無分支，無斷點
- Head 為 `008_wp_11_13`，符合預期
- Smoke test 全數通過（3/3）
- WP-C1 系列（認證遷移）未引入任何 schema 變更，migration chain 維持不變
