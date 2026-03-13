# WP-11-06 Reporting Query Safety Check Report

**檢查日期：** 2026-03-13  
**檢查目的：** 驗證報表查詢是否使用 `session_date` 而非 `punch_out_time`  
**檢查範圍：** `backend/app/modules/attendance/` 所有 Python 檔案

---

## 執行摘要

✅ **結論：系統目前安全 — 未發現使用 `punch_out_time` 進行報表查詢的情況**

**關鍵發現：**
1. ❌ **`session_date` 欄位不存在** — 資料庫 schema 和 model 中均未定義此欄位
2. ✅ **無危險查詢** — 未發現 `punch_out_time BETWEEN` 或 `DATE(punch_out_time)` 的使用
3. ⚠️ **報表功能未實作** — WP-11-06 (Reporting v1) 尚未開始開發

---

## 詳細檢查結果

### 1. 搜尋危險模式

#### 1.1 `punch_out_time BETWEEN` 查詢
```bash
grep -r "punch_out_time.*BETWEEN" backend/app/modules/attendance --include="*.py"
```
**結果：** ✅ 未發現

#### 1.2 `DATE(punch_out_time)` 查詢
```bash
grep -r "DATE(punch_out_time)" backend/app/modules/attendance --include="*.py"
```
**結果：** ✅ 未發現

#### 1.3 `session_date` 欄位使用
```bash
grep -r "session_date" backend/app/modules/attendance --include="*.py"
grep -r "session_date" backend/alembic/versions --include="*.py"
```
**結果：** ❌ 欄位不存在於任何地方

---

### 2. 資料庫 Schema 驗證

#### 2.1 AttendanceSession Model 欄位清單

**檔案：** `backend/app/modules/attendance/models.py`

```python
class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"
    
    # 欄位清單
    id                  # UUID (PK)
    company_id          # String(255) - Tenant Isolation
    user_id             # UUID
    punch_in_time       # DateTime(timezone=True) ✅
    punch_out_time      # DateTime(timezone=True) - nullable
    status              # String(20) - open/closed
    duration_minutes    # Integer - nullable
    policy_id           # UUID - nullable
    notes               # Text - nullable
    created_at          # DateTime(timezone=True)
    updated_at          # DateTime(timezone=True)
```

**確認：** ❌ **無 `session_date` 或 `work_date` 欄位**

#### 2.2 Migration 驗證

**檔案：** `backend/alembic/versions/001b_create_attendance_domain_v2_fixed.py`

```python
op.create_table(
    'attendance_sessions',
    sa.Column('id', UUID(as_uuid=True), ...),
    sa.Column('company_id', sa.String(255), ...),
    sa.Column('user_id', UUID(as_uuid=True), ...),
    sa.Column('punch_in_time', sa.DateTime(timezone=True), ...),
    sa.Column('punch_out_time', sa.DateTime(timezone=True), nullable=True, ...),
    sa.Column('status', sa.String(20), ...),
    sa.Column('duration_minutes', sa.Integer(), nullable=True, ...),
    # ... 其他欄位
)
```

**確認：** ❌ **Migration 中也無 `session_date` 欄位**

---

### 3. 現有查詢分析

#### 3.1 Repository 層查詢 (`repo.py`)

**所有涉及日期過濾的查詢：**

| 方法 | 過濾欄位 | 查詢類型 | 安全性 |
|------|----------|----------|--------|
| `get_open_session()` | `status = 'open'` | 狀態查詢 | ✅ 安全 |
| `get_sessions()` | `company_id`, `user_id`, `status` | 分頁查詢 | ✅ 安全 |
| `count_sessions()` | `company_id`, `user_id`, `status` | 計數查詢 | ✅ 安全 |
| `get_recent_checkpoint()` | `punch_time >= cutoff_time` | 時間範圍 | ✅ 使用 `punch_time`（checkpoint 表） |

**排序欄位：**
- `get_sessions()`: `ORDER BY punch_in_time DESC` ✅ 使用 `punch_in_time`

#### 3.2 API 層查詢 (`api.py`)

**唯一的日期範圍查詢：**

