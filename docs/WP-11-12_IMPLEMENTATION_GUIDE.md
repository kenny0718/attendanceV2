# WP-11-12 Implementation Guide

**票號**: WP-11-12  
**階段**: Phase 2 - Minimal Implementation Slice  
**日期**: 2026-03-08

---

## 已完成項目

### ✅ Phase 1: Foundation 建立

1. **useLocation Composable**
   - ✅ 檔案: `frontend/src/composables/useLocation.js`
   - ✅ 功能: 完整的 location 服務
   - ✅ 文件: `frontend/src/composables/README.md`

2. **Import 已添加**
   - ✅ `frontend/src/stores/attendance.js` 已添加 useLocation import

---

## 待完成項目

### ⏳ Phase 2: 接入外出打卡流程

#### 修改 `frontend/src/stores/attendance.js`

找到 `case 'BREAK_OUT':` (約第 103 行)，修改為：

**修改前**:
```javascript
case 'BREAK_OUT':
  response = await attendanceApi.breakOut({ notes: notes || '' })
  this.todayStatus.break_out = response.punch_time
  this.todayStatus.is_on_break = true
  localStorage.setItem('is_on_break', 'true')
  // 打卡成功後刷新外出打卡記錄
  await this.loadBreakPunches()
  break
```

**修改後**:
```javascript
case 'BREAK_OUT':
  // WP-11-12: 使用 useLocation 取得定位
  const { getLocationIfRequired, deviceType: locDeviceType } = useLocation()
  
  try {
    // 自動判斷是否需要 GPS (Mobile 需要，PC 不需要)
    const gpsData = await getLocationIfRequired()
    
    // 準備 payload
    const payload = { notes: notes || '' }
    
    // 如果有 GPS 資料，加入 payload
    if (gpsData) {
      payload.gps = gpsData
    }
    
    // 呼叫 API
    response = await attendanceApi.breakOut(payload)
    
  } catch (locationError) {
    // 定位失敗，拋出友善錯誤
    throw new Error(locationError.message || '無法獲取定位')
  }
  
  // 更新狀態
  this.todayStatus.break_out = response.punch_time
  this.todayStatus.is_on_break = true
  localStorage.setItem('is_on_break', 'true')
  
  // 打卡成功後刷新外出打卡記錄
  await this.loadBreakPunches()
  break
```

**修改說明**:
1. 使用 `useLocation()` 取得 location 服務
2. 呼叫 `getLocationIfRequired()` 自動判斷是否需要 GPS
3. Mobile 會取得 GPS，PC 會返回 null
4. 如果有 GPS 資料，加入 payload
5. 完整的錯誤處理

---

#### 修改 `frontend/src/views/Home.vue`（可選）

如果要顯示 loading 狀態，可以在 Home.vue 中使用 useLocation：

```vue
<script setup>
import { useLocation } from '@/composables/useLocation'

// 在 setup 中使用
const {
  isLoading: locationLoading,
  error: locationError
} = useLocation()

// 在外出打卡按鈕中顯示 loading
</script>

<template>
  <button 
    @click="handlePunch('BREAK_OUT')"
    :disabled="!canBreakOut || isLoading || locationLoading"
  >
    {{ locationLoading ? '定位中...' : '外出打卡' }}
  </button>
  
  <div v-if="locationError" class="error">
    {{ locationError.message }}
  </div>
</template>
```

---

## 測試驗證

### 1. 單元測試（可選）

建立 `frontend/src/composables/__tests__/useLocation.spec.js`:

```javascript
import { describe, it, expect, vi } from 'vitest'
import { useLocation } from '../useLocation'

describe('useLocation', () => {
  it('should detect device type', () => {
    const { deviceType } = useLocation()
    expect(['mobile', 'pc']).toContain(deviceType.value)
  })
  
  it('should require GPS for mobile', () => {
    const { isGPSRequired, deviceType } = useLocation()
    if (deviceType.value === 'mobile') {
      expect(isGPSRequired.value).toBe(true)
    } else {
      expect(isGPSRequired.value).toBe(false)
    }
  })
})
```

