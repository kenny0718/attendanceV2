# Attendance Location Frontend Refactor Plan

**版本**: 1.0  
**日期**: 2026-03-08  
**狀態**: 設計中  
**票號**: WP-11-12

---

## 執行摘要

本文件定義從 `locationAdapter` 遷移到 `useLocation` composable 的詳細計劃，包括職責劃分、遷移步驟、測試策略和回滾方案。

---

## 當前架構分析

### 現有實作

```
frontend/src/
├── utils/
│   └── locationAdapter.js (128 行)
│       ├── detectDeviceType()
│       ├── getGPSLocation()
│       ├── getLocationIfRequired()
│       ├── LocationError
│       └── LocationErrorCode
├── stores/
│   └── attendance.js (402 行)
│       └── outCheckpointSubmit() - 使用 locationAdapter
└── views/
    └── Home.vue (566 行)
        └── onMounted() - 使用 detectDeviceType()
```

### 依賴關係

```
Home.vue
  └─> detectDeviceType (from locationAdapter)

attendance.js (store)
  ├─> detectDeviceType (from locationAdapter)
  ├─> getLocationIfRequired (from locationAdapter)
  └─> LocationError (from locationAdapter)
```

### 問題分析

1. **locationAdapter 是臨時方案**
   - 標記為 @deprecated
   - 功能完整但不是長期方案
   - 缺乏 reactive state

2. **職責不清晰**
   - Store 直接呼叫 util 函式
   - View 也直接呼叫 util 函式
   - 沒有統一的狀態管理

3. **測試困難**
   - 難以 mock util 函式
   - 沒有 reactive state 可觀察
   - 錯誤處理分散

---

## 目標架構

### 新架構

```
frontend/src/
├── composables/
│   └── useLocation.js (新增)
│       ├── useLocation() composable
│       ├── LocationError class
│       └── LocationErrorCode enum
├── stores/
│   └── attendance.js (修改)
│       └── outCheckpointSubmit() - 使用 useLocation
└── views/
    └── Home.vue (修改)
        └── setup() - 使用 useLocation
```

### 職責劃分

#### Composable (useLocation.js)
**職責**:
- 裝置類型判斷
- GPS 定位獲取
- 錯誤處理
- Loading 狀態管理
- Retry 機制
- 權限狀態追蹤

**不負責**:
- 業務邏輯
- API 呼叫
- UI 渲染
- 資料持久化

#### Store (attendance.js)
**職責**:
- 業務邏輯（OUT checkpoint 提交）
- API 呼叫
- 業務狀態管理
- 業務錯誤處理

**不負責**:
- GPS 定位獲取（委託給 useLocation）
- 裝置類型判斷（委託給 useLocation）
- GPS 錯誤處理（委託給 useLocation）

#### View (Home.vue)
**職責**:
- UI 渲染
- 使用者互動
- 呼叫 store actions
- 顯示 loading/error 狀態

**不負責**:
- GPS 定位獲取（委託給 composable）
- 業務邏輯（委託給 store）
- API 呼叫（委託給 store）

---

## 遷移策略

### 階段 1: 建立 useLocation（1 天）

**目標**: 實作 useLocation composable

**步驟**:
1. 建立 `frontend/src/composables/useLocation.js`
2. 實作核心功能
3. 撰寫單元測試
4. 撰寫使用文件

**交付物**:
- ✅ useLocation.js
- ✅ useLocation.test.js
- ✅ 使用範例

**驗證**:
- 單元測試通過
- 功能與 locationAdapter 一致
- API 符合規格

---

### 階段 2: 遷移 Store（0.5 天）

**目標**: 更新 attendance.js 使用 useLocation

**修改檔案**: `frontend/src/stores/attendance.js`

#### 修改前

```javascript
import { getLocationIfRequired, detectDeviceType, LocationError } from '@/utils/locationAdapter'

export const useAttendanceStore = defineStore('attendance', {
  actions: {
    async outCheckpointSubmit(reasonText) {
      const deviceType = detectDeviceType()
      
      const payload = {
        device_type: deviceType,
        notes: reasonText.trim()
      }
      
      const gpsData = await getLocationIfRequired()
      if (gpsData) {
        payload.gps = gpsData
      }
      
      const response = await attendanceApi.createOutCheckpoint(payload)
      return { success: true, data: response }
    },
    
    handleError(error) {
      if (error instanceof LocationError) {
        return {
          message: error.message,
          code: error.code,
          originalError: error.originalError
        }
      }
      // ...
    }
  }
})
```

#### 修改後

```javascript
import { useLocation } from '@/composables/useLocation'
import { LocationError } from '@/composables/useLocation'

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
      
      const response = await attendanceApi.createOutCheckpoint(payload)
      return { success: true, data: response }
    },
    
    handleError(error) {
      if (error instanceof LocationError) {
        return {
          message: error.message,
          code: error.code,
          originalError: error.originalError
        }
      }
      // ...
    }
  }
})
```

**變更摘要**:
- Import 從 `@/utils/locationAdapter` 改為 `@/composables/useLocation`
- 使用 `useLocation()` 取得 composable 實例
- `deviceType` 改為 `deviceType.value`（reactive ref）
- 其他邏輯保持不變

