# WP-11-13 BREAK_OUT Location Policy Enforcement Patch

## 修改檔案：backend/app/modules/attendance/api.py

### 修改位置：break_out endpoint

在 `@router_v1.post("/break-out")` endpoint 中加入以下修改：

### 1. 更新 docstring

```python
"""Break out (外出打卡) - WP-11-11.5 Blocker Fix, WP-11-13 Location Policy

允許連續外出打卡，不需要先返回

WP-11-13: 加入 location policy 後端 authoritative enforcement
"""
```

### 2. 在 "Get open session" 之後，"Create break_start punch" 之前插入：

```python
# WP-11-13: Location policy enforcement (後端 authoritative)
matched_location_id = None
if request.location:
    from app.modules.attendance.location_policy_service import get_location_policy_service
    
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
    
    # 記錄匹配的 location_id
    if policy_check.matched_location:
        matched_location_id = UUID(policy_check.matched_location["id"])
```

### 3. 修改 repo.create_punch() 呼叫

在 `repo.create_punch()` 的參數中加入：

```python
location_id=matched_location_id  # WP-11-13: 記錄匹配的地點
```

完整的 create_punch 呼叫應該是：

```python
punch = repo.create_punch(
    session_id=session.id,
    company_id=company_id,
    user_id=user_uuid,
    punch_type='break_start',
    punch_time=punch_time,
    ip_address=ip_address,
    location_lat=request.location.latitude if request.location else None,
    location_lng=request.location.longitude if request.location else None,
    notes=request.notes,
    location_id=matched_location_id  # WP-11-13: 記錄匹配的地點
)
```

---

## 修改檔案：backend/app/modules/attendance/repo.py

### 修改位置：create_punch method

在 `create_punch()` method 的參數中加入：

```python
location_id: Optional[UUID] = None
```

在建立 AttendancePunch 物件時加入：

```python
location_id=location_id
```

完整的 method signature 應該是：

```python
def create_punch(
    self,
    session_id: UUID,
    company_id: str,
    user_id: UUID,
    punch_type: str,
    punch_time: datetime,
    ip_address: Optional[str] = None,
    location_lat: Optional[float] = None,
    location_lng: Optional[float] = None,
    notes: Optional[str] = None,
    location_id: Optional[UUID] = None  # WP-11-13
) -> AttendancePunch:
```

---

## 注意事項

1. 這些修改確保後端有 authoritative enforcement
2. 即使前端沒有做 precheck，後端仍會獨立驗證
3. 只在有 location 時才檢查 policy
4. 沒有 allowed locations 時允許任何地點（向後相容）
5. matched_location_id 會被記錄到 attendance_punches.location_id

---

## 測試要點

1. 有 location + 在範圍內 → 成功，記錄 location_id
2. 有 location + 超出範圍 → 403 錯誤
3. 無 location + 無規則 → 成功（向後相容）
4. 無 location + 有規則 → 成功（v1 不強制要求 location）
5. 不破壞既有 BREAK_OUT 流程
