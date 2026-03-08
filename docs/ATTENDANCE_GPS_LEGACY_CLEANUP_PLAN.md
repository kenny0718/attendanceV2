# Attendance GPS Legacy Cleanup Plan

**建立日期**: 2026-03-08  
**基於**: ATTENDANCE_GPS_LEGACY_INVENTORY.md  
**目標**: 安全移除舊 GPS 流程，為 shared location module 做準備

---

## 執行原則

1. **漸進式重構**: 不一次性刪除所有舊程式碼
2. **保持功能可用**: 清理過程中 OUT checkpoint 功能必須持續可用
3. **先建立 adapter**: 避免直接讓主流程壞掉
4. **測試先行**: 每個步驟都要確保測試通過
5. **文件同步**: 更新相關文件

---

## Cleanup 優先級

### P0 - 立即處理（本輪）
- 刪除備份檔案（死碼）
- 移除前端 store 中的 GPS 方法
- 建立臨時 adapter 層
- 統一錯誤訊息

### P1 - 下一輪處理
- 實作 shared location module
- 替換 adapter 為正式實作
- 更新測試案例

### P2 - 未來優化
- 統一錯誤碼命名
- 優化裝置判斷邏輯
- 增強 GPS 精度驗證

---

## 詳細清理計劃

## 階段 1: 刪除死碼與備份檔案

### 1.1 刪除前端備份檔案

**目標**: 移除混淆的備份檔案

| 檔案 | 動作 | 風險 |
|------|------|------|
| `frontend/src/views/Home.vue.tmp` | **REMOVE** | 低 |
| `frontend/src/views/Home.vue.before_fix` | **REMOVE** | 低 |
| `frontend/src/views/Home.vue.backup` | **REMOVE** | 低 |

**執行步驟**:
```bash
cd /opt/attendance-system/frontend/src/views
rm -f Home.vue.tmp Home.vue.before_fix Home.vue.backup
```

**驗證**:
- 確認 `Home.vue` 是最新版本
- 執行前端測試確保功能正常

---

## 階段 2: 建立臨時 Location Adapter

### 2.1 建立 Location Utils

**目標**: 將 GPS 邏輯從 store 抽離到獨立的 util

**新增檔案**: `frontend/src/utils/locationAdapter.js`

```javascript
/**
 * Location Adapter (臨時過渡層)
 * 
 * 目的: 在 shared location module 完成前，提供統一的定位介面
 * 注意: 這是臨時方案，未來會被 useLocation composable 取代
 * 
 * @deprecated 將在 shared location module 完成後移除
 */

/**
 * 獲取裝置類型
 * @returns {'mobile' | 'pc'}
 */
export function detectDeviceType() {
  const userAgent = navigator.userAgent || ''
  const isMobile = /Mobile|Android|iPhone|iPad|iPod/i.test(userAgent)
  return isMobile ? 'mobile' : 'pc'
}

/**
 * GPS 錯誤類型
 */
export class LocationError extends Error {
  constructor(message, code, originalError = null) {
    super(message)
    this.name = 'LocationError'
    this.code = code
    this.originalError = originalError
  }
}

/**
 * GPS 錯誤碼
 */
export const LocationErrorCode = {
  NOT_SUPPORTED: 'NOT_SUPPORTED',
  PERMISSION_DENIED: 'PERMISSION_DENIED',
  POSITION_UNAVAILABLE: 'POSITION_UNAVAILABLE',
  TIMEOUT: 'TIMEOUT',
  UNKNOWN: 'UNKNOWN'
}

/**
 * 獲取 GPS 定位
 * @param {Object} options - 定位選項
 * @returns {Promise<Object>} GPS 資料
 * @throws {LocationError}
 */
export async function getGPSLocation(options = {}) {
  const defaultOptions = {
    enableHighAccuracy: true,
    timeout: 10000,
    maximumAge: 0,
    ...options
  }

  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new LocationError(
        '此裝置不支援定位功能',
        LocationErrorCode.NOT_SUPPORTED
      ))
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          captured_at: new Date().toISOString(),
          provider: 'gps'
        })
      },
      (error) => {
        const locationError = mapGeolocationError(error)
        reject(locationError)
      },
      defaultOptions
    )
  })
}

/**
 * 將瀏覽器 GeolocationPositionError 轉換為 LocationError
 * @private
 */
function mapGeolocationError(error) {
  let message = '無法獲取定位'
  let code = LocationErrorCode.UNKNOWN

  switch (error.code) {
    case error.PERMISSION_DENIED:
      message = '請開啟定位權限後再外出打點'
      code = LocationErrorCode.PERMISSION_DENIED
      break
    case error.POSITION_UNAVAILABLE:
      message = '定位資訊無法取得'
      code = LocationErrorCode.POSITION_UNAVAILABLE
      break
    case error.TIMEOUT:
      message = '定位請求逾時'
      code = LocationErrorCode.TIMEOUT
      break
  }

  return new LocationError(message, code, error)
}

/**
 * 檢查是否需要 GPS（根據裝置類型）
 * @returns {boolean}
 */
export function isGPSRequired() {
  return detectDeviceType() === 'mobile'
}

/**
 * 獲取定位（如果需要）
 * @returns {Promise<Object|null>} GPS 資料或 null
 */
export async function getLocationIfRequired() {
  if (isGPSRequired()) {
    return await getGPSLocation()
  }
  return null
}
```

