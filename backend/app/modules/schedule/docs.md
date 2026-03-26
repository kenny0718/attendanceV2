# Schedule Module — Documentation

**Module:** `backend/app/modules/schedule/`  
**WP Foundation Ticket:** WP-S1-01  
**WP Alignment Fix:** WP-S1-01A  
**Status:** FOUNDATION ONLY — Models aligned to project conventions; No migration yet  
**Last Updated:** 2026-03-18 (WP-S1-01A Models Alignment Fix)

---

## 1. 模組目的

Schedule 模組負責管理公司的班別指派（Shift Management）功能域，包含：

1. **ShiftTemplate** — 可復用的班別模板（如日班、夜班、休假）
2. **ShiftAssignment** — 將某位使用者在某一天指派到某一班別

本模組為獨立模組，不直接耦合 attendance 或 leave 業務邏輯。

---

## 2. WP-S1-01 + WP-S1-01A 完成範圍

| 交付項目 | 票號 | 狀態 |
|---------|------|------|
| `__init__.py` — 模組說明 | WP-S1-01 | ✅ 完成 |
| `models.py` — ORM 模型定義（已對齊慣例）| WP-S1-01A | ✅ 完成 |
| `schemas.py` — Pydantic schema 骨架 | WP-S1-01 | ✅ 完成 |
| `repo.py` — Repository 骨架（stub）| WP-S1-01 | ✅ 完成 |
| `service.py` — Service 骨架（stub）| WP-S1-01 | ✅ 完成 |
| `api.py` — Router 定義（無 endpoint，未掛入主 app）| WP-S1-01 | ✅ 完成 |
| `docs.md` — 本文件 | WP-S1-01A | ✅ 更新 |

---

## 3. 資料模型概覽（WP-S1-01A 對齊後版本）

### 3.1 ORM 慣例對齊基準

本模組 ORM 慣例與以下模組一致：
- `backend/app/modules/attendance/models.py`
- `backend/app/modules/leave/models.py`

| 慣例項目 | 採用值 |
|---------|--------|
| Primary Key 型別 | `UUID(as_uuid=True)` + `server_default=gen_random_uuid()` |
| `company_id` 型別 | `String(255)` + `ForeignKeyConstraint → tenants.id` CASCADE |
| `user_id` 型別 | `UUID(as_uuid=True)` + `ForeignKeyConstraint → users.id` CASCADE |
| FK 定義方式 | `__table_args__` 中的 `ForeignKeyConstraint`（非行內 ForeignKey）|
| Timestamp 型別 | `DateTime(timezone=True)` + `server_default=text('NOW()')` |
| Status 欄位 | `String(20)` + `CheckConstraint`（非 SQLAlchemy Enum type）|

---

### 3.2 ShiftTemplate

代表一個可復用的班別模板，例如「日班」、「夜班」、「休假」。

| 欄位 | 型別 | 說明 |
|------|------|------|
| `id` | `UUID` PK | `gen_random_uuid()` 自動生成 |
| `company_id` | `String(255)` | 租戶隔離；FK → `tenants.id` CASCADE |
| `code` | `String(32)` | 班別代碼，同公司內唯一（UniqueConstraint）|
| `name` | `String(64)` | 班別顯示名稱 |
| `start_time` | `Time` | 班別開始時間 |
| `end_time` | `Time` | 班別結束時間 |
| `break_minutes` | `SmallInteger` | 休息時間（分鐘），`server_default=0` |
| `is_overnight` | `Boolean` | 是否跨日，`server_default=false`（資訊性）|
| `is_active` | `Boolean` | 是否啟用，`server_default=true` |
| `created_at` | `DateTime(tz=True)` | 建立時間（UTC）|
| `updated_at` | `DateTime(tz=True)` | 更新時間（UTC）|

**Constraints / Indexes：**
- `UniqueConstraint('company_id', 'code', name='uq_shift_templates_company_code')`
- `ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE')`
- `Index('idx_shift_templates_company', 'company_id')`
- `Index('idx_shift_templates_company_active', 'company_id', 'is_active')`

---

### 3.3 ShiftAssignment

代表某位使用者在某個日期被指派到某個班別。

