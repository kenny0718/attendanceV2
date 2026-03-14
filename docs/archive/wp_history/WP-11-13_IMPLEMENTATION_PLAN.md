# WP-11-13 Implementation Plan

**票號**: WP-11-13  
**標題**: Attendance Location Policy / Geofence - Step 2 (Backend Foundation)  
**狀態**: In Progress  
**日期**: 2026-03-08  
**版本**: 1.0

---

## 執行摘要

本階段（Step 2）專注於建立 WP-11-13 的後端基礎設施，實作 Allowed Location 資料模型、Policy Service、以及 BREAK_OUT 的後端強制驗證。

**關鍵原則**:
- **前端 policy 檢查只能作為 UX-friendly precheck**
- **真正決定是否允許打卡的權威判斷，必須永遠在後端執行**
- 即使前端沒檢查到，後端仍必須獨立驗證並拒絕不合法打卡

---

## 實作目標

### Step 2 範圍

✅ **包含**:
- Allowed location backend foundation
- Geofence policy evaluation service
- BREAK_OUT backend enforcement（authoritative）
- 管理端 CRUD API（v1 最小版）
- 基礎測試

❌ **不包含**:
- 前端管理 UI（留待後續）
- Map picker（留待後續）
- BREAK_IN / punch-in / punch-out 整合（v1 只做 BREAK_OUT）
- 複雜 policy 規則（時間限制、員工綁定等）
- Location policy check 審計表（v1 暫不實作）

---

## 實作順序

### Step 2A: Migration + Model + Schema

**目標**: 建立資料模型基礎

**工作項目**:
1. 建立 `allowed_locations` 表 migration
2. 擴充 `attendance_punches` 表（新增 `location_id` 欄位）
3. 建立 `AllowedLocation` SQLAlchemy model
4. 建立對應 Pydantic schemas

**預估時間**: 1-2 小時

---

### Step 2B: Distance Helper + Policy Service

**目標**: 建立 policy 評估核心邏輯

**工作項目**:
1. 確認 `gps_utils.py` 的 Haversine 距離計算可重用
2. 建立 `AttendanceLocationPolicyService` 
3. 實作 policy evaluation 邏輯：
   - 讀取公司啟用中的 allowed locations
   - 檢查 GPS 是否命中任一允許地點
   - 回傳 allow/deny + matched location + violation reason

**預估時間**: 2-3 小時

---

### Step 2C: Admin CRUD API

**目標**: 提供管理端 API 供後續前端接入

**工作項目**:
1. `POST /api/v1/admin/allowed-locations` - 建立地點
2. `GET /api/v1/admin/allowed-locations` - 查詢列表
3. `GET /api/v1/admin/allowed-locations/{id}` - 查詢單筆
4. `PUT /api/v1/admin/allowed-locations/{id}` - 更新地點
5. `DELETE /api/v1/admin/allowed-locations/{id}` - 刪除地點
6. Tenant isolation 驗證
7. 基本參數驗證

**預估時間**: 2-3 小時

---

### Step 2D: BREAK_OUT Backend Enforcement

**目標**: 在 BREAK_OUT API 加入 authoritative policy enforcement

**工作項目**:
1. 修改 `/api/v1/attendance/break-out` endpoint
2. 加入 policy service 呼叫
3. 驗證失敗時回傳明確錯誤碼
4. 驗證成功時記錄 `location_id`
5. 確保後端獨立驗證，不依賴前端

**預估時間**: 1-2 小時

---

### Step 2E: Tests + Docs + QA Notes

**目標**: 確保品質與可維護性

**工作項目**:
1. Unit tests（distance calculation, policy evaluation）
2. API tests（CRUD, enforcement）
3. Regression tests（不破壞既有流程）
4. 更新文件

**預估時間**: 2-3 小時

---

## 技術設計

### 1. 資料模型

#### AllowedLocation

