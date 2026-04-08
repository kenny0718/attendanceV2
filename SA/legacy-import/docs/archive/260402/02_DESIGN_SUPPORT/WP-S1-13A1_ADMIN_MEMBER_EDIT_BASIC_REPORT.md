# WP-S1-13A1：Admin Member Edit（基本資料）完成報告

> **日期**：2026-03-29  
> **狀態**：COMPLETED  
> **原則**：最小修改 / patch-style / 禁止 whole-file rewrite

---

## 1. Summary

實作 Admin 成員基本資料編輯（display_name / email / role_id），採 modal edit UI 方式。  
未修改 login_username / password，未重構既有建立與啟停流程。

---

## 2. Files Changed

| 檔案 | 修改方式 | 目的 |
|------|----------|------|
| `backend/app/modules/tenants/schemas_members.py` | append | 新增 `UpdateMemberRequest` / `UpdateMemberResponse` |
| `backend/app/modules/tenants/service.py` | patch（insert）| 新增 `TenantService.update_member()` 業務邏輯 |
| `backend/app/modules/tenants/api_members.py` | patch（import + endpoint）| 新增 `PATCH /{company_id}/members/{membership_id}` endpoint |
| `frontend/src/api/admin.js` | patch | 新增 `updateMember()` API wrapper |
| `frontend/src/views/admin/AdminUsersView.vue` | 4× patch（A/B/C/D）| 加 Edit 按鈕 + Modal HTML + Modal logic + Modal CSS |
| `backend/app/modules/tenants/tests/test_members_api.py` | append | 新增 `TestUpdateMember`（6 cases） |

---

## 3. UI Approach Chosen

**Modal Edit（B）**

- 在 table action 欄加「編輯」按鈕（`btn-edit`）
- 點擊後開啟 overlay modal，顯示 display_name / email / role_id 欄位
- 儲存成功後本地更新列表，延遲 800ms 自動關閉 modal
- 不改動既有 table 結構、不影響啟停按鈕

---

## 4. Backend Contract Findings

- ✅ `GET /{company_id}/members` 既有（不動）
- ✅ `PATCH /{company_id}/members/{membership_id}/active` 既有啟停（不動）
- ✅ `POST /{company_id}/members` 既有新增（不動）
- ❌ `PATCH /{company_id}/members/{membership_id}` **本次新增**

### 新增 endpoint 規格

```
PATCH /api/admin/companies/{company_id}/members/{membership_id}

Request body (all optional):
  display_name: str | null
  email:        str | null   (null = 清除)
  role_id:      str | null

Response 200:
  membership_id, user_id, company_id, role_id,
  display_name, email, membership_is_active

Errors:
  422 NO_FIELDS_TO_UPDATE  — 未提供任何欄位
  422 INVALID_ROLE         — role_id 不存在
  404 MEMBERSHIP_NOT_FOUND — membership 不存在或不屬於此 company
  403 SCOPE_FORBIDDEN      — company_admin/hr_manager 跨公司存取
```

### 權限邏輯（與既有一致）

- `super_admin`：任何公司
- `company_admin` / `hr_manager`：只能操作 `actor.active_company_id` 內成員
- 透過既有 `_assert_admin_company_access()` 函式，**不引入新的 auth 邏輯**

---

## 5. Changes Implemented

### Backend

1. **`schemas_members.py`**：`UpdateMemberRequest`（3 Optional 欄位）、`UpdateMemberResponse`
2. **`service.py`**：`TenantService.update_member()`
   - 驗證 role_id 存在後才 commit
   - company_id 做 membership scope check（tenant isolation）
   - 使用 `self.repo.db` 存取 session
3. **`api_members.py`**：`PATCH /{company_id}/members/{membership_id}`
   - 使用 `model_fields_set` 正確處理 email=null（清除）
   - 若無任何欄位，回 422 `NO_FIELDS_TO_UPDATE`

### Frontend

1. **`admin.js`**：`updateMember(companyId, membershipId, payload)`
2. **`AdminUsersView.vue`**（4× patch-style）：
   - Patch A：action 欄加 `btn-edit` 按鈕
   - Patch B：`</template>` 前加 modal HTML
   - Patch C：`// ── Utils` 前加 modal state/logic（`editModal` ref、`openEdit/closeEdit/saveEdit`）
   - Patch D：`</style>` 前加 modal CSS

---

## 6. Validation

### Backend 測試

| Test Case | 結果 |
|-----------|------|
| `test_super_admin_can_update_display_name` | PASS |
| `test_super_admin_can_update_role_id` | PASS |
| `test_invalid_role_id_returns_422` | PASS |
| `test_membership_not_found_returns_404` | PASS |
| `test_no_fields_returns_422` | PASS |
| `test_company_admin_cross_company_forbidden` | PASS |

**6/6 passed**

### Frontend 完整性檢查

| 項目 | 結果 |
|------|------|
| AdminUsersView.vue non-empty | YES |
| template exists | YES |
| script exists | YES |
| style exists | YES |
| editModal state | YES |
| openEdit / saveEdit / closeEdit | YES |
| modal-overlay in template | YES |
| updateMember call | YES |
| handleToggle unchanged | YES |
| handleAddMember unchanged | YES |
| File size | 35,631 bytes / 790 lines |

### Backend 語法檢查

- `schemas_members.py`：syntax OK（86 lines）
- `service.py`：syntax OK（488 lines）
- `api_members.py`：syntax OK（321 lines）

---

## 7. Risks / Follow-up

| 問題 | 優先級 | 說明 |
|------|--------|------|
| role_id 下拉固定三個選項 | Low | modal 中 role_id select 是 hardcoded（employee/hr_manager/company_admin），若未來新增 role 需更新前端 |
| email 清除邏輯 | Low | 目前空字串 = null = 清除，行為正確但未顯示清除按鈕 |
| test_members_api.py 既有 bug | Medium | `TEST_ROLE_ID = "admin"` 導致既有 GET/POST 測試失敗，需另票修復 |
| login_username / password 編輯 | Low | 本輪不在 scope，保留下一票 |

---

## 8. File Safety Check

| 檔案 | Size | Head | Tail | 結構 |
|------|------|------|------|------|
| `schemas_members.py` | 4,519 bytes / 86 lines | OK | OK | Python syntax OK |
| `service.py` | ~488 lines | OK | OK | Python syntax OK |
| `api_members.py` | ~321 lines | OK | OK | Python syntax OK |
| `AdminUsersView.vue` | 35,631 bytes / 790 lines | `<template>` | `</style>` | template+script+style OK |
| `admin.js` | non-empty | OK | OK | export intact |
| `test_members_api.py` | 768 lines | OK | OK | 6 passed |

---

## 9. Final Status

**company_admin / hr_manager 可正常使用成員編輯功能：YES**

- 成員列表每列有「編輯」按鈕
- 可編輯 display_name / email / role_id
- 儲存後本地即時更新，無需 full reload
- 既有啟停流程完全未受影響
- Backend 權限與 tenant isolation 行為一致
