1. Audit Summary
目前 reporting.py 已達到「可用且邊界初步成形」的狀態：三支既有 endpoint 可由同一 router 維持一致入口，並已正確串接 reporting_repo.py、reporting_service.py、reporting_helpers.py。
API 層仍承擔了不少 orchestration 責任（權限判斷、查詢參數決策、response shaping、display name enrich），但這些多數屬於「可接受的 API 編排責任」。
reporting_helpers.py 現況乾淨，僅有 datetime 驗證與正規化，沒有跨層污染。
reporting_service.py 已承接 user/company summary 聚合邏輯，且保持純計算（無 DB / 無 actor），方向正確。
reporting_repo.py 也維持純讀取層，tenant isolation 與 filter 規則清楚。
整體成熟度：中等偏穩定（可持續擴充，但不宜把新報表再全部塞進同一檔）。
另外，現有 backend/app/modules/attendance/api.py 已不含 reporting 實作段落，因此本輪無法做「拆分前舊版」逐行語意比對，只能基於現存模組邊界做盤點。
2. Current Responsibility Map
責任	目前所在檔案	是否合理留在該層	備註
router 定義與路由掛載	api/reporting.py	是	API 層核心責任
query 參數基本驗證（limit、UUID parse）	api/reporting.py	是	屬 request boundary 驗證
datetime 驗證/正規化工具	api/reporting_helpers.py + api/reporting.py 呼叫	是	helper 純工具、使用方式清楚
scope / permission（actor + admin 判斷）	api/reporting.py	是（短中期）	API 層做授權決策合理
feature gate 檢查	api/reporting.py 呼叫共用 helper	是	一致套用於三支 endpoint
DB 查詢	reporting_repo.py	是	已抽離 API 層，分工正確
聚合計算（user/company summary）	reporting_service.py	是	純函式計算，邊界乾淨
response shaping（SessionResponse、SummaryResponse 組裝）	api/reporting.py	是（可再微調）	API 組 DTO 合理
display name enrichment	api/reporting.py（呼叫 core.user_lookup）	部分合理	目前可留；若日後複雜可抽 presenter/enricher
報表擴充入口（新報表入口治理）	尚未明確模組化	否（長期）	需建立「新報表不回塞 reporting.py」規則
3. Split Quality Findings
已拆對的部分
reporting_repo.py：查詢職責明確、tenant isolation 規則集中。
reporting_service.py：summary 聚合已抽離，且維持純計算。
reporting_helpers.py：純工具、無 DB/actor/schema 依賴污染。
reporting_schemas.py：reporting response contract 獨立，降低 API 層 schema 噪音。
尚未拆乾淨的部分
reporting.py 內仍有較多 endpoint orchestration 細節（尤其 /sessions：scope 分支 + 查詢參數決策 + enrich + mapping）。
display name enrich 邏輯仍在 API 層內 inline（目前可接受，但成長後可能膨脹）。
不該現在動的部分
不建議立即再拆成多 router 檔（週報/月報等）——目前只有三支核心 endpoint，過早拆分會增加維護成本。
不建議動 schemas.py/repo.py 既有 contract（本輪目標是 audit，不是重構）。
4. Future Expansion Boundary
週報：建議未來放 attendance/api/reporting_weekly.py（或 attendance/reporting/weekly_api.py）+ 對應 service/repo 查詢方法。
月報：建議獨立 reporting_monthly.py（或 reporting/monthly_api.py），避免把 period-specific 規則灌進現有 reporting.py。
遲到 / 缺勤 / 異常報表：建議走「事件/異常導向」子模組，例如 reporting_exceptions.py 或 reporting/anomaly_api.py，不要混進 sessions summary 流程。
不應再直接塞回 reporting.py 的原因：目前 reporting.py 已承擔三支核心 endpoint 的編排責任，若再加入多報表類型，會快速變成高耦合入口檔，導致授權規則、查詢參數、回應 shaping 彼此纏結。
5. Safe Split Order
先定義擴充規則，不動現行三支 endpoint：reporting.py 僅保留 core 三支（sessions/user-summary/company-summary）。
新增報表時先分 API 檔，再補 service/repo：先把新 endpoint 放新檔，避免先動既有檔。
重用既有 helper/service/repo 原則：能重用就重用，不先抽象化。
若 /sessions enrich 邏輯成長，再做單一步抽離：僅抽 response enrich/presenter，不碰查詢與授權。
每次只拆一種責任：例如先拆「週報 API 入口」，下一票再拆「週報聚合」；避免一次多軸重構。
6. Final Recommendation
A. 目前先停，等未來新增報表時再逐步拆。
理由：
現況三層邊界（repo/service/helpers）已可用且清楚，立即再拆收益有限。
現有 reporting.py 雖不算極瘦，但仍在可控範圍，且主要是 API orchestration。
真正需要拆分的觸發點是「新報表類型進來」；屆時採新增子模組即可，風險最低、回歸範圍最小。
7. Safety Statement
本次為 Audit only。
我僅進行讀取、檢查、比對與回報，未修改任何檔案。