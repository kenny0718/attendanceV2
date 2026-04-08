# WP-11-13 Location Policy 預留設計

**票號**: WP-11-13 (預留)  
**標題**: Attendance Location Policy / Geofence  
**狀態**: Design Prep Only (本票不實作)  
**日期**: 2026-03-08

---

## 目的

本文件為 WP-11-12 預留未來 Location Policy / Geofence 功能的設計方向。

**重要**: 本票（WP-11-12）只做設計預留，不實作任何 policy 相關功能。

---

## GPS 兩層用途

### Layer 1: Runtime Location Collection（WP-11-12 實作）

**用途**: 打卡當下取得目前 GPS

**實作狀態**: ✅ WP-11-12 完成

---

### Layer 2: Attendance Location Policy（WP-11-13 實作）

**用途**: 公司可在後台設定允許打卡的位置

**實作狀態**: ⏳ 未來票次

---

## 使用情境

### 情境 1: 工地打卡

```
公司: 建築公司
需求: 員工只能在工地範圍內打卡

設定:
- 地點名稱: 台北101工地
- 經緯度: 25.0330, 121.5654
- 半徑: 100 公尺
- 啟用: 是

行為:
- 員工在工地範圍內 → 允許打卡
- 員工在工地範圍外 → 拒絕打卡，顯示「不在允許的打卡範圍內」
```

### 情境 2: 客戶現場

```
公司: 顧問公司
需求: 員工可在多個客戶地點打卡

設定:
- 地點 1: A客戶辦公室 (25.0330, 121.5654, 50m)
- 地點 2: B客戶辦公室 (25.0430, 121.5754, 50m)
- 地點 3: C客戶辦公室 (25.0530, 121.5854, 50m)

行為:
- 員工在任一客戶地點範圍內 → 允許打卡
- 員工不在任何客戶地點範圍內 → 拒絕打卡
```

### 情境 3: 彈性工作

```
公司: 科技公司
需求: 員工可在任何地點打卡

設定:
- 允許任何地點: 是
- 不設定具體地點

行為:
- 員工在任何地點 → 允許打卡
- 仍然記錄 GPS（用於統計分析）
```

### 情境 4: 辦公室 + 彈性

```
公司: 混合辦公
需求: 員工可在辦公室或遠端工作

設定:
- 地點 1: 台北辦公室 (25.0330, 121.5654, 100m)
- 允許任何地點: 是

行為:
- 員工在辦公室 → 允許打卡，標記為「辦公室」
- 員工在其他地點 → 允許打卡，標記為「遠端」
```

---

## 資料模型（預留）

### AllowedLocation

```typescript
interface AllowedLocation {
  // 基本資訊
  id: string                    // UUID
  tenant_id: string             // 租戶 ID
  name: string                  // 地點名稱，例如：「台北101工地」
  description?: string          // 描述
  
  // 位置資訊
  latitude: number              // 緯度
  longitude: number             // 經度
  radius_meters: number         // 允許半徑（公尺）
  
  // 狀態
  enabled: boolean              // 是否啟用
  
  // 時間戳記
  created_at: string            // ISO 8601
  updated_at: string            // ISO 8601
  created_by: string            // 建立者 user_id
  updated_by: string            // 更新者 user_id
}
```

### LocationPolicy

```typescript
interface LocationPolicy {
  // 基本設定
  tenant_id: string
  
  // Policy 設定
  require_location: boolean          // 是否要求定位
  allow_any_location: boolean        // 是否允許任何地點
  
  // 允許的地點列表
  allowed_locations: AllowedLocation[]
  
  // 進階設定（未來）
  strict_mode: boolean               // 嚴格模式：必須在範圍內
  warning_mode: boolean              // 警告模式：範圍外可打卡但警告
  
  // 時間戳記
  updated_at: string
  updated_by: string
}
```

### LocationPolicyCheck

