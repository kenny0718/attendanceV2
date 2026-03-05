# Master Development Roadmap

**系統名稱：** Attendance SaaS System  
**架構版本：** SA_MODULE_SPEC v1.9 (Platform-First Architecture)  
**文件版本：** 1.0  
**建立日期：** 2026-03-04  
**狀態：** ✅ APPROVED

---

## Document Authority

本文件為系統開發的**唯一權威路線圖**。

**整合來源：**
1. SA_MODULE_SPEC v1.9 - 架構規格
2. SA_REALITY_GAP_REPORT.md - 現況分析
3. REALITY_AUDIT_STATUS_INVENTORY.md - 實作盤點
4. ARCHITECTURE_FIX_DECISION.md - 修正決策
5. REALITY_AUDIT_NEXT_ACTIONS.md - 行動計畫

**變更控制：**
- 任何偏離本路線圖的開發需要架構審查
- 路線圖更新需要團隊共識
- 版本控制：每次重大變更產生新版本

---

## 1. Architecture Baseline

### 1.1 System Authority

**SA_MODULE_SPEC v1.9** 為系統架構的唯一權威規範。

**核心原則：**
- Platform-First Identity（使用者為全域身份）
- Same Database, Same Tables（A 架構）
- Tenant Isolation via company_id（租戶隔離）
- Feature Flags（功能分級）
- Scope → Tenant → Feature 驗證順序

**不可妥協的要求（P0）：**
1. 所有 Tenant Data 必須有 company_id
2. 所有查詢必須過濾 company_id
3. company_id 不得來自 request body
4. 8 個 Attendance 回歸測試必須通過
5. Backup/Restore 只操作單一 company

---

### 1.2 Architecture Compliance

**當前符合度：** 75% (17/40 完全符合，11/40 部分符合)

**目標符合度：** > 95%

**達成時間：** Phase 1 完成後

---

## 2. Current System Status

### 2.1 Implemented Modules

| Module | 完成度 | 狀態 | 備註 |
|--------|--------|------|------|
| **tenants** | 100% | ✅ COMPLETE | Migration + CRUD + Entitlements |
| **auth** | 100% | ✅ COMPLETE | JWT + Platform-First v2 |
| **attendance** | 85% | 🚧 IN PROGRESS | 缺回歸測試 + Auth 轉換 |
| **notifications** | 80% | 🚧 IN PROGRESS | 缺 Auth 轉換 |
| **backup** | 100% | ✅ COMPLETE | Export/Restore 符合規範 |
| **audit** | 80% | 🚧 IN PROGRESS | 缺 Auth 轉換 |
| **customer_service** | 100% | ✅ COMPLETE | Scope + Assignments |

**總計：** 7/14 模組已實作（50%）

---

### 2.2 Missing Modules

| Module | 優先度 | 預計 Phase | 說明 |
|--------|--------|-----------|------|
| **locations** | P1 | Phase 2 | 打卡地點管理 |
| **approvals** | P1 | Phase 2 | 審批流程 |
| **leave** | P1 | Phase 2 | 請假管理 |
| **accrual** | P1 | Phase 2 | 假期額度 |
| **vehicles** | P2 | Phase 2 | 車輛管理 |
| **dispatch** | P2 | Phase 2 | 派車管理 |
| **reporting** | P1 | Phase 2 | 報表模組 |

**總計：** 7/14 模組未實作（50%）

---

### 2.3 SA Alignment Status

**完全符合（17 項）：**
- ✅ Platform-First Identity 架構
- ✅ Data Classification (Platform/Membership/Tenant)
- ✅ Tenant Isolation (Write/Query Rules)
- ✅ Platform Roles (super_admin/customer_service/company_user)
- ✅ Scope Checker 實作
- ✅ Feature Flags 基礎設施
- ✅ Backup/Restore 實作
- ✅ Index Rules
- ✅ Error Code 統一
- ✅ Cross-Module Interaction (EventBus)
- ✅ UUID Primary Key (大部分)
- ✅ JWT 基礎設施
- ✅ Actor dependency
- ✅ Entitlements CRUD API
- ✅ Migration chain (001b 已修正)
- ✅ 所有 Tenant Data 有 company_id
- ✅ 所有 repo 強制 tenant filter

**部分符合（11 項）：**
- ⚠️ Request Context (只有 2/7 模組用 JWT)
- ⚠️ Scope Validation (只有 2/7 模組實作)
- ⚠️ Feature Gate (基礎設施完成，未套用)
- ⚠️ Module Structure (缺 docs.md)
- ⚠️ Auth 轉換 (40% 完成)
- ⚠️ API 安全 (混合 Header+JWT)
- ⚠️ Primary Key (tenants 用 VARCHAR)
- ⚠️ 驗證順序 (只有新模組實作)

**完全缺失（12 項）：**
- ❌ 8 個 Attendance 回歸測試
- ❌ 7 個未來模組
- ❌ API 文件 (docs.md)
- ❌ Tenant Isolation 測試 (部分)

---

## 3. Execution Phases

### Phase Overview

