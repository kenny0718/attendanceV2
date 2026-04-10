Title: Attendance Policy Spec
Author: Johnny Lee
Version: 1.0
Date Created: 2026-04-08
Last Modified: 2026-04-08
spec:id: attendance.policy.v1
status: active
module: attendance
subdomain: policy
source_of_truth: SA/modules/attendance-policy.md
related_code_paths:
  - backend/app/modules/attendance/policy_engine.py
  - backend/app/modules/attendance/policy_rules.py
  - backend/app/modules/attendance/policy_missing_segment.py
  - backend/app/modules/attendance/policy_schedule_support.py
  - backend/app/modules/attendance/policy_schedule_models.py
  - backend/app/modules/attendance/work_hour_engine.py
  - backend/app/modules/attendance/punch_close_domain.py
---

# Attendance Policy 開發規格

> 本文件定義 `attendance` 模組中所有「規則計算與語意保護」流程的正式規格。  
> 只要你要改的是遲到 / 早退 / 加班判定、schedule-aware 評估、work hour 計算、missing segment、canonical semantic 或 policy remediation，就應先讀這份。

---

## 1. 文件定位

### 1.1 這份文件是給誰看的

- 你未來要修改 attendance 規則與語意時
- 協助你開發 policy 能力的 AI
- 要 review canonical contract、schedule-aware、close-flow 風險的人

### 1.2 什麼情況要先看這份

- 你要改遲到 / 早退 / 加班判定
- 你要改 schedule-aware evaluation
- 你要改 work hour 計算
- 你要改 missing segment 規則
- 你要改 canonical semantic
- 你要評估 `P6_F5` / `P6_F6` / `P6_F11` / `P6_F12`

### 1.3 它和其他文件的關係

- 主模組總覽：`SA/modules/attendance.md`
- 交易寫入規格：`SA/modules/attendance-capture.md`
- 唯讀報表規格：`SA/modules/attendance-reporting.md`
- 模板來源：`SA/governance/MODULE_SPEC_TEMPLATE.md`
- 風險追蹤：`SA/SDD_PROGRESS_TRACKER.md`

---

## 2. 目的與範圍

### 2.1 本文件負責的範圍

`attendance.policy` 的責任是：

- 根據 session 與 policy 算出遲到 / 早退 / 加班
- 根據 schedule baseline 做 schedule-aware 判定
- 處理 work hour 純計算
- 處理 missing segment 規則
- 保護 canonical semantic 不被 derived 值污染
- 定義高風險 policy remediation 的正式邊界

### 2.2 本文件不負責的範圍

這份文件不處理：

- 主要 DB 寫入落地
- punch / break / checkpoint 交易寫入
- reporting 聚合與報表 response shaping
- schedule 作為 source of truth 的主資料管理
- 任意把 derived 值寫回 persistence

### 2.3 一句話理解

> policy 子域只負責「怎麼算、怎麼判斷、哪些語意不能被破壞」。

---

## 3. 核心原則

| 原則 | 定義 | 可驗證條件 |
|---|---|---|
| Canonical = Gross | `session.duration_minutes` 是 canonical persisted duration，且語意為 gross | 不可把 derived `work_minutes` / `net_work_minutes` 寫回 canonical |
| Break Deduction Derived Only | break deduction 可以算、可以顯示，但不能寫回 canonical | deduction 只存在 evaluation / display payload |
| Reporting Consumer Only | reporting 只能讀 canonical，不可反過來改 semantic | reporting 只讀 `duration_minutes` |
| Schedule Provides Baseline | `schedule` 提供 baseline，policy 只負責依 baseline 判定 | policy 不成為 schedule source of truth |
| Expansion Stop on High-Risk Engine | `policy_engine.py` 是高風險核心檔，不應繼續吸責任 | 新需求優先在既有分層內落地 |
| Derived Does Not Become Persisted Truth | derived 值不可變成 persistence owner | 所有 persistence path 均維持 canonical contract |

---

## 4. 功能規格

### 4.1 Standard Policy Evaluation

**用途**：在一般情況下判斷是否遲到、早退、加班。  
**主要檔案**：`policy_engine.py`, `policy_rules.py`

**必要行為**：
- 根據 session 與 policy 進行標準判定
- 不改寫 canonical persistence contract

### 4.2 Schedule-aware Evaluation

**用途**：當 session 需要參考排班基準時，使用 normalized windows 做判定。  
**主要檔案**：`policy_schedule_support.py`, `policy_schedule_models.py`, `policy_engine.py`