| 欄位 | 型別 | 說明 |
|------|------|------|
| `id` | `UUID` PK | `gen_random_uuid()` 自動生成 |
| `company_id` | `String(255)` | 租戶隔離；FK → `tenants.id` CASCADE |
| `user_id` | `UUID` | 使用者；FK → `users.id` CASCADE |
| `shift_template_id` | `UUID` | 班別模板；FK → `shift_templates.id` RESTRICT |
| `work_date` | `Date` | 指派日期 |
| `status` | `String(20)` | 狀態；CheckConstraint（見下）|
| `notes` | `Text` nullable | 備註 |
| `created_at` | `DateTime(tz=True)` | 建立時間（UTC）|
| `updated_at` | `DateTime(tz=True)` | 更新時間（UTC）|

**Constraints / Indexes：**
- `CheckConstraint("status IN ('scheduled', 'confirmed', 'cancelled')", name='ck_shift_assignments_status')`
- `ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE')`
- `ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')`
- `ForeignKeyConstraint(['shift_template_id'], ['shift_templates.id'], ondelete='RESTRICT')`
- `Index('idx_shift_assignments_company', 'company_id')`
- `Index('idx_shift_assignments_user', 'user_id')`
- `Index('idx_shift_assignments_company_user', 'company_id', 'user_id')`
- `Index('idx_shift_assignments_company_date', 'company_id', 'work_date')`
- `Index('idx_shift_assignments_template', 'shift_template_id')`

---

### 3.4 AssignmentStatus 值

```python
ASSIGNMENT_STATUS_SCHEDULED = "scheduled"   # 預設狀態
ASSIGNMENT_STATUS_CONFIRMED = "confirmed"   # 已確認 / 鎖定
ASSIGNMENT_STATUS_CANCELLED = "cancelled"   # 已取消
```

**實作說明（WP-S1-01A）：**  
使用 `String(20)` + `CheckConstraint` 而非 SQLAlchemy `Enum` type，原因：
- 與 attendance session status 慣例一致（String + CheckConstraint）
- 避免 PostgreSQL `CREATE TYPE` 的 migration 複雜度（ALTER TYPE 有限制）
- 應用層使用常數 `ASSIGNMENT_STATUS_*` 確保型別安全

**WP-S1-02 migration 注意事項：**  
migration 中直接使用 `sa.String(20)` + `sa.CheckConstraint("status IN (...)")` 即可，無需 `sa.Enum()`。

---

## 4. 明確未做項目（Out of Scope）

### 4.1 Migration（WP-S1-02）
- **未做 Alembic migration**
- `shift_templates` 和 `shift_assignments` 資料表**尚未建立於資料庫**
- 資料庫 table 建立屬於 WP-S1-02

### 4.2 API 行為
- **未做任何對外可用 API endpoint**
- `api.py` 的 router **未掛入** 主 app（`main.py` 未更新）

### 4.3 Repo / Service 實作
- 所有 repo 方法均為 stub（`raise NotImplementedError`）
- 所有 service 方法均為 stub（`raise NotImplementedError`）

### 4.4 業務邏輯（後續票）
- 排班衝突檢測
- Rotation / recurring rules
- Leave 整合
- Attendance 整合
- Approval flow
- Frontend UI

### 4.5 WP-S1-01A 中未修改項目
- `schemas.py`（未同步更新 UUID 型別；WP-S1-02 或 WP-S1-03 補齊）
- `repo.py` / `service.py` / `api.py`（行為未變，保持 stub）
- `env.py`（未補 schedule models import；WP-S1-02 內處理）

---

## 5. 架構邊界

```
[schedule module]
    models.py      ← ORM 定義（WP-S1-01A 對齊完成，no migration）
    schemas.py     ← Pydantic schema（待 WP-S1-02/03 同步更新型別）
    repo.py        ← DB 存取骨架（stub only）
    service.py     ← 業務規則骨架（stub only）
    api.py         ← FastAPI router（無 endpoint，未掛入主 app）
    docs.md        ← 本文件（WP-S1-01A 更新）

[獨立邊界]
    schedule ← 不 import attendance 業務邏輯
    schedule ← 不 import leave 業務邏輯
    schedule ← 不修改 core/features.py
    schedule ← 未掛入 main.py
```

---

## 6. 建議後續票順序

