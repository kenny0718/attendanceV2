Title: Schedule Enhancement Gap Analysis and Implementation SDD
Author: Claude
Version: 1.0
Date Created: 2026-04-12
Last Modified: 2026-04-12
spec:id: schedule.enhancement.gap-analysis.v1
status: draft
module: schedule
source_of_truth: SA/modules/schedule-enhancement-gap-analysis-2026-04-12.md
related_docs:
  - SA/modules/schedule.md
  - SA/modules/attendance.md
  - SA/architecture/SYSTEM_SDD.md
  - SA/architecture/MODULE_BOUNDARY_MATRIX.md
  - SA/architecture/PLANNED_VS_IMPLEMENTED_MATRIX.md
related_code_paths:
  - backend/app/modules/schedule/api.py
  - backend/app/modules/schedule/service.py
  - backend/app/modules/schedule/repo.py
  - backend/app/modules/schedule/models.py
  - frontend/src/views/schedule/SchedulePage.vue
  - frontend/src/views/schedule/MySchedulePage.vue
  - frontend/src/api/schedule.js
---

# 排班模組補強分析報告 / 實作 SDD

> 本文件是針對目前 `SA` 目錄既有正式文件、以及現行程式碼中的 `schedule` 模組所做的補強分析報告。  
> 目的不是重寫 `SA/modules/schedule.md`，而是補一份**可直接拿來討論下一步實作**的差距分析與 SDD 草案。

---

## 1. 文件目的

這份文件要回答 4 件事：

1. `SA` 目前對排班模組已經定了哪些正式原則
2. 現行程式碼中的排班能力做到哪裡
3. 兩者相比，還有哪些尚未落地或容易踩雷的地方
4. 如果要往更完整的商用排班系統補強，應該先做什麼

---

## 2. 這次掃描 `SA` 目錄後的重點結論

這次掃描後，和排班模組最相關、而且後續修改時一定要一起看的文件有：

- `SA/modules/schedule.md`
- `SA/modules/attendance.md`
- `SA/architecture/MODULE_BOUNDARY_MATRIX.md`
- `SA/architecture/SYSTEM_SDD.md`
- `SA/architecture/PLANNED_VS_IMPLEMENTED_MATRIX.md`
- `SA/SDD_PROGRESS_TRACKER.md`
- `SA/SA21功能清單基線.md`
- `SA/SA21功能清單_對應SDD分配.md`

### 2.1 目前 `SA` 對 schedule 的正式定位已經很明確

目前 `SA/modules/schedule.md` 已正式把 `schedule` 定位為：

- 排班模板 owner
- 班表指派 owner
- 有效班表查詢 owner
- baseline resolution owner
- 提供 `attendance` 消費的 expected work time / shift segments / normalized windows 的 source of truth

這代表後續任何排班補強，**都不能再把排班主責任拉回 `attendance`**。

### 2.2 `SA` 已經把 schedule 與 attendance 的邊界寫得很清楚

要注意的不是「兩個模組有沒有互動」，而是：

- `schedule` 可以提供 baseline
- `attendance` 可以消費 baseline
- 但 `attendance` 不可以反向定義 schedule semantic

所以之後如果新增：

- 週班表
- 月排班
- 批次排班
- 排班衝突檢查
- 與請假衝突提示

這些仍應優先落在 `schedule` 的責任範圍內，不能偷放到 `attendance.policy` 裡硬做。

### 2.3 `SA` 已接受 schedule 是「現況正式設計演進」

`SA/architecture/PLANNED_VS_IMPLEMENTED_MATRIX.md` 已明確寫到：

- `schedule` 雖不是最早藍圖中最成熟獨立的模組
- 但現況已明確形成正式模組
- 而且這個演進方向是對的

所以現在不是討論「要不要有 schedule 模組」，而是討論：

> 如何把 `schedule` 從基礎 CRUD，補強成真正可營運使用的排班模組。

---

## 3. 目前程式實作盤點

根據現行程式碼，`schedule` 已落地的能力如下。

