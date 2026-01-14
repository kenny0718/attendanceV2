# SA_MODULE_SPEC v1.7（必讀必遵守）
> 目的：確保 A 架構（同庫同表 + company_id）下，A 公司與 B 公司資料完全隔離；
>      並確保「單一公司備份 / 還原」不會混入其他公司資料。

---
## 1. 強制專案結構（沿用 v1.6）
每個模組必須存在下列檔案（缺一不可）：
- api.py / service.py / repo.py / models.py / docs.md / tests/
路徑：
`backend/app/modules/<module_name>/...`

模組清單（沿用 v1.6）：
- tenants / auth / locations / attendance / approvals / notifications / vehicles / dispatch / leave / accrual / reporting

---
## 2. 禁止事項（沿用 v1.6）
- 禁止跨模組直接 import 對方 service/repo/models
- 禁止跨模組直接寫入對方資料表
- 禁止為了手機版修改桌機 CSS
- reporting 只讀彙總，不做任何規則或狀態變更

---
## 3. 允許的跨模組互動方式（沿用 v1.6）
A) EventBus（優先）
B) Public Interface（少量）

---
## 4. attendance 核心不可破壞（P0，沿用 v1.6）
- PENDING_APPROVAL 不參與推導、不參與日結
- 出勤成立必須有 APPROVED IN
- 派車/請假/額度不得改動 attendance 推導與日結語意

---
## 5. customer_service 權限硬規則（沿用 v1.6）
- customer_service 只能操作被指派公司（support_company_assignments）
- 產生 pairing code / 重置密碼 / 撤銷裝置等動作必須寫 audit log

---
## 6. Trusted Device / Site Pairing 規則（沿用 v1.6）
- Pairing code 僅用於裝置綁定，不可作為每日打卡依據
- Pairing code：short-lived（建議 10 分鐘）、one-time
- scope = company_id + site_id
- 配對成功後，該裝置打卡視為 SITE_MATCH（是否 APPROVED 由公司策略決定）

---
## 7. 請假 / 額度 / 統計（沿用 v1.6）
- leave：只管流程
- accrual：只管 ledger
- reporting：只讀彙總，不做任何規則

---
## 8. 派車等級（沿用 v1.6，只做 Level 0 / 1）
- default = 1
- 未完成 APPROVED IN → 禁止開始用車
- AutoClose（預設 23:59）→ dispatch.autoclosed

---
## 9. UI / CSS 改版規則（沿用 v1.6）
- 桌機 CSS 不動
- 手機只允許 @media (max-width: 768px) 排版調整
- 禁止改配色 / HTML 結構

---
## 10. 必跑回歸測試（打卡核心 8 條，沿用 v1.6）
1) NO_MATCH 未填原因 → 拒絕
2) NO_MATCH 有原因 → PENDING
3) APPROVED → 推導正確
4) PENDING 不參與推導與日結
5) 21:00 日結缺卡 / 可能缺卡正確
6) approve pending → 該日重算
7) customer_service 未指派公司 → 403
8) OTP / Reset token 一次性 + 強制改密碼

---
# ✅ v1.7 新增：Tenant Isolation（P0，最重要）

## 11. Tenant Isolation（P0）
> 核心原則：只要是「租戶資料（Tenant Data）」就必須 100% 綁定 company_id，
> 且 company_id 必須由後端依登入者 context 自動注入；任何 CRUD 不得跨 company_id。

### 11.1 資料分類
A) Tenant Data（租戶資料）
- 任何「屬於某公司」的資料，必須是 Tenant Data
- 硬規則：Tenant Data 的每張表必須有 company_id（不得例外）

B) System Data（系統資料）
- 不屬於任何公司，全域共享（例如 permission codes、全域設定等）
- System Data 不得引用 Tenant Data 的資料列作為「跨租戶共享依據」

### 11.2 company_id 注入規則（寫入/更新）
- 禁止信任 request body / querystring 內的 company_id
- Create/Update/Upsert：
  - company_id 必須以 current_company_id 覆寫/注入
  - 若 request 夾帶 company_id：
    - 策略 A（推薦）：忽略 request company_id，統一以 current_company_id 寫入
    - 或 策略 B：直接回 400（但要全系統一致）
  - 任一策略都必須「不可寫入別家公司 company_id」

### 11.3 company_id 篩選規則（讀取/刪除/查詢）
- Read/Update/Delete/Query：
  - 任何 Tenant Data 查詢必須強制套用 company_id == current_company_id
- 禁止任何「不帶 company_id 條件」的 Tenant Data 查詢
- 例外：只有 System Data 才能不帶 company_id

### 11.4 實作約束（必須做到工程師不會漏）
允許以下任一（或混合）方式，但必須達成「系統級保證」：
- Repo Base / Query Helper：提供 tenant_scoped_query(model) 統一注入 company_id（推薦）
- Middleware：統一在 request context / session 層注入限制（要小心例外路徑）
- DB RLS（強烈建議）：作為最後一道保命線（程式漏寫 filter 也不會跨租戶）

---
# ✅ v1.7 新增：Backup / Restore（P0）

## 12. 單一公司備份（Export，P0）
- 目標：輸出只包含指定 company_id 的 Tenant Data
- 硬規則：
  - 每一張 Tenant Data 表的匯出都必須加 company_id filter
  - 禁止「整表掃出後再程式端過濾」

## 13. 單一公司還原（Restore，P0）
- 目標：還原後所有 Tenant Data 必須落在 target_company_id
- 硬規則：
  - 還原寫入時必須覆寫/注入 company_id = target_company_id（不信任備份檔內 company_id）
  - 若備份檔內混入其他 company_id：
    - 必須 fail fast（拒絕還原），避免資料污染

## 14. Restore 前置檢查（P0）
Restore 前必做：
1) Company Consistency Check
   - 備份檔內如存在 company_id 欄位，必須一致（或可被覆寫一致）
2) FK Closure Check（外鍵閉包）
   - 任一被引用資料列必須存在於備份集內（避免引用到其他公司資料）

---
# ✅ v1.7 新增：Tenant/Backup 必跑測試（P0）

## 15. Tenant Isolation 測試（P0）
- A 公司 token 查 B 公司資料 → 必須 403 或空集合（依 API 設計一致）
- A 公司建立/更新資料，即使 body 帶 B 的 company_id → 仍必須落在 A（或直接 400）
- customer_service 未指派公司 → 403（沿用核心測試）

## 16. Backup / Restore 測試（P0）
- 匯出 company A → 輸出不得包含 company B 的任何資料
- 還原到 company A → 還原後查詢不得看到 company B 的資料
- 備份檔混入其他 company_id → restore 必須 fail fast（拒絕）

---

### 17. API Error Handling & Status Code Rules

Decision Principle:
- If the error is caused by FastAPI/Pydantic schema validation → 422
- If the error is caused by system-level business rules → 400


