# API Documentation v2.1

**版本**: 2.0  
**日期**: 2026-03-09  
**狀態**: Draft (Partially Implemented)  
**基礎 URL**: `/api/v1`

---

## 變更摘要 (v1.0 → v2.1)

### 新增功能
- ✅ Location Policy / Geofence API (WP-11-13)
- ✅ Allowed Locations 管理端 CRUD
- ✅ BREAK_OUT 整合 Location Policy 驗證

### 新增錯誤碼
- `LOCATION_POLICY_VIOLATION` - 不在允許的打卡範圍內

---

## 目錄

1. [認證 API](#認證-api)
2. [考勤打卡 API](#考勤打卡-api)
3. **[Location Policy 管理 API](#location-policy-管理-api)** ⭐ 新增
4. [錯誤碼](#錯誤碼)
5. [通用規範](#通用規範)

---

## 認證 API

### 登入

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response 200**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user-123",
    "username": "user@example.com",
    "company_id": "company-456"
  }
}
```

---

## 考勤打卡 API

**Phase 1 Scope**: Location Policy currently only applies to BREAK_OUT flow.
Other punch flows (BREAK_IN, punch-in, punch-out) not yet integrated.

### BREAK_OUT (外出打點) ⭐ 已整合 Location Policy

```http
POST /api/v1/attendance/break-out
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "device_type": "mobile",
  "notes": "外出拜訪客戶",
  "gps": {
    "latitude": 25.0335,
    "longitude": 121.5660,
    "accuracy": 10,
    "captured_at": "2026-03-09T22:30:00+08:00",
    "provider": "gps"
  }
}
```

#### Request Body

| 欄位        | 類型   | 必填 | 說明                                    |
| ----------- | ------ | ---- | --------------------------------------- |
| device_type | string | ✅   | 裝置類型: `mobile` 或 `pc`              |
| notes       | string | ❌   | 外出原因                                |
| gps         | object | ⚠️   | GPS 資訊 (當公司啟用 location policy 時必填) |

#### GPS Object

| 欄位         | 類型   | 必填 | 說明                                |
| ------------ | ------ | ---- | ----------------------------------- |
| latitude     | float  | ✅   | 緯度 (-90 ~ 90)                     |
| longitude    | float  | ✅   | 經度 (-180 ~ 180)                   |
| accuracy     | float  | ✅   | 精度 (公尺)                         |
| captured_at  | string | ✅   | 定位時間 (ISO 8601 with timezone offset，如 2026-03-09T14:30:00Z 或 +08:00)（SA v2.1 §31.5） |
| provider     | string | ✅   | 定位來源: `gps`, `network`, `fused` |

#### Response 200 (成功)

```json
{
  "punch_id": "punch-789",
  "session_id": "session-123",
  "punch_type": "BREAK_OUT",
  "punch_time": "2026-03-09T14:30:00Z",
  "location_lat": 25.0335,
  "location_lng": 121.5660,
  "location_policy": {
    "allowed": true,
    "reason": "在允許的打卡範圍內：台北101工地",
    "matched_location": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "台北101工地",
      "distance_meters": 50
    }
  }
}
```

#### Response 403 (Location Policy Violation) ⭐ 新增

```json
{
  "error_code": "LOCATION_POLICY_VIOLATION",
  "message": "不在允許的打卡範圍內。最近的地點：台北101工地（距離 350 公尺）",
  "nearest_location": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "台北101工地",
    "distance_meters": 350
  }
}
```

#### Response 400 (GPS 必填但未提供)

**HTTP Status**: 400 Bad Request (用於 missing required data)

```json
{
  "error_code": "GPS_REQUIRED_FOR_LOCATION_POLICY",
  "message": "公司已啟用地點限制，必須提供 GPS 座標才能打卡",
  "policy_enabled": true,
  "allowed_locations_count": 3
}
```

**Note**: If company has enabled location policy (has allowed locations),
GPS is REQUIRED regardless of device type. Request will be rejected with
400 GPS_REQUIRED_FOR_LOCATION_POLICY if GPS is not provided.

---

## Location Policy 管理 API

### 1. 建立允許打卡地點

```http
POST /api/v1/admin/allowed-locations
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "台北101工地",
  "description": "台北101建案工地範圍",
  "location_type": "construction_site",
  "latitude": 25.0330,
  "longitude": 121.5654,
  "radius_meters": 200,
  "is_active": true
}
```

#### Request Body

| 欄位          | 類型    | 必填 | 說明                                                                 |
| ------------- | ------- | ---- | -------------------------------------------------------------------- |
| name          | string  | ✅   | 地點名稱 (最多 255 字元)                                             |
| description   | string  | ❌   | 地點描述                                                             |
| location_type | string  | ✅   | 地點類型: `office`, `construction_site`, `customer_site`, `temporary_site` |
| latitude      | float   | ✅   | 緯度 (-90 ~ 90)                                                      |
| longitude     | float   | ✅   | 經度 (-180 ~ 180)                                                    |
| radius_meters | integer | ✅   | 允許半徑（公尺，必須 > 0）                                           |
| is_active     | boolean | ❌   | 是否啟用 (預設: true)                                                |

#### Response 201

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "company_id": "company-123",
  "name": "台北101工地",
  "description": "台北101建案工地範圍",
  "location_type": "construction_site",
#### Response 422 (驗證錯誤)

**HTTP Status**: 422 Unprocessable Entity (用於 schema validation 錯誤)

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Validation failed",
  "errors": [
    {
      "field": "latitude",
      "message": "緯度必須在 -90 到 90 之間"
    },
    {
      "field": "radius_meters",
      "message": "半徑必須大於 0"
    }
  ]
}


---

### 2. 查詢允許地點列表

```http
GET /api/v1/admin/allowed-locations?is_active=true&limit=50&offset=0
Authorization: Bearer {access_token}
```

#### Query Parameters

| 參數      | 類型    | 必填 | 說明                           |
| --------- | ------- | ---- | ------------------------------ |
| is_active | boolean | ❌   | 過濾啟用狀態                   |
| limit     | integer | ❌   | 每頁筆數 (預設: 50，最大: 100) |
| offset    | integer | ❌   | 偏移量 (預設: 0)               |

#### Response 200

```json
{
  "locations": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "company_id": "company-123",
      "name": "台北101工地",
      "description": "台北101建案工地範圍",
      "location_type": "construction_site",
      "latitude": 25.0330,
      "longitude": 121.5654,
      "radius_meters": 200,
      "is_active": true,
      "created_at": "2026-03-09T10:00:00Z",
      "updated_at": "2026-03-09T10:00:00Z",
      "created_by": "user-456",
      "updated_by": null
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "company_id": "company-123",
      "name": "客戶甲辦公室",
      "location_type": "customer_site",
      "latitude": 25.0450,
      "longitude": 121.5200,
      "radius_meters": 100,
      "is_active": true,
      "created_at": "2026-03-09T11:00:00Z",
      "updated_at": "2026-03-09T11:00:00Z"
    }
  ],
  "total": 2,
  "limit": 50,
  "offset": 0
}
```

---

### 3. 查詢單筆允許地點

```http
GET /api/v1/admin/allowed-locations/{location_id}
Authorization: Bearer {access_token}
```

#### Path Parameters

| 參數        | 類型 | 說明     |
| ----------- | ---- | -------- |
| location_id | UUID | 地點 ID  |

#### Response 200

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "company_id": "company-123",
  "name": "台北101工地",
  "description": "台北101建案工地範圍",
  "location_type": "construction_site",
  "latitude": 25.0330,
  "longitude": 121.5654,
  "radius_meters": 200,
  "is_active": true,
  "created_at": "2026-03-09T10:00:00Z",
  "updated_at": "2026-03-09T10:00:00Z",
  "created_by": "user-456",
  "updated_by": null
}
```

