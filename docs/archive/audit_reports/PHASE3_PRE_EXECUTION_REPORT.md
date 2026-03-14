# Phase 3 Pre-Execution Report

**産出日期:** 2026-03-13
**類型:** PRE-EXECUTION REPORT -- 等待確認後才執行修改
**關聯稽核:** ATTENDANCE_SYSTEM_AUDIT_REPORT.md
**範圍:** P1-07 / P1-08 / P2-01 / P2-02 / P2-03 / P2-04

---

## 執行摘要

| 類別 | 數量 |
|------|------|
| 本 Phase 執行修正 | 5 個 |
| 文件紀錄不修改 | 1 個 |
| 延後處理 | 3 個 |
| 修改檔案總數 | 6 個 |

## 1. 本 Phase 執行修正

### Fix-A: P1-07 -- models.py status comment 與 CHECK constraint 不一致

**位置:** backend/app/modules/attendance/models.py 行 95

**現況:**

    column comment: Session 狀態 (open/closed/pending/approved/rejected/missing_punch_out)
    CHECK constraint: status IN (open, closed)  [ck_sessions_status]

**風險:** 開發者讀 comment 誤以為可寫入 pending/approved/rejected/missing_punch_out，
實際寫入時觸發 DB CHECK 違反 (runtime error)。

**修正:** 僅修改 column comment，使其與 CHECK constraint 一致。

    修正後: Session 狀態 (open/closed)。擴充狀態須先執行 migration 更新 CHECK constraint

**影響:** 僅 comment 字串變更，無任何 schema/行為變更。
**風險等級:** 極低 (comment-only change)

---

### Fix-B: P2-04 -- jwt.py datetime.utcnow() naive datetime

**位置:** backend/app/core/security/jwt.py 行 9, 37

**現況:**

    from datetime import datetime, timedelta
    now = datetime.utcnow()  # naive datetime
    payload = {
        iat: int(now.timestamp()),
        exp: int((now + timedelta(seconds=expires_in)).timestamp())
    }

**風險:** datetime.utcnow() 回傳無 tzinfo 的 naive datetime。
timestamp() 在 naive datetime 上依賴 local timezone (非 UTC)，
在非 UTC 伺服器上產生錯誤的 iat/exp 值，JWT 有效期計算錯誤。

**修正:**

    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)  # timezone-aware UTC

**影響:** JWT iat/exp 在任何 server 時區均正確。API contract 不變。
**風險等級:** 低 (修正現有 bug；token 有效期計算更正確)

---

### Fix-C: P2-03 -- test_business_invariant.py datetime.utcnow() (12 處)

**位置:** backend/app/modules/attendance/tests/test_business_invariant.py
**出現次數:** 12 處 (行 71, 101, 126, 157, 186, 220, 252, 270, 295, 323, 356, 382)

**現況:**

    now = datetime.utcnow()  # naive datetime 傳入 TIMESTAMPTZ column

**風險:** naive datetime 傳入 SQLAlchemy TIMESTAMPTZ column，PostgreSQL 行為依賴
server 時區。測試在非 UTC server 上可能給出錯誤結果，與 production code 語義不一致。

**修正:** 全部替換為 datetime.now(timezone.utc)。

**影響:** 測試語義更正確，與 TIMESTAMPTZ column 一致。業務邏輯不變。
**風險等級:** 極低 (測試檔案，無 production impact)

---

### Fix-D: P2-03 -- test_model_constraints.py datetime.utcnow() (15 處)

**位置:** backend/app/modules/attendance/tests/test_model_constraints.py
**出現次數:** 15 處 (行 67, 78, 105, 121, 133, 146, 161, 183, 196, 206, 219, 230, 247, 260, 270)

**現況/風險/修正:** 同 Fix-C。
**風險等級:** 極低 (測試檔案，無 production impact)

---

### Fix-E: P2-01 -- Home.vue formatDateTime / formatTime 未指定時區

**位置:** frontend/src/views/Home.vue 行 279, 283

**現況:**

    const formatDateTime = (timestamp) => {
      return dayjs(timestamp).format(YYYY-MM-DD HH:mm:ss)  // 依賴瀏覽器時區
    }
    const formatTime = (timestamp) => {
      return dayjs(timestamp).format(HH:mm)  // 依賴瀏覽器時區
    }

**風險 (P2):** 非 Asia/Taipei 使用者看到的時間與實際打卡時間不一致。
其他元件 (TodayStatusSection.vue, RecentPunchLogsSection.vue 等) 均使用
dayjs(ts).tz(TZ).format()，此處未統一，行為不一致。

**修正:**

    const TZ = Asia/Taipei
    const formatDateTime = (timestamp) => {
      return dayjs(timestamp).tz(TZ).format(YYYY-MM-DD HH:mm:ss)
    }
    const formatTime = (timestamp) => {
      return dayjs(timestamp).tz(TZ).format(HH:mm)
    }

**影響:** 顯示時間統一為 Asia/Taipei，無 API / 資料變更。
**風險等級:** 極低 (display-only，無業務邏輯)

---

## 2. 文件紀錄 (不修改程式碼)

### Doc-A: P2-02 -- schemas.py 無 naive datetime 拒絕 validator

**位置:** backend/app/modules/attendance/schemas.py

**現況:** AttendanceHistoryRequest.start_date / end_date 為 Optional[datetime]，
無 validator 拒絕 naive datetime (無 tzinfo) 的輸入。

