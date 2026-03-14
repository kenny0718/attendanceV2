# Reality Audit — Next Actions（下一步行動）

**審查日期：** 2026-03-04  
**基於：** REALITY_AUDIT_RISK_REPORT.md  
**目標：** 提供可執行的工作包，優先處理 P0 風險

---

## 工作包優先順序

| WP ID | 名稱 | 優先度 | 預估時間 | 依賴 |
|-------|------|--------|----------|------|
| WP-RA-01 | Migration Chain 驗證與修正 | P0 | 2-4 小時 | 無 |
| WP-RA-02 | 測試 DB 狀態驗證與重建 | P0 | 2-4 小時 | WP-RA-01 |
| WP-RA-03 | 執行完整測試套件 | P0 | 1-2 小時 | WP-RA-02 |
| WP-RA-04 | Auth 轉換決策與計畫 | P0 | 4-8 小時 | WP-RA-03 |
| WP-RA-05 | 文件同步更新 | P1 | 2-3 小時 | WP-RA-03 |
| WP-RA-06 | Migration 001 清理 | P1 | 1 小時 | WP-RA-01 |
| WP-RA-07 | 建立 Fresh DB 驗證流程 | P1 | 2-3 小時 | WP-RA-01 |

---

## WP-RA-01 — Migration Chain 驗證與修正

### Goal
驗證 migration chain 可在全新環境執行，確保 001b 正確取代 001。

### Scope（允許改哪些資料夾/檔案）
- ✅ `backend/alembic/versions/` (檢視、可能刪除 001)
- ✅ `docs/MIGRATION_CHAIN_AUDIT_REPORT.md` (更新驗證結果)
- ⛔ 不修改其他 migration 檔案（除非發現新 bug）

### Definition of Done（可驗收條件）
- [ ] 確認 001 (舊版) 是否存在於 repo
- [ ] 確認實際 DB 的 `alembic_version` 狀態
- [ ] 在全新測試 DB 執行 `alembic upgrade head` 成功
- [ ] 驗證所有預期 tables 都已建立
- [ ] 驗證 `alembic heads` 只顯示一個 head
- [ ] 更新 MIGRATION_CHAIN_AUDIT_REPORT.md 記錄驗證結果

### Tests（要新增/維持什麼測試）
- 新增：`backend/tests/test_migrations.py`
  - `test_fresh_db_migration()`: 測試 fresh DB 可執行 alembic upgrade head
  - `test_single_head()`: 測試只有一個 head
  - `test_all_tables_exist()`: 測試所有預期 tables 存在

### 執行步驟

#### Step 1: 檢查 001 是否存在
```bash
cd /opt/attendance-system/backend
ls -la alembic/versions/001_*.py
```

**預期結果：**
- 如果只有 `001b_create_attendance_domain_v2_fixed.py`：✅ OK
- 如果有 `001_create_attendance_domain_v2.py`：⚠️ 需處理

**處理方式（如果 001 存在）：**
```bash
# 選項 A: 刪除 001 (如果確定沒有 DB 套用過)
rm alembic/versions/001_create_attendance_domain_v2.py

# 選項 B: 重新命名為 .bak
mv alembic/versions/001_create_attendance_domain_v2.py \
   alembic/versions/001_create_attendance_domain_v2.py.deprecated
```

#### Step 2: 檢查實際 DB 狀態
```bash
# 連線到實際 DB
psql -d attendance_db -c "SELECT * FROM alembic_version;"

# 檢查 attendance tables 是否存在
psql -d attendance_db -c "\dt attendance_*"
```

**預期結果：**
- `alembic_version` 應該包含 `wp_11_04a_entitlements`
- 應該有 3 個 attendance tables: policies, sessions, punches

**如果 alembic_version 顯示 001：**
```sql
-- 手動更新為 001b
UPDATE alembic_version SET version_num = '001b' WHERE version_num = '001';
```

#### Step 3: 建立全新測試 DB 驗證
```bash
# 建立全新 DB
createdb attendance_migration_test

# 執行 migration
DATABASE_URL="postgresql://postgres:Raxcxtjq260!@127.0.0.1:5432/attendance_migration_test" \
  alembic upgrade head

# 檢查結果
psql -d attendance_migration_test -c "SELECT * FROM alembic_version;"
psql -d attendance_migration_test -c "\dt"
```

**預期結果：**
- `alembic upgrade head` 執行成功，無錯誤
- `alembic_version` 包含 `wp_11_04a_entitlements`
- 所有 14 個 tables 都存在

#### Step 4: 驗證 single head
```bash
alembic heads
```

**預期結果：**
```
wp_11_04a_entitlements (head)
```

#### Step 5: 清理測試 DB
```bash
dropdb attendance_migration_test
```

