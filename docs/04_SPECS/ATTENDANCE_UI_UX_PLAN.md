# Attendance UI/UX Plan
## 前後端整合規劃文件

**版本**: 1.0  
**建立日期**: 2026-03-05  
**狀態**: ✅ ACTIVE  
**目的**: 定義 Attendance 模組的 UI/UX 流程與後端 API 對應關係

---

## 📋 文件說明

本文件整合自 `docs/UIdoc/` 下的 UI/UX 設計文件，專注於：
- 角色與頁面路由定義
- 每頁需要的資料欄位
- UI route → Backend API mapping
- Session 狀態機定義
- Cross-midnight 跨日規則
- **明確排除 WP-11-06 (Reporting) 功能**

---

## 🎯 系統角色與權限

### 角色定義

| 角色 | 英文名稱 | 權限範圍 | 可訪問頁面 |
|------|---------|---------|-----------|
| 員工 | Employee | 個人資料 | 打卡、個人記錄、個人月曆 |
| 主管 | Manager | 部門資料 | 今日出勤、審核補打卡 |
| HR/Admin | HR/Admin | 公司資料 | 公司統計、員工明細 |
| 系統管理員 | System Admin | 全域 | 所有功能 |

---

## 📱 頁面路由與功能定義

### Employee 員工角色

#### 1. 打卡頁面 `/attendance/punch`

**功能**: 上班/下班/外出/返回打卡

**UI 需要的資料**:
```typescript
interface TodayStatus {
  punch_in: string | null;      // 上班時間 "09:00:15"
  punch_out: string | null;     // 下班時間 "18:30:22"
  break_out: string | null;     // 外出時間
  break_in: string | null;      // 返回時間
  status: 'not_started' | 'working' | 'break' | 'completed';
  elapsed_minutes: number | null; // 已工作分鐘數
}

interface PunchRequest {
  attendance_type: 'IN' | 'OUT' | 'BREAK_OUT' | 'BREAK_IN';
  latitude?: number;
  longitude?: number;
  reason?: string;  // 外部打卡需填寫
}

interface PunchResponse {
  success: boolean;
  message: string;
  timestamp: string;
  is_late?: boolean;
  is_early?: boolean;
}
```

**後端 API 對應**:
- `GET /api/v1/attendance/status` → 獲取今日狀態
- `POST /api/v1/attendance/punch-in` → 上班打卡
- `POST /api/v1/attendance/punch-out` → 下班打卡
- ⚠️ **GAP**: 外出/返回打卡 API 尚未實作

---

#### 2. 個人記錄頁面 `/attendance/sessions`

**功能**: 查詢個人打卡記錄（月份篩選）

**UI 需要的資料**:
```typescript
interface SessionListRequest {
  month: string;  // "YYYY-MM" 格式
  limit?: number;
  offset?: number;
}

interface SessionRecord {
  id: string;
  date: string;              // "2026-03-05"
  punch_in_time: string;     // "09:00:15"
  punch_out_time: string | null;
  work_minutes: number | null;
  status: 'OPEN' | 'APPROVED' | 'PENDING' | 'MISSING_PUNCH_OUT';
  is_late: boolean;
  is_overtime: boolean;
  late_minutes: number;
  overtime_minutes: number;
}

interface SessionListResponse {
  sessions: SessionRecord[];
  total: number;
  month_summary: {
    total_days: number;
    work_days: number;
    late_days: number;
    total_work_hours: number;
  };
}
```

**後端 API 對應**:
- `GET /api/v1/attendance/sessions?month=YYYY-MM` → 查詢月份記錄
- ⚠️ **GAP**: 目前後端只有 `/api/v1/attendance/history`，需要支援 `month` 參數

---

#### 3. 個人月曆頁面 `/attendance/calendar`

**功能**: 月曆視圖顯示出勤狀態

**UI 需要的資料**:
```typescript
interface CalendarRequest {
  month: string;  // "YYYY-MM"
}

interface CalendarDay {
  date: string;              // "2026-03-05"
  status: 'present' | 'absent' | 'late' | 'leave' | 'holiday' | 'weekend';
  punch_in_time: string | null;
  punch_out_time: string | null;
  work_hours: number | null;
  is_late: boolean;
}

interface CalendarResponse {
  month: string;
  days: CalendarDay[];
}
```

