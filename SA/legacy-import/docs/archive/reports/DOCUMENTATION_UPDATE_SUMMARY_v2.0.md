# 文件更新摘要報告

**日期**: 2026-03-09  
**原因**: 新增 GPS 定位與 Location Policy 功能 (WP-11-13)  
**影響範圍**: 系統架構、API 規格、開發文件  
**狀態**: ⚠️ Design Complete / Partially Implemented

---

## 🔑 本次修訂確定的關鍵決策

### 1. GPS 座標要求規則

**決策**: 當 location policy 啟用時，所有裝置都必須提供 GPS

**理由**:
- 後端無法在沒有座標的情況下執行 geofence 驗證
- 簡化規則：policy 啟用 = GPS 必須
- 避免安全漏洞

**影響**:
- PC 裝置如無法提供 GPS，該打卡流程將不支援 location policy
- 前端需明確告知使用者此限制
- Phase 2 可考慮「手動選擇地點」替代方案

### 2. HTTP 狀態碼標準化

**決策**:
- **400**: 請求錯誤（缺少必填欄位、格式錯誤）
- **403**: 業務規則拒絕（不在範圍內、無權限）
- **422**: Schema 驗證錯誤（緯度超出範圍、半徑 <= 0）

**理由**: 符合 HTTP 標準語義，避免與 FastAPI/Pydantic 預設行為衝突

### 3. 實作範圍限制

**決策**: Phase 1 僅實作 BREAK_OUT

**理由**:
- BREAK_OUT 是主要使用場景（外勤人員）
- 降低風險，不影響核心打卡流程
- 驗證架構正確性後再擴展

### 4. 狀態標示誠實化

**決策**: 使用 "Design Complete / Partially Implemented"

**理由**:
- 程式碼已寫但未完整測試
- 環境尚未設定（Python venv, PostgreSQL）
- RBAC 權限控制未實作
- 避免誇大完成度
### 1. SA_MODULE_SPEC_v2.0.md ⭐ 新建
**路徑**: `/opt/attendance-system/docs/SA_MODULE_SPEC_v2.0.md`  
**版本**: v1.9 → v2.0  
**狀態**: ✅ 已建立

**主要變更**:
- ✅ 新增第 11 章：Location Policy Rules
- ✅ 新增 allowed_locations 為 Tenant Data
- ✅ 更新驗證順序：Scope → Tenant Isolation → Feature Gate → **Location Policy**
- ✅ 新增錯誤碼：LOCATION_POLICY_VIOLATION
- ✅ 新增 Feature Flag：attendance.location_policy
- ✅ 新增第 21-23 章：Location Policy 技術規格、開發規範、Migration 記錄

**關鍵新增內容**:
```
# 11. Location Policy Rules (WP-11-13)
- 後端 Authoritative Enforcement
- Policy 邏輯：無 allowed locations → 允許任何地點
- Policy 邏輯：有 allowed locations → 必須在任一地點範圍內
- 資料模型：allowed_locations 表
- API：管理端 CRUD + 打卡端整合
```

---

### 2. ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md ⭐ 新建
**路徑**: `/opt/attendance-system/docs/ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md`  
**版本**: v1.0 (新建)  
**狀態**: ✅ 已建立

**文件結構**:
1. 執行摘要
2. 業務場景（3 個實際案例）
3. 架構設計（設計原則）
4. 資料模型（SQL DDL + 說明）
5. API 規格（完整 Request/Response）
6. 核心服務（LocationPolicyService）
7. GPS 距離計算（Haversine Formula）
8. 前端整合（locationAdapter.js）
9. 驗證流程（完整流程圖）
10. 測試規格（單元測試 + 整合測試）
11. 效能考量
12. 安全性
13. 未來擴充

**關鍵內容**:
- 📍 3 個業務場景：工地打卡、多地點顧問、彈性工作
- 🗄️ 完整資料模型：allowed_locations + attendance_punches 擴充
- 🔧 核心服務：LocationPolicyService 方法說明
- 📐 GPS 計算：Haversine Formula 數學公式
- 🧪 測試規格：5 個單元測試案例

---

### 3. API_DOCUMENTATION_v2.0.md ⭐ 新建
**路徑**: `/opt/attendance-system/docs/API_DOCUMENTATION_v2.0.md`  
**版本**: v1.0 → v2.0  
**狀態**: ✅ 已建立

**主要變更**:
- ✅ 新增 Location Policy 管理 API 章節
- ✅ 更新 BREAK_OUT API（整合 Location Policy）
- ✅ 新增錯誤碼：LOCATION_POLICY_VIOLATION
- ✅ 新增 5 個管理端 API 端點

