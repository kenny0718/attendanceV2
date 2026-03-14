# WP-11-12 Kickoff & Design Document

**票號**: WP-11-12  
**標題**: Shared Location Foundation - Minimal Implementation Slice  
**優先級**: P1  
**狀態**: In Progress  
**開始日期**: 2026-03-08

---

## 執行摘要

本票建立 **shared location foundation**，提供可重用的 location 基礎模組，取代臨時的 `locationAdapter`。

**關鍵原則**:
- ✅ Minimal Implementation Slice - 只做最小可用切片
- ✅ 先建立 foundation，再做漸進式接入
- ✅ 第一刀只接入外出打卡流程
- ✅ 不破壞 WP-11-11.5 已驗證通過的主流程
- ✅ 不做 geofence / map / out-checkpoints

---

## Phase 1: Discovery / Design（已完成）

### 1.1 文件閱讀

已閱讀以下文件：
- ✅ `docs/NEXT_WP_TICKET.md` - WP-11-12 規劃
- ✅ `docs/ATTENDANCE_LOCATION_MODULE_SPEC.md` - useLocation 規格
- ✅ `docs/AI_CONTEXT.md` - 專案架構指引
- ✅ `docs/GATE_PROGRESS_TRACKER.md` - 進度追蹤

### 1.2 現有 Location 實作盤點

#### 目前 Location 相關檔案

| 檔案 | 類型 | 狀態 | 用途 |
|------|------|------|------|
| `frontend/src/utils/locationAdapter.js` | 過渡層 | ✅ 存在 | 臨時 adapter，待替換 |
| `frontend/src/stores/attendance.js` | Store | ✅ 存在 | 包含重複的 GPS 方法 |
| `frontend/src/views/Home.vue` | View | ✅ 存在 | 使用 locationAdapter |

#### Location 使用點分析

**1. locationAdapter.js（過渡層）**
```javascript
// 提供的功能：
- detectDeviceType()      // 裝置類型判斷
- getGPSLocation()        // GPS 定位獲取
- isGPSRequired()         // 是否需要 GPS
- getLocationIfRequired() // 條件式獲取定位
- LocationError           // 錯誤類別
- LocationErrorCode       // 錯誤碼
```

**2. attendance.js（Store）**
```javascript
// 重複實作的方法（需要移除）：
- detectDeviceType()  // 第 219 行
- getGPSLocation()    // 第 225 行

// 使用 location 的流程：
- outCheckpointSubmit()  // OUT checkpoint（已停用）
```

**3. Home.vue（View）**
```javascript
// 使用點：
- import { detectDeviceType } from '@/utils/locationAdapter'
- onMounted() 中設定 deviceType
```

#### 直接使用 navigator.geolocation 的地方

1. ✅ `locationAdapter.js` - 已封裝
2. ✅ `attendance.js` - 重複實作（需移除）
3. ❌ 其他地方 - 無

#### 哪些流程會共用 location 能力

| 流程 | 目前狀態 | 是否需要 GPS | 優先級 |
|------|---------|-------------|--------|
| 上班打卡 | ✅ 穩定 | ❌ 不需要 | P2（後續） |
| 下班打卡 | ✅ 穩定 | ❌ 不需要 | P2（後續） |
| 外出打卡 | ✅ 穩定 | ✅ Mobile 需要 | **P0（第一刀）** |
| 返回打卡 | ✅ 穩定 | ✅ Mobile 需要 | P1（第二刀） |
| OUT Checkpoint | ⏸️ 已停用 | ✅ Mobile 需要 | P3（後續票） |

**選擇外出打卡作為第一刀的理由**：
1. ✅ 本來就最依賴定位（Mobile 必須有 GPS）
2. ✅ 流程相對獨立，不影響上下班打卡
3. ✅ 最適合驗證 shared location foundation
4. ✅ 風險可控，即使失敗也不影響主流程

---

### 1.3 Shared Location Foundation 責任邊界

#### 包含（In Scope）

