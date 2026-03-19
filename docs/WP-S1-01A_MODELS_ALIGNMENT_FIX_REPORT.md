# WP-S1-01A Execution Report — Schedule Models Alignment Fix

**票號:** WP-S1-01A  
**性質:** Models Alignment Fix（Blocking Issue Resolution）  
**完成日期:** 2026-03-18  
**執行者:** AI session（Cursor）  
**前置條件:** WP-S1-01 COMPLETE ✅；WP-S1-02 Pre-Migration Audit NOT READY

---

## 1. Files Read

| 檔案 | 說明 |
|------|------|
| `docs/WP-S1-02_PRE_MIGRATION_AUDIT.md` | 唯一修正依據（B1/B2/M2/M3/M4/M6）|
| `backend/app/modules/schedule/models.py` | 待修正目標 |
| `backend/app/modules/schedule/docs.md` | 待同步更新 |
| `backend/app/modules/attendance/models.py` | 對齊基準（UUID PK、PGUUID、ForeignKeyConstraint）|
| `backend/app/modules/leave/models.py` | 對齊基準（UUID PK、String(255) company_id、ForeignKeyConstraint）|
| `backend/app/modules/audit/models.py` | 對齊基準（String company_id 慣例確認）|
| `backend/app/main.py` | Router 掛載狀況確認 |
| 5 份治理文件 | 狀態同步參考 |

---

## 2. Files Changed

| 檔案 | 操作 | 說明 |
|------|------|------|
| `backend/app/modules/schedule/models.py` | 修改 | B1/B2/M2/M3/M4/M6 全部修正 |
| `backend/app/modules/schedule/docs.md` | 更新 | 反映 WP-S1-01A 所有變更（v1.1）|
| `docs/WP-S1-01A_MODELS_ALIGNMENT_FIX_REPORT.md` | 新建 | 本報告 |
| 治理文件（5 份）| append-only | WP-S1-01A COMPLETE 狀態同步 |

---

## 3. Blocking Fix Result

### B1 — company_id: **FIXED**

| 項目 | 修正前 | 修正後 |
|------|--------|--------|
| 型別 | `Integer` | `String(255)` |
| FK | 無 | `ForeignKeyConstraint(['company_id'], ['tenants.id'], ondelete='CASCADE')` |
| 定義位置 | 行內 Column 屬性 | `__table_args__` |

**驗證結果：**
```
ShiftTemplate.company_id type: String | length: 255
ShiftAssignment.company_id type: String | length: 255
ShiftTemplate FKs: [('company_id', 'tenants.id')]
ShiftAssignment FKs: [('company_id', 'tenants.id'), ...]
```

### B2 — user_id: **FIXED**

| 項目 | 修正前 | 修正後 |
|------|--------|--------|
| 型別 | `Integer` | `UUID(as_uuid=True)` |
| FK | 無 | `ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')` |
| 定義位置 | 行內 Column 屬性 | `__table_args__` |

**驗證結果：**
```
ShiftAssignment.user_id type: UUID
ShiftAssignment FKs: [..., ('user_id', 'users.id')]
```

---

## 4. Minor Fix Result

### M2 — PK alignment: **FIXED**

**決策：** 採用 UUID PK + `gen_random_uuid()`，與 attendance/leave 全系統慣例一致。  
**原因：** attendance、leave 所有新式模型均使用 UUID PK；Integer 僅在舊式 Phase 4 模型（AttendanceRecord, AuditLog）中出現，新模組應對齊 UUID。

**驗證結果：**
```
ShiftTemplate.id type: UUID
ShiftAssignment.id type: UUID
```

### M3 — FK style alignment: **FIXED**

**決策：** 全面改用 `__table_args__` + `ForeignKeyConstraint`，移除行內 `ForeignKey()`。  
**原因：** attendance/leave 所有 FK 均使用 ForeignKeyConstraint，一致性優先。  
**影響：** shift_template_id FK（RESTRICT）也已改為 ForeignKeyConstraint。

### M4 — UniqueConstraint(company_id, code): **ADDED**

`UniqueConstraint('company_id', 'code', name='uq_shift_templates_company_code')` 已加入 ShiftTemplate `__table_args__`。  
**驗證結果：**
```
ShiftTemplate UniqueConstraints: ['uq_shift_templates_company_code']
```

### M6 — Enum readiness: **CLARIFIED**

**決策：** `AssignmentStatus` 從 SQLAlchemy `Enum` type 改為 `String(20)` + `CheckConstraint`。  
**原因：** 與 attendance session status 慣例一致；避免 PostgreSQL `CREATE TYPE` 在 migration 中的複雜度（ALTER TYPE 有限制）。  
**應用層安全：** 使用 `ASSIGNMENT_STATUS_*` 常數（module-level），避免 magic string。  
**WP-S1-02 migration 注意：** 使用 `sa.String(20)` + `sa.CheckConstraint("status IN ('scheduled', 'confirmed', 'cancelled')")`，無需 `sa.Enum()`。

