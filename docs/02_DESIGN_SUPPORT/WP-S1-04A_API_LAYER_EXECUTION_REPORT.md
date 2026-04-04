# WP-S1-04A — Schedule Module API Layer Execution Report

**票號:** WP-S1-04A — Schedule Module API Layer (router file only, not mounted)  
**執行日期:** 2026-03-19  
**執行者:** AI Agent (Cursor)  
**狀態:** COMPLETE — router ready, NOT mounted in main.py

---

## 1. Objective

實作 `backend/app/modules/schedule/api.py` 的 CRUD endpoints，
串接既有 `service.py`，不重複商業邏輯。
Router 定義完成但尚未掛入 `main.py`（WP-S1-04B 執行）。

---

## 2. Files Read

| 檔案 | 說明 |
|------|------|
| backend/app/modules/schedule/api.py | 原骨架（1556 bytes）|
| backend/app/modules/schedule/schemas.py | Request/response schema 確認 |
| backend/app/modules/schedule/service.py | Service method signatures 確認 |
| backend/app/modules/leave/api.py | API 風格參考 |
| backend/app/modules/attendance/api.py | API 風格參考 |
| backend/app/core/dependencies.py | get_actor_with_company 確認 |
| backend/app/core/scope.py | Actor.active_company_id 確認 |
| backend/app/core/features.py | FeatureKeys 確認（schedule.core 尚未定義）|
| backend/app/core/feature_service.py | FeatureDisabledError 確認 |

---

## 3. Files Changed

| 檔案 | 變更類型 | 大小 | 說明 |
|------|----------|------|------|
| backend/app/modules/schedule/api.py | 重寫 | 10948 bytes | 骨架 → 完整 API Layer |
| backend/app/modules/schedule/docs.md | Append | — | WP-S1-04A record |
| docs/WP-S1-04A_API_LAYER_EXECUTION_REPORT.md | 新建 | — | 本報告 |
| 5 份治理文件 | Append | — | 狀態更新 |

**schemas.py: 未修改**（現有 schema 已足夠支援 API layer）

---

## 4. API Endpoint Summary

### ShiftTemplate（6 endpoints）

| Method | Path | Status Code | 說明 |
|--------|------|-------------|------|
| POST | /api/v1/schedule/shift-templates | 201 | 建立模板，code 重複 → 409 |
| GET | /api/v1/schedule/shift-templates | 200 | 列出（?active_only=true）|
| GET | /api/v1/schedule/shift-templates/{id} | 200 | 取得單筆，不存在 → 404 |
| PATCH | /api/v1/schedule/shift-templates/{id} | 200 | 部分更新 |
| POST | /api/v1/schedule/shift-templates/{id}/activate | 200 | 啟用 |
| POST | /api/v1/schedule/shift-templates/{id}/deactivate | 200 | 停用 |

### ShiftAssignment（5 endpoints）

| Method | Path | Status Code | 說明 |
|--------|------|-------------|------|
| POST | /api/v1/schedule/shift-assignments | 201 | 建立指派，跨 tenant → 422 |
| GET | /api/v1/schedule/shift-assignments | 200 | 列出（多種過濾）|
| GET | /api/v1/schedule/shift-assignments/{id} | 200 | 取得單筆 |
| PATCH | /api/v1/schedule/shift-assignments/{id} | 200 | 部分更新，已取消 → 409 |
| POST | /api/v1/schedule/shift-assignments/{id}/cancel | 200 | 取消，重複取消 → 409 |

### list assignments 過濾邏輯
優先順序：
1. `work_date`（單日）+ 可選 `user_id`
2. `user_id` + `start_date` + `end_date`（必須三者齊備）
3. `start_date` / `end_date`（全公司日期範圍）
4. 無條件（列出全公司）

### status change 設計決策
- `PATCH /shift-assignments/{id}` 可直接更新 status 欄位
- `POST /shift-assignments/{id}/cancel` 是獨立的 cancel 動作（語意更清楚）
- 不額外建立 `/change-status` endpoint（cancel 已覆蓋主要需求）

### Feature Gate 決策
- 本輪不加 schedule.core feature gate
- 原因：`FeatureKeys` 目前未定義 `SCHEDULE_CORE`，修改 features.py 超出本票 scope
- 後續票可在掛載 router 時一併加入

---

## 5. Schema Alignment Summary

- schemas.py **未修改**
- 現有 schema 已完全支援 API layer：
  - `ShiftTemplateCreate` / `ShiftTemplateUpdate` / `ShiftTemplateRead`
  - `ShiftAssignmentCreate` / `ShiftAssignmentUpdate` / `ShiftAssignmentRead`
  - `AssignmentStatusSchema`
- UUID 欄位在 WP-S1-02 已對齊，company_id 為 str

---

## 6. Route Validation Result

```
IMPORT_OK
router prefix: /api/v1/schedule
router tags: ['schedule']
Total routes: 11
  ['POST'] /api/v1/schedule/shift-templates
  ['GET']  /api/v1/schedule/shift-templates
  ['GET']  /api/v1/schedule/shift-templates/{template_id}
  ['PATCH'] /api/v1/schedule/shift-templates/{template_id}
  ['POST'] /api/v1/schedule/shift-templates/{template_id}/activate
  ['POST'] /api/v1/schedule/shift-templates/{template_id}/deactivate
  ['POST'] /api/v1/schedule/shift-assignments
  ['GET']  /api/v1/schedule/shift-assignments
  ['GET']  /api/v1/schedule/shift-assignments/{assignment_id}
  ['PATCH'] /api/v1/schedule/shift-assignments/{assignment_id}
  ['POST'] /api/v1/schedule/shift-assignments/{assignment_id}/cancel
main.py: schedule NOT mounted (CORRECT)
EXIT=0
```

---

## 7. Scope Control Confirmation

| 項目 | 狀態 |
|------|------|
| main.py include_router | NO |
| repo.py 修改 | NO |
| service.py 修改 | NO |
| migration 修改 | NO |
| env.py 修改 | NO |
| frontend 修改 | NO |
| attendance/leave/audit 等其他模組修改 | NO |
| features.py 修改 | NO |
| git stash/restore 使用 | NO |

---

## 8. Final Verdict

**WP-S1-04A API LAYER READY: YES**

- api.py: 骨架 → 完整 API Layer（10948 bytes）
- 11 endpoints 全部正確定義
- router import: PASS
- main.py: schedule NOT mounted（CORRECT）
- schemas.py: 無需修改
- Scope lock: 全程遵守

---

## 9. Recommended Next Step

**WP-S1-04B — Schedule Router Mount (main.py)**

建議工作內容：
1. 在 `backend/app/main.py` 加入 `app.include_router(schedule_router)`
2. 加入 `FeatureKeys.SCHEDULE_CORE` 定義（features.py 最小修正）
3. api.py 補 feature gate（`_require_schedule_feature`）
4. 確認 OpenAPI docs 正確顯示 schedule endpoints
5. 做最小 end-to-end 驗證（curl 或 httpx）

**附記：** `HTTP_422_UNPROCESSABLE_ENTITY` deprecation warning 仍存在於 service.py，建議 WP-S1-04B 一併修正為 `HTTP_422_UNPROCESSABLE_CONTENT`。

---

**最後更新:** 2026-03-19  
**更新原因:** WP-S1-04A COMPLETE