**新增 API 端點**:
```
POST   /api/v1/admin/allowed-locations          建立允許地點
GET    /api/v1/admin/allowed-locations          查詢地點列表
GET    /api/v1/admin/allowed-locations/{id}     查詢單筆地點
PUT    /api/v1/admin/allowed-locations/{id}     更新地點
DELETE /api/v1/admin/allowed-locations/{id}     刪除地點
```

**BREAK_OUT API 變更**:
- Request 新增：`gps` 物件（mobile 必填）
- Response 新增：`location_policy` 物件
- 新增 403 錯誤：LOCATION_POLICY_VIOLATION

---

## 📊 文件對照表

| 文件名稱                                  | 版本      | 狀態     | 說明                           |
| ----------------------------------------- | --------- | -------- | ------------------------------ |
| SA_MODULE_SPEC_v1.9.md                    | v1.9      | 保留     | 舊版架構規格（向後相容）       |
| **SA_MODULE_SPEC_v2.0.md**                | **v2.0**  | **⚠️ Design Complete** | **新版架構規格（含 Location Policy）** |
| **ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md** | **v1.0**  | **⚠️ Partial Impl** | **Location Policy 詳細規格**   |
| **API_DOCUMENTATION_v2.0.md**             | **v2.0**  | **⚠️ Draft** | **API 文件（含 Location API）** |
| WP-11-13_LOCATION_POLICY_DESIGN.md        | v1.0      | 保留     | WP-11-13 設計文件              |
| ATTENDANCE_LOCATION_MODULE_SPEC.md        | v1.0      | 保留     | 前端 useLocation 規格          |

---

## 🔄 版本演進

### SA_MODULE_SPEC 版本歷史
```
v1.7 → Tenant baseline
v1.8 → Platform-first identity
v1.9 → Scope / Feature / Backup architecture finalized
v2.0 → Location Policy / Geofence (WP-11-13) ⭐ 本次更新
```

### API_DOCUMENTATION 版本歷史
```
v1.0 → 初版，包含基本考勤 API
v2.0 → 新增 Location Policy API (WP-11-13) ⭐ 本次更新
```

---

## 🎯 GPS 定位功能摘要

### 後端實作

**資料模型**:
- `allowed_locations` 表（允許打卡地點）
  - company_id (Tenant Isolation)
  - latitude / longitude (GPS 座標)
  - radius_meters (允許半徑)
  - location_type (地點類型)
  - is_active (啟用狀態)

**核心服務**:
- `location_policy_service.py` - Location Policy 評估
  - `get_active_allowed_locations()` - 取得啟用地點
  - `check_location_policy()` - 檢查位置是否符合政策

- `gps_utils.py` - GPS 工具
  - `calculate_distance()` - Haversine 距離計算
  - `is_within_distance()` - 檢查是否在範圍內

**API**:
- `admin_location_api.py` - 管理端 CRUD API
  - 建立/查詢/更新/刪除 allowed_locations

**整合**:
- `api.py` - BREAK_OUT 整合 location policy check

**資料庫**:
- Migration 008 - 建立 allowed_locations 表

### 前端實作

**GPS 獲取**:
- `locationAdapter.js` - GPS 定位適配器
  - `detectDeviceType()` - 裝置類型判斷
  - `getGPSLocation()` - 獲取 GPS 定位
  - 錯誤處理：NOT_SUPPORTED, PERMISSION_DENIED, TIMEOUT

**裝置邏輯**:
- Mobile → 必須 GPS
- PC → 不需要 GPS

---

## 📝 開發者需知

### 1. 使用新版文件

**架構設計** → 參考 `SA_MODULE_SPEC_v2.0.md`  
**Location Policy** → 參考 `ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md`  
**API 開發** → 參考 `API_DOCUMENTATION_v2.0.md`

### 2. 舊版文件處理

- ✅ 保留 v1.9 文件（向後相容）
- ✅ 新功能使用 v2.0 文件
- ⚠️ 不要刪除舊版文件（歷史記錄）

### 3. 驗證順序（重要）

```
1️⃣ Scope Validation (JWT)
2️⃣ Tenant Isolation (company_id)
3️⃣ Feature Gate (可選)
4️⃣ Location Policy Check (if enabled and flow supports it) ⭐ Phase 1: BREAK_OUT only
```

### 4. GPS 座標要求 ⭐ 新增

**關鍵規則**:
- 當公司啟用 location policy（有 allowed locations）
- **所有裝置都必須提供 GPS**，無論 Mobile 或 PC
- 無法提供 GPS 的請求將被拒絕（400 GPS_REQUIRED_FOR_LOCATION_POLICY）

| 情境 | 公司設定 | 裝置 | GPS 要求 |
|------|---------|------|----------|
| 1 | 無 allowed locations | Mobile | 建議 |
| 2 | 無 allowed locations | PC | 不需要 |
| 3 | 有 allowed locations | Mobile | **必須** |
| 4 | 有 allowed locations | PC | **必須** |

