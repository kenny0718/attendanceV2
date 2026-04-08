# Current System State

**建立日期：** 2026-03-17（WP-C1-07 COMPLETE 後更新）  
**基於：** 已確認的 repo scan（2026-03-17）+ pytest 27/28 PASS（1 pre-existing）  
**Repository：** `/opt/attendance-system`

---

## 1. Current WP（當前工作包）

**WP-C1-08 Phase 3 — Attendance 測試全面啟用**

- **Status：** CURRENT（WP-C1-07 已 COMPLETE）
- **內容：** attendance router_v1 JWT 遷移後的測試全面啟用
- **範圍：** Backend tests
- **前置條件：** WP-C1-07 COMPLETE ✅

---

## 2. Next WP（下一個工作包）

**Gate 5 完成宣告**

- **Status：** PLANNED（需 WP-C1-08 Phase 3 完成後）
- **內容：** Gate 5 完成宣告
- **範圍：** 全面驗收

---

## 3. Completed Core Modules（已完成核心模組）

| 模組 | 狀態 | 說明 |
|------|------|------|
| **Punch Engine** | ✅ STABLE | punch-in/out、session 建立、跨午夜規則、tenant isolation |
| **Break Engine** | ✅ STABLE | break-out/break-in、GPS 地點條件式驗證 |
| **Session Model** | ✅ STABLE | AttendanceSession 完整資料模型 |
| **Policy Engine** | ✅ STABLE | 遲到/早退/加班計算、Split Shift 支援 |
| **Timezone / Cross-midnight Rules** | ✅ STABLE | Session ownership = punch_in_time 的 Asia/Taipei 日期 |
| **Reporting Backend API** | ✅ COMPLETE | 三支 endpoint（WP-11-06，2026-03-14）|
| **Home UI** | ✅ STABLE | 主打卡頁、3-Card 佈局、mobile-first |
| **Authentication（JWT）** | ✅ STABLE | JWT-based auth，所有模組含 attendance router_v1 遷移完成（WP-C1-07）|
| **OUT Checkpoint Model/Repo** | ✅ PARTIAL | model/repo 存在，API endpoint 未建（WP-C1-09 gap）|
| **PostgreSQL Migration Chain** | ✅ VERIFIED | 21 tables，head = 009_wp_11_08（WP-C1-04，2026-03-17）|
| **Reporting UI** | ✅ COMPLETE | 三頁 UI（WP-11-07，2026-03-15）|
| **Leave Request System** | ✅ COMPLETE | 5 endpoints，tenant isolation（WP-11-08，2026-03-15）|
| **Auth JWT 遷移（audit/notifications/backup）** | ✅ COMPLETE | 78/78 tests PASS（WP-C1-03，2026-03-17）|
| **PostgreSQL 回歸驗證** | ✅ COMPLETE | 78/78 PASS，migration HEAD 確認（WP-C1-04，2026-03-17）|
| **Tenant Isolation 驗證** | ✅ COMPLETE | 39/39 PASS on PostgreSQL（WP-C1-05，2026-03-17）|
| **Attendance router_v1 JWT 遷移** | ✅ COMPLETE | 11/11 endpoints，12/12 tests PASS（WP-C1-07，2026-03-17）|

---

## 4. Partially Implemented Modules（部分完成模組）

| 模組 | 狀態 | 已完成部分 | 缺口 |
|------|------|-----------|------|
| **OUT Checkpoint API** | ⚠️ PARTIAL | model + repo 存在 | API endpoint 未建（404）|
| **router_v1 JWT 遷移** | ✅ COMPLETE | 所有 11 個 router_v1 endpoints 已遷移至 JWT Actor（WP-C1-07）| 舊版 router（mock-create/approve）維持 Header-based（向後相容）|
| **GPS / Location** | ⚠️ FOUNDATION | break-out 條件式驗證 | punch-in/out/break-in 無 location policy |
| **Feature Gate** | ✅ COMPLETE | 5 modules 22/22 tests PASS | WP-C1-06 COMPLETE 2026-03-17 |

---

## 5. Known Limitations（已知限制）

1. **OUT Checkpoint API 404** — WP-C1-09 只建 model/repo，未建 API endpoint
2. **router_v1 punch-in/punch-out/break-out** — 仍使用舊 X-Company-ID header（WP-C1-07 未完成）
3. **Feature Gate** — ✅ 已完成（WP-C1-06，2026-03-17）
4. **WP-11-13 Manual QA BLOCKED** — 需真實瀏覽器 + PostgreSQL 環境