**驗證**:
- ESLint 通過
- 單元測試通過
- OUT checkpoint 功能正常

---

### 階段 3: 遷移 View（0.5 天）

**目標**: 更新 Home.vue 使用 useLocation

**修改檔案**: `frontend/src/views/Home.vue`

#### 修改前

```javascript
import { detectDeviceType } from '@/utils/locationAdapter'

const deviceType = ref('pc')

onMounted(() => {
  // ...
  deviceType.value = detectDeviceType()
  // ...
})
```

#### 修改後

```javascript
import { useLocation } from '@/composables/useLocation'

const { deviceType } = useLocation()

onMounted(() => {
  // ...
  // deviceType 已經是 reactive，不需要手動設定
  // ...
})
```

**變更摘要**:
- Import 從 `@/utils/locationAdapter` 改為 `@/composables/useLocation`
- 使用 `useLocation()` 取得 composable 實例
- `deviceType` 已經是 reactive ref，不需要手動設定
- 移除 `detectDeviceType()` 呼叫

**額外改進**:
可選擇性顯示 loading 和 error 狀態

```javascript
const { deviceType, isLoading, error } = useLocation()

// 在 template 中
<div v-if="isLoading">偵測裝置中...</div>
<div v-if="error">{{ error.message }}</div>
```

**驗證**:
- ESLint 通過
- UI 正常顯示
- 裝置類型判斷正確

---

### 階段 4: 清理 locationAdapter（0.5 天）

**目標**: 移除臨時 adapter

**步驟**:
1. 確認沒有其他檔案引用 locationAdapter
2. 刪除 `frontend/src/utils/locationAdapter.js`
3. 更新 `frontend/src/utils/README.md`
4. 更新相關文件

**驗證命令**:
```bash
# 檢查是否還有引用
grep -r "from '@/utils/locationAdapter'" frontend/src
grep -r "locationAdapter" frontend/src

# 應該沒有結果
```

**交付物**:
- ❌ 刪除 locationAdapter.js
- ✅ 更新 utils/README.md
- ✅ 更新 GATE_PROGRESS_TRACKER.md

---

### 階段 5: 測試與驗證（0.5 天）

**目標**: 完整測試新實作

**測試清單**:

#### 單元測試
- [ ] useLocation composable 測試
- [ ] Store actions 測試
- [ ] Error handling 測試

#### 整合測試
- [ ] Store + useLocation 整合
- [ ] View + useLocation 整合
- [ ] API 呼叫整合

#### 手動測試
- [ ] Mobile 裝置 GPS 必填
- [ ] PC 裝置 GPS 選填
- [ ] 權限拒絕處理
- [ ] 超時處理
- [ ] Retry 機制
- [ ] Loading 狀態顯示
- [ ] Error 訊息顯示

#### 回歸測試
- [ ] OUT checkpoint 提交
- [ ] 外出打卡
- [ ] 返回打卡
- [ ] 歷史記錄顯示

---

## 向後相容保證

### API Contract 不變

**Payload 格式**:
```javascript
// 保持不變
{
  device_type: 'mobile' | 'pc',
  notes: string,
  gps?: {
    latitude: number,
    longitude: number,
    accuracy: number,
    captured_at: string,
    provider: 'gps'
  }
}
```

**錯誤碼**:
```javascript
// 保持不變
LocationErrorCode {
  NOT_SUPPORTED = 'NOT_SUPPORTED',
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  POSITION_UNAVAILABLE = 'POSITION_UNAVAILABLE',
  TIMEOUT = 'TIMEOUT',
  UNKNOWN = 'UNKNOWN'
}
```

**錯誤訊息**:
```javascript
// 保持不變
PERMISSION_DENIED: '請開啟定位權限後再外出打點'
POSITION_UNAVAILABLE: '定位資訊無法取得'
TIMEOUT: '定位請求逾時'
NOT_SUPPORTED: '此裝置不支援定位功能'
```

### 行為一致性

| 功能 | locationAdapter | useLocation | 一致性 |
|------|----------------|-------------|--------|
| 裝置判斷 | detectDeviceType() | deviceType.value | ✅ |
| GPS 獲取 | getGPSLocation() | getCurrentLocation() | ✅ |
| 自動判斷 | getLocationIfRequired() | getLocationIfRequired() | ✅ |
| 錯誤處理 | LocationError | LocationError | ✅ |
| 錯誤碼 | LocationErrorCode | LocationErrorCode | ✅ |

---

## 測試策略

### 單元測試

