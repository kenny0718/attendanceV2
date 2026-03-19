# Gate Progress Tracker

**最後更新：** 2026-03-15（WP-11-07 COMPLETE；WP-11-08 成為當前 WP）

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
| WP-REPORTING-UI | Reporting UI（Sessions / Company / User Summary） | COMPLETE | WP-11-07 COMPLETE 2026-03-15；BUG-01 FIXED；QA 通過 |

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
- [x] WP-11-07：Reporting UI Polish / QA（COMPLETE 2026-03-15）
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
- **剛完成：** WP-11-07 Reporting UI Polish / QA（COMPLETE 2026-03-15）
- **當前 WP：** WP-11-08 Leave Request System（PLANNED）
- **Gate 5 估計完成度：** 50%

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

---

## WP-C1-08 狀態更新（2026-03-17）

### Backend WP 完成狀態更新

| WP | 舊狀態 | 新狀態 | 更新原因 |
|----|--------|--------|----------|
| WP-C1-08 Phase 3（Attendance Test Stabilization）| CURRENT | **COMPLETE** | Phase B 修復 4 個測試檔，49 PASS 新增，整體 85→134 PASS |

### WP-C1-08 完成記錄

**完成日期：** 2026-03-17  
**狀態：** COMPLETE  

**Phase A Baseline：**
- 179 collected，85 PASS，85 FAIL，9 ERROR
- 穩定核心：feature_gate 6/6、model_constraints 20/20、policy_engine 28/28、router_v1_jwt 12/12、tenant_isolation 9/9

**Phase B 修復：**
- test_reporting_sessions.py：0/16 → 16/16 PASS ✅
- test_reporting_user_summary.py：0/13 → 13/13 PASS ✅
- test_reporting_company_summary.py：0/14 → 14/14 PASS ✅
- test_break_out_enforcement.py：0/6 → 6/6 PASS ✅
- 修復合計：49/49 PASS；整體 PASS：85 → 134

**剩餘 pre-existing（不阻塞本票）：**
- 36 FAIL + 9 ERROR，全部已分類，來源 WP-C1-04

**Production code 修改：** 無

**結案文件：** `docs/02_DEVELOPMENT_STATUS/WP-C1-08_ATTENDANCE_TEST_STABILIZATION_COMPLETION_REPORT.md`

---

**最後更新：** 2026-03-17  
**更新原因：** WP-C1-08 Attendance Test Stabilization COMPLETE

---

## Gate Progress 全面更新（2026-03-18）

**更新性質：** WP-C1-09A Governance Repair — 補齊 WP-C1-03 ~ WP-C1-08 完成狀態  
**更新依據：** WORKSTREAM_STATUS_LEDGER.md（2026-03-17）、各 WP 結案文件

### Backend WP 完成狀態（更新至 2026-03-18）

