# MODULE_STATUS_MATRIX.md

## Purpose

各模組的權威狀態表。每個狀態欄位明確區分 DOC_COMPLETE / CODE_COMPLETE / VERIFIED 三種層次，不得混用。

## Scope

覆蓋所有已實作模組（7 個）與缺少模組（7 個）。

## Source of Truth

- CODE SCAN（主要）：直接讀取程式碼、migration、測試檔案
- DOCS（對照）：docs/ 目錄
- RUNTIME VERIFICATION：WP-C1-01（2026-03-11）部分執行

## Last Updated

2026-03-11（WP-C1-01 完成後更新）

---

## 狀態定義

| 標籤 | 定義 |
|------|------|
| `DOC_COMPLETE` | 規格文件存在且完整，但程式碼未實作或未驗證 |
| `CODE_COMPLETE` | 程式碼已實作，但未在真實環境執行驗證 |
| `VERIFIED` | 已在真實環境（真實 PostgreSQL + 真實請求）執行並確認正確 |
| `MISSING` | 完全缺失，規格文件也無詳細定義 |
| `PARTIAL` | 部分實作，有明確缺口 |
| `DEPRECATED` | 已廢棄或已移除 |

---

## A. 已實作模組狀態矩陣

### A1. auth 模組

| 面向 | 狀態 | 缺口說明 |
|------|------|----------|
| **目標定位** | Platform-First Identity，JWT 登入，User/Role/Permission 管理 | - |
| **spec 狀態** | `CODE_COMPLETE` | SA_MODULE_SPEC v2.1 有定義；無獨立 docs.md |
| **backend 結構** | `CODE_COMPLETE` | api.py / service.py / repo.py / models.py / schemas.py 齊全 |
| **migration** | `CODE_COMPLETE` | 3532deda024c_create_auth_tables_v2_platform_first |
| **tests** | `CODE_COMPLETE` | test_login_api.py, test_repo.py（共 2 files）；未在真實 DB 驗證 |
| **auth 方式** | `CODE_COMPLETE` | JWT Bearer（login endpoint 本身無需 auth） |
| **tenant isolation** | `CODE_COMPLETE` | users 為 global（無 company_id）；memberships 有 company_id |
| **RBAC** | `CODE_COMPLETE` | roles/permissions/user_roles 已建立；但 RBAC 在 endpoint 層未強制套用 |
| **feature gate** | `MISSING` | 未套用 |
| **runtime verification** | `MISSING` | 未在真實 DB 執行登入流程驗證 |
| **完成度（保守）** | 80% | |
| **主要風險** | 無獨立 docs.md；RBAC 在 API 層未強制；runtime 未驗證 |
| **可進入下一階段** | ✅ 可，但需補 runtime verification |
| **建議優先級** | P1 |

---

### A2. tenants 模組

| 面向 | 狀態 | 缺口說明 |
|------|------|----------|
| **目標定位** | Tenant 管理、Entitlements CRUD、Feature Flag 控制 | - |
| **spec 狀態** | `CODE_COMPLETE` | SA_MODULE_SPEC v2.1 有定義；無獨立 docs.md |
| **backend 結構** | `CODE_COMPLETE` | api.py / service.py / repo.py / models.py / schemas.py 齊全 |
| **migration** | `CODE_COMPLETE` | 004_create_tenants + wp_11_04a_entitlements |
| **tests** | `CODE_COMPLETE` | test_entitlements_api.py, test_repo.py, test_service.py（3 files） |
| **auth 方式** | `CODE_COMPLETE` | JWT Bearer + `get_current_actor()` ✅ |
| **tenant isolation** | `CODE_COMPLETE` | 所有查詢帶 company_id |
| **RBAC** | `CODE_COMPLETE` | `assert_company_scope()` 已套用 |
| **feature gate** | `PARTIAL` | Feature Gate 基礎設施完整；entitlements API 本身不需 feature gate |
| **runtime verification** | `MISSING` | 未在真實 DB 驗證 |
| **完成度（保守）** | 85% | |
| **主要風險** | runtime 未驗證；docs.md 缺失 |
| **可進入下一階段** | ✅ 可 |
| **建議優先級** | P1 |

