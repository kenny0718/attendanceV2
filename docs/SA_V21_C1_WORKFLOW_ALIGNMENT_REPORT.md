# SA_V21_C1_WORKFLOW_ALIGNMENT_REPORT.md

**報告類型：** 架構對齊驗證報告（文件與治理層面，不涉及程式碼修改）
**分析日期：** 2026-03-12
**分析範圍：** SA_MODULE_SPEC_v2.1 vs C1 工作流（WP-C1-01 ~ WP-C1-09）
**分析者：** AI session (Cursor)
**狀態：** FINAL

---

## 1. 整體結論

```
結論等級：MINOR_DOC_ALIGNMENT
```

**說明：**

SA_MODULE_SPEC v2.1 新增的 Attendance Calculation Architecture（Section 25–32）與 C1 工作流**整體相容**。C1 工作流（WP-C1-01 ~ WP-C1-09）的執行目標（JWT 遷移、基線測試、Out Checkpoint 實作）均未與 v2.1 新規則產生根本衝突。

然而，以下幾點需要文件層面的小幅對齊：

1. `ACCEPTANCE_PLAN.md` 的 Source of Truth 仍列出 `API_DOCUMENTATION_v2.0.md`，但實際 canonical API 文件已為 `API_DOCUMENTATION_v2.1.md`。
2. `ATTENDANCE_DEVELOPMENT_MASTER_FLOW.md` WP-11-05 的「cross-midnight 場景驗證」描述未明確對應 SA v2.1 Section 29 的 Session Ownership Date 規則。
3. `WP-C1-08_REMAINING_FAILURE_RECLASSIFICATION.md`（歷史記錄）已精確識別跨午夜 `duration_minutes=0` 問題為 `BUSINESS_LOGIC_BUG`，與 SA v2.1 Section 29 的診斷完全吻合——此為**正確識別**，無衝突。
4. `DEVELOPMENT_EXECUTION_PLAN.md` 對 WP-C1-04 之後的工作包記錄截斷，但 `WORKSTREAM_STATUS_LEDGER.md` 已補齊執行記錄。

無任何 C1 步驟與 SA v2.1 的新規則產生**阻塞性衝突**。

---

## 2. 對齊矩陣

### 2A：C1 工作流與 SA v2.1 各 Section 逐步對照

| WP | 工作包名稱 | 相關 SA v2.1 Section | 狀態 | 說明 |
|----|-----------|---------------------|------|------|
| WP-C1-01 | PostgreSQL 測試環境建立 + Migration 驗證 | §3 Module Structure, §14 Index Rules | ALIGNED | Migration chain 驗證通過（10 個步驟，單一 head 008_wp_11_13）。符合 §3 強制模組結構與 §14 index 規則。 |
| WP-C1-02 | Attendance Auth JWT 轉換 | §6 Request Context, §9 Tenant Isolation | ALIGNED | 由 WP-C1-07 實際執行完成。JWT Actor 取代 Header auth，company_id 不再來自 request body，符合 §6 與 §9 規定。 |
| WP-C1-03 | Auth 轉換 Batch 2（audit/notifications/backup）| §6 Request Context, §9 Tenant Isolation | ALIGNED | WP-C1-05 已完成 Category A 測試遷移（47 passed）；模組 JWT 遷移已在 WORKSTREAM_STATUS_LEDGER 記錄。SA v2.1 規則無新增限制影響此步驟。 |
| WP-C1-04 | 8 個回歸測試實作 + 真實 DB 執行 | §10 Attendance Core Rules, §28 Work Hour Calculation Rules, §29 Cross-Midnight Rule | MINOR_GAP | DEVELOPMENT_EXECUTION_PLAN.md 對 WP-C1-04 描述截斷不完整。回歸測試 Test 8（cross-midnight）現已由 SA v2.1 §29 提供明確規範；測試預期應對應 §29.2 Session Ownership Date（punch_in Asia/Taipei 日期），此對齊在文件中未明確連結。 |
| WP-C1-05 | 測試套件遷移（JWT） | §6 Request Context | ALIGNED | 已完成 47 passed（Category A）。與 SA v2.1 無衝突。 |
| WP-C1-06 | Migration Baseline 驗證 | §13 Primary Key Design, §14 Index Rules, §23 Migration 記錄 | ALIGNED | Migration smoke tests 3/3 PASS。allowed_locations、attendance_punches 均符合 §14 index 要求與 §23 migration 記錄規範。 |
| WP-C1-07 | Attendance API JWT 遷移 | §6 Request Context, §8 Company Scope Validation, §9 Tenant Isolation | ALIGNED | 11/11 tests PASS。get_actor_with_company() 替代 Header auth，符合 §6 context 建立流程與 §9 write rules。 |
| WP-C1-08 Phase 1 | Attendance Test Re-Enable 基線驗證 | §26 Engine Layering, §27 Responsibility Boundaries | ALIGNED | 35/35 PASS。Policy Engine 測試（24 tests）屬 §26.3 Policy Engine 層，純邏輯測試，無 §27 禁止行為。 |
| WP-C1-08 Phase 2 | Fixture Layer 修復 | §28 Work Hour Calculation Rules, §29 Cross-Midnight Rule | ALIGNED（識別正確） | duration_minutes=0 bug 被正確分類為 BUSINESS_LOGIC_BUG（datetime.utcnow() 誤用導致 naive datetime），與 SA v2.1 §29.1 及 §31.4 禁止行為完全吻合。識別正確，修復待 WP-C1-11。 |
| WP-C1-09 | OUT Checkpoint API 實作 | §26.1 Punch Layer, §27 Responsibility Boundaries, §31 Timezone Rule | ALIGNED | 7/7 tests PASS。Out Checkpoint 正確歸屬於 §26.1 Punch Layer（只記錄原始打卡事件）。get_current_time() utility 已採用 UTC-aware，符合 §31.2 儲存規則。 |

