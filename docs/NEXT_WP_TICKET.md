# Next WP Ticket — Phase 3 Feature Enhancement

**Selected WP:** WP-11-07 Phase 3 — Feature Enhancement & UI/UX Optimization  
**Reason:** Phase 2 & Auth Integration 已完成，可進入 Phase 3 開發  
**Priority:** 🟡 P1 (Feature Enhancement)

---

## ✅ Completed WPs

### WP-11-08 — JWT Auth Integration (Replace Mock User)
**Date**: 2026-03-05 21:00  
**Status**: ✅ COMPLETED

**Deliverables**:
- ✅ 前端新增 Login flow（拿 token / 保存）
- ✅ axios interceptor 使用真 token + company context
- ✅ 移除 authStore.mockUser 依賴
- ✅ 路由保護（未登入不可進 Home）
- ✅ 測試文件：`docs/WP-11-08_AUTH_INTEGRATION_REPORT.md`

**Test Results**:
- ✅ 登入 API 測試通過
- ✅ 前端登入流程測試通過
- ✅ Token 自動帶入測試通過
- ✅ 登出測試通過

**Test Account**:
- Company ID: company-a
- Username: testuser
- Password: test123

### WP-11-07 Phase 2 — API Integration (Mock → Real API)
**Date**: 2026-03-05 20:09  
**Status**: ✅ VERIFIED & COMPLETED

**Test Results**:
- ✅ 所有 API 端點測試通過 (4/4)
- ✅ 錯誤處理測試通過 (3/3)
- ✅ 測試通過率：100%

---

## 🚀 WP-11-07 Phase 3 — Feature Enhancement

### Goal
在 Phase 2 & Auth Integration 完成後，增強 UI 功能和用戶體驗。

---

## 📊 Phase 3 選項與優先級

### Option A: GPS 定位功能 (推薦 P1)

**工作內容**:
- 建立 `composables/useGeolocation.js`
- 在打卡時自動獲取 GPS 座標
- 傳送 location 參數到後端
- 顯示定位狀態（獲取中/成功/失敗）
- 處理用戶拒絕定位的情況

**價值**: 高（防止代打卡，提升打卡準確性）  
**預估時間**: 1-2 天  
**優先級**: 🟡 P1

---

### Option B: UI/UX 優化 (推薦 P1)

**優化項目**:

1. **Toast 通知改善**
   - 使用專業的 Toast 組件庫（如 vue-toastification）
   - 支援多種類型（success/error/warning/info）
   - 可堆疊顯示

2. **Loading 狀態改善**
   - 全局 Loading 組件
   - 骨架屏（Skeleton）
   - 按鈕 Loading 狀態

3. **動畫效果**
   - 頁面切換動畫
   - 列表項目動畫
   - 按鈕點擊回饋

4. **響應式優化**
   - 手機版佈局調整
   - 平板版佈局調整
   - 觸控優化

**價值**: 中（提升用戶滿意度和使用體驗）  
**預估時間**: 2-3 天  
**優先級**: 🟡 P1

---

### Option C: Token Refresh 機制 (推薦 P1)

**工作內容**:
- 實作 refresh token API
- 自動刷新即將過期的 token
- 無感刷新（用戶無需重新登入）
- Token 過期前 5 分鐘自動刷新

**價值**: 高（改善用戶體驗，減少重複登入）  
**預估時間**: 1 天  
**優先級**: 🟡 P1

---

### Option D: 外出/返回功能 (需後端支援)

**前提條件**:
- 後端新增 `/api/v1/attendance/break-out` endpoint
- 後端新增 `/api/v1/attendance/break-in` endpoint

**工作內容**:
- 更新 `api/attendance.js` 新增方法
- 更新 `stores/attendance.js` 支援外出/返回
- 啟用 Home.vue 的外出/返回按鈕
- 測試完整流程

**價值**: 中（額外功能）  
**預估時間**: 1 天（假設後端已完成）  
**優先級**: 🟢 P2

---

### Option E: 其他頁面開發

**頁面清單**:

1. **個人資料頁** (`/profile`)
   - 顯示個人資訊
   - 修改密碼功能
   - 預估時間：2-3 天

2. **請假申請頁** (`/leave-request`)
   - 請假表單
   - 請假記錄列表
   - 預估時間：2-3 天

3. **補打卡申請頁** (`/missed-punch`)
   - 補打卡表單
   - 申請記錄列表
   - 預估時間：2-3 天

4. **報表查詢頁** (`/reports`)
   - 日期範圍篩選
   - 打卡記錄表格
   - 匯出功能
   - 預估時間：3-4 天

**價值**: 高（完整功能）  
**預估時間**: 8-12 天  
**優先級**: 🟢 P2

---

## 📝 建議執行順序

### 立即執行（P0）
1. **手動 UI 測試** - 驗證登入和打卡流程
   - 預估時間：1-2 小時
   - 阻塞：無
   - 價值：確保系統完整性

### 短期（P1）
2. **Token Refresh 機制** - 改善用戶體驗
   - 預估時間：1 天
   - 阻塞：無
   - 價值：高（減少重複登入）

3. **GPS 定位功能** - 提升打卡準確性
   - 預估時間：1-2 天
   - 阻塞：無
   - 價值：高（防止代打卡）

4. **UI/UX 優化** - 改善用戶體驗
   - 預估時間：2-3 天
   - 阻塞：無
   - 價值：中（提升滿意度）

### 中期（P2）
5. **其他頁面開發** - 完善系統功能
   - 預估時間：8-12 天
   - 阻塞：無
   - 價值：高（完整功能）

6. **外出/返回功能** - 需要後端支援
   - 預估時間：1 天（前端）+ 後端開發時間
   - 阻塞：後端 API
   - 價值：中（額外功能）

### 長期（P3）
7. **測試框架** - 單元測試 + E2E 測試
   - 預估時間：3-5 天
   - 阻塞：無
   - 價值：中（代碼質量）

---

## 🎯 推薦方案

### 方案 A：快速迭代（推薦）
1. 手動 UI 測試（1-2 小時）
2. Token Refresh 機制（1 天）
3. GPS 定位功能（1-2 天）
4. UI/UX 優化（2-3 天）

**總時間**: 約 1 週  
**價值**: 高  
**風險**: 低

---

## 🌐 系統訪問資訊

### 當前環境
- **Frontend**: http://192.168.88.164:5173
- **Backend API**: http://192.168.88.164:8000
- **API Docs**: http://192.168.88.164:8000/docs

### 服務狀態
- ✅ Backend (uvicorn): Running on port 8000
- ✅ Frontend (vite): Running on port 5173
- ✅ Nginx: Running on port 80
- ✅ Database: Connected
- ✅ Auth: JWT enabled

### 測試用戶
- **Company ID**: company-a
- **Username**: testuser
- **Password**: test123
- **User ID**: 11bda10d-7541-4230-b1f3-842afab2cea5

---

**Ready to Start:** Phase 3 Development  
**Blocker:** None (Phase 2 & Auth verified)  
**Assignee:** Frontend Team  
**Status:** 🎯 READY

**Document Version:** 11.0  
**Last Updated:** 2026-03-05 21:00  
**Next Review:** Phase 3 kickoff or manual UI testing
