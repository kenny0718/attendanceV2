# AI Context Guide

**目的：** 指引 AI（Cursor / GPT / Claude）在分析專案時優先讀取的核心文件

**最後更新：** 2026-03-04

所有實際開發行為控制：
→ 必須依 CURSOR_EXECUTION_CONTROL.md
→ 並遵守 CURSOR_READ_ORDER.md

AI 必讀規則（最高優先）

所有開發任務必須：

先讀 CURSOR_READ_ORDER.md
再讀 CURSOR_EXECUTION_CONTROL.md
再依任務選擇 frontend / backend rules

未完成上述流程：

❌ 禁止進行任何修改

## 📋 文件優先級

### 🔴 P0 - 必讀文件（架構與規範）

#### 1. SA_MODULE_SPEC_v2.1.md
**唯一架構權威規範**

- Platform-First Identity 架構定義
- Tenant Isolation 規則
- Feature Flags 機制
- 所有模組必須遵循的規範

**使用時機：**
- 設計新功能
- 修改現有模組
- 架構決策
- Code Review

---

#### 2. ATTENDANCE_DEVELOPMENT_ROADMAP.md
**Attendance 系統開發路線圖（現行版）**

- 當前 WP 與下一個 WP
- 各 WP 順序與依賴關係
- WP completion definition
- Protected core 提醒

**使用時機：**
- 規劃開發順序
- 確認 WP 依賴關係
- 評估開發進度

**備註：** 本文件為 Attendance 系統實際治理 roadmap

---


### 🟠 P0.5 - Current Project Control Files

#### ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md
Attendance System 的實際系統架構地圖

- Layered Architecture
- Reporting Module Map
- GPS / Location Module
- Protected Core Areas

**使用時機：**
- 分析模組位置
- 修改系統架構
- 新功能模組掛載位置

---

#### ATTENDANCE_DEVELOPMENT_ROADMAP.md
Attendance 系統實際開發順序

- 當前 WP
- 下一步 WP
- 各模組 roadmap
- WP completion definition

**使用時機：**
- 開始任何 Attendance 開發前
- 確認當前 WP
- 確認下一步功能


### 🟡 P1 - 重要文件（現況與進度）

#### 3. CURRENT_SYSTEM_STATE.md
**當前系統狀態（Single Source of Truth）**

- Current WP / Next WP
- 已完成核心模組清單
- 部分完成模組與缺口
- 已知限制與測試缺口

**使用時機：**
- 了解系統現況
- 確認模組是否已實作
- 評估技術債

---

#### 4. SYSTEM_DEVELOPMENT_STATUS_SNAPSHOT.md
**系統開發狀態快照（v3.0）**

- 完整 repository 結構分析
- 各模組實作狀態
- 已知問題與風險

**使用時機：**
- 深入了解模組實作細節
- 評估架構對齊狀況

---

#### 5. MODULE_STATUS_MATRIX.md
**模組狀態矩陣**

- 各模組狀態一覽
- 技術債記錄

**使用時機：**
- 快速確認模組狀態
- 技術債管理

---

### 🟢 P2 - 參考文件（規格與設計）

#### 8. ATTENDANCE_REGRESSION_SPEC.md
**Attendance 回歸測試規格**

- 8 個核心回歸測試定義
- 測試場景與預期結果

**使用時機：**
- 實作 WP-11-05
- 驗證 Attendance 功能

---

#### 9. WP-11-04B_KICKOFF_PLAN.md
**WP-11-04B 啟動計畫**

- Migration Chain 驗證計畫
- 執行步驟

**使用時機：**
- 執行 WP-11-04B

---

#### 10. WP-11-04B_GATE_READY_REPORT.md
**WP-11-04B Gate Ready 報告**

- Migration 驗證結果
- Gate 5 準備狀態

**使用時機：**
- 確認 Migration 狀態

---

#### 11. NEXT_WP_TICKET.md
**下一個 WP 工作票**

- 當前 WP 狀態
- 下一步行動

**使用時機：**
- 確認當前工作

---

