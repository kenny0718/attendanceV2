# WORKSTREAM_STATUS_LEDGER.md

## Purpose

本文件為「工作流狀態帳本」，每完成一個 WP 或模組後必須更新。
不是一次性報告，而是持續維護的執行記錄。

## Scope

記錄每個 WP 的完成狀態、已驗證內容、未驗證內容、測試結果、文件一致性、下一步建議。

## Source of Truth

- 本文件（持續更新）
- `MODULE_STATUS_MATRIX.md`（模組層面狀態）
- `GATE_PROGRESS_TRACKER.md`（Gate 層面進度）

## Last Updated

2026-03-11（WP-C1-01 完成後更新）

## 更新規則

每完成一個 WP 後，必須在本文件新增一個章節，格式如下：

```markdown
### WP-[ID]：[名稱]

**完成日期：** YYYY-MM-DD  
**Git Commit：** [commit hash]  
**負責人：** [AI session / 開發者]

**已完成：**
- [具體交付物列表]

**已驗證（VERIFIED）：**
- [通過的測試、手動驗證的功能]

**未驗證（NOT_VERIFIED）：**
- [尚未驗證的項目及原因]

**測試結果：**
- pytest 結果：[X/Y PASS]
- Manual QA：[PASS/FAIL/BLOCKED]

**文件一致性：**
- [更新了哪些文件]
- [發現的文件不一致問題]

**下一步：**
- [後續 WP 或行動項目]
```

---

## 歷史記錄

### WP-11-01：Attendance Domain Model

**完成日期：** 2026-03-03  
**Git Commit：** 未記錄  

**已完成：**
- `001b_create_attendance_domain_v2_fixed.py`（migration）
- `attendance/models.py`（attendance_policies, attendance_sessions, attendance_punches）
- `attendance/repo.py`
- `attendance/tests/test_model_constraints.py`
- `attendance/tests/test_migration.py`
- `attendance/tests/test_business_invariant.py`

**已驗證（VERIFIED）：**
- 文件記載：41/41 測試通過（來源：ATTENDANCE_DEVELOPMENT_MASTER_FLOW.md）

**未驗證（NOT_VERIFIED）：**
- 測試是否在真實 PostgreSQL DB 通過（文件未明確說明執行環境）
- migration 001b 在 fresh DB 可否獨立執行

**狀態：** `DOC_COMPLETE`（41 tests）、`CODE_COMPLETE`（code scan 確認）、runtime `NOT_VERIFIED`

---

### WP-11-02：Punch In/Out API

**完成日期：** 2026-03-03  
**Git Commit：** 未記錄  

**已完成：**
- `attendance/api.py`（punch-in, punch-out, current-status, history endpoints）
- `attendance/service.py`
- `attendance/schemas.py`
- `attendance/tests/test_punch_api.py`

**已驗證（VERIFIED）：**
- 文件記載：17/17 測試通過

**未驗證（NOT_VERIFIED）：**
- 測試使用 Header auth（非 JWT），需在 JWT 轉換後重新驗證
- 真實 DB 執行未確認

**狀態：** `CODE_COMPLETE`；auth 方式需 WP-C1-02 修正

---

### WP-11-03：Policy Engine v1

**完成日期：** 2026-03-04  
**Git Commit：** 未記錄  

**已完成：**
- `attendance/policy_engine.py`（24KB）
- `attendance/tests/test_policy_engine.py`

**已驗證（VERIFIED）：**
- 文件記載：24/24 測試通過

**未驗證（NOT_VERIFIED）：**
- PENDING_APPROVAL exclusion 邏輯是否正確（需回歸測試 Test 4 驗證）
- 真實 DB 執行未確認

**狀態：** `CODE_COMPLETE`；runtime `NOT_VERIFIED`

---

### WP-11-04A：Company Entitlements + Feature Flags

**完成日期：** 2026-03-04  
**Git Commit：** 未記錄  

**已完成：**
- `wp_11_04a_entitlements.py`（migration）
- `tenants/api.py`（entitlements CRUD）
- `customer_service/api.py`（assignments）
- `core/feature_service.py`
- `core/features.py`

**已驗證（VERIFIED）：**
- 文件記載：測試通過

**未驗證（NOT_VERIFIED）：**
- Feature Gate 套用至 API endpoint（尚未完成）
- 真實 DB 執行未確認

**狀態：** `CODE_COMPLETE`；Feature Gate 套用 `MISSING`