| Phase | 名稱 | 預估時間 | 狀態 |
|-------|------|----------|------|
| **Phase 1** | Architecture Alignment | 2-3 週 | 🎯 NEXT |
| **Phase 2** | Core Backend Completion | 6-8 週 | ⏳ PLANNED |
| **Phase 3** | SaaS Infrastructure | 2-3 週 | ⏳ PLANNED |
| **Phase 4** | Frontend | 8-10 週 | ⏳ PLANNED |
| **Phase 5** | External Integration | 4-6 週 | ⏳ PLANNED |

**總預估時間：** 22-30 週（5-7 個月）

---

## Phase 1 — Architecture Alignment

**目標：** 將現有系統對齊 SA v1.9 規範

**預估時間：** 2-3 週

**完成標準：**
- SA 符合度 > 95%
- 8 個回歸測試通過
- 所有模組使用 JWT
- Scope 驗證統一實作
- Feature Gate 套用到所有 API

---

### Phase 1 Work Packages

#### WP-11-04B: Migration Chain 驗證

**Goal:** 確保 migration chain 可在 fresh DB 執行

**Priority:** P0（阻斷其他工作）

**Duration:** 1 小時

**Scope:**
- ✅ 檢查實際 DB 的 alembic_version
- ✅ 在 fresh DB 測試 `alembic upgrade head`
- ✅ 清理 001 (舊版) 檔案
- ⛔ 不修改 migration 內容

**Files Affected:**
- `backend/alembic/versions/001_*.py` (可能刪除)
- `docs/MIGRATION_CHAIN_AUDIT_REPORT.md` (更新)

**Tests Required:**
```bash
# 建立 fresh DB
createdb attendance_fresh_test

# 執行 migration
DATABASE_URL="postgresql://...attendance_fresh_test" alembic upgrade head

# 驗證 tables
psql -d attendance_fresh_test -c "\dt"

# 清理
dropdb attendance_fresh_test
```

**Definition of Done:**
- [ ] Fresh DB 可執行 `alembic upgrade head`
- [ ] 所有 14 個 tables 正確建立
- [ ] `alembic heads` 只顯示一個 head
- [ ] 001 (舊版) 已刪除或標記為 deprecated
- [ ] 文件已更新

**Rollback Plan:**
- 如果失敗：不繼續其他 WP，修正 migration

---

#### WP-11-05: Attendance 回歸測試實作

**Goal:** 實作並通過 8 個 Attendance 核心回歸測試

**Priority:** P0（建立測試基線）

**Duration:** 1-2 天

**Scope:**
- ✅ 新增 `backend/app/modules/attendance/tests/test_regression.py`
- ✅ 實作 8 個測試（依據 ATTENDANCE_REGRESSION_SPEC.md）
- ✅ 修正失敗的測試（如果業務邏輯有 bug）
- ⛔ 不新增功能

**Files Affected:**
- `backend/app/modules/attendance/tests/test_regression.py` (新增)
- `backend/app/modules/attendance/service.py` (可能修正)
- `backend/app/modules/attendance/policy_engine.py` (可能修正)

**Tests Required:**

**Test 1: NO_MATCH 未填原因 → 拒絕**
```python
def test_no_match_without_reason_rejected():
    # POST /api/attendance/mock-create
    # type=NO_MATCH, reason=None
    # Expected: 422
```

**Test 2: NO_MATCH 有原因 → PENDING**
```python
def test_no_match_with_reason_pending():
    # POST /api/attendance/mock-create
    # type=NO_MATCH, reason="Forgot to clock in"
    # Expected: 201, status=PENDING_APPROVAL
```

**Test 3: APPROVED → 推導正確**
```python
def test_approved_records_inference():
    # IN at 09:00, OUT at 18:00
    # Expected: 1 pair, work_time=9 hours
```

**Test 4: PENDING 不參與推導與日結**
```python
def test_pending_excluded_from_day_close():
    # APPROVED IN/OUT + PENDING IN
    # Expected: PENDING 不在 pairs
```

**Test 5: 21:00 日結缺卡正確**
```python
def test_day_close_missing_out():
    # IN at 09:00, no OUT
    # Expected: missing OUT detected
```

**Test 6: approve pending → 該日重算**
```python
def test_approve_pending_recalculates_day():
    # Approve PENDING record
    # Expected: day recalculated
```

**Test 7: customer_service 未指派公司 → 403**
```python
def test_customer_service_unassigned_company_403():
    # customer_service token, unassigned company
    # Expected: 403
```

**Test 8: OTP 一次性 + 強制改密碼**
```python
def test_otp_one_time_use_and_force_change():
    # Login with OTP
    # Expected: must_change_password=True
    # OTP reuse → 401
```

**Definition of Done:**
- [ ] 8/8 測試實作完成
- [ ] 8/8 測試通過
- [ ] 如果測試失敗，業務邏輯已修正
- [ ] 測試報告已產出

**Rollback Plan:**
- 如果測試發現嚴重 bug：記錄為 known issue，未來修正
- 如果測試規格不合理：與產品討論調整