---

### 2B：SA v2.1 新規則（Section 25–32）vs 現有文件覆蓋狀況

| SA v2.1 Section | 規則主題 | 相關文件 | 覆蓋狀態 | 說明 |
|----------------|---------|---------|---------|------|
| §25 Architecture Overview | Attendance Calculation Architecture 目的 | SA_v2.1_UPGRADE_NOTE.md, SA_MODULE_SPEC_v2.1.md | COVERED | Upgrade Note 已清楚說明引入背景與適用範圍。 |
| §26 Engine Layering | 五層架構（Punch/Session/Policy/Work Hour/Report） | SA_MODULE_SPEC_v2.1.md | COVERED | 五層定義明確，各 WP 實作物可對應至各層。 |
| §27 Responsibility Boundaries | 四項禁止行為 | SA_MODULE_SPEC_v2.1.md, SA_v2.1_UPGRADE_NOTE.md | COVERED | 禁止項目明確列出。ATTENDANCE_DEVELOPMENT_MASTER_FLOW.md 未明確引用，但未違反。 |
| §28 Work Hour Calculation Rules | raw_duration, break_duration, work_duration 定義 | SA_MODULE_SPEC_v2.1.md | PARTIAL | 術語在 SA v2.1 已定義，但 DEVELOPMENT_EXECUTION_PLAN.md、ACCEPTANCE_PLAN.md 中的 ATT-03 驗收案例未更新以引用 canonical terms。 |
| §29 Cross-Midnight Rule | Duration 計算、Session Ownership Date、月報歸屬 | SA_MODULE_SPEC_v2.1.md, WP-C1-08_REMAINING_FAILURE_RECLASSIFICATION.md | PARTIAL | §29 規則已在 SA v2.1 定義。ATTENDANCE_DEVELOPMENT_MASTER_FLOW.md WP-11-05 提及 cross-midnight 場景，但未更新以明確對應 §29.2 Ownership Date 規則。 |
| §30 Report Consistency Rule | 報表層只讀 canonical 欄位，禁止獨立計算 | SA_MODULE_SPEC_v2.1.md | PARTIAL | ACCEPTANCE_PLAN.md M8 reporting placeholder 未含 §30 合規條件。API_DOCUMENTATION_v2.1.md 報表相關 API 未明確標注 canonical field 依賴。 |
| §31 Timezone Rule | UTC 儲存、Asia/Taipei 業務邊界、ISO-8601 API contract | SA_MODULE_SPEC_v2.1.md, API_DOCUMENTATION_v2.1.md | PARTIAL | API_DOCUMENTATION_v2.1.md 時間格式標注為 2026-03-09T14:30:00Z（UTC with Z suffix），符合 §31.5。但文件未明確宣告禁止 datetime.utcnow() 的 API-level contract 條款。 |
| §32 Future Extensibility | 班表/彈性工時/分段班次/假日規則/調整工作流預留 | SA_MODULE_SPEC_v2.1.md, SPLIT_SHIFT_DESIGN.md | COVERED | §32 為前瞻性設計；SPLIT_SHIFT_DESIGN.md 已存在，與 §32 預留的 Split Shifts 一致。 |

---

### 2C：時區規則（§31）文件一致性掃描

| 文件 | 問題類型 | 具體描述 | 風險等級 |
|------|---------|---------|--------|
| SA_MODULE_SPEC_v2.1.md | 無問題 | §31 明確禁止 datetime.utcnow()，要求 UTC-aware datetime，API ISO-8601 with timezone offset | — |
| API_DOCUMENTATION_v2.1.md | 輕微不完整 | 時間格式範例均使用 Z suffix，符合 §31.5；但 GPS captured_at 