### Risk / Rollback Note
- **風險：** 如果刪除 001，但有 DB 已套用 001，可能造成 alembic 混亂
- **Rollback：** 保留 001 的備份（.bak），如果出問題可還原
- **建議：** 先在測試環境驗證，再套用到生產

---

## WP-RA-02 — 測試 DB 狀態驗證與重建

### Goal
確保測試 DB 的 schema 與 migration 定義一致，修正手動 SQL 造成的不一致。

### Scope（允許改哪些資料夾/檔案）
- ✅ 測試 DB (attendance_test_db)
- ✅ `backend/conftest.py` (檢視，可能修改)
- ✅ `backend/app/conftest.py` (檢視，可能修改)
- ✅ 各模組的 `conftest.py` (檢視)
- ⛔ 不修改 migration 檔案

### Definition of Done（可驗收條件）
- [ ] 檢查測試 DB 的 `alembic_version` 狀態
- [ ] 比對測試 DB schema 與 fresh DB schema
- [ ] 如果不一致，重建測試 DB
- [ ] 檢視所有 conftest.py，確認沒有跳 migration 或手動 SQL
- [ ] 更新 conftest.py 使用正確的 DB setup 方式

### Tests（要新增/維持什麼測試）
- 維持：所有現有測試應該在新測試 DB 上通過

### 執行步驟

#### Step 1: 檢查測試 DB 狀態
```bash
# 檢查 alembic_version
psql -d attendance_test_db -c "SELECT * FROM alembic_version;"

# 匯出 schema
pg_dump -s -d attendance_test_db > /tmp/test_db_schema.sql
```

#### Step 2: 建立 fresh DB 作為基準
```bash
createdb attendance_fresh_baseline
DATABASE_URL="postgresql://postgres:Raxcxtjq260!@127.0.0.1:5432/attendance_fresh_baseline" \
  alembic upgrade head
pg_dump -s -d attendance_fresh_baseline > /tmp/fresh_db_schema.sql
```

#### Step 3: 比對 schema
```bash
diff /tmp/test_db_schema.sql /tmp/fresh_db_schema.sql
```

**如果有差異：**
- 記錄差異內容
- 決定是否需要重建測試 DB

#### Step 4: 重建測試 DB（如果需要）
```bash
# 備份測試資料（如果有重要資料）
pg_dump -d attendance_test_db > /tmp/test_db_backup.sql

# 刪除並重建
dropdb attendance_test_db
createdb attendance_test_db
DATABASE_URL="postgresql://postgres:Raxcxtjq260!@127.0.0.1:5432/attendance_test_db" \
  alembic upgrade head
```

#### Step 5: 檢視 conftest.py
```bash
cd /opt/attendance-system/backend
cat conftest.py
cat app/conftest.py
find app/modules -name "conftest.py" -exec echo "=== {} ===" \; -exec cat {} \;
```

**檢查項目：**
- [ ] 是否有 `Base.metadata.create_all()`？（應該用 alembic）
- [ ] 是否有手動 SQL？（應該避免）
- [ ] 是否有跳過某些 migration？（應該避免）
- [ ] DB fixture 如何建立？（應該用 alembic upgrade）

#### Step 6: 清理
```bash
dropdb attendance_fresh_baseline
rm /tmp/test_db_schema.sql /tmp/fresh_db_schema.sql
```

### Risk / Rollback Note
- **風險：** 重建測試 DB 會遺失測試資料
- **Rollback：** 已備份到 `/tmp/test_db_backup.sql`
- **建議：** 測試 DB 應該可隨時重建，不應依賴手動資料

---

## WP-RA-03 — 執行完整測試套件

### Goal
驗證所有測試可執行，記錄通過率與失敗原因。

### Scope（允許改哪些資料夾/檔案）
- ✅ `backend/` (執行測試)
- ✅ 新增 `docs/TEST_EXECUTION_REPORT.md` (記錄結果)
- ⛔ 不修改測試程式碼（除非是明顯的 import error）

### Definition of Done（可驗收條件）
- [ ] 執行 `pytest --collect-only` 成功
- [ ] 執行 `pytest -v` 並記錄結果
- [ ] 記錄通過/失敗/跳過的測試數量
- [ ] 記錄失敗測試的錯誤訊息
- [ ] 產出 TEST_EXECUTION_REPORT.md

### Tests（要新增/維持什麼測試）
- 維持：所有現有測試

### 執行步驟

#### Step 1: 測試收集
```bash
cd /opt/attendance-system/backend
python -m pytest --collect-only 2>&1 | tee /tmp/pytest_collect.log
```

**檢查：**
- 是否有 import errors？
- 收集到多少測試？

#### Step 2: 執行測試
```bash
python -m pytest -v --tb=short 2>&1 | tee /tmp/pytest_run.log
```

