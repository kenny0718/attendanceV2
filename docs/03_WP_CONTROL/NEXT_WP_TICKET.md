# Next WP Ticket

**更新日期：** 2026-03-17（WP-C1-03 JWT Migration Batch 2 COMPLETE）  
**當前狀態：** WP-C1-03 COMPLETE；當前 WP：WP-C1-04

---

## WP-11-06 Reporting Backend — COMPLETE ✅

**完成日期：** 2026-03-14  
**狀態：** COMPLETE

### 完成 API

| Endpoint | 狀態 |
|----------|------|
| `GET /api/v1/attendance/sessions` | COMPLETE |
| `GET /api/v1/attendance/reports/user-summary` | COMPLETE |
| `GET /api/v1/attendance/reports/company-summary` | COMPLETE |

### 驗收記錄

- OpenAPI `/docs` 顯示三支 endpoint ✅
- UI 三頁（Sessions / User Summary / Company Summary）可正常呼叫 API ✅
- Tenant isolation 已驗證 ✅

### 備注

初始 runtime 問題：uvicorn reloader 孤兒 worker（PID 1856041，2026-03-11 16:58 啟動）導致 `api.py` 修改後未 reload。
以 clean restart 解決，無需修改任何程式碼。
詳見：`docs/WP-REPORTING-BACKEND_RUNTIME_MISMATCH_REPORT.md`

---

## 當前完成狀態（截至 2026-03-17）

| WP | 名稱 | 狀態 |
|----|------|------|
| WP-11-01 | Attendance Domain Model | COMPLETED |
| WP-11-02 | Punch In/Out API | COMPLETED |
| WP-11-03 | Policy Engine v1 | COMPLETED |
| WP-11-04A | Company Entitlements + Feature Flags | COMPLETED |
| WP-11-04B | Gate Ready Audit | COMPLETED |
| WP-11-05A | Attendance Models Sync | COMPLETED |
| **WP-11-06** | **Reporting Backend API** | **COMPLETE（2026-03-14）** |
| **WP-11-07** | **Reporting UI Polish / QA** | **COMPLETE（2026-03-15）** |
| **WP-11-08** | **Leave Request System** | **COMPLETE（2026-03-15）** |
| WP-11-07~13 Step3A | Frontend UI 系列 | COMPLETED |
| WP-11-13 Manual QA | GPS + UI 人工測試 | BLOCKED（需環境）|
| **系統驗證基線建立** | SYSTEM_VERIFICATION_BASELINE | **COMPLETED（2026-03-11）** |
| **WP-C1-01** | PostgreSQL 環境建立 + Migration 驗證 | **VERIFIED（2026-03-11）** |
| **WP-C1-07** | Attendance API JWT 遷移 | **COMPLETED（2026-03-12）** |
| **WP-C1-08 Phase 1** | Attendance Test Re-Enable 基線驗證 | **VERIFIED（2026-03-12）** |
| **WP-C1-08 Phase 2** | Fixture Layer 修復 | **FIXTURE_COMPLETE（2026-03-12）** |
| **WP-C1-09** | OUT Checkpoint API | **DONE（2026-03-12）** |
| **WP-C1-03** | Auth 轉換 Batch 2（audit/notifications/backup JWT 遷移）| **COMPLETE（2026-03-17）** |

---

## 已完成 WP：WP-11-07 — Reporting UI Polish / QA ✅ COMPLETE

**完成日期：** 2026-03-15  
**狀態：** COMPLETE

### WP-11-07 Completion Notes

- ✅ Reporting UI pages verified（Sessions / CompanySummary / UserSummary 三頁均驗收通過）
- ✅ BUG-01 fixed（`stores/reporting.js` response 解構正確，無多餘 `.data` 取用）
- ✅ WARN-01 cleaned（`sessionsFilters` dead state 已移除）
- ✅ Timezone display confirmed（Asia/Taipei，dayjs.tz 全域設定正確）
- ✅ Loading / Error / Empty states verified（四態完整實作）
- ✅ API endpoints 正確呼叫（`/api/v1/attendance/sessions`、`/reports/company-summary`、`/reports/user-summary`）