---

#### WP-11-06: Auth 轉換 Batch 1 (attendance)

**Goal:** 將 attendance 模組轉換為 JWT + Actor

**Priority:** P0（核心業務）

**Duration:** 1 天

**Scope:**
- ✅ 修改 `attendance/api.py` 使用 `get_current_actor()`
- ✅ 加入 Scope 驗證
- ✅ 加入 Feature Gate
- ✅ 更新測試使用 JWT tokens
- ✅ 執行回歸測試確保不破壞
- ⛔ 不修改業務邏輯

**Files Affected:**
- `backend/app/modules/attendance/api.py` (修改)
- `backend/app/modules/attendance/tests/test_api.py` (修改)
- `backend/app/modules/attendance/tests/test_punch_api.py` (修改)

**Implementation Pattern:**

**Before (Header-based):**
```python
@router.post("/api/attendance/punch-in")
def punch_in(
    company_id: str = Depends(get_current_company_id),
    db: Session = Depends(get_db)
):
    return service.punch_in(company_id, db)
```

**After (JWT + Actor):**
```python
@router.post("/api/attendance/punch-in")
def punch_in(
    actor: Actor = Depends(get_current_actor),
    db: Session = Depends(get_db)
):
    # 1. Scope (已包含在 get_current_actor)
    # 2. Tenant Isolation (repo 自動處理)
    # 3. Feature Gate
    assert_feature_enabled(actor.company_id, "attendance.punch_in_out", db)
    
    return service.punch_in(actor.user_id, actor.company_id, db)
```

**Tests Required:**
```bash
# 更新測試使用 JWT
pytest app/modules/attendance/tests/test_api.py -v
pytest app/modules/attendance/tests/test_punch_api.py -v

# 執行回歸測試
pytest app/modules/attendance/tests/test_regression.py -v

# 完整測試
pytest app/modules/attendance/tests/ -v
```

**Definition of Done:**
- [ ] attendance/api.py 所有 endpoints 使用 JWT
- [ ] Scope 驗證已加入
- [ ] Feature Gate 已加入
- [ ] 所有測試通過（包含回歸測試）
- [ ] Header-based auth 已移除

**Rollback Plan:**
- Git revert 到轉換前
- 保留 Header 支援作為 fallback

---

#### WP-12: Auth 轉換 Batch 2-4 (audit, notifications, backup)

**Goal:** 將剩餘 3 個模組轉換為 JWT + Actor

**Priority:** P0

**Duration:** 1-2 天

**Scope:**
- ✅ 修改 audit/api.py
- ✅ 修改 notifications/api.py
- ✅ 修改 backup/api.py
- ✅ 加入 Scope + Feature Gate
- ✅ 更新所有測試
- ⛔ 不修改業務邏輯

**Files Affected:**
- `backend/app/modules/audit/api.py` (修改)
- `backend/app/modules/notifications/api.py` (修改)
- `backend/app/modules/backup/api.py` (修改)
- `backend/app/modules/*/tests/test_api.py` (修改)

**Batch 順序：**
1. audit（1 天）- 管理功能，中等風險
2. notifications（0.5 天）- 低風險
3. backup（0.5 天）- 管理功能，低頻使用

**Tests Required:**
```bash
# 每個模組轉換後執行
pytest app/modules/audit/tests/ -v
pytest app/modules/notifications/tests/ -v
pytest app/modules/backup/tests/ -v

# 完整回歸測試
pytest app/modules/attendance/tests/test_regression.py -v
```

**Definition of Done:**
- [ ] 3 個模組全部使用 JWT
- [ ] Scope 驗證已加入
- [ ] Feature Gate 已加入
- [ ] 所有測試通過
- [ ] Header-based auth 完全移除

**Rollback Plan:**
- 每個 batch 獨立 commit
- 可單獨 revert 問題模組

---

#### WP-13: 測試 DB 重建與驗證

**Goal:** 確保測試 DB schema 與 migration 一致

**Priority:** P1

**Duration:** 0.5 天

**Scope:**
- ✅ 比對測試 DB 與 fresh DB schema
- ✅ 重建測試 DB（如果不一致）
- ✅ 執行完整測試驗證
- ⛔ 不修改 migration

**Files Affected:**
- 測試 DB (attendance_test_db)
- `backend/conftest.py` (可能修改)

**Execution Steps:**
```bash
# 1. 匯出測試 DB schema
pg_dump -s -d attendance_test_db > /tmp/test_schema.sql

# 2. 建立 fresh DB
createdb attendance_fresh_baseline
alembic upgrade head
pg_dump -s -d attendance_fresh_baseline > /tmp/fresh_schema.sql

# 3. 比對
diff /tmp/test_schema.sql /tmp/fresh_schema.sql

# 4. 如果不一致，重建測試 DB
dropdb attendance_test_db
createdb attendance_test_db
alembic upgrade head

# 5. 執行測試
pytest -v
```

**Definition of Done:**
- [ ] 測試 DB schema 與 migration 一致
- [ ] 所有測試通過
- [ ] conftest.py 使用正確的 DB setup

