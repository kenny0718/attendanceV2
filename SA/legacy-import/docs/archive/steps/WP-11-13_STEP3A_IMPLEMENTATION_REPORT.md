# WP-11-13 Step 3A Implementation Report

**票號**: WP-11-13 Step 3A  
**標題**: Frontend Integration for BREAK_OUT Location Policy  
**日期**: 2026-03-08  
**狀態**: ✅ 已完成

---

## 執行摘要

WP-11-13 Step 3A 已完成 BREAK_OUT 的前端整合。實作非常簡潔，因為發現大部分基礎設施已經在 WP-11-12 Phase 2B 完成。

**關鍵發現**:
- ✅ useLocation composable 已存在且功能完整
- ✅ Home.vue 已經在使用 getLocationIfRequired()
- ✅ GPS 資料已經正確傳給後端
- ✅ 後端 enforcement 已經就位

**實際需要的修改**:
- ✅ 加強錯誤處理，特別是 403 LOCATION_POLICY_VIOLATION
- ✅ 改善錯誤訊息的友善度

---

## 實作內容

### 修改檔案（1 個）

**frontend/src/views/Home.vue**

**修改位置**: `handleBreakOutPunch()` 函數的 catch 區塊

**修改內容**:

#### Before（原有錯誤處理）

```javascript
catch (error) {
  console.error('外出打卡失敗:', error)
  
  // 顯示友善的錯誤訊息
  errorMessage.value = error.message || '打卡失敗，請稍後再試'
  showErrorMessage.value = true
  
  setTimeout(() => {
    showErrorMessage.value = false
  }, 5000)
}
```

#### After（WP-11-13 增強錯誤處理）

```javascript
catch (error) {
  console.error('外出打卡失敗:', error)
  
  // WP-11-13: 處理 location policy violation
  if (error.response?.status === 403 && 
      error.response?.data?.detail?.error_code === 'LOCATION_POLICY_VIOLATION') {
    // 顯示詳細的 policy violation 錯誤
    let message = error.response.data.detail.error || '不在允許的打卡範圍內'
    
    // 如果有最近地點資訊，加入提示
    if (error.response.data.detail.nearest_location) {
      const nearest = error.response.data.detail.nearest_location
      message += `\n\n最近的允許地點：${nearest.name}\n距離：${nearest.distance_meters} 公尺`
    }
    
    errorMessage.value = message
  } else if (error.code === 'PERMISSION_DENIED') {
    // GPS 權限被拒絕
    errorMessage.value = '需要定位權限才能外出打卡\n請在瀏覽器設定中允許定位後重試'
  } else if (error.code === 'TIMEOUT') {
    // GPS 超時
    errorMessage.value = '定位請求逾時\n請確認 GPS 訊號良好後重試'
  } else if (error.code === 'POSITION_UNAVAILABLE') {
    // GPS 無法取得
    errorMessage.value = '無法取得定位資訊\n請確認已開啟定位服務'
  } else {
    // 其他錯誤
    errorMessage.value = error.message || '打卡失敗，請稍後再試'
  }
  
  showErrorMessage.value = true
  
  setTimeout(() => {
    showErrorMessage.value = false
  }, 5000)
}
```

---

## 技術分析

### 1. 為什麼修改這麼少？

**原因**: WP-11-12 Phase 2B 已經完成了大部分工作

**已存在的基礎設施**:
1. ✅ `useLocation` composable（完整的 GPS 功能）
2. ✅ `getLocationIfRequired()` 已被調用
3. ✅ GPS 資料已正確格式化並傳給後端
4. ✅ 後端 schema 已支援 `location` 欄位
5. ✅ 後端 enforcement 已實作

**實際缺少的**:
- ❌ 前端沒有處理後端 403 LOCATION_POLICY_VIOLATION 錯誤
- ❌ GPS 錯誤訊息不夠友善

---

### 2. 前端流程分析

#### 完整的 BREAK_OUT 流程

```javascript
// 1. 使用者點擊「外出打卡」
handlePunch('BREAK_OUT')
  ↓
// 2. 調用 handleBreakOutPunch()
handleBreakOutPunch()
  ↓
// 3. 取得 GPS（如果是 mobile）
const gpsData = await getLocationIfRequired()
  ↓
// 4. 傳給 store
await attendanceStore.punchWithLocation('BREAK_OUT', {
  notes: selectedReason.value || '',
  gps: gpsData  // { latitude, longitude, accuracy, captured_at, provider }
})
  ↓
// 5. Store 調用 API
await attendanceApi.breakOut({
  notes: '...',
  location: gpsData ? {
    latitude: gpsData.latitude,
    longitude: gpsData.longitude
  } : undefined
})
  ↓
// 6. 後端驗證 location policy
if (request.location) {
  policy_check = check_location_policy(...)
  if (!policy_check.allowed) {
    return 403 LOCATION_POLICY_VIOLATION
  }
}
  ↓
// 7. 前端處理回應
// - 成功: 顯示成功訊息
// - 403: 顯示 policy violation 錯誤
// - GPS 錯誤: 顯示友善訊息
```

---

### 3. 錯誤處理策略

#### 3.1 後端 403 LOCATION_POLICY_VIOLATION

**檢測**:
```javascript
if (error.response?.status === 403 && 
    error.response?.data?.detail?.error_code === 'LOCATION_POLICY_VIOLATION')
```

**處理**:
- 顯示後端回傳的錯誤訊息
- 如果有 `nearest_location`，顯示最近地點和距離
- 讓使用者知道具體原因