| 票號 | 名稱 | 說明 |
|------|------|------|
| **WP-S1-02** | Migration | 建立 `010_wp_s1_02_create_schedule_tables.py`；同步補 env.py import；schemas.py UUID 型別同步 |
| **WP-S1-03** | Basic Schedule API | ShiftTemplate CRUD API |
| **WP-S1-04** | ShiftAssignment API | 排班指派 / 查詢 / 取消 |
| **WP-S1-05** | Tenant Isolation Tests | 自動化測試 |
| **WP-S1-06** | Feature Gate | schedule.core Feature Gate 套用 |

---

## 7. 給未來 AI 的說明

1. **Schedule 模組 models.py 已對齊慣例（WP-S1-01A）**，但資料庫尚無 schedule 資料表。
2. **下一步是 WP-S1-02（Migration）**，不是直接開始 API。
3. **schemas.py 尚未同步 UUID 型別**，WP-S1-02 或 WP-S1-03 需一併更新。
4. **env.py 尚未補 schedule models import**，WP-S1-02 需補上。
5. **不要修改 attendance / leave / 其他既有模組**，schedule 為獨立邊界。
6. **api.py router 未掛入 main.py**，任何 `/api/v1/schedule` endpoint 均不可用。

---

**文件版本：** v1.1 (WP-S1-01A Models Alignment Fix)  
**前次版本：** v1.0 (WP-S1-01 Foundation)  
**下次更新時機：** WP-S1-02 Migration 完成後

---

## WP-S1-02 Migration Record (2026-03-18)

**票號:** WP-S1-02 Schedule Module Migration  
**狀態:** COMPLETE — Migration 已建立且 `alembic upgrade head` 驗證通過

### Migration 資訊

- **Migration 檔案:** `backend/alembic/versions/010_wp_s1_02_create_schedule_tables.py`
- **revision:** `010_wp_s1_02`
- **down_revision:** `009_wp_11_08`
- **建立資料表:** `shift_templates`, `shift_assignments`

### shift_templates 資料表

| 欄位 | 型別 | 說明 |
|------|------|------|
| id | UUID PK (gen_random_uuid()) | 主鍵 |
| company_id | String(255) FK→tenants.id CASCADE | 租戶隔離 |
| code | String(32) | 班別代碼（唯一限於公司內） |
| name | String(64) | 班別顯示名稱 |
| start_time | Time | 開始時間 |
| end_time | Time | 結束時間 |
| break_minutes | SmallInteger default 0 | 休息分鐘數 |
| is_overnight | Boolean default false | 跨午夜旗標 |
| is_active | Boolean default true | 軟刪除旗標 |
| created_at | DateTime(timezone=True) | 建立時間 (UTC) |
| updated_at | DateTime(timezone=True) | 更新時間 (UTC) |

**Constraints:** `uq_shift_templates_company_code`（company_id, code）  
**FK:** `fk_shift_templates_company_id` → tenants.id CASCADE  
**Indexes:** `idx_shift_templates_company`, `idx_shift_templates_company_active`

### shift_assignments 資料表

| 欄位 | 型別 | 說明 |
|------|------|------|
| id | UUID PK (gen_random_uuid()) | 主鍵 |
| company_id | String(255) FK→tenants.id CASCADE | 租戶隔離 |
| user_id | UUID FK→users.id CASCADE | 使用者 |
| shift_template_id | UUID FK→shift_templates.id RESTRICT | 班別模板 |
| work_date | Date | 指派日期 |
| status | String(20) default 'scheduled' | 狀態（CheckConstraint） |
| notes | Text nullable | 備注 |
| created_at | DateTime(timezone=True) | 建立時間 (UTC) |
| updated_at | DateTime(timezone=True) | 更新時間 (UTC) |

**Constraints:** `ck_shift_assignments_status`（scheduled/confirmed/cancelled）  
**FK:** tenants.id CASCADE, users.id CASCADE, shift_templates.id RESTRICT  
**Indexes:** company, user, company+user, company+date, template

### 模組目前狀態（WP-S1-02 完成後）

- [x] Models 已定義（WP-S1-01 / WP-S1-01A）
- [x] Migration 已建立且驗證通過（WP-S1-02）
- [ ] Router 尚未掛進 main.py（後續票）
- [ ] API endpoints 尚未實作（後續票）
- [ ] repo.py / service.py 仍為 stub（後續票）
- [ ] Attendance / Leave 整合（後續票）

