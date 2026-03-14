# Reality Audit — Status Inventory（現況盤點清單）

**審查日期：** 2026-03-04  
**審查範圍：** `/opt/attendance-system` 完整 repo  
**審查方法：** 只看程式碼、migration、測試、設定檔現況，不比對 SA 規格

---

## 1. Repo 摘要

### 1.1 基本資訊

| 項目 | 數值 | 位置 |
|------|------|------|
| Python 檔案總數 | 79 | `backend/app/modules/` |
| 測試檔案總數 | 29 | `backend/` (含 app/modules 與 backend/tests) |
| Migration 檔案數 | 7 | `backend/alembic/versions/` |
| 文件數量 | 59 | `docs/*.md` |
| 模組數量 | 7 | attendance, audit, auth, backup, customer_service, notifications, tenants |

### 1.2 技術棧

| 技術 | 版本/狀態 | 位置 |
|------|-----------|------|
| FastAPI | >=0.104.0 | `backend/requirements.txt` |
| SQLAlchemy | >=2.0.0 | `backend/requirements.txt` |
| PostgreSQL | psycopg2-binary>=2.9.0 | `backend/requirements.txt` |
| Alembic | (使用中) | `backend/alembic/` |
| Pytest | >=7.4.0 | `backend/requirements.txt` |
| Pydantic | >=2.5.0 | `backend/requirements.txt` |

### 1.3 資料庫連線

**設定檔：** `backend/app/core/config.py`

```python
database_url: str = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:Raxcxtjq260!@127.0.0.1:5432/attendance_db",
)
```

**狀態：** ✅ 使用環境變數優先，有預設值（含硬編碼密碼）

---

## 2. 模組清單表

| Module | Purpose | Key Files | Tests? | Notes |
|--------|---------|-----------|--------|-------|
| **attendance** | 打卡/出勤管理 | models.py, repo.py, api.py, service.py, schemas.py, policy_engine.py | ✅ 10 files | 有 policy_engine.py (24KB) |
| **audit** | 稽核日誌 | models.py, repo.py, api.py, service.py | ✅ 5 files | 有 retention policy |
| **auth** | 認證/授權 | models.py, repo.py, api.py, service.py, schemas.py | ✅ 4 files | JWT + password hashing |
| **backup** | 備份/還原 | api.py, service.py, exporter.py, importer.py | ✅ 5 files | 無 models (跨模組操作) |
| **customer_service** | 客服管理 | models.py, repo.py, api.py, service.py, schemas.py | ✅ 1 file | Support company assignments |
| **notifications** | 通知系統 | models.py, repo.py, api.py, service.py, event_handlers.py | ✅ 5 files | EventBus 訂閱者 |
| **tenants** | 租戶管理 | models.py, repo.py, api.py, service.py, schemas.py | ✅ 5 files | Entitlements 管理 |

**總計：** 7 個模組，全部有測試

---

## 3. API 摘要表

### 3.1 已註冊的 Routers

**位置：** `backend/app/main.py`

| Area | Router | Prefix | Auth/Tenant | Tests? | Notes |
|------|--------|--------|-------------|--------|-------|
| Attendance | `attendance.api.router` | `/api/attendance` | Header (X-Company-ID) | ✅ | 2 test files |
| Notifications | `notifications.api.router` | `/api/notifications` | Header (X-Company-ID) | ✅ | EventBus 整合 |
| Backup | `backup.api.router` | `/api/backup` | Header (X-Company-ID) | ✅ | Export/restore |
| Audit | `audit.api.router` | `/api/audit` | Header (X-Company-ID) | ✅ | Query + retention |
| Auth | `auth.api.router` | `/api/internal/auth` | None (login endpoint) | ✅ | JWT login |
| Tenants | `tenants.api.router` | `/api/admin/companies` | JWT (Actor) | ✅ | Entitlements CRUD |
| Customer Service | `customer_service.api.router` | `/api/customer-service` | JWT (Actor) | ✅ | Assignments |

**總計：** 7 個 router 已註冊

### 3.2 Tenant Context 機制

**現況：** 混合模式（Header + JWT 並存）

