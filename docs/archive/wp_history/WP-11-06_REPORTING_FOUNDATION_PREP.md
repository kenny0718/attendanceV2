# WP-11-06 Reporting Foundation Prep Report

**報告日期：** 2026-03-13  
**報告目的：** 評估跨午夜安全月報的報表基礎準備  
**報告類型：** Documentation-First Analysis (No Code Changes)

---

## 執行摘要

**核心結論：**

✅ **可以安全實作月報，無需 `session_date` 欄位**

**關鍵發現：**
1. ✅ **Canonical 規則已確立** — `duration_minutes` 為唯一合法工時來源（SA v2.1 §28）
2. ✅ **Session 歸屬規則已明確** — 使用 `punch_in_time` 的 Asia/Taipei 日期（SA v2.1 §29.2）
3. ✅ **現有索引足夠** — `idx_sessions_company_punch_in` 支援日期範圍查詢
4. ⚠️ **`session_date` 欄位非必要** — 可用 `punch_in_time` 直接查詢，但有性能考量

**建議：**
- **Phase 1（立即可行）：** 使用 `punch_in_time` 實作報表，無需 schema 變更
- **Phase 2（性能優化）：** 若查詢性能不足，再考慮新增 `session_date` 欄位

---

## 1. 驗證任務結果

### 1.1 是否需要 `session_date` 欄位？

**結論：❌ 非必要（但有條件）**

**分析：**

根據 SA v2.1 §29.2 Session Ownership Date 規則：
```
session 的所屬日期 = punch_in_time 的業務時區（Asia/Taipei）日期
```

**選項 A：使用 `punch_in_time` 直接查詢（推薦 Phase 1）**

```python
# 查詢 2026-03 月份的所有 sessions
from zoneinfo import ZoneInfo
TZ_TAIPEI = ZoneInfo("Asia/Taipei")

# 計算月份邊界（Asia/Taipei）
month_start_taipei = datetime(2026, 3, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
month_end_taipei = datetime(2026, 4, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)

# 轉換為 UTC（DB 儲存格式）
month_start_utc = month_start_taipei.astimezone(timezone.utc)
month_end_utc = month_end_taipei.astimezone(timezone.utc)

# 查詢
sessions = db.query(AttendanceSession).filter(
    AttendanceSession.company_id == company_id,
    AttendanceSession.punch_in_time >= month_start_utc,
    AttendanceSession.punch_in_time < month_end_utc
).all()
```

**優點：**
- ✅ 無需 schema 變更
- ✅ 無需 migration
- ✅ 無需 backfill
- ✅ 現有索引 `idx_sessions_company_punch_in` 可直接使用
- ✅ 符合 SA v2.1 §29.2 規範

**缺點：**
- ⚠️ 每次查詢需計算時區轉換
- ⚠️ 若未來需要「按日期分組」的複雜報表，SQL 會較複雜

**選項 B：新增 `session_date` 欄位（Phase 2 優化）**

```python
# 新增欄位
session_date = Column(Date, nullable=False, 
                     comment='Session 歸屬日期 (punch_in_time 的 Asia/Taipei 日期)')

# 查詢變簡單
sessions = db.query(AttendanceSession).filter(
    AttendanceSession.company_id == company_id,
    AttendanceSession.session_date >= date(2026, 3, 1),
    AttendanceSession.session_date < date(2026, 4, 1)
).all()
```

**優點：**
- ✅ 查詢語法更簡單
- ✅ 按日期分組更高效
- ✅ 索引更小（Date vs DateTime）

**缺點：**
- ❌ 需要 migration
- ❌ 需要 backfill 現有資料
- ❌ 需要在 `create_session()` 時計算並設定
- ❌ 增加資料冗餘

**建議：**
- **立即採用選項 A**（使用 `punch_in_time`）
- **若未來報表查詢性能不足，再採用選項 B**

---

### 1.2 Canonical 規則確認

**規則 1：session_date = punch_in_time 的 Asia/Taipei 日期**

✅ **已確認** — SA v2.1 §29.2

