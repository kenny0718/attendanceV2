# session_date Feasibility Analysis

**日期：** 2026-03-13  
**類型：** Analysis Only — No Code Changes

---

## 1. Current State — Schema Check

### attendance_sessions 現有欄位

| Column | Type | Nullable | Note |
|--------|------|----------|------|
| id | UUID | NOT NULL | PK |
| company_id | String(255) | NOT NULL | Tenant Isolation |
| user_id | UUID | NOT NULL | FK users |
| punch_in_time | DateTime(timezone) | NOT NULL | UTC stored |
| punch_out_time | DateTime(timezone) | NULL | NULL = open session |
| status | String(20) | NOT NULL | open/closed |
| duration_minutes | Integer | NULL | computed on close |
| policy_id | UUID | NULL | FK policies |
| notes | Text | NULL | - |
| created_at | DateTime(timezone) | NOT NULL | UTC |
| updated_at | DateTime(timezone) | NOT NULL | UTC |

**結論：`session_date`、`business_day`、`report_date` 均不存在於 schema。**

### 現有索引

| Index | Columns | Type |
|-------|---------|------|
| idx_sessions_company_id | company_id | BTree |
| idx_sessions_user_id | user_id | BTree |
| idx_sessions_company_user | company_id, user_id | BTree |
| idx_sessions_company_punch_in | company_id, punch_in_time | BTree |
| idx_sessions_status_open | status (WHERE open) | Partial |
| uq_sessions_company_user_open | company_id, user_id (WHERE open) | Unique Partial |

---

## 2. Query Complexity — Monthly Report

### 當前方案（WP-11-06_REPORTING_QUERY_PLAN.md）

月報查詢需在應用層進行時區轉換：

```python
# Step 1: 計算 Asia/Taipei 月份邊界
month_start_taipei = datetime(2026, 3, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)
month_end_taipei   = datetime(2026, 4, 1, 0, 0, 0, tzinfo=TZ_TAIPEI)

# Step 2: 轉換為 UTC
month_start_utc = month_start_taipei.astimezone(timezone.utc)  # 2026-02-28 16:00 UTC
month_end_utc   = month_end_taipei.astimezone(timezone.utc)    # 2026-03-31 16:00 UTC

# Step 3: 查詢
SELECT * FROM attendance_sessions
WHERE company_id = ?
  AND punch_in_time >= '2026-02-28 16:00:00+00'
  AND punch_in_time <  '2026-03-31 16:00:00+00'
```

**跨午夜範例驗證：**
```
punch_in  = 2026-03-31 23:00 Taipei = 2026-03-31 15:00 UTC
punch_out = 2026-04-01 02:00 Taipei = 2026-03-31 18:00 UTC

month_end_utc = 2026-03-31 16:00 UTC

查詢條件: punch_in_time < 2026-03-31 16:00 UTC

2026-03-31 15:00 UTC < 2026-03-31 16:00 UTC → TRUE ✅
→ 正確歸屬於 3 月
```

### 複雜度評估

| 操作 | Model A (punch_in_time) | Model B (session_date) |
|------|------------------------|------------------------|
| 月報查詢 | 需計算 UTC 邊界（2 步驟） | 直接 `WHERE session_date BETWEEN` |
| 按日分組 | 應用層 `.astimezone(TZ).date()` | SQL `GROUP BY session_date` |
| 跨午夜正確性 | ✅ 正確（UTC 邊界計算） | ✅ 正確（預計算存入） |
| 實作複雜度 | 中（需封裝輔助函數） | 低（直接查詢） |

---

## 3. Performance Risk — Index Analysis

### 現有索引足夠性

**查詢模式：**
```sql
WHERE company_id = 'X'
  AND punch_in_time >= '2026-02-28 16:00+00'
  AND punch_in_time <  '2026-03-31 16:00+00'
```

**索引命中：** `idx_sessions_company_punch_in (company_id, punch_in_time)`

✅ 此查詢**可以直接命中現有 BTree 索引**，為 Index Range Scan。

**理由：**
- 第一列 `company_id = ?` 為等值過濾，BTree 可精確定位
- 第二列 `punch_in_time BETWEEN` 為範圍過濾，BTree 支援高效範圍掃描
- 不需要 `DATE()` 函數包裝，無 function-based index 問題

### 危險查詢（若使用 DATE 函數）

```sql
-- ❌ 若改為此寫法，索引失效
WHERE company_id = 'X'
  AND DATE(punch_in_time AT TIME ZONE 'Asia/Taipei') BETWEEN '2026-03-01' AND '2026-03-31'
```