**必要行為**：
- 使用 schedule 提供的 baseline
- 不把 schedule 主責任拉進 attendance
- 不讓 derived work minutes 污染 canonical duration

### 4.3 Work Hour Calculation

**用途**：計算工時、分鐘數與其他衍生值。  
**主要檔案**：`work_hour_engine.py`

**必要行為**：
- 產生 pure calculation 結果
- 區分 canonical 與 derived 欄位

### 4.4 Missing Segment Rules

**用途**：處理缺段、異常或 dry-run 類規則。  
**主要檔案**：`policy_missing_segment.py`

**必要行為**：
- 缺段判定應維持獨立規則責任
- 不用報表補救 missing-segment semantic

### 4.5 Close-flow Policy Adapter

**用途**：在 close flow 附近套用 policy evaluation，並保護 canonical write contract。  
**主要檔案**：`punch_close_domain.py`, `policy_engine.py`

**必要行為**：
- 保持 close-flow owner 邊界清楚
- 維持 `duration_minutes = gross_minutes`

---

## 5. Formalized Semantic Block

```yaml
scope:
  module: attendance
  subdomain: policy
  responsibility:
    - late_early_overtime_evaluation
    - schedule_aware_evaluation
    - work_hour_calculation
    - missing_segment_rules
    - canonical_semantic_guard
    - close_flow_policy_adapter
  non_responsibility:
    - punch_write
    - session_persistence_ownership
    - reporting_aggregation
    - schedule_source_of_truth
    - arbitrary_derived_writeback

contracts:
  canonical_contract:
    canonical_field: session.duration_minutes
    canonical_semantic: gross
    derived_fields:
      - work_minutes
      - net_work_minutes
      - deduction_result.net_work_minutes
  break_deduction:
    derived_only: true
    writeback_to_canonical: false
  reporting_relation:
    reporting_is_canonical_consumer_only: true
  schedule_relation:
    schedule_provides_baseline: true
    policy_can_override_schedule_semantic: false
  write_authority:
    policy_is_not_primary_persistence_owner: true

validation_rules:
  - rule: canonical_never_derived
    description: derived work minutes 不可寫回 canonical duration
    verification: regression test guards duration_minutes remains gross
  - rule: live_punch_out_keeps_gross
    description: live punch-out canonical write 必須維持 gross_minutes
    verification: close_session receives gross_minutes in live path
  - rule: reporting_reads_canonical_only
    description: reporting 只讀 canonical duration_minutes
    verification: reporting smoke passes with canonical unchanged
  - rule: no_second_persistence_path
    description: 不應存在第二條 session.duration_minutes persistence path
    verification: repo-level inventory confirms only allowed write path

change_triggers:
  update_spec_when:
    - policy_rules_changed
    - schedule_aware_logic_changed
    - canonical_contract_changed
    - close_flow_owner_changed
    - remediation_status_changed
```

---

## 6. 開發與驗證流程

### 6.1 開發步驟

1. 先判斷你改的是 pure rule、schedule-aware、close-flow adapter，還是 canonical semantic guard
2. 若有碰到 persistence contract，先同步讀 `attendance-capture.md`
3. 若有碰到 reporting consumer，先同步讀 `attendance-reporting.md`
4. 高風險改動不要直接把責任塞進 `policy_engine.py`
5. 改完後同步回寫本文件、主模組文件與 tracker

### 6.2 最低驗證清單

#### Standard Policy 驗證
- 遲到 / 早退 / 加班規則仍正確
- pure rule 不污染 persistence contract

#### Schedule-aware 驗證
- 依 schedule baseline 正確判定
- 不把 schedule semantic 拉進 attendance 重建
- `work_minutes` 不寫回 `duration_minutes`

#### Canonical Guard 驗證
- canonical persisted duration 維持 gross semantic
- regression test 可防止 derived 覆寫 canonical
- repo-level inventory 無第二條 duration write 路徑

#### Reporting Relation 驗證
- reporting smoke 只讀 canonical `duration_minutes`
- 報表聚合未因 policy 改動而語意漂移

---

## 7. 依賴與共用元件

### 7.1 可依賴
- `attendance.policy_engine`
- `attendance.policy_rules`
- `attendance.policy_missing_segment`
- `attendance.policy_schedule_support`
- `attendance.policy_schedule_models`
- `attendance.work_hour_engine`
- `attendance.punch_close_domain`
- `schedule` 提供的 baseline

