# WP-S1-03 CRUD Core Execution Report

**票號:** WP-S1-03 — Schedule Module CRUD Core  
**執行日期:** 2026-03-19  
**執行者:** AI Agent (Cursor)  
**狀態:** COMPLETE — Smoke Test 15/15 PASS

---

## 1. Objective

將 Schedule 模組從「foundation + migration 已完成」推進到「可被未來 API 層使用的 CRUD Core」。
實作 `repo.py` + `service.py`，取代 WP-S1-01 的 stub（NotImplementedError）。

---

## 2. Files Read

| 檔案 | 說明 |
|------|------|
| backend/app/modules/schedule/models.py | 欄位與 constraint 定義依據 |
| backend/app/modules/schedule/schemas.py | UUID 型別確認 |
| backend/app/modules/schedule/repo.py | 原 stub 內容 |
| backend/app/modules/schedule/service.py | 原 stub 內容 |
| backend/app/modules/attendance/repo.py | 風格參考（tenant isolation pattern）|
| backend/app/modules/leave/repo.py | 風格參考 |
| backend/app/modules/leave/service.py | 風格參考 |

---

## 3. Files Changed

| 檔案 | 變更類型 | 大小 | 說明 |
|------|----------|------|------|
| backend/app/modules/schedule/repo.py | 重寫 | 9436 bytes | stub → CRUD Core |
| backend/app/modules/schedule/service.py | 重寫 | 15037 bytes | stub → CRUD Core |
| backend/app/modules/schedule/docs.md | Append | — | WP-S1-03 record |
| docs/WP-S1-03_CRUD_CORE_EXECUTION_REPORT.md | 新建 | — | 本報告 |
| 5 份治理文件 | Append | — | 狀態更新 |

**schemas.py: 未修改**（WP-S1-02 已對齊，型別完全正確）

---

## 4. Repo Implementation Summary

### ShiftTemplateRepo
| 方法 | 說明 |
|------|------|
| `get_by_id(template_id, company_id)` | 依 PK + company_id，Tenant Isolation |
| `get_by_code(code, company_id)` | 依 code + company_id，uniqueness check 用 |
| `list_by_company(company_id, active_only)` | 列出公司班別模板，可篩選 is_active |
| `create(obj)` | 建立並 commit + refresh |
| `update(obj)` | 更新 updated_at 並 commit |
| `set_active(template_id, company_id, is_active)` | 啟用/停用旗標 |

### ShiftAssignmentRepo
| 方法 | 說明 |
|------|------|
| `get_by_id(assignment_id, company_id)` | 依 PK + company_id，Tenant Isolation |
| `list_by_user_date_range(...)` | 依使用者+日期範圍 |
| `list_by_company_date(company_id, work_date)` | 依公司+單日 |
| `list_by_company(company_id, start_date, end_date)` | 全公司+可選日期範圍 |
| `create(obj)` | 建立並 commit + refresh |
| `update(obj)` | 更新 updated_at 並 commit |
| `cancel(assignment_id, company_id)` | 設定 status=cancelled |

---

## 5. Service Implementation Summary

### ShiftTemplate Service Methods
| 方法 | 業務規則 |
|------|----------|
| `create_shift_template` | company_id 一致性檢查；code 唯一性檢查（409）|
| `get_shift_template` | 404 if not found |
| `list_shift_templates` | active_only 篩選 |
| `update_shift_template` | 部分更新，404 if not found |
| `deactivate_shift_template` | is_active=False，404 if not found |
| `activate_shift_template` | is_active=True，404 if not found |

### ShiftAssignment Service Methods
| 方法 | 業務規則 |
|------|----------|
| `create_shift_assignment` | company_id 一致性；template 同 company + is_active 驗證；422 if invalid |
| `get_shift_assignment` | 404 if not found |
| `list_assignments_for_user` | 依 user_id + date range |
| `list_assignments_for_date` | 依單日 |
| `list_assignments` | 全公司 + 可選 date range |
| `update_shift_assignment` | 已取消不可更新（409）；template 變更需同 company + active 驗證 |
| `cancel_shift_assignment` | 已取消再取消 409；否則 status=cancelled |

