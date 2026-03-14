# Docs Safe Archive Scan Report

**日期：** 2026-03-10
**範圍：** docs/ 根目錄（不含 archive/ 子目錄）
**目的：** 安全掃描，分類所有文件，僅分析不移動

**掃描檔案數：** 63

---

## KEEP_CORE (26 個)

*核心治理、架構規範、功能規格，絕對保留*

| 檔案 | 原因 |
|------|------|
| AI_CONTEXT.md | AI 工具讀取優先級指引，P0 治理文件 |
| AI_DEVELOPMENT_RULES.md | AI 開發規則，P0 治理文件 |
| API_DOCUMENTATION_v2.0.md | API 合約文件，開發必備 |
| ARCHITECTURE_FIX_DECISION.md | 架構修正決策，P1 決策文件 |
| ATTENDANCE_DEVELOPMENT_MASTER_FLOW.md | Gate 5 WP 執行順序唯一權威 |
| ATTENDANCE_LOCATION_MODULE_SPEC.md | Location 模組規格，功能規格文件 |
| ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md | Location Policy 規格，功能規格文件 |
| ATTENDANCE_REGRESSION_SPEC.md | 回歸測試規格，WP-11-05 必備 |
| ATTENDANCE_UI_UX_PLAN.md | UI/UX 計畫，前端開發參考 |
| backup_restore_audit_design.md | Backup/Restore 設計文件，功能規格 |
| GATE_PROGRESS_TRACKER.md | Gate 進度追蹤，核心治理文件（需重建） |
| MASTER_DEVELOPMENT_ROADMAP_v2.md | 開發路線圖唯一權威，31 WP / 6 Phase |
| MIGRATION_CLEAN_REBUILD_POLICY.md | Migration 重建政策，架構規範 |
| NEXT_WP_TICKET.md | 下一個 WP 工作票，核心治理文件 |
| REALITY_AUDIT_NEXT_ACTIONS.md | 行動計畫，P1 現況文件 |
| REALITY_AUDIT_RISK_REPORT.md | 風險評估報告，P1 現況文件 |
| REALITY_AUDIT_STATUS_INVENTORY.md | 系統現況盤點，P1 現況文件 |
| SA_MODULE_SPEC_v2.0.md | 唯一架構規範 v2.0，P0 絕對核心 |
| SA_REALITY_GAP_REPORT.md | 規格與現況差異分析，P1 現況文件 |
| SPLIT_SHIFT_DESIGN.md | Split Shift 設計文件，功能規格 |
| SYSTEM_BLUEPRINT_SAAS_MULTI_TENANT_v1.md | SaaS 多租戶系統藍圖，架構參考 |
| WP-11-13_DEFECT_LOG.md | WP-11-13 缺陷記錄，Manual QA 進行中仍需要 |
| WP-11-13_IMPLEMENTATION_PLAN.md | WP-11-13 實作計畫，仍在進行中 |
| WP-11-13_LOCATION_POLICY_DESIGN.md | Location Policy 設計，功能規格文件 |
| WP-11-13_MANUAL_QA_RUNSHEET.md | Manual QA 執行表，QA 尚未完成仍需要 |
| WP-11-13_BLOCKERS_AND_PREREQS.md | WP-11-13 阻塞項目，Manual QA 仍需要 |

## KEEP_FOR_NOW (19 個)

*設計/計畫/背景文件，近期仍需要*

