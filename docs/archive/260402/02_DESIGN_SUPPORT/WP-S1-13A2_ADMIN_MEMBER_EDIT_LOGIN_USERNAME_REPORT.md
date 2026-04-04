# WP-S1-13A2：Admin Member Edit — login_username 完成報告

> **日期**：2026-03-29  
> **狀態**：COMPLETED  
> **前置**：S1-13A1（display_name / email / role_id 編輯）

---

## 1. Summary

在既有 Edit Modal（S1-13A1）基礎上，補充 `login_username` 可編輯能力。  
採最小 patch-style 修改，未重構任何既有流程。

---

## 2. Files Changed

| 檔案 | 修改方式 | 內容 |
|------|----------|------|
| `backend/.../schemas_members.py` | patch | `UpdateMemberRequest` 加 `login_username: Optional[str]`；`UpdateMemberResponse` 加 `login_username: str` |
| `backend/.../service.py` | patch（update_member 末段）| 加 pre-check + IntegrityError fallback，更新 `membership.login_username` |
| `backend/.../api_members.py` | 3× patch | update_fields 加 login_username；except 加 DUPLICATE_LOGIN_USERNAME→409；return 加 login_username |
| `frontend/.../AdminUsersView.vue` | 6× patch（A~F）| editModal ref/openEdit/saveEdit payload/local update/modal HTML input/form-hint CSS |
| `backend/.../tests/test_members_api.py` | append | `TestUpdateMemberUsername`（4 cases） |

---

## 3. Backend Audit Findings

### unique constraint 位置
- `auth/models.py`：`UniqueConstraint('company_id', 'login_username', name='uq_memberships_company_login')`
- 同公司內唯一，跨公司可重複

### 修改前後 API contract
```
PATCH /api/admin/companies/{company_id}/members/{membership_id}

Request（新增欄位）:
  login_username: str | null   (Optional，不傳 = 不修改)

Response（新增欄位）:
  login_username: str          (修改後的值)

新增錯誤：
  409 DUPLICATE_LOGIN_USERNAME — 同公司 login_username 重複
```

### JWT / 登入流程影響
- JWT 存 `user_id`，不存 `login_username`，**現有 session 不受影響**
- 使用者改完帳號後，下次登入須用新帳號（frontend modal 已有提示）

---

## 4. Conflict Handling

### Backend 策略（pre-check + IntegrityError fallback）

1. **Pre-check**（service.py）：
   ```python
   conflict = db.query(MembershipModel).filter(
       MembershipModel.company_id == company_id,
       MembershipModel.login_username == new_username,
       MembershipModel.id != mem_uuid,
   ).first()
   if conflict: raise ValueError("DUPLICATE_LOGIN_USERNAME")
   ```
2. **IntegrityError fallback**：commit 時若仍觸發 `uq_memberships_company_login`（例如 race condition），捕捉並 rollback，同樣 raise `ValueError("DUPLICATE_LOGIN_USERNAME")`
3. **API 層**：捕捉 `DUPLICATE_LOGIN_USERNAME` → `409 CONFLICT`

### Frontend 錯誤提示
- `editModal.error` 顯示：`「此登入帳號在該公司已被使用，請換一個」`（來自 backend 409 message）

### 警告提示文案
- modal 中 login_username 欄位下方顯示：「修改後，該成員下次登入需使用新的登入帳號」

---

## 5. Changes Implemented

### service.py update_member() 邏輯
- 加 pre-check（避免純靠 DB exception 驅動錯誤）
- 加 IntegrityError rollback + fallback（最後防線，覆蓋 race condition）
- 修改 `db.commit()` 改為 `try/except IntegrityError`

### A1 回歸確認
- `display_name` only patch：仍正常（`login_username` 不在 payload 則不修改）
- `email = null` 清除：仍正常（`model_fields_set` 邏輯不變）
- `role_id` only patch：仍正常

---

## 6. Validation

### TestUpdateMember（A1 原有）

| Test | 結果 |
|------|------|
| test_super_admin_can_update_display_name | PASS |
| test_super_admin_can_update_role_id | PASS |
| test_invalid_role_id_returns_422 | PASS |
| test_membership_not_found_returns_404 | PASS |
| test_no_fields_returns_422 | PASS |
| test_company_admin_cross_company_forbidden | PASS |

### TestUpdateMemberUsername（A2 新增）

| Test | 結果 |
|------|------|
| test_super_admin_can_update_login_username | PASS |
| test_same_company_duplicate_username_returns_409 | PASS |
| test_different_company_same_username_allowed | PASS |
| test_display_name_only_no_login_username_regression | PASS |

**Total：10/10 passed**

---

## 7. Risks / Follow-up

| 問題 | 優先級 | 說明 |
|------|--------|------|
| 使用者不知道自己的新帳號 | Low | 前端已有提示，但無 email 通知功能 |
| 密碼重設 | Low | 本輪 not in scope，保留下一票 |
| `test_members_api.py` 既有 bug（`TEST_ROLE_ID = "admin"`）| Medium | 需另票修復 |

---

## 8. File Safety Check

| 檔案 | Size | Head | Tail | 結構 |
|------|------|------|------|------|
| `schemas_members.py` | 89 lines | OK | OK | syntax OK |
| `service.py` | 511 lines | OK | OK | syntax OK |
| `api_members.py` | 328 lines | OK | OK | syntax OK |
| `AdminUsersView.vue` | 803 lines / 36,402 bytes | `<template>` | `</style>` | template+script+style OK |

### 是否需要 build/dist
- 若使用 `vite dev` 開發模式：**不需要重新 build**，HMR 自動生效
- 若是 production 部署：**需要重新執行 `npm run build`** 才會看到更新

---

## 9. Final Status

**Admin 可編輯 login_username：YES**

- 同公司重複帳號有 409 錯誤提示
- 不同公司相同帳號允許
- A1 既有功能（display_name / email / role_id）未受影響
- JWT / 現有 session 不受影響
