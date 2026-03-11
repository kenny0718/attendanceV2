# WP-11-13 Step 3A - QA 報告

**票號**: WP-11-13 Step 3A  
**標題**: Frontend Integration for BREAK_OUT Location Policy - QA Validation  
**日期**: 2026-03-08  
**QA 類型**: Code Review + Manual Test Plan

---

## 執行摘要

WP-11-13 Step 3A 的程式碼審查已完成。所有關鍵元件和流程已驗證完整性。

**審查結果**: ✅ 通過
- 前端錯誤處理已正確實作
- 後端 enforcement 已就位
- 資料流向正確
- 無明顯程式碼缺陷

**待執行**: Manual QA（需要測試環境）

---

## 階段 1: 程式碼完整性檢查

### 1.1 後端關鍵檔案 ✅

| 檔案 | 狀態 | 說明 |
|------|------|------|
| `models.py` | ✅ | AllowedLocation model + location_id |
| `location_policy_service.py` | ✅ | Policy enforcement logic |
| `admin_location_api.py` | ✅ | Admin CRUD API |
| `api.py` | ✅ | BREAK_OUT endpoint with policy check |
| `008_*.py` | ✅ | Migration file |

---

### 1.2 前端關鍵檔案 ✅

| 檔案 | 狀態 | 說明 |
|------|------|------|
| `Home.vue` | ✅ | handleBreakOutPunch() 錯誤處理 |
| `useLocation.js` | ✅ | GPS composable |
| `attendance.js` (store) | ✅ | punchWithLocation() |
| `attendance.js` (api) | ✅ | breakOut() API call |

---

## 階段 2: 前端流程完整性檢查

### 2.1 BREAK_OUT 流程 ✅

| 檢查項目 | 狀態 | 位置 |
|----------|------|------|
| handlePunch('BREAK_OUT') 調用 | ✅ | Home.vue:54 |
| handleBreakOutPunch() 函數 | ✅ | Home.vue:425 |
| getLocationIfRequired() 調用 | ✅ | Home.vue:428 |
| punchWithLocation() 調用 | ✅ | Home.vue:431 |
| notes 參數傳遞 | ✅ | Home.vue:432 |
| gps 參數傳遞 | ✅ | Home.vue:433 |

**流程圖**:
```
使用者點擊「外出打卡」
    ↓
handlePunch('BREAK_OUT')
    ↓
handleBreakOutPunch()
    ↓
getLocationIfRequired() → GPS 取得
    ↓
punchWithLocation('BREAK_OUT', { notes, gps })
    ↓
attendanceApi.breakOut({ notes, location })
    ↓
後端驗證 location policy
    ↓
回應處理（成功 / 錯誤）
```

---

### 2.2 錯誤處理檢查 ✅

| 檢查項目 | 狀態 | 說明 |
|----------|------|------|
| 403 + LOCATION_POLICY_VIOLATION | ✅ | 檢測後端 policy violation |
| nearest_location 顯示 | ✅ | 顯示最近地點和距離 |
| PERMISSION_DENIED 處理 | ✅ | GPS 權限被拒絕 |
| TIMEOUT 處理 | ✅ | GPS 超時 |
| POSITION_UNAVAILABLE 處理 | ✅ | GPS 無法取得 |
| errorMessage 設定 | ✅ | 錯誤訊息變數 |
| showErrorMessage 顯示 | ✅ | 顯示錯誤 UI |

**錯誤處理程式碼片段**:
```javascript
catch (error) {
  // WP-11-13: 處理 location policy violation
  if (error.response?.status === 403 && 
      error.response?.data?.detail?.error_code === 'LOCATION_POLICY_VIOLATION') {
    let message = error.response.data.detail.error || '不在允許的打卡範圍內'
    
    if (error.response.data.detail.nearest_location) {
      const nearest = error.response.data.detail.nearest_location
      message += `\n\n最近的允許地點：${nearest.name}\n距離：${nearest.distance_meters} 公尺`
    }
    
    errorMessage.value = message
  } else if (error.code === 'PERMISSION_DENIED') {
    errorMessage.value = '需要定位權限才能外出打卡\n請在瀏覽器設定中允許定位後重試'
  } else if (error.code === 'TIMEOUT') {
    errorMessage.value = '定位請求逾時\n請確認 GPS 訊號良好後重試'
  } else if (error.code === 'POSITION_UNAVAILABLE') {
    errorMessage.value = '無法取得定位資訊\n請確認已開啟定位服務'
  } else {
    errorMessage.value = error.message || '打卡失敗，請稍後再試'
  }
}
```

---

### 2.3 useLocation Composable 檢查 ✅