**評估:** start_date / end_date 目前為 placeholder (BOUNDARY_DECISIONS.md P1-04 決策)，
功能尚未實作。在未實作的欄位上加入 validator 為過度工程，且無測試可驗證。

**決策:** 保留為文件紀錄，WP-11-06 實作 start_date/end_date 過濾時同步加入 validator。
**不修改原因:** 符合 Phase 2 決策；避免在未實作功能上加入孤立的 validator。

---

## 3. 延後處理

### Defer-A: P1-08 -- tenants / auth / audit / notifications models naive datetime

**涉及檔案:**
- backend/app/modules/tenants/models.py (3 處 default=datetime.utcnow)
- backend/app/modules/tenants/repo.py (1 處)
- backend/app/modules/auth/models.py (9 處 default=datetime.utcnow)
- backend/app/modules/auth/repo.py (2 處)
- backend/app/modules/audit/models.py (4 處)
- backend/app/modules/audit/repo.py (1 處)
- backend/app/modules/audit/service.py (1 處)
- backend/app/modules/notifications/models.py (1 處)
- backend/app/modules/customer_service/models.py (1 處)

**評估:** 這些模組使用 DateTime (無 timezone=True)，欄位本身就不是 TIMESTAMPTZ。
修改 datetime default 需同步修改 migration (DateTime -> TIMESTAMPTZ)，
超出本 Phase 允許範圍 (不可 create migrations)。

**決策:** 延後至各模組的 architecture alignment WP 中處理。

---

### Defer-B: P1-08 -- audit / backup tests conftest naive datetime

**涉及檔案:**
- backend/app/modules/audit/tests/conftest.py
- backend/app/modules/audit/tests/test_audit_api.py
- backend/app/modules/audit/tests/test_audit_retention.py
- backend/app/modules/backup/tests/conftest.py

**評估:** 這些測試對應的 model 欄位為 DateTime (無時區)，
需與 Defer-A 的 model 修改一起進行。
**決策:** 延後至 Defer-A 一起處理。

---

### Defer-C: backup/exporter.py datetime.utcnow()

**位置:** backend/app/modules/backup/exporter.py 行 53

**現況:** datetime.utcnow().isoformat() + Z 用於 exported_at metadata。
**評估:** 影響範圍限於 backup file metadata，不涉及 DB 寫入。
**決策:** 延後至備份模組 WP 中處理。

---

## 4. 修改檔案清單

| 檔案 | Fix | 變更性質 | 影響 |
|------|-----|---------|------|
| backend/app/modules/attendance/models.py | Fix-A | comment 修改 | 無 schema 變更 |
| backend/app/core/security/jwt.py | Fix-B | import + 1 行替換 | JWT 計算更正確 |
| backend/app/modules/attendance/tests/test_business_invariant.py | Fix-C | 12 處 utcnow 替換 | 無 production impact |
| backend/app/modules/attendance/tests/test_model_constraints.py | Fix-D | 15 處 utcnow 替換 | 無 production impact |
| frontend/src/views/Home.vue | Fix-E | 2 個 format 函數加 .tz(TZ) | display-only |

**審查但不修改的檔案:**

| 檔案 | 原因 |
|------|------|
| backend/app/modules/attendance/schemas.py | P2-02 延後至 WP-11-06 |
| backend/app/modules/tenants/models.py | P1-08 需配合 migration，延後 |
| backend/app/modules/auth/models.py | P1-08 需配合 migration，延後 |
| backend/app/modules/audit/models.py | P1-08 需配合 migration，延後 |
| backend/app/modules/notifications/models.py | P1-08 需配合 migration，延後 |

---

## 5. 風險評估

| Fix | 風險等級 | 說明 |
|-----|---------|------|
| Fix-A models.py comment | 極低 | 僅 Python 字串，無 DB 影響 |
| Fix-B jwt.py utcnow | 低 | 修正現有 bug；timestamp() 行為在 tz-aware datetime 下更可靠 |
| Fix-C test_business_invariant | 極低 | 測試檔案；TIMESTAMPTZ 接受 tz-aware datetime |
| Fix-D test_model_constraints | 極低 | 測試檔案；同上 |
| Fix-E Home.vue .tz() | 極低 | 顯示層；全域 dayjs 已設 Asia/Taipei，.tz() 明確化無副作用 |

**整體評估:** 所有修正均為低風險。不涉及 DB schema 變更、API contract 變更、
業務邏輯變更。最大影響是 Fix-B 使 JWT token 的 iat/exp 更正確。

---

## 6. 驗證計畫 (執行後)

1. 執行 attendance policy engine 測試:
   pytest backend/app/modules/attendance/tests/test_policy_engine.py -v
2. 確認 models.py / jwt.py 無語法錯誤:
   python3 -m py_compile backend/app/modules/attendance/models.py
   python3 -m py_compile backend/app/core/security/jwt.py
3. 確認測試檔案無語法錯誤:
   python3 -m py_compile 兩個測試檔案
4. 人工確認 Home.vue formatDateTime/formatTime 有 .tz(TZ)

---

## 7. 確認後執行

本報告產出完畢。請確認後，Phase 3 修正將依序執行 Fix-A 至 Fix-E。
所有延後項目 (Defer-A/B/C) 不在本次執行範圍內。
