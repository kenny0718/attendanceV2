# Next WP Ticket

**更新日期：** 2026-03-29（S1-13A3 Admin Member Reset Password COMPLETE）
**當前狀態：** S1-13A1 / A2 / A3 COMPLETE；當前 WP：WP-S1-13A4（待定）

---

## 當前 WP：WP-S1-13A4（待定）

**Status:** PENDING
**前置條件:** S1-13A3 COMPLETE ✅
**說明：** S1-13A3 管理員重設成員密碼已完整結案，下一票待使用者指定。

---

**最後更新：** 2026-03-29
**更新原因：** S1-13A3 Admin Member Reset Password COMPLETE（14/14 tests pass）

---

## S1-13A3 Admin Member Reset Password — COMPLETE ✅

**完成日期：** 2026-03-29
**狀態：** COMPLETE

### 完成功能
- `PATCH /api/admin/companies/{company_id}/members/{membership_id}/password` (新增)
- Admin 可安全重設成員密碼，使用 bcrypt hash
- UI：獨立 pwdModal（C 方案），不干擾既有 editModal
- 前後端雙重密碼驗證（min 6 chars + 一致性）
- Response 不含密碼或 hash
- 測試：TestResetMemberPassword 4/4 passed（含 hash 層驗證）

### 已知 Follow-up
- 改密碼後現有 JWT session 不立即失效（需 token blacklist / jti 機制）
- 密碼強度策略目前僅 min 6 chars
- `test_members_api.py` 既有 bug（`TEST_ROLE_ID = "admin"`）待修復

---

## S1-13A2 Admin Member Edit Login Username — COMPLETE ✅

**完成日期：** 2026-03-29
**狀態：** COMPLETE

### 完成功能
- `login_username` 欄位加入 `UpdateMemberRequest` / `UpdateMemberResponse`
- 唯一性衝突回傳 `409 DUPLICATE_LOGIN_USERNAME`
- 前端 editModal 顯示「此帳號名稱在該公司已被使用，請換一個」
- 測試：TestUpdateMemberUsername 4/4 passed

---

## S1-13A1 Admin Member Edit — COMPLETE ✅

**完成日期：** 2026-03-29
**狀態：** COMPLETE

### 完成功能
- `PATCH /api/admin/companies/{company_id}/members/{membership_id}` (新增)
- 可編輯：`display_name` / `email` / `role_id`
- UI：Modal Edit（AdminUsersView.vue 局部 patch）
- 權限：`super_admin` 任意公司；`company_admin/hr_manager` 只能操作自己公司
- 測試：TestUpdateMember 6/6 passed

---

## S1-12 Admin × Attendance — COMPLETE ✅

**完成日期：** 2026-03-29
**狀態：** COMPLETE
- 21/21 tests pass，production-ready