| 檢查項目 | 狀態 | 說明 |
|----------|------|------|
| getCurrentLocation() 函數 | ✅ | 取得 GPS 位置 |
| getLocationIfRequired() 函數 | ✅ | 條件式取得位置 |
| navigator.geolocation 檢查 | ✅ | 瀏覽器支援檢查 |
| LocationErrorCode 定義 | ✅ | 錯誤碼常數 |
| PERMISSION_DENIED 錯誤碼 | ✅ | 權限拒絕 |
| TIMEOUT 錯誤碼 | ✅ | 超時 |
| POSITION_UNAVAILABLE 錯誤碼 | ✅ | 位置無法取得 |

---

## 階段 3: 後端 Location Policy 檢查

### 3.1 Location Policy Service ✅

| 檢查項目 | 狀態 | 說明 |
|----------|------|------|
| check_location_policy() 函數 | ✅ | 主要驗證邏輯 |
| 距離計算 | ✅ | Haversine 公式 |
| PolicyCheckResult 類別 | ✅ | 回傳結果結構 |
| allowed 欄位 | ✅ | 是否允許 |
| reason 欄位 | ✅ | 拒絕原因 |
| matched_location 欄位 | ✅ | 匹配的地點 |
| nearest_location 欄位 | ✅ | 最近的地點 |
| 無 policy 時允許打卡 | ✅ | 向後相容 |
| 範圍內允許打卡 | ✅ | 正常流程 |
| 範圍外拒絕打卡 | ✅ | Policy enforcement |

**Policy 邏輯**:
```python
def check_location_policy(company_id, latitude, longitude):
    # 1. 取得公司的 allowed locations
    locations = get_allowed_locations(company_id)
    
    # 2. 如果沒有 locations，允許打卡（向後相容）
    if not locations:
        return PolicyCheckResult(allowed=True)
    
    # 3. 計算距離，找出匹配的地點
    for location in locations:
        distance = haversine(lat, lng, location.lat, location.lng)
        if distance <= location.radius_meters:
            return PolicyCheckResult(
                allowed=True,
                matched_location=location
            )
    
    # 4. 如果都不在範圍內，拒絕
    return PolicyCheckResult(
        allowed=False,
        reason="不在允許的打卡範圍內",
        nearest_location=nearest
    )
```

---

### 3.2 AllowedLocation Model ✅

| 欄位 | 狀態 | 類型 | 說明 |
|------|------|------|------|
| id | ✅ | UUID | Primary key |
| company_id | ✅ | String | Tenant isolation |
| name | ✅ | String | 地點名稱 |
| latitude | ✅ | Float | 緯度 |
| longitude | ✅ | Float | 經度 |
| radius_meters | ✅ | Integer | 允許範圍（公尺）|
| is_active | ✅ | Boolean | 啟用狀態 |
| created_at | ✅ | DateTime | 建立時間 |
| updated_at | ✅ | DateTime | 更新時間 |

**AttendancePunch 新增欄位**:
- `location_id` (UUID, nullable) - 匹配的地點 ID

---

### 3.3 Admin Location API ✅

| 端點 | 狀態 | 說明 |
|------|------|------|
| POST /admin/allowed-locations | ✅ | 建立地點 |
| GET /admin/allowed-locations | ✅ | 列出地點 |
| GET /admin/allowed-locations/{id} | ✅ | 取得單一地點 |
| PUT /admin/allowed-locations/{id} | ✅ | 更新地點 |
| DELETE /admin/allowed-locations/{id} | ✅ | 刪除地點 |

**Tenant Isolation**: ✅ 所有端點都使用 `company_id` 進行隔離

---

### 3.4 BREAK_OUT API Endpoint ✅

**位置**: `backend/app/modules/attendance/api.py:370`

**關鍵邏輯**:
```python
@router_v1.post("/break-out", response_model=BreakOutResponse, status_code=201)
async def break_out(request: BreakOutRequest, ...):
    # WP-11-13: Location policy enforcement
    matched_location_id = None
    if request.location:
        policy_service = get_location_policy_service(db)
        policy_check = policy_service.check_location_policy(
            company_id=company_id,
            latitude=request.location.latitude,
            longitude=request.location.longitude
        )
        
        if not policy_check.allowed:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": policy_check.reason,
                    "error_code": "LOCATION_POLICY_VIOLATION",
                    "nearest_location": policy_check.nearest_location
                }
            )
        
        if policy_check.matched_location:
            matched_location_id = UUID(policy_check.matched_location["id"])
    
    # Create punch with location_id
    punch = repo.create_punch(
        ...,
        location_id=matched_location_id
    )
```

**檢查結果**: ✅ 所有邏輯正確

---

## 階段 4: 資料流向驗證

### 4.1 Request Payload ✅

**前端發送**:
```javascript
{
  notes: "外出洽公",
  location: {
    latitude: 25.0330,
    longitude: 121.5654
  }
}
```

