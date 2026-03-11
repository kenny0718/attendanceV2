# Attendance GPS Legacy Inventory

**建立日期**: 2026-03-08  
**目的**: 在實作新的 shared location module 前，盤點所有舊 GPS 相關實作，避免新舊流程衝突

---

## 執行摘要

本次盤點發現：
- **前端有完整的舊 GPS 流程**：`attendance.js` store 中包含 `getGPSLocation()` 和 `detectDeviceType()` 方法
- **後端已有基礎 GPS 能力**：`gps_utils.py` 提供距離計算，`AttendanceOutCheckpoint` model 支援 GPS 儲存
- **OUT checkpoint 功能已實作**：WP-11-11 已完成，但前端 GPS 邏輯耦合在 store 中
- **需要清理的主要問題**：前端 GPS 邏輯分散、錯誤處理不統一、缺乏可重用的 location module

---

## 1. 前端直接 GPS 呼叫點

### 1.1 Store 層 GPS 方法

**檔案**: `frontend/src/stores/attendance.js`

#### `getGPSLocation()` 方法 (行 219-256)
```javascript
async getGPSLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('此裝置不支援定位功能'))
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
        let errorMessage = '無法獲取定位'
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = '請開啟定位權限後再外出打點'
            break
          case error.POSITION_UNAVAILABLE:
            errorMessage = '定位資訊無法取得'
            break
          case error.TIMEOUT:
            errorMessage = '定位請求逾時'
            break
        }
        reject(new Error(errorMessage))
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    )
  })
}
```

**分析**:
- ✅ 實作完整，包含錯誤處理
- ❌ 耦合在 attendance store，無法被其他模組重用
- ❌ 錯誤訊息寫死在 store 中
- ❌ 沒有 loading state 管理
- ❌ 沒有 retry 機制

#### `detectDeviceType()` 方法 (行 213-217)
```javascript
detectDeviceType() {
  const userAgent = navigator.userAgent || ''
  const isMobile = /Mobile|Android|iPhone|iPad|iPod/i.test(userAgent)
  return isMobile ? 'mobile' : 'pc'
}
```

**分析**:
- ✅ 簡單實用
- ❌ 耦合在 attendance store
- ❌ 可能需要更精確的裝置判斷邏輯

---

### 1.2 Store 層 GPS 使用點

**檔案**: `frontend/src/stores/attendance.js`

#### `outCheckpointSubmit()` 方法 (行 175-211)
```javascript
async outCheckpointSubmit(reasonText) {
  // ...
  const deviceType = this.detectDeviceType()
  
  const payload = {
    device_type: deviceType,
    notes: reasonText.trim()
  }
  
  if (deviceType === 'mobile') {
    const gpsData = await this.getGPSLocation()  // ← 直接呼叫
    payload.gps = gpsData
  }
  
  const response = await attendanceApi.createOutCheckpoint(payload)
  // ...
}
```

**分析**:
- ❌ GPS 邏輯與業務邏輯混在一起
- ❌ 錯誤處理依賴 try-catch，不夠細緻
- ❌ 沒有 GPS loading 狀態的獨立管理

---

### 1.3 頁面層 GPS 依賴

**檔案**: `frontend/src/views/Home.vue`

#### Device Type 顯示 (行 139-141)
```vue
<span v-if="deviceType === 'pc'" class="text-xs text-text-hint ml-2">(PC 不記錄定位)</span>
<span v-else class="text-xs text-text-hint ml-2">(需要定位權限)</span>
```

#### Device Type 初始化 (行 464-465)
```javascript
onMounted(() => {
  // ...
  deviceType.value = attendanceStore.detectDeviceType()
  // ...
})
```

**分析**:
- ❌ 頁面直接依賴 store 的 device type 判斷
- ❌ UI 提示寫死在頁面中
- ⚠️ 有多個備份檔案 (Home.vue.tmp, Home.vue.before_fix, Home.vue.backup) 包含相同邏輯

---

## 2. API Client 對 GPS Payload 的處理

**檔案**: `frontend/src/api/attendance.js`

