Title: Schedule Module Spec
Author: Johnny Lee
Version: 1.0
Date Created: 2026-04-08
Last Modified: 2026-04-08
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

# Schedule 模組開發規格

> 本文件定義 `schedule` 模組的正式 SDD / Spec。  
> 這個模組是系統中的「排班資料來源」，負責提供預期工作時間、班表指派與可被 `attendance` 消費的班表基線。

---

## 1. 文件定位

### 1.1 這份文件是給誰看的

- 之後要修改排班功能的你
- 協助你開發排班功能的 AI
- 要 review `schedule` 與 `attendance` 邊界的人

### 1.2 什麼情況先看這份

- 你要修改 shift template
- 你要修改 shift assignment
- 你要新增班表查詢 API
- 你要修改排班與出勤整合方式
- 你要判斷某段規則該放 `schedule` 還是 `attendance`

### 1.3 它和其他文件的關係

- 系統級架構：`SA/architecture/SYSTEM_SDD.md`
- 模組邊界：`SA/architecture/MODULE_BOUNDARY_MATRIX.md`
- 出勤模組：`SA/modules/attendance.md`
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

### 2.2 本文件不負責的範圍

這個模組不處理：

- punch in / punch out 寫入
- break out / break in 寫入
- 實際工時計算
- 遲到 / 早退 / 加班最終判定
- JWT 驗證
- 請假審批流程

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

---

## 4. 功能規格

### 4.1 Shift Template CRUD

**用途**：建立、修改、停用班別模板。  
**主要檔案**：`api.py`, `service.py`, `repo.py`, `models.py`

**必要行為**：
- 建立模板時需綁定公司範圍
- 更新模板時保留資料一致性
- 停用模板時不應破壞既有 assignment 解析

### 4.2 Shift Assignment CRUD

**用途**：把班別指派給使用者或特定日期。  
**主要檔案**：`api.py`, `service.py`, `repo.py`

**必要行為**：
- assignment 必須受租戶範圍限制
- assignment 查詢需能定位人員、日期、適用區間
- 不可用 assignment 流程直接改寫 template 語意

### 4.3 Baseline Resolution

**用途**：把模板與指派整理成 `attendance` 可使用的排班基線資料。  
**主要檔案**：`service.py`, `repo.py`

**必要行為**：
- 解析某人某日有效班表
- 輸出標準化班段 / 時間窗口
- 維持單一解析邏輯，不要讓其他模組自己重寫

### 4.4 Standardized Shift Window Export

**用途**：提供出勤模組進行 policy evaluation 所需的標準化輸入。  
**主要檔案**：`service.py`, `schemas.py`

**必要行為**：
- 輸出欄位語意一致
- 若 contract 改變，需同步回寫 `schedule` 與 `attendance` 文件

### 4.5 Schedule Query APIs

**用途**：提供模板、指派、指定日期有效班表等查詢能力。  
**主要檔案**：`api.py`, `service.py`, `repo.py`

**必要行為**：
- query 必須受 tenant scope 限制
- 查詢契約改動需同步檢查 consumer 影響

---

## 5. Formalized Semantic Block

```yaml
scope:
  module: schedule
  responsibility:
    - shift_template_management
    - shift_assignment_management
    - baseline_resolution
    - effective_schedule_lookup
    - normalized_shift_window_export
  non_responsibility:
    - attendance_punch_write
    - attendance_duration_persistence
    - final_attendance_policy_judgement
    - jwt_authentication
    - leave_approval

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

change_triggers:
  update_spec_when:
    - template_contract_changed
    - assignment_flow_changed
    - baseline_resolution_changed
    - attendance_integration_contract_changed
    - effective_schedule_query_changed
```

---

## 6. 開發與驗證流程

### 6.1 開發步驟

1. 先判斷這次改動是 template、assignment、lookup 還是 baseline export
2. 確認是否影響 `attendance` 的 consumer contract
3. 優先在既有 `service.py` / `repo.py` 路徑內落實變更
4. 不要把 schedule rule 直接塞進其他模組
5. 改完後同步回寫 `SA/modules/schedule.md`

### 6.2 最低驗證清單

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

#### Integration 驗證
- 與 `attendance` 的欄位契約一致
- contract 改動時，文件與 consumer 一起更新

---

## 7. 依賴與共用元件

### 7.1 可依賴
- `app.core.dependencies`
- `app.core.scope`
- `schedule.service`
- `schedule.repo`
- `schedule.models`
- `schedule.schemas`

### 7.2 不應承擔
- attendance punch persistence
- attendance reporting aggregation
- leave approval orchestration
- authentication token issuance

### 7.3 與其他模組的責任分界

| 模組 | `schedule` 提供什麼 | `schedule` 不做什麼 |
|---|---|---|
| `attendance` | expected work time、shift segments、normalized windows | 不做 punch write、不做最終出勤事實判定 |
| `auth` | 使用其身份 / actor 結果 | 不處理登入與 token |
| `tenants` | 使用公司與成員範圍 | 不作為 tenant source of truth |
| `leave` | 可被查詢排班背景資料 | 不處理請假審批 |

---

## 8. Do / Don’t

### Do
- 把排班模板與指派分開理解
- 把有效班表解析視為正式責任
- 保持提供給 `attendance` 的 baseline 契約穩定
- 用單一路徑處理 normalization
- contract 改變時同步更新文件

### Don’t
- 不要把 attendance policy 判定塞進 `schedule`
- 不要在 `attendance` 內重抄一份 schedule normalization 邏輯
- 不要讓 API 直接承擔過多業務協調
- 不要跨 tenant 查詢或修改班表
- 不要把 schedule 當作打卡交易寫入模組

### 最容易踩雷的錯誤
1. `schedule` 與 `attendance` 都各自維護一套排班正規化
2. assignment 邏輯和 template 語意混在一起
3. query contract 變了，但沒有同步檢查 `attendance`
4. router 直接承擔太多 business orchestration

---

## 9. 回寫規則

當發生以下任一情況，必須更新本文件：

- template 結構改變
- assignment 流程改變
- baseline resolver 改變
- 有效班表查詢契約改變
- 與 `attendance` 的整合欄位或 semantic 改變

若變更影響跨模組邊界，還要同步更新：

- `SA/modules/attendance.md`
- 必要時 `SA/modules/attendance-policy.md`
- 必要時 `SA/architecture/MODULE_BOUNDARY_MATRIX.md`

---

## 10. 已依目前 baseline 回寫的正式結論（2026-04-08）

- `schedule`（排班）是預期工作時間的 source of truth（正式權威來源）
- `attendance`（出勤）只能消費 schedule baseline，不應反向改寫 schedule 語意
- `schedule` 提供 baseline；最終遲到 / 早退 / 加班判定仍由 `attendance.policy`（出勤規則子域）負責
- 若 baseline export contract 改變，必須同步更新 `schedule` 與 `attendance` 文件及 consumer 驗證