---

## WP-S1-03 CRUD Core Record (2026-03-19)

**票號:** WP-S1-03 — Schedule Module CRUD Core  
**狀態:** COMPLETE — repo.py + service.py 已實作，smoke test 15/15 PASS

### repo.py 現已支援（ShiftTemplate）
- `get_by_id(template_id, company_id)` — 依 id + company_id 查詢（Tenant Isolation）
- `get_by_code(code, company_id)` — 依 code + company_id 查詢（uniqueness check 用）
- `list_by_company(company_id, active_only)` — 列出公司所有/活躍班別模板
- `create(obj)` — 建立並 commit
- `update(obj)` — 更新並 commit
- `set_active(template_id, company_id, is_active)` — 啟用/停用旗標

### repo.py 現已支援（ShiftAssignment）
- `get_by_id(assignment_id, company_id)` — 依 id + company_id 查詢（Tenant Isolation）
- `list_by_user_date_range(company_id, user_id, start_date, end_date)` — 依使用者+日期範圍
- `list_by_company_date(company_id, work_date)` — 依公司+單日
- `list_by_company(company_id, start_date, end_date)` — 依公司+可選日期範圍
- `create(obj)` — 建立並 commit
- `update(obj)` — 更新並 commit
- `cancel(assignment_id, company_id)` — 設定 status=cancelled

### service.py 現已支援（ShiftTemplate）
- `create_shift_template(company_id, payload)` — 建立，含 code 唯一性檢查
- `get_shift_template(company_id, template_id)` — 取得單筆，不存在 404
- `list_shift_templates(company_id, active_only)` — 列出
- `update_shift_template(company_id, template_id, payload)` — 部分更新
- `deactivate_shift_template(company_id, template_id)` — 軟刪除（is_active=False）
- `activate_shift_template(company_id, template_id)` — 重新啟用

### service.py 現已支援（ShiftAssignment）
- `create_shift_assignment(company_id, payload)` — 建立，含 template 同 company 驗證
- `get_shift_assignment(company_id, assignment_id)` — 取得單筆，不存在 404
- `list_assignments_for_user(company_id, user_id, start_date, end_date)` — 依使用者+日期
- `list_assignments_for_date(company_id, work_date)` — 依單日
- `list_assignments(company_id, start_date, end_date)` — 全公司+可選日期
- `update_shift_assignment(company_id, assignment_id, payload)` — 部分更新（含 template 驗證）
- `cancel_shift_assignment(company_id, assignment_id)` — 取消（已取消再取消 409）

### Tenant Isolation 規則
1. 所有 repo 查詢均強制 `WHERE company_id = ?`
2. 不允許只靠 `id` 查詢（必須帶 company_id）
3. 建立 assignment 時，必須確認 shift_template.company_id == company_id
4. 更新時不得引用其他 company 的 template
5. list 查詢預設限制在 company scope

### 仍未完成（後續票）
- [ ] API router / endpoints（WP-S1-04）
- [ ] main.py include_router（WP-S1-04）
- [ ] pytest 完整測試（WP-S1-04 或獨立票）
- [ ] 排班衝突偵測（future）
- [ ] 批量排班（future）
- [ ] Attendance / Leave 整合（future）

---

## WP-S1-04A API Layer Record (2026-03-19)

**票號:** WP-S1-04A — Schedule Module API Layer  
**狀態:** COMPLETE — router ready, NOT YET MOUNTED in main.py

### api.py 現已提供的 ShiftTemplate Endpoints

| Method | Path | 說明 |
|--------|------|------|
| POST | /api/v1/schedule/shift-templates | 建立班別模板（code 重複 → 409）|
| GET | /api/v1/schedule/shift-templates | 列出班別模板（?active_only=true）|
| GET | /api/v1/schedule/shift-templates/{id} | 取得單筆（不存在 → 404）|
| PATCH | /api/v1/schedule/shift-templates/{id} | 部分更新 |
| POST | /api/v1/schedule/shift-templates/{id}/activate | 啟用 |
| POST | /api/v1/schedule/shift-templates/{id}/deactivate | 停用 |

### api.py 現已提供的 ShiftAssignment Endpoints