**後端 API 對應**:
- ⚠️ **GAP**: 可用 `/api/v1/attendance/sessions?month=YYYY-MM` 聚合，但需前端處理
- 建議: 後端提供 `/api/v1/attendance/calendar?month=YYYY-MM` 專用端點

---

### Manager 主管角色

#### 4. 今日出勤頁面 `/attendance/today`

**功能**: 查看部門今日出勤狀態

**UI 需要的資料**:
```typescript
interface TodayAttendanceRequest {
  department_id?: string;  // 可選，篩選部門
  date?: string;           // 可選，預設今日
}

interface EmployeeAttendance {
  user_id: string;
  user_name: string;
  department: string;
  punch_in_time: string | null;
  punch_out_time: string | null;
  status: 'not_started' | 'working' | 'completed' | 'absent';
  is_late: boolean;
  late_minutes: number;
}

interface TodayAttendanceResponse {
  date: string;
  total_employees: number;
  present_count: number;
  absent_count: number;
  late_count: number;
  employees: EmployeeAttendance[];
}
```

**後端 API 對應**:
- ⚠️ **GAP**: 需要新增 `/api/v1/attendance/today` 端點
- 需要支援 `department_id` 篩選
- 需要 Manager scope 驗證

---

#### 5. 審核頁面 `/attendance/approvals`

**功能**: 審核 PENDING 狀態的補打卡申請

**UI 需要的資料**:
```typescript
interface PendingSessionsRequest {
  status?: 'PENDING';
  limit?: number;
  offset?: number;
}

interface PendingSession {
  session_id: string;
  user_id: string;
  user_name: string;
  date: string;
  punch_in_time: string;
  punch_out_time: string | null;
  reason: string;           // 補打卡原因
  status: 'PENDING';
  created_at: string;
}

interface ApprovalRequest {
  session_id: string;
  action: 'approve' | 'reject';
  reviewer_notes?: string;
}

interface ApprovalResponse {
  success: boolean;
  session_id: string;
  new_status: 'APPROVED' | 'REJECTED';
  reviewed_at: string;
  reviewed_by: string;
}
```

**後端 API 對應**:
- ⚠️ **GAP**: 需要新增以下端點：
  - `GET /api/v1/attendance/sessions?status=PENDING` → 查詢待審核
  - `POST /api/v1/attendance/sessions/{id}/approve` → 批准
  - `POST /api/v1/attendance/sessions/{id}/reject` → 拒絕
- 需要 Manager scope 驗證
- 需要 tenant isolation (只能審核自己公司的)

---

### HR/Admin 角色

#### 6. 公司統計頁面 `/attendance/company`

**功能**: 查看公司整體出勤統計

**UI 需要的資料**:
```typescript
interface CompanySummaryRequest {
  month: string;  // "YYYY-MM"
}

interface CompanySummary {
  month: string;
  total_employees: number;
  total_work_days: number;
  average_attendance_rate: number;  // 出勤率 %
  total_late_count: number;
  total_overtime_hours: number;
  department_summary: {
    department_id: string;
    department_name: string;
    employee_count: number;
    attendance_rate: number;
    late_count: number;
  }[];
}
```

**後端 API 對應**:
- ⚠️ **明確排除**: 這是 WP-11-06 (Reporting) 的範圍
- 目前不實作，標記為 FUTURE

---

#### 7. 員工明細頁面 `/attendance/users/{id}`

**功能**: 查看單一員工的月份出勤明細

**UI 需要的資料**:
```typescript
interface UserDetailRequest {
  user_id: string;
  month: string;  // "YYYY-MM"
}

interface UserDetail {
  user_id: string;
  user_name: string;
  department: string;
  month: string;
  sessions: SessionRecord[];  // 同 SessionRecord 定義
  summary: {
    total_days: number;
    work_days: number;
    late_days: number;
    total_work_hours: number;
    average_work_hours: number;
  };
}
```

**後端 API 對應**:
- ⚠️ **明確排除**: 這是 WP-11-06 (Reporting) 的範圍
- 目前不實作，標記為 FUTURE

---

## 🔄 Session 狀態機

### 狀態定義

