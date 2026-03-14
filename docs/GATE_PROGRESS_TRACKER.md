# Gate Progress Tracker

**最後更新：** 2026-03-14（WP-11-06 Reporting Backend COMPLETE 後更新）

---

## ⚠️ 重要狀態說明

**狀態分類說明：**
- `VERIFIED`：已在真實 PostgreSQL 執行並確認正確
- `COMPLETED` / `COMPLETE`：有明確的程式碼 + 文件記錄，且 runtime 驗證通過
- `CODE_COMPLETE`：程式碼存在，但 runtime 未驗證（特別標注）
- `NOT_VERIFIED`：測試存在但從未在真實 DB 通過
- `BLOCKED`：有明確阻塞原因
- `NOT_STARTED`：尚未開始

---

## Gate 5 — Frontend UI Phase

**狀態：** IN_PROGRESS（Phase 1 基線修正進行中）

---

### Backend WP 完成狀態

| WP | 名稱 | 狀態 | 備注 |
|----|------|------|------|
| WP-11-01 | Attendance Domain Model | COMPLETED | code scan 確認；runtime NOT_VERIFIED |
| WP-11-02 | Punch In/Out API | CODE_COMPLETE | auth 使用 Header，需 WP-C1-02 修正 |
| WP-11-03 | Policy Engine v1 | CODE_COMPLETE | runtime NOT_VERIFIED |
| WP-11-04A | Company Entitlements + Feature Flags | CODE_COMPLETE | Feature Gate 套用 MISSING |
| WP-11-04B | Gate Ready Audit | COMPLETED | 部分結論已被 SYSTEM_VERIFICATION_BASELINE 更新 |
| WP-11-05 | Attendance Regression Tests | PARTIAL — 1/8 實作，0/8 在真實 DB 通過 | **P0 缺口** |
| WP-11-05A | Attendance Models Sync | COMPLETED | |
| **WP-11-06** | **Reporting Backend API** | **COMPLETE** | **2026-03-14 完成；三支 endpoint 驗證通過** |
| WP-C1-01 | PostgreSQL 環境建立 + Migration 驗證 | **VERIFIED** | **2026-03-11 完成；attendance_test 17 tables；head=008_wp_11_13** |
| WP-C1-03 | Auth 轉換 Batch 2-4（audit/notifications/backup） | NOT_STARTED | **P0** |
| WP-C1-04 | 回歸測試真實 DB 執行 | NOT_STARTED | 依賴 WP-C1-02 |
| WP-C1-05 | Tenant Isolation 真實 DB 驗證 | NOT_STARTED | 依賴 WP-C1-04 |
| WP-C1-06 | Feature Gate 套用至所有 API | NOT_STARTED | |
| WP-C1-07 | Attendance API JWT 遷移 | **COMPLETED** | **2026-03-12** |
| WP-C1-08 Phase 1 | Attendance Test Re-Enable 基線驗證 | **VERIFIED** | **2026-03-12** |
| WP-C1-08 Phase 2 | Fixture Layer 修復 | **FIXTURE_COMPLETE** | **2026-03-12** |
| WP-C1-09 | OUT Checkpoint API | **DONE** | **2026-03-12** |

---

### Frontend WP 完成狀態

| WP | 名稱 | 狀態 | 備注 |
|----|------|------|------|
| WP-11-07 | UI MVP Kickoff | COMPLETED | |
| WP-11-08 | JWT Auth Integration | COMPLETED | |
| WP-11-10 | OUT Checkpoint Feature | COMPLETED+REMOVED | migration 007 殘留 table |
| WP-11-11.5 | GPS Legacy Cleanup | CLOSED | |
| WP-11-12 Ph1 | useLocation Composable | COMPLETED | |
| WP-11-12 Ph2B | BREAK_OUT Integration | CLOSED | |
| WP-11-13 Step2 | Backend Location Policy | CODE_COMPLETE | commit d8eb797 |
| WP-11-13 Step3A | Frontend Integration | CODE_COMPLETE | |
| WP-11-13 Manual QA | 瀏覽器 GPS + UI 人工測試 | BLOCKED | 需真實瀏覽器 + PostgreSQL 環境 |
| WP-REPORTING-UI | Reporting UI（Sessions / Company / User Summary） | CODE_COMPLETE | BUG-01 待修復（stores/reporting.js 解構）|

---

### WP-11-06 Reporting Backend 完成記錄（2026-03-14）

**狀態：** COMPLETE  
**完成日期：** 2026-03-14

#### Deliverables