---

### A3. attendance 模組

| 面向 | 狀態 | 缺口說明 |
|------|------|----------|
| **目標定位** | 打卡核心（punch-in/out）、break-out/in、Session 管理、Policy Engine、Location Policy | - |
| **spec 狀態** | `DOC_COMPLETE` | SA_MODULE_SPEC v2.1 + ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md |
| **backend 結構** | `CODE_COMPLETE` | api.py / service.py / repo.py / models.py / schemas.py / policy_engine.py / 
---

## WP-C1-08 Attendance Test Stabilization — 完成狀態更新（2026-03-17）

### attendance 模組測試層狀態更新

**更新依據：** WP-C1-08 Phase B COMPLETE（2026-03-17）

| 面向 | 舊狀態 | 新狀態（WP-C1-08 後） | 說明 |
|------|--------|----------------------|------|
| **attendance 測試層（reporting）** | FAIL（hdr() 殘留）| `VERIFIED` | test_reporting_sessions 16/16、test_reporting_user_summary 13/13、test_reporting_company_summary 14/14 PASS |
| **attendance 測試層（break-out enforcement）** | FAIL（feature gate 未 mock）| `VERIFIED` | test_break_out_enforcement 6/6 PASS |
| **attendance 測試層（穩定核心）** | PASS（Phase A）| `VERIFIED`（維持）| feature_gate 6/6、model_constraints 20/20、policy_engine 28/28、router_v1_jwt 12/12、tenant_isolation 9/9 |
| **attendance 測試層（整體）** | 85/179 PASS | 134/179 PASS | 36 FAIL + 9 ERROR 為 pre-existing，不影響本票收尾 |

### attendance 模組 A3 狀態矩陣補充說明

| 面向 | 狀態 | 說明 |
|------|------|------|
| **tests（reporting 層）** | `VERIFIED`（WP-C1-08 COMPLETE）| test_reporting_sessions / user_summary / company_summary 均 PASS；hdr() 遷移完整 |
| **tests（break-out enforcement）** | `VERIFIED`（WP-C1-08 COMPLETE）| feature gate mock 補齊，6/6 PASS |
| **tests（pre-existing 剩餘）** | `PARTIAL`（PRE-EXISTING）| 36 FAIL + 9 ERROR，來源 WP-C1-04；不屬於本票範圍 |
| **WP-C1-08 結論** | `COMPLETE` | 本票範圍內測試穩定化完成；不進入 Phase C |

**Last Updated:** 2026-03-17（WP-C1-08 COMPLETE 後同步更新）

---

## WP-C1-09A Governance Reconstruction — 模組狀態全面補齊（2026-03-18）

**更新依據：** WP-C1-03、WP-C1-04、WP-C1-05、WP-C1-06、WP-C1-07、WP-C1-08 全部 COMPLETE（2026-03-17）  
**更新性質：** 治理補齊（Governance repair），不修改任何 production code  
**Source：** WORKSTREAM_STATUS_LEDGER.md（2026-03-17 記錄）

---

### 更新後各模組狀態矩陣（截至 2026-03-18）

