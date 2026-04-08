# P2 F2 Execution Report — Align break-punches to Canonical Taipei Boundary Owner

> **Document Type**: Execution Report
> **Phase**: 2 — Taipei Business Date Boundary Alignment
> **Ticket**: F2 — Align `break-punches` to the canonical Taipei boundary normalization owner
> **Execution Mode**: Code + test execution completed
> **Status**: Done
> **Inputs**:
> - `docs/attendance/remediation/02_fix/P2_BOUNDARY_FIX_SPEC.md`
> - `docs/attendance/remediation/02_fix/P2_F1_FIX_DECOMPOSITION.md`
> - `docs/attendance/remediation/02_fix/P2_F1_EXECUTION_REPORT.md`
> - `docs/attendance/remediation/02_fix/P2_F2_FIX_SPEC.md`
> - `backend/app/modules/attendance/api/breaks.py`
> - `backend/app/modules/attendance/tests/test_break_punches_boundary.py`
> **Last Updated**: 2026-04-06

---

# 0. Purpose

本文件記錄 Phase 2 / F2 的實際執行結果。

本次工作的唯一目標是：
- 讓 `GET /api/v1/attendance/break-punches`
- 不再使用 route-level UTC-based today boundary
- 改為依附 F1 已建立的 canonical Taipei boundary normalization owner
- 並且只替換 boundary source，不改 query shape，不影響 reporting

---

# 1. Files Changed

本次實際變更檔案只有：
- `backend/app/modules/attendance/api/breaks.py`
- `backend/app/modules/attendance/tests/test_break_punches_boundary.py`

本次未修改的高風險檔案：
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/api/reporting_helpers.py`
- `backend/app/modules/attendance/reporting_repo.py`
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/service.py`
- `backend/app/main.py`
- `backend/app/modules/attendance/api/__init__.py`
- 任何 schema / migration 檔

---

# 2. Boundary Change Summary

## 2.1 Before: Route-Level UTC-Based Today Logic

F2 之前，`break-punches` 在 `breaks.py` 內直接使用：
- `date.today()`
- `datetime.combine(...)`
- `.replace(tzinfo=timezone.utc)`

其邏輯本質為：
- 由 route 自行決定 today
- 直接建立 UTC-based day boundary
- 再以該 boundary 查詢 break punches

這種做法已在 Phase 2 audit / spec 中被判定為：
- route-level boundary ownership
- UTC-based pseudo-business-day logic
- 不符合 Taipei business-date contract

## 2.2 After: Taipei Boundary Owner

F2 完成後，`break-punches` 改為透過 F1 owner 取得：
- `start_utc`
- `end_utc`

也就是：
1. 先由 `Asia/Taipei` owner 決定 business day
2. 再由 helper 層產出 canonical UTC query boundary
3. route 只消費 boundary 結果，不再自行重算 Taipei boundary

## 2.3 Query Shape Preserved

本次變更只替換 boundary source，未改 query shape。

修改後查詢條件仍固定為：
- `AttendancePunch.punch_time >= start_utc`
- `AttendancePunch.punch_time < end_utc`

因此：
- query filtering shape 未改
- query ordering 未改
- response shaping 未改

---

# 3. Owner Usage

## 3.1 Used F1 Owner Functions

本次 F2 使用的 F1 owner function 為：

```python
get_taipei_today
build_taipei_business_date_boundary
```

來源檔案：
- `backend/app/modules/attendance/api/reporting_helpers.py`

## 3.2 Ownership Statement

本次 F2 的 ownership 接線方式為：
- `breaks.py` 直接取用 F1 已建立的 helper owner
- route 不再自行定義 today boundary
- route 不再自行做 Taipei date -> UTC range 推導

## 3.3 No Second Logic Introduced

本次明確未新增：
- 第二套 boundary helper
- break 專用 Taipei boundary 規則
- route-local duplicated today logic

結論：
- **F2 使用既有 F1 owner**
- **未新增第二套邏輯**

---

# 4. Safety Execution Notes

本次依要求使用 `.tmp` 流程：

1. 先建立：
   - `breaks.py.tmp`
   - `test_break_punches_boundary.py.tmp`
2. 讀回 `.tmp` 內容確認
3. 確認正式檔仍非 0KB
4. 先做 `.tmp` 編譯檢查
5. 再以原子覆蓋方式落位正式檔
6. 覆蓋後再執行正式 compile / tests / baseline-after compare

## 4.1 0KB Status

本次執行過程中：
- **未出現 `breaks.py` 變成 0KB**

## 4.2 Abnormal Interruptions

本次執行過程中有兩次測試資料建立相關異常：
- 測試資料腳本首次執行時遇到 import path 問題
- baseline 建立時曾遇到測試資料 FK 插入順序問題

