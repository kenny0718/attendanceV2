# WP-S1-04B — Schedule Router Mount + Feature Gate Report

**票號:** WP-S1-04B — Schedule Router Mount + Feature Gate  
**執行日期:** 2026-03-19  
**執行者:** AI Agent (Cursor)  
**狀態:** COMPLETE — router mounted, feature gate wired, E2E smoke 8/8 PASS

---

## 1. Objective

將 Schedule 模組正式接入主 app：
1. 補齊 `FeatureKeys.SCHEDULE_CORE` 定義
2. `api.py` 加入 feature gate 保護（所有 11 個 endpoints）
3. `main.py` include schedule router
4. E2E smoke 驗證掛載成功

---

## 2. Files Read

| 檔案 | 說明 |
|------|------|
| backend/app/main.py | 現有 router mount 慣例確認 |
| backend/app/core/features.py | 現有 FeatureKeys 結構確認 |
| backend/app/core/feature_service.py | FeatureDisabledError 確認 |
| backend/app/modules/schedule/api.py | WP-S1-04A 版本（待 gate 補入）|
| backend/app/modules/leave/api.py | feature gate 風格參考 |

---

## 3. Files Changed

| 檔案 | 變更類型 | 大小 | 說明 |
|------|----------|------|------|
| backend/app/core/features.py | 修改 | 2246 bytes | 補 SCHEDULE_CORE key + all_keys() |
| backend/app/modules/schedule/api.py | 修改 | 12193 bytes | 補 feature gate（11 endpoints）|
| backend/app/main.py | 修改 | 5135 bytes | include schedule_router |
| backend/app/modules/schedule/docs.md | Append | — | WP-S1-04B record |
| docs/WP-S1-04B_ROUTER_MOUNT_FEATURE_GATE_REPORT.md | 新建 | — | 本報告 |
| 5 份治理文件 | Append | — | 狀態更新 |

---

## 4. Feature Gate Wiring Summary

### FeatureKeys 新增
```python
# backend/app/core/features.py
SCHEDULE_CORE = "schedule.core"  # WP-S1-04B
```
- 同時加入 `all_keys()` 回傳集合
- 命名風格與 `ATTENDANCE_CORE`、`LEAVE_CORE` 一致

### api.py gate helper
```python
def _require_schedule_feature(company_id: str, db: Session) -> None:
    feature_service = get_feature_service(db)
    try:
        feature_service.require_enabled(company_id, FeatureKeys.SCHEDULE_CORE)
    except FeatureDisabledError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FEATURE_DISABLED", ...}
        )
```
- 風格與 leave API 的 `_require_leave_feature` 完全一致
- 所有 11 個 endpoints 均在 `company_id = actor.active_company_id` 後立即呼叫

---

## 5. Router Mount Summary

### main.py 新增
```python
from app.modules.schedule.api import router as schedule_router  # WP-S1-04B
...
app.include_router(schedule_router)  # WP-S1-04B
```
- 位置：leave_router_v1 之後（依模組開發順序）
- 風格與其他模組 include_router 完全一致

---

## 6. Validation Method

採用 **FastAPI TestClient route access smoke**：
- 不需實際啟動 uvicorn
- 驗證 app 可完整載入（import + startup）
- 驗證 schedule routes 已掛載
- 驗證 auth gate 正常攔截（無 JWT → 401）
- 驗證不存在路由 → 404
- 驗證 OpenAPI schema 包含 schedule paths

---

## 7. Validation Result

### Static Validation
- `FeatureKeys.SCHEDULE_CORE == 'schedule.core'`: PASS
- `'schedule.core' in FeatureKeys.all_keys()`: PASS
- `schedule api import`: PASS
- `main app import`: PASS
- Schedule routes in app: **11 routes**

### E2E Smoke Results
```
=== WP-S1-04B E2E Smoke Results ===
1. /health: PASS (200)
2. / root: PASS (200)
3. GET /shift-templates (no auth): PASS (401 - JWT gate blocks)
4. POST /shift-templates (no auth): PASS (401 - JWT gate blocks)
5. GET /shift-assignments (no auth): PASS (401 - JWT gate blocks)
6. POST /shift-assignments (no auth): PASS (401 - JWT gate blocks)
7. GET /nonexistent route: PASS (404)
8. OpenAPI has schedule paths: PASS (7 paths)

Total: 8 | All PASS: True
E2E_SMOKE_PASS
```

### Route Table（已掛載）
```
POST  /api/v1/schedule/shift-templates
GET   /api/v1/schedule/shift-templates
GET   /api/v1/schedule/shift-templates/{template_id}
PATCH /api/v1/schedule/shift-templates/{template_id}
POST  /api/v1/schedule/shift-templates/{template_id}/activate
POST  /api/v1/schedule/shift-templates/{template_id}/deactivate
POST  /api/v1/schedule/shift-assignments
GET   /api/v1/schedule/shift-assignments
GET   /api/v1/schedule/shift-assignments/{assignment_id}
PATCH /api/v1/schedule/shift-assignments/{assignment_id}
POST  /api/v1/schedule/shift-assignments/{assignment_id}/cancel
```

---

## 8. Scope Control Confirmation

| 項目 | 狀態 |
|------|------|
| repo.py 修改 | NO |
| service.py 修改 | NO |
| migration 修改 | NO |
| env.py 修改 | NO |
| frontend 修改 | NO |
| attendance/leave/audit 等其他模組修改 | NO |
| git stash/restore 使用 | NO |
| 大範圍重構 | NO |

**修改範圍：** features.py（+SCHEDULE_CORE）、api.py（+feature gate）、main.py（+include_router）

---

## 9. Final Verdict

**WP-S1-04B MOUNT COMPLETE: YES**

- `FeatureKeys.SCHEDULE_CORE = 'schedule.core'` 已定義
- api.py: 11 endpoints 全部受 feature gate 保護
- main.py: schedule router 正式掛載
- E2E smoke: 8/8 PASS
- app startup: 無錯誤
- Scope lock: 全程遵守

---

## 10. Recommended Next Step

**WP-S1-05 — Schedule Module Integration Testing + Entitlement Setup**

建議工作內容：
1. 在 DB 中為測試 company 設定 `schedule.core` entitlement（`company_entitlements` 表）
2. 補齊 JWT auth 的 end-to-end 驗證（帶 token 的完整 API call）
3. 補 pytest integration tests（schedule API layer）
4. 考慮 schedule.core 的 Plan defaults 設定（PLAN_DEFAULTS in features.py）
5. Frontend 排班頁面串接（Schedule UI）

**附記：** `HTTP_422_UNPROCESSABLE_ENTITY` deprecation warning 仍存在於 service.py，建議在 WP-S1-05 或獨立 cleanup ticket 中修正。

---

**最後更新:** 2026-03-19  
**更新原因:** WP-S1-04B COMPLETE — Schedule module fully mounted and feature-gated
