# GPS Reality Verification Report

**產出日期：** 2026-03-10
**審計範圍：** backend/app/modules/attendance/ + frontend/src/
**目的：** 驗證 WP-11-13 GPS/Location 功能在實際程式碼中是否完整實作
**規則：** READ-ONLY — 未修改任何程式碼

---

## 1. Backend GPS Support

### 1.1 相關檔案清單

| 檔案 | 說明 |
|------|------|
| `attendance/models.py` | AttendancePunch + AllowedLocation DB model |
| `attendance/schemas.py` | LocationData / PunchRequest Pydantic schemas |
| `attendance/api.py` | 打卡 API + location policy enforcement |
| `attendance/location_policy_service.py` | Location Policy 業務邏輯 |
| `attendance/gps_utils.py` | Haversine 距離計算 |
| `attendance/admin_location_api.py` | 允許地點 CRUD API |
| `alembic/versions/008_wp_11_13_create_allowed_locations.py` | DB Migration |

### 1.2 資料庫欄位

**AttendancePunch 表：**

| 欄位 | 型別 | 說明 |
|------|------|------|
| `location_lat` | Numeric(10,8) | 打卡緯度（可選）|
| `location_lng` | Numeric(11,8) | 打卡經度（可選）|
| `location_id` | UUID FK | 匹配的允許地點 ID（WP-11-13）|

**AllowedLocation 表（migration 008）：**

| 欄位 | 型別 | 說明 |
|------|------|------|
| `id` | UUID PK | 地點 ID |
| `company_id` | str | Tenant 隔離 |
| `name` | str | 地點名稱 |
| `latitude` | Numeric(10,7) | 地點中心緯度 |
| `longitude` | Numeric(10,7) | 地點中心經度 |
| `radius_meters` | int | 允許半徑（公尺）|
| `is_active` | bool | 是否啟用 |

### 1.3 API Endpoints

**打卡 API（api.py）：**

| Endpoint | GPS 支援 | Location Policy |
|----------|----------|------------------|
| POST /punch-in | ✅ location 可選 | ❌ 不強制（IN 不需 policy）|
| POST /punch-out | ✅ location 可選 | ❌ 不強制 |
| POST /break-out | ✅ location 可選 | ✅ 強制執行 policy |
| POST /break-in | ✅ location 可選 | ❌ 不強制 |

**Admin Location API（admin_location_api.py）：**

| Endpoint | 說明 |
|----------|------|
| POST /allowed-locations | 建立允許地點 |
| GET /allowed-locations | 列出允許地點 |
| GET /allowed-locations/{id} | 取得單一地點 |
| PUT /allowed-locations/{id} | 更新地點 |
| DELETE /allowed-locations/{id} | 刪除地點 |

### 1.4 Location Policy 邏輯（location_policy_service.py）

**流程：**
1. 取得公司所有 active AllowedLocation
2. 若無任何允許地點 → 放行（允許任何位置打卡）
3. 若有允許地點 → 計算 Haversine 距離
4. 任一地點距離 ≤ radius_meters → 允許，記錄 matched_location_id
5. 全部超出範圍 → 403 LOCATION_POLICY_VIOLATION + nearest_location 資訊

**距離計算（gps_utils.py）：**
- 使用 Haversine formula（球面距離計算）
- 精度：±1% 以內（已有單元測試驗證）

---

## 2. Frontend GPS Capture

### 2.1 相關檔案

| 檔案 | 說明 |
|------|------|
| `composables/useLocation.js` | 統一 GPS 服務（WP-11-12 建立）|
| `utils/locationAdapter.js` | 舊版橋接層（@deprecated，保留向後相容）|
| `views/Home.vue` | 打卡頁面，呼叫 GPS 並傳送 payload |
| `stores/attendance.js` | punchWithLocation() 方法 |

### 2.2 GPS 取得流程（useLocation.js）

```
navigator.geolocation.getCurrentPosition()
  → { latitude, longitude, accuracy, timestamp }
  → location.value = locationData
  → return locationData
```

