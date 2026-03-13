# ATTENDANCE SYSTEM AUDIT REPORT

**稽核日期：** 2026-03-13
**稽核類型：** SCAN ONLY

---

## 目錄

1. 時間來源一致性
2. 業務日期歸屬邏輯
3. 報表查詢安全性
4. Schema 一致性審查
5. 前端時間處理
6. 文件 vs 程式碼一致性
7. 風險彙總 (P0 / P1 / P2)

---

## 1. 時間來源一致性

### 1.1 Production 程式碼掃描（排除 .bak / .backup / tests/）

#### 安全項目

| 檔案 | 行號 | 程式碼 | 風險等級 | 說明 |
|------|------|--------|----------|------|
| backend/app/modules/attendance/repo.py | 31 | return datetime.now(timezone.utc) | SAFE | timezone-aware UTC，符合規範 |
| backend/app/core/config.py | 30 | return datetime.now(timezone.utc) | SAFE | get_utc_now() helper，正確 |

#### 風險項目

| 檔案 | 行號 | 程式碼 | 風險等級 | 說明 |
|------|------|--------|----------|------|
| policy_engine.py | 57-58 | datetime.combine(datetime.today(), self.start_time) | P1 | datetime.today() 回傳 naive local datetime，若 server 時區非 UTC+8 則 WorkWindow.duration_minutes() 計算結果誤差 |
| policy_engine.py | 430 | expected_start = expected_start.replace(tzinfo=punch_in_time.tzinfo) | P1 | .replace(tzinfo=...) 只標記時區不做時刻轉換。若 punch_in_time 為 UTC，遲到判斷誤差最高 8 小時 |
| policy_engine.py | 465 | expected_end = expected_end.replace(tzinfo=punch_out_time.tzinfo) | P1 | 同上，影響早退判斷 |
| policy_engine.py | 637-638 | window_start/end_dt.replace(tzinfo=punch_in_time.tzinfo) | P1 | 同上，影響 WorkWindow 有效工時計算 |

.replace() vs .astimezone() 差異說明：

錯誤（目前做法）：expected_start.replace(tzinfo=UTC) 使 work_start_time 被視為 UTC 08:00 → Taipei 16:00（偏差 8 小時）

正確做法：
  business_date = punch_in_time.astimezone(TZ_TAIPEI).date()
  expected_start = datetime.combine(business_date, work_start_time).replace(tzinfo=TZ_TAIPEI)
  結果：work_start_time = Taipei 08:00 → UTC 00:00（正確）

### 1.2 測試程式碼掃描（informational）

| 檔案 | 出現次數 | 風險說明 |
|------|----------|----------|
| tests/test_business_invariant.py | 13 處 datetime.utcnow() | naive UTC，與 TIMESTAMPTZ column 比對可能引發 tz-aware 衝突 |
| tests/test_model_constraints.py | 14 處 datetime.utcnow() | 同上 |

### 1.3 其他模組（超出 attendance 核心範圍，informational）

| 模組 | 問題 |
|------|------|
| modules/tenants/models.py | default=datetime.utcnow（naive）|
| modules/auth/models.py | 多處 default=datetime.utcnow |
| modules/audit/models.py、service.py | datetime.utcnow() |
| core/security/jwt.py | now = datetime.utcnow() |

---

## 2. 業務日期歸屬邏輯

### 2.1 文件定義規則（SA_MODULE_SPEC_v2.1.md §29）

- session 所屬日期 = punch_in_time 的 Asia/Taipei 業務時區日期
- 月報所屬月份 = session 的 Asia/Taipei punch_in_time 所在月份
- 若 session 跨月，整體歸屬於 punch_in_time 所在月份
- raw_duration = punch_out_time - punch_in_time（UTC 減法，天然支援跨午夜）

### 2.2 跨午夜場景驗證

場景 A（指定測試情境）：
  punch_in  : 2026-03-31 23:00 Asia/Taipei  →  2026-03-31 15:00 UTC
  punch_out : 2026-04-01 02:00 Asia/Taipei  →  2026-03-31 18:00 UTC

| 問題 | 預期 | 程式碼行為 | 符合？ |
|------|------|-----------|--------|
| Session 歸屬日期 | March 31 | 無 session_date 欄位，須應用層計算 | 部分（邏輯正確但欄位缺失） |
| duration_minutes | 180 分鐘 | (18:00 UTC - 15:00 UTC) = 180 | OK |
| check_late 基準日期 | 2026-03-31（Taipei） | punch_in_time.date() → 2026-03-31（UTC 恰好相同） | 此例巧合正確 |