**Core Responsibilities**:
- ✅ 裝置類型判斷（mobile / pc）
- ✅ GPS 定位獲取
- ✅ 權限狀態追蹤（granted / denied / prompt / unknown）
- ✅ Loading 狀態管理
- ✅ 統一錯誤處理（NOT_SUPPORTED / PERMISSION_DENIED / TIMEOUT / etc）
- ✅ 成功回傳結構標準化
- ✅ Reactive state（Vue 3 Composition API）
- ✅ 條件式獲取定位（根據裝置類型）

**API Interface**:
```javascript
// State
- location: Ref<LocationData | null>
- error: Ref<LocationError | null>
- isLoading: Ref<boolean>
- deviceType: Ref<'mobile' | 'pc'>
- permissionState: Ref<'granted' | 'denied' | 'prompt' | 'unknown'>

// Methods
- getCurrentLocation(): Promise<LocationData>
- getLocationIfRequired(): Promise<LocationData | null>
- clearError(): void
- reset(): void

// Computed
- isGPSRequired: ComputedRef<boolean>
```

#### 不包含（Out of Scope）

**明確排除**:
- ❌ Geofencing 規則判斷
- ❌ Location policy 驗證
- ❌ 精度驗證
- ❌ 地圖 UI render
- ❌ 位置歷史記錄
- ❌ 位置分析
- ❌ OUT checkpoint 業務邏輯
- ❌ 複雜的快取機制
- ❌ Retry 機制（第一版不做，保持簡單）

---

### 1.4 UI vs Shared Domain 職責劃分

| 職責 | 歸屬 | 說明 |
|------|------|------|
| 裝置類型判斷 | **Shared** | useLocation composable |
| GPS 定位獲取 | **Shared** | useLocation composable |
| 權限狀態追蹤 | **Shared** | useLocation composable |
| Loading 狀態 | **Shared** | useLocation composable |
| 錯誤處理 | **Shared** | useLocation composable |
| 顯示 loading UI | **UI** | View component |
| 顯示錯誤訊息 | **UI** | View component |
| 打卡業務邏輯 | **Store** | attendance.js |
| API 呼叫 | **Store** | attendance.js |

---

### 1.5 Migration Strategy

**漸進式過渡，不是一次硬切**

#### Phase 1: 建立 Foundation（本票第一階段）
```
1. 建立 useLocation composable
2. 保留 locationAdapter 作為 bridge
3. 只接入外出打卡流程
4. 驗證 foundation 可用性
```

#### Phase 2: 擴展接入（本票第二階段，可選）
```
1. 接入返回打卡流程
2. 驗證多流程共用
3. 逐步移除 locationAdapter 引用
```

#### Phase 3: 完全替換（後續票）
```
1. 接入所有需要 location 的流程
2. 刪除 locationAdapter.js
3. 移除 attendance.js 中的重複方法
```

**關鍵原則**:
- ✅ 每次只改一條流程
- ✅ 保持向後相容
- ✅ 充分測試後再繼續
- ✅ 隨時可以回滾

---

## Phase 2: Minimal Implementation Slice

### 2.1 實作範圍

**第一刀：只做外出打卡流程**

#### 建立檔案

1. **`frontend/src/composables/useLocation.js`**
   - 新建 composable
   - 實作 core location logic
   - Reactive state management

2. **`frontend/src/composables/README.md`**
   - 說明 composables 目錄用途
   - useLocation 使用範例

#### 修改檔案

1. **`frontend/src/stores/attendance.js`**
   - 在 `punch()` 方法的 `BREAK_OUT` case 中使用 useLocation
   - 保留其他流程不動
   - 保留 `detectDeviceType()` 和 `getGPSLocation()` 方法（暫時）

2. **`frontend/src/views/Home.vue`**
   - 在外出打卡相關邏輯中使用 useLocation
   - 顯示 loading / error state
   - 保留其他流程不動

#### 不修改檔案

- ❌ `frontend/src/utils/locationAdapter.js` - 保留作為 bridge
- ❌ 上班/下班打卡流程 - 保持不動
- ❌ 返回打卡流程 - 保持不動（第二刀再做）

---