---

## 6. Gate 5 Progress（開發進度）

**Gate 5 估計完成度：90%**

| 條件 | 狀態 |
|------|------|
| WP-C1-01 PostgreSQL 環境建立 | ✅ VERIFIED |
| WP-11-06 Reporting Backend API | ✅ COMPLETE |
| WP-11-07 Reporting UI Polish / QA | ✅ COMPLETE |
| WP-11-08 Leave Request System | ✅ COMPLETE |
| WP-C1-03 Auth 轉換 Batch 2 | ✅ COMPLETE（2026-03-17）|
| WP-C1-04 PostgreSQL 回歸測試 | ✅ COMPLETE（2026-03-17）|
| WP-C1-05 Tenant Isolation 真實 DB | ✅ COMPLETE（2026-03-17）|
| 所有模組使用 JWT auth | ✅ COMPLETE（WP-C1-07，router_v1 全面 JWT 遷移）|
| Feature Gate 套用 | ✅ COMPLETE（WP-C1-06，2026-03-17）|
| WP-11-13 Manual QA | ⛔ BLOCKED |

---

## 7. Tenant Isolation 狀態（WP-C1-05 結論）

**所有模組 Tenant Isolation 已驗證 ✅**

| 模組 | isolation 狀態 | 測試數 | 結果 |
|------|--------------|--------|------|
| attendance | ✅ VERIFIED | 9 | 9/9 PASS |
| audit | ✅ VERIFIED | 8 | 8/8 PASS |
| notifications | ✅ VERIFIED | 6 | 6/6 PASS |
| backup | ✅ VERIFIED | 6 | 6/6 PASS |
| leave | ✅ VERIFIED | 10 | 10/10 PASS |

**合計：39/39 PASS on PostgreSQL**

---

## 8. Architecture Summary（架構摘要）

- **Frontend：** Vue 3 + Pinia + Axios（mobile-first）
- **Backend：** FastAPI + SQLAlchemy + PostgreSQL
- **Auth：** JWT（Bearer token）
- **Timezone：** Asia/Taipei（cross-midnight 規則）
- **Migration HEAD：** `009_wp_11_08`（21 tables，2026-03-17 verified）

---

**此文件為當前系統狀態的單一真相來源（Single Source of Truth）。**

*本文件由 AI 依據 2026-03-17 實際執行結果更新。*  
*WP-C1-07 COMPLETE：attendance router_v1 JWT Migration，11/11 endpoints，12/12 tests PASS。*

---

## 狀態更新（2026-03-18）— WP-C1-09A Governance Repair

**更新性質：** 治理修復（非 production code 修改）

### Current WP 更新

| 項目 | 舊值（2026-03-17）| 新值（2026-03-18）|
|------|-------------------|-------------------|
| Current WP | WP-C1-08 Phase 3（CURRENT）| WP-C1-09A — Governance Missing Files Reconstruction（IN_PROGRESS）|
| 前一完成 WP | WP-C1-07 | WP-C1-08 COMPLETE（2026-03-17）；WP-C1-09 COMPLETE（2026-03-18）|

### WP-C1-08 正式確認

- **WP-C1-08 Attendance Test Stabilization：COMPLETE（2026-03-17）**
- 134/179 PASS；36 FAIL + 9 ERROR 均為 pre-existing
- Production code 未修改
- 結案文件：`docs/02_DEVELOPMENT_STATUS/WP-C1-08_ATTENDANCE_TEST_STABILIZATION_COMPLETION_REPORT.md`

### Gate 5 進度更新

**Gate 5 估計完成度：~90%**