```python
class AllowedLocation(Base):
    """允許打卡地點模型"""
    
    __tablename__ = "allowed_locations"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, 
                server_default=text('gen_random_uuid()'))
    
    # Tenant Isolation
    company_id = Column(String(255), nullable=False)
    
    # 基本資訊
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location_type = Column(String(50), nullable=False, 
                          server_default='office')
    
    # 位置資訊
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    radius_meters = Column(Integer, nullable=False)
    
    # 狀態
    is_active = Column(Boolean, nullable=False, 
                      server_default='true')
    
    # 審計欄位
    created_at = Column(DateTime, nullable=False, 
                       server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime, nullable=False, 
                       server_default=text('CURRENT_TIMESTAMP'))
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
```

**設計決策**:
- 使用 `Numeric(10, 7)` 儲存經緯度（精度約 1.1 公分）
- `location_type` 預留未來擴充
- `is_active` 支援軟啟用/停用
- v1 使用 hard delete（簡化實作）

#### attendance_punches 擴充

```sql
ALTER TABLE attendance_punches
ADD COLUMN location_id UUID,
ADD CONSTRAINT fk_punches_location 
    FOREIGN KEY (location_id) 
    REFERENCES allowed_locations(id) 
    ON DELETE SET NULL;
```

**設計決策**:
- `location_id` = 命中的 allowed location（不是使用者實際 GPS 點）
- `ON DELETE SET NULL`（保守策略，避免級聯刪除風險）
- 保留既有 `location_lat` / `location_lng` 欄位（記錄實際 GPS）

---

### 2. Policy Service

#### AttendanceLocationPolicyService

```python
class AttendanceLocationPolicyService:
    """Location Policy 評估服務
    
    責任：
    1. 讀取公司啟用中的 allowed locations
    2. 檢查 GPS 是否命中任一允許地點
    3. 回傳 allow/deny + matched location + violation reason
    """
    
    def check_location_policy(
        self,
        company_id: str,
        latitude: float,
        longitude: float
    ) -> PolicyCheckResult:
        """檢查 location policy
        
        邏輯：
        1. 取得公司的所有啟用中的 allowed locations
        2. 如果沒有任何 allowed locations → 允許任何地點打卡
        3. 如果有 allowed locations：
           a. 計算與每個地點的距離
           b. 檢查是否有任一地點在半徑內
           c. 如果有 → 允許打卡，返回匹配的地點
           d. 如果沒有 → 拒絕打卡，返回最近的地點
        """
        pass
```

**PolicyCheckResult**:
```python
@dataclass
class PolicyCheckResult:
    allowed: bool
    reason: str
    matched_location: Optional[Dict] = None
    nearest_location: Optional[Dict] = None
```

---

### 3. API 設計

#### 管理端 API

```
POST   /api/v1/admin/allowed-locations      建立地點
GET    /api/v1/admin/allowed-locations      查詢列表
GET    /api/v1/admin/allowed-locations/{id} 查詢單筆
PUT    /api/v1/admin/allowed-locations/{id} 更新地點
DELETE /api/v1/admin/allowed-locations/{id} 刪除地點
```

#### BREAK_OUT Enforcement

```python
@router_v1.post("/break-out", response_model=BreakOutResponse)
async def break_out(request: BreakOutRequest, ...):
    """外出打卡 - WP-11-13: 加入 location policy 檢查"""
    
    # WP-11-13: 後端 authoritative enforcement
    if request.location:
        policy_check = location_policy_service.check_location_policy(
            company_id=company_id,
            latitude=request.location.latitude,
            longitude=request.location.longitude
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
    
    # 原有打卡邏輯...
    # 記錄 matched_location_id
```

---

### 4. 錯誤碼

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

---

## 風險與回滾

### Migration 風險

**風險**:
- 新增 `allowed_locations` 表可能失敗
- 擴充 `attendance_punches` 表可能影響既有資料

**緩解**:
- Migration 使用 `IF NOT EXISTS` 檢查
- `location_id` 欄位設為 nullable
- FK constraint 使用 `ON DELETE SET NULL`
- 先在 dev 環境測試

**回滾**:
```sql
-- Rollback migration
ALTER TABLE attendance_punches DROP COLUMN location_id;
DROP TABLE allowed_locations;
```

---

### Punch Flow 整合風險

**風險**:
- BREAK_OUT enforcement 可能破壞既有流程
- Policy check 失敗可能導致無法打卡

