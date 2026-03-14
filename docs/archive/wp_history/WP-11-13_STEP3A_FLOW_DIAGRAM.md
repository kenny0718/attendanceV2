# WP-11-13 Step 3A - 技術流程圖

**日期**: 2026-03-08

---

## 完整的 BREAK_OUT Location Policy 流程

```
┌─────────────────────────────────────────────────────────────────┐
│                         使用者操作                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    點擊「外出打卡」按鈕
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend: Home.vue                            │
│                                                                   │
│  handlePunch('BREAK_OUT')                                        │
│      │                                                            │
│      ▼                                                            │
│  handleBreakOutPunch()                                           │
│      │                                                            │
│      ├─ Step 1: 取得 GPS                                         │
│      │   const gpsData = await getLocationIfRequired()           │
│      │                                                            │
│      │   ┌──────────────────────────────────────┐               │
│      │   │  useLocation Composable              │               │
│      │   │  (WP-11-12 Phase 2B 已完成)          │               │
│      │   │                                       │               │
│      │   │  - 偵測裝置類型 (mobile/pc)          │               │
│      │   │  - Mobile: 取得 GPS                  │               │
│      │   │  - PC: 返回 null                     │               │
│      │   │  - 處理 GPS 錯誤                     │               │
│      │   └──────────────────────────────────────┘               │
│      │                                                            │
│      ├─ Step 2: 傳給 Store                                       │
│      │   await attendanceStore.punchWithLocation('BREAK_OUT', {  │
│      │     notes: selectedReason.value || '',                    │
│      │     gps: gpsData                                          │
│      │   })                                                       │
│      │                                                            │
│      └─ Step 3: 錯誤處理 (WP-11-13 Step 3A 新增)                │
│          catch (error) {                                          │
│            if (403 + LOCATION_POLICY_VIOLATION) {                │
│              顯示 policy violation 錯誤                          │
│            } else if (PERMISSION_DENIED) {                       │
│              顯示權限錯誤                                         │
│            } else if (TIMEOUT) {                                 │
│              顯示超時錯誤                                         │
│            } else if (POSITION_UNAVAILABLE) {                    │
│              顯示無法取得定位錯誤                                 │
│            } else {                                              │
│              顯示一般錯誤                                         │
│            }                                                      │
│          }                                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                Frontend: attendance.js Store                     │
│                (WP-11-12 Phase 2B 已完成)                        │
│                                                                   │
│  punchWithLocation(type, payload)                                │
│      │                                                            │
│      ▼                                                            │
│  switch (type) {                                                 │
│    case 'BREAK_OUT':                                             │
│      response = await attendanceApi.breakOut(payload)            │
│  }                                                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                Frontend: attendance.js API                       │
│                (WP-11-12 Phase 2B 已完成)                        │
│                                                                   │
│  breakOut: (data = {}) =>                                        │
│    apiClient.post('/v1/attendance/break-out', data)              │
│                                                                   │
│  Request Body:                                                   │
│  {                                                                │
│    notes: "外出洽公",                                            │
│    location: {                                                   │
│      latitude: 25.0330,                                          │
│      longitude: 121.5654                                         │
│    }                                                              │
│  }                                                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend: api.py                               │
│                (WP-11-13 Step 2 已完成)                          │
│                                                                   │
│  @router.post("/break-out")                                      │
│  async def break_out(request: BreakOutRequest, ...):             │
│      │                                                            │
│      ├─ Step 1: 驗證 JWT                                         │
│      │                                                            │
│      ├─ Step 2: 檢查 location policy                             │
│      │   if request.location:                                    │
│      │     policy_check = location_policy_service               │
│      │       .check_location_policy(...)                         │
│      │                                                            │
│      │     if not policy_check.allowed:                          │
│      │       raise HTTPException(                                │
│      │         status_code=403,                                  │
│      │         detail={                                          │
│      │           "error": "...",                                 │
│      │           "error_code": "LOCATION_POLICY_VIOLATION",     │
│      │           "nearest_location": {...}                       │
│      │         }                                                  │
│      │       )                                                    │
│      │                                                            │
│      └─ Step 3: 建立 punch 記錄                                  │
│          punch = repo.create_punch(                              │
│            punch_type='break_start',                             │
│            location_id=matched_location_id,                      │
│            ...                                                    │
│          )                                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│            Backend: location_policy_service.py                   │
│                (WP-11-13 Step 2 已完成)                          │
│                                                                   │
│  check_location_policy(company_id, lat, lng):                    │
│      │                                                            │
│      ├─ Step 1: 取得公司的 allowed locations                     │
│      │   locations = repo.get_allowed_locations(company_id)      │
│      │                                                            │
│      ├─ Step 2: 如果沒有 locations，允許打卡                     │
│      │   if not locations:                                       │
│      │     return PolicyCheckResult(allowed=True)                │
│      │                                                            │
│      ├─ Step 3: 計算距離（Haversine）                            │
│      │   for location in locations:                              │
│      │     distance = haversine(lat, lng, loc.lat, loc.lng)      │
│      │     if distance <= location.radius_meters:                │
│      │       return PolicyCheckResult(                           │
│      │         allowed=True,                                     │
│      │         matched_location=location                         │
│      │       )                                                    │
│      │                                                            │
│      └─ Step 4: 如果都不在範圍內，拒絕                           │
│          return PolicyCheckResult(                               │
│            allowed=False,                                        │
│            reason="不在允許的打卡範圍內",                        │
│            nearest_location=nearest                              │
│          )                                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         回應處理                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
         ┌─────────────┐           ┌─────────────┐
         │  成功 200   │           │  失敗 403   │
         └─────────────┘           └─────────────┘
                │                           │
                ▼                           ▼
    ┌──────────────────────┐    ┌──────────────────────┐
    │  顯示成功訊息        │    │  WP-11-13 Step 3A    │
    │  "打卡成功"          │    │  錯誤處理增強        │
    └──────────────────────┘    │                      │
                                 │  if (403 + LOCATION_ │
                                 │    POLICY_VIOLATION) │
                                 │  {                   │
                                 │    顯示詳細錯誤      │
                                 │    + 最近地點資訊    │
                                 │  }                   │
                                 └──────────────────────┘
```

