# WP-11-12 Phase 2B 程式碼修改實作指引

**票號**: WP-11-12  
**階段**: Phase 2B Implementation  
**日期**: 2026-03-08

---

## 修改檔案 1: frontend/src/views/Home.vue

### 修改 1.1: 添加 useLocation import

**位置**: 第 320 行附近（import 區塊）

**在這一行之後**:
```javascript
import { detectDeviceType } from '@/utils/locationAdapter'
```

**添加**:
```javascript
import { useLocation } from '@/composables/useLocation'
```

---

### 修改 1.2: 使用 useLocation

**位置**: 第 360 行附近（在 `const deviceType = ref('pc')` 之後）

**添加**:
```javascript
// WP-11-12: 使用 shared location foundation
const {
  location: currentLocation,
  error: locationError,
  isLoading: locationLoading,
  deviceType: detectedDeviceType,
  isGPSRequired,
  getLocationIfRequired
} = useLocation()
```

---

### 修改 1.3: 修改 handlePunch 函數

**位置**: 第 399 行附近

**找到**:
```javascript
// 處理打卡
const handlePunch = async (type) => {
  // 清除之前的錯誤
  attendanceStore.clearError()
  
  try {
    // 如果是外出打卡，使用選擇的原因
    let notes = ''
    if (type === 'BREAK_OUT' && selectedReason.value) {
      notes = selectedReason.value
    }
    
    await attendanceStore.punch(type, notes)
```

**替換為**:
```javascript
// 處理打卡
const handlePunch = async (type) => {
  // 清除之前的錯誤
  attendanceStore.clearError()
  
  try {
    // WP-11-12: 外出打卡使用 shared location foundation
    if (type === 'BREAK_OUT') {
      await handleBreakOutPunch()
      return
    }
    
    // 其他打卡類型保持原有邏輯
    let notes = ''
    if (type === 'BREAK_IN' && selectedReason.value) {
      notes = selectedReason.value
    }
    
    await attendanceStore.punch(type, notes)
```

---

### 修改 1.4: 添加 handleBreakOutPunch 函數

**位置**: 在 handlePunch 函數之後

**添加**:
```javascript
// WP-11-12: 外出打卡專用處理函數
// UI 層主導 location 取得，store 層處理業務邏輯
const handleBreakOutPunch = async () => {
  try {
    // Step 1: UI 層取得 location
    const gpsData = await getLocationIfRequired()
    
    // Step 2: 傳給 store 處理業務邏輯
    await attendanceStore.punchWithLocation('BREAK_OUT', {
      notes: selectedReason.value || '',
      gps: gpsData
    })
    
    // 顯示成功訊息
    successMessage.value = '打卡成功'
    showSuccessMessage.value = true
    setTimeout(() => {
      showSuccessMessage.value = false
    }, 3000)
    
  } catch (error) {
    console.error('外出打卡失敗:', error)
    
    // 顯示友善的錯誤訊息
    errorMessage.value = error.message || '打卡失敗，請稍後再試'
    showErrorMessage.value = true
    
    setTimeout(() => {
      showErrorMessage.value = false
    }, 5000)
  }
}
```

---

### 修改 1.5: 更新 template loading 顯示

**位置**: 第 68 行附近（Loading 狀態區塊）

**找到**:
```vue
<!-- Loading 狀態 -->
<div v-if="isLoading" class="loading-overlay">
  <div class="loading-spinner"></div>
  <p class="text-text-secondary mt-2">打卡中...</p>
</div>
```

**替換為**:
```vue
<!-- Loading 狀態 -->
<div v-if="isLoading || locationLoading" class="loading-overlay">
  <div class="loading-spinner"></div>
  <p class="text-text-secondary mt-2">
    {{ locationLoading ? '定位中...' : '打卡中...' }}
  </p>
</div>
```

---

### 修改 1.6: 更新 template error 顯示

**位置**: 第 150 行附近（錯誤提示區塊）

