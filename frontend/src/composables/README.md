# Composables

Vue 3 Composition API 可重用邏輯模組。

---

## 目錄

- [useLocation](#uselocation) - Location 服務

---

## useLocation

統一的 location 服務，提供裝置類型判斷、GPS 定位獲取、錯誤處理等功能。

### 基本使用

```javascript
import { useLocation } from '@/composables/useLocation'

export default {
  setup() {
    const {
      location,
      error,
      isLoading,
      deviceType,
      isGPSRequired,
      getCurrentLocation,
      getLocationIfRequired
    } = useLocation()
    
    return {
      location,
      error,
      isLoading,
      deviceType,
      isGPSRequired,
      getCurrentLocation,
      getLocationIfRequired
    }
  }
}
```

### API

#### State

| 屬性 | 類型 | 說明 |
|------|------|------|
| `location` | `Ref<LocationData \| null>` | 當前位置資料 |
| `error` | `Ref<LocationError \| null>` | 錯誤資訊 |
| `isLoading` | `Ref<boolean>` | Loading 狀態 |
| `deviceType` | `Ref<'mobile' \| 'pc'>` | 裝置類型 |

#### Computed

| 屬性 | 類型 | 說明 |
|------|------|------|
| `isGPSRequired` | `ComputedRef<boolean>` | 是否需要 GPS（Mobile 需要） |

#### Methods

| 方法 | 參數 | 返回值 | 說明 |
|------|------|--------|------|
| `getCurrentLocation()` | - | `Promise<LocationData>` | 獲取當前位置 |
| `getLocationIfRequired()` | - | `Promise<LocationData \| null>` | 條件式獲取定位 |
| `clearError()` | - | `void` | 清除錯誤 |
| `reset()` | - | `void` | 重置所有狀態 |

### 使用範例

#### 範例 1: 外出打卡

```javascript
import { useLocation } from '@/composables/useLocation'

export default {
  setup() {
    const {
      isLoading,
      error,
      deviceType,
      getLocationIfRequired
    } = useLocation()
    
    async function handleBreakOut() {
      try {
        // 自動判斷是否需要 GPS
        const gps = await getLocationIfRequired()
        
        const payload = {
          device_type: deviceType.value,
          notes: '外出洽公'
        }
        
        if (gps) {
          payload.gps = gps
        }
        
        await api.breakOut(payload)
      } catch (err) {
        console.error(err.message)
      }
    }
    
    return {
      isLoading,
      error,
      handleBreakOut
    }
  }
}
```

#### 範例 2: 顯示 Loading 和錯誤

```vue
<template>
  <div>
    <button 
      @click="handleSubmit"
      :disabled="isLoading"
    >
      {{ isLoading ? '定位中...' : '外出打卡' }}
    </button>
    
    <div v-if="error" class="error">
      {{ error.message }}
    </div>
  </div>
</template>

<script setup>
import { useLocation } from '@/composables/useLocation'

const {
  isLoading,
  error,
  getLocationIfRequired
} = useLocation()

async function handleSubmit() {
  try {
    const gps = await getLocationIfRequired()
    // ... 提交邏輯
  } catch (err) {
    // error 已自動設定
  }
}
</script>
```

#### 範例 3: 手動獲取定位

```javascript
import { useLocation } from '@/composables/useLocation'

const {
  location,
  isLoading,
  getCurrentLocation
} = useLocation()

// 手動獲取定位
async function getLocation() {
  try {
    const loc = await getCurrentLocation()
    console.log('緯度:', loc.latitude)
    console.log('經度:', loc.longitude)
    console.log('精度:', loc.accuracy)
  } catch (err) {
    console.error('定位失敗:', err.message)
  }
}
```

### 資料結構

#### LocationData

```typescript
interface LocationData {
  latitude: number        // 緯度
  longitude: number       // 經度
  accuracy: number        // 精度（公尺）
  captured_at: string     // 捕獲時間（ISO 8601）
  provider: 'gps'         // 定位提供者
}
```

#### LocationError

```typescript
interface LocationError {
  code: string            // 錯誤碼
  message: string         // 錯誤訊息
  originalError?: Error   // 原始錯誤物件
}
```

#### LocationErrorCode

```typescript
const LocationErrorCode = {
  NOT_SUPPORTED: 'NOT_SUPPORTED',           // 瀏覽器不支援
  PERMISSION_DENIED: 'PERMISSION_DENIED',   // 使用者拒絕權限
  POSITION_UNAVAILABLE: 'POSITION_UNAVAILABLE', // 定位資訊無法取得
  TIMEOUT: 'TIMEOUT',                       // 超時
  UNKNOWN: 'UNKNOWN'                        // 未知錯誤
}
```

### 選項

```javascript
const {
  // ...
} = useLocation({
  enableHighAccuracy: true,  // 是否使用高精度（預設 true）
  timeout: 10000,            // 超時時間（預設 10000ms）
  maximumAge: 0              // 快取時間（預設 0ms）
})
```

### 注意事項

1. **權限處理**: 首次使用時瀏覽器會請求定位權限
2. **HTTPS 要求**: 定位功能需要在 HTTPS 環境下使用
3. **裝置支援**: 並非所有裝置都支援定位功能
4. **精度**: 室內定位精度可能較低

### 錯誤處理

```javascript
try {
  const location = await getCurrentLocation()
} catch (err) {
  switch (err.code) {
    case LocationErrorCode.NOT_SUPPORTED:
      // 瀏覽器不支援
      break
    case LocationErrorCode.PERMISSION_DENIED:
      // 使用者拒絕權限
      break
    case LocationErrorCode.TIMEOUT:
      // 超時
      break
    default:
      // 其他錯誤
  }
}
```

---

## 開發指南

### 新增 Composable

1. 在 `composables/` 目錄下建立新檔案
2. 使用 `use` 前綴命名（例如：`useAuth.js`）
3. 遵循 Vue 3 Composition API 規範
4. 提供完整的 JSDoc 註解
5. 更新本 README

### 測試

```bash
# 執行測試
npm run test:unit -- composables/useLocation.spec.js
```

---

**最後更新**: 2026-03-08  
**版本**: 1.0.0
