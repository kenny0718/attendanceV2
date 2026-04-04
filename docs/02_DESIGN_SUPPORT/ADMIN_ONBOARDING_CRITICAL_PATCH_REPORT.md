# Admin Onboarding Critical Patch Report

**日期**: 2026-03-23  
**任務**: Safe Patch Only — Fix AdminOnboardingView Critical Runtime/API Mismatch  
**目標檔案**: `frontend/src/views/admin/AdminOnboardingView.vue`  

---

## 1. Summary

本次僅修復 2 個已確認 Critical 問題，未做任何額外功能調整：

1. 移除 `handleOnboard()` 成功路徑中對未定義函式 `loadCompanies()` 的呼叫（避免 `ReferenceError`）
2. 將 onboarding 的錯誤角色值 `role_id: 'admin'` 改為 `role_id: 'company_admin'`（對齊後端 schema）

---

## 2. Root Cause

### Critical-1: Runtime crash
- `handleOnboard()` 成功後呼叫 `await loadCompanies()`
- 但此 View 中沒有 `loadCompanies` 定義
- 會在成功路徑拋出 `ReferenceError`

### Critical-2: API payload mismatch
- 前端預設角色使用 `admin`
- 後端 onboarding schema/role 驗證預期 `company_admin`
- 導致送出後可能被後端以 `INVALID_ROLE`（422）拒絕

---

## 3. Exact Patch Locations

### Fix-1（loadCompanies）
- 檔案: `frontend/src/views/admin/AdminOnboardingView.vue`
- 區塊: `handleOnboard()` success path
- 變更:
  - 刪除 `await loadCompanies()`（1 行）

### Fix-2（role_id）
共 3 處實際 payload/default 值修正 + 1 處 UI option value 修正：

1. Template 角色選單 option value
   - `<option value="admin">...` → `<option value="company_admin">...`
2. `obForm` 初始值
   - `role_id: 'admin'` → `role_id: 'company_admin'`
3. `resetOnboarding()` 重設值
   - `obForm.initial_user.role_id = 'admin'` → `obForm.initial_user.role_id = 'company_admin'`

---

## 4. Validation Performed

已執行並確認：

1. `git status --short`
2. `git diff --stat`
3. `git diff HEAD -- frontend/src/views/admin/AdminOnboardingView.vue`
4. `grep -n "loadCompanies|value=\"admin\"|role_id: 'admin'|obForm.initial_user.role_id = 'admin'|company_admin" frontend/src/views/admin/AdminOnboardingView.vue`

驗證結果：
- 不再存在 `loadCompanies` 呼叫
- 不再存在 `role_id: 'admin'` 或 `value="admin"`
- `company_admin` 已出現在預期 3 個 role 位置

---

## 5. Files Changed

### Modified
- `frontend/src/views/admin/AdminOnboardingView.vue`

### Added
- `docs/02_DEVELOPMENT_STATUS/ADMIN_ONBOARDING_CRITICAL_PATCH_REPORT.md`（本報告）

---

## 6. Remaining Open Risks

- 本檔案中仍有**先前已存在**的非本任務差異（如標題文案、部分圖示/樣式/區塊差異），本次未處理。
- 本次 patch 嚴格限定於兩個 critical 修補範圍，未做 template 重構、CSS 調整、或其他商業邏輯變更。

---

**Safe Edit 規則遵守聲明**
- 未使用 IDE Write/StrReplace 直接改 `.vue`
- 使用 `/tmp` 腳本進行精準 patch
- 未整檔覆寫
- 僅修改本任務允許範圍
