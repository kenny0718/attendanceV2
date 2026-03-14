# Attendance Phase 1-3 Closeout Summary

**建立日期:** 2026-03-13
**類型:** DOCUMENTATION ONLY
**關聯文件:**
- ATTENDANCE_SYSTEM_AUDIT_REPORT.md
- WP-11-06_REPORTING_BOUNDARY_DECISIONS.md
- WP-11-06_REPORTING_QUERY_GUARDRAILS.md
- PHASE3_PRE_EXECUTION_REPORT.md

## 1. Overview

### 執行原因

2026-03-13 對 attendance 模組進行全面稽核 (ATTENDANCE_SYSTEM_AUDIT_REPORT.md)，發現 policy_engine.py 中存在三個 P1 等級的時區計算錯誤，以及多個跨模組的時間處理不一致問題。這些問題若不修正，將在 WP-11-06 (Reporting v1) 實作期間引發業務日歸屬錯誤和不安全的查詢模式。

### Phase 範圍

| Phase | 類型 | 範圍 |
|-------|------|------|
| Phase 1 | CODE FIX | policy_engine.py 三個 P1 時區 bug 修正 |
| Phase 2 | DOCUMENTATION | WP-11-06 前的 reporting 邊界決策與查詢安全規範 |
| Phase 3 | CONSISTENCY CLEANUP | 跨模組 naive datetime 清理、frontend 時區修正 |

---

## 2. Phase 1 Summary -- Policy Engine Time Fix

### 修正的三個 Bug

**P1-03 (WorkWindow.duration_minutes)**

- 位置: policy_engine.py 行 60-61
- 問題: datetime.today() 依賴 server local timezone，非 UTC+8 server 計算結果偏差
- 修正: 改用 date.min (固定基準日，與時區無關)

**P1-01 + P1-02 (_calculate_late)**

- 位置: policy_engine.py 行 426-431
- 問題: punch_in_time.date() 取 UTC 日期 + .replace(tzinfo=UTC) 貼標
  Taipei 00:00~07:59 打卡業務日偏移 1 天；work_start_time 被解讀為 UTC 時間，偏差 8 小時
- 修正: punch_in_time.astimezone(TZ_TAIPEI).date() 取業務日 + .replace(tzinfo=TZ_TAIPEI)

**P1-01 + P1-02 (_calculate_early_leave)**

- 位置: policy_engine.py 行 459-464
- 問題/修正: 同上，套用於 punch_out_time

**P1-01 + P1-02 (_calculate_work_minutes_split_shift)**

- 位置: policy_engine.py 行 625-631
- 問題/修正: 同上，套用於 split shift window 邊界計算

### 新增內容

- 模組頂層加入: from zoneinfo import ZoneInfo 和 TZ_TAIPEI = ZoneInfo(Asia/Taipei)
- from datetime import 加入 date

### 測試結果

- 執行: pytest app/modules/attendance/tests/test_policy_engine.py
- 結果: 28/28 passed
- 新增 4 個回歸測試 (TestTimezoneFixRegression):
  - test_p1_02_taipei_early_morning_punch_correct_date
  - test_p1_01_utc_punch_no_8hr_offset_on_late_check
  - test_p1_03_work_window_duration_minutes_timezone_safe
  - test_p1_02_split_shift_taipei_early_morning_correct_windows

### 刻意未動

- schema/models: 無修改
- API contract: 無修改
- reporting: 未實作
- 其他模組: 未觸及

---

## 3. Phase 2 Summary -- Reporting Boundary Decisions

Phase 2 為純文件決策，不修改任何程式碼。

### 建立的四條核心規則

**Rule 1: Session Ownership -- 業務日歸屬**

- 定義: 一筆 AttendanceSession 的業務日 = punch_in_time 換算 Asia/Taipei 所在的日期
- 依據: 出勤以「開始工作」為基準，與 punch_out 無關
- 邊界案例: 深夜跨日 (例: punch_in 23:50, punch_out 00:30+1d) 歸屬 punch_in 當日

**Rule 2: Report Month Ownership -- 月份歸屬**

- 定義: 月份報表以 punch_in_time Asia/Taipei month 為準
- 使用: 2025-01 月報包含所有 punch_in 換算 Taipei 後屬於 2025 年 1 月的 session

**Rule 3: Canonical Duration -- 工時來源**

