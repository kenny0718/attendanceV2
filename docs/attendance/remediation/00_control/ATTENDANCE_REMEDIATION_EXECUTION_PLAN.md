# ATTENDANCE REMEDIATION EXECUTION PLAN

> **Document Type**: Controlled Execution Plan
> **Mode**: Audit-Only Initialization Round
> **Execution Rule**: Do not perform Fix in this round
> **Mandatory Pattern**: One ticket at a time

---

# 0. Plan Purpose

本文件用於定義 Attendance remediation 後續工作的**工作定義拆解方式**。

本文件不是修正指南。
本文件只定義：
- 票怎麼拆
- 順序怎麼跑
- 報告放哪裡
- 哪些票屬 Audit
- 哪些票未來才可能進 Gate / Fix

---

# 1. Directory Rules

固定目錄如下：

```text
/docs/attendance/remediation/
├─ 00_control/
├─ 01_audit/
├─ 02_fix/
└─ 03_status/
```

## 00_control
放治理與總控文件：
- `ATTENDANCE_REMEDIATION_GOVERNANCE_CONTROL.md`
- `ATTENDANCE_REMEDIATION_EXECUTION_PLAN.md`

## 01_audit
放所有 Audit 報告：
- `P1_A1_DURATION_WRITE_AUDIT.md`
- `P1_A2_DURATION_FLOW_AUDIT.md`
- `P2_A1_TAIPEI_BOUNDARY_AUDIT.md`
- `P2_A2_BOUNDARY_CONSISTENCY_AUDIT.md`
- `P3_A1_BREAKS_LAYER_AUDIT.md`
- `P3_A2_BREAKS_DB_WRITE_AUDIT.md`
- `P4_A1_REPORTING_GROWTH_AUDIT.md`
- `P5_A1_LEGACY_NEW_FLOW_COUPLING_AUDIT.md`

## 02_fix
本輪不得使用。
僅未來人工判定可進 Gate/Fix 後，才可放 execution report。

## 03_status
放總追蹤表：
- `ATTENDANCE_REMEDIATION_STATUS_TRACKER.md`

---

# 2. Naming Rules

## Audit Reports
格式：
- `P{Phase}_A{Ticket}_{NAME}_AUDIT.md`

## Fix Reports
格式：
- `P{Phase}_F{Ticket}_{NAME}_EXECUTION_REPORT.md`

## Status Tracker
固定：
- `ATTENDANCE_REMEDIATION_STATUS_TRACKER.md`

---

# 3. Ticket Set for Current Audit Round

## Phase 1
- `P1_A1` Duration Write Audit
- `P1_A2` Duration Flow Audit

## Phase 2
- `P2_A1` Taipei Boundary Audit
- `P2_A2` Boundary Consistency Audit

## Phase 3
- `P3_A1` Breaks Layer Audit
- `P3_A2` Breaks DB Write Audit

## Phase 4
- `P4_A1` Reporting Growth Audit

## Phase 5
- `P5_A1` Legacy/New Flow Coupling Audit

---

# 4. Mandatory Execution Order

本輪建議嚴格採以下順序：

1. `P1_A1`
2. `P1_A2`
3. `P2_A1`
4. `P2_A2`
5. `P3_A1`
6. `P3_A2`
7. `P4_A1`
8. `P5_A1`

但治理上，實際執行必須採：

- 一次只跑一張票
- 跑完一張就停
- 將報告交由人工判讀
- 判定是否值得繼續下一張

因此當前允許的唯一下一步為：

## Current Allowed Next Step
- Run `P1_A1 Duration Write Audit` only

---

# 5. Ticket Templates

每一張 Audit 票都必須至少包含：

1. Goal
2. Context
3. Scope
4. Search Targets
5. Evidence Requirements
6. Output File
7. Prohibited Actions
8. Audit Result
9. Risk Level
10. Open Questions
11. Gate Recommendation

---

# 6. Current Round Rule

本輪為 **Audit-Only Round**。

禁止：
- 修改 backend code
- 修改 frontend code
- 新增 fix diff
- 預先產出 execution report
- 自行把 Audit 結論升級為可進 Fix

允許：
- 建立 docs 結構
- 建立控制文件
- 建立 status tracker
- 執行單張 Audit
- 產出單張 Audit 報告

---

# 7. Human Review Rule

每一張 Audit 報告產出後，應由人工判讀以下事項：

1. 這張票是否成立
2. 是否能進 Gate
3. 是否需要開下一張 Audit
4. 是否值得未來進 Fix

未經人工判讀：
- 不得改 tracker 為可進 Fix
- 不得產生 `02_fix/` 文件

---

# 8. Immediate Action

目前 Step 1 完成後，唯一應執行的下一步為：

- 建立並執行 `P1_A1 Duration Write Audit`
- 將 Audit 報告交由人工判讀
- 停止，等待下一指示
