# SDD 學習文件

> 用途：這份文件是寫給未來的你看的。  
> 當你想把某個模組需求交給 AI，並產出一份 **可開發、可回寫、可長期維護** 的 SDD / Spec 時，就先回來看這份。

---

## 1. 這份文件要解決什麼問題

你目前的核心問題不是「沒有文件」，而是：

- `SA/legacy-import/docs/01_ARCHITECTURE/SA_MODULE_SPEC_v2.1.md` 太偏舊版基線，不夠支撐模組級開發
- 你腦中知道每個模組要做什麼，但沒有固定方式餵給 AI
- AI 即使能寫文件，如果輸入格式不固定，產出就會忽大忽小、忽深忽淺
- 沒有模組專屬文件時，AI 很容易把功能放錯地方
- 改完程式若沒有回寫規則，文件很快又失效

所以這份文件的目標是：

> 建立一套你之後可以反覆使用的「模組需求 → SDD / Spec」工作方法。

---

## 2. 先講結論：最有效的做法是什麼

最有效的做法不是再去強化單一總文件，
而是把整個做法改成下面這套：

### 2.1 文件角色重新分工

- `SA/legacy-import/docs/01_ARCHITECTURE/SA_MODULE_SPEC_v2.1.md`
  - 當歷史架構基線 / 舊版總規格追溯材料
- `SA/modules/*.md`
  - 當每個模組真正的開發 SDD / Spec
- `SA/governance/MODULE_SPEC_TEMPLATE.md`
  - 當所有模組共用的標準模板
- `SA/README.md`
  - 當整體入口與閱讀順序說明

### 2.2 真正的核心原則

> 不再要求 AI 從一份大總文件自行猜測整個模組。  
> 改成由你提供模組需求，AI 幫你整理成模組專屬 SDD，之後所有開發都先讀那份模組文件。

---

## 3. 你未來應該怎麼做

你之後若想把某個模組整理成 AI 可讀的 SDD，請固定用下面流程。

### 步驟 1：先選定一個模組

一次只整理一個模組，不要一開始想把全專案一次寫完。

建議順序：

1. `attendance`
2. `schedule`
3. `tenants`
4. `auth`
5. `leave`
6. `notifications`
7. 其他 supporting modules

原因：
- 核心模組先穩，之後其他模組比較不會寫歪
- 跨模組邊界會比較早清楚
- AI 後續開發會穩很多

### 步驟 2：你提供模組需求原料

你不用一開始就自己寫完整 SDD。  
你只要把模組需求用固定格式提供出來就可以。

### 步驟 3：讓 AI 幫你轉成正式 SDD

AI 要做的不是自由發揮，而是：

- 整理責任邊界
- 區分模組負責 / 不負責
- 拆功能群
- 補 Formalized Semantic Block
- 定義驗證方式
- 指出哪些情況要回寫文件

### 步驟 4：之後所有開發先讀 SDD

未來你或 AI 要改某功能時：

1. 先讀 `SA/README.md`
2. 再讀該模組文件
3. 必要時讀子域文件
4. 然後才改程式
5. 改完一定回寫 `SA/`

---

## 4. 你要提供給 AI 的最小輸入格式

下面這個格式，是未來最值得你固定使用的「模組需求輸入表」。

你每次只要填這份，我就能幫你把內容整理成正式 SDD。

```md
模組名稱：
一句話用途：

這個模組要負責：
- 
- 
- 

這個模組不負責：
- 
- 
- 

主要功能：
- 功能1：
  - 用途：
  - API / 畫面 / 背後流程：
  - 權限需求：
  - 是否跨模組：
- 功能2：
  - 用途：
  - API / 畫面 / 背後流程：
  - 權限需求：
  - 是否跨模組：

重要規則 / 契約：
- 
- 
- 

資料範圍 / 租戶隔離規則：
- 
- 

會依賴哪些模組：
- 
- 

哪些事情不能做：
- 
- 

目前已知問題 / 技術債：
- 
- 

希望 AI 開發時注意：
- 
- 
```

---

## 5. 如果你懶得填很完整，最少給我什麼

如果你當下很忙，不想寫很多，也可以只給我這種精簡版：

