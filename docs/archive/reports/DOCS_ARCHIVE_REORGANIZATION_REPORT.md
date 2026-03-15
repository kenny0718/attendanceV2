# DOCS_ARCHIVE_REORGANIZATION_REPORT.md

**建立日期：** 2026-03-14  
**執行者：** AI session (Cursor)  
**目的：** 安全整理 docs/ 根目錄，把歷史文件搬至 archive/ 子目錄，保留 AI 控制文件在根目錄。

---

## 1. 原始 docs/ 盤點摘要

執行前 docs/ 根目錄共有約 **130+ 個文件**（含子目錄）。

docs/archive/ 整理前已有子目錄：
`dev_history/` `gates/` `notes/` `qa/` `reports/` `spec/` `steps/` `wp_history/`

本次新建 archive 子目錄：
`audit_reports/` `debug_reports/` `location_design/` `roadmap_history/`

---

## 2. KEEP_IN_ROOT 清單（22 個文件）

| 文件 | 說明 |
|------|------|
| AI_CONTEXT.md | AI 讀檔指引（P0 核心）|
| AI_DEVELOPMENT_RULES.md | 文件安全規則 |
| AI_DEVELOPMENT_WORKFLOW.md | AI 開發流程規範（P0 核心）|
| API_DOCUMENTATION_v2.1.md | API 文件 |
| ATTENDANCE_DEVELOPMENT_ROADMAP.md | 開發 Roadmap（P0 核心）|
| ATTENDANCE_LOCATION_MODULE_SPEC.md | Location 模組規格（被 SA v2.1 引用，保留）|
| ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md | Location Policy 規格（被 MODULE_STATUS_MATRIX 引用，保留）|
| ATTENDANCE_REGRESSION_SPEC.md | 回歸測試規格 |
| ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md | 系統架構地圖（P0 核心）|
| ATTENDANCE_UI_UX_PLAN.md | UI/UX 設計文件 |
| backup_restore_audit_design.md | Backup/Restore 設計文件 |
| CURSOR_DEVELOPMENT_RULES.md | Cursor 開發規則（P0 核心）|
| GATE_PROGRESS_TRACKER.md | Gate 進度追蹤（P0 核心）|
| MODULE_STATUS_MATRIX.md | 模組狀態矩陣 |
| NEXT_WP_TICKET.md | 當前 WP 工作票（P0 核心）|
| SA_MODULE_SPEC_v2.1.md | 架構規範 v2.1（P0 核心）|
| SPLIT_SHIFT_DESIGN.md | Split Shift 設計 |
| SYSTEM_BLUEPRINT_SAAS_MULTI_TENANT_v1.md | SaaS 多租戶藍圖 |
| TEST_STRATEGY_MASTER.md | 測試策略主文件 |
| WORKSTREAM_STATUS_LEDGER.md | WP 執行狀態帳本 |
| WP_TEMPLATE.md | WP 文件模板 |
| DOCS_ARCHIVE_REORGANIZATION_REPORT.md | 本報告 |

子目錄（保留）：`WP_TASKS/`（含 4 個 WP spec 文件）、`archive/`

---

## 3. MOVE_TO_ARCHIVE 清單（88 個文件）

### 3.1 docs/archive/wp_history/（53 個）

已完成的 WP 計畫、執行前報告、完成報告：