---

## 6. Schema Alignment Summary

- schemas.py **未修改**
- WP-S1-02 已完成 UUID 對齊：`company_id: str`、`id/user_id/shift_template_id: UUID`
- service 層使用 `ShiftTemplateRead.model_validate(obj)` 序列化（Pydantic v2）

---

## 7. Tenant Isolation Rules Implemented

1. 所有 repo 查詢均強制 `WHERE company_id = ?`（使用 `sqlalchemy.and_`）
2. 不允許只靠 `id` 查詢（所有 get_by_id 均帶 company_id）
3. 建立 assignment 時，驗證 `shift_template.company_id == company_id`
4. 更新 assignment 時，若變更 template，驗證新 template 屬於同 company
5. list 查詢預設限制在 company scope
6. company_id mismatch → 403 Forbidden
7. template 不在同 company → 422 Unprocessable

---

## 8. Smoke Validation Result

```
=== WP-S1-03 Smoke Test Results ===
1. create_shift_template: PASS
2. duplicate_code_check: PASS (HTTPException)
3. get_shift_template by id: PASS
4. list_shift_templates: PASS (1 found)
5. update_shift_template: PASS
6. deactivate_shift_template: PASS
7. activate_shift_template: PASS
8. create_shift_assignment: PASS
9. get_shift_assignment by id: PASS
10. list_assignments_for_user: PASS (1 found)
11. list_assignments_for_date: PASS (1 found)
12. update_shift_assignment: PASS
13. cancel_shift_assignment: PASS
14. double_cancel_check: PASS (HTTPException)
15. cross_tenant_template_check: PASS (HTTPException)

Total: 15 | PASS: 15 | FAIL: 0
ALL_SMOKE_PASS
```

**DeprecationWarning:** `HTTP_422_UNPROCESSABLE_ENTITY` 已更名為 `HTTP_422_UNPROCESSABLE_CONTENT`（FastAPI/Starlette 版本差異）。不影響功能，記錄備查，後續可在 WP-S1-04 修正。

---

## 9. Scope Control Confirmation

| 項目 | 狀態 |
|------|------|
| api.py 路由行為修改 | NO |
| main.py include_router | NO |
| migration 修改 | NO |
| env.py 修改 | NO |
| frontend 修改 | NO |
| attendance/leave/audit 等其他模組修改 | NO |
| git stash/restore 使用 | NO |
| 排班演算法 / 衝突偵測 | NO |
| 權限系統整合 | NO |

---

## 10. Final Verdict

**WP-S1-03 CRUD CORE COMPLETE: YES**

- repo.py: stub → 完整 CRUD Core（9436 bytes）
- service.py: stub → 完整業務邏輯（15037 bytes）
- Tenant Isolation: 全面實作
- Smoke Test: 15/15 PASS
- schemas.py: 無需修改（已對齊）
- Scope lock: 全程遵守

---

## 11. Recommended Next Step

**WP-S1-04 — Schedule Module API Layer**

建議工作內容：
1. 實作 `router.py`（FastAPI APIRouter）
2. 建立 ShiftTemplate CRUD endpoints（GET/POST/PATCH）
3. 建立 ShiftAssignment CRUD endpoints（GET/POST/PATCH/cancel）
4. 將 schedule router 掛進 `main.py`
5. 修正 `HTTP_422_UNPROCESSABLE_ENTITY` → `HTTP_422_UNPROCESSABLE_CONTENT` deprecation warning
6. 補 API 層 request/response validation
7. 考慮補 pytest integration tests

**附記：** 本輪發現 FastAPI status code deprecation warning，建議 WP-S1-04 一併修正。

---

**最後更新:** 2026-03-19  
**更新原因:** WP-S1-03 COMPLETE