### 2.2 useLocation Composable 設計

#### 最小 API（第一版）

```javascript
// frontend/src/composables/useLocation.js

import { ref, computed } from 'vue'

/**
 * Location 資料結構
 */
export interface LocationData {
  latitude: number
  longitude: number
  accuracy: number
  captured_at: string  // ISO 8601
  provider: 'gps'
}

/**
 * Location 錯誤結構
 */
export interface LocationError {
  code: string
  message: string
  originalError?: Error
}

/**
 * Location 錯誤碼
 */
export const LocationErrorCode = {
  NOT_SUPPORTED: 'NOT_SUPPORTED',
  PERMISSION_DENIED: 'PERMISSION_DENIED',
  POSITION_UNAVAILABLE: 'POSITION_UNAVAILABLE',
  TIMEOUT: 'TIMEOUT',
  UNKNOWN: 'UNKNOWN'
}

/**
 * useLocation Composable
 * 
 * 提供統一的 location 服務
 * 
 * @param {Object} options - 選項
 * @returns {Object} Location state and methods
 */
export function useLocation(options = {}) {
  // State
  const location = ref(null)
  const error = ref(null)
  const isLoading = ref(false)
  const deviceType = ref('pc')
  
  // Options
  const defaultOptions = {
    enableHighAccuracy: true,
    timeout: 10000,
    maximumAge: 0,
    ...options
  }
  
  // Computed
  const isGPSRequired = computed(() => deviceType.value === 'mobile')
  
  // Methods
  function detectDeviceType() {
    const userAgent = navigator.userAgent || ''
    const isMobile = /Mobile|Android|iPhone|iPad|iPod/i.test(userAgent)
    deviceType.value = isMobile ? 'mobile' : 'pc'
    return deviceType.value
  }
  
  async function getCurrentLocation() {
    isLoading.value = true
    error.value = null
    
    try {
      if (!navigator.geolocation) {
        throw createLocationError(
          '此裝置不支援定位功能',
          LocationErrorCode.NOT_SUPPORTED
        )
      }
      
      const position = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
          resolve,
          reject,
          defaultOptions
        )
      })
      
      const locationData = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        captured_at: new Date().toISOString(),
        provider: 'gps'
      }
      
      location.value = locationData
      return locationData
      
    } catch (err) {
      const locationError = mapGeolocationError(err)
      error.value = locationError
      throw locationError
      
    } finally {
      isLoading.value = false
    }
  }
  
  async function getLocationIfRequired() {
    if (isGPSRequired.value) {
      return await getCurrentLocation()
    }
    return null
  }
  
  function clearError() {
    error.value = null
  }
  
  function reset() {
    location.value = null
    error.value = null
    isLoading.value = false
  }
  
  // Helper functions
  function createLocationError(message, code, originalError = null) {
    return {
      code,
      message,
      originalError
    }
  }
  
  function mapGeolocationError(err) {
    let message = '無法獲取定位'
    let code = LocationErrorCode.UNKNOWN
    
    if (err.code) {
      switch (err.code) {
        case 1: // PERMISSION_DENIED
          message = '請開啟定位權限後再外出打點'
          code = LocationErrorCode.PERMISSION_DENIED
          break
        case 2: // POSITION_UNAVAILABLE
          message = '定位資訊無法取得'
          code = LocationErrorCode.POSITION_UNAVAILABLE
          break
        case 3: // TIMEOUT
          message = '定位請求逾時'
          code = LocationErrorCode.TIMEOUT
          break
      }
    }
    
    return createLocationError(message, code, err)
  }
  
  // Initialize
  detectDeviceType()
  
  return {
    // State
    location,
    error,
    isLoading,
    deviceType,
    
    // Computed
    isGPSRequired,
    
    // Methods
    getCurrentLocation,
    getLocationIfRequired,
    clearError,
    reset
  }
}
```

---

### 2.3 接入外出打卡流程

#### 修改 attendance.js