```python
# GET /api/v1/attendance/break-punches
# 檔案：api.py 第 283-292 行
today = date.today()
start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
end_of_day = start_of_day + timedelta(days=1)

punches = db.query(AttendancePunch).filter(and_(
    AttendancePunch.company_id == company_id,
    AttendancePunch.user_id == user_uuid,
    AttendancePunch.punch_type.in_(["break_start", "break_end"]),
    AttendancePunch.punch_time >= start_of_day,  # ✅ 使用 punch_time
    AttendancePunch.punch_time < end_of_day      # ✅ 使用 punch_time
))
```

**分析：** ✅ 此查詢使用 `AttendancePunch.punch_time`（打卡事件時間），而非 `AttendanceSession.punch_out_time`

#### 3.3 History API 分析

**端點：** `GET /api/v1/attendance/history`  
**檔案：** `api.py` 第 184-203 行

```python
@router_v1.get("/history", response_model=AttendanceHistoryResponse)
async def get_attendance_history(
    limit: int = 50, 
    offset: int = 0, 
    status: Optional[str] = None,
    # ⚠️ 注意：start_date 和 end_date 參數未實作
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db)
):
    # 實際查詢
    sessions = repo.get_sessions(
        company_id=company_id, 
        user_id=user_uuid,
        limit=limit, 
        offset=offset, 
        status=status
        # ⚠️ 未傳遞 start_date/end_date
    )
```

**發現：**
- ⚠️ `AttendanceHistoryRequest` schema 定義了 `start_date` 和 `end_date` 參數
- ❌ 但 API endpoint 和 repository 方法均**未實作**這些參數
- ✅ 目前只使用 `status` 過濾，無日期範圍查詢

---

### 4. 所有查詢位置清單

| 檔案 | 方法/端點 | 查詢類型 | 使用欄位 | 安全性 |
|------|-----------|----------|----------|--------|
| `repo.py:77` | `get_open_session()` | 狀態查詢 | `status = 'open'` | ✅ 安全 |
| `repo.py:150` | `get_sessions()` | 分頁查詢 | `company_id`, `user_id`, `status` | ✅ 安全 |
| `repo.py:163` | 排序 | ORDER BY | `punch_in_time DESC` | ✅ 安全 |
| `repo.py:187` | `count_sessions()` | 計數 | `company_id`, `user_id`, `status` | ✅ 安全 |
| `repo.py:404` | `get_recent_checkpoint()` | 時間範圍 | `punch_time >= cutoff_time` | ✅ 安全（checkpoint 表） |
| `api.py:184` | `GET /history` | 分頁查詢 | 呼叫 `get_sessions()` | ✅ 安全 |
| `api.py:283` | `GET /break-punches` | 日期範圍 | `punch_time BETWEEN` | ✅ 安全（punch 表） |

**總計：** 7 個查詢位置，**全部安全** ✅

---

## 5. WP-11-06 狀態檢查

### 5.1 開發狀態

**根據 `docs/NEXT_WP_TICKET.md` 和 `docs/GATE_PROGRESS_TRACKER.md`：**

| WP | 名稱 | 狀態 |
|----|------|------|
| WP-11-06 | Attendance Reporting v1 | ⏳ **NOT_STARTED** |

**原因：**
- 系統目前處於「基線修正優先」模式
- 優先處理 Auth 遷移（WP-C1-02, WP-C1-03）
- 優先處理回歸測試（WP-C1-04）
- 報表功能延後至 Phase 2

### 5.2 計劃中的報表功能

**根據 `docs/ATTENDANCE_DEVELOPMENT_MASTER_FLOW.md`：**

```
WP-11-06 計劃功能：
- 員工出勤記錄查詢（GET /api/v1/attendance/sessions）
- 公司出勤統計報表（GET /api/v1/attendance/reports/company-summary）
- 個人出勤統計（GET /api/v1/attendance/reports/user-summary）
- CSV 匯出功能（可選）
```

**狀態：** ❌ **以上端點均未實作**

---

## 6. 風險評估

### 6.1 當前風險

| 風險項目 | 風險等級 | 說明 |
|----------|----------|------|
| 使用 `punch_out_time` 進行報表查詢 | 🟢 **無風險** | 未發現此類查詢 |
| 使用 `DATE(punch_out_time)` | 🟢 **無風險** | 未發現此類查詢 |
| `session_date` 欄位缺失 | 🟡 **中風險** | 未來實作報表時需注意 |