- ACCEPTANCE_PLAN.md
- ACCEPTANCE_TEST_PLAN.md
- WP-11-04B_GATE_READY_REPORT.md
- WP-11-04B_KICKOFF_PLAN.md
- WP-11-05D_UI_READINESS.md
- WP-11-06_DURATION_CANONICAL_SAFETY_AUDIT.md
- WP-11-06_INDEX_SAFETY_AUDIT.md
- WP-11-06_REPORTING_BOUNDARY_DECISIONS.md
- WP-11-06_REPORTING_FOUNDATION_PREP.md
- WP-11-06_REPORTING_QUERY_GUARDRAILS.md
- WP-11-06_REPORTING_QUERY_PLAN.md
- WP-11-06_REPORTING_QUERY_SAFETY_CHECK.md
- WP-11-06_SAFE_START_PRE_EXECUTION_REPORT.md
- WP-11-06_SESSION_DATE_FEASIBILITY.md
- WP-11-06_STEP1_SESSIONS_IMPLEMENTATION_PLAN.md
- WP-11-06_STEP2_USER_SUMMARY_IMPLEMENTATION_PLAN.md
- WP-11-06_STEP2_USER_SUMMARY_PRE_EXECUTION_REPORT.md
- WP-11-06_STEP3_COMPANY_SUMMARY_IMPLEMENTATION_PLAN.md
- WP-11-06_STEP3_COMPANY_SUMMARY_PRE_EXECUTION_REPORT.md
- WP-11-07_UI_MVP_KICKOFF.md
- WP-11-11.5_TAG_CREATION_GUIDE.md
- WP-11-12_KICKOFF_DESIGN.md
- WP-11-12_PHASE1_COMPLETION_REPORT.md
- WP-11-12_PHASE2A_CODE_CHANGES.md
- WP-11-12_PHASE2B_STATUS_RECONCILIATION_FINAL.md
- WP-11-12_PHASE2_REVISED_STRATEGY.md
- WP-11-13_BLOCKERS_AND_PREREQS.md
- WP-11-13_DEFECT_LOG.md
- WP-11-13_IMPLEMENTATION_PLAN.md
- WP-11-13_LOCATION_POLICY_DESIGN.md
- WP-11-13_LOCATION_POLICY_PREP.md
- WP-11-13_MANUAL_QA_RUNSHEET.md
- WP-11-13_PUNCH_IN_STATE_SYNC_FIX.md
- WP-11-13_STEP3A_FLOW_DIAGRAM.md
- WP-11-13_STEP3A_QUICK_REFERENCE.md
- WP-11-13_STEP3_FRONTEND_INTEGRATION_PLAN.md
- WP-C1-04_ROUTER_FIX_REPORT.md
- WP-C1-04_TEST_ENVIRONMENT_REPORT.md
- WP-C1-05_TEST_SUITE_MIGRATION_PLAN.md
- WP-C1-05_TEST_SUITE_MIGRATION_REPORT.md
- WP-C1-06_MIGRATION_BASELINE_REPORT.md
- WP-C1-07_ATTENDANCE_API_JWT_MIGRATION_REPORT.md
- WP-C1-08_ATTENDANCE_TEST_REENABLE_PLAN.md
- WP-C1-08_FIXTURE_AUDIT_REPORT.md
- WP-C1-08_PHASE1_BASELINE_RESULT.md
- WP-C1-08_PHASE2_IMPLEMENTATION_PLAN.md
- WP-C1-08_REMAINING_FAILURE_RECLASSIFICATION.md
- WP-C1-09_COMPLETION_NOTE.md
- WP-REPORTING-UI_ACCEPTANCE_REPORT.md
- WP-REPORTING-UI_API_FIELD_MAPPING.md
- WP-REPORTING-UI_FIX_B_REPORT.md
- WP-REPORTING-UI_FRONTEND_CHANGESET_PLAN.md
- WP-REPORTING-UI_IMPLEMENTATION_PLAN.md

### 3.2 docs/archive/audit_reports/（21 個）

一次性 audit、系統盤點、closeout 報告：

- ARCHITECTURE_FIX_DECISION.md（2026-03-04，已過期）
- ATTENDANCE_DB_SCHEMA_AUDIT.md
- ATTENDANCE_PHASE1_3_CLOSEOUT_SUMMARY.md
- ATTENDANCE_SYSTEM_AUDIT_REPORT.md
- DOCS_SAFE_ARCHIVE_SCAN.md
- DOCS_STATE_AUDIT_REPORT.md
- GPS_REALITY_VERIFICATION_REPORT.md
- HOMEPAGE_UI_BASELINE_V1_2.md
- MIGRATION_CLEAN_REBUILD_POLICY.md
- OUT_CHECKPOINT_REMOVAL_PLAN.md
- PHASE3_PRE_EXECUTION_REPORT.md
- REALITY_AUDIT_NEXT_ACTIONS.md（2026-03-04，已過期，被 GATE_PROGRESS_TRACKER 取代）
- REALITY_AUDIT_RISK_REPORT.md（2026-03-04，已過期）
- REALITY_AUDIT_STATUS_INVENTORY.md（2026-03-04，已過期，被 MODULE_STATUS_MATRIX 取代）
- SA_REALITY_GAP_REPORT.md（2026-03-04，已過期，被 MODULE_STATUS_MATRIX 取代）
- SA_V21_C1_WORKFLOW_ALIGNMENT_REPORT.md
- SA_v2.1_UPGRADE_NOTE.md
- SYSTEM_DEVELOPMENT_STATUS_REPORT.md（已過期，被 MODULE_STATUS_MATRIX 取代）
- SYSTEM_GROUND_TRUTH.md（2026-03-11，被 MODULE_STATUS_MATRIX 取代）
- SYSTEM_REALITY_REPORT_v2.md
- SYSTEM_VERIFICATION_BASELINE.md

### 3.3 docs/archive/debug_reports/（4 個）

一次性 debug / investigation 報告：

- REPORTING_UI_BLANK_PAGE_INVESTIGATION.md
- WP-REPORTING-BACKEND_INVESTIGATION_REPORT.md
- WP-REPORTING-BACKEND_RUNTIME_MISMATCH_REPORT.md ⚠️ active docs 有引用（見第 6 節）
- WP-REPORTING-UI_IMPLEMENTATION_AUDIT.md ⚠️ active docs 有引用（見第 6 節）

### 3.4 docs/archive/location_design/（5 個）

Location / GPS 設計草稿（非 active spec）：

- ATTENDANCE_LOCATION_API_CONTRACT_DRAFT.md
- ATTENDANCE_LOCATION_DATA_MODEL_OPTIONS.md
- ATTENDANCE_LOCATION_FRONTEND_REFACTOR_PLAN.md
- ATTENDANCE_LOCATION_TEST_PLAN.md
- ATTENDANCE_LOCATION_VALIDATION_PLAN.md

