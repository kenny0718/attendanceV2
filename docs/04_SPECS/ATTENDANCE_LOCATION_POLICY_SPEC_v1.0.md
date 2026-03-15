# Attendance Location Policy 規格文件

**版本**: 1.0  
**日期**: 2026-03-09  
**狀態**: Design Complete / Partially Implemented  
**相關票號**: WP-11-13

---

## 文件狀態

**設計階段**: ✅ Complete  
**實作階段**: ⚠️ Partial (BREAK_OUT only)  
**測試階段**: ⏳ Pending environment setup  
**部署階段**: ⏳ Not started

---

## 當前實作範圍 (Phase 1)

**✅ 已實作**:
- 資料模型: `allowed_locations` 表
- 後端服務: `location_policy_service.py`
- GPS 工具: `gps_utils.py` (Haversine 距離計算)
- 管理端 API: `admin_location_api.py` (CRUD)
- Migration 008: 資料庫 schema

**⚠️ 部分實作**:
- BREAK_OUT API 整合 (程式碼已寫，待測試驗證)

**❌ 未實作**:
- BREAK_IN 整合
- Punch-in / Punch-out 整合
- 前端 UI (地圖選點器)
- RBAC 權限控制 (管理端 API)
- 完整端到端測試

---

## 執行摘要

本規格定義考勤系統的「允許打卡地點 / Geofence Policy」功能，讓公司管理員可設定允許打卡的地理位置，系統在員工打卡時自動驗證位置是否符合政策。

**核心價值**:
- 🎯 防止員工在非工作地點打卡
- 📍 支援多地點工作場景（工地、客戶現場、辦公室）
- 🔒 後端強制執行，無法繞過
- 🏢 完整 Tenant Isolation

---

## 架構設計

### 設計原則

1. **後端 Authoritative Enforcement**
   - 前端 precheck 僅為 UX 優化
   - 後端必須強制執行 policy
   - 不可信任前端傳來的 location_id

2. **Tenant Isolation**
   - 所有 allowed_locations 必須綁定 company_id
   - 跨公司完全隔離

3. **Policy 邏輯**
   - 無 allowed locations → 允許任何地點
   - 有 allowed locations → 必須在任一地點範圍內

4. **模組內聚**
   - Location policy 邏輯封裝在 attendance 模組內
   - 不跨模組依賴

5. **GPS 座標要求** ⭐ 關鍵規則
   - 當公司設定了 allowed locations (location policy 啟用)
   - 且打卡流程需要 location policy 驗證時
   - **必須提供 GPS 座標**，無論裝置類型
   - 無法提供 GPS 的裝置/流程將被拒絕
   - 理由: 後端無法在沒有座標的情況下執行 geofence 驗證

### 裝置類型與 GPS 要求的決策

**最終規則** (解決 PC vs Mobile 衝突):

| 情境 | 公司設定 | 裝置類型 | GPS 要求 | 行為 |
|------|---------|---------|---------|------|
| 1 | 無 allowed locations | Mobile | 建議提供 | 允許打卡，記錄 GPS (如有) |
| 2 | 無 allowed locations | PC | 不需要 | 允許打卡 |
| 3 | 有 allowed locations | Mobile | **必須提供** | 驗證 GPS，在範圍內才允許 |
| 4 | 有 allowed locations | PC | **必須提供** | 驗證 GPS，在範圍內才允許 |

**關鍵決策**: 
- 當 location policy 啟用時 (有 allowed locations)，**所有裝置都必須提供 GPS**
- PC 裝置如無法提供 GPS，該打卡流程將不支援 location policy
- 前端應在 UI 上明確告知使用者此限制

**向後相容考量**:
- Phase 1 只實作 BREAK_OUT (通常是 Mobile 裝置)
- 未來擴展到其他流程時，需評估 PC 裝置的 GPS 可用性
- 可考慮為 PC 裝置提供「手動選擇地點」的替代方案 (Phase 2)

---

## HTTP 狀態碼標準化

| 狀態碼 | 用途 | 範例 |
|--------|------|------|
| 200 | 成功 | 查詢成功、更新成功 |
| 201 | 建立成功 | POST 建立資源 |
| 204 | 刪除成功 (無內容) | DELETE 成功 |
| **400** | **請求錯誤** (缺少必填欄位、格式錯誤) | GPS_REQUIRED_FOR_LOCATION_POLICY |
| 401 | 未授權 (未登入) | JWT token 無效 |
| **403** | **禁止存取** (權限不足、業務規則拒絕) | LOCATION_POLICY_VIOLATION, FORBIDDEN |
| 404 | 資源不存在 | Location not found |
| **422** | **驗證錯誤** (schema validation) | VALIDATION_ERROR |
| 500 | 伺服器錯誤 | 未預期的錯誤 |

**關鍵區別**:
- **400**: 請求本身有問題 (缺少必填欄位、格式錯誤)
- **422**: 請求格式正確但資料驗證失敗 (緯度超出範圍、半徑 <= 0)
- **403**: 請求合法但業務規則拒絕 (不在允許範圍內、無權限)

---

## 資料模型

### company_id 類型規則

**重要**: company_id 類型必須與 tenants.id 完全一致

**驗證機制**: Foreign Key 約束會在 migration 執行時驗證類型匹配

---

**文件狀態**: ⚠️ Design Complete / Partially Implemented  
**最後更新**: 2026-03-09  
**維護者**: Backend Team  
**待辦事項**: 
- 完成環境設定並執行測試
- 驗證 company_id 類型與 tenants.id 一致
- 實作 RBAC 權限控制
- 擴展到其他打卡流程 (Phase 2)
