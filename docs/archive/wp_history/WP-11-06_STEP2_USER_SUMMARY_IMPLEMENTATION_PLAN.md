# WP-11-06 Step 2 User Summary Implementation Plan

**建立日期：** 2026-03-13
**任務：** WP-11-06 Reporting v1 Step 2
**類型：** IMPLEMENTATION PLAN (Documentation Only)
**狀態：** ACTIVE
**覆蓋範圍：** GET /api/v1/attendance/reports/user-summary ONLY

---

## 1. Endpoint 範圍

    GET /api/v1/attendance/reports/user-summary

此計畫明確不包含：
- GET /api/v1/attendance/reports/company-summary（Step 3）
- 跨用戶聚合（manager 查所有員工）
- CSV export
- 任何 schema migration
- Step 1 sessions endpoint 修改

---

## 2. Query Parameters

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| start_date | datetime (ISO 8601 with tz) | 選填 | punch_in_time 起始過濾；必須為 timezone-aware |
| end_date | datetime (ISO 8601 with tz) | 選填 | punch_in_time 結束過濾（exclusive）；必須為 timezone-aware |

start_date / end_date 型別規則：
- 型別保持 Optional[datetime]（含 tzinfo）
- naive datetime（無 tzinfo）必須被 endpoint 攔截，回傳 422
- API 層呼叫 _normalize_to_utc()，再傳入 repo

---

## 3. Ownership / Scope 規則

Session 歸屬規則：
- 業務日 = punch_in_time 換算 Asia/Taipei 的 .date()
- 月份歸屬 = punch_in_time 換算 Asia/Taipei 的 year/month
- 跨日 session 歸屬 punch_in 當日，不以 punch_out 分割

Tenant Isolation：
- 所有查詢強制 WHERE company_id = ?（從 Header / JWT 取得）

User Scope：
- 員工：只能查詢自己的 summary（user_id 強制等於 current_user_id）
- 嘗試查詢他人回傳 403
- 本 Step 不支援 manager 查詢他人（留待 Step 3 company-summary）

---

## 4. Aggregation 規則

所有聚合在 Python 應用層執行（不在 SQL 端 GROUP BY / SUM）：

    sessions = repo.get_user_summary_sessions(
        company_id, user_id, start_utc, end_utc
    )

    total_sessions        = len(sessions)
    closed_sessions       = sum(1 for s in sessions if s.status == "closed")
    open_sessions         = sum(1 for s in sessions if s.status == "open")
    total_work_minutes    = sum(s.duration_minutes or 0 for s in sessions)
    average_session_minutes = (
        total_work_minutes / closed_sessions
        if closed_sessions > 0 else None
    )
    first_session_time = min(s.punch_in_time for s in sessions) if sessions else None
    last_session_time  = max(s.punch_in_time for s in sessions) if sessions else None

禁止：
    # 禁止重算工時
    work_min = (s.punch_out_time - s.punch_in_time).total_seconds() / 60

    # 禁止 SQL 端聚合（本 Step）
    db.query(func.sum(AttendanceSession.duration_minutes))...

---

## 5. Repo / API 層責任劃分

### 5.1 Repo 層（repo.py — ReportingRepository 內新增）

新增方法：get_user_summary_sessions()

    def get_user_summary_sessions(
        self,
        company_id: str,
        user_id: UUID,
        start_utc: Optional[datetime] = None,
        end_utc: Optional[datetime] = None,
    ) -> List[AttendanceSession]:
        """查詢用戶所有 sessions（user-summary 用途）

        user_id 為必填（不同於 get_sessions_for_reporting 的 Optional）。
        過濾僅使用 punch_in_time。
        不分頁（全量拉取，在應用層聚合）。
        索引命中：idx_sessions_company_punch_in (company_id, punch_in_time)
        """
        query = self.db.query(AttendanceSession).filter(
            AttendanceSession.company_id == company_id,
            AttendanceSession.user_id    == user_id,
        )
        if start_utc is not None:
            query = query.filter(AttendanceSession.punch_in_time >= start_utc)
        if end_utc is not None:
            query = query.filter(AttendanceSession.punch_in_time <  end_utc)
        return query.order_by(AttendanceSession.punch_in_time.asc()).all()

