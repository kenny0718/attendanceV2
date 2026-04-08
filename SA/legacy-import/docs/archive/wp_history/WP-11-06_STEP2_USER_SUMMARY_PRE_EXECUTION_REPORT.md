# WP-11-06 Step 2 User Summary Pre-Execution Report

**建立日期：** 2026-03-13
**任務：** WP-11-06 Reporting v1 Step 2 Pre-Execution
**類型：** PRE-EXECUTION REPORT (Documentation Only)
**狀態：** ACTIVE
**覆蓋範圍：** GET /api/v1/attendance/reports/user-summary ONLY

---

## 1. Step 1 Current State Verification

### 1.1 Step 1 Endpoint 實作狀態

| 項目 | 狀態 | 說明 |
|------|------|------|
| GET /api/v1/attendance/sessions | 已實作 | api.py 行 618，router_v1 已註冊 |
| ReportingRepository | 已實作 | repo.py，含 get_sessions_for_reporting() 和 count_sessions_for_reporting() |
| get_reporting_repository() | 已實作 | factory function，可直接複用 |
| _normalize_to_utc() | 已實作 | api.py，可直接複用 |
| SessionsListResponse | 已實作 | schemas.py |
| test_reporting_sessions.py | 已實作 | 16/16 tests passed |

### 1.2 ReportingRepository 可複用性評估

現有 get_sessions_for_reporting() 回傳 List[AttendanceSession]，
包含所有 user-summary 聚合所需欄位：
  - punch_in_time（first/last session time）
  - duration_minutes（canonical 工時來源）
  - status（open/closed 計數）

user-summary 聚合計算在應用層（Python）執行，不需要額外 SQL 聚合查詢。
此設計保持與 Step 1 相同的索引命中模式，符合 guardrails。

注意：get_user_summary_sessions() 為新方法，但實作邏輯幾乎與
get_sessions_for_reporting() 相同，差異僅在 user_id 為必填（非 Optional）。
不修改舊方法，在 ReportingRepository 內新增。

### 1.3 Blockers 評估

| 項目 | 狀態 |
|------|------|
| Step 1 測試全部通過 | PASS 16/16 |
| policy_engine.py 時區計算正確 | PASS 28/28 |
| 業務日歸屬規則明確 | PASS |
| Query guardrails 明確 | PASS |
| models.py 無需修改 | CONFIRMED |
| 現有索引足夠 | CONFIRMED idx_sessions_company_punch_in |

---

## 2. Readiness Verdict: GO

所有 Step 1 基礎均已穩定，無阻塞項目。Step 2 可安全進行。

前提條件（實作前必須遵守）：

1. user-summary 所有 filter 使用 punch_in_time，不使用 punch_out_time
2. total_work_minutes 必須讀取 duration_minutes 欄位（canonical source）
3. duration_minutes 為 NULL 的 session（open session）不計入工時：or 0
4. start_date / end_date 為 naive datetime 時回傳 422
5. 員工只能查詢自己的 summary（user scope）
6. 不修改 models.py 或任何 migration 檔案
7. 不實作 company-summary（Step 3）

---

## 3. Endpoint 範圍定義

    GET /api/v1/attendance/reports/user-summary

此步驟明確不包含：
- GET /api/v1/attendance/reports/company-summary（Step 3）
- 跨用戶彙總（管理者查所有員工匯總）
- CSV export
- 任何 schema migration
- Step 1 sessions endpoint 修改

---

## 4. Summary Response 欄位定義

| 欄位 | 類型 | 計算規則 |
|------|------|----------|
| user_id | str | 來自 JWT current_user_id |
| total_sessions | int | COUNT(*) 含 open + closed |
| closed_sessions | int | COUNT(status == closed) |
| open_sessions | int | COUNT(status == open) |
| total_work_minutes | int | SUM(duration_minutes or 0)；讀 canonical 欄位 |
| average_session_minutes | Optional[float] | total_work_minutes / closed_sessions；0 closed 時為 None |
| first_session_time | Optional[datetime] | MIN(punch_in_time)；應用層計算；無 session 時為 None |
| last_session_time | Optional[datetime] | MAX(punch_in_time)；應用層計算；無 session 時為 None |
| start_date | Optional[datetime] | 原樣回傳查詢的起始日期 |
| end_date | Optional[datetime] | 原樣回傳查詢的結束日期 |

