Title: Schedule B Phase 1 Implementation Spec 排班系統分析
Author: Claude
Version: 1.1
Date Created: 2026-04-12
Last Modified: 2026-04-12
spec:id: schedule.phase1.b.v1
status: draft
module: schedule
source_of_truth: SA/modules/schedule-phase1-b-spec.md
related_docs:
  - SA/modules/schedule.md
  - SA/modules/schedule-enhancement-gap-analysis-2026-04-12.md
  - SA/modules/attendance.md
related_code_paths:
  - backend/app/modules/schedule/api.py
  - backend/app/modules/schedule/service.py
  - backend/app/modules/schedule/repo.py
  - backend/app/modules/schedule/models.py
  - backend/app/modules/schedule/schemas.py
---

# Schedule B 級第一階段可開發規格

> 本文件專門定義 `schedule` 模組的 **B 級核心排班 Phase 1** 可開發規格。  
> 目的不是討論產品方向，而是把第一階段要做什麼、先不做什麼、API 怎麼切、資料語意怎麼定、和其他模組怎麼對接，先一次寫清楚，降低後續 AI 與開發來回確認成本。

---

## 1. 文件目標

這份文件要解決 6 件事：

1. 定義 B 級 Phase 1 的正式交付範圍
2. 把「現有 CRUD 排班」提升成「可營運使用的排班流程」
3. 明確規定哪些能力這一版一定做、哪些明確不做
4. 明確規定資料語意，避免把發布、確認、員工確認混在一起
5. 明確規定與 `attendance`、`leave`、`notifications` 的整合方式
6. 提前列出仍需拍板的少數問題，避免實作中途反覆中斷

---

## 2. 本階段正式定位

### 2.1 一句話定義

> B 級 Phase 1 = 在既有 template / assignment / baseline 能力之上，補齊「批次排班、週班表查詢、請假衝突 warning、最小發布流程、通知事件、排班/出勤對照查詢」的第一版可營運能力。

### 2.2 本階段不是什麼

本階段 **不是**：

- 完整 workforce management suite
- 完整 C 級協作包
- 完整 roster domain 大重構
- 完整 rule engine 商業配置平台
- 完整月排班可視化與拖拉式 UI
- 完整排班成本分析 / 覆蓋率分析 / 換班申請系統

### 2.3 本階段對現有系統的意義

現況已有：

- Shift Template CRUD
- Shift Assignment CRUD
- baseline resolution
- `attendance` 消費班表 baseline 的基本能力

本階段補的是：

- 從「一筆一筆排」提升到「批次作業」
- 從「資料存在」提升到「有發布語意」
- 從「只有 CRUD」提升到「有營運流程」
- 從「只有 schedule 自己看得懂」提升到「其他模組可整合消費」

---

## 3. Phase 1 正式交付範圍

本階段只做以下 6 個能力包。

### 3.1 P1-B1：Batch Scheduling 批次排班

**要做**：

- 支援多員工、多日期、多模板的一次性批次排班
- 支援 preview-first
- 支援建立前先做 validation
- 支援回傳逐筆成功 / skipped / warning / failure 結果
- 支援重覆 assignment 檢查策略

**不要求**：

- 不做複雜自動排班演算法
- 不做 AI 智能排班
- 不做 coverage optimization
- 不做 availability-based auto assignment

### 3.2 P1-B2：Weekly Schedule Query 週班表查詢

**要做**：

- 管理端可查某週、某群人、某部門條件下的班表結果
- 員工端可查自己的週班表 / 指定區間班表
- 支援彙整 assignment 與發布狀態
- 回傳前端易用的 week-grid / list-friendly 結構

**不要求**：

- 不先做月曆優先資料模型
- 不做 drag-and-drop UI spec
- 不做 coverage heatmap

### 3.3 P1-B3：Leave Conflict Warning 請假衝突提示

**要做**：

- 在單筆排班與批次排班前檢查請假衝突
- 第一版採 `warning-first`
- warning 可出現在 preview 與 commit 結果中
- 保留未來升級成 block / policy-driven 的擴充點