```python
# 正確做法
from zoneinfo import ZoneInfo
TZ_TAIPEI = ZoneInfo("Asia/Taipei")

punch_in_utc = datetime(2026, 3, 11, 16, 0, 0, tzinfo=timezone.utc)
punch_in_taipei = punch_in_utc.astimezone(TZ_TAIPEI)
session_date = punch_in_taipei.date()  # 2026-03-12
```

**跨午夜範例：**
```
punch_in UTC:  2026-03-11 16:00:00 UTC
punch_in 台北: 2026-03-12 00:00:00 Asia/Taipei
session_date:  2026-03-12
```

**規則 2：duration_minutes = punch_out_time - punch_in_time**

✅ **已確認** — SA v2.1 §28.2

```python
# 正確做法（當前實作）
duration_minutes = int((punch_out_time - session.punch_in_time).total_seconds() / 60)
```

**位置：** `backend/app/modules/attendance/api.py` 第 141 行

**驗證：**
- ✅ 使用 timezone-aware datetime
- ✅ 支援跨午夜計算
- ✅ 結果儲存於 `session.duration_minutes`（canonical 欄位）

---

### 1.3 月報實作安全性評估

**問題：月報能否在沒有 `session_date` 欄位的情況下安全實作？**

✅ **答案：可以**

**理由：**

1. **日期歸屬規則明確**
   - SA v2.1 §29.2 定義：session 歸屬於 `punch_in_time` 的 Asia/Taipei 日期
   - SA v2.1 §29.3 定義：月報歸屬於 `punch_in_time` 所在月份

2. **現有索引支援**
   - `idx_sessions_company_punch_in (company_id, punch_in_time)` 可高效查詢日期範圍

3. **Canonical 欄位完整**
   - `duration_minutes` 已正確計算並儲存
   - 報表只需讀取，不需重新計算（符合 SA v2.1 §30）

4. **跨午夜場景已處理**
   - `duration_minutes` 計算使用 UTC-aware datetime，天然支援跨午夜
   - Session 歸屬日期使用 `punch_in_time`，不受 `punch_out_time` 影響

**範例查詢：2026-03 月報**

```python
def get_monthly_report(company_id: str, year: int, month: int):
    """
    獲取指定月份的出勤報表
    
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
    
    # 查詢（使用現有索引）
    sessions = db.query(AttendanceSession).filter(
        AttendanceSession.company_id == company_id,
        AttendanceSession.punch_in_time >= month_start_utc,
        AttendanceSession.punch_in_time < month_end_utc,
        AttendanceSession.status == 'closed'
    ).all()
    
    # 聚合（讀取 canonical 欄位）
    total_work_minutes = sum(s.duration_minutes for s in sessions if s.duration_minutes)
    
    return {
        "company_id": company_id,
        "year": year,
        "month": month,
        "total_sessions": len(sessions),
        "total_work_hours": total_work_minutes / 60,
        "sessions": sessions
    }
```

**安全性檢查清單：**

| 檢查項目 | 狀態 | 說明 |
|---------|------|------|
| 使用 `punch_in_time` 判斷歸屬 | ✅ | 符合 SA v2.1 §29.2 |
| 使用 timezone-aware datetime | ✅ | 避免 naive datetime 錯誤 |
| 讀取 `duration_minutes` canonical 欄位 | ✅ | 符合 SA v2.1 §30 |
| 不重新計算工時 | ✅ | 禁止 `SELECT punch_out - punch_in` |
| 使用現有索引 | ✅ | `idx_sessions_company_punch_in` |
| 跨午夜場景正確 | ✅ | Session 歸屬於 punch_in 日期 |

---

## 2. 風險與限制

### 2.1 性能考量

**潛在問題：**
- 若公司有大量歷史資料（數萬筆 sessions），按月查詢可能較慢
- 時區轉換在應用層進行，無法利用 DB 的日期函數優化

**緩解措施：**
- 現有索引 `idx_sessions_company_punch_in` 已涵蓋查詢條件
- 若性能不足，Phase 2 可新增 `session_date` 欄位 + 索引

### 2.2 查詢複雜度

**潛在問題：**
- 「按日分組」的報表需要在應用層轉換時區後分組
- SQL 無法直接使用 `GROUP BY DATE(punch_in_time)`（因為 DB 儲存 UTC）