### 3.1 後端已有的能力

#### A. Shift Template CRUD

已具備：

- 建立模板
- 查詢模板
- 更新模板
- 啟用 / 停用模板
- company scope 限制
- feature gate 檢查

#### B. Shift Assignment CRUD

已具備：

- 建立單筆指派
- 查詢指派
- 依使用者 / 日期範圍 / 單日 / template / status 過濾
- 更新指派
- 取消指派

#### C. Baseline resolution

已具備：

- 依 `company_id + user_id + work_date` 解析有效班表
- 能輸出 normalized windows
- 有預設 fallback path
- 與 `attendance` 的 baseline contract 已有基礎實作

#### D. Segment model / 跨日能力

已具備：

- 多 segment 結構
- `segment_index` 唯一性檢查
- 絕對時間軸檢查
- overlap 驗證
- 跨日班支援

### 3.2 前端已有的能力

#### A. 管理端 `SchedulePage.vue`

已具備：

- 模板列表
- 模板建立 / 編輯 / 啟停用
- 單筆指派建立
- 指派取消

#### B. 員工端 `MySchedulePage.vue`

已具備：

- 顯示未來 14 天個人班表
- 顯示班別名稱 / 時間 / 狀態 / 備註
- 基本 refresh

---

## 4. 這次掃描 `SA` 後特別要注意的地方

這一段是最重要的，因為這些是之後修改時最容易踩線的地方。

### 4.1 注意點一：`schedule` 是 source of truth，不是附屬工具頁

`SA/modules/schedule.md` 已把 schedule 定義成正式來源，不只是輔助 attendance 的小功能。

因此後續若要補強排班：

- 不能只改前端頁面
- 不能只做資料表 CRUD
- 必須把查詢契約、baseline contract、與 attendance integration 一起看

### 4.2 注意點二：不能在 `attendance` 重抄第二套排班正規化

`SA/modules/schedule.md` 已明訂：

- baseline resolution 應有單一路徑
- `attendance` 不應重寫第二套 normalization

所以未來若補：

- 班表衝突檢查
- 排班視窗計算
- 跨日班規則
- segment 轉換

都應優先放在 `schedule.service` / `schedule.repo` 的正式路徑，不要在 `attendance` 裡再長一份邏輯。

### 4.3 注意點三：`assignment` 與 `template` 不可語意混寫

`SA` 已反覆強調 `Template / Assignment Separation`。

後續若新增：

- 批次排班
- 週班表
- 排班複製
- 員工月曆

必須保持：

- `template` 是 reusable shift definition
- `assignment` 是某人某日被指派到某模板

不要讓 assignment 流程偷偷開始覆蓋 template 語意。

### 4.4 注意點四：若補請假衝突檢查，請把它當 integration，不是 ownership 轉移

未來高機率會補：

- 排班時檢查該員工是否請假
- 排班時提示已有 leave overlap

這件事可以做，但邏輯上應保持：

- `leave` 還是請假 owner
- `schedule` 只是消費 leave 狀態來做排班驗證 / warning
- 不可以在 schedule 內承接請假生命週期主責任

### 4.5 注意點五：如果補發布流程，要新增 roster / publish layer，不要硬塞進目前單筆 assignment status

目前 `assignment.status` 為：

- `scheduled`
- `confirmed`
- `cancelled`

若未來要做：

- 草稿班表
- 已發布班表
- 發布通知
- 發布後鎖定

建議不要直接把這些概念全塞進現有 assignment status，而應新增更高一層的：

- roster batch
- publish record
- schedule period state

否則後面語意會混亂。

---

## 5. 現況差距分析

以下是依照目前 `SA` 正式定位，與現行程式落地結果相比的主要差距。

### 5.1 Gap A：目前是 CRUD 系統，不是排班作業系統

現況偏向：

- 模板管理
- 單筆指派管理
- 基本查詢

但實際營運所需通常還包括：

- 週視圖 / 月視圖
- 以員工為列、日期為欄的排班盤
- 快速套班 / 批次複製
- 可視化缺班與衝突

