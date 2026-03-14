# WP-11-13 Location Policy / Geofence 設計文件

**票號**: WP-11-13  
**標題**: Attendance Location Policy / Geofence  
**狀態**: Design Phase  
**日期**: 2026-03-08  
**版本**: 1.0

---

## 執行摘要

WP-11-13 實作「允許打卡地點 / Geofence Policy」功能，讓公司管理員可在後台設定可打卡地點（例如工地、辦公室、客戶現場），系統在打卡時依據目前位置判斷是否允許打卡。

**關鍵原則**:
- 不重做 useLocation（WP-11-12 已完成）
- 專注於 policy / rule 層
- v1 最小可用驗證鏈路
- 模組內聚設計
- 為未來擴充預留空間

---

## 需求與邊界

### 業務需求

**情境 1: 工地打卡**
```
公司: 建築公司
需求: 員工只能在工地範圍內打卡
行為: 
  - 在工地範圍內 → 允許打卡
  - 在工地範圍外 → 拒絕打卡，顯示「不在允許的打卡範圍內」
```

**情境 2: 多地點打卡**
```
公司: 顧問公司
需求: 員工可在多個客戶地點打卡
行為:
  - 在任一客戶地點範圍內 → 允許打卡
  - 不在任何客戶地點範圍內 → 拒絕打卡
```

**情境 3: 彈性工作**
```
公司: 科技公司
需求: 員工可在任何地點打卡
行為:
  - 員工在任何地點 → 允許打卡
  - 仍然記錄 GPS（用於統計分析）
```

### 範圍邊界

**✅ WP-11-13 v1 包含**:
- 允許打卡地點資料模型
- Geofence 驗證邏輯（Haversine distance）
- Policy evaluation service
- 管理端 CRUD API
- 打卡端 policy 檢查
- BREAK_OUT 整合（v1 最小切片）
- 錯誤碼與錯誤訊息

**❌ WP-11-13 v1 不包含**:
- 地圖 UI / 地圖選點器（留待 WP-11-14）
- 位置歷史軌跡（留待 WP-11-14）
- 複雜 policy 規則（時間限制、員工綁定）
- BREAK_IN / punch-in / punch-out 整合（v1 只做 BREAK_OUT）
- OUT checkpoints
- 重做 useLocation

---

## 資料模型設計

### 1. AllowedLocation (允許打卡地點)

```python
class AllowedLocation(Base):
    """允許打卡地點模型
    
    設計原則：
    1. 支援多筆地點（不要做死成只能一筆）
    2. Tenant isolation (company_id)
    3. 支援啟用/停用
    4. 預留擴充欄位
    """
    
    __tablename__ = "allowed_locations"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, 
                server_default=text('gen_random_uuid()'),
                comment='Location ID (PK)')
    
    # Tenant Isolation
    company_id = Column(String(255), nullable=False, 
                       comment='公司 ID (Tenant Isolation)')
    
    # 基本資訊
    name = Column(String(255), nullable=False, 
                 comment='地點名稱，例如：台北101工地')
    description = Column(Text, nullable=True, 
                        comment='地點描述')
    
    # 地點類型（預留擴充）
    location_type = Column(String(50), nullable=False, 
                          server_default='office',
                          comment='地點類型: office, construction_site, customer_site, temporary_site')
    
    # 位置資訊
    latitude = Column(Numeric(10, 7), nullable=False, 
                     comment='緯度 (Decimal for precision)')
    longitude = Column(Numeric(10, 7), nullable=False, 
                      comment='經度 (Decimal for precision)')
    radius_meters = Column(Integer, nullable=False, 
                          comment='允許半徑（公尺）')
    
    # 狀態
    is_active = Column(Boolean, nullable=False, 
                      server_default='true',
                      comment='是否啟用')
    
    # 審計欄位
    created_at = Column(DateTime, nullable=False, 
                       server_default=text('CURRENT_TIMESTAMP'),
                       comment='建立時間')
    updated_at = Column(DateTime, nullable=False, 
                       server_default=text('CURRENT_TIMESTAMP'),
                       onupdate=get_current_time,
                       comment='更新時間')
    created_by = Column(String(255), nullable=True, 
                       comment='建立者 user_id')
    updated_by = Column(String(255), nullable=True, 
                       comment='更新者 user_id')
    
    # Indexes
    __table_args__ = (
        Index('idx_allowed_locations_company', 'company_id'),
        Index('idx_allowed_locations_active', 'company_id', 'is_active'),
        CheckConstraint('radius_meters > 0', name='chk_radius_positive'),
        CheckConstraint('latitude >= -90 AND latitude <= 90', name='chk_latitude_range'),
        CheckConstraint('longitude >= -180 AND longitude <= 180', name='chk_longitude_range'),
    )
```