#### Response 404

```json
{
  "detail": "Location not found"
}
```

---

### 4. 更新允許地點

```http
PUT /api/v1/admin/allowed-locations/{location_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "台北101工地（更新）",
  "radius_meters": 250,
  "is_active": false
}
```

#### Request Body

所有欄位皆為選填，僅更新提供的欄位：

| 欄位          | 類型    | 說明                                                                 |
| ------------- | ------- | -------------------------------------------------------------------- |
| name          | string  | 地點名稱                                                             |
| description   | string  | 地點描述                                                             |
| location_type | string  | 地點類型: `office`, `construction_site`, `customer_site`, `temporary_site` |
| latitude      | float   | 緯度                                                                 |
| longitude     | float   | 經度                                                                 |
| radius_meters | integer | 允許半徑（公尺）                                                     |
| is_active     | boolean | 是否啟用                                                             |

#### Response 200

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "company_id": "company-123",
  "name": "台北101工地（更新）",
  "description": "台北101建案工地範圍",
  "location_type": "construction_site",
  "latitude": 25.0330,
  "longitude": 121.5654,
  "radius_meters": 250,
  "is_active": false,
  "created_at": "2026-03-09T10:00:00Z",
  "updated_at": "2026-03-09T15:30:00Z",
  "created_by": "user-456",
  "updated_by": "user-456"
}
```

#### Response 404

```json
{
  "detail": "Location not found"
}
```

---

### 5. 刪除允許地點

```http
DELETE /api/v1/admin/allowed-locations/{location_id}
Authorization: Bearer {access_token}
```

#### Path Parameters

| 參數        | 類型 | 說明     |
| ----------- | ---- | -------- |
| location_id | UUID | 地點 ID  |

#### Response 204

No Content (刪除成功)

#### Response 404

```json
{
  "detail": "Location not found"
}
```

---

## 錯誤碼

### HTTP 狀態碼

**標準定義**:

| 狀態碼 | 說明 | 用途 |
| ------ | ------------------------ | ---- |
| 200    | 成功                     | 查詢成功、更新成功 |
| 201    | 建立成功                 | POST 建立資源 |
| 204    | 刪除成功（無內容）       | DELETE 成功 |
| **400**    | **請求錯誤**             | **缺少必填欄位、格式錯誤** |
| 401    | 未授權（未登入）         | JWT token 無效或過期 |
| **403**    | **禁止存取**             | **權限不足、業務規則拒絕** |
| 404    | 資源不存在               | 查詢不存在的資源 |
| **422**    | **驗證錯誤**             | **Schema validation 失敗** |
| 500    | 伺服器內部錯誤           | 未預期的錯誤 |

**關鍵區別**:
- **400**: 請求本身有問題（缺少必填欄位、格式錯誤）
- **403**: 請求合法但業務規則拒絕（不在範圍內、無權限）
- **422**: 請求格式正確但資料驗證失敗（緯度超出範圍）

---

### 業務錯誤碼

| 錯誤碼                      | HTTP | 說明                         | 範例情境                     |
| --------------------------- | ---- | ---------------------------- | ---------------------------- |
| VALIDATION_ERROR            | 422  | Schema 驗證錯誤              | 緯度超出範圍                 |
| GPS_REQUIRED_FOR_LOCATION_POLICY | 400  | Location policy 啟用時必須提供 GPS | 公司有 allowed locations 但未提供 GPS |
| GPS_REQUIRED                | 400  | Mobile 裝置必須提供 GPS      | Mobile 打卡未提供 GPS        |
| UNAUTHORIZED                | 401  | 未授權                       | JWT token 無效或過期         |
| FORBIDDEN                   | 403  | 權限不足                     | 一般員工嘗試建立 allowed location |
| **LOCATION_POLICY_VIOLATION** ⭐ | 403  | 不在允許的打卡範圍內         | 員工在工地 500 公尺外打卡    |
| FEATURE_DISABLED            | 403  | 功能未啟用                   | 公司未訂閱 location_policy   |
| NOT_FOUND                   | 404  | 資源不存在                   | 查詢不存在的 location_id     |
| BUSINESS_RULE_VIOLATION     | 400  | 違反業務規則                 | 重複打卡                     |

---

## 通用規範

### 認證

所有 API（除了登入）都需要在 Header 中提供 JWT token：

```http
Authorization: Bearer {access_token}
```

### Tenant Isolation

所有 API 自動依據 JWT 中的 `company_id` 進行資料隔離：
- 查詢：只能查詢自己公司的資料
- 建立：自動設定 `company_id`
- 更新/刪除：只能操作自己公司的資料

### 時間格式與時區合約（SA v2.1 §31）

所有時間欄位使用 ISO 8601 格式，並必須含 timezone offset：
```
2026-03-09T14:30:00Z          # UTC, Z suffix
2026-03-09T22:30:00+08:00     # Asia/Taipei, 含 timezone offset
```


**時區規則（SA v2.1 §31）：**

| 規則 | 說明 |
|------|------|
| UTC 儲存 | 所有 datetime 欄位在 DB 內儲存 UTC-aware datetime |
| Asia/Taipei 業務邊界 | 今天/本週/本月均以 Asia/Taipei 午夜（00:00）為邊界 |
| API request | 時間欄位必須含 timezone offset（ISO 8601），拒絕 naive datetime |
| API response | 時間欄位以 UTC 回傳，標註 Z suffix |
| datetime.utcnow() | **禁止**使用於任何業務邏輯，會產生 naive datetime |

> 正確做法：`datetime.now(timezone.utc)` 或 `datetime.now(pytz.timezone("Asia/Taipei"))`

### 分頁

使用 `limit` 和 `offset` 進行分頁：

```http
GET /api/v1/admin/allowed-locations?limit=20&offset=40
```

回應包含分頁資訊：

```json
{
  "locations": [...],
  "total": 100,
  "limit": 20,
  "offset": 40
}
```

### 錯誤回應格式

#### 簡單錯誤

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "緯度必須在 -90 到 90 之間"
}
```

