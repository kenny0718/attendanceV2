# Attendance Location Module Specification

**版本**: 1.0  
**日期**: 2026-03-08  
**狀態**: 設計中  
**票號**: WP-11-12

---

## 執行摘要

本規格定義 `useLocation` composable 的設計，用於取代臨時的 `locationAdapter`。此模組提供統一的位置服務介面，支援裝置類型判斷、GPS 定位獲取、錯誤處理、loading 狀態管理和 retry 機制。

**關鍵原則**:
- 向後相容優先
- 不修改後端 API
- 不修改 payload 格式
- 使用 Vue 3 Composition API
- 支援多元件共用

---

## 目標與範圍

### 目標

1. **取代 locationAdapter**: 提供正式的 composable 取代臨時 adapter
2. **統一位置服務**: 集中管理所有位置相關邏輯
3. **改善開發體驗**: 提供 reactive state 和清晰的 API
4. **提升可測試性**: 易於 mock 和測試
5. **為未來擴展鋪路**: 為 geofencing 和 policy 預留擴展點

### 範圍內

- ✅ 裝置類型判斷
- ✅ GPS 定位獲取
- ✅ 統一錯誤處理
- ✅ Loading 狀態管理
- ✅ Retry 機制
- ✅ 權限狀態追蹤
- ✅ 向後相容保證

### 範圍外（後續票）

- ❌ Geofencing（WP-11-13）
- ❌ Location policy（WP-11-13）
- ❌ 精度驗證（WP-11-13）
- ❌ 地圖 UI（WP-11-14）
- ❌ 位置分析（WP-11-15）

---

## API 設計

### useLocation Composable

```typescript
interface UseLocationOptions {
  enableHighAccuracy?: boolean
  timeout?: number
  maximumAge?: number
  autoRetry?: boolean
  maxRetries?: number
  retryDelay?: number
}

interface LocationData {
  latitude: number
  longitude: number
  accuracy: number
  captured_at: string  // ISO 8601
  provider: 'gps' | 'network' | 'fused'
}

interface LocationError {
  code: LocationErrorCode
  message: string
  originalError?: Error
}

enum LocationErrorCode {
  NOT_SUPPORTED = 'NOT_SUPPORTED',
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  POSITION_UNAVAILABLE = 'POSITION_UNAVAILABLE',
  TIMEOUT = 'TIMEOUT',
  UNKNOWN = 'UNKNOWN'
}

enum DeviceType {
  MOBILE = 'mobile',
  PC = 'pc'
}

interface UseLocationReturn {
  // State
  location: Ref<LocationData | null>
  error: Ref<LocationError | null>
  isLoading: Ref<boolean>
  isSupported: Ref<boolean>
  deviceType: Ref<DeviceType>
  permissionState: Ref<'granted' | 'denied' | 'prompt' | 'unknown'>
  
  // Methods
  getCurrentLocation: () => Promise<LocationData>
  getLocationIfRequired: () => Promise<LocationData | null>
  clearError: () => void
  reset: () => void
  
  // Computed
  isGPSRequired: ComputedRef<boolean>
  canRequestLocation: ComputedRef<boolean>
}

function useLocation(options?: UseLocationOptions): UseLocationReturn
```

### 使用範例

#### 基本使用

```javascript
import { useLocation } from '@/composables/useLocation'

export default {
  setup() {
    const {
      location,
      error,
      isLoading,
      deviceType,
      getCurrentLocation,
      getLocationIfRequired
    } = useLocation()
    
    const handleSubmit = async () => {
      try {
        // 自動判斷是否需要 GPS
        const gps = await getLocationIfRequired()
        
        const payload = {
          device_type: deviceType.value,
          notes: reason.value
        }
        
        if (gps) {
          payload.gps = gps
        }
        
        await api.submit(payload)
      } catch (err) {
        console.error(err.message)
      }
    }
    
    return {
      location,
      error,
      isLoading,
      handleSubmit
    }
  }
}
```

#### 進階使用（自訂選項）

