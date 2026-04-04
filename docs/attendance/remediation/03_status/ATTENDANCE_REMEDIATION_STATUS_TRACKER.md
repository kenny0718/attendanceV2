# ATTENDANCE REMEDIATION STATUS TRACKER

> **Scope**: Attendance remediation governance tracking
> **Mode**: Audit-first, no Fix before Gate approval
> **Status Legend**:
> - Not Started
> - In Progress
> - Done
> - Blocked

---

# Tracker Table

| Phase | Ticket | Title | Type | Status | Gate Result | Output Report | Notes |
|---|---|---|---|---|---|---|---|
| P1 | A1 | Duration Write Audit | Audit | Done | N/A | `docs/attendance/remediation/01_audit/P1_A1_DURATION_WRITE_AUDIT.md` | Single writer confirmed; decision in close flow, persisted via session close transaction |
| P1 | A2 | Duration Flow Audit | Audit | Done | N/A | `docs/attendance/remediation/01_audit/P1_A2_DURATION_FLOW_AUDIT.md` | Flow confirmed: gross drives policy/reporting, net remains derived-only |
| P2 | A1 | Taipei Boundary Audit | Audit | Not Started | N/A | `docs/attendance/remediation/01_audit/P2_A1_TAIPEI_BOUNDARY_AUDIT.md` | Audit all business-day timezone handling |
| P2 | A2 | Boundary Consistency Audit | Audit | Not Started | N/A | `docs/attendance/remediation/01_audit/P2_A2_BOUNDARY_CONSISTENCY_AUDIT.md` | Compare endpoint/query boundary consistency |
| P3 | A1 | Breaks Layer Audit | Audit | Not Started | N/A | `docs/attendance/remediation/01_audit/P3_A1_BREAKS_LAYER_AUDIT.md` | Audit API/service/repo responsibility leakage |
| P3 | A2 | Breaks DB Write Audit | Audit | Not Started | N/A | `docs/attendance/remediation/01_audit/P3_A2_BREAKS_DB_WRITE_AUDIT.md` | Audit breaks write-path concentration |
| P4 | A1 | Reporting Growth Audit | Audit | Not Started | N/A | `docs/attendance/remediation/01_audit/P4_A1_REPORTING_GROWTH_AUDIT.md` | Audit reporting growth boundary only |
| P5 | A1 | Legacy/New Flow Coupling Audit | Audit | Not Started | N/A | `docs/attendance/remediation/01_audit/P5_A1_LEGACY_NEW_FLOW_COUPLING_AUDIT.md` | Audit coupling and protected core files |

---

# Governance Rules

1. 本輪只允許 Audit 票，不允許直接進 Fix。
2. 任一 Audit 未經人工判讀前，不得自動開 Fix 票。
3. Gate Result 只有在人工判讀後才可從 `N/A` 更新為 `YES` 或 `NO`。
4. 若任一 Audit 發現 STOP GATE 觸發條件，Status 必須更新為 `Blocked`。
5. 建議執行順序：
   - `P1_A1`
   - `P1_A2`
   - `P2_A1`
   - `P2_A2`
   - `P3_A1`
   - `P3_A2`
   - `P4_A1`
   - `P5_A1`

---

# Current Execution Decision

## Active Next Ticket
- Human Gate Review for Phase 1 (`P1_A1` + `P1_A2`)

## Current Phase State
- `P1_A1` 已完成 Audit
- `P1_A2` 已完成 Audit
- Phase 1 可進入人工 Gate 判讀
- 禁止直接進入 Fix