**設計說明**:
- 使用 `Numeric(10, 7)` 儲存經緯度，精度約 1.1 公分
- `location_type` 預留未來擴充（例如：依類型套用不同規則）
- `is_active` 支援軟啟用/停用
- 不使用 soft delete，直接刪除（簡化 v1）
- `created_by` / `updated_by` 記錄審計資訊

### 2. LocationPolicyCheck (Policy 檢查記錄)

```python
class LocationPolicyCheck(Base):
    """Location Policy 檢查記錄（可選，用於審計）
    
    v1 可以不實作此表，先在 memory 中檢查
    未來如需審計追蹤，再加入此表
    """
    
    __tablename__ = "location_policy_checks"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True)
    company_id = Column(String(255), nullable=False)
    user_id = Column(String(255), nullable=False)
    
    # 檢查時的位置
    check_latitude = Column(Numeric(10, 7), nullable=False)
    check_longitude = Column(Numeric(10, 7), nullable=False)
    
    # 檢查結果
    is_allowed = Column(Boolean, nullable=False)
    matched_location_id = Column(PGUUID(as_uuid=True), nullable=True)
    distance_meters = Column(Integer, nullable=True)
    
    # 檢查時間
    checked_at = Column(DateTime, nullable=False, 
                       server_default=text('CURRENT_TIMESTAMP'))
    
    # 關聯的打卡記錄（如果有）
    punch_id = Column(PGUUID(as_uuid=True), nullable=True)
```

**v1 決策**: 暫不實作此表，先專注於核心 policy 邏輯

---

## API 合約設計

### 管理端 API

#### 1. 建立允許地點

```
POST /api/v1/admin/allowed-locations

Request:
{
  "name": "台北101工地",
  "description": "台北101建案工地",
  "location_type": "construction_site",
  "latitude": 25.0330,
  "longitude": 121.5654,
  "radius_meters": 100,
  "is_active": true
}

Response: 201 Created
{
  "id": "loc-uuid-123",
  "company_id": "company-123",
  "name": "台北101工地",
  "description": "台北101建案工地",
  "location_type": "construction_site",
  "latitude": 25.0330,
  "longitude": 121.5654,
  "radius_meters": 100,
  "is_active": true,
  "created_at": "2026-03-08T10:00:00Z",
  "updated_at": "2026-03-08T10:00:00Z",
  "created_by": "user-123"
}

Errors:
- 400: 參數錯誤（經緯度範圍、半徑必須 > 0）
- 401: 未授權
- 403: 無管理員權限
- 409: 地點名稱重複
```

#### 2. 查詢允許地點列表

```
GET /api/v1/admin/allowed-locations?is_active=true&limit=50&offset=0

Response: 200 OK
{
  "locations": [
    {
      "id": "loc-uuid-123",
      "name": "台北101工地",
      "location_type": "construction_site",
      "latitude": 25.0330,
      "longitude": 121.5654,
      "radius_meters": 100,
      "is_active": true,
      "created_at": "2026-03-08T10:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### 3. 更新允許地點

```
PUT /api/v1/admin/allowed-locations/{location_id}

Request:
{
  "name": "台北101工地（更新）",
  "radius_meters": 150,
  "is_active": true
}

Response: 200 OK
{
  "id": "loc-uuid-123",
  "name": "台北101工地（更新）",
  "radius_meters": 150,
  "is_active": true,
  "updated_at": "2026-03-08T11:00:00Z",
  "updated_by": "user-123"
}

Errors:
- 404: 地點不存在
- 403: 無權限
```

#### 4. 刪除允許地點

```
DELETE /api/v1/admin/allowed-locations/{location_id}

Response: 204 No Content

Errors:
- 404: 地點不存在
- 403: 無權限
```

### 打卡端 API

#### 5. 取得 Location Policy（前端用）

```
GET /api/v1/attendance/location-policy

