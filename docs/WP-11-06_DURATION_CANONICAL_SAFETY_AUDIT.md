# Duration Canonical Safety Audit Report

**審計日期：** 2026-03-13  
**審計範圍：** Backend + Frontend  
**審計目的：** 驗證 `duration_minutes` canonical 欄位是否可能被 break/out/return 流程污染

---

## 執行摘要

**最終判定：✅ SAFE — duration_minutes isolated**

**核心發現：**
1. ✅ `duration_minutes` 只在 `punch_out` 時寫入一次
2. ✅ Break punches 完全隔離，不影響 canonical duration
3. ✅ Out checkpoints 完全隔離，不影響 session duration
4. ✅ Frontend 只讀取 backend canonical 欄位，無重新計算

---

## 1. Write Path List

### 1.1 duration_minutes 寫入位置

| File | Function | Line | What | Trigger |
|------|----------|------|------|---------|
| `api.py` | `punch_out()` | 141 | `duration_minutes = int((punch_out_time - session.punch_in_time).total_seconds() / 60)` | Punch out 時計算 |
| `api.py` | `punch_out()` | 144 | `session.duration_minutes = duration_minutes` | 寫入 session 物件 |
| `repo.py` | `close_session()` | 98 | `session.duration_minutes = duration_minutes` | 接收計算值並持久化 |

**計算規則：**
```python
duration_minutes = int((punch_out_time - session.punch_in_time).total_seconds() / 60)
```

**確認：**
- ✅ 只使用 `punch_in_time` 和 `punch_out_time`
- ✅ 不涉及 break punches
- ✅ 不涉及 out checkpoints
- ✅ 計算發生在 `punch_out` endpoint，一次性寫入

---

### 1.2 Break Flow 路徑

| File | Function | Line | What | Impact on duration_minutes |
|------|----------|------|------|----------------------------|
| `api.py` | `break_out()` | 206-241 | 創建 `punch_type="break_start"` punch | ❌ 無影響 |
| `api.py` | `break_in()` | 246-268 | 創建 `punch_type="break_end"` punch | ❌ 無影響 |
| `repo.py` | `create_punch()` | 115-152 | 寫入 `attendance_punches` 表 | ❌ 無影響 |

**確認：**
- ✅ Break punches 只寫入 `attendance_punches` 表
- ✅ 不修改 `attendance_sessions.duration_minutes`
- ✅ 不修改 `attendance_sessions.punch_out_time`
- ✅ 不修改 `attendance_sessions.status`

**Break flow 完整路徑：**
```
break_out() 
  → repo.create_punch(punch_type="break_start")
    → INSERT INTO attendance_punches
      → 不觸及 attendance_sessions.duration_minutes
```

---

### 1.3 Out Checkpoint 路徑

| File | Function | Line | What | Impact on duration_minutes |
|------|----------|------|------|----------------------------|
| `api.py` | `create_out_checkpoint()` | 328-391 | 創建 out checkpoint 記錄 | ❌ 無影響 |
| `repo.py` | `OutCheckpointRepository.create_checkpoint()` | 340-380 | 寫入 `attendance_out_checkpoints` 表 | ❌ 無影響 |

**確認：**
- ✅ Out checkpoints 寫入獨立表 `attendance_out_checkpoints`
- ✅ 不修改 `attendance_sessions` 任何欄位
- ✅ 只關聯 `session_id`（可為 NULL）

**Out checkpoint 完整路徑：**
```
create_out_checkpoint()
  → OutCheckpointRepository.create_checkpoint()
    → INSERT INTO attendance_out_checkpoints
      → 完全不觸及 attendance_sessions 表
```

---

### 1.4 Frontend 讀取路徑

| File | Location | What | Risk |
|------|----------|------|------|
| `stores/attendance.js` | Line 493 | `duration_minutes: session.duration_minutes` | ✅ 只讀取 backend 欄位 |
| `TodayStatusSection.vue` | - | 只顯示 `punch_in` / `punch_out` 時間 | ✅ 無工時計算 |
| `AttendanceOverviewCard.vue` | - | 只傳遞 props，無計算邏輯 | ✅ 無工時計算 |