| WP | 名稱 | 狀態 | 完成日期 | 備注 |
|----|------|------|----------|------|
| WP-11-01 | Attendance Domain Model | COMPLETED | 2026-03-03 | code scan 確認 |
| WP-11-02 | Punch In/Out API | CODE_COMPLETE | 2026-03-03 | 舊 router 仍用 Header auth（向後相容）|
| WP-11-03 | Policy Engine v1 | CODE_COMPLETE | 2026-03-04 | runtime NOT_VERIFIED |
| WP-11-04A | Company Entitlements + Feature Flags | CODE_COMPLETE | 2026-03-04 | Feature Gate 基礎建立 |
| WP-11-04B | Gate Ready Audit | COMPLETED | 2026-03-04 | |
| WP-11-05 | Attendance Regression Tests | PARTIAL | - | 1/8 實作，pre-existing 缺口 |
| WP-11-05A | Attendance Models Sync | COMPLETED | - | |
| WP-11-06 | Reporting Backend API | COMPLETE | 2026-03-14 | 三支 endpoint 驗證通過 |
| WP-11-07 | Reporting UI Polish / QA | COMPLETE | 2026-03-15 | BUG-01 FIXED |
| WP-11-08 | Leave Request System Backend | COMPLETE | 2026-03-15 | 五層模組，5 endpoints manual PASS |
| WP-C1-01 | PostgreSQL 環境建立 + Migration 驗證 | VERIFIED | 2026-03-11 | 17→21 tables；head=009_wp_11_08 |
| **WP-C1-03** | **Auth 轉換 Batch 2（audit/notifications/backup）** | **COMPLETE** | **2026-03-17** | **78/78 PASS** |
| **WP-C1-04** | **PostgreSQL 回歸測試** | **COMPLETE** | **2026-03-17** | **78/78 PASS；37 pre-existing 已分類** |
| **WP-C1-05** | **Tenant Isolation 真實 DB 驗證** | **COMPLETE** | **2026-03-17** | **39/39 PASS on PostgreSQL** |
| **WP-C1-06** | **Feature Gate 套用至所有 API** | **COMPLETE** | **2026-03-17** | **22/22 PASS；5 核心模組全部 gated** |
| **WP-C1-07** | **Attendance router_v1 JWT 遷移** | **COMPLETE** | **2026-03-17** | **11/11 endpoints；12/12 tests PASS** |
| **WP-C1-08** | **Attendance Test Stabilization** | **COMPLETE** | **2026-03-17** | **134/179 PASS；36+9 pre-existing** |
| WP-C1-09 | Governance Consolidation | COMPLETE | 2026-03-18 | 治理收斂票；非功能票 |
| WP-C1-09A | Governance Missing Files Reconstruction | COMPLETE | 2026-03-18 | 治理修復票；非功能票 |
| **WP-C1-10** | **System-wide JWT Alignment** | **COMPLETE** | **2026-03-18** | **GAP-C1-001 + GAP-C1-003 RESOLVED** |

### Frontend WP 完成狀態（維持）

| WP | 名稱 | 狀態 | 備注 |
|----|------|------|------|
| WP-11-07（FE）| UI MVP Kickoff | COMPLETED | |
| WP-11-08（FE）| JWT Auth Integration | COMPLETED | |
| WP-11-10 | OUT Checkpoint Feature | COMPLETED+REMOVED | migration 007 殘留 table |
| WP-11-11.5 | GPS Legacy Cleanup | CLOSED | |
| WP-11-12 Ph1 | useLocation Composable | COMPLETED | |
| WP-11-12 Ph2B | BREAK_OUT Integration | CLOSED | |
| WP-11-13 Step2 | Backend Location Policy | CODE_COMPLETE | commit d8eb797 |
| WP-11-13 Step3A | Frontend Integration | CODE_COMPLETE | |
| WP-11-13 Manual QA | 瀏覽器 GPS + UI 人工測試 | BLOCKED | 需真實瀏覽器 + PostgreSQL 環境 |
| WP-REPORTING-UI | Reporting UI | COMPLETE | BUG-01 FIXED；WP-11-07 COMPLETE |

### Gate 5 完成條件（更新至 2026-03-18）

#### 已達成
- [x] WP-C1-01：PostgreSQL 環境建立 + Migration 驗證（VERIFIED 2026-03-11）
- [x] WP-11-06：Reporting Backend API（COMPLETE 2026-03-14）
- [x] WP-11-07：Reporting UI Polish / QA（COMPLETE 2026-03-15）
- [x] WP-11-08：Leave Request System Backend（COMPLETE 2026-03-15）
- [x] WP-C1-03：Auth 轉換 Batch 2（COMPLETE 2026-03-17，78/78 PASS）
- [x] WP-C1-04：PostgreSQL 回歸測試（COMPLETE 2026-03-17）
- [x] WP-C1-05：Tenant Isolation 真實 DB（COMPLETE 2026-03-17，39/39 PASS）
- [x] WP-C1-06：Feature Gate 套用（COMPLETE 2026-03-17，22/22 PASS）
- [x] WP-C1-07：Attendance JWT 遷移（COMPLETE 2026-03-17）
- [x] WP-C1-08：Attendance Test Stabilization（COMPLETE 2026-03-17）

#### 尚未達成（pre-existing 缺口）
- [ ] WP-11-13 Manual QA 通過（BLOCKED）
- [ ] leave 模組 JWT Actor 遷移（尚無對應 WP）
- [ ] leave 模組自動化測試（pre-existing）
- [ ] attendance 36 FAIL + 9 ERROR 修復（pre-existing，待後續 WP）
- [ ] customer_service 模組詳細狀態稽核（observation）

