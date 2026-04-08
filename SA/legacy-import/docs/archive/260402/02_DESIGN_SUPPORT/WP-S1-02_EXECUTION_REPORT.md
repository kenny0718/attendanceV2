# WP-S1-02 Execution Report

**票號:** WP-S1-02 — Schedule Module Migration  
**執行日期:** 2026-03-18  
**執行者:** AI Agent (Cursor)  
**狀態:** COMPLETE

---

## 1. Objective

為 Schedule 模組建立第一個正式 Alembic migration，
在 PostgreSQL 中建立 `shift_templates` 與 `shift_assignments` 資料表，
並確保 migration chain 正確接在現有 head（`009_wp_11_08`）之後。

---

## 2. Files Read

| 檔案 | 用途 |
|------|------|
| backend/app/modules/schedule/models.py | 欄位與 constraint 定義依據 |
| backend/app/modules/schedule/schemas.py | UUID 對齊檢查 |
| backend/app/modules/schedule/docs.md | 模組現況確認 |
| backend/alembic/env.py | models import 現況確認 |
| backend/alembic/versions/009_wp_11_08_*.py | down_revision 確認 |
| backend/alembic.ini | DB URL 確認 |
| backups/20260305_165448/alembic/env.py | env.py 重建基礎 |
| docs/WP-S1-02_PRE_MIGRATION_AUDIT.md | pre-audit 結果參考 |
| docs/WP-S1-01A_MODELS_ALIGNMENT_FIX_REPORT.md | models alignment 參考 |

---

## 3. Files Changed

| 檔案 | 變更類型 | 說明 |
|------|----------|------|
| backend/alembic/versions/010_wp_s1_02_create_schedule_tables.py | 新建 | 正式 migration 檔案 |
| backend/alembic/env.py | 修正重建 | 原檔案為 0 bytes，從備份重建並補 schedule models import |
| backend/app/modules/schedule/schemas.py | 修正 | UUID 欄位型別對齊 |
| backend/app/modules/schedule/docs.md | Append | 新增 WP-S1-02 migration 記錄 |
| docs/03_WP_CONTROL/NEXT_WP_TICKET.md | Append | WP-S1-02 完成記錄 + 下一票建議 |
| docs/03_WP_CONTROL/GATE_PROGRESS_TRACKER.md | Append | WP-S1-02 Gate 結果 |
| docs/02_DEVELOPMENT_STATUS/WORKSTREAM_STATUS_LEDGER.md | Append | WP-S1-02 Ledger Entry |
| docs/02_DEVELOPMENT_STATUS/MODULE_STATUS_MATRIX.md | Append | Schedule 模組狀態更新 |
| docs/02_DEVELOPMENT_STATUS/CURRENT_SYSTEM_STATE.md | Append | 系統狀態更新 |
| docs/WP-S1-02_EXECUTION_REPORT.md | 新建 | 本報告 |

---

## 4. Migration File Summary

- **檔案:** `backend/alembic/versions/010_wp_s1_02_create_schedule_tables.py`
- **revision:** `010_wp_s1_02`
- **down_revision:** `009_wp_11_08`
- **建立資料表:** `shift_templates`, `shift_assignments`

### shift_templates
- UUID PK (gen_random_uuid())
- company_id: String(255) FK→tenants.id CASCADE
- code: String(32)
- name: String(64)
- start_time / end_time: Time
- break_minutes: SmallInteger default 0
- is_overnight: Boolean default false
- is_active: Boolean default true
- created_at / updated_at: DateTime(timezone=True)
- UniqueConstraint: `uq_shift_templates_company_code`
- FK: `fk_shift_templates_company_id`
- Indexes: company, company+is_active

### shift_assignments
- UUID PK (gen_random_uuid())
- company_id: String(255) FK→tenants.id CASCADE
- user_id: UUID FK→users.id CASCADE
- shift_template_id: UUID FK→shift_templates.id RESTRICT
- work_date: Date
- status: String(20) default 'scheduled'
- notes: Text nullable
- created_at / updated_at: DateTime(timezone=True)
- CheckConstraint: `ck_shift_assignments_status` (scheduled/confirmed/cancelled)
- FK: fk_shift_assignments_company_id, fk_shift_assignments_user_id, fk_shift_assignments_template_id
- Indexes: company, user, company+user, company+date, template

---

## 5. env.py Minimal Fix Summary