| Method | Path | 說明 |
|--------|------|------|
| POST | /api/v1/schedule/shift-assignments | 建立指派（跨 tenant template → 422）|
| GET | /api/v1/schedule/shift-assignments | 列出指派（?user_id / ?start_date / ?end_date / ?work_date）|
| GET | /api/v1/schedule/shift-assignments/{id} | 取得單筆 |
| PATCH | /api/v1/schedule/shift-assignments/{id} | 部分更新（已取消 → 409）|
| POST | /api/v1/schedule/shift-assignments/{id}/cancel | 取消（已取消再取消 → 409）|

### Request/Filter 規則
- company_id 從 JWT actor 取得，不接受 payload 自填
- list assignments 支援：work_date（單日）/ user_id+date_range / date_range / 全公司
- status change 透過 PATCH update endpoint 處理（含 cancel 獨立端點）

### Tenant Isolation
- 所有 endpoint 透過 JWT actor 取得 company_id
- 跨 tenant 操作由 service 層攔截

### 仍未完成（後續票）
- [ ] main.py include_router（WP-S1-04B）
- [ ] Feature Gate（schedule.core 待定義於 FeatureKeys）
- [ ] pytest integration tests
- [ ] Frontend 串接
- [ ] 排班衝突偵測、批量排班等進階功能

---

## WP-S1-04B Router Mount + Feature Gate Record (2026-03-19)

**票號:** WP-S1-04B — Schedule Router Mount + Feature Gate  
**狀態:** COMPLETE — router mounted, feature gate active

### Schedule Router 已掛入 main.py
- `backend/app/main.py` 已 `include_router(schedule_router)`
- 所有 11 個 endpoints 現已對外可用（需 JWT + schedule.core entitlement）

### Feature Gate
- Feature Key: `schedule.core`（定義於 `app.core.features.FeatureKeys.SCHEDULE_CORE`）
- 所有 11 個 endpoints 均受 `_require_schedule_feature()` 保護
- 未帶 JWT → 401；JWT 有效但 schedule.core 未啟用 → 403 FEATURE_DISABLED

### 目前後端可用 Endpoints

**ShiftTemplate（6）：**
- POST /api/v1/schedule/shift-templates
- GET /api/v1/schedule/shift-templates
- GET /api/v1/schedule/shift-templates/{id}
- PATCH /api/v1/schedule/shift-templates/{id}
- POST /api/v1/schedule/shift-templates/{id}/activate
- POST /api/v1/schedule/shift-templates/{id}/deactivate

**ShiftAssignment（5）：**
- POST /api/v1/schedule/shift-assignments
- GET /api/v1/schedule/shift-assignments
- GET /api/v1/schedule/shift-assignments/{id}
- PATCH /api/v1/schedule/shift-assignments/{id}
- POST /api/v1/schedule/shift-assignments/{id}/cancel

### 仍未完成（後續票）
- [ ] company_entitlements 設定 schedule.core（DB entitlement setup）
- [ ] JWT 完整 e2e 驗證（帶 token 的 API call）
- [ ] pytest integration tests
- [ ] Frontend 串接
- [ ] 排班衝突偵測、批量排班等進階功能

---

## WP-S1-05 Integration Testing + Entitlement Setup（2026-03-19）

### Integration Status: COMPLETE

### Entitlement Requirement
- Feature key: `schedule.core`
- 設定方式: `company_entitlements` 表寫入 `(company_id, feature_key='schedule.core', enabled=True)`
- 測試 fixture: `schedule_entitlement` (conftest.py) 自動建立
- 不可 bypass feature gate，必須走正確 entitlement 流程

### API 使用前提
1. 公司必須有 `schedule.core` entitlement（否則所有 endpoint 回傳 403）
2. 請求必須帶有效 JWT（actor 含 `active_company_id`）
3. Tenant isolation 由 JWT actor 強制（不接受 body 傳入的 company_id 做跨 tenant 操作）

### Pytest Integration Tests
位置: `backend/app/modules/schedule/tests/`

| 檔案 | 測試數 | 狀態 |
|------|--------|------|
| test_schedule_template_api.py | 6 | PASS |
| test_schedule_assignment_api.py | 6 | PASS |
| **合計** | **12** | **12/12 PASS** |

