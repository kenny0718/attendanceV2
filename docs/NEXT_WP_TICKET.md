# Next WP Ticket — WP-11-07 Phase 3 Planning

**Selected WP:** WP-11-07 Phase 3 — Feature Enhancement & UI/UX Optimization  
**Reason:** Phase 2 已完成並通過測試驗證，可進入 Phase 3 開發  
**Priority:** 🟡 P1 (Feature Enhancement)

---

## ✅ Completed WPs

### WP-11-07 Phase 2 — API Integration (Mock → Real API)
**Date**: 2026-03-05 20:09  
**Status**: ✅ VERIFIED & COMPLETED

**Deliverables**:
- ✅ 替換 Mock 數據為真實 API 呼叫
- ✅ 統一錯誤處理策略（409/404/403/5xx/網路錯誤）
- ✅ Tenant/Auth headers 自動注入
- ✅ Loading 狀態與錯誤提示 UI
- ✅ 測試文件：`docs/WP-11-07_UI_MVP_PHASE2_TEST_LOG.md`

**Test Results**:
- ✅ 所有 API 端點測試通過 (4/4)
- ✅ 錯誤處理測試通過 (3/3)
- ✅ 正常打卡流程測試通過
- ✅ 測試通過率：100%

**Environment**:
- ✅ Node.js v20.20.0 LTS
- ✅ Frontend: http://192.168.88.164:5173
- ✅ Backend: http://192.168.88.164:8000
- ✅ Nginx configured for IP access

**Known Limitations**:
- ⚠️ 外出/返回功能暫不支援（後端無 endpoints）
- ⚠️ UI 互動測試需手動在瀏覽器執行

---

## 🚀 WP-11-07 Phase 3 — Feature Enhancement

### Goal
在 Phase 2 測試通過後，增強 UI 功能和用戶體驗。

---

## 📊 Phase 3 選項與優先級

### Option A: GPS 定位功能 (推薦 P1)

**工作內容**:
- 建立 `composables/useGeolocation.js`
- 在打卡時自動獲取 GPS 座標
- 傳送 location 參數到後端
- 顯示定位狀態（獲取中/成功/失敗）
- 處理用戶拒絕定位的情況

**技術實作**:
```javascript
// composables/useGeolocation.js
export function useGeolocation() {
  const getCurrentPosition = () => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('瀏覽器不支援定位功能'))
        return
      }
      
      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          })
        },
        (error) => reject(error)
      )
    })
  }
  
  return { getCurrentPosition }
}
```

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
   - 自動消失時間可配置

2. **Loading 狀態改善**
   - 全局 Loading 組件
   - 骨架屏（Skeleton）
   - 進度條
   - 按鈕 Loading 狀態

3. **動畫效果**
   - 頁面切換動畫
   - 列表項目動畫
   - 按鈕點擊回饋
   - 狀態卡更新動畫

4. **響應式優化**
   - 手機版佈局調整
   - 平板版佈局調整
   - 觸控優化
   - 字體大小調整

**價值**: 中（提升用戶滿意度和使用體驗）  
**預估時間**: 2-3 天  
**優先級**: 🟡 P1

---

### Option C: 手動 UI 測試 (推薦 P0)

**測試內容**:
1. 在瀏覽器中訪問 http://192.168.88.164:5173
2. 執行完整的用戶流程測試
3. 驗證 UI 互動和視覺效果
4. 測試響應式佈局
5. 記錄任何 UI/UX 問題

**測試項目**:
- [ ] 頁面載入動畫
- [ ] 狀態卡顯示
- [ ] 按鈕點擊回饋
- [ ] Toast 通知顯示
- [ ] 記錄列表滾動
- [ ] 響應式佈局（手機/平板/桌面）
- [ ] 錯誤提示顯示
- [ ] Loading 狀態

**價值**: 高（確保用戶體驗）  
**預估時間**: 1-2 小時  
**優先級**: 🔴 P0

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

## 🔧 技術債務

### 需要處理的項目

1. **JWT 認證整合**
   - 當前使用 Mock user
   - 需要實作完整登入流程
   - 優先級：P2