- Mobile 裝置：`isGPSRequired = true`，強制取得 GPS
- PC 裝置：`isGPSRequired = false`，GPS 為可選
- 錯誤處理：PERMISSION_DENIED / TIMEOUT / POSITION_UNAVAILABLE 均有對應訊息

### 2.3 哪些打卡動作需要 GPS

| 打卡動作 | GPS 必要性 | 實作方式 |
|----------|-----------|----------|
| 上班打卡（punch-in）| ❌ 不需要 | 直接呼叫 handlePunch('IN') |
| 下班打卡（punch-out）| ❌ 不需要 | 直接呼叫 handlePunch('OUT') |
| 外出打卡（break-out）| ✅ Mobile 必要 | handleBreakOutPunch() → getLocationIfRequired() |
| 返回打卡（break-in）| ❌ 不需要 | 直接呼叫 handleBreakInPunch() |

### 2.4 外出打卡 Payload 結構

```javascript
// Home.vue handleBreakOutPunch()
const gpsData = await getLocationIfRequired()
const payload = {
  notes: breakOutReason.value.trim()
}
if (gpsData) {
  payload.location = {
    latitude: gpsData.latitude,
    longitude: gpsData.longitude
  }
}
await attendanceStore.punchWithLocation('BREAK_OUT', payload)
```

---

## 3. API Contract（End-to-End Flow）

```
Mobile Browser
  └─ navigator.geolocation.getCurrentPosition()
       └─ { latitude, longitude }
            └─ POST /api/v1/attendance/break-out
                 Body: {
                   "notes": "外出原因",
                   "location": {
                     "latitude": 25.0335,
                     "longitude": 121.5654
                   }
                 }
                 └─ Backend api.py
                      └─ location_policy_service.check_location_policy()
                           └─ gps_utils.calculate_distance() [Haversine]
                                ├─ WITHIN radius → 200 OK, location_id 記錄
                                └─ OUTSIDE radius → 403 LOCATION_POLICY_VIOLATION
                                     └─ { nearest_location: { name, distance_meters } }
                                          └─ Frontend 顯示友善錯誤訊息
```

**DB Storage（成功時）：**
```
AttendancePunch:
  location_lat = 25.0335
  location_lng = 121.5654
  location_id  = <matched AllowedLocation UUID>
```

---

## 4. Database Storage 驗證

| 項目 | 狀態 | 細節 |
|------|------|------|
| AttendancePunch.location_lat | ✅ 存在 | Numeric(10,8), nullable |
| AttendancePunch.location_lng | ✅ 存在 | Numeric(11,8), nullable |
| AttendancePunch.location_id | ✅ 存在 | UUID FK → allowed_locations |
| AllowedLocation table | ✅ 存在 | migration 008 |
| Tenant isolation (company_id) | ✅ 實作 | Index + FK 保護 |
| DB constraints | ✅ 實作 | lat/lng range check, radius > 0 |
| Google Maps link | ✅ 顯示 | 記錄有 lat/lng 時顯示地圖連結 |

---

## 5. Spec vs Reality 對比

依據 ATTENDANCE_LOCATION_MODULE_SPEC.md 和 WP-11-13_LOCATION_POLICY_DESIGN.md

