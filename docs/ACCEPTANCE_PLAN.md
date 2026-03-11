# ACCEPTANCE_PLAN.md

## Purpose

各模組的驗收計畫，定義驗收前置條件、驗收案例、通過標準、失敗記錄方式。

## Scope

覆蓋所有已實作模組與已規劃但未實作的模組（以 Placeholder 方式記錄）。

## Source of Truth

- `MODULE_STATUS_MATRIX.md`（模組狀態）
- `SA_MODULE_SPEC_v2.0.md`（架構規範）
- `API_DOCUMENTATION_v2.0.md`（API 合約）

## Last Updated

2026-03-11

---

## 驗收層次定義

| 層次 | 定義 |
|------|------|
| **CODE-LEVEL** | 程式碼邏輯審查（不需 DB） |
| **API-LEVEL** | 真實 HTTP 請求對真實 DB 執行 |
| **BROWSER/MANUAL QA** | 瀏覽器操作，含 GPS 功能 |
| **DB-LEVEL** | 直接查詢 PostgreSQL 確認資料正確性 |

---

## 驗收失敗記錄方式

所有驗收失敗必須記錄到 `docs/WP-[WP_ID]_DEFECT_LOG.md`，格式：

```
## Defect [ID]
- 發現時間：
- 驗收層次：
- 描述：
- 重現步驟：
- 期望結果：
- 實際結果：
- 嚴重程度：P0/P1/P2
- 狀態：OPEN/FIXED/WONTFIX
```

---

## 模組驗收計畫

### M1. auth 模組

**驗收前置條件：**
- PostgreSQL DB 已啟動，migration 執行完成
- auth 模組的 backend 服務已啟動

**驗收案例：**

| ID | 案例 | 層次 | 通過標準 |
|----|------|------|----------|
| AUTH-01 | 正確帳密登入 | API-LEVEL | 回傳 200 + access_token + user + company + role |
| AUTH-02 | 錯誤帳密登入 | API-LEVEL | 回傳 401 |
| AUTH-03 | JWT token 解析正確 | CODE-LEVEL | decode_access_token 回傳正確 user_id/role_id |
| AUTH-04 | 過期 token 被拒 | API-LEVEL | 使用過期 token 呼叫任何受保護 API → 401 |
| AUTH-05 | user_company_memberships 查詢正確 | DB-LEVEL | 登入後 DB 可查到正確 membership 記錄 |
| AUTH-06 | 非 active user 被拒 | API-LEVEL | is_active=False 的 user 登入 → 403 |

**驗收通過標準：** AUTH-01 ~ AUTH-06 全部通過

---

### M2. tenants 模組

**驗收前置條件：**
- auth 模組驗收通過（M1）
- 有效 JWT token（super_admin 角色）

**驗收案例：**

| ID | 案例 | 層次 | 通過標準 |
|----|------|------|----------|
| TENANT-01 | 查詢公司 entitlements | API-LEVEL | 200 + 正確 feature flags 列表 |
| TENANT-02 | 更新 entitlement（啟用功能） | API-LEVEL | PATCH 後查詢確認 enabled=true |
| TENANT-03 | 無 membership 的 company_user 存取 → 403 | API-LEVEL | 403 + FORBIDDEN |
| TENANT-04 | customer_service 只能存取已指派公司 | API-LEVEL | 未指派的公司 → 403 |
| TENANT-05 | apply-plan 套用預設方案 | API-LEVEL | 200 + 指定 tier 的 features 全部啟用 |
| TENANT-06 | Tenant isolation：A 公司無法查 B 公司 entitlements | API-LEVEL | 403 |

**驗收通過標準：** TENANT-01 ~ TENANT-06 全部通過

---

### M3. attendance 核心模組

**驗收前置條件：**
- WP-C1-02 完成（JWT auth 轉換）
- WP-C1-04 完成（8 個回歸測試通過）
- PostgreSQL DB 有測試資料（tenant + user + membership）

**驗收案例：**

| ID | 案例 | 層次 | 通過標準 |
|----|------|------|----------|
| ATT-01 | punch-in 成功 | API-LEVEL | 201 + session_id + punch_in_time |
| ATT-02 | 重複 punch-in 被拒 | API-LEVEL | 400 + BUSINESS_RULE_VIOLATION |
| ATT-03 | punch-out 成功 | API-LEVEL | 200 + punch_out_time + policy 評估結果 |
| ATT-04 | 無 punch-in 直接 punch-out 被拒 | API-LEVEL | 400 |
| ATT-05 | current-status 回傳正確狀態 | API-LEVEL | 200 + is_punched_in/is_on_break 正確 |
| ATT-06 | break-out 成功（無 location policy） | API-LEVEL | 200 + punch_time |
| ATT-07 | break-in 成功 | API-LEVEL | 200 + punch_time |
| ATT-08 | history 回傳正確分頁 | API-LEVEL | 200 + sessions 列表 |
| ATT-09 | 回歸測試 1-8 全部通過 | DB-LEVEL | 8/8 pytest PASS |
| ATT-10 | Header auth 已移除（不再接受 X-Company-ID） | API-LEVEL | 缺少 JWT → 401（不是 422） |
| ATT-11 | punch note PATCH 成功 | API-LEVEL | 200 + 備註更新 |
| ATT-12 | 其他公司 session 無法存取 | DB-LEVEL | Tenant Isolation PASS |

**驗收通過標準：** ATT-01 ~ ATT-12 全部通過