```md
模組名稱：
一句話用途：

負責：
- 

不負責：
- 

主要功能：
- 

重要規則：
- 

依賴模組：
- 

AI 開發注意：
- 
```

這樣雖然沒有完整版細，但已經足夠讓 AI 幫你先產出第一版 SDD。

---

## 6. AI 會幫你整理成什麼

當你提供模組需求後，理想產物應該包含以下內容。

### 6.1 模組總覽文件

例如：
- `SA/modules/schedule.md`
- `SA/modules/leave.md`
- `SA/modules/notifications.md`

這份會回答：
- 這個模組是做什麼的
- 它負責哪些事情
- 它不負責哪些事情
- 新功能該放哪裡
- 常見錯誤會長在哪裡
- 哪些情況要更新這份文件

### 6.2 子域文件

如果模組很大，就不要只用一份文件硬撐。

例如像 `attendance` 一樣拆成：
- `attendance.md`
- `attendance-capture.md`
- `attendance-reporting.md`
- `attendance-policy.md`

以後其他大模組也可以照這種方式拆。

例如 `leave` 若很大，可以拆成：
- `leave.md`
- `leave-request.md`
- `leave-approval.md`
- `leave-balance.md`

### 6.3 Formalized Semantic Block

每份正式 SDD / Spec 最好都有一段半結構化語意區塊，讓 AI 更容易正確理解。

例如：

```yaml
scope:
  module: leave
  responsibility:
    - leave_request
    - leave_approval
    - leave_balance_adjustment
  non_responsibility:
    - attendance_punch_write
    - auth_token_issue

contracts:
  tenant_isolation:
    source: actor.active_company_id
    body_override_allowed: false
  approval_authority:
    owner: leave.service
    api_direct_override: false
```

這種區塊的好處是：
- 比純文字更容易被 AI 判讀
- 比零散 bullet 更容易驗證
- 未來若導入 `spec-kit` 也比較容易接軌

---

## 7. 什麼樣的 SDD 才算真的有用

不是寫很長就有用。  
真正有用的 SDD，至少要能回答下面這些問題：

1. 這個模組到底負責什麼？
2. 這個模組不負責什麼？
3. 新功能該放哪裡？
4. 哪些欄位 / 流程 / semantic 不能亂動？
5. 這個模組依賴誰？
6. 哪些地方最容易寫錯？
7. 改完後要更新哪份文件？

如果一份文件很長，卻回答不了這幾題，那它還不算好的開發 SDD。

---

## 8. 你未來和 AI 協作的正確方式

未來若你要叫 AI 改功能，不要只說：

- 幫我做請假
- 幫我做排班
- 幫我改 attendance

這樣太模糊，AI 很容易亂補。

你應該改成這種說法：

```md
先讀 `SA/modules/leave.md`
這次要做：
- 新增代理審批
- 不可破壞 tenant isolation
- 不要把 approval rule 寫在 API
改完後要回寫 SA 文件
```

這樣 AI 的方向才會穩。

---

## 9. 每次整理模組時，我建議你的操作順序

以下是最推薦的實戰流程。

### 9.1 第一次整理某個模組

1. 你先提供模組需求
2. AI 先產出 `SA/modules/<module>.md`
3. 若內容太大，再拆子域文件
4. 補上 Formalized Semantic Block
5. 補上驗證與回寫規則

### 9.2 第一次用這份 SDD 開發功能

1. 先讀主模組文件
2. 若功能屬於子域，再讀子域文件
3. 根據文件修改程式
4. 確認是否碰到 tenant / scope / feature gate / boundary
5. 改完後回寫對應文件

### 9.3 之後持續維護

每次功能完成，至少補這些：

- 功能目的
- 影響模組
- API / service / repo / model 改動點
- 是否影響 tenant / scope / feature gate
- 是否影響跨模組邊界
- 已知限制與後續待辦

這部分也要遵守 `SA/governance/DOCUMENTATION_GOVERNANCE.md`。

---

## 10. 你目前最需要的，不是 spec-kit，而是固定輸入格式

現階段真正最重要的不是先裝工具，而是先建立：

> 你如何把模組需求穩定地交給 AI，讓 AI 產出一致格式的 SDD。

所以優先順序應該是：

### 第一階段
- 建立模組需求輸入格式
- 建立模組 spec 模板
- 先完成幾個核心模組的正式 SDD

