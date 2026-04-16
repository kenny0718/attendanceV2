Title: Schedule Module Spec
Author: Johnny Lee
Version: 1.1
Date Created: 2026-04-08
Last Modified: 2026-04-12
spec:id: schedule.module.v1
status: active
module: schedule
source_of_truth: SA/modules/schedule.md
related_code_paths:
  - backend/app/modules/schedule/api.py
  - backend/app/modules/schedule/service.py
  - backend/app/modules/schedule/repo.py
  - backend/app/modules/schedule/models.py
  - backend/app/modules/schedule/schemas.py
---

# Schedule 模組開發規格 排班模組

> 本文件定義 `schedule` 模組的正式 SDD / Spec。  
> 這個模組是系統中的「排班資料來源」，負責提供預期工作時間、班表指派與可被 `attendance` 消費的班表基線。  
> 自 `2026-04-12` 起，產品策略正式採用：**B 級中階營運排班為核心必備能力；C 級進階協作能力保留為未來加值包。**

---

## 1. 文件定位

### 1.1 這份文件是給誰看的

- 之後要修改排班功能的你
- 協助你開發排班功能的 AI
- 要 review `schedule` 與 `attendance` 邊界的人
- 要判斷排班功能屬於核心能力還是進階加值的人

### 1.2 什麼情況先看這份

- 你要修改 shift template
- 你要修改 shift assignment
- 你要新增班表查詢 API
- 你要修改排班與出勤整合方式
- 你要判斷某段規則該放 `schedule` 還是 `attendance`
- 你要判斷某功能屬於 B 級核心排班，還是 C 級進階協作包

### 1.3 它和其他文件的關係

- 系統級架構：`SA/architecture/SYSTEM_SDD.md`
- 模組邊界：`SA/architecture/MODULE_BOUNDARY_MATRIX.md`
- 出勤模組：`SA/modules/attendance.md`
- 補強分析：`SA/modules/schedule-enhancement-gap-analysis-2026-04-12.md`
- 模板來源：`SA/governance/MODULE_SPEC_TEMPLATE.md`

---

## 2. 目的與範圍

### 2.1 本文件負責的範圍

`schedule` 模組負責：

- 管理排班模板（shift template）
- 管理班表指派（shift assignment）
- 查詢某人某日適用班表
- 提供標準化班段資料與 baseline 給 `attendance` 使用
- 作為預期工作時間的 source of truth
- 承接 B 級中階營運排班所需的核心排班能力

### 2.2 本文件不負責的範圍

這個模組不處理：

- punch in / punch out 寫入
- break out / break in 寫入
- 實際工時計算
- 遲到 / 早退 / 加班最終判定
- JWT 驗證
- 請假審批流程
- 員工自助協作流程的最終產品決策 owner

### 2.3 一句話理解

> `schedule` 定義的是「應該怎麼上班」，不是「實際怎麼打卡」。

---

## 3. 核心原則

| 原則 | 定義 | 可驗證條件 |
|---|---|---|
| Schedule as Source of Truth | 班表是預期工作時間的正式來源 | `attendance` 只能讀 schedule，不可反寫 schedule semantic |
| Tenant-Scoped Schedule | 所有模板、指派、查詢都必須受 `company_id` 限制 | 不可跨公司讀寫班表資料 |
| Template / Assignment Separation | 模板管理與指派管理是兩層責任 | template CRUD 與 assignment CRUD 不應混成單一雜湊流程 |
| Baseline Export Consistency | 提供給 `attendance` 的班表 baseline 必須有一致格式 | 不可在 `attendance` 內再複製第二套 normalization |
| Schedule Owns Schedule Rules | 班表規則由 `schedule` 定義 | 不應把 schedule rule 長到 `attendance` router / service |
| Query Before Policy | 排班先提供可消費資料，再由 `attendance` 做出勤判定 | `schedule` 不直接承擔最終遲到早退判定 |
| B-first Product Strategy | B 級中階營運排班是核心能力，不是加值 | B 能力預設屬於核心模組範圍 |
| C-ready Extensibility | C 級協作能力先不強制實作，但架構不可堵死 | 未來可平滑擴充成 entitlement / add-on |

---

## 4. 產品分層與正式功能範圍

### 4.1 B 級：中階營運排班（核心必備能力）

自本版文件起，以下能力屬於 `schedule` 模組的**核心產品範圍**，不是可有可無的附加功能：

- 排班模板管理
- 班別指派管理
- 批次排班能力
- 週 / 區間班表視圖所需的查詢能力
- 請假衝突提示或驗證整合
- 班表發布流程
- 班表通知事件
- 排班 / 出勤對照所需的核心查詢契約

### 4.2 C 級：進階協作加值包（未來可選擴充）

以下能力視為**同一組進階加值包**，目前不列為第一階段必做，但第一階段設計不得阻斷其未來落地：