---

### M4. break flow + GPS / Location Policy

**驗收前置條件：**
- M3 通過
- WP-C2-01 完成（Location Policy 擴展）
- 已建立至少一個 allowed_location 測試資料
- 真實瀏覽器（支援 navigator.geolocation）

**驗收案例：**

| ID | 案例 | 層次 | 通過標準 |
|----|------|------|----------|
| LOC-01 | 無 allowed locations → 任何地點允許打卡 | API-LEVEL | 200，無 location_policy 欄位限制 |
| LOC-02 | 在 allowed location 範圍內打卡 → 允許 | API-LEVEL | 200 + location_policy.allowed=true |
| LOC-03 | 超出 allowed location 範圍 → 403 | API-LEVEL | 403 + LOCATION_POLICY_VIOLATION + nearest_location |
| LOC-04 | 有 location policy 但未提供 GPS → 400 | API-LEVEL | 400 + GPS_REQUIRED_FOR_LOCATION_POLICY |
| LOC-05 | 前端 GPS 定位成功並傳至後端 | BROWSER/MANUAL QA | break-out 按鈕觸發 GPS → API 呼叫含 gps 欄位 |
| LOC-06 | 前端顯示 LOCATION_POLICY_VIOLATION 錯誤訊息 | BROWSER/MANUAL QA | 友善錯誤訊息含距離資訊 |
| LOC-07 | A 公司 location 無法影響 B 公司打卡 | DB-LEVEL | 跨租戶 location policy 隔離 |
| LOC-08 | Admin 建立 allowed location（需 admin role） | API-LEVEL | 201；普通 employee 嘗試 → 403 |

**驗收通過標準：** LOC-01 ~ LOC-08 全部通過

---

### M5. backup 模組

**驗收前置條件：**
- WP-C1-03 完成（backup Auth 轉換）
- DB 有測試資料

**驗收案例：**

| ID | 案例 | 層次 | 通過標準 |
|----|------|------|----------|
| BAK-01 | 匯出公司 A 的備份 | API-LEVEL | 200 + JSON 含所有 Tenant Data |
| BAK-02 | 匯出結果只含公司 A 資料（不含 B） | DB-LEVEL | JSON 中所有 company_id 均為 A |
| BAK-03 | 還原備份至公司 A | API-LEVEL | 200 + 資料還原成功 |
| BAK-04 | 還原後公司 B 資料未被污染 | DB-LEVEL | B 的資料未改變 |
| BAK-05 | 無 backup.export feature → 403 | API-LEVEL | 403 + FEATURE_DISABLED |

**驗收通過標準：** BAK-01 ~ BAK-05 全部通過

---

### M6. audit 模組

**驗收前置條件：**
- WP-C1-03 完成（audit Auth 轉換）

**驗收案例：**

| ID | 案例 | 層次 | 通過標準 |
|----|------|------|----------|
| AUD-01 | 查詢稽核日誌（含分頁） | API-LEVEL | 200 + logs 列表 |
| AUD-02 | 查詢結果只含本公司資料 | DB-LEVEL | 所有 company_id 正確 |
| AUD-03 | 匯出 CSV | API-LEVEL | 200 + CSV content-type |
| AUD-04 | 設定 retention policy | API-LEVEL | 200 + 更新確認 |
| AUD-05 | purge 過期日誌 | API-LEVEL | 200 + 刪除數量 |
| AUD-06 | 無 audit.query feature → 403 | API-LEVEL | 403 + FEATURE_DISABLED |

**驗收通過標準：** AUD-01 ~ AUD-06 全部通過

---

### M7. notifications 模組

**驗收前置條件：**
- WP-C1-03 完成

**驗收案例：**

| ID | 案例 | 層次 | 通過標準 |
|----|------|------|----------|
| NOT-01 | 查詢通知列表 | API-LEVEL | 200 + notifications 列表 |
| NOT-02 | 打卡核准後觸發通知事件 | DB-LEVEL | DB 有對應的 notification 記錄 |
| NOT-03 | Tenant Isolation | DB-LEVEL | 查詢只回傳本公司通知 |

**驗收通過標準：** NOT-01 ~ NOT-03 全部通過

---

### M8. reporting（Future Acceptance Placeholder）

**狀態：** 待 WP-C2-02 完成後建立詳細驗收案例

**預期驗收面向：**
- company-summary 報表資料正確性
- user-summary 報表資料正確性
- Tenant Isolation（只能查自己公司）
- 日期範圍過濾正確
- Scope 驗證（employee 只能查自己）

---

### M9. leave / approval / accrual（Future Acceptance Placeholder）

**狀態：** 待 Phase 2 模組實作後建立

---

## Tenant Isolation 驗收（跨模組）

| ID | 案例 | 層次 | 通過標準 |
|----|------|------|----------|
| TI-01 | A 公司 JWT 無法查詢 B 公司 attendance sessions | DB-LEVEL | 查詢結果為空或 403 |
| TI-02 | A 公司 JWT 無法修改 B 公司 allowed_locations | API-LEVEL | 404（not found in A's scope） |
| TI-03 | 無 membership 的 user → 403 | API-LEVEL | 403 |
| TI-04 | Restore 不污染其他 company | DB-LEVEL | 還原後其他 company 資料不變 |
| TI-05 | customer_service 只能存取已指派公司 | API-LEVEL | 未指派公司 → 403 |

**驗收通過標準：** TI-01 ~ TI-05 