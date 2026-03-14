# Attendance Location Test Plan

**版本**: 1.0  
**日期**: 2026-03-08  
**狀態**: 設計中  
**票號**: WP-11-12

---

## 執行摘要

本文件定義 `useLocation` composable 和相關整合的完整測試計劃，包括單元測試、整合測試、E2E 測試和手動測試。

---

## 測試策略

### 測試金字塔

```
        /\
       /  \  E2E Tests (10%)
      /____\
     /      \  Integration Tests (30%)
    /________\
   /          \  Unit Tests (60%)
  /__________\
```

### 測試範圍

| 層級 | 範圍 | 工具 | 覆蓋率目標 |
|------|------|------|-----------|
| 單元測試 | useLocation composable | Vitest | > 80% |
| 整合測試 | Store + useLocation | Vitest | > 70% |
| E2E 測試 | 完整流程 | Playwright | 關鍵路徑 |
| 手動測試 | 真實裝置 | 人工 | 100% |

---

## 單元測試

### useLocation Composable

#### Test Suite 1: 初始化

```javascript
describe('useLocation - Initialization', () => {
  it('should initialize with correct default values', () => {
    const {
      location,
      error,
      isLoading,
      isSupported,
      deviceType,
      permissionState
    } = useLocation()
    
    expect(location.value).toBeNull()
    expect(error.value).toBeNull()
    expect(isLoading.value).toBe(false)
    expect(isSupported.value).toBe(true)
    expect(deviceType.value).toBeOneOf(['mobile', 'pc'])
    expect(permissionState.value).toBe('unknown')
  })
  
  it('should accept custom options', () => {
    const { } = useLocation({
      enableHighAccuracy: false,
      timeout: 5000,
      autoRetry: true,
      maxRetries: 5
    })
    
    // Options should be applied
  })
  
  it('should detect unsupported browser', () => {
    // Mock navigator.geolocation = undefined
    global.navigator.geolocation = undefined
    
    const { isSupported } = useLocation()
    expect(isSupported.value).toBe(false)
  })
})
```

---

#### Test Suite 2: 裝置類型判斷

```javascript
describe('useLocation - Device Detection', () => {
  it('should detect mobile device', () => {
    // Mock mobile user agent
    Object.defineProperty(navigator, 'userAgent', {
      value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
      configurable: true
    })
    
    const { deviceType } = useLocation()
    expect(deviceType.value).toBe('mobile')
  })
  
  it('should detect PC device', () => {
    // Mock PC user agent
    Object.defineProperty(navigator, 'userAgent', {
      value: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
      configurable: true
    })
    
    const { deviceType } = useLocation()
    expect(deviceType.value).toBe('pc')
  })
  
  it('should detect Android device', () => {
    Object.defineProperty(navigator, 'userAgent', {
      value: 'Mozilla/5.0 (Linux; Android 11)',
      configurable: true
    })
    
    const { deviceType } = useLocation()
    expect(deviceType.value).toBe('mobile')
  })
  
  it('should detect iPad as mobile', () => {
    Object.defineProperty(navigator, 'userAgent', {
      value: 'Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)',
      configurable: true
    })
    
    const { deviceType } = useLocation()
    expect(deviceType.value).toBe('mobile')
  })
})
```

---

#### Test Suite 3: GPS 定位獲取

