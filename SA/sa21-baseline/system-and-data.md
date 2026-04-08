# System and Data（系統與資料）

> 這份文件從 `SA/SA21功能清單基線.md` 拆出「系統級與資料級」內容。  
> 目的是先讓你理解：這套 `SaaS`（軟體即服務）系統最底層是怎麼分資料、怎麼建立 `scope`（操作範圍 / 身分作用範圍）、怎麼避免跨公司污染。

---

## 1. 這份在看什麼

這份不是在看某個單一業務功能，
而是在看：

- 系統是不是 `multi-tenant`（多租戶）
- 資料怎麼分類
- `company_id`（公司識別）怎麼用
- `request context`（請求上下文）怎麼建立
- 為什麼不能把所有資料混在一起想

如果這一層沒先釐清，後面模組很容易放錯。

---

## 2. 系統級功能（System-Level Functions）

## 2.1 多租戶架構（`Multi-tenant Architecture`）
- 系統採同庫同表
- 不同公司共用資料庫與資料表
- 真正的隔離依靠 `company_id`（公司識別）

白話講：

> A 公司跟 B 公司雖然在同一套系統裡，但資料不能互相看到。

## 2.2 平台身份架構（`Platform-first Identity`）
- `users`（平台使用者）是平台身份，不直接屬於某家公司
- 一個 `user`（使用者）可以透過 `membership`（成員關係 / 歸屬關係）進入不同 `company scope`（公司操作範圍）
- `request`（這次操作）中的 `active company`（目前作用中的公司）是這次操作所屬公司

白話講：

> 人是平台的人，這次是用哪家公司的身份做事，要另外判定。

## 2.3 `request context`（請求上下文）
每次 `request`（請求）都應該知道：
- 你是誰（`current_user_id`：目前使用者識別）
- 你這次屬於哪家公司（`current_company_id`：目前公司識別）

而且：
- `company_id` 不能直接信任前端 `body`（請求資料）傳進來的值

---

## 3. 資料分類（Data Classification）

這是你前面問過、最容易亂掉的一段。

## 3.1 `Platform Data`（平台資料）
定義：
- 屬於整個平台
- 不屬於任何單一 `company`（公司）

例子：
- `users`（平台使用者）
- `global_permissions`（全域權限）
- `system_configs`（系統設定）
- `platform_audit_logs`（平台稽核紀錄）

規則：
- 不應有 `company_id`
- 不應用 `tenant filter`（租戶過濾條件）查詢
- 不參與單一公司 `restore`（還原）

白話講：

> 這類資料是整個平台共用的，不是 A 公司或 B 公司專屬。

## 3.2 `Membership Data`（關聯資料 / 歸屬關係資料）
定義：
- 用來表示 `user`（使用者）跟 `company`（公司）的關係
- 或表示客服能支援哪些公司

例子：
- `user_company_memberships`（使用者與公司關聯）
- `support_company_assignments`（客服支援公司指派）

規則：
- 要有 `user_id`
- 要有 `company_id`
- 要能支援 `scope validation`（範圍驗證）

白話講：

> 這類資料不是業務資料，而是在回答「你跟這家公司有沒有關係」。

## 3.3 `Tenant Data`（租戶資料 / 公司自己的資料）
定義：
- 真正屬於某家公司自己的業務資料

例子：
- `attendance`（出勤）
- `leave`（請假）
- `locations`（打卡地點）
- `dispatch`（派工）
- `notifications`（通知）

規則：
- 每張表都要有 `company_id`
- 查詢一定要帶 `company_id`
- 寫入不能信任 `request`（請求）傳入的 `company_id`

白話講：

> 這類資料就是 A 公司自己的資料，不能讓 B 公司看到。

---

## 4. 為什麼資料分類重要

因為這三類資料在下面三件事的規則不同：

### 4.1 `isolation`（隔離）
- `Platform Data`（平台資料）：不是用公司隔離
- `Membership Data`（關聯資料）：用來判定關係與 `scope`（作用範圍）
- `Tenant Data`（租戶資料）：必須靠公司隔離

### 4.2 `restore`（還原）
- `Platform Data`（平台資料）：不屬於單一公司，不應直接跟公司還原綁在一起
- `Membership Data`（關聯資料）：要小心處理，不是一般業務資料
- `Tenant Data`（租戶資料）：才是單公司備份 / 還原的主體

### 4.3 `query`（查詢）
- `Platform Data`（平台資料）：查全域
- `Membership Data`（關聯資料）：查關係
- `Tenant Data`（租戶資料）：查公司自己的資料

---

## 5. `Tenant Isolation`（租戶隔離）基線

## 5.1 寫入規則
- `Create / Update`（建立 / 更新）不可信任 `request body`（請求內容）裡的 `company_id`
- 後端應以 `current_company_id`（目前公司識別）覆寫

## 5.2 查詢規則
- `Tenant Data`（租戶資料）查詢必須 `WHERE company_id = current_company_id`
- 不能先全表查出來再在應用層過濾

## 5.3 工程保證機制
除了規則之外，還應考慮：
- `base repo / query helper`（共用資料存取基底 / 查詢輔助）
- `dependency / middleware`（依賴注入 / 中介層）
- `RLS`（`Row Level Security`，資料列層級安全）

白話講：

> 不能只靠人記得，要讓系統幫忙守規則。

---

## 6. 你目前看這份時，最需要確認什麼

你只要先確認下面幾題：

1. 你能不能接受資料分成這三類？
2. `users`（平台使用者）你要不要當成平台資料？
3. `membership`（關聯 / 歸屬關係）你要不要獨立看待，不跟業務資料混在一起？
4. 你能不能接受 `tenant data`（租戶資料）一律強綁 `company_id`？
5. 你要不要在後續 `SDD`（系統設計文件）裡，把這些規則放進 `SYSTEM_SDD`（系統級設計文件）？

---

## 7. 下一步會接到哪裡

這份確認完之後，下一份建議看：

- `SA/sa21-baseline/platform-and-saas.md`

因為那份會開始接：
- `auth`（身分驗證 / 登入）
- `roles`（角色）
- `scope`（操作範圍）
- `feature flags`（功能開關）
- `audit`（稽核）
- `backup / restore`（備份 / 還原）
