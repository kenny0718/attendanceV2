# Attendance Location Validation Service Plan

**文件版本**: 1.0  
**建立日期**: 2026-03-08  
**狀態**: ✅ DRAFT  
**目的**: 設計後端可重用的半徑驗證服務

---

## 1. Service Architecture

### 1.1 Service Layer

```python
# backend/app/modules/attendance/services/location_validation_service.py

class LocationValidationService:
    """定位驗證服務（可重用）"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_location(
        self,
        location: LocationPayload,
        target_lat: Optional[float],
        target_lng: Optional[float],
        allowed_radius_m: Optional[float],
        min_accuracy_m: Optional[float] = None
    ) -> LocationValidationResult:
        """驗證定位是否符合政策
        
        Args:
            location: 使用者定位資料
            target_lat: 目標點緯度（None = 不限制）
            target_lng: 目標點經度（None = 不限制）
            allowed_radius_m: 允許半徑（公尺，None = 不限制）
            min_accuracy_m: 最小精度要求（公尺，None = 不限制）
        
        Returns:
            LocationValidationResult
        """
        
        # 1. 驗證座標格式
        if not self._is_valid_coordinates(location.latitude, location.longitude):
            return LocationValidationResult(
                is_valid=False,
                validation_code="INVALID_COORDINATES",
                validation_message="座標格式錯誤"
            )
        
        # 2. 驗證精度
        if min_accuracy_m and location.accuracy > min_accuracy_m:
            return LocationValidationResult(
                is_valid=False,
                validation_code="ACCURACY_TOO_LOW",
                validation_message=f"GPS 精度不足（需要 < {min_accuracy_m}m）"
            )
        
        # 3. 若無目標點，直接通過
        if target_lat is None or target_lng is None:
            return LocationValidationResult(
                is_valid=True,
                validation_code="VALID_NO_RESTRICTION",
                validation_message="驗證通過（無範圍限制）"
            )
        
        # 4. 計算距離
        from app.modules.attendance.gps_utils import calculate_distance
        
        distance_m = calculate_distance(
            (location.latitude, location.longitude),
            (target_lat, target_lng)
        )
        
        # 5. 若無半徑限制，直接通過
        if allowed_radius_m is None:
            return LocationValidationResult(
                is_valid=True,
                is_within_radius=None,
                distance_meters=distance_m,
                target_latitude=target_lat,
                target_longitude=target_lng,
                validation_code="VALID_NO_RESTRICTION",
                validation_message="驗證通過（無半徑限制）"
            )
        
        # 6. 驗證是否在半徑內
        is_within = distance_m <= allowed_radius_m
        
        if is_within:
            return LocationValidationResult(
                is_valid=True,
                is_within_radius=True,
                distance_meters=distance_m,
                allowed_radius_meters=allowed_radius_m,
                target_latitude=target_lat,
                target_longitude=target_lng,
                validation_code="VALID_WITHIN_RADIUS",
                validation_message=f"驗證通過（距離 {distance_m:.0f}m）"
            )
        else:
            return LocationValidationResult(
                is_valid=False,
                is_within_radius=False,
                distance_meters=distance_m,
                allowed_radius_meters=allowed_radius_m,
                target_latitude=target_lat,
                target_longitude=target_lng,
                validation_code="OUTSIDE_ALLOWED_RADIUS",
                validation_message=f"超出允許範圍（距離 {distance_m:.0f}m，限制 {allowed_radius_m:.0f}m）"
            )
    
    def _is_valid_coordinates(self, lat: float, lng: float) -> bool:
        """驗證座標範圍"""
        return -90 <= lat <= 90 and -180 <= lng <= 180
```

---

## 2. Distance Calculation

### 2.1 Haversine Formula

已實作於 `gps_utils.py`，可直接重用：

```python
def calculate_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """使用 Haversine 公式計算距離（公尺）"""
    # 已實作，精度 ~0.5% for < 1000km
```

**特性**:
- ✅ 精度高（誤差 < 0.5%）
- ✅ 效能好（O(1)）
- ✅ 適用範圍廣（< 1000km）

**不適用情境**:
- ❌ 極地區域（緯度 > 85°）
- ❌ 跨越國際換日線

---

## 3. Policy Configuration

### 3.1 Location Policy Interface

```python
class LocationPolicy:
    """定位政策（未來擴充用）"""
    
    is_required: bool                    # 是否必須提供定位
    target_latitude: Optional[float]     # 目標點緯度
    target_longitude: Optional[float]    # 目標點經度
    allowed_radius_meters: Optional[float]  # 允許半徑（公尺）
    min_accuracy_meters: Optional[float]    # 最小精度要求（公尺）
    location_label: Optional[str]           # 地點名稱（顯示用）
```