#### 詳細錯誤（含欄位資訊）

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Validation failed",
  "errors": [
    {
      "field": "latitude",
      "message": "緯度必須在 -90 到 90 之間"
    },
    {
      "field": "radius_meters",
      "message": "半徑必須大於 0"
    }
  ]
}
```

#### Location Policy Violation 錯誤

```json
{
  "error_code": "LOCATION_POLICY_VIOLATION",
  "message": "不在允許的打卡範圍內。最近的地點：台北101工地（距離 350 公尺）",
  "nearest_location": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "台北101工地",
    "distance_meters": 350
  }
}
```

---

## Location Type 列舉值

| 值                | 說明         | 使用場景             |
| ----------------- | ------------ | -------------------- |
| office            | 辦公室       | 公司總部、分公司     |
| construction_site | 工地         | 建築工地、施工現場   |
| customer_site     | 客戶現場     | 客戶辦公室、拜訪地點 |
| temporary_site    | 臨時工作地點 | 短期專案、臨時據點   |

---

## 使用範例

### 範例 1: 建立工地並設定打卡範圍

```bash
# 1. 建立允許地點
curl -X POST https://api.example.com/api/v1/admin/allowed-locations \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "信義區工地A",
    "location_type": "construction_site",
    "latitude": 25.0330,
    "longitude": 121.5654,
    "radius_meters": 200,
    "is_active": true
  }'