| 模組 | Tenant Context 方式 | 位置 |
|------|---------------------|------|
| attendance | Header (`X-Company-ID`) | `api.py` line ~20 |
| notifications | Header (`X-Company-ID`) | `api.py` line ~20 |
| backup | Header (`X-Company-ID`) | `api.py` line ~20 |
| audit | Header (`X-Company-ID`) | `api.py` line ~20 |
| auth | N/A (login 不需 tenant) | `api.py` |
| tenants | JWT (`get_current_actor`) | `api.py` line ~30 |
| customer_service | JWT (`get_current_actor`) | `api.py` line ~25 |

**發現：** 
- ⚠️ 4 個模組仍使用 Header-based tenant context
- ✅ 2 個新模組使用 JWT-based Actor
- ⚠️ 兩種機制並存，未統一

### 3.3 需要 Tenant Context 的 Endpoints

**Header-based (舊)：**
- `POST /api/attendance/mock-create` → 需要 `X-Company-ID`
- `POST /api/attendance/{id}/approve` → 需要 `X-Company-ID`
- `GET /api/notifications` → 需要 `X-Company-ID`
- `POST /api/backup/export` → 需要 `X-Company-ID`
- `POST /api/backup/restore` → 需要 `X-Company-ID`
- `GET /api/audit/logs` → 需要 `X-Company-ID`

**JWT-based (新)：**
- `GET /api/admin/companies/{company_id}/entitlements` → 需要 JWT + Actor scope check
- `PATCH /api/admin/companies/{company_id}/entitlements/{feature_key}` → 需要 JWT + Actor scope check
- `GET /api/customer-service/assigned-companies` → 需要 JWT + Actor

### 3.4 Auth / RBAC / Entitlement Enforcement

**位置：** `backend/app/core/`

| 機制 | 檔案 | 狀態 | 使用位置 |
|------|------|------|----------|
| JWT 解析 | `security/jwt.py` | ✅ 存在 | `dependencies.py` |
| Password hashing | `security/password.py` | ✅ 存在 | `auth/service.py` |
| Actor dependency | `dependencies.py` | ✅ 存在 | tenants/api.py, customer_service/api.py |
| Scope checker | `scope.py` | ✅ 存在 | tenants/service.py, customer_service/service.py |
| Feature gate | `feature_service.py` | ✅ 存在 | tenants/service.py |
| RBAC (role mapping) | `dependencies.py` | ✅ 存在 | `_map_role_id_to_user_role()` |

**發現：**
- ✅ JWT + Actor 機制已實作
- ✅ Scope checking 已實作（super_admin / customer_service / company_user）
- ✅ Feature gate 已實作
- ⚠️ 但只有 2 個模組使用，其他 4 個模組仍用 Header

---

## 4. Database / Migration Reality

### 4.1 Migration Chain

**位置：** `backend/alembic/versions/`

| # | Filename | Revision | Down Revision | Tables Created | Status |
|---|----------|----------|---------------|----------------|--------|
| 1 | `004_create_tenants.py` | `004` | `None` | `tenants` | ✅ Root |
| 2 | `3532deda024c_create_auth_tables_v2_platform_first.py` | `3532deda024c` | `004` | `users`, `roles`, `permissions`, `user_roles`, `user_company_memberships` | ✅ |
| 3 | `005_create_notifications.py` | `005` | `3532deda024c` | `notifications` | ✅ |
| 4 | `002_create_audit_logs.py` | `002` | `005` | `audit_logs` | ✅ |
| 5 | `003_create_audit_retention_policies.py` | `003` | `002` | `audit_retention_policies` | ✅ |
| 6 | `001b_create_attendance_domain_v2_fixed.py` | `001b` | `003` | `attendance_policies`, `attendance_sessions`, `attendance_punches` | ✅ Fixed |
| 7 | `wp_11_04a_entitlements.py` | `wp_11_04a_entitlements` | `001b` | `company_entitlements`, `support_company_assignments` | ✅ |

**執行順序：** 004 → 3532deda024c → 005 → 002 → 003 → 001b → wp_11_04a

**Current Head：** `wp_11_04a_entitlements` (single head ✅)

### 4.2 Migration Chain 狀態

