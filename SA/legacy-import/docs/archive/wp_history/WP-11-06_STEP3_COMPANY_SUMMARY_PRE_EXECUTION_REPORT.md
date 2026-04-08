# WP-11-06 Step 3 Company Summary Pre-Execution Report

**建立日期：** 2026-03-13  
**任務：** WP-11-06 Reporting v1 Step 3 Pre-Execution  
**類型：** PRE-EXECUTION REPORT (Documentation Only — No Code Changes)  
**狀態：** ACTIVE  
**覆蓋範圍：** GET /api/v1/attendance/reports/company-summary ONLY  

---

## 1. Step 1 / Step 2 Current State Verification

### 1.1 既有 Endpoint 狀態

| 項目 | 狀態 | 說明 |
|------|------|------|
| GET /api/v1/attendance/sessions | ✅ 已實作 | router_v1 已註冊；16/16 tests passed |
| GET /api/v1/attendance/reports/user-summary | ✅ 已實作 | router_v1 已註冊；13/13 tests passed |
| 兩 endpoint 合計驗證 | ✅ 29 passed | 2026-03-13 實測結果 |

### 1.2 ReportingRepository 可複用性

| 項目 | 狀態 | 說明 |
|------|------|------|
| ReportingRepository class | ✅ 已實作 | repo.py，3 個方法均可複用 |
| get_sessions_for_reporting() | ✅ 可複用 | user_id Optional，可接受 None 查全公司 |
| count_sessions_for_reporting() | ✅ 可複用 | 同上 |
| get_user_summary_sessions() | ✅ Step 2 新增 | user_id 必填；Step 3 新增 get_company_summary_sessions() |
| get_reporting_repository() | ✅ Factory | 可直接複用 |

### 1.3 Helper 可複用性

| 項目 | 狀態 |
|------|------|
| _normalize_to_utc() | ✅ api.py 內定義，Step 3 直接複用 |

### 1.4 Index 支援評估

| 索引 | 欄位 | company-summary 查詢命中 |
|------|------|---------------------------|
| idx_sessions_company_punch_in | (company_id, punch_in_time) | ✅ 命中（主要查詢索引）|
| idx_sessions_company_user | (company_id, user_id) | 不適用（company-summary 不按 user 過濾）|

company-summary 查詢模式：
```
WHERE company_id = :cid
  AND punch_in_time >= :start_utc   -- 使用 idx_sessions_company_punch_in
  AND punch_in_time <  :end_utc
```
此模式與 Step 1 / Step 2 相同，確保 Index Range Scan。

### 1.5 Schema / Migration 需求

| 項目 | 評估 |
|------|------|
| 需要新增資料庫欄位 | ❌ 不需要 |
| 需要 migration 檔案 | ❌ 不需要 |
| 需要修改 models.py | ❌ 不需要 |
| CompanySummaryResponse 為純 Python schema | ✅ 只加 schemas.py |

### 1.6 Tenant Isolation 機制

| 項目 | 狀態 |
|------|------|
| company_id 來源 | Header X-Company-ID（與 Step 1 / 2 相同）|
| 所有 repo 查詢強制 WHERE company_id = ? | ✅ 已在 ReportingRepository 全面實施 |
| company A 無法查 company B | ✅ 已由 Step 2 USR-05 驗證機制確認 |

---

## 2. Readiness Verdict: **GO**

### 通過條件

| 條件 | 狀態 |
|------|------|
| Step 1 測試全部通過（16/16）| ✅ PASS |
| Step 2 測試全部通過（13/13）| ✅ PASS |
| ReportingRepository 可直接擴充 | ✅ CONFIRMED |
| _normalize_to_utc() 可複用 | ✅ CONFIRMED |
| 現有索引足夠支撐 company-summary 查詢 | ✅ CONFIRMED |
| 無 schema migration 需求 | ✅ CONFIRMED |
| Step 1 / Step 2 endpoints 不需修改 | ✅ CONFIRMED |

### 前提條件（實作前必須遵守）

1. company-summary 所有 filter 使用 `punch_in_time`，**不使用** `punch_out_time`
2. `total_work_minutes` 必須讀取 `duration_minutes` 欄位（canonical source，SA v2.1 §28）
3. `duration_minutes` 為 NULL 的 session（open session）不計入工時：`or 0`
4. `start_date` / `end_date` 為 naive datetime 時回傳 422
5. 聚合在 **Python 應用層**執行（不在 SQL 端 SUM / GROUP BY）
6. 不修改 models.py 或任何 migration 檔案
7. 不修改 Step 1 / Step 2 endpoints
8. 不實作 CSV export
9. 不實作 per-department analytics

---

## 3. Endpoint 範圍定義

```
GET /api/v1/attendance/reports/company-summary
```