**緩解**:
- 只在有 location 時才檢查 policy
- 沒有 allowed locations 時允許任何地點
- 保留既有錯誤處理邏輯
- 充分測試 regression

**回滾**:
- 移除 policy check 程式碼
- 恢復原有 BREAK_OUT 邏輯

---

### Tenant Isolation 風險

**風險**:
- Allowed locations 可能跨租戶洩漏
- Policy check 可能檢查到其他公司的地點

**緩解**:
- 所有查詢必須包含 `company_id` filter
- API 層驗證 tenant context
- 測試跨租戶隔離

---

## 測試策略

### Unit Tests

**Distance Calculation**:
- 測試 Haversine 公式正確性
- 測試邊界條件（赤道、極點）

**Policy Evaluation**:
- 無 allowed locations → allow any
- 在範圍內 → allow
- 超出範圍 → deny
- 多個地點，命中其中一個 → allow
- require location 但缺 GPS → deny

---

### API Tests

**Admin CRUD**:
- 建立地點成功
- 查詢列表（分頁、過濾）
- 更新地點
- 刪除地點
- Tenant isolation
- 參數驗證（經緯度範圍、半徑 > 0）

**BREAK_OUT Enforcement**:
- 有 location + 在範圍內 → 成功
- 有 location + 超出範圍 → 403 錯誤
- 無 location + 無規則 → 成功
- 無 location + 有規則 → 成功（v1 不強制要求 location）

---

### Regression Tests

**確保不破壞既有流程**:
- BREAK_OUT 無 location 時仍可打卡
- BREAK_IN 不受影響
- punch-in / punch-out 不受影響
- 既有 session 邏輯不受影響

---

## v1 範圍確認

### ✅ Step 2 包含

- `allowed_locations` 表與 model
- `attendance_punches.location_id` 欄位
- Distance helper（重用 `gps_utils.py`）
- `AttendanceLocationPolicyService`
- 管理端 CRUD API（最小版）
- BREAK_OUT backend enforcement
- 基礎測試

---

### ❌ Step 2 不包含

**前端相關**:
- 前端管理 UI
- Map picker
- 地點列表顯示
- 前端 policy precheck（留待 Step 3）

**其他打卡流程**:
- BREAK_IN enforcement
- punch-in enforcement
- punch-out enforcement

**進階功能**:
- Location policy check 審計表
- 複雜 policy 規則
- 時間限制
- 員工/部門綁定

---

## 後續步驟

### Step 3: 前端整合（後續票）

- 前端 policy precheck（UX-friendly）
- 管理端 UI（地點列表、CRUD）
- 錯誤訊息顯示

### Step 4: 擴充到其他流程（後續票）

- BREAK_IN enforcement
- punch-in enforcement
- punch-out enforcement

### Step 5: 進階功能（後續票）

- Map picker
- 位置歷史軌跡
- 複雜 policy 規則

---

## Definition of Done

### Step 2 完成條件

- [x] `WP-11-13_IMPLEMENTATION_PLAN.md` 已建立
- [ ] `allowed_locations` migration 已建立並測試
- [ ] `AllowedLocation` model 已建立
- [ ] `AttendanceLocationPolicyService` 已實作
- [ ] Policy evaluation 邏輯正確
- [ ] 管理端 CRUD API 可用
- [ ] BREAK_OUT 已有後端 authoritative enforcement
- [ ] 測試覆蓋核心場景
- [ ] Tracker 已更新
- [ ] 尚未做的項目有清楚記錄

---

## 相關文件

- `docs/WP-11-13_LOCATION_POLICY_DESIGN.md` - 設計文件
- `docs/WP-11-13_LOCATION_POLICY_PREP.md` - 預留設計
- `docs/WP-11-12_PHASE2B_CLOSEOUT_SUMMARY.md` - 前置票結案
- `docs/GATE_PROGRESS_TRACKER.md` - 進度追蹤
- `docs/NEXT_WP_TICKET.md` - 下一步規劃

---

**建立日期**: 2026-03-08  
**最後更新**: 2026-03-08  
**狀態**: In Progress  
**當前階段**: Step 2A - Migration + Model + Schema