#### Step 3: 分析結果
```bash
# 統計
grep -E "passed|failed|skipped|error" /tmp/pytest_run.log | tail -1

# 失敗測試
grep "FAILED" /tmp/pytest_run.log
```

#### Step 4: 產出報告
建立 `docs/TEST_EXECUTION_REPORT.md`：
```markdown
# Test Execution Report

**日期：** 2026-03-04
**環境：** attendance_test_db

## 統計

- 總測試數：XX
- 通過：XX
- 失敗：XX
- 跳過：XX

## 失敗測試

### test_xxx
- 檔案：xxx
- 錯誤：xxx
- 原因：xxx
```

### Risk / Rollback Note
- **風險：** 無（只是執行測試）
- **建議：** 不要在生產 DB 執行測試

---

## WP-RA-04 — Auth 轉換決策與計畫

### Goal
決定是否統一為 JWT，如果是，制定轉換計畫。

### Scope（允許改哪些資料夾/檔案）
- ✅ 新增 `docs/AUTH_TRANSITION_DECISION.md`
- ✅ 更新 `docs/AUTH_TRANSITION_PLAN.md`
- ⛔ 不修改程式碼（本 WP 只做決策）

### Definition of Done（可驗收條件）
- [ ] 產出決策文件：AUTH_TRANSITION_DECISION.md
- [ ] 決策包含：統一為 JWT / 保持混合 / 其他
- [ ] 如果統一為 JWT：更新 AUTH_TRANSITION_PLAN.md
- [ ] 定義轉換的 4 個模組的優先順序
- [ ] 估算每個模組的轉換時間

### 執行步驟

#### Step 1: 評估現況
需要轉換的模組：
1. attendance (2 個 API endpoints)
2. notifications (1 個 API endpoint)
3. backup (2 個 API endpoints)
4. audit (多個 API endpoints)

#### Step 2: 決策考量

**選項 A：統一為 JWT**
- 優點：
  - 安全性提升（有使用者驗證）
  - 可實作 RBAC
  - API 行為一致
- 缺點：
  - 需要修改 4 個模組
  - 需要更新所有測試
  - 需要更新 API 文件
- 工作量：1-2 天

**選項 B：保持混合**
- 優點：
  - 不需修改現有程式碼
  - 向後相容
- 缺點：
  - 安全風險（Header-based 無使用者驗證）
  - 維護成本高（兩套機制）
  - API 行為不一致
- 工作量：0（但技術債累積）

**選項 C：Header 加強驗證**
- 優點：
  - 改動最小
  - 向後相容
- 缺點：
  - 仍需傳兩個 headers (X-Company-ID + X-User-ID)
  - 無法實作 RBAC
- 工作量：0.5 天

#### Step 3: 建議決策
**建議：選項 A（統一為 JWT）**

理由：
1. 長期維護成本更低
2. 安全性更好
3. 符合現代 API 設計
4. 已有 JWT 基礎設施（get_current_actor）

#### Step 4: 轉換計畫（如果選 A）

**Batch 1: attendance (優先)**
- 檔案：`backend/app/modules/attendance/api.py`
- 修改：2 個 endpoints
- 測試：`backend/app/modules/attendance/tests/test_api.py`
- 時間：4 小時

**Batch 2: audit**
- 檔案：`backend/app/modules/audit/api.py`
- 修改：多個 endpoints
- 測試：`backend/app/modules/audit/tests/test_audit_api.py`
- 時間：4 小時

**Batch 3: notifications**
- 檔案：`backend/app/modules/notifications/api.py`
- 修改：1 個 endpoint
- 測試：`backend/app/modules/notifications/tests/test_api.py`
- 時間：2 小時

**Batch 4: backup**
- 檔案：`backend/app/modules/backup/api.py`
- 修改：2 個 endpoints
- 測試：`backend/app/modules/backup/tests/test_api.py`
- 時間：3 小時

**總時間：13 小時（約 2 個工作天）**

### Risk / Rollback Note
- **風險：** 轉換後舊 client 無法使用（需要 JWT）
- **Rollback：** 保留 git commit，可 revert
- **建議：** 先在測試環境驗證，再部署生產

---

## WP-RA-05 — 文件同步更新

### Goal
更新過時文件，確保文件與實作一致。

### Scope（允許改哪些資料夾/檔案）
- ✅ `docs/STATUS_MATRIX.md`
- ✅ `docs/DEVELOPMENT_ORDER.md`
- ✅ `docs/GATE_PROGRESS_TRACKER.md`
- ⛔ 不修改程式碼