```javascript
describe('useLocation - Get Current Location', () => {
  it('should get current location successfully', async () => {
    // Mock successful geolocation
    global.navigator.geolocation = {
      getCurrentPosition: vi.fn((success) => {
        success({
          coords: {
            latitude: 25.0330,
            longitude: 121.5654,
            accuracy: 10.5
          },
          timestamp: Date.now()
        })
      })
    }
    
    const { getCurrentLocation, location, isLoading } = useLocation()
    
    expect(isLoading.value).toBe(false)
    
    const result = await getCurrentLocation()
    
    expect(result).toMatchObject({
      latitude: 25.0330,
      longitude: 121.5654,
      accuracy: 10.5,
      provider: 'gps'
    })
    expect(result.captured_at).toBeDefined()
    expect(location.value).toEqual(result)
    expect(isLoading.value).toBe(false)
  })
  
  it('should set loading state during request', async () => {
    let resolvePosition
    global.navigator.geolocation = {
      getCurrentPosition: vi.fn((success) => {
        resolvePosition = () => success({
          coords: { latitude: 25.0330, longitude: 121.5654, accuracy: 10 }
        })
      })
    }
    
    const { getCurrentLocation, isLoading } = useLocation()
    
    const promise = getCurrentLocation()
    expect(isLoading.value).toBe(true)
    
    resolvePosition()
    await promise
    
    expect(isLoading.value).toBe(false)
  })
})
```

---

#### Test Suite 4: 錯誤處理

```javascript
describe('useLocation - Error Handling', () => {
  it('should handle permission denied', async () => {
    global.navigator.geolocation = {
      getCurrentPosition: vi.fn((_, error) => {
        error({
          code: 1,
          message: 'User denied Geolocation'
        })
      })
    }
    
    const { getCurrentLocation, error } = useLocation()
    
    await expect(getCurrentLocation()).rejects.toThrow(LocationError)
    expect(error.value?.code).toBe(LocationErrorCode.PERMISSION_DENIED)
    expect(error.value?.message).toBe('請開啟定位權限後再外出打點')
  })
  
  it('should handle position unavailable', async () => {
    global.navigator.geolocation = {
      getCurrentPosition: vi.fn((_, error) => {
        error({ code: 2, message: 'Position unavailable' })
      })
    }
    
    const { getCurrentLocation, error } = useLocation()
    
    await expect(getCurrentLocation()).rejects.toThrow()
    expect(error.value?.code).toBe(LocationErrorCode.POSITION_UNAVAILABLE)
  })
  
  it('should handle timeout', async () => {
    global.navigator.geolocation = {
      getCurrentPosition: vi.fn((_, error) => {
        error({ code: 3, message: 'Timeout' })
      })
    }
    
    const { getCurrentLocation, error } = useLocation()
    
    await expect(getCurrentLocation()).rejects.toThrow()
    expect(error.value?.code).toBe(LocationErrorCode.TIMEOUT)
  })
  
  it('should handle unsupported browser', async () => {
    global.navigator.geolocation = undefined
    
    const { getCurrentLocation, error } = useLocation()
    
    await expect(getCurrentLocation()).rejects.toThrow()
    expect(error.value?.code).toBe(LocationErrorCode.NOT_SUPPORTED)
  })
})
```

---

#### Test Suite 5: Retry 機制

```javascript
describe('useLocation - Retry Mechanism', () => {
  it('should retry on timeout when autoRetry enabled', async () => {
    let callCount = 0
    global.navigator.geolocation = {
      getCurrentPosition: vi.fn((success, error) => {
        callCount++
        if (callCount < 3) {
          error({ code: 3, message: 'Timeout' })
        } else {
          success({
            coords: { latitude: 25.0330, longitude: 121.5654, accuracy: 10 }
          })
        }
      })
    }
    
    const { getCurrentLocation } = useLocation({
      autoRetry: true,
      maxRetries: 3,
      retryDelay: 100
    })
    
    const result = await getCurrentLocation()
    
    expect(callCount).toBe(3)
    expect(result).toBeDefined()
  })
  
  it('should not retry when autoRetry disabled', async () => {
    let callCount = 0
    global.navigator.geolocation = {
      getCurrentPosition: vi.fn((_, error) => {
        callCount++
        error({ code: 3, message: 'Timeout' })
      })
    }
    
    const { getCurrentLocation } = useLocation({
      autoRetry: false
    })
    
    await expect(getCurrentLocation()).rejects.toThrow()
    expect(callCount).toBe(1)
  })
  
  it('should not retry on permission denied', async () => {
    let callCount = 0
    global.navigator.geolocation = {
      getCurrentPosition: vi.fn((_, error) => {
        callCount++
        error({ code: 1, message: 'Permission denied' })
      })
    }
    
    const { getCurrentLocation } = useLocation({
      autoRetry: true,
      maxRetries: 3
    })
    
    await expect(getCurrentLocation()).rejects.toThrow()
    expect(callCount).toBe(1)
  })
})
```