| 檔案 | 原因 |
|------|------|
| ATTENDANCE_LOCATION_API_CONTRACT_DRAFT.md | Location API 合約草稿，Phase 2 前端開發仍需參考 |
| ATTENDANCE_LOCATION_DATA_MODEL_OPTIONS.md | Location 資料模型選項，已決策但保留背景 |
| ATTENDANCE_LOCATION_FRONTEND_REFACTOR_PLAN.md | Location 前端重構計畫，尚未完全執行 |
| ATTENDANCE_LOCATION_TEST_PLAN.md | Location 測試計畫，Manual QA 未完成前仍需要 |
| ATTENDANCE_LOCATION_VALIDATION_PLAN.md | Location 驗證計畫，Manual QA 未完成前仍需要 |
| DOCS_STATE_AUDIT_REPORT.md | 本 session 的審計報告，近期參考用 |
| GPS_REALITY_VERIFICATION_REPORT.md | GPS 現況驗證報告，近期參考用 |
| HOMEPAGE_UI_BASELINE_V1_2.md | 首頁 UI 基準規範 V1.2，前端開發保護文件 |
| HOME_UI2_REFACTOR_PLAN.md | Home UI 2.0 重構計畫，Phase 4 工作 |
| OUT_CHECKPOINT_REMOVAL_PLAN.md | OUT Checkpoint 移除計畫，已執行但保留背景 |
| WP-11-04B_KICKOFF_PLAN.md | WP-11-04B 啟動計畫，AI_CONTEXT.md 中引用 |
| WP-11-04B_GATE_READY_REPORT.md | Gate Ready 報告，AI_CONTEXT.md 中引用 |
| WP-11-12_KICKOFF_DESIGN.md | WP-11-12 初始設計，已完成但仍有設計參考價值 |
| WP-11-12_PHASE2_REVISED_STRATEGY.md | Phase 2 修正策略，設計決策背景 |
| WP-11-13_LOCATION_POLICY_PREP.md | Location Policy 準備文件，背景資料 |
| WP-11-13_STEP3_FRONTEND_INTEGRATION_PLAN.md | Step 3 Frontend 整合計畫，設計參考 |
| WP-11-13_STEP3A_FLOW_DIAGRAM.md | Step 3A Flow 圖，技術參考 |
| WP-11-13_STEP3A_QUICK_REFERENCE.md | Step 3A 快速參考，WP-11-13 仍未完全關閉 |
| WP-11-13_PUNCH_IN_STATE_SYNC_FIX.md | Punch-in 狀態同步修復，設計決策記錄 |

## SAFE_TO_ARCHIVE (18 個)

*可安全歸檔的報告/記錄/已完成 WP 文件*

| 檔案 | 原因 |
|------|------|
| ATTENDANCE_ARCH_VALIDATION_REPORT.md | 架構驗證報告，已完成的報告類文件 |
| ATTENDANCE_GPS_LEGACY_CLEANUP_PLAN.md | GPS Legacy 清理計畫，清理已執行完畢 |
| DOCS_ARCHIVE_LOG.md | Archive 操作記錄，應放入 archive/ 本身 |
| GATE_PROGRESS_TRACKER.md.backup | GATE_TRACKER 舊備份，可歸檔 |
| GIT_CLEANUP_BEFORE_TIMEZONE_REFACTOR.md | Git 清理指令記錄，操作已完成 |
| GIT_TAG_WP-11-11.5_COMMANDS.md | Git tag 指令記錄，操作已完成 |
| HOMEPAGE_BACKUP_CLEANUP_RECOMMENDATION.md | 首頁備份清理建議，清理已執行 |
| HOMEPAGE_PROTECTION_BASELINE_COMPLETION_REPORT.md | 首頁保護基準完成報告，報告類文件 |
| MASTER_DEVELOPMENT_ROADMAP.md | Roadmap v1，已被 v2 取代 |
| MILESTONE_WP-11-11.5_CODE_CLEANUP_COMPLETE.md | WP-11-11.5 Milestone 記錄，已關閉 |
| MILESTONE_WP-11-11.5_COMMIT.txt | WP-11-11.5 Commit 記錄，已關閉 |
| TIMEZONE_REFACTOR_READINESS.md | Timezone 重構準備文件，非當前工作 |
| WP-11-05D_UI_READINESS.md | WP-11-05D UI 準備度，WP 已完成 |
| WP-11-07_UI_MVP_KICKOFF.md | WP-11-07 UI MVP 啟動，WP 已完成 |
| WP-11-11.5_TAG_CREATION_GUIDE.md | WP-11-11.5 Tag 建立指南，WP 已關閉 |
| WP-11-12_PHASE1_COMPLETION_REPORT.md | WP-11-12 Phase 1 完成報告，WP 已關閉 |
| WP-11-12_PHASE2A_CODE_CHANGES.md | WP-11-12 Phase 2A 程式碼變更記錄，已完成 |
| WP-11-12_PHASE2B_STATUS_RECONCILIATION_FINAL.md | WP-11-12 Phase 2B 狀態對齊最終版，已關閉 |