**標記**: `REFACTOR` - 臨時 adapter，未來會被取代

---

### 2.2 更新 Attendance Store

**目標**: 移除 store 中的 GPS 方法，改用 adapter

**檔案**: `frontend/src/stores/attendance.js`

**變更清單**:

| 方法/程式碼 | 動作 | 替代方案 |
|------------|------|----------|
| `getGPSLocation()` | **REMOVE** | 使用 `locationAdapter.getGPSLocation()` |
| `detectDeviceType()` | **REMOVE** | 使用 `locationAdapter.detectDeviceType()` |
| `outCheckpointSubmit()` 中的 GPS 邏輯 | **REFACTOR** | 使用 `locationAdapter.getLocationIfRequired()` |
| `handleError()` 中的 GPS 錯誤處理 | **REFACTOR** | 使用 `LocationError` |

**重構後的 `outCheckpointSubmit()`**:
```javascript
import { getLocationIfRequired, detectDeviceType, LocationError } from '@/utils/locationAdapter'

async outCheckpointSubmit(reasonText) {
  if (this.outCheckpointLoading) {
    console.warn('操作進行中，請稍候...')
    return
  }
  
  if (!reasonText || reasonText.trim() === '') {
    throw new Error('請先選擇原因')
  }
  
  this.outCheckpointLoading = true
  this.outCheckpointError = null
  
  try {
    const deviceType = detectDeviceType()
    
    const payload = {
      device_type: deviceType,
      notes: reasonText.trim()
    }
    
    // 使用 adapter 獲取定位（如果需要）
    const gpsData = await getLocationIfRequired()
    if (gpsData) {
      payload.gps = gpsData
    }
    
    const response = await attendanceApi.createOutCheckpoint(payload)
    
    this.lastSelectedReason = reasonText
    localStorage.setItem('lastSelectedReason', reasonText)
    
    await this.loadOutCheckpoints()
    
    return { success: true, data: response }
  } catch (error) {
    // LocationError 會有更清楚的錯誤訊息
    this.outCheckpointError = this.handleError(error)
    
    try {
      await this.loadOutCheckpoints()
    } catch (refreshError) {
      console.error('刷新列表失敗:', refreshError)
    }
    
    throw this.outCheckpointError
  } finally {
    this.outCheckpointLoading = false
  }
}
```

**標記**: `REFACTOR` - 使用臨時 adapter

---

### 2.3 更新 Home.vue

**目標**: 移除頁面對 store GPS 方法的直接依賴