| Spec 項目 | 狀態 | 實作細節 |
|-----------|------|----------|
| AllowedLocation CRUD API | ✅ FULLY_IMPLEMENTED | admin_location_api.py 5 個 endpoints |
| GPS 座標接收（latitude/longitude）| ✅ FULLY_IMPLEMENTED | schemas.py LocationData |
| GPS 座標儲存（DB）| ✅ FULLY_IMPLEMENTED | AttendancePunch.location_lat/lng |
| Haversine 距離計算 | ✅ FULLY_IMPLEMENTED | gps_utils.py calculate_distance() |
| Location Policy 驗證（BREAK_OUT）| ✅ FULLY_IMPLEMENTED | location_policy_service.py |
| 403 LOCATION_POLICY_VIOLATION | ✅ FULLY_IMPLEMENTED | api.py + frontend 錯誤處理 |
| nearest_location 回傳 | ✅ FULLY_IMPLEMENTED | policy_service 回傳距離 + 名稱 |
| matched_location_id 儲存 | ✅ FULLY_IMPLEMENTED | AttendancePunch.location_id FK |
| Tenant Isolation | ✅ FULLY_IMPLEMENTED | company_id 過濾 |
| Frontend GPS 取得（Mobile）| ✅ FULLY_IMPLEMENTED | useLocation.js + navigator.geolocation |
| Frontend GPS 取得（PC 可選）| ✅ FULLY_IMPLEMENTED | isGPSRequired computed |
| 友善錯誤訊息 | ✅ FULLY_IMPLEMENTED | PERMISSION_DENIED/TIMEOUT/POSITION_UNAVAILABLE |
| Google Maps 連結 | ✅ FULLY_IMPLEMENTED | Home.vue + OutLogsSection.vue |
| 測試覆蓋 | ✅ 測試檔存在 | test_location_policy.py, test_break_out_enforcement.py |
| 測試實際執行通過 | ⚠️ UNVERIFIED | 需 PostgreSQL 環境執行 |
| Admin UI（允許地點管理）| ❌ NOT_IMPLEMENTED | 後端 API 存在，但前端無管理介面 |

### 對比分類

| 分類 | 項目數 |
|------|--------|
| FULLY_IMPLEMENTED | 14 項 |
| UNVERIFIED（需環境測試）| 1 項 |
| NOT_IMPLEMENTED | 1 項（Admin UI）|

---

## 6. Final Status

### 整體評定：✅ SUBSTANTIALLY_COMPLETE（實質完成）

**已完整實作（程式碼層面）：**
- ✅ Backend GPS 接收、儲存、驗證、距離計算
- ✅ AllowedLocation CRUD API
- ✅ Location Policy enforcement（BREAK_OUT 強制）
- ✅ Frontend GPS 取得（useLocation composable）
- ✅ E2E 流程：GPS → API → Policy Check → DB Storage
- ✅ 錯誤處理：403 + 友善訊息 + 最近地點資訊
- ✅ Tenant Isolation
- ✅ 測試案例已撰寫

**未完成項目：**
- ⚠️ 測試未在真實 DB 環境執行（環境阻塞）
- ❌ Admin UI（管理員設定允許地點的前端介面）未建立
  - 目前只能透過 API 直接操作
  - 此為 Phase 2 Frontend 工作（WP-25 Admin UI 範圍）

**阻塞原因：**
- Manual QA（GPS + 真實環境）需要：
  1. 真實瀏覽器（支援 navigator.geolocation）
  2. PostgreSQL 資料庫 + migration 008 執行
  3. Backend 服務啟動
  4. 實際地點測試（需在 AllowedLocation 設定的範圍內外各測一次）

---

## 附錄：關鍵程式碼位置快速索引

| 功能 | 檔案 | 行號 |
|------|------|------|
| AllowedLocation model | backend/models.py | L306-358 |
| AttendancePunch GPS fields | backend/models.py | L150-173 |
| Location Policy Service | backend/location_policy_service.py | 全檔 |
| Haversine 計算 | backend/gps_utils.py | L10-48 |
| BREAK_OUT policy enforcement | backend/api.py | L422-482 |
| Admin Location CRUD | backend/admin_location_api.py | 全檔 |
| useLocation composable | frontend/composables/useLocation.js | 全檔 |
| handleBreakOutPunch | frontend/views/Home.vue | L333-395 |
| GPS payload 傳送 | frontend/views/Home.vue | L346-359 |
| punchWithLocation | frontend/stores/attendance.js | L181+ |

---

**END OF GPS_REALITY_VERIFICATION_REPORT.md**

*產出者：AI Reality Check Session 2026-03-10*
*注意：本報告為純程式碼審計輸出，未修改任何檔案*
