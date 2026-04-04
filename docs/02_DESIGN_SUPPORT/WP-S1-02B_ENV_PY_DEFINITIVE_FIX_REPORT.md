# WP-S1-02B — env.py Definitive Fix Report

**票號:** WP-S1-02B — env.py Definitive Fix  
**執行日期:** 2026-03-19  
**執行者:** AI Agent (Cursor)  
**狀態:** COMPLETE — ALEMBIC SAFE = YES

---

## 1. Objective

正式修復 `backend/alembic/env.py`，讓 Alembic 恢復為可持續使用的正式狀態。
涵蓋所有應由 Alembic 管理的 ORM 模組，並驗證 `alembic current` / `alembic upgrade head` 正常運作。

---

## 2. Files Read

| 檔案 | 說明 |
|------|------|
| docs/WP-S1-02A_ENV_PY_INTEGRITY_AUDIT.md | 審計報告，確認問題範圍 |
| backups/20260305_165448/alembic/env.py | 舊備份版本參考（不作為最終依據）|
| backend/alembic.ini | DB URL 確認 |
| backend/alembic/versions/*.py | Migration chain 確認 |
| backend/app/modules/*/models.py | 8 個模組的 ORM class 完整盤點 |
| backend/app/core/database.py | Base 來源確認 |

---

## 3. Files Changed

| 檔案 | 變更類型 | 說明 |
|------|----------|------|
| backend/alembic/env.py | 重建 | 從 0 bytes 重建為 5464 bytes 正式版 |
| backend/alembic/versions/010_wp_s1_02_create_schedule_tables.py.tmp | 刪除 | 殘留暫存檔清除 |
| docs/WP-S1-02A_ENV_PY_INTEGRITY_AUDIT.md | Append | 加入 closure note |
| docs/WP-S1-02B_ENV_PY_DEFINITIVE_FIX_REPORT.md | 新建 | 本報告 |
| docs/03_WP_CONTROL/NEXT_WP_TICKET.md | Append | WP-S1-02B 完成記錄 |
| docs/03_WP_CONTROL/GATE_PROGRESS_TRACKER.md | Append | Gate 結果 |
| docs/02_DEVELOPMENT_STATUS/WORKSTREAM_STATUS_LEDGER.md | Append | Ledger entry |
| docs/02_DEVELOPMENT_STATUS/MODULE_STATUS_MATRIX.md | Append | 狀態更新 |
| docs/02_DEVELOPMENT_STATUS/CURRENT_SYSTEM_STATE.md | Append | 系統狀態更新 |

---

## 4. Root Cause / Risk Context

### env.py 持續被清空的現象
- WP-S1-02 執行前：env.py 為 0 bytes
- WP-S1-02 寫入後（2026-03-18 21:07，2992 bytes）
- WP-S1-02B 執行時（2026-03-19 08:44）：env.py 再次為 0 bytes

**根本原因：** 未能完全確認，但時間點（08:44）與 IDE 啟動 / 檔案同步行為高度相關。
可能是某個 file watcher 或 IDE 自動操作導致。

### WP-S1-02 重建不完整的問題
- 備份版本（2026-03-05）只有 notifications + attendance
- WP-S1-02 重建時補了 leave + schedule，但漏掉 auth / audit / tenants / customer_service
- autogenerate coverage 只有 50%（4/8 模組）

### 本輪修正策略
- 不依賴備份，從目前專案實際結構重建
- 顯式 import 所有 8 個 ORM 模組的全部 model classes
- 靜態測試通過後才 cp 到正式路徑

---

## 5. Final env.py Structure Summary

```
backend/alembic/env.py  (5464 bytes)
├── docstring: 模組說明 + metadata strategy + 已納入/不納入模組清單
├── sys.path: Path(__file__).resolve().parent.parent → backend/
├── imports: Base, settings, 8 個模組全部 model classes
├── config: context.config + settings.database_url 覆蓋
├── fileConfig: 標準 logging 設定
├── target_metadata: Base.metadata
├── run_migrations_offline(): 標準實作
└── run_migrations_online(): 標準實作，pool.NullPool
```

---

## 6. Module Coverage Summary