**不要求**：

- 不在 `schedule` 內接手請假審批
- 不在本階段做複雜可配置衝突規則後台
- 不做跨多請假類型的超細商業規則引擎

### 3.4 P1-B4：Minimal Publish Flow 最小發布流程

**要做**：

- 能把指定區間的班表標記為已發布
- 能辨識未發布 / 已發布 狀態
- 發布後可提供通知事件
- 發布操作以「區間 / 批次」為主，不是逐筆 assignment 手動拼裝

**不要求**：

- 不強制先做完整 `roster` / `schedule_period` / `publish_record` 大模型
- 不做員工 acknowledgment
- 不做發布後不可修改的硬鎖版制度
- 不做多層審批流程

### 3.5 P1-B5：Notification Event 通知事件

**要做**：

- 發布班表後產生可被 `notifications` 消費的事件
- 可標記事件類型、公司、期間、影響員工集合
- 採事件驅動整合，不在 `schedule` 內直接硬發送訊息

**不要求**：

- 不直接串所有訊息供應商
- 不在 `schedule` 內產生通知模板內容
- 不做已讀回執與追發策略

### 3.6 P1-B6：Schedule / Attendance Reconcile Query 排班 / 出勤對照查詢

**要做**：

- 提供對照查詢所需的 schedule-side read contract
- 可查某人 / 某日期 / 某週的 expected shift baseline
- 可讓 `attendance` 或管理端畫面對照「預期班表 vs 實際出勤」

**不要求**：

- 不把最終 late / early / overtime 判定搬進 `schedule`
- 不讓 `schedule` 成為出勤報表 owner

---

## 4. 本階段明確不做的功能

以下功能雖然重要，但不屬於 B Phase 1：

- availability 提報 / 偏好時段
- shift swap 換班申請
- employee acknowledgment / read receipt
- coverage analytics
- 自動補位
- 智能排班建議
- 月曆中心資料模型
- 排班成本 / 工時預估分析
- 多版本草稿比較
- 排班審批工作流

這些全部保留給後續 C 級或 B 第二階段，不在本文件強制落地。

---

## 5. 既有基線與延續原則

### 5.1 沿用現有正式規則

本階段延續 `SA/modules/schedule.md` 已拍板內容：

- `schedule` 是 expected work time 的 source of truth
- `attendance` 只消費 baseline，不反寫排班語意
- `assignment.status.confirmed` 不是 publish completed
- 請假衝突第一版採 `warning-first`
- B 級能力屬核心模組 scope
- C 級能力保留擴充，但不先落地

### 5.2 本階段不得破壞的邊界

- 不可把 schedule semantic 拉回 `attendance`
- 不可把 leave lifecycle owner 寫進 `schedule`
- 不可把 notification 主流程硬塞進 `schedule`
- 不可把 publish semantic 直接混成 assignment 的唯一狀態語意

---

## 6. Phase 1 資料語意與最小資料模型策略

### 6.1 assignment 語意維持不變

既有 `assignment.status` 仍維持 assignment 自身語意：

- `scheduled`
- `confirmed`
- `cancelled`

正式規則：

- assignment status 管的是「這筆指派本身是否有效 / 已確認 / 已取消」
- assignment status **不等於** publish status
- assignment status **不等於** employee acknowledgment

### 6.2 publish status 應與 assignment status 分離

本階段即使不做完整大模型，也必須維持 publish 語意獨立。

**最低要求**：

- 發布狀態需存在於 assignment 外層或 publish layer
- 查詢週班表時，前端可辨識「該區間是否已發布」
- 發布事件需可對應到一次發布動作，不可只剩逐筆 assignment 模糊狀態

### 6.3 建議的第一版最小資料模型策略

本文件建議第一版採 **輕量 publish layer**，而不是完整重建 roster domain。

建議新增一個最小發布實體，暫稱：

- `schedule_publish_batch`

