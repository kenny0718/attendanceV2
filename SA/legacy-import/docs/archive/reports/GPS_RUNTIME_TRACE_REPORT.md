# GPS 運行時追蹤報告

## 執行時間
2026-03-09 11:26

## 問題描述

用戶報告：
- 手機操作外出打卡時，出現白色視窗/彈窗
- 視窗內容不可見
- 懷疑 GPS 無法正常取得或保存

---

## 前端 GPS 流程 Trace

### 1. 哪些操作會要求 GPS

根據代碼分析：

| 操作 | 是否要求 GPS | 條件 |
|------|-------------|------|
| 上班打卡 | ❌ 否 | 不使用 `getLocationIfRequired` |
| 下班打卡 | ❌ 否 | 不使用 `getLocationIfRequired` |
| **外出打卡** | ✅ **是** | **使用 `getLocationIfRequired`，Mobile 需要 GPS** |
| 返回打卡 | ❌ 否 | 不使用 `getLocationIfRequired` |

**證據：**
```javascript
// Home.vue line 492
const handleBreakOutPunch = async () => {
  // 驗證原因...
  
  try {
    // Step 1: UI 層取得 location
    const gpsData = await getLocationIfRequired()  // ← 只有外出打卡會調用
    
    // Step 2: 傳給 store 處理業務邏輯，帶入原因
    await attendanceStore.punchWithLocation('BREAK_OUT', {
      notes: breakOutReason.value.trim(),
      gps: gpsData  // ← 傳遞 GPS 數據
    })
  }
}
```

### 2. 實際呼叫 geolocation 的方法

**方法名稱：** `getCurrentLocation()`  
**檔案位置：** `/opt/attendance-system/frontend/src/composables/useLocation.js`  
**呼叫時機：** 當 `deviceType === 'mobile'` 且調用 `getLocationIfRequired()` 時

**實作：**
```javascript
// useLocation.js line 138-165
async function getCurrentLocation() {
  isLoading.value = true
  error.value = null
  
  try {
    // 檢查瀏覽器支援
    if (!navigator.geolocation) {
      throw createLocationError(
        '此裝置不支援定位功能',
        LocationErrorCode.NOT_SUPPORTED
      )
    }
    
    // 獲取定位
    const position = await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        resolve,
        reject,
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        }
      )
    })
    
    // 建立標準化的位置資料
    const locationData = {
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      accuracy: position.coords.accuracy,
      captured_at: new Date().toISOString(),
      provider: 'gps'
    }
    
    location.value = locationData
    return locationData
  }
}
```

### 3. GPS 成功後資料流向

**成功路徑：**
```
getCurrentLocation() 
  → 返回 locationData { latitude, longitude, accuracy, captured_at, provider }
  → getLocationIfRequired() 返回 locationData
  → handleBreakOutPunch() 接收為 gpsData
  → 傳入 punchWithLocation('BREAK_OUT', { notes, gps: gpsData })
  → store 調用 attendanceApi.breakOut({ notes, gps: gpsData })
  → 發送 POST /api/v1/attendance/break-out
```

### 4. GPS 失敗時的錯誤處理

**錯誤類型與訊息：**

| 錯誤碼 | 訊息 | 觸發條件 |
|--------|------|----------|
| `PERMISSION_DENIED` | "需要定位權限才能外出打卡\n請在瀏覽器設定中允許定位後重試" | 用戶拒絕定位權限 |
| `TIMEOUT` | "定位請求逾時\n請確認 GPS 訊號良好後重試" | 10 秒內無法取得定位 |
| `POSITION_UNAVAILABLE` | "無法取得定位資訊\n請確認已開啟定位服務" | GPS 硬體或服務不可用 |
| `NOT_SUPPORTED` | "此裝置不支援定位功能" | 瀏覽器不支援 geolocation |

**顯示方式：**
```javascript
// Home.vue line 527-541
errorMessage.value = message
showErrorMessage.value = true

setTimeout(() => {
  showErrorMessage.value = false
}, 5000)
```