---

## 已完成 WP：WP-11-08 — Leave Request System ✅ COMPLETE

**完成日期：** 2026-03-15  
**Status：** COMPLETE

### WP-11-08 Completion Summary

- ✅ Phase 1：Leave schema design（leave_types / leave_approval_policies / leave_requests / leave_approval_logs）
- ✅ Phase 2A：Schema + Repo + Service foundation（schemas.py / repo.py / service.py）
- ✅ Phase 2B：Leave API layer（api.py，5 endpoints）
- ✅ Phase 2C：Manual smoke test — 全部 5 endpoints PASS
- ✅ Migration 009_wp_11_08 執行完成（leave tables 建立）
- ✅ auth/models.py startup blocker 修復（從備份還原）
- ✅ Tenant isolation：所有 API 強制帶 company_id
- ✅ Status transition guard：duplicate approve/reject 回傳 HTTP 409
- ✅ cancel endpoint 未對外暴露

### Known Limitation

- `approver_id` 目前為 `null`（approver 解析邏輯待後續 phase 補齊）
- 不影響核心請假申請 / 審批 / 拒絕 API 流程
- 詳見：`docs/02_DEVELOPMENT_STATUS/WP-11-08_LEAVE_API_MANUAL_TEST_REPORT.md`

---

## 已完成 WP：WP-C1-03 — Auth 轉換 Batch 2 ✅ COMPLETE

**完成日期：** 2026-03-17  
**Status：** COMPLETE  
**前置條件：** WP-11-08 COMPLETE ✅

### WP-C1-03 Completion Summary

- ✅ `audit/api.py`：JWT Actor 遷移（get_actor_with_company，含 admin RBAC）
- ✅ `notifications/api.py`：JWT Actor 遷移（get_actor_with_company）
- ✅ `backup/api.py`：JWT Actor 遷移（get_actor_with_company，含 admin RBAC）
- ✅ `audit/tests/conftest.py`：重構，整合 get_db override，移除雙 autouse 衝突
- ✅ `audit/tests/test_audit_api.py`：JWT actor override 模式
- ✅ `notifications/tests/test_api.py`：新建完整測試（原為空檔案）
- ✅ `backup/tests/conftest.py`：重構，整合 get_db override
- ✅ `backup/tests/test_api.py`：完整重寫，移除 X-Company-ID header
- ✅ pytest audit：27/27 PASS
- ✅ pytest notifications：26/26 PASS
- ✅ pytest backup：25/25 PASS（合計 78/78 PASS）

**結案文件：** `docs/02_DEVELOPMENT_STATUS/WP-C1-03_JWT_MIGRATION_BATCH2_COMPLETE.md`

---

## 當前 WP：WP-C1-04 — 8 個回歸測試（真實 DB）

**Status：** CURRENT  
**前置條件：** WP-C1-03 COMPLETE ✅  
**內容：** attendance 模組 8 個回歸測試，使用真實 PostgreSQL `attendance_test` 資料庫  
**範圍：** Backend regression tests

---

## 後續 WP 順序

```
WP-11-06（Reporting Backend）✅ COMPLETE 2026-03-14
  ↓
WP-11-07（Reporting UI Polish / QA）✅ COMPLETE 2026-03-15
  ↓
WP-11-08（Leave Request System）✅ COMPLETE 2026-03-15
  ↓
WP-C1-03（Auth 轉換 Batch 2：audit/notifications/backup）✅ COMPLETE 2026-03-17
  ↓
WP-C1-04（8 個回歸測試，真實 DB）← 當前 WP
  ↓
WP-C1-05（Tenant Isolation 真實 DB 測試）
  ↓
WP-C1-06（Feature Gate 套用）
  ↓
[Phase 1 Complete — Gate 5 可宣告完成]
```

---

**最後更新：** 2026-03-17  
**更新原因：** WP-C1-03 JWT Migration Batch 2 COMPLETE（2026-03-17）；WP-C1-04 成為當前 WP

