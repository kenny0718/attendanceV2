# REPORTING MODULE ARCHITECTURE (v1)

本文件定義 attendance reporting 模組的責任邊界與拆分規則。
目的：避免 reporting 模組膨脹成單一大型檔案（>1000 行），並確保長期可維護性。

--------------------------------------------------
[核心原則]
--------------------------------------------------

Reporting 模組採用「責任分層」設計，而非功能堆疊。

❌ 禁止：
- 將所有 reporting 邏輯集中在單一檔案（如 reporting.py）
- 使用「先寫進去，再拆分」策略
- 混合 query / aggregation / formatting / routing

✅ 必須：
- 在寫入前判斷責任層
- 根據責任層放入對應檔案
- 維持單一責任原則（Single Responsibility）

--------------------------------------------------
[模組結構]
--------------------------------------------------

attendance/

  api/
    reporting.py

  reporting_service.py
  reporting_repo.py
  reporting_helpers.py
  reporting_schemas.py

--------------------------------------------------
[責任定義]
--------------------------------------------------

1. api/reporting.py
--------------------------------------------------
只負責：

- route 定義（@router.get）
- permission gate（admin / hr）
- request parsing（query params）
- 呼叫 reporting_service
- 回傳 response schema

禁止：

- 寫資料查詢（SQLAlchemy）
- 寫 aggregation 邏輯
- 寫 display_name enrich 細節
- 寫複雜 response shaping
- 寫報表計算邏輯

--------------------------------------------------

2. reporting_service.py
--------------------------------------------------
只負責：

- 報表 orchestration（流程控制）
- 多資料來源整合（repo + helper）
- aggregation（user summary / company summary）
- response shaping（轉成 schema 所需格式）

適合放：

- build_session_report(...)
- build_user_summary_report(...)
- build_company_summary_report(...)

禁止：

- 直接寫 SQLAlchemy query
- 定義 router
- 定義 schema class

--------------------------------------------------

3. reporting_repo.py
--------------------------------------------------
只負責：

- 資料查詢（DB access）
- filter / where / order
- tenant isolation
- raw row retrieval

適合放：

- list_sessions_by_company(...)
- list_sessions_by_user(...)
- get_summary_rows(...)

禁止：

- aggregation（總結計算）
- response shaping
- display_name enrich
- business decision

--------------------------------------------------

4. reporting_helpers.py
--------------------------------------------------
只負責：

- 輕量工具函式
- datetime normalize
- display label 處理
- 小型欄位轉換

禁止：

- 主流程 orchestration
- DB query
- 大型 aggregation

--------------------------------------------------

5. reporting_schemas.py
--------------------------------------------------
只負責：

- request schema（query params）
- response schema
- summary item schema

禁止：

- helper logic
- query
- orchestration

--------------------------------------------------
[分層原則]
--------------------------------------------------

查資料（Query）：
→ reporting_repo.py

算資料（Aggregation / Summary）：
→ reporting_service.py

格式處理（Formatting）：
→ reporting_helpers.py

API入口（Routing）：
→ api/reporting.py

資料契約（Schema）：
→ reporting_schemas.py

--------------------------------------------------
[拆分觸發條件（強制）]
--------------------------------------------------

若符合以下任一條件，必須優先拆分：

1. 新增一組報表（非單一欄位調整）
2. reporting.py 超過 300 行
3. reporting.py 出現 aggregation 邏輯
4. reporting_service.py 同時處理多種報表類型
5. reporting_repo.py 同時承載不同查詢族群
6. 同一檔案同時包含：
   - routing + query + aggregation + formatting
7. 預期該功能會持續擴展

符合以上條件：

❌ 禁止直接寫入既有檔案
✅ 必須先提出拆分方案

--------------------------------------------------
[未來擴展策略]
--------------------------------------------------

當 reporting 模組持續成長時：

第一階段：
維持 5 檔結構（本文件定義）

第二階段（必要時）：
拆分為：

- reporting_session_service.py
- reporting_summary_service.py
或
- reporting_session_repo.py
- reporting_summary_repo.py

⚠️ 禁止一開始過度拆分

--------------------------------------------------
[禁止事項（強制）]
--------------------------------------------------

禁止：

- 將所有 reporting 功能塞入 reporting.py
- 在 api 層寫 aggregation
- 在 repo 層寫 business logic
- 在 helper 層寫主流程
- 在 schema 層寫任何邏輯
- 使用「先寫再拆」策略

--------------------------------------------------
[與其他模組關係]
--------------------------------------------------

policy_engine.py：
- 不可被 reporting 使用來重新計算結果

work_hour_engine.py：
- 為 canonical 工時計算來源
- reporting 不可自行重算 work minutes / paid hours

reporting 模組：
- 僅做 read / aggregation / display
- 不可改變資料語義

--------------------------------------------------
[核心設計準則]
--------------------------------------------------

Reporting 的本質是：

- Read-only
- Aggregation
- Presentation

而不是：

- Calculation source
- Business rule engine
- Data mutation layer

--------------------------------------------------