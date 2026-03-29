# WP-TECHDEBT：AdminUsersView.vue 拆分計畫

> **日期**：2026-03-29
> **狀態**：ANALYSIS ONLY — 不實作，僅供計畫確認
> **對象**：`frontend/src/views/admin/AdminUsersView.vue`（906 行）

---

## 1. Summary

### 是否建議拆？
**是。** 906 行已超過安全閾值，繼續堆功能將顯著提高 Cursor 0KB 風險與維護成本。

### 為何現在要拆？
- 每次 patch 都需讀取 900+ 行大檔，truncate 風險高
- 目前已有 6 個責任區塊，任何功能新增都可能互相干擾
- S1-13A1/A2/A3 剛完成，結構相對穩定，是最佳拆分時機
- 拆分後每個元件 < 200 行，未來 patch 可精確定位

---

## 2. Current Structure Audit

### 檔案結構

| 區段 | 行數範圍 | 負責內容 |
|------|----------|----------|
| `<template>` | L1–L347 | 整頁 HTML 模板（346 行）|
| `<script setup>` | L349–L645 | 所有 JS 邏輯（296 行）|
| `<style scoped>` | L647–L907 | 所有 CSS（260 行）|

### Template 責任分解

| 區塊 | 行數 | 責任 |
|------|------|------|
| Company Selector | L18–L55 | 公司下拉選單、載入狀態 |
| Add Member Panel | L57–L116 | 新增成員表單（5 欄位）|
| Members Panel | L117–L270 | Filter bar + Table + 狀態訊息 |
| Initial state placeholder | L264–L273 | 未選公司提示 |
| editModal | L276–L317 | 基本資料 + login_username 編輯 Modal |
| pwdModal | L318–L347 | 重設密碼 Modal |

### Script 責任分解

| 區塊 | 行數 | 責任 |
|------|------|------|
| Companies | L355–L375 | `loadCompanies()`、`companies` ref |
| Members | L375–L403 | `loadMembers()`、`onCompanyChange()` |
| Toggle | L404–L426 | `handleToggle()`、`togglingId` |
| Add Member | L427–L465 | `handleAddMember()`、`newMember` ref |
| Filter/Search | L466–L503 | `filteredMembers` computed、`clearFilters()` |
| editModal | L504–L537 | `openEdit()`、`closeEdit()`、`saveEdit()` |
| pwdModal | L538–L610 | `openPwd()`、`closePwd()`、`savePwd()` |
| saveEdit logic | L611–L644 | `saveEdit()` 實作、local update |
| Utils | L644–L645 | `formatDate()` |

### State 依賴關係

```
selectedCompanyId (page level)
  ├── loadMembers() → members[]
  │     ├── filteredMembers (computed)
  │     ├── handleToggle() → local update
  │     ├── handleAddMember() → loadMembers() reload
  │     ├── openEdit(member) → editModal.membershipId
  │     │     └── saveEdit() → local update members[]
  │     └── openPwd(member) → pwdModal.membershipId
  │           └── savePwd() → API call only
  └── onCompanyChange() → reset filters
```

**關鍵依賴**：`members[]`、`selectedCompanyId`、`loadMembers()` 是所有子功能的共用 state，必須留在 page container 層。

---

## 3. Split Options Comparison

### Option A — 最小拆分（3 元件）

拆出：
- `MemberEditModal.vue`（editModal HTML + openEdit/closeEdit/saveEdit）
- `MemberPasswordModal.vue`（pwdModal HTML + openPwd/closePwd/savePwd）
- `AdminUsersView.vue` 保留其餘所有內容

| 項目 | 評估 |
|------|------|
| 修改風險 | **Low**：只抽 modal，其餘不動 |
| 0KB 防護 | **Medium**：主檔從 906 → ~700 行 |
| 後續維護性 | **Good**：modal 完全獨立，日後新增欄位只改 modal 檔 |
| 適合現階段 | **Yes**：最小侵入，不重構 state |
| 主檔預估行數 | ~700 行（仍偏大）|
| 每個新元件行數 | editModal ~80 行、pwdModal ~60 行 |

**Props/Emit 設計**：
```
MemberEditModal.vue
  props: open, member, companyId
  emits: close, saved(updatedMember)

MemberPasswordModal.vue
  props: open, member, companyId
  emits: close
```

---

### Option B — 中度拆分（5 元件）

在 A 基礎上再拆：
- `MemberCreatePanel.vue`（新增成員表單）
- `MemberFilterBar.vue`（搜尋 + 篩選列）