---

#### Test Suite 6: getLocationIfRequired

```javascript
describe('useLocation - Get Location If Required', () => {
  it('should return GPS for mobile device', async () => {
    Object.defineProperty(navigator, 'userAgent', {
      value: 'Mozilla/5.0 (iPhone)',
      configurable: true
    })
    
    global.navigator.geolocation = {
      getCurrentPosition: vi.fn((success) => {
        success({
          coords: { latitude: 25.0330, longitude: 121.5654, accuracy: 10 }
        })
      })
    }
    
    const { getLocationIfRequired } = useLocation()
    const result = await getLocationIfRequired()
    
    expect(result).toBeDefined()
    expect(result.latitude).toBe(25.0330)
  })
  
  it('should return null for PC device', async () => {
    Object.defineProperty(navigator, 'userAgent', {
      value: 'Mozilla/5.0 (Windows NT 10.0)',
      configurable: true
    })
    
    const { getLocationIfRequired } = useLocation()
    const result = await getLocationIfRequired()
    
    expect(result).toBeNull()
  })
})
```

---

#### Test Suite 7: Computed Properties

```javascript
describe('useLocation - Computed Properties', () => {
  it('isGPSRequired should be true for mobile', () => {
    Object.defineProperty(navigator, 'userAgent', {
      value: 'Mozilla/5.0 (iPhone)',
      configurable: true
    })
    
    const { isGPSRequired } = useLocation()
    expect(isGPSRequired.value).toBe(true)
  })
  
  it('isGPSRequired should be false for PC', () => {
    Object.defineProperty(navigator, 'userAgent', {
      value: 'Mozilla/5.0 (Windows NT 10.0)',
      configurable: true
    })
    
    const { isGPSRequired } = useLocation()
    expect(isGPSRequired.value).toBe(false)
  })
  
  it('canRequestLocation should be false when not supported', () => {
    global.navigator.geolocation = undefined
    
    const { canRequestLocation } = useLocation()
    expect(canRequestLocation.value).toBe(false)
  })
})
```

---

## 整合測試

### Store + useLocation

```javascript
describe('Attendance Store with useLocation', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })
  
  it('should submit OUT checkpoint with GPS on mobile', async () => {
    // Mock mobile device
    Object.defineProperty(navigator, 'userAgent', {
      value: 'Mozilla/5.0 (iPhone)',
      configurable: true
    })
    
    // Mock geolocation
    global.navigator.geolocation = {
      getCurrentPosition: vi.fn((success) => {
        success({
          coords: { latitude: 25.0330, longitude: 121.5654, accuracy: 10 }
        })
      })
    }
    
    // Mock API
    vi.mock('@/api/attendance', () => ({
      attendanceApi: {
        createOutCheckpoint: vi.fn().mockResolvedValue({
          checkpoint_id: '123',
          punch_time: '2026-03-08T10:00:00Z'
        })
      }
    }))
    
    const store = useAttendanceStore()
    const result = await store.outCheckpointSubmit('外出洽公')
    
    expect(result.success).toBe(true)
    expect(attendanceApi.createOutCheckpoint).toHaveBeenCalledWith({
      device_type: 'mobile',
      notes: '外出洽公',
      gps: expect.objectContaining({
        latitude: 25.0330,
        longitude: 121.5654
      })
    })
  })
  
  it('should submit OUT checkpoint without GPS on PC', async () => {
    Object.defineProperty(navigator, 'userAgent', {
      value: 'Mozilla/5.0 (Windows NT 10.0)',
      configurable: true
    })
    
    const store = useAttendanceStore()
    const result = await store.outCheckpointSubmit('外出洽公')
    
    expect(result.success).toBe(true)
    expect(attendanceApi.createOutCheckpoint).toHaveBeenCalledWith({
      device_type: 'pc',
      notes: '外出洽公'
    })
  })
  
  it('should handle LocationError in store', async () => {
    Object.defineProperty(navigator, 'userAgent', {
      value: 'Mozilla/5.0 (iPhone)',
      configurable: true
    })
    
    global.navigator.geolocation = {
      getCurrentPosition: vi.fn((_, error) => {
        error({ code: 1, message: 'Permission denied' })
      })
    }
    
    const store = useAttendanceStore()
    
    await expect(store.outCheckpointSubmit('外出洽公')).rejects.toThrow()
    expect(store.outCheckpointError).toBeDefined()
    expect(store.outCheckpointError.code).toBe(LocationErrorCode.PERMISSION_DENIED)
  })
})
```