#### 12. backup_restore_audit_design.md
**Backup/Restore 設計文件**

- Backup/Restore 架構設計
- 單一公司隔離機制

**使用時機：**
- 修改 Backup/Restore 功能

---

#### 13. SPLIT_SHIFT_DESIGN.md
**Split Shift 設計文件**

- 分段班次設計
- 業務邏輯說明

**使用時機：**
- 實作 Split Shift 功能

---

#### 14. SYSTEM_BLUEPRINT_SAAS_MULTI_TENANT_v1.md
**SaaS 多租戶系統藍圖**

- 系統整體架構
- 多租戶設計原則

**使用時機：**
- 理解系統整體架構

---

#### 15. MIGRATION_CHAIN_AUDIT_REPORT.md
**Migration Chain 審查報告**

- Migration 鏈狀態
- 問題與建議

**使用時機：**
- Migration 相關工作

---

#### 16. MIGRATION_CLEAN_REBUILD_POLICY.md
**Migration Clean Rebuild 政策**

- Migration 重建策略
- 執行原則

**使用時機：**
- Migration 重建決策

---

#### 17. GATE_PROGRESS_TRACKER.md
**Gate 進度追蹤**

- Gate 1-5 進度
- 當前狀態

**使用時機：**
- 追蹤開發進度

---

## 📁 Archive 目錄說明

`docs/archive/` 包含歷史文件，**不應作為開發參考**。

### archive/gates/
- Gate 4 相關文件
- WP-11-04A 相關文件
- 已完成的 Gate 歷史記錄

### archive/spec/
- SA_MODULE_SPECV1.8.md（已過時，使用 v1.9）
- AUTH_SCHEMA_SPEC.md（已整合至 v1.9）
- AUTH_TRANSITION_PLAN.md（已完成）
- AUTH_MIGRATION_REWRITE_PLAN_WP-10-02B.md（已完成）

### archive/dev_history/
- PHASE1-7 實作完成報告
- DELIVERY_REPORT.md
- DEVELOPMENT_PROGRESS.md
- DEVELOPMENT_ORDER.md
- STATUS_MATRIX.md
- Gate 5 相關歷史文件
- WP-10, WP-11-01, WP-11-02, WP-11-03 完成報告

### archive/notes/
- Cursor 任務模板
- DEV_NOTES_*.md
- 工具版本記錄

---

## 🎯 AI 使用指南

### 當你需要...

#### 了解架構規範
→ 讀取 `SA_MODULE_SPEC_v2.1.md`

#### 規劃開發順序
→ 讀取 `ATTENDANCE_DEVELOPMENT_ROADMAP.md`

#### 了解系統現況
→ 讀取 `CURRENT_SYSTEM_STATE.md`

#### 評估風險 / 技術債
→ 讀取 `CURRENT_SYSTEM_STATE.md` §5 Known Limitations
→ 讀取 `MODULE_STATUS_MATRIX.md`

#### 確認下一步工作
→ 讀取 `NEXT_WP_TICKET.md` 或 `ATTENDANCE_DEVELOPMENT_ROADMAP.md`

#### 評估模組實作狀態
→ 讀取 `SYSTEM_DEVELOPMENT_STATUS_SNAPSHOT.md`

#### 實作新功能
→ 先讀取 `SA_MODULE_SPEC_v2.1.md`，確認符合規範

#### 修改現有模組
→ 先讀取 `CURRENT_SYSTEM_STATE.md`，確認模組狀態

#### 架構決策
→ 讀取 `SA_MODULE_SPEC_v2.1.md` + `ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md`

---

## ⚠️ 重要提醒

### ❌ 不要做的事

1. **不要參考 archive 目錄的文件**
   - 這些是歷史文件，可能已過時或被取代

2. **不要使用 SA_MODULE_SPECV1.8.md**
   - 已過時，使用 v1.9

3. **不要使用已過期的 roadmap 文件**
   - 使用 ATTENDANCE_DEVELOPMENT_ROADMAP.md（當前有效）

