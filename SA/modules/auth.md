# auth 模組 SDD

**模組名稱**：`auth`  
**你可以把它理解成**：整個系統的「登入入口」  
**程式位置**：`backend/app/modules/auth`

---

## 1. 這個模組是做什麼的？

`auth` 專門處理「你是誰、能不能登入、登入後要發什麼 token」。

白話說：

- 使用者輸入帳號密碼
- 系統檢查這個人能不能登入
- 如果可以，就發 JWT 給前端
- 同時回傳登入後前端初始化首頁所需的最小身份資料

它是**身分入口**，不是業務模組。

---

## 2. 主要功能

### 2.1 Login API
用途：讓使用者登入系統。

### 2.2 Membership 查詢
用途：確認這個 user 在哪個 company 裡有身份。

### 2.3 Role 查詢
用途：確認登入後應該帶什麼角色資訊。

### 2.4 Token claims 輸出
用途：決定 JWT 內要放哪些必要資訊。

### 2.5 Login Session Bootstrap Data
用途：回傳登入後前端初始化畫面所需的最小資料，不必讓首頁再自行猜測使用者身份與功能顯示條件。

---

## 3. 你應該怎麼理解它的邊界

### `auth` 負責
- 登入
- 驗證帳密
- 建立 JWT
- 提供身份相關基礎資訊
- 使用登入輸入值識別對應公司與會員身份
- 提供登入後前端初始化所需的 session bootstrap data

### `auth` 不負責
- 出勤規則
- 排班規則本身
- 請假流程
- 公司資料管理
- 報表聚合
- 公司主資料欄位定義
- 員工欄位語意的正式定義

一句話：

> `auth` 只處理「身份」，不處理「業務」。

---

## 4. 常見相關檔案

- `api.py`：登入 API 入口
- `service.py`：登入流程與驗證邏輯
- `repo.py`：查 user / membership / role
- `models.py`：資料模型
- `schemas.py`：request / response 格式

---

## 5. 新功能應該放哪裡？

### 應放在 `auth`
- 登入方式調整
- JWT claim 調整
- company + login_username 驗證
- 身份建立邏輯
- 使用 `company_id` / `tax_id` 作為登入識別的流程
- 定義 login response / me profile response 的身份 bootstrap 欄位

### 不應放在 `auth`
- company entitlement 管理 → 應放 `tenants`
- 公司識別欄位定義（`company_id`、`tax_id`）→ 應放 `tenants`
- 公司工商資料查詢與帶入規則 → 應放 `tenants`
- 打卡 / 出勤 → 應放 `attendance`
- 請假 → 應放 `leave`
- `uses_schedule` 這類員工公司內欄位的正式語意定義 → 應放 `tenants`

---

## 6. 最容易寫錯的地方

1. 把 `auth` 當成公司管理模組用
2. 把 role / scope 規則寫死在登入 API 裡
3. 改了 JWT claims 卻沒有同步更新依賴它的其他模組
4. 把 `company_id` / `tax_id` 的欄位語意與唯一性規則寫進 `auth`
5. 讓前端自行猜首頁該顯示哪些入口，而不是由登入回應或 profile API 提供正式欄位

---

## 7. 什麼情況一定要更新這份文件？

- 登入流程改了
- JWT claim 結構改了
- membership 驗證改了
- role 來源改了
- 登入 API 契約改了
- 公司登入識別規則改了
- login response / me profile 的 bootstrap 欄位改了

---

## 8. 公司登入識別規則對齊

### 8.1 正式責任切分
公司識別欄位的正式定義屬於 `tenants`，登入驗證流程屬於 `auth`。

也就是：
- `tenants` 定義 `company_id`、`tax_id` 的欄位語意、唯一性與正式資料來源
- `auth` 使用這些欄位作為登入識別輸入，進行後續驗證流程

### 8.2 可接受的公司登入識別
公司登入時，輸入值可接受：

1. `company_id`
2. `tax_id`

