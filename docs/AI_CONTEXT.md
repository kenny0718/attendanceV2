# AI Context Guide

**目的：** 指引 AI（Cursor / GPT / Claude）在分析專案時優先讀取的核心文件

**最後更新：** 2026-03-04

---

## 📋 文件優先級

### 🔴 P0 - 必讀文件（架構與規範）

#### 1. SA_MODULE_SPEC_v1.9.md
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

#### 2. MASTER_DEVELOPMENT_ROADMAP_v2.md
**開發路線圖（最新版）**

- 6 個 Phase 的執行順序
- 31 個 Work Packages 定義
- 依賴關係與啟動條件
- Production Readiness Checklist

**使用時機：**
- 規劃開發順序
- 確認 WP 依賴關係
- 評估開發進度

**備註：** v1 版本已過時，請使用 v2

---

### 🟡 P1 - 重要文件（現況與決策）

#### 3. REALITY_AUDIT_STATUS_INVENTORY.md
**系統現況盤點**

- 7 個已實作模組狀態
- 79 個 Python 檔案清單
- 29 個測試檔案
- 模組完成度評估

**使用時機：**
- 了解系統現況
- 確認模組是否已實作
- 評估技術債

---

#### 4. REALITY_AUDIT_RISK_REPORT.md
**風險評估報告**

- P0/P1/P2 風險分類
- 3 個 P0 風險
- 5 個 P1 風險
- 5 個 P2 風險

**使用時機：**
- 風險評估
- 優先順序決策
- 技術債管理

---

#### 5. REALITY_AUDIT_NEXT_ACTIONS.md
**行動計畫**

- 7 個 Work Packages
- 執行步驟
- 預期成果

**使用時機：**
- 規劃下一步工作
- 確認執行細節

---

#### 6. SA_REALITY_GAP_REPORT.md
**規格與現況差異分析**

- SA v1.9 vs Reality 比對
- 70% 符合度分析
- 17/40 完全符合
- 11/40 部分符合
- 12/40 完全缺失

**使用時機：**
- 評估 SA 符合度
- 確認待補項目
- 架構對齊工作

---

#### 7. ARCHITECTURE_FIX_DECISION.md
**架構修正決策**

- 技術審查結果
- 修正建議
- 執行優先順序

**使用時機：**
- 架構修正工作
- 技術決策參考

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
→ 讀取 `SA_MODULE_SPEC_v1.9.md`

#### 規劃開發順序
→ 讀取 `MASTER_DEVELOPMENT_ROADMAP_v2.md`

#### 了解系統現況
→ 讀取 `REALITY_AUDIT_STATUS_INVENTORY.md`

#### 評估風險
→ 讀取 `REALITY_AUDIT_RISK_REPORT.md`

#### 確認下一步工作
→ 讀取 `REALITY_AUDIT_NEXT_ACTIONS.md` 或 `NEXT_WP_TICKET.md`

#### 評估 SA 符合度
→ 讀取 `SA_REALITY_GAP_REPORT.md`

#### 實作新功能
→ 先讀取 `SA_MODULE_SPEC_v1.9.md`，確認符合規範

#### 修改現有模組
→ 先讀取 `REALITY_AUDIT_STATUS_INVENTORY.md`，確認模組狀態

#### 架構決策
→ 讀取 `SA_MODULE_SPEC_v1.9.md` + `ARCHITECTURE_FIX_DECISION.md`

---

## ⚠️ 重要提醒

### ❌ 不要做的事

1. **不要參考 archive 目錄的文件**
   - 這些是歷史文件，可能已過時或被取代

2. **不要使用 SA_MODULE_SPECV1.8.md**
   - 已過時，使用 v1.9

3. **不要使用 MASTER_DEVELOPMENT_ROADMAP.md (v1)**
   - 已過時，使用 v2

4. **不要參考 PHASE1-7 實作報告**
   - 這些是歷史記錄，當前狀態請參考 REALITY_AUDIT_*

5. **不要參考 Gate 4 文件**
   - 已完成，當前在 Gate 5

---

### ✅ 應該做的事

1. **優先讀取 P0 文件**
   - SA_MODULE_SPEC_v1.9.md
   - MASTER_DEVELOPMENT_ROADMAP_v2.md

2. **確認系統現況**
   - REALITY_AUDIT_STATUS_INVENTORY.md
   - SA_REALITY_GAP_REPORT.md

3. **遵循架構規範**
   - 所有開發必須符合 SA v1.9
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
| SA_MODULE_SPEC | v1.9 | ✅ ACTIVE | 唯一權威 |
| MASTER_DEVELOPMENT_ROADMAP | v2 | ✅ ACTIVE | 使用 v2 |
| REALITY_AUDIT_* | 2026-03-04 | ✅ ACTIVE | 最新盤點 |
| SA_REALITY_GAP_REPORT | 2026-03-04 | ✅ ACTIVE | 最新分析 |
| ARCHITECTURE_FIX_DECISION | 2026-03-04 | ✅ ACTIVE | 最新決策 |

---

## 🔄 文件更新原則

### 何時更新文件

1. **完成 Phase 或 WP**
   - 更新 GATE_PROGRESS_TRACKER.md
   - 更新 NEXT_WP_TICKET.md

2. **架構變更**
   - 更新 SA_MODULE_SPEC（需團隊共識）
   - 更新 ARCHITECTURE_FIX_DECISION.md

3. **系統現況變化**
   - 更新 REALITY_AUDIT_STATUS_INVENTORY.md
   - 更新 SA_REALITY_GAP_REPORT.md

4. **風險變化**
   - 更新 REALITY_AUDIT_RISK_REPORT.md

5. **開發計畫調整**
   - 更新 MASTER_DEVELOPMENT_ROADMAP_v2.md（需團隊共識）

---

## 📝 總結

**核心原則：**
1. SA_MODULE_SPEC_v1.9.md 是唯一架構權威
2. MASTER_DEVELOPMENT_ROADMAP_v2.md 是開發順序權威
3. REALITY_AUDIT_* 是系統現況權威
4. archive 目錄僅供歷史參考，不作為開發依據

**AI 工作流程：**
1. 讀取 SA_MODULE_SPEC_v1.9.md 了解架構
2. 讀取 MASTER_DEVELOPMENT_ROADMAP_v2.md 了解開發順序
3. 讀取 REALITY_AUDIT_STATUS_INVENTORY.md 了解現況
4. 讀取相關 P1/P2 文件了解細節
5. 開始開發工作

---

**END OF AI_CONTEXT.md**