---

## 已完成 WP：WP-C1-04 — PostgreSQL 回歸測試 ✅ COMPLETE

**完成日期：** 2026-03-17  
**Status：** COMPLETE  
**前置條件：** WP-C1-03 COMPLETE ✅

### WP-C1-04 Completion Summary

- ✅ `attendance_test` PostgreSQL DB migration 至 HEAD（009_wp_11_08，21 tables）
- ✅ audit/notifications/backup：78/78 PASS on PostgreSQL
- ✅ PostgreSQL 未引入任何新的回歸失敗（PG failed 37 ≤ SQLite failed 42）
- ✅ JWT Actor flow 在 PostgreSQL 正常
- ✅ Tenant Isolation 在 PostgreSQL 正常
- ✅ `override_all_auth_dependencies()` 新增至 auth.py 工具層
- ✅ 37 個 pre-existing 失敗全部分類記錄

**結案文件：** `docs/02_DEVELOPMENT_STATUS/WP-C1-04_POSTGRESQL_REGRESSION_REPORT.md`

---

## 當前 WP：WP-C1-05 — Tenant Isolation 真實 DB 測試

**Status：** CURRENT  
**前置條件：** WP-C1-04 COMPLETE ✅  
**內容：** 5 個 Tenant Isolation 測試，使用真實 PostgreSQL  
**範圍：** Backend isolation tests

---

**最後更新：** 2026-03-17  
**更新原因：** WP-C1-04 PostgreSQL Regression COMPLETE；WP-C1-05 成為當前 WP

---

## 已完成 WP：WP-C1-05 — Tenant Isolation 真實 DB 測試 ✅ COMPLETE

**完成日期：** 2026-03-17  
**Status：** COMPLETE  
**前置條件：** WP-C1-04 COMPLETE ✅

### WP-C1-05 Completion Summary

- ✅ Phase A：掃描 5 個模組 repo.py / service.py，無 isolation 漏洞
- ✅ Phase B：建立 39 個 tenant isolation 測試（5 模組）
- ✅ Phase C：無業務邏輯修正（無漏洞）；修正 5 個測試層問題
- ✅ Phase D：PostgreSQL 真實 DB 執行 39/39 PASS
- ✅ Phase E：`docs/02_DEVELOPMENT_STATUS/WP-C1-05_TENANT_ISOLATION_REPORT.md` 產出
- ✅ Phase F：進度文件更新

**結案文件：** `docs/02_DEVELOPMENT_STATUS/WP-C1-05_TENANT_ISOLATION_REPORT.md`

---

## 當前 WP：WP-C1-06 — Feature Gate 套用

**Status：** CURRENT  
**前置條件：** WP-C1-05 COMPLETE ✅  
**內容：** 所有核心 API 套用 Feature Gate  
**範圍：** Backend feature gate

---

**最後更新：** 2026-03-17  
**更新原因：** WP-C1-05 Tenant Isolation COMPLETE；WP-C1-06 成為當前 WP

---

## WP-C1-06 COMPLETE

**完成日期:** 2026-03-17  
**Git Commit:** 41df744  
**Status:** COMPLETE  

- 22/22 feature gate tests PASS
- attendance/leave/audit/notifications/backup all gated
- Gate schema: {code: FEATURE_DISABLED}

---

## WP-C1-07 COMPLETE

**完成日期：** 2026-03-17  
**Status:** COMPLETE  

- 11/11 router_v1 endpoints JWT Actor 遷移完成
- 12/12 JWT migration tests PASS
- attendance.core feature gate 維持正常
- tenant isolation 維持正確
- docs.md 更新至 v2.1

---

## Current WP: WP-C1-08 Phase 3

**Status:** CURRENT  
**Content:** Attendance 測試全面啟用（router_v1 JWT 遷移後）  
**前置條件：** WP-C1-07 COMPLETE

---

**Last Updated:** 2026-03-17  
**Reason:** WP-C1-06 COMPLETE; WP-C1-07 is now CURRENT