2. **環境變數管理**
   - 當前 company_id 寫在 authStore
   - 應該從登入後取得
   - 優先級：P2

3. **錯誤邊界**
   - 需要全局錯誤處理
   - 防止 UI 崩潰
   - 優先級：P1

4. **單元測試**
   - 目前沒有前端測試
   - 應該加入 Vitest
   - 優先級：P3

5. **E2E 測試**
   - 加入 Playwright 或 Cypress
   - 自動化 UI 測試
   - 優先級：P3

---

## 📝 建議執行順序

### 立即執行（P0）
1. **手動 UI 測試** - 驗證用戶體驗
   - 預估時間：1-2 小時
   - 阻塞：無
   - 價值：確保 Phase 2 完整性

### 短期（P1）
2. **GPS 定位功能** - 提升打卡準確性
   - 預估時間：1-2 天
   - 阻塞：無
   - 價值：高（防止代打卡）

3. **UI/UX 優化** - 改善用戶體驗
   - 預估時間：2-3 天
   - 阻塞：無
   - 價值：中（提升滿意度）

### 中期（P2）
4. **其他頁面開發** - 完善系統功能
   - 預估時間：8-12 天
   - 阻塞：無
   - 價值：高（完整功能）

5. **JWT 認證整合** - 實作真實登入
   - 預估時間：2-3 天
   - 阻塞：需要後端 Auth API
   - 價值：高（安全性）

### 長期（P3）
6. **外出/返回功能** - 需要後端支援
   - 預估時間：1 天（前端）+ 後端開發時間
   - 阻塞：後端 API
   - 價值：中（額外功能）

7. **測試框架** - 單元測試 + E2E 測試
   - 預估時間：3-5 天
   - 阻塞：無
   - 價值：中（代碼質量）

---

## 🎯 推薦方案

### 方案 A：快速迭代（推薦）
1. 手動 UI 測試（1-2 小時）
2. GPS 定位功能（1-2 天）
3. UI/UX 優化（2-3 天）
4. 其他頁面開發（8-12 天）

**總時間**: 約 2 週  
**價值**: 高  
**風險**: 低

### 方案 B：穩健發展
1. 手動 UI 測試（1-2 小時）
2. UI/UX 優化（2-3 天）
3. JWT 認證整合（2-3 天）
4. GPS 定位功能（1-2 天）
5. 其他頁面開發（8-12 天）

**總時間**: 約 3 週  
**價值**: 高  
**風險**: 低

### 方案 C：最小可行產品
1. 手動 UI 測試（1-2 小時）
2. GPS 定位功能（1-2 天）
3. 基本 UI 優化（1 天）

**總時間**: 約 3-4 天  
**價值**: 中  
**風險**: 低

---

## 📋 Decision Required

請決定下一步方向：

**Option 1**: 執行方案 A（快速迭代）- 推薦  
**Option 2**: 執行方案 B（穩健發展）  
**Option 3**: 執行方案 C（最小可行產品）  
**Option 4**: 自定義方案

---

## 🌐 系統訪問資訊

### 當前環境
- **Frontend Dev**: http://192.168.88.164:5173
- **Frontend (Nginx)**: http://192.168.88.164/dev/
- **Backend API**: http://192.168.88.164:8000
- **API Docs**: http://192.168.88.164:8000/docs

### 服務狀態
- ✅ Backend (uvicorn): Running on port 8000
- ✅ Frontend (vite): Running on port 5173
- ✅ Nginx: Running on port 80
- ✅ Database: Connected

### 測試用戶
- **User ID**: 11bda10d-7541-4230-b1f3-842afab2cea5
- **Name**: 測試員工
- **Email**: test@company-a.com
- **Company**: company-a

---

**Ready to Start:** Phase 3 Development  
**Blocker:** None (Phase 2 verified)  
**Assignee:** Frontend Team  
**Status:** 🎯 READY

**Document Version:** 10.0  
**Last Updated:** 2026-03-05 20:09  
**Next Review:** Phase 3 kickoff or manual UI testing
