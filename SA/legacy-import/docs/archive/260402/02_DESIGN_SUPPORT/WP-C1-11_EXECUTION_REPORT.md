# WP-C1-11 Execution Report — OUT Checkpoint API Implementation

**完成日期：** 2026-03-18  
**執行者：** Cursor AI Agent  
**前置票：** WP-C1-10A（Closeout Audit）  
**性質：** Blocking Gap Resolution — GAP-C1-002

---

## 1. Files Changed

| 檔案 | 修改目的 |
|------|----------|
| `backend/app/modules/attendance/api.py` | 新增 `POST /out-checkpoint` + `GET /out-checkpoints` 兩個 endpoint；更新 schema/repo import |
| `backend/app/modules/attendance/tests/conftest.py` | 新增 `test_entitlement` fixture，確保 `attendance.core` feature gate 通過測試 |
| `backend/app/modules/attendance/docs.md` | 同步新增兩個 endpoint 的 API 記錄與測試記錄 |
| `docs/03_WP_CONTROL/NEXT_WP_TICKET.md` | WP-C1-11 狀態更新為 COMPLETE；GAP-C1-002 標示 RESOLVED |
| `docs/03_WP_CONTROL/GATE_PROGRESS_TRACKER.md` | 加入 WP-C1-11 完成記錄 |

---

## 2. API Implementation Result

### 新增 Endpoints

#### `POST /api/v1/attendance/out-checkpoint`
- **Auth：** `get_actor_with_company`（JWT Actor，WP-C1-07 canonical pattern）
- **Feature Gate：** `_require_attendance_feature(company_id, db)`
- **Tenant Isolation：** `company_id` 強制由 JWT Actor 取得，不信任 request body
- **GPS Validation：** `device_type=mobile` 且未提供 GPS → 422（`GPS_REQUIRED`）
- **De-dup：** 30 秒內 + 50 公尺內重複打卡 → 409（`DUPLICATE_CHECKPOINT`）
- **Session：** `session_id` optional（無 open session 亦允許建立 checkpoint）
- **Response：** `OutCheckpointResponse`（`checkpoint_id`, `punch_time`, `gps`, `message`）

#### `GET /api/v1/attendance/out-checkpoints`
- **Auth：** `get_actor_with_company`（JWT Actor）
- **Feature Gate：** `_require_attendance_feature(company_id, db)`
- **Tenant Isolation：** `company_id` 強制由 JWT Actor 取得
- **分頁：** `limit`（1-100）、`offset`
- **Response：** `OutCheckpointListResponse`（`checkpoints`, `total`, `limit`, `offset`）

### 重用現有元件
- **Schema：** `OutCheckpointRequest`, `OutCheckpointResponse`, `OutCheckpointListItem`, `OutCheckpointListResponse`, `GPSData`（均已存在於 `schemas.py`）
- **Repo：** `OutCheckpointRepository`（`create_checkpoint`, `get_recent_checkpoint`, `get_checkpoints`, `count_checkpoints`）（已存在於 `repo.py`）
- **GPS Utils：** `is_within_distance()` from `gps_utils.py`（已存在）
- **Model：** `AttendanceOutCheckpoint`（已存在於 `models.py`）

### 未處理殘缺
- 無。所有 blocking gap 已解決。

---

## 3. Test Result

### 直接相關測試：`test_out_checkpoint.py`

| 測試 | 結果 |
|------|------|
| `TestOutCheckpointMultiSubmit::test_multi_checkpoint_allowed` | ✅ PASS |
| `TestOutCheckpointGPSValidation::test_mobile_requires_gps` | ✅ PASS |
| `TestOutCheckpointGPSValidation::test_pc_no_gps_allowed` | ✅ PASS |
| `TestOutCheckpointDedup::test_anti_spam_duplicate_checkpoint` | ✅ PASS |
| `TestOutCheckpointGPSCoordinates::test_invalid_latitude` | ✅ PASS |
| `TestOutCheckpointList::test_list_checkpoints_pagination` | ✅ PASS |
| `TestOutCheckpointWithoutSession::test_checkpoint_without_session` | ✅ PASS |

**結果：7/7 PASS**（原始 7/7 FAIL → 7/7 PASS）

### 全 attendance 測試（排除 pre-existing collection error）

```
136 passed, 9 failed, 9 errors（test_migration.py collection error 排除）
```

- 9 FAIL / 9 ERROR 均為 pre-existing，與本票無關（`test_business_invariant`, `test_location_policy`, `test_tenant_isolation`, `test_regression`, `test_tenant_validation`）
- 本票未引入任何新 FAIL

---

## 4. Docs Sync Result

- **attendance/docs.md updated：** YES
  - 加入 `POST /out-checkpoint` endpoint 記錄
  - 加入 `GET /out-checkpoints` endpoint 記錄
  - 加入 `test_out_checkpoint.py` 測試記錄
- **NEXT_WP_TICKET.md updated：** YES（WP-C1-11 → COMPLETE；GAP-C1-002 → RESOLVED）
- **GATE_PROGRESS_TRACKER.md updated：** YES（加入 WP-C1-11 完成記錄）
- **WORKSTREAM_STATUS_LEDGER.md：** 未修改（舊記錄描述不同票，非本票範圍）
- **MODULE_STATUS_MATRIX.md：** 未修改（未觸及範圍）

---

## 5. Scope Control Confirmation

| 項目 | 結果 |
|------|------|
| production code changed | YES（api.py：新增 2 endpoints + import） |
| API behavior changed | YES（新增缺失 endpoint，不破壞既有 API） |
| test files changed | YES（conftest.py：新增 test_entitlement fixture） |
| repo cleanup performed | NO |
| JWT architecture changed | NO |
| unrelated endpoints modified | NO |
| leave / audit / backup / notifications touched | NO |
| reporting tests touched | NO |
| outing redesign performed | NO |

---

## 6. Final Recommendation

- **WP-C1-11：** ✅ COMPLETED
- **GAP-C1-002：** ✅ RESOLVED（OUT Checkpoint API endpoint 已實作，7/7 blocking tests PASS）
- **可進入下一張票：** YES
  - 建議下一步：test stabilization ticket（處理 pre-existing 9 FAIL / 9 ERROR）或 closeout audit
- **Attendance Checkpoint Residual Gap：** 無。OUT Checkpoint API 完整實作，mobile GPS validation、de-dup、session optional、分頁列表均已覆蓋。

---

*本報告依實際執行結果產生，所有測試數據均為實際 pytest 執行結果。*