**找到**:
```vue
<!-- 錯誤提示 -->
<div 
  v-if="showErrorMessage" 
  class="error-toast fixed bottom-8 right-8 bg-error text-white px-6 py-3 rounded-lg shadow-xl z-50 max-w-md"
>
  <div class="flex items-start gap-2">
    <svg class="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
    </svg>
    <span>{{ errorMessage }}</span>
  </div>
</div>
```

**替換為**:
```vue
<!-- 錯誤提示 -->
<div 
  v-if="showErrorMessage || locationError" 
  class="error-toast fixed bottom-8 right-8 bg-error text-white px-6 py-3 rounded-lg shadow-xl z-50 max-w-md"
>
  <div class="flex items-start gap-2">
    <svg class="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
    </svg>
    <span>{{ locationError?.message || errorMessage }}</span>
  </div>
</div>
```

---

## 修改檔案 2: frontend/src/stores/attendance.js

### 修改 2.1: 添加 punchWithLocation 方法

**位置**: 在 `punch()` 方法之後（約第 130 行）

**添加**:
```javascript
// WP-11-12: 接收 location 作為參數的打卡方法
// UI 層負責取得 location，store 層負責業務邏輯
async punchWithLocation(type, payload) {
  // 防止重複點擊
  if (this.isLoading) {
    console.warn('操作進行中，請稍候...')
    return
  }
  
  this.isLoading = true
  this.error = null
  this.lastAction = type
  
  try {
    let response
    
    switch (type) {
      case 'BREAK_OUT':
        // 直接使用傳入的 payload（包含 notes 和 gps）
        response = await attendanceApi.breakOut(payload)
        this.todayStatus.break_out = response.punch_time
        this.todayStatus.is_on_break = true
        localStorage.setItem('is_on_break', 'true')
        // 打卡成功後刷新外出打卡記錄
        await this.loadBreakPunches()
        break
        
      case 'BREAK_IN':
        // 未來可以用相同方式處理返回打卡
        response = await attendanceApi.breakIn(payload)
        this.todayStatus.break_in = response.punch_time
        this.todayStatus.is_on_break = false
        localStorage.setItem('is_on_break', 'false')
        await this.loadBreakPunches()
        break
        
      default:
        throw new Error('未知的打卡類型')
    }
    
    // 打卡成功後刷新記錄
    await this.fetchRecentLogs()
    
    return { success: true, data: response }
    
  } catch (error) {
    // 統一錯誤處理
    this.error = this.handleError(error)
    
    // 發生錯誤時刷新狀態，確保 UI 與後端同步
    try {
      await this.fetchTodayStatus()
    } catch (refreshError) {
      console.error('刷新狀態失敗:', refreshError)
    }
    
    throw this.error
    
  } finally {
    this.isLoading = false
  }
},
```

---

### 修改 2.2: 標記 detectDeviceType 為 deprecated

**位置**: 第 219 行附近

**找到**:
```javascript
detectDeviceType() {
  const userAgent = navigator.userAgent || ''
  const isMobile = /Mobile|Android|iPhone|iPad|iPod/i.test(userAgent)
  return isMobile ? 'mobile' : 'pc'
},
```

**替換為**:
```javascript
// @deprecated WP-11-12: 請使用 useLocation composable
// 保留此方法僅供向後相容，未來將移除
detectDeviceType() {
  const userAgent = navigator.userAgent || ''
  const isMobile = /Mobile|Android|iPhone|iPad|iPod/i.test(userAgent)
  return isMobile ? 'mobile' : 'pc'
},
```

---

### 修改 2.3: 標記 getGPSLocation 為 deprecated

**位置**: 第 225 行附近

**找到**:
```javascript
// WP-11-11: 獲取 GPS 位置
async getGPSLocation() {
```

**替換為**:
```javascript
// @deprecated WP-11-12: 請使用 useLocation composable
// 保留此方法僅供向後相容，未來將移除
// WP-11-11: 獲取 GPS 位置
async getGPSLocation() {
```