### OUT Checkpoint API (行 27-29)
```javascript
// 創建 OUT checkpoint
createOutCheckpoint: (data) => apiClient.post('/v1/attendance/out-checkpoint', data),
```

**分析**:
- ✅ API client 層很乾淨，只負責發送請求
- ✅ GPS payload 組裝在 store 層，符合職責分離
- ⚠️ 但 store 層組裝邏輯應該移到 shared module

---

## 3. 後端 GPS 相關實作

### 3.1 GPS 工具函式

**檔案**: `backend/app/modules/attendance/gps_utils.py`

**功能**:
- `calculate_distance()`: Haversine 公式計算兩點距離
- `is_within_distance()`: 判斷兩點是否在指定距離內

**分析**:
- ✅ **KEEP**: 這是可重用的基礎工具，應該保留
- ✅ 實作正確，有完整的 docstring
- ✅ 用於 OUT checkpoint 的去重邏輯

---

### 3.2 GPS Schema 定義

**檔案**: `backend/app/modules/attendance/schemas.py`

#### `GPSData` Schema (行 135-142)
```python
class GPSData(BaseModel):
    """GPS data for checkpoint events"""
    latitude: float = Field(..., ge=-90, le=90, description="緯度")
    longitude: float = Field(..., ge=-180, le=180, description="經度")
    accuracy: Optional[float] = Field(None, ge=0, description="GPS 精度 (公尺)")
    captured_at: Optional[datetime] = Field(None, description="GPS 擷取時間")
    provider: Optional[str] = Field(None, pattern="^(gps|network|fused)$", description="GPS 提供者")
```

#### `OutCheckpointRequest` Schema (行 145-159)
```python
class OutCheckpointRequest(BaseModel):
    device_type: str = Field(..., pattern="^(mobile|pc)$", description="裝置類型 (mobile|pc)")
    gps: Optional[GPSData] = Field(None, description="GPS 資料 (mobile 必填, pc 選填)")
    notes: Optional[str] = Field(None, max_length=500, description="備註")
    client_timezone: Optional[str] = Field(None, max_length=50, description="客戶端時區")
    
    @validator('gps')
    def validate_gps_for_mobile(cls, v, values):
        """Validate that mobile devices provide GPS"""
        if values.get('device_type') == 'mobile' and not v:
            raise ValueError('請開啟定位後再外出打卡')
        return v
```

**分析**:
- ✅ **KEEP**: Schema 定義清晰，驗證邏輯正確
- ✅ 已經實作 mobile 必須提供 GPS 的驗證
- ⚠️ 錯誤訊息 "請開啟定位後再外出打卡" 應該統一管理

---

### 3.3 GPS Model 定義

**檔案**: `backend/app/modules/attendance/models.py`

#### `AttendanceOutCheckpoint` Model (行 200-260)
```python
class AttendanceOutCheckpoint(Base):
    """外出打卡點模型 (WP-11-10)"""
    __tablename__ = "attendance_out_checkpoints"
    
    # GPS Data (MANDATORY for mobile, OPTIONAL for pc)
    gps_lat = Column(Numeric(10, 8), nullable=True, comment='緯度 (required for mobile)')
    gps_lng = Column(Numeric(11, 8), nullable=True, comment='經度 (required for mobile)')
    gps_accuracy_m = Column(Numeric(8, 2), nullable=True, comment='GPS 精度 (公尺)')
    gps_captured_at = Column(DateTime(timezone=True), nullable=True, comment='GPS 擷取時間 (client-side timestamp)')
    gps_provider = Column(String(20), nullable=True, comment='GPS 提供者 (gps|network|fused)')
    device_type = Column(String(20), nullable=False, comment='裝置類型 (mobile|pc)')
    # ...
```

**分析**:
- ✅ **KEEP**: 資料模型設計合理
- ✅ 支援 GPS 資料儲存
- ✅ 有適當的索引和約束

---

### 3.4 GPS Repository 方法

**檔案**: `backend/app/modules/attendance/repo.py`

**方法**: `create_out_checkpoint()` (推測，未完整讀取)

**分析**:
- ✅ **KEEP**: Repository 層負責資料存取，應該保留
- ⚠️ 需要確認是否有其他 GPS 相關的查詢方法

