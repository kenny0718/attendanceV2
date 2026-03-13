# WP-11-06 Step 1 Sessions Implementation Plan

**建立日期：** 2026-03-13
**任務：** WP-11-06 Reporting v1 — Step 1 Only
**類型：** IMPLEMENTATION PLAN (Documentation Only — No Code Changes)
**狀態：** ACTIVE
**覆蓋範圍：** GET /api/v1/attendance/sessions ONLY

---

## 1. Endpoint 範圍

本計畫僅覆蓋以下單一 endpoint：

    GET /api/v1/attendance/sessions

**此計畫明確不包含：**

- GET /api/v1/attendance/reports/user-summary（Step 2，後續任務）
- GET /api/v1/attendance/reports/company-summary（Step 3，後續任務）
- CSV export
- 任何 schema migration
- 任何現有 attendance core 邏輯修改

---

## 2. Query Parameters

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| start_date | datetime (ISO 8601 with tz) | 選填 | punch_in_time 起始過濾；必須為 timezone-aware |
| end_date | datetime (ISO 8601 with tz) | 選填 | punch_in_time 結束過濾（exclusive）；必須為 timezone-aware |
| user_id | UUID | 選填 | 過濾特定用戶；管理者可查他人，員工只能查自己 |
| status | string | 選填 | open 或 closed；不傳回傳全部 |
| limit | int | 選填 | 預設 50，最大 100 |
| offset | int | 選填 | 預設 0 |

**start_date / end_date 型別規則：**

- 型別保持 Optional[datetime]（含 tzinfo），不得改為 date
- naive datetime（無 tzinfo）必須被 validator 拒絕，回傳 422
- API 層收到後必須先 normalize_to_utc()，再傳入 repo

---

## 3. Ownership / Scope 規則

### 3.1 Session 歸屬規則

- Session 歸屬日 = punch_in_time 換算 Asia/Taipei 的 .date()
- 跨日 session（punch_in 23:50，punch_out 00:30+1d）歸屬 punch_in 當日
- 禁止以 punch_out_time 判斷日期歸屬

### 3.2 Tenant Isolation

- 所有查詢必須強制 WHERE company_id = ?（從 JWT tenant context 取得）
- 禁止跨 company_id 查詢

### 3.3 User Scope

- 員工（employee role）：只能查詢自己的 sessions（user_id 強制等於 JWT user_id）
- 管理者（manager / admin role）：可查詢本公司任意 user_id 的 sessions
- user_id 未傳入時：員工查自己；管理者查全公司

---

## 4. Pagination 規則

- limit 範圍：1 ~ 100，超出回傳 400
- offset 範圍：>= 0，超出範圍回傳空 sessions 列表（不報錯）
- Response 必須包含 total（未分頁總數），供前端計算頁數
- 排序：punch_in_time DESC（最新優先）

---

## 5. Date/Month Filter Handling 規則

### 5.1 Filter 語義

- start_date：punch_in_time >= start_utc（inclusive）
- end_date：punch_in_time < end_utc（exclusive）
- 兩者均為可選，可只傳其中一個

### 5.2 API 層處理流程

```
1. 接收 start_date / end_date（Optional[datetime]）
2. 若為 naive datetime（tzinfo is None）→ 拒絕，回傳 422
3. 呼叫 normalize_to_utc(start_date) → start_utc
4. 呼叫 normalize_to_utc(end_date)   → end_utc
5. 傳入 repo.get_sessions_for_reporting(start_utc=start_utc, end_utc=end_utc, ...)
```

### 5.3 Repo 層 Filter 實作

```python
if start_utc:
    query = query.filter(AttendanceSession.punch_in_time >= start_utc)
if end_utc:
    query = query.filter(AttendanceSession.punch_in_time < end_utc)

# 禁止：
# query.filter(AttendanceSession.punch_out_time >= start_utc)  -- 語義錯誤
# query.filter(func.date(AttendanceSession.punch_in_time) == date)  -- 索引失效
```

### 5.4 月份過濾（本 endpoint 使用日期範圍，非月份參數）