- 定義: 所有工時統計使用 attendance_sessions.duration_minutes
- 禁止: 在 reporting 層重新計算 punch_out_time - punch_in_time
- 原因: duration_minutes 已由 policy_engine 正確計算，包含休息扣除

**Rule 4: Session Boundary -- punch_in_time 所有權**

- 定義: 跨日 session 的所有時間邊界以 punch_in_time 為基準，不以 punch_out_time 分割
- 禁止: 按 punch_out_time 做日期邊界切割或 BETWEEN 查詢

### Query Guardrails

BOUNDARY_DECISIONS.md 和 REPORTING_QUERY_GUARDRAILS.md 建立了明確的查詢安全規範:

| 模式 | 狀態 | 原因 |
|------|------|------|
| DATE(punch_in_time) | 禁止 | 依賴 DB server 時區，非 Asia/Taipei |
| EXTRACT(month FROM ...) | 禁止 | 同上 |
| CAST(punch_in_time AS DATE) | 禁止 | 同上 |
| punch_out_time BETWEEN ... | 禁止 | session ownership 以 punch_in 為準 |
| duration_minutes 重新計算 | 禁止 | 應使用 canonical duration |
| application-layer date filter | 允許 | Python datetime.astimezone(TZ_TAIPEI).date() |
| AT TIME ZONE Taipei (PostgreSQL) | 允許 | 明確指定時區的 SQL 運算 |

### 未來工作

- WP-11-06: Reporting v1 實作，須遵循上述所有規則
- start_date / end_date 過濾器實作（目前為 placeholder）
- naive datetime 拒絕 validator（待 start_date/end_date 啟用時同步加入）

---

## 4. Phase 3 Summary -- Consistency Cleanup

### 完成的修正 (5 個)

**Fix-A: P1-07 -- models.py status comment vs CHECK constraint**

- 檔案: backend/app/modules/attendance/models.py 行 95
- 修正: column comment 由錯誤列出 6 種狀態改為與 CHECK constraint 一致的 (open/closed)
- 注記: 擴充狀態 (pending/approved/rejected/missing_punch_out) 須先執行 migration 更新 ck_sessions_status

**Fix-B: P2-04 -- jwt.py datetime.utcnow() naive datetime**

- 檔案: backend/app/core/security/jwt.py 行 9, 37
- 修正: datetime.utcnow() -> datetime.now(timezone.utc)
- 效果: JWT iat/exp 在非 UTC server 上亦正確

**Fix-C: P2-03 -- test_business_invariant.py (12 處)**

- 檔案: backend/app/modules/attendance/tests/test_business_invariant.py
- 修正: 12 處 datetime.utcnow() -> datetime.now(timezone.utc)；import 加入 timezone

**Fix-D: P2-03 -- test_model_constraints.py (15 處)**

- 檔案: backend/app/modules/attendance/tests/test_model_constraints.py
- 修正: 15 處 datetime.utcnow() -> datetime.now(timezone.utc)；import 加入 timezone

**Fix-E: P2-01 -- Home.vue formatDateTime / formatTime 未指定時區**

- 檔案: frontend/src/views/Home.vue 行 279, 283
- 修正: dayjs(timestamp).format(...) -> dayjs(timestamp).tz(Asia/Taipei).format(...)
- 效果: 非 Asia/Taipei 瀏覽器使用者看到正確的 Taipei 時間

### Phase 3 延後項目

| 項目 | 原因 |
|------|------|
| tenants/auth/audit/notifications models datetime.utcnow | 需配合 DateTime->TIMESTAMPTZ migration |
| audit/backup tests conftest | 與上項連動 |
| backup/exporter.py datetime.utcnow | 影響限於 backup metadata，低優先 |
| schemas.py naive datetime validator | 延後至 WP-11-06 start_date/end_date 實作 |

### 測試結果

- 執行: pytest app/modules/attendance/tests/test_policy_engine.py
- 結果: 28/28 passed, 7 warnings
- 所有 5 個修改檔案通過 py_compile 語法驗證

---

## 5. Final Guardrails

以下規則為 attendance 模組所有後續開發的強制規範。

### 時間儲存