| 項目 | 評估 |
|------|------|
| 修改風險 | **Medium**：Create panel 依賴 `loadMembers()`，需 emit 通知 |
| 0KB 防護 | **High**：主檔從 906 → ~500 行 |
| 後續維護性 | **Very Good**：各功能完全隔離 |
| 適合現階段 | **Yes（謹慎）**：需仔細設計 emit/callback |
| 主檔預估行數 | ~500 行 |
| 每個新元件行數 | CreatePanel ~120 行、FilterBar ~60 行 |

**Props/Emit 設計**：
```
MemberCreatePanel.vue
  props: companyId, availableRoles
  emits: created(memberName) → parent calls loadMembers()

MemberFilterBar.vue
  props: members[], modelValue(filters)
  emits: update:modelValue
```

---

### Option C — 深度拆分（page container + composables + 6+ 元件）

架構：
```
AdminUsersView.vue (page container, ~150 行)
  ├── useAdminMembers.js (composable: 所有 member state + API)
  ├── useAdminFilters.js (composable: filter/search logic)
  ├── CompanySelector.vue
  ├── MemberCreatePanel.vue
  ├── MembersTable.vue (含 toggle)
  ├── MemberEditModal.vue
  └── MemberPasswordModal.vue
```

| 項目 | 評估 |
|------|------|
| 修改風險 | **High**：需重構 state 流向，涉及所有元件 |
| 0KB 防護 | **Very High**：每個檔案 < 150 行 |
| 後續維護性 | **Excellent**：長期最佳 |
| 適合現階段 | **No**：重構成本高，容易引入 regression |
| 主檔預估行數 | ~150 行 |

**不建議現在做 C**：
- composable 拆分需全面重測
- 目前無 Vue Test Utils 覆蓋，regression 難以快速確認
- 屬於重構而非功能增補，應另開重構票

---

### 三方案比較表

| 維度 | Option A | Option B | Option C |
|------|----------|----------|----------|
| 修改風險 | Low | Medium | High |
| 0KB 防護 | Medium | High | Very High |
| 後續維護性 | Good | Very Good | Excellent |
| 適合現階段 | ✅ Yes | ✅ 謹慎 | ❌ No |
| 執行票數 | 2 票 | 4 票 | 6+ 票 |
| 主檔最終行數 | ~700 | ~500 | ~150 |

---

## 4. Recommended Plan

### 建議採 Option A（最小拆分）+ 視情況推進到 B

**理由：**
1. 風險最低，不重構 state 流向
2. modal 是最自然的邊界（已有獨立 ref + open/close/save）
3. 主檔預估降至 ~700 行，已可安全操作
4. 若後續需求繼續增加，再推進到 B（MemberCreatePanel）

### 拆分順序

#### 第一步：抽 MemberPasswordModal.vue（最小、最安全）
- 最小依賴：只需 `companyId`、`member.membership_id`、`member.display_name`
- `savePwd()` 不需要 `loadMembers()`，emit `close` 即可
- 風險：**Very Low**
- 主檔減少：~70 行

#### 第二步：抽 MemberEditModal.vue
- 依賴：`companyId`、`member`、`availableRoles`
- `saveEdit()` 需 emit `saved(updatedMember)` 讓 parent 做 local update
- 風險：**Low**（local update 邏輯需謹慎傳遞）
- 主檔再減少：~90 行

#### 第三步（可選，視需求）：抽 MemberCreatePanel.vue
- 依賴：`companyId`、`availableRoles`
- emit `created(memberName)` → parent 呼叫 `loadMembers()`
- 風險：**Medium**（需測試新增後 reload 流程）

#### 暫不拆：
- CompanySelector（耦合 `onCompanyChange`，拆出收益低）
- MembersTable（耦合 `togglingId`、`openEdit`、`openPwd`，拆出需傳太多 props）
- FilterBar（邏輯簡單，不值得獨立一票）

---

## 5. Safe Execution Strategy

### 票 1：WP-TECHDEBT-A1 — 抽 MemberPasswordModal.vue

**涉及檔案：**
- 新增：`frontend/src/components/admin/MemberPasswordModal.vue`
- 修改：`AdminUsersView.vue`（移除 pwdModal HTML + 相關 script，改用元件）

**步驟：**
1. 讀取 AdminUsersView.vue 完整內容（禁止 whole-file rewrite）
2. 新建 MemberPasswordModal.vue（props: open/member/companyId，emits: close）
3. 將 pwdModal HTML + savePwd() + closePwd() 移入新元件
4. AdminUsersView.vue patch：移除對應 HTML + script，改用 `<MemberPasswordModal>`
5. 驗證：size > 0、head/tail 正常、瀏覽器手動測試重設密碼流程