Sessions endpoint 接受任意日期範圍（start_date / end_date），
不提供 year / month 月份參數（月份參數留給 user-summary / company-summary）。
若呼叫方要查某月，須自行計算月份邊界並傳入 start_date / end_date。

---

## 6. Repo / Service / API 層責任劃分

### 6.1 Repo 層（repo.py）

新增方法：get_sessions_for_reporting()

責任：
- 接受 company_id（必填）、user_id（Optional）、start_utc（Optional）、
  end_utc（Optional）、status（Optional）、limit、offset
- 強制 WHERE company_id = ?（tenant isolation）
- 若 user_id 傳入則加 WHERE user_id = ?
- 若 start_utc 傳入則加 WHERE punch_in_time >= start_utc
- 若 end_utc 傳入則加 WHERE punch_in_time < end_utc
- 排序：punch_in_time DESC
- 分頁：.limit(limit).offset(offset)
- 不進行時區轉換（由 API 層負責）
- 不進行 scope 驗證（由 API 層負責）

新增方法：count_sessions_for_reporting()

責任：
- 接受同上（不含 limit / offset）
- 回傳符合條件的 session 總數（用於 total 欄位）

不修改：
- get_sessions()（現有個人歷史記錄方法，保持不變）
- count_sessions()（保持不變）

```python
def get_sessions_for_reporting(
    self,
    company_id: str,
    user_id: Optional[UUID] = None,
    start_utc: Optional[datetime] = None,
    end_utc: Optional[datetime] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[AttendanceSession]:
    query = self.db.query(AttendanceSession).filter(
        AttendanceSession.company_id == company_id
    )
    if user_id is not None:
        query = query.filter(AttendanceSession.user_id == user_id)
    if start_utc is not None:
        query = query.filter(AttendanceSession.punch_in_time >= start_utc)
    if end_utc is not None:
        query = query.filter(AttendanceSession.punch_in_time < end_utc)
    if status is not None:
        query = query.filter(AttendanceSession.status == status)
    return (
        query
        .order_by(AttendanceSession.punch_in_time.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
```

### 6.2 Service 層

Sessions endpoint 不需要 service 層。
API 層直接呼叫 repo，不經過 service.py。
（Reporting 為唯讀查詢，無業務邏輯計算需求。）

### 6.3 API 層（api.py）

新增 endpoint：GET /api/v1/attendance/sessions

責任：
- 從 JWT 取得 company_id 和 current_user_id
- 驗證 limit 範圍（1 ~ 100），超出回傳 400
- 驗證 start_date / end_date 為 timezone-aware（naive 回傳 422）
- 實作 user scope 驗證：
    - 員工：強制 user_id = current_user_id
    - 管理者：允許任意 user_id（含 None = 全公司）
- 呼叫 normalize_to_utc(start_date) 和 normalize_to_utc(end_date)
- 呼叫 repo.get_sessions_for_reporting()
- 呼叫 repo.count_sessions_for_reporting()
- 組裝並回傳 SessionsListResponse

### 6.4 Schemas 層（schemas.py）

新增：

```python
class SessionsListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int
    limit: int
    offset: int
```

Query params 以 FastAPI Query() 方式接收，不需要獨立 Request schema。
SessionResponse 直接複用現有定義。

---

## 7. Minimal Test Plan

### 7.1 測試檔案

新建：backend/app/modules/attendance/tests/test_reporting_sessions.py
不修改任何現有測試檔案。

### 7.2 測試案例清單