---

## 錯誤處理流程（WP-11-13 Step 3A 重點）

```
┌─────────────────────────────────────────────────────────────────┐
│                    錯誤發生點                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┬─────────────┐
                │             │             │             │
                ▼             ▼             ▼             ▼
         ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
         │ GPS 錯誤 │  │後端 403  │  │網路錯誤  │  │其他錯誤  │
         └──────────┘  └──────────┘  └──────────┘  └──────────┘
                │             │             │             │
                ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│                Frontend: handleBreakOutPunch()                   │
│                     catch (error) { ... }                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  錯誤類型判斷    │
                    └─────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 403 + POLICY │    │  GPS 錯誤    │    │  其他錯誤    │
│  VIOLATION   │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 顯示詳細錯誤 │    │ 顯示友善提示 │    │ 顯示一般錯誤 │
│ + 最近地點   │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## GPS 錯誤處理細節

```
┌─────────────────────────────────────────────────────────────────┐
│                    useLocation.getCurrentLocation()              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                  navigator.geolocation.getCurrentPosition()
                              │
                ┌─────────────┼─────────────┬─────────────┐
                │             │             │             │
                ▼             ▼             ▼             ▼
         ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
         │ 權限拒絕 │  │ 位置無法 │  │   超時   │  │ 不支援   │
         │ code: 1  │  │ 取得     │  │ code: 3  │  │          │
         │          │  │ code: 2  │  │          │  │          │
         └──────────┘  └──────────┘  └──────────┘  └──────────┘
                │             │             │             │
                ▼             ▼             ▼             ▼
         ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
         │PERMISSION│  │ POSITION │  │ TIMEOUT  │  │   NOT    │
         │ _DENIED  │  │_UNAVAIL  │  │          │  │SUPPORTED │
         └──────────┘  └──────────┘  └──────────┘  └──────────┘
                │             │             │             │
                └─────────────┴─────────────┴─────────────┘
                              │
                              ▼
                    throw LocationError
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│            handleBreakOutPunch() catch 區塊                      │
│                                                                   │
│  if (error.code === 'PERMISSION_DENIED') {                       │
│    errorMessage.value = '需要定位權限才能外出打卡\n              │
│                          請在瀏覽器設定中允許定位後重試'         │
│  }                                                                │
│  else if (error.code === 'TIMEOUT') {                            │
│    errorMessage.value = '定位請求逾時\n                          │
│                          請確認 GPS 訊號良好後重試'              │
│  }                                                                │
│  else if (error.code === 'POSITION_UNAVAILABLE') {               │
│    errorMessage.value = '無法取得定位資訊\n                      │
│                          請確認已開啟定位服務'                   │
│  }                                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 後端 403 錯誤處理細節