### 7.2 不應承擔
- attendance write persistence owner
- reporting view model owner
- schedule source-of-truth owner
- frontend semantic correction

### 7.3 共用元件

| 元件 | 功能 | 強制性 |
|---|---|---|
| `policy_engine.py` | 政策 façade / orchestration | ✅ |
| `policy_rules.py` | 細部 late / early / overtime 規則 | ✅ |
| `work_hour_engine.py` | 工時計算 | ✅ |
| `punch_close_domain.py` | close-flow policy adapter | 高風險修改時必看 |
| `SA/SDD_PROGRESS_TRACKER.md` | remediation / risk status | 高風險改動時必看 |

---

## 8. Do / Don’t

### Do
- 保護 canonical = gross 的正式基線
- 把 break deduction 維持為 derived only
- 讓 schedule 提供 baseline、policy 做判定
- 高風險改動時同步檢查 tracker 與 close-flow
- 補 regression 與 smoke 驗證

### Don’t
- 不要把 `work_minutes` / `net_work_minutes` 寫回 canonical
- 不要把 schedule 主責任拉進 attendance
- 不要讓 `policy_engine.py` 再吸收更多歷史責任
- 不要把 reporting 當補救 transaction semantic 的地方
- 不要只改文件就宣告 remediation 完成

### 最容易踩雷的錯誤
1. 把 derived 分鐘數當 canonical persisted duration
2. 在 schedule-aware helper 裡偷偷改寫 canonical
3. 讓 `policy_engine.py` 越改越胖
4. 忘記同步檢查 reporting canonical consumer

---

## 9. 回寫規則

當發生以下任一情況，必須更新本文件：

- late / early / overtime 規則改變
- schedule-aware evaluation 改變
- canonical semantic 改變
- close-flow owner 邊界改變
- remediation 判定或 tracker 狀態改變
- repo-level canonical write inventory 改變

若變更影響跨子域或跨模組邊界，還要同步更新：

- `SA/modules/attendance.md`
- `SA/modules/attendance-capture.md`
- `SA/modules/attendance-reporting.md`
- `SA/SDD_PROGRESS_TRACKER.md`
- 必要時 `SA/architecture/MODULE_BOUNDARY_MATRIX.md`

---

## 10. 已依目前 baseline 回寫的正式結論（2026-04-08）

- `attendance.policy` 是規則判斷與語意保護層，不是任意 persistence owner
- `schedule` 提供 baseline，`attendance.policy` 依 baseline 進行規則判定
- `canonical = gross`、`break deduction = derived only`、`reporting = canonical consumer only` 是不可破壞正式基線
- `P6_F6` 的 dormant schedule-aware helper 已完成 canonical guard 修補，且已有 targeted regression 與 reporting smoke
- 主 `punch-out` live path 目前仍走 gross canonical write
- `approve/pending` 後重算 owner 尚未盤出正式 attendance policy 重算路徑；此議題應改追 `R-APPROVE-PENDING-OWNER-INVENTORY`

---

## 11. Remediation SDD Blocks（供後續 AI / 人工依規格修正）

### R-F6-SCHEDULE-AWARE-CANONICAL-GUARD

#### 1. 問題定義
schedule-aware dormant helper 曾存在將 derived `work_minutes` 寫入 `session.duration_minutes` 的風險，會直接破壞 canonical semantic。

#### 2. 正式 owner
- 模組：`attendance`
- 子域：`attendance.policy`
- 核心檔案：`punch_close_domain.py`、`work_hour_engine.py`、`policy_engine.py`
- 關聯檔案：`api/punch.py`、`repo.py`、`attendance_punch_repo.py`
- 文件檔案：`SA/modules/attendance-policy.md`

#### 3. 完成條件
- canonical drift 寫入點已移除
- `session.duration_minutes` 維持 canonical gross semantic
- regression test 防止 `work_minutes` 再寫回 canonical
- reporting smoke 確認 canonical consumer 未被污染
- 最小 repo-level inventory 已完成
- tracker 與文件已同步回寫

#### 4. 驗證條件
- targeted regression test 通過
- reporting smoke 通過
- 無新的 `work_minutes -> duration_minutes` 寫入路徑
- live path canonical write 仍為 `gross_minutes`

#### 5. 文件回寫清單
- `SA/modules/attendance-policy.md`
- `SA/modules/attendance.md`
- `SA/SDD_PROGRESS_TRACKER.md`