```typescript
enum SessionStatus {
  OPEN = 'open',                      // 已打上班卡，未打下班卡
  CLOSED = 'closed',                  // 已打下班卡（正常完成）
  PENDING = 'pending',                // 待審核（補打卡、異常打卡）
  APPROVED = 'approved',              // 已審核通過
  REJECTED = 'rejected',              // 已拒絕
  MISSING_PUNCH_OUT = 'missing_punch_out'  // 缺下班卡（日結後）
}
```

### 狀態轉換規則

```
[初始] 
  ↓ punch-in
[OPEN] ────────────────────────────────────┐
  ↓ punch-out                              │
  ├─ Match Policy → [APPROVED]             │ 21:00 日結
  ├─ NO_MATCH + reason → [PENDING]         │ (缺 punch-out)
  └─ NO_MATCH + no reason → 拒絕 (400)     ↓
                                      [MISSING_PUNCH_OUT]
[PENDING]
  ├─ Manager approve → [APPROVED]
  └─ Manager reject → [REJECTED]

[APPROVED] → 參與工時計算、日結統計
[PENDING] → 不參與工時計算、日結統計
[REJECTED] → 不參與工時計算、日結統計
[MISSING_PUNCH_OUT] → 不參與工時計算、日結統計
```

### 後端實作狀態

**已實作**:
- ✅ `OPEN` / `CLOSED` 狀態 (models.py, migration)
- ✅ punch-in 建立 OPEN session
- ✅ punch-out 關閉 session → CLOSED

**未實作 (GAP)**:
- ❌ `PENDING` 狀態
- ❌ `APPROVED` 狀態
- ❌ `REJECTED` 狀態
- ❌ `MISSING_PUNCH_OUT` 狀態
- ❌ NO_MATCH 必填 reason 驗證
- ❌ Manager approve/reject workflow

**證據**:
- 檔案: `backend/app/modules/attendance/models.py:87`
- 目前只有: `status IN ('open', 'closed')`

---

## 📅 Cross-Midnight 跨日規則

### 規則定義

**核心規則**: `work_date = punch_in_time.date()`

跨日工時歸屬以 **punch_in 那天** 為準，不論 punch_out 是否跨日。

### 範例場景

```
場景 1: 夜班跨日
- Punch in:  2026-03-31 23:00
- Punch out: 2026-04-01 02:00
- Work duration: 3 hours (180 minutes)
- Attribution date: 2026-03-31 ✅ (punch_in date)

場景 2: 正常班次
- Punch in:  2026-03-05 09:00
- Punch out: 2026-03-05 18:00
- Work duration: 9 hours (540 minutes)
- Attribution date: 2026-03-05 ✅

場景 3: 超長加班跨日
- Punch in:  2026-03-05 09:00
- Punch out: 2026-03-06 01:00
- Work duration: 16 hours (960 minutes)
- Attribution date: 2026-03-05 ✅ (punch_in date)
```

### 後端實作狀態

**已實作**:
- ✅ `punch_in_time` 欄位 (DateTime with timezone)
- ✅ `punch_out_time` 欄位 (DateTime with timezone)
- ✅ `duration_minutes` 計算 (punch_out - punch_in)

**測試覆蓋**:
- ✅ Test 8: `test_8_cross_midnight_work_attribution`
- 檔案: `backend/app/modules/attendance/tests/test_regression.py:test_8`
- 驗證: attribution_date = punch_in_time.date()

**Query 層實作**:
- ⚠️ **需確認**: 月份查詢是否用 `punch_in_time` 的 date window
- 範例: `WHERE DATE(punch_in_time) BETWEEN '2026-03-01' AND '2026-03-31'`

---

## 🔧 Policy Engine Integration

### Policy Evaluation 流程

```
punch-out 時觸發:
1. 計算 work_minutes = punch_out - punch_in
2. 查詢 user 的 policy (或使用 default policy)
3. 呼叫 policy_engine.evaluate(session, policy)
4. 回傳 policy_evaluation 結果
```

### Policy Evaluation 欄位

```typescript
interface PolicyEvaluation {
  is_late: boolean;
  late_minutes: number;
  is_early_leave: boolean;
  early_leave_minutes: number;
  is_overtime: boolean;
  overtime_minutes: number;
  work_minutes: number;
  policy_name: string | null;
}
```

