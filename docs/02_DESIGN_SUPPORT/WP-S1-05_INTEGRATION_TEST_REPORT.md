# WP-S1-05 Integration Test Execution Report

**票號:** WP-S1-05 — Schedule Integration Testing + Entitlement Setup  
**執行日期:** 2026-03-19  
**執行者:** AI Assistant  
**狀態:** COMPLETE

---

## 1. Objective

驗證 Schedule 模組在「真實使用情境」下端對端可運作：
- 有 JWT actor（透過 dependency_override）
- 有 company_id（tenant isolation）
- 有 feature entitlement（schedule.core）
- API 可以成功 CRUD（ShiftTemplate + ShiftAssignment）

---

## 2. Files Read

| 檔案 | 用途 |
|------|------|
| backend/app/modules/schedule/api.py | 確認 feature gate 路徑、endpoint 結構 |
| backend/app/modules/schedule/service.py | 確認業務邏輯 |
| backend/app/modules/schedule/models.py | 確認 FK constraints（user_id → users） |
| backend/app/core/features.py | 確認 FeatureKeys.SCHEDULE_CORE 存在 |
| backend/app/core/feature_service.py | 確認 FeatureDisabledError |
| backend/app/tests/utils/auth.py | 確認 create_test_actor / override_actor_dependency |
| backend/app/conftest.py | 確認 test_db fixture 位置（空檔） |
| backend/app/modules/attendance/tests/conftest.py | 風格參考 |
| backend/app/modules/leave/tests/test_feature_gate.py | feature gate test 風格參考 |
| backend/app/modules/audit/tests/conftest.py | test_db 定義參考 |
| backend/app/modules/auth/models.py | User FK 必填欄位確認 |

---

## 3. Files Changed / Created

| 檔案 | 類型 | 說明 |
|------|------|------|
| backend/app/modules/schedule/tests/__init__.py | 新建 | 空 init |
| backend/app/modules/schedule/tests/conftest.py | 新建 | test_db + schedule_db + schedule_entitlement + actor fixtures |
| backend/app/modules/schedule/tests/test_schedule_template_api.py | 新建 | 6 integration tests |
| backend/app/modules/schedule/tests/test_schedule_assignment_api.py | 新建 | 6 integration tests |
| backend/app/modules/schedule/docs.md | append | WP-S1-05 integration status |
| docs/03_WP_CONTROL/NEXT_WP_TICKET.md | append | WP-S1-05 完成記錄 |
| docs/03_WP_CONTROL/GATE_PROGRESS_TRACKER.md | append | Gate 結果 |
| docs/02_DEVELOPMENT_STATUS/WORKSTREAM_STATUS_LEDGER.md | append | Ledger entry |
| docs/02_DEVELOPMENT_STATUS/MODULE_STATUS_MATRIX.md | append | Schedule 狀態更新 |
| docs/WP-S1-05_INTEGRATION_TEST_REPORT.md | 新建 | 本文件 |

**不修改：** models.py / repo.py / service.py / migration / frontend / env.py

---

## 4. Entitlement Setup

**狀態: DONE**

- Feature key: `schedule.core`（`FeatureKeys.SCHEDULE_CORE`）
- 設定方式: `CompanyEntitlement` 寫入 test DB（`company_entitlements` 表）
- Fixture: `schedule_entitlement`（conftest.py）
- 流程: 正確走 entitlement 機制，無 bypass / hardcode
- Company A (`schedule-test-company-a`): schedule.core = enabled
- Company B (`schedule-test-company-b`): 無 schedule.core（用於 negative case）

---

## 5. JWT Flow

**狀態: PASS**

- 使用 `create_test_actor(company_id, user_id, role_id)` 建立測試 Actor
- 使用 `override_actor_dependency(actor)` context manager 注入
- Actor 含正確 `active_company_id`，所有 endpoint 取用 `actor.active_company_id` 做 tenant isolation
- 無需產生真實 JWT token，符合現有 attendance/leave 測試慣例

---

## 6. API Integration Result

### ShiftTemplate Flow