- availability（員工可排班 / 不可排班時段）
- shift swap（換班申請）
- employee acknowledgment（員工確認班表）
- coverage analytics（人力覆蓋分析）

### 4.3 產品策略正式結論

- B 級能力屬核心能力，應視為正式 `schedule` scope
- C 級能力不在第一階段強制落地，但要保留資料模型、狀態流、通知流、feature gate 的擴充空間
- 未來若進入商業化方案分級，C 級能力應優先採 `entitlement / feature gate` 設計

---

## 5. 功能規格

### 5.1 Shift Template CRUD

**用途**：建立、修改、停用班別模板。  
**主要檔案**：`api.py`, `service.py`, `repo.py`, `models.py`

**必要行為**：
- 建立模板時需綁定公司範圍
- 更新模板時保留資料一致性
- 停用模板時不應破壞既有 assignment 解析

### 5.2 Shift Assignment CRUD

**用途**：把班別指派給使用者或特定日期。  
**主要檔案**：`api.py`, `service.py`, `repo.py`

**必要行為**：
- assignment 必須受租戶範圍限制
- assignment 查詢需能定位人員、日期、適用區間
- 不可用 assignment 流程直接改寫 template 語意

### 5.3 Baseline Resolution

**用途**：把模板與指派整理成 `attendance` 可使用的排班基線資料。  
**主要檔案**：`service.py`, `repo.py`

**必要行為**：
- 解析某人某日有效班表
- 輸出標準化班段 / 時間窗口
- 維持單一解析邏輯，不要讓其他模組自己重寫

### 5.4 Standardized Shift Window Export

**用途**：提供出勤模組進行 policy evaluation 所需的標準化輸入。  
**主要檔案**：`service.py`, `schemas.py`

**必要行為**：
- 輸出欄位語意一致
- 若 contract 改變，需同步回寫 `schedule` 與 `attendance` 文件

### 5.5 Schedule Query APIs

**用途**：提供模板、指派、指定日期有效班表等查詢能力。  
**主要檔案**：`api.py`, `service.py`, `repo.py`

**必要行為**：
- query 必須受 tenant scope 限制
- 查詢契約改動需同步檢查 consumer 影響

### 5.6 Batch Scheduling（B 級核心）

**用途**：提供營運端可實際使用的批次排班能力。  
**主要檔案**：後續新增於 `api.py`, `service.py`, `repo.py`

**必要行為**：
- 支援多員工、多日期、多模板的一次性套班
- 支援 preview-first 或明確的衝突處理策略
- 不可讓批次排班繞過既有 tenant / validation / baseline contract

### 5.7 Leave Conflict Integration（B 級核心）

**用途**：在排班建立或批次套班前，檢查與請假資料的衝突。  
**主要檔案**：後續落於 `schedule.service` 為主

**必要行為**：
- `schedule` 只做排班驗證 / warning，不取得請假主責任
- leave 仍是 leave owner
- 驗證策略需明確定義是 warning、block，或可配置政策

### 5.8 Publish / Notify / Reconcile（B 級核心）

**用途**：讓排班從資料 CRUD 升級成可營運流程。  
**主要檔案**：後續依設計新增對應 service / event / query path

**必要行為**：
- 班表發布流程需有正式狀態語意
- 通知應優先採事件驅動，而不是 schedule 內硬發訊息
- 排班 / 出勤對照屬 integration-oriented read contract，不可破壞 `attendance` owner 邊界

---

## 6. 預設實作決策（降低 AI 與人來回確認成本）

以下為本文件目前採用的**預設決策**。除非之後另有明確覆寫，AI 或開發者應優先依這些預設進行規劃與實作。

### 6.1 產品優先順序

1. 先做 B 級核心能力
2. C 級能力先保留擴充，不先強制落地
3. 若 B 與 C 衝突，以 B 的穩定落地優先

### 6.2 規劃預設

- 管理端排班 UI：優先採**週班表**思路，不以月曆作為第一優先
- 批次排班：優先採**preview-first** 思路
- 請假衝突：第一階段預設可先採 **warning-first**，除非業務規則另行定義為 block
- 通知整合：優先採事件驅動消費，不採 schedule 內嵌硬通知
- C 級四功能：視為同一進階包，不拆成四個獨立產品方案

### 6.3 明確禁止的做法

- 不要把 B 級需求塞回 `attendance` 內硬做
- 不要因為先做 B，就把未來 C 的狀態流寫死
- 不要把 publish 語意粗暴塞進現有 `assignment.status` 而不經過正式定義
- 不要把 `leave` 整合寫成 schedule 直接接管請假生命週期

---

## 7. Formalized Semantic Block

