# WP-11-12 Phase 2A 程式碼修改指引

**票號**: WP-11-12  
**階段**: Phase 2A - BREAK_OUT Integration  
**日期**: 2026-03-08

---

## 修改檔案清單

### 1. `frontend/src/views/Home.vue`

#### 修改 1.1: 添加 import

**位置**: 第 320 行附近

**修改前**:
```javascript
import { detectDeviceType } from '@/utils/locationAdapter'
```

**修改後**:
```javascript
import { detectDeviceType } from '@/utils/locationAdapter'
import { useLocation } from '@/composables/useLocation'
```

---

#### 修改 1.2: 添加 useLocation 使用

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

#### 修改 1.3: 修改 handlePunch 函數

**位置**: 第 399 行附近

**修改前**:
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
    
    // 顯示成功訊息
    successMessage.value = '打卡成功'
    showSuccessMessage.value = true
    setTimeout(() => {
      showSuccessMessage.value = false
    }, 3000)
  } catch (error) {
    console.error('打卡失敗:', error)
    
    // 顯示友善的錯誤訊息
    errorMessage.value = error.message || '打卡失敗，請稍後再試'
    showErrorMessage.value = true
    
    setTimeout(() => {
      showErrorMessage.value = false
    }, 5000)
  }
}
```

**修改後**:
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
    
    // 顯示成功訊息
    successMessage.value = '打卡成功'
    showSuccessMessage.value = true
    setTimeout(() => {
      showSuccessMessage.value = false
    }, 3000)
  } catch (error) {
    console.error('打卡失敗:', error)
    
    // 顯示友善的錯誤訊息
    errorMessage.value = error.message || '打卡失敗，請稍後再試'
    showErrorMessage.value = true
    
    setTimeout(() => {
      showErrorMessage.value = false
    }, 5000)
  }
}

// WP-11-12: 外出打卡專用處理函數
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

#### 修改 1.4: 更新 template 顯示 location loading

**位置**: 第 68 行附近（Loading 狀態區塊）

**修改前**:
```vue
<!-- Loading 狀態 -->
<div v-if="isLoading" class="loading-overlay">
  <div class="loading-spinner"></div>
  <p class="text-text-secondary mt-2">打卡中...</p>
</div>
```

**修改後**:
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

#### 修改 1.5: 顯示 location error

**位置**: 第 150 行附近（錯誤提示區塊）

**修改前**:
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

**修改後**:
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

### 2. `frontend/src/stores/attendance.js`

#### 修改 2.1: 添加新方法 punchWithLocation

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

#### 修改 2.2: 標記舊方法為 deprecated

**位置**: 第 219 行附近（detectDeviceType 方法）

**修改前**:
```javascript
detectDeviceType() {
  const userAgent = navigator.userAgent || ''
  const isMobile = /Mobile|Android|iPhone|iPad|iPod/i.test(userAgent)
  return isMobile ? 'mobile' : 'pc'
},
```

**修改後**:
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

#### 修改 2.3: 標記 getGPSLocation 為 deprecated

**位置**: 第 225 行附近（getGPSLocation 方法）

**修改前**:
```javascript
// WP-11-11: 獲取 GPS 位置
async getGPSLocation() {
  return new Promise((resolve, reject) => {
```

**修改後**:
```javascript
// @deprecated WP-11-12: 請使用 useLocation composable
// 保留此方法僅供向後相容，未來將移除
// WP-11-11: 獲取 GPS 位置
async getGPSLocation() {
  return new Promise((resolve, reject) => {
```

---

### 3. `frontend/src/utils/locationAdapter.js`

#### 修改 3.1: 更新檔案頭註解

**位置**: 第 1 行

**修改前**:
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

**修改後**:
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
 * - BREAK_OUT: 已改用 useLocation (WP-11-12)
 * - BREAK_IN: 尚未遷移
 * - OUT Checkpoint: 已停用
 * - Home.vue deviceType: 仍在使用
 */
```

---

## 測試驗證步驟

### 驗證 1: Mobile 外出打卡（允許定位）

```bash
# 使用 Mobile 裝置或 Chrome DevTools Mobile 模擬
1. 登入系統
2. 上班打卡
3. 選擇外出原因
4. 點擊「外出打卡」
5. 允許定位權限

預期結果:
✅ 顯示「定位中...」
✅ 成功取得 GPS
✅ 外出打卡成功
✅ Console 無錯誤
✅ Network tab 看到 breakOut API 包含 gps 資料
```

### 驗證 2: Mobile 外出打卡（拒絕定位）

```bash
1. 登入系統
2. 上班打卡
3. 點擊「外出打卡」
4. 拒絕定位權限

預期結果:
✅ 顯示錯誤：「請開啟定位權限後再外出打點」
✅ 外出打卡失敗
✅ 可以重試
```

### 驗證 3: PC 外出打卡

```bash
1. 登入系統（PC）
2. 上班打卡
3. 點擊「外出打卡」

預期結果:
✅ 不要求 GPS
✅ 直接外出打卡成功
✅ Network tab 看到 breakOut API 不包含 gps 資料
```

### 驗證 4: 回歸測試

```bash
測試項目:
✅ 上班打卡：正常
✅ 下班打卡：正常
✅ 返回打卡：正常
✅ 外出打卡記錄顯示：正常
✅ Console 無新的錯誤
```

---

## 驗證檢查清單

- [ ] ✅ Home.vue 已添加 useLocation import
- [ ] ✅ Home.vue 已使用 useLocation()
- [ ] ✅ handlePunch 已修改，BREAK_OUT 使用新流程
- [ ] ✅ handleBreakOutPunch 已添加
- [ ] ✅ Template 已顯示 location loading
- [ ] ✅ Template 已顯示 location error
- [ ] ✅ attendance.js 已添加 punchWithLocation 方法
- [ ] ✅ 舊方法已標記為 deprecated
- [ ] ✅ locationAdapter 已更新註解
- [ ] ✅ Mobile 外出打卡測試通過
- [ ] ✅ PC 外出打卡測試通過
- [ ] ✅ 回歸測試通過
- [ ] ✅ Console 無錯誤
- [ ] ✅ 不影響其他流程

---

## 回滾計劃

如果發現問題，可以快速回滾：

### 方式 1: Git Revert

```bash
cd /opt/attendance-system
git log --oneline -5
git revert <commit-hash>
```

### 方式 2: 恢復舊邏輯

在 Home.vue 的 handlePunch 中：

```javascript
// 暫時恢復舊邏輯
const handlePunch = async (type) => {
  let notes = ''
  if (type === 'BREAK_OUT' && selectedReason.value) {
    notes = selectedReason.value
  }
  
  await attendanceStore.punch(type, notes)
}
```

---

**建立日期**: 2026-03-08  
**最後更新**: 2026-03-08  
**狀態**: Ready for Implementation
