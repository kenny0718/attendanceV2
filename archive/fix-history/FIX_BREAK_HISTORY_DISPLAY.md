# 修復外出打卡記錄顯示問題

**修復日期**: 2026-03-06 18:29  
**問題**: 連續外出打卡功能正常，但記錄顯示不正確

---

## 問題描述

用戶反映：
- ✅ 可以連續外出打卡（功能正常）
- ❌ 但是"今日外出記錄"顯示有問題，所有記錄看起來一樣

## 根本原因

1. **後端 `history` API 只返回 sessions**
   - 只包含上班/下班時間
   - 不包含 session 內的 punches（外出/返回打卡記錄）

2. **前端 `fetchRecentLogs` 只顯示 session**
   - 只轉換 session 的上班/下班時間
   - 忽略了 punches 數據

3. **外出/返回打卡存儲在 `attendance_punches` 表**
   - `punch_type = 'break_start'` (外出)
   - `punch_type = 'break_end'` (返回)
   - 這些記錄沒有被查詢和顯示

## 修復方案

### 1. 後端修改

#### 1.1 schemas.py - 添加 PunchResponse
```python
class PunchResponse(BaseModel):
    """Single punch record response"""
    punch_id: UUID
    punch_type: str  # in/out/break_start/break_end
    punch_time: datetime
    notes: Optional[str]
```

#### 1.2 schemas.py - 更新 SessionResponse
```python
class SessionResponse(BaseModel):
    # ... 原有字段 ...
    punches: Optional[list] = Field(default_factory=list, 
        description="All punches in this session")
```

#### 1.3 repo.py - 添加 get_session_punches 方法
```python
def get_session_punches(self, session_id: UUID) -> list:
    """獲取 session 的所有 punch 記錄"""
    return (
        self.db.query(AttendancePunch)
        .filter(AttendancePunch.session_id == session_id)
        .order_by(AttendancePunch.punch_time.asc())
        .all()
    )
```

#### 1.4 api.py - 修改 get_attendance_history
```python
# 為每個 session 查詢並附加 punches
for s in sessions:
    punches = repo.get_session_punches(s.id)
    punch_list = [
        {
            'punch_id': str(p.id),
            'punch_type': p.punch_type,
            'punch_time': p.punch_time,
            'notes': p.notes
        }
        for p in punches
    ]
    
    session_responses.append(
        SessionResponse(..., punches=punch_list)
    )
```

### 2. 前端修改

#### 2.1 attendance.js - 更新 fetchRecentLogs
```javascript
async fetchRecentLogs() {
  const data = await attendanceApi.getHistory({ limit: 10, offset: 0 })
  
  const allLogs = []
  data.sessions.forEach(session => {
    if (session.punches && session.punches.length > 0) {
      // 展開所有 punch 記錄
      session.punches.forEach(punch => {
        allLogs.push({
          id: punch.punch_id,
          timestamp: punch.punch_time,
          attendance_type: this.getPunchTypeLabel(punch.punch_type),
          status: 'success',
          notes: punch.notes
        })
      })
    }
  })
  
  // 按時間倒序排列
  this.recentLogs = allLogs.sort((a, b) => 
    new Date(b.timestamp) - new Date(a.timestamp)
  ).slice(0, 20)
}
```

#### 2.2 添加 getPunchTypeLabel 方法
```javascript
getPunchTypeLabel(punchType) {
  const typeMap = {
    'in': 'IN',
    'out': 'OUT',
    'break_start': 'BREAK_OUT',
    'break_end': 'BREAK_IN'
  }
  return typeMap[punchType] || punchType.toUpperCase()
}
```

## 修改文件

### 後端
- `backend/app/modules/attendance/schemas.py`
  - 備份: `schemas.py.backup.20260306_182833`
- `backend/app/modules/attendance/repo.py`
  - 備份: `repo.py.backup.20260306_182902`
- `backend/app/modules/attendance/api.py`
  - 備份: `api.py.backup.20260306_182849`

### 前端
- `frontend/src/stores/attendance.js`
  - 備份: `attendance.js.backup.20260306_182923`

## 效果

修復後，"最近打卡記錄"區塊將顯示：
- ✅ 上班打卡 (IN)
- ✅ 外出打卡 (BREAK_OUT) - 可以有多筆
- ✅ 返回打卡 (BREAK_IN)
- ✅ 下班打卡 (OUT)
- ✅ 自動補返回 (BREAK_IN，備註：自動返回（下班時補）)

所有記錄按時間倒序排列，最多顯示 20 筆。

## 測試驗證

### 測試場景
1. 上班打卡
2. 外出打卡（第1次）
3. 外出打卡（第2次）
4. 外出打卡（第3次）
5. 返回打卡
6. 下班打卡

### 預期結果
"最近打卡記錄"應該顯示 6 筆記錄：
- 下班 (OUT) - 最新
- 返回 (BREAK_IN)
- 外出 (BREAK_OUT) - 第3次
- 外出 (BREAK_OUT) - 第2次
- 外出 (BREAK_OUT) - 第1次
- 上班 (IN) - 最早

## 部署狀態

- ✅ 後端代碼已修改
- ✅ 前端代碼已修改並重新編譯
- ✅ 後端服務已重啟（18:29:55）
- ✅ 所有修改已備份

## 注意事項

1. **清除瀏覽器緩存**: 用戶需要 Ctrl+F5 強制刷新
2. **API 變更**: `SessionResponse` 新增 `punches` 字段，向後兼容
3. **性能**: 每個 session 會額外查詢一次 punches，如果記錄很多可能需要優化

---

**修復完成**: 2026-03-06 18:29:55  
**狀態**: ✅ 已完成並部署