**Rollback Plan:**
- 保留測試 DB 備份
- 可還原舊 DB

---

#### WP-14: API 文件補充

**Goal:** 為每個模組建立 API 文件

**Priority:** P2

**Duration:** 0.5 天

**Scope:**
- ✅ 為 7 個模組建立 docs.md
- ✅ 記錄業務邏輯
- ✅ 補充使用範例
- ⛔ 不修改程式碼

**Files Affected:**
- `backend/app/modules/attendance/docs.md` (新增)
- `backend/app/modules/audit/docs.md` (新增)
- `backend/app/modules/auth/docs.md` (新增)
- `backend/app/modules/backup/docs.md` (新增)
- `backend/app/modules/customer_service/docs.md` (新增)
- `backend/app/modules/notifications/docs.md` (新增)
- `backend/app/modules/tenants/docs.md` (新增)

**Template:**
```markdown
# [Module Name] API Documentation

## Overview
[模組用途]

## Business Logic
[業務流程說明]

## API Endpoints
詳見 OpenAPI: http://localhost:8000/docs

### [Endpoint Name]
- Method: POST
- Path: /api/[module]/[action]
- Auth: JWT (Actor)
- Scope: [required scope]
- Feature: [required feature]

## Examples
### [Use Case]
```bash
curl -X POST http://localhost:8000/api/[module]/[action] \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'
```

## Integration
- 發布事件：[event names]
- 訂閱事件：[event names]

## Error Codes
- 401: Unauthorized
- 403: Forbidden (Scope/Feature)
- 400: Business Rule Violation
- 422: Schema Validation Error
```

**Definition of Done:**
- [ ] 7 個 docs.md 完成
- [ ] 文件包含業務邏輯說明
- [ ] 文件包含使用範例
- [ ] 文件包含錯誤碼說明

---

### Phase 1 Summary

**完成後狀態：**
- SA 符合度：75% → 95%
- Auth 統一：2/7 → 7/7 模組使用 JWT
- Scope 驗證：2/7 → 7/7 模組實作
- Feature Gate：0/7 → 7/7 模組實作
- 回歸測試：0/8 → 8/8 通過
- API 文件：0/7 → 7/7 完成

**Gate 5 狀態：** ✅ COMPLETE

---
## Phase 2 — Core Backend Completion

**目標：** 實作剩餘的核心業務模組

**預估時間：** 6-8 週

**完成標準：**
- 7 個缺失模組全部實作
- 所有模組符合 SA v1.9 規範
- 所有模組有完整測試
- 所有模組有 API 文件

---

### Phase 2 Work Packages

#### WP-15: Reporting 模組

**Goal:** 實作報表模組（只讀彙總）

**Priority:** P1

**Duration:** 1-2 週

**Scope:**
- ✅ 建立 reporting 模組結構
- ✅ 實作報表查詢 API
- ✅ 實作資料彙總邏輯
- ⛔ 不修改其他模組資料

**Files to Create:**
- `backend/app/modules/reporting/__init__.py`
- `backend/app/modules/reporting/models.py`
- `backend/app/modules/reporting/repo.py`
- `backend/app/modules/reporting/service.py`
- `backend/app/modules/reporting/api.py`
- `backend/app/modules/reporting/docs.md`
- `backend/app/modules/reporting/tests/`

**Key Features:**
- 出勤報表（日/週/月）
- 請假統計
- 加班統計
- 異常報表
- 匯出功能（CSV/Excel）

**SA v1.9 Compliance:**
- ✅ 只讀模組（不修改資料）
- ✅ 使用 JWT + Actor
- ✅ Scope 驗證
- ✅ Feature Gate
- ✅ Tenant Isolation

**Definition of Done:**
- [ ] 模組結構完整
- [ ] 所有報表 API 實作
- [ ] 測試覆蓋率 > 80%
- [ ] API 文件完成

---

#### WP-16: Locations 模組

**Goal:** 實作地點管理模組

**Priority:** P1

**Duration:** 1 週

**Scope:**
- ✅ 建立 locations 模組
- ✅ 實作地點 CRUD
- ✅ 實作地理圍欄驗證
- ⛔ 不修改 attendance 模組

**Files to Create:**
- `backend/alembic/versions/XXX_create_locations.py`
- `backend/app/modules/locations/` (完整模組)

**Database Schema:**
```sql
CREATE TABLE locations (
    id UUID PRIMARY KEY,
    company_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    radius_meters INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (company_id) REFERENCES tenants(id) ON DELETE CASCADE
);
CREATE INDEX idx_locations_company_id ON locations(company_id);
```

**Key Features:**
- 地點 CRUD
- 地理圍欄驗證
- 地點群組管理

**Definition of Done:**
- [ ] Migration 完成
- [ ] CRUD API 完成
- [ ] 地理圍欄邏輯實作
- [ ] 測試覆蓋率 > 80%

---

#### WP-17: Approvals 模組

**Goal:** 實作審批流程模組

**Priority:** P1

**Duration:** 2 週

