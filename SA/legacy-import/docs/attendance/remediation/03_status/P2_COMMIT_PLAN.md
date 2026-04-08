# P2 Commit Plan — Final Closeout Grouping

> **Document Type**: Commit Plan  
> **Phase**: 2 — Taipei Business-Date Boundary Alignment  
> **Purpose**: Define concrete, file-level commit grouping options for Phase 2 closeout  
> **Execution Mode**: Planning / governance only  
> **Status**: Ready for operator use  
> **Inputs**:
> - `docs/attendance/remediation/00_control/P2_PHASE_FINAL_SUMMARY.md`
> - `docs/attendance/remediation/02_fix/P2_BOUNDARY_FIX_SPEC.md`
> - `docs/attendance/remediation/02_fix/P2_F1_EXECUTION_REPORT.md`
> - `docs/attendance/remediation/02_fix/P2_F2_EXECUTION_REPORT.md`
> - `docs/attendance/remediation/02_fix/P2_F3_FIX_SPEC.md`
> - `docs/attendance/remediation/02_fix/P2_F3_BASELINE.md`
> - `docs/attendance/remediation/02_fix/P2_F3_BLOCKER_REPORT.md`
> - `backend/app/modules/attendance/api/reporting_helpers.py`
> - `backend/app/modules/attendance/api/breaks.py`
> - `backend/app/modules/attendance/api/reporting.py`
> - `backend/app/modules/attendance/tests/test_reporting_helpers_boundary.py`
> - `backend/app/modules/attendance/tests/test_break_punches_boundary.py`
> - `backend/app/modules/attendance/tests/test_reporting_sessions.py`
> - `backend/app/main.py`
> **Last Updated**: 2026-04-06

---

# 0. Purpose

本文件提供 Phase 2 收尾時的具體 commit grouping 計畫，目標是：

- 降低治理風險
- 保持 before / after 因果清楚
- 讓 boundary owner、breaks 接線、reporting 接線、runtime unblock、治理文件可被獨立審閱
- 讓 operator 可依穩定度需求選擇「完整收法」或「精簡收法」

本文件只定義 commit plan，**不執行 commit**。

---

# 1. Commit Planning Principles

Phase 2 的 commit 分組必須遵守下列原則：

1. boundary owner 建立（F1）應與 runtime 接線（F2 / F3）分開
2. breaks 對齊與 reporting 對齊應可獨立審閱
3. `backend/app/main.py` 的 runtime unblock 應獨立成票，不與 boundary logic 混在一起
4. execution / baseline / blocker / final summary 文件應盡量與對應 code 票配對
5. 若需精簡提交，至少仍須保留：
   - boundary owner code
   - breaks / reporting 接線 code
   - `main.py` runtime unblock
   - 最核心治理文件

---

# 2. Candidate File Inventory

本 Phase 2 涉及的主要檔案如下。

## 2.1 Code Files

- `backend/app/modules/attendance/api/reporting_helpers.py`
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/main.py`

## 2.2 Test Files

- `backend/app/modules/attendance/tests/test_reporting_helpers_boundary.py`
- `backend/app/modules/attendance/tests/test_break_punches_boundary.py`
- `backend/app/modules/attendance/tests/test_reporting_sessions.py`
- `backend/app/modules/attendance/tests/test_reporting_user_summary.py`
- `backend/app/modules/attendance/tests/test_reporting_company_summary.py`

## 2.3 Governance / Fix Spec / Baseline Files

- `docs/attendance/remediation/02_fix/P2_BOUNDARY_FIX_SPEC.md`
- `docs/attendance/remediation/02_fix/P2_F1_EXECUTION_REPORT.md`
- `docs/attendance/remediation/02_fix/P2_F2_EXECUTION_REPORT.md`
- `docs/attendance/remediation/02_fix/P2_F3_FIX_SPEC.md`
- `docs/attendance/remediation/02_fix/P2_F3_BASELINE.md`
- `docs/attendance/remediation/02_fix/P2_F3_BLOCKER_REPORT.md`
- `docs/attendance/remediation/00_control/P2_PHASE_FINAL_SUMMARY.md`
- `docs/attendance/remediation/03_status/P2_COMMIT_PLAN.md`

---

# 3. Version A — 最穩定版（文件 + code 一起收）

本版本適用於：

- 需要最清楚審閱軌跡
- 需要讓每一刀 code 都有對應治理文件
- 需要將 runtime unblock 與 boundary alignment 完全分離

## A1. Commit 1 — F1 owner only

### Include files
- `backend/app/modules/attendance/api/reporting_helpers.py`
- `backend/app/modules/attendance/tests/test_reporting_helpers_boundary.py`
- `docs/attendance/remediation/02_fix/P2_BOUNDARY_FIX_SPEC.md`
- `docs/attendance/remediation/02_fix/P2_F1_EXECUTION_REPORT.md`

### Recommended message
```text
feat(attendance): add canonical Taipei business-date boundary owner
```

### Rationale
此 commit 只建立 owner，不接入 runtime route，可獨立審閱為 pure/helper contract 票。

---

## A2. Commit 2 — F2 breaks alignment

### Include files
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/tests/test_break_punches_boundary.py`
- `docs/attendance/remediation/02_fix/P2_F2_EXECUTION_REPORT.md`