**useLocation.test.js**:
```javascript
import { describe, it, expect, vi } from 'vitest'
import { useLocation } from '@/composables/useLocation'

describe('useLocation', () => {
  it('should initialize with correct default values', () => {
    const { location, error, isLoading, isSupported } = useLocation()
    
    expect(location.value).toBeNull()
    expect(error.value).toBeNull()
    expect(isLoading.value).toBe(false)
    expect(isSupported.value).toBe(true)
  })
  
  it('should detect device type', () => {
    const { deviceType } = useLocation()
    expect(['mobile', 'pc']).toContain(deviceType.value)
  })
  
  it('should get current location', async () => {
    // Mock navigator.geolocation
    global.navigator.geolocation = {
      getCurrentPosition: vi.fn((success) => {
        success({
          coords: {
            latitude: 25.0330,
            longitude: 121.5654,
            accuracy: 10
          }
        })
      })
    }
    
    const { getCurrentLocation, location } = useLocation()
    await getCurrentLocation()
    
    expect(location.value).toMatchObject({
      latitude: 25.0330,
      longitude: 121.5654,
      accuracy: 10
    })
  })
  
  it('should handle permission denied', async () => {
    global.navigator.geolocation = {
      getCurrentPosition: vi.fn((_, error) => {
        error({ code: 1, message: 'Permission denied' })
      })
    }
    
    const { getCurrentLocation, error } = useLocation()
    
    await expect(getCurrentLocation()).rejects.toThrow()
    expect(error.value?.code).toBe('PERMISSION_DENIED')
  })
})
```

### 整合測試

**attendance.store.test.js**:
```javascript
import { describe, it, expect, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAttendanceStore } from '@/stores/attendance'

describe('attendance store with useLocation', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })
  
  it('should submit OUT checkpoint with GPS on mobile', async () => {
    // Mock useLocation
    vi.mock('@/composables/useLocation', () => ({
      useLocation: () => ({
        deviceType: { value: 'mobile' },
        getLocationIfRequired: vi.fn().mockResolvedValue({
          latitude: 25.0330,
          longitude: 121.5654,
          accuracy: 10,
          captured_at: '2026-03-08T10:00:00Z',
          provider: 'gps'
        })
      })
    }))
    
    const store = useAttendanceStore()
    const result = await store.outCheckpointSubmit('外出洽公')
    
    expect(result.success).toBe(true)
  })
})
```

---

## 風險與緩解

### 風險 1: 破壞現有功能

**風險等級**: 高  
**影響**: OUT checkpoint 功能中斷

**緩解措施**:
- 完整的單元測試
- 完整的整合測試
- 在測試環境先驗證
- 保留 locationAdapter 直到確認無問題
- 準備回滾計劃

### 風險 2: 效能問題

**風險等級**: 低  
**影響**: 定位速度變慢

**緩解措施**:
- 效能測試
- 快取機制
- 監控定位時間
- 優化 retry 邏輯

### 風險 3: 相容性問題

**風險等級**: 中  
**影響**: 特定裝置或瀏覽器無法使用

**緩解措施**:
- 瀏覽器相容性測試
- Polyfill 支援
- Graceful degradation
- 錯誤監控

---

## 回滾計劃

### 回滾觸發條件

- 關鍵功能中斷
- 嚴重效能問題
- 大量使用者回報問題
- 測試失敗率 > 10%

### 回滾步驟

1. **立即回滾**:
   ```bash
   git revert <commit-hash>
   git push
   ```

2. **恢復 locationAdapter**:
   ```bash
   git checkout <previous-commit> -- frontend/src/utils/locationAdapter.js
   ```

3. **恢復 Store**:
   ```bash
   git checkout <previous-commit> -- frontend/src/stores/attendance.js
   ```

4. **恢復 View**:
   ```bash
   git checkout <previous-commit> -- frontend/src/views/Home.vue
   ```

5. **驗證**:
   - 執行測試
   - 手動驗證功能
   - 監控錯誤日誌

### 回滾後行動

- 分析失敗原因
- 修復問題
- 補充測試
- 重新部署

---

## 時程規劃

| 階段 | 工作 | 預計時間 | 負責人 |
|------|------|---------|--------|
| 1 | 建立 useLocation | 1 天 | - |
| 2 | 遷移 Store | 0.5 天 | - |
| 3 | 遷移 View | 0.5 天 | - |
| 4 | 清理 locationAdapter | 0.5 天 | - |
| 5 | 測試與驗證 | 0.5 天 | - |
| **總計** | | **3 天** | |

---

## 成功指標

### 功能指標

- ✅ OUT checkpoint 功能正常
- ✅ Mobile GPS 必填驗證正常
- ✅ PC GPS 選填正常
- ✅ 錯誤訊息正確顯示
- ✅ Loading 狀態正確顯示

### 程式碼指標

- ✅ 單元測試覆蓋率 > 80%
- ✅ 整合測試通過
- ✅ ESLint 無錯誤
- ✅ 無 console 錯誤

### 效能指標

- ✅ 定位時間 < 5 秒
- ✅ 記憶體使用 < 1MB
- ✅ 無記憶體洩漏

---

## 參考資料

- [ATTENDANCE_LOCATION_MODULE_SPEC.md](./ATTENDANCE_LOCATION_MODULE_SPEC.md)
- [WP-11-11.5_COMPLETION_REPORT.md](./WP-11-11.5_COMPLETION_REPORT.md)
- [locationAdapter.js](../frontend/src/utils/locationAdapter.js)

---

**版本歷史**:
- v1.0 (2026-03-08): 初始版本