規則：
- `company_id` 為必備登入識別
- `tax_id` 為可選登入識別
- 若公司未提供 `tax_id`，不影響登入流程，改以 `company_id` 作為公司識別

### 8.3 auth 模組內的正式限制
`auth` 不應在模組內重新定義以下內容：

- `company_id` 是否必填
- `tax_id` 是否必填
- `tax_id` 的唯一性規則
- 公司工商資料查詢來源
- 公司資料查詢成功後應落到哪些公司主資料欄位

這些都應以 `SA/modules/tenants.md` 為正式來源。

### 8.4 與 tenants 的對齊規則
若未來發生以下任一變動，`auth` 與 `tenants` 必須同步回寫：

- 公司登入識別欄位改動
- `company_id` / `tax_id` 的登入優先規則改動
- 登入 API 輸入契約改動
- 公司識別方式從單一欄位擴充成多種欄位

---

## 9. Login Session Bootstrap Data

### 9.1 為什麼需要這一層
員工登入成功後，前端首頁需要立即知道：

- 我是誰
- 我現在在哪一家公司
- 我目前登入的公司內身份是什麼
- 首頁有哪些入口應顯示

因此 login response 不應只是一個 token，還應同時回傳**前端初始化首頁所需的最小身份資料**。

### 9.2 bootstrap data 的定義原則
這些資料是：

- 由後端正式提供
- 可直接成為前端 auth store / session store 的初始化來源
- 只放首頁與登入後共用畫面真的需要的最小欄位
- 不取代完整 profile API，但可降低登入後第一屏還要額外猜測的成本

### 9.3 建議登入回應至少提供的欄位
建議 `login response` 至少提供：

- `access_token`
- `token_type`
- `user`
  - `id`
  - `display_name`
  - `email`
- `company`
  - `id`
  - `name`
  - `display_name`（若已有）
- `role`
  - `id`
  - `name`
- `membership`
  - `membership_id`
  - `company_id`
  - `role_id`
  - `login_username`
  - `is_active`
  - `uses_schedule`

若目前不想立即新增 `membership` 物件，也至少應保證首頁需要的 membership-level 欄位可以從登入回應或 `me/profile` API 取得。

### 9.4 前端首頁初始化責任
登入回應應被視為前端首頁初始化資料來源之一。

它應可支援以下畫面：

- Navbar 顯示公司名稱
- Navbar 顯示登入身分
- Navbar 判斷是否顯示後台管理入口
- 員工首頁個人服務入口顯示條件

### 9.5 `uses_schedule` 的來源規則
`uses_schedule` 不應由前端自行猜測。

正式規則：
- `uses_schedule` 屬於 Membership / 員工公司內資料
- 欄位定義與語意以 `tenants` 為正式來源
- 前端顯示「我的班表」前，必須從後端取得該欄位
- 欄位來源可為：
  1. login response
  2. `me` / profile API

禁止作法：
- 看到 `employee` role 就直接顯示班表
- 看到公司有排班功能就對所有員工顯示班表
- 用前端硬編碼條件推論誰該看到班表

### 9.6 login response 與 profile API 的分工
建議原則：

- `login response`：提供登入成功後首頁立即需要的最小 bootstrap data
- `me / profile API`：提供較完整、可延後載入的個人 / membership 詳細資料

也就是：
- 若首頁一登入就要判斷 `我的班表` 是否顯示，則 `uses_schedule` 最好直接進 login response
- 若暫時不放進 login response，則前端應在首頁初始化前先取得 profile API，而不是自行推論

---


### 9.7 目前已完成的 baseline（2026-04-10）
目前 baseline 已完成：

- `LoginResponse` 正式新增 `membership` 物件
- `membership` 目前包含：
  - `membership_id`
  - `company_id`
  - `role_id`
  - `login_username`
  - `is_active`
  - `uses_schedule`
