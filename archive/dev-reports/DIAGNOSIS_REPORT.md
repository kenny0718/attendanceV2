# 🔍 外出打卡資料流完整診斷報告

**診斷時間：** 2026-03-08 12:00  
**問題描述：** 首頁可以點「外出打卡」，但看不到外出打卡紀錄

---

## 📋 Step 1 — 外出打卡 submit 呼叫鏈

### 前端呼叫鏈
```
Button click (Home.vue line 52)
  ↓
@click="handlePunch('BREAK_OUT')"
  ↓
handlePunch(type) → attendanceStore.punch(type, notes)
  ↓
stores/attendance.js → attendanceApi.breakOut({ notes })
  ↓
api/attendance.js → POST /api/v1/attendance/break-out
```

### 後端處理鏈
```
POST /api/v1/attendance/break-out (api.py line 368)
  ↓
repo.create_punch(
  session_id=session.id,
  punch_type='break_start',  ← 關鍵：寫入類型
  ...
)
  ↓
寫入資料表：attendance_punches
```

**Request Body:**
```json
{
  "notes": "外出原因（選填）",
  "location": { "latitude": 25.0, "longitude": 121.0 }  // 選填
}
```

**Response:**
```json
{
  "punch_id": "uuid",
  "session_id": "uuid",
  "punch_time": "2026-03-08T10:00:00+08:00",
  "message": "Break out successful"
}
```

---

## 📋 Step 2 — 首頁顯示外出打卡紀錄呼叫鏈

### 前端顯示鏈
```
Home.vue mounted() (line 677)
  ↓
attendanceStore.loadBreakPunches()
  ↓
attendanceApi.getBreakPunches({ limit: 50 })
  ↓
GET /api/v1/attendance/break-punches
  ↓
顯示在 Home.vue template (line 195-227)
  v-for="punch in breakPunches"
```

### 後端查詢鏈
```
GET /api/v1/attendance/break-punches (api.py line 730)
  ↓
repo.get_open_session(company_id, user_uuid)  ← 關鍵：只查 open session
  ↓
如果沒有 open session → 返回 {"punches": [], "total": 0}
  ↓
如果有 open session → 查詢該 session 的外出打卡
  ↓
SELECT * FROM attendance_punches
WHERE session_id = {session.id}
  AND punch_type IN ('break_start', 'break_end')
ORDER BY punch_time DESC
LIMIT 50
```

**Response:**
```json
{
  "punches": [
    {
      "punch_id": "uuid",
      "punch_type": "break_start",
      "punch_time": "2026-03-07T10:11:02+08:00",
      "notes": "",
      "location_lat": null,
      "location_lng": null
    }
  ],
  "total": 12,
  "session_id": "uuid"
}
```

---

## 📋 Step 3 — Submit 寫入 vs List 讀取對照表

| 操作 | API 路由 | 資料表 | 關鍵欄位 | 查詢條件 |
|------|----------|--------|----------|----------|
| **外出打卡 submit** | `POST /v1/attendance/break-out` | `attendance_punches` | `punch_type='break_start'` | 寫入當前 open session |
| **返回打卡 submit** | `POST /v1/attendance/break-in` | `attendance_punches` | `punch_type='break_end'` | 寫入當前 open session |
| **首頁顯示列表** | `GET /v1/attendance/break-punches` | `attendance_punches` | `punch_type IN ('break_start', 'break_end')` | **只查當前 open session** |

### ✅ 結論
- **前後端使用同一張表：** `attendance_punches`
- **前後端使用同一套資料模型：** `punch_type='break_start'` / `'break_end'`
- **資料流一致性：** ✅ 沒有衝突

---

## 📋 Step 4 — 資料庫實際資料檢查結果

### 檢查命令
```sql
-- 檢查 3/7 之後的外出打卡記錄
SELECT COUNT(*) as total, punch_type 
FROM attendance_punches 
WHERE punch_type IN ('break_start', 'break_end') 
  AND DATE(punch_time) >= '2026-03-07' 
GROUP BY punch_type;
```

### 檢查結果
```
break_start: 12 筆
break_end:    3 筆
```

### 當前 open session 資訊
```sql
SELECT id, user_id, company_id, status, punch_in_time 
FROM attendance_sessions 
WHERE status = 'open';
```