錯誤會顯示在右下角的 **error-toast**（紅色背景，白色文字）

---

## GPS Request Payload Trace

### 問題發現：欄位名稱不匹配

**前端發送：**
```javascript
// Home.vue line 495-498
await attendanceStore.punchWithLocation('BREAK_OUT', {
  notes: breakOutReason.value.trim(),
  gps: gpsData  // ← 欄位名稱是 "gps"
})
```

**Store 傳遞：**
```javascript
// attendance.js line 141
response = await attendanceApi.breakOut(payload)
// payload = { notes: "...", gps: { latitude, longitude, ... } }
```

**後端期望：**
```python
# schemas.py
class BreakOutRequest(BaseModel):
    notes: Optional[str] = None
    location: Optional[LocationData] = None  # ← 欄位名稱是 "location"
    punch_time: Optional[datetime] = None

class LocationData(BaseModel):
    latitude: float
    longitude: float
```

### 🔴 **根本原因：欄位名稱不匹配**

- **前端發送：** `{ notes: "...", gps: { latitude, longitude, ... } }`
- **後端期望：** `{ notes: "...", location: { latitude, longitude } }`
- **結果：** 後端收到 `gps` 欄位，但 schema 中沒有定義，被忽略
- **最終：** `location` 為 `None`，GPS 未保存到資料庫

---

## 後端 Route / Schema / DB Trace

### 1. Break-Out Route

**檔案：** `/opt/attendance-system/backend/app/modules/attendance/api.py`  
**路由：** `POST /api/v1/attendance/break-out`  
**行號：** 370-420

**Request Schema：**
```python
class BreakOutRequest(BaseModel):
    notes: Optional[str] = Field(None, max_length=500)
    location: Optional[LocationData] = Field(None)  # ← 正確欄位名
    punch_time: Optional[datetime] = Field(None)
```

**處理邏輯：**
```python
@router_v1.post("/break-out", response_model=BreakOutResponse, status_code=201)
async def break_out(
    request: BreakOutRequest,  # ← 接收 request.location
    ...
):
    # WP-11-13: Location policy enforcement
    matched_location_id = None
    if request.location:  # ← 檢查 location 是否存在
        # 執行 location policy 檢查
        policy_check = policy_service.check_location_policy(
            company_id=company_id,
            latitude=request.location.latitude,
            longitude=request.location.longitude
        )
```

### 2. 資料庫欄位

**表名：** `attendance_punches`  
**GPS 欄位：**
- `location_lat` (DOUBLE PRECISION) - 緯度
- `location_lng` (DOUBLE PRECISION) - 經度
- `location_id` (UUID) - 匹配的允許地點 ID（若有 policy）

**證據：**
```sql
SELECT 
    id, 
    punch_type, 
    punch_time, 
    location_lat,  -- ← GPS 緯度欄位
    location_lng,  -- ← GPS 經度欄位
    notes,
    created_at
FROM attendance_punches 
WHERE punch_type IN ('break_start', 'break_end')
ORDER BY created_at DESC 
LIMIT 10
```

### 3. 資料庫實際數據

**查詢結果（2026-03-09 11:26）：**

最近 10 筆外出/返回記錄：

| ID | 類型 | 時間 | GPS Lat | GPS Lng | 備註 |
|----|------|------|---------|---------|------|
| 6eb8955a... | break_start | 2026-03-09 11:20:46 | **None** | **None** | 外出洽公112 |
| 897c5b99... | break_start | 2026-03-09 10:52:38 | **None** | **None** | 客戶訪問 |
| 1bf0df89... | break_start | 2026-03-09 09:17:36 | **None** | **None** | 拜訪客戶 |
| 30c03945... | break_start | 2026-03-09 09:17:29 | **None** | **None** | 外出洽公 |
| 2767e440... | break_end | 2026-03-08 22:25:16 | **None** | **None** | |
| 37b21b33... | break_start | 2026-03-08 22:25:15 | **None** | **None** | 銀行辦事 |