不修改：
- get_sessions_for_reporting()（Step 1 方法，保持不變）
- count_sessions_for_reporting()（保持不變）

### 5.2 Service 層

user-summary 不需要 service 層。API 層直接呼叫 repo，再做應用層聚合。

### 5.3 API 層（api.py）

新增 endpoint：GET /api/v1/attendance/reports/user-summary

責任：
1. 從 JWT / Header 取得 company_id 和 current_user_id
2. 驗證 current_user_id 存在（400 if missing）
3. 驗證 start_date / end_date 為 timezone-aware（422 if naive）
4. User scope：強制 user_id = UUID(current_user_id)，不允許查他人（403）
5. 呼叫 _normalize_to_utc(start_date) / _normalize_to_utc(end_date)
6. 呼叫 repo.get_user_summary_sessions()
7. 應用層聚合（total_sessions, closed_sessions, open_sessions,
   total_work_minutes, average_session_minutes, first/last_session_time）
8. 組裝並回傳 UserSummaryResponse

### 5.4 Schemas 層（schemas.py）

新增：

    class UserSummaryResponse(BaseModel):
        user_id: str
        total_sessions: int
        closed_sessions: int
        open_sessions: int
        total_work_minutes: int
        average_session_minutes: Optional[float]
        first_session_time: Optional[datetime]
        last_session_time: Optional[datetime]
        start_date: Optional[datetime]
        end_date: Optional[datetime]

---

## 6. Response Schema

成功回應（200 OK）：

    {
      "user_id": "uuid-string",
      "total_sessions": 22,
      "closed_sessions": 21,
      "open_sessions": 1,
      "total_work_minutes": 10080,
      "average_session_minutes": 480.0,
      "first_session_time": "2026-03-01T01:00:00+00:00",
      "last_session_time": "2026-03-31T01:00:00+00:00",
      "start_date": "2026-03-01T00:00:00+08:00",
      "end_date": "2026-04-01T00:00:00+08:00"
    }

空結果（無符合 session）回應（200 OK）：

    {
      "user_id": "uuid-string",
      "total_sessions": 0,
      "closed_sessions": 0,
      "open_sessions": 0,
      "total_work_minutes": 0,
      "average_session_minutes": null,
      "first_session_time": null,
      "last_session_time": null,
      "start_date": "2026-03-01T00:00:00+08:00",
      "end_date": "2026-04-01T00:00:00+08:00"
    }

錯誤回應：

| HTTP Status | 情境 |
|-------------|------|
| 400 | current_user_id 缺失 |
| 401 | 未帶認證 header |
| 403 | 嘗試查詢他人 summary |
| 422 | start_date 或 end_date 為 naive datetime |

---

## 7. Minimal Test Plan

新建：backend/app/modules/attendance/tests/test_reporting_user_summary.py
不修改任何現有測試檔案。

| Test ID | 測試函數名稱 | 驗證項目 |
|---------|-------------|----------|
| USR-01 | test_basic_summary_counts | total/closed/open sessions 計數正確；total_work_minutes 讀取 duration_minutes |
| USR-02 | test_date_range_filter | start_date/end_date 過濾只計入 punch_in_time 在範圍內的 sessions |
| USR-03 | test_cross_midnight_session_counted | punch_in 3/31 23:50 Taipei 計入 3 月 summary，不計入 4 月 |
| USR-04 | test_null_duration_not_counted | open session duration_minutes IS NULL 不影響 total_work_minutes |
| USR-05 | test_tenant_isolation | company A 使用者查不到 company B 的 summary（total=0） |
| USR-06 | test_user_scope_forbidden | 員工查詢他人 summary 回傳 403 |
| USR-07 | test_naive_datetime_returns_422 | start_date 無 tzinfo 回傳 422 |
| USR-08 | test_empty_result_returns_zeros | 無符合 session 時回傳全零 summary，不報錯 |