- **問題:** env.py 為 0 bytes（原因不明，可能被意外清空）
- **處理:** 從 `backups/20260305_165448/alembic/env.py` 重建，並補入：
  ```python
  from app.modules.leave.models import (LeaveType, LeaveApprovalPolicy, LeaveRequest, LeaveApprovalLog)
  # WP-S1-02: Schedule models
  from app.modules.schedule.models import ShiftTemplate, ShiftAssignment
  ```
- **修改範圍:** 僅補 model imports，不動其他 env.py 架構

---

## 6. schemas.py Alignment Summary

| 欄位 | 修改前 | 修改後 | 原因 |
|------|--------|--------|------|
| ShiftTemplateBase.company_id | int | str | models.py 為 String(255) |
| ShiftTemplateRead.id | int | UUID | models.py 為 UUID PK |
| ShiftAssignmentBase.company_id | int | str | models.py 為 String(255) |
| ShiftAssignmentBase.user_id | int | UUID | models.py 為 UUID FK |
| ShiftAssignmentBase.shift_template_id | int | UUID | models.py 為 UUID FK |
| ShiftAssignmentRead.id | int | UUID | models.py 為 UUID PK |
| ShiftAssignmentUpdate.shift_template_id | Optional[int] | Optional[UUID] | models.py 為 UUID FK |

---

## 7. Upgrade Validation Result

```
INFO [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO [alembic.runtime.migration] Will assume transactional DDL.
INFO [alembic.runtime.migration] Running upgrade 009_wp_11_08 -> 010_wp_s1_02,
     WP-S1-02: Create schedule tables (shift_templates, shift_assignments)
```

- alembic upgrade head: **PASS**
- alembic_version: `010_wp_s1_02` ✓
- shift_templates exists: **YES** ✓
- shift_assignments exists: **YES** ✓
- uq_shift_templates_company_code: **YES** (type=u) ✓
- ck_shift_assignments_status: **YES** (type=c) ✓
- fk_shift_templates_company_id: **YES** (type=f) ✓
- fk_shift_assignments_company_id: **YES** (type=f) ✓
- fk_shift_assignments_user_id: **YES** (type=f) ✓
- fk_shift_assignments_template_id: **YES** (type=f) ✓
- Indexes (10 total): **ALL PRESENT** ✓

---

## 8. Downgrade Design Review

### Drop Order
1. 先 drop indexes for shift_assignments
2. drop shift_assignments（有 FK 指向 shift_templates，必須先刪）
3. drop indexes for shift_templates
4. drop shift_templates

### 安全性評估
- **safe drop order confirmed: YES**
- shift_assignments.shift_template_id 是 RESTRICT FK，必須先刪 assignments 才能刪 templates
- downgrade 不會留下孤立 FK 或相依性問題
- 本輪未實際執行 downgrade（非強制要求），downgrade 寫法已靜態審查確認正確

---

## 9. Scope Control Confirmation

| 項目 | 狀態 |
|------|------|
| main.py changed | NO |
| frontend changed | NO |
| attendance/leave/audit/backup/notifications changed | NO |
| old migrations modified | NO |
| schedule router 掛進 main.py | NO |
| schedule API endpoints 新增 | NO |
| repo.py / service.py 功能實作 | NO |
| git stash/restore used | NO |

---

## 10. Final Verdict

**WP-S1-02 COMPLETE: YES**

所有必要工作項目均已完成並驗證：
- Migration 建立 ✓
- upgrade head PASS ✓
- 資料表與 constraints 驗證 ✓
- env.py 修正 ✓
- schemas.py UUID 對齊 ✓
- docs 與治理文件同步 ✓
- Scope lock 全程遵守 ✓

---

## 11. Recommended Next Step

**WP-S1-03 — Schedule Module CRUD Implementation**

建議內容：
1. 實作 `repo.py`：ShiftTemplate CRUD + ShiftAssignment CRUD（取代 stub）
2. 實作 `service.py`：業務邏輯層（tenant isolation, status validation）
3. 建立 `router.py` 並掛進 `main.py`
4. 補齊 API endpoints（GET/POST/PATCH/DELETE）
5. 補 unit tests（pytest）

前提已具備：
- ✓ Models 已對齊（WP-S1-01A）
- ✓ Schemas UUID 已對齊（WP-S1-02）
- ✓ 資料表已存在於 DB（WP-S1-02）