| 步驟 | Endpoint | 狀態碼 | 結果 |
|------|----------|--------|------|
| Create | POST /api/v1/schedule/shift-templates | 201 | PASS |
| Get | GET /api/v1/schedule/shift-templates/{id} | 200 | PASS |
| List | GET /api/v1/schedule/shift-templates | 200 | PASS |
| Update | PATCH /api/v1/schedule/shift-templates/{id} | 200 | PASS |
| Deactivate | POST /api/v1/schedule/shift-templates/{id}/deactivate | 200 | PASS |
| Activate | POST /api/v1/schedule/shift-templates/{id}/activate | 200 | PASS |

### ShiftAssignment Flow

| 步驟 | Endpoint | 狀態碼 | 結果 |
|------|----------|--------|------|
| Create | POST /api/v1/schedule/shift-assignments | 201 | PASS |
| Get | GET /api/v1/schedule/shift-assignments/{id} | 200 | PASS |
| List | GET /api/v1/schedule/shift-assignments | 200 | PASS |
| Update | PATCH /api/v1/schedule/shift-assignments/{id} | 200 | PASS |
| Cancel | POST /api/v1/schedule/shift-assignments/{id}/cancel | 200 | PASS |

---

## 7. Negative Case Result

| Case | 預期狀態碼 | 實際 | 結果 |
|------|-----------|------|------|
| 無 entitlement → GET /shift-templates | 403 FEATURE_DISABLED | 403 | PASS |
| 無 entitlement → POST /shift-templates | 403 FEATURE_DISABLED | 403 | PASS |
| 無 entitlement → GET /shift-assignments | 403 FEATURE_DISABLED | 403 | PASS |
| 無 entitlement → POST /shift-assignments | 403 FEATURE_DISABLED | 403 | PASS |
| duplicate template code | 409 | 409 | PASS |
| get nonexistent template | 404 | 404 | PASS |
| cross-tenant template | 404 | 404 | PASS |
| double cancel assignment | 409 | 409 | PASS |
| get nonexistent assignment | 404 | 404 | PASS |
| cross-tenant assignment | 404 | 404 | PASS |

---

## 8. Pytest Result

```
====== 12 passed, 19 warnings in 7.22s ======
```

| 測試檔 | 測試數 | PASS | FAIL |
|--------|--------|------|------|
| test_schedule_template_api.py | 6 | 6 | 0 |
| test_schedule_assignment_api.py | 6 | 6 | 0 |
| **合計** | **12** | **12** | **0** |

**修正過程:**
1. 初次執行：4 FAILED（user FK violation + feature gate 422）
2. 修正 conftest：加入 `User` model import + test user 建立（FK 滿足）
3. 修正 assignment feature gate test：使用有效 payload（Pydantic 先通過再 mock 攔截）
4. 最終執行：12/12 PASS

---

## 9. Scope Control

| 項目 | 狀態 |
|------|------|
| models.py changed | NO |
| repo.py changed | NO |
| service.py changed | NO |
| migration changed | NO |
| env.py changed | NO |
| frontend changed | NO |
| git stash used | NO |
| 核心商業邏輯修改 | NO |

---

## 10. Final Verdict

**WP-S1-05 INTEGRATION COMPLETE: YES**

所有驗證項目全部通過：
- ✓ schedule.core entitlement 正確設定
- ✓ JWT actor + company_id tenant isolation 正常
- ✓ Feature gate 有/無 entitlement 行為正確
- ✓ ShiftTemplate 完整 CRUD flow PASS
- ✓ ShiftAssignment 完整 CRUD flow PASS
- ✓ Negative cases 全部正確回應
- ✓ pytest 12/12 PASS，不破壞現有測試

---

## 11. Remaining Gaps

| 項目 | 說明 | 建議票號 |
|------|------|----------|
| Production entitlement 設定 | 正式 DB 尚未設定 schedule.core | WP-S1-06 |
| 真實 JWT e2e | 目前使用 dependency_override；正式 JWT flow 未驗證 | WP-S1-06 |
| Frontend 串接 | Schedule API 尚無 UI | 後續 Frontend WP |
| 排班進階功能 | 衝突偵測、批量排班、循環排班 | 後續 S2/S3 |