**驗證結果：**
```
ShiftAssignment.status type: String
ShiftAssignment CheckConstraints: ['ck_shift_assignments_status']
AssignmentStatus values: ('scheduled', 'confirmed', 'cancelled')
```

---

## 5. Docs Sync

### schedule/docs.md updated: **YES**

**Updated sections:**
- Section 2：新增 WP-S1-01A 交付項目
- Section 3：完整更新資料模型（UUID PK、String company_id、UUID user_id、CheckConstraint、所有 FK/Index/Constraint 列表）
- Section 3.4：AssignmentStatus 實作說明（String + CheckConstraint 原因說明）
- Section 4.5：明確列出 WP-S1-01A 中未修改項目（schemas.py、env.py 等）
- Section 7：更新給未來 AI 的說明
- 版本號更新為 v1.1

---

## 6. Validation Result

所有 smoke test 項目通過（`/opt/attendance-system/backend/venv/bin/python3 /tmp/smoke_s1a.py`）：

```
IMPORT_OK
ShiftTemplate table: shift_templates
ShiftAssignment table: shift_assignments
ShiftTemplate.id type: UUID
ShiftAssignment.id type: UUID
ShiftTemplate.company_id type: String | length: 255
ShiftAssignment.company_id type: String | length: 255
ShiftAssignment.user_id type: UUID
ShiftAssignment.status type: String
AssignmentStatus values: ('scheduled', 'confirmed', 'cancelled')
ShiftTemplate FKs: [('company_id', 'tenants.id')]
ShiftAssignment FKs: [('company_id', 'tenants.id'), ('shift_template_id', 'shift_templates.id'), ('user_id', 'users.id')]
ShiftTemplate UniqueConstraints: ['uq_shift_templates_company_code']
ShiftAssignment CheckConstraints: ['ck_shift_assignments_status']
main.py: schedule NOT in router list (CORRECT)
ALL_CHECKS_PASS
```

---

## 7. Scope Control Confirmation

| 項目 | 結果 |
|------|------|
| migration changed | **NO** |
| main.py changed | **NO** |
| frontend changed | **NO** |
| attendance / leave / audit / backup / notifications changed | **NO** |
| env.py changed | **NO** |
| repo.py / service.py / api.py / schemas.py behavior changed | **NO** |
| git stash / restore used | **NO** |

---

## 8. Final Readiness Verdict

### READY FOR WP-S1-02: **YES**

**Pre-Migration Audit 中所有 Blocking Issues 已解決：**

| Issue | 狀態 |
|-------|------|
| B1: company_id Integer → String(255) + FK | ✅ RESOLVED |
| B2: user_id Integer → UUID + FK | ✅ RESOLVED |

**剩餘 Minor Issues（不阻塞 WP-S1-02）：**

| Issue | 狀態 |
|-------|------|
| M1: env.py 補 schedule import | 待 WP-S1-02 內處理 |
| schemas.py UUID 型別同步 | 待 WP-S1-02 或 WP-S1-03 處理 |

---

## 9. Alignment Basis Declaration

本票採用以下對齊基準，優先以「現有專案一致性」為最高原則：

| 項目 | 基準來源 |
|------|----------|
| UUID PK + gen_random_uuid() | attendance/models.py（AttendancePolicy, AttendanceSession, AttendancePunch）|
| String(255) company_id | attendance/models.py + leave/models.py + audit/models.py |
| UUID user_id | attendance/models.py（AttendanceSession.user_id）|
| ForeignKeyConstraint 在 __table_args__ | attendance/models.py + leave/models.py |
| String(20) + CheckConstraint status | attendance/models.py（AttendanceSession.status = String(20) + CheckConstraint）|
| DateTime(timezone=True) + server_default=NOW() | attendance/models.py + leave/models.py |

---

## 10. Recommended Next Step

**WP-S1-02 — Schedule Module Migration**

- 建立 `010_wp_s1_02_create_schedule_tables.py`
- `revision = '010_wp_s1_02'`，`down_revision = '009_wp_11_08'`
- 手動撰寫 `op.create_table('shift_templates', ...)` 和 `op.create_table('shift_assignments', ...)`
- 在 `alembic/env.py` 補上：`from app.modules.schedule.models import ShiftTemplate, ShiftAssignment`
- 同步更新 `schemas.py` 的 UUID 型別（`id` 欄位由 `int` → `UUID`）
- 執行 `alembic upgrade head` 並驗證 21 → 23 tables

---

**結案確認：** WP-S1-01A Schedule Models Alignment Fix COMPLETE  
**Blocking Issues：** 全部已解決（B1 + B2 FIXED）  
**READY FOR WP-S1-02：YES**  
**文件版本：** v1.0  
**建立日期：** 2026-03-18
