# WP-11-04B Kickoff Plan

**Work Package:** WP-11-04B — Attendance Reports v1 (Phase B Implementation)  
**Gate:** 5 (Attendance Core APIs)  
**Status:** Ready to Start  
**Created:** 2026-03-04  
**Auth Model:** 🔒 FROZEN (Gate 4 closed)

---

## 執行摘要

WP-11-04B 將實作 Attendance Reports v1，提供公司和員工的出勤記錄查詢、統計報表功能。

**前置條件：**
- ✅ WP-11-01: Attendance Domain Model（已完成）
- ✅ WP-11-02: Punch In/Out API（已完成，17/17 測試通過）
- ✅ WP-11-03: Policy Engine v1（已完成，12/12 測試通過）
- ✅ WP-11-04A: Company Entitlements + Feature Flags（已完成）
- ✅ Migration chain 健康（Fresh DB rebuild 100% 成功）

**交付目標：**
- 員工出勤記錄查詢 API
- 公司出勤統計報表 API
- 遲到/早退/加班統計
- CSV 匯出功能（可選）
- 完整測試覆蓋（目標：15+ 測試）

---

## 1. Scope 定義

### 1.1 功能範圍（In Scope）

#### A) 員工出勤記錄查詢

**API Endpoint:**
```
GET /api/v1/attendance/sessions
```

**功能：**
- 查詢指定時間範圍的出勤記錄
- 支援分頁（limit/offset）
- 支援排序（按 punch_in_time）
- 支援篩選（by user_id, status）
- 回傳完整 session 資訊（含 policy evaluation）

**權限：**
- Company User: 只能查詢自己的記錄
- Company Admin: 可查詢公司內所有員工記錄
- Customer Service: 可查詢被指派公司的記錄（只讀）
- Super Admin: 可查詢任意公司記錄

**驗證順序：**
1. Scope 檢查（assert_company_scope）
2. Tenant Isolation（WHERE company_id = ?）
3. User Scope 檢查（非 admin 只能查自己）

---

#### B) 公司出勤統計報表

**API Endpoint:**
```
GET /api/v1/attendance/reports/company-summary
```

**功能：**
- 統計指定時間範圍的公司出勤數據
- 總出勤人次
- 總工時
- 遲到次數/人次
- 早退次數/人次
- 加班總時數
- 平均工時

**權限：**
- Company Admin: 可查詢自己公司
- Customer Service: 可查詢被指派公司（只讀）
- Super Admin: 可查詢任意公司

**驗證順序：**
1. Scope 檢查（assert_company_scope）
2. Tenant Isolation（WHERE company_id = ?）

---

#### C) 個人出勤統計

**API Endpoint:**
```
GET /api/v1/attendance/reports/user-summary
```

**功能：**
- 統計指定時間範圍的個人出勤數據
- 總出勤天數
- 總工時
- 遲到次數
- 早退次數
- 加班總時數
- 平均每日工時

**權限：**
- Company User: 只能查詢自己
- Company Admin: 可查詢公司內任意員工
- Customer Service: 可查詢被指派公司的員工（只讀）
- Super Admin: 可查詢任意員工

---

#### D) CSV 匯出（可選，P1）

**API Endpoint:**
```
GET /api/v1/attendance/export/csv
```

**功能：**
- 匯出出勤記錄為 CSV 格式
- 支援與查詢 API 相同的篩選條件
- 回傳 CSV 檔案（Content-Type: text/csv）

**權限：**
- 與查詢 API 相同

---

### 1.2 非功能範圍（Out of Scope）

**本 WP 不包含：**
- ❌ Excel (XLSX) 匯出（未來 WP）
- ❌ PDF 報表（未來 WP）
- ❌ 圖表視覺化（前端負責）
- ❌ 排班管理（未來 Gate）
- ❌ 請假管理（未來 Gate）
- ❌ 加班申請審批（未來 WP）
- ❌ 即時通知（WP-11-05 Audit Hooks）
- ❌ Telegram 整合（WP-11-06）

---

## 2. 技術設計

### 2.1 資料模型（無需修改）

**使用現有表：**
- `attendance_sessions` - 出勤 session（WP-11-01）
- `attendance_punches` - 打卡記錄（WP-11-01）
- `attendance_policies` - 考勤政策（WP-11-01）
- `users` - 使用者（Gate 4，FROZEN）
- `user_company_memberships` - 公司成員（Gate 4，FROZEN）

**不需要新增表或欄位**

---

### 2.2 API 設計

#### API 1: 查詢出勤記錄

**Request:**
```http
GET /api/v1/attendance/sessions?start_date=2026-03-01&end_date=2026-03-31&user_id=xxx&limit=20&offset=0
Authorization: Bearer {jwt_token}
```

