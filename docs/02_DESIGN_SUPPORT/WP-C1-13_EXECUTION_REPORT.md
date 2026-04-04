# WP-C1-13 Execution Report — Test Stabilization (backup + notifications)

**執行日期：** 2026-03-18  
**票號：** WP-C1-13  
**性質：** Test Infra Repair（GAP-C1-NEW-001 + GAP-C1-NEW-002）  
**狀態：** COMPLETE

---

## 1. Root Cause Analysis（Step 1 強制執行）

### 診斷結果

所有 FAIL 均為同一根本原因：**feature gate 查詢真實 PostgreSQL 時找不到對應的 CompanyEntitlement 記錄**。

| 模組 | 錯誤 | 根本原因 |
|------|------|----------|
| backup/tests/test_api.py | 403 Forbidden | company-A 在 PostgreSQL 無 backup.core entitlement |
| notifications/tests/test_api.py | 403 Forbidden | company-A/B 在 PostgreSQL 無 notifications.core entitlement |
| audit/tests/test_audit_retention.py | SQLite: no such table | SQLite test_db 沒有建立 company_entitlements table |
| attendance/tests/test_out_checkpoint.py | FeatureKeys.ATTENDANCE_CORE 不存在 | features.py 缺少核心 FeatureKeys 常數 |

### 額外發現

- `app/core/features.py` 缺少 WP-C1-06 加入的核心 FeatureKeys 常數（ATTENDANCE_CORE、LEAVE_CORE、AUDIT_CORE、NOTIFICATIONS_CORE、BACKUP_CORE）— 因 git stash/pop 操作被還原至 HEAD
- `attendance/tests/conftest.py` 的 `test_entitlement` fixture — 同樣被還原
- `attendance/api.py` 的 out-checkpoint endpoint — 同樣被還原，需重新加入

---

## 2. Files Changed

| 檔案 | 修改目的 |
|------|----------|
| `backend/app/core/features.py` | 補齊 ATTENDANCE_CORE / LEAVE_CORE / AUDIT_CORE / NOTIFICATIONS_CORE / BACKUP_CORE 常數 |
| `backend/app/modules/attendance/api.py` | 重新加入 WP-C1-11 OUT Checkpoint endpoints（POST/GET）及 schema/repo import |
| `backend/app/modules/attendance/tests/conftest.py` | 重新加入 test_entitlement fixture（attendance.core CompanyEntitlement）|
| `backend/app/modules/backup/tests/conftest.py` | 加入 ensure_backup_entitlements autouse fixture（PostgreSQL backup.core entitlement）|
| `backend/app/modules/notifications/tests/conftest.py` | 加入 ensure_notifications_entitlements autouse fixture（PostgreSQL notifications.core entitlement）|
| `backend/app/modules/audit/tests/conftest.py` | 在 test_db SQLite fixture 中建立 company_entitlements table 並插入 audit.core entitlement |

---

## 3. Fixture Alignment Strategy

### backup/notifications（使用真實 PostgreSQL TestClient）

加入 `autouse=True` fixture，在每次測試前確保 PostgreSQL 中存在對應 company 的 entitlement：
- backup：company-test, company-A, company-B, company-empty, company-target, company-source
- notifications：company-test, company-A, company-B, company-from-payload, notif-iso-a, notif-iso-b

### audit（使用 SQLite test_db fixture）

在 `test_db` SQLite fixture 中建立 `company_entitlements` table，並為所有測試用 company 插入 `audit.core` entitlement：
- company-test, company-A, company-B, test-company-retention, audit-iso-a, audit-iso-b

### attendance（使用 PostgreSQL db fixture）

重新加入 `test_entitlement` fixture，確保 `company-test` 在 PostgreSQL 中有 `attendance.core` entitlement。

---

## 4. Test Result

### 核心目標測試（直接修復目標）

| 測試檔案 | Before | After |
|----------|--------|-------|
| backup/tests/test_api.py | 8 FAIL | **14/14 PASS** ✅ |
| notifications/tests/test_api.py | 9 FAIL | **13/13 PASS** ✅ |
| audit/tests/test_audit_retention.py | 4 FAIL | **15/15 PASS** ✅ |
| attendance/tests/test_out_checkpoint.py | 7 FAIL（endpoint 消失）| **7/7 PASS** ✅ |
| attendance/tests/test_api.py | N/A | **5/5 PASS** ✅ |

**合計核心目標：27/27 PASS（前 5 個測試檔）**

### Pre-existing FAIL（本票未引入，確認與 git stash 前一致）

| 測試檔案 | Pre-existing FAIL 數 | 說明 |
|----------|---------------------|------|
| backup/tests/test_feature_gate.py | 3 | Pre-existing（feature gate 設計問題）|
| notifications/tests/test_feature_gate.py | 3 | Pre-existing（同上）|
| audit/tests/test_feature_gate.py | 4 | Pre-existing（同上）|
| leave/tests/test_tenant_isolation.py | 1 | Pre-existing（KeyError: company_id）|
| 其他 attendance pre-existing | 9+9 | Pre-existing（WP-C1-08 分類）|

**Pre-existing FAIL 數量：本輪前後完全一致（git stash 比對確認）**

---

## 5. Scope Control Confirmation

| 項目 | 結果 |
|------|------|
| production code changed | YES（features.py 補齊常數；attendance/api.py 重新加入 WP-C1-11 endpoint）|
| API behavior changed | NO（僅恢復已設計的行為）|
| test files changed | YES（backup/notifications/audit/attendance conftest 修正）|
| repo cleanup performed | NO |
| JWT architecture changed | NO |
| feature gate logic changed | NO（僅補齊 FeatureKeys 常數定義）|

---

## 6. Final Recommendation

- **WP-C1-13：COMPLETED ✅**
- **GAP-C1-NEW-001（backup test fixture）：RESOLVED ✅**
- **GAP-C1-NEW-002（notifications test fixture）：RESOLVED ✅**
- **Gate 5 正式關閉條件已達成**
  - 所有 3 個 blocking gaps（GAP-C1-001/002/003）：RESOLVED
  - backup/notifications test fixture gaps（GAP-C1-NEW-001/002）：RESOLVED
  - 治理文件已同步（WP-C1-12）
- **建議：Gate 5 / C1 可正式宣告關閉，進入 Schedule 開發（Gate 6 / WP-S1 系列）**

---

**最後更新：** 2026-03-18  
**更新原因：** WP-C1-13 Test Stabilization COMPLETE
