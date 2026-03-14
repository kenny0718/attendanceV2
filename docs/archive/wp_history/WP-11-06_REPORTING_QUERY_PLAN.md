# WP-11-06 Reporting Query Plan

**文件版本：** 1.0  
**建立日期：** 2026-03-13  
**目的：** 定義報表查詢的標準規範與安全模式  
**狀態：** ACTIVE

---

## 目錄

1. [核心規範](#核心規範)
2. [查詢模式](#查詢模式)
3. [禁止模式](#禁止模式)
4. [標準查詢範例](#標準查詢範例)
5. [性能優化](#性能優化)
6. [Code Review Checklist](#code-review-checklist)

---

## 核心規範

### 規範 1：Session 歸屬日期

**來源：** SA v2.1 §29.2 Session Ownership Date

```
session 的所屬日期 = punch_in_time 的業務時區（Asia/Taipei）日期
```

**實作：**

```python
from zoneinfo import ZoneInfo
TZ_TAIPEI = ZoneInfo("Asia/Taipei")

# 計算 session 歸屬日期
punch_in_utc = session.punch_in_time  # UTC datetime
punch_in_taipei = punch_in_utc.astimezone(TZ_TAIPEI)
session_date = punch_in_taipei.date()
```

**跨午夜範例：**

```python
# 範例：2026-03-31 23:00 上班，2026-04-01 02:00 下班
punch_in_utc = datetime(2026, 3, 31, 15, 0, 0, tzinfo=timezone.utc)  # UTC
punch_in_taipei = punch_in_utc.astimezone(TZ_TAIPEI)  # 2026-03-31 23:00 Taipei
session_date = punch_in_taipei.date()  # 2026-03-31

# 此 session 歸屬於 3 月，即使 punch_out 在 4 月
```

---

### 規範 2：月報歸屬

**來源：** SA v2.1 §29.3 Monthly Reporting Ownership

```
月報所屬月份 = session 的 Asia/Taipei punch_in_time 所在月份
```

**實作：**

```python
# 查詢 2026-03 月份的所有 sessions
from zoneinfo import ZoneInfo
TZ_TAIPEI = ZoneInfo("Asia/Taipei")

# 計算月份邊界（Asia/Taipei）
month_start_taipei = datetime(2026, 3, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
month_end_taipei = datetime(2026, 4, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)

# 轉換為 UTC（DB 儲存格式）
month_start_utc = month_start_taipei.astimezone(timezone.utc)  # 2026-02-28 16:00 UTC
month_end_utc = month_end_taipei.astimezone(timezone.utc)      # 2026-03-31 16:00 UTC

# 查詢
sessions = db.query(AttendanceSession).filter(
    AttendanceSession.company_id == company_id,
    AttendanceSession.punch_in_time >= month_start_utc,
    AttendanceSession.punch_in_time < month_end_utc
).all()
```

---

### 規範 3：Canonical 工時欄位

**來源：** SA v2.1 §28, §30 Report Consistency Rule

```
報表顯示的工時 = attendance_sessions.duration_minutes
```

**強制規則：**

1. ✅ 報表必須讀取 `duration_minutes` 欄位
2. ❌ 報表禁止重新計算工時（禁止 `SELECT punch_out_time - punch_in_time`）
3. ❌ 前端禁止用 JS 重新計算工時

**實作：**

```python
# ✅ 正確：讀取 canonical 欄位
total_work_minutes = sum(s.duration_minutes for s in sessions if s.duration_minutes)
total_work_hours = total_work_minutes / 60

# ❌ 錯誤：重新計算
total_work_minutes = sum(
    (s.punch_out_time - s.punch_in_time).total_seconds() / 60 
    for s in sessions
)  # 禁止！
```

---

### 規範 4：Timezone-Aware Datetime

**來源：** SA v2.1 §31 Timezone Rule

**強制規則：**

1. ✅ 所有 datetime 必須為 timezone-aware
2. ❌ 禁止使用 `datetime.utcnow()`（產生 naive datetime）
3. ✅ 使用 `datetime.now(timezone.utc)` 或 `datetime.now(TZ_TAIPEI)`

**實作：**

```python
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# ✅ 正確
now_utc = datetime.now(timezone.utc)
now_taipei = datetime.now(ZoneInfo("Asia/Taipei"))

# ❌ 錯誤
now_naive = datetime.utcnow()  # 禁止！產生 naive datetime
```

---

## 查詢模式

### 模式 1：月報查詢

**用途：** 查詢指定月份的所有 sessions

```python
def get_monthly_sessions(
    db: Session,
    company_id: str,
    year: int,
    month: int
) -> List[AttendanceSession]:
    """
    查詢指定月份的所有 sessions
    
    符合 SA v2.1 §29.3: 月報歸屬 = punch_in_time 所在月份
    """
    from zoneinfo import ZoneInfo
    TZ_TAIPEI = ZoneInfo("Asia/Taipei")
    
    # 計算月份邊界（Asia/Taipei）
    month_start_taipei = datetime(year, month, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
    
    if month == 12:
        month_end_taipei = datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
    else:
        month_end_taipei = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
    
    # 轉換為 UTC
    month_start_utc = month_start_taipei.astimezone(timezone.utc)
    month_end_utc = month_end_taipei.astimezone(timezone.utc)
    
    # 查詢（使用現有索引 idx_sessions_company_punch_in）
    sessions = db.query(AttendanceSession).filter(
        AttendanceSession.company_id == company_id,
        AttendanceSession.punch_in_time >= month_start_utc,
        AttendanceSession.punch_in_time < month_end_utc,
        AttendanceSession.status == 'closed'
    ).all()
    
    return sessions
```

---

### 模式 2：日期範圍查詢

**用途：** 查詢任意日期範圍的 sessions

```python
def get_sessions_by_date_range(
    db: Session,
    company_id: str,
    start_date: date,
    end_date: date
) -> List[AttendanceSession]:
    """
    查詢日期範圍內的 sessions
    
    start_date, end_date: Asia/Taipei 日期
    """
    from zoneinfo import ZoneInfo
    TZ_TAIPEI = ZoneInfo("Asia/Taipei")
    
    # 轉換為 datetime（Asia/Taipei）
    start_datetime_taipei = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=TZ_TAIPEI)
    end_datetime_taipei = datetime.combine(end_date, datetime.min.time()).replace(tzinfo=TZ_TAIPEI)
    
    # 轉換為 UTC
    start_datetime_utc = start_datetime_taipei.astimezone(timezone.utc)
    end_datetime_utc = end_datetime_taipei.astimezone(timezone.utc)
    
    # 查詢
    sessions = db.query(AttendanceSession).filter(
        AttendanceSession.company_id == company_id,
        AttendanceSession.punch_in_time >= start_datetime_utc,
        AttendanceSession.punch_in_time < end_datetime_utc
    ).all()
    
    return sessions
```

---

### 模式 3：按日分組

**用途：** 將 sessions 按 Asia/Taipei 日期分組

```python
def group_sessions_by_date(
    sessions: List[AttendanceSession]
) -> Dict[date, List[AttendanceSession]]:
    """
    將 sessions 按 Asia/Taipei 日期分組
    
    符合 SA v2.1 §29.2: session_date = punch_in_time 的 Taipei 日期
    """
    from collections import defaultdict
    from zoneinfo import ZoneInfo
    TZ_TAIPEI = ZoneInfo("Asia/Taipei")
    
    sessions_by_date = defaultdict(list)
    
    for session in sessions:
        # 計算 session 歸屬日期
        session_date = session.punch_in_time.astimezone(TZ_TAIPEI).date()
        sessions_by_date[session_date].append(session)
    
    return dict(sessions_by_date)
```

---

### 模式 4：工時聚合

**用途：** 聚合計算總工時

```python
def calculate_total_work_hours(
    sessions: List[AttendanceSession]
) -> float:
    """
    計算總工時（小時）
    
    符合 SA v2.1 §30: 讀取 canonical 欄位，不重新計算
    """
    total_minutes = sum(
        s.duration_minutes 
        for s in sessions 
        if s.duration_minutes is not None
    )
    
    return total_minutes / 60.0
```

---

## 禁止模式

### 禁止 1：使用 punch_out_time 判斷歸屬

```python
# ❌ 錯誤：使用 punch_out_time 進行日期過濾
sessions = db.query(AttendanceSession).filter(
    AttendanceSession.punch_out_time.between(start_date, end_date)
)

# 問題：
# 1. punch_out_time 可能為 NULL（open session）
# 2. 跨午夜 session 會被錯誤分類到下班日期
```

---

### 禁止 2：使用 DATE(punch_out_time)

```python
# ❌ 錯誤：使用 DATE(punch_out_time)
from sqlalchemy import func

sessions = db.query(AttendanceSession).filter(
    func.date(AttendanceSession.punch_out_time) == target_date
)

# 問題：同上
```

---

### 禁止 3：重新計算工時

```python
# ❌ 錯誤：在報表層重新計算工時
total_work_minutes = sum(
    (s.punch_out_time - s.punch_in_time).total_seconds() / 60
    for s in sessions
)

# 問題：
# 1. 違反 SA v2.1 §30 Report Consistency Rule
# 2. 可能與 canonical 欄位不一致
# 3. 未考慮 break_duration
```

---

### 禁止 4：使用 naive datetime

```python
# ❌ 錯誤：使用 datetime.utcnow()
now = datetime.utcnow()  # naive datetime

# ❌ 錯誤：混合 naive 和 aware datetime
duration = punch_out_time - datetime.utcnow()  # 錯誤！

# ✅ 正確
now = datetime.now(timezone.utc)
duration = punch_out_time - now
```

---

### 禁止 5：前端重新計算工時

```javascript
// ❌ 錯誤：前端用 JS 重新計算工時
const workHours = (punchOutTime - punchInTime) / (1000 * 60 * 60);

// ✅ 正確：讀取後端 canonical 欄位
const workHours = session.duration_minutes / 60;
```

---

## 標準查詢範例

### 範例 1：公司月報

```python
def get_company_monthly_report(
    db: Session,
    company_id: str,
    year: int,
    month: int
) -> Dict[str, Any]:
    """
    公司月報
    
    符合 SA v2.1 §29.3, §30
    """
    from zoneinfo import ZoneInfo
    TZ_TAIPEI = ZoneInfo("Asia/Taipei")
    
    # 計算月份邊界
    month_start_taipei = datetime(year, month, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
    if month == 12:
        month_end_taipei = datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
    else:
        month_end_taipei = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
    
    month_start_utc = month_start_taipei.astimezone(timezone.utc)
    month_end_utc = month_end_taipei.astimezone(timezone.utc)
    
    # 查詢 sessions
    sessions = db.query(AttendanceSession).filter(
        AttendanceSession.company_id == company_id,
        AttendanceSession.punch_in_time >= month_start_utc,
        AttendanceSession.punch_in_time < month_end_utc,
        AttendanceSession.status == 'closed'
    ).all()
    
    # 聚合（讀取 canonical 欄位）
    total_work_minutes = sum(s.duration_minutes for s in sessions if s.duration_minutes)
    unique_users = len(set(s.user_id for s in sessions))
    
    # 按用戶分組
    from collections import defaultdict
    sessions_by_user = defaultdict(list)
    for s in sessions:
        sessions_by_user[s.user_id].append(s)
    
    by_user = []
    for user_id, user_sessions in sessions_by_user.items():
        user_work_minutes = sum(s.duration_minutes for s in user_sessions if s.duration_minutes)
        by_user.append({
            "user_id": str(user_id),
            "total_sessions": len(user_sessions),
            "total_work_hours": user_work_minutes / 60
        })
    
    return {
        "company_id": company_id,
        "year": year,
        "month": month,
        "summary": {
            "total_employees": unique_users,
            "total_sessions": len(sessions),
            "total_work_hours": total_work_minutes / 60,
            "avg_work_hours_per_employee": (total_work_minutes / 60 / unique_users) if unique_users > 0 else 0
        },
        "by_user": by_user
    }
```

---

### 範例 2：個人月報

```python
def get_user_monthly_report(
    db: Session,
    company_id: str,
    user_id: UUID,
    year: int,
    month: int
) -> Dict[str, Any]:
    """
    個人月報
    
    符合 SA v2.1 §29.3, §30
    """
    from zoneinfo import ZoneInfo
    TZ_TAIPEI = ZoneInfo("Asia/Taipei")
    
    # 計算月份邊界
    month_start_taipei = datetime(year, month, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
    if month == 12:
        month_end_taipei = datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
    else:
        month_end_taipei = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
    
    month_start_utc = month_start_taipei.astimezone(timezone.utc)
    month_end_utc = month_end_taipei.astimezone(timezone.utc)
    
    # 查詢 sessions
    sessions = db.query(AttendanceSession).filter(
        AttendanceSession.company_id == company_id,
        AttendanceSession.user_id == user_id,
        AttendanceSession.punch_in_time >= month_start_utc,
        AttendanceSession.punch_in_time < month_end_utc,
        AttendanceSession.status == 'closed'
    ).all()
    
    # 聚合
    total_work_minutes = sum(s.duration_minutes for s in sessions if s.duration_minutes)
    
    # 按日分組
    sessions_by_date = defaultdict(list)
    for s in sessions:
        session_date = s.punch_in_time.astimezone(TZ_TAIPEI).date()
        sessions_by_date[session_date].append(s)
    
    total_work_days = len(sessions_by_date)
    
    return {
        "user_id": str(user_id),
        "year": year,
        "month": month,
        "summary": {
            "total_sessions": len(sessions),
            "total_work_hours": total_work_minutes / 60,
            "total_work_days": total_work_days
        },
        "sessions": [
            {
                "session_id": str(s.id),
                "punch_in_time": s.punch_in_time.isoformat(),
                "punch_out_time": s.punch_out_time.isoformat() if s.punch_out_time else None,
                "duration_minutes": s.duration_minutes,
                "status": s.status
            }
            for s in sessions
        ]
    }
```

---

### 範例 3：日報（按日分組）

```python
def get_daily_report(
    db: Session,
    company_id: str,
    year: int,
    month: int
) -> Dict[date, Dict[str, Any]]:
    """
    日報（按日分組）
    
    符合 SA v2.1 §29.2, §30
    """
    from zoneinfo import ZoneInfo
    from collections import defaultdict
    TZ_TAIPEI = ZoneInfo("Asia/Taipei")
    
    # 查詢月份所有 sessions
    sessions = get_monthly_sessions(db, company_id, year, month)
    
    # 按日分組
    sessions_by_date = defaultdict(list)
    for s in sessions:
        session_date = s.punch_in_time.astimezone(TZ_TAIPEI).date()
        sessions_by_date[session_date].append(s)
    
    # 計算每日統計
    daily_report = {}
    for date, day_sessions in sessions_by_date.items():
        total_work_minutes = sum(s.duration_minutes for s in day_sessions if s.duration_minutes)
        unique_users = len(set(s.user_id for s in day_sessions))
        
        daily_report[date] = {
            "date": date.isoformat(),
            "total_sessions": len(day_sessions),
            "total_employees": unique_users,
            "total_work_hours": total_work_minutes / 60
        }
    
    return daily_report
```

---

## 性能優化

### 優化 1：使用現有索引

**現有索引：**
```sql
CREATE INDEX idx_sessions_company_punch_in 
ON attendance_sessions (company_id, punch_in_time);
```

**查詢優化：**
```python
# ✅ 使用索引
sessions = db.query(AttendanceSession).filter(
    AttendanceSession.company_id == company_id,  # 索引第一列
    AttendanceSession.punch_in_time >= start_utc,  # 索引第二列
    AttendanceSession.punch_in_time < end_utc
).all()
```

---

### 優化 2：分頁查詢

```python
def get_sessions_paginated(
    db: Session,
    company_id: str,
    start_date: date,
    end_date: date,
    limit: int = 50,
    offset: int = 0
) -> Tuple[List[AttendanceSession], int]:
    """
    分頁查詢
    """
    from zoneinfo import ZoneInfo
    TZ_TAIPEI = ZoneInfo("Asia/Taipei")
    
    # 轉換日期
    start_datetime_taipei = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=TZ_TAIPEI)
    end_datetime_taipei = datetime.combine(end_date, datetime.min.time()).replace(tzinfo=TZ_TAIPEI)
    start_datetime_utc = start_datetime_taipei.astimezone(timezone.utc)
    end_datetime_utc = end_datetime_taipei.astimezone(timezone.utc)
    
    # 查詢
    query = db.query(AttendanceSession).filter(
        AttendanceSession.company_id == company_id,
        AttendanceSession.punch_in_time >= start_datetime_utc,
        AttendanceSession.punch_in_time < end_datetime_utc
    )
    
    total = query.count()
    sessions = query.order_by(AttendanceSession.punch_in_time.desc()).limit(limit).offset(offset).all()
    
    return sessions, total
```

---

### 優化 3：選擇性載入

```python
# 只載入需要的欄位
from sqlalchemy import func

# 聚合查詢（不載入完整 session）
result = db.query(
    func.count(AttendanceSession.id).label('total_sessions'),
    func.sum(AttendanceSession.duration_minutes).label('total_minutes')
).filter(
    AttendanceSession.company_id == company_id,
    AttendanceSession.punch_in_time >= start_utc,
    AttendanceSession.punch_in_time < end_utc
).first()

total_sessions = result.total_sessions
total_work_hours = result.total_minutes / 60 if result.total_minutes else 0
```

---

## Code Review Checklist

### 報表查詢安全檢查清單

```markdown
## WP-11-06 Reporting Query Safety Checklist

### 日期歸屬
- [ ] 使用 `punch_in_time` 判斷 session 歸屬日期
- [ ] 禁止使用 `punch_out_time` 進行日期過濾
- [ ] 禁止使用 `DATE(punch_out_time)`

### Timezone
- [ ] 使用 timezone-aware datetime
- [ ] 禁止使用 `datetime.utcnow()`
- [ ] 使用 `datetime.now(timezone.utc)` 或 `datetime.now(TZ_TAIPEI)`
- [ ] 日期邊界計算使用 Asia/Taipei 時區

### Canonical 欄位
- [ ] 讀取 `duration_minutes` canonical 欄位
- [ ] 禁止重新計算工時（禁止 `SELECT punch_out - punch_in`）
- [ ] 前端不重新計算工時（只顯示後端 canonical 欄位）

### 安全性
- [ ] Tenant Isolation 強制執行（WHERE company_id = ?）
- [ ] Scope 驗證實作（員工只能查自己）
- [ ] 使用現有索引 `idx_sessions_company_punch_in`

### 性能
- [ ] 大量資料使用分頁查詢
- [ ] 聚合查詢使用 SQL 函數（不載入完整 session）
- [ ] 查詢條件順序符合索引順序
```

---

## 附錄：時區轉換參考

### Asia/Taipei 與 UTC 轉換

```python
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TZ_TAIPEI = ZoneInfo("Asia/Taipei")

# Taipei → UTC
taipei_time = datetime(2026, 3, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
utc_time = taipei_time.astimezone(timezone.utc)
# 結果：2026-02-28 16:00:00 UTC

# UTC → Taipei
utc_time = datetime(2026, 2, 28, 16, 0, 0, tzinfo=timezone.utc)
taipei_time = utc_time.astimezone(TZ_TAIPEI)
# 結果：2026-03-01 00:00:00 Asia/Taipei
```

### 月份邊界計算

```python
def get_month_boundaries_utc(year: int, month: int) -> Tuple[datetime, datetime]:
    """
    計算月份邊界（UTC）
    
    返回：(month_start_utc, month_end_utc)
    """
    from zoneinfo import ZoneInfo
    TZ_TAIPEI = ZoneInfo("Asia/Taipei")
    
    # 月初（Asia/Taipei）
    month_start_taipei = datetime(year, month, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
    
    # 月末（下個月初）
    if month == 12:
        month_end_taipei = datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
    else:
        month_end_taipei = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
    
    # 轉換為 UTC
    month_start_utc = month_start_taipei.astimezone(timezone.utc)
    month_end_utc = month_end_taipei.astimezone(timezone.utc)
    
    return month_start_utc, month_end_utc
```

---

**文件版本：** 1.0  
**最後更新：** 2026-03-13  
**維護者：** Backend Team  
**相關文件：**
- `SA_MODULE_SPEC_v2.1.md` (§28-31)
- `WP-11-06_REPORTING_FOUNDATION_PREP.md`
- `API_DOCUMENTATION_v2.1.md`