---

### View + useLocation

```javascript
describe('Home.vue with useLocation', () => {
  it('should display device type', async () => {
    const wrapper = mount(Home)
    
    await nextTick()
    
    const deviceType = wrapper.vm.deviceType
    expect(['mobile', 'pc']).toContain(deviceType)
  })
  
  it('should show loading state during location request', async () => {
    const wrapper = mount(Home)
    
    // Trigger location request
    await wrapper.vm.handleOutCheckpoint()
    
    expect(wrapper.vm.isLoading).toBe(true)
  })
  
  it('should show error message on location error', async () => {
    global.navigator.geolocation = {
      getCurrentPosition: vi.fn((_, error) => {
        error({ code: 1, message: 'Permission denied' })
      })
    }
    
    const wrapper = mount(Home)
    
    await wrapper.vm.handleOutCheckpoint()
    
    expect(wrapper.vm.errorMessage).toContain('定位權限')
  })
})
```

---

## E2E 測試

### Test Case 1: Mobile 完整流程

```javascript
test('Mobile user submits OUT checkpoint with GPS', async ({ page }) => {
  // 模擬 mobile 裝置
  await page.setViewportSize({ width: 375, height: 667 })
  await page.setUserAgent('Mozilla/5.0 (iPhone)')
  
  // 授予定位權限
  await page.context().grantPermissions(['geolocation'])
  await page.context().setGeolocation({ latitude: 25.0330, longitude: 121.5654 })
  
  // 登入
  await page.goto('/login')
  await page.fill('[name="username"]', 'testuser')
  await page.fill('[name="password"]', 'password')
  await page.click('button[type="submit"]')
  
  // 等待首頁載入
  await page.waitForURL('/home')
  
  // 選擇原因
  await page.click('text=外出洽公')
  
  // 提交 OUT checkpoint
  await page.click('text=記錄當前位置')
  
  // 等待成功訊息
  await expect(page.locator('text=位置記錄成功')).toBeVisible()
  
  // 驗證記錄出現在列表中
  await expect(page.locator('.checkpoint-list')).toContainText('外出洽公')
})
```

---

### Test Case 2: PC 完整流程

```javascript
test('PC user submits OUT checkpoint without GPS', async ({ page }) => {
  // 模擬 PC 裝置
  await page.setViewportSize({ width: 1920, height: 1080 })
  
  // 登入
  await page.goto('/login')
  await page.fill('[name="username"]', 'testuser')
  await page.fill('[name="password"]', 'password')
  await page.click('button[type="submit"]')
  
  // 等待首頁載入
  await page.waitForURL('/home')
  
  // 確認顯示 PC 提示
  await expect(page.locator('text=PC 不記錄定位')).toBeVisible()
  
  // 選擇原因
  await page.click('text=外出洽公')
  
  // 提交 OUT checkpoint
  await page.click('text=記錄當前位置')
  
  // 等待成功訊息
  await expect(page.locator('text=位置記錄成功')).toBeVisible()
})
```

---

### Test Case 3: 權限拒絕處理