## REVIEW_NEEDED (0 個)

*不確定，保守保留待人工確認*

| 檔案 | 原因 |
|------|------|

---

## DIRECT_ARCHIVE_CANDIDATES

以下檔案分類為 SAFE_TO_ARCHIVE，可在下一步操作中移動至 docs/archive/。
**注意：本報告不執行任何移動操作。**

| # | 檔案名稱 | 建議目的地 | 原因 |
|---|----------|-----------|------|
| 1 | ATTENDANCE_ARCH_VALIDATION_REPORT.md | docs/archive/reports/ | 架構驗證報告，已完成的報告類文件 |
| 2 | ATTENDANCE_GPS_LEGACY_CLEANUP_PLAN.md | docs/archive/reports/ | GPS Legacy 清理計畫，清理已執行完畢 |
| 3 | DOCS_ARCHIVE_LOG.md | docs/archive/reports/ | Archive 操作記錄，應放入 archive/ 本身 |
| 4 | GATE_PROGRESS_TRACKER.md.backup | docs/archive/reports/ | GATE_TRACKER 舊備份，可歸檔 |
| 5 | GIT_CLEANUP_BEFORE_TIMEZONE_REFACTOR.md | docs/archive/dev_history/ | Git 清理指令記錄，操作已完成 |
| 6 | GIT_TAG_WP-11-11.5_COMMANDS.md | docs/archive/wp_history/ | Git tag 指令記錄，操作已完成 |
| 7 | HOMEPAGE_BACKUP_CLEANUP_RECOMMENDATION.md | docs/archive/reports/ | 首頁備份清理建議，清理已執行 |
| 8 | HOMEPAGE_PROTECTION_BASELINE_COMPLETION_REPORT.md | docs/archive/reports/ | 首頁保護基準完成報告，報告類文件 |
| 9 | MASTER_DEVELOPMENT_ROADMAP.md | docs/archive/dev_history/ | Roadmap v1，已被 v2 取代 |
| 10 | MILESTONE_WP-11-11.5_CODE_CLEANUP_COMPLETE.md | docs/archive/wp_history/ | WP-11-11.5 Milestone 記錄，已關閉 |
| 11 | MILESTONE_WP-11-11.5_COMMIT.txt | docs/archive/wp_history/ | WP-11-11.5 Commit 記錄，已關閉 |
| 12 | TIMEZONE_REFACTOR_READINESS.md | docs/archive/reports/ | Timezone 重構準備文件，非當前工作 |
| 13 | WP-11-05D_UI_READINESS.md | docs/archive/wp_history/ | WP-11-05D UI 準備度，WP 已完成 |
| 14 | WP-11-07_UI_MVP_KICKOFF.md | docs/archive/wp_history/ | WP-11-07 UI MVP 啟動，WP 已完成 |
| 15 | WP-11-11.5_TAG_CREATION_GUIDE.md | docs/archive/wp_history/ | WP-11-11.5 Tag 建立指南，WP 已關閉 |
| 16 | WP-11-12_PHASE1_COMPLETION_REPORT.md | docs/archive/wp_history/ | WP-11-12 Phase 1 完成報告，WP 已關閉 |
| 17 | WP-11-12_PHASE2A_CODE_CHANGES.md | docs/archive/wp_history/ | WP-11-12 Phase 2A 程式碼變更記錄，已完成 |
| 18 | WP-11-12_PHASE2B_STATUS_RECONCILIATION_FINAL.md | docs/archive/wp_history/ | WP-11-12 Phase 2B 狀態對齊最終版，已關閉 |

---

**END OF DOCS_SAFE_ARCHIVE_SCAN.md**
*純分析報告，未移動任何檔案*