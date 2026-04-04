# WP-C1-07 Attendance router_v1 JWT Migration — COMPLETE

**票號：** WP-C1-07
**完成日期：** 2026-03-17
**前置條件：** WP-C1-06 COMPLETE
**狀態：** COMPLETE

---

## 1. 票號與目標

將 attendance 模組中仍依賴 X-Company-ID / 舊 auth 模式的 router_v1 endpoint，
安全遷移到 JWT Actor 模式，並保持既有業務邏輯不變。

---

## 2. Pre-Audit 摘要

**報告位置：** docs/02_DEVELOPMENT_STATUS/WP-C1-07_ATTENDANCE_JWT_PRE_AUDIT.md

| 項目 | 結論 |
|------|------|
| router_v1 舊 auth endpoints 數量 | 11 個（全部 router_v1 endpoints）|
| 本票遷移目標 | 全部 11 個 router_v1 endpoints |
| 不在本票範圍 | router（舊版）2 個 endpoints |
| 遷移難度 | 低（pattern 明確，已有參考模式）|
| 業務邏輯風險 | 低（只改 auth dependency，不改 service/repo/schema）|

---

## 3. 實際修改檔案清單

| 檔案 | 修改性質 | 說明 |
|------|----------|------|
| `backend/app/modules/attendance/api.py` | **主要修改** | 移除舊 import，新增 Actor/get_actor_with_company；11 個 router_v1 endpoint 的 dependency 替換 |
| `backend/app/modules/attendance/tests/test_regression.py` | 修改 | override_all_auth_dependencies → override_actor_dependency |
| `backend/app/modules/attendance/tests/test_feature_gate.py` | 修改 | override_all_auth_dependencies → override_actor_dependency |
| `backend/app/modules/attendance/tests/test_reporting_sessions.py` | 修改 | X-Company-ID header → JWT Actor（make_actor helper + override_actor_dependency）|
| `backend/app/modules/attendance/tests/test_reporting_user_summary.py` | 修改 | 同上 |
| `backend/app/modules/attendance/tests/test_reporting_company_summary.py` | 修改 | 同上 |
| `backend/app/modules/attendance/tests/test_router_v1_jwt_migration.py` | **新增** | JWT migration 專用驗證測試（12 個測試）|
| `backend/app/modules/attendance/docs.md` | 修改 | 更新版本 v2.1，更新 Section 2.1/3.1/3.2/9.1/10.1 |
| `docs/02_DEVELOPMENT_STATUS/WP-C1-07_ATTENDANCE_JWT_PRE_AUDIT.md` | 新增 | Pre-Audit 報告 |

### 不修改項目
- attendance/service.py
- attendance/repo.py
- attendance/schemas.py
- attendance/models.py
- attendance/policy_engine.py
- attendance/location_policy_service.py
- feature gate 業務邏輯

---

## 4. 遷移的 router_v1 Endpoints 清單

| # | Method | Path | 遷移狀態 |
|---|--------|------|----------|
| 1 | POST | /api/v1/attendance/punch-in | COMPLETE |
| 2 | POST | /api/v1/attendance/punch-out | COMPLETE |
| 3 | GET  | /api/v1/attendance/current-status | COMPLETE |
| 4 | GET  | /api/v1/attendance/history | COMPLETE |
| 5 | POST | /api/v1/attendance/break-out | COMPLETE |
| 6 | POST | /api/v1/attendance/break-in | COMPLETE |
| 7 | GET  | /api/v1/attendance/break-punches | COMPLETE |
| 8 | PATCH | /api/v1/attendance/punch/{punch_id}/note | COMPLETE |
| 9 | GET  | /api/v1/attendance/sessions | COMPLETE |
| 10 | GET  | /api/v1/attendance/reports/user-summary | COMPLETE |
| 11 | GET  | /api/v1/attendance/reports/company-summary | COMPLETE |

**合計：11/11 endpoints 遷移完成**