### 驗證結果
- Feature Gate（有/無 entitlement）: PASS
- JWT + tenant context: PASS（dependency_override 模擬）
- ShiftTemplate CRUD flow: PASS（create/get/list/update/activate/deactivate）
- ShiftAssignment CRUD flow: PASS（create/get/list/update/cancel）
- Negative cases: PASS（duplicate 409, not found 404, cross-tenant 404, double-cancel 409）

---

## WP-S1-06 Production Entitlement + Real JWT E2E（2026-03-19）

**票號:** WP-S1-06 — Schedule Production Entitlement + Real JWT E2E  
**狀態:** COMPLETE  
**完成時間:** 2026-03-19

### 1. Entitlement Path Audit

#### schedule.core 正式啟用路徑

| 層級 | 說明 |
|------|------|
| Feature Key | `FeatureKeys.SCHEDULE_CORE = "schedule.core"`（定義於 `backend/app/core/features.py`）|
| DB 資料表 | `company_entitlements`（model: `CompanyEntitlement`）|
| 啟用方式 | 在 `company_entitlements` 寫入 `(company_id, feature_key='schedule.core', enabled=True)` |
| API 管理端點 | `GET/POST /api/v1/tenants/{company_id}/entitlements`（tenants module 已提供）|
| 測試 fixture | `schedule_entitlement`（conftest.py）自動建立 |

#### PLAN_DEFAULTS 現況

`PLAN_DEFAULTS`（`app/core/features.py`）目前**未納入 `schedule.core`**：

```python
PLAN_DEFAULTS = {
    "Basic": {
        FeatureKeys.ATTENDANCE_SHIFT_TEMPLATES: False,
        FeatureKeys.ATTENDANCE_SPLIT_SHIFT: False,
        FeatureKeys.ATTENDANCE_SHIFT_OVERRIDES: False,
    },
    "Pro": {
        FeatureKeys.ATTENDANCE_SHIFT_TEMPLATES: True,
        FeatureKeys.ATTENDANCE_SPLIT_SHIFT: True,
        FeatureKeys.ATTENDANCE_SHIFT_OVERRIDES: True,
    },
}
```

**結論：** `schedule.core` 尚未納入 `PLAN_DEFAULTS`，不影響 entitlement 機制本身（entitlement 直接由 `company_entitlements` 表控制），但 production/staging rollout 時需手動為各公司在 `company_entitlements` 表寫入 `schedule.core=enabled`，或透過 tenants API endpoint 設定。

**本輪決定：** `PLAN_DEFAULTS` 屬 plan-tier 概念（Basic/Pro plan 預設配置），不屬於 schedule module 本身的 entitlement 機制。未將 `schedule.core` 納入 `PLAN_DEFAULTS` 屬正常狀態——schedule 模組處於 opt-in 階段，需顯式啟用。不做修改，記錄為已知缺口（WP-S1-07 or later）。

### 2. Real JWT Verification Method

- 使用 `app.core.security.jwt.create_access_token()` 產生真實 HS256 signed JWT
- Claims: `{sub: user_id, company_id: xxx, role_id: admin}`
- 透過 `Authorization: Bearer <token>` header 傳入
- 完整路徑：`get_current_actor()` → `decode_access_token()` → User DB 查詢 → Membership 驗證 → Actor 建立 → `get_actor_with_company()` → endpoint
- **不使用** `override_actor_dependency`（依 WP-S1-06 要求）
- 僅 override `get_db`（讓 test DB 注入，不影響 auth 路徑）

### 3. Real JWT E2E 測試結果（14/14 PASS）

**測試檔:** `backend/app/modules/schedule/tests/test_schedule_real_jwt_e2e.py`

#### Auth Baseline
| 測試 | 結果 |
|------|------|
| No token → 401 | PASS |
| Invalid token → 401 | PASS |
| Valid JWT + entitlement → 200 | PASS |
| Valid JWT + no entitlement → 403 FEATURE_DISABLED | PASS |

#### Template Flow（Real JWT）
| 測試 | 結果 |
|------|------|
| create template | PASS |
| get template by id | PASS |
| list templates | PASS |

#### Assignment Flow（Real JWT）
| 測試 | 結果 |
|------|------|
| create assignment | PASS |
| get assignment by id | PASS |
| cancel assignment | PASS |