**檔案**: `frontend/src/views/Home.vue`

**變更清單**:

```javascript
// 移除
// deviceType.value = attendanceStore.detectDeviceType()

// 改為
import { detectDeviceType } from '@/utils/locationAdapter'

onMounted(() => {
  attendanceStore.fetchTodayStatus()
  attendanceStore.fetchRecentLogs()
  attendanceStore.loadOutCheckpoints()
  attendanceStore.loadBreakPunches()
  attendanceStore.hydrateReasonsFromLocalStorage()
  
  // 使用 adapter
  deviceType.value = detectDeviceType()
  
  if (lastSelectedReason.value) {
    selectedReason.value = lastSelectedReason.value
  }
})
```

**標記**: `REFACTOR` - 使用臨時 adapter

---

## 階段 3: 統一錯誤處理

### 3.1 更新 Store 錯誤處理

**目標**: 讓 `handleError()` 能正確處理 `LocationError`

**檔案**: `frontend/src/stores/attendance.js`

**變更**: 在 `handleError()` 方法開頭加入 LocationError 處理

```javascript
import { LocationError } from '@/utils/locationAdapter'

handleError(error) {
  let errorMessage = '操作失敗'
  let errorCode = null
  
  // 處理 LocationError
  if (error instanceof LocationError) {
    return {
      message: error.message,
      code: error.code,
      originalError: error.originalError
    }
  }
  
  // 原有的錯誤處理邏輯...
  if (error.status) {
    // ...
  }
  
  return {
    message: errorMessage,
    code: errorCode,
    originalError: error
  }
}
```

**標記**: `REFACTOR` - 統一錯誤處理

---

## 階段 4: 清理測試

### 4.1 前端測試更新

**目標**: 如果有測試直接依賴舊 GPS 方法，需要更新

**檢查項目**:
- 是否有測試直接呼叫 `attendanceStore.getGPSLocation()`
- 是否有測試直接呼叫 `attendanceStore.detectDeviceType()`

**處理方式**:
- 如果有，改為測試 `locationAdapter` 的方法
- 或者 mock `locationAdapter`

**標記**: `VERIFY` - 需要檢查是否有相關測試

---

### 4.2 後端測試保持不變

**目標**: 後端測試不需要改動

**原因**:
- 後端 GPS 邏輯沒有改變
- `gps_utils.py` 保持不變
- Schema 驗證邏輯保持不變

**標記**: `KEEP` - 後端測試不動

---

## 階段 5: 文件更新

### 5.1 新增 Adapter 說明文件

**新增檔案**: `frontend/src/utils/README.md`

```markdown
# Utils 目錄說明

## locationAdapter.js

**狀態**: ⚠️ 臨時過渡層 (Temporary Adapter)

這是在實作 shared location module 之前的臨時方案。

### 使用方式

```javascript
import { getGPSLocation, detectDeviceType, getLocationIfRequired } from '@/utils/locationAdapter'

// 獲取裝置類型
const deviceType = detectDeviceType() // 'mobile' | 'pc'

// 獲取 GPS 定位
try {
  const gps = await getGPSLocation()
  console.log(gps.latitude, gps.longitude)
} catch (error) {
  if (error instanceof LocationError) {
    console.error(error.message, error.code)
  }
}

// 根據裝置類型自動決定是否獲取定位
const gps = await getLocationIfRequired() // mobile: GPS data, pc: null
```

### 未來計劃

此 adapter 將在 `composables/useLocation.js` 完成後被取代。

預計時程: WP-11-12 (Shared Location Module)
```

---

### 5.2 更新主要文件

**檔案**: `docs/GATE_PROGRESS_TRACKER.md` (需要建立)

新增以下內容:
```markdown
## WP-11-11.5: GPS Legacy Cleanup (完成)

- ✅ 盤點所有舊 GPS 實作
- ✅ 刪除備份檔案
- ✅ 建立臨時 location adapter
- ✅ 重構 attendance store GPS 邏輯
- ✅ 統一錯誤處理
- ⏳ 待辦: 實作 shared location module (WP-11-12)
```

