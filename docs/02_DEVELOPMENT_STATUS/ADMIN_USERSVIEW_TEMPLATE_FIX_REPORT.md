# ADMIN_USERSVIEW_TEMPLATE_FIX_REPORT

## 1. Summary

本次僅修復 `frontend/src/views/admin/AdminUsersView.vue` 的 `<template>` 結構錯誤（`Invalid end tag`）。
修補後已成功執行 `npm run build`，Vite build 通過。

---

## 2. Root cause of invalid end tag

Vite 報錯位置在 `~273` 行附近。根因是 `<template>` 區塊中存在**多餘的 closing tag**：

- `</div>` 在 members table 區塊關閉後被多關一次
- 導致後續 `v-else` 區塊的巢狀對應錯位，最終在 template 結尾觸發 `Invalid end tag`

具體位置（修補前）在約 `258~262` 行：

- `</div>`（關閉 table-wrapper）
- `</div>`（關閉 members-panel）
- `</div>`（**多餘，應移除**）

---

## 3. Exact line area patched

僅修改 `frontend/src/views/admin/AdminUsersView.vue` 的 `<template>`，約 `258~262` 行：

- 刪除 1 行多餘 `</div>`

未修改：
- `<script setup>`
- `<style scoped>`
- 任何 API 呼叫/方法/computed/樣式

---

## 4. Validation performed

已執行：

1. `git status --short`
2. `git diff --stat`
3. `nl -ba frontend/src/views/admin/AdminUsersView.vue | sed -n '230,290p'`
4. `git diff -- frontend/src/views/admin/AdminUsersView.vue`
5. `npm run build`（於 `frontend/` 目錄）

---

## 5. Build result

`npm run build` 結果：✅ 成功

- `vite v5.4.21 building for production...`
- `✓ built in 4.95s`
- 無 `Invalid end tag` 錯誤

---

## 6. Files changed

### Modified
- `frontend/src/views/admin/AdminUsersView.vue`
  - 本次任務實際新增修補：template 刪除 1 個多餘 `</div>`

### Added
- `docs/02_DEVELOPMENT_STATUS/ADMIN_USERSVIEW_TEMPLATE_FIX_REPORT.md`

---

## 7. Remaining risk

- 本檔案仍有**先前任務遺留**的 script 2 行差異（`handleAddMember` 的 error parsing：`err?.response?.data` → `err?.data`）。
- 該差異非本次 template 修補引入，且已在前一份報告（`ADMIN_USERSVIEW_RESTORE_AND_PATCH_REPORT.md`）記錄。
- 就本次目標而言，template 結構已修正且 build 通過，風險解除。