#### Negative Cases
| 測試 | 結果 |
|------|------|
| no entitlement → list blocked (403) | PASS |
| no entitlement → create blocked (403) | PASS |
| cross-tenant template access blocked (403/404) | PASS |
| unauthenticated assignment → 401 | PASS |

**pytest 結果:** `14 passed, 19 warnings in 1.91s`

### 4. Bug Fixed（最小修正）

測試開發過程中發現並修正一個測試層 bug：
- **問題：** `from app.main import app as fastapi_app` 若在 fixture 函數內執行 `import app.modules.*`，Python 會將 `app` 局部重綁為 package，覆蓋 FastAPI instance
- **修正：** 將 model imports 移至 module level，並使用 `fastapi_app` alias 區分 FastAPI instance 與 `app` package
- **影響範圍：** 僅測試檔案（不影響 production code）

### 5. 仍未完成項目

| 項目 | 說明 | 建議票號 |
|------|------|----------|
| `schedule.core` 納入 PLAN_DEFAULTS | 需決定 plan tier 策略 | WP-S1-07 |
| Production/Staging entitlement seeding | 正式環境需手動或自動設定 | WP-S1-07 |
| Frontend 串接 | Schedule API 尚無 UI | 後續 Frontend WP |
| 排班進階功能 | 衝突偵測、批量排班、循環排班 | S2/S3 |

---

**文件版本:** v1.6 (WP-S1-06 Real JWT E2E COMPLETE)  
**前次版本:** v1.5 (WP-S1-05 Integration Testing COMPLETE)

## WP-S1-07B Template Edit UI Update (2026-03-25)

### Scope
- Frontend `/schedule` page新增 Template inline edit（單列編輯）
- 使用既有 API：`PATCH /api/v1/schedule/shift-templates/{template_id}`
- 不涉及 Assignment Edit、不涉及 backend API/schema/service/repo 變更

### UI 行為
- 每列模板新增「編輯」按鈕
- 同一時間僅允許一列進入編輯狀態
- 可編輯欄位：
  - `name`
  - `start_time`
  - `end_time`
  - `break_minutes`
  - `is_overnight`
- 取消編輯會還原原值
- 儲存成功後刷新 template list，並顯示成功訊息

### Payload（最小欄位）
`updateTemplate()` 僅送以下欄位：
- `name`
- `start_time`
- `end_time`
- `break_minutes`
- `is_overnight`

未送出 `is_active`（由既有啟用/停用流程管理）。

## WP-S1-07C Create Contract Alignment Fix (2026-03-25)

### 背景
`POST /api/v1/schedule/shift-templates` 曾有 contract 漂移：
- 設計上 company scope 來自 JWT actor
- create schema 卻要求 body.company_id
- 導致前端（不送 company_id）回 422

### 修正內容（最小）
- `ShiftTemplateCreate` 不再要求 `company_id`
- create service 不再依賴 `payload.company_id` 比對
- create 寫入 company_id 仍完全來自 `actor.active_company_id`

### Tenant Isolation
- 來源不變：JWT actor scope
- 不將 tenant boundary 責任轉移到 client payload

### 影響範圍
- 修正 Template create contract
- update / activate / deactivate 行為不變
- Assignment create 目前仍是舊型 contract（本票未調整）



## WP-S1-08 Assignment Create Contract Alignment Fix (2026-03-26)

### 背景
`POST /api/v1/schedule/shift-assignments` 存在與 Template create 不一致的 contract：
- create schema 要求 body.company_id
- service.create_shift_assignment() 依賴 / 比對 payload.company_id
- 與既定 tenant isolation（company scope 由 JWT actor 決定）不一致

### 修正內容（最小）
- `ShiftAssignmentCreate` 改為獨立 schema（不繼承 `ShiftAssignmentBase`）
- `ShiftAssignmentCreate` 不包含 `company_id`
- `create_shift_assignment(company_id, payload)` 移除 payload.company_id mismatch guard
- create 寫入 `company_id` 仍完全來自 API 層 `actor.active_company_id`

### Tenant Isolation
- tenant boundary 來源維持 JWT actor scope
- 不將 company scope 責任轉移到 client payload

### 影響範圍
- 僅調整 Assignment create contract
- Assignment read response 仍保留 `company_id`
- Assignment update/list/get/cancel flow 不變
- Template flow 不變