**後端接收**:
```python
class BreakOutRequest(BaseModel):
    notes: Optional[str]
    location: Optional[LocationData]

class LocationData(BaseModel):
    latitude: float
    longitude: float
```

**驗證**: ✅ Schema 匹配

---

### 4.2 Response Payload ✅

**成功回應 (200)**:
```json
{
  "punch_id": "...",
  "session_id": "...",
  "punch_time": "2026-03-08T10:30:00Z",
  "message": "外出打卡成功"
}
```

**錯誤回應 (403)**:
```json
{
  "detail": {
    "error": "不在允許的打卡範圍內。最近的地點：台北101工地（距離 250 公尺）",
    "error_code": "LOCATION_POLICY_VIOLATION",
    "nearest_location": {
      "id": "...",
      "name": "台北101工地",
      "distance_meters": 250
    }
  }
}
```

**驗證**: ✅ 前端正確處理兩種回應

---

## 階段 5: 相容性檢查

### 5.1 不影響的流程 ✅

| 流程 | 狀態 | 說明 |
|------|------|------|
| BREAK_IN | ✅ | 使用不同的函數 |
| punch-in | ✅ | 使用不同的函數 |
| punch-out | ✅ | 使用不同的函數 |
| OUT Checkpoint | ✅ | 使用不同的函數 |
| 頁面載入 | ✅ | 無影響 |

**驗證方式**: 檢查 Home.vue 中的其他函數，確認沒有被修改

---

### 5.2 共用元件 ✅

| 元件 | 使用者 | 影響 |
|------|--------|------|
| useLocation | BREAK_OUT, OUT Checkpoint | 無破壞性變更 |
| attendance store | 所有打卡流程 | 無破壞性變更 |
| attendance API | 所有打卡流程 | 無破壞性變更 |

---

## 階段 6: Manual QA Test Plan

### 6.1 測試環境需求

**前置條件**:
1. ✅ Migration 008 已執行
2. ✅ 後端服務運行（包含 Step 2 程式碼）
3. ✅ 前端服務運行（包含 Step 3A 程式碼）
4. ⏳ 測試資料準備（公司、使用者、allowed locations）

---

### 6.2 測試案例

#### Test Case 1: 無 Policy - 正常打卡

**前置條件**:
- 公司沒有設定 allowed locations

**步驟**:
1. 登入系統
2. 先打上班卡
3. 點擊「外出打卡」
4. （Mobile）允許定位權限
5. 確認打卡

**預期結果**:
- ✅ 打卡成功
- ✅ 顯示「打卡成功」訊息
- ✅ 外出時間記錄正確

**實際結果**: ⏳ 待測試

---

#### Test Case 2: 有 Policy + 在範圍內

**前置條件**:
- 公司有設定 allowed location（例如：台北101工地，半徑 100 公尺）
- 使用者在範圍內（距離 < 100 公尺）

**步驟**:
1. 登入系統
2. 先打上班卡
3. 點擊「外出打卡」
4. （Mobile）允許定位權限
5. 確認打卡

**預期結果**:
- ✅ 打卡成功
- ✅ 顯示「打卡成功」訊息
- ✅ 外出時間記錄正確
- ✅ location_id 記錄正確

**實際結果**: ⏳ 待測試

---

#### Test Case 3: 有 Policy + 超出範圍

**前置條件**:
- 公司有設定 allowed location（例如：台北101工地，半徑 100 公尺）
- 使用者在範圍外（距離 > 100 公尺）

**步驟**:
1. 登入系統
2. 先打上班卡
3. 點擊「外出打卡」
4. （Mobile）允許定位權限
5. 確認打卡

**預期結果**:
- ❌ 打卡失敗（403）
- ✅ 顯示錯誤訊息：「不在允許的打卡範圍內」
- ✅ 顯示最近地點：「最近的允許地點：台北101工地」
- ✅ 顯示距離：「距離：250 公尺」
- ✅ 錯誤訊息友善且清楚

**實際結果**: ⏳ 待測試

---

#### Test Case 4: GPS 權限被拒絕

**前置條件**:
- 使用 Mobile 裝置
- 拒絕定位權限

**步驟**:
1. 登入系統
2. 先打上班卡
3. 點擊「外出打卡」
4. 拒絕定位權限

**預期結果**:
- ❌ 打卡失敗
- ✅ 顯示錯誤訊息：「需要定位權限才能外出打卡」
- ✅ 顯示提示：「請在瀏覽器設定中允許定位後重試」
- ✅ 錯誤訊息友善且清楚

**實際結果**: ⏳ 待測試

---

#### Test Case 5: GPS 超時

**前置條件**:
- 使用 Mobile 裝置
- GPS 訊號不良

**步驟**:
1. 登入系統
2. 先打上班卡
3. 點擊「外出打卡」
4. 允許定位權限
5. 等待超時（10 秒）