| 項目 | 狀態 |
|------|------|
| Sessions Reporting API（`GET /api/v1/attendance/sessions`） | ✅ COMPLETE |
| User Summary API（`GET /api/v1/attendance/reports/user-summary`） | ✅ COMPLETE |
| Company Summary API（`GET /api/v1/attendance/reports/company-summary`） | ✅ COMPLETE |

#### 驗收記錄

- OpenAPI `/docs` 顯示三支 endpoint ✅
- UI 三頁（Sessions / User Summary / Company Summary）可正常呼叫 API ✅
- Tenant isolation 已驗證 ✅

#### Notes

Initial runtime issue caused by uvicorn reloader orphan worker（PID 1856041，started 2026-03-11 16:58）.
`api.py` was updated on 2026-03-13 19:13 but the reloader process had already died,
so the worker never reloaded the new code.
Resolved by clean restart. No code changes required.
詳見：`docs/WP-REPORTING-BACKEND_RUNTIME_MISMATCH_REPORT.md`

---

### Gate 5 完成條件

- [x] WP-C1-01：PostgreSQL 環境建立 + Migration 驗證（VERIFIED 2026-03-11）
- [x] WP-11-06：Reporting Backend API（COMPLETE 2026-03-14）
- [ ] Phase 1 基線修正完成（WP-C1-02 ~ WP-C1-07）
- [ ] WP-11-13 Manual QA 通過
- [ ] SA 符合度 > 95%（目前約 65-70%）
- [ ] 8 個回歸測試在真實 DB 通過（目前 0/8）
- [ ] 5 個 Tenant Isolation 測試在真實 DB 通過（目前 0/5）
- [ ] 所有模組使用 JWT auth（目前 2/7）
- [ ] Feature Gate 套用至所有核心 API（目前 0%）

---

### 當前位置

- **剛完成：** WP-11-06 Reporting Backend API（2026-03-14）
- **當前阻塞：** 4 個 P0 技術債（見 NEXT_WP_TICKET.md）
- **建議下一步：** WP-11-07（Reporting UI Improvements）
- **Gate 5 估計完成度：** 45%

---

### 已知文件不一致（需後續修正）

| 文件 | 問題 | 狀態 |
|------|------|------|
| SYSTEM_DEVELOPMENT_STATUS_REPORT.md | backup auth 方式誤標為 JWT | Superseded by MODULE_STATUS_MATRIX.md |
| ATTENDANCE_DEVELOPMENT_MASTER_FLOW.md | WP-11-04B 狀態仍為 CURRENT | 需更新 |
| REALITY_AUDIT_STATUS_INVENTORY.md | 未含 migration 006/007/008 | 已過期，Superseded |
| SA_REALITY_GAP_REPORT.md | 未反映 WP-11-13 實作 | 已過期，Superseded |

---

## WP-C1-01 執行記錄（2026-03-11）

### 環境設定步驟

| 步驟 | 指令 | 結果 |
|------|------|---------|
| PostgreSQL 服務確認 | pg_isready -h localhost -p 5432 | accepting connections ✅ |
| 資料庫清單確認 | psql -U postgres -c '\l' | attendance_test 存在 ✅ |
| attendance_user 密碼重設 | ALTER USER attendance_user WITH PASSWORD 'attendance_pass' | ALTER ROLE ✅ |
| attendance_test 權限授予 | GRANT ALL PRIVILEGES ON DATABASE attendance_test | GRANT ✅ |
| schema 權限授予 | GRANT ALL ON SCHEMA public TO attendance_user | GRANT ✅ |
| schema owner 設定 | ALTER SCHEMA public OWNER TO attendance_user | ALTER SCHEMA ✅ |
| alembic upgrade head | DATABASE_URL=attendance_test alembic upgrade head | 10 steps 成功 ✅ |
| alembic current 確認 | alembic current | 008_wp_11_13 (head) ✅ |
| alembic heads 確認 | alembic heads | 008_wp_11_13 (head)（唯一）✅ |
| table 清單確認 | psql -d attendance_test -c '\dt' | 17 tables ✅ |

### 基線測試結果

| 測試 | PASS | FAIL | 總計 | 狀態 |
|------|------|------|------|------|
| test_model_constraints.py | 20 | 0 | 20 | ✅ PASS |
| test_business_invariant.py | 6 | 6 | 12 | ⚠️ PARTIAL（API 簽名問題）|
| test_migration.py | 0 | 9 | 9 | ❌ FAIL（env.py URL 覆蓋問題）|