此步驟明確**不**包含：
- per-user breakdown（各員工詳細）
- per-department analytics
- CSV export
- dashboard KPI（趨勢、比較）
- 任何 schema migration
- Step 1 / Step 2 endpoints 修改

---

## 4. Query Parameters

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| start_date | datetime (ISO 8601 with tz) | 選填 | punch_in_time 起始過濾；必須為 timezone-aware |
| end_date | datetime (ISO 8601 with tz) | 選填 | punch_in_time 結束過濾（exclusive）；必須為 timezone-aware |

start_date / end_date 規則：
- 型別保持 Optional[datetime]（含 tzinfo）
- naive datetime 必須被 endpoint 攔截，回傳 422
- API 層呼叫 `_normalize_to_utc()`，再傳入 repo

---

## 5. Response Fields 定義

| 欄位 | 類型 | 計算規則 |
|------|------|----------|
| company_id | str | 來自 Header / JWT |
| total_users_with_sessions | int | Python: `len(set(s.user_id for s in sessions))` |
| total_sessions | int | `len(sessions)` |
| open_sessions | int | `sum(1 for s in sessions if s.status == "open")` |
| closed_sessions | int | `sum(1 for s in sessions if s.status == "closed")` |
| total_work_minutes | int | `sum(s.duration_minutes or 0 for s in sessions)` |
| average_minutes_per_session | Optional[float] | `total_work_minutes / closed_sessions` if closed > 0 else None |
| average_minutes_per_user | Optional[float] | `total_work_minutes / total_users_with_sessions` if users > 0 else None |
| first_session_time | Optional[datetime] | `min(s.punch_in_time for s in sessions)` if sessions else None |
| last_session_time | Optional[datetime] | `max(s.punch_in_time for s in sessions)` if sessions else None |

禁止計算方式：
```python
# 禁止重算工時
work_min = (s.punch_out_time - s.punch_in_time).total_seconds() / 60

# 禁止 SQL 端聚合
db.query(func.sum(AttendanceSession.duration_minutes))...

# 禁止 SQL 端 COUNT DISTINCT
db.query(func.count(func.distinct(AttendanceSession.user_id)))...
```

---

## 6. Aggregation 策略

**決策：Python 應用層聚合（選項 A）**

理由：
1. 與 Step 1 / Step 2 保持一致的架構模式
2. 不引入 SQL 端 `func.sum()` / `func.count(distinct())` — 避免測試難度增加
3. `idx_sessions_company_punch_in` 已能高效取回全公司 sessions，Python 端聚合成本可接受
4. 不包裹 indexed column，無索引失效風險
5. 資料量超過 10 萬筆時可評估切換 SQL 聚合（留待未來優化）

詳細計算流程見 WP-11-06_STEP3_COMPANY_SUMMARY_IMPLEMENTATION_PLAN.md §4

---

## 7. Risks

| 風險 | 說明 | 嚴重程度 |
|------|------|----------|
| total_work_minutes 重算工時 | 誤用 punch_out - punch_in 而非 duration_minutes | P1 |
| average 除以零 | closed_sessions == 0 或 total_users == 0 時未處理 | P1 |
| open session 計入工時 | duration_minutes IS NULL 未做 or 0 防禦 | P1 |
| start_date/end_date 時區錯誤 | 未呼叫 _normalize_to_utc() | P1 |
| naive datetime 未攔截 | 允許 naive datetime 進入 DB 查詢 | P1 |
| 查詢全公司無 user_id filter | 必須確保 company_id filter 仍存在（tenant isolation）| P1 |
| total_users_with_sessions SQL 計算 | 誤用 COUNT DISTINCT 包裹索引欄位 | P2 |
| Step 1 / Step 2 被誤修改 | scope 蔓延 | P2 |

---

## 8. Test Plan（設計，不實作）

| Test ID | 案例 | 驗證重點 |
|---------|------|----------|
| CMP-01 | 基本公司 summary | total_sessions, open/closed, total_work_minutes, total_users_with_sessions |
| CMP-02 | start_date/end_date 過濾 | 只計入 punch_in_time 在範圍內的 sessions |
| CMP-03 | 跨日 session 歸屬 | punch_in 3/31 23:50 Taipei 計入 3 月，不計入 4 月 |
| CMP-04 | NULL duration 處理 | open session duration_minutes IS NULL 不影響 total_work_minutes |
| CMP-05 | Tenant Isolation | company A 查不到 company B 的 sessions |
| CMP-06 | 空公司資料集 | 無 session 時回傳全零 summary，不報錯 |
| CMP-07 | Naive datetime 回傳 422 | start_date 無 tzinfo 回傳 422 |

---

*文件完畢。Readiness Verdict: **GO***  
*下一步：依照 