| 模組 | Functional Status | Auth Status | Test Status | Governance Status | Notes |
|------|-------------------|-------------|-------------|-------------------|-------|
| **auth** | CODE_COMPLETE | JWT（login 本身無需 auth）| CODE_COMPLETE | LEDGER 記錄至 WP-11-04A | RBAC 在 API 層未強制套用；runtime 未驗證 |
| **tenants** | CODE_COMPLETE | JWT + get_current_actor() | CODE_COMPLETE | LEDGER 記錄 | runtime 未驗證 |
| **attendance** | VERIFIED | JWT Actor（router_v1，WP-C1-07）| PARTIAL（134/179 PASS）| WP-C1-08 COMPLETE | 36 FAIL + 9 ERROR 為 pre-existing；reporting/break-out enforcement 已修復 |
| **audit** | CODE_COMPLETE | JWT Actor（WP-C1-03）| VERIFIED（27/27 PASS）| WP-C1-03 COMPLETE | 78/78 PASS（含 notifications/backup）；E2E 未驗證 |
| **notifications** | CODE_COMPLETE | JWT Actor（WP-C1-03）| VERIFIED（26/26 PASS）| WP-C1-03 COMPLETE | 同上 |
| **backup** | CODE_COMPLETE | JWT Actor（WP-C1-03）| VERIFIED（25/25 PASS）| WP-C1-03 COMPLETE | 同上 |
| **leave** | COMPLETE | 舊式 Header auth（待遷移）| NOT STARTED（無 tests 目錄）| WP-11-08 COMPLETE | 5 endpoints manual PASS；JWT Actor 遷移尚無對應 WP |
| **customer_service** | CODE_COMPLETE | unknown | unknown | LEDGER 無詳細記錄 | 模組存在；詳細狀態待稽核 |
| **schedule** | NOT STARTED | N/A | N/A | NOT STARTED | 無任何 implementation 證據；不得寫成 in progress |

---

### Tenant Isolation 狀態（WP-C1-05 結論）

| 模組 | Isolation 狀態 | 測試數 | 結果 |
|------|--------------|--------|------|
| attendance | VERIFIED | 9 | 9/9 PASS on PostgreSQL |
| audit | VERIFIED | 8 | 8/8 PASS on PostgreSQL |
| notifications | VERIFIED | 6 | 6/6 PASS on PostgreSQL |
| backup | VERIFIED | 6 | 6/6 PASS on PostgreSQL |
| leave | VERIFIED | 10 | 10/10 PASS on PostgreSQL |
| **合計** | **VERIFIED** | **39** | **39/39 PASS** |

---

### Feature Gate 狀態（WP-C1-06 結論）

| 模組 | Feature Gate | Gate Key | 測試 |
|------|-------------|----------|------|
| attendance | COMPLETE | attendance.core | 6/6 PASS |
| leave | COMPLETE | leave.core | verified |
| audit | COMPLETE | audit.core | verified |
| notifications | COMPLETE | notifications.core | verified |
| backup | COMPLETE | backup.core | verified |
| **合計** | **22/22 PASS** | - | - |
| auth / tenants / customer_service | NOT GATED | 設計決策，非缺口 | - |
| schedule | NOT STARTED | 無 implementation | - |

---

### Known Gaps（已知缺口，Out of Scope for WP-C1-09A）

| 缺口 | 模組 | 說明 | 是否阻塞 |
|------|------|------|----------|
| leave JWT Actor 遷移 | leave | 目前使用 Header auth；尚無對應 WP | 否（pre-existing）|
| leave 自動化測試 | leave | 無 tests 目錄；WP-11-08 僅有 manual test | 否（pre-existing）|
| auth runtime 驗證 | auth | 登入流程未在真實 DB 驗證 | 否（pre-existing）|
| tenants runtime 驗證 | tenants | 未在真實 DB 驗證 | 否（pre-existing）|
| customer_service 詳細狀態 | customer_service | LEDGER 無詳細記錄，需獨立稽核 | 否（observation）|
| attendance 36 FAIL + 9 ERROR | attendance | 全部 pre-existing，WP-C1-04 已分類 | 否（pre-existing）|
| schedule 未實作 | schedule | 無任何 implementation，不在當前 roadmap 範圍 | 否（planned）|

---

### Reconstruction Note

本矩陣依以下來源重建：
- WORKSTREAM_STATUS_LEDGER.md（主要來源，2026-03-17）
- GATE_PROGRESS_TRACKER.md（補充）
- CURRENT_SYSTEM_STATE.md（補充）
- WP-C1-03/04/05/06/07/08 各別結案文件（交叉比對）

對於缺乏直接文件證據之處（customer_service），採保守標示（unknown / observation only）。
本次更新為治理補齊，不代表 code 層有任何修改。

**Last Updated:** 2026-03-18  
**Updated by:** WP-C1-09A Governance Missing Files Reconstruction