4. **不要參考 PHASE1-7 實作報告**
   - 這些是歷史記錄，當前狀態請參考 CURRENT_SYSTEM_STATE.md

5. **不要參考 Gate 4 文件**
   - 已完成，當前在 Gate 5

---

### ✅ 應該做的事

1. **優先讀取 P0 文件**
   - SA_MODULE_SPEC_v2.1.md
   - ATTENDANCE_DEVELOPMENT_ROADMAP.md

2. **確認系統現況**
   - CURRENT_SYSTEM_STATE.md
   - SYSTEM_DEVELOPMENT_STATUS_SNAPSHOT.md

3. **遵循架構規範**
   - 所有開發必須符合 SA v2.1
   - 不可妥協的 P0 要求必須滿足

4. **按照 Roadmap 執行**
   - 遵循 Phase 順序
   - 確認 WP 依賴關係

5. **記錄重要決策**
   - 更新相關文件
   - 保持文件同步

---

## 📊 文件版本控制

| 文件 | 當前版本 | 狀態 | 備註 |
|------|---------|------|------|
| SA_MODULE_SPEC | v2.1 | ✅ ACTIVE | 唯一架構權威 |
| ATTENDANCE_DEVELOPMENT_ROADMAP | 2026-03-14 | ✅ ACTIVE | WP 順序與狀態 |
| ATTENDANCE_SYSTEM_ARCHITECTURE_MAP | 2026-03-14 | ✅ ACTIVE | 系統架構地圖 |
| CURRENT_SYSTEM_STATE | 2026-03-15 | ✅ ACTIVE | 系統現況 SSoT |
| GATE_PROGRESS_TRACKER | 2026-03-15 | ✅ ACTIVE | Gate 進度追蹤 |
| NEXT_WP_TICKET | 2026-03-15 | ✅ ACTIVE | 當前 WP 定義 |
| SYSTEM_DEVELOPMENT_STATUS_SNAPSHOT | v3.0 / 2026-03-15 | ✅ ACTIVE | 完整 repo 分析 |

---

## 🔄 文件更新原則

### 何時更新文件

1. **完成 Phase 或 WP**
   - 更新 GATE_PROGRESS_TRACKER.md
   - 更新 NEXT_WP_TICKET.md

2. **架構變更**
   - 更新 SA_MODULE_SPEC（需團隊共識）
   - 更新 ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md

3. **系統現況變化**
   - 更新 CURRENT_SYSTEM_STATE.md
   - 更新 SYSTEM_DEVELOPMENT_STATUS_SNAPSHOT.md

4. **風險 / 技術債變化**
   - 更新 CURRENT_SYSTEM_STATE.md §5 Known Limitations
   - 更新 MODULE_STATUS_MATRIX.md

5. **開發計畫調整**
   - 更新 ATTENDANCE_DEVELOPMENT_ROADMAP.md（需團隊共識）

---

## 📝 總結

**核心原則：**
1. SA_MODULE_SPEC_v2.1.md 是唯一架構權威
2. ATTENDANCE_DEVELOPMENT_ROADMAP.md 是開發順序權威
3. CURRENT_SYSTEM_STATE.md 是系統現況權威（Single Source of Truth）
4. archive 目錄僅供歷史參考，不作為開發依據

**AI 工作流程：**
1. 讀取 SA_MODULE_SPEC_v2.1.md 了解架構規範
2. 讀取 ATTENDANCE_DEVELOPMENT_ROADMAP.md 了解開發順序
3. 讀取 CURRENT_SYSTEM_STATE.md 了解現況
4. 讀取相關 P1/P2 文件了解細節
5. 開始開發工作

---
Before implementing any feature,
Cursor MUST read:

docs/ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md
docs/ATTENDANCE_DEVELOPMENT_ROADMAP.md

Cursor must NOT jump to another WP
until current WP is marked COMPLETE.

Cursor MUST read:
docs/ATTENDANCE_SYSTEM_ARCHITECTURE_MAP.md
docs/ATTENDANCE_DEVELOPMENT_ROADMAP.md
before implementing any feature.

**END OF AI_CONTEXT.md**
