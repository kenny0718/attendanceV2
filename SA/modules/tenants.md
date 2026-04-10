# tenants 模組 SDD

**模組名稱**：`tenants`  
**你可以把它理解成**：系統的「公司與租戶管理中心」  
**程式位置**：`backend/app/modules/tenants`

---

## 1. 這個模組是做什麼的？

`tenants` 管理的是「公司這個租戶單位」本身。

白話說：

- 公司資料在這裡管理
- 公司成員在這裡管理
- 功能開關（entitlements）也在這裡管理
- onboarding 也屬於這裡

---

## 2. 主要功能

### 2.1 Company CRUD
用途：建立與管理公司資料。

### 2.2 Members 管理
用途：管理公司內有哪些成員、成員的基本設定。

### 2.3 Onboarding
用途：處理公司開通或初始設定流程。

### 2.4 Feature Entitlements
用途：決定這家公司能不能用某些功能。

### 2.5 Company Branding
用途：管理公司前台顯示所需的品牌資訊，例如公司正式名稱、顯示名稱與 Logo。

### 2.6 Employee / Member Profile
用途：管理員工 / 成員在公司內使用系統所需的基本欄位、登入識別與功能顯示條件。

---

## 3. 模組邊界

### `tenants` 負責
- 公司資料
- 公司成員
- onboarding
- entitlements
- 公司品牌資訊
- 員工 / 成員資料欄位定義
- 員工層級功能顯示 flag

### `tenants` 不負責
- 登入驗證本身 → `auth`
- 出勤規則 → `attendance`
- 請假流程 → `leave`
- 前端 navbar 呈現細節 → `frontend`

一句話：

> 只要是「公司這個租戶單位的設定」，優先看是不是應該放在 `tenants`。

---

## 4. 常見相關檔案

- `api.py`
- `api_members.py`
- `api_onboarding.py`
- `api_entitlements.py`
- `service.py`
- `repo.py`
- `models.py`

---

## 5. 新功能應該放哪裡？

### 應放在 `tenants`
- company CRUD
- members 管理
- entitlement 管理
- onboarding
- 公司品牌欄位（`name`、`display_name`、`logo_url`）
- 公司詳情 / 編輯可維護的品牌資訊欄位
- 員工 / 成員欄位定義（如 `display_name`、`email`、`uses_schedule`）
- 員工層級功能顯示條件

### 不應放在 `tenants`
- login token 發放
- attendance policy
- leave approval lifecycle
- navbar 元件外觀樣式本身

---

## 6. 最容易寫錯的地方

1. 把 `tenants` 跟 `auth` 混在一起
2. 把公司管理頁面的所有東西都塞進 `tenants`，導致它變成超大 admin 雜物箱
3. entitlements 改了卻沒同步確認 feature gate 使用者
4. 把公司前台顯示規則硬寫在前端，卻沒有在 `tenants` 定義正式欄位與語意
5. 把員工首頁是否顯示某功能，寫死在前端 role 判斷，而沒有正式回到員工 / 成員欄位規格

---

## 7. 什麼情況一定要更新這份文件？

- 公司資料模型改了
- members 管理改了
- 員工 / 成員欄位改了
- onboarding 流程改了
- entitlement / feature 流程改了
- 公司品牌欄位改了
- 公司詳情 / 編輯欄位改了
- 公司識別欄位改了
- 公司工商資料查詢規則改了

---

## 8. 公司品牌資訊（Company Branding）規劃

### 8.1 欄位責任歸屬
公司品牌與顯示資訊屬於 `tenants` 模組管理範圍，因為它本質上是公司（tenant）層級設定，而不是前端暫存資料。

### 8.2 公司資料欄位規格
建議 `Tenant` / Company 正式支援以下欄位：

- `name`：公司正式名稱，必填
- `display_name`：前台畫面顯示名稱，選填
- `logo_url`：公司 Logo 圖片路徑，選填

欄位語意：
- `name` 是正式名稱與後台管理主要識別欄位
- `display_name` 用於前台品牌顯示，可比正式名稱更短、更貼近客戶品牌
- `logo_url` 是 Logo 圖片存放位置或可讀取路徑，不直接代表圖片二進位內容本身

### 8.3 前台顯示優先順序
前端顯示公司品牌時，應使用以下優先順序：

1. `logo_url`
2. `display_name`
3. `name`

也就是：
- 有 Logo 就優先顯示 Logo
- 沒有 Logo 才顯示 `display_name`
- 若 `display_name` 未設定，則退回 `name`

### 8.4 管理畫面最低要求
`公司詳情 / 編輯` 畫面應支援維護：

