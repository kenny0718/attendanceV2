# AdminUsersView Restore and Patch Report

**建立日期：** 2026-03-23  
**執行性質：** Safe Restore + Minimal Patch  
**依據：** ADMIN_FRONTEND_AUDIT_REPORT.md（HIGH RISK — regression 判定）
**執行依據規則：** CURSOR_FRONTEND_SAFE_EDIT_RULES.md

---

## 1. Summary

| 項目 | 結果 |
|------|------|
| AdminUsersView.vue restore 狀態 | ✅ 已還原（643 行，與 HEAD 一致）|
| Add Member Panel（WP-S1-10D）| ✅ 存在 |
| Filter / Search Bar（S1-10F）| ✅ 存在 |
| Toggle Membership Active（S1-10C）| ✅ 存在 |
| filteredMembers computed | ✅ 存在 |
| handleAddMember() error parsing 修補 | ✅ 已套用 |
| 非預期額外變更 | **無** |
| 功能檔修改方式 | Shell（git restore + sed patch），非 IDE Write |
| Safe Edit 規則遵守 | ✅ 完全遵守 |

---

## 2. Why Restore Was Required

先前審計（`ADMIN_FRONTEND_AUDIT_REPORT.md`）發現工作樹 `AdminUsersView.vue` 相比 HEAD 存在以下 HIGH RISK regression：

- **-340 行（-52%）**：三個主要功能區塊全部消失
- Add Member Panel（WP-S1-10D）整體移除
- Filter / Search / Status / Role 控制欄（S1-10F）整體移除
- Toggle Membership Active（S1-10C）整體移除
- `filteredMembers` computed、`handleToggle()`、`handleAddMember()` 全部移除
- `import { computed }` 被移除
- `v-for="m in filteredMembers"` 退化為 `v-for="m in members"`

此刪減無對應 git commit 說明，判定為疑似 regression（非故意功能降級）。

同時審計發現 HEAD 版本 `handleAddMember()` 的 error parsing 存在路徑錯誤：
- 錯誤：`err?.response?.data?.detail?.code`
- `api/client.js` 的 reject 結構為 `{ status, message, data }`（已包裝，非 axios 原始 response）
- 正確路徑應為：`err?.data?.detail?.code`

---

## 3. Pre-Restore Git Findings

```
git status --short 結果：
 M frontend/src/views/admin/AdminUsersView.vue

git diff --stat HEAD 結果：
 frontend/src/views/admin/AdminUsersView.vue | 378 ++---------------------
 5 files changed, 46 insertions(+), 389 deletions(-)

工作樹行數：303 行（14,416 bytes）
HEAD 行數：643 行（~30,068 bytes）
差異：-340 行（-52%）
```

---

## 4. Restore Action Performed

**執行指令：**
```bash
git restore frontend/src/views/admin/AdminUsersView.vue
```

**還原後驗證：**
```
git diff HEAD -- frontend/src/views/admin/AdminUsersView.vue
→ 僅剩 error parsing patch（+2 / -2 行），無其他差異

工作樹行數：643 行
HEAD 行數：643 行
差異：0（restore 完成）
```

---

## 5. Minimal Patch Detail

### 修補範圍：`handleAddMember()` catch 區塊 error parsing

**修補位置：** `frontend/src/views/admin/AdminUsersView.vue`，第 377–388 行

**修補內容（唯一變更）：**

```diff
  } catch (err) {
-   const code = err?.response?.data?.detail?.code
+   const code = err?.data?.detail?.code
    if (code === 'DUPLICATE_LOGIN_USERNAME') {
      addMemberError.value = '此公司已有相同的登入帳號，請更換。'
    } else if (code === 'INVALID_ROLE') {
      addMemberError.value = '角色不存在，請選擇有效角色。'
    } else {
-     addMemberError.value = err?.response?.data?.detail?.message || err.message || '建立失敗，請稍後再試'
+     addMemberError.value = err?.data?.detail?.message || err.message || '建立失敗，請稍後再試'
    }
  }
```

**修補原因：**
`frontend/src/api/client.js` 的 response interceptor 在 error 時回傳：
```javascript
return Promise.reject({ status, message: data?.detail || data?.message || '請求失敗', data })
```
reject 物件結構為 `{ status, message, data }`，`data` 即 axios `error.response.data`（FastAPI response body）。
正確 error code 取法為 `err?.data?.detail?.code`，與 `AdminOnboardingView.vue` 使用方式一致。

**修補方式：** Shell `sed` 指令，非 IDE Write/StrReplace。

---

## 6. Validation Performed

### 6.1 功能區塊確認（grep 驗證）

| 功能區塊 | grep 關鍵字 | 行號 | 狀態 |
|----------|------------|------|------|
| Add Member Panel | `Add Member Panel (WP-S1-10D)` | 57 | ✅ 存在 |
| Add Member 表單 | `handleAddMember` | 76, 359 | ✅ 存在 |
| Filter bar | `Filter bar 