**Scope:**
- ✅ 建立 approvals 模組
- ✅ 實作審批流程引擎
- ✅ 整合 attendance/leave 模組
- ⛔ 不破壞現有審批邏輯

**Files to Create:**
- `backend/alembic/versions/XXX_create_approvals.py`
- `backend/app/modules/approvals/` (完整模組)

**Database Schema:**
```sql
CREATE TABLE approval_workflows (
    id UUID PRIMARY KEY,
    company_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- attendance, leave, overtime
    steps JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE approval_requests (
    id UUID PRIMARY KEY,
    company_id VARCHAR(255) NOT NULL,
    workflow_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    current_step INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL, -- pending, approved, rejected
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (workflow_id) REFERENCES approval_workflows(id)
);
```

**Key Features:**
- 多層級審批流程
- 審批歷史記錄
- 審批通知
- 審批統計

**Definition of Done:**
- [ ] Migration 完成
- [ ] 審批引擎實作
- [ ] 與 attendance 整合
- [ ] 測試覆蓋率 > 80%

---

#### WP-18: Leave 模組

**Goal:** 實作請假管理模組

**Priority:** P1

**Duration:** 2 週

**Scope:**
- ✅ 建立 leave 模組
- ✅ 實作請假 CRUD
- ✅ 整合 approvals 模組
- ✅ 整合 accrual 模組
- ⛔ 不修改 attendance 推導邏輯

**Files to Create:**
- `backend/alembic/versions/XXX_create_leave.py`
- `backend/app/modules/leave/` (完整模組)

**Database Schema:**
```sql
CREATE TABLE leave_types (
    id UUID PRIMARY KEY,
    company_id VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) NOT NULL,
    requires_approval BOOLEAN DEFAULT TRUE,
    affects_attendance BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE leave_requests (
    id UUID PRIMARY KEY,
    company_id VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL,
    leave_type_id UUID NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    days DECIMAL(4,2) NOT NULL,
    reason TEXT,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (leave_type_id) REFERENCES leave_types(id)
);
```

**Key Features:**
- 請假類型管理
- 請假申請/審批
- 請假額度檢查
- 請假統計

**Definition of Done:**
- [ ] Migration 完成
- [ ] CRUD API 完成
- [ ] 與 approvals 整合
- [ ] 與 accrual 整合
- [ ] 測試覆蓋率 > 80%

---

#### WP-19: Accrual 模組

**Goal:** 實作假期額度管理模組

**Priority:** P1

**Duration:** 1-2 週

**Scope:**
- ✅ 建立 accrual 模組
- ✅ 實作額度 ledger
- ✅ 實作額度計算引擎
- ⛔ 不修改 leave 模組

**Files to Create:**
- `backend/alembic/versions/XXX_create_accrual.py`
- `backend/app/modules/accrual/` (完整模組)

