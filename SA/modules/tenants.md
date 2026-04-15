# tenants 模組 SDD

**模組名稱**：`tenants`  
**定位**：公司 / 租戶層級的管理中心  
**程式位置**：`backend/app/modules/tenants`

---

## 1. 模組目的

`tenants` 負責管理「公司這個租戶單位」本身，以及所有直接屬於公司層級的設定與管理能力。

白話說：

- 公司主資料在這裡管理
- 公司成員在這裡管理
- onboarding 在這裡管理
- entitlements 在這裡管理

一句話：

> 只要是「公司這個租戶單位的正式設定」，優先判斷是否屬於 `tenants`。

---

## 2. 模組邊界

### `tenants` 負責

- 公司主資料
- 公司成員
- onboarding
- feature entitlements
- 公司顯示名稱等主資料欄位（例如 `display_name`）
- 公司層級識別欄位（例如 `company_id`、`tax_id`）

### `tenants` 不負責

- 登入驗證本身 → `auth`
- 出勤規則本身 → `attendance`
- 請假流程本身 → `leave`
- 前端 navbar 呈現細節 → `frontend`
- 多據點打卡地點規則本身 → 未來應屬 location / attendance 類別模組

---

## 3. 主要功能

### 3.1 Company CRUD
建立與管理公司主資料。

### 3.2 Members 管理
管理公司內有哪些成員，以及成員基本設定。

### 3.3 Onboarding
處理公司開通與初始設定流程。

### 3.4 Feature Entitlements
管理公司可使用哪些功能。

---

## 4. 功能拆分治理原則（正式）

本模組後續開發正式採以下原則：

> 一個功能一個模組 / 一組檔案；不是每個小功能、每支 API、每個小互動都拆一個檔。

這是 `tenants` 模組後續新增功能時的正式判斷依據。

### 4.1 什麼叫「功能」

這裡的「功能」指的是：

- 一組有共同資料語意的能力
- 一組會一起被維護、一起變更、一起討論的 use case
- 一組可被明確命名的子領域
- 一組未來需求會持續長在同一塊的能力

在 `tenants` 內，以下屬於「功能級」：

- company CRUD
- onboarding
- members 管理
- entitlements

### 4.2 什麼不算功能級

以下通常**不構成獨立拆檔理由**：

- 單一欄位驗證
- 單一按鈕行為
- 單一 API endpoint
- 單一 helper function
- 單一錯誤處理分支
- 單一 upload / lookup / patch 動作

例如：

- `tax id lookup API` 本身通常不算一個完整功能
- `company detail endpoint` 本身通常不算一個完整功能

它們通常只是既有功能底下的一個能力。

---

## 5. 後端拆分原則

後端正式採：

> `api.py` 主入口 + 功能級子模組

### 5.1 `api.py` 的角色

`api.py` 必須是 `tenants` 模組的 API 主入口 / 聚合點。

正式責任：

- 作為 `tenants` 對外 API 的統一入口
- 匯入並註冊功能級 router
- 保持模組對外入口一致
- 避免路由入口四散

也就是：

- 外部看 `tenants`，先看 `api.py`
- 即使有子檔案，仍由 `api.py` 統一掛載

### 5.2 何時才拆出 `api_xxx.py`

只有當某一塊已形成**明確功能邊界**時，才可拆出：

- `api_onboarding.py`
- `api_members.py`
- `api_entitlements.py`

### 5.3 不應該怎麼拆

正式禁止以下拆法：

- 每個 endpoint 一個檔案
- 每新增 1~2 支 API 就新增一個 `api_xxx.py`
- 因為單一 upload / lookup / delete 動作就拆新模組
- 只為了把檔案行數變少而拆檔

### 5.4 當前建議粒度

`tenants` 後端目前建議維持以下粒度：

- `api.py`：company 主資料 / router 聚合入口
- `api_onboarding.py`：onboarding
- `api_members.py`：members
- `api_entitlements.py`：entitlements
- `service.py`：主要業務協調
- `repo.py`：主要資料存取

補充原則：

- 若某能力仍屬 company 主資料的一部分，先留在 `api.py`

---

## 6. 前端拆分原則

