# frontend 模組 SDD

**模組名稱**：`frontend`  
**你可以把它理解成**：系統的「使用者操作介面」  
**程式位置**：`frontend/`

---

## 1. 這個模組是做什麼的？

前端是 Vue 3 SPA，負責讓使用者操作系統。

白話說：

- 顯示畫面
- 保存登入狀態
- 導頁
- 呼叫 API
- 做使用者體驗層的權限限制

但它不是最終安全邊界。

---

## 2. 主要功能

### 2.1 Auth Store 與 Session Restore
用途：保存 JWT、登入狀態、重新整理頁面後恢復 session。

### 2.2 Route Guard
用途：控制哪些角色可以進哪些頁。

### 2.3 API Client 包裝
用途：統一送 token、處理錯誤、呼叫後端。

### 2.4 頁面模組
目前主要包含：
- attendance
- reporting
- schedule
- admin
- leave

---

## 3. 主要區塊

- `src/api/`：API 封裝
- `src/stores/`：Pinia 狀態管理
- `src/router/`：路由與 route guard
- `src/views/`：頁面
- `src/components/`：共用元件

---

## 4. 模組邊界

### `frontend` 負責
- 畫面呈現
- 頁面流程
- 呼叫 API
- UX 層角色限制

### `frontend` 不負責
- 最終權限判定
- tenant isolation 權威驗證
- 核心業務規則最終決策

一句話：

> 前端可以幫忙擋畫面，但真正的安全與權限仍要靠後端。

---

## 5. 新功能應該放哪裡？

### 應放在 `frontend`
- 新頁面
- route guard
- API client 行為
- store 狀態流程
- 員工首頁入口排列
- 個人服務顯示條件 consume

### 不應放在 `frontend`
- 最終 RBAC 規則
- attendance canonical semantic
- feature entitlement 真正授權邏輯
- `uses_schedule` 的正式定義

---

## 6. 最容易寫錯的地方

1. 以前端 localStorage 的角色當成最終權限依據
2. 前端偷偷複製一份後端規則，導致兩邊越來越不一致
3. API 契約改了卻沒同步改 store 與 view
4. 只用角色判斷是否顯示「我的班表」，而不是吃正式欄位

---

## 7. 什麼情況一定要更新這份文件？

- route guard 改了
- 登入保存格式改了
- API client 改了
- 前端角色判斷改了
- 大型頁面結構改了
- 員工首頁個人服務 IA 改了
- 登入回傳欄位改了
- 前端頁面模板基準改了
- 共用卡片語言改了

---

## 8. 員工首頁與個人服務規劃

### 8.1 Navbar 定位
員工端頂部 `navbar` 應以「公司 / 身分 / 登出 / 管理入口」為主，不應再承載員工日常主要功能導航。

### 8.2 個人服務區塊定位
員工首頁下方 `個人服務` 是主要服務入口區，應放使用者真正常用的項目。

目前規劃：
- `個人資料`
- `加班申請`
- `出勤紀錄`
- `補打卡申請`
- `請假申請`
- `我的班表`（條件顯示）

### 8.3 不應放在員工首頁的資訊
以下資訊不應當成員工首頁主要卡片：
- 系統狀態
- API 狀態
- 技術性健康檢查資訊
- 排班管理入口

### 8.4 `我的班表` 顯示規則
`我的班表` 不應對所有員工固定顯示，也不應只用角色判斷。

建議正式規則：
- 由登入回應 / 員工資料中的 `uses_schedule` 控制
- `uses_schedule = true` 才顯示 `我的班表`
- `uses_schedule = false` 則不顯示

### 8.5 加班 / 補打卡顯示規則
若未來後端補上正式欄位，前端建議依下列欄位控制：
- `can_apply_overtime`
- `can_request_makeup_attendance`

在正式欄位未落地前，可先以 UI 佔位或 disabled card 呈現，但不能把前端暫時狀態當正式規格。

### 8.6 子頁返回原則
頂部工具列若不再承載主導航，則各功能頁面應自行提供「返回首頁」或明確返回入口，避免使用者進入子頁後缺乏返回路徑。

### 8.7 前端頁面基準模板（2026-04-10 起）
未來前端新頁面與既有頁面收斂，正式以 `frontend/src/views/LeaveRequestView.vue` 作為畫面骨架基準。

基準原則：
- 先有共同頁面骨架，再依功能增加卡片，不反過來先做特殊版型
- `Navbar` 放在頁面內容 container 內，與下方卡片共用同一個版心
- 頁面主體使用單一路徑的垂直堆疊，不使用大型 hero、儀表板拼貼或多套卡片語言混用
- 頁面上的功能差異，應透過新增 / 移除卡片區塊表達，而不是替每個功能頁重做一套新風格
- 員工端與 `admin` 頁面應共用同一套骨架語言，不能各自維護不同背景、容器與卡片規格