**判斷**：這是目前最大的產品差距。

### 5.2 Gap B：缺批次能力

現況只有單筆 assignment create。  
缺少：

- 批次建立 assignments
- 複製上週班表
- 日期區間快速套班
- 週模板 / recurring schedule

**判斷**：若不補，實務操作成本很高。

### 5.3 Gap C：管理端 UX 仍是工程管理頁，不是營運排班頁

目前要輸入：

- `user_id`
- `shift_template_id`
- `work_date`

這比較像工程後台，不像 HR / 店主管會用的排班工具。

**判斷**：前端 UX 是第一個會影響真實使用落地的障礙。

### 5.4 Gap D：缺跨模組衝突檢查

目前 `SA` 已清楚定邊界，但實作尚未補齊：

- 與 `leave` 的請假衝突
- 與 `attendance` 的排班 vs 實際出勤對照
- 同人同日 / 同時段 assignment overlap 防呆（如果 repo / create path 還未完整防）
- 最小休息時間 / 最大工時等排班規則

**判斷**：這是第二階段的重要補強。

### 5.5 Gap E：缺「班表發布」與通知事件

目前可以建立 assignment，但沒有正式的：

- publish schedule
- notify employee
- revision history
- changed since last publish

而你系統中已有 `notifications` 模組，這代表這塊很適合往正式事件流整合。

### 5.6 Gap F：員工端只有看表，沒有互動

目前員工端是 read-only。  
尚缺：

- 月曆 / 週曆模式
- 接收異動提示
- 可用性回報
- 換班 / 調班申請
- 排班確認

**判斷**：這些不一定是第一期，但若目標是學 Swingvy 類做法，遲早要補。

---

## 6. 建議實作方向

以下不是一次做完，而是建議的實作順序。

### 6.1 Phase 1：先把排班從 CRUD 補成可用的排班台

#### 目標
讓主管能用一個頁面排整週班，而不是逐筆新增。

#### 建議功能

1. 週班表 grid view
   - 橫軸：日期
   - 縱軸：員工
   - cell 顯示班別

2. 員工選擇器
   - 顯示姓名 / 部門 / 職位
   - 不再輸入 UUID

3. 批次建立 assignments API
   - 支援多人、多日期、多模板一次寫入

4. 複製班表 API
   - 例如把本週複製到下週

5. 單日 / 區間視圖查詢 API
   - 以 grid 消費模型輸出資料

#### 這一期應落在哪裡

- 後端：`schedule` 模組
- 前端：`frontend/src/views/schedule/`
- 文件：更新 `SA/modules/schedule.md`

### 6.2 Phase 2：補衝突檢查與跨模組整合

#### 建議功能

1. leave overlap warning / blocking
2. assignment overlap 檢查
3. 最小休息時間檢查
4. 每日 / 每週工時上限警示
5. schedule vs attendance 異常對照頁

#### 注意

這一期最容易踩到邊界，因此一定要遵守：

- `schedule` 定義 expected work arrangement
- `leave` 仍是 leave owner
- `attendance` 仍是 attendance fact owner

### 6.3 Phase 3：補商用品能力

#### 建議功能

1. roster publish
2. 異動通知
3. 員工自助確認 / 換班申請
4. availability / preferred hours
5. 月曆視圖 / mobile friendly personal roster

---

## 7. 建議的正式實作項目拆解

以下是較適合直接拆成工作項的版本。

### 7.1 Backend API 建議新增

#### A. Grid / roster 查詢
- `GET /api/v1/schedule/roster-grid`
- `GET /api/v1/schedule/roster-summary`

#### B. 批次指派
- `POST /api/v1/schedule/shift-assignments/bulk`

#### C. 複製班表
- `POST /api/v1/schedule/rosters/copy`

#### D. 排班驗證
- `POST /api/v1/schedule/shift-assignments/validate`

#### E. 發布流程（第二或第三期）
- `POST /api/v1/schedule/rosters/publish`
- `GET /api/v1/schedule/rosters/publish-history`

