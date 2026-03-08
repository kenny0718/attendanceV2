# Attendance Location API Contract

**版本**: 1.0  
**日期**: 2026-03-08  
**狀態**: 文件化現有 API  
**票號**: WP-11-12

---

## 執行摘要

本文件記錄現有的 OUT checkpoint API contract，確保 `useLocation` 實作時保持向後相容。此文件不定義新 API，僅文件化現有實作。

---

## OUT Checkpoint API

### Endpoint

```
POST /v1/attendance/out-checkpoint
```

### 認證

```
Authorization: Bearer <jwt_token>
```

### Request

#### Headers

```
Content-Type: application/json
Authorization: Bearer <jwt_token>
```

#### Body Schema

```typescript
interface OutCheckpointRequest {
  device_type: 'mobile' | 'pc'
  gps?: GPSData
  notes?: string
  client_timezone?: string
}

interface GPSData {
  latitude: number        // -90 to 90
  longitude: number       // -180 to 180
  accuracy?: number       // meters, >= 0
  captured_at?: string    // ISO 8601
  provider?: 'gps' | 'network' | 'fused'
}
```

#### 驗證規則

| 欄位 | 必填 | 規則 |
|------|------|------|
| device_type | ✅ | 'mobile' 或 'pc' |
| gps | ⚠️ | mobile 必填，pc 選填 |
| gps.latitude | ✅ | -90 ≤ lat ≤ 90 |
| gps.longitude | ✅ | -180 ≤ lng ≤ 180 |
| gps.accuracy | ❌ | >= 0 |
| gps.captured_at | ❌ | ISO 8601 格式 |
| gps.provider | ❌ | 'gps', 'network', 或 'fused' |
| notes | ❌ | 最大 500 字元 |
| client_timezone | ❌ | 最大 50 字元 |

#### Request 範例

**Mobile 裝置**:
```json
{
  "device_type": "mobile",
  "gps": {
    "latitude": 25.0330,
    "longitude": 121.5654,
    "accuracy": 10.5,
    "captured_at": "2026-03-08T10:30:00.000Z",
    "provider": "gps"
  },
  "notes": "外出洽公",
  "client_timezone": "Asia/Taipei"
}
```

**PC 裝置**:
```json
{
  "device_type": "pc",
  "notes": "外出洽公"
}
```

---

### Response

#### Success (201 Created)

```typescript
interface OutCheckpointResponse {
  checkpoint_id: string    // UUID
  punch_time: string       // ISO 8601, server-set
  gps?: GPSData
  message: string
}
```

**範例**:
```json
{
  "checkpoint_id": "550e8400-e29b-41d4-a716-446655440000",
  "punch_time": "2026-03-08T10:30:15.123Z",
  "gps": {
    "latitude": 25.0330,
    "longitude": 121.5654,
    "accuracy": 10.5,
    "captured_at": "2026-03-08T10:30:00.000Z",
    "provider": "gps"
  },
  "message": "Checkpoint recorded successfully"
}
```

---

#### Error Responses

##### 400 Bad Request

**原因**: 請求參數錯誤

```json
{
  "error": "請求參數錯誤",
  "error_code": "BAD_REQUEST"
}
```

---

##### 403 Forbidden

**原因**: 無權限或租戶無效

```json
{
  "error": "無權限/租戶無效，請重新登入或確認公司",
  "error_code": "FORBIDDEN"
}
```

---

##### 409 Conflict

**原因**: 重複打點（短時間/近距離）

```json
{
  "error": "請勿重複打點（短時間/近距離）",
  "error_code": "DUPLICATE_CHECKPOINT",
  "last_checkpoint_time": "2026-03-08T10:25:00.000Z"
}
```

**去重邏輯**:
- 時間間隔 < 5 分鐘
- 距離 < 50 公尺（如果有 GPS）

---

##### 422 Unprocessable Entity

**原因**: Mobile 裝置未提供 GPS

```json
{
  "error": "請開啟定位後再外出打點",
  "error_code": "GPS_REQUIRED"
}
```

**觸發條件**:
- `device_type === 'mobile'`
- `gps` 欄位為 null 或 undefined

---

##### 500 Internal Server Error

**原因**: 伺服器錯誤

```json
{
  "error": "伺服器或網路異常，請稍後重試",
  "error_code": "INTERNAL_ERROR"
}
```

---

## 錯誤碼對照表

### 後端錯誤碼

| HTTP Status | error_code | 說明 | 前端處理 |
|-------------|-----------|------|---------|
| 400 | BAD_REQUEST | 請求參數錯誤 | 顯示錯誤訊息 |
| 403 | FORBIDDEN | 無權限 | 提示重新登入 |
| 409 | DUPLICATE_CHECKPOINT | 重複打點 | 顯示錯誤訊息 |
| 422 | GPS_REQUIRED | GPS 必填 | 提示開啟定位 |
| 500 | INTERNAL_ERROR | 伺服器錯誤 | 提示稍後重試 |