建議骨架：
- 頁面背景：`linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)`
- 頁面容器：`max-width + margin: 0 auto + padding + gap`
- 第一張卡：頁面說明卡（eyebrow / title / description）
- 後續卡片：依功能加入表單卡、列表卡、狀態卡、結果卡

卡片視覺基準：
- `background: rgba(255, 255, 255, 0.84)`
- `border-radius: 24px`
- `padding: 24px`
- `border: 1px solid rgba(148, 163, 184, 0.18)`
- `box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08)`

正式共用元件：
- `frontend/src/components/PageShell.vue`
- `frontend/src/components/PageCard.vue`
- `frontend/src/components/PageIntroCard.vue`

實作規範：
- 新頁面優先使用 `PageShell + PageIntroCard + PageCard` 組合，不應再為單一頁面重寫一套外層骨架
- `admin` 底下頁面也應沿用同一套頁面模板，只在卡片內容層處理功能差異
- 共用卡片語言應優先收斂到全域 design tokens / 共用 class / 共用 base component
- `Card.vue`、`Navbar.vue`、首頁個人服務入口卡應逐步與此基準對齊
- 未來若新增 `出勤紀錄`、`請假`、`班表`、`報表`、`申請單`、`admin` 管理頁等頁面，預設都先套這個骨架，再加上該頁專屬卡片
- 若真的需要偏離此模板，必須先有明確 UX 理由，而不是因為方便各頁各寫一套

### 8.8 個人服務入口卡統一規則（2026-04-10 起）
員工首頁 `個人服務` 下方的入口卡，正式以同一套卡片語言呈現，至少包含：
- `個人資料`
- `加班申請`
- `出勤紀錄`
- `補打卡申請`
- `請假申請`
- `我的班表`（條件顯示）

規則：
- 以上入口不可各自使用不同圓角、陰影、邊框、內距規格
- 啟用中的入口與 disabled 入口可在透明度、文字色、背景淡化上區分，但骨架應保持同一套
- 後續若新增新入口，也應直接沿用此卡片基準

---

## 9. 已依目前 baseline 回寫的正式結論（2026-04-10）

- 前端不是最終安全邊界，最終權限、tenant isolation、feature gate 仍由後端 authoritative enforcement（權威判定）
- 前端可以做 `precheck`（預檢）與 UX 提示，但不能作為最終合法性依據
- 員工端 P0 重點是手機查看自己當月正式出勤紀錄
- `HR / 管理端` 報表應與員工端查閱視角分流，不應混成同一個前端使用情境
- 員工首頁主入口應集中在內容區的 `個人服務`，而不是長駐頂部工具列
- `個人資料`、`出勤紀錄`、`請假申請`、`補打卡申請`、`加班申請` 為員工首頁主要候選入口
- `我的班表` 應採 `uses_schedule` 條件顯示，不應對所有員工固定顯示
- `排班管理` 只應放在後台管理，不應出現在員工打卡首頁
- 子頁面在移除頂部主導航後，應補明確返回首頁機制
- `frontend/src/views/LeaveRequestView.vue` 為目前前端頁面骨架與卡片語言的正式基準模板
- 新頁面應優先沿用同一套容器與卡片語言，功能差異用新增卡片區塊方式擴充，而不是各頁自建新風格
- `admin` 頁面也應逐步收斂到同一套 `PageShell / PageIntroCard / PageCard` 結構
- `Navbar.vue`、`Card.vue`、首頁 `個人服務` 入口卡已開始向此基準收斂，後續開發應延續同一路徑

---

## 10. Admin Layout Governance（2026-04-10 新增）### 10.1 這次問題的正式定義
本次 `/admin` 與 `/admin/companies` 發生的「切換時像放大一下、寬度看起來差一點、視覺有閃動感」，正式歸類為：

- 前端 layout governance 不一致
- 頁面骨架未被所有 admin 頁一致採用
- 視覺穩定性（visual stability）審查不足

這不是單一字級、單一卡片寬度或單一 CSS 數值問題，而是「同一功能群組底下的頁面沒有被同一套頁面模板完整治理」。

### 10.2 admin 頁面的正式骨架要求
自本條建立後，`admin` 相關頁面正式以 `/admin` 首頁所採用的共用頁面骨架為唯一基準。

最低要求如下：
- 使用 `PageShell`
- `admin` 系列頁面統一使用相同 `max-width`
- `Navbar` 必須放在同一層頁面 container 節奏內
- 頁面頂部說明區應使用同一路徑的 intro component（優先 `AdminPageIntro`，其次 `PageIntroCard`）
- 頁面主內容應以 `PageCard` 或相容的共用卡片元件組成
- 不可同時混用 `PageShell` 新模板與舊 `.admin-page > .container > .admin-header` 自製骨架

一句話：

> `admin` 是同一功能群組，不得每個子頁各自維護一套不同外層模板。

### 10.3 禁止的作法
以下作法自即日起視為前端治理違規：

