# WP-11-13 Step 3 Frontend Integration Plan

**票號**: WP-11-13 Step 3  
**標題**: Location Policy Frontend Integration  
**日期**: 2026-03-08  
**前置條件**: Step 2 Backend Foundation 已完成並驗證

---

## 執行摘要

Step 3 專注於前端整合，讓使用者能夠：
1. 在 BREAK_OUT 時進行友善的前端 precheck（非 authoritative）
2. 處理各種 GPS 相關錯誤情況
3. 顯示清楚的錯誤訊息

**關鍵原則**:
- 前端 precheck 只是 UX-friendly，不是 authoritative
- 後端永遠是最終決策者
- 不在前端重複實作 policy 邏輯
- 保持簡單，專注於使用者體驗

---

## 範圍定義

### ✅ Step 3 包含

1. **BREAK_OUT 前端 precheck**
   - 在送出 API 前檢查 location policy
   - 提前顯示友善錯誤訊息
   - 節省不必要的 API 請求

2. **錯誤處理優化**
   - 處理 browser 無 GPS
   - 處理 permission denied
   - 處理 timeout
   - 處理後端 403 LOCATION_POLICY_VIOLATION

3. **基本 UI 改善**
   - 顯示 policy 狀態（是否有地點限制）
   - 顯示清楚的錯誤訊息
   - Loading 狀態

### ❌ Step 3 不包含

1. **管理端 UI**（留待 Step 3B 或後續票）
   - 地點列表頁面
   - 新增/編輯地點表單
   - Map picker
   - 地圖視覺化

2. **其他打卡流程**
   - BREAK_IN enforcement
   - punch-in enforcement
   - punch-out enforcement

3. **進階功能**
   - 位置歷史軌跡
   - 地點使用統計
   - 複雜 policy 規則

---

## 技術設計

### 1. BREAK_OUT 前端流程

#### 當前流程（WP-11-12 Phase 2B）

```javascript
async function handleBreakOutPunch() {
  try {
    // Step 1: 取得 location
    const gpsData = await getLocationIfRequired()
    
    // Step 2: 執行打卡
    await attendanceStore.punchWithLocation('BREAK_OUT', {
      notes: selectedReason.value,
      gps: gpsData
    })
    
  } catch (error) {
    // 錯誤處理
  }
}
```

#### Step 3 新流程

```javascript
async function handleBreakOutPunch() {
  try {
    // Step 1: 取得 location
    const gpsData = await getLocationIfRequired()
    
    // Step 2: 前端 precheck（WP-11-13 新增，UX-friendly only）
    if (gpsData && locationPolicy.value.hasRestrictions) {
      const precheckResult = checkLocationLocally(gpsData, locationPolicy.value)
      
      if (!precheckResult.allowed) {
        // 提前顯示友善錯誤，不送 API
        errorMessage.value = precheckResult.reason
        showErrorMessage.value = true
        return
      }
    }
    
    // Step 3: 執行打卡（後端仍會做 authoritative check）
    await attendanceStore.punchWithLocation('BREAK_OUT', {
      notes: selectedReason.value,
      gps: gpsData
    })
    
  } catch (error) {
    // Step 4: 處理後端 403 LOCATION_POLICY_VIOLATION
    if (error.response?.status === 403 && 
        error.response?.data?.detail?.error_code === 'LOCATION_POLICY_VIOLATION') {
      errorMessage.value = error.response.data.detail.error
      if (error.response.data.detail.nearest_location) {
        const nearest = error.response.data.detail.nearest_location
        errorMessage.value += `\n最近的地點：${nearest.name}（距離 ${nearest.distance_meters} 公尺）`
      }
      showErrorMessage.value = true
    } else {
      // 其他錯誤
      handleGenericError(error)
    }
  }
}
```

---

### 2. useLocationPolicy Composable