**範例：按日統計**

```python
# 需要在應用層分組
from collections import defaultdict

sessions_by_date = defaultdict(list)
for session in sessions:
    session_date = session.punch_in_time.astimezone(TZ_TAIPEI).date()
    sessions_by_date[session_date].append(session)

daily_summary = {
    date: {
        "total_sessions": len(sessions),
        "total_work_minutes": sum(s.duration_minutes for s in sessions if s.duration_minutes)
    }
    for date, sessions in sessions_by_date.items()
}
```

**緩解措施：**
- Phase 1 先實作月報（較簡單）
- 若需要複雜的日報，Phase 2 再考慮 `session_date` 欄位

---

## 3. 建議實作計畫

### Phase 1：使用 `punch_in_time` 實作報表（推薦立即執行）

**範圍：**
- 實作 3 個報表 API（company-summary, user-summary, sessions）
- 使用 `punch_in_time` 進行日期過濾
- 讀取 `duration_minutes` canonical 欄位

**優點：**
- ✅ 無需 schema 變更
- ✅ 無需 migration
- ✅ 可立即開始開發
- ✅ 符合 SA v2.1 所有規範

**交付物：**
- `backend/app/modules/attendance/api.py`（新增 3 個 endpoints）
- `backend/app/modules/attendance/repo.py`（新增報表查詢方法）
- `backend/app/modules/attendance/tests/test_reporting_api.py`
- `docs/WP-11-06_REPORTING_IMPLEMENTATION_REPORT.md`

**預估工時：** 3-5 個工作天

---

### Phase 2：性能優化（條件觸發）

**觸發條件：**
- Phase 1 報表查詢性能不足（> 2 秒）
- 需要複雜的按日分組報表
- 資料量超過 10 萬筆 sessions

**實作內容：**

#### Step 1: Schema 變更

**Migration: `009_add_session_date.py`**

```python
def upgrade():
    # 1. 新增欄位（nullable）
    op.add_column('attendance_sessions',
        sa.Column('session_date', sa.Date(), nullable=True,
                 comment='Session 歸屬日期 (punch_in_time 的 Asia/Taipei 日期)'))
    
    # 2. Backfill 現有資料
    # （見 Step 2）
    
    # 3. 設定 NOT NULL
    op.alter_column('attendance_sessions', 'session_date', nullable=False)
    
    # 4. 新增索引
    op.create_index('idx_sessions_company_date',
                   'attendance_sessions',
                   ['company_id', 'session_date'])
```

#### Step 2: Backfill 策略

**選項 A：Migration 內 backfill（小資料量）**

```python
# 在 migration 中執行
from sqlalchemy import text

op.execute(text("""
    UPDATE attendance_sessions
    SET session_date = (punch_in_time AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Taipei')::date
    WHERE session_date IS NULL
"""))
```

**選項 B：獨立 script backfill（大資料量）**

```python
# scripts/backfill_session_date.py
from zoneinfo import ZoneInfo
TZ_TAIPEI = ZoneInfo("Asia/Taipei")

sessions = db.query(AttendanceSession).filter(
    AttendanceSession.session_date == None
).yield_per(1000)

for session in sessions:
    session_date = session.punch_in_time.astimezone(TZ_TAIPEI).date()
    session.session_date = session_date
    
    if count % 1000 == 0:
        db.commit()

db.commit()
```

#### Step 3: 更新 `create_session()`

```python
def create_session(
    self,
    company_id: str,
    user_id: UUID,
    punch_in_time: datetime,
    notes: Optional[str] = None
) -> AttendanceSession:
    """創建新的出勤 session"""
    from zoneinfo import ZoneInfo
    TZ_TAIPEI = ZoneInfo("Asia/Taipei")
    
    # 計算 session_date
    session_date = punch_in_time.astimezone(TZ_TAIPEI).date()
    
    session = AttendanceSession(
        company_id=company_id,
        user_id=user_id,
        punch_in_time=punch_in_time,
        session_date=session_date,  # 新增
        status='open',
        notes=notes
    )
    
    self.db.add(session)
    self.db.commit()
    self.db.refresh(session)
    
    return session
```