- 前端 `auth store` 已保存 `membership` bootstrap 資料
- 員工首頁 `PersonalServiceCard` 已依 `uses_schedule` 控制是否顯示 `我的班表`

此狀態代表：
- 前端不需要再用 role 或公司功能去猜測班表入口
- `uses_schedule` 已成為正式後端來源欄位

---

## 10. 與 tenants 的員工欄位責任切分

### 10.1 User 與 Membership 要分兩層理解
依目前正式方向，員工資料要拆成兩層：

#### A. User：全域身份
回答「這個人是誰」

典型欄位：
- `id`
- `display_name`
- `email`
- `password_hash`
- `is_active`
- `must_change_password`

#### B. Membership：公司內身份
回答「這個人在這家公司是誰、可以看到哪些公司內功能」

典型欄位：
- `membership_id`
- `company_id`
- `role_id`
- `login_username`
- `membership_is_active`
- `uses_schedule`

### 10.2 auth 在這個切分中的責任
`auth` 的責任不是重新定義這些欄位的業務語意，而是：

- 讀取正確的 user / membership 資料
- 在登入成功後把首頁初始化所需欄位回給前端
- 確保前端拿到的是正式來源，而不是猜出來的值

### 10.3 tenants 在這個切分中的責任
`tenants` 是 membership-level 欄位的正式治理來源，包含：

- `uses_schedule` 是否存在
- `uses_schedule` 代表什麼
- 成員管理 UI 是否可維護該欄位
- 建立 / 編輯 member API 是否支援該欄位

### 10.4 對齊原則
若未來以下任一項改動，`auth` 與 `tenants` 應同步更新：

- membership 欄位新增或刪除
- 首頁功能入口顯示規則改動
- login response / profile response 欄位改動
- 員工首頁 bootstrap 欄位來源改動

---

## 11. 目前 code baseline 對照觀察（2026-04-09）

依目前程式碼可觀察到：

- `LoginResponse` 目前已有 `user`、`company`、`role`，但尚未提供 `membership` 物件
- 後端 `auth.service` 目前登入成功後已有查到 membership，可直接作為擴充回傳欄位的落點
- 前端 `auth` store 目前只保存 `user`、`company`、`role`、`token`
- 前端 `PersonalServiceCard` 目前尚未依 `uses_schedule` 條件顯示「我的班表」

因此若要支援正式規格，最小調整方向是：

1. 後端 membership schema 增加 `uses_schedule`
2. login response 或 profile API 帶出 `uses_schedule`
3. 前端 auth store 保存 `membership` 或等價 bootstrap 欄位
4. 員工首頁依 `uses_schedule` 顯示 `我的班表`

---

## 12. 已依目前 baseline 回寫的正式結論（2026-04-09）

- `auth`（身分驗證）回答的是「你是誰」
- `scope validation`（操作範圍驗證）回答的是「你能不能操作這家公司」
- `auth` 不應單獨決定所有 `company scope`（公司操作範圍）
- `platform-first identity`（平台優先身份）與 `membership`（成員關係）應分開理解
- `auth` 可接受 `company_id` 或 `tax_id` 作為公司登入識別，但欄位定義與資料來源仍以 `tenants` 為正式權威來源
- login response 不只是 token 回應，也應是前端登入後首頁初始化資料來源之一
- `uses_schedule` 屬於 Membership / 員工公司內資料欄位，不可由前端自行猜測
- `uses_schedule` 應由 login response 或 `me/profile` API 提供給前端
- `auth` 應對齊 `tenants` 所定義的 User / Membership 責任切分，不可在模組內另行發明欄位語意
- session-based JWT consumer 若要求 `session_id` claim，則 login / refresh / 測試所建立的 access token 都必須維持此契約；真 JWT E2E 不得再以缺少 `session_id` 的測試 token 代表正式登入狀態
- 若下游功能同時依賴 membership 與 feature gate（例如 `schedule`），真 JWT 測試必須一併 seed `role`、`membership`、`entitlement`，不可只驗 token decode 成功