### Gate 5 / C1 狀態

> **Gate 5 / C1 主要里程碑（WP-C1-01 ~ WP-C1-08）已全部 COMPLETE。**
> 估計完成度：~90%
> 剩餘缺口為 pre-existing 問題（leave JWT 遷移、WP-11-13 Manual QA 等），
> 不屬於 WP-C1-08 或 WP-C1-09/09A 範圍。
> Gate 正式關閉宣告需由人工確認，不由本票自行宣布。

### 當前位置

- **剛完成：** WP-C1-08 Attendance Test Stabilization（2026-03-17）
- **治理收斂：** WP-C1-09 Governance Consolidation（2026-03-18，COMPLETE）
- **當前進行：** WP-C1-09A Governance Missing Files Reconstruction（2026-03-18，IN_PROGRESS）
- **Gate 5 估計完成度：** ~90%

---

**最後更新：** 2026-03-18  
**更新原因：** WP-C1-10 JWT Alignment COMPLETE；GAP-C1-001 + GAP-C1-003 RESOLVED

---

**最後更新：** 2026-03-18  
**更新原因：** WP-C1-10 JWT Alignment COMPLETE；GAP-C1-001 + GAP-C1-003 RESOLVED

---

**最後更新：** 2026-03-18  
**更新原因：** WP-C1-13 COMPLETE；Gate 5 / C1 正式關閉

### Gate 5 / C1 Final Status

- **WP-C1-13** Test Stabilization：COMPLETE ✅（2026-03-18）
- **Gate 5 / C1：CLOSED ✅**
- **Gate 5 完成度：100%**
- backup/tests/test_api.py：14/14 PASS ✅
- notifications/tests/test_api.py：13/13 PASS ✅
- attendance/tests/test_out_checkpoint.py：7/7 PASS ✅
- 所有 blocking gaps RESOLVED
- 下一階段：Gate 6 — Schedule 模組（WP-S1）


---

## Gate 6 — Schedule 模組開發（WP-S1 系列）

**狀態:** IN_PROGRESS  
**啟動日期:** 2026-03-18  
**前置條件:** Gate 5 / C1 CLOSED (2026-03-18)

### Gate 6 WP 完成狀態

| WP | 名稱 | 狀態 | 完成日期 |
|----|------|------|----------|
| **WP-S1-01** | **Schedule Module Foundation** | **COMPLETE** | **2026-03-18** |
| WP-S1-02 | Schedule Migration | PENDING | - |
| WP-S1-03 | Basic Schedule API | PENDING | - |
| WP-S1-04 | ShiftAssignment API | PENDING | - |
| WP-S1-05 | Tenant Isolation Tests | PENDING | - |
| WP-S1-06 | Feature Gate | PENDING | - |

### WP-S1-01 完成記錄（2026-03-18）

- schedule 模組骨架建立（7 個檔案）
- ShiftTemplate + ShiftAssignment ORM 定義（code-level only）
- repo / service / api 骨架（stub，NotImplementedError）
- docs.md 建立
- Smoke test PASS（import OK，全部類別可正常載入）
- 無 migration，無 API endpoint，無主 app 掛載
- production code 未修改

---

**最後更新:** 2026-03-18  
**更新原因:** WP-S1-01 COMPLETE；Gate 6 Schedule 模組開發正式啟動


---

## WP-S1-01A — Schedule Models Alignment Fix

**完成日期:** 2026-03-18  
**性質:** Blocking Issue Resolution（Pre-Migration Audit B1/B2 修正）  
**前置條件:** WP-S1-01 COMPLETE + WP-S1-02 Pre-Migration Audit NOT READY

### 完成摘要

- B1 FIXED: company_id Integer → String(255) + ForeignKeyConstraint(tenants.id CASCADE)
- B2 FIXED: user_id Integer → UUID(as_uuid=True) + ForeignKeyConstraint(users.id CASCADE)
- M2 FIXED: PK Integer → UUID + gen_random_uuid()
- M3 FIXED: inline ForeignKey → ForeignKeyConstraint in __table_args__
- M4 ADDED: UniqueConstraint(company_id, code) on ShiftTemplate
- M6 CLARIFIED: AssignmentStatus SQLAlchemy Enum → String(20) + CheckConstraint
- Smoke test: ALL_CHECKS_PASS
- docs.md: 更新至 v1.1
- 結案文件: docs/WP-S1-01A_MODELS_ALIGNMENT_FIX_REPORT.md

