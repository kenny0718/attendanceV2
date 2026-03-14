# WP-11-06 Reporting Boundary Decisions

**文件版本:** 1.0
**建立日期:** 2026-03-13
**類型:** ANALYSIS + DOCUMENTATION ONLY
**關聯稽核:** ATTENDANCE_SYSTEM_AUDIT_REPORT.md P1-04 / P1-05 / P1-06
**狀態:** ACTIVE — WP-11-06 實作前必讀

---

## 目的

在進入 WP-11-06 (Reporting v1) 實作之前，明確記錄三個設計決策：

1. Reporting 歸屬規則 (session 屬於哪個業務日 / 月份)
2. start_date / end_date schema 欄位現況與策略
3. session_date 欄位是否引入，以及時機

本文件不修改任何程式碼、schema 或 migration。

## 1. Reporting 歸屬規則

### 1.1 Session 所屬業務日

**規範來源:** SA v2.1 §29.2 Session Ownership Date

| 屬性 | 規則 |
|------|------|
| 定義 | session 所屬業務日 = punch_in_time 轉換為 Asia/Taipei 後的 .date() |
| 跨午夜 | session 於 23:50 Taipei 打卡、隔天 01:30 離開 -> 歸屬當天 |
| 錯誤做法 | punch_in_time.date() (UTC date) — Taipei 00:00~07:59 打卡偏移 1 天 |
| 正確做法 | punch_in_time.astimezone(TZ_TAIPEI).date() |

正確計算範例:

    from zoneinfo import ZoneInfo
    from datetime import datetime, timezone
    TZ_TAIPEI = ZoneInfo('Asia/Taipei')

    # punch_in = 2026-03-31 23:00 Taipei = 2026-03-31 15:00 UTC
    punch_in_utc = datetime(2026, 3, 31, 15, 0, 0, tzinfo=timezone.utc)
    session_date = punch_in_utc.astimezone(TZ_TAIPEI).date()
    # => date(2026, 3, 31)  ✅ 歸屬 3 月 31 日

高風險情境 (Taipei 凌晨打卡):

    # punch_in = 2026-03-12 00:30 Taipei = 2026-03-11 16:30 UTC
    punch_in_utc = datetime(2026, 3, 11, 16, 30, 0, tzinfo=timezone.utc)

    wrong   = punch_in_utc.date()                         # => 2026-03-11 ❌ UTC date
    correct = punch_in_utc.astimezone(TZ_TAIPEI).date()   # => 2026-03-12 ✅ Taipei date

---

### 1.2 月報所屬月份

**規範來源:** SA v2.1 §29.3 Monthly Reporting Ownership

| 屬性 | 規則 |
|------|------|
| 定義 | 月報月份 = punch_in_time 的 Asia/Taipei 月份 |
| 跨月 session | punch_in 在 3/31 23:50 Taipei, punch_out 在 4/1 00:30 Taipei -> 歸屬 3 月 |
| 過濾欄位 | 必須以 punch_in_time 為範圍過濾欄位，絕不可用 punch_out_time |

