# P1 Semantic Decision — Final (Closeout)

> **Document Type**: Final Semantic Decision / Source of Truth  
> **Phase**: P1 Closeout  
> **Decision Status**: FINAL  
> **Decision Authority**: Attendance remediation governance  
> **Scope**: Attendance canonical duration semantics  
> **Last Updated**: 2026-04-07

---

## 1. Executive Summary

The Attendance system canonical duration semantic is formally fixed to **Option A: gross canonical**.

Canonical duration is defined as the gross elapsed minutes between `punch_in` and `punch_out`, persisted in `session.duration_minutes`.

`break deduction`, `net work minutes`, and all break-adjusted metrics are **derived values only**. They are not canonical, must not replace canonical duration, and must not redefine the meaning of `session.duration_minutes`.

This document is the formal semantic source of truth for all future Attendance work involving policy, reporting, close-flow orchestration, and downstream duration consumers.

---

## 2. Canonical Definition（唯一來源）

The canonical duration field in the Attendance system is defined as:

- **Canonical field**: `session.duration_minutes`
- **Canonical semantic**: **gross minutes**
- **Canonical formula**: `punch_out - punch_in`
- **Break treatment**: **no break deduction is applied to the canonical value**

Formal definition:

- `session.duration_minutes` **is defined as** the gross elapsed minutes from session open to session close.
- `session.duration_minutes` **must not** subtract break minutes.
- `session.duration_minutes` **must not** be reinterpreted as net work minutes.

For avoidance of doubt:

- gross minutes = elapsed session minutes before break deduction
- net minutes = gross minutes minus validated break deduction
- only gross minutes are canonical

---

## 3. Canonical Ownership

Canonical ownership is fixed as follows:

- **Owner**: punch-out close-flow orchestration
- **Calculation source**: `work_hour_engine`
- **Repository role**: persistence only
- **Policy role**: consumer only
- **Reporting role**: consumer only

The ownership contract is normative:

1. The punch-out close-flow orchestration **owns the canonical duration decision**.
2. `work_hour_engine` **may provide calculation capability**, but it **is not the canonical owner**.
3. The repository layer **must only persist the canonical value provided to it**.
4. Policy evaluation **must consume canonical duration** and **must not redefine it**.
5. Reporting and summary logic **must consume canonical duration** and **must not redefine it**.

This means:

- ownership belongs to the close-flow orchestration boundary
- calculation support may exist below that boundary
- persistence and downstream readers do not own semantic authority

---

## 4. Allowed vs Forbidden Semantics

### Allowed

The following semantics are allowed and are formally approved:

- gross minutes as the **only canonical duration**
- net minutes as a **derived value only**
- break deduction as a **derived value only**
- reporting display of derived values, provided canonical duration is not overwritten
- policy consumption of canonical duration without redefining its meaning
- summary consumption of canonical duration without recalculation of canonical meaning

### Forbidden

The following semantics and behaviors are forbidden:

- using net minutes to overwrite `session.duration_minutes`
- redefining canonical duration inside policy logic
- redefining canonical duration inside reporting logic
- allowing the repository layer to decide work-duration semantics
- writing break deduction back into the canonical DB field
- treating break-adjusted duration as canonical without a new formal decision phase
- mixing gross and net semantics under the same `session.duration_minutes` contract

The Attendance system **must not** operate with mixed canonical semantics.

---

## 5. Derived Values Policy

The following values are defined as **derived only**:

- `net_work_minutes`
- break-adjusted duration
- future overtime metrics
- future leave-related duration metrics
- future missing-segment-related duration metrics
- any future duration variant produced from canonical duration plus additional rules

Derived-value policy is fixed as follows:

1. Derived values **must remain derived**.
2. Derived values **must not be promoted to canonical**.
3. Derived values **must not overwrite** `session.duration_minutes`.
4. Derived values **must not silently inherit canonical authority** through naming, reporting, or persistence.
5. Any future metric derived from gross canonical duration **must preserve the gross canonical source unchanged**.