**Query Parameters:**
- `start_date` (required): ISO 8601 date (YYYY-MM-DD)
- `end_date` (required): ISO 8601 date (YYYY-MM-DD)
- `user_id` (optional): 篩選特定使用者（admin only）
- `status` (optional): open/closed
- `limit` (optional): 預設 20，最大 100
- `offset` (optional): 預設 0

**Response:**
```json
{
  "sessions": [
    {
      "id": "uuid",
      "company_id": "company-001",
      "user_id": "uuid",
      "user_name": "張三",
      "punch_in_time": "2026-03-01T09:05:00Z",
      "punch_out_time": "2026-03-01T18:30:00Z",
      "status": "closed",
      "duration_minutes": 505,
      "policy_evaluation": {
        "is_late": true,
        "late_minutes": 5,
        "is_early_leave": false,
        "early_leave_minutes": 0,
        "is_overtime": true,
        "overtime_minutes": 65
      },
      "notes": null
    }
  ],
  "pagination": {
    "total": 150,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

**Error Responses:**
- 400: Invalid date range
- 403: Forbidden (scope violation)
- 422: Validation error

---

#### API 2: 公司出勤統計

**Request:**
```http
GET /api/v1/attendance/reports/company-summary?start_date=2026-03-01&end_date=2026-03-31
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "company_id": "company-001",
  "period": {
    "start_date": "2026-03-01",
    "end_date": "2026-03-31"
  },
  "summary": {
    "total_sessions": 450,
    "total_work_hours": 3600.5,
    "total_employees": 15,
    "late_count": 23,
    "early_leave_count": 5,
    "overtime_hours": 120.5,
    "average_work_hours_per_session": 8.0
  }
}
```

---

#### API 3: 個人出勤統計

**Request:**
```http
GET /api/v1/attendance/reports/user-summary?user_id=xxx&start_date=2026-03-01&end_date=2026-03-31
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "user_id": "uuid",
  "user_name": "張三",
  "company_id": "company-001",
  "period": {
    "start_date": "2026-03-01",
    "end_date": "2026-03-31"
  },
  "summary": {
    "total_sessions": 22,
    "total_work_hours": 176.5,
    "late_count": 2,
    "early_leave_count": 0,
    "overtime_hours": 8.5,
    "average_work_hours_per_day": 8.0
  }
}
```

---

### 2.3 Repository 層

**新增方法（backend/app/modules/attendance/repo.py）：**

```python
class AttendanceRepository:
    # 現有方法...
    
    # WP-11-04B 新增
    def get_sessions_by_date_range(
        self,
        company_id: str,
        start_date: date,
        end_date: date,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[AttendanceSession], int]:
        """查詢出勤記錄（含分頁）"""
        pass
    
    def get_company_summary(
        self,
        company_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """公司出勤統計"""
        pass
    
    def get_user_summary(
        self,
        company_id: str,
        user_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """個人出勤統計"""
        pass
```

---

### 2.4 Service 層

**新增方法（backend/app/modules/attendance/service.py）：**

```python
class AttendanceService:
    # 現有方法...
    
    # WP-11-04B 新增
    def get_sessions(
        self,
        actor: Actor,
        company_id: str,
        start_date: date,
        end_date: date,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        """查詢出勤記錄（含權限檢查）"""
        # 1. Scope 檢查
        # 2. User scope 檢查（非 admin 只能查自己）
        # 3. 呼叫 repo
        # 4. 加入 policy evaluation（如果 session 已關閉）
        pass
    
    def get_company_summary(
        self,
        actor: Actor,
        company_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """公司出勤統計（含權限檢查）"""
        pass
    
    def get_user_summary(
        self,
        actor: Actor,
        company_id: str,
        user_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """個人出勤統計（含權限檢查）"""
        pass
```

---

### 2.5 API 層

**新增端點（backend/app/modules/attendance/api.py）：**

```python
@router.get("/sessions")
def get_attendance_sessions(
    start_date: date,
    end_date: date,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db)
):
    """查詢出勤記錄"""
    pass

@router.get("/reports/company-summary")
def get_company_summary(
    start_date: date,
    end_date: date,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db)
):
    """公司出勤統計"""
    pass

@router.get("/reports/user-summary")
def get_user_summary(
    user_id: str,
    start_date: date,
    end_date: date,
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db)
):
    """個人出勤統計"""
    pass
```

---

## 3. 驗證順序（強制）

所有 API 必須遵守固定驗證順序：

```python
# Step 1: Scope 檢查
assert_company_scope(actor, company_id, db)

# Step 2: User Scope 檢查（如果需要）
if not actor.is_admin() and user_id != actor.user_id:
    raise ScopeError("Cannot access other user's data")

# Step 3: Tenant Isolation
# 確保查詢只針對該公司（WHERE company_id = ?）

# Step 4: Feature Gate（如果需要）
# feature_service.require_enabled(company_id, feature_key)
```

---

## 4. 測試計畫

### 4.1 測試檔案

**新增測試檔案：**
- `backend/app/modules/attendance/tests/test_reports_api.py`

**測試覆蓋目標：** 15+ 測試

---

### 4.2 測試案例

#### A) 查詢出勤記錄 API

**測試案例：**
1. ✅ Company user 可查詢自己的記錄
2. ✅ Company user 不可查詢其他人的記錄（403）
3. ✅ Company admin 可查詢公司內所有員工記錄
4. ✅ Customer service 可查詢被指派公司的記錄
5. ✅ Customer service 不可查詢未指派公司的記錄（403）
6. ✅ Super admin 可查詢任意公司記錄
7. ✅ 日期範圍篩選正確
8. ✅ 分頁功能正確（limit/offset）
9. ✅ 狀態篩選正確（open/closed）
10. ✅ 回傳資料包含 policy evaluation

---

#### B) 公司出勤統計 API

**測試案例：**
1. ✅ Company admin 可查詢自己公司統計
2. ✅ Company user 不可查詢公司統計（403）
3. ✅ Customer service 可查詢被指派公司統計
4. ✅ Super admin 可查詢任意公司統計
5. ✅ 統計數據正確（總工時、遲到次數等）

---

#### C) 個人出勤統計 API

**測試案例：**
1. ✅ Company user 可查詢自己的統計
2. ✅ Company user 不可查詢其他人的統計（403）
3. ✅ Company admin 可查詢公司內任意員工統計
4. ✅ 統計數據正確

---

#### D) Tenant Isolation

**測試案例：**
1. ✅ 跨公司資料不可取（WHERE company_id 生效）
2. ✅ Customer service 只能查詢被指派公司

---

## 5. 檔案修改清單

### 5.1 新增檔案

**無需新增檔案**（使用現有檔案）

---

### 5.2 修改檔案

| 檔案 | 修改內容 | 預估行數 |
|------|---------|---------|
| `backend/app/modules/attendance/repo.py` | 新增 3 個查詢方法 | +150 |
| `backend/app/modules/attendance/service.py` | 新增 3 個 service 方法 | +200 |
| `backend/app/modules/attendance/api.py` | 新增 3 個 API 端點 | +150 |
| `backend/app/modules/attendance/schemas.py` | 新增 request/response schemas | +100 |
| `backend/app/modules/attendance/tests/test_reports_api.py` | 新增測試檔案 | +600 |

**總計：** ~1200 行新增程式碼

---

## 6. Migration 需求

**Migration 需求：** ❌ **無需 migration**

**理由：**
- 使用現有表（attendance_sessions, attendance_punches, attendance_policies）
- 無需新增表或欄位
- 現有索引已足夠（idx_sessions_company_punch_in）

**如果效能不足，可考慮新增索引（P1）：**
```sql
-- 可選：加速日期範圍查詢
CREATE INDEX idx_sessions_company_date_range 
  ON attendance_sessions(company_id, punch_in_time, punch_out_time);
```

---

## 7. 驗收標準

### 7.1 功能驗收

- ✅ 所有 3 個 API 端點正常運作
- ✅ 權限檢查正確（company user/admin/customer service/super admin）
- ✅ Tenant isolation 生效（跨公司資料不可取）
- ✅ 日期範圍篩選正確
- ✅ 分頁功能正確
- ✅ 統計數據正確（與 policy engine 一致）

---

### 7.2 測試驗收

- ✅ 至少 15 個測試案例
- ✅ 所有測試通過（15/15）
- ✅ 測試覆蓋所有權限組合
- ✅ 測試覆蓋 tenant isolation
- ✅ 測試覆蓋邊界情況（空結果、大量資料）

---

### 7.3 程式碼品質

- ✅ 遵守驗證順序（Scope → Tenant Isolation → Feature Gate）
- ✅ 錯誤格式統一（403 Forbidden, 400 Bad Request）
- ✅ 無 linter 錯誤
- ✅ 程式碼註解清晰
- ✅ 符合專案 coding style

---

### 7.4 文件驗收

- ✅ API 文件完整（request/response 範例）
- ✅ 更新 README（如果需要）
- ✅ 產出 WP-11-04B_COMPLETION_REPORT.md

---

## 8. 風險與依賴

### 8.1 依賴項目

**已完成：**
- ✅ WP-11-01: Attendance Domain Model
- ✅ WP-11-02: Punch In/Out API
- ✅ WP-11-03: Policy Engine v1
- ✅ WP-11-04A: Company Entitlements + Feature Flags
- ✅ Migration chain 健康

**無阻塞依賴**

---

### 8.2 風險評估

| 風險 | 機率 | 影響 | 緩解措施 |
|------|------|------|---------|
| 效能問題（大量資料查詢） | 中 | 中 | 使用現有索引，必要時新增複合索引 |
| 權限邏輯複雜 | 低 | 中 | 使用現有 scope.py，遵循既有模式 |
| 統計數據不一致 | 低 | 高 | 使用 policy_engine 統一計算邏輯 |
| 測試覆蓋不足 | 低 | 中 | 目標 15+ 測試，覆蓋所有權限組合 |

**整體風險：** 🟢 **低**

---

## 9. 時程估算

### 9.1 工作拆解

| 任務 | 預估時間 | 優先級 |
|------|---------|--------|
| 修復 test_migration_smoke.py | 0.5 小時 | P0 |
| Repository 層實作 | 2 小時 | P0 |
| Service 層實作 | 3 小時 | P0 |
| API 層實作 | 2 小時 | P0 |
| Schemas 定義 | 1 小時 | P0 |
| 測試撰寫 | 4 小時 | P0 |
| 測試除錯 | 2 小時 | P0 |
| 文件撰寫 | 1 小時 | P0 |
| Code review 修正 | 1 小時 | P1 |
| CSV 匯出（可選） | 2 小時 | P1 |

**總計：** 16.5 小時（不含 CSV 匯出）

**預估完成時間：** 2-3 個工作天

---

## 10. 開工檢查清單

### 10.1 環境檢查

- ✅ Migration chain 健康（alembic heads 單一 head）
- ✅ Fresh DB rebuild 成功
- ✅ Production DB version 正確（wp_11_04a_entitlements）
- ✅ Test DB version 正確（wp_11_04a_entitlements）
- 🔴 test_migration_smoke.py 需修復（第一個 commit）

---

### 10.2 程式碼檢查

- ✅ WP-11-02 API 正常運作（17/17 測試通過）
- ✅ WP-11-03 Policy Engine 正常運作（12/12 測試通過）
- ✅ WP-11-04A Entitlements 已部署
- ✅ 現有測試全部通過

---

### 10.3 文件檢查

- ✅ WP-11-04B_GATE_READY_REPORT.md 已產出
- ✅ WP-11-04B_KICKOFF_PLAN.md 已產出（本文件）
- ✅ GATE_5_BOUNDARY_RULES.md 已閱讀
- ✅ MIGRATION_CLEAN_REBUILD_POLICY.md 已遵守

---

## 11. 第一個 Commit 檢查清單

**第一個 commit 必須包含：**

1. ✅ 修復 test_migration_smoke.py
   ```python
   # backend/tests/test_migration_smoke.py
   # 修改 cwd 路徑：
   cwd=os.path.join(os.path.dirname(__file__), '..')
   ```

2. ✅ 執行測試確認通過
   ```bash
   pytest tests/test_migration_smoke.py -v
   # 預期：3 passed
   ```

3. ✅ Commit message
   ```
   fix(test): correct alembic.ini path in test_migration_smoke.py
   
   WP-11-04B: Fix cwd calculation in migration smoke tests.
   Changed from '../..' to '..' to correctly locate alembic.ini.
   
   Tests: 3/3 passing
   ```

---

## 12. 參考文件

**Migration 相關：**
- `docs/MIGRATION_CLEAN_REBUILD_POLICY.md`
- `docs/MIGRATION_CHAIN_AUDIT_REPORT.md`
- `docs/WP-11-04B_GATE_READY_REPORT.md`

**WP-11-04A 相關：**
- `docs/WP-11-04A_COMPLETION_REPORT_FINAL.md`
- `backend/app/core/features.py`
- `backend/app/core/scope.py`

**Attendance 相關：**
- `docs/WP-11-01_ATTENDANCE_DOMAIN_MODEL_SPEC.md`
- `docs/WP-11-02_REPORT.md`
- `docs/WP-11-03_REPORT.md`
- `backend/app/modules/attendance/policy_engine.py`

**Gate 5 相關：**
- `docs/GATE_5_BOUNDARY_RULES.md`
- `docs/GATE_PROGRESS_TRACKER.md`

---

## 13. 結論

**開工狀態：** ✅ **可以開工**

**關鍵里程碑：**
1. ✅ Migration chain 健康（放行檢查通過）
2. ✅ 所有依賴 WP 已完成
3. ✅ Kickoff Plan 已產出
4. 🔴 第一個 commit 修復 test_migration_smoke.py

**預期交付：**
- 3 個 API 端點（查詢、公司統計、個人統計）
- 15+ 測試案例
- 完整文件
- 2-3 個工作天完成

**下一步：**
1. 修復 test_migration_smoke.py（第一個 commit）
2. 實作 Repository 層
3. 實作 Service 層
4. 實作 API 層
5. 撰寫測試
6. 產出完成報告

---

**文件產出時間：** 2026-03-04 19:30 UTC+8  
**產出人員：** Claude Sonnet 4.6  
**狀態：** Ready to Start