計算規則補充：

  total_work_minutes = sum(s.duration_minutes or 0 for s in sessions)
  # 禁止：(punch_out_time - punch_in_time).total_seconds() / 60

  average_session_minutes = (
      total_work_minutes / closed_sessions
      if closed_sessions > 0 else None
  )

  first_session_time = min(s.punch_in_time for s in sessions) if sessions else None
  last_session_time  = max(s.punch_in_time for s in sessions) if sessions else None

---

## 5. Files to Modify

需修改的檔案：

| 檔案 | 修改類型 | 說明 |
|------|----------|------|
| backend/app/modules/attendance/schemas.py | 新增 Schema | UserSummaryResponse |
| backend/app/modules/attendance/repo.py | 在 ReportingRepository 新增方法 | get_user_summary_sessions() |
| backend/app/modules/attendance/api.py | 新增 endpoint | GET /api/v1/attendance/reports/user-summary |
| backend/app/modules/attendance/tests/test_reporting_user_summary.py | 新建 | USR-01 ~ USR-08 |

不得修改的檔案：

| 檔案 | 原因 |
|------|------|
| models.py | 無需新增欄位 |
| policy_engine.py | 與 reporting 無關 |
| service.py | user-summary 為唯讀查詢，不需要 service layer |
| 任何 migration 檔案 | WP-11-06 不引入 migration |
| Step 1 sessions endpoint | 不修改現有 endpoint |
| test_reporting_sessions.py | 不修改現有測試 |

---

## 6. Query Rules

允許模式（Index Range Scan）：

    WHERE company_id = :cid
      AND user_id    = :uid
      AND punch_in_time >= :start_utc
      AND punch_in_time <  :end_utc

禁止模式（任何違反均為 P1 缺陷）：

    DATE(punch_in_time)               -- 索引失效
    EXTRACT(month FROM punch_in_time)  -- 索引失效
    CAST(punch_in_time AS DATE)        -- 索引失效
    punch_out_time BETWEEN x AND y    -- NULL 危險 + 語義錯誤 + 無索引
    punch_out_time - punch_in_time     -- 禁止重算工時
    func.date(AttendanceSession.punch_in_time)  -- SQLAlchemy 版，禁止

---

## 7. Risks

| 風險 | 說明 | 嚴重程度 |
|------|------|----------|
| total_work_minutes 重算工時 | 誤用 punch_out - punch_in 而非 duration_minutes | P1 |
| average_session_minutes 除以零 | closed_sessions == 0 時未處理，拋出 ZeroDivisionError | P1 |
| open session 計入工時 | duration_minutes IS NULL 未做 or 0 防禦 | P1 |
| start_date/end_date 時區錯誤 | 未呼叫 _normalize_to_utc()，直接傳入 repo | P1 |
| user scope 漏洞 | 未驗證 user_id，員工可查他人資料 | P1 |
| naive datetime 未攔截 | 未檢查 tzinfo，允許 naive datetime 進入 DB 查詢 | P1 |
| company-summary 提早實作 | 本 Step 不實作跨用戶彙總，誤加入導致 scope 蔓延 | P2 |

---

## 8. Test Plan（設計，不實作）

| Test ID | 案例 | 驗證重點 |
|---------|------|----------|
| USR-01 | 基本 summary 查詢 | total_sessions, closed_sessions, open_sessions 計數正確 |
| USR-02 | start_date/end_date 日期範圍過濾 | 僅計入 punch_in_time 在範圍內的 sessions |
| USR-03 | 跨日 session 計數 | punch_in 3/31 23:50 Taipei 正確計入 3 月 |
| USR-04 | NULL duration_minutes 不計入工時 | open session 的 duration_minutes IS NULL 不影響 total_work_minutes |
| USR-05 | Tenant Isolation | company A 使用者查不到 company B 的 summary |
| USR-06 | User Scope | 員工查他人 summary 回傳 403 |
| USR-07 | Naive datetime 回傳 422 | start_date 無 tzinfo 回傳 422 |
| USR-08 | 空結果行為 | 無符合 session 時回傳全零 summary，不報錯 |

---

*文件完畢。Readiness Verdict: GO*
*下一步：依照 WP-11-06_STEP2_USER_SUMMARY_IMPLEMENTATION_PLAN.md 實作 user-summary endpoint。*