### Definition of Done（可驗收條件）
- [ ] 更新 STATUS_MATRIX.md 的 auth 模組狀態
- [ ] 統一 DEVELOPMENT_ORDER.md 與 GATE_PROGRESS_TRACKER.md 的 WP 數量
- [ ] 標記已完成的 WPs
- [ ] 更新「下一步」建議

### 執行步驟

#### Step 1: 更新 STATUS_MATRIX.md
修改：
- auth 模組：❌ Missing → ✅ Complete
- tenants 模組：更新狀態
- customer_service 模組：更新狀態
- 更新日期為 2026-03-04

#### Step 2: 統一 WP 定義
檢查：
- DEVELOPMENT_ORDER.md 說 17 個 WPs
- GATE_PROGRESS_TRACKER.md 說 20 個 WPs
- 找出差異的 3 個 WPs

補充到 DEVELOPMENT_ORDER.md：
- WP-11-03S (Split Shift Support)
- WP-11-04A (Entitlements)
- 其他？

#### Step 3: 更新完成狀態
在 GATE_PROGRESS_TRACKER.md 標記：
- WP-11-04A：✅ COMPLETED

### Risk / Rollback Note
- **風險：** 無（只更新文件）

---

## WP-RA-06 — Migration 001 清理

### Goal
移除或標記 deprecated 的 migration 001。

### Scope（允許改哪些資料夾/檔案）
- ✅ `backend/alembic/versions/001_*.py`
- ⛔ 不修改其他 migration

### Definition of Done（可驗收條件）
- [ ] 001 (舊版) 已刪除或重新命名
- [ ] `alembic heads` 仍顯示 single head
- [ ] 在 fresh DB 執行 `alembic upgrade head` 仍成功

### 執行步驟
（見 WP-RA-01 Step 1）

### Risk / Rollback Note
- **風險：** 如果有 DB 已套用 001，刪除檔案不影響（alembic 只看 alembic_version table）
- **Rollback：** 保留 .bak 備份

---

## WP-RA-07 — 建立 Fresh DB 驗證流程

### Goal
建立自動化腳本，驗證 migration chain 可在 fresh DB 執行。

### Scope（允許改哪些資料夾/檔案）
- ✅ 新增 `backend/scripts/verify_fresh_db.sh`
- ✅ 新增 `backend/tests/test_migrations.py`
- ⛔ 不修改 migration 檔案

### Definition of Done（可驗收條件）
- [ ] 建立 `verify_fresh_db.sh` 腳本
- [ ] 腳本可自動建立 temp DB、執行 migration、驗證 tables、清理
- [ ] 建立 `test_migrations.py` 測試
- [ ] 測試可在 CI 執行

### 執行步驟

#### Step 1: 建立腳本
```bash
#!/bin/bash
# backend/scripts/verify_fresh_db.sh

set -e

TEMP_DB="attendance_verify_$(date +%s)"

echo "Creating temp DB: $TEMP_DB"
createdb $TEMP_DB

echo "Running migrations..."
DATABASE_URL="postgresql://postgres:Raxcxtjq260!@127.0.0.1:5432/$TEMP_DB" \
  alembic upgrade head

echo "Verifying tables..."
TABLES=$(psql -d $TEMP_DB -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")
echo "Found $TABLES tables"

if [ "$TABLES" -lt 14 ]; then
  echo "ERROR: Expected at least 14 tables, found $TABLES"
  exit 1
fi

echo "Cleaning up..."
dropdb $TEMP_DB

echo "✅ Fresh DB verification passed"
```

#### Step 2: 建立測試
```python
# backend/tests/test_migrations.py
import pytest
import subprocess

def test_fresh_db_migration():
    """Test that alembic upgrade head works on fresh DB"""
    result = subprocess.run(
        ["bash", "scripts/verify_fresh_db.sh"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Migration failed: {result.stderr}"
```

### Risk / Rollback Note
- **風險：** 無（只建立驗證工具）

---

## 執行建議

### 第一週（P0 風險）
- Day 1: WP-RA-01 (Migration 驗證)
- Day 2: WP-RA-02 (測試 DB 重建)
- Day 3: WP-RA-03 (執行測試)
- Day 4-5: WP-RA-04 (Auth 轉換決策 + 實作)

### 第二週（P1 風險）
- Day 1: WP-RA-05 (文件更新)
- Day 2: WP-RA-06 + WP-RA-07 (Migration 清理 + 驗證流程)

### 驗收標準（整體）
- [ ] Migration chain 可在 fresh DB 執行
- [ ] 測試 DB 與 migration 一致
- [ ] 測試通過率 > 90%
- [ ] Auth 機制統一（或有明確決策）
- [ ] 文件與實作一致
- [ ] 有自動化驗證流程

---

**文件版本：** 1.0  
**產出日期：** 2026-03-04  
**審查者：** Claude Opus 4.6 (Cursor AI)