**結論：** ✅ 所有記錄的 GPS 欄位都是 `None`，證實 GPS 未被保存

---

## 主機 Log / DB 檢查結果

### 1. 後端服務狀態

**運行方式：** uvicorn  
**進程：**
```
root  1361373  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**狀態：** ✅ 正常運行

### 2. API 請求日誌

**最近的 break-out 請求：**
```
INFO: 192.168.88.235:0 - "POST /api/v1/attendance/break-out HTTP/1.1" 201 Created
```

**狀態碼：** 201 Created  
**結論：** ✅ 請求成功，但 GPS 未保存（因為欄位名稱不匹配）

### 3. 資料庫查詢證據

**SQL 查詢：**
```sql
SELECT location_lat, location_lng, notes, created_at
FROM attendance_punches 
WHERE punch_type = 'break_start'
ORDER BY created_at DESC 
LIMIT 10
```

**結果：** 所有 `location_lat` 和 `location_lng` 都是 `NULL`

---

## 白色視窗來源分析

### 可能的白色視窗來源

根據代碼檢查，前端有以下可能顯示的元素：

#### 1. Error Toast（最可能）
**檔案：** `Home.vue` line 297-309  
**觸發條件：** `showErrorMessage === true`

```vue
<div 
  v-if="showErrorMessage" 
  class="error-toast fixed bottom-8 right-8 bg-error text-white px-6 py-3 rounded-lg shadow-xl z-50 max-w-md"
>
  <div class="flex items-start gap-2">
    <svg class="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
      <path fill-rule="evenodd" d="..." clip-rule="evenodd" />
    </svg>
    <span>{{ errorMessage }}</span>
  </div>
</div>
```

**樣式：**
- 背景：`bg-error`（紅色）
- 文字：`text-white`（白色）
- 位置：右下角固定
- z-index: 50

#### 2. Success Toast
**檔案：** `Home.vue` line 289-295  
**觸發條件：** `showSuccessMessage === true`

```vue
<div 
  v-if="showSuccessMessage" 
  class="success-toast fixed bottom-8 right-8 bg-success text-white px-6 py-3 rounded-lg shadow-xl z-50"
>
  ✓ {{ successMessage }}
</div>
```

#### 3. 編輯對話框
**檔案：** `Home.vue` line 311-343  
**觸發條件：** `showEditDialog === true`

```vue
<div v-if="showEditDialog" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
  <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md mx-4">
    <h3 class="text-lg font-semibold text-text-primary mb-4">編輯外出原因</h3>
    <!-- ... -->
  </div>