建議欄位：

- `id`
- `company_id`
- `start_date`
- `end_date`
- `published_at`
- `published_by`
- `notes`（optional）
- `target_scope_snapshot`（optional，記錄當下條件，例如 team / department / user_ids）

正式語意：

- 它代表一次「針對某區間 / 某範圍班表」的發布動作
- 它不是未來完整 roster 模型的終點，但足夠承接 Phase 1 的發布語意與通知事件

### 6.4 為何先用 publish batch，而不是直接做完整 roster

原因：

- 你已拍板第一版先做最小可擴充發布流程
- 目前系統已有 assignment CRUD，先疊 publish layer 成本較低
- 可以先滿足週班表、發布、通知、已發布識別需求
- 未來若要升級成 `roster / schedule_period / publish_record`，仍可平滑遷移

### 6.5 Phase 1 不建議的做法

- 不要把 `published` 塞進 `assignment.status`
- 不要讓前端自己猜哪些 assignment 算已發布
- 不要用「最後更新時間」冒充發布時間
- 不要把一次發布拆成逐筆 assignment 個別發訊息的主語意

---

## 7. API 能力規格

本段定義的是 **應新增的 API contract 類型**，不是最終 URL 字串唯一版本；但若無特殊理由，開發應優先照本文件命名風格落地。

### 7.1 Batch Scheduling APIs

#### 7.1.1 預覽批次排班

`POST /api/v1/schedule/batch-assignments/preview`

**用途**：

- 不寫入資料
- 檢查輸入是否合法
- 檢查 template / user / date 範圍
- 檢查重覆 assignment
- 檢查 leave conflict
- 回傳預覽摘要與逐筆結果

**request 概念欄位**：

- `user_ids[]`
- `dates[]` 或 `date_range`
- `shift_template_id`
- `mode`（第一版正式採 `skip_existing`，預留未來擴充）
- `notes`（optional）

**response 概念欄位**：

- `summary.total_candidates`
- `summary.creatable`
- `summary.skipped`
- `summary.warnings`
- `summary.errors`
- `items[]`
  - `user_id`
  - `work_date`
  - `result` = `ok | skipped | warning | error`
  - `warning_codes[]`
  - `error_codes[]`
  - `existing_assignment_id`（若有）
  - `leave_conflicts[]`（若有）

#### 7.1.2 提交批次排班

`POST /api/v1/schedule/batch-assignments/commit`

**用途**：

- 真正建立 assignment
- 採 preview-first 導向
- 回傳逐筆建立結果

**正式規則**：

- 第一版允許 preview 後直接 commit，也可視需要支援直接 commit
- 若直接 commit，系統仍須內部重跑 validation，不可信任前一次 preview 結果
- 預設策略為：遇到已存在 assignment 的項目標記 `skipped`，不覆蓋；遇到 error 的項目不建立；warning 項目可建立，但需明確回傳 warning

### 7.2 Weekly Schedule Query APIs

#### 7.2.1 管理端週班表查詢

`GET /api/v1/schedule/weekly-view`

**query 建議欄位**：

- `start_date`
- `end_date`
- `user_ids[]`（optional）
- `department_id`（optional，若現有資料模型已有）
- `team_id`（optional）
- `published_only`（optional）

**response 最低要求**：

- 回傳指定區間內各 user 的 daily assignments
- 每日結果能帶出 template 基本資訊
- 可辨識 publish 狀態
- 便於前端產出 week-grid 或 list view

#### 7.2.2 員工端我的週班表查詢

`GET /api/v1/schedule/my/weekly-view`

**正式規則**：

- user_id 來自 actor，不可信任 query override
- 至少回傳：日期、班別、時段、assignment status、publish status

### 7.3 Leave Conflict Validation Contract

不論是單筆 assignment、batch preview、batch commit，皆應共用同一套 schedule-side conflict contract。

**最低輸出欄位建議**：