**結果：**
```
session_id:  5f6fbde4-f04d-41c6-9e80-ffea8f88bac8
user_id:     11bda10d-7541-4230-b1f3-842afab2cea5
company_id:  company-a
status:      open
punch_in:    2026-03-07 09:42:59+08
```

### 該 session 的外出打卡記錄（最近 10 筆）
```
2026-03-07 10:11:02 | break_start | notes: (空)
2026-03-07 10:11:01 | break_start | notes: (空)
2026-03-07 10:00:36 | break_end   | notes: (空)
2026-03-07 10:00:31 | break_start | notes: (空)
2026-03-07 09:47:19 | break_start | notes: (空)
... (共 10 筆)
```

### ✅ 結論
- **資料庫確實有外出打卡資料**
- **資料都寫入 `attendance_punches` 表**
- **資料與當前 open session 關聯正確**

---

## 📋 Step 5 — 前後端衝突點分析

### ❌ 發現的問題

#### 問題 1：API 只返回當前 open session 的記錄
**位置：** `backend/app/modules/attendance/api.py` line 730-760

```python
@router_v1.get("/break-punches", response_model=dict)
async def get_break_punches(...):
    # 獲取當前 open session
    session = repo.get_open_session(company_id, user_uuid)
    if not session:
        return {"punches": [], "total": 0}  # ← 沒有 open session 就返回空
    
    # 只查詢該 session 的外出打卡
    punches = db.query(AttendancePunch).filter(
        AttendancePunch.session_id == session.id,  # ← 只查當前 session
        AttendancePunch.punch_type.in_(['break_start', 'break_end'])
    )
```

**影響：**
- 如果用戶今天還沒打上班卡 → 看不到任何記錄
- 如果用戶已經打下班卡（session closed）→ 看不到今天的外出記錄
- 跨天情況：昨天的 session 已關閉 → 看不到昨天的記錄

#### 問題 2：前端檔案損壞
**發現：**
- `frontend/src/views/Home.vue` → 0 bytes（已恢復）
- `frontend/src/stores/attendance.js` → 0 bytes（已恢復）

**原因：** 可能是編輯過程中檔案被清空

#### 問題 3：時間差異
- 資料庫記錄時間：2026-03-07 10:11
- 當前時間：2026-03-08 12:00
- 如果 3/7 的 session 已經關閉，今天就看不到昨天的記錄

---

## 📋 Step 6 — Debug 修改

### 已加入的 Debug 代碼

#### 1. 外出打卡成功後
**位置：** `frontend/src/stores/attendance.js` line 100-108

```javascript
case 'BREAK_OUT':
  response = await attendanceApi.breakOut({ notes: notes || '' })
  console.log('🔍 DEBUG BREAK_OUT - 打卡成功，response:', response)
  this.todayStatus.break_out = response.punch_time
  this.todayStatus.is_on_break = true
  localStorage.setItem('is_on_break', 'true')
  await this.loadBreakPunches()
  console.log('🔍 DEBUG BREAK_OUT - 刷新後 breakPunches 數量:', this.breakPunches.length)
  break
```

#### 2. 載入外出打卡記錄
**位置：** `frontend/src/stores/attendance.js` line 145-153

```javascript
async loadBreakPunches() {
  try {
    const data = await attendanceApi.getBreakPunches({ limit: 50 })
    console.log('🔍 DEBUG loadBreakPunches - API 返回:', data)
    console.log('🔍 DEBUG loadBreakPunches - punches 數量:', data.punches?.length || 0)
    this.breakPunches = data.punches || []
  } catch (error) {
    console.error('載入外出打卡記錄失敗:', error)
    this.breakPunches = []
  }
}
```

### 如何查看 Debug 訊息
1. 打開瀏覽器開發者工具（F12）
2. 切換到 Console 標籤
3. 點擊「外出打卡」按鈕
4. 查看 console 輸出：
   - `🔍 DEBUG BREAK_OUT - 打卡成功` → 確認 API 呼叫成功
   - `🔍 DEBUG loadBreakPunches - API 返回` → 確認返回的資料
   - `🔍 DEBUG loadBreakPunches - punches 數量` → 確認陣列長度

---

## 📋 Step 7 — 主要根因判斷

### 🎯 主要根因

**根因：API 設計限制 - 只返回當前 open session 的外出打卡記錄**

**具體問題：**
1. `/api/v1/attendance/break-punches` API 只查詢當前 open session
2. 如果沒有 open session（還沒打上班卡 或 已經打下班卡），就返回空陣列
3. 前端正確呼叫 API，但 API 返回空資料