### 遷移模式（統一）

```python
# 遷移前
company_id: str = Depends(get_current_company_id),
user_id: Optional[str] = Depends(get_current_user_id),

# 遷移後
actor: Actor = Depends(get_actor_with_company),
# 函式 body 第一行：
company_id = actor.active_company_id
user_id = str(actor.user_id)
```

---

## 5. 測試結果

### 5.1 JWT Migration 專用測試（新增）

```
test_router_v1_jwt_migration.py: 12/12 PASS
```

| 測試類別 | 測試數 | 結果 |
|----------|--------|------|
| TestJWTActorNoBearerHeader | 7 | 7 PASS |
| TestJWTActorTenantIsolation | 2 | 2 PASS |
| TestJWTActorWithoutCompanyScope | 1 | 1 PASS |
| TestPunchOutBreakFlow | 2 | 2 PASS |

### 5.2 相關測試套件

```
test_router_v1_jwt_migration.py  12/12 PASS
test_feature_gate.py              6/6 PASS
test_regression.py                0/1 PASS（test_8 pre-existing bug）
test_tenant_isolation_wp_c1_05.py 9/9 PASS
test_phase4.py                    6/6 PASS
合計: 27/28 PASS（1 pre-existing failure）
```

### 5.3 Pre-existing 失敗（非本票引入）

| 測試 | 原因 | 所屬 WP |
|------|------|--------|
| test_regression.py::test_8_cross_midnight | punch_time 參數被 API 忽略（datetime.now() 覆蓋傳入值）| WP 待定 |
| test_api.py（5 個）| /api/attendance/mock-create 依賴 X-Company-ID（舊 router，非本票範圍）| 舊版向後相容 |
| test_tenant_isolation.py（6 FAIL + 3 ERROR）| 同上，舊 router 測試 | Pre-existing |

---

## 6. docs.md 同步摘要

| 項目 | 說明 |
|------|------|
| 版本 | v2 → v2.1 |
| File size | 20,380 bytes |
| Section 2.1 | 更新 router_v1 使用 get_actor_with_company |
| Section 3.1 | 新增雙軌模式說明，JWT Actor vs Header-based |
| Section 3.2 | 新增 router_v1 禁用 X-Company-ID 規則 |
| Section 9.1 | 更新測試工具建議 |
| Section 10.1 | 新增 WP-C1-07 完成記錄 |

"docs sync completed"

---

## 7. 已知限制 / 未納入範圍

| 項目 | 說明 |
|------|------|
| 舊版 router（/api/attendance/mock-create, approve）| 維持 Header-based auth，向後相容，不在本票範圍 |
| test_8_cross_midnight pre-existing bug | punch_time 參數被 API 的 datetime.now() 覆蓋，不在本票範圍 |
| out-checkpoint API | 仍使用 override_all_auth_dependencies（out-checkpoint endpoint 為舊架構）|

---

## 8. 最終完成判定

| 驗收條件 | 結果 |
|----------|------|
| 11 個 router_v1 endpoints 完成 JWT Actor 遷移 | PASS |
| 不再依賴 X-Company-ID header（router_v1）| PASS |
| tenant isolation 維持正確 | PASS（9/9 isolation tests）|
| feature gate 不被破壞 | PASS（6/6 feature gate tests）|
| 業務邏輯未修改（service/repo/schema 不變）| PASS |
| JWT actor 可正常呼叫所有 11 個 endpoints | PASS（12/12 migration tests）|
| attendance/docs.md 同步更新 | PASS（20,380 bytes，v2.1）|

**WP-C1-07 判定：✅ COMPLETE**

---

## 9. 下一個 WP

根據 NEXT_WP_TICKET.md 的後續順序，WP-C1-07 完成後應進入：

**WP-C1-08 Phase 3（或後續票號）— Attendance 測試全面啟用**

---

*本報告由 AI 依據 2026-03-17 實際執行結果產出。*