### 3.5 docs/archive/roadmap_history/（5 個）

舊版 Roadmap / 執行入口文件：

- ATTENDANCE_DEVELOPMENT_MASTER_FLOW.md
- CURSOR_EXECUTION_ENTRY.md（已被 AI_DEVELOPMENT_WORKFLOW.md 取代）
- DEVELOPMENT_EXECUTION_PLAN.md
- DEVELOPMENT_MASTER_PLAN.md
- MASTER_DEVELOPMENT_ROADMAP_v2.md（已被 ATTENDANCE_DEVELOPMENT_ROADMAP.md 取代）

---

## 4. REVIEW_NEEDED 清單

無。所有文件已根據內容與引用關係明確分類，不存在無法判斷的文件。

---

## 5. 實際建立的 archive 子目錄

| 目錄 | 狀態 | 文件數 |
|------|------|--------|
| docs/archive/wp_history/ | 已存在 + 本次擴充 | 53 個（本次新增）|
| docs/archive/audit_reports/ | 本次新建 | 21 個 |
| docs/archive/debug_reports/ | 本次新建 | 4 個 |
| docs/archive/location_design/ | 本次新建 | 5 個 |
| docs/archive/roadmap_history/ | 本次新建 | 5 個 |
| docs/archive/dev_history/ | 已存在，未動 | 38 個 |
| docs/archive/gates/ | 已存在，未動 | 11 個 |
| docs/archive/notes/ | 已存在，未動 | 6 個 |
| docs/archive/qa/ | 已存在，未動 | 8 個 |
| docs/archive/reports/ | 已存在，未動 | 51 個 |
| docs/archive/spec/ | 已存在，未動 | 4 個 |
| docs/archive/steps/ | 已存在，未動 | 10 個 |

---

## 6. 被更新引用路徑的 active docs

### 6.1 掃描結果

搬移前掃描 7 個 active docs，發現以下引用：

| Active Doc | 引用的已歸檔文件 | 磁碟狀態 |
|------------|-----------------|----------|
| AI_DEVELOPMENT_WORKFLOW.md | WP-REPORTING-BACKEND_RUNTIME_MISMATCH_REPORT.md | 磁碟為空（0 bytes）|
| ATTENDANCE_DEVELOPMENT_ROADMAP.md | WP-REPORTING-BACKEND_RUNTIME_MISMATCH_REPORT.md、MASTER_DEVELOPMENT_ROADMAP_v2.md | 磁碟為空（0 bytes）|
| NEXT_WP_TICKET.md | WP-REPORTING-BACKEND_RUNTIME_MISMATCH_REPORT.md、WP-REPORTING-UI_IMPLEMENTATION_AUDIT.md | 磁碟為空（0 bytes）|
| GATE_PROGRESS_TRACKER.md | WP-REPORTING-BACKEND_RUNTIME_MISMATCH_REPORT.md | 磁碟為空（0 bytes）|
| AI_CONTEXT.md | MASTER_DEVELOPMENT_ROADMAP_v2.md、REALITY_AUDIT_*、SA_REALITY_GAP_REPORT、ARCHITECTURE_FIX_DECISION | 磁碟為空（0 bytes）|

### 6.2 環境說明與待處理事項

上述 5 個 active docs 在磁碟上均為 **0 bytes**。其內容存在於 Cursor IDE workspace buffer 中，磁碟物理文件是空的。

文件搬移完全不受影響（archive 搬移針對磁碟有真實內容的文件，全部成功執行）。

**使用者需在 IDE 中手動處理的路徑替換：**

| 舊路徑（需替換）| 新路徑 |
|----------------|--------|
| `docs/WP-REPORTING-BACKEND_RUNTIME_MISMATCH_REPORT.md` | `docs/archive/debug_reports/WP-REPORTING-BACKEND_RUNTIME_MISMATCH_REPORT.md` |
| `WP-REPORTING-UI_IMPLEMENTATION_AUDIT.md` | `docs/archive/debug_reports/WP-REPORTING-UI_IMPLEMENTATION_AUDIT.md` |
| `MASTER_DEVELOPMENT_ROADMAP_v2.md` | `docs/archive/roadmap_history/MASTER_DEVELOPMENT_ROADMAP_v2.md` |
| `REALITY_AUDIT_STATUS_INVENTORY.md` | `docs/archive/audit_reports/REALITY_AUDIT_STATUS_INVENTORY.md` |
| `REALITY_AUDIT_RISK_REPORT.md` | `docs/archive/audit_reports/REALITY_AUDIT_RISK_REPORT.md` |
| `REALITY_AUDIT_NEXT_ACTIONS.md` | `docs/archive/audit_reports/REALITY_AUDIT_NEXT_ACTIONS.md` |
| `SA_REALITY_GAP_REPORT.md` | `docs/archive/audit_reports/SA_REALITY_GAP_REPORT.md` |
| `ARCHITECTURE_FIX_DECISION.md` | `docs/archive/audit_reports/ARCHITECTURE_FIX_DECISION.md` |

---

## 7. Broken Reference 檢查

| 範圍 | 