---

## 4. 測試檔中與 GPS 綁定的案例

**檔案**: `backend/app/modules/attendance/tests/test_out_checkpoint.py`

**發現**:
- 包含 `GPS_REQUIRED` 錯誤碼的測試
- 測試 mobile 裝置必須提供 GPS 的驗證邏輯

**分析**:
- ✅ **KEEP**: 測試應該保留，確保 GPS 驗證邏輯正確
- ⚠️ 如果前端 GPS 流程改變，可能需要更新測試案例

---

## 5. 錯誤碼與訊息 Mapping

### 5.1 前端錯誤處理

**檔案**: `frontend/src/stores/attendance.js`

#### `handleError()` 方法 (行 327-378)
```javascript
handleError(error) {
  let errorMessage = '操作失敗'
  let errorCode = null
  
  if (error.status) {
    errorCode = error.status
    
    switch (error.status) {
      case 409:
        if (error.data?.detail?.error_code === 'DUPLICATE_CHECKPOINT') {
          errorMessage = '請勿重複打點（短時間/近距離）'
        } else if (error.data?.detail?.error_code === 'ALREADY_ON_BREAK') {
          errorMessage = '已經在外出狀態，請先返回打卡'
        } else if (error.data?.detail?.error_code === 'NOT_ON_BREAK') {
          errorMessage = '目前不在外出狀態，請先外出打卡'
        } else {
          errorMessage = error.message || '已有打開的打卡記錄，請勿重複打卡'
        }
        break
        
      case 422:
        if (error.data?.detail?.error_code === 'GPS_REQUIRED') {
          errorMessage = '請開啟定位後再外出打點'
        } else {
          errorMessage = error.message || '請求參數錯誤'
        }
        break
      // ...
    }
  } else if (error.message) {
    if (error.message.includes('網絡') || error.message.includes('Network') || error.message.includes('網路')) {
      errorMessage = '網路連線失敗，請檢查網路設定'
    } else {
      errorMessage = error.message
    }
  }
  
  return {
    message: errorMessage,
    code: errorCode,
    originalError: error
  }
}
```

**分析**:
- ❌ 錯誤訊息寫死在 store 中，不利於維護
- ❌ `GPS_REQUIRED` 錯誤碼處理應該移到 shared location module
- ❌ 錯誤處理邏輯過於複雜，應該簡化

### 5.2 GPS 特定錯誤訊息

**位置**: `getGPSLocation()` 方法內

```javascript
switch (error.code) {
  case error.PERMISSION_DENIED:
    errorMessage = '請開啟定位權限後再外出打點'
    break
  case error.POSITION_UNAVAILABLE:
    errorMessage = '定位資訊無法取得'
    break
  case error.TIMEOUT:
    errorMessage = '定位請求逾時'
    break
}
```

**分析**:
- ❌ GPS 錯誤訊息應該統一管理
- ❌ 應該移到 shared location module 的 error handler

---

## 6. 備份檔案與死碼

### 6.1 前端備份檔案

發現以下備份檔案包含相同的 GPS 邏輯：
- `frontend/src/views/Home.vue.tmp`
- `frontend/src/views/Home.vue.before_fix`
- `frontend/src/views/Home.vue.backup`

**分析**:
- ❌ **REMOVE**: 這些備份檔案應該刪除，避免混淆

### 6.2 後端 API 檔案

**檔案**: `backend/app/modules/attendance/api.py`

**狀態**: 檔案為空 (只有 1 行)

**分析**:
- ⚠️ **VERIFY**: 需要確認 OUT checkpoint API 實作在哪裡
- 可能在其他檔案或已被重構

---

## 7. 依賴關係圖