這兩者皆屬：
- 測試資料組裝 / 執行環境問題
- 非產品程式邏輯異常
- 未造成正式檔損壞
- 未造成 `.tmp` 流程中斷為危險狀態

結論：
- 有短暫驗證腳本修正
- **無危險性中斷**
- **無 0KB 事故**

---

# 5. Test Results

## 5.1 Compile Validation

已通過：

```bash
python3 -m py_compile backend/app/modules/attendance/api/breaks.py backend/app/modules/attendance/tests/test_break_punches_boundary.py
```

## 5.2 New Tests Added

本次新增測試檔：
- `backend/app/modules/attendance/tests/test_break_punches_boundary.py`

執行指令：

```bash
pytest -q backend/app/modules/attendance/tests/test_break_punches_boundary.py
```

執行結果：

```text
3 passed, 20 warnings in 0.83s
```

## 5.3 Covered Cases

本次新增 tests 覆蓋：
- Taipei midnight boundary
  - `23:50 / 00:10` 歸屬正確
- Cross-day / UTC vs Taipei
  - UTC 前一日但 Taipei 已隔日
- Query correctness
  - `start_utc` inclusive
  - `end_utc` exclusive
  - 維持 `>= start_utc, < end_utc`

## 5.4 Existing Tests Impact

本次另外驗證既有 F1 pure/helper boundary tests：

```bash
pytest -q backend/app/modules/attendance/tests/test_reporting_helpers_boundary.py
```

執行結果：

```text
4 passed, 20 warnings in 0.03s
```

判定：
- F1 owner helper 行為未受影響
- 本次接線未破壞既有 boundary owner contract

## 5.5 Warnings

測試中出現的 warnings 為既有：
- Pydantic V2 deprecation warnings
- FastAPI `on_event` deprecation warning

判定：
- 非本票新引入
- 不構成 F2 失敗

---

# 6. Baseline vs After

## 6.1 Baseline (Before)

使用固定測試資料、固定查詢條件：
- `GET /api/v1/attendance/break-punches?limit=50`

Baseline 結果：
- 筆數：`2`
- 最早：`2026-04-06T23:50:00+08:00`
- 最晚：`2026-04-07T00:10:00+08:00`
- 是否跨日：`True`

## 6.2 After

使用與 baseline 相同的固定資料與相同查詢條件重查：

After 結果：
- 筆數：`2`
- 最早：`2026-04-06T00:10:00+08:00`
- 最晚：`2026-04-06T23:50:00+08:00`
- 是否跨日：`False`

## 6.3 Difference Explanation

本次 before / after 的差異為：
- 筆數不變
- 時間範圍改變
- 跨日狀態由 `True` 變為 `False`

原因是：
- 修改前以 UTC-based today boundary 查詢
- 會把台北 business day 的午夜附近記錄錯分到錯誤的「today」集合
- 修改後改為 Taipei business-date owner
- 同一個 Taipei business day 的 `00:10` 與 `23:50` 被正確歸到同一天

## 6.4 Audit Judgment

本次差異判定為：
- **合理**
- **可解釋**
- **屬於修正性變化（corrective change）**

這不是額外引入的新規則，
而是把 `break-punches` 拉回已在 Phase 2 規格中明確定義的 Taipei business-date contract。

---

# 7. Reporting Impact Assessment

## Result
- **YES — 完全未影響 reporting**

## Evidence
1. 本次未修改：
   - `backend/app/modules/attendance/api/reporting.py`
   - `backend/app/modules/attendance/api/reporting_helpers.py`
   - `backend/app/modules/attendance/reporting_repo.py`

2. 本次僅修改：
   - `backend/app/modules/attendance/api/breaks.py`
   - `backend/app/modules/attendance/tests/test_break_punches_boundary.py`

3. F1 owner helper 檔案本身未改動，只被 `breaks.py` 取用

4. 既有 F1 helper tests 仍通過：
   - `test_reporting_helpers_boundary.py` → `4 passed`

結論：
- reporting route / helper / repo 行為均未改動
- 本次影響面限定於 `break-punches` boundary ownership 對齊

---

# 8. Final Result

本次 P2 / F2 可判定為：

- **Execution Result: PASS**

原因：
- `break-punches` 已改用 Taipei boundary normalization owner
- 只替換 boundary source
- query shape 未改
- response shaping 未改
- 新增 tests 已通過
- 既有 F1 tests 未受影響
- baseline / after 差異可合理解釋，且屬修正性變化
- 未影響 reporting
- `.tmp` 安全流程已完成，無 0KB 事故

一句話總結：

**P2 F2 已成功完成，`break-punches` 現在正式依附 F1 的 Taipei business-date owner，行為修正為 Taipei 業務日邊界，且未影響 reporting。**