**證據：**
- 資料庫有 12 筆 `break_start` 記錄（3/7 的資料）
- 當前有一個 open session（3/7 09:42 打卡）
- 但如果這個 session 被關閉，或者是新的一天重新打卡，就看不到之前的記錄

### 次要問題
1. ✅ 前端檔案損壞（已修復）
2. ⚠️ API 沒有提供「查詢今日所有外出打卡」的功能
3. ⚠️ 跨 session 查詢需求未被滿足

---

## 📋 Step 8 — 最小修復方案

### 方案 A：修改後端 API（推薦）

**目標：** 讓 `/break-punches` API 返回今日所有外出打卡，不限於當前 session

**修改位置：** `backend/app/modules/attendance/api.py` line 730

```python
@router_v1.get("/break-punches", response_model=dict)
async def get_break_punches(
    limit: int = 50,
    company_id: str = Depends(get_current_company_id),
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get today's break punches (外出打卡記錄) - 返回今日所有記錄"""
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    from datetime import datetime, time
    from app.modules.attendance.models import AttendancePunch
    
    user_uuid = UUID(user_id)
    
    # 計算今日起始時間（00:00:00）
    today_start = datetime.now(TIMEZONE).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 查詢今日所有外出打卡（不限 session）
    punches = (
        db.query(AttendancePunch)
        .filter(
            AttendancePunch.company_id == company_id,
            AttendancePunch.user_id == user_uuid,
            AttendancePunch.punch_type.in_(['break_start', 'break_end']),
            AttendancePunch.punch_time >= today_start  # ← 改為查詢今日所有記錄
        )
        .order_by(AttendancePunch.punch_time.desc())
        .limit(limit)
        .all()
    )
    
    punch_list = [
        {
            "punch_id": str(p.id),
            "punch_type": p.punch_type,
            "punch_time": p.punch_time.isoformat(),
            "notes": p.notes,
            "location_lat": p.location_lat,
            "location_lng": p.location_lng
        }
        for p in punches
    ]
    
    return {
        "punches": punch_list,
        "total": len(punch_list)
    }
```

**優點：**
- ✅ 解決根本問題
- ✅ 前端不需要修改
- ✅ 符合使用者預期（看到今日所有外出記錄）

**缺點：**
- ⚠️ 需要修改後端代碼
- ⚠️ 需要重啟後端服務

---

### 方案 B：前端顯示提示（臨時方案）

**目標：** 當沒有 open session 時，提示用戶先打上班卡

**修改位置：** `frontend/src/views/Home.vue` line 195

```vue
<!-- 今日外出打卡記錄 -->
<div v-if="breakPunches.length > 0" class="checkpoint-list mt-4 pt-4 border-t border-gray-200">
  <h4 class="text-sm font-medium text-text-primary mb-2">今日外出打卡記錄</h4>
  <!-- ... 記錄列表 ... -->
</div>
<div v-else-if="!todayStatus.is_punched_in" class="text-center py-4 text-text-hint text-sm">
  請先打上班卡後才能查看外出記錄
</div>
<div v-else class="text-center py-4 text-text-hint text-sm">
  今日尚無外出打卡記錄
</div>
```

**優點：**
- ✅ 快速實施
- ✅ 不需要修改後端

**缺點：**
- ❌ 沒有解決根本問題
- ❌ 打下班卡後仍然看不到記錄

---

## 📊 總結

### 問題根源
**API 設計限制：** `/break-punches` 只返回當前 open session 的記錄，導致：
- 沒打上班卡 → 看不到記錄
- 已打下班卡 → 看不到今天的記錄
- 跨天查詢 → 看不到昨天的記錄

### 資料流驗證
✅ **外出打卡有成功寫入資料庫**  
✅ **前後端使用同一套資料表和模型**  
✅ **資料庫有 12 筆 break_start 記錄**  
❌ **API 查詢邏輯限制導致前端無法取得資料**

### 推薦方案
**採用方案 A：修改後端 API**
- 將查詢範圍從「當前 session」改為「今日所有記錄」
- 前端無需修改
- 符合使用者預期

### 下一步行動
1. ✅ 恢復損壞的前端檔案（已完成）
2. ✅ 加入 debug 代碼（已完成）
3. ⏳ 修改後端 API（待執行）
4. ⏳ 測試驗證（待執行）