Response: 200 OK
{
  "require_location": true,
  "allow_any_location": false,
  "allowed_locations": [
    {
      "id": "loc-uuid-123",
      "name": "台北101工地",
      "latitude": 25.0330,
      "longitude": 121.5654,
      "radius_meters": 100
    }
  ]
}

說明:
- require_location: 是否要求定位（v1 可先 hardcode true）
- allow_any_location: 是否允許任何地點（v1 根據是否有 allowed_locations 判斷）
- 只返回 is_active=true 的地點
- 不返回 description / created_at 等管理資訊
```

#### 6. 打卡時的 Policy 檢查（內部）

```
內部 Service Method:
check_location_policy(company_id, latitude, longitude) -> PolicyCheckResult

PolicyCheckResult:
{
  "allowed": boolean,
  "reason": string,
  "matched_location": {
    "id": string,
    "name": string,
    "distance_meters": number
  } | null,
  "nearest_location": {
    "id": string,
    "name": string,
    "distance_meters": number
  } | null
}

範例 1: 允許打卡
{
  "allowed": true,
  "reason": "在允許的打卡範圍內：台北101工地",
  "matched_location": {
    "id": "loc-uuid-123",
    "name": "台北101工地",
    "distance_meters": 45
  }
}

範例 2: 拒絕打卡
{
  "allowed": false,
  "reason": "不在允許的打卡範圍內。最近的地點：台北101工地（距離 250 公尺）",
  "matched_location": null,
  "nearest_location": {
    "id": "loc-uuid-123",
    "name": "台北101工地",
    "distance_meters": 250
  }
}

範例 3: 允許任何地點
{
  "allowed": true,
  "reason": "公司允許任何地點打卡"
}
```

---

## Policy Evaluation Flow

### 核心邏輯

```python
def check_location_policy(company_id: str, latitude: float, longitude: float) -> PolicyCheckResult:
    """
    檢查 location policy
    
    邏輯:
    1. 取得公司的所有啟用中的 allowed locations
    2. 如果沒有任何 allowed locations → 允許任何地點打卡
    3. 如果有 allowed locations:
       a. 計算與每個地點的距離
       b. 檢查是否有任一地點在半徑內
       c. 如果有 → 允許打卡，返回匹配的地點
       d. 如果沒有 → 拒絕打卡，返回最近的地點
    """
    
    # Step 1: 取得啟用中的 allowed locations
    locations = get_active_allowed_locations(company_id)
    
    # Step 2: 如果沒有設定任何地點 → 允許任何地點
    if not locations:
        return PolicyCheckResult(
            allowed=True,
            reason="公司允許任何地點打卡"
        )
    
    # Step 3: 計算距離並檢查
    matched_location = None
    nearest_location = None
    min_distance = float('inf')
    
    for location in locations:
        distance = calculate_haversine_distance(
            latitude, longitude,
            location.latitude, location.longitude
        )
        
        # 更新最近地點
        if distance < min_distance:
            min_distance = distance
            nearest_location = location
        
        # 檢查是否在半徑內
        if distance <= location.radius_meters:
            matched_location = location
            break  # 找到第一個匹配的就可以
    
    # Step 4: 返回結果
    if matched_location:
        return PolicyCheckResult(
            allowed=True,
            reason=f"在允許的打卡範圍內：{matched_location.name}",
            matched_location={
                "id": matched_location.id,
                "name": matched_location.name,
                "distance_meters": int(calculate_haversine_distance(...))
            }
        )
    else:
        return PolicyCheckResult(
            allowed=False,
            reason=f"不在允許的打卡範圍內。最近的地點：{nearest_location.name}（距離 {int(min_distance)} 公尺）",
            nearest_location={
                "id": nearest_location.id,
                "name": nearest_location.name,
                "distance_meters": int(min_distance)
            }
        )
```

### Haversine Distance 計算

```python
import math