**確認：**
- ✅ Frontend 無任何 `duration_minutes` 計算邏輯
- ✅ 無 `punch_out_time - punch_in_time` 計算
- ✅ 無 dayjs diff 計算工時
- ✅ 只顯示 backend 回傳的 canonical 欄位

**Frontend 搜尋結果：**
```bash
grep -rn "duration\|elapsed\|work.*hour" frontend/src --include="*.vue"
# 結果：無任何工時計算邏輯
```

---

## 2. Risk Table

| Area | Finding | Risk Level | Detail |
|------|---------|------------|--------|
| **Canonical Write** | `duration_minutes` 只在 `punch_out` 時寫入一次 | 🟢 SAFE | 計算規則明確：`punch_out_time - punch_in_time` |
| **Break Flow** | Break punches 完全隔離 | 🟢 SAFE | 只寫入 `attendance_punches` 表，不觸及 session |
| **Out Checkpoint** | Out checkpoints 完全隔離 | 🟢 SAFE | 獨立表 `attendance_out_checkpoints`，不觸及 session |
| **Frontend Recalc** | Frontend 無工時計算 | 🟢 SAFE | 只讀取 backend `duration_minutes` 欄位 |
| **Reporting** | 報表只讀取 canonical 欄位 | 🟢 SAFE | `recentLogs` 直接使用 `session.duration_minutes` |
| **Break Duration** | Break duration 未實作 | 🟡 INFO | 目前無 break duration 計算，未來需注意隔離 |

---

## 3. Detailed Findings

### 3.1 Canonical Duration Source

**寫入位置：** `backend/app/modules/attendance/api.py:141-148`

```python
# Line 141: 計算
duration_minutes = int((punch_out_time - session.punch_in_time).total_seconds() / 60)

# Line 143: 寫入 session 物件
session.punch_out_time = punch_out_time
session.duration_minutes = duration_minutes
session.status = "closed"

# Line 147: 持久化
session = repo.close_session(
    session=session, 
    punch_out_time=punch_out_time,
    duration_minutes=duration_minutes,  # 傳遞計算值
    policy_id=policy.id if policy else None
)
```

**確認：**
- ✅ 計算規則：`(punch_out_time - punch_in_time).total_seconds() / 60`
- ✅ 只使用 session 的 `punch_in_time` 和 `punch_out_time`
- ✅ 不涉及任何 break punches
- ✅ 不涉及任何 out checkpoints
- ✅ 一次性寫入，無後續修改

---

### 3.2 Break Flow Impact

**Break Out 流程：** `api.py:206-241`

```python
@router_v1.post("/break-out", response_model=BreakOutResponse, status_code=201)
async def break_out(...):
    # 1. 獲取 open session
    session = repo.get_open_session(company_id, user_uuid)
    
    # 2. 創建 break_start punch
    punch = repo.create_punch(
        session_id=session.id,
        punch_type="break_start",  # 只是事件記錄
        punch_time=punch_time,
        ...
    )
    
    # 3. 回傳 punch 資訊
    return BreakOutResponse(punch_id=punch.id, ...)
    
    # ✅ 確認：完全不觸及 session.duration_minutes
```

**Break In 流程：** `api.py:246-268`

```python
@router_v1.post("/break-in", response_model=BreakInResponse, status_code=201)
async def break_in(...):
    # 1. 獲取 open session
    session = repo.get_open_session(company_id, user_uuid)
    
    # 2. 創建 break_end punch
    punch = repo.create_punch(
        session_id=session.id,
        punch_type="break_end",  # 只是事件記錄
        punch_time=punch_time,
        ...
    )
    
    # 3. 回傳 punch 資訊
    return BreakInResponse(punch_id=punch.id, ...)
    
    # ✅ 確認：完全不觸及 session.duration_minutes
```

