# Utils 目錄說明

本目錄包含前端共用的工具函式。

---

## locationAdapter.js

**狀態**: ⚠️ 臨時過渡層 (Temporary Adapter)

這是在實作 shared location module 之前的臨時方案。

### 目的

在 `composables/useLocation.js` 完成前，提供統一的定位介面，避免前端程式碼直接依賴 `navigator.geolocation`。

### 使用方式

```javascript
import { 
  getGPSLocation, 
  detectDeviceType, 
  getLocationIfRequired,
  LocationError,
  LocationErrorCode
} from '@/utils/locationAdapter'

// 1. 獲取裝置類型
const deviceType = detectDeviceType() // 'mobile' | 'pc'

// 2. 獲取 GPS 定位
try {
  const gps = await getGPSLocation()
  console.log(gps.latitude, gps.longitude)
} catch (error) {
  if (error instanceof LocationError) {
    console.error(error.message, error.code)
  }
}

// 3. 根據裝置類型自動決定是否獲取定位
const gps = await getLocationIfRequired() 
// mobile: 返回 GPS data
// pc: 返回 null
```

### API 說明

#### `detectDeviceType(): 'mobile' | 'pc'`

偵測當前裝置類型。

**返回值**:
- `'mobile'`: 行動裝置（手機、平板）
- `'pc'`: 桌面裝置

**實作方式**: 檢查 User Agent

---

#### `getGPSLocation(options?): Promise<GPSData>`

獲取 GPS 定位。

**參數**:
- `options` (可選): 定位選項
  - `enableHighAccuracy`: 是否使用高精度（預設: true）
  - `timeout`: 超時時間（預設: 10000ms）
  - `maximumAge`: 快取時間（預設: 0）

**返回值**:
```javascript
{
  latitude: number,      // 緯度
  longitude: number,     // 經度
  accuracy: number,      // 精度（公尺）
  captured_at: string,   // 擷取時間（ISO 8601）
  provider: 'gps'        // 提供者
}
```

**錯誤**:
- 拋出 `LocationError`

---

#### `getLocationIfRequired(): Promise<GPSData | null>`

根據裝置類型自動決定是否獲取定位。

**返回值**:
- Mobile: 返回 GPS data
- PC: 返回 null

**錯誤**:
- Mobile 裝置會拋出 `LocationError`（如果定位失敗）

---

#### `isGPSRequired(): boolean`

檢查當前裝置是否需要 GPS。

**返回值**:
- `true`: Mobile 裝置，需要 GPS
- `false`: PC 裝置，不需要 GPS

---

### 錯誤處理

#### `LocationError`

統一的定位錯誤類型。

**屬性**:
- `message`: 錯誤訊息（中文）
- `code`: 錯誤碼（LocationErrorCode）
- `originalError`: 原始錯誤物件

**範例**:
```javascript
try {
  const gps = await getGPSLocation()
} catch (error) {
  if (error instanceof LocationError) {
    switch (error.code) {
      case LocationErrorCode.PERMISSION_DENIED:
        // 使用者拒絕定位權限
        break
      case LocationErrorCode.POSITION_UNAVAILABLE:
        // 定位資訊無法取得
        break
      case LocationErrorCode.TIMEOUT:
        // 定位請求逾時
        break
      case LocationErrorCode.NOT_SUPPORTED:
        // 裝置不支援定位
        break
    }
  }
}
```

#### `LocationErrorCode`

錯誤碼常數。

```javascript
{
  NOT_SUPPORTED: 'NOT_SUPPORTED',           // 裝置不支援定位
  PERMISSION_DENIED: 'PERMISSION_DENIED',   // 使用者拒絕權限
  POSITION_UNAVAILABLE: 'POSITION_UNAVAILABLE', // 定位無法取得
  TIMEOUT: 'TIMEOUT',                       // 請求逾時
  UNKNOWN: 'UNKNOWN'                        // 未知錯誤
}
```

---

### 使用範例

#### 範例 1: 在 Store 中使用

```javascript
import { getLocationIfRequired, detectDeviceType } from '@/utils/locationAdapter'

export const useAttendanceStore = defineStore('attendance', {
  actions: {
    async submitCheckpoint(reason) {
      const deviceType = detectDeviceType()
      
      const payload = {
        device_type: deviceType,
        notes: reason
      }
      
      // 自動判斷是否需要 GPS
      const gps = await getLocationIfRequired()
      if (gps) {
        payload.gps = gps
      }
      
      return await api.createCheckpoint(payload)
    }
  }
})
```

#### 範例 2: 在 Component 中使用

```vue
<script setup>
import { ref } from 'vue'
import { detectDeviceType, getGPSLocation, LocationError } from '@/utils/locationAdapter'

const deviceType = ref('pc')
const gpsData = ref(null)
const error = ref(null)

const checkDevice = () => {
  deviceType.value = detectDeviceType()
}

const getLocation = async () => {
  try {
    gpsData.value = await getGPSLocation()
    error.value = null
  } catch (err) {
    if (err instanceof LocationError) {
      error.value = err.message
    }
  }
}
</script>
```

---

### 未來計劃

此 adapter 將在 `composables/useLocation.js` 完成後被取代。

**預計時程**: WP-11-12 (Shared Location Module)

**遷移計劃**:
1. 實作 `useLocation` composable
2. 替換所有 `locationAdapter` 引用
3. 刪除 `locationAdapter.js`

**相關文件**:
- `docs/ATTENDANCE_GPS_LEGACY_CLEANUP_PLAN.md`
- `docs/ATTENDANCE_LOCATION_MODULE_SPEC.md` (待建立)

---

## 其他工具（未來擴充）

本目錄未來可能包含：
- `dateUtils.js`: 日期時間工具
- `formatUtils.js`: 格式化工具
- `validationUtils.js`: 驗證工具
- `storageUtils.js`: LocalStorage 工具

---

**最後更新**: 2026-03-08
