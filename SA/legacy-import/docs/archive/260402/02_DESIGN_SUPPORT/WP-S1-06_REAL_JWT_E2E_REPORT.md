# WP-S1-06 Real JWT E2E Execution Report

**票號:** WP-S1-06 — Schedule Production Entitlement + Real JWT E2E  
**執行日期:** 2026-03-19  
**執行者:** AI Assistant  
**狀態:** COMPLETE

---

## 1. Objective

將 Schedule 模組從「test fixture integration 已通過（WP-S1-05）」提升到「接近真實環境的後端可驗證狀態」。

本輪完成目標：
1. 確認 `schedule.core` 在實際 entitlement 機制中的正式配置方式
2. 驗證真實 JWT 驗證流程下，Schedule API 可被合法存取
3. 驗證無 entitlement 時會被正確拒絕（403 FEATURE_DISABLED）
4. 驗證 tenant/company scope 在真實 auth 流程下仍成立
5. 不修改 migration / env.py / frontend / 核心業務邏輯

---

## 2. Files Read

| 檔案 | 用途 |
|------|------|
| backend/app/modules/schedule/api.py | 確認 feature gate 路徑、endpoint 結構 |
| backend/app/modules/schedule/service.py | 確認業務邏輯 |
| backend/app/modules/schedule/repo.py | 確認 tenant isolation |
| backend/app/modules/schedule/docs.md | 確認現有狀態記錄 |
| backend/app/core/features.py | 確認 SCHEDULE_CORE + PLAN_DEFAULTS |
| backend/app/core/feature_service.py | 確認 FeatureService.is_enabled 查詢路徑 |
| backend/app/core/dependencies.py | 確認 get_current_actor 完整流程 |
| backend/app/core/scope.py | 確認 Actor / UserRole |
| backend/app/core/security/jwt.py | 確認 create_access_token / decode_access_token |
| backend/app/core/config.py | 確認 jwt_secret_key |
| backend/app/main.py | 確認 router mount |
| backend/app/modules/auth/models.py | 確認 User / Membership 欄位 |
| backend/app/modules/auth/repo.py | 確認 get_user_by_id / get_user_memberships |
| backend/app/modules/auth/service.py | 確認 create_access_token 呼叫方式 |
| backend/app/modules/tenants/models.py | 確認 CompanyEntitlement 欄位 |
| backend/app/tests/utils/auth.py | 確認現有 test helper（override 方式）|
| backend/app/modules/schedule/tests/conftest.py | 確認 WP-S1-05 fixture 方式 |
| backend/app/modules/schedule/tests/test_schedule_template_api.py | WP-S1-05 測試參考 |
| backend/app/modules/schedule/tests/test_schedule_assignment_api.py | WP-S1-05 測試參考 |
| docs/WP-S1-05_INTEGRATION_TEST_REPORT.md | WP-S1-05 結案報告 |
| docs/03_WP_CONTROL/NEXT_WP_TICKET.md | 治理文件 |
| docs/03_WP_CONTROL/GATE_PROGRESS_TRACKER.md | 治理文件 |
| docs/02_DEVELOPMENT_STATUS/WORKSTREAM_STATUS_LEDGER.md | 治理文件 |
| docs/02_DEVELOPMENT_STATUS/MODULE_STATUS_MATRIX.md | 治理文件 |
| docs/02_DEVELOPMENT_STATUS/CURRENT_SYSTEM_STATE.md | 治理文件 |

---

## 3. Files Changed

| 檔案 | 類型 | 說明 |
|------|------|------|
| backend/app/modules/schedule/tests/test_schedule_real_jwt_e2e.py | **新建** | 14 real JWT E2E 測試 |
| backend/app/modules/schedule/docs.md | **append** | WP-S1-06 Entitlement Audit + JWT E2E 記錄 |
| docs/WP-S1-06_REAL_JWT_E2E_REPORT.md | **新建** | 本報告 |
| docs/03_WP_CONTROL/NEXT_WP_TICKET.md | **append** | WP-S1-06 完成記錄 |
| docs/03_WP_CONTROL/GATE_PROGRESS_TRACKER.md | **append** | Gate 6 WP-S1-06 COMPLETE |
| docs/02_DEVELOPMENT_STATUS/WORKSTREAM_STATUS_LEDGER.md | **append** | WP-S1-06 Ledger entry |
| docs/02_DEVELOPMENT_STATUS/MODULE_STATUS_MATRIX.md | **append** | Schedule 狀態更新 |
| docs/02_DEVELOPMENT_STATUS/CURRENT_SYSTEM_STATE.md | **append** | System state 更新 |