No derived metric has authority to replace the canonical field.

---

## 6. Reporting Contract

Reporting is governed by the following contract:

1. Reporting **must directly use** canonical duration from `session.duration_minutes` when referencing canonical duration.
2. Summary logic **must not recalculate canonical duration** from raw punches, break punches, or alternative formulas.
3. Reporting **must not reinterpret** canonical duration as net duration.
4. Derived values, if shown, **must be presented in separate fields or separate columns** from canonical duration.
5. Reporting totals that represent canonical duration **must aggregate the persisted canonical field**.

Therefore:

- canonical duration in reporting = persisted gross duration
- derived duration in reporting = separately labeled non-canonical metric
- canonical and derived values must not be merged into one semantic field

---

## 7. Break Deduction Rule

Break deduction is governed by the following rule:

- break deduction is **supplemental information only**
- break deduction **must not affect canonical duration**
- break deduction **must not be written back** to `session.duration_minutes`

Normative statements:

1. Break deduction **is not** part of canonical persistence.
2. Break deduction **must remain** an attached or downstream computation.
3. Break deduction results **may inform derived outputs**.
4. Break deduction results **must not redefine** gross canonical duration.

The system contract is explicit:

- canonical persists gross
- break deduction derives net
- derived net does not mutate canonical gross

---

## 8. Future Change Policy（非常重要）

If the Attendance system is ever changed from **Option A: gross canonical** to **Option B: net canonical**, the following process is mandatory:

1. A **new formal decision phase must be opened**.
2. The semantic change **must not** be introduced inside ordinary feature development.
3. The semantic change **must not** be hidden inside implementation details, refactors, reporting updates, or policy updates.
4. A new audit set **must** be executed for:
   - policy consumers
   - reporting consumers
   - DB field contract
   - historical data interpretation
   - close-flow ownership and persistence contract
5. A new explicit migration and compatibility decision **must** be documented before execution.

No feature ticket, bug-fix ticket, or reporting ticket has authority to silently switch canonical semantics from gross to net.

---

## 9. Compatibility with Policy Engine Freeze

This semantic decision is compatible with `POLICY_ENGINE_FREEZE.md`.

Compatibility is defined as follows:

1. `POLICY_ENGINE_FREEZE.md` protects responsibility boundaries and prevents `policy_engine.py` from regaining non-façade responsibilities.
2. The freeze document does **not** define canonical duration semantics.
3. This document defines the canonical duration semantic source of truth.
4. Policy engine governance and freeze rules remain fully active.
5. Policy modules are consumers of canonical semantics defined here and **must not** replace this decision.

Therefore:

- freeze governs responsibility containment
- this document governs duration meaning
- the two documents are complementary and non-conflicting

---

## 10. Known Drift / Tech Debt（來自 P1 Report）

The following semantic or structural drift items are formally recorded as known tech debt. They are listed for governance visibility only and are not resolved by this document:

- `work_hour_engine` ownership commentary is not fully consistent with formal canonical ownership
- `canonical_minutes` naming creates semantic risk if used to imply net authority or alternate canonical meaning
- `punch_close_flow` vs `punch_close_domain` naming shows boundary drift risk
- reporting currently depends completely on canonical persistence and therefore has direct exposure to canonical semantic changes

These items are recorded only.

No remediation is authorized by this document.

---

## 11. Decision Statement（可引用）

Canonical duration in the Attendance system is defined as gross minutes persisted in `session.duration_minutes`. Gross minutes are calculated as the elapsed duration from `punch_in` to `punch_out` without break deduction. This field is the single canonical duration source for downstream policy and reporting consumers. Break deduction, net work minutes, and all break-adjusted or rule-adjusted duration metrics are derived values only and must not overwrite, replace, or redefine `session.duration_minutes`. Any future change from gross canonical semantics to net canonical semantics requires a new formal decision phase, fresh audit coverage across policy, reporting, and DB contracts, and explicit migration governance. Semantic drift between gross and net duration under the same canonical field is forbidden.