場景 B（高風險：Asia/Taipei 00:00~07:59 打卡）：
  punch_in  : 2026-03-12 00:30 Asia/Taipei  →  2026-03-11 16:30 UTC

| 問題 | 預期 | 程式碼行為 | 符合？ |
|------|------|-----------|--------|
| Session 所屬日期 | 2026-03-12 | 須應用層計算，目前未實作 | 未實作 |
| check_late 基準日期 | 2026-03-12（Taipei） | punch_in_time.date() → 2026-03-11（UTC） | 偏差 1 天 |

結論：policy_engine.py 在 Asia/Taipei 00:00~07:59 打卡的 session，遲到/早退判斷基準日期將錯誤偏移 1 天。
原因：程式碼使用 punch_in_time.date()（UTC 日期）而非 punch_in_time.astimezone(TZ_TAIPEI).date()（Taipei 日期）。

### 2.3 程式碼路徑清單

| 路徑 | 使用的日期欄位 | 問題 |
|------|--------------|------|
| policy_engine.py:424 check_late() | punch_in_time.date() UTC | 應改為 punch_in_time.astimezone(TZ_TAIPEI).date() |
| policy_engine.py:459 check_early_leave() | punch_out_time.date() UTC | 同上 |
| policy_engine.py:627,631 _calculate_effective_work() | punch_in_time.date() UTC | 同上 |
| repo.py get_sessions() | 無日期過濾 | 安全 |
| 報表查詢（WP-11-06） | 未實作 | 預防性風險 |

---

## 3. 報表查詢安全性

### 3.1 危險模式掃描結果

搜尋範圍：backend/app/modules/attendance/（排除 .bak / .backup）