```yaml
scope:
  module: schedule
  responsibility:
    - shift_template_management
    - shift_assignment_management
    - baseline_resolution
    - effective_schedule_lookup
    - normalized_shift_window_export
    - batch_scheduling_core
    - leave_conflict_integration
    - roster_publish_notify_reconcile_contract
  non_responsibility:
    - attendance_punch_write
    - attendance_duration_persistence
    - final_attendance_policy_judgement
    - jwt_authentication
    - leave_approval
    - employee_self_service_collaboration_owner

contracts:
  tenant_isolation:
    source: actor.active_company_id
    body_override_allowed: false
  semantic_owner:
    schedule_source_of_truth: true
    attendance_can_override_schedule_semantic: false
  write_authority:
    owner: schedule.service_and_repo
    api_direct_db_write: false
  product_tiering:
    core_capability:
      - batch_scheduling
      - leave_conflict
      - publish_flow
      - notification_event
      - schedule_attendance_reconcile
    add_on_capability:
      - availability
      - shift_swap
      - employee_acknowledgment
      - coverage_analytics
  integration_contract:
    exported_to: attendance
    exported_semantics:
      - expected_work_time
      - shift_segments
      - normalized_windows

validation_rules:
  - rule: no_cross_tenant_schedule_access
    description: 不可跨公司查詢或修改 template / assignment
    verification: access with another company scope is rejected
  - rule: attendance_reads_but_does_not_redefine
    description: attendance 只能消費 schedule baseline，不可反寫 schedule semantic
    verification: no schedule normalization duplicated inside attendance feature change
  - rule: single_baseline_resolution_path
    description: 有效班表解析應有單一路徑
    verification: effective schedule lookup goes through schedule service/repo path
  - rule: b_capabilities_are_not_optional
    description: B 級能力屬核心排班 scope，不應視為純加值
    verification: roadmap and SDD classify B as core
  - rule: c_capabilities_must_remain_extensible
    description: C 級能力可延後，但不能被第一期設計堵死
    verification: future add-on can be introduced without breaking core contract

change_triggers:
  update_spec_when:
    - template_contract_changed
    - assignment_flow_changed
    - baseline_resolution_changed
    - attendance_integration_contract_changed
    - effective_schedule_query_changed
    - batch_scheduling_contract_changed
    - publish_notify_flow_changed
    - product_tiering_changed
```

---

## 8. 開發與驗證流程

### 8.1 開發步驟

1. 先判斷這次改動是 template、assignment、lookup、baseline export，還是 B 級營運能力補強
2. 確認是否影響 `attendance` 的 consumer contract
3. 確認是否影響未來 C 級擴充能力
4. 優先在既有 `service.py` / `repo.py` 路徑內落實變更
5. 不要把 schedule rule 直接塞進其他模組
6. 改完後同步回寫 `SA/modules/schedule.md`

### 8.2 最低驗證清單

#### Template 驗證
- 可正確建立 / 修改 / 停用模板
- 不可跨公司操作模板

#### Assignment 驗證
- 可正確建立 / 修改 / 查詢 assignment
- 指派結果可對應到指定人員與日期
- 不可用 assignment 改壞 template 語意

#### Baseline 驗證
- 可解析某人某日有效班表
- 標準化輸出格式一致
- `attendance` 可直接消費，不需額外抄第二套解析邏輯

#### B 級能力驗證
- 批次排班不可破壞 tenant isolation
- 請假衝突整合不可取得 leave owner 身分
- 發布與通知流程需保留正式狀態與事件語意
- 排班 / 出勤對照不可反向改寫 `attendance` 語意

#### Integration 驗證
- 與 `attendance` 的欄位契約一致
- contract 改動時，文件與 consumer 一起更新

#### Real JWT E2E 驗證基線（2026-04-16）
- 真 JWT 測試 fixture 必須補齊 `roles`、`users`、`user_company_memberships`、`company_entitlements`，不可只建立 token 後直接呼叫 API
- `schedule` feature gate 的正式 key 為 `schedule.core`，不得寫成 `schedule_core`
- JWT consumer 目前視 `session_id` 為 access token 必要 claim；測試建立真 JWT 時必須帶入
- company A / company B 的 entitlement 狀態應明確分開 seed，才能驗證 enabled / disabled 與跨租戶拒絕行為
- 真 JWT E2E 最低驗證應覆蓋：401（無 token / invalid token）、200（已啟用 company）、403（feature disabled company）、template CRUD 基線、assignment CRUD 基線、cross-tenant 阻擋

---

## 9. 依賴與共用元件

### 9.1 可依賴
- `app.core.dependencies`
- `app.core.scope`
- `schedule.service`
- `schedule.repo`
- `schedule.models`
- `schedule.schemas`
- 必要時透過明確 integration path 消費 `leave` / `notifications` 能力

### 9.2 不應承擔
- attendance punch persistence
- attendance reporting aggregation
- leave approval orchestration
- authentication token issuance
- employee self-service full workflow ownership

