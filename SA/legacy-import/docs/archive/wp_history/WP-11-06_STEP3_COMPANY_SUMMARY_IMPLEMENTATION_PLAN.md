# WP-11-06 Step 3 Company Summary Implementation Plan

**建立日期：** 2026-03-13  
**任務：** WP-11-06 Reporting v1 Step 3  
**類型：** IMPLEMENTATION PLAN (Documentation Only — No Code Changes)  
**狀態：** ACTIVE  
**覆蓋範圍：** GET /api/v1/attendance/reports/company-summary ONLY  

---

## 1. Endpoint 範圍

```
GET /api/v1/attendance/reports/company-summary
```

此計畫明確**不**包含：
- per-user breakdown（各員工詳細列表）
- per-department analytics
- CSV export
- dashboard KPI
- 任何 schema migration
- Step 1 sessions endpoint 修改
- Step 2 user-summary endpoint 修改

---

## 2. Query Parameters

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| start_date | datetime (ISO 8601 with tz) | 選填 | punch_in_time 起始過濾；必須為 timezone-aware |
| end_date | datetime (ISO 8601 with tz) | 選填 | punch_in_time 結束過濾（exclusive）；必須為 timezone-aware |

start_date / end_date 型別規則：
- 型別保持 `Optional[datetime]`（含 tzinfo）
- naive datetime（無 tzinfo）必須被 endpoint 攔截，回傳 422
- API 層呼叫 `_normalize_to_utc()`，再傳入 repo

---

## 3. Allowed Files / Forbidden Files

### 允許修改

| 檔案 | 修改類型 | 說明 |
|------|----------|------|
| `backend/app/modules/attendance/schemas.py` | 新增 Schema | 新增 `CompanySummaryResponse` |
| `backend/app/modules/attendance/repo.py` | 新增方法 | 在 `ReportingRepository` 內新增 `get_company_summary_sessions()` |
| `backend/app/modules/attendance/api.py` | 新增 endpoint | `GET /api/v1/attendance/reports/company-summary` |
| `backend/app/modules/attendance/tests/test_reporting_company_summary.py` | 新建 | CMP-01 ~ CMP-07 |

### 禁止修改

| 檔案 | 原因 |
|------|------|
| `models.py` | 無需新增欄位；不引入 migration |
| `policy_engine.py` | 與 reporting 無關 |
| `service.py` | company-summary 為唯讀查詢，不需要 service layer |
| 任何 `versions/` migration 檔案 | WP-11-06 不引入 migration |
| `api.py` Step 1 sessions endpoint | 不修改現有 endpoint |
| `api.py` Step 2 user-summary endpoint | 不修改現有 endpoint |
| `test_reporting_sessions.py` | 不修改現有測試 |
| `test_reporting_user_summary.py` | 不修改現有測試 |

---

## 4. Query Rules

### 4.1 允許的 WHERE 模式（Index Range Scan）

```sql
WHERE company_id     = :cid
  AND punch_in_time >= :start_utc
  AND punch_in_time <  :end_utc
```

索引命中：`idx_sessions_company_punch_in (company_id, punch_in_time)`  
掃描類型：Index Range Scan  

### 4.2 禁止模式（任何違反均為 P1 缺陷）

| 禁止模式 | 風險 |
|---------|------|
| `DATE(punch_in_time)` | 索引失效，全表掃描 |
| `EXTRACT(... FROM punch_in_time)` | 索引失效 |
| `CAST(punch_in_time AS DATE)` | 索引失效 |
| `func.date(AttendanceSession.punch_in_time)` | SQLAlchemy 版，同樣索引失效 |
| `punch_out_time BETWEEN x AND y` | NULL 排除 + 語義錯誤 + 無索引 |
| `punch_out_time >= start` 用於歸屬過濾 | 跨月 session 誤分類 |
| `func.sum(AttendanceSession.duration_minutes)` | SQL 端聚合（本 Step 禁止）|
| `func.count(func.distinct(AttendanceSession.user_id))` | SQL 端聚合（本 Step 禁止）|
| naive datetime 傳入 DB | 時區不確定行為 |

