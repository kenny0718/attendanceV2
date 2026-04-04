# ROLE_DICTIONARY_AUDIT_AND_CONTROLLED_CLEANUP_REPORT

- 日期：2026-03-23
- 範圍：Frontend/Backend role dictionary 交叉盤點與受控清理
- 原則：僅移除「已確認 dead / unused」參考；不動 migration 歷史、不做資料庫清理、不做模型重構

---

## 1. Summary

本次完成前後端 role identifiers 全面盤點，並依三類分類：

1. Active roles（前後端現行使用）
2. Legacy-but-needed roles（歷史相容層，暫不可刪）
3. Confirmed dead references（可安全移除）

結論：
- 目前可確認 Active 的核心角色為：`super_admin`、`company_admin`、`hr_manager`、`employee`。
- `customer_service` 為後端現行 scope 角色，屬 Active（雖非本次 admin 前端主流程）。
- `manager`、`admin`、`hr`、`system_admin` 仍存在於後端相容映射或歷史資料相容語義，**目前不足以判定為 confirmed dead**。
- 本次未發現可 100% 安全刪除且不影響相容性的 dead references，因此不進行程式碼刪除。

---

## 2. Full role inventory

> 說明：以下為本次重點掃描（frontend 指定檔 + backend/app + migration 參考）

### 2.1 `super_admin`
- Frontend:
  - `frontend/src/stores/auth.js`
  - `frontend/src/router/index.js`
  - `frontend/src/views/admin/AdminOnboardingView.vue`
  - `frontend/src/api/admin.js`（註解）
- Backend:
  - `backend/app/core/dependencies.py`
  - `backend/app/core/scope.py`
  - `backend/app/modules/tenants/api.py`
  - `backend/app/modules/tenants/api_onboarding.py`
  - `backend/app/modules/customer_service/*`
- 判定：Active

### 2.2 `company_admin`
- Frontend:
  - `frontend/src/views/admin/AdminUsersView.vue`
  - `frontend/src/views/admin/AdminOnboardingView.vue`
  - `frontend/src/stores/auth.js`
  - `frontend/src/router/index.js`
- Backend:
  - `backend/app/core/scope.py`（admin 判斷）
  - `backend/app/modules/tenants/api.py`
  - `backend/app/modules/tenants/api_members.py`
  - `backend/app/modules/tenants/schemas_onboarding.py`（default）
- Migration:
  - `backend/alembic/versions/3532deda024c_create_auth_tables_v2_platform_first.py`
- 判定：Active

### 2.3 `hr_manager`
- Frontend:
  - `frontend/src/views/admin/AdminUsersView.vue`
  - `frontend/src/stores/auth.js`
  - `frontend/src/router/index.js`
- Backend:
  - `backend/app/core/scope.py`（admin 判斷）
  - `backend/app/modules/tenants/api.py`
  - `backend/app/modules/tenants/api_members.py`
- Migration:
  - `backend/alembic/versions/011_s1_11d_add_hr_manager_role.py`
- 判定：Active

### 2.4 `employee`
- Frontend:
  - `frontend/src/views/admin/AdminUsersView.vue`
  - `frontend/src/router/index.js`（註解）
- Backend:
  - `backend/app/core/scope.py`
  - `backend/app/modules/tenants/schemas_members.py`（default）
  - 多個 attendance/audit/backup 測試與流程引用
- Migration:
  - `backend/alembic/versions/3532deda024c_create_auth_tables_v2_platform_first.py`
- 判定：Active

### 2.5 `customer_service`
- Frontend:
  - 本次指定前端檔案無角色選單引用
- Backend:
  - `backend/app/core/dependencies.py`
  - `backend/app/core/scope.py`
  - `backend/app/modules/customer_service/*`
  - `backend/app/modules/tenants/api_entitlements.py`
- Migration:
  - `backend/alembic/versions/3532deda024c_create_auth_tables_v2_platform_first.py`
- 判定：Active（後端 scope 角色）

### 2.6 `manager`
- Frontend:
  - `frontend/src/views/admin/AdminUsersView.vue`（目前未作為 option value；僅由字串匹配可能命中 `hr_manager`）
- Backend:
  - `backend/app/core/dependencies.py`（相容映射）
  - `backend/app/modules/attendance/api.py`（legacy role 檢查分支）
  - `backend/app/modules/auth/repo.py` 註解/說明
- Migration:
  - `backend/alembic/versions/3532deda024c_create_auth_tables_v2_platform_first.py`（role seed）
- 判定：Legacy-but-needed（相容層仍在）

### 2.7 `admin`
- Frontend:
  - 主要為路徑/註解字串（如 `/admin`、`role-admin` 樣式 class）
- Backend:
  - `backend/app/core/dependencies.py`（相容映射）
  - `backend/app/modules/attendance/api.py`（legacy role 檢查分支）
  - 多數 `api/admin/*` 路由標籤或路徑字串
- 判定：Legacy-but-needed（含路由語義與相容映射，不可直接刪）

### 2.8 `hr`
- Frontend:
  - 無獨立 role 使用
- Backend:
  - `backend/app/core/dependencies.py`（相容映射）
  - `backend/app/modules/attendance/api.py`（legacy role 檢查分支）
- 判定：Legacy-but-needed（舊角色相容層）

### 2.9 `system_admin`
- Frontend:
  - 無
- Backend:
  - `backend/app/core/dependencies.py`（映射到 `SUPER_ADMIN`）
- 判定：Legacy-but-needed（別名相容層）

---

## 3. Active roles

- `super_admin`
- `company_admin`
- `hr_manager`
- `employee`
- `customer_service`（後端 scope active）

---

## 4. Legacy-but-needed roles

- `manager`
- `admin`
- `hr`
- `system_admin`

理由：
- 仍存在於後端相容映射或舊資料相容語義（例如 JWT role 映射、attendance 分支判斷）。
- 尚未完成「資料層已無舊值」與「線上 token/舊資料完全清空」之證據，故不可判定 dead。

---

## 5. Confirmed dead references

本次結果：**無（None）**。

判定依據：
- 未找到可證明「在現行流程、相容層、歷史資料相容需求中都不會被命中」的角色參考。
- 所有候選（`manager/admin/hr/system_admin`）都至少在後端相容映射或流程分支中仍有語義作用，故不得直接刪。

---

## 6. Exact cleanup applied

- 程式碼清理：**無**（避免誤刪 legacy 相容層）
- 本次僅新增報告檔：
  - `docs/02_DEVELOPMENT_STATUS/ROLE_DICTIONARY_AUDIT_AND_CONTROLLED_CLEANUP_REPORT.md`

---

## 7. Validation performed

已執行：
1. `git status --short`
2. `git diff --stat`
3. Frontend 指定檔 role 字串逐檔檢查
4. Backend `app/` 與 migration 歷史角色識別字掃描
5. non-test backend 檔案中的 legacy role 實際命中點人工複核

---

## 8. Build/test result

- 本次未修改 frontend/backend 功能程式碼（僅新增報告）。
- 因無功能代碼變更，未觸發額外 build/test。

---

## 9. Remaining items deferred for future role governance

1. 建議後續開治理票，先完成「線上資料是否仍含 `manager/admin/hr/system_admin`」盤點，再決定是否移除相容映射。
2. `backend/app/modules/attendance/api.py` 仍有 legacy role 判斷（`admin/manager/hr`）；在資料治理完成前不應刪除。
3. Frontend `AdminUsersView` 的 `role-admin` 樣式 class 目前不構成明確 dead（可能對 legacy membership 顯示仍有保護性作用），暫不處理。