**資料庫層級隔離：**
```
attendance_sessions (session 主表)
  ├─ id (PK)
  ├─ punch_in_time
  ├─ punch_out_time
  └─ duration_minutes  ← Canonical 欄位

attendance_punches (事件記錄表)
  ├─ id (PK)
  ├─ session_id (FK)
  ├─ punch_type (in/out/break_start/break_end)
  └─ punch_time
  
  ✅ 兩表完全隔離，break punches 不影響 session.duration_minutes
```

---

### 3.3 Out Checkpoint Impact

**Out Checkpoint 流程：** `api.py:328-391`

```python
@router_v1.post("/out-checkpoint", status_code=201)
async def create_out_checkpoint(...):
    # 1. 獲取 open session（可選）
    open_session = s_repo.get_open_session(company_id, user_uuid)
    session_id = open_session.id if open_session else None
    
    # 2. 創建 checkpoint（獨立表）
    cp = ck_repo.create_checkpoint(
        company_id=company_id,
        user_id=user_uuid,
        session_id=session_id,  # 只是關聯，不修改 session
        device_type=request.device_type,
        punch_time=punch_time,
        gps_lat=...,
        ...
    )
    
    # 3. 回傳 checkpoint 資訊
    return {"checkpoint_id": str(cp.id), ...}
    
    # ✅ 確認：完全不觸及 attendance_sessions 表
```

**資料庫層級隔離：**
```
attendance_sessions (session 主表)
  └─ duration_minutes  ← Canonical 欄位

attendance_out_checkpoints (獨立表)
  ├─ id (PK)
  ├─ session_id (FK, nullable)  ← 只是關聯
  ├─ punch_time
  └─ gps_lat, gps_lng, ...
  
  ✅ 完全獨立的表，不影響 session.duration_minutes
```

---

### 3.4 Frontend Recalculation Risk

**搜尋結果：**
```bash
# 搜尋工時計算相關代碼
grep -rn "duration\|elapsed\|work.*hour\|total.*hour" frontend/src --include="*.vue" --include="*.js"

# 結果：只有一處讀取
frontend/src/stores/attendance.js:493: duration_minutes: session.duration_minutes
```

**Frontend 使用方式：**

```javascript
// stores/attendance.js:493
this.recentLogs = data.sessions.map(session => {
  return {
    id: session.session_id,
    timestamp: isPunchOut ? session.punch_out_time : session.punch_in_time,
    attendance_type: isPunchOut ? 'OUT' : 'IN',
    status: 'success',
    is_late: false,
    duration_minutes: session.duration_minutes  // ✅ 只讀取，不計算
  }
})
```

**確認：**
- ✅ Frontend 只讀取 `session.duration_minutes`
- ✅ 無任何 `punch_out_time - punch_in_time` 計算
- ✅ 無任何 dayjs diff 計算
- ✅ 無任何 JS 工時重新計算

---

### 3.5 Reporting Pollution Risk

**History API Response：** `api.py:184-203`

```python
@router_v1.get("/history", response_model=AttendanceHistoryResponse)
async def get_attendance_history(...):
    sessions = repo.get_sessions(...)
    
    sr_list = [
        SessionResponse(
            session_id=s.id,
            user_id=s.user_id,
            company_id=s.company_id,
            punch_in_time=s.punch_in_time,
            punch_out_time=s.punch_out_time,
            duration_minutes=s.duration_minutes,  # ✅ 直接讀取 canonical 欄位
            status=s.status
        ) 
        for s in sessions
    ]
    
    return AttendanceHistoryResponse(sessions=sr_list, ...)
```

**確認：**
- ✅ 報表 API 直接讀取 `session.duration_minutes`
- ✅ 不重新計算工時
- ✅ 不混合 break punches
- ✅ 不混合 out checkpoints

---

## 4. Architecture Verification

### 4.1 資料表隔離

```
attendance_sessions (主表)
  ├─ id (PK)
  ├─ punch_in_time
  ├─ punch_out_time
  ├─ duration_minutes  ← Canonical 欄位
  └─ status

attendance_punches (事件表)
  ├─ id (PK)
  ├─ session_id (FK)
  ├─ punch_type (in/out/break_start/break_end)
  └─ punch_time

attendance_out_checkpoints (獨立表)
  ├─ id (PK)
  ├─ session_id (FK, nullable)
  ├─ punch_time
  └─ gps_lat, gps_lng, ...
```