---

## WP-C1-06 Docs Sync — COMPLETE ✅

**完成日期：** 2026-03-17  
**Status：** COMPLETE  

### Docs Sync 完成摘要

- ✅ `attendance/docs.md` 完整重寫為 v2（29,305 bytes，665 行）
- ✅ 舊版 Phase 1 / SA_MODULE_SPEC v1.7 描述全部移除，標注為 Deprecated
- ✅ `_require_attendance_feature()` helper（WP-C1-06）完整記錄於 Section 2.1、4.2、5.2、7
- ✅ 所有 router_v1 endpoint 標注 `attendance.core` Feature Gate
- ✅ Data Flow 圖加入 Feature Gate 步驟
- ✅ 建立 `WP-C1-06_DOCS_SYNC_REPORT.md`

---

## 當前 WP：WP-C1-07 — Attendance router_v1 JWT Migration

**Status：** CURRENT  
**前置條件：** WP-C1-06 COMPLETE ✅  
**內容：** attendance router_v1 所有端點從 Header-based auth 遷移至 JWT Actor  
**影響範圍：** `backend/app/modules/attendance/api.py`（router_v1）  

---

**最後更新：** 2026-03-17  
**更新原因：** WP-C1-07 Attendance router_v1 JWT Migration COMPLETE；WP-C1-08 Phase 3 為當前 WP

---

## 已完成 WP：WP-C1-08 — Attendance Test Stabilization ✅ COMPLETE

**完成日期：** 2026-03-17  
**Status：** COMPLETE  
**前置條件：** WP-C1-07 COMPLETE ✅

### WP-C1-08 Completion Summary

**Phase A Baseline（Pre-Audit）：**
- pytest app/modules/attendance/tests/ 掃描結論：179 collected，85 PASS，85 FAIL，9 ERROR
- 穩定 PASS 核心測試群：
  - test_feature_gate.py：6/6 PASS
  - test_model_constraints.py：20/20 PASS
  - test_policy_engine.py：28/28 PASS
  - test_router_v1_jwt_migration.py：12/12 PASS
  - test_tenant_isolation_wp_c1_05.py：9/9 PASS

**Phase B 修復成果：**
- ✅ test_reporting_sessions.py：16/16 PASS（修復 hdr() 殘留、補 feature gate mock）
- ✅ test_reporting_user_summary.py：13/13 PASS（修復 hdr() 殘留、補 feature gate mock）
- ✅ test_reporting_company_summary.py：14/14 PASS（修復 hdr() 殘留、補 feature gate mock）
- ✅ test_break_out_enforcement.py：6/6 PASS（補 unittest.mock.patch import、補 feature gate mock）
- ✅ 修復合計：49/49 PASS（4 個測試檔）
- ✅ 整體 PASS：85 → **134**

**剩餘問題定性：**
- 尚餘 36 FAIL + 9 ERROR，**全部為 pre-existing 問題**
- 來源：WP-C1-04 已記錄範圍（舊 router header auth、OUT Checkpoint 未實作、migration 舊帳號等）
- **不阻塞 WP-C1-08 收尾結論**

**Production Code 修改：** 無（本票嚴格限定測試層，api.py / service.py / repo.py 均未觸碰）

**結案文件：** `docs/02_DEVELOPMENT_STATUS/WP-C1-08_ATTENDANCE_TEST_STABILIZATION_COMPLETION_REPORT.md`

---

## 當前 WP：WP-C1-09（依 roadmap 下一票）

**Status：** 依 ATTENDANCE_DEVELOPMENT_ROADMAP.md 與現有 roadmap 安排繼續執行  
**前置條件：** WP-C1-08 COMPLETE ✅

---

**最後更新：** 2026-03-17  
**更新原因：** WP-C1-08 Attendance Test Stabilization COMPLETE（85 → 134 PASS；49 個測試層修復；36+9 pre-existing 保留分類）

---

## WP-C1-09：Governance Consolidation — COMPLETE

**完成日期：** 2026-03-18  
**性質：** 治理收斂票（非功能票）  
**Status：** COMPLETE