</div>
```

### 白色視窗的真實身份

**最可能的情況：**

由於前端發送的 GPS 欄位名稱錯誤（`gps` 而非 `location`），後端：
1. 接收到請求，但 `location` 為 `None`
2. 跳過 location policy 檢查（因為沒有 location）
3. 成功創建打卡記錄（201 Created）
4. 前端收到成功響應
5. 顯示 **Success Toast**（綠色背景，白色文字）

**但是：**

如果用戶在手機上看到的是「白色視窗」，可能是：

1. **Success Toast 在某些手機上顯示異常**
   - CSS 變數 `--success` 可能在某些環境下未正確載入
   - 導致背景變成白色或透明
   - 文字仍是白色，所以看不到內容

2. **瀏覽器的 GPS 權限提示**
   - 當 `navigator.geolocation.getCurrentPosition()` 被調用時
   - 瀏覽器會彈出原生權限提示
   - 某些手機瀏覽器的提示可能是白色背景

3. **Loading 狀態**
   - `isLoading` 為 true 時可能有 loading overlay
   - 但代碼中沒有全屏 loading overlay

### 為何內容看不到

**最可能原因：**

Success Toast 的 CSS 變數問題：
```css
.success-toast {
  background-color: var(--success);  /* 如果未定義，可能是白色 */
  color: white;  /* 白色文字 */
}
```

如果 `--success` 變數未正確載入或在手機上失效：
- 背景變成白色（預設值）
- 文字也是白色
- 結果：白色背景 + 白色文字 = 看不到內容

---

## 初步根因判斷

### 🔴 主要問題：GPS 欄位名稱不匹配

**前端：**
```javascript
{ notes: "...", gps: { latitude, longitude, ... } }
```

**後端：**
```python
{ notes: "...", location: { latitude, longitude } }
```

**影響：**
1. GPS 數據未被後端接收
2. 所有外出打卡記錄的 GPS 都是 `NULL`
3. Location policy 檢查被跳過（因為沒有 location）
4. 但打卡仍然成功（因為 location 是 optional）

### 🟡 次要問題：白色視窗

**可能原因：**
1. Success Toast 的 CSS 變數在手機上未正確載入
2. 或者是瀏覽器的 GPS 權限提示（但這不是我們的代碼）

---

## 下一步建議

### 1. 修復 GPS 欄位名稱（優先）

**方案 A：修改前端（推薦）**
```javascript
// Home.vue
await attendanceStore.punchWithLocation('BREAK_OUT', {
  notes: breakOutReason.value.trim(),
  location: gpsData  // ← 改為 location
})
```

**方案 B：修改後端**
```python
# schemas.py
class BreakOutRequest(BaseModel):
    notes: Optional[str] = None
    gps: Optional[LocationData] = None  # ← 改為 gps
```

**推薦方案 A**，因為：
- 後端 schema 已經在多處使用 `location`
- 前端只需要改一個地方
- 符合後端既有的命名慣例

### 2. 修復白色視窗問題

**檢查 CSS 變數定義：**
```css
/* 確保 --success 變數在所有環境下都有定義 */
:root {
  --success: #10b981;  /* 綠色 */
  --error: #ef4444;    /* 紅色 */
}
```

**或使用直接顏色值：**
```vue
<div class="success-toast ... bg-green-500 text-white">
  ✓ {{ successMessage }}
</div>
```

### 3. 驗證修復

修復後需要驗證：
1. 手機外出打卡時，GPS 是否正確取得
2. 資料庫中 `location_lat` 和 `location_lng` 是否有值
3. Success Toast 是否正常顯示（綠色背景，白色文字）
4. 外出紀錄列表中是否顯示 Google Maps 連結

---

## 證據總結

### ✅ 確認的事實

1. **前端 GPS 流程正常**
   - `useLocation` composable 實作正確
   - `getCurrentLocation()` 會正確調用 `navigator.geolocation`
   - 只有外出打卡會要求 GPS（Mobile only）

2. **後端 API 正常運行**
   - Break-out endpoint 正常響應（201 Created）
   - Schema 定義正確（使用 `location` 欄位）
   - 資料庫欄位存在（`location_lat`, `location_lng`）

3. **GPS 未被保存**
   - 資料庫查詢證實：所有記錄的 GPS 都是 `NULL`
   - 最近 10 筆外出打卡記錄都沒有 GPS 數據

4. **欄位名稱不匹配**
   - 前端發送 `gps`
   - 後端期望 `location`
   - 導致 GPS 數據被忽略

### 🔍 需要進一步確認

1. **白色視窗的真實身份**
   - 是 Success Toast？
   - 是瀏覽器 GPS 權限提示？
   - 是其他元素？

2. **前端是否真的取得了 GPS**
   - 需要在手機上實際測試
   - 檢查 console.log 輸出
   - 確認 `gpsData` 是否有值

---

## 結論

**Most likely failure layer:** 🔴 **前端與後端之間的 API 契約不一致**

- 前端發送 `gps` 欄位
- 後端期望 `location` 欄位
- 導致 GPS 數據未被接收和保存

**修復優先級：**
1. 🔴 **高優先**：修復 GPS 欄位名稱不匹配
2. 🟡 **中優先**：修復白色視窗顯示問題
3. 🟢 **低優先**：優化錯誤提示和用戶體驗