```typescript
interface LocationPolicyCheck {
  // 檢查結果
  allowed: boolean                   // 是否允許打卡
  reason: string                     // 原因
  
  // 匹配的地點（如果有）
  matched_location?: {
    id: string
    name: string
    distance_meters: number          // 距離中心點的距離
    within_radius: boolean           // 是否在半徑內
  }
  
  // 最近的地點（如果沒有匹配）
  nearest_location?: {
    id: string
    name: string
    distance_meters: number
  }
  
  // 檢查時間
  checked_at: string
}
```

---

## API 設計（預留）

### 後端 API

#### 1. 取得 Location Policy

```
GET /api/v1/attendance/location-policy

Response:
{
  "require_location": true,
  "allow_any_location": false,
  "allowed_locations": [
    {
      "id": "loc-123",
      "name": "台北101工地",
      "latitude": 25.0330,
      "longitude": 121.5654,
      "radius_meters": 100,
      "enabled": true
    }
  ]
}
```

#### 2. 檢查 Location

```
POST /api/v1/attendance/location-policy/check

Request:
{
  "latitude": 25.0335,
  "longitude": 121.5660
}

Response:
{
  "allowed": true,
  "reason": "在允許的打卡範圍內",
  "matched_location": {
    "id": "loc-123",
    "name": "台北101工地",
    "distance_meters": 45,
    "within_radius": true
  }
}
```

#### 3. 管理 Allowed Locations（管理員）

```
GET    /api/v1/admin/allowed-locations
POST   /api/v1/admin/allowed-locations
PUT    /api/v1/admin/allowed-locations/:id
DELETE /api/v1/admin/allowed-locations/:id
```

---

## 前端整合點（預留）

### 整合點 1: UI Layer (Home.vue)

```vue
<script setup>
import { useLocation } from '@/composables/useLocation'
import { useLocationPolicy } from '@/composables/useLocationPolicy'  // 未來

const {
  location,
  error: locationError,
  isLoading: locationLoading,
  getLocationIfRequired
} = useLocation()

// 未來可以加入
// const {
//   policy,
//   checkLocation,
//   isChecking
// } = useLocationPolicy()

async function handleBreakOut() {
  try {
    // Step 1: 取得 location (WP-11-12 已完成)
    const gpsData = await getLocationIfRequired()
    
    // Step 2: 檢查 location policy (WP-11-13 未來)
    // if (policy.value.require_location && gpsData) {
    //   const policyCheck = await checkLocation(gpsData)
    //   
    //   if (!policyCheck.allowed) {
    //     showError(policyCheck.reason)
    //     return
    //   }
    // }
    
    // Step 3: 執行打卡
    await attendanceStore.punchWithLocation('BREAK_OUT', {
      notes: selectedReason.value,
      gps: gpsData
      // 未來可以加入
      // policy_check: policyCheck
    })
    
  } catch (err) {
    // 錯誤處理
  }
}
</script>

<template>
  <!-- 未來可以顯示 policy 資訊 -->
  <!-- <div v-if="policy.allowed_locations.length > 0">
    <p>允許的打卡地點：</p>
    <ul>
      <li v-for="loc in policy.allowed_locations" :key="loc.id">
        {{ loc.name }}
      </li>
    </ul>
  </div> -->
  
  <button @click="handleBreakOut">外出打卡</button>
</template>
```

### 整合點 2: Store Layer (attendance.js)

```javascript
// 未來可以加入 policy 參數
async punchWithLocation(type, payload, options = {}) {
  this.isLoading = true
  
  try {
    // 未來可以在 payload 中包含 policy check 結果
    // if (options.policyCheck) {
    //   payload.location_policy_check = {
    //     allowed_location_id: options.policyCheck.matched_location?.id,
    //     distance_from_center: options.policyCheck.matched_location?.distance_meters,
    //     within_radius: options.policyCheck.matched_location?.within_radius
    //   }
    // }
    
    const response = await attendanceApi.breakOut(payload)
    
    // 更新狀態
    this.todayStatus.break_out = response.punch_time
    this.todayStatus.is_on_break = true
    
    return { success: true, data: response }
    
  } finally {
    this.isLoading = false
  }
}
```