```javascript
test('Handle permission denied gracefully', async ({ page, context }) => {
  // 模擬 mobile 裝置
  await page.setViewportSize({ width: 375, height: 667 })
  await page.setUserAgent('Mozilla/5.0 (iPhone)')
  
  // 拒絕定位權限
  await context.grantPermissions([])
  
  // 登入並導航到首頁
  await page.goto('/login')
  await page.fill('[name="username"]', 'testuser')
  await page.fill('[name="password"]', 'password')
  await page.click('button[type="submit"]')
  await page.waitForURL('/home')
  
  // 選擇原因並提交
  await page.click('text=外出洽公')
  await page.click('text=記錄當前位置')
  
  // 驗證錯誤訊息
  await expect(page.locator('text=請開啟定位權限')).toBeVisible()
})
```

---

## 手動測試

### 測試矩陣

| 裝置 | 瀏覽器 | GPS 狀態 | 預期結果 |
|------|--------|---------|---------|
| iPhone | Safari | 允許 | ✅ 提交成功（有 GPS） |
| iPhone | Safari | 拒絕 | ❌ 顯示權限錯誤 |
| iPhone | Chrome | 允許 | ✅ 提交成功（有 GPS） |
| Android | Chrome | 允許 | ✅ 提交成功（有 GPS） |
| Android | Chrome | 拒絕 | ❌ 顯示權限錯誤 |
| iPad | Safari | 允許 | ✅ 提交成功（有 GPS） |
| PC | Chrome | - | ✅ 提交成功（無 GPS） |
| PC | Firefox | - | ✅ 提交成功（無 GPS） |
| PC | Edge | - | ✅ 提交成功（無 GPS） |

---

### 測試步驟

#### Test Case: Mobile GPS 正常流程

**前置條件**:
- 使用真實 iPhone 或 Android 裝置
- 已安裝測試 App 或開啟測試網站
- GPS 功能已開啟

**步驟**:
1. 登入系統
2. 導航到首頁
3. 確認顯示「需要定位權限」提示
4. 點選「外出洽公」原因
5. 點選「記錄當前位置」按鈕
6. 如果首次使用，允許定位權限
7. 等待定位完成（應顯示 loading）
8. 確認顯示「位置記錄成功」訊息
9. 確認記錄出現在列表中，並顯示 📍 圖示

**預期結果**:
- ✅ 定位時間 < 5 秒
- ✅ 顯示成功訊息
- ✅ 記錄包含 GPS 資料
- ✅ 後端收到正確的 payload

---

#### Test Case: 權限拒絕處理

**前置條件**:
- 使用真實 mobile 裝置
- 已拒絕定位權限

**步驟**:
1. 登入系統
2. 導航到首頁
3. 點選「外出洽公」原因
4. 點選「記錄當前位置」按鈕
5. 觀察錯誤訊息

**預期結果**:
- ✅ 顯示「請開啟定位權限後再外出打點」
- ✅ 不會無限重試
- ✅ 提供明確的指引

---

#### Test Case: GPS 超時處理

**前置條件**:
- 使用真實 mobile 裝置
- 在 GPS 訊號不佳的環境（如室內）

**步驟**:
1. 登入系統
2. 導航到首頁
3. 點選「外出洽公」原因
4. 點選「記錄當前位置」按鈕
5. 等待超時（10 秒）

**預期結果**:
- ✅ 顯示「定位請求逾時」
- ✅ 如果啟用 retry，會自動重試
- ✅ 最終失敗後顯示明確錯誤

---

## 效能測試

### 測試指標

| 指標 | 目標 | 測試方法 |
|------|------|---------|
| 首次定位時間 | < 5s | 真實裝置測試 |
| 快取命中率 | > 80% | 模擬重複請求 |
| 記憶體使用 | < 1MB | Chrome DevTools |
| CPU 使用 | 可忽略 | Performance Monitor |

### 測試案例