```typescript
// composables/useLocationPolicy.ts

export interface LocationPolicy {
  hasRestrictions: boolean  // 是否有地點限制
  allowedLocations: Array<{
    id: string
    name: string
    latitude: number
    longitude: number
    radius_meters: number
  }>
}

export interface PrecheckResult {
  allowed: boolean
  reason: string
  matchedLocation?: {
    name: string
    distance: number
  }
  nearestLocation?: {
    name: string
    distance: number
  }
}

export function useLocationPolicy() {
  const policy = ref<LocationPolicy | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  
  /**
   * 取得公司的 location policy
   * 在頁面載入時呼叫一次即可
   */
  async function fetchPolicy() {
    isLoading.value = true
    error.value = null
    
    try {
      // 呼叫後端 API（待實作）
      // const response = await api.get('/api/v1/attendance/location-policy')
      
      // 暫時模擬
      policy.value = {
        hasRestrictions: false,
        allowedLocations: []
      }
    } catch (err) {
      error.value = '無法取得地點政策'
      console.error('Failed to fetch location policy:', err)
    } finally {
      isLoading.value = false
    }
  }
  
  /**
   * 前端 precheck（UX-friendly only，非 authoritative）
   * 
   * 注意：這只是為了提供更好的使用者體驗
   * 後端仍會做最終的 authoritative check
   */
  function checkLocationLocally(
    gps: { latitude: number; longitude: number },
    policy: LocationPolicy
  ): PrecheckResult {
    // 如果沒有限制，允許
    if (!policy.hasRestrictions || policy.allowedLocations.length === 0) {
      return {
        allowed: true,
        reason: '公司允許任何地點打卡'
      }
    }
    
    // 計算與每個地點的距離
    let matchedLocation = null
    let nearestLocation = null
    let minDistance = Infinity
    
    for (const location of policy.allowedLocations) {
      const distance = calculateDistance(
        gps.latitude,
        gps.longitude,
        location.latitude,
        location.longitude
      )
      
      // 更新最近地點
      if (distance < minDistance) {
        minDistance = distance
        nearestLocation = {
          name: location.name,
          distance: Math.round(distance)
        }
      }
      
      // 檢查是否在範圍內
      if (distance <= location.radius_meters) {
        matchedLocation = {
          name: location.name,
          distance: Math.round(distance)
        }
        break
      }
    }
    
    // 返回結果
    if (matchedLocation) {
      return {
        allowed: true,
        reason: `在允許的打卡範圍內：${matchedLocation.name}`,
        matchedLocation
      }
    } else {
      return {
        allowed: false,
        reason: `不在允許的打卡範圍內`,
        nearestLocation
      }
    }
  }
  
  /**
   * 簡單的 Haversine 距離計算（公尺）
   */
  function calculateDistance(
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
  ): number {
    const R = 6371000 // 地球半徑（公尺）
    const φ1 = (lat1 * Math.PI) / 180
    const φ2 = (lat2 * Math.PI) / 180
    const Δφ = ((lat2 - lat1) * Math.PI) / 180
    const Δλ = ((lon2 - lon1) * Math.PI) / 180
    
    const a =
      Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
      Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2)
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
    
    return R * c
  }
  
  return {
    policy,
    isLoading,
    error,
    fetchPolicy,
    checkLocationLocally
  }
}
```

---

### 3. 錯誤處理策略

#### 3.1 Browser 無 GPS 可用

```javascript
// 在 useLocation.js 中已處理
// 如果 browser 不支援 geolocation，會回傳 null
// 前端應該允許繼續（後端會根據 policy 決定）
```

#### 3.2 Permission Denied

```javascript
// useLocation.js 已處理
// 會拋出錯誤，前端顯示友善訊息
errorMessage.value = '需要定位權限才能外出打卡，請在瀏覽器設定中允許定位'
```

#### 3.3 Timeout

```javascript
// useLocation.js 已處理
// 會拋出錯誤，前端顯示友善訊息
errorMessage.value = '定位逾時，請確認 GPS 訊號良好後重試'
```

#### 3.4 後端 403 LOCATION_POLICY_VIOLATION

```javascript
// 在 handleBreakOutPunch 的 catch 區塊處理
if (error.response?.status === 403 && 
    error.response?.data?.detail?.error_code === 'LOCATION_POLICY_VIOLATION') {
  // 顯示後端回傳的詳細錯誤訊息
  errorMessage.value = error.response.data.detail.error
  
  // 如果有最近地點資訊，也顯示
  if (error.response.data.detail.nearest_location) {
    const nearest = error.response.data.detail.nearest_location
    errorMessage.value += `\n\n最近的允許地點：\n${nearest.name}\n距離：${nearest.distance_meters} 公尺`
  }
  
  showErrorMessage.value = true
}
```

---

### 4. 需要修改的檔案

#### 前端檔案（預估）

1. **新增檔案**:
   - `frontend/src/composables/useLocationPolicy.ts` - Location policy composable
   - `frontend/src/api/locationPolicy.ts` - API 呼叫（可選）

2. **修改檔案**:
   - `frontend/src/views/Home.vue` - 修改 handleBreakOutPunch
   - `frontend/src/stores/attendance.ts` - 可能需要加入錯誤處理