### 7.2 Backend domain 建議新增

#### A. `roster` / `schedule_period` 概念
用途：承接整週 / 整月排班與發布，不要把所有語意壓在單筆 assignment 上。

#### B. `bulk assignment service`
用途：統一：
- 批次建單
- 衝突檢查
- skip / replace / merge policy

#### C. `schedule validation service`
用途：集中處理：
- overlap
- leave conflict
- rest-hour rule
- max-hour warning

### 7.3 Frontend 建議新增

#### A. 管理端週班表頁
可先新增：
- `frontend/src/views/schedule/ScheduleRosterPage.vue`

#### B. 批次排班面板
功能：
- 多選員工
- 選擇日期區間
- 選擇班別模板
- 一次套用

#### C. 員工端月曆頁
可先擴充 `MySchedulePage.vue` 或新增 `MyScheduleCalendarPage.vue`

---

## 8. 建議的資料與語意原則

### 8.1 應繼續維持的原則

1. `schedule` 是 expected work time source of truth
2. `attendance` 只消費 baseline
3. baseline normalization 單一路徑
4. template 與 assignment 分離
5. 所有 schedule query / write 都受 `company_id` 限制

### 8.2 建議新增的原則

1. Bulk-first, not single-row-first
   - 真正營運排班以批次為主，單筆只是補洞手段

2. Roster-view-first, not CRUD-form-first
   - 管理介面應優先支援 grid / calendar，而非單筆表單

3. Validation-before-persist
   - 批次排班前應先有 validation path

4. Publish-layer-separation
   - 發布語意不應混在 assignment status 裡

---

## 9. 修改時的風險清單

### 9.1 高風險

1. 在 `attendance` 內新增第二套 schedule baseline 邏輯
2. 直接用 assignment status 承載 publish workflow
3. 批次 API 直接在 router 層硬做 orchestrate
4. 前端先做漂亮 grid，但後端 contract 還停留在單筆 CRUD 模式

### 9.2 中風險

1. leave 檢查做成 schedule 內部 hard coupling
2. template 與 assignment 更新流程語意混掉
3. grid view 查詢 contract 和既有 `listAssignments` contract 混在一起

### 9.3 低風險但要留意

1. 員工端 14 天列表改成月曆時，仍要保留 mobile readability
2. 班別顏色 / badge / UX 命名要先定語意，不要只看視覺

---

## 10. 本次建議結論

### 10.1 一句話結論

目前 `schedule` 模組底層結構與 `SA` 正式定位是健康的，真正不足的不是資料模型，而是：

> 還缺「批次排班、週期視圖、衝突檢查、發布流程、通知整合」這一整層排班營運能力。

### 10.2 最值得優先補的 5 項

1. 週班表 / 排班 grid view
2. 批次建立 assignment API
3. 員工選擇器，淘汰 UUID 手輸
4. leave / overlap 驗證
5. roster publish + notification event

### 10.3 這份文件的使用方式

你接下來如果要實作排班補強，建議順序：

1. 先用這份文件確定功能優先順序
2. 確認後，把正式原則回寫 `SA/modules/schedule.md`
3. 再拆 backend / frontend 的工作項
4. 若涉及 `attendance` 邊界變更，同步回寫 `SA/modules/attendance.md` 與 `SA/architecture/MODULE_BOUNDARY_MATRIX.md`

---

## 11. 建議下一步

如果你看完這份文件認同方向，下一輪可以直接做下面其中一份：

### 選項 A：技術實作版 SDD
我再幫你細化成：

- 資料表調整建議
- API contract 草案
- 前端頁面資訊架構
- 驗證規則清單
- phased rollout 計畫

### 選項 B：先回寫正式模組文件
我直接把這份報告濃縮回寫進：

- `SA/modules/schedule.md`
- 必要時 `SA/architecture/MODULE_BOUNDARY_MATRIX.md`
- 必要時 `SA/SDD_PROGRESS_TRACKER.md`

讓 `SA` 變成正式一致版本，再開始動 code。