---

## 5. Aggregation 策略

**採用：Python 應用層聚合（選項 A）**

理由：
1. 與 Step 1 / Step 2 一致，不引入新的 SQL 聚合模式
2. 不包裹 indexed column，無索引失效風險
3. 現有索引 `idx_sessions_company_punch_in` 足以高效取回全公司 sessions
4. 資料量超過 10 萬筆時可評估切換 SQL 聚合（留待未來優化）

### 5.1 完整聚合計算流程

```python
sessions = repo.get_company_summary_sessions(
    company_id=company_id,
    start_utc=start_utc,
    end_utc=end_utc,
)

# 基本計數
total_sessions  = len(sessions)
closed_sessions = sum(1 for s in sessions if s.status == "closed")
open_sessions   = sum(1 for s in sessions if s.status == "open")

# 用戶去重（Python set）— 禁止 SQL COUNT DISTINCT
total_users_with_sessions = len(set(s.user_id for s in sessions))

# 工時（canonical duration_minutes，NULL 計為 0）
total_work_minutes = sum(s.duration_minutes or 0 for s in sessions)

# 平均：除以零防護
average_minutes_per_session = (
    total_work_minutes / closed_sessions
    if closed_sessions > 0 else None
)
average_minutes_per_user = (
    total_work_minutes / total_users_with_sessions
    if total_users_with_sessions > 0 else None
)

# first / last：應用層 min / max
first_session_time = min(s.punch_in_time for s in sessions) if sessions else None
last_session_time  = max(s.punch_in_time for s in sessions) if sessions else None
```

### 5.2 禁止計算方式

```python
# 禁止重算工時
work_min = (s.punch_out_time - s.punch_in_time).total_seconds() / 60

# 禁止 SQL 端聚合
db.query(func.sum(AttendanceSession.duration_minutes)).filter(...).scalar()

# 禁止 SQL COUNT DISTINCT
db.query(func.count(func.distinct(AttendanceSession.user_id))).filter(...).scalar()
```

---

## 6. File Impact Plan

### 6.1 schemas.py — 新增 CompanySummaryResponse

在 `UserSummaryResponse` 之後新增：

```python
# ============================================
# WP-11-06 Step 3: Company Summary Reporting Schema
# ============================================

class CompanySummaryResponse(BaseModel):
    """Company-level attendance summary response (WP-11-06 Step 3)"""
    company_id: str = Field(..., description="查詢的公司 ID")
    total_users_with_sessions: int = Field(..., description="有出勤記錄的用戶數（Python set 去重）")
    total_sessions: int = Field(..., description="符合條件的 session 總數（含 open + closed）")
    open_sessions: int = Field(..., description="進行中的 session 數")
    closed_sessions: int = Field(..., description="已完成的 session 數")
    total_work_minutes: int = Field(..., description="總工時（分鐘），讀取 canonical duration_minutes，NULL 計為 0")
    average_minutes_per_session: Optional[float] = Field(None, description="平均每次 session 工時，無 closed session 時為 null")
    average_minutes_per_user: Optional[float] = Field(None, description="平均每位用戶工時，無用戶時為 null")
    first_session_time: Optional[datetime] = Field(None, description="最早 punch_in_time，無 session 時為 null")
    last_session_time: Optional[datetime] = Field(None, description="最近 punch_in_time，無 session 時為 null")
```

### 6.2 repo.py — 新增 get_company_summary_sessions()

在 `ReportingRepository` 內、`get_user_summary_sessions()` 之後新增：

