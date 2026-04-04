# LEGACY_ROLE_CLEANUP_PHASE1_REPORT

- 日期：2026-03-24
- 票據範圍：Phase 1A + 1B + 1C（收尾）
- 原則：僅移除 `admin` / `hr` 的指定 legacy compatibility 路徑；保留 `manager`、`system_admin`

---

## 1. Summary

本報告收斂 Legacy Role Cleanup Phase 1 的可交付狀態：

- Phase 1A（`dependencies.py`）：
  - 移除 `admin` / `hr` 的顯式 compatibility mapping
  - 保留 `manager` 與 `system_admin`
- Phase 1B（`attendance/api.py`）：
  - `GET /api/v1/attendance/sessions` 的 legacy 管理者分支由
    `("admin", "manager", "hr")` 收斂為僅 `"manager"`
- Phase 1C（本票）：
  - 補齊最小測試與收尾文件，不新增 production cleanup

---

## 2. What Phase 1 Removed

### 2.1 dependencies mapping（Phase 1A）
- 移除：`"admin": UserRole.COMPANY_USER`
- 移除：`"hr": UserRole.COMPANY_USER`

### 2.2 attendance sessions branch（Phase 1B）
- 移除 sessions 查他人分支中的 `admin` / `hr` 可通行條件
- 僅保留 `manager` 可通行

---

## 3. What Phase 1 Intentionally Kept

1. `manager`：
   - 在 `dependencies.py` 仍映射為 `COMPANY_USER`
   - 在 `attendance/sessions` 仍可走管理者查詢他人分支
2. `system_admin`：
   - 在 `dependencies.py` 仍映射至 `SUPER_ADMIN`
3. 其他 production 行為：
   - 本票未擴及其他 endpoint、migration、資料庫資料

---

## 4. Files Changed by Phase

### 4.1 Phase 1A
- `backend/app/core/dependencies.py`

### 4.2 Phase 1B
- `backend/app/modules/attendance/api.py`

### 4.3 Phase 1C（tests/docs sync only）
- `backend/app/core/tests/test_legacy_role_cleanup_phase1.py`（新增）
- `backend/app/modules/attendance/tests/test_legacy_role_cleanup_phase1b.py`（新增）
- `docs/02_DEVELOPMENT_STATUS/LEGACY_ROLE_CLEANUP_PHASE1_REPORT.md`（新增）
- `docs/01_ARCHITECTURE/ROLE_NAMING_SOURCE_OF_TRUTH.md`（小幅狀態註記）

---

## 5. Validation Executed

執行最小測試範圍（backend venv）：

```bash
/opt/attendance-system/backend/venv/bin/pytest -q   /opt/attendance-system/backend/app/core/tests/test_legacy_role_cleanup_phase1.py   /opt/attendance-system/backend/app/modules/attendance/tests/test_legacy_role_cleanup_phase1b.py
```

結果：`5 passed`（僅有既存 warning，無新增失敗）。

---

## 6. Remaining Deferred Risks

1. `manager` 仍屬 legacy-but-retained，仍有 runtime 可達性；不在本階段移除。
2. `system_admin -> SUPER_ADMIN` 為 auth-critical 映射，仍保留。
3. 全面 legacy cleanup（含 `manager` / `system_admin`）仍需額外 token/runtime 證據與獨立治理票。

---

## 7. Closure Decision

- Phase 1（限定範圍：`admin` / `hr`）已完成最小可交付收尾。
- 本報告不包含下一階段（manager/system_admin）清理決策。