- 所有 timestamp 欄位使用 DateTime(timezone=True) (TIMESTAMPTZ)
- 所有 Python datetime 物件使用 timezone-aware (tzinfo 不得為 None)
- 禁止: datetime.utcnow()  ->  使用: datetime.now(timezone.utc)

### 業務日邊界

- 業務日計算一律以 Asia/Taipei 為準
- punch_in_time.astimezone(ZoneInfo("Asia/Taipei")).date() 為業務日
- work_start_time / work_end_time 視為 Asia/Taipei local time，比較前須 combine + replace(tzinfo=TZ_TAIPEI)

### Reporting 歸屬

- Session 歸屬日: punch_in_time Asia/Taipei date
- 月份歸屬: punch_in_time Asia/Taipei month
- Canonical 工時: attendance_sessions.duration_minutes (不得在 reporting 層重算)
- 跨日 session 不分割，以 punch_in 日為主

### 禁止的查詢模式

    -- 禁止 (依賴 DB server 時區)
    DATE(punch_in_time)
    EXTRACT(month FROM punch_in_time)
    CAST(punch_in_time AS DATE)

    -- 禁止 (session ownership 以 punch_in 為準)
    punch_out_time BETWEEN :start AND :end

    -- 禁止 (應使用 canonical duration)
    punch_out_time - punch_in_time

    -- 允許
    punch_in_time AT TIME ZONE "Asia/Taipei"
    -- 或 application-layer: punch_in_time.astimezone(TZ_TAIPEI).date()

### Frontend

- 所有 timestamp 顯示使用 dayjs(ts).tz("Asia/Taipei").format(...)
- 禁止: dayjs(ts).format(...) (依賴瀏覽器時區)

---

## 6. Deferred Items

以下項目在 Phase 1-3 中刻意延後，原因如下:

| 項目 | 類別 | 延後原因 | 建議處理時機 |
|------|------|---------|-------------|
| tenants/auth/audit/notifications models: DateTime -> TIMESTAMPTZ | P1-08 | 需要 migration，超出 Phase 3 範圍 | 各模組 architecture WP |
| auth/repo.py datetime.utcnow() | P1-08 | 同上 | 同上 |
| audit/service.py datetime.utcnow() | P1-08 | 同上 | 同上 |
| audit/backup tests conftest naive datetime | P1-08 | 與 model migration 連動 | 同上 |
| backup/exporter.py datetime.utcnow() | P1-08 | 影響限於 backup metadata | 備份模組 WP |
| schemas.py naive datetime 拒絕 validator | P2-02 | start_date/end_date 過濾未實作 | WP-11-06 實作期間 |
| AttendanceSession status 擴充 | P1-07 | 需 migration 更新 ck_sessions_status | 審批流程 WP |
| WP-11-06 Reporting v1 實作 | N/A | 超出本 audit/fix 範圍 | WP-11-06 |

---

## 7. Final Status

### Attendance 時間/Reporting 基礎 -- 穩定性評估

**結論: 可以進入 WP-11-06 實作。**

| 基礎項目 | 狀態 |
|---------|------|
| policy_engine.py 時區計算 | 已修正 (Phase 1) |
| 業務日歸屬規則 | 已文件化 (Phase 2) |
| 月份歸屬規則 | 已文件化 (Phase 2) |
| Canonical duration 規則 | 已文件化 (Phase 2) |
| Query guardrails | 已文件化 (Phase 2) |
| JWT naive datetime bug | 已修正 (Phase 3) |
| Test timezone consistency | 已修正 (Phase 3) |
| Frontend timezone display | 已修正 (Phase 3) |
| models.py comment vs constraint | 已修正 (Phase 3) |

### 前提條件

WP-11-06 實作前必須確認:

1. 所有 reporting query 遵循 Section 5 的 guardrails
2. start_date / end_date 過濾器實作時，同步加入 naive datetime 拒絕 validator
3. 跨日 session 的測試案例已涵蓋 punch_in 23:50 / punch_out 00:30+1d 等邊界情況

### 已知限制

- tenants/auth/audit 模組的 DateTime 欄位仍非 TIMESTAMPTZ (Defer-A)
  此限制不影響 attendance reporting，但需在各模組 WP 中修正
- AttendanceSession.status CHECK constraint 仍限於 open/closed (Defer-B)
  擴充審批流程前無法使用 pending/approved/rejected 狀態

---

*文件完畢。Phase 1-3 全部閉環。*
