# WP-TECHDEBT-B Phase 1：Modal Split 完成報告

> **日期**：2026-03-29
> **狀態**：COMPLETE
> **票號**：WP-TECHDEBT-VUE-01

---

## 1. Summary

將 `AdminUsersView.vue` 中的兩個 modal 抽出為獨立元件，主檔從 **907 行降至 708 行**（-199 行，-22%）。
功能行為完全不變，A1/A2/A3 edit flow 均正常。

---

## 2. Files Changed

| 檔案 | 類型 | 說明 |
|------|------|------|
| `frontend/src/components/admin/MemberPasswordModal.vue` | 新增 | 164 行，重設密碼 modal |
| `frontend/src/components/admin/MemberEditModal.vue` | 新增 | 188 行，基本資料編輯 modal |
| `frontend/src/views/admin/AdminUsersView.vue` | 3× patch | 907 → 708 行（-199 行）|

---

## 3. Components Extracted

### MemberPasswordModal.vue（164 行）
- Template：overlay + modal-box（display_name 確認、new_password、confirm_password）
- Script：本地 state（newPassword/confirmPassword/loading/error/success）+ `savePwd()` + `watch(open)` 重置
- Style：modal 通用 CSS + `.pwd-member-name`

### MemberEditModal.vue（188 行）
- Template：overlay + modal-box（display_name/email/role_id/login_username/form-hint）
- Script：本地 state（localDisplayName/localEmail/localRoleId/localLoginUsername/loading/error/success）+ `saveEdit()` + `watch(open)` 重置
- Style：modal 通用 CSS + `.form-hint`

---

## 4. Props / Emits Design

### MemberPasswordModal
```
props:
  open       Boolean  (required) — v-if 控制顯示
  member     Object   (default null) — { membership_id, display_name }
  companyId  String   (required) — 用於 API 呼叫
emits:
  close      — parent 設 pwdModalOpen = false
```

### MemberEditModal
```
props:
  open       Boolean  (required)
  member     Object   (default null) — { membership_id, display_name, email, role_id, login_username }
  companyId  String   (required)
emits:
  close      — parent 設 editModalOpen = false
  saved      — emit(updatedMember) → parent 做 local list update
```

---

## 5. Changes In AdminUsersView.vue

### Template（3× patch）
- 移除 editModal HTML block（L276–L317）
- 移除 pwdModal HTML block（L318–L347）
- 替換為 `<MemberEditModal>` + `<MemberPasswordModal>` 元件標籤

### Script（2× patch）
- 加入兩個元件 import
- 移除：`editModal ref`、`openEdit/closeEdit/saveEdit`、`pwdModal ref`、`openPwd/closePwd/savePwd`（共 ~130 行）
- 新增：`editModalOpen/editModalMember ref`、`pwdModalOpen/pwdModalMember ref`、精簡版 `openEdit/openPwd`、`onMemberSaved` local update handler

### Style（1× patch）
- 移除：`.modal-overlay` `.modal-box` `.modal-header` `.modal-title` `.modal-close` `.modal-body` `.modal-footer` `.modal-error` `.modal-success` `.btn-cancel` `.btn-save` `.form-hint` `.pwd-member-name`（已遷移至子元件）
- 保留：`.btn-edit` `.btn-pwd`（action 欄按鈕仍在 parent table）

---

## 6. Validation

### 結構驗證（28/28 checks）
- template/script/style 三段均存在 ✅
- 兩個元件 import + tag 存在 ✅
- 新 ref（editModalOpen/pwdModalOpen）存在 ✅
- 舊 ref（editModal/pwdModal）已移除 ✅
- saveEdit/savePwd 已移除（在子元件中）✅
- modal CSS 已移除，btn-edit/btn-pwd CSS 保留 ✅
- handleToggle/handleAddMember/filteredMembers/selectedCompanyId 均保留 ✅

### 功能驗證
- MemberPasswordModal：open/驗證（長度/一致性）/成功/關閉 ✅
- MemberEditModal：open/display_name+email+role_id+login_username 儲存/409 DUPLICATE_LOGIN_USERNAME/saved emit/local update ✅
- Regression：toggle active/新增成員/filter 不受影響 ✅

---

## 7. Risks / Follow-up

| 項目 | 說明 |
|------|------|
| production build | 需執行 `npm run build` 才在 production 生效（dev HMR 自動）|
| Phase 2（可選）| 抽 MemberCreatePanel.vue（主檔仍有 708 行，可視需求推進）|
| Phase 3（可選）| 抽 MemberFilterBar.vue（可進一步降低主檔行數）|

---

## 8. File Safety Check

| 檔案 | Lines | Bytes | Head | Tail |
|------|-------|-------|------|------|
| `MemberPasswordModal.vue` | 164 | ~4.2KB | `<template>` | `</style>` |
| `MemberEditModal.vue` | 188 | ~5.0KB | `<template>` | `</style>` |
| `AdminUsersView.vue` | 708 | 32,436 bytes | `<template>` | `</style>` |

---

## 9. Final Status

| 標準 | 結果 |
|------|------|
| 主檔行數降低 | ✅ 907 → 708（-22%）|
| 功能完全不變 | ✅ |
| 禁止 whole-file rewrite | ✅ 全部 patch-style |
| 元件設計完整（props/emits）| ✅ |
| CSS 隨元件遷移 | ✅ |
| 驗證全數通過 | ✅ 28/28 |

**WP-TECHDEBT-VUE-01 COMPLETE**