- `has_conflict`
- `conflict_type`
- `leave_request_id`（若能取得）
- `leave_type`（若能取得）
- `overlap_start`
- `overlap_end`
- `severity` = `warning`
- `message`

### 7.4 Publish APIs

#### 7.4.1 發布指定區間班表

`POST /api/v1/schedule/publish`

**request 建議欄位**：

- `start_date`
- `end_date`
- `target_scope`（例如 all / user_ids / department / team）
- `notes`（optional）

**response 最低要求**：

- `publish_batch_id`
- `published_at`
- `published_by`
- `scope_summary`
- `affected_assignment_count`
- `event_enqueued` 或等價事件資訊

**正式規則**：

- 發布是區間級操作
- 發布應可重複執行，但需明確定義重複發布結果
- 第一版可先採「同區間重新發布 = 新增一筆 publish batch」策略，不強求複雜版本樹

#### 7.4.2 查詢區間發布狀態

`GET /api/v1/schedule/publish-status`

**用途**：

- 供週班表或管理端畫面判斷某區間是否已發布
- 供後續出勤對照畫面顯示班表穩定度

### 7.5 Reconcile Query APIs

#### 7.5.1 指定人員 / 日期排班基線查詢

`GET /api/v1/schedule/reconcile/baseline`

**用途**：

- 提供 `attendance` 或管理端對照某人某日預期班表

**最低回傳欄位**：

- `user_id`
- `work_date`
- `assignment_id`
- `shift_template_id`
- `assignment_status`
- `publish_status`
- `expected_work_minutes` 或等價 baseline 資訊
- `segments[]`
- `normalized_windows`

---

## 8. 核心流程規格

### 8.1 批次排班流程

1. 管理端送出批次條件
2. 系統先做 preview
3. 系統驗證：
   - tenant scope
   - user existence / scope
   - template validity
   - duplicate assignment
   - leave conflict
4. 系統回傳逐筆 preview 結果
5. 管理端確認後送 commit
6. 系統再次驗證
7. 系統建立 assignment
8. 對已存在 assignment 的項目標記 `skipped`
9. 回傳 success / skipped / warning / error 統計

### 8.2 請假衝突處理流程

1. 取得待排班的 user + date + shift window
2. 向 leave integration path 查詢 overlap
3. 若有 overlap：
   - 第一版標記 `warning`
   - 不直接 hard block
4. 將 warning 回傳到 preview / commit 結果
5. assignment 可建立，但 warning 必須可見

### 8.3 發布流程

1. 管理端選定區間與目標範圍
2. 系統統計該區間內 assignment 集合
3. 系統建立 `schedule_publish_batch`
4. 系統寫入發布事件資料
5. 系統回傳 publish result
6. `notifications` 可後續消費事件做訊息通知

### 8.4 週班表查詢流程

1. 前端指定週區間
2. 系統讀取該區間 assignment
3. 系統結合 publish status
4. 視需要附帶 template 基本資訊
5. 回傳前端友善結構

### 8.5 排班 / 出勤對照流程

1. consumer 指定 user / date / range
2. `schedule` 回傳 baseline 與 publish 狀態
3. `attendance` 依 baseline 做遲到、早退、加班等判定
4. `schedule` 不負責改寫 attendance 結果

---

## 9. 模組責任分工

### 9.1 `schedule` 負責

- 排班模板與指派 owner
- 批次排班 orchestration
- leave conflict validation consumption
- publish batch owner
- publish event emission
- weekly schedule read model
- reconcile 所需 schedule-side baseline contract

### 9.2 `attendance` 負責

- 實際出勤交易寫入
- attendance policy evaluation
- late / early / overtime 判定
- reporting aggregation

### 9.3 `leave` 負責

- 請假申請與審批生命週期
- 請假正式狀態語意
- 請假區間資料 source of truth

### 9.4 `notifications` 負責

- 通知事件消費後的實際訊息送出
- 模板內容
- 通知渠道與投遞策略

---

## 10. 事件規格

### 10.1 本階段至少要有的事件

