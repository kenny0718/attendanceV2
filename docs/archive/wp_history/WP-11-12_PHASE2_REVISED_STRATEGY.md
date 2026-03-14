# WP-11-12 Phase 2 實作策略修正

**票號**: WP-11-12  
**階段**: Phase 2A - BREAK_OUT Integration (Revised)  
**日期**: 2026-03-08  
**狀態**: In Progress

---

## 策略修正說明

### 原策略問題

原本計劃讓 store 直接主導 `useLocation()` state，會導致：
- ❌ Store 和 View 各自維護兩套 location state
- ❌ Reactive state 管理混亂
- ❌ UI 層無法直接控制 loading / error 顯示
- ❌ 違反關注點分離原則

### 新策略

**UI 層主導 location 取得，Store 層處理業務邏輯**

```
┌─────────────────────────────────────────┐
│ Home.vue (UI Layer)                     │
│ - 使用 useLocation()                    │
│ - 管理 location loading / error UI     │
│ - 取得 location 後傳給 store           │
└─────────────────────────────────────────┘
                    ↓
         location data (or null)
                    ↓
┌─────────────────────────────────────────┐
│ attendance.js (Store/Business Layer)    │
│ - 接收 location 參數                    │
│ - 處理打卡業務邏輯                      │
│ - 呼叫 API                              │
│ - 不直接管理 composable UI state       │
└─────────────────────────────────────────┘
```

---

## GPS 兩層用途明確分離

### Layer 1: Runtime Location Collection（本票實作）

**用途**: 打卡當下取得目前 GPS

**適用流程**:
- 外出打卡 (BREAK_OUT)
- 返回打卡 (BREAK_IN)
- 未來其他需要記錄位置的流程

**實作方式**:
- 使用 `useLocation` composable
- UI 層主導取得
- 傳遞給 store 作為 API payload

**本票完成**: ✅ 實作 BREAK_OUT 整合

---

### Layer 2: Attendance Location Policy / Geofence（未來票）

**用途**: 公司可在後台設定允許打卡的位置

**使用情境**:
- 工地打卡：只能在工地範圍內打卡
- 客戶現場：只能在客戶地點打卡
- 辦公室：只能在辦公室範圍內打卡
- 彈性工作：任何地點都可打卡

**資料模型（預留）**:
```typescript
interface AllowedLocation {
  id: string
  name: string              // 例如：「台北工地」
  latitude: number
  longitude: number
  radius_meters: number     // 允許半徑（公尺）
  enabled: boolean
  description?: string
  created_at: string
  updated_at: string
}

interface LocationPolicy {
  require_location: boolean          // 是否要求定位
  allowed_locations: AllowedLocation[]  // 允許的地點列表
  allow_any_location: boolean        // 是否允許任何地點
}
```

**未來流程**:
```
1. 取得目前 location (Layer 1)
2. 檢查 location policy (Layer 2)
3. 驗證是否在允許範圍內
4. 決定是否允許打卡
```

**本票完成**: ✅ 設計預留，不實作

---

## 架構設計

### UI Layer (Home.vue)

**責任**:
- 使用 `useLocation()` 取得 location 服務
- 管理 location loading / error UI
- 顯示定位中、權限拒絕、超時等狀態
- 取得 location 後傳給 store

**不負責**:
- ❌ 打卡業務邏輯
- ❌ API 呼叫
- ❌ 狀態持久化

**程式碼結構**:
```vue
<script setup>
import { useLocation } from '@/composables/useLocation'

// 只在 UI 層使用一次 useLocation
const {
  location,
  error: locationError,
  isLoading: locationLoading,
  deviceType,
  isGPSRequired,
  getLocationIfRequired
} = useLocation()

async function handleBreakOut() {
  try {
    // UI 層負責取得 location
    const gpsData = await getLocationIfRequired()
    
    // 傳給 store 處理業務邏輯
    await attendanceStore.punchWithLocation('BREAK_OUT', {
      notes: selectedReason.value,
      gps: gpsData
    })
    
  } catch (err) {
    // locationError 已自動設定
    // UI 層顯示錯誤
  }
}
</script>

<template>
  <!-- 顯示 location loading -->
  <div v-if="locationLoading">定位中...</div>
  
  <!-- 顯示 location error -->
  <div v-if="locationError">{{ locationError.message }}</div>
  
  <!-- 外出打卡按鈕 -->
  <button 
    @click="handleBreakOut"
    :disabled="locationLoading || isLoading"
  >
    外出打卡
  </button>
</template>
```