月份邊界計算 (WP-11-06 實作時必用):

    def get_month_utc_boundaries(year: int, month: int):
        if month == 12:
            next_year, next_month = year + 1, 1
        else:
            next_year, next_month = year, month + 1
        TZ_TAIPEI = ZoneInfo('Asia/Taipei')
        start = datetime(year, month, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
        end   = datetime(next_year, next_month, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
        return start.astimezone(timezone.utc), end.astimezone(timezone.utc)

    # 2026-03:
    # start_utc = 2026-02-28 16:00:00+00  (3/1 00:00 Taipei)
    # end_utc   = 2026-03-31 16:00:00+00  (4/1 00:00 Taipei)

跨午夜歸屬驗證:

    punch_in  = 2026-03-31 23:00 Taipei = 2026-03-31 15:00 UTC
    punch_out = 2026-04-01 02:00 Taipei = 2026-03-31 18:00 UTC
    month_end_utc = 2026-03-31 16:00 UTC

    punch_in_time < month_end_utc ?
    2026-03-31 15:00 UTC < 2026-03-31 16:00 UTC -> TRUE
    => 正確歸屬 3 月 ✅

---

### 1.3 Canonical 工時欄位

**規範來源:** SA v2.1 §28, §30 Report Consistency Rule

| 屬性 | 規則 |
|------|------|
| 報表工時來源 | 唯一來源: attendance_sessions.duration_minutes |
| 計算時機 | 僅在 punch_out 時寫入一次，之後只讀不算 |
| 禁止 | 報表層重新計算 punch_out_time - punch_in_time |
| 禁止 | 前端計算工時 |
| NULL 處理 | open session 的 duration_minutes 為 NULL，報表層必須防禦性處理 (or 0) |

---

## 2. start_date / end_date Schema 欄位策略

### 2.1 現況 (稽核 P1-04)

**current state:**

| 層級 | 狀態 | 詳細 |
|------|------|------|
| Schema 定義 | 已定義 | AttendanceHistoryRequest.start_date / end_date，Optional[datetime]，schemas.py:154-159 |
| API endpoint | 未傳遞 | GET /api/v1/attendance/history 接收參數後丟棄，未傳入 repo |
| Repo 層 | 未實作 | get_sessions() 無日期範圍參數 |
| 前端使用 | 無 | 前端未傳遞此參數 |

**結論: start_date / end_date 為 placeholder schema，已定義但從未實作。目前為完全無效的死欄位。**

**risk:**
若 WP-11-06 開發者補實作時未遵守安全查詢規則，極易引入危險模式:

    # 危險 A: 直接將 client datetime 當 UTC 邊界 (時區未轉換)
    if start_date:
        query = query.filter(AttendanceSession.punch_in_time >= start_date)
        # 若 start_date 為 Taipei 時間但未轉 UTC，偏差 8 小時

    # 危險 B: 用 punch_out_time 作歸屬過濾
    if end_date:
        query = query.filter(AttendanceSession.punch_out_time <= end_date)
        # 語義錯誤: 跨月 session 誤分類; open session 被靜默排除 (NULL < end_date = FALSE)

### 2.2 決策

| 選項 | 決策 | 理由 |
|------|------|------|
| 立即移除 schema 欄位 | 不執行 | 超出本 Phase 範圍；移除等同 API breaking change |
| 立即實作 | 不執行 | WP-11-06 才是正確時機 |
| 保留 schema 標記未啟用，WP-11-06 實作時強制遵守 guardrails | 採用 | 風險最低 |

**實作時機:** WP-11-06

**WP-11-06 實作 start_date / end_date 的強制規則:**

1. Schema 型別保持 Optional[datetime] (含 tzinfo)，不得改為 date
2. API 層收到後，必須先轉換為 UTC boundary，再傳入 repo
3. Repo 過濾條件: punch_in_time >= start_utc AND punch_in_time < end_utc
4. 禁止直接 punch_in_time >= start_date (client datetime 不保證為 UTC)
5. 禁止 punch_out_time 作為範圍過濾欄位 (P1-06)
6. 防禦性處理 duration_minutes IS NULL (open session) 不可靜默排除

---

## 3. session_date 欄位策略

### 3.1 現況 (稽核 P1-05)

**current state:**

| 項目 | 狀態 |
|------|------|
| 欄位存在 | 否 - attendance_sessions 無 session_date, work_date, business_day 欄位 |
| Migration | 否 - 無任何相關 migration |
| 業務日計算 | 必須在應用層執行: punch_in_time.astimezone(TZ_TAIPEI).date() |
| 月報查詢 | UTC boundary 比較 punch_in_time，命中 idx_sessions_company_punch_in 索引 |

**risk:**

| 風險 | 說明 | 嚴重程度 |
|------|------|----------|
| 開發者錯誤 | 直接使用 punch_in_time.date() (UTC) 計算業務日 | P1 |
| SQL 層錯誤 | 嘗試 DATE(punch_in_time AT TIME ZONE ...) 於 WHERE -> 索引失效 | P1 |
| 分組錯誤 | GROUP BY DATE(punch_in_time) 使用 UTC 日期，凌晨打卡歸屬日偏移 | P1 |

### 3.2 決策

**結論: 維持現狀 (應用層計算)。session_date 欄位留待未來性能優化時評估引入。**

| 選項 | 決策 | 理由 |
|------|------|------|
| 立即引入 (migration) | 不執行 | 超出本 Phase 範圍；現有索引足夠支撐 WP-11-06 |
| WP-11-06 中引入 | 不建議 | WP-11-06 應專注 reporting 邏輯，引入新欄位增加 migration 複雜度 |
| 未來性能優化時引入 | 建議路徑 | 見觸發條件 |

**未來引入 session_date 的觸發條件 (任一成立即可評估):**

1. production 月報查詢出現 slow query (punch_in_time range scan 不足夠)
2. 報表需要在 SQL 層 GROUP BY session_date (應用層分組效能不足)
3. 多次 WP-11-06 實作錯誤均源自業務日計算錯誤

**若未來引入，migration 規範:**

    -- 使用 PostgreSQL GENERATED STORED 確保不可手動覆寫
    ALTER TABLE attendance_sessions
        ADD COLUMN session_date DATE
            GENERATED ALWAYS AS
            (CAST(punch_in_time AT TIME ZONE 'Asia/Taipei' AS DATE)) STORED;

    CREATE INDEX idx_sessions_company_session_date
        ON attendance_sessions (company_id, session_date);

---

## 4. 摘要決策表

| Issue | ID | 現況 | 風險 | 決策 | 實作時機 |
|-------|-----|------|------|------|----------|
| start_date/end_date 未實作 | P1-04 | placeholder schema 死欄位 | 補實作時易引入危險查詢 | 保留 schema，WP-11-06 實作時強制遵守 guardrails | WP-11-06 |
| session_date 欄位不存在 | P1-05 | 無此欄位，應用層計算 | 開發者易誤用 UTC date 或函數包裹 WHERE | 維持現狀，未來性能需求出現時再評估 | Future migration |
| punch_out_time 無報表索引 | P1-06 | 無 punch_out_time 索引；open session 為 NULL | 若用於 WHERE 過濾則全表掃描；NULL 語義錯誤 | 禁止用於報表歸屬過濾；查詢模式見 guardrails 文件 | N/A (永遠禁止) |