---

## WP-S1-01 Schedule Foundation — 模組狀態新增（2026-03-18）

**更新依據:** WP-S1-01 COMPLETE（2026-03-18）  
**更新性質:** 新模組加入矩陣（foundation only）

### schedule 模組狀態（新增）

| 面向 | 狀態 | 說明 |
|------|------|------|
| **目標定位** | 班別模板管理 + 班別指派 | ShiftTemplate / ShiftAssignment |
| **backend 結構** | FOUNDATION | 7 個骨架檔案建立；所有 repo/service 方法為 stub |
| **migration** | NOT_STARTED | 無 Alembic migration；資料表尚未建立 |
| **tests** | NOT_STARTED | 無測試檔案 |
| **auth 方式** | NOT_STARTED | 無 API endpoint；auth 尚未套用 |
| **tenant isolation** | DESIGN_ONLY | models 含 company_id 欄位；查詢層未實作 |
| **feature gate** | NOT_STARTED | 無 gate 定義 |
| **runtime verification** | NOT_STARTED | 無任何 runtime 驗證 |
| **完成度（保守）** | 5% | Foundation skeleton only |
| **主要風險** | 無 migration；無 API；所有方法 NotImplementedError |
| **可進入下一階段** | 需先完成 WP-S1-02 Migration |
| **建議優先級** | WP-S1-02 Migration（下一票）|

**Last Updated:** 2026-03-18  
**Updated by:** WP-S1-01 Schedule Module Foundation


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

## Schedule Module Status Update (2026-03-18)

| Item | WP-S1-01 | WP-S1-01A | WP-S1-02 |
|------|----------|-----------|----------|
| models.py | DONE | ALIGNED | — |
| schemas.py | DONE | — | UUID ALIGNED |
| Migration | — | — | DONE |
| shift_templates table | — | — | CREATED |
| shift_assignments table | — | — | CREATED |
| env.py schedule import | — | — | ADDED |
| router.py | stub | stub | stub |
| repo.py | stub | stub | stub |
| service.py | stub | stub | stub |
| main.py mount | NO | NO | NO |
| API endpoints | NO | NO | NO |

**Overall Schedule Module Status:** MIGRATION COMPLETE, CRUD PENDING (WP-S1-03)

**最後更新:** 2026-03-18

---

## Alembic Infrastructure Status Update (2026-03-19) — WP-S1-02B

| Module | models.py | Migration | env.py納入(WP-S1-02) | env.py納入(WP-S1-02B) |
|--------|-----------|-----------|---------------------|----------------------|
| auth | YES | YES | NO | **YES** |
| attendance | YES | YES | YES | YES |
| audit | YES | YES | NO | **YES** |
| leave | YES | YES | YES | YES |
| notifications | YES | YES | YES | YES |
| schedule | YES | YES | YES | YES |
| tenants | YES | YES | NO | **YES** |
| customer_service | YES | YES | NO | **YES** |
| backup | NO | — | NO | NO (不需要) |

**env.py Coverage: 8/8 (100%) — ALEMBIC SAFE = YES**

**最後更新:** 2026-03-19

---

## Schedule Module Status Update (2026-03-19) — WP-S1-03

| Item | WP-S1-01 | WP-S1-01A | WP-S1-02 | WP-S1-02B | WP-S1-03 |
|------|----------|-----------|----------|-----------|----------|
| models.py | DONE | ALIGNED | — | — | — |
| schemas.py | DONE | — | UUID ALIGNED | — | — |
| Migration | — | — | DONE | — | — |
| env.py | — | — | PARTIAL | COMPLETE | — |
| repo.py | stub | stub | stub | stub | **CRUD CORE** |
| service.py | stub | stub | stub | stub | **CRUD CORE** |
| router.py | stub | stub | stub | stub | stub |
| main.py mount | NO | NO | NO | NO | NO |
| API endpoints | NO | NO | NO | NO | NO |
| Smoke Test | — | — | — | — | 15/15 PASS |

**最後更新:** 2026-03-19