### Recommended message
```text
fix(attendance): align break-punches with Taipei boundary owner
```

### Rationale
此 commit 只處理 breaks 對齊，不混入 reporting。

---

## A3. Commit 3 — F3 reporting alignment

### Include files
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/tests/test_reporting_sessions.py`
- `backend/app/modules/attendance/tests/test_reporting_user_summary.py`
- `backend/app/modules/attendance/tests/test_reporting_company_summary.py`
- `docs/attendance/remediation/02_fix/P2_F3_FIX_SPEC.md`
- `docs/attendance/remediation/02_fix/P2_F3_BASELINE.md`

### Recommended message
```text
fix(attendance): align reporting entrypoints with Taipei boundary owner
```

### Rationale
此 commit 專注 reporting boundary owner 對齊與其對應 baseline / spec。

---

## A4. Commit 4 — runtime unblock and validation governance

### Include files
- `backend/app/main.py`
- `docs/attendance/remediation/02_fix/P2_F3_BLOCKER_REPORT.md`

### Recommended message
```text
fix(app): restore main entry importability for Phase 2 validation
```

### Rationale
此 commit 應獨立，因為它不是 boundary logic 票，而是 runtime / validation unblock 票。

---

## A5. Commit 5 — Phase closeout governance

### Include files
- `docs/attendance/remediation/00_control/P2_PHASE_FINAL_SUMMARY.md`
- `docs/attendance/remediation/03_status/P2_COMMIT_PLAN.md`

### Recommended message
```text
docs(remediation): finalize Phase 2 boundary alignment closeout
```

### Rationale
此 commit 僅作為 Phase 2 治理收尾，不與產品 code 混在一起。

---

# 4. Version B — 精簡版（只收必要 code + 核心文件）

本版本適用於：

- 需要較少 commit 數量
- 仍希望保留合理治理證據
- 允許部分 execution docs 後補

## B1. Commit 1 — boundary owner + breaks alignment

### Include files
- `backend/app/modules/attendance/api/reporting_helpers.py`
- `backend/app/modules/attendance/tests/test_reporting_helpers_boundary.py`
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/tests/test_break_punches_boundary.py`
- `docs/attendance/remediation/02_fix/P2_BOUNDARY_FIX_SPEC.md`
- `docs/attendance/remediation/02_fix/P2_F1_EXECUTION_REPORT.md`
- `docs/attendance/remediation/02_fix/P2_F2_EXECUTION_REPORT.md`

### Recommended message
```text
feat(attendance): add Taipei boundary owner and align break-punches
```

### Rationale
若需壓縮 commit 數量，可將 F1 + F2 合併，因為兩者因果鏈連續且風險仍可接受。

---

## B2. Commit 2 — reporting alignment + runtime unblock

