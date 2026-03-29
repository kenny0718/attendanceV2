# WP-S1-13A3：Admin Member Reset Password 完成報告

> **日期**：2026-03-29  
> **狀態**：COMPLETED  
> **前置**：S1-13A1（基本資料編輯）、S1-13A2（login_username 編輯）

---

## 1. Summary

新增管理員重設成員密碼功能。獨立 `pwdModal`，不干擾既有 editModal（A1/A2）。  
採最小 patch-style 修改，密碼不回傳、不記錄在 log/response。

---

## 2. Files Changed

| 檔案 | 修改方式 | 內容 |
|------|----------|------|
| `schemas_members.py` | append | `ResetMemberPasswordRequest`（min 6 chars）/ `ResetMemberPasswordResponse`（無密碼欄位）|
| `service.py` | patch insert | `TenantService.reset_member_password()`（server-side policy + `AuthRepository.update_password()`）|
| `api_members.py` | 2× patch（import + endpoint）| `PATCH /{company_id}/members/{membership_id}/password` |
| `frontend/src/api/admin.js` | patch | `resetMemberPassword()` wrapper |
| `AdminUsersView.vue` | 4× patch（A~D）| 「密碼」按鈕 / pwdModal HTML / state+logic / CSS |
| `test_members_api.py` | append | `TestResetMemberPassword`（4 cases）|

---

## 3. UI Approach Chosen

**C. 獨立小 modal（`pwdModal`）**

- Action 欄新增「密碼」按鈕（橘色，視覺區隔）
- 獨立 `pwdModal` ref，與 `editModal` 完全分離
- 顯示成員名稱確認對象，填寫新密碼 + 確認密碼
- 成功後顯示「密碼已成功重設」，延遲 1 秒關閉

---

## 4. Backend Audit Findings

### Password hashing 工具
- `app/core/security/password.py`：`hash_password()` / `verify_password()`（bcrypt）
- `AuthRepository.update_password(user, new_plain_password)` — 直接重用，內部 `hash_password()` + `db.commit()` + `db.refresh()`
- **不需要新增 hashing 邏輯**

### 可重用路徑
- `service.py` 呼叫 `AuthRepository(db).update_password()`，business logic 在 service 層
- API 層只做 permission check + error mapping

---

## 5. Password Handling

### Hashing 流程
```
request.new_password → service.reset_member_password()
  → server-side len check (≥6)
  → AuthRepository.update_password(user, plain)
    → hash_password(plain) [bcrypt]
    → user.password_hash = hashed
    → db.commit() / db.refresh()
  → return {membership_id, user_id}  ← plain password NOT returned
```

### Response 安全性
- `ResetMemberPasswordResponse`：只有 `membership_id`、`user_id`、`message`
- **不含** `password`、`password_hash`、任何 auth 細節

### 本輪使用的最小 password policy
- 非空（Pydantic `min_length=1` + 額外 `len >= 6` 檢查）
- 長度 ≥ 6（與 `CreateMemberRequest.password` 一致）
- 最大長度 255

### JWT / Session 影響
- JWT 存 `user_id`，不存 password hash
- **現有 session 不會立即失效**（無 token blacklist 機制）
- 使用者改密碼後，現有 token 在自然過期前仍有效
- **這是已知行為，列為 follow-up**（見第 8 節）

---

## 6. Changes Implemented

### service.py `reset_member_password()`
- Server-side policy：`len < 6` → `ValueError("PASSWORD_TOO_SHORT")`
- Tenant isolation：`MembershipModel.company_id == company_id`
- 重用 `AuthRepository.update_password()`，不自行 hash
- `return {membership_id, user_id}` — 不含 plain password 或 hash

### Frontend client-side validation（savePwd）
- `pwd.length < 6` → 顯示「密碼至少6個字元」
- `pwd !== confirm` → 顯示「兩次密碼輸入不一致」
- Backend 仍獨立再次驗證（雙重保護）

---

## 7. Validation

| Test | 結果 |
|------|------|
| `test_super_admin_can_reset_password`（hash 改變 + verify_password=True）| PASS |
| `test_short_password_rejected`（422）| PASS |
| `test_employee_cannot_reset_password`（403）| PASS |
| `test_company_admin_cross_company_forbidden`（403）| PASS |
| `TestUpdateMember`（A1，6 cases）| PASS |
| `TestUpdateMemberUsername`（A2，4 cases）| PASS |

**Total：14/14 passed**

### Hash 層驗證說明
- `test_super_admin_can_reset_password` 明確驗證：
  1. `user.password_hash != old_hash`（hash 確實改變）
  2. `verify_password("newpass123", user.password_hash) == True`
- 端對端重新登入驗證未做（測試 auth endpoint 需要完整登入流程，成本較高）

---

## 8. Risks / Follow-up

| 問題 | 優先級 | 說明 |
|------|--------|------|
| 現有 JWT session 不立即失效 | Medium | 改密碼後舊 token 仍有效直到過期。需 token blacklist 或 jti 機制。保留下一票。|
| 密碼強度策略 | Low | 目前只做 min 6 chars，無複雜度要求 |
| 端對端登入驗證測試 | Low | hash 層已驗證，端對端登入成本較高，保留 |
| `test_members_api.py` 既有 bug（`TEST_ROLE_ID = "admin"`）| Medium | 需另票修復 |

---

## 9. File Safety Check

| 檔案 | Size | Head | Tail | 結構 |
|------|------|------|------|------|
| `schemas_members.py` | 110 lines | OK | OK | syntax OK |
| `service.py` | 563 lines | OK | OK | syntax OK |
| `api_members.py` | 389 lines | OK | OK | syntax OK |
| `AdminUsersView.vue` | 907 lines / 39,999 bytes | `<template>` | `</style>` | template+script+style OK |

### Production build 需求
- **dev mode（vite dev）**：無需重新 build，HMR 自動生效
- **production 部署**：需執行 `npm run build` 才會看到更新

---

## 10. Final Status

**Admin 可安全重設成員密碼：YES**

- 密碼正確 bcrypt hash
- Response 不含密碼或 hash
- A1/A2 功能完全不受影響（14/14 passed）
- JWT / 現有 session 行為已知，列為 follow-up