```javascript
const {
  location,
  error,
  isLoading,
  getCurrentLocation
} = useLocation({
  enableHighAccuracy: true,
  timeout: 15000,
  autoRetry: true,
  maxRetries: 3,
  retryDelay: 2000
})

// 手動獲取位置
const fetchLocation = async () => {
  try {
    const loc = await getCurrentLocation()
    console.log('位置:', loc.latitude, loc.longitude)
  } catch (err) {
    if (err.code === LocationErrorCode.PERMISSION_DENIED) {
      // 處理權限拒絕
    }
  }
}
```

#### 在 Store 中使用

```javascript
import { useLocation } from '@/composables/useLocation'

export const useAttendanceStore = defineStore('attendance', {
  actions: {
    async outCheckpointSubmit(reasonText) {
      const { getLocationIfRequired, deviceType } = useLocation()
      
      const payload = {
        device_type: deviceType.value,
        notes: reasonText.trim()
      }
      
      const gpsData = await getLocationIfRequired()
      if (gpsData) {
        payload.gps = gpsData
      }
      
      return await attendanceApi.createOutCheckpoint(payload)
    }
  }
})
```

---

## 狀態管理

### Reactive State

```javascript
// 內部狀態（使用 ref）
const location = ref<LocationData | null>(null)
const error = ref<LocationError | null>(null)
const isLoading = ref(false)
const isSupported = ref(false)
const deviceType = ref<DeviceType>(DeviceType.PC)
const permissionState = ref<PermissionState>('unknown')

// Computed
const isGPSRequired = computed(() => deviceType.value === DeviceType.MOBILE)
const canRequestLocation = computed(() => 
  isSupported.value && permissionState.value !== 'denied'
)
```

### 狀態生命週期

```
初始化 → 檢查支援 → 判斷裝置 → 準備就緒
                                    ↓
                              請求位置
                                    ↓
                    ┌───────────────┴───────────────┐
                    ↓                               ↓
                成功                             失敗
                    ↓                               ↓
            更新 location                    更新 error
                    ↓                               ↓
            清除 loading                    清除 loading
                    ↓                               ↓
                  完成                      可選 retry
```

---

## 錯誤處理

### 錯誤類型

```javascript
class LocationError extends Error {
  constructor(
    public code: LocationErrorCode,
    public message: string,
    public originalError?: Error
  ) {
    super(message)
    this.name = 'LocationError'
  }
}
```

### 錯誤碼映射

| GeolocationPositionError | LocationErrorCode | 使用者訊息 |
|-------------------------|-------------------|-----------|
| PERMISSION_DENIED (1) | PERMISSION_DENIED | 請開啟定位權限後再外出打點 |
| POSITION_UNAVAILABLE (2) | POSITION_UNAVAILABLE | 定位資訊無法取得 |
| TIMEOUT (3) | TIMEOUT | 定位請求逾時 |
| - | NOT_SUPPORTED | 此裝置不支援定位功能 |
| - | UNKNOWN | 無法獲取定位 |

### 錯誤處理流程

```javascript
async function getCurrentLocation(): Promise<LocationData> {
  if (!isSupported.value) {
    throw new LocationError(
      LocationErrorCode.NOT_SUPPORTED,
      '此裝置不支援定位功能'
    )
  }
  
  isLoading.value = true
  error.value = null
  
  try {
    const position = await getPosition(options)
    location.value = mapPosition(position)
    return location.value
  } catch (err) {
    const locationError = mapError(err)
    error.value = locationError
    
    // Auto retry if enabled
    if (options.autoRetry && retryCount < options.maxRetries) {
      await delay(options.retryDelay)
      return getCurrentLocation()
    }
    
    throw locationError
  } finally {
    isLoading.value = false
  }
}
```

---

## Retry 機制

### 設計原則

1. **可選啟用**: 預設不啟用，避免過度重試
2. **指數退避**: 每次重試延遲時間遞增
3. **最大次數限制**: 避免無限重試
4. **特定錯誤重試**: 只對 TIMEOUT 和 POSITION_UNAVAILABLE 重試

### 實作