#### `schedule.assignments.published`

**用途**：班表發布後供通知模組或其他 consumer 使用。

**最低 payload 建議欄位**：

- `event_id`
- `event_type`
- `company_id`
- `publish_batch_id`
- `start_date`
- `end_date`
- `published_by`
- `affected_user_ids[]`
- `affected_assignment_count`
- `occurred_at`

### 10.2 事件設計規則

- `schedule` 只負責發出事件或寫入事件來源資料
- `schedule` 不負責通知主流程編排
- 事件 payload 要足夠讓 consumer 不需回頭重查過多 schedule 內部語意

---

## 11. 權限、租戶與安全規則

### 11.1 Tenant Isolation

- 所有 schedule 讀寫都必須以 actor 的 `active_company_id` 為準
- 不可信任 request body 自帶 `company_id`

### 11.2 Actor-derived identity

- 員工端我的班表查詢，`user_id` 必須來自 actor
- 管理端查詢他人班表時，需沿用既有管理權限模型

### 11.3 Publish / Batch 操作

- 批次排班與發布應視為管理能力
- 若未來要加 entitlement / feature gate，B 級 Phase 1 也應走既有 feature gate 模式

---

## 12. 與現有 API 的關係

### 12.1 現有 API 保留

現有：

- `shift-templates` CRUD
- `shift-assignments` CRUD

仍保留作為基礎能力。

### 12.2 新增 API 不應破壞既有語意

- 不要把既有 `PATCH /shift-assignments/{id}` 擴充成負責整個批次排班流程
- 不要把 `cancel` 語意混成發布撤回
- 不要用 assignment update API 偷塞 publish logic

### 12.3 建議落地方式

- CRUD API 繼續維持 resource-oriented
- 批次 / 發布 / 對照查詢，新增明確 process-oriented API

---

## 13. 驗證與驗收標準

### 13.1 批次排班驗收

- 可一次為多人多日建立 assignment
- preview 與 commit 結果一致性合理
- duplicate assignment 有明確處理結果
- 已存在 assignment 的項目會被標記 `skipped`，不會被靜默覆蓋
- leave conflict warning 可被回傳
- tenant isolation 不被破壞

### 13.2 週班表查詢驗收

- 可正確查詢指定週區間
- 前端不需自己拼裝 publish 狀態
- 員工端與管理端查詢契約清楚分離

### 13.3 發布流程驗收

- 可對指定區間建立發布紀錄
- 可辨識某區間是否已發布
- 發布後可產生事件
- assignment status 未被污染成 publish status

### 13.4 對照查詢驗收

- `attendance` 可消費 schedule baseline
- schedule 與 attendance 的 semantic owner 不混線
- 查詢欄位足以做 expected vs actual 對照

---

## 14. 建議實作順序

### Phase 1-1

1. 批次排班 preview / commit
2. leave conflict warning contract
3. 管理端週班表查詢

### Phase 1-2

4. 最小 publish batch
5. publish status query
6. published event

### Phase 1-3

7. reconcile baseline query
8. 員工端我的週班表查詢補強
9. 文件、測試、consumer contract 對齊

---

## 15. 本文件已替你先拍板的實作預設

除非後續明確覆寫，AI 與開發者應直接按以下預設落地：

- 批次排班採 `preview-first`
- 批次排班遇到既有 assignment 採 `skip_existing`
- 請假衝突採 `warning-first`
- 發布流程採最小 publish layer，不先做完整 roster domain
- 發布狀態與 assignment status 分離
- 第一版發布後允許修改 assignment，但視為發布後異動
- 通知採事件驅動，不在 schedule 內直接送訊息
- 週班表優先於月班表
- 月班表列入 B Phase 2，不列入 C 級加值包
- 對照查詢只提供 schedule baseline，不接手 attendance 判定

---

## 16. 已拍板正式決策（避免後續 AI 反覆追問）

### 16.1 批次排班遇到既有 assignment 的策略

本文件已先拍板第一版正式策略如下：