# 2. 員工在工地內打卡（成功）
curl -X POST https://api.example.com/api/v1/attendance/break-out \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "device_type": "mobile",
    "notes": "外出巡視工地",
    "gps": {
      "latitude": 25.0335,
      "longitude": 121.5660,
      "accuracy": 10,
      "captured_at": "2026-03-09T22:30:00+08:00",
      "provider": "gps"
    }
  }'
```

### 範例 2: 查詢所有啟用中的地點

```bash
curl -X GET "https://api.example.com/api/v1/admin/allowed-locations?is_active=true" \
  -H "Authorization: Bearer {token}"
```

### 範例 3: 停用某個地點

```bash
curl -X PUT https://api.example.com/api/v1/admin/allowed-locations/{location_id} \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'
```

---

## 工時與報表欄位治理說明（SA v2.1 §26–30）

依據 SA_MODULE_SPEC_v2.1 的 Attendance Calculation Architecture，所有工時與報表相關欄位遵守以下規則：

| 規則 | 內容 |
|------|------|
| 工時 canonical 來源 | 報表顯示的工時必須讀取 （Work Hour Engine 計算，§26.4） |
| 禁止獨立計算 | Report Layer 不得執行獨立工時計算（禁止 ）（§30） |
| 前端一致性 | 前端報表元件不得用 JS 重算工時，必須讀取後端 canonical 欄位（§30.2） |
| 跨午夜 session | 所屬日期以 punch_in_time 的 Asia/Taipei 日期為準（§29.2） |
| 缺失 punch_out | session 標記為 INCOMPLETE，前端顯示未完成，不得填入估算値（§28.4） |

---

## 版本歷史

| 版本 | 日期       | 變更內容                                  |
| ---- | ---------- | ----------------------------------------- |
| 1.0  | 2026-03-01 | 初版，包含基本考勤 API                    |
| 2.0  | 2026-03-09 | 新增 Location Policy API (WP-11-13)       |
| 2.1  | 2026-03-12 | 新增 Timezone Contract 與 Report Consistency 治理說明（SA v2.1 §29、31、30 alignment） |

---

## 相關文件

- `SA_MODULE_SPEC_v2.1.md` - 系統架構規格
- `ATTENDANCE_LOCATION_POLICY_SPEC_v1.0.md` - Location Policy 詳細規格
- `WP-11-13_LOCATION_POLICY_DESIGN.md` - WP-11-13 設計文件

---

**文件狀態**: ⚠️ Draft (Partially Implemented)  
**最後更新**: 2026-03-12  
**維護者**: Backend Team