```python
def get_company_summary_sessions(
    self,
    company_id: str,
    start_utc: Optional[datetime] = None,
    end_utc: Optional[datetime] = None,
) -> List[AttendanceSession]:
    """查詢公司所有 sessions（company-summary 用途，WP-11-06 Step 3）

    不過濾 user_id（查全公司）。
    不分頁（全量拉取，在應用層聚合）。
    過濾僅使用 punch_in_time（禁止 punch_out_time）。
    索引命中: idx_sessions_company_punch_in (company_id, punch_in_time)
    """
    query = self.db.query(AttendanceSession).filter(
        AttendanceSession.company_id == company_id
    )

    if start_utc is not None:
        query = query.filter(AttendanceSession.punch_in_time >= start_utc)

    if end_utc is not None:
        query = query.filter(AttendanceSession.punch_in_time < end_utc)

    return query.order_by(AttendanceSession.punch_in_time.asc()).all()
```

**注意：** `user_id` 不加 filter — 這是與 `get_user_summary_sessions()` 的唯一差異。
不修改 `get_sessions_for_reporting()`、`count_sessions_for_reporting()`、`get_user_summary_sessions()`。

### 6.3 api.py — 新增 endpoint

在 Step 2 user-summary endpoint 之後新增：

```python
@router_v1.get("/reports/company-summary", response_model=CompanySummaryResponse)
async def get_company_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    company_id: str = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
```

**Endpoint 責任：**
1. 驗證 start_date / end_date 為 timezone-aware（422 if naive）
2. 呼叫 `_normalize_to_utc()` 轉換為 UTC
3. 呼叫 `repo.get_company_summary_sessions()`
4. Python 應用層聚合（見 §5.1）
5. 回傳 `CompanySummaryResponse`

**注意：** company-summary 不需要 `current_user_id` — 任何屬於該公司的認證用戶皆可查詢。

**同時更新** `api.py` 頂部 import，加入 `CompanySummaryResponse`。

### 6.4 tests/test_reporting_company_summary.py — 新建

測試檔案位置：`backend/app/modules/attendance/tests/test_reporting_company_summary.py`

---

## 7. Response Schema

### 成功回應（200 OK）

```json
{
  "company_id": "company-abc",
  "total_users_with_sessions": 15,
  "total_sessions": 330,
  "open_sessions": 3,
  "closed_sessions": 327,
  "total_work_minutes": 156960,
  "average_minutes_per_session": 480.0,
  "average_minutes_per_user": 10464.0,
  "first_session_time": "2026-03-01T01:00:00+00:00",
  "last_session_time": "2026-03-31T01:00:00+00:00"
}
```

### 空結果（200 OK）

```json
{
  "company_id": "company-abc",
  "total_users_with_sessions": 0,
  "total_sessions": 0,
  "open_sessions": 0,
  "closed_sessions": 0,
  "total_work_minutes": 0,
  "average_minutes_per_session": null,
  "average_minutes_per_user": null,
  "first_session_time": null,
  "last_session_time": null
}
```

### 錯誤回應

| HTTP Status | 情境 |
|-------------|------|
| 401 | 未帶認證 header |
| 422 | start_date 或 end_date 為 naive datetime |

---

## 8. Minimal Test Plan

新建：`backend/app/modules/attendance/tests/test_reporting_company_summary.py`  
不修改任何現有測試檔案。

### 測試案例

| Test ID | 測試函數名稱 | 驗證重點 |
|---------|-------------|----------|
| CMP-01 | `test_basic_company_summary` | total_sessions, open/closed counts, total_work_minutes, total_users_with_sessions 正確 |
| CMP-02 | `test_date_range_filter` | start_date/end_date 過濾只計入 punch_in_time 在範圍內的 sessions；範圍外不計入 |
| CMP-03 | `test_cross_midnight_session_ownership` | punch_in 3/31 23:50 Taipei 計入 3 月，不計入 4 月 |
| CMP-04 | `test_null_duration_not_counted` | open session duration_minutes IS NULL 不影響 total_work_minutes |
| CMP-05 | `test_tenant_isolation` | company A 查不到 company B 的 sessions（total_sessions 不含對方資料）|
| CMP-06 | `test_empty_company_returns_zeros` | 無 session 時回傳全零 summary，average 欄位為 null，不報錯 |
| CMP-07 | `test_naive_datetime_returns_422` | start_date 無 tzinfo 