**不修改：** models.py / repo.py / service.py / api.py / main.py / migration / frontend / env.py / 核心業務邏輯

---

## 4. Entitlement Path Audit

### 4.1 schedule.core 正式啟用路徑（已確認）

| 層級 | 說明 |
|------|------|
| Feature Key | `FeatureKeys.SCHEDULE_CORE = "schedule.core"` |
| 定義位置 | `backend/app/core/features.py` |
| 驗證位置 | `FeatureService.is_enabled()` → `FeatureService.require_enabled()` |
| 查詢機制 | `db.query(CompanyEntitlement).filter(company_id=?, feature_key='schedule.core')` |
| DB 資料表 | `company_entitlements`（已建立，migration 007 或更早）|
| 啟用方式 | 寫入 `(company_id, feature_key='schedule.core', enabled=True)` |
| API 管理端點 | `GET /api/v1/tenants/{company_id}/entitlements`（已實作於 tenants module）|
| 所有 11 endpoints 保護狀態 | `_require_schedule_feature()` 在每個 endpoint 首先調用 |

### 4.2 PLAN_DEFAULTS 現況

`PLAN_DEFAULTS` 目前**未納入 `schedule.core`**：

```python
# backend/app/core/features.py
PLAN_DEFAULTS = {
    "Basic": {  # 只含 attendance.* keys }
    "Pro":   {  # 只含 attendance.* keys }
}
```

**影響評估：**
- `PLAN_DEFAULTS` 是 plan-tier 概念，用於初始化新公司時的預設 feature 配置
- `schedule.core` 不在 `PLAN_DEFAULTS` 中 = 新公司預設**不啟用** schedule 模組
- 這是合理的 opt-in 設計（schedule 為新模組，需顯式啟用）
- Production 啟用路徑：透過 tenants API 或直接 DB 操作寫入 `company_entitlements`

**本輪決定：** 不修改 `PLAN_DEFAULTS`。記錄為已知缺口，待 rollout 策略確定後處理（建議 WP-S1-07）。

### 4.3 Entitlement 正式設定：本輪是否補齊？

- **測試層：** ✅ 已補齊（`jwt_test_db` fixture 正確建立 `CompanyEntitlement`）
- **Production/Staging：** ❌ 尚未補齊（需 ops 操作或 seed script）
- **阻塞點：** 無（測試驗證已完整；production rollout 屬 ops 工作，不阻塞本輪）

---

## 5. Real JWT Verification Method

### 方法

使用 `app.core.security.jwt.create_access_token()` 產生真實 HS256 簽名 JWT：

```python
def make_jwt(company_id: str, user_id: UUID = JWT_USER_ID, role_id: str = JWT_ROLE_ID) -> str:
    return create_access_token({
        "sub": str(user_id),
        "company_id": company_id,
        "role_id": role_id,
    })

def auth_headers(company_id: str) -> dict:
    return {"Authorization": f"Bearer {make_jwt(company_id)}"}
```

### 完整驗證路徑（不走 override_actor_dependency）

```
HTTP Request
  └─ Authorization: Bearer <real_hs256_token>
       └─ get_current_actor() [dependencies.py]
            ├─ decode_access_token(token)  → {sub, company_id, role_id}
            ├─ auth_repo.get_user_by_id(user_id)  → User (DB)
            ├─ user.is_active 驗證
            ├─ auth_repo.get_user_memberships(user_id)  → [Membership] (DB)
            ├─ JWT company_id in membership.company_ids 驗證
            └─ Actor(active_company_id=company_id, active_role_id=membership.role_id)
                  └─ get_actor_with_company()  → 確保 active_company_id 非空
                       └─ endpoint handler
                            └─ _require_schedule_feature(actor.active_company_id, db)
                                 └─ feature_service.require_enabled() → DB 查詢
```

### 唯一允許的 override

只 override `get_db`（讓 test DB session 注入），**不** override `get_current_actor` 或 `get_actor_with_company`：

