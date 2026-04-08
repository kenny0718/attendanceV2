# ATTENDANCE REMEDIATION STATUS TRACKER

> **Scope**: Attendance remediation governance tracking
> **Mode**: Audit-first, no Fix before Gate approval unless a documented phase closeout already exists
> **Status Legend**:
> - Not Started
> - In Progress
> - Done
> - Partial
> - Pending Decision
> - Pass / Closed
> - Blocked

---

# Tracker Table

| Phase | Ticket | Title | Type | Status | Gate Result | Output Report | Notes |
|---|---|---|---|---|---|---|---|
| P1 | A1 | Duration Write Audit | Audit | Done | N/A | `docs/attendance/remediation/01_audit/P1_A1_DURATION_WRITE_AUDIT.md` | Single writer confirmed; decision in close flow, persisted via session close transaction |
| P1 | A2 | Duration Flow Audit | Audit | Done | N/A | `docs/attendance/remediation/01_audit/P1_A2_DURATION_FLOW_AUDIT.md` | Flow confirmed: gross drives policy/reporting, net remains derived-only |
| P1 | Gate | Phase 1 Gate Review | Gate | Done | Pending Decision | `docs/attendance/remediation/00_control/P1_PHASE_GATE_REVIEW.md` | Gate material prepared; human must choose Option A vs Option B |
| P1 | F1 | First Cut — Canonical Pure Calculation Source | Fix | Done | N/A | `docs/attendance/remediation/02_fix/P1_F1_FIRST_CUT_EXECUTION_REPORT.md` | First cut completed in pure layer only; runtime semantics unchanged |
| P1 | Closeout | Phase 1 Semantic Decision | Decision | Pending Decision | N/A | `docs/attendance/remediation/00_control/P1_PHASE_GATE_REVIEW.md` | Audit + gate + first cut exist, but final semantic decision is still not closed (`gross` vs `net canonical`) |
| P2 | A1 | Taipei Boundary Audit | Audit | Done | N/A | `docs/attendance/remediation/01_audit/P2_A1_TAIPEI_BOUNDARY_AUDIT.md` | Audit completed; identified boundary ownership and HIGH-risk UTC pseudo-day issue |
| P2 | A2 | Boundary Consistency Audit | Audit | Done | N/A | `docs/attendance/remediation/01_audit/P2_A2_BOUNDARY_CONSISTENCY_AUDIT.md` | Audit completed; confirmed breaks/reporting boundary divergence |
| P2 | Closeout | Taipei Business-Date Boundary Alignment | Phase Closeout | Pass / Closed | PASS | `docs/attendance/remediation/00_control/P2_PHASE_FINAL_SUMMARY.md` | Phase 2 final summary records F1/F2/F3 complete and overall result PASS |
| PE | GOV | Policy Engine Governance | Governance | Done | N/A | `docs/attendance/architecture/POLICY_ENGINE_GOVERNANCE.md` | Governance boundary established; `policy_engine.py` fixed as orchestration façade |
| PE | FREEZE | Policy Engine Freeze | Freeze | Done | N/A | `docs/attendance/architecture/POLICY_ENGINE_FREEZE.md` | Active freeze established; three-cut remediation closed for current governance round |
| P3 | A1 | Breaks Layer Audit | Audit | Not Started | N/A | `docs/attendance/remediation/01_audit/P3_A1_BREAKS_LAYER_AUDIT.md` | Audit API/service/repo responsibility leakage |
| P3 | A2 | Breaks DB Write Audit | Audit | Not Started | N/A | `docs/attendance/remediation/01_audit/P3_A2_BREAKS_DB_WRITE_AUDIT.md` | Audit breaks write-path concentration |
| P4 | A1 | Reporting Growth Audit | Audit | Not Started | N/A | `docs/attendance/remediation/01_audit/P4_A1_REPORTING_GROWTH_AUDIT.md` | Audit reporting growth boundary only |
| P5 | A1 | Legacy/New Flow Coupling Audit | Audit | Not Started | N/A | `docs/attendance/remediation/01_audit/P5_A1_LEGACY_NEW_FLOW_COUPLING_AUDIT.md` | Audit coupling and protected core files |

---

# Governance Rules

1. 本輪 remediation 仍以 Audit / Gate 驅動，不可把未完成 phase 自動視為已修復。
2. 只有在已有正式 closeout 文件時，tracker 才可標記為 `Pass / Closed`。
3. `Gate Result` 只有在文件已明確給出結果時，才可從 `N/A` 更新為具體值。
4. 若任一 Audit 發現 STOP GATE 觸發條件，Status 必須更新為 `Blocked`。
5. Policy Engine 相關後續工作必須先遵守：
   - `docs/attendance/architecture/POLICY_ENGINE_GOVERNANCE.md`
   - `docs/attendance/architecture/POLICY_ENGINE_FREEZE.md`

---

# Current Status Summary

## What is already closed
- Phase 2 boundary alignment 已有正式 closeout，結果為 **PASS**。
- Policy Engine governance 已完成。
- Policy Engine freeze 已完成，且目前處於 active freeze 狀態。

## What is not fully closed yet
- Phase 1 不是未開始，但也**尚未最終結案**。
- Phase 1 目前已完成：
   - `P1_A1`
   - `P1_A2`
  - `P1` gate review material
  - `P1_F1` first cut
- 但 final semantic decision 仍待人工決策：
  - Option A = 維持 `gross`
  - Option B = 切換為 `net canonical`

## Remaining open work
- `P3_A1` = Not Started
- `P3_A2` = Not Started
- `P4_A1` = Not Started
- `P5_A1` = Not Started

---

# Current Execution Decision

## Active Next Items
1. Human decision for Phase 1 semantic closeout (`Option A` / `Option B`)
2. Run remaining audits in controlled order:
   - `P3_A1`
   - `P3_A2`
   - `P4_A1`
   - `P5_A1`

## Overall Remediation State
- Policy Engine governance round: **Closed**
- Phase 2: **Pass / Closed**
- Phase 1: **Partial / Pending Decision**
- Phase 3 / 4 / 5: **Not Started**
- Overall attendance remediation: **Not Fully Closed**
