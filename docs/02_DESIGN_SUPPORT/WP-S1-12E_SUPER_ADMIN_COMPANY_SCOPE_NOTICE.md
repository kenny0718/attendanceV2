# WP-S1-12E Super Admin Company Scope Notice

**日期：** 2026-03-28
**執行人：** Cursor AI Agent
**任務：** RISK-03 UI 限制提示修正
**Commit：** c477497
**狀態：** COMPLETE

---

## 1. Summary

本輪修正 S1-12 已知限制 RISK-03：
- super_admin 無 active_company_id 時，/admin/attendance 原本呈現空集合，體感像「功能壞掉」
- 本輪加入明確 UI 提示，區分「功能限制」與「查無資料」兩種狀態
- 僅做最小 patch-style 修改，不影響任何 business logic / tenant isolation / API contract

---

## 2. Files Changed

| 檔案 | 變更類型 | 說明 |
|------|----------|------|
| frontend/src/views/admin/AdminAttendanceView.vue | patch（+13 行）| 加入 super_admin 無 scope 提示 |

---

## 3. Root Cause

super_admin 的 JWT actor 可能沒有 active_company_id（無公司 scope）。
backend repo 層強制 `WHERE company_id = ?`，company_id=None 時返回空集合。
前端無法區分「真的無資料」和「因缺少 company scope 而無法查詢」。
使用者體感：功能壞掉或沒有資料。

---

## 4. Fix Approach

### 判斷方式

authStore 已有：
- `isSuperAdmin = role?.id === "super_admin"`
- `companyId = company?.id`

新增 computed：

```js
const isSuperAdminNoScope = computed(
  () => authStore.isSuperAdmin && !authStore.companyId
)
```

### Template 修改（state-box 鏈優先順序）

```
v-if="isSuperAdminNoScope"          → 限制提示（最優先）
v-else-if="loading"                  → 載入中
v-else-if="error"                    → 載入失敗
v-else-if="!queried"                 → 請選擇日期範圍
v-else-if="sessions.length === 0"    → 此期間無打卡紀錄
v-else                               → 資料表格
```

`isSuperAdminNoScope` 優先最高，不會和其他 state 混淆。

### 提示內容

```
標題：需要公司範圍才能查詢
說明：目前帳號未選定公司範圍，無法查詢打卡資料。
      請先切換至特定公司後再使用此功能。
```

### Style

```css
.state-notice {
  color: #92400e;
  background: #fffbeb;
  border-radius: 12px;
  border: 1px solid #fde68a;
}
```

琥珀色警告風格，與 state-error（紅色）明確區分。

---

## 5. Validation

### Scenario 1：super_admin 無 active_company_id

```
isSuperAdmin = true, companyId = null/undefined
→ isSuperAdminNoScope = true
→ 顯示「需要公司範圍才能查詢」提示（琥珀色）
→ 不顯示 loading / error / empty state
→ 不誤判為系統錯誤
```

### Scenario 2：super_admin 有 active_company_id

```
isSuperAdmin = true, companyId = "company-xxx"
→ isSuperAdminNoScope = false
→ 走正常查詢流程（onMounted loadSessions）
→ 顯示該公司打卡資料
```

### Scenario 3：company_admin / hr_manager

```
isSuperAdmin = false
→ isSuperAdminNoScope = false（不管有無 companyId）
→ 原本查詢流程完全不受影響
→ tenant isolation 維持不變
```

### Scenario 4：employee

```
router guard 拒絕進入 /admin/attendance（維持不變）
```

---

## 6. Regression Check

| 項目 | 影響 | 結果 |
|------|------|------|
| company_admin 查詢流程 | 無影響 | PASS |
| hr_manager 查詢流程 | 無影響 | PASS |
| Tenant isolation | 無影響 | PASS |
| Route guard | 無影響 | PASS |
| API contract | 無影響 | PASS |
| SessionResponse schema | 無影響 | PASS |

---

## 7. Risks / Follow-up

| 風險 | 等級 | 說明 |
|------|------|------|
| super_admin 跨公司查詢 | 需設計 | 本輪不做，需獨立設計 company selector |
| user_a.id.id test bug | Medium | test_reporting_sessions.py 3 處需修正 |

---

## 8. Final Status

**RISK-03：RESOLVED（UI 層）**

- super_admin 無 company scope 時，使用者看到明確的限制提示
- 不誤判為系統錯誤
- 不影響既有安全與 tenant 邏輯
- 深層的「super_admin 跨公司查詢」功能設計留待獨立票處理

---

*本輪成功標準達成：已知限制清楚顯示，避免誤判為系統壞掉。*