### 第二階段
- 讓日常開發改成先讀 SDD 再改程式
- 改完強制回寫 SA 文件

### 第三階段
- 若你之後覺得 spec workflow 已經成熟
- 再考慮是否導入 `spec-kit`

也就是：
- **先把文件方法跑順**
- **再考慮工具化**

---

## 11. 最推薦的整體方案

你未來最值得固定採用的做法是：

### Module Intake → SDD Generation → Implementation → SA Writeback

拆開來就是：

#### A. Module Intake
你提供模組需求原料。

#### B. SDD Generation
AI 幫你生成模組 SDD / 子域 Spec。

#### C. Implementation
未來開發先讀對應模組文件，再改程式。

#### D. SA Writeback
改完程式後，把變更回寫到 `SA/`。

這樣一來，文件就不再只是「紀錄」，而是變成真正能驅動開發的東西。

---

## 12. 你之後可以直接複製貼上的指令範例

### 範例 1：叫 AI 幫你產出模組 SDD

```md
請依照 `SA/governance/MODULE_SPEC_TEMPLATE.md`
把以下模組需求整理成 `SA/modules/schedule.md` 正式 SDD：

模組名稱：schedule
一句話用途：管理排班模板、班表指派、查詢可用班表

負責：
- 排班模板管理
- 指派班表給使用者
- 查詢某人某日適用班表

不負責：
- attendance 打卡寫入
- JWT 驗證
- leave 審批

主要功能：
- template CRUD
- assignment CRUD
- 查詢指定日期有效班表

重要規則：
- 不可跨公司查詢
- schedule 是班表 source of truth
- attendance 只能讀 schedule，不可反寫

依賴模組：
- auth
- tenants
- attendance

AI 開發注意：
- 不要把 schedule rule 寫到 attendance router
- 不要讓 API 直接承擔過多業務協調
```

### 範例 2：叫 AI 依據 SDD 開發功能

```md
先讀 `SA/modules/schedule.md`
這次要做「查詢使用者某日有效班表」API。
要求：
- 不可破壞 tenant isolation
- 不要把邏輯塞進 router
- 改完後回寫 `SA/modules/schedule.md`
```

### 範例 3：叫 AI 幫你判斷要不要拆子文件

```md
先讀 `SA/modules/leave.md`
請判斷 leave 模組是否應拆成子域文件。
如果需要，請提出拆分方案與每份文件責任邊界。
```

---

## 13. 什麼情況下應該拆子文件

以下情況很適合拆：

- 同一模組同時有交易寫入、查詢報表、規則引擎
- 同一模組文件已經太長，AI 很容易看不準重點
- 高風險流程需要更明確的正式規格
- 同模組內不同子域常常由不同檔案群負責

拆分後的目標不是變多文件，
而是讓每份文件都能回答清楚：

- 這份文件管什麼
- 這份文件不管什麼
- 這類功能該改哪裡

---

## 14. 未來你自己判斷文件好不好用的檢查表

每次你看某份 SDD，都可以問自己：

- 我看完後知道功能該放哪裡嗎？
- 我知道哪些不能亂動嗎？
- 我知道它依賴哪些模組嗎？
- 我知道 API / service / repo 大概該在哪一層改嗎？
- 我知道改完要回寫哪份文件嗎？

如果答案大多是「不知道」，就代表這份文件還要補強。

---

## 15. 最後結論

如果你的目標是：

> 我提供每個模組需要的功能，讓 AI 幫我整理成 SDD 文件，之後 AI 看這些文件就能比較穩定地開發。

那你最有效的做法就是：

1. 不再把 `SA_MODULE_SPEC_v2.1.md` 當唯一開發來源
2. 改成以 `SA/modules/*.md` 作為模組正式開發文件
3. 每個模組都用固定輸入格式提供需求
4. 用 `SA/governance/MODULE_SPEC_TEMPLATE.md` 生成一致格式 SDD
5. 每次改程式前先讀 SDD，改完後回寫 `SA/`

一句話總結：

> 先把「需求怎麼餵給 AI」標準化，再把「AI 產出的 SDD」標準化，最後再把「開發後回寫文件」制度化。

這樣你未來才不會再回到「文件很多，但 AI 還是看不懂」的狀態。