### 9.3 與其他模組的責任分界

| 模組 | `schedule` 提供什麼 | `schedule` 不做什麼 |
|---|---|---|
| `attendance` | expected work time、shift segments、normalized windows、reconcile 所需排班資料 | 不做 punch write、不做最終出勤事實判定 |
| `auth` | 使用其身份 / actor 結果 | 不處理登入與 token |
| `tenants` | 使用公司與成員範圍、未來可搭配 entitlements | 不作為 tenant source of truth |
| `leave` | 提供排班前衝突檢查所需背景資料 | 不處理請假審批 |
| `notifications` | 可消費排班事件做通知 | 不負責通知主流程決策 |

---

## 10. Do / Don’t

### Do
- 把排班模板與指派分開理解
- 把有效班表解析視為正式責任
- 保持提供給 `attendance` 的 baseline 契約穩定
- 用單一路徑處理 normalization
- 把 B 級能力視為正式 schedule scope
- 為 C 級能力保留擴充空間
- contract 改變時同步更新文件

### Don’t
- 不要把 attendance policy 判定塞進 `schedule`
- 不要在 `attendance` 內重抄一份 schedule normalization 邏輯
- 不要讓 API 直接承擔過多業務協調
- 不要跨 tenant 查詢或修改班表
- 不要把 schedule 當作打卡交易寫入模組
- 不要把 C 級概念在沒有正式定義前，粗暴塞進現有 B 級欄位語意

### 最容易踩雷的錯誤
1. `schedule` 與 `attendance` 都各自維護一套排班正規化
2. assignment 邏輯和 template 語意混在一起
3. query contract 變了，但沒有同步檢查 `attendance`
4. router 直接承擔太多 business orchestration
5. 把 B 級營運流程硬塞進單筆 CRUD，而沒有正式流程語意
6. 為了趕第一期，把未來 C 級擴充路徑全部寫死

---

## 11. 已拍板決策（避免後續 AI 反覆追問）

### 11.1 `assignment.status.confirmed` 的正式語意

本文件已先拍板如下：

- `confirmed` = 管理端已確認該筆 assignment 有效
- `confirmed` 不等於已發布
- `confirmed` 不等於員工已確認
- `confirmed` 也不直接等於不可再修改的最終鎖定狀態

**正式規則**：後續 AI 與開發者不得擅自把 `confirmed` 解讀成 publish completed 或 employee acknowledgment。

### 11.2 B 級發布流程的第一版策略

本文件已先拍板第一版策略如下：

- 第一版先做**最小可擴充發布流程**
- 目標是先支援班表發布、可辨識發布狀態、可觸發通知
- 第一版不強制先做完整 `roster` / `schedule_period` / `publish_record` 大模型

**正式規則**：若需先落地第一版，應優先以可擴充方式實作；不得把所有發布語意粗暴塞進單筆 assignment status。

### 11.3 請假衝突的第一版策略

本文件已先拍板第一版策略如下：

- 第一版採 **warning-first**
- 先提示排班與請假衝突
- 第一版預設不直接 hard block

**正式規則**：若未來有公司級政策需求，可再升級為 hard block 或 company policy-driven，但第一版預設為 warning-first。

### 11.4 C 級加值包的 entitlement 命名

未來應正式補上 feature key / entitlement key 命名，但本版先不強制定死字串。

---

## 12. 回寫規則

當發生以下任一情況，必須更新本文件：

- template 結構改變
- assignment 流程改變
- baseline resolver 改變
- 有效班表查詢契約改變
- 與 `attendance` 的整合欄位或 semantic 改變
- B 級核心能力範圍改變
- C 級加值包內容改變
- product tiering / entitlement 規劃改變

若變更影響跨模組邊界，還要同步更新：

- `SA/modules/attendance.md`
- 必要時 `SA/modules/attendance-policy.md`
- 必要時 `SA/architecture/MODULE_BOUNDARY_MATRIX.md`
- 必要時 `SA/SDD_PROGRESS_TRACKER.md`

---

## 13. 已依目前 baseline 回寫的正式結論（2026-04-12）

- `schedule`（排班）是預期工作時間的 source of truth（正式權威來源）
- `attendance`（出勤）只能消費 schedule baseline，不應反向改寫 schedule 語意
- `schedule` 提供 baseline；最終遲到 / 早退 / 加班判定仍由 `attendance.policy`（出勤規則子域）負責
- B 級中階營運排班能力屬於核心排班 scope，不是加值功能
- C 級能力採同一組進階協作加值包策略，包含 availability、shift swap、employee acknowledgment、coverage analytics
- 若 baseline export contract 改變，必須同步更新 `schedule` 與 `attendance` 文件及 consumer 驗證
- 若未來進入商業化方案分級，C 級能力應優先透過 entitlement / feature gate 方式落地
