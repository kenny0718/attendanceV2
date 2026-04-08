# WP-11-06 Reporting Query Guardrails

**文件版本:** 1.0
**建立日期:** 2026-03-13
**類型:** ANALYSIS + DOCUMENTATION ONLY
**關聯稽核:** ATTENDANCE_SYSTEM_AUDIT_REPORT.md P1-06 / §3.1 / §3.4
**狀態:** ACTIVE — WP-11-06 實作前必讀

---

## 目的

定義 WP-11-06 報表查詢的安全模式與禁止模式。
任何違反本文件規則的查詢均視為高風險，須在 code review 時攔截。
本文件不修改任何程式碼、schema 或 migration。

---

## 1. 禁止查詢模式

### 1.1 函數包裹 indexed column — 索引失效

下列模式會使 PostgreSQL 無法使用索引，導致全表掃描：

**禁止 (SQL):**

    WHERE DATE(punch_in_time) = target_date
    WHERE DATE(punch_in_time AT TIME ZONE Asia/Taipei) = target_date
    WHERE EXTRACT(YEAR FROM punch_in_time) = 2026
    WHERE EXTRACT(MONTH FROM punch_in_time) = 3
    WHERE CAST(punch_in_time AS DATE) = target_date

**禁止 (SQLAlchemy):**

    func.date(AttendanceSession.punch_in_time) == target_date
    extract(year, AttendanceSession.punch_in_time) == 2026

**根本原因:** 函數包裹使 PostgreSQL query planner 無法使用
idx_sessions_company_punch_in BTree 索引，退化為全表掃描。
### 1.2 punch_out_time 用於報表歸屬過濾

**禁止 (SQL):**

    WHERE punch_out_time BETWEEN :start AND :end
    WHERE punch_out_time >= :start AND punch_out_time < :end
    WHERE DATE(punch_out_time) = :target_date

**禁止 (SQLAlchemy):**

    AttendanceSession.punch_out_time.between(start, end)
    AttendanceSession.punch_out_time >= start

**三重危險 (稽核 P1-06):**

| 危險 | 說明 |
|------|------|
| NULL 靜默排除 | open session 的 punch_out_time 為 NULL；NULL BETWEEN x AND y = FALSE，session 被靜默排除 |
| 語義錯誤 | 跨月 session (punch_in 3/31, punch_out 4/1) 應歸屬 3 月，用 punch_out_time 過濾則歸屬 4 月 |
| 無索引 | attendance_sessions 無 punch_out_time 索引，全表掃描 |

**punch_out_time 的合法用途:**

- 計算工作時長 (punch_out_time - punch_in_time) — 僅在應用層，不在 WHERE 子句
- 顯示下班時間 (SELECT punch_out_time) — 合法
- NULL check (IS NULL / IS NOT NULL) 用於過濾 open/closed session — 合法

---

### 1.3 naive datetime 比較

**禁止:**

    # Python: naive datetime 傳入 TIMESTAMPTZ column
    punch_in_time = datetime(2026, 3, 1, 0, 0, 0)   # no tzinfo
    query.filter(AttendanceSession.punch_in_time >= punch_in_time)  # FORBIDDEN

**要求:** 所有與 TIMESTAMPTZ column 比較的 datetime 物件必須為 timezone-aware。

---

### 1.4 客戶端 datetime 未轉 UTC 直接過濾

**禁止:**

    # API 層直接將 start_date 傳入 repo (未轉 UTC)
    if start_date:
        query = query.filter(punch_in_time >= start_date)  # FORBIDDEN
        # 若 start_date 為 Taipei 時間，偏差 8 小時

**要求:** API 層必須先將 start_date / end_date 轉換為 UTC，再傳入 repo。

---

### 1.5 報表層重新計算工時

**禁止:**

    -- SQL: 重新計算工時
    SELECT EXTRACT(EPOCH FROM (punch_out_time - punch_in_time)) / 60 AS work_minutes

    -- Python: 報表層重算
    work_minutes = (session.punch_out_time - session.punch_in_time).total_seconds() / 60

**要求:** 報表工時必須讀取 duration_minutes 欄位（canonical source，SA v2.1 §28）。