前端正式採：

> 頁面容器 + 功能區塊元件

### 6.1 View 的責任

主 View 負責：

- 頁面狀態
- 資料流
- submit 流程
- 權限判斷
- success / error 控制

### 6.2 子元件的責任

子元件應對應「功能區塊」，例如：

- 公司列表區
- 公司詳情 / 編輯區
- 成員管理區
- onboarding 表單區
- onboarding 成功結果區

### 6.3 不應該怎麼拆

正式禁止以下拆法：

- 每個 input 一個元件
- 每個小互動一個元件
- 每個小按鈕流程一個 composable
- 因為區塊裡有 2~3 個欄位，就獨立拆成很碎的檔案

### 6.4 何時才拆子元件

符合以下情況，才建議拆：

- 畫面中已存在明確功能區塊
- 該區塊可以被獨立命名
- 該區塊有自己的 state / submit / 顯示責任
- 後續需求會持續加在該區塊

---

## 7. 拆新檔的判斷標準

符合以下任兩項以上，可視為應拆：

- 已形成可被獨立命名的子功能
- 後續需求會持續集中在這一塊
- 與同檔其他內容耦合度低
- 已有自己的 request / response / state / UI 區域
- 維護時會被單獨討論與指稱

符合以下任一項，原則上不拆：

- 只是單一欄位或單一按鈕邏輯
- 只是新增一支 API
- 拆出後只剩薄薄一層轉呼叫
- 名稱過碎，無法一眼看出功能邊界
- 拆分理由只是想縮短檔案長度

---

## 8. 新功能應該放哪裡

### 應放在 `tenants`

- company CRUD
- members 管理
- entitlement 管理
- onboarding
- 公司主資料欄位（`name`、`display_name`）
- 公司詳情 / 編輯可維護的品牌資訊欄位
- 公司主資料 detail API
- 公司統編查詢帶入規則

### 不應放在 `tenants`

- login token 發放
- attendance policy
- leave approval lifecycle
- navbar 元件外觀樣式本身
- 多據點打卡地點規則本身

---

## 9. 常見相關檔案

- `api.py`
- `api_members.py`
- `api_onboarding.py`
- `api_entitlements.py`
- `service.py`
- `repo.py`
- `models.py`
- `schemas.py`
- `schemas_companies.py`
- `schemas_members.py`
- `schemas_entitlements.py`
- `schemas_onboarding.py`

---

## 10. 目前後端現況對照分析（2026-04-13）

本段是依照目前 `backend/app/modules/tenants` 實際結構，對照本文件第 4～7 節拆分治理原則後得到的正式分析結論。

### 10.1 目前實際檔案結構

目前後端主要檔案如下：

- `api.py`
- `api_onboarding.py`
- `api_members.py`
- `api_entitlements.py`
- `service.py`
- `repo.py`
- `schemas.py`
- `schemas_companies.py`
- `schemas_members.py`
- `schemas_entitlements.py`
- `schemas_onboarding.py`

### 10.2 目前屬於「合理」的地方

以下拆分目前判定為合理，符合「主入口 + 功能級子模組」原則：

#### 1. `api.py` 作為主入口，方向正確
目前 `api.py` 仍是 `tenants` 的主要 router 入口，且由它統一掛載其他功能路由。這一點符合本文件要求，應繼續維持。

#### 2. `api_onboarding.py` 獨立，合理
`onboarding` 是完整流程，不是單一 API 動作，包含：
- 建立 company
- 建立初始 user
- 建立 membership
- 原子交易與 rollback

因此它已屬明確功能級子模組，獨立合理。

#### 3. `api_members.py` 獨立，合理
`members` 已經是一整組公司成員管理能力，包含：
- list members
- create member
- update member
- toggle active
- reset password

這是一組會持續增長、可獨立命名、可單獨維護的子功能，獨立合理。

#### 4. `api_entitlements.py` 獨立，合理
`entitlements` 是明確子領域，且權限、資料模型、操作邏輯都與 company CRUD 不同，因此獨立合理。

依照本文件原則，單一 lookup、單一 upload、單一 patch 動作本身不構成拆檔理由。