**Database Schema:**
```sql
CREATE TABLE accrual_policies (
    id UUID PRIMARY KEY,
    company_id VARCHAR(255) NOT NULL,
    leave_type_id UUID NOT NULL,
    accrual_rate DECIMAL(6,2) NOT NULL,
    accrual_period VARCHAR(20) NOT NULL, -- monthly, yearly
    max_balance DECIMAL(6,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE accrual_ledger (
    id UUID PRIMARY KEY,
    company_id VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL,
    leave_type_id UUID NOT NULL,
    transaction_type VARCHAR(20) NOT NULL, -- accrual, usage, adjustment
    amount DECIMAL(6,2) NOT NULL,
    balance DECIMAL(6,2) NOT NULL,
    reference_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Key Features:**
- 額度累積規則
- 額度使用記錄
- 額度查詢
- 額度調整

**Definition of Done:**
- [ ] Migration 完成
- [ ] Ledger 實作
- [ ] 計算引擎實作
- [ ] 測試覆蓋率 > 80%

---

#### WP-20: Vehicles 模組

**Goal:** 實作車輛管理模組

**Priority:** P2

**Duration:** 1 週

**Scope:**
- ✅ 建立 vehicles 模組
- ✅ 實作車輛 CRUD
- ⛔ 不實作派車邏輯（WP-21）

**Files to Create:**
- `backend/alembic/versions/XXX_create_vehicles.py`
- `backend/app/modules/vehicles/` (完整模組)

**Definition of Done:**
- [ ] Migration 完成
- [ ] CRUD API 完成
- [ ] 測試覆蓋率 > 80%

---

#### WP-21: Dispatch 模組

**Goal:** 實作派車管理模組

**Priority:** P2

**Duration:** 1-2 週

**Scope:**
- ✅ 建立 dispatch 模組
- ✅ 實作派車邏輯
- ✅ 整合 vehicles 模組
- ✅ 整合 attendance 模組

**Files to Create:**
- `backend/alembic/versions/XXX_create_dispatch.py`
- `backend/app/modules/dispatch/` (完整模組)

**Key Features:**
- 派車申請/審批
- 車輛使用記錄
- 派車統計

**Definition of Done:**
- [ ] Migration 完成
- [ ] 派車邏輯實作
- [ ] 與 attendance 整合
- [ ] 測試覆蓋率 > 80%

---

### Phase 2 Summary

**完成後狀態：**
- 模組完成度：7/14 → 14/14 (100%)
- 所有模組符合 SA v1.9
- 所有模組有完整測試
- 所有模組有 API 文件

---

## Phase 3 — SaaS Infrastructure

**目標：** 強化 SaaS 基礎設施

**預估時間：** 2-3 週

**完成標準：**
- Tenant 管理完善
- Feature Tier 系統完整
- Backup/Restore 自動化

---

### Phase 3 Work Packages

#### WP-22: Tenant 管理強化

**Goal:** 強化 Tenant 管理功能

**Duration:** 1 週

**Scope:**
- ✅ Tenant 生命週期管理
- ✅ Tenant 配額管理
- ✅ Tenant 使用統計
- ✅ Tenant 自助管理 API

**Key Features:**
- Tenant 啟用/停用
- Tenant 配額限制（使用者數、儲存空間）
- Tenant 使用統計（API 呼叫、儲存使用）
- Tenant 設定管理

**Definition of Done:**
- [ ] 生命週期 API 完成
- [ ] 配額系統實作
- [ ] 統計 API 完成
- [ ] 測試覆蓋率 > 80%

---

#### WP-23: Feature Tier 系統

**Goal:** 實作功能分級系統

**Duration:** 1 週

**Scope:**
- ✅ 定義 Feature Tiers (Free/Pro/Enterprise)
- ✅ 實作 Tier 管理 API
- ✅ 實作 Tier 升級/降級邏輯
- ✅ 整合 Billing（未來）

**Feature Tiers:**

**Free Tier:**
- attendance.punch_in_out
- attendance.basic_reports
- 最多 10 個使用者

**Pro Tier:**
- Free Tier +
- attendance.policy_engine
- attendance.split_shift
- leave.management
- 最多 100 個使用者

**Enterprise Tier:**
- Pro Tier +
- attendance.advanced_reports
- approvals.multi_level
- dispatch.management
- 無使用者限制

**Definition of Done:**
- [ ] Tier 定義完成
- [ ] Tier 管理 API 完成
- [ ] 升級/降級邏輯實作
- [ ] 測試覆蓋率 > 80%

---

#### WP-24: Backup/Restore 自動化

**Goal:** 實作自動化備份/還原

**Duration:** 1 週

**Scope:**
- ✅ 排程備份
- ✅ 備份版本管理
- ✅ 一鍵還原
- ✅ 備份驗證

**Key Features:**
- 自動排程備份（每日/每週）
- 備份版本保留策略
- 備份完整性驗證
- 還原前預覽

**Definition of Done:**
- [ ] 排程系統實作
- [ ] 版本管理實作
- [ ] 驗證邏輯實作
- [ ] 測試覆蓋率 > 80%

---

### Phase 3 Summary

**完成後狀態：**
- SaaS 基礎設施完整
- 可支援多租戶生產環境
- 可支援功能分級計費

---

## Phase 4 — Frontend

**目標：** 實作前端 UI

**預估時間：** 8-10 週

**完成標準：**
- Admin UI 完成
- Employee UI 完成
- Mobile responsive
- 所有 API 整合完成

---

### Frontend Start Criteria

**必須滿足以下條件才能開始 Frontend 開發：**

#### 技術條件
- [ ] Phase 1 完成（Architecture Alignment）
- [ ] Phase 2 完成（Core Backend Completion）
- [ ] 所有 API 有 OpenAPI 文件
- [ ] 所有 API 測試通過
- [ ] Backend 可穩定運行

#### API 穩定性
- [ ] API 合約凍結（不再變更 request/response schema）
- [ ] 錯誤碼統一且文件化
- [ ] API 效能測試通過

#### 開發環境
- [ ] Backend dev server 可穩定運行
- [ ] 測試資料可快速建立
- [ ] API mock server 可用（選擇性）

#### 文件完整性
- [ ] 所有 API 有使用範例
- [ ] 所有業務流程有文件
- [ ] UI/UX 設計稿完成

---

### Phase 4 Work Packages

#### WP-25: Frontend 架構建立

**Goal:** 建立 Frontend 專案架構

**Duration:** 1 週

**Scope:**
- ✅ 選擇技術棧（React/Vue/Angular）
- ✅ 建立專案結構
- ✅ 設定開發環境
- ✅ 整合 API client

**Recommended Stack:**
- Framework: React + TypeScript
- State Management: Redux Toolkit / Zustand
- UI Library: Material-UI / Ant Design
- API Client: Axios + React Query
- Routing: React Router
- Form: React Hook Form + Zod

**Definition of Done:**
- [ ] 專案建立完成
- [ ] 開發環境可運行
- [ ] API client 整合完成
- [ ] 基礎元件庫建立

---

#### WP-26: Admin UI - Tenant 管理

**Goal:** 實作 Admin 租戶管理介面

**Duration:** 1 週

**Scope:**
- ✅ Tenant 列表
- ✅ Tenant 建立/編輯
- ✅ Tenant 啟用/停用
- ✅ Tenant 配額管理

**Definition of Done:**
- [ ] 所有頁面完成
- [ ] API 整合完成
- [ ] UI 測試通過

---

#### WP-27: Admin UI - 使用者管理

**Goal:** 實作 Admin 使用者管理介面

**Duration:** 1 週

**Scope:**
- ✅ 使用者列表
- ✅ 使用者建立/編輯
- ✅ 角色指派
- ✅ 權限管理

**Definition of Done:**
- [ ] 所有頁面完成
- [ ] API 整合完成
- [ ] UI 測試通過

---

#### WP-28: Admin UI - 功能管理

**Goal:** 實作 Admin 功能管理介面

**Duration:** 1 週

**Scope:**
- ✅ Feature Flags 管理
- ✅ Entitlements 設定
- ✅ Tier 管理

**Definition of Done:**
- [ ] 所有頁面完成
- [ ] API 整合完成
- [ ] UI 測試通過

---

#### WP-29: Employee UI - 打卡功能

**Goal:** 實作員工打卡介面

**Duration:** 2 週

**Scope:**
- ✅ Punch In/Out
- ✅ 當前狀態顯示
- ✅ 打卡歷史
- ✅ 地理位置驗證

**Definition of Done:**
- [ ] 所有頁面完成
- [ ] API 整合完成
- [ ] 地理位置功能正常
- [ ] Mobile responsive

---

#### WP-30: Employee UI - 請假功能

**Goal:** 實作員工請假介面

**Duration:** 1 週

**Scope:**
- ✅ 請假申請
- ✅ 請假歷史
- ✅ 額度查詢
- ✅ 審批狀態追蹤

**Definition of Done:**
- [ ] 所有頁面完成
- [ ] API 整合完成
- [ ] UI 測試通過

---

#### WP-31: Employee UI - 報表功能

**Goal:** 實作員工報表介面

**Duration:** 1 週

**Scope:**
- ✅ 個人出勤報表
- ✅ 請假統計
- ✅ 加班統計
- ✅ 匯出功能

**Definition of Done:**
- [ ] 所有頁面完成
- [ ] API 整合完成
- [ ] 匯出功能正常

---

### Phase 4 Summary

**完成後狀態：**
- Admin UI 完整
- Employee UI 完整
- Mobile responsive
- 可進行 UAT

---

## Phase 5 — External Integration

**目標：** 實作外部系統整合

**預估時間：** 4-6 週

**完成標準：**
- 裝置整合完成
- 薪資匯出完成
- Webhook 系統完成

---

### Phase 5 Work Packages

#### WP-32: 裝置整合

**Goal:** 整合打卡裝置

**Duration:** 2 週

**Scope:**
- ✅ 裝置 API 設計
- ✅ 裝置註冊/配對
- ✅ 裝置資料同步
- ✅ 裝置管理介面

**Definition of Done:**
- [ ] 裝置 API 完成
- [ ] 配對流程實作
- [ ] 同步邏輯實作
- [ ] 測試覆蓋率 > 80%

---

#### WP-33: 薪資匯出

**Goal:** 實作薪資系統匯出

**Duration:** 1 週

**Scope:**
- ✅ 薪資資料彙總
- ✅ 匯出格式定義
- ✅ 匯出 API
- ✅ 匯出排程

**Definition of Done:**
- [ ] 匯出 API 完成
- [ ] 格式支援（CSV/Excel）
- [ ] 排程系統實作
- [ ] 測試覆蓋率 > 80%

---

#### WP-34: Webhook 系統

**Goal:** 實作 Webhook 通知系統

**Duration:** 2 週

**Scope:**
- ✅ Webhook 註冊管理
- ✅ 事件訂閱機制
- ✅ Webhook 發送邏輯
- ✅ 重試機制

**Key Events:**
- attendance.punch_in
- attendance.punch_out
- leave.approved
- leave.rejected

**Definition of Done:**
- [ ] Webhook 管理 API 完成
- [ ] 發送邏輯實作
- [ ] 重試機制實作
- [ ] 測試覆蓋率 > 80%

---

### Phase 5 Summary

**完成後狀態：**
- 可整合外部裝置
- 可匯出薪資資料
- 可接收 Webhook 通知

---

## 4. Production Readiness Checklist

### 4.1 功能完整性

- [ ] 所有 Phase 1-3 完成
- [ ] 所有核心模組實作
- [ ] 所有 API 測試通過
- [ ] 所有回歸測試通過

---

### 4.2 效能指標

- [ ] API 回應時間 < 200ms (P95)
- [ ] 資料庫查詢優化
- [ ] 索引建立完整
- [ ] 快取策略實作

---

### 4.3 安全性

- [ ] JWT 驗證完整
- [ ] Scope 驗證統一
- [ ] Feature Gate 實作
- [ ] SQL Injection 防護
- [ ] XSS 防護
- [ ] CSRF 防護
- [ ] Rate Limiting

---

### 4.4 可靠性

- [ ] 錯誤處理完整
- [ ] 日誌記錄完整
- [ ] 監控系統建立
- [ ] 告警機制建立
- [ ] Backup 自動化
- [ ] Disaster Recovery 計畫

---

### 4.5 可維護性

- [ ] 程式碼文件完整
- [ ] API 文件完整
- [ ] 部署文件完整
- [ ] 運維手冊完整
- [ ] 測試覆蓋率 > 80%

---

### 4.6 合規性

- [ ] SA v1.9 符合度 > 95%
- [ ] Tenant Isolation 驗證
- [ ] 資料隱私保護
- [ ] Audit Log 完整

---

## 5. Risk Management

### 5.1 技術風險

| 風險 | 機率 | 影響 | 緩解措施 |
|------|------|------|----------|
| 回歸測試失敗 | 中 | 高 | 預留 buffer time，準備修正計畫 |
| Auth 轉換破壞功能 | 中 | 高 | 批次轉換，保留 fallback |
| Migration 失敗 | 低 | 高 | 先驗證，再執行 |
| 效能問題 | 中 | 中 | 效能測試，優化查詢 |
| 整合問題 | 中 | 中 | 早期整合測試 |

---

### 5.2 時程風險

| 風險 | 機率 | 影響 | 緩解措施 |
|------|------|------|----------|
| Phase 1 延誤 | 中 | 高 | 預留 buffer，調整優先順序 |
| Phase 2 延誤 | 中 | 中 | 分批交付，降低風險 |
| 資源不足 | 低 | 高 | 提前規劃，外部支援 |

---

## 6. Success Metrics

### 6.1 開發指標

| 指標 | 目標 | 測量方式 |
|------|------|----------|
| SA 符合度 | > 95% | GAP 分析 |
| 測試覆蓋率 | > 80% | pytest --cov |
| API 文件完整度 | 100% | 人工檢查 |
| 程式碼品質 | A 級 | SonarQube |

---

### 6.2 效能指標

| 指標 | 目標 | 測量方式 |
|------|------|----------|
| API 回應時間 (P95) | < 200ms | APM 工具 |
| 資料庫查詢時間 (P95) | < 50ms | DB 監控 |
| 並發使用者 | > 1000 | 壓力測試 |

---

### 6.3 業務指標

| 指標 | 目標 | 測量方式 |
|------|------|----------|
| 系統可用性 | > 99.9% | 監控系統 |
| 錯誤率 | < 0.1% | 日誌分析 |
| 使用者滿意度 | > 4.5/5 | 問卷調查 |

---

## 7. Timeline Summary

### 7.1 Overall Timeline

```
Phase 1: Architecture Alignment     [████████░░] 2-3 週   (Week 1-3)
Phase 2: Core Backend Completion    [░░░░░░░░░░] 6-8 週   (Week 4-11)
Phase 3: SaaS Infrastructure        [░░░░░░░░░░] 2-3 週   (Week 12-14)
Phase 4: Frontend                   [░░░░░░░░░░] 8-10 週  (Week 15-24)
Phase 5: External Integration       [░░░░░░░░░░] 4-6 週   (Week 25-30)