### 6.2 未來實作建議

當 WP-11-06 開始實作時，**必須遵循以下原則：**

#### ❌ 錯誤做法（不安全）
```python
# 錯誤 1：使用 punch_out_time 進行日期範圍查詢
sessions = db.query(AttendanceSession).filter(
    AttendanceSession.punch_out_time.between(start_date, end_date)  # ❌ 錯誤
)

# 錯誤 2：使用 DATE(punch_out_time)
sessions = db.query(AttendanceSession).filter(
    func.date(AttendanceSession.punch_out_time) == target_date  # ❌ 錯誤
)
```

**問題：**
- `punch_out_time` 可能為 NULL（open session）
- 跨午夜班次會被錯誤分類到下班日期

#### ✅ 正確做法（安全）

**選項 1：使用 `punch_in_time`（推薦）**
```python
# 使用 punch_in_time 作為 session 歸屬日期
sessions = db.query(AttendanceSession).filter(
    AttendanceSession.punch_in_time >= start_of_day,
    AttendanceSession.punch_in_time < end_of_day
)
```

**選項 2：新增 `session_date` 欄位**
```python
# 1. 新增 migration
op.add_column('attendance_sessions', 
    sa.Column('session_date', sa.Date(), nullable=False,
              comment='Session 歸屬日期 (punch_in_time.date())'))

# 2. 在 create_session() 時設定
session.session_date = punch_in_time.date()

# 3. 報表查詢使用 session_date
sessions = db.query(AttendanceSession).filter(
    AttendanceSession.session_date == target_date  # ✅ 安全
)
```

---

## 7. 結論與建議

### 7.1 檢查結論

✅ **系統目前安全**
- 未發現使用 `punch_out_time BETWEEN` 的查詢
- 未發現使用 `DATE(punch_out_time)` 的查詢
- 現有查詢均使用安全的欄位（`punch_in_time`, `punch_time`, `status`）

### 7.2 發現的問題

1. ❌ **`session_date` 欄位不存在** — 需在 WP-11-06 實作前決定是否新增
2. ⚠️ **`AttendanceHistoryRequest` 的 `start_date`/`end_date` 參數未實作** — schema 定義與實作不一致
3. ⏳ **WP-11-06 尚未開始** — 報表功能完全未實作

### 7.3 行動建議

#### 立即行動（P0）
- ✅ **無需立即行動** — 系統目前無安全風險

#### WP-11-06 實作前（P1）
1. **決定日期欄位策略：**
   - 選項 A：使用 `punch_in_time` 作為 session 歸屬日期（簡單）
   - 選項 B：新增 `session_date` 欄位（更明確，推薦）

2. **建立報表查詢規範文件：**
   - 明確禁止使用 `punch_out_time` 進行日期過濾
   - 提供標準查詢範例
   - 加入 code review checklist

3. **修正 schema 不一致：**
   - 移除 `AttendanceHistoryRequest` 中未實作的 `start_date`/`end_date`
   - 或實作這些參數（使用安全的查詢方式）

#### 文件更新（P2）
- 建立 `docs/WP-11-06_REPORTING_QUERY_PLAN.md`（目前不存在）
- 在 SA_MODULE_SPEC 中加入報表查詢安全規範

---

## 8. 附錄：檢查指令清單

```bash
# 1. 搜尋 punch_out_time BETWEEN
grep -r "punch_out_time.*BETWEEN" backend/app/modules/attendance --include="*.py"

# 2. 搜尋 DATE(punch_out_time)
grep -r "DATE(punch_out_time)" backend/app/modules/attendance --include="*.py"

# 3. 搜尋 session_date
grep -r "session_date" backend/app/modules/attendance --include="*.py"
grep -r "session_date" backend/alembic/versions --include="*.py"

# 4. 列出所有查詢
grep -n "\.filter\|\.query" backend/app/modules/attendance/repo.py

# 5. 檢查 model 定義
cat backend/app/modules/attendance/models.py | grep -A50 "class AttendanceSession"

# 6. 檢查 migration
cat backend/alembic/versions/001b_create_attendance_domain_v2_fixed.py | grep -A50 "attendance_sessions"
```

---

**檢查完成時間：** 2026-03-13  
**檢查人員：** AI Assistant  
**下次檢查建議：** WP-11-06 實作前
