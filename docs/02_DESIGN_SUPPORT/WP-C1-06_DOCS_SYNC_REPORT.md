# WP-C1-06 Docs Sync Report — attendance/docs.md v2

> **類型**：Docs Sync（程式碼已完成，補齊文件同步）  
> **日期**：2026-03-17  
> **關聯 WP**：WP-C1-06（Feature Gate 套用）  
> **狀態**：COMPLETE  

---

## 1. WP Summary

| 欄位 | 內容 |
|------|------|
| WP ID | WP-C1-06（Feature Gate 套用）|
| 目標 | 將 `attendance/docs.md` 從舊版 Phase 1 文件完整重寫為 v2，對齊實際程式碼狀態，並同步 WP-C1-06 Feature Gate 變更 |
| 完成日期 | 2026-03-17 |
| 觸發原因 | 舊版 docs.md 仍描述 SA_MODULE_SPEC v1.7 / Phase 1 Mock 架構，與實際程式碼嚴重不符 |

## 2. Files Changed

| 檔案 | 變更類型 | 說明 |
|------|---------|------|
| `backend/app/modules/attendance/docs.md` | 完整重寫 | Phase 1 舊版 → v2（29,305 bytes，665 行） |
| `backend/app/core/features.py` | 程式碼（已於 WP-C1-06 完成） | 新增模組層級 Gate（WP-C1-06），docs.md 同步反映 |
| `backend/app/modules/attendance/api.py` | 程式碼（已於 WP-C1-06 完成） | 新增 `_require_attendance_feature()`，docs.md 同步反映 |

## 3. Implementation Details

### 3.1 docs.md 重寫內容（舊版 → v2）

| 舊版問題 | v2 修正 |
|---------|---------|
| 描述 SA_MODULE_SPEC v1.7 header-based tenant | 改為描述 JWT/context injection |
| 描述 Phase 1 Mock API | 標注為 Deprecated，說明已全面替換 |
| 無 Feature Gate 說明 | 完整描述 FeatureKeys、FeatureService、`_require_attendance_feature()` |
| 無 Policy Engine 架構 | 新增 AttendancePolicyEngine、WorkSchedule、PolicyEvaluationResult 說明 |
| 無 Location Policy 說明 | 新增 AttendanceLocationPolicyService 說明（WP-11-13） |
| 無 Reporting API 說明 | 新增 Sessions / UserSummary / CompanySummary 三個 reporting endpoint |
| 無 Data Flow 圖 | 新增 Punch In / Punch Out / Break Out / Approve 四個 flow 圖 |
| 無 Testing 清單 | 列出 19 個實際存在的測試檔案 |

### 3.2 WP-C1-06 Feature Gate 同步（docs.md 更新）

- **Section 2.1 API Layer**：新增 `_require_attendance_feature(company_id, db)` 說明（WP-C1-06）
- **Section 2.6 Feature Gate**：補充 `router_v1` 所有端點統一執行 `attendance.core` gate
- **Section 4.1 Feature Keys**：`attendance.core` 標注 WP-C1-06，新增模組層級 Gate 表格
- **Section 4.2（新增）**：`_require_attendance_feature()` 完整程式碼範例
- **Section 4.3 Flow**：Flow 圖新增 `attendance.core` gate 步驟
- **Section 5.2 所有 v1 端點**：每個 endpoint 加入 Feature Gate 欄位標注
- **Section 7 Data Flow**：Punch In / Punch Out / Break Out flow 圖加入 Feature Gate 步驟
- **Section 9.1（新增）**：測試輔助工具說明（`override_all_auth_dependencies`，WP-C1-04）
- **Section 9.3**：Feature Gate 驗收條件更新

## 4. Feature Impact

| 影響範疇 | 說明 |
|---------|------|
| API 文件 | 所有 router_v1 endpoint 均標注 `attendance.core` Feature Gate |
| Feature Gate | `_require_attendance_feature()` helper 完整記錄於 docs |
| Data Flow | Punch In / Out / Break Out flow 圖均含 Feature Gate 步驟 |
| Auth Model | JWT/context injection 取代舊版 header-based tenant |
| Deprecated | SA_MODULE_SPEC v1.7 / Phase 1 Mock 明確標注為 Deprecated |

## 5. Testing Result

| 項目 | 結果 |
|------|------|
| docs.md 禁止關鍵字（`X-Company-ID`、`Phase 1`、`SA_MODULE_SPEC v1.7`）| ✅ 僅出現在 Section 10 Deprecated |
| docs.md 必要關鍵字（JWT、company_id、Feature Gate、UTC、Deprecated）| ✅ 全部存在 |
| docs.md 章節完整性（10 個章節）| ✅ 全部存在（行 9~638） |
| docs.md 與 api.py 一致性 | ✅ 所有端點均有對應說明 |
| docs.md 與 features.py 一致性 | ✅ 所有 FeatureKey 均記錄 |
| WP-C1-06 feature gate 同步 | ✅ `_require_attendance_feature()` 已完整記錄 |

## 6. Known Limitations

- `router_v1` 端點目前仍使用 Header-based auth（`get_current_company_id`），JWT migration 待 WP-C1-07 完成後，docs.md Section 3.1 需更新認證機制說明
- `feature_gate_demo.py` 的三個 stub endpoint（shift-overrides / shift-templates / split-shifts）尚未有實際業務實作，docs.md 已標注為 stub
- OUT Checkpoint endpoint（`/api/v1/attendance/out-checkpoint`）在 docs.md 中未列出（由 WP-C1-09 負責），不在本 WP 範圍

---

*本報告由 AI session（Cursor）產生，2026-03-17*