- 預設採 `skip_existing`
- 若某 `user_id + work_date` 已存在有效 assignment，該筆不覆蓋
- 該筆應在 preview 與 commit 結果中明確標記為 `skipped`
- `skipped` 屬於可見結果，不應被默默吞掉
- 第一版不提供 `overwrite_existing` 作為預設行為

**正式規則**：

- 批次排班第一版的定位是「補空白」，不是「整批重排」
- 若已有 assignment，不可被批次排班靜默覆蓋
- 若未來要支援 `overwrite_existing`，必須作為獨立能力與獨立規格補入，不得在第一版中隱性出現

**原因**：

- 最安全
- 不會把既有人工排班蓋掉
- 可降低第一版 audit、通知、發布後異動等複雜度
- 後續若要做 `overwrite`，可獨立加能力

### 16.2 發布狀態的查詢粒度

本文件已先拍板第一版正式策略如下：

- 第一版以「區間 + target scope 是否已有 publish batch 覆蓋」作為 published 判斷基礎
- 第一版不強制建立逐筆 assignment 的 immutable publish snapshot
- 週班表查詢、發布狀態查詢、對照查詢，皆可依 publish batch coverage 判斷該區間是否已發布
- 若同區間重新發布，第一版可視為新增一筆 publish batch，不強求複雜版本樹

**正式規則**：

- 第一版的 publish status 屬於「區間 / scope 級語意」，不是「逐筆 assignment 永久凍結快照語意」
- 不得要求第一版提供逐筆不可變發布版本比對能力
- 若未來需要精確追蹤某筆 assignment 在每次發布當下的內容，再升級為 immutable snapshot / versioned publish model

**原因**：

- 較符合第一版最小可擴充發布流程策略
- 可先滿足班表是否已發布、可否通知、畫面是否顯示已發布狀態等營運需求
- 可避免第一版就導入過重的版本管理與快照模型

### 16.3 發布後是否允許再修改 assignment

本文件已先拍板第一版正式策略如下：

- 第一版允許發布後修改 assignment
- 發布後的新增、修改、取消，都應視為「發布後異動」
- 第一版不強制發布後異動必須先重新發布
- 第一版不強制實作發布後硬鎖定

**正式規則**：

- 第一版的 publish 語意表示「該區間班表已被正式發布過」，不等於「之後完全不可修改」
- 發布後若 assignment 發生變動，不得把該變動假裝成原始發布內容從未變更
- 未來若需要更嚴格治理，可再升級為：
  - 修改後需重新發布
  - 修改後標記 pending re-publish
  - 發布後部分欄位不可修改
  - 發布後完整鎖版

**原因**：

- 較符合第一版先求可落地、可營運的策略
- 可避免第一版就被鎖定 / 解鎖 / 重發 / 審批流程拖重
- 與前述 `assignment.status.confirmed` 不等於最終鎖定的正式語意一致

### 16.4 月班表的產品分層定位

本文件正式定義如下：

- 月班表屬於 **B 級核心排班能力**
- 月班表 **不是** C 級進階協作加值包
- 月班表不列入 B Phase 1
- 月班表改列入 **B Phase 2**

**正式規則**：

- 不得將月班表誤歸類為 availability、shift swap、employee acknowledgment、coverage analytics 這類 C 級能力
- 不得因月班表延後實作，就把它視為可有可無的非核心功能
- 後續 roadmap、SDD、開發拆工、AI 任務規劃，都應將月班表視為 B 級核心排班的第二階段能力

**原因**：

- 月班表本質上仍屬於核心排班視圖與核心排班查詢能力的延伸
- 月班表不屬於員工協作、加值互動或進階分析產品線
- 第一階段先做週班表，是因為週班表更符合營運排班與發布操作節奏；不是因為月班表不重要

### 16.5 為什麼 B Phase 1 優先做週班表

本文件正式定義如下：