**預期結果**:
- ❌ 打卡失敗
- ✅ 顯示錯誤訊息：「定位請求逾時」
- ✅ 顯示提示：「請確認 GPS 訊號良好後重試」
- ✅ 錯誤訊息友善且清楚

**實際結果**: ⏳ 待測試

---

#### Test Case 6: GPS 無法取得

**前置條件**:
- 使用 Mobile 裝置
- 關閉定位服務

**步驟**:
1. 登入系統
2. 先打上班卡
3. 點擊「外出打卡」
4. 允許定位權限（但定位服務關閉）

**預期結果**:
- ❌ 打卡失敗
- ✅ 顯示錯誤訊息：「無法取得定位資訊」
- ✅ 顯示提示：「請確認已開啟定位服務」
- ✅ 錯誤訊息友善且清楚

**實際結果**: ⏳ 待測試

---

#### Test Case 7: PC 裝置（無 GPS）

**前置條件**:
- 使用 PC 裝置

**步驟**:
1. 登入系統
2. 先打上班卡
3. 點擊「外出打卡」
4. 確認打卡

**預期結果**:
- ✅ 打卡成功（不需要 GPS）
- ✅ 顯示「打卡成功」訊息
- ✅ location 欄位為 null

**實際結果**: ⏳ 待測試

---

#### Test Case 8: 其他流程不受影響

**步驟**:
1. 測試 BREAK_IN（返回打卡）
2. 測試 punch-in（上班打卡）
3. 測試 punch-out（下班打卡）
4. 測試 OUT Checkpoint（外出位置記錄）

**預期結果**:
- ✅ 所有流程正常運作
- ✅ 無錯誤發生
- ✅ 無 UI 異常

**實際結果**: ⏳ 待測試

---

## 階段 7: 程式碼品質檢查

### 7.1 程式碼風格 ✅

- ✅ 遵循專案 coding style
- ✅ 變數命名清晰
- ✅ 註解適當
- ✅ 無 console.log 殘留（除了錯誤處理）

---

### 7.2 錯誤處理 ✅

- ✅ 所有錯誤情況都有處理
- ✅ 錯誤訊息友善
- ✅ 不暴露敏感資訊
- ✅ 有適當的 fallback

---

### 7.3 效能考量 ✅

- ✅ 無不必要的 API 請求
- ✅ GPS timeout 設定合理（10 秒）
- ✅ 錯誤訊息自動消失（5 秒）

---

### 7.4 安全性 ✅

- ✅ 後端是唯一的 enforcement 來源
- ✅ 前端只負責 UX
- ✅ Tenant isolation 正確
- ✅ 無 SQL injection 風險

---

## 階段 8: 文件完整性檢查

### 8.1 實作文件 ✅

| 文件 | 狀態 | 說明 |
|------|------|------|
| IMPLEMENTATION_REPORT.md | ✅ | 詳細實作報告 |
| SUMMARY.md | ✅ | 完成總結 |
| CHANGES.md | ✅ | 修改清單 |
| FLOW_DIAGRAM.md | ✅ | 技術流程圖 |
| QUICK_REFERENCE.md | ✅ | 快速參考卡 |
| COMPLETION.txt | ✅ | 完成報告 |

---

### 8.2 規劃文件 ✅

| 文件 | 狀態 | 說明 |
|------|------|------|
| NEXT_WP_TICKET.md | ✅ | 下一步規劃 |
| IMPLEMENTATION_PLAN.md | ✅ | 整體計劃 |
| STEP3_PLAN.md | ✅ | Step 3 計劃 |

---

## 發現的問題

### 無嚴重問題

程式碼審查未發現嚴重問題或 bug。

---

## 建議

### 1. Manual QA 執行

**優先級**: High

**說明**: 需要在測試環境執行完整的 Manual QA，驗證所有測試案例。

---

### 2. 錯誤訊息本地化

**優先級**: Low

**說明**: 目前錯誤訊息是硬編碼的中文。未來可以考慮使用 i18n。

---

### 3. 前端 Precheck（可選）

**優先級**: Low

**說明**: 可以考慮加入前端 precheck，在送出 API 前提前檢查，但目前的實作已經足夠好。

---

## 結論

### ✅ 程式碼審查通過

**總結**:
- 所有關鍵元件已正確實作
- 資料流向正確
- 錯誤處理完整
- 無明顯程式碼缺陷
- 相容性良好

**下一步**:
1. 執行 Manual QA（需要測試環境）
2. 驗證所有測試案例
3. 根據測試結果決定是否需要修正
4. 準備部署到 production

---

**建立日期**: 2026-03-08  
**審查者**: AI Assistant  
**狀態**: ✅ 程式碼審查通過  
**待執行**: Manual QA
