# Master Development Roadmap v2

**系統名稱：** Attendance SaaS System  
**架構版本：** SA_MODULE_SPEC v1.9 (Platform-First Architecture)  
**文件版本：** 2.0  
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

**v2 變更：**
- ✅ 移除週次時間線，改用 Work Package 流程
- ✅ 調整 Frontend 預估時間：8-10 週 → 3-4 週
- ✅ 將 Vehicles/Dispatch 移至 Phase 6: Extensions
- ✅ Frontend 啟動條件新增 Tenant Isolation 驗證

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
6. Tenant Isolation 驗證完成

---

### 1.2 Architecture Compliance

**當前符合度：** 75% (17/40 完全符合，11/40 部分符合)

**目標符合度：** > 95%

**達成條件：** Phase 1 完成後

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
| **reporting** | P1 | Phase 2 | 報表模組 |
| **vehicles** | P2 | Phase 6 | 車輛管理（延後至擴充階段）|
| **dispatch** | P2 | Phase 6 | 派車管理（延後至擴充階段）|

**核心模組：** 5/12 未實作（Phase 2 目標）  
**擴充模組：** 2/14 未實作（Phase 6 目標）

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
- ❌ 5 個核心模組未實作
- ❌ 2 個擴充模組未實作
- ❌ API 文件 (docs.md)
- ❌ Tenant Isolation 測試 (部分)

---

## 3. Execution Phases

### Phase Overview

| Phase | 名稱 | 依賴關係 | 狀態 |
|-------|------|----------|------|
| **Phase 1** | Architecture Alignment | - | 🎯 NEXT |
| **Phase 2** | Core Backend Completion | Phase 1 | ⏳ PLANNED |
| **Phase 3** | SaaS Infrastructure | Phase 2 | ⏳ PLANNED |
| **Phase 4** | Frontend | Phase 1, 2, 3 | ⏳ PLANNED |
| **Phase 5** | External Integration | Phase 2, 3 | ⏳ PLANNED |
| **Phase 6** | Extensions | Phase 2, 3 | ⏳ OPTIONAL |

**關鍵路徑：** Phase 1 → Phase 2 → Phase 3 → Phase 4  
**平行開發：** Phase 5, 6 可與 Phase 4 平行進行

---

## Phase 1 — Architecture Alignment

**目標：** 將現有系統對齊 SA v1.9 規範

**完成標準：**
- SA 符合度 > 95%
- 8 個回歸測試通過
- 所有模組使用 JWT
- Scope 驗證統一實作
- Feature Gate 套用到所有 API
- Tenant Isolation 驗證完成

**依賴關係：** 無（可立即開始）

---

### Phase 1 Work Packages

#### WP-11-04B: Migration Chain 驗證

**Goal:** 確保 migration chain 可在 fresh DB 執行

**Priority:** P0（阻斷其他工作）

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

**依賴關係：** 無  
**後續 WP：** WP-11-05

---

#### WP-11-05: Attendance 回歸測試實作

**Goal:** 實作並通過 8 個 Attendance 核心回歸測試

**Priority:** P0（建立測試基線）

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

**依賴關係：** WP-11-04B  
**後續 WP：** WP-11-06

---

#### WP-11-06: Auth 轉換 Batch 1 (attendance)

**Goal:** 將 attendance 模組轉換為 JWT + Actor

**Priority:** P0（核心業務）

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

**依賴關係：** WP-11-05  
**後續 WP：** WP-12

---

#### WP-12: Auth 轉換 Batch 2-4 (audit, notifications, backup)

**Goal:** 將剩餘 3 個模組轉換為 JWT + Actor

**Priority:** P0

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
1. audit - 管理功能，中等風險
2. notifications - 低風險
3. backup - 管理功能，低頻使用

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

**依賴關係：** WP-11-06  
**後續 WP：** WP-13

---

#### WP-13: Tenant Isolation 驗證測試

**Goal:** 實作並通過 Tenant Isolation 驗證測試

**Priority:** P0（Frontend 啟動條件）

**Scope:**
- ✅ 建立 Tenant Isolation 測試套件
- ✅ 驗證跨租戶資料隔離
- ✅ 驗證 Scope 驗證機制
- ✅ 驗證 Backup/Restore 隔離
- ⛔ 不修改業務邏輯

**Files to Create:**
- `backend/app/tests/test_tenant_isolation.py` (新增)

**Tests Required:**

**Test 1: A company 無法讀取 B company**
```python
def test_company_a_cannot_read_company_b_data():
    # Company A user token
    # Query Company B data
    # Expected: 403 or empty result
```

**Test 2: 錯誤 company_id 寫入被拒**
```python
def test_wrong_company_id_write_rejected():
    # Company A user token
    # Try to write with company_id = B
    # Expected: company_id overwritten to A
```

**Test 3: 無 membership → 403**
```python
def test_no_membership_returns_403():
    # User without membership
    # Try to access company data
    # Expected: 403
```

**Test 4: Restore 不污染其他 company**
```python
def test_restore_does_not_pollute_other_companies():
    # Restore Company A data
    # Verify Company B data unchanged
    # Expected: Company B data intact
```

**Test 5: customer_service 只能存取已指派公司**
```python
def test_customer_service_scope_enforcement():
    # customer_service token
    # Try to access unassigned company
    # Expected: 403
```

**Definition of Done:**
- [ ] 5/5 測試實作完成
- [ ] 5/5 測試通過
- [ ] 測試報告已產出
- [ ] 文件已更新

**Rollback Plan:**
- 如果測試失敗：記錄為 P0 bug，必須修正後才能繼續

**依賴關係：** WP-12  
**後續 WP：** WP-14

---

#### WP-14: 測試 DB 重建與驗證

**Goal:** 確保測試 DB schema 與 migration 一致

**Priority:** P1

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

**依賴關係：** WP-13  
**後續 WP：** WP-15

---

#### WP-15: API 文件補充

**Goal:** 為每個模組建立 API 文件

**Priority:** P2

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

**依賴關係：** WP-14  
**後續 WP：** Phase 2

---

### Phase 1 Summary

**完成後狀態：**
- SA 符合度：75% → 95%
- Auth 統一：2/7 → 7/7 模組使用 JWT
- Scope 驗證：2/7 → 7/7 模組實作
- Feature Gate：0/7 → 7/7 模組實作
- 回歸測試：0/8 → 8/8 通過
- Tenant Isolation 測試：0/5 → 5/5 通過
- API 文件：0/7 → 7/7 完成

**Gate 5 狀態：** ✅ COMPLETE

**可啟動：** Phase 2, Phase 4 (Frontend)

---