- 公司名稱（`name`）
- 顯示名稱（`display_name`）
- 上傳 Logo / Logo 路徑（`logo_url`）
- 時區（`timezone`）
- 啟用狀態（`is_active`）

### 8.5 Logo 上傳規劃
`logo_url` 是正式欄位；Logo 上傳是其對應的管理能力。

建議規格：
- 支援格式：`PNG`、`JPG/JPEG`
- 建議大小：2MB 以內
- 建議型式：橫式 Logo、透明背景 PNG 優先
- 後端保存圖片後，回填 `logo_url`

### 8.6 文件治理要求
若未來新增或修改以下任一項，必須同步回寫本文件：

- `Tenant` model 欄位改動
- Company create/update schema 改動
- 公司詳情 / 編輯畫面欄位改動
- 公司品牌顯示優先順序改動

---

## 9. 公司識別與工商資料規劃

### 9.1 公司識別欄位
公司正式識別欄位建議包含：

- `company_id`：公司登入識別碼，必填、唯一
- `tax_id`：公司統一編號，選填；若有值則必須唯一

欄位原則：
- `company_id` 是所有公司都必須具備的正式識別欄位
- `tax_id` 不可強制要求，因為部分客戶可能沒有申請統一編號
- 若公司有 `tax_id`，則可作為補充識別欄位使用

### 9.2 登入識別規則
公司登入時，輸入值可接受：

1. `company_id`
2. `tax_id`

規則：
- `company_id` 為必備登入識別
- `tax_id` 為可選登入識別
- 若公司未提供 `tax_id`，不影響建立公司與登入流程

### 9.3 公司主資料欄位
公司主資料建議至少支援以下欄位：

- `company_id`
- `tax_id`
- `name`
- `display_name`
- `owner_name`
- `address`
- `logo_url`

最低要求：
- `company_id`：必填
- `name`：必填
- `tax_id`：選填
- `display_name`：選填
- `owner_name`：選填
- `address`：選填
- `logo_url`：選填

### 9.4 公司資料查詢與帶入規則
當使用者輸入合法 `tax_id` 時，系統可支援查詢公司資料並帶入，以降低人工輸入成本。

查詢成功時，至少可帶入以下欄位：

- `tax_id`
- `name`
- `owner_name`
- `address`

### 9.5 資料來源策略
公司資料查詢功能的正式規則如下：

- 可用 `tax_id` 查詢公司資料並帶入
- 不強制綁定特定第三方資料網站
- 正式整合前，先走人工查核 / 半自動模式

說明：
- 在正式資料來源、授權、穩定性與維運方式確認前，不將特定外部網站視為正式系統依賴
- 現階段可由人工查核外部資料後回填，或以半自動流程輔助帶入欄位

### 9.6 模組責任
此規劃中：

- `tenants` 負責公司主資料、`company_id` / `tax_id` 欄位定義，以及查詢後資料的正式落點
- `auth` 負責使用 `company_id` 或 `tax_id` 進行登入識別與後續驗證流程

---

## 10. 員工 / 成員資料欄位規劃

### 10.1 目前 code baseline 已存在的欄位
依目前 code inventory：

#### Global User 層
- `id`
- `display_name`
- `email`
- `password_hash`
- `is_active`
- `is_otp`
- `must_change_password`
- `last_login_at`
- `created_at`
- `updated_at`

#### Membership（user_company_memberships）層
- `id`（membership_id）
- `user_id`
- `company_id`
- `role_id`
- `login_username`
- `login_email`
- `is_active`
- `created_at`
- `updated_at`

#### 目前管理端 create / edit 實際可維護欄位
- `display_name`
- `email`
- `login_username`
- `password`（建立時 / 重設時）
- `role_id`
- `membership_is_active`

### 10.2 正式責任切分
員工資料不應只當成單一 table 來理解，而應拆成兩層：

#### A. Global User
回答「這個人是誰」
適合放：
- `display_name`
- `email`
- 密碼相關欄位
- 全域啟用狀態
- 登入安全相關欄位

#### B. Membership
回答「這個人在這家公司是什麼身份、可以看到哪些公司內功能」
適合放：
- `company_id`
- `role_id`
- `login_username`
- membership 啟用狀態
- 公司內功能顯示 flag

### 10.3 建議納入正式規格的員工 / 成員欄位
建議分成 P0 與 P1：

#### P0：現在就應正式納入文件的欄位
##### User 層
- `display_name`：必填，前台顯示名稱
- `email`：選填，通知與聯絡用途
- `is_active`：必填，全域帳號啟用狀態
- `must_change_password`：選填，首次登入 / 重設密碼後是否強制改密碼