---

## 修改檔案 3: frontend/src/utils/locationAdapter.js

### 修改 3.1: 更新檔案頭註解

**位置**: 第 1 行

**找到**:
```javascript
/**
 * Location Adapter (臨時過渡層)
 * 
 * 目的: 在 shared location module 完成前，提供統一的定位介面
 * 注意: 這是臨時方案，未來會被 useLocation composable 取代
 * 
 * @deprecated 將在 shared location module 完成後移除
 */
```

**替換為**:
```javascript
/**
 * Location Adapter (臨時過渡層 - Transitional Bridge)
 * 
 * 目的: 在 shared location module 完成前，提供統一的定位介面
 * 注意: 這是臨時方案，未來會被 useLocation composable 取代
 * 
 * @deprecated WP-11-12: 請使用 useLocation composable
 * @status Transitional Bridge - 保留供向後相容
 * @removal 當所有流程都使用 useLocation 後將移除
 * 
 * 目前狀態:
 * - BREAK_OUT: ✅ 已改用 useLocation (WP-11-12 Phase 2B)
 * - BREAK_IN: ⏳ 尚未遷移
 * - OUT Checkpoint: ⏸️ 已停用
 * - Home.vue deviceType: ⏳ 仍在使用
 */
```

---

## 驗證步驟

### 1. 編譯檢查

```bash
cd /opt/attendance-system/frontend
npm run build
# 或
npm run dev
```

確認無編譯錯誤。

---

### 2. 手動測試

#### TC-01: Mobile 外出打卡（允許定位）

1. 使用 Chrome DevTools 切換到 Mobile 模式
2. 登入系統
3. 上班打卡
4. 選擇外出原因
5. 點擊「外出打卡」
6. 允許定位權限

**預期結果**:
- ✅ 顯示「定位中...」
- ✅ 成功取得 GPS
- ✅ 外出打卡成功
- ✅ Console 無錯誤

#### TC-02: Mobile 外出打卡（拒絕定位）

1. 使用 Chrome DevTools 切換到 Mobile 模式
2. 登入系統
3. 上班打卡
4. 點擊「外出打卡」
5. 拒絕定位權限

**預期結果**:
- ✅ 顯示錯誤：「請開啟定位權限後再外出打點」
- ✅ 外出打卡失敗

#### TC-03: PC 外出打卡

1. 使用 PC 模式
2. 登入系統
3. 上班打卡
4. 點擊「外出打卡」

**預期結果**:
- ✅ 不要求 GPS
- ✅ 直接外出打卡成功

#### TC-04: 回歸測試

- ✅ 上班打卡：正常
- ✅ 下班打卡：正常
- ✅ 返回打卡：正常

---

## 提交 Git

```bash
cd /opt/attendance-system

git add frontend/src/views/Home.vue
git add frontend/src/stores/attendance.js
git add frontend/src/utils/locationAdapter.js
git add docs/WP-11-12_PHASE2B_IMPLEMENTATION_REPORT.md

git commit -m "feat(location): WP-11-12 Phase 2B - BREAK_OUT Integration

實作內容：
- Home.vue: 使用 useLocation，UI 層主導 location 取得
- attendance.js: 新增 punchWithLocation 方法
- locationAdapter: 標記為 transitional bridge

架構：
- UI 層唯一使用 useLocation()
- Store 層只接收 location payload
- 避免雙重 useLocation() state

測試：
- BREAK_OUT 已接入 shared location foundation
- 不破壞已穩定流程
- 為未來 location policy 預留擴充點

相關：
- WP-11-12 Phase 2B
- 前置: Phase 2A (設計完成)
- 下一步: BREAK_IN 遷移或 WP-11-13 準備"
```

---

**建立日期**: 2026-03-08  
**最後更新**: 2026-03-08  
**狀態**: Ready for Implementation
