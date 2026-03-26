# S1-11 / A1-1 Completion Report

- 日期：2026-03-24
- 狀態：Completed
- 範圍：A1-1（Authorization Boundary Fix）+ A1-1T（Test Alignment）

## 1. Summary
- 本票目標：收斂 tenants admin 授權邊界並完成測試對齊。
- 完成狀態：**Completed**。
- 核心成果：已將 tenants admin 權限收斂為「`super_admin` 全域、`company_admin/hr_manager` 僅 own company、跨公司一律 403」，並完成最小測試對齊與驗證。

## 2. Files Changed
### Production
- `backend/app/modules/tenants/api.py`
- `backend/app/modules/tenants/api_members.py`

### Tests
- `backend/app/modules/tenants/tests/test_companies_api.py`
- `backend/app/modules/tenants/tests/test_members_api.py`
- `backend/app/modules/tenants/tests/test_toggle_membership.py`

## 3. Authorization Matrix (After Fix)

| 角色 | 可跨公司 | 可操作 companies | 可操作 members |
|---|---|---|---|
| `super_admin` | 是 | 是（全域） | 是（全域） |
| `company_admin` | 否 | 是（僅 own company） | 是（僅 own company） |
| `hr_manager` | 否 | 是（僅 own company） | 是（僅 own company） |
| `employee` | 否 | 否 | 否 |

## 4. Key Changes
- 引入 `_assert_admin_company_access(...)`（companies / members API）。
- 強制 company scope 驗證（含 active company 一致性）。
- `list_companies` 行為收斂：
  - `super_admin` 看全部
  - `company_admin/hr_manager` 僅 own company 單筆
- 移除舊跨公司可操作行為（改為 403）。

## 5. Tests Alignment
- 舊跨公司成功案例改為拒絕：多個 `company_admin/hr_manager` case 由 **200 → 403**。
- own company 合法操作案例對齊：部分 case 由 **403 → 200/201**。
- `list_companies` 測試強化：不只驗證 status code，也驗證回傳內容為 own company 單筆（`total == 1` 且 `id` 符合）。

## 6. Validation Result
- 測試範圍：
  - `test_companies_api.py`
  - `test_members_api.py`
  - `test_toggle_membership.py`
- 結果：**72 passed**
- 是否有失敗：**NO**
- 是否有新增風險：**NO**（僅既有 warnings，無本票新增失敗）

## 7. Incident Note
- 事故：`backend/app/modules/tenants/api.py` 與 `api_members.py` 曾出現 0-byte 清空。
- 處理：
  1. 先以版本庫內容恢復（git restore / checkout）
  2. 再重新套用 A1-1 授權邊界修補
- 最終狀態：已恢復且經 A1-1T 測試驗證通過。

## 8. Known Limitations
- 尚未進入 legacy cleanup phase 2。
- role normalization 在其他模組仍有待後續收斂（本票未擴 scope）。

## 9. NEXT_WP_TICKET.md updated
NO