##### Membership 層
- `company_id`：必填，所屬公司
- `role_id`：必填，公司內角色
- `login_username`：必填，公司內登入帳號
- `membership_is_active`：必填，是否可在該公司內使用系統
- `uses_schedule`：選填布林；是否顯示「我的班表」

#### P1：建議後續納入，但不一定現在立刻做 UI
##### User 層
- `mobile_phone`：選填，通知 / 驗證 / 聯絡用途
- `employee_no`：選填，內部員編
- `avatar_url`：選填，個人頭像

##### Membership 層
- `job_title`：選填，公司內職稱
- `department_name`：選填，部門名稱
- `hire_date`：選填，到職日
- `work_location`：選填，主要工作地點
- `attendance_group_id`：選填，出勤規則群組
- `manager_user_id`：選填，直屬主管
- `can_apply_overtime`：選填布林；是否顯示加班申請
- `can_request_makeup_attendance`：選填布林；是否顯示補打卡申請

### 10.4 `uses_schedule` 正式定義
`uses_schedule` 建議定義在 Membership / 員工公司內資料層，而不是 Tenant 全公司層或純前端判斷。

欄位語意：
- `true`：此員工需要使用班表功能，首頁可顯示「我的班表」
- `false`：此員工不需要班表功能，首頁不顯示「我的班表」
- 預設值建議為 `false`

原因：
- 是否需要看班表，是員工個別差異，不是整家公司所有人都相同
- 只用公司層級開關不夠精準
- 只用 role 判斷也不正確，因為不是所有 `employee` 都需要輪班

### 10.5 首頁功能入口與員工欄位對應
員工首頁「個人服務」顯示條件建議如下：

- `個人資料`：所有登入員工可見
- `出勤紀錄`：所有登入員工可見
- `請假申請`：依請假功能與權限可見
- `補打卡申請`：建議由 `can_request_makeup_attendance` 或對應規則控制
- `加班申請`：建議由 `can_apply_overtime` 或對應規則控制
- `我的班表`：由 `uses_schedule = true` 控制

### 10.6 管理畫面最低要求
後台成員建立 / 編輯最低應可逐步支援：

#### 目前 baseline 已有
- `display_name`
- `email`
- `login_username`
- `role_id`
- `password` / `reset password`
- `membership_is_active`
- `uses_schedule`（已完成 create / edit 支援）

#### 建議下一步補齊
- `can_apply_overtime`
- `can_request_makeup_attendance`
- `employee_no`
- `department_name`
- `job_title`


### 10.7 目前已完成的 baseline（2026-04-10）
目前 baseline 已完成：

- `Membership` 正式新增 `uses_schedule`
- members create API 已支援寫入 `uses_schedule`
- members edit API 已支援更新 `uses_schedule`
- members list response 已支援回傳 `uses_schedule`
- 管理端新增成員 / 編輯成員 UI 已支援維護 `uses_schedule`

此狀態代表 `uses_schedule` 已不是純文件規劃，而是已落地的 membership-level 欄位。

### 10.7 設計原則
- 不要把所有員工資料都塞進 `User` 全域欄位
- 與公司內制度有關的欄位，優先放 Membership 層
- 與跨公司身份有關的欄位，優先放 User 層
- 首頁功能入口顯示規則，應有正式欄位來源，不應只靠前端臨時判斷

---

## 11. 已依目前 baseline 回寫的正式結論（2026-04-09）

- `tenants`（租戶 / 公司管理）是 company 治理的 source of truth（正式權威來源）
- `feature entitlements`（功能授權）應作為 `feature gate`（功能閘門）判定來源
- `membership`（成員關係）應和一般業務資料分開理解
- `company_id`（公司識別）不應由前端 request body 當成權威來源
- 公司品牌資訊（`name`、`display_name`、`logo_url`）屬於 company 治理範圍，正式來源應為 `tenants`
- `company_id` 為必填且可登入的正式公司識別欄位
- `tax_id` 為選填且若有值則必須唯一，也可作為登入識別
- 公司資料查詢可使用 `tax_id` 帶入 `name`、`owner_name`、`address`，但現階段不綁定特定第三方網站，正式整合前先走人工查核 / 半自動模式
- 員工 / 成員資料應明確區分 `User`（全域身份）與 `Membership`（公司內身份）兩層
- `uses_schedule` 應定義在員工公司內資料 / Membership 層，用來控制是否顯示「我的班表」
- 員工首頁功能入口顯示，應以正式欄位或 feature gate 為依據，不應只靠前端硬編碼