```javascript
test('Location request should complete within 5 seconds', async () => {
  const { getCurrentLocation } = useLocation()
  
  const startTime = Date.now()
  await getCurrentLocation()
  const endTime = Date.now()
  
  const duration = endTime - startTime
  expect(duration).toBeLessThan(5000)
})

test('Cache should reduce subsequent requests', async () => {
  const { getCurrentLocation } = useLocation({
    cache: { enabled: true, maxAge: 300000 }
  })
  
  // First request
  const start1 = Date.now()
  await getCurrentLocation()
  const duration1 = Date.now() - start1
  
  // Second request (should use cache)
  const start2 = Date.now()
  await getCurrentLocation()
  const duration2 = Date.now() - start2
  
  expect(duration2).toBeLessThan(duration1 / 10)
})
```

---

## 相容性測試

### 瀏覽器支援

| 瀏覽器 | 版本 | 支援狀態 | 測試結果 |
|--------|------|---------|---------|
| Chrome | >= 90 | ✅ 完全支援 | ⏳ 待測試 |
| Firefox | >= 88 | ✅ 完全支援 | ⏳ 待測試 |
| Safari | >= 14 | ✅ 完全支援 | ⏳ 待測試 |
| Edge | >= 90 | ✅ 完全支援 | ⏳ 待測試 |
| IE 11 | - | ❌ 不支援 | N/A |

### 裝置支援

| 裝置 | OS 版本 | 支援狀態 | 測試結果 |
|------|---------|---------|---------|
| iPhone | iOS >= 14 | ✅ 完全支援 | ⏳ 待測試 |
| Android | >= 10 | ✅ 完全支援 | ⏳ 待測試 |
| iPad | iPadOS >= 14 | ✅ 完全支援 | ⏳ 待測試 |

---

## 測試環境

### 開發環境

- **工具**: Vitest
- **覆蓋率**: Istanbul
- **Mock**: vi.fn()
- **執行**: `npm run test:unit`

### CI/CD 環境

- **平台**: GitHub Actions
- **觸發**: 每次 push 和 PR
- **報告**: 自動生成覆蓋率報告
- **門檻**: 覆蓋率 > 80%

### 測試環境

- **URL**: https://staging.example.com
- **資料**: 測試資料庫
- **GPS**: Mock GPS 座標
- **使用者**: 測試帳號

---

## 測試數據

### Mock GPS 座標

```javascript
export const mockLocations = {
  taipei: {
    latitude: 25.0330,
    longitude: 121.5654,
    accuracy: 10
  },
  kaohsiung: {
    latitude: 22.6273,
    longitude: 120.3014,
    accuracy: 15
  },
  taichung: {
    latitude: 24.1477,
    longitude: 120.6736,
    accuracy: 12
  }
}
```

### 測試使用者

```javascript
export const testUsers = {
  mobile: {
    username: 'mobile_user',
    password: 'test123',
    device: 'iPhone'
  },
  pc: {
    username: 'pc_user',
    password: 'test123',
    device: 'PC'
  }
}
```

---

## 測試報告

### 報告格式

```markdown
# Test Report - useLocation

**日期**: 2026-03-08  
**版本**: 1.0.0

## 摘要
- 總測試數: 45
- 通過: 43
- 失敗: 2
- 跳過: 0
- 覆蓋率: 85%

## 失敗測試
1. Test Case: Retry on timeout
   - 原因: Mock 設定錯誤
   - 狀態: 已修復

2. Test Case: Permission state tracking
   - 原因: 瀏覽器不支援 Permissions API
   - 狀態: 已標記為 skip

## 建議
- 補充 Safari 特定測試
- 增加邊緣案例測試
```

---

## 參考資料

- [Vitest Documentation](https://vitest.dev/)
- [Playwright Documentation](https://playwright.dev/)
- [ATTENDANCE_LOCATION_MODULE_SPEC.md](./ATTENDANCE_LOCATION_MODULE_SPEC.md)
- [ATTENDANCE_LOCATION_FRONTEND_REFACTOR_PLAN.md](./ATTENDANCE_LOCATION_FRONTEND_REFACTOR_PLAN.md)

---

**版本歷史**:
- v1.0 (2026-03-08): 初始版本