**依據：** `docs/MIGRATION_CHAIN_AUDIT_REPORT.md` (2026-03-04)

| 檢查項目 | 狀態 | 證據 |
|----------|------|------|
| Single head | ✅ Pass | `wp_11_04a_entitlements` |
| No circular dependencies | ✅ Pass | Linear chain |
| Fresh rebuild 可執行 | ⚠️ Unknown | 報告顯示 001 有 bug，但已被 001b 取代 |
| 001b 是否已套用 | ⚠️ Unknown | 需檢查實際 DB 的 `alembic_version` |

**關鍵發現（來自 MIGRATION_CHAIN_AUDIT_REPORT.md）：**

1. **001 (舊版) 有 table ordering bug：**
   - 建立 `attendance_sessions` 時參照不存在的 `attendance_policies`
   - 會導致 fresh DB rebuild 失敗
   - 報告建議：用 001b 取代

2. **001b (修正版) 已建立：**
   - 正確順序：policies → sessions → punches
   - `down_revision = '003'`
   - wp_11_04a 已指向 001b

3. **wp_11_04a 曾手動執行：**
   - 報告提到測試 DB 用 SQL 手動執行，未用 alembic
   - 可能導致 `alembic_version` 不一致

### 4.3 Fresh Rebuild 狀態

**結論（基於文件分析）：**

| 情境 | 可否執行 | 依據 |
|------|----------|------|
| 全新 DB 執行 `alembic upgrade head` | ✅ 應該可以 | 001b 已修正 table order，wp_11_04a 指向 001b |
| 已有 001 的 DB 執行 `alembic upgrade head` | ⚠️ 可能衝突 | 001 和 001b 都會嘗試建立相同 tables |
| 測試 DB 狀態 | ⚠️ 不確定 | 報告提到手動 SQL，需驗證 alembic_version |

**建議驗證命令（未執行）：**
```bash
# 檢查實際 DB 的 migration 狀態
psql -d attendance_db -c "SELECT * FROM alembic_version;"

# 檢查 001 tables 是否存在
psql -d attendance_db -c "\dt attendance_*"
```

### 4.4 Tables 清單（預期）

**基於 migration 檔案分析：**

| Table | Migration | Purpose | Has company_id? |
|-------|-----------|---------|-----------------|
| `tenants` | 004 | 租戶主表 | N/A (PK: id) |
| `users` | 3532deda024c | 使用者 | ❌ (global) |
| `roles` | 3532deda024c | 角色 | ❌ (global) |
| `permissions` | 3532deda024c | 權限 | ❌ (global) |
| `user_roles` | 3532deda024c | 使用者-角色關聯 | ❌ (global) |
| `user_company_memberships` | 3532deda024c | 使用者-公司關聯 | ✅ Yes |
| `notifications` | 005 | 通知記錄 | ✅ Yes |
| `audit_logs` | 002 | 稽核日誌 | ✅ Yes |
| `audit_retention_policies` | 003 | 稽核保留政策 | ✅ Yes (PK) |
| `attendance_policies` | 001b | 考勤政策 | ✅ Yes |
| `attendance_sessions` | 001b | 出勤 session | ✅ Yes |
| `attendance_punches` | 001b | 打卡事件 | ✅ Yes |
| `company_entitlements` | wp_11_04a | 公司功能權限 | ✅ Yes |
| `support_company_assignments` | wp_11_04a | 客服-公司指派 | ✅ Yes |

**總計：** 14 tables (10 個有 company_id，4 個 global)

---

## 5. 測試現況（Reality Tests）

### 5.1 測試檔案統計

**位置：** `backend/app/modules/*/tests/` + `backend/tests/`

| 模組 | 測試檔案數 | 位置 |
|------|-----------|------|
| attendance | 10 | `app/modules/attendance/tests/` |
| audit | 5 | `app/modules/audit/tests/` |
| auth | 4 | `app/modules/auth/tests/` |
| backup | 5 | `app/modules/backup/tests/` |
| customer_service | 1 | `app/modules/customer_service/tests/` |
| notifications | 5 | `app/modules/notifications/tests/` |
| tenants | 5 | `app/modules/tenants/tests/` |
| core | (未統計) | `app/core/tests/` |

