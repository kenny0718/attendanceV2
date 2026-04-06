# P2 F1 Execution Report — Taipei Boundary Normalization Owner

> **Document Type**: Execution Report
> **Phase**: 2 — Taipei Business Date Boundary Alignment
> **Ticket**: F1 First Cut — Define canonical Taipei boundary normalization owner
> **Execution Mode**: Code + test execution completed
> **Status**: Done
> **Inputs**:
> - `docs/attendance/remediation/02_fix/P2_BOUNDARY_FIX_SPEC.md`
> - `docs/attendance/remediation/02_fix/P2_F1_FIX_DECOMPOSITION.md`
> - `backend/app/modules/attendance/api/reporting_helpers.py`
> **Last Updated**: 2026-04-06

---

# 0. Purpose

本文件記錄 Phase 2 / F1 第一刀的實際執行結果。

本次工作的唯一目標是：
- 在 pure/helper layer 建立單一 Taipei business-date normalization owner
- 不接入任何現有 runtime route / service / repo
- 不改變任何現有 reporting / breaks 行為

---

# 1. Files Changed

本次實際變更檔案只有：
- `backend/app/modules/attendance/api/reporting_helpers.py`
- `backend/app/modules/attendance/tests/test_reporting_helpers_boundary.py`

本次未修改：
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/reporting_repo.py`
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/main.py`
- `backend/app/modules/attendance/api/__init__.py`
- 任何 schema / migration 檔

---

# 2. New Helper / Function Signature

本次新增 pure/helper owner 與 result model：

```python
@dataclass(frozen=True)
class TaipeiBusinessDateBoundary:
    business_date: date
    timezone_name: str
    start_local: datetime
    end_local: datetime
    start_utc: datetime
    end_utc: datetime
```

```python
def get_taipei_today(now: Optional[datetime] = None) -> date:
```

```python
def build_taipei_business_date_boundary(
    business_date: date,
) -> TaipeiBusinessDateBoundary:
```

---

# 3. Boundary Contract Summary

本次建立的 canonical pure/helper contract 為：

1. `today` 一律以 `Asia/Taipei` 為 owner
2. `business_date` 一律解讀為 Taipei local calendar date
3. 先建立 Taipei local boundary：
   - `start_local`
   - `end_local`
4. 再轉成 canonical UTC query boundary：
   - `start_utc`
   - `end_utc`
5. query shape 固定為：
   - `>= start_utc`
   - `< end_utc`

本次 contract 只存在於 pure/helper layer，尚未接線。

---

# 4. Safety Execution Notes

本次依要求使用 `.tmp` 流程：

1. 先建立：
   - `reporting_helpers.py.tmp`
   - `test_reporting_helpers_boundary.py.tmp`
2. 讀回 `.tmp` 內容確認
3. 確認正式檔仍非 0KB
4. 再覆蓋正式檔
5. 完成驗證後刪除 `.tmp`

執行過程中曾二度遇到：
- `reporting_helpers.py` 意外變成 0KB

處理方式：
- 立即停止
- 從版本庫安全復原
- 重新走 `.tmp` 流程
- 未在 0KB 狀態下直接硬寫正式檔

---

# 5. Test Results

## 5.1 Compile Validation
已通過：

```bash
python3 -m py_compile backend/app/modules/attendance/api/reporting_helpers.py backend/app/modules/attendance/tests/test_reporting_helpers_boundary.py
```

## 5.2 Pure/helper Tests
已通過：

```bash
source venv/bin/activate
python -m pytest -q backend/app/modules/attendance/tests/test_reporting_helpers_boundary.py
```

執行結果：

```text
4 passed, 20 warnings in 0.03s
```

## 5.3 Covered Cases
本次 pure tests 覆蓋：
- Taipei today boundary
- business date -> UTC range
- cross-month basic boundary
- helper 純函式特性（同輸入同輸出）

## 5.4 Warnings
測試中出現的 warnings 為既有：
- Pydantic V2 deprecation warnings
- FastAPI `on_event` deprecation warning

判定：
- 非本票新引入
- 不構成 F1 失敗

---

# 6. Evidence: Not Wired into Runtime Flow

## Result
- **YES — 目前未接入任何 route / service / repo**

## Evidence
1. 本次未修改：
   - `breaks.py`
   - `reporting.py`
   - `reporting_repo.py`
   - `repo.py`
   - `service.py`
2. 未修改任何 import path / runtime wiring
3. 對 attendance 模組內搜尋：
   - `get_taipei_today`
   - `build_taipei_business_date_boundary`
   - `TaipeiBusinessDateBoundary`
   未發現既有 route / service / repo 使用點
4. 現有 `_normalize_to_utc(...)` 行為仍保留，未被替換

結論：
- 新 owner 已存在
- 但系統 runtime flow 尚未依附它

---

# 7. Final Result

本次 P2 / F1 第一刀可判定為：

- **Execution Result: PASS**

原因：
- 單一 Taipei business-date normalization owner 已建立
- 結果 model 已建立
- pure tests 已新增並通過
- 未修改任何受禁 route / repo / service 檔案
- 未接入 runtime flow
- 符合 F1「只建立 owner、不接線」的要求

一句話總結：

**P2 F1 已成功完成，Taipei business-date 現在有一個 pure/helper 層的 canonical owner，但 breaks 與 reporting 尚未接入，runtime 行為仍維持原狀。**