### 整合點 3: Composable Layer (useLocationPolicy.js)

```javascript
// 未來可以建立 useLocationPolicy composable

import { ref, computed } from 'vue'
import { locationPolicyApi } from '@/api/locationPolicy'

export function useLocationPolicy() {
  const policy = ref(null)
  const isLoading = ref(false)
  const error = ref(null)
  
  async function fetchPolicy() {
    isLoading.value = true
    try {
      policy.value = await locationPolicyApi.getPolicy()
    } catch (err) {
      error.value = err
    } finally {
      isLoading.value = false
    }
  }
  
  async function checkLocation(gpsData) {
    try {
      return await locationPolicyApi.checkLocation(gpsData)
    } catch (err) {
      throw err
    }
  }
  
  const requireLocation = computed(() => policy.value?.require_location ?? false)
  const allowAnyLocation = computed(() => policy.value?.allow_any_location ?? true)
  
  return {
    policy,
    isLoading,
    error,
    fetchPolicy,
    checkLocation,
    requireLocation,
    allowAnyLocation
  }
}
```

---

## Geofence 計算邏輯（預留）

### Haversine Distance

```javascript
/**
 * 計算兩個 GPS 座標之間的距離（公尺）
 * 使用 Haversine formula
 */
function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371000 // 地球半徑（公尺）
  const φ1 = lat1 * Math.PI / 180
  const φ2 = lat2 * Math.PI / 180
  const Δφ = (lat2 - lat1) * Math.PI / 180
  const Δλ = (lon2 - lon1) * Math.PI / 180
  
  const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
            Math.cos(φ1) * Math.cos(φ2) *
            Math.sin(Δλ / 2) * Math.sin(Δλ / 2)
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  
  return R * c // 距離（公尺）
}

/**
 * 檢查是否在允許範圍內
 */
function isWithinRadius(currentLat, currentLon, centerLat, centerLon, radiusMeters) {
  const distance = calculateDistance(currentLat, currentLon, centerLat, centerLon)
  return distance <= radiusMeters
}
```

---

## 未來實作順序

### WP-11-13 Phase 1: 基礎 Policy

1. 後端資料模型
2. 後端 API
3. 前端 useLocationPolicy composable
4. 前端 policy 檢查整合

### WP-11-13 Phase 2: 管理介面

1. 管理員後台 UI
2. 地點管理（新增/編輯/刪除）
3. Policy 設定

### WP-11-13 Phase 3: 進階功能

1. 地圖顯示
2. 位置標記
3. 歷史軌跡
4. 統計分析

---

## 注意事項

### 裝置類型 vs Policy

**目前（WP-11-12）**:
- Mobile 需要 GPS
- PC 不需要 GPS
- 寫死在程式碼中

**未來（WP-11-13）**:
- 應改由 policy 決定是否要求定位
- 不應該根據裝置類型判斷
- 例如：PC 也可能需要定位（如果公司要求）

**建議**:
```javascript
// ❌ 不好：寫死裝置類型
if (deviceType === 'mobile') {
  requireGPS = true
}

// ✅ 好：由 policy 決定
if (policy.require_location) {
  requireGPS = true
}
```

---

## 本票明確不做

- ❌ 不實作 geofence 規則
- ❌ 不實作後台地點管理
- ❌ 不實作 allowed locations API
- ❌ 不實作 location policy 驗證
- ❌ 不實作地圖顯示
- ❌ 不修改裝置類型判斷邏輯（保持現狀）

**只做**: 設計預留，文件記錄

---

**建立日期**: 2026-03-08  
**最後更新**: 2026-03-08  
**狀態**: Design Prep Only  
**實作票號**: WP-11-13 (未來)