#### Step 4: 更新報表查詢

```python
# 查詢變簡單
def get_monthly_report(company_id: str, year: int, month: int):
    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1)
    else:
        month_end = date(year, month + 1, 1)
    
    sessions = db.query(AttendanceSession).filter(
        AttendanceSession.company_id == company_id,
        AttendanceSession.session_date >= month_start,
        AttendanceSession.session_date < month_end,
        AttendanceSession.status == 'closed'
    ).all()
    
    # ... 聚合邏輯
```

#### Step 5: 驗收測試

```python
# tests/test_session_date_backfill.py

def test_session_date_matches_punch_in_taipei_date():
    """驗證 session_date 正確對應 punch_in_time 的 Taipei 日期"""
    from zoneinfo import ZoneInfo
    TZ_TAIPEI = ZoneInfo("Asia/Taipei")
    
    # 跨午夜場景
    punch_in_utc = datetime(2026, 3, 11, 16, 0, 0, tzinfo=timezone.utc)
    session = repo.create_session(company_id, user_id, punch_in_utc)
    
    expected_date = punch_in_utc.astimezone(TZ_TAIPEI).date()
    assert session.session_date == expected_date  # 2026-03-12

def test_monthly_report_uses_session_date():
    """驗證月報使用 session_date 查詢"""
    # ... 測試邏輯
```

**預估工時：** 2-3 個工作天

---

## 4. 報表 API 規格建議

### 4.1 GET /api/v1/attendance/reports/company-summary

**用途：** 公司月報（管理者查看）

**Query Parameters:**
```
year: int (required)
month: int (required, 1-12)
```

**Response:**
```json
{
  "company_id": "company-123",
  "year": 2026,
  "month": 3,
  "summary": {
    "total_employees": 50,
    "total_sessions": 1200,
    "total_work_hours": 9600.5,
    "avg_work_hours_per_employee": 192.01
  },
  "by_user": [
    {
      "user_id": "user-456",
      "user_name": "張三",
      "total_sessions": 22,
      "total_work_hours": 176.5,
      "late_count": 2,
      "early_leave_count": 0
    }
  ]
}
```

**查詢邏輯：**
- 使用 `punch_in_time` 判斷月份歸屬
- 讀取 `duration_minutes` canonical 欄位
- 聚合計算（不重新計算工時）

---

### 4.2 GET /api/v1/attendance/reports/user-summary

**用途：** 個人月報（員工查看自己）

**Query Parameters:**
```
year: int (required)
month: int (required, 1-12)
user_id: UUID (optional, 預設為當前用戶)
```

**Response:**
```json
{
  "user_id": "user-456",
  "user_name": "張三",
  "year": 2026,
  "month": 3,
  "summary": {
    "total_sessions": 22,
    "total_work_hours": 176.5,
    "total_work_days": 22,
    "late_count": 2,
    "early_leave_count": 0,
    "overtime_hours": 8.5
  },
  "sessions": [
    {
      "session_id": "session-789",
      "punch_in_time": "2026-03-01T09:05:00+08:00",
      "punch_out_time": "2026-03-01T18:00:00+08:00",
      "duration_minutes": 535,
      "is_late": true,
      "late_minutes": 5
    }
  ]
}
```

---

### 4.3 GET /api/v1/attendance/sessions

**用途：** 出勤記錄查詢（支援日期範圍）