| Test ID | 測試函數名稱 | 驗證項目 |
|---------|-------------|----------|
| SES-01 | test_sessions_basic_pagination | 基本分頁：回傳 sessions 列表 + total |
| SES-02 | test_sessions_date_filter_start_end | start_date/end_date 過濾正確 |
| SES-03 | test_sessions_taipei_midnight_ownership | punch_in 00:30 Taipei 正確歸屬當日（非 UTC 前日） |
| SES-04 | test_sessions_cross_month_ownership | punch_in 3/31 23:50 Taipei 歸屬 3 月，不歸 4 月 |
| SES-05 | test_sessions_status_filter | status=closed 只回傳 closed sessions |
| SES-06 | test_sessions_tenant_isolation | company A JWT 查不到 company B sessions |
| SES-07 | test_sessions_user_scope_self_only | 員工只能查自己（user_id 非自己回傳 403 或空） |
| SES-08 | test_sessions_open_session_null_duration | open session duration_minutes 為 NULL，response 不崩潰 |
| SES-09 | test_sessions_limit_boundary | limit=0 回傳 400；limit=101 回傳 400 |
| SES-10 | test_sessions_total_matches_count | total 與不分頁的實際數量一致 |

### 7.3 跨日歸屬測試詳細說明（SES-03, SES-04）

SES-03：Taipei 凌晨打卡

```python
def test_sessions_taipei_midnight_ownership(test_session, test_user, client):
    from zoneinfo import ZoneInfo
    from datetime import datetime, timezone, timedelta
    TZ_TAIPEI = ZoneInfo("Asia/Taipei")
    # punch_in = 2026-03-12 00:30 Taipei = 2026-03-11 16:30 UTC
    punch_in_taipei = datetime(2026, 3, 12, 0, 30, 0, tzinfo=TZ_TAIPEI)
    punch_in_utc = punch_in_taipei.astimezone(timezone.utc)
    make_closed_session(test_session, test_user.company_id, test_user.id, punch_in_utc)
    # 查詢 2026-03-12 範圍（Taipei）
    start = datetime(2026, 3, 12, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
    end   = datetime(2026, 3, 13, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
    # 期望：session 被查到（punch_in UTC 在此範圍內）
    resp = client.get("/api/v1/attendance/sessions",
        params={"start_date": start.isoformat(), "end_date": end.isoformat()},
        headers={"X-Company-ID": test_user.company_id, ...}
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
```

SES-04：跨月歸屬

```python
def test_sessions_cross_month_ownership(test_session, test_user, client):
    from zoneinfo import ZoneInfo
    from datetime import datetime, timezone
    TZ_TAIPEI = ZoneInfo("Asia/Taipei")
    # punch_in = 2026-03-31 23:50 Taipei = 2026-03-31 15:50 UTC
    punch_in_taipei = datetime(2026, 3, 31, 23, 50, 0, tzinfo=TZ_TAIPEI)
    punch_in_utc = punch_in_taipei.astimezone(timezone.utc)
    make_closed_session(test_session, test_user.company_id, test_user.id, punch_in_utc)
    # 查 3 月範圍，期望找到
    mar_start = datetime(2026, 3, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
    apr_start = datetime(2026, 4, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
    resp = client.get("/api/v1/attendance/sessions",
        params={"start_date": mar_start.isoformat(), "end_date": apr_start.isoformat()},
        headers={...}
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1  # 歸屬 3 月
    # 查 4 月範圍，期望找不到
    may_start = datetime(2026, 5, 1, 0, 0, 0, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
    resp2 = client.get("/api/v1/attendance/sessions",
        params={"start_date": apr_start.isoformat(), "end_date": may_start.isoformat()},
        headers={...}
    )
    assert resp2.json()["total"] == 0  # 不歸屬 4 月
```

---

## 8. 刻意延後至後續 Steps 的項目

下列項目在本計畫中刻意不實作，原因如下：

