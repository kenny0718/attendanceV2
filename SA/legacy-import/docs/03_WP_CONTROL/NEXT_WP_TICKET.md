# Next WP Ticket

**更新日期：** 2026-03-29（WP-S1-14A Leave Request Create COMPLETE）
**當前狀態：** S1-13 COMPLETE；TECHDEBT-VUE-01/02 COMPLETE；S1-14A COMPLETE；當前 WP：WP-S1-14B（待定）

---

## 當前 WP：WP-S1-14B（待定）

**Status:** PENDING
**前置條件:** WP-S1-14A COMPLETE ✅
**說明：** 請假申請建立完成，下一票待使用者指定。

候選方向：
- `WP-S1-14B`：請假列表 UI（員工查看自己的申請）
- `WP-S1-14C`：審核流程（主管 approve/reject）
- `WP-S1-14D`：Leave Types 管理 UI（Admin 設定假別）
- `WP-BUGFIX-LEAVE-TEST`：修復 `test_my_requests_only_returns_own_company_data` KeyError
- `WP-BUGFIX-TEST-ROLE`：修復 `TEST_ROLE_ID = "admin"` 既有 bug

---

**最後更新：** 2026-03-29
**更新原因：** WP-S1-14A Leave Request Create COMPLETE（frontend form + API client + router）

---

## WP-S1-14A Leave Request Create — COMPLETE ✅

**完成日期：** 2026-03-29
**狀態：** COMPLETE

### 完成功能
- `LeaveRequestView.vue`（338 行）：請假申請表單
- `frontend/src/api/leave.js`：createLeaveRequest / getMyLeaveRequests
- `/leave` route 加入 router
- Backend 已由 WP-11-08 完整實作（POST /api/v1/leave/requests）
- tenant isolation：company_id / user_id 來自 JWT，不接受 client 傳入
- Feature Gate：leave.core 未啟用時前端顯示友善錯誤訊息
- Backend leave tests：13/14 passed（1 fail 為既有 bug）

### 已知 Follow-up
- Leave Type UUID 需手動輸入（後續可加 leave types 管理 UI）
- `test_my_requests_only_returns_own_company_data` KeyError（既有 bug）
- Navbar 尚未加入 Leave 入口連結

---

## WP-TECHDEBT-VUE-02 MemberCreatePanel Split — COMPLETE ✅

**完成日期：** 2026-03-29  **狀態：** COMPLETE
- `MemberCreatePanel.vue` 獨立元件（172 行）
- `AdminUsersView.vue` 907 → 594 行（-35%）

---

## WP-TECHDEBT-VUE-01 AdminUsersView Modal Split — COMPLETE ✅

**完成日期：** 2026-03-29  **狀態：** COMPLETE
- `MemberPasswordModal.vue`（164 行）+ `MemberEditModal.vue`（188 行）
- `AdminUsersView.vue` 907 → 708 行（-22%）

---

## S1-13A3 Admin Member Reset Password — COMPLETE ✅

**完成日期：** 2026-03-29  **狀態：** COMPLETE
- `PATCH /api/admin/companies/{company_id}/members/{membership_id}/password`
- bcrypt hash，Response 不含密碼；4/4 tests passed

---

## S1-13A2 Admin Member Edit Login Username — COMPLETE ✅

**完成日期：** 2026-03-29  **狀態：** COMPLETE
- login_username 編輯 + 409 DUPLICATE_LOGIN_USERNAME；4/4 passed

---

## S1-13A1 Admin Member Edit — COMPLETE ✅

**完成日期：** 2026-03-29  **狀態：** COMPLETE
- `PATCH /api/admin/companies/{company_id}/members/{membership_id}`；6/6 passed

---

## S1-12 Admin × Attendance — COMPLETE ✅

**完成日期：** 2026-03-29  **狀態：** COMPLETE
- 21/21 tests pass，production-ready
