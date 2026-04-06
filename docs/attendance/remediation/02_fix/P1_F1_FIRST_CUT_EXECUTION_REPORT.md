# P1 F1 First-Cut Execution Report

> **Document Type**: Execution Report
> **Phase**: 1 — Option B / F1
> **Ticket**: First Cut — Introduce canonical pure calculation source
> **Execution Mode**: Code + test execution completed
> **Status**: Done
> **Inputs**:
> - `docs/attendance/remediation/02_fix/P1_OPTION_B_FIX_DECOMPOSITION.md`
> - `docs/attendance/remediation/02_fix/P1_F1_GATE.md`
> - `docs/attendance/remediation/02_fix/P1_F1_FIX_SPEC.md`
> **Last Updated**: 2026-04-06

---

# 0. Purpose

本文件記錄 P1 / F1 第一刀的實際執行結果。

本次工作的唯一目標是：
- 在 pure layer 建立 canonical duration 計算來源
- 不改變任何既有 runtime 行為
- 不接入主鏈

本文件重點回答：
- 實際改了哪些檔案
- 新增了哪些 pure function / DTO
- 測試是否通過
- 是否完全未影響既有 flow

---

# 1. Execution Scope

## 1.1 實際允許範圍
本次執行遵守 F1 Gate 與 Fix Spec，只在 pure layer 內工作。

## 1.2 實際修改檔案
本次實際修改檔案只有 2 個：
- `backend/app/modules/attendance/work_hour_engine.py`
- `backend/app/modules/attendance/tests/test_work_hour_engine.py`

## 1.3 未修改檔案
本次未修改以下高風險主鏈檔案：
- `backend/app/modules/attendance/api/punch.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/punch_close_domain.py`
- `backend/app/modules/attendance/policy_engine.py`
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/reporting_service.py`
- `backend/app/modules/attendance/reporting_repo.py`
- 任何 schema / migration 檔

---

# 2. Files Changed

## 2.1 `backend/app/modules/attendance/work_hour_engine.py`
新增：
- `CanonicalWorkDurationResult`
- `calculate_canonical_work_duration(...)`

保留不變：
- `calculate_work_duration(...)`
- `calculate_break_deduction(...)`
- 既有 `BreakPunchDTO` / `BreakDeductionResult` 行為

## 2.2 `backend/app/modules/attendance/tests/test_work_hour_engine.py`
新增 pure calculation tests，驗證：
- canonical = gross（無 break）
- canonical = gross - break（單段 break）
- 多段 break 時 canonical 結果正確
- 新 function signature 保持 pure function 型態

---

# 3. Function Signature

本次新增的 canonical pure function 為：

```python
def calculate_canonical_work_duration(
    punch_in_time: datetime,
    punch_out_time: datetime,
    break_punches: List[BreakPunchDTO],
) -> CanonicalWorkDurationResult:
```

## 3.1 Function Role
此 function 的角色為：
- 作為 F1 階段的 canonical pure calculation source
- 以 pure composition 方式重用：
  - `calculate_work_duration(...)`
  - `calculate_break_deduction(...)`

## 3.2 Function Boundary
此 function：
- 不碰 DB
- 不碰 repo
- 不碰 API
- 不碰 policy
- 不碰 reporting
- 不寫 session state
- 不接入 runtime flow

---

# 4. Result Model Definition

本次新增 DTO：

```python
@dataclass
class CanonicalWorkDurationResult:
    gross_minutes: int
    break_minutes: int
    canonical_minutes: int
    valid_break_pair_count: int
    anomaly_count: int
    anomalies: List[BreakAnomaly] = field(default_factory=list)
    was_clamped: bool = False
    pairing_strategy: str = "tolerant_state_machine"
    rounding_strategy: str = "floor_per_segment"
```

## 4.1 Semantic Meaning
- `gross_minutes`
  - 原始工時
- `break_minutes`
  - break deduction
- `canonical_minutes`
  - net work duration

## 4.2 Compatibility Meaning
在 F1 階段：
- `canonical_minutes` 只是 pure output
- **不代表** 系統已切換 persisted `duration_minutes` semantics

---

# 5. Safety Execution Notes

## 5.1 安全寫入方式
本次實作依要求先採用 `.tmp` 安全流程：
1. 先產生 `.tmp` 版本
2. 讀回檢查 `.tmp` 內容
3. 確認無誤後再覆蓋正式檔
4. 最後刪除 `.tmp`

## 5.2 中途異常處理
執行過程中曾發現：
- `work_hour_engine.py` 一度出現 0KB 異常
- `backend/app/main.py` 一度出現 0KB 異常

處理方式：
- 皆先依 git 版本安全復原
- 復原後才繼續執行
- 未在 0KB 狀態下強行覆寫正式檔

這符合本次票的 Stop Condition 與安全邊界要求。

---

# 6. Test Results

## 6.1 Compile Validation
已通過：

```bash
python3 -m py_compile backend/app/modules/attendance/work_hour_engine.py backend/app/modules/attendance/tests/test_work_hour_engine.py
```

## 6.2 venv Test Validation
依要求使用專案既有 venv：

```bash
source venv/bin/activate
python -m pytest -q backend/app/modules/attendance/tests/test_work_hour_engine.py
```

執行結果：

```text
38 passed, 20 warnings in 0.10s
```

## 6.3 Warnings
本次測試中出現的 warnings 為：
- Pydantic V2 deprecation warnings
- FastAPI `on_event` deprecation warning

判定：
- 非本票新引入
- 不構成 F1 第一刀失敗

---

# 7. Existing Flow Impact Assessment

## 7.1 是否完全未影響既有 flow
**YES**

## 7.2 Evidence
證據如下：

1. 本次只修改 pure layer 與純測試檔
2. 未修改任何 API / repo / policy / reporting 主鏈檔案
3. 未改 import path
4. 未改 runtime wiring
5. 未讓 `calculate_canonical_work_duration(...)` 被現有 flow 呼叫
6. 未替換任何既有 `gross_minutes` 使用點
7. `calculate_work_duration(...)` 既有語意維持不變
8. `calculate_break_deduction(...)` 既有語意維持不變
9. 純測試全部通過

---

# 8. Git Status Snapshot

在本次收尾時，與 F1 直接相關的變更為：
- `backend/app/modules/attendance/work_hour_engine.py`
- `backend/app/modules/attendance/tests/test_work_hour_engine.py`
- `docs/attendance/remediation/02_fix/P1_F1_AUDIT_CANONICAL_SOURCE.md`
- `docs/attendance/remediation/02_fix/P1_F1_FIX_SPEC.md`
- `docs/attendance/remediation/02_fix/P1_F1_GATE.md`

本次執行過程產生的 `.tmp` 已刪除，不再留在工作樹中。

---

# 9. Final Result

本次 F1 第一刀可判定為：

- **Execution Result: PASS**

原因：
- canonical pure calculation source 已建立
- DTO 已建立
- pure tests 已新增並通過
- runtime flow 未被接入
- 既有 gross semantics 未受影響
- 未越界進入 F2 / F3

一句話總結：

**F1 第一刀已成功完成，canonical 現在有一個安全存在的 pure layer 位置，但系統仍完全維持現有 gross runtime semantics。**