**範例訊息**:
```
不在允許的打卡範圍內。最近的地點：台北101工地（距離 250 公尺）

最近的允許地點：台北101工地
距離：250 公尺
```

---

#### 3.2 GPS 權限被拒絕

**檢測**:
```javascript
else if (error.code === 'PERMISSION_DENIED')
```

**處理**:
```
需要定位權限才能外出打卡
請在瀏覽器設定中允許定位後重試
```

---

#### 3.3 GPS 超時

**檢測**:
```javascript
else if (error.code === 'TIMEOUT')
```

**處理**:
```
定位請求逾時
請確認 GPS 訊號良好後重試
```

---

#### 3.4 GPS 無法取得

**檢測**:
```javascript
else if (error.code === 'POSITION_UNAVAILABLE')
```

**處理**:
```
無法取得定位資訊
請確認已開啟定位服務
```

---

### 4. 為什麼不需要前端 precheck？

**原因**:
1. **架構已經很好**: 前端取得 GPS → 後端驗證 → 前端顯示結果
2. **避免重複邏輯**: 前端 precheck 需要重複實作距離計算和 policy 邏輯
3. **維護成本**: 前後端兩套邏輯容易不一致
4. **使用者體驗**: 錯誤訊息已經很清楚，不需要提前檢查

**如果未來需要 precheck**:
- 可以加入 `useLocationPolicy` composable
- 實作 `fetchPolicy()` 和 `checkLocationLocally()`
- 但目前的實作已經足夠好

---

## 驗證結果

### 語法驗證 ✅

```bash
✅ Home.vue 修改成功
✅ LOCATION_POLICY_VIOLATION 處理已加入
✅ nearest_location 處理已加入
✅ GPS 錯誤處理已加入
```

### 功能驗證（待測試環境）

**測試案例**:
1. ⏳ 無 policy → 正常打卡
2. ⏳ 有 policy + 在範圍內 → 正常打卡
3. ⏳ 有 policy + 超出範圍 → 顯示 policy violation 錯誤
4. ⏳ GPS permission denied → 顯示友善訊息
5. ⏳ GPS timeout → 顯示友善訊息
6. ⏳ GPS unavailable → 顯示友善訊息

---

## 相容性確認

### 不影響的流程 ✅

- ✅ BREAK_IN（使用不同的函數）
- ✅ punch-in（使用不同的函數）
- ✅ punch-out（使用不同的函數）
- ✅ OUT Checkpoint（使用不同的函數）

### 共用的基礎設施

- ✅ `useLocation` composable（可被其他流程重用）
- ✅ 錯誤處理模式（可被其他流程參考）

---

## 未實作的內容（留待後續）

### Step 3B: Admin UI（後續票）

**不在 Step 3A 範圍**:
- ❌ 管理端地點列表頁面
- ❌ 新增/編輯地點表單
- ❌ Map picker
- ❌ 地圖視覺化

**原因**: 
- Admin UI 是獨立功能
- 不影響打卡流程
- 工作量較大，應該獨立成票

---

### 前端 Precheck（可選，未實作）

**不在 Step 3A 範圍**:
- ❌ `useLocationPolicy` composable
- ❌ `fetchPolicy()` API
- ❌ `checkLocationLocally()` 前端驗證
- ❌ 提前顯示錯誤訊息

**原因**:
- 目前的錯誤處理已經足夠友善
- 避免前後端邏輯重複
- 降低維護成本
- 如果未來需要，可以輕鬆加入

---

### 其他打卡流程（後續票）

**不在 Step 3A 範圍**:
- ❌ BREAK_IN location policy
- ❌ punch-in location policy
- ❌ punch-out location policy

**原因**: Step 3A 只專注於 BREAK_OUT

---

## 後續建議

### 1. 部署與測試

**立即可執行**:
1. 部署到測試環境
2. 執行 Manual QA
3. 測試各種錯誤情況
4. 驗證錯誤訊息友善度

---

### 2. 如果需要前端 Precheck

**可選的增強**:
1. 建立 `useLocationPolicy` composable
2. 實作 `fetchPolicy()` 取得公司 policy
3. 實作 `checkLocationLocally()` 前端驗證
4. 在送出 API 前提前檢查並顯示錯誤

**優點**:
- 節省不必要的 API 請求
- 更快的錯誤回饋

**缺點**:
- 增加前端複雜度
- 需要維護兩套邏輯
- 可能出現不一致

---

### 3. Step 3B: Admin UI

**建議**:
- 獨立成新票
- 實作地點管理頁面
- 提供 CRUD 介面
- 考慮加入 Map picker

---

## 結論

### ✅ WP-11-13 Step 3A 已完成

**完成項目**:
1. ✅ BREAK_OUT 錯誤處理增強
2. ✅ 後端 403 LOCATION_POLICY_VIOLATION 處理
3. ✅ GPS 錯誤訊息優化
4. ✅ 友善的使用者提示

**修改檔案**: 1 個
- `frontend/src/views/Home.vue`

**修改行數**: ~30 行（錯誤處理邏輯）

**無破壞性變更**: ✅
- 不影響其他打卡流程
- 不影響既有功能
- 向後相容

**下一步**:
- 部署到測試環境
- Manual QA
- （可選）Step 3B: Admin UI

---

**建立日期**: 2026-03-08  
**狀態**: ✅ 已完成  
**可部署**: ✅ Yes  
**下一步**: 部署與測試
