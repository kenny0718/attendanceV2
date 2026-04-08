# WP-11-13 Step 3A - 修改清單

**日期**: 2026-03-08  
**狀態**: ✅ 已完成

---

## 修改檔案

### 1. frontend/src/views/Home.vue

**修改位置**: `handleBreakOutPunch()` 函數的 catch 區塊（第 425-455 行）

**修改類型**: 增強錯誤處理

**修改內容**:

#### 新增的錯誤處理邏輯

1. **後端 403 LOCATION_POLICY_VIOLATION**
   ```javascript
   if (error.response?.status === 403 && 
       error.response?.data?.detail?.error_code === 'LOCATION_POLICY_VIOLATION') {
     let message = error.response.data.detail.error || '不在允許的打卡範圍內'
     
     if (error.response.data.detail.nearest_location) {
       const nearest = error.response.data.detail.nearest_location
       message += `\n\n最近的允許地點：${nearest.name}\n距離：${nearest.distance_meters} 公尺`
     }
     
     errorMessage.value = message
   }
   ```

2. **GPS 權限被拒絕**
   ```javascript
   else if (error.code === 'PERMISSION_DENIED') {
     errorMessage.value = '需要定位權限才能外出打卡\n請在瀏覽器設定中允許定位後重試'
   }
   ```

3. **GPS 超時**
   ```javascript
   else if (error.code === 'TIMEOUT') {
     errorMessage.value = '定位請求逾時\n請確認 GPS 訊號良好後重試'
   }
   ```

4. **GPS 無法取得**
   ```javascript
   else if (error.code === 'POSITION_UNAVAILABLE') {
     errorMessage.value = '無法取得定位資訊\n請確認已開啟定位服務'
   }
   ```

---

## 未修改的檔案（已存在且正確）

以下檔案在 WP-11-12 Phase 2B 已經完成，不需要修改：

- ✅ `frontend/src/composables/useLocation.js` - GPS 功能完整
- ✅ `frontend/src/stores/attendance.js` - 已正確傳遞 gps 資料
- ✅ `frontend/src/api/attendance.js` - API 已正確
- ✅ `backend/app/modules/attendance/schemas.py` - Schema 已支援 location
- ✅ `backend/app/modules/attendance/api.py` - 後端 enforcement 已實作

---

## 修改統計

- **修改檔案數**: 1
- **新增行數**: ~30 行
- **刪除行數**: ~5 行
- **淨增加**: ~25 行

---

## 影響範圍

### ✅ 影響的功能
- BREAK_OUT 打卡錯誤處理

### ❌ 不影響的功能
- BREAK_IN 打卡
- punch-in 打卡
- punch-out 打卡
- OUT Checkpoint
- 其他所有功能

---

## 測試建議

### 手動測試案例

1. **無 policy 情況**
   - 操作: 外出打卡
   - 預期: 正常打卡成功

2. **有 policy + 在範圍內**
   - 操作: 在允許地點外出打卡
   - 預期: 正常打卡成功

3. **有 policy + 超出範圍**
   - 操作: 在不允許地點外出打卡
   - 預期: 顯示「不在允許的打卡範圍內」+ 最近地點資訊

4. **GPS 權限被拒絕**
   - 操作: 拒絕定位權限後外出打卡
   - 預期: 顯示「需要定位權限才能外出打卡」

5. **GPS 超時**
   - 操作: GPS 訊號不良時外出打卡
   - 預期: 顯示「定位請求逾時」

6. **GPS 無法取得**
   - 操作: 關閉定位服務後外出打卡
   - 預期: 顯示「無法取得定位資訊」

---

## 部署檢查清單

- [ ] 前端 build 成功
- [ ] 無 linting 錯誤
- [ ] 無 TypeScript 錯誤
- [ ] 部署到測試環境
- [ ] 執行手動測試
- [ ] 驗證錯誤訊息顯示正確
- [ ] 驗證不影響其他功能

---

**建立日期**: 2026-03-08  
**狀態**: ✅ 已完成  
**可部署**: ✅ Yes