3. **不修改**:
   - `frontend/src/composables/useLocation.js` - 已經完成，不需修改
   - `frontend/src/utils/locationAdapter.js` - 保持不變

---

### 5. API Endpoint（後端需要新增）

```
GET /api/v1/attendance/location-policy

Response:
{
  "require_location": true,
  "allow_any_location": false,
  "allowed_locations": [
    {
      "id": "uuid",
      "name": "台北101工地",
      "latitude": 25.0330,
      "longitude": 121.5654,
      "radius_meters": 100
    }
  ]
}
```

**注意**: 這個 endpoint 需要在 Step 3 實作（後端）

---

## 實作順序

### Phase 3A: 後端 API（1-2 小時）

1. 在 `backend/app/modules/attendance/api.py` 新增 endpoint:
   ```python
   @router_v1.get("/location-policy")
   async def get_location_policy(
       company_id: str = Depends(get_current_company_id),
       db: Session = Depends(get_db)
   ):
       """取得公司的 location policy（前端用）"""
       pass
   ```

2. 實作邏輯：
   - 查詢公司的 active allowed locations
   - 只返回必要欄位（id, name, lat, lng, radius）
   - 不返回 description, created_at 等管理資訊

---

### Phase 3B: 前端 Composable（1-2 小時）

1. 建立 `useLocationPolicy.ts`
2. 實作 `fetchPolicy()`
3. 實作 `checkLocationLocally()`
4. 實作 `calculateDistance()`

---

### Phase 3C: Home.vue 整合（1-2 小時）

1. Import `useLocationPolicy`
2. 在 `onMounted` 時呼叫 `fetchPolicy()`
3. 修改 `handleBreakOutPunch()` 加入前端 precheck
4. 優化錯誤處理

---

### Phase 3D: 測試與驗證（1-2 小時）

1. 測試無 policy 情況
2. 測試有 policy + 在範圍內
3. 測試有 policy + 超出範圍
4. 測試各種錯誤情況
5. 測試前端 precheck 與後端 enforcement 的一致性

---

## 管理端 UI 決策

### 建議：拆分成 Step 3B（或獨立票）

**理由**:
1. 管理端 UI 是獨立功能，不影響打卡流程
2. 可以先完成打卡端整合，驗證核心功能
3. 管理端 UI 工作量較大（列表、表單、驗證）
4. 降低單一票的複雜度

**Step 3A 範圍**:
- BREAK_OUT 前端整合
- 錯誤處理
- 基本 UI 改善

**Step 3B 範圍**（後續票）:
- 管理端地點列表頁面
- 新增/編輯地點表單
- 刪除確認
- 啟用/停用切換
- 分頁與搜尋

---

## 風險與注意事項

### 1. 前端 precheck 與後端不一致

**風險**: 前端說可以，後端說不行（或反之）

**緩解**:
- 前端使用相同的距離計算公式（Haversine）
- 前端 precheck 只是提示，不是最終決策
- 後端永遠是 authoritative
- 測試時驗證一致性

---

### 2. GPS 精度問題

**風險**: GPS 精度不足，使用者在邊界附近

**緩解**:
- 前端顯示清楚的錯誤訊息
- 建議使用者移動到更明確的位置
- 後端使用相同的精度標準

---

### 3. 網路延遲

**風險**: fetchPolicy 延遲，影響使用者體驗

**緩解**:
- 在頁面載入時就 fetch policy（不是打卡時才 fetch）
- 加入 loading 狀態
- 快取 policy（合理的 TTL）

---

## Definition of Done

### Step 3A 完成條件

- [ ] 後端 `/api/v1/attendance/location-policy` endpoint 已實作
- [ ] `useLocationPolicy` composable 已建立
- [ ] Home.vue 已整合前端 precheck
- [ ] 錯誤處理已優化
- [ ] 測試通過（無 policy, 有 policy, 各種錯誤）
- [ ] 前端 precheck 與後端 enforcement 一致性已驗證
- [ ] 文件已更新

---

## 相關文件

- `docs/WP-11-13_LOCATION_POLICY_DESIGN.md` - 設計文件
- `docs/WP-11-13_IMPLEMENTATION_PLAN.md` - 實作計劃
- `docs/WP-11-13_STEP2_VERIFICATION_REPORT.md` - Step 2 驗證報告
- `docs/WP-11-12_PHASE2B_CLOSEOUT_SUMMARY.md` - useLocation 基礎

---

**建立日期**: 2026-03-08  
**狀態**: 計劃中  
**預估工作量**: 1-1.5 天（Step 3A only）  
**前置條件**: Step 2 已完成並驗證 ✅