### Include files
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/tests/test_reporting_sessions.py`
- `backend/app/modules/attendance/tests/test_reporting_user_summary.py`
- `backend/app/modules/attendance/tests/test_reporting_company_summary.py`
- `backend/app/main.py`
- `docs/attendance/remediation/02_fix/P2_F3_FIX_SPEC.md`
- `docs/attendance/remediation/02_fix/P2_F3_BASELINE.md`
- `docs/attendance/remediation/02_fix/P2_F3_BLOCKER_REPORT.md`

### Recommended message
```text
fix(attendance): align reporting boundary owner and restore runtime validation path
```

### Rationale
若必須精簡，F3 與 runtime unblock 可收在同一票，但審閱時需特別標註：
- reporting boundary alignment
- runtime mismatch resolution
是兩類不同性質的修正

---

## B3. Commit 3 — minimal phase closeout docs

### Include files
- `docs/attendance/remediation/00_control/P2_PHASE_FINAL_SUMMARY.md`
- `docs/attendance/remediation/03_status/P2_COMMIT_PLAN.md`

### Recommended message
```text
docs(remediation): add Phase 2 final summary and commit plan
```

### Rationale
即使走精簡版，也建議將 final summary 與 commit plan 獨立成 docs commit。

---

# 5. Files That Should Be Committed Together

以下配對建議為**強建議**。

## 5.1 F1 code + F1 execution doc

應一起 commit：
- `backend/app/modules/attendance/api/reporting_helpers.py`
- `backend/app/modules/attendance/tests/test_reporting_helpers_boundary.py`
- `docs/attendance/remediation/02_fix/P2_F1_EXECUTION_REPORT.md`

## 5.2 F2 code + F2 execution doc

應一起 commit：
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/tests/test_break_punches_boundary.py`
- `docs/attendance/remediation/02_fix/P2_F2_EXECUTION_REPORT.md`

## 5.3 F3 code + F3 baseline/spec

應一起 commit：
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/tests/test_reporting_sessions.py`
- `backend/app/modules/attendance/tests/test_reporting_user_summary.py`
- `backend/app/modules/attendance/tests/test_reporting_company_summary.py`
- `docs/attendance/remediation/02_fix/P2_F3_FIX_SPEC.md`
- `docs/attendance/remediation/02_fix/P2_F3_BASELINE.md`

## 5.4 Runtime unblock + blocker report

應一起 commit：
- `backend/app/main.py`
- `docs/attendance/remediation/02_fix/P2_F3_BLOCKER_REPORT.md`

---

# 6. Files That May Be Added Later

以下文件可視團隊節奏選擇後補，但不建議永久缺失：

- `docs/attendance/remediation/00_control/P2_PHASE_FINAL_SUMMARY.md`
- `docs/attendance/remediation/03_status/P2_COMMIT_PLAN.md`

若採精簡版，這兩份文件可在 code merge 後補一個 docs-only commit。

---

# 7. Files That Should Not Be Mixed Carelessly

以下檔案不建議與其他 Phase / unrelated cleanup 混在一起：

- `backend/app/main.py`
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/api/reporting_helpers.py`

原因：

- `main.py` 是 app entry / runtime unblock
- `reporting.py` 是 F3 boundary convergence 主體
- `breaks.py` 是 F2 convergence 主體
- `reporting_helpers.py` 是 F1 owner source

這四者都屬於 Phase 2 因果鏈中的關鍵檔，不應與 unrelated formatting / cleanup / Phase 3 work 混合提交。

---

# 8. Recommended Operator Choice

若目前目標是：

- **最大審閱清晰度**
- **最強可審計性**
- **最容易 rollback 某一階段**

則建議選：

- **Version A — 最穩定版**

若目前目標是：

- **減少 commit 數量**
- **快速完成 Phase 2 收尾入庫**
- **仍保留核心治理文件**

則可選：

- **Version B — 精簡版**

---

# 9. Final Recommendation

本文件的正式建議為：

- **預設採用 Version A**

理由：

1. F1 / F2 / F3 的責任邊界清楚
2. `main.py` runtime unblock 性質特殊，獨立提交最安全
3. 各 execution / baseline / blocker 文件可與對應 code 成對審閱
4. 日後若需追查 representation、runtime mismatch、boundary contract 演進，Version A 最易審計

一句話總結：

**若沒有明確時間壓力，Phase 2 應以 Version A 收尾；若需要縮短提交序列，則以 Version B 作為可接受但次佳的治理替代方案。**
