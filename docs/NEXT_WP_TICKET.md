# Next WP Ticket — Manual Testing & Phase 3 Planning

**Selected WP:** Manual Testing + WP-11-07 Phase 3 Planning  
**Reason:** Phase 2 code completed, need manual testing before Phase 3  
**Priority:** 🔴 P0 (Testing) / 🟡 P1 (Phase 3)

---

## Completed WPs

### WP-11-07 Phase 2 — API Integration (Mock → Real API)
**Date**: 2026-03-05  
**Status**: ✅ CODE COMPLETED (Pending Manual Test)

**Deliverables**:
- ✅ 替換 Mock 數據為真實 API 呼叫
- ✅ 統一錯誤處理策略（409/404/403/5xx/網路錯誤）
- ✅ Tenant/Auth headers 自動注入
- ✅ Loading 狀態與錯誤提示 UI
- ✅ 測試文件：`docs/WP-11-07_UI_MVP_PHASE2_TEST_LOG.md`

**Key Changes**:
- ✅ `stores/attendance.js` - 移除所有 Mock，改用真實 API
- ✅ `api/attendance.js` - 簡化為 4 個核心方法
- ✅ `views/Home.vue` - 新增錯誤 Toast 提示
- ✅ 錯誤處理：自動刷新狀態，防止 UI 與後端不同步

**API Integration**:
- ✅ POST `/api/v1/attendance/punch-in`
- ✅ POST `/api/v1/attendance/punch-out`
- ✅ GET `/api/v1/attendance/current-status`
- ✅ GET `/api/v1/attendance/history`

**Known Limitations**:
- ⚠️ 外出/返回功能暫不支援（後端無 endpoints）
- ⚠️ 需要 Node.js 環境才能執行測試

**Next**: Manual Testing

---

## 🧪 Immediate Task: Manual Testing

### Goal
執行完整的手動測試流程，驗證 API 串接是否正常運作。

### Prerequisites
1. **Node.js 環境**
   - 需要 Node.js 18+ 和 npm
   - 如果未安裝，需要先安裝

2. **後端服務運行**
   ```bash
   cd /opt/attendance-system/backend
   source ../venv/bin/activate
   uvicorn app.main:app --reload --port 8000
   ```

3. **前端依賴安裝**
   ```bash
   cd /opt/attendance-system/frontend
   npm install
   ```

### Testing Steps

#### 1. 啟動前端開發服務器
```bash
cd /opt/attendance-system/frontend
npm run dev
```

訪問：http://localhost:5173

#### 2. 執行測試流程

**正常流程**:
1. [ ] 頁面載入 → 檢查狀態卡顯示
2. [ ] 點擊「上班打卡」→ 檢查成功提示和狀態更新
3. [ ] 點擊「下班打卡」→ 檢查成功提示和狀態更新
4. [ ] 檢查最近記錄列表是否更新

**錯誤流程**:
1. [ ] 重複打卡 → 檢查 409 錯誤提示
2. [ ] 未打卡就下班 → 檢查 404 錯誤提示
3. [ ] 停止後端 → 檢查網路錯誤提示

#### 3. 更新測試結果

在 `docs/WP-11-07_UI_MVP_PHASE2_TEST_LOG.md` 中：
- 更新所有 `[ ]` 為 `[x]` 或 `[✗]`
- 記錄實際 API response
- 記錄任何發現的問題

#### 4. 問題修復（如果有）

如果測試發現問題：
- 記錄問題詳情
- 修復代碼
- 重新測試
- 更新文件

---

## 🚀 WP-11-07 Phase 3 — Feature Enhancement

### Goal
在 Phase 2 測試通過後，增強 UI 功能和用戶體驗。

### Option A: 外出/返回功能（需後端支援）

**前提條件**:
- 後端新增 `/api/v1/attendance/break-out` endpoint
- 後端新增 `/api/v1/attendance/break-in` endpoint

**工作內容**:
- 更新 `api/attendance.js` 新增方法
- 更新 `stores/attendance.js` 支援外出/返回
- 啟用 Home.vue 的外出/返回按鈕
- 測試完整流程

**預估時間**: 1 天（假設後端已完成）

---

### Option B: GPS 定位功能

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
        (error) => {
          reject(error)
        }
      )
    })
  }
  
  return { getCurrentPosition }
}
```

**預估時間**: 1-2 天

---

### Option C: 其他頁面開發

**頁面清單**:
1. **個人資料頁** (`/profile`)
   - 顯示個人資訊
   - 修改密碼功能

2. **請假申請頁** (`/leave-request`)
   - 請假表單
   - 請假記錄列表

3. **補打卡申請頁** (`/missed-punch`)
   - 補打卡表單
   - 申請記錄列表

4. **報表查詢頁** (`/reports`)
   - 日期範圍篩選
   - 打卡記錄表格
   - 匯出功能

**預估時間**: 每頁 2-3 天

---

### Option D: UI/UX 優化

**優化項目**:
1. **Toast 通知改善**
   - 使用專業的 Toast 組件庫（如 vue-toastification）
   - 支援多種類型（success/error/warning/info）
   - 可堆疊顯示

2. **Loading 狀態改善**
   - 全局 Loading 組件
   - 骨架屏（Skeleton）
   - 進度條

3. **動畫效果**
   - 頁面切換動畫
   - 列表項目動畫
   - 按鈕點擊回饋

4. **響應式優化**
   - 手機版佈局調整
   - 平板版佈局調整
   - 觸控優化

**預估時間**: 2-3 天

---

## 📊 建議優先順序

### 立即執行（P0）
1. **Manual Testing** - 驗證 Phase 2 功能
   - 預估時間：1-2 小時
   - 阻塞：所有後續開發

### 短期（P1）
2. **GPS 定位功能** - 提升打卡準確性
   - 預估時間：1-2 天
   - 價值：高（防止代打卡）

3. **UI/UX 優化** - 改善用戶體驗
   - 預估時間：2-3 天
   - 價值：中（提升滿意度）

### 中期（P2）
4. **其他頁面開發** - 完善系統功能
   - 預估時間：8-12 天
   - 價值：高（完整功能）

### 長期（P3）
5. **外出/返回功能** - 需要後端支援
   - 預估時間：1 天（前端）+ 後端開發時間
   - 價值：中（額外功能）

---

## 🔧 技術債務

### 需要處理的項目
1. **JWT 認證整合**
   - 當前使用 Mock user
   - 需要實作完整登入流程

2. **環境變數管理**
   - 當前 company_id 寫在 authStore
   - 應該從登入後取得

3. **錯誤邊界**
   - 需要全局錯誤處理
   - 防止 UI 崩潰

4. **單元測試**
   - 目前沒有前端測試
   - 應該加入 Vitest

---

## 📝 Decision Required

請決定下一步方向：

**Option 1**: 先完成 Manual Testing，確保 Phase 2 穩定  
**Option 2**: 直接開始 Phase 3 開發（假設 Phase 2 沒問題）  
**Option 3**: 先處理技術債務（JWT、測試等）  

---

**Ready to Start:** Pending Node.js installation  
**Blocker:** 需要 Node.js 環境執行測試  
**Assignee:** Frontend Team  
**Status:** ⏳ NEXT