---
## 2. 安全查詢模式

### 2.1 標準月報查詢模式

使用 Asia/Taipei 月份邊界轉換為 UTC，直接比較 indexed column。

    from zoneinfo import ZoneInfo
    from datetime import datetime, timezone
    from sqlalchemy import and_
    TZ_TAIPEI = ZoneInfo(Asia/Taipei)

    def get_monthly_sessions(db, company_id: str, year: int, month: int):
        # Step 1: Asia/Taipei 月份邊界
        if month == 12:
            next_year, next_month = year + 1, 1
        else:
            next_year, next_month = year, month + 1
        start_taipei = datetime(year, month, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
        end_taipei   = datetime(next_year, next_month, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)

        # Step 2: 轉換為 UTC
        start_utc = start_taipei.astimezone(timezone.utc)
        end_utc   = end_taipei.astimezone(timezone.utc)

        # Step 3: 查詢（命中 idx_sessions_company_punch_in）
        return db.query(AttendanceSession).filter(
            and_(
                AttendanceSession.company_id == company_id,
                AttendanceSession.punch_in_time >= start_utc,
                AttendanceSession.punch_in_time <  end_utc
            )
        ).all()

**索引命中分析:**

    查詢: WHERE company_id = X AND punch_in_time >= A AND punch_in_time < B
    索引: idx_sessions_company_punch_in (company_id, punch_in_time)
    掃描類型: Index Range Scan
    函數包裹: 無
    效能: O(log N + result_size)

---

### 2.2 日報查詢模式（單日）

    from datetime import timedelta

    def get_daily_sessions(db, company_id: str, target_taipei_date):
        start_taipei = datetime(
            target_taipei_date.year,
            target_taipei_date.month,
            target_taipei_date.day,
            0, 0, 0, tzinfo=TZ_TAIPEI
        )
        end_taipei = start_taipei + timedelta(days=1)
        start_utc  = start_taipei.astimezone(timezone.utc)
        end_utc    = end_taipei.astimezone(timezone.utc)

        return db.query(AttendanceSession).filter(
            and_(
                AttendanceSession.company_id == company_id,
                AttendanceSession.punch_in_time >= start_utc,
                AttendanceSession.punch_in_time <  end_utc
            )
        ).all()

---

### 2.3 應用層業務日分組模式

當需要按業務日分組時，必須在 Python 應用層執行：

    from collections import defaultdict

    def group_by_taipei_date(sessions):
        grouped = defaultdict(list)
        for session in sessions:
            taipei_date = session.punch_in_time.astimezone(TZ_TAIPEI).date()
            grouped[taipei_date].append(session)
        return dict(grouped)

    # 禁止 SQL: GROUP BY DATE(punch_in_time)              -- UTC date，時區錯誤
    # 禁止 SQL: GROUP BY DATE(punch_in_time AT TIME ZONE ...) -- 索引失效

---

### 2.4 start_date / end_date API 層安全處理模式

(WP-11-06 實作 AttendanceHistoryRequest 過濾時使用)

    def normalize_to_utc(dt):
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ_TAIPEI)  # 假設為 Taipei（最寬容解釋）
        return dt.astimezone(timezone.utc)

    # API endpoint:
    start_utc = normalize_to_utc(request.start_date)
    end_utc   = normalize_to_utc(request.end_date)
    sessions  = repo.get_sessions(
        company_id=company_id,
        start_utc=start_utc,
        end_utc=end_utc
    )

    # Repo:
    def get_sessions(self, ..., start_utc=None, end_utc=None):
        if start_utc:
            query = query.filter(AttendanceSession.punch_in_time >= start_utc)
        if end_utc:
            query = query.filter(AttendanceSession.punch_in_time <  end_utc)

---

### 2.5 duration_minutes 防禦性讀取模式

    # 報表顯示工時（open session: None -> 0）
    work_minutes = session.duration_minutes or 0

    # 月報加總
    total_minutes = sum(s.duration_minutes or 0 for s in sessions)

    # 禁止:
    # work_minutes = (session.punch_out_time - session.punch_in_time).total_seconds() / 60

---
## 3. 索引使用指南

