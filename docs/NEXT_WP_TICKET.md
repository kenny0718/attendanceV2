# Next WP Ticket

**更新日期**: 2026-03-08

---

## 當前狀態

### 已完成
- ✅ WP-11-07: Break Out/In 功能
- ✅ WP-11-10: OUT Checkpoint 功能
- ✅ WP-11-11: OUT Checkpoint 前端整合
- ✅ WP-11-11.5: GPS Legacy Cleanup（程式碼重構完成）

### 進行中
- 🔄 WP-11-12: Shared Location Module（設計階段）

---

## WP-11-11.5: GPS Legacy Cleanup（已完成）

### 狀態
✅ **程式碼重構完成** (2026-03-08)  
⏸️ **手動 QA 驗證待執行**

### 已完成
1. ✅ 建立 Legacy GPS Inventory
2. ✅ 建立 Cleanup Plan
3. ✅ 刪除前端備份檔案（死碼）
4. ✅ 建立 Location Adapter（臨時過渡層）
5. ✅ 更新 `frontend/src/stores/attendance.js`
   - 添加 locationAdapter import
   - 刪除 `detectDeviceType()` 方法
   - 刪除 `getGPSLocation()` 方法
   - 重構 `outCheckpointSubmit()` 使用 adapter
   - 更新 `handleError()` 處理 LocationError
6. ✅ 更新 `frontend/src/views/Home.vue`
   - 添加 locationAdapter import
   - 更新 `onMounted()` 使用 adapter
7. ✅ 建立 `frontend/src/utils/README.md`

### 待執行（手動 QA）
- [ ] 部署到測試環境
- [ ] OUT checkpoint 功能驗證
- [ ] Mobile 裝置 GPS 必填驗證
- [ ] PC 裝置 GPS 選填驗證
- [ ] GPS 錯誤訊息驗證
- [ ] 權限拒絕情境測試
- [ ] 超時情境測試

### 完成報告
- `docs/WP-11-11.5_COMPLETION_REPORT.md`

---

## WP-11-12: Shared Location Module（當前票）

### 狀態
🔄 **設計階段進行中**

### 目標
實作可重用的 shared location module，取代臨時 locationAdapter。

### 範圍
1. 建立 `composables/useLocation.js`
2. 實作 location state management
3. 實作統一的錯誤處理
4. 實作 loading state 管理
5. 實作 retry 機制
6. 替換所有 locationAdapter 引用

### 不包含（後續票）
- ❌ Location policy（範圍驗證、精度要求）→ WP-11-13
- ❌ 地圖 UI → WP-11-14
- ❌ Location analytics → WP-11-15

### 前置條件
- ✅ GPS Legacy Cleanup 完成
- ✅ Store 重構完成
- ✅ locationAdapter 已建立

### 預計時程
- 設計階段: 1 天（進行中）
- 實作階段: 2 天
- 測試階段: 1 天
- 總計: 4 天

### 設計文件（本輪建立）
- ⏳ `docs/ATTENDANCE_LOCATION_MODULE_SPEC.md`
- ⏳ `docs/ATTENDANCE_LOCATION_FRONTEND_REFACTOR_PLAN.md`
- ⏳ `docs/ATTENDANCE_LOCATION_API_CONTRACT_DRAFT.md`
- ⏳ `docs/ATTENDANCE_LOCATION_TEST_PLAN.md`

### 關鍵設計決策
1. **Composable API 設計**
   - 使用 Vue 3 Composition API
   - 提供 reactive state
   - 支援多個元件同時使用

2. **向後相容**
   - 第一階段保持 API contract 不變
   - 不修改後端
   - 不修改 payload 格式

3. **錯誤處理統一**
   - 統一 LocationError 格式
   - 統一錯誤碼
   - 統一錯誤訊息

4. **State Management**
   - 使用 composable 內部 state
   - 不依賴 Pinia store
   - 支援 SSR（未來）

---

## 未來票務規劃

### WP-11-13: Location Policy Migration
**預計開始**: WP-11-12 完成後

**範圍**:
- 將現有的 GPS 驗證邏輯遷移到 location policy
- 實作範圍驗證（geofencing）
- 實作精度要求驗證
- 實作自訂驗證規則

### WP-11-14: Location UI Enhancement
**預計開始**: WP-11-13 完成後

**範圍**:
- 地圖顯示當前位置
- 地圖顯示歷史打卡點
- 地圖顯示允許範圍
- 地圖互動功能

### WP-11-15: Location Analytics
**預計開始**: WP-11-14 完成後

**範圍**:
- 打卡位置分析
- 異常位置偵測
- 位置軌跡報表
- 位置熱力圖

---

## 技術債務

### 高優先級
1. **手動 QA 驗證**（WP-11-11.5）
   - 風險：程式碼已修改但未實際測試
   - 影響：可能有執行時錯誤
   - 建議：盡快在測試環境驗證

2. **前端測試覆蓋**
   - 風險：重構後沒有測試保護
   - 影響：回歸風險高
   - 建議：為 locationAdapter 和 useLocation 建立單元測試

### 中優先級
1. **API 文件更新**
   - OUT checkpoint API 文件需要補充
   - GPS payload 格式需要明確定義
   - 建議：在 WP-11-12 設計階段完成

2. **錯誤碼統一**
   - `GPS_REQUIRED` vs `LOCATION_REQUIRED`
   - 建議統一使用 `LOCATION_REQUIRED`
   - 建議：在 WP-11-12 實作時處理

### 低優先級
1. **裝置判斷邏輯優化**
   - 目前使用簡單的 User Agent 判斷
   - 可考慮使用更精確的方法
   - 建議：在 WP-11-13 或更後期處理

---

## 決策記錄

### 2026-03-08: 為什麼使用臨時 Adapter？
- **原因**: 避免一次性大規模重構造成功能中斷
- **好處**: 漸進式重構，保持功能可用
- **代價**: 需要兩階段重構（adapter → useLocation）
- **決定**: 接受兩階段重構，優先保證穩定性
- **結果**: ✅ adapter 已建立並整合

### 2026-03-08: 為什麼不直接實作 useLocation？
- **原因**: 需要先清理舊流程，避免衝突
- **好處**: 清理後的程式碼更容易整合新 module
- **代價**: 多一個臨時 adapter 層
- **決定**: 先清理再實作，確保架構清晰
- **結果**: ✅ 清理完成，可以開始 useLocation 設計

### 2026-03-08: WP-11-12 範圍決策
- **決定**: 第一階段只實作核心 composable，不包含 policy 和 UI
- **原因**: 降低複雜度，確保核心功能穩定
- **好處**: 更快交付，更容易測試
- **代價**: 需要多個票務完成完整功能
- **結果**: 分為 WP-11-12/13/14/15 四個階段

---

## 聯絡資訊

如有問題，請參考：
- 技術文件: `docs/` 目錄
- Git 歷史: 查看相關 commit
- 程式碼註解: 查看 `@deprecated` 標記

---

**最後更新**: 2026-03-08  
**下次檢視**: WP-11-12 設計完成後