**Query Parameters:**
```
start_date: date (optional, ISO 8601)
end_date: date (optional, ISO 8601)
user_id: UUID (optional)
status: string (optional, open/closed)
limit: int (default 50, max 100)
offset: int (default 0)
```

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "session-789",
      "user_id": "user-456",
      "punch_in_time": "2026-03-01T09:05:00+08:00",
      "punch_out_time": "2026-03-01T18:00:00+08:00",
      "duration_minutes": 535,
      "status": "closed"
    }
  ],
  "total": 1200,
  "limit": 50,
  "offset": 0
}
```

---

## 5. 驗收測試計畫

### 5.1 功能測試

| Test ID | 測試案例 | 預期結果 |
|---------|---------|---------|
| REP-01 | 查詢 2026-03 月報 | 回傳該月所有 sessions |
| REP-02 | 跨午夜 session 歸屬正確 | punch_in 2026-03-31 23:00 → 歸屬 3 月 |
| REP-03 | 工時讀取 canonical 欄位 | 使用 `duration_minutes`，不重新計算 |
| REP-04 | Tenant Isolation | A 公司無法查詢 B 公司報表 |
| REP-05 | Scope 驗證 | 員工只能查自己，管理者可查全公司 |
| REP-06 | 月報聚合正確 | total_work_hours = sum(duration_minutes) / 60 |
| REP-07 | 缺少 punch_out 的 session | 不計入已完成工時 |
| REP-08 | 跨月 session | 歸屬於 punch_in 所在月份 |

### 5.2 性能測試

| Test ID | 測試案例 | 通過標準 |
|---------|---------|---------|
| PERF-01 | 查詢 1 個月資料（1000 sessions） | < 1 秒 |
| PERF-02 | 查詢 1 年資料（12000 sessions） | < 3 秒 |
| PERF-03 | 公司月報（50 員工） | < 2 秒 |

**若性能測試未通過，觸發 Phase 2（新增 `session_date` 欄位）**

---

## 6. 文件交付清單

### 6.1 必要文件

| 文件 | 狀態 | 說明 |
|------|------|------|
| WP-11-06_REPORTING_FOUNDATION_PREP.md | ✅ 本文件 | 基礎準備評估 |
| WP-11-06_REPORTING_QUERY_PLAN.md | ⏳ 待建立 | 查詢規範與範例 |
| WP-11-06_REPORTING_API_SPEC.md | ⏳ 待建立 | API 詳細規格 |
| WP-11-06_REPORTING_IMPLEMENTATION_REPORT.md | ⏳ 實作後 | 實作報告 |

### 6.2 Code Review Checklist

**報表查詢安全檢查清單：**

```markdown
## WP-11-06 Reporting Query Safety Checklist

- [ ] 使用 `punch_in_time` 判斷 session 歸屬日期
- [ ] 使用 timezone-aware datetime（禁止 `datetime.utcnow()`）
- [ ] 讀取 `duration_minutes` canonical 欄位
- [ ] 禁止重新計算工時（禁止 `SELECT punch_out - punch_in`）
- [ ] 禁止使用 `punch_out_time` 進行日期過濾
- [ ] 禁止使用 `DATE(punch_out_time)`
- [ ] Tenant Isolation 強制執行（WHERE company_id = ?）
- [ ] Scope 驗證實作（員工只能查自己）
- [ ] 前端不重新計算工時（只顯示後端 canonical 欄位）
```

---

## 7. 總結與建議

### 7.1 核心結論

✅ **月報可以安全實作，無需 `session_date` 欄位**

**理由：**
1. SA v2.1 §29.2 明確定義 session 歸屬規則（使用 `punch_in_time`）
2. 現有索引 `idx_sessions_company_punch_in` 支援高效查詢
3. Canonical 欄位 `duration_minutes` 已正確計算並儲存
4. 跨午夜場景已正確處理

### 7.2 建議執行順序

**立即執行（Phase 1）：**
1. 實作 3 個報表 API（使用 `punch_in_time`）
2. 實作 15+ 驗收測試
3. 執行性能測試

**條件觸發（Phase 2）：**
- 若性能測試未通過，執行 `session_date` 欄位新增計畫

### 7.3 風險提示

⚠️ **必須避免的錯誤：**
1. ❌ 使用 `punch_out_time` 判斷 session 歸屬
2. ❌ 在報表層重新計算工時
3. ❌ 使用 naive datetime（`datetime.utcnow()`）
4. ❌ 前端用 JS 重新計算工時

✅ **正確做法：**
1. ✅ 使用 `punch_in_time` 的 Asia/Taipei 日期判斷歸屬
2. ✅ 讀取 `duration_minutes` canonical 欄位
3. ✅ 使用 timezone-aware datetime
4. ✅ 前端只顯示後端 canonical 欄位

---

**報告完成時間：** 2026-03-13  
**報告人員：** AI Assistant  
**下一步：** 等待 Phase 1 基線修正完成後，開始 WP-11-06 實作