### 3.1 attendance_sessions 現有索引

| 索引 | 欄位 | 適用查詢 | 報表可用 |
|------|------|---------|----------|
| idx_sessions_company_punch_in | company_id, punch_in_time | 月報、日報、歷史查詢 | YES |
| idx_sessions_company_user | company_id, user_id | 個人歷史分頁 | 部分 |
| uq_sessions_company_user_open | company_id, user_id (WHERE open) | 打卡狀態查詢 | NO |
| idx_sessions_status_open | status (WHERE open) | open session 查詢 | NO |
| (缺失) | punch_out_time | 無 | 禁止用於過濾 |

### 3.2 索引使用規則

1. 月報查詢必須命中 idx_sessions_company_punch_in
2. WHERE 子句中 punch_in_time 不得有任何函數包裹
3. punch_out_time 禁止用於歸屬過濾
4. 若未來引入 session_date 欄位，可建立 (company_id, session_date) 索引
   但在此之前，不可使用 session_date 進行任何查詢

---

## 4. Code Review Checklist

WP-11-06 任何涉及 attendance_sessions 查詢的 PR，必須通過以下全部檢查項目：

**時區安全:**
- [ ] 月份邊界以 Asia/Taipei 計算後轉換為 UTC
- [ ] 所有傳入 DB 查詢的 datetime 均為 timezone-aware
- [ ] 無 naive datetime (datetime without tzinfo) 傳入 SQLAlchemy filter

**索引安全:**
- [ ] WHERE 子句中 punch_in_time 無函數包裹 (無 DATE(), EXTRACT(), CAST())
- [ ] 無 GROUP BY DATE(punch_in_time) 或 GROUP BY DATE(punch_in_time AT TIME ZONE ...)
- [ ] 月報查詢使用 punch_in_time >= start_utc AND punch_in_time < end_utc 模式

**語義安全:**
- [ ] 無 punch_out_time 用於報表歸屬過濾
- [ ] 無 punch_out_time BETWEEN 或 punch_out_time <= end_date
- [ ] duration_minutes 讀取有 or 0 防禦（open session NULL 處理）
- [ ] 報表工時讀取自 duration_minutes，未重新計算

**start_date / end_date 實作安全 (若本 PR 實作此功能):**
- [ ] API 層有 normalize_to_utc() 或等效轉換
- [ ] Repo 過濾使用 punch_in_time，非 punch_out_time
- [ ] start_date / end_date 型別保持 Optional[datetime]，非 date

---

## 5. 禁止模式摘要表

| 禁止模式 | 風險類型 | 影響 |
|---------|---------|------|
| DATE(punch_in_time) | 索引失效 | 全表掃描 |
| EXTRACT(...FROM punch_in_time) | 索引失效 | 全表掃描 |
| CAST(punch_in_time AS DATE) | 索引失效 | 全表掃描 |
| punch_out_time BETWEEN x AND y | NULL 排除 + 語義錯誤 + 無索引 | 資料遺失 + 全表掃描 |
| punch_out_time >= start 作歸屬過濾 | 語義錯誤 | 跨月 session 誤分類 |
| naive datetime 傳入 TIMESTAMPTZ | 時區錯誤 | 不確定行為 |
| client datetime 未轉 UTC 直接過濾 | 時區偏差 | 8 小時偏差 |
| 報表層重新計算 punch_out - punch_in | 語義違反 | 違反 SA v2.1 §28 |
| GROUP BY DATE(punch_in_time) | 時區錯誤 | Taipei 凌晨打卡歸屬偏移 |

---

## 6. 安全模式快速參考

**月報查詢 (一行版):**

    # 在 Asia/Taipei 計算月份邊界 -> 轉 UTC -> 比較 punch_in_time (indexed)
    WHERE company_id = :cid
      AND punch_in_time >= :month_start_utc  -- 2026-02-28 16:00+00 for March
      AND punch_in_time <  :month_end_utc    -- 2026-03-31 16:00+00 for March

**業務日計算 (Python):**

    taipei_date = session.punch_in_time.astimezone(TZ_TAIPEI).date()

**工時讀取:**

    work_minutes = session.duration_minutes or 0