### 後端實作狀態

**已實作**:
- ✅ `policy_engine.py` (24KB, WP-11-03)
- ✅ `AttendancePolicyEngine.evaluate()` 方法
- ✅ Policy evaluation 邏輯 (遲到/早退/加班)

**未實作 (GAP)**:
- ❌ punch-out API 未呼叫 policy engine
- ❌ punch-out response 未包含 `policy_evaluation` 欄位
- ❌ NO_MATCH → PENDING 邏輯未實作
- ❌ NO_MATCH 必填 reason 驗證未實作

**證據**:
- Policy Engine: `backend/app/modules/attendance/policy_engine.py`
- Punch API: `backend/app/modules/attendance/api.py` (目前只有 mock endpoints)
- Schema: `backend/app/modules/attendance/schemas.py:PolicyEvaluationResponse` ✅ 已定義

---

## ✅ Approval Workflow

### 審核流程

```
1. Employee 補打卡 → 建立 PENDING session
2. Manager 查詢 PENDING sessions
3. Manager approve/reject
4. Session 狀態變更 → APPROVED / REJECTED
5. 若 APPROVED → 重新計算當日工時
```

### 審核所需欄位

```typescript
interface PendingSession {
  session_id: string;
  user_id: string;
  user_name: string;
  date: string;
  punch_in_time: string;
  punch_out_time: string | null;
  reason: string;           // ← 必要
  status: 'PENDING';
  created_at: string;
}

interface ApprovalAction {
  session_id: string;
  action: 'approve' | 'reject';
  reviewer_id: string;      // ← 必要
  reviewer_notes: string;   // ← 可選
  reviewed_at: string;      // ← 自動
}
```

### 後端實作狀態

**已實作**:
- ✅ `approve_attendance_record()` 方法 (repo.py)
- ✅ Tenant isolation (只能審核自己公司的)
- ✅ 404 if not found or not belong to company

**未實作 (GAP)**:
- ❌ PENDING 狀態支援
- ❌ `GET /api/v1/attendance/sessions?status=PENDING` 端點
- ❌ `POST /api/v1/attendance/sessions/{id}/approve` 端點
- ❌ `POST /api/v1/attendance/sessions/{id}/reject` 端點
- ❌ `reason` 欄位 (AttendanceSession model)
- ❌ `reviewer_id` 欄位
- ❌ `reviewed_at` 欄位
- ❌ Manager scope 驗證

**證據**:
- Repo: `backend/app/modules/attendance/repo.py:approve_attendance_record()`
- 目前只有舊的 `attendance_records` 表，不是 `attendance_sessions`

---

## 🧪 Regression Tests 覆蓋

### WP-11-05 測試清單

| # | 測試名稱 | UI/UX 規則 | 狀態 |
|---|---------|-----------|------|
| 1 | NO_MATCH without reason → rejected | PENDING 狀態 + reason 必填 | SKIP |
| 2 | NO_MATCH with reason → pending | PENDING 狀態 | SKIP |
| 3 | Approved → policy evaluation correct | Policy evaluation | SKIP |
| 4 | Pending not in daily summary | PENDING 不參與統計 | SKIP |
| 5 | Daily close missing punch-out | MISSING_PUNCH_OUT 狀態 | SKIP |
| 6 | Approve pending → recalculate daily | Approval workflow | SKIP |
| 7 | Customer service unassigned → 403 | Scope 驗證 | SKIP |
| 8 | Cross-midnight work attribution | Cross-midnight 規則 | ✅ PASS |
| 9 | Double punch prevention | Business invariant | ✅ PASS |
| 10 | Tenant isolation cross-company | Tenant isolation | ✅ PASS |

**測試檔案**: `backend/app/modules/attendance/tests/test_regression.py`

**關鍵測試 (Test 8)**:
```python
def test_8_cross_midnight_work_attribution(self, client, test_user, night_shift_policy, db):
    # Punch in at 2026-03-31 23:00
    # Punch out at 2026-04-01 02:00
    # Expected: work_minutes=180, attribution_date=2026-03-31
```

---

## 🚫 明確排除 WP-11-06 (Reporting)

### 排除範圍

以下功能屬於 WP-11-06，**不在當前驗證範圍內**：