**驗證清單：**
- [ ] MemberPasswordModal.vue size > 0
- [ ] AdminUsersView.vue size > 0，行數約 830
- [ ] editModal 功能完全不受影響
- [ ] 重設密碼 modal 開啟/驗證/成功/失敗流程正常

---

### 票 2：WP-TECHDEBT-A2 — 抽 MemberEditModal.vue

**涉及檔案：**
- 新增：`frontend/src/components/admin/MemberEditModal.vue`
- 修改：`AdminUsersView.vue`

**步驟：**
1. 讀取目前 AdminUsersView.vue
2. 新建 MemberEditModal.vue（props: open/member/companyId/availableRoles，emits: close/saved）
3. 將 editModal HTML + openEdit/closeEdit/saveEdit 移入新元件
4. AdminUsersView.vue patch：移除對應內容，改用 `<MemberEditModal @saved="onMemberSaved">`
5. parent 實作 `onMemberSaved(updatedMember)` 做 local update

**驗證清單：**
- [ ] MemberEditModal.vue size > 0
- [ ] AdminUsersView.vue size > 0，行數約 730
- [ ] 編輯 display_name / email / role_id / login_username 正常
- [ ] 409 DUPLICATE_LOGIN_USERNAME 錯誤顯示正常
- [ ] local update 後列表即時反映

---

### 票 3（可選）：WP-TECHDEBT-B1 — 抽 MemberCreatePanel.vue

**前提：** 票 1 + 票 2 完成且穩定後才考慮

**涉及檔案：**
- 新增：`frontend/src/components/admin/MemberCreatePanel.vue`
- 修改：`AdminUsersView.vue`

**驗證清單：**
- [ ] 新增成員後列表自動 reload
- [ ] DUPLICATE_LOGIN_USERNAME 錯誤顯示正常
- [ ] 新增後 filter 自動重置

---

### 每票必做驗證

1. 目標元件 size > 0、head/tail 正常
2. AdminUsersView.vue size > 0、head/tail 正常
3. `<template>` + `<script setup>` + `<style scoped>` 三段均存在
4. 舊功能（toggle active、filter、company selector）完全不受影響
5. 新元件 props/emits 文件化在元件頂部 comment

---

## 6. Risks / Warnings

### 高風險警告

| 風險 | 說明 | 對策 |
|------|------|------|
| AdminUsersView.vue 被截斷 | 大檔 patch 時 Cursor 可能 0KB | 每步驟後立即驗證 size + tail |
| emit 設計不完整 | saveEdit 後 local update 邏輯若未正確 emit，列表不更新 | 先設計 emit 介面再實作 |
| availableRoles 傳遞遺漏 | editModal 需要 roles 列表，若未傳入則 select 空白 | 明確 props 定義，型別標注 |
| CSS 拆分困難 | `<style scoped>` 有 modal 相關 CSS 混在主檔 | modal CSS 隨元件一起遷移，不殘留 |
| 票 3 風險較高 | CreatePanel 的 emit created → loadMembers 鏈路較複雜 | 確認票 1+2 穩定後再做 |

### 現在不要做的事

- **禁止** 同時拆 2 個以上元件（單票只拆 1 個）
- **禁止** 在拆分同時修改功能邏輯（拆分票不做功能變更）
- **禁止** Option C（composable 重構）— 現階段無前端測試覆蓋
- **禁止** 移除 `<style scoped>` 的 CSS variable 定義（會影響全頁）
- **禁止** MembersTable 獨立為元件（prop drilling 過深，現階段不值得）

---

## 7. Final Recommendation

### 下一步：先拆 MemberPasswordModal.vue

**原因：**
1. 依賴最簡單：`companyId` + `membershipId` + `display_name`
2. `savePwd()` 完全獨立，不需要 `loadMembers()` callback
3. emit 設計最簡單：只需 `close`
4. 拆完後可驗證「元件化流程」是否順暢，再推進 editModal
5. 主檔安全減少 ~70 行

### 建議票號命名
- `WP-TECHDEBT-VUE-01`：抽 MemberPasswordModal.vue
- `WP-TECHDEBT-VUE-02`：抽 MemberEditModal.vue
- `WP-TECHDEBT-VUE-03`（可選）：抽 MemberCreatePanel.vue

### 預期最終結果（A+B 完成後）
- `AdminUsersView.vue`：~500–550 行（安全範圍）
- `MemberPasswordModal.vue`：~70 行
- `MemberEditModal.vue`：~100 行
- `MemberCreatePanel.vue`：~120 行（可選）
- 每個元件獨立可測試、獨立 patch

---

*報告產生時間：2026-03-29*
*分析基準：AdminUsersView.vue @ commit d7c2fb0（906 行）*