```
前端 GPS 流程:
┌─────────────────────────────────────────────────────────────┐
│ Home.vue                                                     │
│  ├─ deviceType = detectDeviceType()                         │
│  └─ handleOutCheckpoint()                                   │
│      └─ attendanceStore.outCheckpointSubmit(reason)         │
│          └─ attendance.js (store)                           │
│              ├─ detectDeviceType()                          │
│              ├─ getGPSLocation() ← navigator.geolocation    │
│              ├─ handleError() ← GPS_REQUIRED mapping        │
│              └─ attendanceApi.createOutCheckpoint(payload)  │
│                  └─ attendance.js (api client)              │
│                      └─ POST /v1/attendance/out-checkpoint  │
└─────────────────────────────────────────────────────────────┘

後端 GPS 流程:
┌─────────────────────────────────────────────────────────────┐
│ POST /v1/attendance/out-checkpoint                          │
│  └─ OutCheckpointRequest (schema)                           │
│      ├─ validate_gps_for_mobile() ← GPS_REQUIRED           │
│      └─ GPSData (schema)                                    │
│          └─ AttendanceOutCheckpoint (model)                 │
│              ├─ gps_lat, gps_lng, gps_accuracy_m           │
│              └─ device_type                                 │
│                  └─ gps_utils.py                            │
│                      └─ calculate_distance() (去重邏輯)      │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. 總結與建議

### 8.1 必須保留 (KEEP)

| 項目 | 檔案 | 原因 |
|------|------|------|
| GPS 工具函式 | `backend/app/modules/attendance/gps_utils.py` | 可重用的基礎能力 |
| GPS Schema | `backend/app/modules/attendance/schemas.py` | 資料契約定義 |
| GPS Model | `backend/app/modules/attendance/models.py` | 資料儲存結構 |
| GPS Repository | `backend/app/modules/attendance/repo.py` | 資料存取層 |
| GPS 測試 | `backend/app/modules/attendance/tests/test_out_checkpoint.py` | 確保功能正確 |

### 8.2 必須移除 (REMOVE)

| 項目 | 檔案 | 原因 |
|------|------|------|
| 備份檔案 | `frontend/src/views/Home.vue.{tmp,before_fix,backup}` | 死碼，造成混淆 |

### 8.3 必須重構 (REFACTOR)

| 項目 | 檔案 | 原因 | 目標 |
|------|------|------|------|
| `getGPSLocation()` | `frontend/src/stores/attendance.js` | 耦合在 store，無法重用 | 移到 `composables/useLocation.js` |
| `detectDeviceType()` | `frontend/src/stores/attendance.js` | 耦合在 store | 移到 `utils/device.js` 或 `useLocation` |
| GPS 錯誤處理 | `frontend/src/stores/attendance.js` | 錯誤訊息分散 | 統一到 location module |
| `outCheckpointSubmit()` | `frontend/src/stores/attendance.js` | GPS 邏輯與業務邏輯混合 | 使用 `useLocation` composable |

### 8.4 需要驗證 (VERIFY)

| 項目 | 檔案 | 問題 |
|------|------|------|
| OUT checkpoint API | `backend/app/modules/attendance/api.py` | 檔案為空，需確認實作位置 |
| Break punches API | `frontend/src/api/attendance.js` | 是否與 OUT checkpoint 重複？ |
| GPS 錯誤碼 | 前後端 | `GPS_REQUIRED` 是否統一？ |

### 8.5 需要統一命名 (RENAME)

| 項目 | 現況 | 建議 |
|------|------|------|
| 錯誤碼 | `GPS_REQUIRED` | 統一為 `LOCATION_REQUIRED` |
| GPS vs Location | 混用 | 統一使用 `location` |
| device_type | 前後端一致 | ✅ 已統一 |

---

## 9. 風險評估

### 9.1 高風險項目

1. **OUT checkpoint 功能已上線**: 不能直接刪除，需要漸進式重構
2. **前端 GPS 邏輯耦合**: 移除前需要先建立 adapter 層
3. **錯誤處理分散**: 需要確保新舊錯誤訊息一致

### 9.2 中風險項目

1. **備份檔案**: 刪除前需確認沒有未合併的程式碼
2. **測試依賴**: 重構後需要更新測試案例

### 9.3 低風險項目

1. **後端基礎能力**: 不需要改動，可以直接重用
2. **API contract**: 已經定義清楚，不需要改動

---

## 10. 下一步行動

參考 `ATTENDANCE_GPS_LEGACY_CLEANUP_PLAN.md` 進行具體的清理計劃。