| 模組 | Tables 數 | ORM Classes | env.py 納入 | 說明 |
|------|-----------|-------------|-------------|------|
| tenants | 2 | Tenant, CompanyEntitlement | YES | |
| auth | 5 | User, Membership, Role, Permission, RolePermission | YES | |
| notifications | 1 | Notification | YES | |
| audit | 2 | AuditRetentionPolicy, AuditLog | YES | |
| attendance | 6 | AttendancePolicy, AttendanceSession, AttendancePunch, AttendanceOutCheckpoint, AttendanceRecord, AllowedLocation | YES | |
| leave | 4 | LeaveType, LeaveApprovalPolicy, LeaveRequest, LeaveApprovalLog | YES | |
| schedule | 2 | ShiftTemplate, ShiftAssignment | YES | |
| customer_service | 1 | SupportCompanyAssignment | YES | |
| backup | 0 | — | NO | 無 models.py，無 ORM table，不屬 Alembic 管理 |

**Coverage: 8/8 模組（100%）**  
**Base.metadata tables: 23 個（全部正確登記）**

---

## 7. Metadata Strategy

**策略：顯式 import + 共同 Base**

- 所有模組均繼承 `app.core.database.Base`
- `env.py` 透過顯式 import 逐一列出所有 model classes
- `target_metadata = Base.metadata`
- 不依賴中央 `app/db/base.py`（專案目前無此設計）
- 新增模組時，需在 env.py 的顯式 import 區段補上對應 class

**驗證結果：**
```
Base.metadata.tables = [
  allowed_locations, attendance_out_checkpoints, attendance_policies,
  attendance_punches, attendance_records, attendance_sessions,
  audit_logs, audit_retention_policies, company_entitlements,
  leave_approval_logs, leave_approval_policies, leave_requests, leave_types,
  notifications, permissions, role_permissions, roles,
  shift_assignments, shift_templates, support_company_assignments,
  tenants, user_company_memberships, users
]  # 共 23 個 tables
```

---

## 8. Cleanup Summary

| 項目 | 操作 | 結果 |
|------|------|------|
| versions/010_wp_s1_02_create_schedule_tables.py.tmp | 刪除 | 成功 |
| versions/001_create_attendance_domain_v2.py.deprecated | 保留 | 依審計報告，此檔不在 chain 中，安全；本輪不處理 |

---

## 9. Validation Result

### Static Validation
- env.py 存在且非空：**YES**（5464 bytes）
- Python import 測試：**PASS**（ALL_IMPORTS_OK）
- Base.metadata tables：**23 個**（全部正確）

### Runtime Validation
```
$ alembic current
010_wp_s1_02 (head)
INFO [alembic.runtime.migration] Context impl PostgresqlImpl.
EXIT=0
```
**alembic current: PASS**

```
$ alembic upgrade head
INFO [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO [alembic.runtime.migration] Will assume transactional DDL.
EXIT=0
```
**alembic upgrade head: PASS（no-op，DB 已在 head）**

---

## 10. Scope Control Confirmation

| 項目 | 狀態 |
|------|------|
| 新 migration 建立 | NO |
| 既有 migration 修改 | NO |
| models 業務定義修改 | NO |
| main.py 修改 | NO |
| frontend 修改 | NO |
| git stash/restore 使用 | NO |
| schedule/attendance/leave/audit 等 production code 修改 | NO |

---

## 11. Final Verdict

**ALEMBIC SAFE: YES**

- env.py 正式重建完成（5464 bytes）
- 8/8 模組全部納入（100% coverage）
- Base.metadata 23 tables 全部正確登記
- alembic current: PASS
- alembic upgrade head: PASS
- .tmp 殘留清除完成
- Scope lock 全程遵守

---

## 12. Recommended Next Step

**WP-S1-03 — Schedule Module CRUD Implementation**

前提已全備：
- Models 對齊（WP-S1-01A）✓
- Schemas UUID 對齊（WP-S1-02）✓
- 資料表存在於 DB（WP-S1-02）✓
- Alembic 基礎設施穩定（WP-S1-02B）✓

建議工作內容：
1. 實作 `repo.py`（ShiftTemplate + ShiftAssignment CRUD）
2. 實作 `service.py`（業務邏輯、tenant isolation）
3. 建立 `router.py` 並掛進 `main.py`
4. 補 API endpoints
5. 補 unit tests

**附加建議：** 調查 env.py 被自動清空的根本原因，避免未來再次發生。

---

**最後更新:** 2026-03-19  
**更新原因:** WP-S1-02B COMPLETE