```javascript
interface RetryConfig {
  autoRetry: boolean
  maxRetries: number
  retryDelay: number
  retryableErrors: LocationErrorCode[]
}

const defaultRetryConfig: RetryConfig = {
  autoRetry: false,
  maxRetries: 3,
  retryDelay: 2000,
  retryableErrors: [
    LocationErrorCode.TIMEOUT,
    LocationErrorCode.POSITION_UNAVAILABLE
  ]
}

async function getCurrentLocationWithRetry(): Promise<LocationData> {
  let retryCount = 0
  
  while (retryCount <= options.maxRetries) {
    try {
      return await getCurrentLocation()
    } catch (err) {
      if (!shouldRetry(err, retryCount)) {
        throw err
      }
      
      retryCount++
      const delay = options.retryDelay * Math.pow(2, retryCount - 1)
      await sleep(delay)
    }
  }
  
  throw new LocationError(
    LocationErrorCode.TIMEOUT,
    '定位請求多次失敗'
  )
}

function shouldRetry(error: LocationError, retryCount: number): boolean {
  return (
    options.autoRetry &&
    retryCount < options.maxRetries &&
    options.retryableErrors.includes(error.code)
  )
}
```

---

## 裝置類型判斷

### 判斷邏輯

```javascript
function detectDeviceType(): DeviceType {
  const userAgent = navigator.userAgent || ''
  const isMobile = /Mobile|Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent)
  
  // 額外檢查 touch 支援
  const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0
  
  // 檢查螢幕尺寸
  const isSmallScreen = window.innerWidth < 768
  
  // 綜合判斷
  if (isMobile || (hasTouch && isSmallScreen)) {
    return DeviceType.MOBILE
  }
  
  return DeviceType.PC
}
```

### 判斷時機

- 初始化時判斷一次
- 不監聽 resize 事件（避免效能問題）
- 可手動重新判斷（提供 `refreshDeviceType()` 方法）

---

## 權限管理

### 權限狀態追蹤

```javascript
async function checkPermission(): Promise<PermissionState> {
  if (!navigator.permissions) {
    return 'unknown'
  }
  
  try {
    const result = await navigator.permissions.query({ name: 'geolocation' })
    permissionState.value = result.state
    
    // 監聽權限變化
    result.addEventListener('change', () => {
      permissionState.value = result.state
    })
    
    return result.state
  } catch {
    return 'unknown'
  }
}
```

### 權限請求流程

```
檢查權限狀態
    ↓
┌───┴───┐
↓       ↓
granted  prompt/denied
↓       ↓
直接獲取  請求權限
位置      ↓
        ┌─┴─┐
        ↓   ↓
      允許  拒絕
        ↓   ↓
      獲取  錯誤
      位置  處理
```

---

## 向後相容

### 與 locationAdapter 的對應

| locationAdapter | useLocation | 說明 |
|----------------|-------------|------|
| `detectDeviceType()` | `deviceType.value` | Reactive ref |
| `getGPSLocation()` | `getCurrentLocation()` | Promise-based |
| `getLocationIfRequired()` | `getLocationIfRequired()` | 相同 API |
| `LocationError` | `LocationError` | 相同類別 |
| `LocationErrorCode` | `LocationErrorCode` | 相同 enum |

### 遷移策略

**階段 1: 並存**
- useLocation 和 locationAdapter 同時存在
- 新程式碼使用 useLocation
- 舊程式碼保持不變

**階段 2: 遷移**
- 逐步替換 locationAdapter 引用
- 更新 attendance.js
- 更新 Home.vue

**階段 3: 清理**
- 刪除 locationAdapter.js
- 更新文件
- 更新測試

---

## 效能考量

### 快取策略

```javascript
interface CacheConfig {
  enabled: boolean
  maxAge: number  // milliseconds
}

const cache = {
  location: null as LocationData | null,
  timestamp: 0
}

function getCachedLocation(): LocationData | null {
  if (!options.cache.enabled) {
    return null
  }
  
  const age = Date.now() - cache.timestamp
  if (age > options.cache.maxAge) {
    return null
  }
  
  return cache.location
}

async function getCurrentLocation(): Promise<LocationData> {
  const cached = getCachedLocation()
  if (cached) {
    return cached
  }
  
  const location = await fetchLocation()
  
  cache.location = location
  cache.timestamp = Date.now()
  
  return location
}
```