| 條件 | 狀態 |
|------|------|
| WP-C1-01 PostgreSQL 環境建立 | ✅ VERIFIED（2026-03-11）|
| WP-C1-03 Auth 轉換 Batch 2 | ✅ COMPLETE（2026-03-17，78/78 PASS）|
| WP-C1-04 PostgreSQL 回歸測試 | ✅ COMPLETE（2026-03-17）|
| WP-C1-05 Tenant Isolation 真實 DB | ✅ COMPLETE（2026-03-17，39/39 PASS）|
| WP-C1-06 Feature Gate 套用 | ✅ COMPLETE（2026-03-17，22/22 PASS）|
| WP-C1-07 Attendance JWT 遷移 | ✅ COMPLETE（2026-03-17）|
| WP-C1-08 Attendance Test Stabilization | ✅ COMPLETE（2026-03-17）|
| WP-C1-09 Governance Consolidation | ✅ COMPLETE（2026-03-18）|
| WP-11-06 Reporting Backend API | ✅ COMPLETE（2026-03-14）|
| WP-11-07 Reporting UI Polish / QA | ✅ COMPLETE（2026-03-15）|
| WP-11-08 Leave Request System | ✅ COMPLETE（2026-03-15）|
| WP-11-13 Manual QA | ⛔ BLOCKED（pre-existing）|
| leave JWT Actor 遷移 | ⚠️ PENDING（尚無對應 WP）|

### Known Limitations 更新

舊版 §5 Known Limitations 中：
- 第 2 條「router_v1 punch-in/punch-out/break-out 仍使用 X-Company-ID header」— **已由 WP-C1-07 解決（COMPLETE）**
- 第 3 條「Feature Gate — 待完成」— **已由 WP-C1-06 解決（COMPLETE，22/22 PASS）**

補充已知限制：
- leave 模組使用舊式 Header auth（JWT Actor 遷移尚無對應 WP）
- leave 模組無自動化測試（manual test PASS，pre-existing）

---

**最後更新：** 2026-03-18  
**更新原因：** WP-C1-09A Governance Repair — 同步 WP-C1-08 COMPLETE 狀態，更新 Current WP 為 WP-C1-09A


---

## 狀態更新（2026-03-18）— WP-S1-01 Schedule Module Foundation

**更新性質:** Gate 6 啟動；Schedule 模組 Foundation 建立

### Current WP 更新

| 項目 | 舊值 | 新值（2026-03-18）|
|------|------|-------------------|
| Gate | Gate 5 / C1（CLOSED）| Gate 6 — Schedule 模組開發（IN_PROGRESS）|
| Current WP | WP-C1-13（COMPLETE）| WP-S1-01 COMPLETE；WP-S1-02 為下一票 |

### WP-S1-01 正式確認

- **WP-S1-01 Schedule Module Foundation: COMPLETE（2026-03-18）**
- 7 個骨架檔案建立（__init__, models, schemas, repo, service, api, docs.md）
- ShiftTemplate + ShiftAssignment ORM 定義（code-level only，無 migration）
- Smoke test PASS（import OK）
- production code 未修改
- 結案文件: docs/WP-S1-01_EXECUTION_REPORT.md

### Gate 6 進度

| WP | 名稱 | 狀態 |
|----|------|------|
| WP-S1-01 | Schedule Module Foundation | COMPLETE（2026-03-18）|
| WP-S1-02 | Schedule Migration | PENDING |
| WP-S1-03+ | Basic API / Tests / Feature Gate | PENDING |

### Schedule 模組現況

- 模組位置: backend/app/modules/schedule/
- 資料表: 尚未建立（需 WP-S1-02 Migration）
- API endpoint: 無（需 WP-S1-03）
- 主 app 掛載: 無（需 WP-S1-03）

---

**最後更新:** 2026-03-18  
**更新原因:** WP-S1-01 COMPLETE；Gate 6 Schedule 模組開發啟動


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

## System State Update (2026-03-18) — WP-S1-02 Complete

### Database State
- alembic_version: `010_wp_s1_02`
- Total tables: 23 (21 existing + shift_templates + shift_assignments)
- New tables: `shift_templates`, `shift_assignments`

### Schedule Module State
- Migration: APPLIED (010_wp_s1_02)
- Models: ALIGNED (WP-S1-01A)
- Schemas: UUID ALIGNED (WP-S1-02)
- Router: stub (not mounted)
- API: NO endpoints live
- repo/service: stub (raise NotImplementedError)

### What Is NOT Done (Schedule)
- No CRUD endpoints
- No router mounted in main.py
- No repo.py / service.py implementation
- No attendance / leave integration

**最後更新:** 2026-03-18  
**更新原因:** WP-S1-02 COMPLETE

---

## System State Update (2026-03-19) — WP-S1-02B Complete

### Alembic Infrastructure State
- alembic_version: `010_wp_s1_02` (head)
- env.py: STABLE（5464 bytes，正式版）
- env.py coverage: 8/8 modules, 23 tables
- ALEMBIC SAFE: YES

