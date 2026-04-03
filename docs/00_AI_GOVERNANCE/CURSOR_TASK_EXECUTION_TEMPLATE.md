# CURSOR TASK EXECUTION TEMPLATE (v2)
# 強制前置分析 + 模組責任判定 + 拆分決策控制

本文件為所有開發任務的「強制前置流程」。
目的：避免邏輯集中、避免先寫再拆、維持模組責任邊界。

--------------------------------------------------
[PRE-EXECUTION ARCHITECTURE GATE]（強制）
--------------------------------------------------

在任何修改開始前，必須完成以下分析。

未完成：
❌ 禁止修改任何檔案
❌ 禁止產生程式碼
❌ 禁止進入 FIX 階段

--------------------------------------------------
[STEP 1] 模組責任歸屬判定（必填）
--------------------------------------------------

請判定本次需求屬於哪一層（可多選，但必須說明主層）：

- policy_engine（policy orchestration）
- policy_rules（late / early / overtime / holiday / violation rules）
- policy_schedule_models（WorkWindow / WorkSchedule / FlexTimeBand）
- work_hour_engine（canonical work minute / paid hour / break deduction）

- api layer（routing / permission / request parsing / response assembly）
- service layer（business orchestration / aggregation）
- repo layer（data access / query only）

- reporting orchestration（報表流程控制）
- reporting helper / formatter（欄位處理 / 顯示加工）
- schema / contract layer（API schema / response shape）

必須回答：
1. 主責任層（Primary Layer）
2. 次責任層（Secondary Layers）
3. 為什麼不是其他層（簡要說明）

--------------------------------------------------
[STEP 2] 是否需要拆分（必填）
--------------------------------------------------

請判斷：

是否需要拆分新檔案？
- YES / NO

若 YES，必須提供：
- 拆分檔名
- 每個檔案責任
- 為什麼不能放在既有檔案

若 NO，必須說明：
- 為何目前檔案責任仍單一且清晰
- 為何不會造成未來擴展困難

--------------------------------------------------
[STEP 3] 技術債風險評估（必填）
--------------------------------------------------

若不拆分，本次變更的技術債風險：

- LOW（不會影響未來擴展）
- MEDIUM（未來可能需要拆分）
- HIGH（幾乎確定會造成重構）

必須說明原因。

--------------------------------------------------
[STEP 4] API / SERVICE / REPO 分層判定（必填）
--------------------------------------------------

若本次涉及 API 或資料流程，必須回答：

1. 這次邏輯應放在哪一層：
   - API（只負責 request/response + permission）
   - Service（負責流程與聚合）
   - Repo（只負責查詢）

2. 是否出現以下違規風險：
   - API 做 business logic
   - API 做 aggregation
   - Service 做 DB query
   - Repo 做判斷邏輯

若有風險：
→ 必須提出修正分層方案

--------------------------------------------------
[STEP 5] 拆分觸發條件檢查（強制）
--------------------------------------------------

若符合以下任一條件，必須優先拆分：

- 新增「一組規則」（非單一條件）
- 新增「一組報表」
- 新增「多個 endpoint」
- 同一檔案同時包含：
  - orchestration + calculation + formatting + query
- 單一檔案責任變模糊
- 預期後續會持續擴充同類功能

符合任一條件：
❌ 禁止直接寫入原檔
✅ 必須先提出拆分方案

--------------------------------------------------
[STEP 6] 禁止事項（強制）
--------------------------------------------------

禁止：

- 未完成分析直接寫檔
- 將所有邏輯集中寫入單一檔案
- 把 rule 寫進 policy_engine.py
- 把 calculation 寫進 API
- 把 aggregation 寫進 repo
- 將 reporting 全部塞入 reporting.py
- 使用「先寫再拆」策略

--------------------------------------------------
[STEP 7] 拆分確認流程（強制）
--------------------------------------------------

若 STEP 2 判定為 YES：

必須：
1. 先提出拆分方案
2. 等待確認
3. 才可進入實作

不得直接開始修改。

--------------------------------------------------
[STEP 8] 進入實作前確認
--------------------------------------------------

完成以下才可進入 FIX：

- 模組歸屬已確認
- 拆分決策已確認
- 無違反責任邊界
- 無違反 API/service/repo 分層

--------------------------------------------------
[核心原則]
--------------------------------------------------

❌ 錯誤流程：
寫 → 發現太大 → 再拆

✅ 正確流程：
分析 → 判斷是否拆 → 再寫

--------------------------------------------------
[ATTENDANCE MODULE 固定責任邊界]
--------------------------------------------------

- policy_engine.py：
  僅允許 policy evaluation orchestration

- policy_rules.py：
  僅允許 late / early / overtime / holiday / violation rules

- policy_schedule_models.py：
  僅允許 WorkWindow / WorkSchedule / FlexTimeBand

- work_hour_engine.py：
  僅允許 canonical work minute / paid hour / break deduction

違反以上：
❌ 必須停止並回報