### 5. 錯誤處理

**新增錯誤碼**: `LOCATION_POLICY_VIOLATION`

```json
{
  "error_code": "LOCATION_POLICY_VIOLATION",
  "message": "不在允許的打卡範圍內。最近的地點：台北101工地（距離 350 公尺）",
  "nearest_location": {
    "id": "550e8400-...",
    "name": "台北101工地",
    "distance_meters": 350
  }
}
```

---

## 🧪 測試建議

### 必須測試的場景

1. **無 allowed locations** → 允許任何地點打卡
2. **在範圍內** → 允許打卡，記錄 location_id
3. **不在範圍內** → 拒絕打卡，返回 403
4. **多地點** → 命中任一地點即可
5. **Tenant Isolation** → A 公司無法讀取 B 公司地點

### 測試檔案

- `backend/app/modules/attendance/tests/test_location_policy.py`

---

## 📚 相關文件索引

### 架構文件
- `SA_MODULE_SPEC_v2.0.md` - 系統架構規格 v2.0 ⭐
- `SA_MODULE_SPEC_v1.9.md` - 系統架構規格 v1.9（舊版）
- `SYSTEM_BLUEPRINT_SAAS_MULTI_TENANT_v1.md` - SaaS 多租戶藍圖

### 功能規格
- `ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md` - Location Policy 規格 ⭐
- `ATTENDANCE_LOCATION_MODULE_SPEC.md` - 前端 useLocation 規格
- `WP-11-13_LOCATION_POLICY_DESIGN.md` - WP-11-13 設計文件

### API 文件
- `API_DOCUMENTATION_v2.0.md` - API 文件 v2.0 ⭐

### 實作報告
- `WP-11-13_CRITICAL_FIX_COMPLETION_REPORT.md` - 實作完成報告
- `WP-11-13_EXECUTION_STATUS_REPORT.md` - 執行狀態報告

---

## ⏳ 待辦事項

### 環境設定
- [ ] 建立 Python venv 並安裝依賴
- [ ] 啟動 PostgreSQL 資料庫
- [ ] 執行 Migration 008
- [ ] 驗證 company_id 類型與 tenants.id 一致

### 測試
- [ ] Backend Unit Tests
- [ ] API Integration Tests
- [ ] Manual QA (8 test cases)

### 實作
- [ ] RBAC 權限控制（管理端 API）
- [ ] 前端 UI（地圖選點器）
- [ ] 擴展到其他打卡流程（Phase 2）

---

**報告產生時間**: 2026-03-09  
**執行者**: AI Assistant  
**狀態**: ⚠️ Corrections Documented


## 📊 最終決策總結

### GPS 規則（最終版本）

| 情境 | 公司設定 | 裝置類型 | GPS 要求 | 行為 |
|------|---------|---------|---------|------|
| 1 | 無 allowed locations | Mobile | 建議提供 | 允許打卡，記錄 GPS (如有) |
| 2 | 無 allowed locations | PC | 不需要 | 允許打卡 |
| 3 | **有 allowed locations** | Mobile | **必須提供** | 驗證 GPS，在範圍內才允許 |
| 4 | **有 allowed locations** | PC | **必須提供** | 驗證 GPS，在範圍內才允許 |

**關鍵決策**: 當 location policy 啟用時，所有裝置都必須提供 GPS

### HTTP 狀態碼規則（最終版本）

| 狀態碼 | 用途 | 範例 |
|--------|------|------|
| **400** | 請求錯誤（缺少必填欄位） | GPS_REQUIRED_FOR_LOCATION_POLICY |
| **403** | 業務規則拒絕 | LOCATION_POLICY_VIOLATION |
| **422** | Schema 驗證錯誤 | VALIDATION_ERROR (緯度超出範圍) |

**關鍵區別**:
- 400: 請求本身有問題（缺少 GPS）
- 403: 請求合法但業務規則拒絕（不在範圍內）
- 422: 請求格式正確但資料驗證失敗（緯度 > 90）

### company_id 類型規則

**規則**: company_id 類型必須與 tenants.id 完全一致

**實作**: 由 Foreign Key 約束保證，migration 時會驗證

### 實作範圍（Phase 1）

**已實作**: BREAK_OUT only

**未實作**: BREAK_IN, Punch-in, Punch-out

---

## ❓ 待決策的開放問題

1. **PC 裝置 GPS 可用性**: Phase 2 是否提供「手動選擇地點」替代方案？
2. **RBAC 權限模型**: 誰可以管理 allowed locations？（公司管理員 / HR 經理 / 自訂角色）
3. **Feature Flag**: location_policy 是否為付費功能？需要 entitlement 檢查嗎？

---