### What Was Fixed
- env.py 從 0 bytes 重建為完整正式版
- auth / audit / tenants / customer_service 4 個模組首次正式納入 env.py
- .tmp 殘留檔清除

### Current DB Tables (23)
allowed_locations, attendance_out_checkpoints, attendance_policies,
attendance_punches, attendance_records, attendance_sessions,
alembic_version, audit_logs, audit_retention_policies,
company_entitlements, leave_approval_logs, leave_approval_policies,
leave_requests, leave_types, notifications, permissions,
role_permissions, roles, shift_assignments, shift_templates,
support_company_assignments, tenants, user_company_memberships, users

### Schedule Module State (unchanged from WP-S1-02)
- Migration: APPLIED (010_wp_s1_02)
- Router: stub (not mounted)
- API: NO endpoints live
- repo/service: stub (raise NotImplementedError)

**最後更新:** 2026-03-19  
**更新原因:** WP-S1-02B COMPLETE — Alembic infrastructure stabilized

---

## System State Update (2026-03-19) — WP-S1-03 Complete

### Schedule Module State
- Migration: APPLIED (010_wp_s1_02)
- repo.py: CRUD CORE (ShiftTemplate + ShiftAssignment, Tenant Isolation)
- service.py: CRUD CORE (業務邏輯 + error handling)
- Router: stub (not mounted)
- API: NO endpoints live
- Smoke Test: 15/15 PASS

### What Is NOT Done (Schedule)
- No API router mounted in main.py
- No FastAPI endpoints live
- No pytest full coverage
- No conflict detection
- No attendance/leave integration

**最後更新:** 2026-03-19  
**更新原因:** WP-S1-03 COMPLETE — CRUD Core implemented

---

## System State Update (2026-03-19) — WP-S1-04A Complete

### Schedule Module State
- Migration: APPLIED (010_wp_s1_02)
- repo.py: CRUD CORE
- service.py: CRUD CORE
- api.py: API LAYER READY (11 endpoints, router not mounted)
- Router: defined but NOT mounted in main.py
- API: NOT live (pending WP-S1-04B)

### Pending (Schedule)
- WP-S1-04B: main.py router mount + feature gate
- Frontend 串接
- pytest integration tests

**最後更新:** 2026-03-19  
**更新原因:** WP-S1-04A COMPLETE — API layer ready, pending mount

---

## System State Update (2026-03-19) — WP-S1-04B Complete

### Schedule Module State
- Migration: APPLIED (010_wp_s1_02)
- repo.py: CRUD CORE
- service.py: CRUD CORE
- api.py: MOUNTED + FEATURE GATED (11 endpoints)
- Router: LIVE in main.py
- Feature Key: schedule.core (defined)
- JWT auth: active (401 no-auth)
- Feature gate: active (403 if schedule.core disabled)

### Pending (Schedule)
- company_entitlements: schedule.core not yet set in DB
- Frontend 串接
- pytest integration tests
- Advanced scheduling features

**最後更新:** 2026-03-19  
**更新原因:** WP-S1-04B COMPLETE — Schedule fully mounted

---

## System State Update (2026-03-19) -- WP-S1-06 Complete

### Schedule Module State (WP-S1-06 complete)
- Migration: APPLIED (010_wp_s1_02)
- repo.py: CRUD CORE
- service.py: CRUD CORE
- api.py: MOUNTED + FEATURE GATED (11 endpoints)
- Router: LIVE in main.py
- Feature Key: schedule.core (defined + verified)
- Entitlement path: CONFIRMED (company_entitlements table)
- Real JWT auth: VERIFIED (HS256, full dependency chain)
- Integration tests (WP-S1-05): 12/12 PASS
- Real JWT E2E tests (WP-S1-06): 14/14 PASS

### What Is NOT Done (Schedule)
- PLAN_DEFAULTS does not include schedule.core (opt-in; WP-S1-07)
- Production/Staging entitlement seeding (ops work; WP-S1-07)
- Frontend Schedule UI (future WP)
- Advanced scheduling: conflict detection, bulk assign, recurring rules
- Attendance/Leave integration

### Current WP
WP-S1-06 COMPLETE. Next: WP-S1-07 (Production Rollout Prep) or Frontend Schedule WP.

**Last Updated:** 2026-03-19
**Reason:** WP-S1-06 Real JWT E2E COMPLETE (14/14 PASS)