Total: 22-30 週 (5-7 個月)
```

---

### 7.2 Critical Path

```
WP-11-04B (Migration 驗證) → 
WP-11-05 (回歸測試) → 
WP-11-06 (Auth 轉換 Batch 1) → 
WP-12 (Auth 轉換 Batch 2-4) → 
Phase 2 (Core Backend) → 
Phase 3 (SaaS Infrastructure) → 
Phase 4 (Frontend) → 
Phase 5 (External Integration) → 
Production
```

---

### 7.3 Milestones

| Milestone | 目標日期 | 驗收標準 |
|-----------|---------|----------|
| **M1: Gate 5 完成** | Week 3 | Phase 1 完成，SA 符合度 > 95% |
| **M2: Backend 完成** | Week 11 | Phase 2 完成，所有模組實作 |
| **M3: SaaS 就緒** | Week 14 | Phase 3 完成，可支援多租戶 |
| **M4: Frontend 完成** | Week 24 | Phase 4 完成，可進行 UAT |
| **M5: 生產就緒** | Week 30 | Phase 5 完成，通過所有檢查 |

---

## 8. Approval & Sign-off

**路線圖狀態：** ✅ APPROVED

**核准者：**
- 架構師：_________________
- 技術負責人：_________________
- 產品負責人：_________________
- 專案經理：_________________

**核准日期：** 2026-03-04

**下一次審查：** Phase 1 完成後

---

## 9. Document Control

**文件版本：** 1.0  
**建立日期：** 2026-03-04  
**最後更新：** 2026-03-04  
**維護者：** 架構團隊

**變更歷史：**
- v1.0 (2026-03-04): 初版建立

**相關文件：**
- SA_MODULE_SPEC v1.9
- SA_REALITY_GAP_REPORT.md
- ARCHITECTURE_FIX_DECISION.md
- GATE_PROGRESS_TRACKER.md

---

**END OF ROADMAP**