**問題：** `DATE(punch_in_time AT TIME ZONE ...)` 對索引列套用函數，PostgreSQL **無法使用 BTree index**，導致 full table scan。

**當前方案（UTC 邊界比較）不使用函數包裝，索引完全有效。**

### 按日分組的性能差異

| 操作 | Model A | Model B |
|------|---------|----------|
| `GROUP BY` 日期 | 需應用層分組（Python defaultdict） | SQL `GROUP BY session_date` |
| 分組查詢效能 | 載入所有 rows 後 Python 處理 | DB 端直接聚合，回傳更少資料 |
| 100 員工 × 22 天 ≈ 2200 rows | 應用層可接受 | SQL 端更高效 |
| 規模化（1000 員工 × 22 天 ≈ 22000 rows） | 應用層壓力大 | SQL 端仍高效 |

---

## 4. Model Comparison

### Model A — 維持現有設計（派生自 punch_in_time）

**優點：**
- ✅ 無需 schema 變更、migration、backfill
- ✅ 無資料冗餘
- ✅ 現有索引足夠支援月報查詢
- ✅ 可立即實作報表
- ✅ Single source of truth（punch_in_time 是唯一來源）

**缺點：**
- ⚠️ 每次查詢需在應用層計算 UTC 邊界
- ⚠️ 按日分組需在 Python 層處理
- ⚠️ SQL 層無法直接 `GROUP BY session_date`
- ⚠️ 規模化後（>10 萬 sessions）應用層分組有壓力

---

### Model B — 新增 session_date 欄位

**定義：**
```
session_date = punch_in_time 的 Asia/Taipei business date
規則：session_date = punch_in_time.astimezone(TZ_TAIPEI).date()
```

**優點：**
- ✅ 查詢語法簡單：`WHERE session_date BETWEEN '2026-03-01' AND '2026-03-31'`
- ✅ SQL 層直接 `GROUP BY session_date`
- ✅ 未來薪資匯出更直觀
- ✅ 月報聚合效能更好（特別是大資料量）
- ✅ 欄位語意明確，降低開發者認知負擔

**缺點：**
- ❌ 需要新 migration（`009_add_session_date.py`）
- ❌ 需要 backfill 現有資料
- ❌ 需要在 `create_session()` 設定欄位
- ❌ 資料冗餘（可從 punch_in_time 派生）
- ❌ 需要 Domain Model 凍結期額外審核

---

## 5. Recommendation

### **OPTION A — 維持現有設計，暫不引入 session_date**

**理由：**

1. **當前系統規模不需要 session_date**
   - 現有索引 `idx_sessions_company_punch_in` 足夠支援月報查詢
   - UTC 邊界查詢為 Index Range Scan，無性能問題
   - 應用層時區轉換已有標準封裝（`get_month_boundaries_utc()`）

2. **WP-C1 基線修正尚未完成**
   - 當前優先處理 Auth 遷移（WP-C1-03）
   - Domain Model 凍結期不應引入新欄位
   - 新 migration 增加基線驗證複雜度

3. **跨午夜場景已正確處理**
   - UTC 邊界比較天然支援跨午夜
   - SA v2.1 §29.3 規則在 Model A 下完全可實現

4. **OPTION B 保留為 Phase 2 優化**
   - 若月報查詢性能不足（>2 秒），再引入 session_date
   - 引入觸發條件：資料量 >10 萬 sessions 或需 SQL 端 GROUP BY

### OPTION B 觸發條件（未來參考）

若以下任一條件成立，應執行 OPTION B：
- 月報 API 響應時間 > 2 秒（測試環境 1000+ sessions）
- 需要複雜的 SQL 端按日聚合報表
- 未來薪資模組需要 session_date 作為 join key
- 資料量超過 10 萬 sessions per company

---

## 6. Summary

| 問題 | 結論 |
|------|------|
| schema 是否已有 session_date？ | ❌ 不存在 |
| 月報查詢需要時區轉換？ | ✅ 需要，但在應用層計算 UTC 邊界即可 |
| 現有索引是否足夠？ | ✅ `idx_sessions_company_punch_in` 足夠（Index Range Scan） |
| DATE() 函數會導致 full scan？ | ✅ 是，應避免使用 |
| 建議方案 | **OPTION A** — 維持現有設計 |
| OPTION B 時機 | 規模化後性能不足時再引入 |

**最終結論：** 當前系統無需引入 `session_date` 欄位即可安全實作月報，OPTION B 保留為未來性能優化選項。

---

**分析完成時間：** 2026-03-13  
**類型：** Analysis Only