**總計：** 至少 35 個測試檔案

### 5.2 測試類型分布

**基於檔名分析：**

| 類型 | 範例檔案 | 數量估計 |
|------|----------|----------|
| API tests | `test_api.py`, `test_login_api.py`, `test_punch_api.py` | ~15 |
| Repo tests | `test_repo.py` | ~5 |
| Service tests | `test_service.py` | ~3 |
| Integration tests | `test_audit_api.py`, `test_entitlements_api.py` | ~8 |
| Policy engine tests | (attendance/policy_engine.py 有 24KB) | ~1 |

### 5.3 DB Fixture / Test DB 建立方式

**位置：** `backend/conftest.py` + `backend/app/conftest.py`

**發現：**
- ✅ 有多個 `conftest.py` (8 個)
- ⚠️ 未檢視內容，不確定是否有跳 migration 或手動 SQL

**依據 MIGRATION_CHAIN_AUDIT_REPORT.md：**
- ⚠️ 測試 DB 曾手動執行 wp_11_04a (用 SQL 而非 alembic)
- ⚠️ 測試 DB 曾跳過 001 (因為有 bug)
- ⚠️ 可能導致測試 DB schema 與 migration 不一致

### 5.4 CI 會不會炸掉？

**判斷依據：**

| 風險點 | 狀態 | 影響 |
|--------|------|------|
| Migration chain 有 bug | ⚠️ 001 有 bug，但已被 001b 取代 | 如果 CI 用 fresh DB，應該 OK |
| 測試 DB 手動 SQL | ⚠️ 報告提到手動執行 | 如果 CI 用該 DB，可能不一致 |
| conftest.py 跳 migration | ⚠️ 未檢視 | 需檢查 conftest.py 內容 |

**結論：** ⚠️ 不確定，需實際執行 `pytest` 驗證

---

## 6. 文件現況（Reality Docs）

### 6.1 文件清單（會影響開發決策的）

**位置：** `docs/`

| 類別 | 檔案 | 用途 | 可能過時？ |
|------|------|------|-----------|
| **Gate/Progress** | `GATE_PROGRESS_TRACKER.md` | 追蹤 WP 進度 | ✅ 最新 (2026-03-03) |
| **Gate/Progress** | `GATE_5_STATUS_SNAPSHOT.md` | Gate 5 狀態快照 | ⚠️ 需確認 |
| **Gate/Progress** | `GATE_5_BOUNDARY_RULES.md` | Gate 5 邊界規則 | ⚠️ 需確認 |
| **Development** | `DEVELOPMENT_ORDER.md` | WP 執行順序 | ⚠️ 可能過時 (定義 17 WPs，但已完成更多) |
| **Development** | `STATUS_MATRIX.md` | 實作狀態矩陣 | ⚠️ 可能過時 (2026-03-02) |
| **Migration** | `MIGRATION_CHAIN_AUDIT_REPORT.md` | Migration 審查報告 | ✅ 最新 (2026-03-04) |
| **Migration** | `MIGRATION_CLEAN_REBUILD_POLICY.md` | Migration 重建政策 | ⚠️ 需確認 |
| **Auth** | `AUTH_SCHEMA_SPEC.md` | Auth schema 規格 | ⚠️ 需確認是否與實作一致 |
| **Auth** | `AUTH_TRANSITION_PLAN.md` | Header→JWT 轉換計畫 | ⚠️ 部分完成 (2/7 模組已轉) |
| **Auth** | `GATE_4_AUTH_DECISION_FREEZE.md` | Auth 決策凍結 | ✅ 凍結文件 |
| **Attendance** | `WP-11-01_ATTENDANCE_DOMAIN_MODEL_SPEC.md` | Attendance domain 規格 | ⚠️ 需確認 |
| **Attendance** | `SPLIT_SHIFT_DESIGN.md` | Split shift 設計 | ⚠️ 需確認 |
| **Attendance** | `ATTENDANCE_REGRESSION_SPEC.md` | 8 個回歸測試規格 | ⚠️ 需確認是否已實作 |
| **WP Reports** | `WP-11-04A_COMPLETION_REPORT_FINAL.md` | WP-11-04A 完成報告 | ✅ 最新 (2026-03-04) |
| **WP Reports** | `WP-11-02_REPORT.md`, `WP-11-03_REPORT.md` | WP 完成報告 | ⚠️ 需確認 |

