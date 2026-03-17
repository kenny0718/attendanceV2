# WP-C1-07 Attendance router_v1 JWT Migration — Pre-Audit 報告

**建立日期：** 2026-03-17
**狀態：** PRE-AUDIT（code 修改前）
**目的：** 在執行任何 code 修改前，明確盤點 attendance/api.py 現況、遷移範圍與風險

---

## 1. attendance/api.py Auth 現況摘要

### 1.1 現行 dependency 模式

attendance/api.py 目前存在兩種 auth dependency 模式並存：

| Dependency 函式 | 來源模組 | 型別 | 說明 |
|----------------|---------|------|------|
| get_current_company_id | app.core.tenant_context | Header-based | 從 X-Company-ID header 讀取 |
| get_current_user_id | app.core.tenant_context | Header-based | 從 X-User-ID header 讀取（選填） |
| get_actor_with_company | app.core.dependencies | JWT Actor | 從 JWT Bearer token 解析 |

### 1.2 router_v1 目前使用舊模式

router_v1（prefix: /api/v1/attendance）的所有 endpoint 均使用：
  company_id: str = Depends(get_current_company_id)
  user_id: Optional[str] = Depends(get_current_user_id)

### 1.3 目標模式（參考 audit/api.py）

  actor: Actor = Depends(get_actor_with_company)
  company_id = actor.active_company_id
  user_id = str(actor.user_id)

---

## 2. router_v1 舊 Auth Endpoints 清單（完整）

| # | Method | Path | 說明 |
|---|--------|------|------|
| 1 | POST | /api/v1/attendance/punch-in | 上班打卡 |
| 2 | POST | /api/v1/attendance/punch-out | 下班打卡 |
| 3 | GET  | /api/v1/attendance/current-status | 查詢當前狀態 |
| 4 | GET  | /api/v1/attendance/history | 歷史出勤記錄 |
| 5 | POST | /api/v1/attendance/break-out | 外出打卡 |
| 6 | POST | /api/v1/attendance/break-in | 返回打卡 |
| 7 | GET  | /api/v1/attendance/break-punches | 今日外出/返回記錄 |
| 8 | PATCH | /api/v1/attendance/punch/{punch_id}/note | 更新打卡備註 |
| 9 | GET  | /api/v1/attendance/sessions | Sessions 報表 |
| 10 | GET  | /api/v1/attendance/reports/user-summary | 用戶摘要 |
| 11 | GET  | /api/v1/attendance/reports/company-summary | 公司摘要 |

合計：11 個 router_v1 endpoints，全部使用舊 Header-based auth。

---

## 3. 本票要遷移的 Endpoint 清單（WP-C1-07 範圍）

全部 11 個 router_v1 endpoints 均在本票遷移範圍。

遷移方式：
- 移除 get_current_company_id / get_current_user_id dependency
- 新增 actor: Actor = Depends(get_actor_with_company)
- company_id = actor.active_company_id
- user_id = str(actor.user_id)（已為 UUID，不需再 UUID() 轉換）

---

## 4. 本票不處理的 Endpoint 清單

| # | Method | Path | 不處理原因 |
|---|--------|------|----------|
| 12 | POST | /api/attendance/mock-create | 舊版向後相容 API |
| 13 | POST | /api/attendance/{id}/approve | 舊版向後相容 API |

---

## 5. 遷移風險說明

### 低風險
- user_id 型別：舊為 Optional[str]，新為 actor.user_id（UUID）。內部已有 UUID() 轉換，改用 actor.user_id 直接使用即可。
- _require_attendance_feature helper 只改呼叫參數來源，helper 本身不變。
- /sessions endpoint 的 user_id query param 與 auth dependency 的 user_id 是不同參數，需小心區分。

### 中風險
- user_id 由 Optional 改為必定有值：JWT Actor 模式 actor.user_id 永遠有值，原有 if not user_id: raise 400 防衛分支不再觸發，保留無害。
- 測試層：override_all_auth_dependencies → override_actor_dependency，需同步更新。

### 不在本票範圍的已知問題
- test_regression.py::test_8_cross_midnight: punch_time 參數被 API 忽略（pre-existing bug）
- out-checkpoint API 404（WP-C1-09 未完成）

---

## 6. 預計採用的 JWT Actor 實作方式

### Import 變更

移除：
  from app.core.tenant_context import get_current_company_id, get_current_user_id

新增：
  from app.core.scope import Actor
  from app.core.dependencies import get_actor_with_company

### Endpoint 簽名範例（punch-in）

遷移前：
  async def punch_in(
      request: PunchInRequest,
      company_id: str = Depends(get_current_company_id),
      user_id: Optional[str] = Depends(get_current_user_id),
      http_request: Request = None,
      db: Session = Depends(get_db)
  ):

遷移後：
  async def punch_in(
      request: PunchInRequest,
      actor: Actor = Depends(get_actor_with_company),
      http_request: Request = None,
      db: Session = Depends(get_db)
  ):
      company_id = actor.active_company_id
      user_id = str(actor.user_id)

### 測試層變更

遷移前（雙 override）：
  with override_all_auth_dependencies(actor):
      response = client.post("/api/v1/attendance/punch-in", json={})

遷移後（單 override）：
  with override_actor_dependency(actor):
      response = client.post("/api/v1/attendance/punch-in", json={})

---

## 7. 預計修改檔案清單

| 檔案 | 修改性質 |
|------|----------|
| backend/app/modules/attendance/api.py | 必改：移除舊 import，替換 11 個 endpoint 的 dependency |
| backend/app/modules/attendance/tests/test_regression.py | 修改：override_all_auth_dependencies → override_actor_dependency |
| backend/app/modules/attendance/tests/test_punch_api.py | 修改：若有舊 header 模式則更新 |
| 新增 test_router_v1_jwt_migration.py | 新增：驗證 JWT actor 可正常呼叫所有 11 個 endpoints |
| backend/app/modules/attendance/docs.md | 必改：更新 Tenant & Auth Model 章節 |

### 不修改項目
- attendance/service.py
- attendance/repo.py
- attendance/schemas.py
- attendance/models.py
- attendance/policy_engine.py
- attendance/location_policy_service.py

---

## 8. Pre-Audit 結論

| 項目 | 結論 |
|------|------|
| router_v1 舊 auth endpoints 數量 | 11 個（全部 router_v1 endpoints） |
| 本票遷移目標 | 全部 11 個 router_v1 endpoints |
| 不在本票範圍 | router（舊版）2 個 endpoints |
| 遷移難度 | 低（pattern 明確，已有參考模式） |
| 業務邏輯風險 | 低（只改 auth dependency，不改 service/repo/schema） |
| 測試層影響 | 需同步更新使用 override_all_auth_dependencies 的測試 |

Pre-Audit 完成。可開始執行 Part 2 — 最小遷移。

---

*本報告由 AI 依據 2026-03-17 實際 code scan 產出。*