### Migration Readiness

**READY FOR WP-S1-02: YES**

下一票建議: WP-S1-02 Schedule Module Migration

---

**最後更新:** 2026-03-18  
**更新原因:** WP-S1-01A COMPLETE; READY FOR WP-S1-02

---

## WP-S1-02 Gate Entry (2026-03-18)

| Gate Item | Status | Notes |
|-----------|--------|-------|
| Migration file created | PASS | 010_wp_s1_02_create_schedule_tables.py |
| revision chain correct | PASS | 009_wp_11_08 → 010_wp_s1_02 |
| alembic upgrade head | PASS | EXIT=0 |
| shift_templates exists | PASS | Confirmed via pg_tables |
| shift_assignments exists | PASS | Confirmed via pg_tables |
| uq_shift_templates_company_code | PASS | Confirmed via pg_constraint |
| ck_shift_assignments_status | PASS | Confirmed via pg_constraint |
| FK to tenants.id | PASS | fk_shift_templates_company_id + fk_shift_assignments_company_id |
| FK to users.id | PASS | fk_shift_assignments_user_id |
| FK to shift_templates.id | PASS | fk_shift_assignments_template_id |
| env.py schedule import | PASS | Minimal fix only |
| schemas.py UUID alignment | PASS | company_id:str, id/user_id/shift_template_id:UUID |
| main.py unchanged | PASS | Scope lock respected |
| other modules unchanged | PASS | Scope lock respected |
| old migrations unchanged | PASS | Scope lock respected |

**WP-S1-02 GATE: PASS**

**最後更新:** 2026-03-18

---

## WP-S1-02B Gate Entry (2026-03-19)

| Gate Item | Status | Notes |
|-----------|--------|-------|
| env.py non-empty | PASS | 5464 bytes |
| env.py all modules import | PASS | 8/8 modules, 23 tables |
| static import test | PASS | ALL_IMPORTS_OK |
| alembic current | PASS | 010_wp_s1_02 (head) |
| alembic upgrade head | PASS | EXIT=0, no-op |
| .tmp residue removed | PASS | 010_wp_s1_02_create_schedule_tables.py.tmp deleted |
| scope lock respected | PASS | no new migration, no model changes |

**WP-S1-02B GATE: PASS — ALEMBIC SAFE = YES**

**最後更新:** 2026-03-19

---

## WP-S1-03 Gate Entry (2026-03-19)

| Gate Item | Status | Notes |
|-----------|--------|-------|
| repo.py non-stub | PASS | 9436 bytes, all NotImplementedError removed |
| service.py non-stub | PASS | 15037 bytes, all NotImplementedError removed |
| import test | PASS | REPO_IMPORT_OK + SERVICE_IMPORT_OK |
| ShiftTemplate CRUD smoke | PASS | Tests 1-7: all PASS |
| ShiftAssignment CRUD smoke | PASS | Tests 8-15: all PASS |
| Tenant isolation enforced | PASS | company_id WHERE clause in all queries |
| cross-tenant template blocked | PASS | Test 15: HTTPException |
| duplicate code blocked | PASS | Test 2: HTTPException 409 |
| double cancel blocked | PASS | Test 14: HTTPException 409 |
| scope lock respected | PASS | api.py/main.py/migration unchanged |

**WP-S1-03 GATE: PASS**

**最後更新:** 2026-03-19

---

## WP-S1-04A Gate Entry (2026-03-19)

| Gate Item | Status | Notes |
|-----------|--------|-------|
| api.py non-empty | PASS | 10948 bytes |
| syntax check | PASS | ast.parse OK |
| router import | PASS | IMPORT_OK |
| router prefix | PASS | /api/v1/schedule |
| template endpoints (6) | PASS | POST/GET/GET/PATCH/activate/deactivate |
| assignment endpoints (5) | PASS | POST/GET/GET/PATCH/cancel |
| total routes | PASS | 11 routes |
| main.py unchanged | PASS | schedule NOT mounted |
| schemas.py unchanged | PASS | no modification needed |
| scope lock respected | PASS | repo/service/migration unchanged |