1. ❌ 公司統計報表 (`/attendance/company`)
2. ❌ 員工明細報表 (`/attendance/users/{id}`)
3. ❌ 部門統計報表
4. ❌ CSV 匯出功能
5. ❌ 圖表視覺化
6. ❌ 月份/季度/年度統計

### 當前範圍 (WP-11-01 ~ WP-11-05)

✅ 包含:
- 打卡功能 (punch-in/out)
- 個人記錄查詢 (sessions)
- Policy evaluation
- Tenant isolation
- Cross-midnight 處理

❌ 不包含:
- Reporting endpoints
- 統計聚合
- 圖表資料

---

## 📊 API Mapping 總覽表

| UI Route | 功能 | Backend API | 狀態 |
|----------|------|-------------|------|
| `/attendance/punch` | 打卡頁面 | `GET /api/v1/attendance/status` | ✅ 已實作 |
| | | `POST /api/v1/attendance/punch-in` | ✅ 已實作 |
| | | `POST /api/v1/attendance/punch-out` | ✅ 已實作 |
| | | `POST /api/v1/attendance/break-out` | ❌ GAP |
| | | `POST /api/v1/attendance/break-in` | ❌ GAP |
| `/attendance/sessions` | 個人記錄 | `GET /api/v1/attendance/sessions?month=YYYY-MM` | ⚠️ 部分實作 |
| `/attendance/calendar` | 個人月曆 | `GET /api/v1/attendance/calendar?month=YYYY-MM` | ❌ GAP |
| `/attendance/today` | 今日出勤 | `GET /api/v1/attendance/today` | ❌ GAP |
| `/attendance/approvals` | 審核頁面 | `GET /api/v1/attendance/sessions?status=PENDING` | ❌ GAP |
| | | `POST /api/v1/attendance/sessions/{id}/approve` | ❌ GAP |
| | | `POST /api/v1/attendance/sessions/{id}/reject` | ❌ GAP |
| `/attendance/company` | 公司統計 | ❌ WP-11-06 (排除) | FUTURE |
| `/attendance/users/{id}` | 員工明細 | ❌ WP-11-06 (排除) | FUTURE |

---

## 🔍 GAP 總結

### P0 - 阻斷性 GAP

1. **Session 狀態機不完整**
   - 缺少: PENDING, APPROVED, REJECTED, MISSING_PUNCH_OUT
   - 影響: 無法支援補打卡審核流程

2. **Approval Workflow 未實作**
   - 缺少: approve/reject endpoints
   - 缺少: reason, reviewer_id, reviewed_at 欄位
   - 影響: Manager 無法審核

3. **Policy Engine 未整合到 punch-out**
   - 缺少: punch-out 時呼叫 policy engine
   - 缺少: policy_evaluation 回傳欄位
   - 影響: 無法自動判斷遲到/加班

### P1 - 功能性 GAP

4. **外出/返回打卡未實作**
   - 缺少: break-out / break-in endpoints
   - 影響: 員工無法記錄外出

5. **月份查詢參數支援**
   - 缺少: `month=YYYY-MM` 參數支援
   - 影響: 前端需要自行轉換日期範圍

6. **今日出勤列表**
   - 缺少: `/api/v1/attendance/today` endpoint
   - 影響: Manager 無法查看今日出勤

7. **月曆視圖資料**
   - 缺少: `/api/v1/attendance/calendar` endpoint
   - 影響: 需前端聚合 sessions 資料

---

## 📝 開發建議

### 短期 (WP-11-05 完成後)

1. 補充 Session 狀態機 (PENDING, APPROVED, REJECTED)
2. 實作 Approval Workflow endpoints
3. 整合 Policy Engine 到 punch-out API

### 中期 (WP-11-06 之前)

4. 實作外出/返回打卡
5. 優化月份查詢參數
6. 實作今日出勤列表

### 長期 (WP-11-06)

7. 實作 Reporting 模組
8. 實作統計聚合
9. 實作 CSV 匯出

---

**文件版本**: 1.0  
**建立日期**: 2026-03-05  
**維護者**: 架構團隊  
**狀態**: ✅ ACTIVE

---

**END OF ATTENDANCE_UI_UX_PLAN.md**