USR-03 詳細設計（跨日歸屬）：

    # punch_in = 2026-03-31 23:50 Taipei = 2026-03-31 15:50 UTC
    # 查 3 月範圍 (Taipei UTC boundaries) -> 應計入 total_sessions
    # 查 4 月範圍 -> 不應計入

USR-04 詳細設計（NULL duration）：

    # 建立 open session（duration_minutes=None）
    # 建立 closed session（duration_minutes=480）
    # 期望：total_work_minutes == 480（不受 None 影響）
    # 期望：open_sessions == 1，closed_sessions == 1

---

## 8. 刻意延後至後續 Steps 的項目

| 項目 | 延後原因 | 預計時機 |
|------|----------|----------|
| GET /api/v1/attendance/reports/company-summary | 需跨用戶聚合，複雜度高 | Step 3 |
| Manager 查詢他人 summary | 目前 Header auth 無 role 欄位 | JWT migration 後 |
| SQL 端 SUM() / GROUP BY 優化 | 應用層聚合 Phase 1 足夠 | 資料量超 10 萬 sessions 時評估 |
| session_date 欄位 | WP-11-06_SESSION_DATE_FEASIBILITY.md 決策不引入 | 未來性能優化 |
| CSV export | 超出 Reporting v1 範圍 | 未來 WP |

---

## 9. Implementation Order

建議按以下順序實作，每步確認後再進行下一步：

1. schemas.py — 新增 UserSummaryResponse
   確認所有 Optional 欄位正確標記

2. repo.py — 在 ReportingRepository 內新增 get_user_summary_sessions()
   確認查詢不含 DATE() / EXTRACT() / punch_out_time
   確認 tenant isolation（WHERE company_id）
   確認 user_id 為必填參數

3. api.py — 新增 GET /api/v1/attendance/reports/user-summary
   確認 _normalize_to_utc() 正確呼叫
   確認 user scope（不允許查他人，403）
   確認 naive datetime 422 攔截
   確認 average_session_minutes 除以零防護

4. tests/test_reporting_user_summary.py — 實作 USR-01 ~ USR-08
   優先實作 USR-03（跨月歸屬）
   優先實作 USR-04（NULL duration）
   優先實作 USR-05（tenant isolation）

---

## 10. Code Review Checklist（Step 2 專用）

查詢安全：
- [ ] WHERE 子句中 punch_in_time 無函數包裹
- [ ] 無 punch_out_time 用於範圍過濾
- [ ] 月份邊界使用 Asia/Taipei 計算後轉 UTC

時區安全：
- [ ] 所有傳入 DB 的 datetime 均為 timezone-aware
- [ ] naive datetime 傳入時回傳 422
- [ ] _normalize_to_utc() 在 API 層正確呼叫

Canonical Duration：
- [ ] total_work_minutes 讀取 duration_minutes（不重新計算）
- [ ] open session（duration_minutes IS NULL）防禦：or 0
- [ ] average_session_minutes 除以零防護：closed_sessions == 0 時回傳 None

Tenant / Scope：
- [ ] 所有查詢強制 WHERE company_id = ?
- [ ] 員工無法查詢他人 summary（403）

測試：
- [ ] USR-03（跨月歸屬）通過
- [ ] USR-04（NULL duration）通過
- [ ] USR-05（tenant isolation）通過
- [ ] USR-07（naive datetime 422）通過

---

*文件完畢。Step 2 Implementation Plan 覆蓋範圍：GET /api/v1/attendance/reports/user-summary ONLY*
*company-summary 在本計畫中刻意延後，待 Step 2 穩定後進行 Step 3。*