def calculate_haversine_distance(lat1: float, lon1: float, 
                                 lat2: float, lon2: float) -> float:
    """
    計算兩個 GPS 座標之間的距離（公尺）
    使用 Haversine formula
    
    Args:
        lat1, lon1: 第一個點的經緯度
        lat2, lon2: 第二個點的經緯度
    
    Returns:
        距離（公尺）
    """
    R = 6371000  # 地球半徑（公尺）
    
    # 轉換為弧度
    φ1 = math.radians(lat1)
    φ2 = math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(Δφ / 2) ** 2 +
         math.cos(φ1) * math.cos(φ2) *
         math.sin(Δλ / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    
    return distance
```

---

## 整合點設計

### v1 最小切片：BREAK_OUT

**選擇理由**:
1. BREAK_OUT 已有 shared location foundation（WP-11-12 Phase 2B）
2. 風險最低，不影響主打卡流程
3. 可先驗證 policy 架構正確性
4. 外出打卡是最需要 geofence 的場景

### 整合流程

```
使用者點擊「外出打卡」
    ↓
Home.vue: handleBreakOutPunch()
    ↓
UI 層: getLocationIfRequired() 取得 GPS
    ↓
UI 層: checkLocationPolicy(gps) 檢查 policy (新增)
    ↓
如果 policy.allowed == false:
    顯示錯誤: policy.reason
    return (不送出 API)
    ↓
如果 policy.allowed == true:
    attendanceStore.punchWithLocation('BREAK_OUT', {
      notes: selectedReason,
      gps: gpsData,
      matched_location_id: policy.matched_location?.id  (新增)
    })
    ↓
後端: breakOut API 接收 matched_location_id
    ↓
儲存到 attendance_punches.location_id (新增欄位)
```

### 後端整合點

```python
# backend/app/modules/attendance/api.py

@router.post("/break-out", response_model=BreakOutResponse)
async def break_out(
    request: BreakOutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """外出打卡 (WP-11-07 Phase 3B)
    
    WP-11-13: 加入 location policy 檢查
    """
    
    # WP-11-13: 如果有 GPS，檢查 location policy
    if request.gps:
        policy_check = location_policy_service.check_location_policy(
            company_id=current_user.company_id,
            latitude=request.gps.latitude,
            longitude=request.gps.longitude
        )
        
        if not policy_check.allowed:
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": "LOCATION_POLICY_VIOLATION",
                    "message": policy_check.reason,
                    "nearest_location": policy_check.nearest_location
                }
            )
    
    # 原有打卡邏輯
    punch = attendance_service.break_out(
        company_id=current_user.company_id,
        user_id=current_user.id,
        notes=request.notes,
        gps=request.gps,
        matched_location_id=policy_check.matched_location.id if policy_check.matched_location else None
    )
    
    return BreakOutResponse(...)
```

### 前端整合點

```javascript
// frontend/src/views/Home.vue

// WP-11-13: 新增 useLocationPolicy
import { useLocationPolicy } from '@/composables/useLocationPolicy'

const {
  policy,
  checkLocation,
  isChecking,
  fetchPolicy
} = useLocationPolicy()

// 頁面載入時取得 policy
onMounted(async () => {
  await fetchPolicy()
})

async function handleBreakOutPunch() {
  try {
    // Step 1: 取得 location
    const gpsData = await getLocationIfRequired()
    
    // Step 2: 檢查 location policy (WP-11-13 新增)
    if (gpsData && policy.value.require_location) {
      const policyCheck = await checkLocation(gpsData)
      
      if (!policyCheck.allowed) {
        errorMessage.value = policyCheck.reason
        showErrorMessage.value = true
        return  // 不送出 API
      }
    }
    
    // Step 3: 執行打卡
    await attendanceStore.punchWithLocation('BREAK_OUT', {
      notes: selectedReason.value,
      gps: gpsData,
      matched_location_id: policyCheck?.matched_location?.id
    })
    
  } catch (error) {
    // 錯誤處理
  }
}
```

---

## 錯誤碼設計

### 新增錯誤碼

```python
class LocationPolicyErrorCode:
    """Location Policy 相關錯誤碼"""
    
    # Policy violation
    LOCATION_POLICY_VIOLATION = "LOCATION_POLICY_VIOLATION"
    # 不在允許的打卡範圍內
    
    # Location required
    LOCATION_REQUIRED = "LOCATION_REQUIRED"
    # 公司要求定位，但未提供 GPS
    
    # Invalid location data
    INVALID_LOCATION_DATA = "INVALID_LOCATION_DATA"
    # GPS 資料格式錯誤
