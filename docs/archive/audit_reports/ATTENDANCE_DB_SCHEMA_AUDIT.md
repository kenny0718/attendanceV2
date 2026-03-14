# Attendance DB Schema Audit

**稽核日期:** 2026-03-13
**類型:** READ-ONLY 稽核，無任何 schema/code 修改
**資料庫:** PostgreSQL @ 127.0.0.1:5432 / attendance_db
**連線來源:** backend/app/core/config.py DATABASE_URL

---

## Table Structure

**資料表:** `public.attendance_sessions`

| ordinal | column_name | data_type | is_nullable | column_default |
|---------|-------------|-----------|-------------|----------------|
| 1 | id | uuid | NO | gen_random_uuid() |
| 2 | company_id | character varying | NO | (none) |
| 3 | user_id | uuid | NO | (none) |
| 4 | punch_in_time | timestamp with time zone | NO | (none) |
| 5 | punch_out_time | timestamp with time zone | YES | (none) |
| 6 | status | character varying | NO | open |
| 7 | duration_minutes | integer | YES | (none) |
| 8 | policy_id | uuid | YES | (none) |
| 9 | notes | text | YES | (none) |
| 10 | created_at | timestamp with time zone | NO | now() |
| 11 | updated_at | timestamp with time zone | NO | now() |

**共 11 個欄位。**

---

## Indexes

**資料表:** `public.attendance_sessions` (共 7 個 index)

| indexname | type | columns | condition |
|-----------|------|---------|-----------|
| attendance_sessions_pkey | UNIQUE BTREE | id | (none) |
| idx_sessions_company_id | BTREE | company_id | (none) |
| idx_sessions_company_punch_in | BTREE | company_id, punch_in_time | (none) |
| idx_sessions_company_user | BTREE | company_id, user_id | (none) |
| idx_sessions_status_open | BTREE | status | WHERE status = 'open' |
| idx_sessions_user_id | BTREE | user_id | (none) |
| uq_sessions_company_user_open | UNIQUE BTREE | company_id, user_id | WHERE status = 'open' |

**完整 indexdef:**

    attendance_sessions_pkey:
      CREATE UNIQUE INDEX attendance_sessions_pkey
      ON public.attendance_sessions USING btree (id)

    idx_sessions_company_id:
      CREATE INDEX idx_sessions_company_id
      ON public.attendance_sessions USING btree (company_id)

    idx_sessions_company_punch_in:
      CREATE INDEX idx_sessions_company_punch_in
      ON public.attendance_sessions USING btree (company_id, punch_in_time)

    idx_sessions_company_user:
      CREATE INDEX idx_sessions_company_user
      ON public.attendance_sessions USING btree (company_id, user_id)

    idx_sessions_status_open:
      CREATE INDEX idx_sessions_status_open
      ON public.attendance_sessions USING btree (status)
      WHERE ((status)::text = 'open'::text)

    idx_sessions_user_id:
      CREATE INDEX idx_sessions_user_id
      ON public.attendance_sessions USING btree (user_id)

    uq_sessions_company_user_open:
      CREATE UNIQUE INDEX uq_sessions_company_user_open
      ON public.attendance_sessions USING btree (company_id, user_id)
      WHERE ((status)::text = 'open'::text)

---

## Constraints

| conname | type | definition |
|---------|------|------------|
| attendance_sessions_pkey | PRIMARY KEY | PRIMARY KEY (id) |
| ck_sessions_status | CHECK | CHECK (status IN ('open','closed','pending','approved','rejected','missing_punch_out')) |
| attendance_sessions_company_id_fkey | FOREIGN KEY | FOREIGN KEY (company_id) REFERENCES tenants(id) ON DELETE CASCADE |
| attendance_sessions_user_id_fkey | FOREIGN KEY | FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE |
| attendance_sessions_policy_id_fkey | FOREIGN KEY | FOREIGN KEY (policy_id) REFERENCES attendance_policies(id) ON DELETE SET NULL |

**完整 CHECK constraint:**

    ck_sessions_status:
      CHECK (((status)::text = ANY ((
        ARRAY[
          'open'::character varying,
          'closed'::character varying,
          'pending'::character varying,
          'approved'::character varying,
          'rejected'::character varying,
          'missing_punch_out'::character varying
        ])::text[]
      )))

---

## Time Model Observations

### 1. Timestamp 欄位均為 TIMESTAMPTZ

- punch_in_time: `timestamp with time zone` NOT NULL
- punch_out_time: `timestamp with time zone` NULL (open session 時為 NULL)
- created_at: `timestamp with time zone` NOT NULL, default now()
- updated_at: `timestamp with time zone` NOT NULL, default now()

所有時間欄位均為 timezone-aware (TIMESTAMPTZ)，與 Phase 3 guardrails 一致。

### 2. punch_in_time 複合 Index

idx_sessions_company_punch_in (company_id, punch_in_time) 存在，
支援 WP-11-06 reporting 按公司+時間範圍查詢。
punch_in_time 為 leading column 之一，符合 Phase 2 session ownership 規則
(以 punch_in_time 為歸屬基準)。

### 3. ck_sessions_status CHECK constraint 實際狀態

DB 實際 CHECK constraint 包含 6 種狀態:
  open, closed, pending, approved, rejected, missing_punch_out

此與 Phase 3 Fix-A 的 models.py comment 修正有差異:
- Fix-A 將 models.py column comment 修正為 (open/closed)，
  理由是當時 audit report 認為 CHECK 只有 open/closed。
- 但 DB 實際 CHECK constraint 已包含全部 6 種狀態。
- 結論: DB schema 超前於 models.py 的文件描述。
  models.py comment 需再次更新，以反映 DB 實際的 6 種狀態。
  (見 Observation 3 行動建議)

### 4. Partial Unique Index (business rule enforcement)

uq_sessions_company_user_open 確保每個 (company_id, user_id) 組合
最多只有一筆 status=open 的 session，DB 層面強制執行單一進行中打卡規則。

### 5. Open session 查詢最佳化

idx_sessions_status_open (partial index, WHERE status=open) 存在，
查詢進行中 session 時效率高，不需全表掃描。

### 6. duration_minutes 為 nullable

duration_minutes 允許 NULL，對應 open session (尚未 punch_out) 的情況。
Closed session 應有非 NULL 值。reporting 查詢需 WHERE status=closed 或 IS NOT NULL。

---

## Action Required (Fix-A Correction)

Phase 3 Fix-A 將 models.py comment 改為 (open/closed)，
但 DB 實際 CHECK constraint 包含 6 種狀態。

需要再次更新 models.py 行 95 的 comment，使其與 DB 實際一致:

    # 建議修正:
    comment="Session 狀態 (open/closed/pending/approved/rejected/missing_punch_out)
             DB ck_sessions_status CHECK constraint 已包含全部 6 種狀態"

此為 comment-only 修正，不影響任何 schema 或行為。

---

## Summary

| 項目 | 結果 |
|------|------|
| 資料表 | attendance_sessions |
| 欄位數 | 11 |
| Timestamp 欄位時區 | 全部 TIMESTAMPTZ (符合 guardrails) |
| Index 數 | 7 (含 2 個 partial index) |
| punch_in_time index | 存在 (compound: company_id + punch_in_time) |
| Unique open session 保護 | 存在 (uq_sessions_company_user_open) |
| CHECK constraint 實際狀態 | 6 種狀態 (open/closed/pending/approved/rejected/missing_punch_out) |
| models.py comment 與 DB 一致性 | 不一致，需 comment 修正 (見 Action Required) |