**隔離驗證：**
- ✅ `duration_minutes` 只存在於 `attendance_sessions` 表
- ✅ Break punches 只寫入 `attendance_punches` 表
- ✅ Out checkpoints 只寫入 `attendance_out_checkpoints` 表
- ✅ 三個表之間無 trigger 或 cascade update

---

### 4.2 Write Path 隔離

```
Punch Out Flow:
  punch_out() 
    → 計算 duration_minutes
    → session.duration_minutes = duration_minutes
    → repo.close_session()
      → DB UPDATE attendance_sessions SET duration_minutes = ?
        ✅ 唯一寫入路徑

Break Flow:
  break_out() / break_in()
    → repo.create_punch(punch_type="break_start/break_end")
      → DB INSERT INTO attendance_punches
        ✅ 不觸及 attendance_sessions.duration_minutes

Out Checkpoint Flow:
  create_out_checkpoint()
    → OutCheckpointRepository.create_checkpoint()
      → DB INSERT INTO attendance_out_checkpoints
        ✅ 不觸及 attendance_sessions 表
```

---

## 5. Future Risk Assessment

### 5.1 潛在風險點（目前不存在）

| 潛在風險 | 當前狀態 | 建議 |
|---------|---------|------|
| Break duration 計算 | ❌ 未實作 | 若未來實作，必須隔離於獨立欄位（如 `break_duration_minutes`），不可污染 `duration_minutes` |
| Out checkpoint duration | ❌ 未實作 | 若未來實作，必須隔離於獨立欄位，不可污染 `duration_minutes` |
| Frontend 工時顯示 | ✅ 只讀取 backend | 維持現狀，禁止 JS 重新計算 |
| 報表層重新計算 | ✅ 只讀取 canonical | 維持現狀，禁止 SQL 重新計算 |

---

### 5.2 Code Review Checklist（未來開發）

若未來需要實作 break duration 或其他工時相關功能，必須遵守：

```markdown
## Duration Canonical Safety Checklist

- [ ] 新功能不修改 `attendance_sessions.duration_minutes`
- [ ] 新功能使用獨立欄位（如 `break_duration_minutes`）
- [ ] 新功能不在 `punch_out` 流程中插入計算邏輯
- [ ] Frontend 不重新計算工時
- [ ] 報表層不重新計算工時
- [ ] 所有工時計算集中於 Work Hour Engine
```

---

## 6. Final Verdict

**✅ SAFE — duration_minutes isolated**

**理由：**

1. **Canonical 寫入隔離**
   - `duration_minutes` 只在 `punch_out` 時寫入一次
   - 計算規則明確：`punch_out_time - punch_in_time`
   - 無其他路徑可修改此欄位

2. **Break Flow 完全隔離**
   - Break punches 只寫入 `attendance_punches` 表
   - 不觸及 `attendance_sessions.duration_minutes`
   - 資料庫層級完全隔離

3. **Out Checkpoint 完全隔離**
   - Out checkpoints 寫入獨立表 `attendance_out_checkpoints`
   - 完全不觸及 `attendance_sessions` 表
   - 只有 `session_id` 關聯（FK），無 cascade update

4. **Frontend 無重新計算**
   - Frontend 只讀取 backend `duration_minutes` 欄位
   - 無任何 JS 工時計算邏輯
   - 符合 SA v2.1 §30 Report Consistency Rule

5. **報表層無污染**
   - 報表 API 直接讀取 `session.duration_minutes`
   - 不混合 break punches 或 out checkpoints
   - 不重新計算工時

**結論：**

當前系統架構下，`duration_minutes` canonical 欄位完全隔離且安全。Break punches 和 out checkpoints 均為獨立的事件記錄，不影響 session 的 canonical work duration。

---

**審計完成時間：** 2026-03-13  
**審計人員：** AI Assistant  
**下次審計建議：** 若未來實作 break duration 計算，需重新審計