---

### WP-11-04B：Gate Ready Audit

**完成日期：** 2026-03-04  
**Git Commit：** 未記錄  

**已完成：**
- SA_REALITY_GAP_REPORT.md
- REALITY_AUDIT_STATUS_INVENTORY.md
- MIGRATION_CHAIN_AUDIT_REPORT.md（referenced）

**未驗證（NOT_VERIFIED）：**
- 部分結論已過期（如 backup auth 方式誤記）

**狀態：** `DOC_COMPLETE`；被本次 SYSTEM_VERIFICATION_BASELINE.md 更新取代

---

### WP-11-05A：Attendance Models Sync

**完成日期：** 未記錄  
**Git Commit：** 未記錄  

**狀態：** 文件列為 COMPLETED，具體內容未詳細記錄

---

### WP-11-07 ~ WP-11-13 Step3A：Frontend UI 系列

**完成日期範圍：** 2026-03-05 ~ 2026-03-10  
**最後 Git Commit：** d8eb797（WP-11-13 Critical Bug Fix，2026-03-08）

**已完成：**
- Login.vue、Home.vue（3-Card 佈局）
- auth store、attendance store
- useLocation composable（GPS）
- break-out/in GPS 整合
- Location Policy 錯誤處理
- punch note 編輯

**已驗證（VERIFIED）：**
- Code scan 確認元件存在

**未驗證（NOT_VERIFIED）：**
- WP-11-13 Manual QA：BLOCKED（需真實瀏覽器 + PostgreSQL）
- GPS 定位實際流程
- Location Policy 端到端驗證

**狀態：** `CODE_COMPLETE`；Manual QA `NOT_VERIFIED`

---

### WP-C1-01：PostgreSQL 執行環境驗證

**完成日期：** 2026-03-11  
**Git Commit：** N/A（純環境驗證，無程式碼修改）  
**負責人：** AI session（Cursor）

**已完成：**
- PostgreSQL 服務確認可連線（localhost:5432 accepting connections）
- `attendance_test` 資料庫確認存在
- `attendance_user` 密碼重設為 `attendance_pass`（與測試檔案硬碼一致）
- `attendance_test` public schema 權限設定（GRANT ALL ON SCHEMA public TO attendance_user; ALTER SCHEMA public OWNER TO attendance_user）
- `alembic upgrade head` 對 `attendance_test` 執行成功（10 個 migration 步驟全部通過）
- `alembic current` 確認：`008_wp_11_13 (head)`
- `alembic heads` 確認：只有一個 head `008_wp_11_13`
- 三個基線測試執行完畢，取得通過率基線

**已驗證（VERIFIED）：**
- PostgreSQL localhost:5432 可連線 ✅
- `attendance_db` alembic current = `008_wp_11_13 (head)` ✅
- `attendance_test` alembic upgrade head 成功執行至 `008_wp_11_13` ✅
- alembic heads 只顯示一個 head（`008_wp_11_13`）✅
- `attendance_test` 建立 17 個 table（超過文件要求最少 15 個）✅
- `test_model_constraints.py`：**20/20 PASS**（真實 PostgreSQL attendance_test 執行）✅

**已建立的 Table 清單（attendance_test，共 17 個）：**
- alembic_version, allowed_locations, attendance_out_checkpoints, attendance_policies
- attendance_punches, attendance_sessions, audit_logs, audit_retention_policies
- company_entitlements, notifications, permissions, role_permissions
- roles, support_company_assignments, tenants, user_company_memberships, users

**未驗證（NOT_VERIFIED）／阻塞記錄：**

1. **test_business_invariant.py：6/12 PASS，6 FAIL**
   - 失敗原因 A：`AttendanceSessionRepository.close_session()` 不接受 `company_id` keyword argument，但測試傳入此參數（API 簽名不符，為既有程式碼問題）
   - 失敗原因 B：datetime timezone mismatch（DB 回傳含 timezone，測試比較 naive datetime）
   - 此為既有程式碼缺陷，非環境問題，留待 WP-C1-02 修正

2. **test_migration.py：0/9 PASS**
   - 失敗原因：`alembic/env.py` L32 `config.set_main_option("sqlalchemy.url", settings.database_url)` 強制覆蓋，使測試 fixture 中設定的 `TEST_DATABASE_URL` 完全無效
   - migration 永遠連到 `attendance_db`（.env 