### 前端錯誤碼（LocationError）

| LocationErrorCode | 說明 | 對應瀏覽器錯誤 |
|------------------|------|---------------|
| NOT_SUPPORTED | 不支援定位 | - |
| PERMISSION_DENIED | 權限拒絕 | GeolocationPositionError.PERMISSION_DENIED (1) |
| POSITION_UNAVAILABLE | 定位無法取得 | GeolocationPositionError.POSITION_UNAVAILABLE (2) |
| TIMEOUT | 請求逾時 | GeolocationPositionError.TIMEOUT (3) |
| UNKNOWN | 未知錯誤 | - |

---

## 錯誤訊息對照表

### 後端錯誤訊息

| error_code | 中文訊息 | 英文訊息 |
|-----------|---------|---------|
| DUPLICATE_CHECKPOINT | 請勿重複打點（短時間/近距離） | Duplicate checkpoint (too soon/too close) |
| GPS_REQUIRED | 請開啟定位後再外出打點 | GPS is required for mobile devices |
| FORBIDDEN | 無權限/租戶無效，請重新登入或確認公司 | Forbidden / Invalid tenant |
| BAD_REQUEST | 請求參數錯誤 | Bad request |
| INTERNAL_ERROR | 伺服器或網路異常，請稍後重試 | Internal server error |

### 前端錯誤訊息（LocationError）

| LocationErrorCode | 中文訊息 | 英文訊息 |
|------------------|---------|---------|
| NOT_SUPPORTED | 此裝置不支援定位功能 | Geolocation is not supported |
| PERMISSION_DENIED | 請開啟定位權限後再外出打點 | Location permission denied |
| POSITION_UNAVAILABLE | 定位資訊無法取得 | Position unavailable |
| TIMEOUT | 定位請求逾時 | Location request timeout |
| UNKNOWN | 無法獲取定位 | Unable to get location |

---

## Payload 格式規範

### GPS Data 格式

```typescript
interface GPSData {
  latitude: number        // 必填，-90 to 90
  longitude: number       // 必填，-180 to 180
  accuracy?: number       // 選填，meters, >= 0
  captured_at?: string    // 選填，ISO 8601
  provider?: string       // 選填，'gps' | 'network' | 'fused'
}
```

### 座標精度

- **latitude**: 小數點後 8 位（約 1.1mm 精度）
- **longitude**: 小數點後 8 位（約 1.1mm 精度）
- **accuracy**: 小數點後 2 位（公尺）

### 時間格式

- **ISO 8601**: `YYYY-MM-DDTHH:mm:ss.sssZ`
- **時區**: UTC (Z)
- **範例**: `2026-03-08T10:30:00.000Z`

---

## 向後相容保證

### WP-11-12 保證

在 WP-11-12 實作 `useLocation` 時：

✅ **保持不變**:
- Request payload 格式
- Response payload 格式
- 錯誤碼
- 錯誤訊息
- 驗證規則
- HTTP status codes

❌ **不修改**:
- 後端 API
- 後端 schema
- 資料庫 model
- 驗證邏輯

### 未來可能變更（WP-11-13+）

⚠️ **可能新增**（不破壞現有功能）:
- 新的 GPS provider 類型
- 新的驗證規則（geofencing）
- 新的錯誤碼（policy 相關）
- 新的選填欄位

⚠️ **不會移除**:
- 現有欄位
- 現有錯誤碼
- 現有驗證規則

---

## 測試案例

### 正常流程

#### Test Case 1: Mobile 裝置提交（有 GPS）

**Request**:
```json
{
  "device_type": "mobile",
  "gps": {
    "latitude": 25.0330,
    "longitude": 121.5654,
    "accuracy": 10.5,
    "captured_at": "2026-03-08T10:30:00.000Z",
    "provider": "gps"
  },
  "notes": "外出洽公"
}
```

**Expected Response**: 201 Created
```json
{
  "checkpoint_id": "...",
  "punch_time": "...",
  "gps": { ... },
  "message": "Checkpoint recorded successfully"
}
```

---

#### Test Case 2: PC 裝置提交（無 GPS）

**Request**:
```json
{
  "device_type": "pc",
  "notes": "外出洽公"
}
```

**Expected Response**: 201 Created
```json
{
  "checkpoint_id": "...",
  "punch_time": "...",
  "message": "Checkpoint recorded successfully"
}
```

---

### 錯誤流程

#### Test Case 3: Mobile 裝置未提供 GPS

**Request**:
```json
{
  "device_type": "mobile",
  "notes": "外出洽公"
}
```

