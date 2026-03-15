# WP-11-08 Leave API Manual Test Report

## Summary

| 項目 | 內容 |
|------|------|
| **WP** | WP-11-08 Leave Request System |
| **測試日期** | 2026-03-15 |
| **測試結果** | ✅ PASS |
| **測試範圍** | 5 個 Leave API endpoints |
| **測試環境** | localhost:8765，PostgreSQL，company-a |

---

## Test Data Used

| 項目 | 值 |
|------|----|
| `company_id` | `company-a` |
| `user_id` | `11bda10d-7541-4230-b1f3-842afab2cea5`（測試員工）|
| `leave_type_id` | `9b3fa51a-5d0e-427c-b9ad-8a6af10998b0`（特休假）|
| matched policy | company-wide default，min=0.5 days，max=無上限，approval_level=1 |

---

## Endpoint Test Results

| Endpoint | HTTP | 結果 | 說明 |
|----------|------|------|------|
| `POST /api/v1/leave/requests` | 201 | ✅ PASS | status=pending，reason 自動 trim，total_days=3.0 正確計算，required_approval_level=1 |
| `GET /api/v1/leave/my-requests` | 200 | ✅ PASS | total=1，status=pending filter 正常 |
| `GET /api/v1/leave/pending` | 200 | ✅ PASS | total=1，pending request 正確出現 |
| `POST /api/v1/leave/requests/{id}/approve` | 200 | ✅ PASS | status 變為 `approved` |
| `POST /api/v1/leave/requests/{id}/reject` | 200 | ✅ PASS | status 變為 `rejected` |

---

## State Transition Results

| 轉換 | 結果 |
|------|------|
| `pending → approved` | ✅ PASS |
| `pending → rejected` | ✅ PASS |
| 重複 approve 已結案 request | ✅ HTTP 409，`error_code: INVALID_STATUS_TRANSITION` |
| 重複 reject 已結案 request | ✅ HTTP 409，`error_code: INVALID_STATUS_TRANSITION` |

---

## Isolation / Policy Results

| 項目 | 結果 |
|------|------|
| company_id 隔離 | ✅ 所有 repo 查詢強制帶 company_id |
| policy matching | ✅ company-wide default policy 正確匹配，approval_level=1 寫入 |
| approver 邏輯 | ⚠️ 最小版本：`approver_id=null`（待後續補齊）|

---

## Route Exposure Results

| 項目 | 結果 |
|------|------|
| cancel endpoint 暴露 | ✅ 未暴露（OpenAPI cancel routes: 0）|
| OpenAPI leave routes | ✅ 5 條，與預期完全一致 |

---

## Known Limitations

### approver_id 目前為 null

- `approver_id` 欄位在 `leave_requests` 中目前儲存為 `null`
- approver 解析邏輯（查 manager chain）在 Phase 2A 已標注為待補，不在本 WP 範圍
- **不影響核心 API 流程**：請假申請、審批通過、審批拒絕均可正常運作
- 後續需要在 submit_leave_request() 中加入 manager chain 查詢邏輯

---

## Files Implemented (WP-11-08)

| 檔案 | 說明 |
|------|------|
| `backend/alembic/env.py` | leave models 已加入 Alembic metadata |
| `backend/alembic/versions/009_wp_11_08_create_leave_tables.py` | leave tables migration |
| `backend/app/modules/leave/models.py` | LeaveType / LeaveApprovalPolicy / LeaveRequest / LeaveApprovalLog |
| `backend/app/modules/leave/schemas.py` | 所有 request/response/action schemas |
| `backend/app/modules/leave/repo.py` | 4 個 repository class，全部帶 company_id 隔離 |
| `backend/app/modules/leave/service.py` | submit / list / approve / reject / cancel service methods |
| `backend/app/modules/leave/api.py` | 5 個 FastAPI endpoints |
| `backend/app/main.py` | leave router 已掛載 |
| `backend/app/modules/auth/models.py` | 從備份還原（startup blocker 修復）|

---

## Final Verdict

**✅ WP-11-08 Leave API core workflow 完成**

- 5 個 endpoints 全部 PASS
- 狀態流轉正確，重複操作防護正常
- Tenant isolation 驗證通過
- cancel endpoint 未暴露
- 已可進入下一 workstream（WP-C1-03）