---

### Store Layer (attendance.js)

**責任**:
- 接收已取得的 location 資料
- 處理打卡業務邏輯
- 呼叫 API
- 更新 state
- 錯誤處理

**不負責**:
- ❌ 直接管理 composable reactive state
- ❌ UI loading / error 顯示
- ❌ 直接呼叫 navigator.geolocation

**程式碼結構**:
```javascript
// 新方法：接收 location 作為參數
async punchWithLocation(type, payload) {
  this.isLoading = true
  this.error = null
  
  try {
    let response
    
    switch (type) {
      case 'BREAK_OUT':
        // 直接使用傳入的 payload（包含 gps）
        response = await attendanceApi.breakOut(payload)
        this.todayStatus.break_out = response.punch_time
        this.todayStatus.is_on_break = true
        localStorage.setItem('is_on_break', 'true')
        await this.loadBreakPunches()
        break
        
      // ... 其他 case
    }
    
    return { success: true, data: response }
    
  } catch (error) {
    this.error = this.handleError(error)
    throw this.error
    
  } finally {
    this.isLoading = false
  }
}
```

---

### Composable Layer (useLocation.js)

**責任**:
- 提供統一的 location 服務
- 裝置類型判斷
- GPS 定位獲取
- Loading 狀態管理
- 錯誤處理

**不負責**:
- ❌ Geofence 規則驗證
- ❌ Location policy 檢查
- ❌ 打卡業務邏輯

**保持不變**: 已在 Phase 1 完成

---

## 避免雙重 useLocation() State

### ❌ 錯誤做法

```javascript
// Home.vue
const location1 = useLocation()

// attendance.js
const location2 = useLocation()

// 問題：兩個獨立的 reactive state，無法同步
```

### ✅ 正確做法

```javascript
// Home.vue (唯一使用點)
const {
  location,
  error,
  isLoading,
  getLocationIfRequired
} = useLocation()

// 取得 location 後傳給 store
const gps = await getLocationIfRequired()
await store.punchWithLocation('BREAK_OUT', { gps })

// attendance.js (只接收資料)
async punchWithLocation(type, payload) {
  // payload.gps 已經是取得好的資料
  await api.breakOut(payload)
}
```

---

## 未來 Geofence / Allowed Locations 整合點

### 整合點 1: UI Layer

```vue
<script setup>
// 未來可以加入 location policy 檢查
async function handleBreakOut() {
  // Step 1: 取得 location (本票已完成)
  const gpsData = await getLocationIfRequired()
  
  // Step 2: 檢查 location policy (未來票)
  // const policyCheck = await checkLocationPolicy(gpsData)
  // if (!policyCheck.allowed) {
  //   showError('不在允許的打卡範圍內')
  //   return
  // }
  
  // Step 3: 執行打卡
  await store.punchWithLocation('BREAK_OUT', { gps: gpsData })
}
</script>
```

### 整合點 2: Store Layer

```javascript
// 未來可以加入 policy 參數
async punchWithLocation(type, payload, options = {}) {
  // options.skipPolicyCheck - 是否跳過 policy 檢查
  // options.policyResult - policy 檢查結果
  
  // 未來可以在這裡記錄 policy 檢查結果
  // if (options.policyResult) {
  //   payload.policy_check = options.policyResult
  // }
  
  await api.breakOut(payload)
}
```

### 整合點 3: API Layer

```javascript
// 未來 API payload 可以包含 policy 資訊
{
  notes: '外出洽公',
  gps: {
    latitude: 25.0330,
    longitude: 121.5654,
    accuracy: 10,
    captured_at: '2026-03-08T10:00:00Z',
    provider: 'gps'
  },
  // 未來可以加入
  // location_policy_check: {
  //   allowed_location_id: 'loc-123',
  //   distance_from_center: 50,
  //   within_radius: true
  // }
}
```