**Expected Response**: 422 Unprocessable Entity
```json
{
  "error": "請開啟定位後再外出打點",
  "error_code": "GPS_REQUIRED"
}
```

---

#### Test Case 4: 重複打點

**Precondition**: 5 分鐘內已有打點記錄

**Request**:
```json
{
  "device_type": "mobile",
  "gps": {
    "latitude": 25.0330,
    "longitude": 121.5654,
    "accuracy": 10.5,
    "captured_at": "2026-03-08T10:30:00.000Z",
    "provider": "gps"
  },
  "notes": "外出洽公"
}
```

**Expected Response**: 409 Conflict
```json
{
  "error": "請勿重複打點（短時間/近距離）",
  "error_code": "DUPLICATE_CHECKPOINT",
  "last_checkpoint_time": "2026-03-08T10:25:00.000Z"
}
```

---

#### Test Case 5: 無效座標

**Request**:
```json
{
  "device_type": "mobile",
  "gps": {
    "latitude": 91.0,  // 超出範圍
    "longitude": 121.5654,
    "accuracy": 10.5,
    "captured_at": "2026-03-08T10:30:00.000Z",
    "provider": "gps"
  },
  "notes": "外出洽公"
}
```

**Expected Response**: 400 Bad Request
```json
{
  "error": "請求參數錯誤",
  "error_code": "BAD_REQUEST"
}
```

---

## 前端實作指引

### 組裝 Payload

```javascript
import { useLocation } from '@/composables/useLocation'

async function submitOutCheckpoint(reason) {
  const { getLocationIfRequired, deviceType } = useLocation()
  
  // 基本 payload
  const payload = {
    device_type: deviceType.value,
    notes: reason
  }
  
  // 獲取 GPS（如果需要）
  try {
    const gps = await getLocationIfRequired()
    if (gps) {
      payload.gps = gps
    }
  } catch (error) {
    // LocationError 會自動拋出
    throw error
  }
  
  // 提交
  return await api.post('/v1/attendance/out-checkpoint', payload)
}
```

### 錯誤處理

```javascript
try {
  await submitOutCheckpoint('外出洽公')
} catch (error) {
  // LocationError（前端）
  if (error instanceof LocationError) {
    switch (error.code) {
      case LocationErrorCode.PERMISSION_DENIED:
        showError('請開啟定位權限後再外出打點')
        break
      case LocationErrorCode.TIMEOUT:
        showError('定位請求逾時')
        break
      default:
        showError(error.message)
    }
    return
  }
  
  // API Error（後端）
  if (error.status) {
    switch (error.status) {
      case 409:
        if (error.data?.error_code === 'DUPLICATE_CHECKPOINT') {
          showError('請勿重複打點（短時間/近距離）')
        }
        break
      case 422:
        if (error.data?.error_code === 'GPS_REQUIRED') {
          showError('請開啟定位後再外出打點')
        }
        break
      default:
        showError(error.message || '操作失敗')
    }
  }
}
```

---

## 安全考量

### 資料驗證

**前端**:
- 驗證座標範圍
- 驗證時間格式
- 驗證欄位類型

**後端**:
- 再次驗證所有欄位
- 不信任前端資料
- SQL injection 防護
- XSS 防護

### 隱私保護

- GPS 資料使用 HTTPS 傳輸
- 不在前端長期儲存 GPS 資料
- 後端 GPS 資料加密儲存
- 符合 GDPR 要求

### 權限控制

- JWT 認證
- Tenant isolation
- 使用者只能提交自己的打點
- 管理員可查看所有打點

---

## 效能考量

### Request Size

- 典型 payload: ~200 bytes
- 最大 payload: ~1KB
- 壓縮: gzip

### Response Time

- P50: < 200ms
- P95: < 500ms
- P99: < 1s

### Rate Limiting

- 每使用者: 10 requests / minute
- 每 IP: 100 requests / minute

---

## 監控與日誌

### 關鍵指標

- 請求成功率
- 平均回應時間
- 錯誤率（按錯誤碼分類）
- GPS 資料品質（精度分布）

### 日誌記錄

**記錄**:
- 請求時間
- 使用者 ID
- 裝置類型
- GPS 精度
- 錯誤碼

**不記錄**:
- 完整 GPS 座標（隱私）
- JWT token
- 敏感資訊

---

## 參考資料

- [Backend Schema](../backend/app/modules/attendance/schemas.py)
- [Backend API](../backend/app/modules/attendance/api.py)
- [Frontend API Client](../frontend/src/api/attendance.js)
- [ATTENDANCE_LOCATION_MODULE_SPEC.md](./ATTENDANCE_LOCATION_MODULE_SPEC.md)

---

**版本歷史**:
- v1.0 (2026-03-08): 初始版本，文件化現有 API