### 2. 整合測試

**測試案例**:

#### TC-01: Mobile 外出打卡（允許定位）
```
前置條件: 使用 Mobile 裝置，允許定位權限
步驟:
1. 登入系統
2. 上班打卡
3. 點擊「外出打卡」
4. 選擇原因
5. 點擊「記錄當前位置」或直接外出打卡

預期結果:
✅ 顯示「定位中...」loading 狀態
✅ 成功取得 GPS
✅ 外出打卡成功
✅ 記錄包含 GPS 座標
```

#### TC-02: Mobile 外出打卡（拒絕定位）
```
前置條件: 使用 Mobile 裝置，拒絕定位權限
步驟:
1. 登入系統
2. 上班打卡
3. 點擊「外出打卡」
4. 拒絕定位權限

預期結果:
✅ 顯示錯誤訊息：「請開啟定位權限後再外出打點」
✅ 外出打卡失敗
✅ 可以重試
```

#### TC-03: PC 外出打卡
```
前置條件: 使用 PC
步驟:
1. 登入系統
2. 上班打卡
3. 點擊「外出打卡」

預期結果:
✅ 不要求 GPS
✅ 直接外出打卡成功
✅ 記錄不包含 GPS
```

#### TC-04: 不影響其他流程
```
測試項目:
✅ 上班打卡：正常
✅ 下班打卡：正常
✅ 返回打卡：正常（暫時不使用 useLocation）
```

---

## 驗收標準

### 功能驗收

- [ ] ✅ useLocation composable 已建立
- [ ] ✅ 外出打卡流程已接入 useLocation
- [ ] ✅ Mobile 可以取得 GPS
- [ ] ✅ PC 不要求 GPS
- [ ] ✅ Loading 狀態正確
- [ ] ✅ 錯誤處理正確
- [ ] ✅ 不影響其他已穩定流程

### 程式碼品質

- [ ] ✅ 程式碼清晰易讀
- [ ] ✅ 註解完整
- [ ] ✅ 無 console error
- [ ] ✅ 無 linter error

### 文件完整

- [ ] ✅ useLocation API 文件
- [ ] ✅ 使用範例
- [ ] ✅ 測試指引

---

## 回滾計劃

如果發現問題，可以快速回滾：

### 方式 1: Git Revert

```bash
cd /opt/attendance-system
git revert HEAD
```

### 方式 2: 恢復 locationAdapter

如果 useLocation 有問題，可以暫時恢復使用 locationAdapter：

```javascript
// 在 attendance.js 中
case 'BREAK_OUT':
  // 暫時恢復使用舊方法
  const deviceType = this.detectDeviceType()
  const payload = { notes: notes || '' }
  
  if (deviceType === 'mobile') {
    const gpsData = await this.getGPSLocation()
    payload.gps = gpsData
  }
  
  response = await attendanceApi.breakOut(payload)
  // ...
  break
```

---

## 下一步

### WP-11-12 第二階段（可選）

如果第一階段成功，可以繼續：

1. **接入返回打卡流程**
   - 修改 `case 'BREAK_IN':`
   - 使用相同的 useLocation 模式

2. **驗證多流程共用**
   - 確認 useLocation 可以被多個流程重用
   - 驗證 state 不會互相干擾

3. **逐步移除 locationAdapter**
   - 當所有流程都使用 useLocation 後
   - 可以刪除 locationAdapter.js

### 後續票次

- **WP-11-13**: Location Policy（Geofencing）
- **WP-11-14**: UI Enhancement（地圖顯示）
- **WP-11-15**: OUT Checkpoints 完整功能

---

**建立日期**: 2026-03-08  
**最後更新**: 2026-03-08  
**狀態**: Ready for Implementation