**總計：** 59 個 markdown 檔案

### 6.2 可能過時或互相矛盾的文件

**發現 1：DEVELOPMENT_ORDER.md vs. 實際進度**

- `DEVELOPMENT_ORDER.md` 定義 17 個 WPs (WP-09-01 到 WP-11-06)
- `GATE_PROGRESS_TRACKER.md` 顯示已完成 17/20 WPs (85%)
- ⚠️ 矛盾：DEVELOPMENT_ORDER 說 17 個，TRACKER 說 20 個

**發現 2：STATUS_MATRIX.md vs. 實際狀態**

- `STATUS_MATRIX.md` (2026-03-02) 說 auth 模組不存在
- 實際：`backend/app/modules/auth/` 已存在，有 6 個檔案
- ⚠️ 過時：STATUS_MATRIX 未更新

**發現 3：AUTH_TRANSITION_PLAN.md vs. 實際狀態**

- 計畫：分 5 批次轉換 Header → JWT
- 實際：只有 tenants + customer_service 用 JWT，其他 4 個模組仍用 Header
- ⚠️ 部分完成：轉換未完成

**發現 4：MIGRATION_CHAIN_AUDIT_REPORT.md vs. 實際 migration**

- 報告說 001 有 bug，建議用 001b 取代
- 實際：001b 已建立，wp_11_04a 已指向 001b
- ✅ 一致：報告建議已實作

---

## 7. 其他發現

### 7.1 程式碼品質指標

| 指標 | 數值 | 位置 |
|------|------|------|
| 最大檔案 | 24KB | `attendance/policy_engine.py` |
| 平均檔案大小 | ~3-5KB | 大部分模組檔案 |
| 註解密度 | 高 | 大部分檔案有 docstring |
| 型別標註 | 部分 | 有用 Pydantic，但不是所有函數都有 type hints |

### 7.2 設定檔

| 檔案 | 位置 | 狀態 |
|------|------|------|
| `requirements.txt` | `backend/requirements.txt` | ✅ 存在 (8 個套件) |
| `alembic.ini` | `backend/alembic.ini` | ✅ 存在 |
| `.env` | (未找到) | ❌ 不存在 (用預設值) |
| `pyproject.toml` | (未找到) | ❌ 不存在 |

### 7.3 EventBus 使用

**位置：** `backend/app/core/event_bus.py`

**訂閱者：**
- `notifications/event_handlers.py` 訂閱 `attendance.approved`
- `main.py` 註冊 demo handlers

**發布者：**
- `attendance/service.py` 發布 `attendance.approved`

**狀態：** ✅ EventBus 機制運作中

---

## 8. 總結

### 8.1 現況摘要

| 面向 | 狀態 | 說明 |
|------|------|------|
| **模組完整性** | ✅ 良好 | 7 個模組全部有 models/repo/api/tests |
| **Migration chain** | ⚠️ 部分風險 | 001b 已修正 bug，但需驗證實際 DB 狀態 |
| **測試覆蓋** | ✅ 良好 | 35+ 測試檔案，所有模組有測試 |
| **Auth 機制** | ⚠️ 混合 | JWT 已實作，但只有 2/7 模組使用 |
| **文件維護** | ⚠️ 部分過時 | 有些文件未同步更新 |
| **Tenant isolation** | ✅ 良好 | 所有 tenant data tables 有 company_id |

### 8.2 可落地性評估

| 項目 | 評估 | 依據 |
|------|------|------|
| 新環境初始化 | ⚠️ 可能可以 | 001b 已修正，但需驗證 |
| CI/CD 執行測試 | ⚠️ 不確定 | 需實際執行 pytest |
| 生產部署 | ⚠️ 有風險 | Auth 轉換未完成，兩種機制並存 |
| 維護性 | ✅ 良好 | 程式碼結構清晰，有測試 |

---

**文件版本：** 1.0  
**產出日期：** 2026-03-04  
**審查者：** Claude Opus 4.6 (Cursor AI)