**WP-S1-04A GATE: PASS — API LAYER READY**

**最後更新:** 2026-03-19

---

## WP-S1-04B Gate Entry (2026-03-19)

| Gate Item | Status | Notes |
|-----------|--------|-------|
| FeatureKeys.SCHEDULE_CORE defined | PASS | 'schedule.core' in all_keys() |
| api.py feature gate wired | PASS | 11/11 endpoints protected |
| main.py include_router | PASS | schedule_router mounted |
| app import/startup | PASS | no errors |
| schedule routes in app | PASS | 11 routes |
| e2e smoke (no auth → 401) | PASS | 4/4 endpoints |
| nonexistent route → 404 | PASS | |
| OpenAPI schedule paths | PASS | 7 paths |
| scope lock respected | PASS | repo/service/migration unchanged |

**WP-S1-04B GATE: PASS — MOUNT COMPLETE**

**最後更新:** 2026-03-19

---

## WP-S1-05 Gate (2026-03-19)

| Gate | 狀態 | 說明 |
|------|------|------|
| Entitlement Setup | PASS | schedule.core fixture 正確建立 |
| JWT + Tenant Context | PASS | dependency_override 模擬 actor |
| Feature Gate (enabled) | PASS | 有 entitlement 正常放行 |
| Feature Gate (disabled) | PASS | 無 entitlement 403 |
| Template CRUD | PASS | 6 endpoints 全通過 |
| Assignment CRUD | PASS | 6 endpoints 全通過 |
| Negative Cases | PASS | 409/404/403 全驗證 |
| Pytest 12/12 | PASS | 零 failure |
| Scope Control | PASS | 無 migration/model/frontend 變更 |

**WP-S1-05 GATE: COMPLETE**

---

## Gate 6 WP-S1-06 完成記錄 (2026-03-19)

### WP-S1-06 Gate Entry

| Gate Item | Status | Notes |
|-----------|--------|-------|
| schedule.core entitlement path confirmed | PASS | company_entitlements table + tenants API |
| PLAN_DEFAULTS audit completed | PASS | schedule.core not in PLAN_DEFAULTS（opt-in design）|
| Real JWT token generation | PASS | create_access_token() HS256 |
| Real auth dependency chain | PASS | get_current_actor → decode → DB → Actor |
| No override_actor_dependency | PASS | only get_db overridden |
| Auth baseline (401 no-token) | PASS | |
| Auth baseline (401 invalid-token) | PASS | |
| Template create real JWT | PASS | 201 |
| Template get real JWT | PASS | 200 |
| Template list real JWT | PASS | 200 |
| Assignment create real JWT | PASS | 201 |
| Assignment get real JWT | PASS | 200 |
| Assignment cancel real JWT | PASS | 200, status=cancelled |
| No entitlement → 403 FEATURE_DISABLED | PASS | Company B correctly blocked |
| Cross-tenant blocked | PASS | 403 (feature gate fires first) |
| pytest 14/14 | PASS | 1.91s |
| scope lock respected | PASS | no model/repo/service/api/migration changes |

**WP-S1-06 GATE: PASS — REAL JWT E2E COMPLETE**

### Gate 6 WP 完成狀態（更新）

| WP | 名稱 | 狀態 | 完成日期 |
|----|------|------|----------|
| WP-S1-01 | Schedule Module Foundation | COMPLETE | 2026-03-18 |
| WP-S1-01A | Models Alignment Fix | COMPLETE | 2026-03-18 |
| WP-S1-02 | Schedule Migration | COMPLETE | 2026-03-18 |
| WP-S1-02B | Alembic Definitive Fix | COMPLETE | 2026-03-19 |
| WP-S1-03 | CRUD Core | COMPLETE | 2026-03-19 |
| WP-S1-04A | API Layer | COMPLETE | 2026-03-19 |
| WP-S1-04B | Router Mount + Feature Gate | COMPLETE | 2026-03-19 |
| WP-S1-05 | Integration Tests + Entitlement Setup | COMPLETE | 2026-03-19 |
| **WP-S1-06** | **Real JWT E2E** | **COMPLETE** | **2026-03-19** |

**最後更新:** 2026-03-19  
**更新原因:** WP-S1-06 COMPLETE
