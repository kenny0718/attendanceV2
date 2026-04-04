# ADMIN_USERS_ROLE_DICTIONARY_ALIGNMENT_REPORT

- 日期：2026-03-23
- 範圍：`frontend/src/views/admin/AdminUsersView.vue` 角色字典對齊（Safe Patch Only）
- 性質：後端 source-of-truth 審計 + 前端最小差異驗證 + build 驗證

---

## 1. Summary

本次依照 safe-edit 規範，先完成後端角色來源審計，再核對 `AdminUsersView.vue` 的新增成員角色字典。

結論：
- `AdminUsersView.vue` 目前角色選單 value 已為後端可接受值（`employee` / `hr_manager` / `company_admin`）。
- `newMember.role_id` 預設值為 `employee`，屬後端有效角色。
- 送出 payload 的 `role_id` 直接取自 `newMember.role_id`，不會再送出 `manager`。
- 因此本次 **不需要額外程式碼修補**；主要交付為審計與驗證報告。

---

## 2. Backend role source of truth

### 2.1 成員建立 API 的最終驗證
- 檔案：`backend/app/modules/tenants/api_members.py`
- 行為：`create_company_member` 會以 `RoleModel.id == request.role_id` 查詢；查無則回 `422 INVALID_ROLE`。

### 2.2 Schema 預設角色
- 檔案：`backend/app/modules/tenants/schemas_members.py`
- `CreateMemberRequest.role_id` 預設：`employee`。

- 檔案：`backend/app/modules/tenants/schemas_onboarding.py`
- `OnboardingUserRequest.role_id` 預設：`company_admin`。

### 2.3 角色種子資料（migration）
- 檔案：`backend/alembic/versions/3532deda024c_create_auth_tables_v2_platform_first.py`
  - 內含角色：`employee`、`manager`、`company_admin`、`customer_service`
- 檔案：`backend/alembic/versions/011_s1_11d_add_hr_manager_role.py`
  - 新增：`hr_manager`

### 2.4 本票流程應採用角色集合（Admin Access Alignment）
依目前 Admin 前端治理與 smoke/audit 文件脈絡，本次對齊的公司管理流程角色集合為：
- `super_admin`
- `company_admin`
- `hr_manager`
- `employee`

> 註：`manager` 雖存在於舊 migration 種子，但在現行 Admin Access 對齊規範中屬舊值，不應再由 `AdminUsersView` 新增成員流程提供。

---

## 3. Frontend role dictionary before patch (audit result)

審計 `frontend/src/views/admin/AdminUsersView.vue`：
- Add Member role options：
  - `employee`
  - `hr_manager`
  - `company_admin`
- default selected role：`employee`
- submit payload：`role_id: newMember.value.role_id`

---

## 4. Exact mismatches found

- 本次實際檔案審計未發現 mismatch。
- 未發現 `manager` 出現在新增成員 role option value。
- 未發現預設值為無效角色。
- 未發現 payload 改寫為非後端接受值。

---

## 5. Exact patches applied

- `frontend/src/views/admin/AdminUsersView.vue`：**無需修改**（已對齊）。
- 僅新增本報告文件：
  - `docs/02_DEVELOPMENT_STATUS/ADMIN_USERS_ROLE_DICTIONARY_ALIGNMENT_REPORT.md`

---

## 6. Validation performed

已執行：
1. `git status --short`
2. `git diff --stat`
3. 後端 source-of-truth 檔案審計（members API / onboarding schema / role migrations）
4. `AdminUsersView.vue` role options、default、submit payload 檢查
5. `cd frontend && npm run build`

---

## 7. Build result

- 指令：`cd frontend && npm run build`
- 結果：✅ PASS（Vite build 成功）

---

## 8. Remaining limitations / follow-up recommendations

1. `AdminUsersView` 已對齊，但若其他頁（例如 onboarding）仍出現舊角色值，仍可能產生 422（需獨立票修復）。
2. 後端目前仍保留 `manager`（migration 種子），但前端 Admin 管理流程已採 `hr_manager`；建議後續由後端/資料治理票釐清是否需正式淘汰或遷移舊角色資料。
3. 本次嚴格遵守最小範圍：未調整 router、CSS、文案、流程或其他 business logic。