- B Phase 1 的主操作視圖以 **週班表** 為優先
- 月班表不作為第一階段主查詢與主操作模型
- 第一階段應先優先支援週區間查詢、週區間排班、週區間發布、週區間異動管理

**正式規則**：

- 第一階段若需在週班表與月班表之間擇一優先，應優先實作週班表
- 不得因 UI 偏好或展示需求，反向把月班表拉成第一階段主模型
- 若第一階段需補充區間查詢，也應以「7 天到 14 天可操作區間」優先，而不是先做完整月曆中心模型

**原因**：

- 週班表較符合實際排班、補班、調班、發布與重新發布的營運節奏
- 週班表較適合批次排班 preview / commit 的作業流程
- 週班表較適合第一階段的最小 publish flow
- 週班表可降低第一階段在資料量、畫面密度、查詢複雜度、異動判讀上的風險
- 月班表較偏總覽視圖與中期規劃視圖，較適合作為第二階段補強

### 16.6 月班表在 B Phase 2 的正式定位

本文件正式定義如下：

- B Phase 2 應補上月班表查詢與月視圖能力
- 月班表屬於對週班表的延伸，不是替代週班表
- 月班表的主要目的為提供更大區間的總覽、跨週瀏覽與管理端檢視能力

**Phase 2 最低目標**：

- 可查詢指定月份或跨月區間的班表結果
- 可顯示各員工在月區間內的 assignment 分布
- 可辨識已發布 / 未發布 / 發布後異動等狀態
- 可支援從月視圖進入週視圖或日視圖的 drill-down
- 可支援管理端做月層級排班檢視

**正式規則**：

- B Phase 2 的月班表是「總覽與檢視能力補強」，不是第一階段的主作業入口
- 月班表應建立在既有週班表、發布狀態、assignment 查詢契約之上，不應重新發明第二套排班語意
- 月班表若實作，仍應沿用 `schedule` 作為排班 source of truth，不得把月視圖邏輯轉移至 `attendance` 或其他模組

### 16.7 避免誤解的明確規則

為避免後續 AI 或開發者誤判，本文件明確定義：

- 週班表優先，不代表月班表不重要
- 月班表延後到 B Phase 2，不代表月班表屬於 C 級加值功能
- 月班表屬於核心排班能力，只是實作順序晚於週班表
- 第一階段主目標是先完成可營運的排班操作流程；第二階段再補更大範圍的總覽視圖
- 若後續 AI、規格文件、roadmap 或拆工文件將月班表歸類為 C 級能力，應視為與本文件衝突，需回到本文件修正

**一句話正式結論**：

- 週班表 = B Phase 1
- 月班表 = B Phase 2
- 兩者都屬於 B 級核心排班能力

---

## 17. 本階段與下一階段的排班視圖結論

本文件正式拍板：

- B Phase 1 以週班表作為主查詢與主操作視圖
- B Phase 2 補上月班表作為總覽與延伸檢視視圖
- 週班表與月班表皆屬於 B 級核心排班能力
- 月班表不是 C 級加值功能

### 補充說明（給人看的白話版）

第一階段先做週班表，不是因為月班表不重要，而是因為第一階段的重點是先把排班作業流程做穩，包括批次排班、請假衝突提示、發布、通知與對照查詢。這些能力都比較適合以「一週」為主節奏來設計。

月班表仍然是核心排班能力的一部分，只是它更偏向總覽、跨週瀏覽與中期檢視，因此安排在 B Phase 2 實作。後續不應把月班表誤認為 C 級加值功能。

---

## 18. 建議結論

若你要的是「先把 B 級排班真正做成能開發、能交付、能繼續擴」的規格，那本文件建議直接以以下組合進入開發：

1. 保留既有 template / assignment CRUD
2. 新增 batch preview / commit
3. 新增 leave conflict warning contract
4. 新增 weekly schedule query
5. 新增最小 publish batch
6. 新增 publish event
7. 新增 reconcile baseline query

這樣可以在不重做整個 schedule domain 的前提下，先把 B 級核心排班的第一階段做完整。