---

## 實作檔案清單

### 修改檔案

1. **`frontend/src/views/Home.vue`**
   - 使用 `useLocation()` 在 UI 層
   - 修改 `handlePunch` 處理 BREAK_OUT
   - 顯示 location loading / error UI

2. **`frontend/src/stores/attendance.js`**
   - 新增 `punchWithLocation()` 方法
   - 調整 BREAK_OUT 流程接收 location 參數
   - 移除直接呼叫 geolocation 的程式碼（保留但標記為 deprecated）

3. **`docs/WP-11-12_PHASE2_REVISED_STRATEGY.md`** (本文件)
   - 記錄策略修正
   - 記錄 GPS 兩層用途
   - 記錄未來整合點

4. **`docs/WP-11-13_LOCATION_POLICY_PREP.md`** (新增)
   - Location policy 設計預留
   - 資料模型建議
   - 整合點說明

### 不修改檔案

- ✅ `frontend/src/composables/useLocation.js` - 保持不變
- ✅ `frontend/src/utils/locationAdapter.js` - 保留作為 bridge
- ✅ BREAK_IN / IN / OUT 流程 - 保持不變

---

## 測試驗證

### TC-01: Mobile 外出打卡（允許定位）

```
前置條件: Mobile 裝置，允許定位權限
步驟:
1. 登入系統
2. 上班打卡
3. 點擊「外出打卡」
4. 選擇原因
5. 點擊確認

預期結果:
✅ 顯示「定位中...」
✅ 成功取得 GPS
✅ 外出打卡成功
✅ 記錄包含 GPS 座標
```

### TC-02: Mobile 外出打卡（拒絕定位）

```
前置條件: Mobile 裝置，拒絕定位權限
步驟:
1. 登入系統
2. 上班打卡
3. 點擊「外出打卡」
4. 拒絕定位權限

預期結果:
✅ 顯示錯誤：「請開啟定位權限後再外出打點」
✅ 外出打卡失敗
✅ 可以重試
```

### TC-03: PC 外出打卡

```
前置條件: PC
步驟:
1. 登入系統
2. 上班打卡
3. 點擊「外出打卡」

預期結果:
✅ 不要求 GPS
✅ 直接外出打卡成功
✅ 記錄不包含 GPS

注意: 未來應改由 policy 決定是否要求定位
```

### TC-04: 回歸測試

```
驗證項目:
✅ 上班打卡：正常
✅ 下班打卡：正常
✅ 返回打卡：正常
✅ 不引入新的重複 geolocation 實作
```

---

## Definition of Done

### Phase 2A 完成條件

- [ ] ✅ BREAK_OUT 已改用 shared location foundation
- [ ] ✅ Location 取得由 UI 層統一主導
- [ ] ✅ Store 僅負責業務與 API
- [ ] ✅ 避免雙重 useLocation() state
- [ ] ✅ 未來 geofence 已有明確設計預留
- [ ] ✅ 文件已更新
- [ ] ✅ 不破壞已穩定流程
- [ ] ✅ 測試驗證通過

---

## 明確不做的事項

### 本票不做

- ❌ Geofence 規則實作
- ❌ 後台地點管理 UI
- ❌ Allowed locations API
- ❌ Location policy 驗證邏輯
- ❌ Map render
- ❌ OUT checkpoints
- ❌ BREAK_IN 全面重構
- ❌ 上班/下班打卡位置化
- ❌ 大量 state management overhaul

### 留到後續票

**WP-11-13: Location Policy**
- Geofence 規則實作
- Allowed locations 資料模型
- Policy 驗證邏輯
- 後台管理 UI

**WP-11-14: UI Enhancement**
- 地圖顯示
- 位置標記
- 歷史軌跡

---

**建立日期**: 2026-03-08  
**最後更新**: 2026-03-08  
**狀態**: Ready to Implement