因此目前把以下能力留在 `api.py`：
- company list / create / detail / update
- tax id lookup


### 10.3 目前屬於「偏碎，但尚可接受」的地方

以下目前不是立即要改，但已出現碎裂傾向，後續新增時不應再往下拆。

#### 1. `schemas.py` + 功能級 schema 多檔
目前 schema 已拆成多檔，另外保留一個 `schemas.py` 作為 re-export façade。

正式判定：
- 這不算嚴重過碎
- 但已經接近「一個子功能一組 schema 檔」的上限
- 在目前規模下可接受

正式原則：

> schema 拆分目前先停在「功能級 schema」，不要再往「單一 API schema」細拆。

#### 2. `service.py` 內已混有多個子領域邏輯
目前 `service.py` 內同時存在：
- tenant / company 主資料邏輯
- tax id lookup provider
- member update / reset password
- entitlement service 類別

正式判定：
- 目前仍可接受
- 但已呈現「多子領域共存」狀態

因此目前結論不是立刻拆，而是：

> `service.py` 暫時可維持，但後續新增邏輯必須先判斷是否已達到真正功能級，再決定是否拆 `service_xxx.py`；不可因單一小功能就繼續細拆。

### 10.4 目前屬於「過碎風險點」的地方

以下雖未必已經錯，但若再往同方向發展，會明顯違反本文件治理原則。

#### 1. `api_members.py` 內有部分邏輯直接操作 `auth` repository / model
目前 `api_members.py` 內直接引用：
- `Membership`
- `User`
- `Role`
- `AuthRepository`

正式判定：
- 功能邊界本身仍算 `members`
- 但實作責任略有下沉到 API 層
- 若未來再把 members 底下每個操作各自再拆 service / helper / repo，會很容易變成碎片化

因此建議：
- 短期可接受
- 後續若 members 再持續增長，應優先考慮整理成「members 功能級 service」，而不是把每個 members 動作各拆一檔

#### 2. `schemas.py` façade 屬於兼容層，短期可留，長期不應再擴散
目前 `schemas.py` 是 re-export 相容層，這在過渡期可接受。

但正式要求：
- 不應再新增更多 façade / shim 檔
- 新程式若可直接引用功能級 schema 檔，應優先直接引用
- 避免模組內同時出現太多「轉出口檔」造成結構判讀成本提高

### 10.5 目前不建議調整的地方

以下目前不建議重構，避免為了整理而整理：

理由：
- 若現在拆，屬於以單一 API 動作拆檔，違反本文件原則

#### 2. 不建議把 `lookup-by-tax-id` 再拆成 `api_lookup.py`
理由：
- 單一 lookup 動作不構成功能級模組
- 目前仍屬 company 主資料輔助能力

#### 3. 不建議把 company detail / update 再拆成 `api_company_detail.py` 或 `api_company_update.py`
理由：
- 這是標準 CRUD / detail 行為
- 屬 company 主資料主體
- 若拆出只會讓模組入口更碎

### 10.6 目前正式結論

依本次盤點結果，`tenants` 後端目前整體結構判定如下：

#### 合理
- `api.py` 作為主入口
- `api_onboarding.py`
- `api_members.py`
- `api_entitlements.py`

#### 偏碎但可接受
- 功能級 schema 多檔拆分
- `schemas.py` façade 過渡層
- `service.py` 內多子領域共存

#### 目前不應再往下拆
- tax id lookup
- company detail / update
- members 底下單一操作

### 10.7 後續調整優先順序

若未來要調整 `tenants` 後端結構，正式優先順序如下：

1. **先維持 `api.py` 為單一主入口**
2. **先避免新增小型 `api_xxx.py`**
3. **若 `members` 持續變大，優先考慮整理其 service 邊界，而不是把單一 members 動作再切碎**
5. **schema 拆分停在功能級，不再往單一 API 細拆**

本文件因此正式認定：

> `tenants` 目前 API 結構整體方向是合理的；真正需要防止的是「從現在開始再往更細的小功能檔案繼續拆」。

---

## 11. 最容易寫錯的地方