| 模式 | 結果 |
|------|------|
| DATE( | 未發現 |
| EXTRACT( | 未發現 |
| CAST( | 未發現 |
| punch_out_time BETWEEN | 未發現 |
| func.date( | 未發現 |
| strftime | 未發現 |
| date_trunc | 未發現 |

現階段結論：目前 production 無任何危險查詢模式。

### 3.2 現有查詢索引安全性

| 端點 / 方法 | 查詢條件 | 命中索引 | 安全 |
|------------|---------|----------|------|
| GET /history → get_sessions() | company_id + user_id | idx_sessions_company_user | OK |
| GET /history 排序 | ORDER BY punch_in_time DESC | idx_sessions_company_punch_in | OK |
| GET /status → get_open_session() | company_id + user_id + status=open | uq_sessions_company_user_open（partial） | OK |
| get_recent_checkpoint() | company_id + user_id + punch_time >= cutoff | idx_checkpoints_company_user_time | OK |

### 3.3 AttendanceHistoryRequest Schema vs 實作不一致（P1）

schemas.py:154-159 定義了 start_date / end_date 過濾參數，但 repo.get_sessions() 及 API endpoint 均未實作這些參數。
P1 風險：未來補實作時，若開發者未遵循 UTC boundary 模式，極易引入 DATE() 函數或 punch_out_time BETWEEN 危險查詢。

### 3.4 punch_out_time 三重危險（預防性說明）

若未來有人以 punch_out_time 進行報表查詢：
1. NULL 風險：open session 的 punch_out_time 為 NULL，BETWEEN 會靜默排除。
2. 語義錯誤：跨午夜 session 應歸屬 punch_in 日期，用 punch_out 日期會誤分類。
3. 無索引：attendance_sessions 無 punch_out_time 索引，全表掃描。

### 3.5 推薦查詢模式

正確做法（以 Asia/Taipei 計算月份邊界，轉 UTC 後直接比較 indexed column）：
  from zoneinfo import ZoneInfo
  TZ_TAIPEI = ZoneInfo('Asia/Taipei')
  month_start_utc = datetime(year, month, 1, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
  month_end_utc   = datetime(year, month + 1, 1, tzinfo=TZ_TAIPEI).astimezone(timezone.utc)
  WHERE company_id = ? AND punch_in_time >= month_start_utc AND punch_in_time < month_end_utc
  -- 命中 idx_sessions_company_punch_in，Index Range Scan

---

## 4. Schema 一致性審查

### 4.1 Timestamp 型別一致性

| 表 | 欄位 | SQLAlchemy | PostgreSQL 型別 | 符合規範 |
|----|------|-----------|-----------------|----------|
| attendance_sessions | punch_in_time | DateTime(timezone=True) | TIMESTAMPTZ | OK |
| attendance_sessions | punch_out_time | DateTime(timezone=True) | TIMESTAMPTZ | OK |
| attendance_sessions | created_at | DateTime(timezone=True) | TIMESTAMPTZ | OK |
| attendance_sessions | updated_at | DateTime(timezone=True) | TIMESTAMPTZ | OK |
| attendance_punches | punch_time | DateTime(timezone=True) | TIMESTAMPTZ | OK |
| attendance_punches | created_at | DateTime(timezone=True) | TIMESTAMPTZ | OK |

結論：attendance 核心兩張表所有 datetime 欄位均為 TIMESTAMPTZ，符合 SA v2.1 規範。
對照：其他模組（tenants、auth、audit）使用 DateTime（無 timezone=True），為系統層面跨模組不一致。

### 4.2 session_date 欄位缺失

- attendance_sessions 無 session_date 欄位。
- 已由 docs/WP-11-06_SESSION_DATE_FEASIBILITY.md 分析並決議：目前暫不引入，保留為未來性能優化選項。
- 現狀影響：月報查詢必須透過應用層 Python 以 punch_in_time.astimezone(TZ_TAIPEI).date() 進行日期分組，無法在 SQL 層直接 GROUP BY session_date。
- 未來風險：若開發者使用 DATE(punch_in_time AT TIME ZONE ...) 於 WHERE 子句，將導致索引失效（全表掃描）。

### 4.3 duration_minutes 規範性

| 項目 | 狀態 | 說明 |
|------|------|------|
| 唯一寫入路徑 | OK | 只在 punch_out endpoint 寫入一次 |
| 計算規則 | OK | (punch_out_time - punch_in_time).total_seconds() / 60 |
| Break punches 隔離 | OK | 只寫入 attendance_punches 表，不觸及 session |
| Out checkpoints 隔離 | OK | 獨立表 attendance_out_checkpoints |
| Frontend 不重新計算 | OK | 只讀取 session.duration_minutes |
| NULL 處理 | 注意 | open session 的 duration_minutes 為 NULL，報表層必須防禦性處理 |

### 4.4 索引支援度評估

| 索引 | 欄位 | 支援場景 | 評估 |
|------|------|---------|------|
| idx_sessions_company_punch_in | company_id, punch_in_time | 月報範圍查詢 | OK |
| idx_sessions_company_user | company_id, user_id | 個人歷史、分頁 | OK |
| uq_sessions_company_user_open | company_id, user_id WHERE open | 打卡狀態查詢 | OK |
| idx_punches_company_time | company_id, punch_time | Break punch 範圍查詢 | OK |
| （缺失） | punch_out_time | 若以下班時間過濾 | 無索引，全表掃描 |

### 4.5 Schema 風險彙總

| 項目 | 狀態 | 風險等級 |
|------|------|----------|
| TIMESTAMPTZ 一致性（attendance 核心表） | 正確 | 無 |
| session_date 欄位 | 不存在 | P1 |
| duration_minutes canonical 隔離 | 安全 | 無 |
| punch_out_time 無索引 | 無索引 | P1（若未來使用） |
| start_date/end_date schema vs impl | 不一致 | P2 |

---

## 5. 前端時間處理

### 5.1 dayjs 全域設定

frontend/src/main.js:8-15 設定：
  dayjs.extend(utc)
  dayjs.extend(timezone)
  dayjs.tz.setDefault('Asia/Taipei')  // 全域預設時區

全域設定正確，所有元件均可繼承此設定。

### 5.2 各元件時間顯示安全性

| 檔案 | 使用方式 | 風險評估 |
|------|---------|----------|
| stores/attendance.js | dayjs(ts).tz(TZ).format('HH:mm') | OK：明確指定 Asia/Taipei |
| TodayStatusSection.vue | dayjs(props.punchIn).tz(TZ).format('HH:mm') | OK |
| RecentPunchLogsSection.vue | dayjs(timestamp).tz(TZ).format('YYYY-MM-DD HH:mm:ss') | OK |
| OutLogsSection.vue | dayjs(timestamp).tz(TZ).format('HH:mm') | OK |
| Home.vue | dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss') | P2：未使用 .tz(TZ)，依賴瀏覽器本地時區 |

Home.vue 風險說明：dayjs(timestamp).format() 若無 .tz() 指定，會使用瀏覽器本地時區。
對非 Asia/Taipei 時區的使用者，時間顯示錯誤。

### 5.3 duration_minutes 前端處理

- 前端完全不計算工時。
- stores/attendance.js:493：duration_minutes: session.duration_minutes（只傳遞 backend canonical 值）
- 無任何 JS 工時計算邏輯。符合 SA v2.1 §30 Report Consistency Rule。

### 5.4 new Date().toISOString() 用法

| 檔案 | 行號 | 用法 | 風險評估 |
|------|------|------|----------|
| stores/attendance.js | 359 | captured_at: new Date().toISOString() | OK：GPS 時間戳，UTC Z suffix，符合 API 規範 |
| composables/useLocation.js | 159 | 同上 | OK |
| utils/locationAdapter.js | 80 | 同上 | OK |

### 5.5 前端時間處理風險彙總

| 項目 | 狀態 | 風險 |
|------|------|------|
| 全域 dayjs 時區設定 | 正確 | 無 |
| 主要元件 .tz(TZ) 使用 | 正確 | 無 |
| Home.vue 時間格式化 | 未指定 .tz() | P2 |
| duration 重新計算 | 無 | 無 |
| GPS captured_at toISOString | 正確 | 無 |

---

## 6. 文件 vs 程式碼一致性

### 6.1 時區儲存規則

| 規範來源 | 規則 | 程式碼實際 | 符合？ |
|---------|------|-----------|--------|
| SA v2.1 §30 | 所有 datetime 欄位儲存 UTC-aware datetime | DateTime(timezone=True) = TIMESTAMPTZ | OK |
| SA v2.1 §30 | API response 以 UTC 回傳，Z suffix | backend 回傳 UTC datetime | OK |
| API DOC v2.1 | API request 必須含 timezone offset | schema 無 naive datetime 拒絕 validator | P2 |

### 6.2 業務日期規則

| 規範來源 | 規則 | 程式碼實際 | 符合？ |
|---------|------|-----------|--------|
| SA v2.1 §29.2 | session 所屬日期 = punch_in_time 的 Asia/Taipei 日期 | policy_engine 使用 punch_in_time.date()（UTC） | 不符合 |
| SA v2.1 §29.2 | 跨日 session 歸屬 punch_in 日期 | duration 計算正確，遲到/早退判斷使用 UTC 日期 | 部分不符 |
| SA v2.1 §30 | 今天/本週/本月以 Asia/Taipei 午夜為邊界 | 未見 TZ_TAIPEI 邊界計算於 production 端點 | P1 |

### 6.3 Reporting 規則

| 規範來源 | 規則 | 程式碼實際 | 符合？ |
|---------|------|-----------|--------|
| SA v2.1 §30 | 報表工時 = attendance_sessions.duration_minutes | frontend 只讀取此欄位 | OK |
| SA v2.1 §28.2 | raw_duration = punch_out_time - punch_in_time | api.py 計算方式符合 | OK |
| SA v2.1 §28.3 | 前端不得自行計算 break_duration | 前端無此計算 | OK |
| WP-11-06 INDEX SAFETY | WHERE 禁用 DATE()/EXTRACT() 函數包裹 | 目前無此模式 | OK |

### 6.4 API 文件 vs Schema 不一致

| 項目 | 文件定義 | 程式碼實際 | 差距 |
|------|---------|-----------|------|
| AttendanceHistoryRequest.start_date | 日期範圍過濾 | Schema 定義但 API + repo 均未實作 | P1 |
| AttendanceHistoryRequest.end_date | 同上 | 同上 | P1 |
| status 允許值 | model comment 列出 6 種狀態 | DB CHECK constraint 只允許 open/closed | P1 |

status 不一致說明：
AttendanceSession.status 的 column comment 列出了 6 種狀態（open/closed/pending/approved/rejected/missing_punch_out），
但 __table_args__ 中的 CHECK constraint 僅允許 open 和 closed。
若未來要實作 approval workflow，必須先透過 migration 擴展 CHECK constraint
（006_expand_session_status.py 已存在，需確認是否已 apply），
否則寫入新狀態值會觸發 DB CHECK 違反，runtime error。

---

## 7. 風險彙總

### P0 — 架構或資料完整性風險

**目前無 P0 等級風險。**

attendance 核心資料（TIMESTAMPTZ 欄位型別、duration_minutes 隔離、tenant isolation）架構健全，無立即性資料損毀風險。

---

### P1 — 邏輯不一致或未來 Bug 風險

| ID | 位置 | 問題描述 | 影響範圍 |
|----|------|---------|----------|
| P1-01 | policy_engine.py:430,465,637,638 | .replace(tzinfo=punch_in_time.tzinfo) 用於組合 work_start/end_time。若 punch_in_time 為 UTC，考勤政策基準時間偏移 8 小時 | 遲到/早退/overtime 計算全面錯誤 |
| P1-02 | policy_engine.py:424,459,627,631 | punch_in_time.date() 取 UTC 日期而非 Asia/Taipei 日期，Taipei 00:00~07:59 打卡的 session 判斷基準日期偏差 1 天 | 遲到/早退判斷錯誤 |
| P1-03 | policy_engine.py:57-58 | datetime.today() 在 WorkWindow.duration_minutes() 使用 naive local datetime | 若 server 時區非 UTC+8，窗口時長計算錯誤 |
| P1-04 | schemas.py:158-159 | start_date/end_date 已定義但 API + repo 均未實作 | 未來補實作時容易引入危險查詢模式 |
| P1-05 | attendance_sessions schema | 無 session_date 欄位 | 報表開發時需應用層計算 Taipei 日期，開發者容易犯錯 |
| P1-06 | attendance_sessions schema | 無 punch_out_time 索引 | 若未來用於 WHERE 過濾則全表掃描 |
| P1-07 | models.py status comment vs CHECK constraint | comment 宣稱 6 種 status，CHECK 只允許 2 種 | approval workflow 開發者寫入新狀態值時 runtime error |
| P1-08 | modules/tenants, auth, audit models | 使用 DateTime（無 timezone=True），naive datetime default | 跨模組時間處理不一致，join 查詢可能產生時區混淆 |

---

### P2 — 輕微不一致或文件偏移

| ID | 位置 | 問題描述 |
|----|------|----------|
| P2-01 | frontend/src/views/Home.vue:279,283 | dayjs(timestamp).format() 未使用 .tz(TZ)，依賴瀏覽器本地時區 |
| P2-02 | schemas.py API request | 無 naive datetime 拒絕 validator，無法強制要求 timezone offset |
| P2-03 | tests/test_business_invariant.py, test_model_constraints.py | 大量使用 datetime.utcnow()（naive），測試與 production TIMESTAMPTZ 不一致 |
| P2-04 | core/security/jwt.py:37 | now = datetime.utcnow()（naive），與全系統 UTC-aware 風格不一致 |

---

## 稽核總結

### 整體架構評分

| 面向 | 評分 | 說明 |
|------|------|------|
| Schema 設計 | 良好 | TIMESTAMPTZ 使用正確，duration_minutes 隔離佳，索引完備 |
| 時間來源（production API/repo） | 良好 | repo.py 使用 UTC-aware datetime，無危險時間來源 |
| 政策引擎時間計算 | 有風險 | .replace(tzinfo) 用法錯誤，Asia/Taipei 日期未正確計算（P1-01/P1-02） |
| 報表查詢安全性 | 良好 | 目前無危險查詢，但 WP-11-06 開始前需建立規範 |
| 前端時間處理 | 良好 | 主要元件正確使用 .tz(TZ)，Home.vue 有一處 P2 |
| 文件一致性 | 部分不符 | policy_engine 實作與 SA v2.1 §29.2 規範有差距 |

### 最高優先修正項目

1. P1-01 / P1-02（policy_engine.py）：所有 .replace(tzinfo=...) 應改為先取
   punch_in_time.astimezone(TZ_TAIPEI).date() 作為業務日期，
   再組合 work_start/end_time 並標記 Asia/Taipei 時區。

2. P1-03（policy_engine.py:57-58）：WorkWindow.duration_minutes() 中的
   datetime.today() 應改為時區無關的計算（直接用 timedelta 計算兩個 time 物件的差距）。

3. P1-04（schemas.py）：AttendanceHistoryRequest.start_date/end_date
   要麼實作（使用 UTC boundary 模式），要麼從 schema 移除。

4. P1-07（models.py）：確認 006_expand_session_status.py migration 是否已 apply，
   或將 CHECK constraint 與 model comment 同步。

### 進入 WP-11-06 (Reporting) 前的必要前置條件

- 確立 session_date 欄位決策（新增 migration 或維持應用層計算）。
- 建立 Reporting Query 規範：明確禁止 DATE()/EXTRACT() 函數包裹、
  禁止 punch_out_time 作為報表過濾欄位。
- 修正 policy_engine.py 的 Asia/Taipei 日期計算（P1-01/P1-02）。

---

*Report generated: 2026-03-13*
*Audit type: SCAN ONLY — no code modifications made*