1. 在 `admin` 子頁重新手寫新的最外層背景、container、header 骨架
2. `admin` 某些頁使用 `PageShell`，某些頁維持 `.admin-page/.container/.panel` 舊模板，形成混搭
3. 只局部調字級、padding、寬度數值，卻不先確認是不是整體骨架不一致
4. 沒有和 `/admin` 首頁做視覺對照，就直接修改 `/admin/*` 子頁
5. 使用「看起來差不多」當作對齊標準，而不是以同一份共用模板為準

### 10.4 修改 admin 頁面前的必做審查
之後只要修改以下任一頁面：
- `/admin`
- `/admin/companies`
- `/admin/users`
- `/admin/attendance`
- `/admin/onboarding`
- 未來新增的任何 `/admin/*`

都必須先完成以下審查：

#### 審查 A：先看共用模板
必須先閱讀：
- `frontend/src/components/PageShell.vue`
- `frontend/src/components/PageCard.vue`
- `frontend/src/components/PageIntroCard.vue`
- `frontend/src/components/admin/AdminPageIntro.vue`
- `frontend/src/views/Admin.vue`

若未先看以上檔案，不應直接開始改 admin 子頁。

#### 審查 B：先比對參考頁
至少要對照：
- `/admin`
- 當前要修改的 `/admin/*` 頁
- 一個已被視為視覺穩定的參考頁（例如 `/leave` 或其他已確定穩定頁）

比對項目至少包含：
- 是否同一個最外層背景
- 是否同一個 container 寬度
- `Navbar` 是否位在同一層節奏
- intro/header 的高度與 spacing 是否同一套
- 主卡片是否同一套圓角、陰影、邊框、padding 語言
- 切頁時 scrollbar 是否造成 viewport 寬度改變

#### 審查 C：先判斷根因，再改數值
若使用者回報「寬度不一樣」「點進去會閃」「像放大一下」，必須先依下列順序排查：
1. 是否使用同一個 layout/template
2. 是否存在不同 `max-width`
3. 是否存在不同背景 / container / header 骨架
4. 是否是 scrollbar 出現 / 消失造成視覺寬度抖動
5. 最後才是字級、padding、局部元件尺寸問題

禁止一開始就直接亂調：
- `font-size`
- `padding`
- `gap`
- `max-width`

除非前面 1~4 已確認不是根因。

### 10.5 Visual Stability（視覺穩定性）正式列入驗收標準
之後前端頁面修改，不只看「功能有沒有對」，還要看「切換是否穩」。

`admin` 頁面的驗收至少包含：
- 從 `/admin` 進入子頁時，不應有明顯放大 / 縮小 / 寬度跳動感
- 從子頁返回 `/admin` 時，不應有明顯視覺位移
- 同一群組頁面的 container 邊界應肉眼一致
- 同一群組頁面的標題區塊高度應肉眼一致
- 若頁面高度差異造成 scrollbar 切換，應優先處理 viewport 穩定性

### 10.6 全域 viewport 穩定性要求
若前端頁面切換時會因內容高度不同導致 scrollbar 出現 / 消失，進而造成版面寬度閃動，應將此視為 layout bug，而非可接受現象。

建議處理方向：
- 以全域 CSS 方式穩定 scrollbar gutter
- 避免讓頁面在某些 route 有 scrollbar、某些 route 沒有 scrollbar 時產生肉眼可見的寬度跳動

此條屬於前端共用體驗治理，不限於 `admin`。

### 10.7 本次事件的正式教訓
本次事件反映出以下治理缺口：

1. 已存在共用模板，但實際沒有被所有相關頁面一致使用
2. 修改者若只看單一頁面，很容易把問題誤判成字級或局部寬度
3. 使用者回報「看起來差一點」時，通常代表視覺穩定性出了問題，不應簡化成單點 CSS 微調
4. 後續若未先寫回 SDD，AI 或開發者很容易在下一次再重犯同樣的審查不足

### 10.8 之後遇到同類問題的標準處理流程
未來若再收到這類回報：
- 寬度不一致
- 頁面切換有閃動
- 點進去像放大 / 縮小
- 同群組頁面體感不一致

標準流程如下：

1. 先確認該群組是否已有正式共用模板
2. 盤點哪些頁面沒接上同一套模板
3. 審查全域 scrollbar / viewport 穩定性
4. 再處理局部字級、粗細、內距
5. 改完後必須實際做頁面切換比對，而不是只看單一頁截圖

---

## 11. 已依本次事件補充的正式結論（2026-04-10）

- `admin` 頁面切換的視覺穩定性，屬於前端架構一致性問題，不是單純樣式微調問題
- `admin` 共用 layout 只做出元件還不夠，必須要求所有 `admin` 頁一致接上
- `/admin` 為 `admin` 系列頁面的正式骨架參考頁
- 使用者回報「像放大一下」時，必須把 scrollbar / viewport width shift 納入第一輪排查
- 之後修改 `admin` 頁面，必須先做共用模板審查，再做局部樣式調整