---

## 驗證清單

完成清理後，必須確認以下項目：

### 功能驗證

- [ ] OUT checkpoint 功能正常運作
- [ ] Mobile 裝置必須提供 GPS
- [ ] PC 裝置可選擇性提供 GPS
- [ ] GPS 錯誤訊息正確顯示
- [ ] 裝置類型判斷正確

### 程式碼品質

- [ ] 沒有 `attendanceStore.getGPSLocation()` 的呼叫
- [ ] 沒有 `attendanceStore.detectDeviceType()` 的呼叫
- [ ] 所有 GPS 邏輯都透過 `locationAdapter`
- [ ] 沒有備份檔案 (*.tmp, *.backup, *.before_fix)
- [ ] ESLint 沒有錯誤

### 測試驗證

- [ ] 前端測試通過
- [ ] 後端測試通過
- [ ] E2E 測試通過 (如果有)

### 文件驗證

- [ ] `ATTENDANCE_GPS_LEGACY_INVENTORY.md` 已建立
- [ ] `ATTENDANCE_GPS_LEGACY_CLEANUP_PLAN.md` 已建立
- [ ] `frontend/src/utils/README.md` 已建立
- [ ] `GATE_PROGRESS_TRACKER.md` 已更新

---

## 回滾計劃

如果清理過程中出現問題，可以按照以下步驟回滾：

### 回滾步驟

1. **Git 回滾**:
   ```bash
   git checkout HEAD -- frontend/src/stores/attendance.js
   git checkout HEAD -- frontend/src/views/Home.vue
   ```

2. **刪除新增的檔案**:
   ```bash
   rm frontend/src/utils/locationAdapter.js
   rm frontend/src/utils/README.md
   ```

3. **驗證功能**:
   - 測試 OUT checkpoint 功能
   - 確認 GPS 定位正常

---

## 風險與緩解措施

### 風險 1: OUT checkpoint 功能中斷

**機率**: 中  
**影響**: 高  
**緩解措施**:
- 在測試環境先完整測試
- 保留 Git commit，可快速回滾
- 分階段部署，先部署到 staging

### 風險 2: GPS 錯誤訊息不一致

**機率**: 低  
**影響**: 中  
**緩解措施**:
- 統一使用 `LocationError`
- 在 adapter 中集中管理錯誤訊息
- 測試所有錯誤情境

### 風險 3: 裝置類型判斷錯誤

**機率**: 低  
**影響**: 中  
**緩解措施**:
- 保持原有的判斷邏輯
- 增加測試案例
- 記錄 user agent 供後續分析

---

## 時程規劃

| 階段 | 預計時間 | 負責人 | 狀態 |
|------|---------|--------|------|
| 階段 1: 刪除死碼 | 0.5 小時 | - | ⏳ 待執行 |
| 階段 2: 建立 adapter | 2 小時 | - | ⏳ 待執行 |
| 階段 3: 統一錯誤處理 | 1 小時 | - | ⏳ 待執行 |
| 階段 4: 清理測試 | 1 小時 | - | ⏳ 待執行 |
| 階段 5: 文件更新 | 0.5 小時 | - | ⏳ 待執行 |
| **總計** | **5 小時** | - | - |

---

## 下一步

完成本次 cleanup 後，下一步是：

1. **WP-11-12**: 實作 Shared Location Module (`composables/useLocation.js`)
2. **WP-11-13**: 替換 locationAdapter 為正式的 useLocation
3. **WP-11-14**: 實作 Location Policy (範圍驗證、精度要求等)
4. **WP-11-15**: 整合地圖 UI

參考文件:
- `ATTENDANCE_LOCATION_MODULE_SPEC.md` (待建立)
- `ATTENDANCE_LOCATION_FRONTEND_REFACTOR_PLAN.md` (待建立)