| 項目 | 延後原因 | 預計實作時機 |
|------|----------|--------------|
| GET /api/v1/attendance/reports/user-summary | 依賴 Sessions endpoint 穩定後進行；需要月份邊界計算邏輯驗證 | Step 2 |
| GET /api/v1/attendance/reports/company-summary | 需要跨用戶聚合，複雜度高；依賴 user-summary 邏輯正確後進行 | Step 3 |
| year / month query parameters | Sessions endpoint 使用 start_date/end_date 彈性範圍；月份參數為 reporting endpoints 專屬 | Step 2/3 |
| duration_minutes 聚合計算（sum / avg） | Sessions endpoint 只列出 sessions，不做聚合 | Step 2/3 |
| late_count / early_leave_count 計算 | 需要 policy evaluation 結果；sessions 表目前不存 is_late 欄位 | Step 2 設計時評估 |
| CSV export | 超出 Reporting v1 範圍 | 未來 WP |
| session_date 欄位引入 | 依 WP-11-06_SESSION_DATE_FEASIBILITY.md 決策，Phase 1 不引入 | 未來性能優化時評估 |
| Naive datetime validator（schemas.py） | 依 ATTENDANCE_PHASE1_3_CLOSEOUT_SUMMARY.md §6 Defer-C，start_date/end_date 啟用時同步加入 | 本 Step 實作時加入 |

---

## 9. Response Schema

### 9.1 成功回應（200 OK）

```json
{
  "sessions": [
    {
      "session_id": "uuid",
      "user_id": "uuid",
      "company_id": "company-123",
      "punch_in_time": "2026-03-01T09:05:00+08:00",
      "punch_out_time": "2026-03-01T18:00:00+08:00",
      "duration_minutes": 535,
      "status": "closed"
    }
  ],
  "total": 220,
  "limit": 50,
  "offset": 0
}
```

### 9.2 錯誤回應

| HTTP Status | 情境 | error_code |
|-------------|------|------------|
| 400 | limit 超出範圍（<1 或 >100） | INVALID_PARAM |
| 401 | 未帶 JWT token | UNAUTHORIZED |
| 403 | 員工嘗試查詢他人 sessions | FORBIDDEN |
| 422 | start_date / end_date 為 naive datetime | VALIDATION_ERROR |

---

## 10. 實作順序建議

建議按以下順序實作，可在每步確認後再進行下一步：

1. schemas.py — 新增 SessionsListResponse
   - 確認 SessionResponse 可直接複用
   - 新增 naive datetime validator

2. repo.py — 新增 get_sessions_for_reporting() 和 count_sessions_for_reporting()
   - 確認查詢不包含 DATE() / EXTRACT() / punch_out_time 過濾
   - 確認 tenant isolation（WHERE company_id）

3. api.py — 新增 GET /api/v1/attendance/sessions
   - 確認 normalize_to_utc() 正確呼叫
   - 確認 user scope 驗證邏輯
   - 確認 limit 驗證

4. tests/test_reporting_sessions.py — 實作 SES-01 ~ SES-10
   - 優先實作 SES-03 / SES-04（跨日歸屬邊界案例）
   - 優先實作 SES-06（tenant isolation）

---

## 11. Code Review Checklist（Step 1 專用）

在 Step 1 PR 提交前，必須通過以下所有檢查：

**查詢安全：**
- [ ] WHERE 子句中 punch_in_time 無函數包裹（無 DATE()、EXTRACT()、CAST()）
- [ ] 無 punch_out_time 用於範圍過濾
- [ ] 無 punch_out_time BETWEEN
- [ ] 月份邊界使用 Asia/Taipei 計算後轉 UTC

**時區安全：**
- [ ] 所有傳入 DB 查詢的 datetime 均為 timezone-aware
- [ ] naive datetime 傳入時回傳 422
- [ ] normalize_to_utc() 在 API 層正確呼叫

**Canonical Duration：**
- [ ] Response 讀取 duration_minutes 欄位
- [ ] 無重新計算 punch_out_time - punch_in_time
- [ ] open session（duration_minutes IS NULL）不崩潰

**Tenant / Scope：**
- [ ] 所有查詢強制 WHERE company_id = ?
- [ ] 員工無法查詢他人 sessions

**測試：**
- [ ] SES-03（Taipei 凌晨歸屬）通過
- [ ] SES-04（跨月歸屬）通過
- [ ] SES-06（tenant isolation）通過

---

*文件完畢。Step 1 Implementation Plan 覆蓋範圍：GET /api/v1/attendance/sessions ONLY*
*user-summary 和 company-summary 在本計畫中刻意延後，待 Step 1 穩定後進行。*