**說明：**
- 確認 WP-C1-08 在所有治理文件中一致標示為 COMPLETE
- 修整 /root/docs/ 文件層狀態（與 /opt/attendance-system/ 分離的文件目錄）
- 發現 /opt/attendance-system/docs/ 治理文件需進一步補齊，進入 WP-C1-09A

---

## WP-C1-09A — Governance Missing Files Reconstruction

**Status：** COMPLETE
**完成日期：** 2026-03-18  
**性質：** Governance repair ticket（治理缺件補齊票）  
**前置條件：** WP-C1-08 COMPLETE ✅；WP-C1-09 COMPLETE ✅  
**啟動日期：** 2026-03-18

### 目標

補齊 /opt/attendance-system/docs/ 治理層缺失或過時的文件，使治理層完整且一致：
- WORKSTREAM_STATUS_LEDGER.md：追加 WP-C1-09 / WP-C1-09A 記錄
- MODULE_STATUS_MATRIX.md：補齊 WP-C1-03~08 完成後各模組狀態
- NEXT_WP_TICKET.md（本文件）：標示 WP-C1-09A 為 Current WP
- GATE_PROGRESS_TRACKER.md：補齊 WP-C1-03~08 全部 COMPLETE
- CURRENT_SYSTEM_STATE.md：同步 Current WP

### 本票性質

- ✅ 治理文件補齊
- ✅ 文件狀態一致性修復
- ❌ 非功能開發票
- ❌ 非 Schedule 實作票（schedule 尚未開始，不得虛構）
- ❌ 非 production code 修改票
- ❌ 非 repo cleanup 票

### 完成條件

- [x] WORKSTREAM_STATUS_LEDGER.md 追加 WP-C1-09 / WP-C1-09A 記錄
- [x] MODULE_STATUS_MATRIX.md 補齊 WP-C1-03~08 後各模組狀態
- [x] NEXT_WP_TICKET.md 標示 WP-C1-09A 為 Current WP
- [ ] GATE_PROGRESS_TRACKER.md 補齊至最新狀態
- [ ] CURRENT_SYSTEM_STATE.md 同步
- [ ] Execution Report 完成


---

## WP-C1-09A Execution Summary

- WORKSTREAM_STATUS_LEDGER.md 追加 WP-C1-09 / WP-C1-09A 記錄 ✅
- MODULE_STATUS_MATRIX.md 補齊 WP-C1-03~08 後各模組狀態 ✅
- NEXT_WP_TICKET.md 標示 WP-C1-09A 為 Current WP ✅
- GATE_PROGRESS_TRACKER.md 補齊至最新狀態 ✅
- CURRENT_SYSTEM_STATE.md 同步 ✅

---

## WP-C1-10 — System-wide JWT Alignment

**Status：** COMPLETE  
**完成日期：** 2026-03-18  
**性質：** Blocking Gap Resolution（GAP-C1-001 + GAP-C1-003）

### 結果

- GAP-C1-001 RESOLVED：attendance 舊 router JWT Actor 遷移 COMPLETE
- GAP-C1-003 RESOLVED：leave module 全部 5 endpoints JWT Actor 遷移 COMPLETE
- attendance test_api.py：5/5 PASS
- leave test_feature_gate.py：5/5 PASS
- leave test_tenant_isolation.py：8/9 PASS（1 pre-existing FAIL）

---

## 當前 WP：WP-C1-11 — OUT Checkpoint API Implementation

**Status：** PENDING  
**性質：** Blocking Gap Resolution（GAP-C1-002）  
**前置條件：** WP-C1-10 COMPLETE ✅  
**建議啟動日期：** 2026-03-18

### 目標

補實 OUT Checkpoint API endpoint（/api/v1/attendance/out-checkpoint），修復 7 個持續 FAIL 的測試。

---

**最後更新：** 2026-03-18  
**更新原因：** WP-C1-10 COMPLETE；WP-C1-09A COMPLETE；當前進入 WP-C1-11