### 效能指標

- **首次定位時間**: < 5 秒（高精度模式）
- **快取命中率**: > 80%（5 分鐘內重複請求）
- **記憶體使用**: < 1MB
- **CPU 使用**: 可忽略（非持續運行）

---

## 測試策略

### 單元測試

```javascript
describe('useLocation', () => {
  it('should detect device type', () => {
    const { deviceType } = useLocation()
    expect(deviceType.value).toBeOneOf(['mobile', 'pc'])
  })
  
  it('should get current location', async () => {
    const { getCurrentLocation } = useLocation()
    const location = await getCurrentLocation()
    expect(location).toHaveProperty('latitude')
    expect(location).toHaveProperty('longitude')
  })
  
  it('should handle permission denied', async () => {
    // Mock geolocation API
    mockGeolocationError(GeolocationPositionError.PERMISSION_DENIED)
    
    const { getCurrentLocation } = useLocation()
    await expect(getCurrentLocation()).rejects.toThrow(LocationError)
  })
  
  it('should retry on timeout', async () => {
    const { getCurrentLocation } = useLocation({
      autoRetry: true,
      maxRetries: 2
    })
    
    // First call fails, second succeeds
    mockGeolocationTimeout().then(mockGeolocationSuccess())
    
    const location = await getCurrentLocation()
    expect(location).toBeDefined()
  })
})
```

### 整合測試

- 與 attendance store 整合
- 與 OUT checkpoint API 整合
- 多元件同時使用

### E2E 測試

- Mobile 裝置流程
- PC 裝置流程
- 權限拒絕流程
- 超時重試流程

---

## 安全考量

### 隱私保護

1. **最小權限原則**: 只在需要時請求定位
2. **使用者同意**: 明確告知為何需要定位
3. **資料加密**: GPS 資料傳輸使用 HTTPS
4. **不持久化**: 不在前端長期儲存 GPS 資料

### 錯誤資訊

- 不洩漏系統內部資訊
- 錯誤訊息對使用者友善
- 詳細錯誤記錄到 console（開發模式）

---

## 未來擴展

### 預留擴展點

```javascript
interface UseLocationOptions {
  // 現有選項
  enableHighAccuracy?: boolean
  timeout?: number
  
  // 未來擴展（WP-11-13）
  policy?: LocationPolicy
  geofencing?: GeofencingConfig
  validation?: ValidationRules
  
  // 未來擴展（WP-11-14）
  mapIntegration?: MapConfig
  
  // 未來擴展（WP-11-15）
  analytics?: AnalyticsConfig
}
```

### 擴展方向

1. **Location Policy（WP-11-13）**
   - 範圍驗證
   - 精度要求
   - 自訂規則

2. **地圖整合（WP-11-14）**
   - 顯示當前位置
   - 顯示歷史軌跡
   - 互動功能

3. **分析功能（WP-11-15）**
   - 位置統計
   - 異常偵測
   - 報表生成

---

## 決策記錄

### 為什麼使用 Composable 而非 Store？

**決定**: 使用 Composable  
**原因**:
- 更靈活，可在任何元件使用
- 不需要全域狀態
- 更容易測試
- 符合 Vue 3 最佳實踐

### 為什麼不使用 Pinia Plugin？

**決定**: 不使用 Plugin  
**原因**:
- 位置服務不是全域狀態
- 不需要持久化
- Composable 更輕量
- 避免過度設計

### 為什麼預設不啟用 Retry？

**決定**: 預設關閉  
**原因**:
- 避免過度重試消耗電量
- 使用者可能已拒絕權限
- 讓呼叫方決定是否重試
- 更明確的錯誤處理

---

## 參考資料

- [MDN: Geolocation API](https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API)
- [Vue 3 Composition API](https://vuejs.org/guide/extras/composition-api-faq.html)
- [WP-11-11.5 Completion Report](./WP-11-11.5_COMPLETION_REPORT.md)
- [locationAdapter.js](../frontend/src/utils/locationAdapter.js)

---

**版本歷史**:
- v1.0 (2026-03-08): 初始版本