```javascript
// 在 BREAK_OUT case 中使用 useLocation

case 'BREAK_OUT':
  // 如果需要 GPS，使用 useLocation
  if (notes) {
    // 外出打卡需要定位
    const { getLocationIfRequired, deviceType } = useLocation()
    
    try {
      const gpsData = await getLocationIfRequired()
      
      const payload = { notes }
      if (gpsData) {
        payload.gps = gpsData
      }
      
      response = await attendanceApi.breakOut(payload)
    } catch (locationError) {
      // 定位失敗，拋出友善錯誤
      throw new Error(locationError.message)
    }
  } else {
    // 沒有原因，直接打卡（不需要定位）
    response = await attendanceApi.breakOut({ notes: notes || '' })
  }
  
  this.todayStatus.break_out = response.punch_time
  this.todayStatus.is_on_break = true
  localStorage.setItem('is_on_break', 'true')
  await this.loadBreakPunches()
  break
```

---

### 2.4 測試與驗證

#### Composable 層測試

**測試案例**:
1. ✅ 成功取得位置（Mobile）
2. ✅ PC 不需要位置
3. ✅ 使用者拒絕權限
4. ✅ 瀏覽器不支援
5. ✅ Timeout 情境
6. ✅ 裝置類型判斷正確

#### 整合驗證

**驗證項目**:
1. ✅ 外出打卡流程正常
2. ✅ Mobile 可以取得 GPS
3. ✅ PC 不要求 GPS
4. ✅ Loading 狀態正確顯示
5. ✅ 錯誤訊息正確顯示
6. ✅ 不影響其他已穩定流程（上班/下班/返回）

---

## 未來擴充點

### 後續票次規劃

**WP-11-12 第二階段（可選）**:
- 接入返回打卡流程
- 驗證多流程共用

**WP-11-13: Location Policy**:
- Geofencing 規則
- 精度驗證
- 範圍驗證

**WP-11-14: UI Enhancement**:
- 地圖顯示
- 位置標記
- 歷史軌跡

**WP-11-15: OUT Checkpoints**:
- 後端 API 實作
- 前端完整 UI
- 列表管理

---

## Definition of Done

### 第一階段完成條件

- [ ] ✅ `useLocation` composable 已建立
- [ ] ✅ 外出打卡流程已接入 useLocation
- [ ] ✅ 現有已通過 QA 的主流程沒有被破壞
- [ ] ✅ Composable 層測試通過
- [ ] ✅ 整合驗證通過
- [ ] ✅ 文件已更新

### 驗收標準

**功能驗收**:
- [ ] 外出打卡（Mobile）可以取得 GPS
- [ ] 外出打卡（PC）不要求 GPS
- [ ] Loading 狀態正確
- [ ] 錯誤處理正確
- [ ] 上班/下班/返回打卡不受影響

**程式碼品質**:
- [ ] 程式碼清晰易讀
- [ ] 註解完整
- [ ] 無 console error
- [ ] 無 linter error

**文件完整**:
- [ ] useLocation API 文件
- [ ] 使用範例
- [ ] Migration plan
- [ ] 測試報告

---

## 風險評估

### 高風險

| 風險 | 影響 | 機率 | 緩解措施 |
|------|------|------|----------|
| 破壞現有打卡功能 | 高 | 低 | 只改外出打卡，其他流程不動 |
| GPS 取得失敗 | 中 | 中 | 完整錯誤處理，友善錯誤訊息 |

### 中風險

| 風險 | 影響 | 機率 | 緩解措施 |
|------|------|------|----------|
| 效能問題 | 中 | 低 | 使用 Vue 3 reactive，效能良好 |
| 測試覆蓋不足 | 中 | 中 | 補充單元測試和整合測試 |

---

## 時程規劃

### Phase 1: Foundation（1-2 天）

**Day 1**:
- 建立 `useLocation` composable
- 實作 core logic
- 基本測試

**Day 2**:
- 接入外出打卡流程
- 整合測試
- 文件更新

### Phase 2: Verification（0.5 天）

- 完整驗證
- Bug fix
- 最終測試

---

**建立日期**: 2026-03-08  
**最後更新**: 2026-03-08  
**狀態**: Ready to Implement