```

### 錯誤訊息範例

```json
{
  "error_code": "LOCATION_POLICY_VIOLATION",
  "message": "不在允許的打卡範圍內。最近的地點：台北101工地（距離 250 公尺）",
  "nearest_location": {
    "id": "loc-uuid-123",
    "name": "台北101工地",
    "distance_meters": 250
  }
}
```

---

## 資料庫 Migration

### Migration: 建立 allowed_locations 表

```sql
-- WP-11-13: Create allowed_locations table

CREATE TABLE allowed_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    location_type VARCHAR(50) NOT NULL DEFAULT 'office',
    latitude NUMERIC(10, 7) NOT NULL,
    longitude NUMERIC(10, 7) NOT NULL,
    radius_meters INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    
    CONSTRAINT chk_radius_positive CHECK (radius_meters > 0),
    CONSTRAINT chk_latitude_range CHECK (latitude >= -90 AND latitude <= 90),
    CONSTRAINT chk_longitude_range CHECK (longitude >= -180 AND longitude <= 180)
);

CREATE INDEX idx_allowed_locations_company ON allowed_locations(company_id);
CREATE INDEX idx_allowed_locations_active ON allowed_locations(company_id, is_active);

COMMENT ON TABLE allowed_locations IS 'WP-11-13: 允許打卡地點';
COMMENT ON COLUMN allowed_locations.id IS 'Location ID (PK)';
COMMENT ON COLUMN allowed_locations.company_id IS '公司 ID (Tenant Isolation)';
COMMENT ON COLUMN allowed_locations.name IS '地點名稱，例如：台北101工地';
COMMENT ON COLUMN allowed_locations.location_type IS '地點類型: office, construction_site, customer_site, temporary_site';
COMMENT ON COLUMN allowed_locations.latitude IS '緯度 (Decimal for precision)';
COMMENT ON COLUMN allowed_locations.longitude IS '經度 (Decimal for precision)';
COMMENT ON COLUMN allowed_locations.radius_meters IS '允許半徑（公尺）';
COMMENT ON COLUMN allowed_locations.is_active IS '是否啟用';
```

### Migration: 擴充 attendance_punches 表

```sql
-- WP-11-13: Add location_id to attendance_punches

ALTER TABLE attendance_punches
ADD COLUMN location_id UUID,
ADD CONSTRAINT fk_punches_location 
    FOREIGN KEY (location_id) 
    REFERENCES allowed_locations(id) 
    ON DELETE SET NULL;

CREATE INDEX idx_punches_location ON attendance_punches(location_id);

COMMENT ON COLUMN attendance_punches.location_id IS 'WP-11-13: 匹配的允許地點 ID';
```

---

## 未來擴充方向

### Phase 2: 擴充到其他打卡流程

```
v1: BREAK_OUT
v2: BREAK_IN, punch-in, punch-out
```

### Phase 3: 進階 Policy 規則

```
- 時間限制（例如：只在工作時間內要求 geofence）
- 員工/部門綁定（不同員工可打卡的地點不同）
- 班表綁定（依班表決定允許地點）
- 警告模式（範圍外可打卡但警告）
```

### Phase 4: 管理後台 UI

```
- 地圖選點器
- 視覺化半徑
- 批次匯入地點
- 地點使用統計
```

### Phase 5: 位置分析

```
- 員工位置熱圖
- 打卡地點分布
- 異常位置偵測
```

---

## 技術債務與注意事項

### 裝置類型 vs Policy

**目前問題**:
- WP-11-12 寫死：Mobile 需要 GPS，PC 不需要
- 應改由 policy 決定

**未來改善**:
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

**v1 決策**: 暫不修改，保持向後相容

### Decimal vs Float

**決策**: 使用 `Numeric(10, 7)` 儲存經緯度
- 精度約 1.1 公分
- 避免浮點數精度問題

### Soft Delete vs Hard Delete

**v1 決策**: Hard delete
- 簡化實作
- 未來如需審計，可改為 soft delete

---

## 相關文件

- `docs/WP-11-13_IMPLEMENTATION_PLAN.md` - 實作計劃
- `docs/WP-11-12_PHASE2B_CLOSEOUT_SUMMARY.md` - 前置票結案
- `docs/WP-11-13_LOCATION_POLICY_PREP.md` - 預留設計

---

**建立日期**: 2026-03-08  
**最後更新**: 2026-03-08  
**狀態**: Design Complete  
**下一步**: Implementation Planning
