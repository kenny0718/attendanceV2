# Next WP Ticket

**更新日期：** 2026-03-29（WP-TECHDEBT-VUE-02 MemberCreatePanel Split COMPLETE）
**當前狀態：** S1-13A1/A2/A3 COMPLETE；TECHDEBT-VUE-01/02 COMPLETE；當前 WP：待定

---

## 當前 WP：待定

**Status:** PENDING
**前置條件:** WP-TECHDEBT-VUE-02 COMPLETE ✅
**說明：** AdminUsersView.vue Phase 1+2 拆分完成（907→594 行，-35%），下一票待使用者指定。

候選方向：
- `WP-TECHDEBT-VUE-03`：抽 MemberFilterBar.vue（主檔 594→~540 行，收益遞減，可選）
- `WP-S1-14`：下一個功能票
- `WP-BUGFIX-TEST-ROLE`：修復 `TEST_ROLE_ID = "admin"` 既有 bug

---

**最後更新：** 2026-03-29
**更新原因：** WP-TECHDEBT-VUE-02 MemberCreatePanel 拆分完成（708→594 行）

---

## WP-TECHDEBT-VUE-02 MemberCreatePanel Split — COMPLETE ✅

**完成日期：** 2026-03-29
**狀態：** COMPLETE

### 完成功能
- `MemberCreatePanel.vue` 獨立元件（172 行）
- `AdminUsersView.vue` 708 → 594 行（-16%）
- Phase 1+2 合計：907 → 594 行（-35%）
- 功能完全不變，29/29 結構驗證通過
- emit `created` → parent `clearFilters()` + `loadMembers()`

### 下一候選（Phase 3，可選）
- `WP-TECHDEBT-VUE-03`：抽 MemberFilterBar.vue

---

## WP-TECHDEBT-VUE-01 AdminUsersView Modal Split — COMPLETE ✅

**完成日期：** 2026-03-29
**狀態：** COMPLETE

### 完成功能
- `MemberPasswordModal.vue` 獨立元件（164 行）
- `MemberEditModal.vue` 獨立元件（188 行）
- `AdminUsersView.vue` 907 → 708 行（-22%）
- 28/28 結構驗證通過

---

## S1-13A3 Admin Member Reset Password — COMPLETE ✅

**完成日期：** 2026-03-29
**狀態：** COMPLETE

### 完成功能
- `PATCH /api/admin/companies/{company_id}/members/{membership_id}/password`
- bcrypt hash，Response 不含密碼或 hash
- 測試：TestResetMemberPassword 4/4 passed

### 已知 Follow-up
- 改密碼後現有 JWT session 不立即失效（需 token blacklist / jti 機制）

---

## S1-13A2 Admin Member Edit Login Username — COMPLETE ✅

**完成日期：** 2026-03-29
**狀態：** COMPLETE

### 完成功能
- `login_username` 欄位加入 UpdateMemberRequest / UpdateMemberResponse
- 唯一性衝突回傳 `409 DUPLICATE_LOGIN_USERNAME`
- 測試：TestUpdateMemberUsername 4/4 passed

---

## S1-13A1 Admin Member Edit — COMPLETE ✅

**完成日期：** 2026-03-29
**狀態：** COMPLETE

### 完成功能
- `PATCH /api/admin/companies/{company_id}/members/{membership_id}`
- 可編輯：display_name / email / role_id
- 測試：TestUpdateMember 6/6 passed

---

## S1-12 Admin × Attendance — COMPLETE ✅

**完成日期：** 2026-03-29
**狀態：** COMPLETE
- 21/21 tests pass，production-ready