```
┌─────────────────────────────────────────────────────────────────┐
│                Backend: location_policy_service                  │
│                                                                   │
│  policy_check = check_location_policy(...)                       │
│                                                                   │
│  if not policy_check.allowed:                                    │
│    raise HTTPException(                                          │
│      status_code=403,                                            │
│      detail={                                                    │
│        "error": "不在允許的打卡範圍內。最近的地點：台北101工地  │
│                 （距離 250 公尺）",                              │
│        "error_code": "LOCATION_POLICY_VIOLATION",               │
│        "nearest_location": {                                     │
│          "id": "...",                                            │
│          "name": "台北101工地",                                  │
│          "distance_meters": 250                                  │
│        }                                                          │
│      }                                                            │
│    )                                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    HTTP 403 Response
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│            Frontend: handleBreakOutPunch() catch                 │
│                                                                   │
│  if (error.response?.status === 403 &&                           │
│      error.response?.data?.detail?.error_code ===                │
│        'LOCATION_POLICY_VIOLATION') {                            │
│                                                                   │
│    let message = error.response.data.detail.error ||             │
│                  '不在允許的打卡範圍內'                          │
│                                                                   │
│    if (error.response.data.detail.nearest_location) {            │
│      const nearest = error.response.data.detail.nearest_location │
│      message += `\n\n最近的允許地點：${nearest.name}\n           │
│                  距離：${nearest.distance_meters} 公尺`          │
│    }                                                              │
│                                                                   │
│    errorMessage.value = message                                  │
│  }                                                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    顯示錯誤訊息給使用者
```

---

## 資料流向

```
┌──────────────┐
│   使用者     │
└──────────────┘
       │
       │ 點擊「外出打卡」
       ▼
┌──────────────┐
│  Home.vue    │
└──────────────┘
       │
       │ getLocationIfRequired()
       ▼
┌──────────────┐
│ useLocation  │ ← WP-11-12 Phase 2B
└──────────────┘
       │
       │ { latitude, longitude, accuracy, ... }
       ▼
┌──────────────┐
│ attendance   │
│   Store      │ ← WP-11-12 Phase 2B
└──────────────┘
       │
       │ { notes, location: { latitude, longitude } }
       ▼
┌──────────────┐
│ attendance   │
│    API       │ ← WP-11-12 Phase 2B
└──────────────┘
       │
       │ POST /v1/attendance/break-out
       ▼
┌──────────────┐
│  Backend     │
│   api.py     │ ← WP-11-13 Step 2
└──────────────┘
       │
       │ check_location_policy()
       ▼
┌──────────────┐
│  location_   │
│  policy_     │ ← WP-11-13 Step 2
│  service     │
└──────────────┘
       │
       ├─ allowed=True → 200 OK
       │
       └─ allowed=False → 403 LOCATION_POLICY_VIOLATION
                              │
                              ▼
                        ┌──────────────┐
                        │  Frontend    │
                        │  錯誤處理    │ ← WP-11-13 Step 3A
                        └──────────────┘
                              │
                              ▼
                        顯示友善錯誤訊息
```

---

## 各階段完成狀態

```
WP-11-12 Phase 2B (已完成)
├─ useLocation composable
├─ getLocationIfRequired()
├─ GPS 資料格式化
├─ Store 整合
└─ API 整合

WP-11-13 Step 2 (已完成)
├─ AllowedLocation model
├─ location_policy_service
├─ Admin CRUD API
├─ Backend enforcement
└─ Migration

WP-11-13 Step 3A (已完成) ← 本次實作
├─ 403 LOCATION_POLICY_VIOLATION 處理
├─ GPS 錯誤訊息優化
└─ 友善的使用者提示

WP-11-13 Step 3B (未實作)
├─ Admin UI
├─ 地點管理頁面
└─ CRUD 表單
```

---

**建立日期**: 2026-03-08  
**狀態**: ✅ 已完成