### 3.2 Policy Source（未來實作）

**Phase 1（本輪）**: Hard-coded 或從環境變數讀取

```python
def get_location_policy(company_id: str, punch_type: str) -> LocationPolicy:
    """取得定位政策（暫時 hard-coded）"""
    
    # 暫時：所有公司都不強制定位
    return LocationPolicy(
        is_required=False,
        target_latitude=None,
        target_longitude=None,
        allowed_radius_meters=None,
        min_accuracy_meters=None,
        location_label=None
    )
```

**Phase 2（未來）**: 從資料庫讀取

```python
def get_location_policy(company_id: str, punch_type: str) -> LocationPolicy:
    """從資料庫讀取定位政策"""
    
    policy = db.query(AttendanceLocationPolicy).filter(
        AttendanceLocationPolicy.company_id == company_id,
        AttendanceLocationPolicy.punch_type == punch_type
    ).first()
    
    if not policy:
        return LocationPolicy(is_required=False, ...)
    
    return LocationPolicy(
        is_required=policy.is_required,
        target_latitude=policy.target_latitude,
        target_longitude=policy.target_longitude,
        allowed_radius_meters=policy.allowed_radius_meters,
        min_accuracy_meters=policy.min_accuracy_meters,
        location_label=policy.location_label
    )
```

---

## 4. API Integration

### 4.1 Punch-In with Location Validation

```python
@router.post("/punch-in")
async def punch_in(
    request: PunchInRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    # 1. 取得定位政策
    location_service = LocationValidationService(db)
    policy = location_service.get_location_policy(
        company_id=tenant_context.company_id,
        punch_type='IN'
    )
    
    # 2. 驗證定位（若需要）
    if policy.is_required and not request.location:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "LOCATION_REQUIRED",
                "message": "此打卡點需要提供定位資訊"
            }
        )
    
    if request.location:
        validation_result = location_service.validate_location(
            location=request.location,
            target_lat=policy.target_latitude,
            target_lng=policy.target_longitude,
            allowed_radius_m=policy.allowed_radius_meters,
            min_accuracy_m=policy.min_accuracy_meters
        )
        
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": validation_result.validation_code,
                    "message": validation_result.validation_message,
                    "distance_meters": validation_result.distance_meters,
                    "allowed_radius_meters": validation_result.allowed_radius_meters
                }
            )
    
    # 3. 執行打卡
    # ...
```

---

## 5. Testing Strategy

### 5.1 Unit Tests

```python
def test_validate_within_radius():
    """測試：在範圍內"""
    service = LocationValidationService(db)
    
    result = service.validate_location(
        location=LocationPayload(
            latitude=25.0330,
            longitude=121.5654,
            accuracy=15.5,
            captured_at=datetime.now()
        ),
        target_lat=25.0335,
        target_lng=121.5660,
        allowed_radius_m=100
    )
    
    assert result.is_valid is True
    assert result.is_within_radius is True
    assert result.distance_meters < 100

def test_validate_outside_radius():
    """測試：超出範圍"""
    # ...

def test_validate_no_restriction():
    """測試：無限制"""
    # ...

def test_validate_invalid_coordinates():
    """測試：無效座標"""
    # ...

def test_validate_accuracy_too_low():
    """測試：精度不足"""
    # ...
```

---

## 6. Error Handling

### 6.1 Validation Errors

| 錯誤碼 | HTTP Status | 說明 |
|--------|-------------|------|
| `INVALID_COORDINATES` | 422 | 座標格式錯誤 |
| `ACCURACY_TOO_LOW` | 422 | 精度不足 |
| `LOCATION_REQUIRED` | 422 | 必須提供定位 |
| `OUTSIDE_ALLOWED_RADIUS` | 403 | 超出允許範圍 |
| `TARGET_NOT_CONFIGURED` | 500 | 目標點未設定 |

---

## 7. Performance Considerations

- **距離計算**: O(1)，非常快
- **快取政策**: 定位政策可快取（很少變動）
- **索引優化**: GPS 欄位建立 partial index

---

## 8. Definition of Done

- [ ] `LocationValidationService` 實作完成
- [ ] 單元測試覆蓋率 > 90%
- [ ] 整合到 punch-in/punch-out API
- [ ] 錯誤處理完整
- [ ] 文件更新

---

**文件狀態**: ✅ DRAFT  
**下一步**: 建立 `ATTENDANCE_LOCATION_DATA_MODEL_OPTIONS.md`

---

**END OF PLAN**
