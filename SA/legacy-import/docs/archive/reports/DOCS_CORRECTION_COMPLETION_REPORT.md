

## 📊 文件修正完成報告

### 修改的文件 (4 份)

1. ✅ SA_MODULE_SPEC_v2.0.md
2. ✅ ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md  
3. ✅ API_DOCUMENTATION_v2.0.md
4. ✅ DOCUMENTATION_UPDATE_SUMMARY_v2.0.md

### 實際修改的段落

#### SA_MODULE_SPEC_v2.0.md (7 處修改)
- 版本狀態: Platform-First Architecture → Design Complete (Location Policy Partially Implemented)
- 11.2 節: 新增 GPS 座標要求和 Phase 1 範圍說明
- 11.3 節: company_id 改為 "must match tenants.id type exactly"
- 16 節: 標準化 HTTP 狀態碼 (400/403/422)
- 21.2 節: 修正 GPS 要求規則（policy 啟用時所有裝置都需要）
- 23 節: 新增 company_id 類型驗證說明
- 底部: 新增實作狀態標示

#### ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md (重新創建)
- 文件頭部: 新增文件狀態區塊
- 新增: 當前實作範圍 (Phase 1) 區塊
- 架構設計: 新增 GPS 座標要求規則和裝置類型決策表
- 新增: HTTP 狀態碼標準化章節
- 資料模型: company_id 類型規則說明
- 底部: 新增待辦事項清單

#### API_DOCUMENTATION_v2.0.md (7 處修改)
- 狀態: Production → Draft (Partially Implemented)
- 考勤打卡 API: 新增 Phase 1 Scope 說明
- Request Body: GPS 要求改為「當公司啟用 location policy 時必填」
- HTTP 狀態碼: 標準化 400/403/422 定義
- 錯誤碼表: 新增 GPS_REQUIRED_FOR_LOCATION_POLICY (400)
- 錯誤碼表: VALIDATION_ERROR 改為 422
- 400 錯誤範例: 新增詳細說明和 Note
- 底部: 修改狀態為 Draft

#### DOCUMENTATION_UPDATE_SUMMARY_v2.0.md (5 處修改)
- 頭部: 新增狀態和關鍵決策區塊
- 文件對照表: 更新所有狀態為 Design Complete/Partial Impl/Draft
- 驗證順序: 新增 Phase 1 限制說明
- 新增: GPS 座標要求規則表格
- 錯誤處理: 標準化 400/403/422 範例
- 新增: 最終決策總結區塊
- 新增: 待決策的開放問題區塊
- 檢查清單: 改為待辦事項清單

---

## 📋 4 份文件的最終狀態

1. **SA_MODULE_SPEC_v2.0.md**: Design Complete (Location Policy Partially Implemented)
2. **ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md**: Design Complete / Partially Implemented
3. **API_DOCUMENTATION_v2.0.md**: Draft (Partially Implemented)
4. **DOCUMENTATION_UPDATE_SUMMARY_v2.0.md**: Corrections Documented

---

## 🎯 最終 GPS 規則

| 情境 | 公司設定 | 裝置類型 | GPS 要求 | 行為 |
|------|---------|---------|---------|------|
| 1 | 無 allowed locations | Mobile | 建議提供 | 允許打卡，記錄 GPS (如有) |
| 2 | 無 allowed locations | PC | 不需要 | 允許打卡 |
| 3 | **有 allowed locations** | Mobile | **必須提供** | 驗證 GPS，在範圍內才允許 |
| 4 | **有 allowed locations** | PC | **必須提供** | 驗證 GPS，在範圍內才允許 |

**關鍵決策**: 當 location policy 啟用時（有 allowed locations），所有裝置都必須提供 GPS

**理由**: 後端無法在沒有座標的情況下執行 geofence 驗證

---

## 📐 最終 HTTP Status 規則

### 單一明確標準

| 狀態碼 | 語義 | 使用時機 | Location Policy 範例 |
|--------|------|---------|---------------------|
| **400** | Bad Request | 請求本身有問題（缺少必填欄位、格式錯誤） | GPS_REQUIRED_FOR_LOCATION_POLICY |
| **403** | Forbidden | 請求合法但業務規則拒絕 | LOCATION_POLICY_VIOLATION |
| **422** | Unprocessable Entity | 請求格式正確但 schema 驗證失敗 | VALIDATION_ERROR (緯度 > 90) |

### 判定流程



### 與 FastAPI/Pydantic 的對應

- **Pydantic 自動驗證失敗** → 422 (預設行為，保持一致)
- **手動檢查缺少欄位** → 400 (在 Pydantic 之前檢查)
- **業務邏輯拒絕** → 403 (在 service 層檢查)

---

## ❓ 還剩哪些 Open Questions

### 1. PC 裝置 GPS 可用性

**問題**: PC 裝置無法提供 GPS 時如何處理？

**選項**:
- A. 拒絕打卡（當前決策）
- B. 提供「手動選擇地點」UI（Phase 2 考慮）
- C. 為 PC 裝置停用 location policy（不建議，有安全漏洞）

**建議**: Phase 1 保持當前決策，Phase 2 評估選項 B

### 2. RBAC 權限模型

**問題**: 誰可以管理 allowed locations？

**選項**:
- A. 僅公司管理員
- B. HR 經理角色
- C. 自訂「location manager」角色

**當前狀態**: 程式碼中標記為 TODO，未實作

### 3. Feature Flag / Entitlement

**問題**: location_policy 是否為付費功能？

**考量**:
- Feature flag: `attendance.location_policy`
- 可能需要 entitlement 檢查
- 影響 API 403 錯誤回應（FEATURE_DISABLED vs LOCATION_POLICY_VIOLATION）

**當前狀態**: 未實作 feature gate 檢查

### 4. company_id 實際類型

**問題**: tenants.id 實際使用什麼類型？

**當前假設**: VARCHAR(255)

**需要驗證**: 執行 migration 前必須確認

**安全機制**: Foreign Key 約束會在 migration 時驗證

---

**修正完成時間**: 2026-03-09  
**修正者**: Documentation Review Team  
**狀態**: ✅ All 4 files corrected