1. 把 `tenants` 跟 `auth` 混在一起
2. 把公司管理頁面的所有東西都塞進 `tenants`，變成後台雜物箱
3. 把每個小功能都拆成一個檔，導致結構過碎
4. 把單一 API 誤判成一個完整子模組
6. 把 schema 繼續往單一 API 細拆

---

## 12. 調整決策清單（正式）

本段定義目前 `tenants` 模組的正式調整策略，用來約束後續實作，避免在沒有必要時繼續細拆。

### 12.1 現在應調整的方向

#### 1. 維持 `api.py` 為唯一主入口
正式要求：
- `tenants` 對外 API 入口維持由 `api.py` 統一承接
- 子功能 router 一律由 `api.py` 掛載
- 不應繞過 `api.py` 分散註冊入口

#### 2. `members` 若持續成長，優先整理成功能級 service
正式要求：
- 若 `members` 後續需求持續增加，優先考慮整理成 `members` 功能級 service 邊界
- 不應把 `create member`、`update member`、`reset password`、`toggle active` 各自拆成獨立 service 檔

正式邊界建議：
- API 層保留：權限檢查、request/response 轉換、HTTP error mapping
- `members` service 保留：member 建立、member 更新、密碼重設、啟停狀態切換、role 驗證、company 內唯一性檢查、membership 與 company 關聯檢查、與 auth repository 的協調
- repository / model 層保留：資料查詢與持久化本身

目前判定：
- `api_members.py` 目前已承擔部分資料與 `auth` 協調細節
- 短期可接受，但不應再把更多 members 細節堆進 API 層
- 若後續 members 繼續長大，應優先把這些業務協調收斂進單一 `members` 功能級 service，而不是把每個 members 動作再拆成多個小 service

正式要求：

#### 4. schema 拆分停在功能級
正式要求：
- 維持目前功能級 schema 結構即可
- 不再往單一 API 細拆 `schemas_xxx.py`

### 12.2 現在不應調整的地方


#### 2. 不應新增 `api_lookup.py`
理由：`lookup-by-tax-id` 仍屬 company 主資料輔助能力，不構成功能級模組。

#### 3. 不應新增 `api_company_detail.py` / `api_company_update.py`
理由：這些仍屬標準 company CRUD / detail 行為，應保留在 `api.py`。

#### 4. 不應因為 `service.py` 變胖就先亂拆
理由：檔案大小本身不是拆分理由；只有功能邊界成熟時，才可拆出 `service_xxx.py`。

#### 5. 不應再新增 façade / shim 類型檔案
理由：目前 `schemas.py` 作為過渡相容層可接受，但不應再擴散出更多轉出口檔。

### 12.3 若未來真的要重構，正式順序

1. 先維持 `api.py` 為單一主入口
2. 先避免新增小型 `api_xxx.py`
3. 若 `members` 持續變大，優先整理其 service 邊界
5. schema 拆分停在功能級，不再往單一 API 細拆

### 12.4 簡化判斷句

任何人想拆檔前，先問四句：

1. 這是一個功能，還是一個動作？
2. 這塊需求未來會持續集中嗎？
3. 拆出去後，名稱能不能直接代表一個子領域？
4. 不拆會真的造成邊界混亂嗎？

若以上問題無法得到明確肯定，原則上先不拆。

---

## 13. 文件治理要求

若未來發生以下任一情況，必須同步更新本文件：

- 公司資料模型改了
- members 管理改了
- onboarding 流程改了
- entitlement / feature 流程改了
- 公司品牌欄位改了
- 公司詳情 / 編輯欄位改了
- 公司識別欄位改了
- 公司工商資料查詢規則改了
- company detail API 結構改了
- 新增任何 `api_xxx.py`
- 新增任何 `service_xxx.py`
- 前端把一個 View 拆成多個功能子元件
- 對本文件第 10 節現況結論有任何調整
- 對本文件第 12 節調整決策有任何調整

新增拆分時，文件中必須補充說明：

- 新檔案對應哪一個「功能」
- 為什麼它已達到功能級拆分
- 主入口與子模組之間的責任邊界
- 是否推翻第 10 節既有現況判定
- 是否推翻第 12 節既有調整決策