```python
app.dependency_overrides[get_db] = _override_get_db  # 唯一 override
# get_current_actor: NO override (走真實 JWT decode)
# get_actor_with_company: NO override
```

---

## 6. Real API E2E Result

**測試檔:** `backend/app/modules/schedule/tests/test_schedule_real_jwt_e2e.py`  
**執行結果:** `14 passed, 19 warnings in 1.91s`

### Template Flow

| 步驟 | Endpoint | 預期狀態碼 | 實際 | 結果 |
|------|----------|-----------|------|------|
| create | POST /api/v1/schedule/shift-templates | 201 | 201 | **PASS** |
| get | GET /api/v1/schedule/shift-templates/{id} | 200 | 200 | **PASS** |
| list | GET /api/v1/schedule/shift-templates | 200 | 200 | **PASS** |

### Assignment Flow

| 步驟 | Endpoint | 預期狀態碼 | 實際 | 結果 |
|------|----------|-----------|------|------|
| create | POST /api/v1/schedule/shift-assignments | 201 | 201 | **PASS** |
| get | GET /api/v1/schedule/shift-assignments/{id} | 200 | 200 | **PASS** |
| cancel | POST /api/v1/schedule/shift-assignments/{id}/cancel | 200 | 200 | **PASS** |

---

## 7. Negative Case Result

| Case | 預期 | 實際 | 結果 |
|------|------|------|------|
| No JWT token → GET /shift-templates | 401 | 401 | **PASS** |
| Invalid/unsigned token → GET /shift-templates | 401 | 401 | **PASS** |
| Valid JWT, no entitlement → GET /shift-templates | 403 FEATURE_DISABLED | 403 | **PASS** |
| Valid JWT, no entitlement → POST /shift-templates | 403 FEATURE_DISABLED | 403 | **PASS** |
| Cross-tenant: Company B JWT → GET Company A template | 403 or 404 | 403 | **PASS** |
| No JWT → GET /shift-assignments | 401 | 401 | **PASS** |

---

## 8. Scope Control Confirmation

| 項目 | 狀態 |
|------|------|
| models.py changed | NO |
| repo.py changed | NO |
| service.py changed | NO |
| api.py changed | NO |
| main.py changed | NO |
| migration changed | NO |
| env.py changed | NO |
| frontend changed | NO |
| git stash/restore used | NO |
| 核心業務邏輯修改 | NO |
| 其他模組修改 | NO |

---

## 9. Final Verdict

**WP-S1-06 STABILIZATION COMPLETE: YES**

| 驗證項目 | 結果 |
|---------|------|
| schedule.core entitlement 正式路徑確認 | YES |
| Production/default setup completed | NO（已記錄為 remaining gap）|
| 真實 JWT auth flow | PASS |
| Template real API flow | PASS |
| Assignment real API flow | PASS |
| No entitlement blocked | PASS |
| Cross-tenant blocked | PASS |
| pytest 14/14 PASS | YES |

---

## 10. Remaining Gaps

| Gap | 說明 | 優先級 | 建議票號 |
|-----|------|--------|----------|
| PLAN_DEFAULTS 未納入 schedule.core | 新公司預設不啟用 schedule；需手動設定 | Medium | WP-S1-07 |
| Production/Staging entitlement seeding | 正式環境需 ops 操作或 seed script | Medium | WP-S1-07 |
| Frontend 串接 | Schedule API 尚無 UI | Low | 後續 Frontend WP |
| 排班進階功能 | 衝突偵測、批量排班、循環排班等 | Low | S2/S3 系列 |
| list assignments 無 entitlement 測試 | 僅測試了 template; assignment 403 間接驗證 | Low | WP-S1-07 |

---

## 11. Recommended Next Step

**建議 WP-S1-07：Schedule Production Rollout Preparation**

範圍建議：
1. 決定 `schedule.core` 在 `PLAN_DEFAULTS` 中的位置（Basic/Pro/Enterprise）
2. 建立 production entitlement seed script 或 migration
3. 補齊 assignment negative case（no entitlement → 403）
4. Frontend Schedule UI 串接評估

或直接進入 **Frontend Schedule WP**（若 backend 已足夠穩定）。

---

**最後更新:** 2026-03-19  
**WP-S1-06 COMPLETE**
